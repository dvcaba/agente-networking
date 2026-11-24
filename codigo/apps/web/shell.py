"""Lo común de todas las pantallas: tema visual, cabecera, barra lateral y los dos paneles
de las esperas largas.

La barra lateral se dibuja desde los sistemas que existen: crear uno lo hace aparecer solo,
sin tocar la interfaz.
"""

from __future__ import annotations

import nicegui
from nicegui import ui

from core import systems

# Pone Quasar en español: localiza los textos por defecto del framework
# (paginación de tablas "Registros por página" / "1-3 de 3", selects "Sin
# resultados", botones de diálogos…). El pack lo sirve la propia NiceGUI, sin
# CDN externo. Espera a que window.Quasar exista para evitar carreras de carga.
_QUASAR_LANG_JS = f"""
<script>
(function(){{
  var url = "/_nicegui/{nicegui.__version__}/static/lang/es.umd.prod.js";
  function set() {{ try {{ window.Quasar.lang.set(window.Quasar.Lang.es); }} catch (e) {{}} }}
  function apply() {{
    if (!window.Quasar) {{ return setTimeout(apply, 50); }}
    if (window.Quasar.Lang && window.Quasar.Lang.es) {{ return set(); }}
    var s = document.createElement('script');
    s.src = url; s.onload = set;
    document.head.appendChild(s);
  }}
  apply();
}})();
</script>
"""

