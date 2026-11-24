"""Ingesta de conocimiento al vector store.

Recorre directorios de fuentes (md/txt/pdf), extrae procedencia (frontmatter si
existe), trocea y hace upsert idempotente (ids estables por hash). Cada chunk
lleva metadata de procedencia para que el RAG pueda citar.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from . import store

_CHUNK = 1000
_OVERLAP = 150


def _read_frontmatter(text: str) -> tuple[dict, str]:
    """Separa frontmatter YAML (--- ... ---) del cuerpo. ({}, text) si no hay."""
    if text.startswith("---"):
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
        if m:
            try:
                meta = yaml.safe_load(m.group(1)) or {}
                if isinstance(meta, dict):
                    return meta, m.group(2)
            except yaml.YAMLError:
                pass
    return {}, text


def _read_file(path: Path) -> tuple[dict, str]:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        texto = "\n".join((p.extract_text() or "") for p in reader.pages)
        return {}, texto
    texto = path.read_text(encoding="utf-8", errors="replace")
    return _read_frontmatter(texto)


def _chunks(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    out: list[str] = []
    i = 0
    while i < len(text):
        out.append(text[i : i + _CHUNK])
        i += _CHUNK - _OVERLAP
    return out


def _title_from(meta: dict, text: str, path: Path) -> str:
    if meta.get("title"):
        return str(meta["title"])
    # Primero un «#»; si no hay, un «##». Los artículos del redactor abren con «##», y sin
    # este segundo intento se citaban con el nombre del fichero: «substack».
    for patron in (r"^#\s+(.+)$", r"^##\s+(.+)$"):
        m = re.search(patron, text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return path.stem


def _id(source: str, idx: int) -> str:
    return hashlib.sha1(f"{source}#{idx}".encode("utf-8")).hexdigest()[:16]


def ingest(
    index_dir: Path,
    collection_name: str,
    sources: list[tuple[Path, str]],
    *,
    capa: str = "disciplina",
    columna: str = "",
) -> int:
    """Ingesta los directorios ``sources`` = [(dir, kind), ...]. Devuelve nº de chunks.

    ``kind`` ∈ {"downloaded", "research", "propio"} → nivel de confianza en la respuesta.
    ``propio`` es lo que ha escrito el usuario: su postura, no una fuente que la verifique.

    ``capa`` ∈ {"disciplina", "sector", "encargo"} → a qué altura de conocimiento
    pertenece lo ingestado (ver DISENO §5). Disciplina y sector pueden compartir colección
    porque se separan con este metadato al recuperar; el encargo va en colección aparte.
    ``columna`` es la procedencia cuando la capa es "encargo": sirve para saber de quién
    es cada chunk, no para aislarlo —eso lo hace la colección—.
    """
    collection = store.get_collection(index_dir, collection_name)
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []

    for base, kind in sources:
        if not base.exists():
            continue
        # Una fuente puede ser un fichero suelto, no solo un directorio: los borradores del
        # redactor guardan dos versiones del mismo texto (linkedin.md y substack.md), y
        # ingerir la carpeta entera metería cada idea dos veces y llenaría las citas de
        # duplicados.
        rutas = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in rutas:
            if path.suffix.lower() not in {".md", ".txt", ".pdf"} or not path.is_file():
                continue
            if path.name.lower() == "readme.md":
                continue
            meta, body = _read_file(path)
            rel = str(path)
            title = _title_from(meta, body, path)
            for idx, chunk in enumerate(_chunks(body)):
                ids.append(_id(rel, idx))
                docs.append(chunk)
                metas.append(
                    {
                        "source": path.name,
                        "title": title,
                        "url": str(meta.get("url") or meta.get("source") or ""),
                        "date": str(meta.get("date") or ""),
                        "kind": kind,
                        "capa": capa,
                        "columna": columna,
                    }
                )

    store.upsert(collection, ids, docs, metas)
    return len(ids)
