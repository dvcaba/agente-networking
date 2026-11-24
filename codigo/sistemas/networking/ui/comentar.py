from __future__ import annotations

from nicegui import ui

from sistemas.networking.bridge.claude_bridge import ClaudeResponse, invoke_claude
from sistemas.networking.bridge.prompts import prompt_comentario_post_standalone
from sistemas.networking.ui.layout import header


def _js_str(s: str) -> str:
    return "`" + s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$") + "`"


def render_comentar() -> None:
    header()
    state: dict = {"session_id": None, "loading": False}

    with ui.column().classes("w-full max-w-3xl mx-auto p-8 gap-3"):
        ui.label("Comentar un post").classes("text-2xl font-bold")
        ui.label(
            "Pega un post de LinkedIn y te genero comentarios para aportar perspectiva "
            "(sin pedir nada). No hace falta que la persona sea contacto."
        ).classes("text-sm text-gray-500")

        post_area = (
            ui.textarea(placeholder="Pega aquí el contenido del post...")
            .props("outlined autogrow rows=10")
            .classes("w-full")
        )
        autor_input = ui.input("Quién lo publica / contexto (opcional)").classes("w-full")
        gen_btn = ui.button("Generar comentarios", icon="auto_awesome").classes(
            "bg-blue-600 text-white"
        )
        results = ui.column().classes("w-full gap-3")

    def _copy(text: str) -> None:
        ui.run_javascript(f"navigator.clipboard.writeText({_js_str(text)})")
        ui.notify("Copiado al portapapeles.", type="positive")

    def add_result(response: ClaudeResponse) -> None:
        with results:
            with ui.card().classes("w-full p-3 bg-white border border-gray-200"):
                meta = "Claude"
                if response.duration_ms:
                    meta += f" · {response.duration_ms / 1000:.1f}s"
                ui.label(meta).classes("text-xs text-gray-500 mb-1")
                ui.markdown(response.text).classes("text-sm leading-relaxed")
                ui.button(
                    "Copiar todo", icon="content_copy",
                    on_click=lambda t=response.text: _copy(t),
                ).props("flat dense")

    async def run(prompt: str) -> None:
        if state["loading"]:
            return
        state["loading"] = True
        gen_btn.set_enabled(False)
        with results:
            loading = ui.row().classes("items-center gap-2 text-gray-500 text-sm")
            with loading:
                ui.spinner(size="sm")
                ui.label("Generando comentarios — 20-60s.")
        try:
            response = await invoke_claude(prompt, session_id=state["session_id"], timeout=240)
        except Exception as e:
            loading.delete()
            ui.notify(str(e), type="negative")
            state["loading"] = False
            gen_btn.set_enabled(True)
            return
        loading.delete()
        if response.session_id:
            state["session_id"] = response.session_id
        if not response.success:
            ui.notify(response.error or "Respuesta vacía.", type="negative")
        else:
            add_result(response)
        state["loading"] = False
        gen_btn.set_enabled(True)

    async def on_generar() -> None:
        post = (post_area.value or "").strip()
        if not post:
            ui.notify("Pega el contenido del post primero.", type="negative")
            return
        state["session_id"] = None  # cada generación arranca limpia
        results.clear()
        await run(prompt_comentario_post_standalone(post, autor_input.value or ""))

    gen_btn.on_click(on_generar)
