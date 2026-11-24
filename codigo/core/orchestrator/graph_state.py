"""Estado que viaja por el grafo de un workflow.

Un workflow se compila a un ``StateGraph`` de LangGraph; sus nodos (los pasos) leen y
escriben este estado. Acumula el contexto, las salidas de cada paso (para el fan-in) y
la traza. El reducer por defecto de LangGraph (sobrescribir por clave) basta porque la
traducción inicial encadena los pasos en orden de lista (sin ramas concurrentes).
"""

from __future__ import annotations

from typing import TypedDict

# Profundidad máxima de anidamiento de workflows (workflow que llama a workflow).
# Backstop ante recursión mal definida, además de la detección de ciclos exacta.
MAX_DEPTH = 12


class WFState(TypedDict, total=False):
    ctx: dict  # contexto acumulado (incluye los inputs iniciales y _wf_stack)
    outputs: dict  # ref-del-paso -> texto producido, para el fan-in ('from')
    prev_text: str  # texto del paso inmediatamente anterior (si no hay 'from')
    last: dict  # salida del último paso ejecutado
    trace: list  # [{agent, titulo, segundos, ok, texto?, claves?, fuentes?, error?}]
    error: str | None  # mensaje si algún paso falló (cortocircuita el resto)
    success: bool  # False si hubo fallo; ausente en el camino feliz
