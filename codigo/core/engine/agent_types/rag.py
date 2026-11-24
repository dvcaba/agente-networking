"""Tipo ``rag``: responde con citas desde la biblioteca de SU sistema.

Cada sistema tiene la suya y solo lee de ahí (D7): si el conocimiento viviera fuera, desde
dentro del sistema no podrías saber qué está usando. Una sola colección, así que tampoco
hace falta fusionar resultados de varias — eso era del modelo de temas.

Las fichas antiguas, con ``knowledge`` propio, siguen construyéndose por su camino hasta que
se retiren.
"""

from __future__ import annotations

from core.engine.agent_base import AgentSpec
from core.services.knowledge_rag import rag_agent

from ..blueprint.model import AgentBlueprint
from .base import BuildContext, register_kind, source_dirs


@register_kind("rag")
def build_rag(agent: AgentBlueprint, path: tuple, ctx: BuildContext) -> AgentSpec:
    comunes = {
        "path": path,
        "name": agent.name,
        "title": agent.title,
        "description": agent.description,
        "top_k": agent.top_k,
        "model": agent.model,
        "starters": agent.starters,
    }
    if not ctx.heredado:
        sistema = ctx.sistema

        def _capas():
            # Se resuelven en cada consulta: añadir un documento o una carpeta de procedencia
            # no obliga a reiniciar.
            from core import espacio

            return espacio.layers(sistema)

        return rag_agent(**comunes, layers=_capas)

    return rag_agent(
        **comunes,
        index_dir=ctx.index_dir,
        collection=ctx.collection,
        source_dirs=source_dirs(ctx, agent),
    )
