"""El contrato de agente de la plataforma.

Un agente tiene una **ruta jerárquica** (`path`) + un nombre hoja (`name`), de
modo que su id es una ruta de namespace: ``marketing.contenido.news-scout``. Eso
permite un árbol de dominios → áreas → sub-áreas → agentes de cualquier
profundidad sin abstracciones rígidas: el CLI y el shell web derivan la
navegación de las rutas.

Tres formas de construir un agente:

- **Determinista / calculadora** (sin Claude): :func:`tool_agent` envuelve una
  función pura ``dict -> dict``. Para el Nivel 1 de finance (cono SIGMA, etc.).
- **Simple** (un turno LLM): :func:`simple_agent`. Para los flujos de networking.
- **De flujo** (varios pasos): construye un grafo LangGraph y expón su ``.invoke``
  como ``run`` (ver agentes de contenido).

Añadir un agente = crear su paquete, construir un AgentSpec y registrarlo con
``core.engine.registry.register``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Callable

from core.services import llm

# entrada (dict) -> salida (dict)
RunFn = Callable[[dict], dict]

# (entrada, out) -> emite trozos de texto; rellena ``out`` con session_id/sources/...
# Opcional: si un agente lo expone, la UI lo muestra token a token (streaming).
StreamFn = Callable[[dict, dict], AsyncIterator[str]]


@dataclass
class InputField:
    """Campo de entrada de un agente (para formularios del shell web / CLI)."""

    name: str  # clave en el dict de entrada
    label: str
    default: str = ""
    help: str = ""
    # origen del dato: 'manual' (lo teclea el usuario), 'agent' (lo aporta otro
    # agente en un workflow) o 'external' (viene de una app/API). El formulario web
    # solo muestra los 'manual'.
    source: str = "manual"


@dataclass
class AgentSpec:
    """Descriptor de un agente registrable, situado en el árbol de dominios."""

    path: tuple[str, ...]  # namespace, p.ej. ("marketing", "contenido")
    name: str  # hoja en kebab-case (slug interno/id), p.ej. "news-scout"
    description: str
    run: RunFn
    inputs: list[InputField] | None = None  # opcional: describe el formulario
    title: str | None = None  # nombre legible de cara al usuario (idioma del usuario)
    chat: bool = False  # True si la UI debe renderizarlo como conversación (multi-turno)
    starters: list[str] | None = None  # sugerencias de inicio para el chat
    stream: "StreamFn | None" = None  # opcional: respuesta token a token en el chat

    @property
    def id(self) -> str:
        """Ruta completa: 'marketing.contenido.news-scout'."""
        return ".".join((*self.path, self.name))

    @property
    def display_title(self) -> str:
        """Nombre legible para la UI. Si no hay ``title``, embellece el slug."""
        return self.title or self.name.replace("-", " ").replace("_", " ").capitalize()


def tool_agent(
    path: tuple[str, ...],
    name: str,
    description: str,
    fn: RunFn,
    *,
    inputs: list[InputField] | None = None,
    title: str | None = None,
) -> AgentSpec:
    """Agente determinista: una función pura ``dict -> dict``, sin Claude.

    Para calculadoras y herramientas con fórmula cerrada (Nivel 1 de finance).
    """
    return AgentSpec(
        path=path, name=name, description=description, run=fn, inputs=inputs, title=title
    )


def simple_agent(
    path: tuple[str, ...],
    name: str,
    description: str,
    build_prompt: Callable[[dict], str],
    *,
    system: str | None = None,
    model: str | None = None,
    inputs: list[InputField] | None = None,
    title: str | None = None,
    starters: list[str] | None = None,
) -> AgentSpec:
    """Agente LLM de un solo turno.

    ``build_prompt(entrada)`` produce el prompt. La salida es
    ``{"text", "success", "error", "session_id"}``.
    """

    def _run(entrada: dict) -> dict:
        prompt = build_prompt(entrada)
        kwargs = {"system": system, "session_id": entrada.get("session_id")}
        if model is not None:
            kwargs["model"] = model
        resp = llm.ask_sync(prompt, **kwargs)
        return {
            "text": resp.text,
            "success": resp.success,
            "error": resp.error,
            "session_id": resp.session_id,
        }

    async def _stream(entrada: dict, out: dict):
        prompt = build_prompt(entrada)
        kwargs = {"system": system, "session_id": entrada.get("session_id"), "out": out}
        if model is not None:
            kwargs["model"] = model
        async for chunk in llm.ask_stream(prompt, **kwargs):
            yield chunk

    return AgentSpec(
        path=path, name=name, description=description, run=_run, inputs=inputs, title=title,
        chat=True,  # un turno LLM que arrastra session_id -> conversacional
        starters=starters,
        stream=_stream,
    )
