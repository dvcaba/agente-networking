"""Orquestador — el MOTOR de flujos, sobre LangGraph. Común a todo.

Traduce cada ``workflow`` de una ficha a un grafo LangGraph y lo expone como un
``AgentSpec`` ejecutable (:func:`workflow_agent`). El motor es único; la definición de
cada flujo vive como datos en la ficha del dominio.

Distinción: aquí está la *maquinaria* (construir y ejecutar grafos); el *qué* (los pasos
de cada flujo) son datos del dominio.
"""

from __future__ import annotations

from .executor import workflow_agent
from .graph_builder import build_workflow_graph, resolve_step
from .graph_state import MAX_DEPTH, WFState

__all__ = ["workflow_agent", "build_workflow_graph", "resolve_step", "WFState", "MAX_DEPTH"]
