from __future__ import annotations

from nicegui import ui

from sistemas.networking.storage.contactos import (
    ESTADOS_RELACION,
    PAISES_PREDEFINIDOS,
    SALIDAS_PREDEFINIDAS,
    TIER_LABELS,
    TIERS,
    TIPOS_CONTACTO_PREDEFINIDOS,
    ContactoExistenteError,
    NuevoContactoInput,
    create_contacto,
)

_OPCION_OTRO = "Otro"

_CHIPS_PUNTOS_CONEXION: tuple[str, ...] = (
    "Ex-misma empresa",
    "Misma universidad / formación",
    "Contacto común",
    "Mismo evento",
    "Mismo tema / publicación",
    "Mismo sector",
)


def open_nuevo_dialog(prefill: NuevoContactoInput | None = None) -> None:
    state = prefill or NuevoContactoInput(nombre="")

    def _initial_select(value: str, opciones: tuple[str, ...]) -> str | None:
        if not value:
            return None
        return value if value in opciones else _OPCION_OTRO

    pais_inicial = _initial_select(state.pais, PAISES_PREDEFINIDOS)
    tipo_inicial = _initial_select(state.tipo_contacto, TIPOS_CONTACTO_PREDEFINIDOS)

    with ui.dialog() as dialog, ui.card().classes(
        "w-[640px] max-w-[92vw] max-h-[90vh] overflow-auto p-6"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Nuevo contacto").classes("text-2xl font-bold")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")
        ui.label(
            "Solo el nombre es obligatorio. El resto puedes rellenarlo después."
        ).classes("text-sm text-gray-500")

        with ui.column().classes("w-full gap-3 mt-2"):
            ui.input("Nombre completo *").bind_value(state, "nombre").classes("w-full")

            with ui.row().classes("w-full gap-3"):
                ui.input("Empresa").bind_value(state, "empresa").classes("flex-1")
                ui.input("Rol").bind_value(state, "rol").classes("flex-1")

            with ui.row().classes("w-full gap-3 items-start"):
                pais_select = ui.select(
                    options=[*PAISES_PREDEFINIDOS, _OPCION_OTRO],
                    label="País",
                    value=pais_inicial,
                ).classes("flex-1")
                pais_otro = (
                    ui.input("Especificar país").bind_value(state, "pais").classes("flex-1")
                )
                pais_otro.bind_visibility_from(
                    pais_select, "value", backward=lambda v: v == _OPCION_OTRO
                )

            with ui.row().classes("w-full gap-3 items-start"):
                tipo_select = ui.select(
                    options=[*TIPOS_CONTACTO_PREDEFINIDOS, _OPCION_OTRO],
                    label="Tipo de contacto",
                    value=tipo_inicial,
                ).classes("flex-1")
                tipo_otro = (
                    ui.input("Especificar tipo")
                    .bind_value(state, "tipo_contacto")
                    .classes("flex-1")
                )
                tipo_otro.bind_visibility_from(
                    tipo_select, "value", backward=lambda v: v == _OPCION_OTRO
                )

            with ui.row().classes("w-full gap-3 items-start"):
                ui.select(
                    options={t: TIER_LABELS[t] for t in TIERS},
                    label="Prioridad", clearable=True,
                ).bind_value(state, "tier").classes("flex-1").tooltip(
                    "Cuánto te vuelcas en esta relación: 1 alta … 4 en pausa."
                )
                ui.select(
                    options=list(ESTADOS_RELACION),
                    label="Estado de la relación",
                    clearable=True,
                ).bind_value(state, "estado_relacion").classes("flex-1")
            ui.select(
                options=list(SALIDAS_PREDEFINIDAS),
                label="Salidas (qué podría dar esta relación)",
                multiple=True,
                new_value_mode="add-unique",
                clearable=True,
            ).props("use-chips").bind_value(state, "salidas").classes("w-full").tooltip(
                "Multi-valor y abierto: añade las que quieras."
            )

            ui.textarea("Cómo le conocí / por qué le contacto").bind_value(
                state, "conexion"
            ).classes("w-full").tooltip(
                "Sin esto, el agente no podrá redactar un buen primer mensaje."
            )

            ui.label("Puntos de conexión (opcional)").classes(
                "text-sm font-medium text-gray-700 mt-1"
            )
            ui.label("Click en una sugerencia para añadirla al textarea:").classes(
                "text-xs text-gray-500"
            )
            puntos_textarea = (
                ui.textarea(placeholder="Hechos compartidos, uno por línea.")
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

            ui.textarea("Oferta / publicación / contexto pegado (opcional)").bind_value(
                state, "contexto"
            ).classes("w-full").props("rows=5").tooltip(
                "Pega aquí el texto de la oferta, post, charla, etc."
            )

            with ui.expansion("Más detalles", icon="more_horiz").classes("w-full"):
                ui.input("LinkedIn (URL)").bind_value(state, "linkedin").classes("w-full")
                ui.input("Email").bind_value(state, "email").classes("w-full")

        def on_submit() -> None:
            if pais_select.value and pais_select.value != _OPCION_OTRO:
                state.pais = pais_select.value
            if tipo_select.value and tipo_select.value != _OPCION_OTRO:
                state.tipo_contacto = tipo_select.value
            state.estado_relacion = state.estado_relacion or ""
            state.salidas = state.salidas or []

            try:
                path = create_contacto(state)
            except ValueError as e:
                ui.notify(str(e), type="negative")
                return
            except ContactoExistenteError as e:
                ui.notify(str(e), type="negative")
                return
            ui.notify(f"Contacto creado: {path.name}", type="positive")
            dialog.close()
            ui.navigate.to(f"/networking/contacto/{path.stem}")

        with ui.row().classes("w-full justify-end mt-4 gap-2"):
            ui.button("Cancelar", on_click=dialog.close).props("flat")
            ui.button("Crear contacto", on_click=on_submit).classes(
                "bg-blue-600 text-white px-6 py-2 rounded"
            )

    dialog.open()
