"""Ejecutar un especialista o un proceso: la pantalla que sirve para cualquiera.

Dos modos, según si conversa:
- **conversación**: coach, «pregunta a tus fuentes»… hilo multi-turno que arrastra la
  sesión y enseña de dónde sale cada cosa.
- **formulario**: el resto. Los campos salen de lo que el especialista declara; la salida
  se pinta legible (tabla, texto, fuentes agrupadas) y el dato en bruto queda plegado.
"""

from __future__ import annotations

import json
from pathlib import Path

from nicegui import run, ui

from core import salidas, uso
from core.engine.agent_base import AgentSpec

from .shell import panel_esperando, shell_header


def render_runner(spec: AgentSpec, texto: str = "") -> None:
    """``texto`` viene de la caja «¿Qué necesitas?»: llega escrito, pero NO se ejecuta solo.
    Lanzar algo que tarda minutos sin que lo hayas pedido es peor que copiarlo a mano."""
    if spec.chat:
        _render_chat(spec, texto)
    else:
        _render_form(spec, texto)


# ============================================================= modo conversación
def _chat_field(spec: AgentSpec) -> str:
    """Nombre del input de texto del chat (el primer 'manual', o 'question')."""
    manuales = [f for f in (spec.inputs or []) if getattr(f, "source", "manual") == "manual"]
    return manuales[0].name if manuales else "question"


def _thinking_text(spec: AgentSpec) -> str:
    return "consultando tus fuentes…" if "rag" in spec.name else "pensando…"


def _render_chat(spec: AgentSpec, texto: str = "") -> None:
    shell_header(spec.display_title)
    render_chat_body(spec, texto)


