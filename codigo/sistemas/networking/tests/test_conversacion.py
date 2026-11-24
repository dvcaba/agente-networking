from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from sistemas.networking.storage import conversacion as conv
from sistemas.networking.storage.contactos import (
    Contacto,
    NuevoContactoInput,
    create_contacto,
    get_contacto,
)

HOY = date(2026, 10, 13)


def _c(slug: str, historico: list[tuple[int, str, str]], **kw) -> Contacto:
    """Contacto con histórico: (hace cuántos días, título, contenido)."""
    partes = [f"### {(HOY - timedelta(days=d)).isoformat()} — {t}\n\n{x}" for d, t, x in historico]
    return Contacto(slug=slug, nombre=f"{slug.title()} Apellido", path=Path("/x"),
                    historico_raw="\n\n".join(partes), **kw)


# --- Quién habla ---

def test_quien_habla_por_titulo():
    assert conv.quien_habla("Respondió") == "el"
    assert conv.quien_habla("Respondí") == "yo"
    assert conv.quien_habla("Primer mensaje enviado") == "yo"
    assert conv.quien_habla("Follow-up enviado") == "yo"
    assert conv.quien_habla("Café / llamada") == "nota"
    assert conv.quien_habla("Creado") == "nota"


# --- En qué punto está ---

def test_sin_empezar_si_solo_esta_creado():
    s = conv.situacion(_c("a", [(10, "Creado", "")], creado_fecha=HOY - timedelta(days=10)), HOY)
    assert (s.estado, s.dias) == ("sin_empezar", 10)
    assert conv.modo_para(s) == "primer"


def test_te_toca_si_lo_ultimo_es_suyo():
    s = conv.situacion(_c("a", [(5, "Primer mensaje enviado", "hola"), (1, "Respondió", "qué tal")]), HOY)
    assert s.estado == "te_toca"
    assert conv.modo_para(s) == "continuar"


def test_esperando_si_lo_ultimo_es_mio():
    s = conv.situacion(_c("a", [(4, "Primer mensaje enviado", "hola")]), HOY)
    assert (s.estado, s.dias) == ("esperando", 4)
    assert conv.modo_para(s) == "follow_up"


def test_dejar_respirar_tras_tres_mensajes_sin_respuesta():
    h = [(12, "Primer mensaje enviado", "a"), (7, "Follow-up enviado", "b"), (2, "Follow-up enviado", "c")]
    assert conv.situacion(_c("a", h), HOY).estado == "dejar_respirar"


def test_se_enfria_tras_dos_semanas():
    s = conv.situacion(_c("a", [(30, "Respondí", "x"), (21, "Café / llamada", "bien")]), HOY)
    assert (s.estado, s.dias) == ("se_enfria", 21)


def test_reactivar_si_hace_mucho():
    s = conv.situacion(_c("a", [(200, "Café / llamada", "")]), HOY)
    assert conv.modo_para(s) == "reactivacion"


def test_al_dia_tras_un_cafe_reciente():
    assert conv.situacion(_c("a", [(2, "Café / llamada", "")]), HOY).estado == "al_dia"


# --- Avisos ---

def test_avisos_en_orden_y_con_frases(reset_data):
    cs = [
        _c("frio", [(20, "Respondí", "x")]),
        _c("espera", [(5, "Primer mensaje enviado", "hola")]),
        _c("toca", [(3, "Primer mensaje enviado", "hola"), (1, "Respondió", "¿hablamos el jueves?")]),
        _c("reciente", [(1, "Primer mensaje enviado", "hola")]),
    ]
    avisos = conv.avisos(cs, HOY)
    assert [a.slug for a in avisos] == ["toca", "espera", "frio"]
    assert [a.tipo for a in avisos] == ["responder", "recordatorio", "enfria"]
    assert avisos[0].texto == "Toca te ha contestado. Te toca responder."
    assert avisos[0].detalle == "¿hablamos el jueves?"
    assert avisos[1].modo == "follow_up"


def test_avisos_sin_tope_y_gente_nueva_desde_el_primer_dia(reset_data):
    cs = [_c(f"e{i}", [(5, "Primer mensaje enviado", "h")]) for i in range(8)]
    cs += [_c("nuevo", [(0, "Creado", "")])]
    avisos = conv.avisos(cs, HOY)
    assert len(avisos) == 9
    assert avisos[-1].tipo == "empezar" and avisos[-1].slug == "nuevo"


def test_posponer_y_silenciar(reset_data):
    cs = [_c("frio", [(20, "Respondí", "x")]), _c("espera", [(5, "Primer mensaje enviado", "h")])]
    conv.posponer("frio", HOY)
    conv.silenciar("espera")
    assert conv.avisos(cs, HOY) == []
    # Pospuesto vuelve al día siguiente; silenciado no.
    assert [a.slug for a in conv.avisos(cs, HOY + timedelta(days=1))] == ["frio"]


def test_archivados_y_descartados_no_aparecen():
    cs = [_c("a", [(5, "Primer mensaje enviado", "h")], archivado=True),
          _c("b", [(5, "Primer mensaje enviado", "h")], estado_relacion="descartado")]
    assert conv.ordenar(cs, HOY) == []


def test_progreso_del_mes():
    cs = [_c("a", [(3, "Primer mensaje enviado", ""), (1, "Respondió", ""), (0, "Café / llamada", "")]),
          _c("b", [(40, "Primer mensaje enviado", "")])]  # el mes pasado no cuenta
    assert conv.progreso_mes(cs, HOY) == (1, 1, 1)


# --- Lo que se escribe en la ficha ---

def test_registrar_cambia_historico_y_estado(reset_data):
    create_contacto(NuevoContactoInput(nombre="Marc Keller", estado_relacion="identificado"),
                    today=HOY - timedelta(days=3))
    conv.registrar_enviado("marc-keller", "primer", "Hola Marc", HOY - timedelta(days=2))
    c = get_contacto("marc-keller")
    assert c.estado_relacion == "contactado"
    assert conv.situacion(c, HOY).estado == "esperando"

    conv.registrar_respuesta("marc-keller", "Claro, el jueves", HOY)
    c = get_contacto("marc-keller")
    assert c.estado_relacion == "en conversación"
    s = conv.situacion(c, HOY)
    assert s.estado == "te_toca" and s.ultima.contenido == "Claro, el jueves"


# --- Lo que devuelve Claude ---

_RESPUESTA = """## Diagnóstico
- **Tipo de respuesta detectado**: acepta llamada

### Opción 1 — Directo
**Por qué este ángulo:** cierra fecha.
**Mensaje:**
> Hola Marc, el jueves me va bien.
> ¿A las 16:00?

### Opción 2 — Breve
**Por qué este ángulo:** deja que elija.
**Mensaje:**
> Perfecto. Te leo.

---
"""


def test_parse_borradores():
    intro, ops = conv.parse_borradores(_RESPUESTA)
    assert "acepta llamada" in intro
    assert [o.etiqueta for o in ops] == ["Directo", "Breve"]
    assert ops[0].mensaje == "Hola Marc, el jueves me va bien.\n¿A las 16:00?"
    assert ops[0].porque == "cierra fecha."
    assert ops[1].mensaje == "Perfecto. Te leo."


def test_parse_sin_opciones_devuelve_el_texto():
    intro, ops = conv.parse_borradores("Aún es pronto para insistir: dale hasta el jueves.")
    assert ops == [] and intro.startswith("Aún es pronto")
