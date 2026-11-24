from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from core import espacio, identity
from sistemas.networking.config import DATA_PATH

# Quién eres EN NETWORKING: vive en su propia carpeta `identidad/`, porque puedes querer
# una voz distinta en cada sistema (D8). Desde aquí se leen y se editan igual que antes.
_IDENTITY_FILES = {"profile.md", "goals.md", "narrative.md", "style.md"}
#: El espacio de trabajo al que pertenece este código.
ESPACIO = "networking"

_PREFIJO_BIBLIOTECA = "biblioteca/"
_PROCEDENCIA_TEXTO = {
    "oficial": "documentos de referencia",
    "investigacion": "investigación",
    "propio": "escrito por ti",
}


def _raiz_y_ruta(relpath: str) -> tuple[Path, str]:
    """Raíz a la que pertenece un documento, y su ruta dentro de ella."""
    if relpath in _IDENTITY_FILES:
        return identity.identidad_dir(ESPACIO), relpath
    if relpath.startswith(_PREFIJO_BIBLIOTECA):
        return espacio.biblioteca_dir(ESPACIO), relpath[len(_PREFIJO_BIBLIOTECA):]
    return DATA_PATH, relpath


@dataclass
class Doc:
    titulo: str
    relpath: str  # relativo a su raíz (ver _raiz_y_ruta)
    editable: bool
    grupo: str


# Documentos de estrategia: editables desde la app.
_ESTRATEGIA: list[Doc] = [
    Doc("Perfil profesional", "profile.md", True, "Estrategia"),
    Doc("Objetivos de búsqueda", "goals.md", True, "Estrategia"),
    Doc("Narrativa / pitch", "narrative.md", True, "Estrategia"),
    Doc("Estilo de comunicación", "style.md", True, "Estrategia"),
    Doc("Pendientes (plan de acción)", "pendientes.md", True, "Estrategia"),
    Doc("Candidatos identificados", "candidatos.md", True, "Estrategia"),
]


def _existe(relpath: str) -> bool:
    raiz, ruta = _raiz_y_ruta(relpath)
    return (raiz / ruta).exists()


def estrategia_docs() -> list[Doc]:
    return [d for d in _ESTRATEGIA if _existe(d.relpath)]


def biblioteca_docs() -> list[Doc]:
    """Consulta de solo lectura: la biblioteca de ESTE sistema y sus plantillas."""
    out: list[Doc] = []
    base = espacio.biblioteca_dir(ESPACIO)
    for procedencia, rutas in espacio.documents(ESPACIO).items():
        for p in rutas:
            if p.suffix.lower() != ".md":
                continue
            rel = p.relative_to(base).as_posix()
            out.append(Doc(p.stem, f"{_PREFIJO_BIBLIOTECA}{rel}", False,
                           _PROCEDENCIA_TEXTO[procedencia]))
    plantillas = DATA_PATH / "plantillas"
    if plantillas.exists():
        for p in sorted(plantillas.glob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            out.append(Doc(p.stem, str(p.relative_to(DATA_PATH)), False, "Plantillas"))
    return out


def biblioteca_por_grupo() -> "OrderedDict[str, list[Doc]]":
    grupos: "OrderedDict[str, list[Doc]]" = OrderedDict()
    for d in biblioteca_docs():
        grupos.setdefault(d.grupo, []).append(d)
    return grupos


def _safe_target(relpath: str) -> Path:
    raiz, ruta = _raiz_y_ruta(relpath)
    base = raiz.resolve()
    target = (base / ruta).resolve()
    # Defensa contra path traversal: el resultado debe vivir dentro de su raíz.
    if base != target and base not in target.parents:
        raise ValueError(f"Ruta fuera de su raíz: {relpath}")
    return target


def read_doc(relpath: str) -> str:
    target = _safe_target(relpath)
    if not target.exists():
        raise FileNotFoundError(relpath)
    return target.read_text(encoding="utf-8")


def write_doc(relpath: str, content: str) -> None:
    _safe_target(relpath).write_text(content, encoding="utf-8")
