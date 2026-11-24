"""Registro de tipos de agente: ``kind`` -> handler que lo construye.

Cada molde (``simple``, ``rag``, ``investigator``, ``tool``/``flow``) se construye con
un handler registrado aquí. **Añadir un tipo nuevo** (p. ej. ``graph`` para LangGraph)
es crear un módulo que llame a :func:`register_kind` — sin tocar el intérprete
(``build.py``). Esto saca el antiguo ``if kind == ...`` del motor.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.engine.agent_base import AgentSpec, InputField, tool_agent

from ..blueprint.context import resolve_context
from ..blueprint.model import AgentBlueprint, BlueprintError, DomainBlueprint

_INDEX_DIRNAME = ".rag_index"


@dataclass
class BuildContext:
    """Todo lo que un handler puede necesitar para construir un agente del dominio.

    Cada tipo toma de aquí lo que precise (el conocimiento, el índice, la colección…);
    los que no lo necesitan simplemente lo ignoran.
    """

    bp: DomainBlueprint
    base_dir: Path
    index_dir: Path
    collection: str
    #: Fichas antiguas con ``knowledge`` propio. Un sistema no las usa: lee de su biblioteca.
    heredado: bool = False

    @property
    def sistema(self) -> str:
        """De qué sistema se está construyendo. Su biblioteca y su identidad son las suyas."""
        return self.bp.domain

    @classmethod
    def for_domain(cls, bp: DomainBlueprint, base_dir: Path) -> "BuildContext":
        if bp.knowledge:  # ficha antigua: su conocimiento cuelga de su propia carpeta
            return cls(
                bp=bp, base_dir=base_dir, index_dir=base_dir / _INDEX_DIRNAME,
                collection=bp.knowledge.collection, heredado=True,
            )
        from core import espacio

        return cls(
            bp=bp,
            base_dir=base_dir,
            index_dir=espacio.index_dir(bp.domain),
            collection=espacio.collection(bp.domain),
        )


# kind -> función(agent, path, ctx) -> AgentSpec
Builder = Callable[[AgentBlueprint, tuple, BuildContext], AgentSpec]
_BUILDERS: dict[str, Builder] = {}


def register_kind(*kinds: str) -> Callable[[Builder], Builder]:
    """Decorador: registra un handler para uno o varios ``kind``."""

    def deco(fn: Builder) -> Builder:
        for k in kinds:
            _BUILDERS[k] = fn
        return fn

    return deco


def known_kinds() -> list[str]:
    return sorted(_BUILDERS)


def build_agent(agent: AgentBlueprint, path: tuple, ctx: BuildContext) -> AgentSpec:
    """Construye un agente buscando el handler de su ``kind`` en el registro."""
    builder = _BUILDERS.get(agent.kind)
    if builder is None:
        raise BlueprintError(
            f"[{agent.name}] tipo de agente desconocido: {agent.kind!r}. "
            f"Tipos disponibles: {', '.join(known_kinds())}."
        )
    return builder(agent, path, ctx)


# ---------------------------------------------------------------------------
# Helpers compartidos por los handlers
# ---------------------------------------------------------------------------


def inputs_of(agent: AgentBlueprint) -> list[InputField] | None:
    if not agent.inputs:
        return None
    return [
        InputField(
            name=f["name"],
            label=f.get("label", f["name"]),
            default=f.get("default", ""),
            help=f.get("help", ""),
            source=f.get("source", "manual"),
        )
        for f in agent.inputs
    ]


def source_dirs(ctx: BuildContext, agent: AgentBlueprint):
    """[(dir_absoluto, kind), ...] del conocimiento del dominio, filtrado si el agente acota."""
    fuentes = ctx.bp.knowledge.sources if ctx.bp.knowledge else []
    if agent.sources is not None:
        permitidos = set(agent.sources)
        fuentes = [s for s in fuentes if s.dir in permitidos]
    return [(ctx.base_dir / s.dir, s.kind) for s in fuentes]


def make_build_prompt(agent: AgentBlueprint, sistema: str = "") -> Callable[[dict], str]:
    """El prompt del agente, con el contexto que pida resuelto para SU sistema."""
    template = agent.prompt_template or ""
    ctx_keys = agent.context or []
    names = agent.input_names

    def build_prompt(entrada: dict) -> str:
        valores = {n: (entrada.get(n) or "") for n in names}
        cuerpo = template.format(**valores)
        ctx = resolve_context(ctx_keys, sistema)
        return f"{ctx}\n\n{cuerpo}" if ctx else cuerpo

    return build_prompt


def build_code_ref(agent: AgentBlueprint, path: tuple) -> AgentSpec:
    """Resuelve ``code_ref`` ('modulo:simbolo'). El símbolo es un AgentSpec o un RunFn (tool)."""
    mod_name, _, sym = agent.code_ref.partition(":")
    try:
        modulo = importlib.import_module(mod_name)
        simbolo = getattr(modulo, sym)
    except (ImportError, AttributeError) as e:
        raise BlueprintError(f"[{agent.name}] code_ref no resoluble '{agent.code_ref}': {e}")
    if isinstance(simbolo, AgentSpec):
        return simbolo
    if callable(simbolo):
        return tool_agent(
            path=path,
            name=agent.name,
            title=agent.title,
            description=agent.description,
            fn=simbolo,
            inputs=inputs_of(agent),
        )
    raise BlueprintError(
        f"[{agent.name}] code_ref '{agent.code_ref}' no es AgentSpec ni callable."
    )


def build_stub(agent: AgentBlueprint, path: tuple) -> AgentSpec:
    """Agente-placeholder para un molde de código aún SIN implementar.

    No falla: al ejecutarse explica que está pendiente de programador y muestra su
    contrato y requisitos, para que el dev sepa qué construir y luego enchufe el ``code_ref``.
    """
    contract = agent.contract or ""
    needs = list(agent.needs or [])

    def _run(_entrada: dict) -> dict:
        lineas = [
            f"⏳ **{agent.title}** está pendiente de implementación por un programador.",
            f"**Contrato:** {contract}",
        ]
        if needs:
            lineas.append("**Requiere:** " + "; ".join(needs))
        return {
            "success": True,
            "pending_developer": True,
            "text": "\n\n".join(lineas),
            "contract": contract,
            "needs": needs,
        }

    return AgentSpec(
        path=path,
        name=agent.name,
        title=agent.title,
        description=agent.description + " · ⏳ pendiente de programador",
        run=_run,
        inputs=inputs_of(agent),
    )
