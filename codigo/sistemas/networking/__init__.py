"""Sistema «Networking»: tus relaciones profesionales.

Es a la vez una app (pantallas NiceGUI en ``ui/``) y un conjunto de especialistas
declarados en ``sistema.yaml``. Aquí vive el que está hecho en código: el coach, cuyo
prompt arma ``bridge/prompts.py`` con tu perfil, objetivos, estilo y pendientes.

No se registra al importarse: lo registra el cargador de sistemas, porque la ficha lo
referencia (``code_ref: sistemas.networking:ASSISTANT``). El import de prompts es perezoso
para no arrastrar la app al cargar el sistema desde el CLI.
"""

from __future__ import annotations

from core.engine.agent_base import InputField, simple_agent


def _build_assistant_prompt(entrada: dict) -> str:
    pregunta = entrada.get("question") or entrada.get("text") or ""
    # Solo el primer turno carga el contexto completo (perfil/objetivos/estilo…);
    # en los siguientes basta el mensaje crudo, porque la sesión ya lo arrastra.
    if entrada.get("session_id"):
        return pregunta
    from sistemas.networking.bridge.prompts import prompt_asistente

    return prompt_asistente(pregunta)


ASSISTANT = simple_agent(
    ("networking",),
    "assistant",
    "Consulta libre sobre tu networking, con tu perfil, objetivos y estilo como contexto.",
    _build_assistant_prompt,
    model="claude-opus-4-8",
    title="Coach de networking",
    starters=[
        "¿Por quién empiezo a hacer networking?",
        "Ayúdame a escribir un primer mensaje",
        "¿Cómo reactivo un contacto con el que perdí el hilo?",
    ],
    inputs=[InputField("question", "Tu consulta", "", "Estrategia, a quién contactar, dudas…")],
)
