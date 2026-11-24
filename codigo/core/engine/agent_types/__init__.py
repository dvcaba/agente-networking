"""Tipos de agente — un handler por ``kind``, todos en un registro.

Importar este paquete registra los tipos integrados (efecto de import de cada módulo).
Para añadir un tipo nuevo (p. ej. ``graph`` para LangGraph): crea un módulo aquí que
llame a ``register_kind`` y añádelo a la lista de imports de abajo. El intérprete
``build.py`` no se toca.
"""

from __future__ import annotations

from .base import BuildContext, build_agent, known_kinds, register_kind

# Importar cada módulo registra su(s) tipo(s) en el registro.
from . import investigator, rag, simple, tool  # noqa: F401,E402  (efecto: registra)

__all__ = ["BuildContext", "build_agent", "known_kinds", "register_kind"]
