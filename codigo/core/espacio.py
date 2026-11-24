"""El espacio de trabajo de un sistema: su biblioteca, su identidad, sus entradas y salidas.

Sustituyó a la biblioteca común, que guardaba el conocimiento de todos los sistemas en un
solo sitio. Aquí cada sistema lleva lo suyo dentro:

    sistemas/<sistema>/
      sistema.yaml     la ficha: qué es, sus especialistas y sus procesos
      biblioteca/      lo que ESTE sistema sabe
        oficial/       manuales y documentos de referencia
        investigacion/ notas de sus investigadores, con fuentes
        propio/        lo que escribiste tú
        originales/    PDFs de origen; no se indexan, ya están transcritos
      identidad/       quién eres EN ESTE SISTEMA (perfil, objetivos, narrativa, estilo)
      entradas/        lo que le das para trabajar
      salidas/         lo que produce
      .indice/         su índice de búsqueda (reconstruible, fuera de git)

Por qué así (decisiones D6, D7, D20): si el conocimiento vive fuera, desde dentro de un
sistema no puedes saber qué está usando. Y una biblioteca común crece hasta ser inmanejable.
Que dos sistemas necesiten el mismo documento es la excepción, y se resuelve duplicándolo.

Se va el concepto de «tema»: lo que un sistema sabe es **una** colección, la suya. Dentro de
cada procedencia puedes crear las carpetas que quieras, pero son carpetas, no una entidad
del modelo — y por eso ya no hace falta fusionar resultados de varias colecciones.

La mecánica —trocear, indexar, buscar, citar— sigue siendo la de
``core.services.knowledge_rag``. Este módulo solo decide QUÉ se indexa y DÓNDE.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from core.engine.paths import ROOT
from core.services.knowledge_rag import ingest as _ingest
from core.services.knowledge_rag import store as _store

#: Carpeta de procedencia -> tipo que entiende el buscador, y que decide cómo se presenta un
#: pasaje al citarlo («documento autoritativo», «texto propio»…).
PROCEDENCIAS: dict[str, str] = {
    "oficial": "downloaded",
    "investigacion": "research",
    "propio": "propio",
}

BIBLIOTECA = "biblioteca"
IDENTIDAD = "identidad"
ENTRADAS = "entradas"
SALIDAS = "salidas"
INDICE = ".indice"

#: `originales/` queda fuera a propósito: son los PDF de origen de documentos que ya están
#: transcritos, y volver a indexarlos duplicaría cada pasaje.
SIN_INDEXAR = "originales"

_SLUG = re.compile(r"^[a-z][a-z0-9-]*$")
_EXTENSIONES = {".md", ".txt", ".pdf"}


class EspacioError(ValueError):
    """Algo no cuadra en la estructura de un sistema."""


def _raiz() -> Path:
    """Raíz de los sistemas.

    Se resuelve aquí, y no importando ``core.systems``, para no crear un ciclo: la identidad
    pasará a leer de aquí, y ``systems`` ya importa la identidad.
    """
    return Path(os.environ.get("AGENT_PLATFORM_SISTEMAS") or ROOT / "sistemas")


def _variable_datos(sistema: str) -> str:
    return "AGENT_DATOS_" + sistema.upper().replace("-", "_")


def espacio_dir(sistema: str) -> Path:
    """Dónde están los datos de un sistema: identidad, entradas, biblioteca, salidas, índice.

    Por defecto, junto a su código. ``AGENT_DATOS_<SISTEMA>`` (p. ej. ``AGENT_DATOS_NETWORKING``)
    los saca a otra carpeta: así el código se puede compartir sin tus datos personales.
    """
    if not _SLUG.match(sistema or ""):
        raise EspacioError(
            f"Identificador de sistema inválido: {sistema!r}. En minúsculas y con guiones "
            "(p. ej. 'compraventa-coches')."
        )
    propio = os.environ.get(_variable_datos(sistema))
    return Path(propio) if propio else _raiz() / sistema


def biblioteca_dir(sistema: str) -> Path:
    return espacio_dir(sistema) / BIBLIOTECA


def identidad_dir(sistema: str) -> Path:
    return espacio_dir(sistema) / IDENTIDAD


def entradas_dir(sistema: str) -> Path:
    return espacio_dir(sistema) / ENTRADAS


def salidas_dir(sistema: str) -> Path:
    return espacio_dir(sistema) / SALIDAS


def index_dir(sistema: str) -> Path:
    """El índice vive dentro del sistema: es suyo y se va con él a la papelera."""
    return espacio_dir(sistema) / INDICE


def collection(sistema: str) -> str:
    """Una colección por sistema. El prefijo da los 3 caracteres que Chroma exige como mínimo."""
    return f"sistema-{sistema}"


def sources(sistema: str) -> list[tuple[Path, str]]:
    """Las carpetas de procedencia, existan o no todavía.

    Se devuelven también las que aún no existen: la primera nota de un investigador crea
    ``investigacion/`` después de construir el agente, y si la lista se fijara con las
    carpetas existentes esa nota no se indexaría nunca. La ingesta ya se salta las que no
    están.
    """
    base = biblioteca_dir(sistema)
    return [(base / carpeta, tipo) for carpeta, tipo in PROCEDENCIAS.items()]


def documents(sistema: str) -> dict[str, list[Path]]:
    """Los documentos indexables de un sistema, por procedencia."""
    base = biblioteca_dir(sistema)
    salida: dict[str, list[Path]] = {}
    for carpeta in PROCEDENCIAS:
        d = base / carpeta
        salida[carpeta] = sorted(
            p for p in d.rglob("*")
            if p.is_file() and p.suffix.lower() in _EXTENSIONES and p.name.lower() != "readme.md"
        ) if d.exists() else []
    return salida


def ficheros(carpeta: Path) -> list[Path]:
    """Lo que hay en una carpeta del espacio (entradas, salidas), sin lo oculto."""
    if not carpeta.exists():
        return []
    return sorted(
        p for p in carpeta.rglob("*")
        if p.is_file() and not p.name.startswith(".")
    )


def write_dir(sistema: str, procedencia: str = "investigacion") -> Path:
    """Dónde escribe un documento nuevo este sistema. Crea la carpeta si falta."""
    if procedencia not in PROCEDENCIAS:
        raise EspacioError(
            f"Procedencia desconocida: {procedencia!r}. Usa una de {sorted(PROCEDENCIAS)}."
        )
    destino = biblioteca_dir(sistema) / procedencia
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def frontmatter(ruta: Path) -> dict:
    """Lo que el documento declara de sí mismo (título, fecha, fuentes). {} si no declara nada."""
    if ruta.suffix.lower() != ".md":
        return {}
    meta, _ = _ingest._read_frontmatter(ruta.read_text(encoding="utf-8", errors="replace"))
    return meta


def titulo(ruta: Path) -> str:
    """Cómo se llama un documento: lo que declare, su primer encabezado, o su nombre."""
    texto = (
        ruta.read_text(encoding="utf-8", errors="replace")
        if ruta.suffix.lower() == ".md" else ""
    )
    return _ingest._title_from(frontmatter(ruta), texto, ruta)


#: Tope al leer un documento para enseñarlo. No es censura: es que una transcripción de un
#: libro entero bloquea la pantalla mientras se pinta, y para saber qué dice un documento no
#: hace falta cargarlo entero de golpe.
MAXIMO_LECTURA = 200_000

#: Lo que se puede leer aquí. Un PDF no: ya está transcrito a .md al lado, y enseñar bytes
#: en vez de decir la verdad («esto no se lee desde aquí») sería peor que no enseñarlo.
_LEGIBLES = {".md", ".txt"}


def leer(ruta: Path) -> str | None:
    """El contenido de un documento, para poder leerlo sin salir de la pantalla.

    Devuelve ``None`` cuando el formato no se puede leer aquí; quien llame lo dice en vez de
    fingir que está vacío. Antes los documentos solo se listaban por su nombre: sabías que
    existían y no lo que decían, que es la mitad de no poder fiarte de lo que hay dentro.
    """
    if ruta.suffix.lower() not in _LEGIBLES or not ruta.exists():
        return None
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    if len(texto) <= MAXIMO_LECTURA:
        return texto
    return texto[:MAXIMO_LECTURA] + "\n\n… (cortado aquí; el documento sigue en su fichero)"


def layers(sistema: str) -> list[tuple[Path, str, list[tuple[Path, str]]]]:
    """Lo que consulta un especialista de este sistema: su biblioteca, y solo la suya."""
    return [(index_dir(sistema), collection(sistema), sources(sistema))]


def consulta_agent(sistema: str, top_k: int = 6):
    """Un especialista que responde desde la biblioteca de este sistema, citando.

    Es el destino «consultar» de la caja «¿Qué necesitas?»: una pregunta puntual se responde
    y ya está, sin montar nada. No se registra ni pertenece a la ficha del sistema; se
    construye cuando hace falta, así que ve los documentos que haya en ese momento.
    """
    from core.services.knowledge_rag import rag_agent

    return rag_agent(
        path=(sistema,),
        name="consulta",
        title="Respuesta desde su biblioteca",
        description="Responde desde la biblioteca de este sistema, citando de dónde sale cada cosa.",
        layers=lambda: layers(sistema),
        top_k=top_k,
    )


def reindex(sistema: str) -> int:
    """Reconstruye el índice del sistema desde cero. Devuelve el número de fragmentos."""
    _store.reset_collection(index_dir(sistema), collection(sistema))
    return _ingest.ingest(
        index_dir(sistema), collection(sistema), sources(sistema), capa="biblioteca"
    )
