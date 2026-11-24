from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from nicegui import ui

from sistemas.networking.storage.contactos import (
    Contacto,
    ESTADOS_RELACION,
    PAISES_PREDEFINIDOS,
    SALIDAS_PREDEFINIDAS,
    TIER_LABELS,
    TIERS,
    TIPOS_CONTACTO_PREDEFINIDOS,
    list_contactos,
    normalize_text,
)
from sistemas.networking.ui.layout import header

_TEMPERATURAS_OPTIONS: tuple[str, ...] = ("caliente", "tibio", "frío", "desconocido")

_TEMP_ICON: dict[str, str] = {
    "caliente": "🔥 Caliente",
    "tibio": "◔ Tibio",
    "frío": "❄️ Frío",
    "desconocido": "— Sin estado",
}

_TIER_CORTO: dict[int, str] = {1: "Alta", 2: "Media", 3: "Ligera", 4: "Pausa"}

_AGRUPAR_OPCIONES: tuple[str, ...] = (
    "Ninguno",
    "Temperatura",
    "Prioridad",
    "Estado",
    "País",
    "Tipo",
    "Empresa",
)


@dataclass
class FiltrosListado:
    busqueda: str = ""
    temperaturas: list[str] = field(default_factory=list)
    paises: list[str] = field(default_factory=list)
    tipos: list[str] = field(default_factory=list)
    tiers: list[int] = field(default_factory=list)
    estados: list[str] = field(default_factory=list)
    salidas: list[str] = field(default_factory=list)
    solo_incompletos: bool = False
    incluir_archivados: bool = False
    agrupar_por: str = "Ninguno"


def _matches_busqueda(c: Contacto, q: str) -> bool:
    if not q:
        return True
    q_norm = normalize_text(q)
    haystack = " ".join(
        normalize_text(x)
        for x in (c.nombre, c.empresa, c.rol, c.pais, c.tipo_contacto)
        if x
    )
    return q_norm in haystack


def _aplicar_filtros(contactos: list[Contacto], f: FiltrosListado) -> list[Contacto]:
    from sistemas.networking.storage.contactos import esta_incompleto

    out = contactos
    if not f.incluir_archivados:
        out = [c for c in out if not c.archivado]
    if f.temperaturas:
        out = [c for c in out if c.temperatura in f.temperaturas]
    if f.paises:
        out = [c for c in out if c.pais in f.paises]
    if f.tipos:
        out = [c for c in out if c.tipo_contacto in f.tipos]
    if f.tiers:
        out = [c for c in out if c.tier in f.tiers]
    if f.estados:
        out = [c for c in out if c.estado_relacion in f.estados]
    if f.salidas:
        out = [c for c in out if any(s in c.salidas for s in f.salidas)]
    if f.solo_incompletos:
        out = [c for c in out if esta_incompleto(c)]
    if f.busqueda:
        out = [c for c in out if _matches_busqueda(c, f.busqueda)]
    return out


def _grupo_key(c: Contacto, criterio: str) -> str:
    if criterio == "Temperatura":
        return _TEMP_ICON.get(c.temperatura, c.temperatura)
    if criterio == "Prioridad":
        return TIER_LABELS.get(c.tier, "Sin prioridad") if c.tier else "Sin prioridad"
    if criterio == "Estado":
        return c.estado_relacion or "Sin estado"
    if criterio == "País":
        return c.pais or "Sin país"
    if criterio == "Tipo":
        return c.tipo_contacto or "Sin tipo"
    if criterio == "Empresa":
        return c.empresa or "Sin empresa"
    return ""


def _format_fecha(d: date | None) -> str:
    return d.isoformat() if d else "—"


def _build_row(c: Contacto) -> dict:
    return {
        "slug": c.slug,
        "nombre": c.nombre,
        "empresa": c.empresa or "—",
        "pais": c.pais or "—",
        "tipo": c.tipo_contacto or "—",
        "temperatura": _TEMP_ICON.get(c.temperatura, c.temperatura),
        "tier": _TIER_CORTO.get(c.tier, "—"),
        "estado": c.estado_relacion or "—",
        "proxima_fecha": _format_fecha(c.proxima_fecha),
        "archivado": "Sí" if c.archivado else "",
    }


def _tabla(contactos: list[Contacto]) -> None:
    columns = [
        {"name": "nombre", "label": "Nombre", "field": "nombre", "align": "left", "sortable": True},
        {"name": "empresa", "label": "Empresa", "field": "empresa", "align": "left", "sortable": True},
        {"name": "pais", "label": "País", "field": "pais", "align": "left", "sortable": True},
        {"name": "tipo", "label": "Tipo", "field": "tipo", "align": "left", "sortable": True},
        {
            "name": "temperatura",
            "label": "Temp",
            "field": "temperatura",
            "align": "left",
            "sortable": True,
        },
        {"name": "tier", "label": "Prioridad", "field": "tier", "align": "left", "sortable": True},
        {"name": "estado", "label": "Estado", "field": "estado", "align": "left", "sortable": True},
        {
            "name": "proxima_fecha",
            "label": "Próx. fecha",
            "field": "proxima_fecha",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "archivado",
            "label": "Arch",
            "field": "archivado",
            "align": "left",
            "sortable": True,
        },
    ]
    rows = [_build_row(c) for c in contactos]
    tabla = ui.table(
        columns=columns,
        rows=rows,
        row_key="slug",
        pagination={"rowsPerPage": 25, "sortBy": "nombre"},
    ).classes("w-full").props("flat dense bordered")

    def on_row_click(e):
        slug = e.args[1].get("slug")
        if slug:
            ui.navigate.to(f"/networking/contacto/{slug}")

    tabla.on("row-click", on_row_click)


