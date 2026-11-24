from __future__ import annotations

from datetime import date
from typing import Callable

from nicegui import ui

from sistemas.networking.bridge.claude_bridge import ClaudeResponse, invoke_claude
from sistemas.networking.bridge.prompts import (
    prompt_comentario_post,
    prompt_continuar_conversacion,
    prompt_follow_up,
    prompt_primer_mensaje,
    prompt_reactivacion_dormant_tie,
)
from sistemas.networking.storage.contactos import (
    Contacto,
    ContactoNoEncontradoError,
    append_interaccion,
    get_contacto,
)
from sistemas.networking.ui.interaccion import open_interaccion_dialog


def _js_str(s: str) -> str:
    return (
        "`"
        + s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        + "`"
    )


def _copy_to_clipboard(text: str) -> None:
    ui.run_javascript(f"navigator.clipboard.writeText({_js_str(text)})")
    ui.notify("Copiado al portapapeles.", type="positive")


async def _open_redactor(
    c: Contacto,
    *,
    titulo_dialog: str,
    subtitulo_dialog: str,
    primer_prompt_builder: Callable[[Contacto], str],
    interaccion_titulo_default: str,
    primer_turno_mensaje: str,
) -> None:
    state: dict = {"session_id": None, "loading": False}

    with ui.dialog().props("persistent") as dialog, ui.card().classes(
        "w-[860px] max-w-[95vw] h-[88vh] flex flex-col p-0 gap-0"
    ):
        with ui.row().classes(
            "w-full items-center justify-between p-4 border-b border-gray-200"
        ):
            with ui.column().classes("gap-0"):
                ui.label(titulo_dialog).classes("text-lg font-semibold")
                ui.label(subtitulo_dialog).classes("text-xs text-gray-500")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")

        scroll = ui.scroll_area().classes("flex-1 w-full")
        with scroll:
            history = ui.column().classes("w-full p-4 gap-4")

        with ui.row().classes(
            "w-full items-end p-3 border-t border-gray-200 gap-2 bg-gray-50"
        ):
            input_field = (
                ui.textarea(placeholder="Pídele cambios concretos al mensaje...")
                .props("outlined dense autogrow")
                .classes("flex-1")
            )
            send_btn = ui.button("Enviar", icon="send").classes(
                "bg-blue-600 text-white"
            )

    def scroll_to_bottom() -> None:
        scroll.scroll_to(percent=1.0)

    def add_user_turn(text: str) -> None:
        with history:
            with ui.card().classes("w-full p-3 bg-blue-50 self-end max-w-[85%]"):
                ui.label("Tú").classes("text-xs text-gray-500 mb-1")
                ui.markdown(text).classes("text-sm")
        scroll_to_bottom()

    def add_assistant_turn(response: ClaudeResponse) -> None:
        with history:
            with ui.card().classes("w-full p-3 bg-white border border-gray-200"):
                meta = "Claude"
                if response.duration_ms:
                    meta += f" · {response.duration_ms / 1000:.1f}s"
                ui.label(meta).classes("text-xs text-gray-500 mb-1")
                ui.markdown(response.text).classes("text-sm leading-relaxed")
                with ui.row().classes("w-full justify-end mt-2 gap-1"):
                    ui.button(
                        "Marcar como enviado",
                        icon="send",
                        on_click=lambda t=response.text: open_interaccion_dialog(
                            c.slug,
                            default_titulo=interaccion_titulo_default,
                            default_contenido=t,
                        ),
                    ).props("flat dense")
                    ui.button(
                        "Copiar",
                        icon="content_copy",
                        on_click=lambda t=response.text: _copy_to_clipboard(t),
                    ).props("flat dense")
        scroll_to_bottom()

    def add_error(message: str) -> None:
        with history:
            with ui.card().classes(
                "w-full p-3 bg-red-50 border border-red-200 text-red-800 text-sm"
            ):
                ui.label("Error").classes("font-semibold mb-1")
                ui.label(message)
        scroll_to_bottom()

    async def run_turn(prompt: str, *, first: bool, timeout: int = 240) -> None:
        if state["loading"]:
            return
        state["loading"] = True
        send_btn.set_enabled(False)
        input_field.set_enabled(False)

        with history:
            loading_row = ui.row().classes("items-center gap-2 text-gray-500 text-sm")
            with loading_row:
                ui.spinner(size="sm")
                ui.label(primer_turno_mensaje if first else "Claude está pensando...")
        scroll_to_bottom()

        try:
            response = await invoke_claude(
                prompt,
                session_id=state["session_id"],
                timeout=timeout,
            )
        except Exception as e:
            loading_row.delete()
            add_error(str(e))
            state["loading"] = False
            send_btn.set_enabled(True)
            input_field.set_enabled(True)
            return

        loading_row.delete()

        if response.session_id:
            state["session_id"] = response.session_id

        if not response.success:
            add_error(response.error or "Respuesta vacía.")
        else:
            add_assistant_turn(response)

        state["loading"] = False
        send_btn.set_enabled(True)
        input_field.set_enabled(True)

    async def on_send() -> None:
        text = (input_field.value or "").strip()
        if not text or state["loading"]:
            return
        input_field.value = ""
        add_user_turn(text)
        await run_turn(text, first=False)

    send_btn.on_click(on_send)
    dialog.open()

    await run_turn(primer_prompt_builder(c), first=True)