def render_chat_body(spec: AgentSpec, texto: str = "") -> None:
    """Cuerpo del chat (sin cabecera), reutilizable bajo cualquier shell/sección."""
    field = _chat_field(spec)
    estado: dict = {"session_id": None}

    with ui.column().classes("w-full max-w-3xl mx-auto p-6 gap-3"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(spec.display_title).classes("text-3xl font-bold")
            nueva_btn = ui.button("Nueva conversación", icon="refresh").props("flat dense")
        ui.label(spec.description).classes("text-sm text-gray-600")

        hilo = ui.column().classes("w-full gap-3 mt-2")

        # Sugerencias de inicio (clicables) para que el usuario sepa qué pedir.
        sugerencias = ui.row().classes("w-full gap-2 flex-wrap")

        def _pintar_sugerencias() -> None:
            sugerencias.clear()
            if not spec.starters:
                return
            with sugerencias:
                ui.label("Prueba a preguntar:").classes("text-xs text-gray-500 w-full")
                for s in spec.starters:
                    ui.button(s, on_click=lambda s=s: _enviar(s)).props("outline dense").classes(
                        "text-xs normal-case"
                    )

        with ui.row().classes("w-full items-center gap-2"):
            caja = (
                ui.input(placeholder="Escribe tu mensaje…")
                .props("outlined dense")
                .classes("flex-grow")
            )
            enviar_btn = ui.button(icon="send").props("round").classes("bg-blue-600 text-white")
        if texto:
            caja.value = texto

        async def _enviar(texto: str | None = None) -> None:
            msg = (texto if texto is not None else (caja.value or "")).strip()
            if not msg:
                return
            caja.value = ""
            sugerencias.clear()  # tras el primer mensaje, fuera las sugerencias
            with hilo:
                _bubble(msg, mine=True)
                pensando = ui.row().classes("items-center gap-2")
                with pensando:
                    ui.spinner(size="sm")
                    ui.label(_thinking_text(spec)).classes("text-gray-500 text-sm")

            payload = {field: msg}
            if estado["session_id"]:
                payload["session_id"] = estado["session_id"]

            uso.registrar(spec.id)
            # Si el agente sabe emitir por trozos, lo pintamos token a token.
            if spec.stream is not None:
                await _stream_respuesta(spec, payload, hilo, pensando, estado)
                return

            try:
                out = await run.io_bound(spec.run, payload)
            except Exception as e:  # noqa: BLE001
                pensando.delete()
                with hilo:
                    _bubble(f"Error: {type(e).__name__}: {e}")
                return
            pensando.delete()
            if isinstance(out, dict) and out.get("session_id"):
                estado["session_id"] = out["session_id"]
            with hilo:
                _answer_bubble(out)
            # Las piezas simples se USAN conversando: si esto no se guardara, «cada
            # ejecución deja un documento» sería falso justo donde más se trabaja (D24).
            if isinstance(out, dict) and out.get("success"):
                await run.io_bound(salidas.guardar_conversacion, spec, msg,
                                   str(out.get("text") or ""),
                                   sesion=estado.get("session_id"))

        def _nueva() -> None:
            hilo.clear()
            estado["session_id"] = None
            _pintar_sugerencias()

        enviar_btn.on("click", _enviar)
        caja.on("keydown.enter", _enviar)
        nueva_btn.on("click", _nueva)
        _pintar_sugerencias()


async def _stream_respuesta(spec, payload: dict, hilo, pensando, estado: dict) -> None:
    """Consume ``spec.stream`` y va pintando la respuesta token a token en una burbuja."""
    out: dict = {}
    with hilo, ui.row().classes("w-full justify-start"):
        card = ui.card().classes("bg-gray-100 p-3 rounded-lg").style("max-width: 80%")
        with card:
            md = ui.markdown("")
    acc = ""
    primera = True
    try:
        async for chunk in spec.stream(payload, out):
            if primera:
                pensando.delete()  # llegó el primer trozo: fuera el "pensando…"
                primera = False
            acc += chunk
            md.set_content(acc)
    except Exception as e:  # noqa: BLE001 — nunca dejar el chat colgado
        out.setdefault("error", f"{type(e).__name__}: {e}")
    if primera:
        pensando.delete()  # no llegó ningún trozo
    if out.get("session_id"):
        estado["session_id"] = out["session_id"]
    if not acc:
        md.set_content(f"Error: {out.get('error')}" if out.get("error") else "(sin respuesta)")
    if out.get("sources"):
        with card:
            render_fuentes(out["sources"])
    # Aquí el texto no viene en `out`: es lo que se ha ido pintando. Sin esto, el camino
    # por el que de verdad responden los especialistas no dejaría rastro (D24).
    if acc:
        await run.io_bound(salidas.guardar_conversacion, spec,
                           str(payload.get(_chat_field(spec)) or ""), acc,
                           sesion=estado.get("session_id"))


def _bubble(text: str, *, mine: bool = False) -> None:
    align = "justify-end" if mine else "justify-start"
    color = "bg-blue-600 text-white" if mine else "bg-gray-100"
    with ui.row().classes(f"w-full {align}"):
        with ui.card().classes(f"{color} p-3 rounded-lg").style("max-width: 80%"):
            ui.markdown(text)


def _answer_bubble(out) -> None:
    if not isinstance(out, dict):
        _bubble(str(out))
        return
    texto = out.get("text")
    if not texto:
        texto = f"Error: {out.get('error')}" if out.get("error") else "(sin respuesta)"
    with ui.row().classes("w-full justify-start"):
        with ui.card().classes("bg-gray-100 p-3 rounded-lg").style("max-width: 80%"):
            ui.markdown(texto)
            if out.get("sources"):
                render_fuentes(out["sources"])


_TIPO_FUENTE = {"downloaded": "documento", "research": "investigación", "propio": "texto tuyo"}


def agrupar_fuentes(sources: list) -> list[dict]:
    """Una entrada por documento, con todas las citas que apuntan a él.

    El RAG numera por FRAGMENTO, no por documento: una respuesta citaba [1], [2] y [3] del
    mismo manual y la lista lo repetía tres veces, así que «Fuentes (6)» eran 3 documentos.
    La numeración no se toca —es la que usa el texto de la respuesta—; solo se agrupa al
    enseñarla.
    """
    grupos: dict[tuple[str, str], dict] = {}
    for s in sources:
        titulo = s.get("title") or s.get("source") or "fuente"
        url = s.get("url") or ""
        tipo = s.get("kind") or ""
        grupo = grupos.setdefault(
            (titulo, url),
            {"title": titulo, "url": url, "tipo": _TIPO_FUENTE.get(tipo, tipo), "citas": []},
        )
        grupo["citas"].append(s.get("n"))
    return list(grupos.values())


def render_fuentes(sources: list) -> None:
    """De dónde sale cada cosa, agrupado por documento."""
    grupos = agrupar_fuentes(sources)
    total = len(grupos)
    with ui.expansion(
        f"Fuentes · {total} documento{'' if total == 1 else 's'}"
    ).classes("w-full text-sm"):
        for g in grupos:
            etiqueta = "".join(f"[{c}]" for c in g["citas"]) + f" {g['title']}"
            if g["tipo"]:
                etiqueta += f" · {g['tipo']}"
            if g["url"]:
                ui.link(etiqueta, g["url"], new_tab=True).classes("text-xs")
            else:
                ui.label(etiqueta).classes("text-xs text-gray-600")


# ================================================================= modo formulario
def _render_form(spec: AgentSpec, texto: str = "") -> None:
    shell_header(spec.display_title)
    with ui.column().classes("w-full max-w-3xl mx-auto p-8 gap-4"):
        ui.label(spec.display_title).classes("text-3xl font-bold")
        ui.label(spec.description).classes("text-sm text-gray-600")

        campos: dict = {}
        libre = None
        # Solo se piden al usuario los inputs 'manual'; los 'agent'/'external' los
        # aporta un workflow u otra app (invocación programática).
        manuales = [f for f in (spec.inputs or []) if getattr(f, "source", "manual") == "manual"]
        if manuales:
            for i, f in enumerate(manuales):
                # Lo que escribiste en la caja va al primer campo: es el que describe qué
                # quieres (el activo, el tema, la pregunta).
                inicial = texto if (i == 0 and texto) else f.default
                campos[f.name] = (
                    ui.input(label=f.label, value=inicial, placeholder=f.help)
                    .props("outlined dense")
                    .classes("w-full")
                )
        elif spec.inputs is None:
            libre = (
                ui.textarea(
                    label="Argumentos (clave=valor por línea)",
                    placeholder="close=5000\nvol_pct=15",
                )
                .props("outlined")
                .classes("w-full")
            )

        salida = ui.column().classes("w-full gap-2 mt-2")

        async def _ejecutar() -> None:
            entrada: dict = {}
            if campos:
                entrada = {k: (w.value or "") for k, w in campos.items()}
            elif libre is not None:
                for linea in (libre.value or "").splitlines():
                    if "=" in linea:
                        k, v = linea.split("=", 1)
                        entrada[k.strip()] = v.strip()

            salida.clear()
            with salida:
                # Un workflow puede tardar diez minutos: con un spinner mudo no se distingue
                # «trabajando» de «colgado».
                espera = panel_esperando(
                    "Trabajando (los flujos de varios pasos tardan varios minutos)"
                )
            uso.registrar(spec.id)
            try:
                resultado = await run.io_bound(spec.run, entrada)
            except Exception as e:  # noqa: BLE001
                espera.delete()
                with salida:
                    ui.label(f"Error: {type(e).__name__}: {e}").classes("text-red-600")
                return
            espera.delete()
            etiquetas = {f.name: f.label for f in spec.inputs or []}
            _render_output(salida, resultado, etiquetas)

            # Lo que produce se guarda como documento, firmado por la pieza que lo hizo
            # (D24). Antes esto se pintaba aquí y se perdía al cerrar la pestaña.
            guardado = await run.io_bound(salidas.guardar, spec, entrada, resultado)
            if guardado is not None:
                with salida:
                    ui.label(f"Guardado en salidas/{guardado.name}").classes(
                        "text-xs text-gray-500")

        ui.button("Ejecutar", icon="play_arrow", on_click=_ejecutar).classes(
            "bg-blue-600 text-white"
        )


# Claves internas que no se vuelcan como JSON crudo. `steps` sigue aquí a propósito:
# ya no se esconde —tiene su propio bloque, «Cómo se ha hecho»—, pero volcarlo además
# como JSON sería enseñar lo mismo dos veces, una de ellas ilegible.
_INTERNAL = {"text", "success", "error", "session_id", "sources", "pending_developer", "steps"}


#: Las salidas de las herramientas son identificadores de código, en inglés. El runner es la
#: frontera donde se traducen: una calculadora cuyo valor entero es «dónde puede acabar el
#: precio» enseñaba un JSON con 'upper', 'lower' y 'prob_within'.
_GLOSARIO = {
    "upper": "Superior",
    "lower": "Inferior",
    "prob_within": "Probabilidad de quedar dentro",
    "levels": "Niveles",
    "sigma": "Desviación (σ)",
}


def etiqueta_campo(clave: str, etiquetas: dict[str, str]) -> str:
    """Nombre legible de un campo: la etiqueta que declaró el agente, el glosario, o la
    clave sin guiones bajos, por ese orden."""
    if clave in etiquetas:
        return etiquetas[clave]
    if clave in _GLOSARIO:
        return _GLOSARIO[clave]
    texto = clave.replace("_", " ").strip()
    return texto[:1].upper() + texto[1:]


def valor_legible(valor) -> str:
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, float):
        return f"{valor:.4f}".rstrip("0").rstrip(".")
    if isinstance(valor, (dict, list)):
        return json.dumps(valor, ensure_ascii=False, default=str)
    return str(valor)


