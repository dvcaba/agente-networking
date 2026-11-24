"""La relación con cada contacto vista como una conversación: quién habló el último, a quién
le toca, y qué merece un aviso hoy.

Todo sale del histórico que ya guarda cada ficha (``### AAAA-MM-DD — Título``). No hay un
segundo almacén de mensajes: si editas la ficha a mano, la conversación cambia igual.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from sistemas.networking.config import DATA_PATH
from sistemas.networking.storage.contactos import (
    Contacto,
    _parse_date,
    append_interaccion,
    get_contacto,
    normalize_text,
    set_estado_relacion,
)

Quien = Literal["yo", "el", "nota"]
Estado = Literal["te_toca", "esperando", "dejar_respirar", "se_enfria", "al_dia", "sin_empezar"]
Modo = Literal["primer", "continuar", "follow_up", "reactivacion"]

#: Días sin hablar a partir de los cuales una relación se enfría.
DIAS_ENFRIA = 14
#: Desde cuándo un silencio merece recordatorio (CLAUDE.md, regla 12: 3-7 días).
DIAS_RECORDATORIO = 3
#: Mensajes seguidos sin respuesta (el primero + 2 recordatorios) tras los que se deja respirar.
MAX_SEGUIDOS = 3
#: Más allá de esto, retomar es reactivar un contacto dormido, no un recordatorio.
DIAS_REACTIVAR = 90

#: Cada tipo de aviso tiene su apartado en Inicio, en este orden y sin tope: que haya
#: muchos seguimientos no debe esconder a la gente nueva, ni al revés.
SECCIONES: dict[str, str] = {
    "responder": "Te han contestado",
    "plan": "Tenías apuntado",
    "recordatorio": "Esperan un recordatorio",
    "enfria": "Se están enfriando",
    "empezar": "Gente nueva por escribir",
}

# Cómo se reconoce quién habla a partir del título de la entrada. Los títulos los ponen las
# pantallas de la app («Primer mensaje enviado», «Respondió», «Respondí»…) o tú a mano.
_DEL_CONTACTO = ("respondio", "contesto", "me escribio", "me respondio", "recibido", "su respuesta")
_MIOS = ("enviado", "envie", "respondi", "le escribi", "comente", "mi respuesta")


@dataclass
class Entrada:
    fecha: date
    titulo: str
    contenido: str
    quien: Quien


@dataclass
class Situacion:
    estado: Estado
    dias: int
    ultima: Entrada | None


@dataclass
class Aviso:
    slug: str
    tipo: Literal["responder", "plan", "recordatorio", "enfria", "empezar"]
    texto: str
    detalle: str
    boton: str
    modo: Modo
    puede_silenciar: bool = False


def quien_habla(titulo: str) -> Quien:
    t = normalize_text(titulo)
    if any(t.startswith(m) or f" {m}" in t for m in _DEL_CONTACTO):
        return "el"
    if any(m in t for m in _MIOS):
        return "yo"
    return "nota"


def entradas(c: Contacto) -> list[Entrada]:
    """El histórico de la ficha, en orden de fecha (estable para el mismo día)."""
    trozos = re.split(r"^###\s+", c.historico_raw or "", flags=re.MULTILINE)
    out: list[Entrada] = []
    for trozo in trozos[1:]:
        cabecera, _, cuerpo = trozo.partition("\n")
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s*(?:[—-]\s*(.*))?$", cabecera.strip())
        if not m:
            continue
        fecha = _parse_date(m.group(1))
        if not fecha:
            continue
        titulo = (m.group(2) or "").strip()
        out.append(Entrada(fecha, titulo, cuerpo.strip(), quien_habla(titulo)))
    return sorted(out, key=lambda e: e.fecha)


def _es_alta(e: Entrada) -> bool:
    return normalize_text(e.titulo).startswith("creado")


def situacion(c: Contacto, hoy: date) -> Situacion:
    todas = entradas(c)
    eventos = [e for e in todas if not _es_alta(e)]
    if not eventos:
        desde = c.creado_fecha or hoy
        return Situacion("sin_empezar", (hoy - desde).days, None)

    ultima = eventos[-1]
    dias = (hoy - ultima.fecha).days
    if ultima.quien == "el":
        return Situacion("te_toca", dias, ultima)
    if ultima.quien == "yo":
        seguidos = 0
        for e in reversed(eventos):
            if e.quien != "yo":
                break
            seguidos += 1
        if seguidos >= MAX_SEGUIDOS:
            return Situacion("dejar_respirar", dias, ultima)
    if dias >= DIAS_ENFRIA:
        return Situacion("se_enfria", dias, ultima)
    if ultima.quien == "yo":
        return Situacion("esperando", dias, ultima)
    return Situacion("al_dia", dias, ultima)


def modo_para(s: Situacion) -> Modo:
    """Qué mensaje toca preparar según en qué punto está la conversación."""
    if s.estado == "sin_empezar":
        return "primer"
    if s.estado in ("te_toca", "al_dia"):
        return "continuar"
    if s.estado == "se_enfria" and s.dias >= DIAS_REACTIVAR:
        return "reactivacion"
    return "follow_up"


def _dias_txt(n: int) -> str:
    return "1 día" if n == 1 else f"{n} días"


def etiqueta(s: Situacion) -> str:
    """El estado en palabras, para la lista de conversaciones."""
    if s.estado == "te_toca":
        return "Te toca responder"
    if s.estado == "esperando":
        return "Esperando su respuesta · " + ("desde hoy" if s.dias == 0 else _dias_txt(s.dias))
    if s.estado == "dejar_respirar":
        return "Sin respuesta · mejor dejar respirar"
    if s.estado == "se_enfria":
        return f"Se enfría · {_dias_txt(s.dias)} sin hablar"
    if s.estado == "al_dia":
        return "Al día"
    return "Sin empezar"


def _nombre_corto(c: Contacto) -> str:
    return c.nombre.split()[0] if c.nombre.strip() else c.slug


def _resumen(texto: str, n: int = 110) -> str:
    plano = " ".join(texto.split())
    return plano if len(plano) <= n else plano[: n - 1].rstrip() + "…"


# --- Avisos pospuestos o silenciados ------------------------------------------------------
# Un JSON aparte (no .md) para que posponer un aviso no recargue las pantallas abiertas.

def _avisos_path():
    return DATA_PATH / "avisos.json"


def _leer_pausas() -> dict[str, str]:
    try:
        return json.loads(_avisos_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _guardar_pausas(pausas: dict[str, str]) -> None:
    _avisos_path().write_text(json.dumps(pausas, ensure_ascii=False, indent=2), encoding="utf-8")


def posponer(slug: str, hoy: date) -> None:
    pausas = _leer_pausas()
    pausas[slug] = (hoy + timedelta(days=1)).isoformat()
    _guardar_pausas(pausas)


def silenciar(slug: str) -> None:
    pausas = _leer_pausas()
    pausas[slug] = "nunca"
    _guardar_pausas(pausas)


def _reactivar_avisos(slug: str) -> None:
    pausas = _leer_pausas()
    if pausas.pop(slug, None) is not None:
        _guardar_pausas(pausas)


def _en_pausa(slug: str, hoy: date, pausas: dict[str, str]) -> bool:
    valor = pausas.get(slug)
    if not valor:
        return False
    if valor == "nunca":
        return True
    hasta = _parse_date(valor)
    return bool(hasta and hasta > hoy)


def visibles(contactos: list[Contacto]) -> list[Contacto]:
    return [c for c in contactos if not c.archivado and c.estado_relacion != "descartado"]


_ORDEN = {"te_toca": 0, "se_enfria": 1, "esperando": 2, "sin_empezar": 3,
          "al_dia": 4, "dejar_respirar": 5}


def ordenar(contactos: list[Contacto], hoy: date) -> list[tuple[Contacto, Situacion]]:
    """Primero quien te necesita; dentro de cada grupo, quien lleva más tiempo esperando."""
    pares = [(c, situacion(c, hoy)) for c in visibles(contactos)]
    return sorted(pares, key=lambda p: (_ORDEN[p[1].estado], -p[1].dias))


def avisos(contactos: list[Contacto], hoy: date) -> list[Aviso]:
    pausas = _leer_pausas()
    grupos: dict[str, list[tuple[int, Aviso]]] = {k: [] for k in SECCIONES}
    for c in visibles(contactos):
        if _en_pausa(c.slug, hoy, pausas):
            continue
        s = situacion(c, hoy)
        nombre = _nombre_corto(c)
        if s.estado == "te_toca" and s.ultima:
            grupos["responder"].append((s.dias, Aviso(
                c.slug, "responder", f"{nombre} te ha contestado. Te toca responder.",
                _resumen(s.ultima.contenido) or "Abre la conversación para verlo.",
                "Responder", "continuar")))
        elif c.proxima_fecha and c.proxima_fecha <= hoy and c.proxima_accion:
            grupos["plan"].append(((hoy - c.proxima_fecha).days, Aviso(
                c.slug, "plan", f"Con {nombre} tenías apuntado: {c.proxima_accion}",
                "Era para hoy." if c.proxima_fecha == hoy
                else f"Era para hace {_dias_txt((hoy - c.proxima_fecha).days)}.",
                "Abrir", modo_para(s))))
        elif s.estado == "esperando" and s.dias >= DIAS_RECORDATORIO:
            grupos["recordatorio"].append((s.dias, Aviso(
                c.slug, "recordatorio", f"{nombre} no contesta desde hace {_dias_txt(s.dias)}.",
                "Buen momento para un recordatorio corto.", "Preparar recordatorio", "follow_up")))
        elif s.estado == "se_enfria":
            grupos["enfria"].append((s.dias, Aviso(
                c.slug, "enfria", f"Con {nombre} la relación se está enfriando.",
                f"{_dias_txt(s.dias)} sin hablar.", "Escribirle", modo_para(s),
                puede_silenciar=True)))
        elif s.estado == "sin_empezar":
            grupos["empezar"].append((s.dias, Aviso(
                c.slug, "empezar",
                f"Aún no le has escrito a {nombre}." if s.dias < 1
                else f"{nombre} lleva {_dias_txt(s.dias)} en tus contactos sin que le escribas.",
                " · ".join(x for x in (c.rol, c.empresa) if x) or "Aún no le has escrito.",
                "Primer mensaje", "primer", puede_silenciar=True)))
    out: list[Aviso] = []
    for grupo in grupos.values():
        out.extend(a for _, a in sorted(grupo, key=lambda p: -p[0]))
    return out


def progreso_mes(contactos: list[Contacto], hoy: date) -> tuple[int, int, int]:
    """(primeros mensajes, respuestas recibidas, cafés o llamadas) en el mes en curso."""
    primeros = respuestas = encuentros = 0
    for c in contactos:
        for e in entradas(c):
            if (e.fecha.year, e.fecha.month) != (hoy.year, hoy.month):
                continue
            t = normalize_text(e.titulo)
            if "primer mensaje" in t:
                primeros += 1
            elif e.quien == "el":
                respuestas += 1
            elif any(k in t for k in ("cafe", "llamada", "reunion", "videollamada")):
                encuentros += 1
    return primeros, respuestas, encuentros


# --- Lo que la pantalla escribe en la ficha ------------------------------------------------

_TITULO_ENVIADO: dict[Modo, str] = {
    "primer": "Primer mensaje enviado",
    "follow_up": "Follow-up enviado",
    "reactivacion": "Mensaje de reactivación enviado",
    "continuar": "Respondí",
}


def registrar_enviado(slug: str, modo: Modo, texto: str, hoy: date) -> None:
    append_interaccion(slug, hoy, _TITULO_ENVIADO[modo], texto)
    if get_contacto(slug).estado_relacion in (None, "identificado"):
        set_estado_relacion(slug, "contactado")
    _reactivar_avisos(slug)


def registrar_respuesta(slug: str, texto: str, hoy: date) -> None:
    append_interaccion(slug, hoy, "Respondió", texto)
    if get_contacto(slug).estado_relacion in (None, "identificado", "contactado", "latente", "dormido"):
        set_estado_relacion(slug, "en conversación")
    _reactivar_avisos(slug)


def registrar_encuentro(slug: str, fecha: date, notas: str) -> None:
    append_interaccion(slug, fecha, "Café / llamada", notas)
    if get_contacto(slug).estado_relacion != "en conversación":
        set_estado_relacion(slug, "en conversación")
    _reactivar_avisos(slug)


# --- Lo que devuelve Claude, en tarjetas ---------------------------------------------------

@dataclass
class Borrador:
    etiqueta: str
    porque: str
    mensaje: str


_OPCION = re.compile(r"^#{2,4}\s*Opci[oó]n\s*\d+\s*(?:[—–:-]\s*(.*))?$", re.MULTILINE)


def parse_borradores(texto: str) -> tuple[str, list[Borrador]]:
    """Separa la respuesta de Claude en (lo que dice antes, las opciones de mensaje).

    Si el formato no se reconoce, no hay opciones y todo va en el primer valor: la pantalla
    lo enseña tal cual en vez de perderlo.
    """
    marcas = list(_OPCION.finditer(texto))
    if not marcas:
        return texto.strip(), []
    intro = texto[: marcas[0].start()].strip()
    out: list[Borrador] = []
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        bloque = texto[m.end():fin]
        porque_m = re.search(r"\*\*Por qu[eé][^*]*\*\*:?\s*(.+)", bloque)
        porque = porque_m.group(1).strip() if porque_m else ""
        _, _, tras = bloque.partition("**Mensaje:**")
        cuerpo = tras if tras else bloque
        citas = [re.sub(r"^>\s?", "", ln) for ln in cuerpo.splitlines() if ln.lstrip().startswith(">")]
        mensaje = "\n".join(citas).strip() if citas else cuerpo.strip()
        # Un separador o un comentario final tras el mensaje no forman parte de él.
        mensaje = re.split(r"\n-{3,}\s*$", mensaje, flags=re.MULTILINE)[0].strip()
        if mensaje:
            out.append(Borrador((m.group(1) or f"Opción {i + 1}").strip(), porque, mensaje))
    return intro, out
