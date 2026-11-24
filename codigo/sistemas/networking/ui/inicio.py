"""Inicio: lo que toca hoy arriba, por apartados, y tus conversaciones debajo, como un chat.

Sustituye al antiguo panel de contadores. La pantalla se lee en frases («Marc te ha
contestado») en vez de en cifras, y la conversación es a la vez el histórico y el redactor:
pegas lo que te contestan, el agente propone la respuesta y, al marcarla como enviada,
queda apuntada en la ficha. La lógica vive en ``storage/conversacion.py``.
"""

from __future__ import annotations

import html
import json
from datetime import date

from nicegui import ui

from apps.web.shell import panel_error, panel_esperando
from sistemas.networking.bridge.claude_bridge import invoke_claude
from sistemas.networking.bridge.prompts import (
    prompt_continuar_conversacion,
    prompt_follow_up,
    prompt_primer_mensaje,
    prompt_reactivacion_dormant_tie,
)
from sistemas.networking.storage import conversacion as conv
from sistemas.networking.storage.candidatos import (
    Candidato,
    candidato_slug,
    candidato_to_prefill,
    list_candidatos,
)
from sistemas.networking.storage.contactos import (
    Contacto,
    ContactoNoEncontradoError,
    get_contacto,
    list_contactos,
)
from sistemas.networking.storage.watcher import get_version
from sistemas.networking.ui.layout import header
from sistemas.networking.ui.nuevo import open_nuevo_dialog
from sistemas.networking.ui.redactor import open_redactor_comentario

_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
_AVATAR = ("#5b62d6", "#0f9d6b", "#c2700a", "#3b7bdb", "#9b4fc2", "#d0567a")
_TEMPERATURA = {
    "caliente": ("var(--hot)", "Relación caliente"),
    "tibio": ("var(--warm)", "Relación tibia"),
    "frío": ("var(--cold)", "Relación fría"),
    "desconocido": ("#9aa0ad", "Temperatura sin marcar"),
}
_ICONO_AVISO = {
    "responder": ("reply", "ok"),
    "plan": ("event", "accent"),
    "recordatorio": ("schedule", "warm"),
    "enfria": ("ac_unit", "cold"),
    "empezar": ("person_add", "accent"),
}
_CHIP = {
    "te_toca": "ok", "esperando": "warm", "dejar_respirar": "muted",
    "se_enfria": "cold", "al_dia": "muted", "sin_empezar": "muted",
}
_BOTON_PREPARAR = {
    "primer": "Prepárame el primer mensaje",
    "continuar": "Prepárame una respuesta",
    "follow_up": "Prepárame un recordatorio",
    "reactivacion": "Prepárame un mensaje para retomar",
}
_PROMPT = {
    "primer": prompt_primer_mensaje,
    "continuar": prompt_continuar_conversacion,
    "follow_up": prompt_follow_up,
    "reactivacion": prompt_reactivacion_dormant_tie,
}