def _texto_largo(valor) -> bool:
    return isinstance(valor, str) and ("\n" in valor or len(valor) > 160)


def _pintar_datos(datos: dict, etiquetas: dict[str, str]) -> None:
    """Una salida estructurada, como la leería una persona: pares nombre-valor, tablas para
    los dicts de dicts (los niveles ±1σ/±2σ/±3σ) y listas con viñetas."""
    cortos = {
        k: v for k, v in datos.items() if not isinstance(v, (dict, list)) and not _texto_largo(v)
    }
    if cortos:
        with ui.element("div").classes("grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm"):
            for k, v in cortos.items():
                ui.label(etiqueta_campo(k, etiquetas)).classes("text-gray-500")
                ui.label(valor_legible(v)).classes("font-medium")
    for k, v in datos.items():
        if _texto_largo(v):
            with ui.expansion(etiqueta_campo(k, etiquetas)).classes("w-full text-sm"):
                ui.code(v).classes("w-full")
        elif isinstance(v, dict) and v:
            ui.label(etiqueta_campo(k, etiquetas)).classes("text-sm font-semibold mt-1")
            if all(isinstance(x, dict) for x in v.values()):
                columnas = list(dict.fromkeys(c for x in v.values() for c in x))
                ui.table(
                    columns=[{"name": "_fila", "label": "", "field": "_fila", "align": "left"}]
                    + [{"name": c, "label": etiqueta_campo(c, etiquetas), "field": c}
                       for c in columnas],
                    rows=[{"_fila": fila, **{c: valor_legible(x.get(c, "")) for c in columnas}}
                          for fila, x in v.items()],
                    row_key="_fila",
                ).props("flat dense bordered").classes("w-full")
            else:
                _pintar_datos(v, etiquetas)
        elif isinstance(v, list) and v:
            ui.label(etiqueta_campo(k, etiquetas)).classes("text-sm font-semibold mt-1")
            for item in v:
                ui.label(f"· {valor_legible(item)}").classes("text-sm text-gray-700")


