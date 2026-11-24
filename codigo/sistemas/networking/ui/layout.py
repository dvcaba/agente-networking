from __future__ import annotations

from nicegui import ui

from sistemas.networking.storage.contactos import buscar_contactos
from sistemas.networking.storage.watcher import get_version
from sistemas.networking.ui.nuevo import open_nuevo_dialog


def _attach_auto_refresh() -> None:
    """Cada cliente recuerda la versión vista; si un .md cambia fuera de la app
    (editor, Claude Code CLI), el watcher bumpea la versión y la página recarga."""
    seen = {"v": get_version()}

    def _check() -> None:
        current = get_version()
        if current != seen["v"]:
            seen["v"] = current
            ui.navigate.reload()

    ui.timer(2.0, _check)


def _nav_btn(label: str, icon: str, ruta: str, key: str, activo: str) -> None:
    btn = ui.button(label, on_click=lambda: ui.navigate.to(ruta), icon=icon).props("flat")
    if key == activo:
        btn.classes("text-blue-600 font-semibold")


def header(activo: str = "", *, auto_refresh: bool = True) -> None:
    # Import tardío: la cabecera común es de la web, que se rehace en la fase 3. Importarla
    # arriba hacía que cargar cualquier pantalla —o su test— exigiera la web entera.
    from apps.web.shell import _theme

    if auto_refresh:
        _attach_auto_refresh()
    # 1) Barra superior propia. Antes era la de la plataforma (`shell_header`), que ponía
    #    «agent-platform» y un menú lateral a `/` y `/sistema/networking`: páginas que en
    #    esta app no existen, así que cada clic acababa en 404. Del motor solo se usa el tema.
    _theme()
    with ui.header(elevated=False).classes(
        "bg-white border-b border-gray-200 px-5 py-2 items-center"
    ), ui.row().classes("items-center gap-2 cursor-pointer").on(
        "click", lambda: ui.navigate.to("/networking")
    ):
        ui.icon("diversity_3").classes("text-indigo-500 text-2xl")
        ui.label("Agente de networking").classes("text-lg font-semibold")
    # 2) Sub-navegación de las pantallas.
    with ui.row().classes(
        "w-full bg-gray-50 border-b border-gray-200 px-8 py-2 items-center justify-between gap-4"
    ):
        with ui.row().classes("items-center gap-1"):
            _nav_btn("Inicio", "forum", "/networking", "inicio", activo)
            _nav_btn("Contactos", "people", "/networking/contactos", "contactos", activo)
            _nav_btn("Candidatos", "how_to_reg", "/networking/candidatos", "candidatos", activo)
            _nav_btn("Asistente", "chat", "/networking/asistente", "asistente", activo)
            with ui.button("Herramientas", icon="build").props("flat"):
                with ui.menu():
                    ui.menu_item(
                        "Buscar gente",
                        on_click=lambda: ui.navigate.to("/networking/buscar-gente"),
                    )
                    ui.menu_item(
                        "Comentar un post",
                        on_click=lambda: ui.navigate.to("/networking/comentar"),
                    )
            with ui.button("Documentos", icon="folder_open").props("flat"):
                with ui.menu():
                    ui.menu_item(
                        "Estrategia", on_click=lambda: ui.navigate.to("/networking/estrategia"),
                    )
                    ui.menu_item(
                        "Biblioteca", on_click=lambda: ui.navigate.to("/networking/biblioteca"),
                    )

        with ui.row().classes("items-center gap-2 flex-1 justify-end"):
            _render_busqueda_global()
            ui.button(
                "Nuevo contacto",
                on_click=open_nuevo_dialog,
                icon="add",
            ).classes("bg-blue-600 text-white")


def _render_busqueda_global() -> None:
    search_input = (
        ui.input(placeholder="Buscar contacto...")
        .props("outlined dense clearable")
        .classes("max-w-xs w-72")
    )
    with search_input:
        menu = ui.menu().props("fit no-parent-event").classes("min-w-[300px]")
        with menu:
            results_col = ui.column().classes(
                "p-0 max-h-[400px] overflow-auto w-full"
            )

    def update_results() -> None:
        q = (search_input.value or "").strip()
        results_col.clear()
        if len(q) < 2:
            menu.close()
            return
        try:
            matches = buscar_contactos(q)
        except Exception:
            menu.close()
            return

        with results_col:
            if not matches:
                ui.label("Sin resultados").classes(
                    "text-xs text-gray-500 px-3 py-2"
                )
            else:
                for c in matches:
                    with ui.column().classes(
                        "w-full px-3 py-2 cursor-pointer hover:bg-gray-100 gap-0"
                    ).on("click", lambda c=c: _go_to(c.slug, menu, search_input)):
                        ui.label(c.nombre).classes("text-sm font-medium")
                        sub = " · ".join(x for x in (c.empresa, c.pais) if x)
                        if sub:
                            ui.label(sub).classes("text-xs text-gray-500")
        menu.open()

    search_input.on("update:model-value", lambda _: update_results())


def _go_to(slug: str, menu, search_input) -> None:
    menu.close()
    search_input.value = ""
    ui.navigate.to(f"/networking/contacto/{slug}")