_CSS = """
.ini-chip{display:inline-block;font-size:.72rem;font-weight:700;padding:1px 8px;border-radius:99px;margin-top:3px}
.ini-chip.ok{background:var(--ok-soft);color:var(--ok)}
.ini-chip.warm{background:var(--warm-soft);color:var(--warm)}
.ini-chip.cold{background:var(--cold-soft);color:var(--cold)}
.ini-chip.muted{background:#eef0f5;color:#5d6473}
.ini-ico{width:30px;height:30px;border-radius:8px;display:grid;place-items:center;flex:0 0 30px}
.ini-ico.ok{background:var(--ok-soft);color:var(--ok)}
.ini-ico.warm{background:var(--warm-soft);color:var(--warm)}
.ini-ico.cold{background:var(--cold-soft);color:var(--cold)}
.ini-ico.accent{background:var(--accent-soft);color:var(--accent)}
.ini-av{width:42px;height:42px;border-radius:50%;display:grid;place-items:center;color:#fff;
        font-weight:700;font-size:.85rem;position:relative;flex:0 0 42px}
.ini-av i{position:absolute;right:-1px;bottom:-1px;width:13px;height:13px;border-radius:50%;border:2px solid #fff}
.ini-conv{cursor:pointer;border-bottom:1px solid var(--border)}
.ini-conv:hover{background:#f6f7fa}
.ini-conv.sel{background:var(--accent-soft)}
.ini-seccion .q-item{padding:0;min-height:28px}
.ini-seccion .q-expansion-item__content{padding-top:.4rem}
.ini-ellipsis{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ini-yo{align-self:flex-end;background:var(--accent);color:#fff;border-radius:14px 14px 4px 14px}
.ini-el{align-self:flex-start;background:#fff;border:1px solid var(--border);border-radius:14px 14px 14px 4px}
.ini-msg{max-width:min(600px,85%);padding:.55rem .85rem;white-space:pre-wrap;overflow-wrap:anywhere;font-size:.95rem;line-height:1.45}
.ini-msg small{display:block;opacity:.72;font-size:.72rem;margin-top:.25rem}
.ini-dia{align-self:center;font-size:.75rem;color:#5d6473;background:#fff;border:1px solid var(--border);
         border-radius:99px;padding:1px 10px}
.ini-nota{align-self:center;text-align:center;max-width:520px;color:#5d6473;font-size:.85rem;font-style:italic;white-space:pre-wrap}
.ini-borrador{border:1px solid var(--border);border-radius:10px;padding:.7rem .85rem;background:#fff}
.ini-angulo{font-size:.72rem;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.05em}
.ini-grid{display:grid;grid-template-columns:var(--ini-ancho,440px) 6px minmax(0,1fr);width:100%}
.ini-tirador{cursor:col-resize;background:var(--border);transition:background .15s}
.ini-tirador:hover,.ini-tirador.activo{background:var(--accent)}
.ini-envuelve{white-space:normal;overflow-wrap:anywhere}
.ini-lado{height:calc(100vh - var(--ini-top,165px));overflow:auto;flex-wrap:nowrap}
.ini-panel{height:calc(100vh - var(--ini-top,165px));background:#eef0f5;min-width:0;flex-wrap:nowrap}
.ini-lado>*{flex-shrink:0}
.ini-solo-movil{display:none!important}
@media (max-width:767px){
  .ini-grid{grid-template-columns:minmax(0,1fr)}
  .ini-tirador{display:none}
  .ini-lado{height:auto;border-right:0}
  .ini-panel{height:calc(100vh - var(--ini-top,165px));min-height:70vh}
  .ini-grid.con-slug .ini-lado{display:none}
  .ini-grid:not(.con-slug) .ini-panel{display:none}
  .ini-solo-movil{display:inline-flex!important}
  .ini-solo-escritorio{display:none!important}
}
"""


def _fecha_corta(d: date | None, hoy: date) -> str:
    if not d:
        return ""
    if d == hoy:
        return "hoy"
    if (hoy - d).days == 1:
        return "ayer"
    return f"{d.day} {_MESES[d.month - 1]}"


def _n(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _iniciales(nombre: str) -> str:
    return "".join(p[0] for p in nombre.split()[:2]).upper() or "?"


def _avatar(c: Contacto) -> None:
    color = _AVATAR[sum(map(ord, c.slug)) % len(_AVATAR)]
    punto = _TEMPERATURA.get(c.temperatura, _TEMPERATURA["desconocido"])[0]
    ui.html(
        f'<div class="ini-av" style="background:{color}">{html.escape(_iniciales(c.nombre))}'
        f'<i style="background:{punto}"></i></div>'
    )


def _ultima_linea(c: Contacto) -> str:
    mensajes = [e for e in conv.entradas(c) if e.quien != "nota"]
    if not mensajes:
        return "Todavía no le has escrito"
    e = mensajes[-1]
    texto = " ".join((e.contenido or e.titulo).split())
    return ("Tú: " if e.quien == "yo" else "") + texto


def _copiar(texto: str) -> None:
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(texto)})")
    ui.notify("Copiado. Pégalo en LinkedIn.", type="positive")


_DE_TU_ENTORNO = {"Alumni / formación", "Ex-colega"}


