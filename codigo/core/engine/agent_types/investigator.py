"""Tipo ``investigator``: investiga el estado del arte y escribe notas con fuentes.

En un sistema, escribe su nota en la biblioteca de ESE sistema (``investigacion/``) y la
reindexa. En una ficha antigua, en la carpeta ``research`` de su ``knowledge``.

El encargo (``brief``) puede completarse con contexto registrado (``context``), p. ej. tus
objetivos desde «Sobre mí»: el investigador de marketing los metía en su encargo, y sin
esto se perderían al pasar a una ficha declarativa.
"""

from __future__ import annotations

from core.engine.agent_base import AgentSpec
from core.services.knowledge_rag import investigator_agent

from ..blueprint.context import resolve_context
from ..blueprint.model import AgentBlueprint
from .base import BuildContext, register_kind, source_dirs


@register_kind("investigator")
def build_investigator(agent: AgentBlueprint, path: tuple, ctx: BuildContext) -> AgentSpec:
    # respeta el nombre de entrada que declaró la ficha (p. ej. 'asset', no 'topic')
    ficha_inputs = agent.inputs or []
    ikey = ficha_inputs[0]["name"] if ficha_inputs else "topic"
    ilabel = ficha_inputs[0].get("label", ikey) if ficha_inputs else "Tema a investigar"

    brief = agent.brief or ""
    extra = resolve_context(agent.context or [], ctx.bp.domain)
    if extra:
        brief = f"{brief}\n\n{extra}"

    if not ctx.heredado:
        from core import espacio  # tardío: las fichas antiguas no dependen del espacio

        sistema = ctx.sistema
        donde = {
            "knowledge_dir": espacio.write_dir(sistema, "investigacion"),
            "index_dir": espacio.index_dir(sistema),
            "collection": espacio.collection(sistema),
            "source_dirs": espacio.sources(sistema),
        }
    else:
        donde = {
            "knowledge_dir": next(
                (ctx.base_dir / s.dir for s in ctx.bp.knowledge.sources if s.kind == "research"),
                ctx.base_dir / "knowledge",
            ),
            "index_dir": ctx.index_dir,
            "collection": ctx.collection,
            "source_dirs": source_dirs(ctx, agent),
        }

    return investigator_agent(
        path=path,
        name=agent.name,
        title=agent.title,
        description=agent.description,
        brief=brief,
        input_key=ikey,
        input_label=ilabel,
        **donde,
        **({"model": agent.model} if agent.model else {}),
    )
