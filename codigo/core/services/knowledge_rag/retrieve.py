"""Recuperación por CAPAS: consulta varias colecciones y fusiona los rankings.

El conocimiento vive en tres capas (ver DISENO §5):

- **disciplina** — el oficio en general (SEO, CWV, E-E-A-T). Igual para todos los negocios.
- **sector** — el oficio aplicado a un tipo de negocio (SEO para retail local).
- **encargo** — lo que se ha producido sobre un negocio concreto.

Disciplina y sector comparten colección y se separan por metadato: no hay
confidencialidad en juego. El encargo lleva **colección propia**, porque un filtro
olvidado no falla —devuelve resultados de otro cliente—.

Consultar varias colecciones obliga a fusionar rankings, y sumar distancias de espacios
vectoriales distintos no significa nada. Se usa **Reciprocal Rank Fusion**, que combina
por POSICIÓN y no por puntuación, así que no le afecta que cada colección puntúe en su
propia escala. El algoritmo viene de ``agente-conver-rags`` (``ResultFusion.fuse_by_rrf``),
del que se muda la idea y no el andamiaje: allí hace falta un registro de proveedores
porque los RAGs son heterogéneos (uno llama a la API del BOE); aquí el almacén es uno.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from . import store

#: Constante de RRF. 60 es el valor del paper original y el que usa agente-conver-rags:
#: amortigua las primeras posiciones para que un solo ranking no domine la fusión.
_RRF_K = 60


def retrieve(
    index_dir: Path,
    collection_name: str,
    question: str,
    top_k: int = 6,
    where: dict | None = None,
) -> list[dict]:
    """Devuelve [{text, meta, distance}, ...] de UNA colección, por relevancia."""
    collection = store.get_collection(index_dir, collection_name)
    return store.query(collection, question, top_k, where)


def _clave(hit: dict) -> str:
    """Identidad de un chunk para deduplicar entre colecciones."""
    m = hit.get("meta") or {}
    return f"{m.get('source', '')}|{m.get('title', '')}|{hit.get('text', '')[:120]}"


#: Formas de fusionar los resultados de varias colecciones (ver :func:`retrieve_capas`).
FUSIONES = ("rrf", "distancia")


def retrieve_capas(
    capas: list[tuple[Path, str, dict | None]],
    question: str,
    top_k: int = 6,
    fusion: str = "rrf",
) -> list[dict]:
    """Consulta varias capas y fusiona los resultados.

    Dos fusiones, y elegir mal sale caro:

    - ``"rrf"`` (por defecto) combina por POSICIÓN. Es la correcta cuando las colecciones
      puntúan en escalas distintas. Su precio: el mejor resultado de una colección que no
      tiene nada que ver con la pregunta empata con el mejor de la que sí.
    - ``"distancia"`` ordena todo junto por distancia a la pregunta. Solo es válida si
      todas las colecciones usan el mismo modelo de embeddings —como los temas de la
      biblioteca—, porque entonces las distancias son comparables.

    ``capas`` es [(index_dir, nombre, where|None), ...]. Cada entrada lleva SU directorio
    de índice porque las capas no tienen por qué vivir juntas: la biblioteca guarda todos
    sus temas en ``biblioteca/.indice``, pero una ficha antigua indexa en su propia carpeta.

    El resultado va ordenado por la puntuación fusionada, con la procedencia en
    ``meta['coleccion']`` para que la respuesta pueda decir de dónde sale cada cosa.

    Se pide ``top_k`` a cada capa (no top_k repartido): que una esté vacía o sea poco
    relevante no debe dejar sin resultados a las demás.
    """
    if fusion not in FUSIONES:
        raise ValueError(f"Fusión desconocida: {fusion!r}. Usa una de {FUSIONES}.")

    puntuaciones: dict[str, float] = defaultdict(float)
    mejores: dict[str, dict] = {}

    for index_dir, nombre, where in capas:
        hits = retrieve(index_dir, nombre, question, top_k, where)
        for rango, hit in enumerate(hits):
            hit = {**hit, "meta": {**(hit.get("meta") or {}), "coleccion": nombre}}
            k = _clave(hit)
            puntuaciones[k] += 1.0 / (_RRF_K + rango + 1)
            # Si el mismo chunk sale en dos colecciones, nos quedamos con el más cercano.
            if k not in mejores or hit.get("distance", 1e9) < mejores[k].get("distance", 1e9):
                mejores[k] = hit

    if fusion == "distancia":
        ordenadas = sorted(mejores, key=lambda k: mejores[k].get("distance", 1e9))
        return [mejores[k] for k in ordenadas[:top_k]]

    ordenadas = sorted(puntuaciones, key=lambda k: puntuaciones[k], reverse=True)
    return [{**mejores[k], "rrf": puntuaciones[k]} for k in ordenadas[:top_k]]