def _rastro(pasos: list) -> None:
    """Cómo se ha hecho: qué hizo cada paso de un proceso, cuánto tardó y qué sacó.

    Iba oculto, y con razón a medias: el rastro solo guardaba si cada paso había ido bien,
    así que no había casi nada que enseñar. Ahora que el motor registra lo que produjo cada
    uno, esconderlo sería pedirte que te fíes de un resultado sin poder ver de dónde sale.

    Va plegado: cuando el proceso ha ido bien, lo que quieres leer es su salida; el detalle
    está ahí para cuando quieras comprobarlo o algo no cuadre.
    """
    total = sum(p.get("segundos") or 0 for p in pasos if isinstance(p, dict))
    fallo = any(isinstance(p, dict) and p.get("ok") is False for p in pasos)
    titulo = (f"Cómo se ha hecho · {len(pasos)} pasos · {total:.0f}s"
              + (" · algo falló" if fallo else ""))
    with ui.expansion(titulo).classes("w-full text-sm rastro"):
        for i, paso in enumerate(pasos, 1):
            if not isinstance(paso, dict):
                continue
            ok = paso.get("ok") is not False
            with ui.row().classes("items-start gap-2 flex-nowrap w-full border-t pt-2"):
                ui.icon("check_circle" if ok else "error_outline").classes(
                    f"text-base mt-0.5 {'text-green-600' if ok else 'text-red-500'}")
                with ui.column().classes("gap-0 min-w-0 w-full"):
                    nombre = paso.get("titulo") or paso.get("agent") or "?"
                    ui.label(f"{i}. {nombre} · {paso.get('segundos', 0)} s").classes(
                        "text-sm font-medium leading-snug")
                    if paso.get("error"):
                        ui.label(str(paso["error"])).classes("text-xs text-red-600")
                    if paso.get("texto"):
                        ui.label(str(paso["texto"])).classes(
                            "text-xs text-gray-600 whitespace-pre-wrap break-words")
                    detalles = []
                    if paso.get("fuentes"):
                        detalles.append(f"citó {paso['fuentes']} fuentes")
                    if paso.get("claves"):
                        detalles.append("devolvió: " + ", ".join(paso["claves"]))
                    if detalles:
                        ui.label(" · ".join(detalles)).classes("text-xs text-gray-500")


