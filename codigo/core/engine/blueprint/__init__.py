"""Intérprete de fichas: convierte una ficha en especialistas ejecutables.

Aquí solo se interpreta; quién lee los ficheros y los registra es :mod:`core.systems`.
Tener dos formas de cargar una ficha —una por sistema y otra por fichero suelto— es de
donde salían los agentes colgando de sitios que ya no existían.

- ``domain_from_dict`` + ``validate``  : leer y validar la ficha.
- ``build_domain``                     : construir sus ``AgentSpec`` (sin registrar).
- ``register_context`` / ``resolve_context`` : contexto con nombre para las fichas ``simple``.
"""

from __future__ import annotations

from .build import build_domain
from .context import register_context, resolve_context
from .model import BlueprintError, DomainBlueprint, domain_from_dict, validate

__all__ = [
    "BlueprintError",
    "DomainBlueprint",
    "build_domain",
    "domain_from_dict",
    "register_context",
    "resolve_context",
    "validate",
]