def render_contactos_listado() -> None:
    header("contactos")
    filtros = FiltrosListado()

    with ui.column().classes("w-full max-w-6xl mx-auto p-8 gap-4"):
        ui.label("Contactos").classes("text-2xl font-bold")

        with ui.card().classes("w-full p-3 gap-2"):
            busqueda_input = (
                ui.input(placeholder="Buscar nombre / empresa / país / rol...")
                .props("outlined dense clearable")
                .classes("w-full")
            )
            with ui.expansion("Más filtros", icon="filter_list").classes("w-full"):
                with ui.row().classes("w-full gap-2 flex-wrap items-center"):
                    temp_select = (
                        ui.select(
                            options=list(_TEMPERATURAS_OPTIONS), label="Temperatura",
                            multiple=True, clearable=True,
                        )
                        .props("dense outlined use-chips").classes("min-w-[170px]")
                    )
                    pais_select = (
                        ui.select(
                            options=[*PAISES_PREDEFINIDOS], label="País",
                            multiple=True, clearable=True,
                        )
                        .props("dense outlined use-chips").classes("min-w-[170px]")
                    )
                    tipo_select = (
                        ui.select(
                            options=[*TIPOS_CONTACTO_PREDEFINIDOS], label="Tipo",
                            multiple=True, clearable=True,
                        )
                        .props("dense outlined use-chips").classes("min-w-[200px]")
                    )
                    tier_select = (
                        ui.select(
                            options={t: TIER_LABELS[t] for t in TIERS}, label="Prioridad",
                            multiple=True, clearable=True,
                        )
                        .props("dense outlined use-chips").classes("min-w-[180px]")
                    )
                    estado_select = (
                        ui.select(
                            options=list(ESTADOS_RELACION), label="Estado",
                            multiple=True, clearable=True,
                        )
                        .props("dense outlined use-chips").classes("min-w-[200px]")
                    )
                    salidas_select = (
                        ui.select(
                            options=list(SALIDAS_PREDEFINIDAS), label="Salidas",
                            multiple=True, clearable=True,
                        )
                        .props("dense outlined use-chips").classes("min-w-[220px]")
                    )
                with ui.row().classes("w-full gap-4 items-center mt-2"):
                    incompletos_toggle = ui.switch("Solo incompletos").classes("text-sm")
                    archivados_toggle = ui.switch("Incluir archivados").classes("text-sm")
                    ui.space()
                    agrupar_select = (
                        ui.select(
                            options=list(_AGRUPAR_OPCIONES), value="Ninguno",
                            label="Agrupar por",
                        )
                        .props("dense outlined").classes("min-w-[160px]")
                    )

        @ui.refreshable
        def render_listado() -> None:
            filtros.busqueda = busqueda_input.value or ""
            filtros.temperaturas = list(temp_select.value or [])
            filtros.paises = list(pais_select.value or [])
            filtros.tipos = list(tipo_select.value or [])
            filtros.tiers = list(tier_select.value or [])
            filtros.estados = list(estado_select.value or [])
            filtros.salidas = list(salidas_select.value or [])
            filtros.solo_incompletos = bool(incompletos_toggle.value)
            filtros.incluir_archivados = bool(archivados_toggle.value)
            filtros.agrupar_por = agrupar_select.value or "Ninguno"

            todos = list_contactos()
            visibles = _aplicar_filtros(todos, filtros)

            with ui.column().classes("w-full gap-2"):
                ui.label(
                    f"{len(visibles)} de {len(todos)} contactos"
                ).classes("text-sm text-gray-500")

                if not visibles:
                    ui.label("Sin resultados con los filtros actuales.").classes(
                        "text-gray-500 italic py-8 text-center"
                    )
                    return

                if filtros.agrupar_por == "Ninguno":
                    _tabla(visibles)
                    return

                grupos: dict[str, list[Contacto]] = defaultdict(list)
                for c in visibles:
                    grupos[_grupo_key(c, filtros.agrupar_por)].append(c)

                for clave in sorted(grupos.keys()):
                    items = grupos[clave]
                    with ui.column().classes("w-full gap-1"):
                        ui.label(f"{clave}  ({len(items)})").classes(
                            "text-sm font-semibold text-gray-700 mt-2"
                        )
                        _tabla(items)

        for w in (
            busqueda_input,
            temp_select,
            pais_select,
            tipo_select,
            tier_select,
            estado_select,
            salidas_select,
            incompletos_toggle,
            archivados_toggle,
            agrupar_select,
        ):
            w.on("update:model-value", lambda _: render_listado.refresh())

        render_listado()
