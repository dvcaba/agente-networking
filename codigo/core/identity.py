"""Quién eres **en un sistema**: perfil, narrativa, estilo, objetivos y muestras de voz.

Vive dentro de cada sistema, en ``sistemas/<sistema>/identidad/``, y no en un sitio común.
No es solo coherencia con que cada sistema sea autocontenido: es que **puedes querer una
identidad distinta en cada uno** — escribir en Contenido con una voz que no es la que usas
en Networking (decisión D8). Con una copia única eso es imposible.

Este módulo es solo el acceso cómodo desde los prompts: los ficheros son de quien los tiene.
"""

from __future__ import annotations

from pathlib import Path

from core import espacio

#: Nombre de los textos, sin extensión. Son los mismos que ya usabas.
PERFIL, NARRATIVA, ESTILO, OBJETIVOS = "profile", "narrative", "style", "goals"

def identidad_dir(sistema: str) -> Path:
    """Dónde están tus textos para este sistema.

    Se resuelve en cada llamada porque la raíz puede cambiar (los tests la apuntan a una
    carpeta temporal).
    """
    return espacio.identidad_dir(sistema)


def read(sistema: str, name: str) -> str:
    """Lee un texto tuyo por nombre, sin extensión. '' si no existe."""
    ruta = identidad_dir(sistema) / f"{name}.md"
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""


def profile(sistema: str) -> str:
    return read(sistema, PERFIL)


def narrative(sistema: str) -> str:
    return read(sistema, NARRATIVA)


def style(sistema: str) -> str:
    return read(sistema, ESTILO)


def goals(sistema: str) -> str:
    return read(sistema, OBJETIVOS)


def voice_samples(sistema: str, max_chars: int = 6000) -> str:
    """Tus muestras reales de voz (``identidad/voz/*.md``), concatenadas y truncadas.

    El tope existe porque esto entra dentro de un prompt: sin él, unas cuantas muestras
    largas se comen el encargo entero.
    """
    carpeta = identidad_dir(sistema) / "voz"
    if not carpeta.exists():
        return ""
    textos = [
        p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(carpeta.glob("*.md"))
    ]
    return "\n\n---\n\n".join(textos)[:max_chars]
