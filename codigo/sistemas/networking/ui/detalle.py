from __future__ import annotations

from datetime import date

from nicegui import ui

from sistemas.networking.storage.contactos import (
    Contacto,
    ContactoNoEncontradoError,
    TIER_LABELS,
    borrar_contacto,
    esta_incompleto,
    get_contacto,
    set_archivado,
)
from sistemas.networking.ui.editar import open_editar_dialog
from sistemas.networking.ui.interaccion import open_interaccion_dialog
from sistemas.networking.ui.layout import header
from sistemas.networking.ui.redactor import (
    open_redactor_comentario,
    open_redactor_follow_up,
    open_redactor_primer_mensaje,
    open_redactor_reactivacion,
    open_redactor_responder,
)

_LABEL_TEMPERATURA: dict[str, str] = {
    "caliente": "Caliente",
    "tibio": "Tibio",
    "frío": "Frío",
    "desconocido": "Sin estado",
}

_COLOR_TEMPERATURA: dict[str, str] = {
    "caliente": "bg-red-100 text-red-800",
    "tibio": "bg-amber-100 text-amber-800",
    "frío": "bg-blue-100 text-blue-800",
    "desconocido": "bg-gray-100 text-gray-700",
}


def _format_date(d: date | None) -> str:
    return d.isoformat() if d else "—"


def _data_row(label: str, value: str | None) -> None:
    if not value:
        return
    with ui.row().classes("w-full gap-2 items-baseline"):
        ui.label(label).classes(
            "text-xs uppercase text-gray-500 w-48 flex-shrink-0 mt-1"
        )
        ui.label(value).classes("text-sm text-gray-800 flex-1")


def _historico_render(historico_raw: str) -> None:
    if not historico_raw.strip():
        ui.label("Sin histórico registrado.").classes("text-sm text-gray-500 italic")
        return
    ui.markdown(historico_raw).classes("text-sm")


def _confirm_borrar(c: Contacto) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Borrar contacto").classes("text-lg font-semibold")
        ui.label(
            f"Vas a borrar a '{c.nombre}' y todo su histórico. "
            "Esta acción no se puede deshacer."
        ).classes("text-sm text-gray-600")
        ui.label(
            "Si solo quieres dejarlo inactivo, usa Archivar (conserva el histórico)."
        ).classes("text-xs text-gray-500 mt-1")

        def do_borrar() -> None:
            try:
                borrar_contacto(c.slug)
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")
                return
            ui.notify(f"Contacto '{c.nombre}' borrado.", type="positive")
            dialog.close()
            ui.navigate.to("/networking")

        with ui.row().classes("w-full justify-end gap-2 mt-3"):
            ui.button("Cancelar", on_click=dialog.close).props("flat")
            ui.button("Borrar", on_click=do_borrar).classes(
                "bg-red-600 text-white px-4 py-1 rounded"
            )
    dialog.open()


def _toggle_archivado(c: Contacto) -> None:
    try:
        set_archivado(c.slug, not c.archivado)
    except Exception as e:
        ui.notify(f"Error: {e}", type="negative")
        return
    accion = "archivado" if not c.archivado else "restaurado"
    ui.notify(f"Contacto {accion}.", type="positive")
    ui.navigate.to(f"/networking/contacto/{c.slug}")


def _accion_sugerida(c: Contacto):
    """Sugiere la acción de redacción más probable según el estado del contacto."""
    titulo = (c.ultima_interaccion_titulo or "").lower()
    sin_interaccion = titulo in ("", "creado")
    if "respond" in titulo:
        return ("Responder", "forum", open_redactor_responder)
    if c.estado_relacion == "dormido":
        return ("Reactivar", "restart_alt", open_redactor_reactivacion)
    if c.estado_relacion == "en conversación":
        return ("Responder", "forum", open_redactor_responder)
    if c.estado_relacion == "identificado" or sin_interaccion:
        return ("Primer mensaje", "auto_awesome", open_redactor_primer_mensaje)
    return ("Follow-up", "reply", open_redactor_follow_up)