def _candidatos_pendientes(contactos: list[Contacto]) -> list[Candidato]:
    """Candidatos que aún no has pasado a contactos y que son gente NUEVA.

    Los de tu entorno (compañeros de estudios, puentes) siguen en Candidatos, pero no son la
    base del networking: aquí no se proponen.
    """
    ya = {c.slug for c in contactos}
    return [c for c in list_candidatos()
            if candidato_slug(c) not in ya and c.tipo_contacto not in _DE_TU_ENTORNO]


def render_inicio(slug: str | None = None, preparar: str = "") -> None:
    ui.add_css(_CSS)
    # Sin la recarga automática del resto de pantallas: aquí un cambio en las fichas
    # refresca la lista y la conversación en sitio, sin perder una propuesta a medias.
    header("inicio", auto_refresh=False)
    ui.query(".nicegui-content").classes("p-0 gap-0")

    estado: dict = {"ocupado": False, "propuesta": None, "pegando": False, "visto": get_version()}

    def contacto_abierto() -> Contacto | None:
        if not slug:
            return None
        try:
            return get_contacto(slug)
        except ContactoNoEncontradoError:
            return None

    # --- Columna izquierda: para hoy + conversaciones ------------------------------------

    @ui.refreshable
    def lado() -> None:
        hoy = date.today()
        todos = list_contactos()
        pares = conv.ordenar(todos, hoy)
        avisos = conv.avisos(todos, hoy)
        primeros, respuestas, encuentros = conv.progreso_mes(todos, hoy)

        ui.label(
            f"Este mes: {_n(primeros, 'primer mensaje', 'primeros mensajes')} · "
            f"{_n(respuestas, 'respuesta', 'respuestas')} · "
            f"{_n(encuentros, 'café o llamada', 'cafés o llamadas')}"
        ).classes("text-xs text-gray-500")

        candidatos = _candidatos_pendientes(todos)
        if not pares and not candidatos:
            with ui.card().classes("w-full p-4 gap-2"):
                ui.label("Aún no tienes conversaciones").classes("font-semibold")
                ui.label(
                    "Empieza por Candidatos: elige a alguien y pásalo a tus contactos. "
                    "Aparecerá aquí y el agente te ayudará con el primer mensaje."
                ).classes("text-sm text-gray-600")
                ui.button(
                    "Ir a Candidatos", icon="how_to_reg",
                    on_click=lambda: ui.navigate.to("/networking/candidatos"),
                ).classes("self-start")
            return

        if not avisos and not candidatos:
            ui.label(
                "Nada pendiente por hoy. Te aviso aquí cuando alguien conteste o toque "
                "un recordatorio."
            ).classes("text-sm text-gray-600 border border-dashed border-gray-300 rounded-xl p-3")
        # Un apartado por tipo de aviso, sin tope; los vacíos no se enseñan.
        for tipo, titulo in conv.SECCIONES.items():
            del_tipo = [a for a in avisos if a.tipo == tipo]
            extra = candidatos if tipo == "empezar" else []
            if not del_tipo and not extra:
                continue
            with ui.expansion(value=True).classes("w-full ini-seccion") as sec:
                with sec.add_slot("header"), ui.row().classes(
                    "w-full items-baseline justify-between"
                ):
                    ui.label(titulo.upper()).classes(
                        "text-xs font-semibold text-gray-500 tracking-wide"
                    )
                    ui.label(str(len(del_tipo) + len(extra))).classes(
                        "text-xs font-semibold text-gray-500"
                    )
                with ui.column().classes("w-full gap-2"):
                    for a in del_tipo:
                        _tarjeta_aviso(a, hoy)
                    if extra:
                        if del_tipo:
                            ui.label("De tu lista de candidatos").classes(
                                "text-xs text-gray-500 mt-1"
                            )
                        with ui.card().classes("w-full p-0 gap-0 overflow-hidden"):
                            for cand in extra:
                                _fila_candidato(cand)

        if not pares:
            return
        ui.label("TUS CONVERSACIONES").classes(
            "text-xs font-semibold text-gray-500 tracking-wide mt-3"
        )
        with ui.card().classes("w-full p-0 gap-0 overflow-hidden"):
            for c, s in pares:
                _fila_conversacion(c, s, hoy)
        with ui.row().classes("gap-3 text-xs text-gray-500"):
            for color, txt in (("var(--hot)", "caliente"), ("var(--warm)", "tibia"),
                               ("var(--cold)", "fría"), ("#9aa0ad", "sin marcar")):
                ui.html(
                    f'<span><i style="display:inline-block;width:9px;height:9px;'
                    f'border-radius:50%;background:{color};margin-right:4px"></i>{txt}</span>'
                )

    def _tarjeta_aviso(a: conv.Aviso, hoy: date) -> None:
        icono, tono = _ICONO_AVISO[a.tipo]
        with ui.card().classes("w-full p-3 gap-2"):
            with ui.row().classes("items-start gap-3 flex-nowrap w-full"):
                ui.html(f'<div class="ini-ico {tono}"><span class="material-icons" '
                        f'style="font-size:18px">{icono}</span></div>')
                with ui.column().classes("gap-0 min-w-0"):
                    ui.label(a.texto).classes("text-sm font-semibold leading-snug")
                    ui.label(a.detalle).classes("text-xs text-gray-500 leading-snug")
            with ui.row().classes("gap-2 pl-10"):
                ui.button(
                    a.boton,
                    on_click=lambda a=a: ui.navigate.to(
                        f"/networking/conversacion/{a.slug}?preparar={a.modo}"
                    ),
                ).props("dense unelevated").classes("px-3")

                def _posponer(a=a) -> None:
                    conv.posponer(a.slug, hoy)
                    ui.notify("Vale, te lo vuelvo a enseñar mañana.")
                    lado.refresh()

                ui.button("Mañana", on_click=_posponer).props("dense flat")
                if a.puede_silenciar:
                    def _silenciar(a=a) -> None:
                        conv.silenciar(a.slug)
                        ui.notify("Entendido. No te avisaré más de este contacto.")
                        lado.refresh()

                    ui.button("Dejar estar", on_click=_silenciar).props("dense flat")

    def _fila_candidato(cand: Candidato) -> None:
        # Nombre y puesto completos, sin cortar: sin ellos la fila no sirve para decidir.
        with ui.column().classes("ini-conv w-full gap-0 px-3 py-2"):
            ui.label(cand.nombre).classes("text-sm font-semibold ini-envuelve")
            if cand.rol:
                ui.label(cand.rol).classes("text-xs text-gray-600 ini-envuelve")
            with ui.row().classes("items-center gap-3 mt-1"):
                ui.button(
                    "Pasar a contactos", icon="person_add",
                    on_click=lambda cand=cand: open_nuevo_dialog(prefill=candidato_to_prefill(cand)),
                ).props("dense flat no-caps").classes("px-1 text-xs")
                if cand.linkedin:
                    ui.link("LinkedIn ↗", cand.linkedin, new_tab=True).classes(
                        "text-xs text-indigo-600"
                    )

    def _fila_conversacion(c: Contacto, s: conv.Situacion, hoy: date) -> None:
        clases = "ini-conv w-full items-center gap-3 px-3 py-2 flex-nowrap"
        if c.slug == slug:
            clases += " sel"
        with ui.row().classes(clases).on(
            "click", lambda c=c: ui.navigate.to(f"/networking/conversacion/{c.slug}")
        ):
            _avatar(c)
            with ui.column().classes("gap-0 min-w-0 flex-1"):
                with ui.row().classes("w-full justify-between flex-nowrap gap-2"):
                    ui.label(c.nombre).classes("text-sm font-semibold ini-envuelve")
                    ui.label(_fecha_corta(s.ultima.fecha if s.ultima else None, hoy)).classes(
                        "text-xs text-gray-500 whitespace-nowrap"
                    )
                sub = " · ".join(x for x in (c.rol, c.empresa) if x)
                if sub:
                    ui.label(sub).classes("text-xs text-gray-500 ini-envuelve w-full")
                ui.label(_ultima_linea(c)).classes("text-xs ini-ellipsis w-full")
                ui.html(f'<span class="ini-chip {_CHIP[s.estado]}">{html.escape(conv.etiqueta(s))}</span>')

    # --- Columna derecha: la conversación abierta ----------------------------------------

    @ui.refreshable
    def panel() -> None:
        c = contacto_abierto()
        if c is None:
            with ui.column().classes("w-full h-full items-center justify-center p-8"):
                ui.icon("forum").classes("text-5xl text-gray-300")
                ui.label(
                    "No existe ese contacto." if slug else "Elige una conversación de la lista."
                ).classes("text-gray-500")
            return

        hoy = date.today()
        s = conv.situacion(c, hoy)
        modo = conv.modo_para(s)
        color, temp_txt = _TEMPERATURA.get(c.temperatura, _TEMPERATURA["desconocido"])

        with ui.row().classes(
            "w-full items-center gap-3 px-5 py-3 bg-white border-b border-gray-200 flex-nowrap"
        ):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/networking")).props(
                "flat round dense"
            ).classes("ini-solo-movil")
            _avatar(c)
            with ui.column().classes("gap-0 min-w-0 flex-1"):
                ui.label(c.nombre).classes("text-base font-semibold")
                sub = " · ".join(x for x in (c.rol, c.empresa, c.pais) if x)
                if sub:
                    ui.label(sub).classes("text-xs text-gray-500 ini-ellipsis")
            ui.html(f'<span class="ini-solo-escritorio" style="color:{color};font-size:.8rem;'
                    f'font-weight:600;white-space:nowrap">{temp_txt}</span>')
            ui.link("Ver ficha", f"/networking/contacto/{c.slug}").classes("text-sm link-action")

        area = ui.scroll_area().classes("flex-1 w-full")
        with area, ui.column().classes("w-full p-5 gap-2"):
            _hilo(c)
            if estado["ocupado"]:
                panel_esperando("El agente está leyendo la conversación y tu estilo",
                                tipico_s=45, techo_s=240)
            elif estado["propuesta"] and estado["propuesta"]["slug"] == c.slug:
                _propuesta(c)
        ui.timer(0.15, lambda: area.scroll_to(percent=1.0), once=True)

        with ui.column().classes("w-full gap-2 px-5 py-3 bg-white border-t border-gray-200"):
            if estado["pegando"]:
                ui.label(
                    "Pega lo que te ha contestado en LinkedIn. Queda guardado en la "
                    "conversación y el agente te propone respuestas."
                ).classes("text-xs text-gray-500")
                caja = ui.textarea(placeholder="Pega aquí su mensaje…").props(
                    "outlined autogrow"
                ).classes("w-full")

                async def _guardar_pegado() -> None:
                    texto = (caja.value or "").strip()
                    if not texto:
                        ui.notify("Pega primero lo que te ha contestado.", type="warning")
                        return
                    conv.registrar_respuesta(c.slug, texto, date.today())
                    estado["pegando"] = False
                    await _preparar(c.slug, "continuar")

                def _cancelar() -> None:
                    estado["pegando"] = False
                    panel.refresh()

                with ui.row().classes("gap-2"):
                    ui.button("Guardar y proponer respuesta", on_click=_guardar_pegado).props(
                        "unelevated"
                    )
                    ui.button("Cancelar", on_click=_cancelar).props("flat")
            else:
                def _abrir_pegado() -> None:
                    estado["pegando"] = True
                    panel.refresh()

                with ui.row().classes("gap-2 flex-wrap"):
                    ui.button("Pegar lo que me ha contestado", icon="content_paste",
                              on_click=_abrir_pegado).props("unelevated")
                    ui.button(_BOTON_PREPARAR[modo], icon="auto_awesome",
                              on_click=lambda: _preparar(c.slug, modo)).props("outline")
                    ui.button("Apuntar un café o llamada", icon="event",
                              on_click=lambda: _dialogo_encuentro(c)).props("flat")
                    ui.button("Comentar un post suyo", icon="chat_bubble_outline",
                              on_click=lambda: open_redactor_comentario(c)).props("flat")

    def _hilo(c: Contacto) -> None:
        hoy = date.today()
        dia_anterior = None
        todas = conv.entradas(c)
        if not [e for e in todas if e.quien != "nota"]:
            ui.label("Aún no le has escrito.").classes("ini-nota")
        for e in todas:
            if e.fecha != dia_anterior:
                ui.label(_fecha_corta(e.fecha, hoy)).classes("ini-dia")
                dia_anterior = e.fecha
            if e.quien == "nota":
                texto = ("Lo añadiste a tus contactos." if e.titulo.lower().startswith("creado")
                         else f"{e.titulo}\n{e.contenido}".strip())
                ui.label(texto).classes("ini-nota")
                continue
            with ui.element("div").classes(f"ini-msg ini-{e.quien}"):
                ui.label(e.contenido or e.titulo)
                ui.html(f"<small>{html.escape(e.titulo)}</small>")

    def _propuesta(c: Contacto) -> None:
        p = estado["propuesta"]
        if p.get("error"):
            panel_error(p["error"], reintentar=lambda: _preparar(c.slug, p["modo"]))
            return
        intro, opciones = conv.parse_borradores(p["texto"])
        with ui.card().classes("w-full p-4 gap-3"):
            if opciones:
                ui.label(
                    f"Te propongo {len(opciones)} versiones. Copia la que te guste, envíala tú "
                    "por LinkedIn y pulsa «Lo he enviado»."
                ).classes("text-sm text-gray-600")
            if intro:
                with ui.expansion("Lo que he tenido en cuenta" if opciones else "Respuesta del agente",
                                  value=not opciones).classes("w-full text-sm"):
                    ui.markdown(intro).classes("text-sm")
            for b in opciones:
                with ui.column().classes("ini-borrador w-full gap-1"):
                    ui.label(b.etiqueta).classes("ini-angulo")
                    if b.porque:
                        ui.label(b.porque).classes("text-xs text-gray-500")
                    ui.label(b.mensaje).classes("text-sm whitespace-pre-wrap")
                    with ui.row().classes("gap-2 mt-1"):
                        ui.button("Copiar", icon="content_copy",
                                  on_click=lambda b=b: _copiar(b.mensaje)).props("dense flat")

                        def _enviado(b=b) -> None:
                            conv.registrar_enviado(c.slug, p["modo"], b.mensaje, date.today())
                            estado["propuesta"] = None
                            ui.notify("Apuntado. Si no contesta en unos días, te aviso.",
                                      type="positive")
                            _refrescar()

                        ui.button("Lo he enviado", icon="check", on_click=_enviado).props(
                            "dense unelevated"
                        )
            with ui.row().classes("w-full gap-2 items-end flex-nowrap"):
                cambios = ui.input(placeholder="¿Algún cambio? Más corto, más formal, otro enfoque…").props(
                    "outlined dense"
                ).classes("flex-1")
                ui.button("Rehacer", on_click=lambda: _preparar(
                    c.slug, p["modo"], cambios=(cambios.value or "").strip()
                )).props("outline dense")
                ui.button("Descartar", on_click=_descartar).props("flat dense")

    def _descartar() -> None:
        estado["propuesta"] = None
        panel.refresh()

    async def _preparar(slug_c: str, modo: str, cambios: str = "") -> None:
        if estado["ocupado"]:
            return
        try:
            c = get_contacto(slug_c)
        except ContactoNoEncontradoError as e:
            ui.notify(str(e), type="negative")
            return
        previa = estado["propuesta"]
        sesion = previa.get("session_id") if (cambios and previa) else None
        prompt = cambios if sesion else _PROMPT[modo](c)
        estado["ocupado"] = True
        panel.refresh()
        try:
            r = await invoke_claude(prompt, session_id=sesion, timeout=240)
            estado["propuesta"] = {
                "slug": slug_c, "modo": modo, "texto": r.text, "session_id": r.session_id,
                "error": None if r.success else (r.error or "Respuesta vacía."),
            }
        except Exception as e:  # noqa: BLE001 — el fallo se enseña en pantalla, con reintentar
            estado["propuesta"] = {"slug": slug_c, "modo": modo, "texto": "",
                                   "session_id": None, "error": str(e)}
        finally:
            estado["ocupado"] = False
        _refrescar()

    def _dialogo_encuentro(c: Contacto) -> None:
        with ui.dialog() as d, ui.card().classes("w-[520px] max-w-[92vw] p-5 gap-3"):
            ui.label(f"Café o llamada con {c.nombre}").classes("text-lg font-semibold")
            fecha = ui.input("Fecha (AAAA-MM-DD)", value=date.today().isoformat()).classes("w-full")
            notas = ui.textarea("¿De qué hablasteis? ¿Quedasteis en algo?").props(
                "outlined autogrow"
            ).classes("w-full")

            def _guardar() -> None:
                try:
                    f = date.fromisoformat((fecha.value or "").strip())
                except ValueError:
                    ui.notify("Fecha inválida. Usa AAAA-MM-DD.", type="negative")
                    return
                conv.registrar_encuentro(c.slug, f, notas.value or "")
                d.close()
                ui.notify("Apuntado. Si quieres, pide ahora el mensaje de agradecimiento.",
                          type="positive")
                _refrescar()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=d.close).props("flat")
                ui.button("Guardar", on_click=_guardar).props("unelevated")
        d.open()

    def _refrescar() -> None:
        estado["visto"] = get_version()
        lado.refresh()
        panel.refresh()

    def _vigilar() -> None:
        # Cambios hechos fuera (editor, otra pestaña, la ficha): refrescar en sitio.
        if not estado["ocupado"] and get_version() != estado["visto"]:
            _refrescar()

    # --- Montaje ----------------------------------------------------------------------------

    # Las dos columnas con CSS propio (ver _CSS): las variantes responsive de Tailwind
    # (`md:…`) no se aplican en esta versión de NiceGUI y el panel acababa en la tira izquierda.
    with ui.element("div").classes("ini-grid" + (" con-slug" if slug else "")):
        with ui.column().classes("ini-lado gap-3 p-4"):
            lado()
        ui.element("div").classes("ini-tirador").props('title="Arrastra para ensanchar la lista"')
        with ui.column().classes("ini-panel gap-0"):
            panel()

    # Que las columnas ocupen justo lo que queda bajo la cabecera, mida lo que mida (la
    # barra de navegación cambia de alto según el ancho de la ventana).
    ui.run_javascript(
        "const g=document.querySelector('.ini-grid');"
        "if(g){const f=()=>document.documentElement.style.setProperty("
        "'--ini-top',g.getBoundingClientRect().top+window.scrollY+'px');"
        "f();window.addEventListener('resize',f);}"
    )
    # Ensanchar la lista arrastrando la línea que la separa de la conversación. El ancho se
    # recuerda en este navegador; si el navegador no deja guardarlo, se usa el de siempre.
    ui.run_javascript(
        "const r=document.documentElement.style;"
        "try{const w=localStorage.getItem('ini-ancho');if(w)r.setProperty('--ini-ancho',w+'px');}catch(e){}"
        "const t=document.querySelector('.ini-tirador'),g=document.querySelector('.ini-grid');"
        "if(t&&g){t.addEventListener('mousedown',ev=>{ev.preventDefault();t.classList.add('activo');"
        "const mover=e=>{const w=Math.max(300,Math.min(e.clientX-g.getBoundingClientRect().left,"
        "window.innerWidth-360));r.setProperty('--ini-ancho',w+'px');"
        "try{localStorage.setItem('ini-ancho',Math.round(w));}catch(err){}};"
        "const soltar=()=>{t.classList.remove('activo');document.removeEventListener('mousemove',mover);"
        "document.removeEventListener('mouseup',soltar);};"
        "document.addEventListener('mousemove',mover);document.addEventListener('mouseup',soltar);});}"
    )
    ui.timer(2.0, _vigilar)
    if slug and preparar in _PROMPT:
        ui.timer(0.3, lambda: _preparar(slug, preparar), once=True)
