"""Intérprete: ficha (DomainBlueprint) -> lista de ``AgentSpec``.

Cada agente se construye según su ``kind`` con el handler registrado en
``agent_types`` (un módulo por tipo). Para añadir un tipo nuevo se registra allí, sin
tocar este intérprete. Los ``workflows`` se compilan en el ``orchestrator`` (LangGraph)
a un ``AgentSpec`` ejecutable.

``base_dir`` es la carpeta del dominio: ancla las rutas de conocimiento y el índice.
"""

from __future__ import annotations

from pathlib import Path

from core.engine.agent_base import AgentSpec
from core.orchestrator import workflow_agent

from ..agent_types import BuildContext, build_agent
from .model import AgentBlueprint, DomainBlueprint


def _path(domain: str, agent: AgentBlueprint) -> tuple[str, ...]:
    return tuple(agent.path) if agent.path else (domain,)


def build_domain(bp: DomainBlueprint, base_dir: Path) -> list[AgentSpec]:
    """Convierte una ficha de dominio en ``AgentSpec``. No registra (eso lo hace el loader)."""
    ctx = BuildContext.for_domain(bp, base_dir)
    specs: list[AgentSpec] = [
        build_agent(agent, _path(bp.domain, agent), ctx) for agent in bp.agents
    ]

    by_name = {a.name: s for a, s in zip(bp.agents, specs)}
    for wf in bp.workflows:
        specs.append(workflow_agent(bp.domain, wf, by_name))

    return specs
