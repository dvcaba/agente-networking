from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from sistemas.networking.storage import contactos as C


def test_slugify():
    assert C.slugify("Ana López Gómez") == "ana-lopez-gomez"
    assert C.slugify("José  María") == "jose-maria"


def test_parse_tier():
    assert C._parse_tier("3") == 3
    assert C._parse_tier("Tier 2 — medio") == 2
    assert C._parse_tier(None) is None
    assert C._parse_tier("sin numero") is None


def test_parse_salidas():
    assert C._parse_salidas("empleo, amistad") == ["empleo", "amistad"]
    assert C._parse_salidas("") == []
    assert C._parse_salidas(None) == []


def test_normalize_estado():
    assert C._normalize_estado("Contactado") == "contactado"
    assert C._normalize_estado("en conversación activa") == "en conversación"
    assert C._normalize_estado("xyz") is None


def test_normalize_temperatura():
    assert C._normalize_temperatura("caliente") == "caliente"
    assert C._normalize_temperatura("frío / tibio") == "frío"
    assert C._normalize_temperatura(None) == "desconocido"


def test_create_parse_roundtrip(reset_data):
    inp = C.NuevoContactoInput(
        nombre="Ana López", empresa="ACME", rol="Head of AI",
        tipo_contacto="Ex-colega", temperatura="tibio", tier=1,
        estado_relacion="contactado", salidas=["empleo", "amistad"],
        proxima_accion="reactivar", proxima_fecha="2026-06-01",
    )
    path = C.create_contacto(inp, today=date(2026, 5, 27))
    c = C.parse_contacto(path)
    assert c.nombre == "Ana López"
    assert c.empresa == "ACME"
    assert c.tier == 1
    assert c.estado_relacion == "contactado"
    assert c.salidas == ["empleo", "amistad"]
    assert c.temperatura == "tibio"
    assert c.proxima_fecha == date(2026, 6, 1)


def test_list_skips_meta_y_readme(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Uno"))
    (reset_data / "contactos" / "_meta.md").write_text("# meta\n", encoding="utf-8")
    (reset_data / "contactos" / "README.md").write_text("# readme\n", encoding="utf-8")
    slugs = {c.slug for c in C.list_contactos()}
    assert "uno" in slugs
    assert "_meta" not in slugs and "readme" not in slugs
    assert len(slugs) == 1


def test_create_duplicate_raises(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Dup"))
    with pytest.raises(C.ContactoExistenteError):
        C.create_contacto(C.NuevoContactoInput(nombre="Dup"))


def test_append_interaccion(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Hist"))
    C.append_interaccion("hist", date(2026, 5, 27), "Respondió", "dijo hola 987")
    c = C.get_contacto("hist")
    assert "Respondió" in c.historico_raw and "dijo hola 987" in c.historico_raw


def test_set_archivado(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Arch"))
    C.set_archivado("arch", True)
    assert C.get_contacto("arch").archivado is True
    C.set_archivado("arch", False)
    assert C.get_contacto("arch").archivado is False


def test_update_preserva_historico(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Upd", rol="X"))
    C.append_interaccion("upd", date(2026, 5, 27), "Nota", "contenido unico 123")
    C.update_contacto("upd", C.EditContactoInput(rol="Y", temperatura="caliente"))
    c = C.get_contacto("upd")
    assert c.rol == "Y"
    assert c.temperatura == "caliente"
    assert "contenido unico 123" in c.historico_raw


def test_esta_incompleto():
    inc = C.Contacto(slug="x", nombre="X", path=Path("/x"))
    assert C.esta_incompleto(inc) is True
    comp = C.Contacto(
        slug="y", nombre="Y", path=Path("/y"), empresa="ACME", conexion="ex-colega"
    )
    assert C.esta_incompleto(comp) is False


def test_borrar(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Del"))
    C.borrar_contacto("del")
    with pytest.raises(C.ContactoNoEncontradoError):
        C.get_contacto("del")


def test_buscar_contactos(reset_data):
    C.create_contacto(C.NuevoContactoInput(nombre="Carlos Pérez", empresa="BBVA"))
    C.create_contacto(C.NuevoContactoInput(nombre="Marta Ruiz", empresa="Santander"))
    assert {c.slug for c in C.buscar_contactos("bbva")} == {"carlos-perez"}
    assert {c.slug for c in C.buscar_contactos("perez")} == {"carlos-perez"}
