from __future__ import annotations

from nicegui import ui

from sistemas.networking.storage.documentos import (
    Doc,
    biblioteca_por_grupo,
    estrategia_docs,
    read_doc,
    write_doc,
)
from sistemas.networking.ui.layout import header


def _ver_dialog(doc: Doc) -> None:
    try:
        contenido = read_doc(doc.relpath)
    except Exception as e:
        ui.notify(f"Error: {e}", type="negative")
        return
    with ui.dialog() as dialog, ui.card().classes(
        "w-[900px] max-w-[95vw] h-[88vh] flex flex-col p-4 gap-2"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(doc.titulo).classes("text-lg font-semibold")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")
        ui.label(f"data/{doc.relpath}").classes("text-xs text-gray-400")
        with ui.scroll_area().classes("flex-1 w-full"):
            ui.markdown(contenido).classes("text-sm")
    dialog.open()


def _editar_dialog(doc: Doc) -> None:
    try:
        contenido = read_doc(doc.relpath)
    except Exception as e:
        ui.notify(f"Error leyendo: {e}", type="negative")
        return
    with ui.dialog().props("persistent") as dialog, ui.card().classes(
        "w-[900px] max-w-[95vw] h-[88vh] flex flex-col p-4 gap-2"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"Editar — {doc.titulo}").classes("text-lg font-semibold")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")
        ui.label(f"data/{doc.relpath}").classes("text-xs text-gray-400")
        area = (
            ui.textarea(value=contenido)
            .classes("w-full flex-1")
            .props("outlined input-class=font-mono")
        )

        def guardar() -> None:
            try:
                write_doc(doc.relpath, area.value or "")
            except Exception as e:
                ui.notify(f"Error guardando: {e}", type="negative")
                return
            ui.notify(f"Guardado: data/{doc.relpath}", type="positive")
            dialog.close()
            ui.navigate.reload()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=dialog.close).props("flat")
            ui.button("Guardar", icon="save", on_click=guardar).classes(
                "bg-blue-600 text-white"
            )
    dialog.open()


def render_estrategia() -> None:
    header()
    with ui.column().classes("w-full max-w-4xl mx-auto p-8 gap-4"):
        ui.label("Estrategia").classes("text-2xl font-bold")
        ui.label(
            "Quién eres, qué buscas, tu pitch, tu estilo y tu plan. "
            "El agente lee esto para redactar y aconsejar."
        ).classes("text-sm text-gray-500")

        for doc in estrategia_docs():
            with ui.card().classes("w-full p-4"):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.column().classes("gap-0"):
                        ui.label(doc.titulo).classes("text-base font-semibold")
                        ui.label(f"data/{doc.relpath}").classes("text-xs text-gray-400")
                    with ui.row().classes("gap-1"):
                        ui.button(
                            "Ver", icon="visibility",
                            on_click=lambda d=doc: _ver_dialog(d),
                        ).props("flat dense")
                        ui.button(
                            "Editar", icon="edit",
                            on_click=lambda d=doc: _editar_dialog(d),
                        ).props("dense").classes("bg-blue-600 text-white")


def render_biblioteca() -> None:
    header()
    grupos = biblioteca_por_grupo()
    total = sum(len(v) for v in grupos.values())
    with ui.column().classes("w-full max-w-4xl mx-auto p-8 gap-4"):
        with ui.row().classes("w-full items-baseline gap-3"):
            ui.label("Biblioteca").classes("text-2xl font-bold")
            ui.label(f"{total} documentos").classes("text-sm text-gray-500")
        ui.label(
            "Knowledge base sourceada y plantillas. Solo lectura — se mantienen "
            "por conversación con el agente."
        ).classes("text-sm text-gray-500")

        if total == 0:
            ui.label("No hay documentos de consulta ni plantillas.").classes(
                "text-gray-500 italic"
            )
            return

        for grupo, docs in grupos.items():
            with ui.card().classes("w-full p-4"):
                ui.label(grupo).classes("text-sm font-semibold text-gray-800 mb-1")
                for d in docs:
                    ui.button(
                        d.titulo, icon="article",
                        on_click=lambda dd=d: _ver_dialog(dd),
                    ).props("flat dense no-caps").classes("w-full justify-start")
