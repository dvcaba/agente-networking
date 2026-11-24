"""Raíz del proyecto.

``core`` es framework puro: NO conoce rutas de dominio. Cada dominio/área calcula
sus propias rutas de datos/config desde ``Path(__file__).parent``.
"""

from __future__ import annotations

from pathlib import Path

# core/engine/paths.py -> core/engine/ -> core/ -> <ROOT>
# (parents[1] daba 'core/': quedó desfasado al mover el módulo dentro de 'engine').
ROOT: Path = Path(__file__).resolve().parents[2]