async def open_redactor_primer_mensaje(c: Contacto) -> None:
    await _open_redactor(
        c,
        titulo_dialog=f"Redactar primer mensaje — {c.nombre}",
        subtitulo_dialog=(
            "Chat con Claude. Pídele cambios concretos hasta llegar al mensaje final."
        ),
        primer_prompt_builder=prompt_primer_mensaje,
        interaccion_titulo_default="Primer mensaje enviado",
        primer_turno_mensaje=(
            "Generando primer borrador con Opus 4.7 — primer turno tarda 20-60s."
        ),
    )


async def open_redactor_reactivacion(c: Contacto) -> None:
    await _open_redactor(
        c,
        titulo_dialog=f"Reactivar dormant tie — {c.nombre}",
        subtitulo_dialog=(
            "Mensaje de reactivación: reabrir la conversación con curiosidad genuina, "
            "sin pedir nada. PING primero, ASK después."
        ),
        primer_prompt_builder=prompt_reactivacion_dormant_tie,
        interaccion_titulo_default="Mensaje de reactivación enviado",
        primer_turno_mensaje=(
            "Generando mensaje de reactivación con Opus 4.7 — primer turno tarda 20-60s."
        ),
    )


async def open_redactor_follow_up(c: Contacto) -> None:
    await _open_redactor(
        c,
        titulo_dialog=f"Redactar follow-up — {c.nombre}",
        subtitulo_dialog=(
            "Claude detecta el tipo de follow-up viendo el histórico. "
            "Te avisará si toca dejar respirar."
        ),
        primer_prompt_builder=prompt_follow_up,
        interaccion_titulo_default="Follow-up enviado",
        primer_turno_mensaje=(
            "Leyendo el histórico y detectando tipo de follow-up con Opus 4.7 — 20-60s."
        ),
    )


def _parse_fecha(raw: str) -> date | None:
    raw = (raw or "").strip()
    parts = raw.split("-")
    if len(parts) != 3:
        return None
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError):
        return None