def render_detalle(slug: str) -> None:
    header("contactos")

    try:
        c = get_contacto(slug)
    except ContactoNoEncontradoError:
        with ui.column().classes("w-full max-w-3xl mx-auto p-8 gap-3"):
            ui.label("Contacto no encontrado").classes("text-2xl font-bold")
            ui.label(f"No existe ningún contacto con slug '{slug}'.").classes(
                "text-gray-600"
            )
            ui.button("← Volver al inicio", on_click=lambda: ui.navigate.to("/networking")).props(
                "flat"
            )
        return

    with ui.column().classes("w-full max-w-3xl mx-auto p-8 gap-6"):
        with ui.row().classes("w-full items-start justify-between"):
            with ui.column().classes("gap-1"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(c.nombre).classes("text-3xl font-bold")
                    ui.label(_LABEL_TEMPERATURA[c.temperatura]).classes(
                        "px-2 py-1 rounded text-xs font-medium "
                        f"{_COLOR_TEMPERATURA[c.temperatura]}"
                    )
                    if c.archivado:
                        ui.label("Archivado").classes(
                            "px-2 py-1 rounded text-xs font-medium "
                            "bg-gray-200 text-gray-700"
                        )
                    if esta_incompleto(c):
                        ui.label("Incompleto").classes(
                            "px-2 py-1 rounded text-xs font-medium "
                            "bg-yellow-100 text-yellow-800"
                        )
                subt_parts = [x for x in (c.rol, c.empresa, c.pais, c.tipo_contacto) if x]
                if subt_parts:
                    ui.label(" · ".join(subt_parts)).classes("text-sm text-gray-600")
            with ui.row().classes("gap-2 items-center"):
                # Acción principal sugerida según el estado del contacto.
                label, icon, handler = _accion_sugerida(c)
                ui.button(
                    label, icon=icon,
                    on_click=lambda c=c, h=handler: h(c),
                ).classes("bg-blue-600 text-white").tooltip(
                    "Acción sugerida según el estado. Otras opciones en 'Redactar'."
                )
                # Resto de tipos de mensaje, agrupados.
                with ui.button("Redactar", icon="edit_note").props("flat"):
                    with ui.menu():
                        ui.menu_item(
                            "Primer mensaje",
                            on_click=lambda c=c: open_redactor_primer_mensaje(c),
                        )
                        ui.menu_item(
                            "Reactivar (dormant tie)",
                            on_click=lambda c=c: open_redactor_reactivacion(c),
                        )
                        ui.menu_item(
                            "Follow-up",
                            on_click=lambda c=c: open_redactor_follow_up(c),
                        )
                        ui.menu_item(
                            "Responder (continuar)",
                            on_click=lambda c=c: open_redactor_responder(c),
                        )
                        ui.menu_item(
                            "Comentar su post",
                            on_click=lambda c=c: open_redactor_comentario(c),
                        )
                ui.button(
                    "Editar", icon="edit",
                    on_click=lambda c=c: open_editar_dialog(
                        c,
                        on_saved=lambda c=c: ui.navigate.to(f"/networking/contacto/{c.slug}"),
                    ),
                ).props("flat")
                # Acciones de gestión, en menú secundario.
                with ui.button(icon="more_vert").props("flat round"):
                    with ui.menu():
                        if c.archivado:
                            ui.menu_item(
                                "Restaurar", on_click=lambda c=c: _toggle_archivado(c),
                            )
                        else:
                            ui.menu_item(
                                "Archivar", on_click=lambda c=c: _toggle_archivado(c),
                            )
                        ui.separator()
                        ui.menu_item(
                            "Borrar", on_click=lambda c=c: _confirm_borrar(c),
                        ).classes("text-red-600")

        with ui.card().classes("w-full p-4"):
            ui.label("Datos").classes("text-xs uppercase text-gray-500 font-semibold")
            _data_row("Empresa", c.empresa)
            _data_row("Rol", c.rol)
            _data_row("País", c.pais)
            _data_row("Tipo de contacto", c.tipo_contacto)
            _data_row("LinkedIn", c.linkedin)
            _data_row("Email", c.email)
            _data_row("Cómo le conocí / por qué le contacto", c.conexion)
            _data_row("Puntos de conexión", c.puntos_conexion)

        with ui.card().classes("w-full p-4"):
            ui.label("Estado").classes(
                "text-xs uppercase text-gray-500 font-semibold"
            )
            _data_row("Temperatura", _LABEL_TEMPERATURA[c.temperatura])
            _data_row("Prioridad", TIER_LABELS.get(c.tier) if c.tier else None)
            _data_row("Estado de la relación", c.estado_relacion)
            _data_row("Salidas", ", ".join(c.salidas) if c.salidas else None)
            _data_row("Próxima acción", c.proxima_accion)
            _data_row("Próxima fecha", _format_date(c.proxima_fecha))

        if c.contexto:
            with ui.card().classes("w-full p-4"):
                ui.label("Contexto pegado").classes(
                    "text-xs uppercase text-gray-500 font-semibold mb-2"
                )
                ui.markdown(c.contexto).classes("text-sm")

        with ui.card().classes("w-full p-4"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Histórico").classes(
                    "text-xs uppercase text-gray-500 font-semibold"
                )
                ui.button(
                    "+ Añadir interacción",
                    on_click=lambda c=c: open_interaccion_dialog(
                        c.slug,
                        on_added=lambda c=c: ui.navigate.to(f"/networking/contacto/{c.slug}"),
                    ),
                ).props("flat dense")
            _historico_render(c.historico_raw)

        with ui.row().classes("w-full text-xs text-gray-400 mt-2"):
            ui.label(f"Archivo: {c.path}")
