"""Vector store local (Chroma) — una colección por dominio.

Persistente en disco, embeddings locales con el embedder ONNX por defecto de
Chroma (sin torch, sin API key). Punto ÚNICO para cambiar de embedder: si la
calidad en español flojea, sustituir ``embedding_function`` por un modelo
multilingüe de sentence-transformers aquí.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings


def get_collection(index_dir: Path, name: str):
    """Devuelve (creando si hace falta) la colección persistente del dominio."""
    index_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(index_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    # embedding_function por defecto = ONNX MiniLM local (sin torch).
    return client.get_or_create_collection(name=name)


def reset_collection(index_dir: Path, name: str):
    """Vacía la colección y la devuelve vacía, lista para volver a indexar.

    Reindexar sin esto deja fragmentos de documentos que ya no existen: ``upsert`` añade y
    actualiza, pero nunca quita. Un documento borrado o renombrado seguiría citándose.
    """
    index_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(index_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    # Se comprueba antes de borrar: borrar una colección inexistente lanza NotFoundError.
    if name in {c.name for c in client.list_collections()}:
        client.delete_collection(name)
    return client.get_or_create_collection(name=name)


def upsert(collection, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
    if not ids:
        return
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def query(collection, text: str, top_k: int, where: dict | None = None) -> list[dict]:
    """Top-k chunks para una consulta, con su metadata y distancia.

    ``where`` filtra por metadatos (sintaxis de Chroma). Se usa para separar las CAPAS de
    conocimiento que comparten colección —disciplina y sector—: preguntar por SEO técnico
    y que conteste con notas de email marketing da una respuesta con citas y equivocada,
    que es peor que no tener RAG.

    Los hechos de un ENCARGO no se separan así: van en colección aparte. Un filtro
    olvidado no falla, devuelve resultados de otro cliente.
    """
    n = collection.count()
    if n == 0:
        return []
    res = collection.query(
        query_texts=[text], n_results=min(top_k, n), **({"where": where} if where else {})
    )
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    salida: list[dict] = []
    for doc, meta, dist in zip(docs, metas, dists):
        salida.append({"text": doc, "meta": meta or {}, "distance": dist})
    return salida
