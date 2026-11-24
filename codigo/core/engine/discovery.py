"""Descubrimiento: registra los especialistas y procesos de todos los sistemas.

Todo sale de ``sistemas/*/sistema.yaml`` (ver :mod:`core.systems`), incluidos los
especialistas hechos en código, que la ficha referencia con ``code_ref``. Las superficies
(CLI y web) solo llaman a :func:`load_all`.

El arquitecto («crear un sistema») no se registra por ahora: genera fichas en el formato
antiguo (``domains/<d>/domain.yaml``), y hasta que genere sistemas —fase 5 de
``docs/especificacion-producto.md``— registrarlo sería ofrecer algo que escribe donde ya
no hay nada.
"""

from __future__ import annotations


def load_all() -> list:
    """Registra todos los sistemas. Devuelve los sistemas cargados."""
    from core import systems

    return systems.load_all()
