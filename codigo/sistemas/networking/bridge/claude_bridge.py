"""Puente a Claude para la app de networking.

Antes hablaba con el CLI de Claude por subprocess. Ahora delega en el cliente
único de la plataforma (``core.services.llm``), manteniendo la MISMA firma pública
(``ClaudeResponse`` + ``invoke_claude``) para que la UI no cambie.

Sigue siendo advisory-only: Claude razona y redacta, nunca escribe archivos —
la app es la única que persiste (lo garantiza ``core.services.llm`` por defecto).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.services import llm

# La app de networking razona con el modelo más capaz por defecto.
_DEFAULT_MODEL = "claude-opus-4-8"
_DEFAULT_TIMEOUT_S = 180


@dataclass
class ClaudeResponse:
    text: str
    success: bool
    duration_ms: int = 0
    error: str | None = None
    session_id: str | None = None
    raw: dict | None = None


async def invoke_claude(
    prompt: str,
    *,
    session_id: str | None = None,
    system_prompt: str | None = None,
    model: str = _DEFAULT_MODEL,
    timeout: int = _DEFAULT_TIMEOUT_S,
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
) -> ClaudeResponse:
    """Pregunta a Claude vía el cliente de la plataforma.

    Firma idéntica a la versión subprocess anterior. Por defecto bloquea
    herramientas de escritura/ejecución (lo aplica ``core.services.llm``).
    """
    resp = await llm.ask(
        prompt,
        system=system_prompt,
        model=model,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
        session_id=session_id,
        timeout=timeout,
    )
    return ClaudeResponse(
        text=resp.text,
        success=resp.success,
        duration_ms=resp.duration_ms,
        error=resp.error,
        session_id=resp.session_id,
        raw=resp.raw,
    )
