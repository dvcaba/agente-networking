from __future__ import annotations

from typing import Callable

from nicegui import ui

from sistemas.networking.storage.contactos import (
    Contacto,
    ContactoNoEncontradoError,
    EditContactoInput,
    ESTADOS_RELACION,
    PAISES_PREDEFINIDOS,
    SALIDAS_PREDEFINIDAS,
    TIER_LABELS,
    TIERS,
    TIPOS_CONTACTO_PREDEFINIDOS,
    update_contacto,
)

_OPCION_OTRO = "Otro"

_TEMPERATURAS_OPCIONES: tuple[str, ...] = ("frío", "tibio", "caliente")

_CHIPS_PUNTOS_CONEXION: tuple[str, ...] = (
    "Ex-misma empresa",
    "Misma universidad / formación",
    "Contacto común",
    "Mismo evento",
    "Mismo tema / publicación",
    "Mismo sector",
)


def _initial_select_value(current: str | None, opciones: tuple[str, ...]) -> tuple:
    if not current:
        return None, ""
    if current in opciones:
        return current, ""
    return _OPCION_OTRO, current


def open_editar_dialog(
    c: Contacto,
    *,
    on_saved: Callable[[], None] | None = None,
) -> None:
    state = EditContactoInput(
        empresa=c.empresa or "",
        rol=c.rol or "",
        pais=c.pais or "",
        tipo_contacto=c.tipo_contacto or "",
        linkedin=c.linkedin or "",
        email=c.email or "",
        conexion=c.conexion or "",
        puntos_conexion=c.puntos_conexion or "",
        contexto=c.contexto or "",
        temperatura=c.temperatura if c.temperatura in _TEMPERATURAS_OPCIONES else "frío",
        tier=c.tier,
        estado_relacion=c.estado_relacion or "",
        salidas=list(c.salidas),
        proxima_accion=c.proxima_accion or "",
        proxima_fecha=c.proxima_fecha.isoformat() if c.proxima_fecha else "",
    )

    pais_initial, pais_otro_initial = _initial_select_value(c.pais, PAISES_PREDEFINIDOS)
    tipo_initial, tipo_otro_initial = _initial_select_value(
        c.tipo_contacto, TIPOS_CONTACTO_PREDEFINIDOS
    )

    with ui.dialog().props("persistent") as dialog, ui.card().classes(
        "w-[680px] max-w-[94vw] max-h-[90vh] overflow-auto p-6"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"Editar — {c.nombre}").classes("text-xl font-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")
        ui.label("Los cambios se guardan en el archivo .md. El histórico no se toca.").classes(
            "text-sm text-gray-500"
        )

        with ui.column().classes("w-full gap-3 mt-2"):
            with ui.row().classes("w-full gap-3"):
                ui.input("Empresa").bind_value(state, "empresa").classes("flex-1")
                ui.input("Rol").bind_value(state, "rol").classes("flex-1")

            with ui.row().classes("w-full gap-3 items-start"):
                pais_select = ui.select(
                    options=[*PAISES_PREDEFINIDOS, _OPCION_OTRO],
                    label="País",
                    value=pais_initial,
                ).classes("flex-1")
                pais_otro = ui.input(
                    "Especificar país", value=pais_otro_initial
                ).classes("flex-1")
                pais_otro.bind_visibility_from(
                    pais_select, "value", backward=lambda v: v == _OPCION_OTRO
                )

            with ui.row().classes("w-full gap-3 items-start"):
                tipo_select = ui.select(
                    options=[*TIPOS_CONTACTO_PREDEFINIDOS, _OPCION_OTRO],
                    label="Tipo de contacto",
                    value=tipo_initial,
                ).classes("flex-1")
                tipo_otro = ui.input(
                    "Especificar tipo", value=tipo_otro_initial
                ).classes("flex-1")
                tipo_otro.bind_visibility_from(
                    tipo_select, "value", backward=lambda v: v == _OPCION_OTRO
                )

            ui.textarea("Cómo le conocí / por qué le contacto").bind_value(
                state, "conexion"
            ).classes("w-full")

            ui.label("Puntos de conexión").classes(
                "text-sm font-medium text-gray-700 mt-1"
            )
            puntos_textarea = (
                ui.textarea()
                .bind_value(state, "puntos_conexion")
                .classes("w-full")
                .props("rows=4")
            )

            def add_chip(prefijo: str) -> None:
                current = puntos_textarea.value or ""
                addition = f"- {prefijo}: " if prefijo else "- "
                sep = "\n" if current and not current.endswith("\n") else ""
                puntos_textarea.value = current + sep + addition

            with ui.row().classes("flex-wrap gap-1"):
                for chip_label in _CHIPS_PUNTOS_CONEXION:
                    ui.chip(
                        chip_label,
                        icon="add",
                        on_click=lambda lbl=chip_label: add_chip(lbl),
                    ).props("clickable color=grey-3 text-color=grey-9")
                ui.chip(
                    "Otro",
                    icon="add",
                    on_click=lambda: add_chip(""),
                ).props("clickable color=grey-3 text-color=grey-9")

            ui.textarea("Oferta / publicación / contexto pegado").bind_value(
                state, "contexto"
            ).classes("w-full").props("rows=5")

            ui.label("Estado").classes(
                "text-xs uppercase text-gray-500 font-semibold mt-3"
            )
            with ui.row().classes("w-full gap-3 items-start"):
                ui.select(
                    options=list(_TEMPERATURAS_OPCIONES),
                    label="Temperatura",
                    value=state.temperatura,
                ).bind_value(state, "temperatura").classes("flex-1")
                ui.input(
                    "Próxima fecha (AAAA-MM-DD)",
                ).bind_value(state, "proxima_fecha").classes("flex-1")
            with ui.row().classes("w-full gap-3 items-start"):
                ui.select(
                    options={t: TIER_LABELS[t] for t in TIERS},
                    label="Prioridad",
                    value=state.tier,
                    clearable=True,
                ).bind_value(state, "tier").classes("flex-1")
                ui.select(
                    options=list(ESTADOS_RELACION),
                    label="Estado de la relación",
                    value=state.estado_relacion or None,
                    clearable=True,
                ).bind_value(state, "estado_relacion").classes("flex-1")
            ui.select(
                options=list(SALIDAS_PREDEFINIDAS),
                label="Salidas (qué podría dar esta relación)",
                value=state.salidas,
                multiple=True,
                new_value_mode="add-unique",
                clearable=True,
            ).props("use-chips").bind_value(state, "salidas").classes("w-full")
            ui.input("Próxima acción").bind_value(state, "proxima_accion").classes("w-full")

            with ui.expansion("Más detalles", icon="more_horiz").classes("w-full"):
                ui.input("LinkedIn (URL)").bind_value(state, "linkedin").classes("w-full")
                ui.input("Email").bind_value(state, "email").classes("w-full")

        def on_submit() -> None:
            if pais_select.value and pais_select.value != _OPCION_OTRO:
                state.pais = pais_select.value
            elif pais_select.value == _OPCION_OTRO:
                state.pais = (pais_otro.value or "").strip()
            else:
                state.pais = ""

            if tipo_select.value and tipo_select.value != _OPCION_OTRO:
                state.tipo_contacto = tipo_select.value
            elif tipo_select.value == _OPCION_OTRO:
                state.tipo_contacto = (tipo_otro.value or "").strip()
            else:
                state.tipo_contacto = ""

            state.estado_relacion = state.estado_relacion or ""
            state.salidas = state.salidas or []

            try:
                update_contacto(c.slug, state)
            except (ValueError, ContactoNoEncontradoError) as e:
                ui.notify(str(e), type="negative")
                return
            ui.notify("Cambios guardados.", type="positive")
            dialog.close()
            if on_saved:
                on_saved()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancelar", on_click=dialog.close).props("flat")
            ui.button("Guardar", on_click=on_submit).classes(
                "bg-blue-600 text-white px-6 py-2 rounded"
            )

    dialog.open()
