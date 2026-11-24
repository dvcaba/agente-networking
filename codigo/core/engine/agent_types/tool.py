"""Tipos ``tool`` / ``flow``: código que escribió un dev (una *tool* en ``tools/``).

Si la ficha trae ``code_ref``, se resuelve al código real; si no, queda como STUB
(pendiente de programador) que explica su contrato al ejecutarse.
"""

from __future__ import annotations

from core.engine.agent_base import AgentSpec

from ..blueprint.model import AgentBlueprint
from .base import BuildContext, build_code_ref, build_stub, register_kind


@register_kind("tool", "flow")
def build_tool(agent: AgentBlueprint, path: tuple, ctx: BuildContext) -> AgentSpec:
    return build_code_ref(agent, path) if agent.code_ref else build_stub(agent, path)
