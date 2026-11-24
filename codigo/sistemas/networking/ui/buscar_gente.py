from __future__ import annotations

from datetime import date

from nicegui import ui

from sistemas.networking.bridge.claude_bridge import invoke_claude
from sistemas.networking.bridge.prompts import prompt_buscar_gente
from sistemas.networking.storage import perfiles
from sistemas.networking.storage.candidatos import append_candidatos_section
from sistemas.networking.ui.layout import header


def render_buscar_gente() -> None:
    header()
    state: dict = {"loading": False, "resultado": None, "query": ""}

    with ui.column().classes("w-full max-w-3xl mx-auto p-8 gap-3"):
        ui.label("Buscar gente").classes("text-2xl font-bold")
        ui.label(
            "Describe a quién buscas y el agente investiga en la web (búsqueda focalizada, "
            "5-10 personas). Tú revisas antes de añadirlos a Candidatos."
        ).classes("text-sm text-gray-500")

        query_input = (
            ui.input(
                placeholder='Ej: "Heads of AI Risk en banca suiza" o "responsables de datos en energía en Valencia"'
            )
            .props("outlined")
            .classes("w-full")
        )
        buscar_btn = ui.button("Buscar", icon="travel_explore").classes(
            "bg-blue-600 text-white"
        )
        ui.label(
            "⚠️ Lista de búsqueda pública, no de tu red real. Valida en LinkedIn antes de contactar."
        ).classes("text-xs text-amber-700")

        sugeridas = perfiles.busquedas()
        if sugeridas:
            ui.label(
                "Búsquedas sugeridas, de tu investigación de perfiles. Pulsa una para usarla."
            ).classes("text-sm text-gray-600 mt-2")
            por_perfil: dict[str, list[str]] = {}
            for b in sugeridas:
                por_perfil.setdefault(b.perfil, []).append(b.texto)
            for perfil, textos in por_perfil.items():
                with ui.expansion(perfil).classes("w-full text-sm"), ui.column().classes(
                    "w-full gap-1"
                ):
                    for t in textos:
                        ui.button(
                            t, on_click=lambda t=t: query_input.set_value(t),
                        ).props("flat dense no-caps align=left").classes(
                            "w-full text-left normal-case"
                        )

        resultado_col = ui.column().classes("w-full gap-3")

    def render_resultado(texto: str) -> None:
        resultado_col.clear()
        with resultado_col:
            with ui.card().classes("w-full p-3 bg-white border border-gray-200"):
                ui.label("Resultado").classes("text-xs text-gray-500 mb-1")
                ui.markdown(texto).classes("text-sm")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(
                        "Descartar", icon="close",
                        on_click=lambda: resultado_col.clear(),
                    ).props("flat dense")
                    ui.button(
                        "Añadir a Candidatos", icon="playlist_add",
                        on_click=anadir,
                    ).classes("bg-blue-600 text-white")

    def anadir() -> None:
        if not state["resultado"]:
            return
        titulo = f"Búsqueda: {state['query']} ({date.today().isoformat()})"
        try:
            append_candidatos_section(titulo, state["resultado"])
        except Exception as e:
            ui.notify(f"Error guardando: {e}", type="negative")
            return
        ui.notify("Añadido a Candidatos.", type="positive")
        ui.navigate.to("/networking/candidatos")

    async def on_buscar() -> None:
        query = (query_input.value or "").strip()
        if not query:
            ui.notify("Describe a quién buscas.", type="negative")
            return
        if state["loading"]:
            return
        state["loading"] = True
        state["query"] = query
        buscar_btn.set_enabled(False)
        resultado_col.clear()
        import time
        with resultado_col:
            loading = ui.row().classes("items-center gap-2 text-gray-500 text-sm")
            with loading:
                ui.spinner(size="sm")
                progreso = ui.label(
                    "Investigando en la web... 0s — puede tardar 1-3 min, no cierres la pestaña."
                )
        _t0 = time.monotonic()
        _timer = ui.timer(
            1.0,
            lambda: progreso.set_text(
                f"Investigando en la web... {int(time.monotonic() - _t0)}s "
                "— puede tardar 1-3 min, no cierres la pestaña."
            ),
        )

        try:
            response = await invoke_claude(
                prompt_buscar_gente(query),
                allowed_tools=["WebSearch", "WebFetch"],
                timeout=300,
            )
        except Exception as e:
            _timer.active = False
            loading.delete()
            ui.notify(str(e), type="negative")
            state["loading"] = False
            buscar_btn.set_enabled(True)
            return

        _timer.active = False
        loading.delete()
        if not response.success:
            ui.notify(response.error or "Sin respuesta.", type="negative")
        else:
            state["resultado"] = response.text
            render_resultado(response.text)
        state["loading"] = False
        buscar_btn.set_enabled(True)

    buscar_btn.on_click(on_buscar)