_THEME_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  /* Tipografía Inter ajustada, superficies definidas por borde antes que por sombra,
     acento índigo y una paleta semántica para que el color informe, no decore. */
  :root {
    --bg:#f5f6f9; --bg-2:#eef0f5; --surface:#ffffff; --border:#e6e8ee;
    --ink:#0b0d12; --body:#272b33; --muted:#5d6473;
    --accent:#5b62d6; --accent-d:#454dbf; --accent-soft:#ecedfb;
    --ok:#0f9d6b; --ok-soft:#e4f6ee;
    --warm:#c2700a; --warm-soft:#fcf1dd;
    --hot:#dc4a35; --hot-soft:#fdeae6;
    --cold:#3b7bdb; --cold-soft:#e7f0fc;
    --shadow-sm:0 1px 2px rgba(16,17,26,.05);
    --shadow-lg:0 12px 30px rgba(16,17,26,.11), 0 2px 6px rgba(16,17,26,.06);
  }

  /* Escala global: subir el tamaño raíz agranda toda la app de forma uniforme. */
  html { font-size: 18.75px !important; }

  body, .q-layout, .q-page-container, .q-page, .nicegui-content {
    background: linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%) !important;
    background-attachment: fixed !important;
  }
  body, .q-field, .q-btn, .q-item, .q-menu {
    font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif !important;
  }
  body { color: var(--body); line-height: 1.65; font-size: 17.5px;
         -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }

  .text-3xl { font-size:2.3rem !important; line-height:1.12 !important; font-weight:780 !important;
              color:var(--ink); letter-spacing:-.028em; }
  .text-2xl { font-size:1.7rem !important;  line-height:1.22 !important; font-weight:740 !important;
              color:var(--ink); letter-spacing:-.022em; }
  .text-xl  { font-size:1.4rem !important;  font-weight:680 !important; color:var(--ink); letter-spacing:-.015em; }
  .text-lg  { font-size:1.28rem !important; font-weight:640 !important; letter-spacing:-.01em; }
  .text-base{ font-size:1.0625rem !important; }
  .text-sm  { font-size:1rem !important; }
  .text-xs  { font-size:.875rem !important; }
  .font-semibold { color:var(--ink); font-weight:640; }
  .font-bold { color:var(--ink); }
  .text-gray-600 { color:var(--muted) !important; }
  .text-gray-500 { color:#6b7280 !important; }

  .q-card { background:var(--surface) !important; border:1px solid var(--border) !important;
            border-radius:14px !important; box-shadow:var(--shadow-sm) !important;
            transition: box-shadow .18s ease, transform .18s ease, border-color .18s ease; }
  .q-card:hover { box-shadow:var(--shadow-lg) !important; border-color:#d7dae3 !important; }
  .q-expansion-item { background:var(--surface); border:1px solid var(--border);
                      border-radius:12px !important; margin-bottom:8px; }

  .text-blue-600, .text-blue-500, .text-indigo-500, .text-indigo-600 { color:var(--accent) !important; }
  .bg-blue-100, .bg-blue-50, .bg-indigo-100, .bg-indigo-50 { background:var(--accent-soft) !important; }
  .bg-blue-600, .bg-indigo-600 {
    background:linear-gradient(135deg, var(--accent), var(--accent-d)) !important;
    color:#fff !important; box-shadow:0 1px 2px rgba(69,77,191,.35) !important; }
  .bg-blue-600:hover, .bg-indigo-600:hover { filter:brightness(1.06); }

  /* Links dentro de un párrafo: subrayado fino que se engrosa al pasar el ratón. */
  a, a.q-link { color:var(--accent) !important; font-weight:600 !important;
                text-decoration:underline !important;
                text-decoration-color:rgba(91,98,214,.38) !important;
                text-decoration-thickness:1.5px !important; text-underline-offset:3px !important;
                transition:text-decoration-color .15s ease, text-decoration-thickness .15s ease, color .15s ease; }
  a:hover { color:var(--accent-d) !important;
            text-decoration-color:var(--accent) !important; text-decoration-thickness:2px !important; }

  /* Links de acción: pastilla con fondo índigo suave; se ve que se puede pulsar. */
  a.link-action, .link-action { display:inline-flex !important; align-items:center; gap:.4em;
        padding:.34em .72em !important; border-radius:9px;
        background:var(--accent-soft); color:var(--accent) !important; font-weight:640 !important;
        text-decoration:none !important; border:1px solid rgba(91,98,214,.20);
        line-height:1.2; transition:background .15s, border-color .15s, color .15s, transform .15s; }
  a.link-action:hover, .link-action:hover { background:#e1e3fa; border-color:rgba(91,98,214,.38);
        color:var(--accent-d) !important; transform:translateY(-1px); }

  .card-cta { color:var(--accent); font-weight:650; letter-spacing:-.005em;
              display:inline-block; transition:transform .16s ease, color .16s ease; }
  .q-card:hover .card-cta { transform:translateX(3px); color:var(--accent-d); }

  .chip-ok   { color:var(--ok)   !important; }
  .chip-warm { color:var(--warm) !important; }
  .chip-hot  { color:var(--hot)  !important; }
  .chip-cold { color:var(--cold) !important; }

  .q-header { box-shadow:0 1px 0 var(--border), 0 1px 8px rgba(16,17,26,.03) !important; }

  .q-btn { font-weight:600 !important; border-radius:9px !important; text-transform:none !important; }
  .q-btn.bg-primary, .q-btn--standard.text-white {
    background:linear-gradient(135deg, var(--accent), var(--accent-d)) !important;
    box-shadow:0 1px 2px rgba(69,77,191,.35) !important; }
  .q-field__control { border-radius:9px !important; }
  ::selection { background:var(--accent-soft); }

  /* Markdown (respuestas del chat, documentos): sin esto un '### fecha' se pinta casi
     como el título de la página y rompe la jerarquía. */
  .nicegui-markdown h1, .q-markdown h1 { font-size:1.45rem !important; font-weight:740 !important;
        color:var(--ink); line-height:1.25; margin:.2em 0 .4em; letter-spacing:-.015em; }
  .nicegui-markdown h2, .q-markdown h2 { font-size:1.2rem !important; font-weight:680 !important;
        color:var(--ink); margin:.9em 0 .35em; }
  .nicegui-markdown h3, .q-markdown h3 { font-size:1.05rem !important; font-weight:660 !important;
        color:var(--ink); margin:.85em 0 .3em; }
  .nicegui-markdown h4, .q-markdown h4 { font-size:.98rem !important; font-weight:640 !important;
        color:var(--body); margin:.7em 0 .25em; text-transform:uppercase; letter-spacing:.02em; }
  .nicegui-markdown p, .q-markdown p { margin:.45em 0; }
  .nicegui-markdown ul, .nicegui-markdown ol { margin:.4em 0; padding-left:1.3em; }
  .nicegui-markdown li { margin:.15em 0; }
  .nicegui-markdown hr { border:0; border-top:1px solid var(--border); margin:1em 0; }
</style>
"""


def _theme() -> None:
    # El color primary de Quasar también: los botones de NiceGUI usan 'primary', no las
    # clases bg-*, y sin esto salían azules pese al tema.
    ui.colors(primary="#5e6ad2", secondary="#5e6ad2", accent="#5e6ad2")
    ui.add_head_html(_THEME_CSS)
    ui.add_head_html(_QUASAR_LANG_JS)


def shell_header(subtitulo: str = "") -> None:
    """Barra superior común, con la barra lateral."""
    _theme()
    with ui.header(elevated=False).classes(
        "bg-white border-b border-gray-200 px-5 py-2 items-center justify-between"
    ):
        with ui.row().classes("items-center gap-2 cursor-pointer").on(
            "click", lambda: ui.navigate.to("/")
        ):
            ui.icon("hub").classes("text-indigo-500 text-2xl")
            ui.label("agent-platform").classes("text-lg font-semibold")
        if subtitulo:
            ui.label(subtitulo).classes("text-sm text-gray-500")
    _sidebar()


def _nav_item(label: str, icon: str, href: str) -> None:
    with ui.row().classes(
        "w-full items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100"
    ).on("click", lambda h=href: ui.navigate.to(h)):
        ui.icon(icon).classes("text-gray-500 text-xl")
        ui.label(label).classes("text-sm font-medium")


def _sidebar() -> None:
    with ui.left_drawer(fixed=True).props("width=248 bordered").classes(
        "bg-white border-r border-gray-200 p-3 gap-1"
    ):
        _nav_item("Inicio", "home", "/")
        ui.label("TUS SISTEMAS").classes(
            "text-xs font-semibold text-gray-400 tracking-wide mt-4 mb-1 px-3"
        )
        for s in systems.find():
            _nav_item(s.label, s.icon or "folder", f"/sistema/{s.slug}")


def cuantos_documentos(sistema) -> int:
    """Cuántos documentos tiene la biblioteca de este sistema."""
    from core import espacio

    return sum(len(v) for v in espacio.documents(sistema.slug).values())


def _reloj(segundos: int) -> str:
    """Lo que lleva corriendo, al segundo."""
    return f"{segundos}s" if segundos < 60 else f"{segundos // 60}m {segundos % 60:02d}s"


def _plazo(segundos: int) -> str:
    """Un plazo aproximado. En minutos, salvo que no llegue a uno: redondear a minutos
    por debajo del minuto da «0 min», que no dice nada."""
    return f"{segundos} s" if segundos < 60 else f"{round(segundos / 60)} min"


def panel_esperando(
    texto: str, *, tipico_s: int | None = None, techo_s: int | None = None
) -> ui.row:
    """Espera larga con reloj: dice cuánto lleva y si eso es normal.

    Un spinner mudo delante de una llamada de minutos no distingue «está trabajando» de
    «esto está muerto», y quien mira acaba suponiendo lo segundo. El contador es la
    diferencia.

    Los dos plazos son distintos y hacen falta los dos. ``tipico_s`` es lo que tarda cuando
    va bien —lo que se anuncia de entrada— y ``techo_s`` el peor caso antes de rendirse, que
    solo se menciona al pasarse del primero: anunciar el techo desde el principio asusta sin
    informar, y callarlo cuando la espera se alarga deja de nuevo la duda de si sigue vivo.

    Sin plazos, solo cuenta: para lo que no tiene duración conocida.

    Devuelve la fila para que quien la creó la borre al terminar (el ``ui.timer`` muere
    con ella).
    """
    fila = ui.row().classes("items-center gap-2")
    with fila:
        ui.spinner(size="sm")
        marca = ui.label().classes("text-gray-500 text-sm")

    transcurrido = {"s": 0}

    def _tic() -> None:
        transcurrido["s"] += 1
        s = transcurrido["s"]
        if tipico_s is None:
            marca.set_text(f"{texto} · {_reloj(s)}")
        elif s <= tipico_s:
            marca.set_text(f"{texto} · {_reloj(s)} (suele tardar {_plazo(tipico_s)})")
        else:
            limite = f" (se rinde a los {_plazo(techo_s)})" if techo_s else ""
            marca.set_text(f"{texto} · {_reloj(s)} · va lento, sigue intentándolo{limite}")

    _tic()
    with fila:
        ui.timer(1.0, _tic)
    return fila


#: Lo que se dice cuando el fallo viene del modelo, que es el caso frecuente en una
#: llamada larga. No sirve para un fallo nuestro: ahí reintentar no arregla nada.
SUGERENCIA_MODELO = (
    "No se ha perdido nada de lo que ya tenías. Casi siempre es saturación pasajera del "
    "modelo: reintentar en un momento suele bastar."
)


def panel_error(
    mensaje: str, *, reintentar=None, titulo: str = "No he podido terminar",
    sugerencia: str = SUGERENCIA_MODELO,
) -> None:
    """El error de una llamada larga, como panel que SE QUEDA.

    Estaba como aviso flotante de cinco segundos. Tras esperar minutos delante de la
    pantalla nadie llega a leerlo, la vista vuelve al principio y el resultado es una app
    que «no hace nada» sin decir por qué. Un fallo que costó tiempo tiene que dejar rastro,
    y el camino de vuelta —reintentar— tiene que estar ahí mismo.
    """
    with ui.card().classes("w-full p-5 gap-2 border-l-4 border-red-400"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("error_outline").classes("text-red-500")
            ui.label(titulo).classes("text-lg font-semibold")
        if sugerencia:
            ui.label(sugerencia).classes("text-sm text-gray-600")
        ui.label(mensaje).classes(
            "text-xs text-gray-500 bg-gray-50 rounded p-2 w-full break-words"
        )
        if reintentar is not None:
            ui.button("Reintentar", icon="refresh", on_click=reintentar).classes("self-start")


#: Un icono por tipo de aviso. Si aparece un tipo nuevo sin icono, el test lo dice: una
#: fila sin icono en una lista de avisos parece un fallo de carga.
ICONOS = {
    "jerga": "translate",
    "nombre": "badge",
    "sin-uso": "hourglass_empty",
    "antiguo": "schedule",
}


def pintar_lista(hallazgos: list, *, vacio: str) -> None:
    """Los avisos, o el hueco dicho con todas las letras.

    Que no haya nada es un resultado, no una pantalla a medio cargar: si no se dice, quien
    mira se queda sin saber si es que no hay o es que falló.
    """
    if not hallazgos:
        ui.label(vacio).classes("text-sm text-gray-600 zona-avisos")
        return
    with ui.column().classes("w-full gap-2 zona-avisos"):
        for h in hallazgos:
            _fila(h)


def _fila(h) -> None:
    with ui.card().classes("w-full p-4 gap-1"), ui.row().classes(
        "items-start gap-3 flex-nowrap"
    ):
        ui.icon(ICONOS.get(h.tipo, "help_outline")).classes("text-indigo-600 mt-0.5")
        with ui.column().classes("gap-0 min-w-0"):
            ui.label(h.texto).classes("text-sm leading-snug")
            ui.label(h.propuesta).classes("text-xs text-gray-500 leading-snug")
            if h.donde:
                ui.link("Ir allí →", h.donde).classes("text-xs link-action")
