"""Cliente Claude único de la plataforma.

Usa `claude-agent-sdk`, que por debajo lanza el CLI de Claude Code y usa la
**suscripción** local — NO requiere ANTHROPIC_API_KEY. Funde lo que antes
estaban dos clientes distintos:

- ``creador_de_contenido/comun/claude.py``  (SDK, simple)
- ``agente-networking-suite/src/bridge/claude_bridge.py``  (subprocess: parseo
  JSON, timeout, session_id, errores, blindaje advisory-only)

Toda llamada a Claude de cualquier agente pasa por aquí.

Por defecto bloquea herramientas de escritura/ejecución (advisory-only): Claude
razona y redacta, pero NUNCA escribe archivos ni ejecuta comandos. Es el agente
quien decide qué persistir. Esto preserva la regla dura de networking.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

DEFAULT_MODEL = "claude-sonnet-4-6"

# Herramientas que NINGÚN agente puede usar por defecto: el agente (o la app) es
# el único que escribe archivos o ejecuta comandos. Claude solo razona y redacta.
BLOCKED_DEFAULT: list[str] = ["Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"]

_DEFAULT_TIMEOUT_S = 180

# Reintentos ante saturación del servidor (HTTP 529 / "overloaded"). No es un
# fallo del código ni del prompt: es temporal. Backoff creciente entre intentos.
_DEFAULT_RETRIES = 2
_BACKOFF_S = (2, 8)


def _es_overload(texto: str | None) -> bool:
    """True si el error indica saturación del servidor (reintentable)."""
    if not texto:
        return False
    t = texto.lower()
    return "529" in t or "overload" in t


def _es_timeout(texto: str | None) -> bool:
    """True si el error es un timeout (bajo saturación el servidor a veces no
    responde y cuelga: con ``retry_on_timeout`` lo tratamos como reintentable)."""
    return bool(texto) and "timeout" in texto.lower()


def _es_resultado_erroneo(texto: str | None) -> bool:
    """True si el CLI terminó con un resultado marcado como error, y es reintentable.

    El SDK convierte ``is_error=True`` del CLI en "Claude Code returned an error result:
    <subtipo>". Se ha visto llegar con subtipo ``success`` —contradictorio— y reintentar
    la misma llamada funciona a la primera: es transitorio. Sin esto, una ejecución larga
    del arquitecto se cae entera por un fallo de un segundo.

    ``error_max_turns`` se excluye a propósito: ahí el CLI agotó los turnos permitidos y
    repetir da exactamente el mismo resultado.
    """
    if not texto:
        return False
    t = texto.lower()
    return "returned an error result" in t and "max_turns" not in t


@dataclass
class Response:
    """Resultado de una llamada a Claude. Equivalente al antiguo ClaudeResponse."""

    text: str
    success: bool
    duration_ms: int = 0
    error: str | None = None
    session_id: str | None = None
    raw: dict = field(default_factory=dict)

    def __bool__(self) -> bool:  # permite `if respuesta:`
        return self.success


async def ask(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    session_id: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT_S,
    retries: int = _DEFAULT_RETRIES,
    retry_on_timeout: bool = False,
) -> Response:
    """Pregunta a Claude y devuelve una Response.

    - ``system``: system prompt adicional (solo en el primer turno de una sesión).
    - ``session_id``: si se pasa, continúa esa conversación (multi-turno).
    - ``disallowed_tools``: si es None, se aplica BLOCKED_DEFAULT (advisory-only).
      Pasa ``[]`` explícito para no bloquear nada.
    - ``retries``: reintentos extra ante saturación del servidor (529/overload).
    - ``retry_on_timeout``: si True, un timeout también reintenta (útil para llamadas
      pesadas donde el cuelgue suele ser saturación; usa un ``timeout`` por intento
      más corto para que los reintentos sean útiles y no esperas eternas).

    Ante un 529/overload (y, si ``retry_on_timeout``, un timeout) reintenta con
    backoff; el resto de errores se devuelven al primer intento.
    """
    ultima: Response | None = None
    for intento in range(retries + 1):
        ultima = await _ask_once(
            prompt,
            system=system,
            model=model,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            session_id=session_id,
            timeout=timeout,
        )
        reintentable = (
            _es_overload(ultima.error)
            or _es_resultado_erroneo(ultima.error)
            or (retry_on_timeout and _es_timeout(ultima.error))
        )
        if ultima.success or not reintentable:
            return ultima
        if intento < retries:
            await asyncio.sleep(_BACKOFF_S[min(intento, len(_BACKOFF_S) - 1)])
    # Agotados los reintentos: mensaje honesto (saturación / sin respuesta).
    return Response(
        text="",
        success=False,
        error=(
            "Claude no ha completado la llamada tras "
            f"{retries + 1} intentos (saturación, sin respuesta o resultado erróneo). "
            "Suele ser temporal: reintenta en un momento "
            "(estado: https://status.claude.com)."
        ),
    )


async def _ask_once(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    session_id: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT_S,
) -> Response:
    """Un único intento de llamada a Claude (sin reintentos)."""
    bloqueadas = BLOCKED_DEFAULT if disallowed_tools is None else disallowed_tools

    opciones = ClaudeAgentOptions(
        model=model,
        # En continuación de sesión no se reinyecta el system prompt.
        system_prompt=system if not session_id else None,
        allowed_tools=allowed_tools or [],
        disallowed_tools=bloqueadas,
        resume=session_id,
    )

    partes: list[str] = []
    resultado: ResultMessage | None = None

    async def _consumir() -> None:
        nonlocal resultado
        async for mensaje in query(prompt=prompt, options=opciones):
            if isinstance(mensaje, AssistantMessage):
                for bloque in mensaje.content:
                    if isinstance(bloque, TextBlock):
                        partes.append(bloque.text)
            elif isinstance(mensaje, ResultMessage):
                resultado = mensaje

    try:
        await asyncio.wait_for(_consumir(), timeout=timeout)
    except asyncio.TimeoutError:
        return Response(
            text="",
            success=False,
            error=(
                f"Timeout tras {timeout}s (el servidor puede estar saturado; "
                "si se repite, reintenta en un momento)."
            ),
        )
    except Exception as e:  # noqa: BLE001 — superficie de error uniforme para los agentes
        return Response(text="", success=False, error=f"{type(e).__name__}: {e}")

    texto = "".join(partes)

    if resultado is not None and resultado.is_error:
        return Response(
            text=texto,
            success=False,
            duration_ms=int(getattr(resultado, "duration_ms", 0) or 0),
            error=str(getattr(resultado, "result", None) or "Error de Claude"),
            session_id=getattr(resultado, "session_id", None),
        )

    return Response(
        text=texto or (getattr(resultado, "result", "") if resultado else ""),
        success=True,
        duration_ms=int(getattr(resultado, "duration_ms", 0) or 0) if resultado else 0,
        session_id=getattr(resultado, "session_id", None) if resultado else None,
    )


def ask_sync(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    session_id: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT_S,
    retries: int = _DEFAULT_RETRIES,
    retry_on_timeout: bool = False,
) -> Response:
    """Versión síncrona de :func:`ask` (envuelve asyncio.run)."""
    return asyncio.run(
        ask(
            prompt,
            system=system,
            model=model,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            session_id=session_id,
            timeout=timeout,
            retries=retries,
            retry_on_timeout=retry_on_timeout,
        )
    )


async def ask_stream(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    session_id: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT_S,
    out: dict | None = None,
) -> AsyncIterator[str]:
    """Pregunta a Claude EMITIENDO la respuesta por trozos (para chat token a token).

    Rellena ``out`` (si se pasa) con ``{session_id, success, error}`` al terminar.
    Mantiene el blindaje advisory-only. ``timeout`` es de inactividad entre trozos.
    """
    meta = out if out is not None else {}
    opciones = ClaudeAgentOptions(
        model=model,
        system_prompt=system if not session_id else None,
        allowed_tools=[],
        disallowed_tools=BLOCKED_DEFAULT,
        resume=session_id,
    )
    resultado: ResultMessage | None = None

    async def _gen():
        nonlocal resultado
        async for mensaje in query(prompt=prompt, options=opciones):
            if isinstance(mensaje, AssistantMessage):
                for bloque in mensaje.content:
                    if isinstance(bloque, TextBlock):
                        yield bloque.text
            elif isinstance(mensaje, ResultMessage):
                resultado = mensaje

    agen = _gen()
    try:
        while True:
            try:
                chunk = await asyncio.wait_for(agen.__anext__(), timeout=timeout)
            except StopAsyncIteration:
                break
            yield chunk
    except asyncio.TimeoutError:
        meta.update(success=False, error=f"Timeout tras {timeout}s (el servidor puede estar saturado).")
        return
    except Exception as e:  # noqa: BLE001 — superficie de error uniforme
        meta.update(success=False, error=f"{type(e).__name__}: {e}")
        return
    finally:
        await agen.aclose()

    if resultado is not None and getattr(resultado, "is_error", False):
        meta.update(
            success=False,
            error=str(getattr(resultado, "result", None) or "Error de Claude"),
            session_id=getattr(resultado, "session_id", None),
        )
    else:
        meta.update(
            success=True,
            session_id=getattr(resultado, "session_id", None) if resultado else None,
        )
