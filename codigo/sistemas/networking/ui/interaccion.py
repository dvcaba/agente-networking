from __future__ import annotations

from datetime import date
from typing import Callable

from nicegui import ui

from sistemas.networking.storage.contactos import (
    ContactoNoEncontradoError,
    append_interaccion,
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


def open_interaccion_dialog(
    slug: str,
    *,
    default_titulo: str = "",
    default_contenido: str = "",
    default_fecha: str | None = None,
    on_added: Callable[[], None] | None = None,
) -> None:
    fecha_str = default_fecha or date.today().isoformat()

    with ui.dialog().props("persistent") as dialog, ui.card().classes(
        "w-[600px] max-w-[92vw] p-6"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Añadir interacción").classes("text-xl font-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")

        ui.label(
            "Registra un evento en el histórico del contacto "
            "(mensaje enviado, respuesta recibida, café, etc.)."
        ).classes("text-sm text-gray-500")

        with ui.column().classes("w-full gap-3 mt-2"):
            fecha_input = ui.input(
                "Fecha (AAAA-MM-DD)", value=fecha_str
            ).classes("w-full")
            titulo_input = ui.input(
                "Título *",
                value=default_titulo,
                placeholder="Ej: Primer mensaje enviado",
            ).classes("w-full")
            contenido_area = (
                ui.textarea(
                    "Contenido / detalle (opcional)",
                    value=default_contenido,
                )
                .classes("w-full")
                .props("rows=8")
            )

        def on_submit() -> None:
            fecha = _parse_fecha(fecha_input.value or "")
            if not fecha:
                ui.notify(
                    "Fecha inválida. Usa formato AAAA-MM-DD.", type="negative"
                )
                return
            titulo = (titulo_input.value or "").strip()
            if not titulo:
                ui.notify("El título es obligatorio.", type="negative")
                return
            try:
                append_interaccion(
                    slug, fecha, titulo, contenido_area.value or ""
                )
            except (ValueError, ContactoNoEncontradoError) as e:
                ui.notify(str(e), type="negative")
                return
            ui.notify("Interacción añadida.", type="positive")
            dialog.close()
            if on_added:
                on_added()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancelar", on_click=dialog.close).props("flat")
            ui.button("Añadir", on_click=on_submit).classes(
                "bg-blue-600 text-white px-4 py-1 rounded"
            )

    dialog.open()