def open_redactor_comentario(c: Contacto) -> None:
    with ui.dialog().props("persistent") as dialog_post, ui.card().classes(
        "w-[640px] max-w-[92vw] p-6"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"Comentar post — {c.nombre}").classes("text-xl font-bold")
            ui.button(icon="close", on_click=dialog_post.close).props(
                "flat round dense"
            )
        ui.label(
            "Pega el texto del post de LinkedIn sobre el que quieres comentar. "
            "Yo no veo LinkedIn — necesito que me lo pegues."
        ).classes("text-sm text-gray-500")

        post_area = (
            ui.textarea(placeholder="Pega aquí el contenido del post...")
            .classes("w-full mt-2")
            .props("rows=12 autogrow")
        )

        async def on_generar() -> None:
            post_text = (post_area.value or "").strip()
            if not post_text:
                ui.notify("Pega el contenido del post primero.", type="negative")
                return
            dialog_post.close()
            await _open_redactor(
                c,
                titulo_dialog=f"Comentar post — {c.nombre}",
                subtitulo_dialog=(
                    "Comentario público: aportar perspectiva, sin pedir nada."
                ),
                primer_prompt_builder=lambda c: prompt_comentario_post(c, post_text),
                interaccion_titulo_default="Comenté su post",
                primer_turno_mensaje=(
                    "Generando comentarios con Opus 4.7 — primer turno tarda 20-60s."
                ),
            )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancelar", on_click=dialog_post.close).props("flat")
            ui.button(
                "Generar comentarios",
                icon="auto_awesome",
                on_click=on_generar,
            ).classes("bg-blue-600 text-white px-6 py-2 rounded")

    dialog_post.open()


def open_redactor_responder(c: Contacto) -> None:
    hoy_str = date.today().isoformat()

    with ui.dialog().props("persistent") as dialog_fase1, ui.card().classes(
        "w-[640px] max-w-[92vw] p-6"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"Continuar conversación — {c.nombre}").classes(
                "text-xl font-bold"
            )
            ui.button(icon="close", on_click=dialog_fase1.close).props(
                "flat round dense"
            )
        ui.label(
            "Pega la respuesta que te ha dado el contacto. Se registrará en el "
            "histórico antes de generar tu réplica."
        ).classes("text-sm text-gray-500")

        with ui.column().classes("w-full gap-3 mt-2"):
            respuesta_area = (
                ui.textarea(placeholder="Pega aquí la respuesta del contacto...")
                .classes("w-full")
                .props("rows=10 autogrow")
            )
            with ui.row().classes("w-full gap-3 items-center"):
                fecha_input = ui.input(
                    "Fecha de la respuesta (AAAA-MM-DD)", value=hoy_str
                ).classes("flex-1")

        async def on_generar() -> None:
            respuesta = (respuesta_area.value or "").strip()
            if not respuesta:
                ui.notify("Pega la respuesta del contacto primero.", type="negative")
                return
            fecha = _parse_fecha(fecha_input.value or "")
            if not fecha:
                ui.notify("Fecha inválida. Usa AAAA-MM-DD.", type="negative")
                return

            try:
                append_interaccion(c.slug, fecha, "Respondió", respuesta)
            except (ValueError, ContactoNoEncontradoError) as e:
                ui.notify(str(e), type="negative")
                return

            ui.notify("Respuesta registrada en el histórico.", type="positive")
            dialog_fase1.close()

            try:
                c_actualizado = get_contacto(c.slug)
            except ContactoNoEncontradoError as e:
                ui.notify(str(e), type="negative")
                return

            await _open_redactor(
                c_actualizado,
                titulo_dialog=f"Continuar conversación — {c.nombre}",
                subtitulo_dialog=(
                    "Claude tiene contexto del histórico completo + la respuesta "
                    "que acabas de pegar."
                ),
                primer_prompt_builder=prompt_continuar_conversacion,
                interaccion_titulo_default="Respondí",
                primer_turno_mensaje=(
                    "Leyendo histórico y respuesta con Opus 4.7 — 20-60s."
                ),
            )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancelar", on_click=dialog_fase1.close).props("flat")
            ui.button("Generar respuesta", icon="auto_awesome", on_click=on_generar).classes(
                "bg-blue-600 text-white px-6 py-2 rounded"
            )

    dialog_fase1.open()
