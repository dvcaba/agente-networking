"""Envuelve un workflow compilado en un ``AgentSpec`` ejecutable.

El ``AgentSpec`` resultante se comporta como un agente más: al ejecutarse, prepara el
estado inicial (con las guardas de ciclo y profundidad), invoca el grafo LangGraph y
extrae el resultado en el formato que espera el resto de la plataforma:
``{**salida-del-último-paso, success, steps}`` (o ``{success: False, error, steps}``).
"""

from __future__ import annotations

from core.engine.agent_base import AgentSpec, InputField

from .graph_builder import build_workflow_graph, resolve_step
from .graph_state import MAX_DEPTH


def _workflow_inputs(domain: str, wf, by_name: dict) -> list[InputField]:
    """Inputs del workflow = inputs MANUALES de sus pasos (en orden, sin duplicar), para
    que la UI muestre campos de verdad. Best-effort: lo que no resuelva ahora (p. ej. un
    workflow aún no registrado) simplemente no se pre-lista."""
    wf_inputs: list[InputField] = []
    vistos: set[str] = set()
    for s in wf.steps:
        sp = resolve_step(s.ref, s.kind, domain, by_name)
        for f in (sp.inputs if sp else None) or []:
            if getattr(f, "source", "manual") == "manual" and f.name not in vistos:
                vistos.add(f.name)
                wf_inputs.append(f)
    return wf_inputs


def workflow_agent(domain: str, wf, by_name: dict) -> AgentSpec:
    """Compila un workflow a un ``AgentSpec`` cuyo ``run`` ejecuta el grafo LangGraph."""
    graph = build_workflow_graph(domain, wf.steps, by_name)
    wf_id = ".".join((domain, wf.name))
    refs = [s.ref for s in wf.steps]
    wf_inputs = _workflow_inputs(domain, wf, by_name)

    def _run(entrada: dict) -> dict:
        # --- guardas: ciclos y profundidad (workflow que llama a workflow) ---
        stack = tuple(entrada.get("_wf_stack") or ())
        if wf_id in stack:
            cadena = " → ".join((*stack, wf_id))
            return {"success": False, "error": f"Ciclo de workflows detectado: {cadena}"}
        if len(stack) >= MAX_DEPTH:
            return {"success": False,
                    "error": f"Profundidad máxima de workflows excedida ({MAX_DEPTH})."}

        ctx0 = dict(entrada)
        ctx0["_wf_stack"] = (*stack, wf_id)  # se propaga a sub-workflows en sus pasos
        init = {"ctx": ctx0, "outputs": {}, "prev_text": "", "last": {}, "trace": []}
        # límite de supersteps: lineal = nº de pasos; holgura para sub-workflows.
        config = {"recursion_limit": max(25, len(wf.steps) * 2 + 5)}
        final = graph.invoke(init, config=config)

        trace = final.get("trace") or []
        if final.get("success") is False:
            return {"success": False, "error": final.get("error"), "steps": trace}
        # no fugar la pila interna hacia fuera
        ultimo = {k: v for k, v in (final.get("last") or {}).items() if k != "_wf_stack"}
        return {**ultimo, "success": True, "steps": trace}

    return AgentSpec(
        path=(domain,),
        name=wf.name,
        title=wf.title,
        description=wf.description or f"Workflow: {' → '.join(refs)}",
        run=_run,
        inputs=wf_inputs or None,
    )
