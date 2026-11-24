"""Tipo ``simple``: razona/redacta con el modelo en un turno, desde una plantilla."""

from __future__ import annotations

from core.engine.agent_base import AgentSpec, simple_agent

from ..blueprint.model import AgentBlueprint
from .base import BuildContext, build_code_ref, inputs_of, make_build_prompt, register_kind


@register_kind("simple")
def build_simple(agent: AgentBlueprint, path: tuple, ctx: BuildContext) -> AgentSpec:
    if agent.code_ref:  # conversacional, pero con el prompt hecho en código
        return build_code_ref(agent, path)
    return simple_agent(
        path,
        agent.name,
        agent.description,
        make_build_prompt(agent, ctx.bp.domain),
        system=agent.system,
        model=agent.model,
        inputs=inputs_of(agent),
        title=agent.title,
        starters=agent.starters,
    )
