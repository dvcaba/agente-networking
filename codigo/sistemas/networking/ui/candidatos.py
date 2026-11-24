from __future__ import annotations

from collections import defaultdict

from nicegui import ui

from sistemas.networking.storage.candidatos import (
    Candidato,
    candidato_slug,
    candidato_to_prefill,
    candidates_path,
    list_candidatos,
)
from sistemas.networking.storage.contactos import list_contactos
from sistemas.networking.ui.layout import header
from sistemas.networking.ui.nuevo import open_nuevo_dialog

_CONF_COLOR: dict[str, str] = {
    "confirmed": "bg-green-100 text-green-800",
    "inferred": "bg-amber-100 text-amber-800",
    "speculative": "bg-gray-100 text-gray-600",
}


def _confidence_badge(confidence: str) -> None:
    color = _CONF_COLOR.get(confidence.lower(), "bg-gray-100 text-gray-600")
    ui.label(confidence or "—").classes(
        f"px-2 py-0.5 rounded text-xs font-medium {color}"
    )


def _candidato_row(c: Candidato, existing_slugs: set[str], on_promoted) -> None:
    ya_es_contacto = candidato_slug(c) in existing_slugs

    with ui.row().classes(
        "w-full items-center gap-3 px-3 py-2 rounded hover:bg-gray-50 border-b border-gray-100"
    ):
        with ui.column().classes("gap-0 flex-1 min-w-0"):
            with ui.row().classes("items-center gap-2"):
                ui.label(c.nombre).classes("font-medium text-sm")
                _confidence_badge(c.confidence)
            if c.rol:
                ui.label(c.rol).classes("text-xs text-gray-500 truncate")
            if c.valor:
                ui.label(c.valor).classes("text-xs text-gray-400 truncate max-w-[520px]")

        if c.linkedin:
            ui.link("LinkedIn ↗", c.linkedin, new_tab=True).classes("text-sm link-action")

        if ya_es_contacto:
            ui.button(
                "Ya es contacto",
                icon="check",
                on_click=lambda c=c: ui.navigate.to(f"/networking/contacto/{candidato_slug(c)}"),
            ).props("flat dense").classes("text-green-700")
        else:
            ui.button(
                "Promover a contacto",
                icon="person_add",
                on_click=lambda c=c: open_nuevo_dialog(
                    prefill=candidato_to_prefill(c)
                ),
            ).props("dense").classes("bg-blue-600 text-white")


def render_candidatos() -> None:
    header("candidatos")
    candidatos = list_candidatos()
    existing_slugs = {c.slug for c in list_contactos()}

    with ui.column().classes("w-full max-w-5xl mx-auto p-8 gap-4"):
        with ui.column().classes("w-full gap-0"):
            with ui.row().classes("w-full items-baseline gap-3"):
                ui.label("Candidatos identificados").classes("text-2xl font-bold")
                ui.label(f"{len(candidatos)} personas").classes("text-sm text-gray-500")
            ui.label(
                "Gente del research, aún no son contactos. \"Promover a contacto\" "
                "les crea su ficha y los saca de aquí."
            ).classes("text-sm text-gray-500")

        if not candidatos:
            with ui.card().classes("w-full p-6"):
                ui.label("No se encontraron candidatos.").classes("text-gray-700")
                ui.label(
                    f"Se esperaba el archivo: {candidates_path()}"
                ).classes("text-xs text-gray-500")
            return

        with ui.card().classes("w-full p-4 bg-amber-50 border border-amber-200"):
            ui.label("⚠️ Antes de promover").classes("text-sm font-semibold text-amber-900")
            ui.markdown(
                "Lista derivada de búsqueda pública (snippets LinkedIn + web), no de "
                "tu red real. **Valida en LinkedIn logueado** y **marca quiénes "
                "recuerdas personalmente** antes de contactar. Al promover, el contacto "
                "se crea con temperatura *frío* y procedencia pre-rellenada — revísalo. "
                "El campo 'Rol' trae el texto del research sin separar empresa; ajústalo."
            ).classes("text-xs text-amber-800")

        grupos: dict[str, list[Candidato]] = defaultdict(list)
        for c in candidatos:
            grupos[c.categoria].append(c)

        # Orden por número de categoría (cat_num del primer item de cada grupo)
        def _grupo_orden(item: tuple[str, list[Candidato]]) -> int:
            try:
                return int(item[1][0].cat_num)
            except (ValueError, IndexError):
                return 999

        for cat_title, items in sorted(grupos.items(), key=_grupo_orden):
            with ui.card().classes("w-full p-4"):
                with ui.row().classes("w-full items-center justify-between mb-1"):
                    ui.label(cat_title).classes("text-sm font-semibold text-gray-800")
                    ui.label(f"{len(items)}").classes("text-xs text-gray-500")
                if items:
                    ui.label(f"Origen: {items[0].origen}").classes(
                        "text-xs text-gray-500 mb-2"
                    )
                for c in items:
                    _candidato_row(c, existing_slugs, None)
