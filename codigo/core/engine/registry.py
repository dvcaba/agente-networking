"""Registro de especialistas y procesos.

Se indexan por su id, ``<sistema>.<nombre>`` (``inversion.sigma-cone``). Lo llena
``core.engine.discovery.load_all`` a partir de las fichas de ``sistemas/``; el CLI y la web
lo consultan.
"""

from __future__ import annotations

from collections import OrderedDict

from core.engine.agent_base import AgentSpec

_REGISTRY: dict[str, AgentSpec] = {}


def register(spec: AgentSpec) -> AgentSpec:
    """Registra un agente por su id de ruta. Idempotente (el último gana)."""
    _REGISTRY[spec.id] = spec
    return spec


def all_agents() -> list[AgentSpec]:
    return sorted(_REGISTRY.values(), key=lambda s: s.id)


def get(ref: str) -> AgentSpec:
    """Resuelve por id completo o por sufijo de hoja único.

    'contenido.news-scout' o 'news-scout' (si no es ambiguo).
    """
    if ref in _REGISTRY:
        return _REGISTRY[ref]
    matches = [s for s in _REGISTRY.values() if s.name == ref or s.id.endswith("." + ref)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        disponibles = ", ".join(sorted(_REGISTRY)) or "(ninguno)"
        raise KeyError(f"Agente desconocido: {ref!r}. Disponibles: {disponibles}")
    ambiguos = ", ".join(sorted(s.id for s in matches))
    raise KeyError(f"Referencia ambigua {ref!r}; coincide con: {ambiguos}")


def unregister(ref: str) -> bool:
    """Da de baja una pieza por su id exacto. Devuelve si estaba."""
    return _REGISTRY.pop(ref, None) is not None


def unregister_system(slug: str) -> list[str]:
    """Da de baja todas las piezas de un sistema. Devuelve las que se han quitado.

    Hace falta al renombrar o al apartar un sistema: si no, sus piezas siguen resolviéndose
    —y ejecutándose— contra una carpeta que ya no existe o que ahora se llama de otra
    forma. Es el mismo fallo que teníamos con los especialistas colgando de rutas viejas,
    pero en memoria, que además no se ve al mirar el disco.
    """
    fuera = [i for i in _REGISTRY if i.split(".")[0] == slug]
    for i in fuera:
        del _REGISTRY[i]
    return sorted(fuera)


def grouped_by_prefix() -> OrderedDict[str, list[AgentSpec]]:
    """Agrupa los agentes por su ruta de namespace (para CLI / nav).

    Clave = 'inversion'; valor = los especialistas y procesos de ese sistema.
    """
    grupos: OrderedDict[str, list[AgentSpec]] = OrderedDict()
    for spec in all_agents():
        grupos.setdefault(".".join(spec.path), []).append(spec)
    return grupos
