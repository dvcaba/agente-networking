"""Los perfiles de gente a buscar: una nota de la biblioteca con búsquedas listas para usar.

La nota (``biblioteca/investigacion/perfiles-a-buscar.md``) dice a qué tipo de gente te
conviene conocer. «Buscar gente» la usa de dos formas: se la da al agente como criterio y
enseña sus búsquedas para lanzarlas con un clic. Si no existe, todo sigue funcionando.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core import espacio
from sistemas.networking import config  # noqa: F401 — fija dónde están tus datos

ESPACIO = "networking"
_FICHERO = "perfiles-a-buscar.md"
_PERFIL = re.compile(r"^###\s+(?:\d+\.\s*)?(.+?)\s*$")
_BUSQUEDA = re.compile(r"^\s*-\s+`([^`]+)`\s*$")


@dataclass(frozen=True)
class Busqueda:
    perfil: str
    texto: str


def ruta() -> Path:
    return espacio.biblioteca_dir(ESPACIO) / "investigacion" / _FICHERO


def texto() -> str:
    p = ruta()
    return p.read_text(encoding="utf-8") if p.exists() else ""


def busquedas() -> list[Busqueda]:
    """Las búsquedas listadas bajo cada perfil (líneas «- `…`»), en el orden de la nota."""
    out: list[Busqueda] = []
    perfil = ""
    for linea in texto().splitlines():
        if m := _PERFIL.match(linea):
            perfil = m.group(1)
        elif perfil and (m := _BUSQUEDA.match(linea)):
            out.append(Busqueda(perfil, m.group(1)))
    return out
