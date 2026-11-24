"""Modelo de la ficha de agente (dirigido por datos) + validación.

Una ficha describe un agente o un dominio entero SIN código. El intérprete
(:mod:`core.engine.blueprint.build`) la convierte en ``AgentSpec`` reusando las
factorías de ``core.engine.agent_base`` / ``core.services.knowledge_rag``.

Aquí solo viven los datos y su validación; nada de Claude ni de I/O.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass, field

# slug seguro: minúsculas, empieza por letra; evita path traversal al escribir ficheros.
_SLUG = re.compile(r"^[a-z][a-z0-9_-]*$")

# Moldes soportados. Los tres primeros los genera el arquitecto (son datos);
# tool/flow referencian código que escribió un desarrollador (code_ref).
KINDS = {"simple", "rag", "investigator", "tool", "flow"}
_DATA_KINDS = {"simple", "rag", "investigator"}
_CODE_KINDS = {"tool", "flow"}
_KNOWLEDGE_KINDS = {"research", "downloaded"}
_INPUT_SOURCES = {"manual", "agent", "external"}


class BlueprintError(ValueError):
    """Ficha inválida. El mensaje es legible para enseñárselo al creador."""


@dataclass
class SourceSpec:
    dir: str
    kind: str  # "research" | "downloaded"


@dataclass
class KnowledgeSpec:
    collection: str
    sources: list[SourceSpec] = field(default_factory=list)


@dataclass
class AgentBlueprint:
    name: str
    title: str
    description: str
    kind: str
    path: list[str] | None = None
    model: str | None = None
    inputs: list[dict] | None = None
    # simple / rag
    system: str | None = None
    prompt_template: str | None = None
    context: list[str] | None = None
    starters: list[str] | None = None  # sugerencias de inicio del chat
    # rag
    top_k: int = 6
    sources: list[str] | None = None  # subconjunto de dirs del conocimiento del dominio
    # investigator
    brief: str | None = None
    # tool / flow
    code_ref: str | None = None       # 'modulo:simbolo' si ya está implementado
    contract: str | None = None       # qué hace / qué entra y sale (obligatorio en stubs)
    needs: list[str] | None = None    # requisitos externos: APIs, credenciales, datos de una app…

    @property
    def input_names(self) -> set[str]:
        return {f["name"] for f in (self.inputs or []) if "name" in f}

    @property
    def is_stub(self) -> bool:
        """True si es un molde de código aún SIN implementar (pendiente de programador)."""
        return self.kind in _CODE_KINDS and not self.code_ref


@dataclass
class WorkflowStep:
    """Un paso = una referencia a un EJECUTABLE (agente o workflow).

    ``ref`` es un nombre local (agente/workflow del propio dominio) o un id completo
    (``finance.compare-and-decide``) para apuntar a otra área. ``kind`` distingue si
    se referencia un agente o un workflow. La resolución real se hace en run time
    contra el registro (ver build).
    """

    ref: str                   # nombre local o id completo del ejecutable
    kind: str = "agent"        # "agent" | "workflow"
    from_: str | list | None = None  # ref(s) del/los paso(s) previo(s) que alimentan a este
                                     # (un str = cadena simple; una lista = fan-in)

    @property
    def agent(self) -> str:
        """Compat: código/diagrama que leían ``.agent`` (= la referencia del paso)."""
        return self.ref


@dataclass
class WorkflowSpec:
    name: str
    title: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)


@dataclass
class DomainBlueprint:
    domain: str
    label: str
    description: str = ""
    icon: str | None = None
    knowledge: KnowledgeSpec | None = None
    agents: list[AgentBlueprint] = field(default_factory=list)
    workflows: list[WorkflowSpec] = field(default_factory=list)
    # Temas de la biblioteca a los que se conecta un sistema. Sustituye a 'knowledge', que
    # era conocimiento encerrado en su dominio; se mantiene para las fichas antiguas.


# ----------------------------------------------------------------------- parseo
def _source_from(raw: dict) -> SourceSpec:
    return SourceSpec(dir=str(raw.get("dir", "")), kind=str(raw.get("kind", "")))


def domain_from_dict(data: dict) -> DomainBlueprint:
    """Construye (sin validar) un DomainBlueprint desde un dict (YAML/JSON cargado)."""
    if not isinstance(data, dict):
        raise BlueprintError("La ficha de dominio debe ser un mapa (dict).")

    knowledge = None
    kraw = data.get("knowledge")
    if isinstance(kraw, dict):
        knowledge = KnowledgeSpec(
            collection=str(kraw.get("collection", "")),
            sources=[_source_from(s) for s in (kraw.get("sources") or []) if isinstance(s, dict)],
        )

    agents: list[AgentBlueprint] = []
    for araw in data.get("agents") or []:
        if not isinstance(araw, dict):
            raise BlueprintError("Cada agente debe ser un mapa (dict).")
        agents.append(
            AgentBlueprint(
                name=str(araw.get("name", "")),
                title=str(araw.get("title", "")),
                description=str(araw.get("description", "")),
                kind=str(araw.get("kind", "")),
                path=list(araw["path"]) if araw.get("path") else None,
                model=araw.get("model"),
                inputs=araw.get("inputs"),
                system=araw.get("system"),
                prompt_template=araw.get("prompt_template"),
                context=araw.get("context"),
                starters=araw.get("starters"),
                top_k=int(araw.get("top_k", 6)),
                sources=araw.get("sources"),
                brief=araw.get("brief"),
                code_ref=araw.get("code_ref"),
                contract=araw.get("contract"),
                needs=araw.get("needs"),
            )
        )

    workflows: list[WorkflowSpec] = []
    for wraw in data.get("workflows") or []:
        if not isinstance(wraw, dict):
            raise BlueprintError("Cada workflow debe ser un mapa (dict).")
        steps = []
        for sraw in wraw.get("steps") or []:
            if not isinstance(sraw, dict):
                raise BlueprintError("Cada paso de workflow debe ser un mapa (dict).")
            # Un paso referencia un agente (agent:) o un workflow (workflow:).
            if sraw.get("workflow"):
                ref, kind = str(sraw["workflow"]), "workflow"
            else:
                ref, kind = str(sraw.get("agent", "")), "agent"
            steps.append(WorkflowStep(ref=ref, kind=kind, from_=sraw.get("from")))
        workflows.append(
            WorkflowSpec(
                name=str(wraw.get("name", "")),
                title=str(wraw.get("title", "")),
                description=str(wraw.get("description", "")),
                steps=steps,
            )
        )

    return DomainBlueprint(
        domain=str(data.get("domain", "")),
        label=str(data.get("label", "")),
        description=str(data.get("description", "")),
        icon=data.get("icon"),
        knowledge=knowledge,
        agents=agents,
        workflows=workflows,
    )


# -------------------------------------------------------------------- validación
def _template_fields(template: str) -> set[str]:
    """Placeholders nombrados de una plantilla ``str.format`` (sin posicionales)."""
    return {
        fname
        for _, fname, _, _ in string.Formatter().parse(template)
        if fname  # ignora texto literal entre placeholders
    }


def validate(bp: DomainBlueprint) -> None:
    """Valida la ficha de dominio. Lanza ``BlueprintError`` con mensaje legible."""
    if not bp.domain:
        raise BlueprintError("Falta 'domain' (slug del dominio).")
    if not _SLUG.match(bp.domain):
        raise BlueprintError(
            f"'domain' inválido: {bp.domain!r}. Usa minúsculas/guiones (ej. 'networking')."
        )
    if not bp.label:
        raise BlueprintError(f"El dominio '{bp.domain}' no tiene 'label' (nombre legible).")

    if bp.knowledge:
        if not bp.knowledge.collection:
            raise BlueprintError(f"[{bp.domain}] 'knowledge' sin 'collection'.")
        for s in bp.knowledge.sources:
            if not s.dir:
                raise BlueprintError(f"[{bp.domain}] una fuente de conocimiento sin 'dir'.")
            if s.kind not in _KNOWLEDGE_KINDS:
                raise BlueprintError(
                    f"[{bp.domain}] fuente '{s.dir}' con kind '{s.kind}'; "
                    f"debe ser uno de {sorted(_KNOWLEDGE_KINDS)}."
                )

    if not bp.agents:
        raise BlueprintError(f"El dominio '{bp.domain}' no declara agentes.")

    vistos: set[tuple] = set()
    for a in bp.agents:
        etq = f"[{bp.domain}.{a.name or '?'}]"
        if not a.name:
            raise BlueprintError(f"{etq} agente sin 'name'.")
        if not _SLUG.match(a.name):
            raise BlueprintError(f"{etq} 'name' inválido: {a.name!r}. Usa minúsculas/guiones.")
        for seg in a.path or []:
            if not _SLUG.match(seg):
                raise BlueprintError(f"{etq} segmento de 'path' inválido: {seg!r}.")
        if not a.title:
            raise BlueprintError(f"{etq} sin 'title' (nombre de cara al usuario).")
        if not a.description:
            raise BlueprintError(f"{etq} sin 'description'.")
        if a.kind not in KINDS:
            raise BlueprintError(f"{etq} kind '{a.kind}'; debe ser uno de {sorted(KINDS)}.")

        clave = (tuple(a.path) if a.path else (bp.domain,), a.name)
        if clave in vistos:
            raise BlueprintError(f"{etq} ruta duplicada: {'.'.join(clave[0])}.{a.name}.")
        vistos.add(clave)

        for f in a.inputs or []:
            src = f.get("source", "manual")
            if src not in _INPUT_SOURCES:
                raise BlueprintError(
                    f"{etq} input '{f.get('name')}' con source '{src}'; "
                    f"debe ser uno de {sorted(_INPUT_SOURCES)}."
                )

        if a.starters is not None and not (
            isinstance(a.starters, list) and all(isinstance(s, str) for s in a.starters)
        ):
            raise BlueprintError(f"{etq} 'starters' debe ser una lista de textos.")

        if a.code_ref and ":" not in a.code_ref:
            raise BlueprintError(f"{etq} 'code_ref' debe ir en formato 'modulo:simbolo'.")

        # Un especialista hecho en código (code_ref) declara el molde para decir cómo se
        # comporta —conversa, calcula, encadena pasos—, no para construirse desde la ficha.
        if a.kind == "simple" and a.code_ref:
            pass
        elif a.kind == "simple":
            if not a.prompt_template:
                raise BlueprintError(f"{etq} molde 'simple' requiere 'prompt_template'.")
            faltan = _template_fields(a.prompt_template) - a.input_names
            if faltan:
                raise BlueprintError(
                    f"{etq} 'prompt_template' usa placeholders no declarados en 'inputs': "
                    f"{sorted(faltan)}."
                )
        elif a.kind == "rag":
            # Un especialista de un sistema lee la biblioteca de SU sistema: no hay nada que
            # declarar ni que validar. Solo las fichas antiguas necesitan su 'knowledge'.
            pass
        elif a.kind == "investigator":
            if not a.brief:
                raise BlueprintError(f"{etq} molde 'investigator' requiere 'brief'.")
            if not bp.knowledge:
                pass  # en un sistema, escribe en su propia biblioteca
            elif not bp.knowledge or not any(
                s.kind == "research" for s in bp.knowledge.sources
            ):
                raise BlueprintError(
                    f"{etq} molde 'investigator' requiere una fuente 'research' en 'knowledge' "
                    "(dónde escribir las notas)."
                )
        elif a.kind in _CODE_KINDS and not a.code_ref and not a.contract:
            # stub sin implementar: vale, pero debe decir QUÉ debe hacer.
            raise BlueprintError(
                f"{etq} molde '{a.kind}' sin 'code_ref' es un stub pendiente de "
                "programador: requiere 'contract' (qué debe hacer, qué entra y sale)."
            )

    _validate_workflows(bp)


def _validate_workflows(bp: DomainBlueprint) -> None:
    nombres_agente = {a.name for a in bp.agents}
    nombres_wf = {w.name for w in bp.workflows}
    locales = nombres_agente | nombres_wf
    vistos_wf: set[str] = set()
    for w in bp.workflows:
        etq = f"[{bp.domain}.{w.name or '?'}]"
        if not w.name or not _SLUG.match(w.name):
            raise BlueprintError(f"{etq} workflow con 'name' inválido o ausente.")
        if not w.title:
            raise BlueprintError(f"{etq} workflow sin 'title'.")
        if w.name in nombres_agente:
            raise BlueprintError(f"{etq} el workflow colisiona con un agente del mismo nombre.")
        if w.name in vistos_wf:
            raise BlueprintError(f"{etq} workflow duplicado.")
        vistos_wf.add(w.name)
        if not w.steps:
            raise BlueprintError(f"{etq} workflow sin 'steps'.")
        if w.steps and w.steps[0].kind == "workflow" and not w.steps[0].from_:
            pass  # un workflow como primer paso recibe la entrada del usuario; ok
        previos: set[str] = set()
        for s in w.steps:
            if not s.ref:
                raise BlueprintError(f"{etq} un paso sin 'agent' ni 'workflow'.")
            # Referencia por id completo (contiene '.') → se resuelve en run time
            # (otros dominios pueden no estar cargados al validar). Si es un nombre
            # local (sin '.'), debe existir como agente o workflow del dominio.
            if "." not in s.ref and s.ref not in locales:
                tipo = "workflow" if s.kind == "workflow" else "agente"
                raise BlueprintError(
                    f"{etq} paso referencia un {tipo} local inexistente: {s.ref!r}."
                )
            # 'from' puede ser un str (cadena simple) o una lista (fan-in de varios pasos)
            if s.from_:
                froms = s.from_ if isinstance(s.from_, list) else [s.from_]
                for fr in froms:
                    if fr not in previos:
                        raise BlueprintError(
                            f"{etq} paso '{s.ref}' usa from='{fr}', que no es un paso previo."
                        )
            previos.add(s.ref)
