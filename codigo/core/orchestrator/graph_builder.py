"""Construye el grafo LangGraph de un workflow (o de un paso suelto).

Traducción inicial fiel al intérprete anterior: los pasos se encadenan en **orden de
lista** (START → paso0 → paso1 → … → END) y el fan-in (``from``) se resuelve a nivel de
datos (cada nodo lee del estado las salidas de los pasos indicados). El orden de lista
garantiza que los pasos previos ya corrieron, así que no hacen falta aristas extra para
el fan-in. Las ramas/bucles condicionales llegarán después como aristas condicionales,
ya sobre este mismo motor.
"""

from __future__ import annotations

import time

from langgraph.graph import END, START, StateGraph

from .graph_state import WFState


def resolve_step(ref: str, kind: str, domain: str, by_name: dict):
    """Resuelve la referencia de un paso a un ``AgentSpec`` (agente o workflow).

    Orden: agente local por nombre (rápido) → id completo en el registro → id local
    ``domain.ref`` en el registro. Devuelve ``None`` si no resuelve.
    """
    from core.engine import registry  # lazy: evita cualquier ciclo de import al cargar

    if kind == "agent" and "." not in ref and ref in by_name:
        return by_name[ref]
    candidatos = [ref] if "." in ref else [f"{domain}.{ref}", ref]
    for cand in candidatos:
        try:
            return registry.get(cand)
        except KeyError:
            continue
    return None


def _incoming(frm, outputs: dict, prev_text: str) -> str:
    """Texto entrante a un paso: si declara 'from', une las salidas de esos pasos
    (fan-in); si no, la del paso inmediatamente anterior."""
    if frm:
        refs = frm if isinstance(frm, list) else [frm]
        return "\n\n".join(outputs.get(r, "") for r in refs).strip() or prev_text
    return prev_text


#: Cuánto texto de cada paso se guarda en el rastro. Es para que puedas ver qué produjo,
#: no para llevarte la salida entera: el rastro viaja dentro del estado del grafo.
_RESUMEN = 400


def _resumir(out) -> dict:
    """Qué se guarda de lo que produjo un paso.

    Antes el rastro solo decía si el paso fue bien. Con eso no se puede auditar nada: para
    saber si una investigación es fiable hay que poder ver qué sacó cada especialista, no
    solo que no reventó.
    """
    if not isinstance(out, dict):
        return {"texto": str(out)[:_RESUMEN]}
    datos = {k: v for k, v in out.items() if k not in _INTERNAS}
    resumen = {"claves": sorted(datos)} if datos else {}
    if out.get("text"):
        resumen["texto"] = str(out["text"])[:_RESUMEN]
    if out.get("sources"):
        resumen["fuentes"] = len(out["sources"])
    return resumen


#: Claves de servicio: no son «lo que produjo el paso».
_INTERNAS = {"text", "success", "error", "session_id", "sources", "steps", "_wf_stack"}


def _make_node(step, domain: str, by_name: dict):
    """Crea la función-nodo de un paso del workflow."""
    ref, kind, frm = step.ref, step.kind, step.from_

    def node(state: WFState) -> dict:
        if state.get("error"):  # un paso previo ya falló: cortocircuita
            return {}

        ctx = dict(state.get("ctx") or {})
        outputs = dict(state.get("outputs") or {})
        prev_text = state.get("prev_text") or ""
        trace = list(state.get("trace") or [])
        last = state.get("last") or {}

        spec = resolve_step(ref, kind, domain, by_name)
        if spec is None:
            return {"trace": trace, "error": f"Paso no resoluble: {ref!r} (kind={kind}).",
                    "success": False}

        entrante = _incoming(frm, outputs, prev_text)
        paso_ctx = dict(ctx)
        # rellena las entradas 'source: agent' con el texto entrante
        for f in spec.inputs or []:
            if getattr(f, "source", "manual") == "agent" and not paso_ctx.get(f.name):
                paso_ctx[f.name] = entrante

        t0 = time.perf_counter()
        out = spec.run(paso_ctx)
        segundos = round(time.perf_counter() - t0, 1)
        marca = {"agent": ref, "titulo": spec.display_title, "segundos": segundos}
        if isinstance(out, dict):
            ctx = {**ctx, **out}
            last = out
            if out.get("text"):
                prev_text = out["text"]
                outputs[ref] = out["text"]
            if out.get("success") is False:
                return {"ctx": ctx, "outputs": outputs, "prev_text": prev_text, "last": last,
                        "trace": trace + [{**marca, "ok": False,
                                           "error": out.get("error"), **_resumir(out)}],
                        "error": f"Paso '{ref}' falló: {out.get('error')}", "success": False}

        ok = isinstance(out, dict) and out.get("success") is not False
        return {"ctx": ctx, "outputs": outputs, "prev_text": prev_text, "last": last,
                "trace": trace + [{**marca, "ok": ok, **_resumir(out)}]}

    return node


def build_workflow_graph(domain: str, steps, by_name: dict):
    """Compila los pasos de un workflow a un grafo LangGraph encadenado en orden."""
    g = StateGraph(WFState)
    prev = START
    for i, step in enumerate(steps):
        node_name = f"s{i}"
        g.add_node(node_name, _make_node(step, domain, by_name))
        g.add_edge(prev, node_name)
        prev = node_name
    g.add_edge(prev, END)  # si no hay pasos: START → END
    return g.compile()