def _render_output(container, resultado, etiquetas: dict[str, str] | None = None) -> None:
    with container:
        if not isinstance(resultado, dict):
            ui.markdown(str(resultado))
            return

        if resultado.get("pending_developer"):
            ui.badge("⏳ pendiente de programador").classes("bg-amber-500 text-white")

        if resultado.get("success") is False or resultado.get("error"):
            ui.label(f"Error: {resultado.get('error')}").classes("text-red-600")
            if not resultado.get("text"):
                return

        if resultado.get("text"):
            with ui.card().classes("w-full p-4"):
                ui.markdown(resultado["text"])

        if resultado.get("sources"):
            render_fuentes(resultado["sources"])

        if resultado.get("steps"):
            _rastro(resultado["steps"])

        # Versiones de contenido (LinkedIn / Substack)
        versiones = {k: v for k, v in resultado.items() if k.endswith("_version") and v}
        if versiones:
            with ui.tabs().classes("w-full") as tabs:
                for k in versiones:
                    ui.tab(k.replace("_version", ""))
            with ui.tab_panels(tabs, value=next(iter(versiones)).replace("_version", "")).classes(
                "w-full"
            ):
                for k, v in versiones.items():
                    with ui.tab_panel(k.replace("_version", "")):
                        ui.markdown(v)

        # Rutas de archivos generados
        for k, v in resultado.items():
            if k.endswith("_path") and v:
                ui.label(f"{k}: {v}").classes("text-xs text-gray-500")
                p = Path(str(v))
                archivo = p if p.suffix else None
                if archivo is None and p.is_dir():
                    mds = sorted(p.glob("*.md"))
                    archivo = mds[0] if mds else None
                if archivo and archivo.exists():
                    with ui.expansion(f"Ver {archivo.name}").classes("w-full"):
                        ui.markdown(archivo.read_text(encoding="utf-8"))

        # Resto: JSON (calculadoras como sigma-cone, listas del designer…)
        resto = {
            k: v
            for k, v in resultado.items()
            if k not in _INTERNAL and not k.endswith("_version") and not k.endswith("_path")
        }
        if resto:
            with ui.card().classes("w-full p-4 gap-3"):
                _pintar_datos(resto, etiquetas or {})
                with ui.expansion("Ver los datos en bruto").classes("w-full text-xs text-gray-500"):
                    ui.code(json.dumps(resto, ensure_ascii=False, indent=2, default=str)).classes(
                        "w-full"
                    )
