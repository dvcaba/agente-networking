from __future__ import annotations

from sistemas.networking.storage import candidatos as K


def test_list_candidatos(reset_data):
    cands = K.list_candidatos()
    assert len(cands) == 2
    ana = next(c for c in cands if c.nombre == "Ana Test")
    assert ana.confidence == "confirmed"
    assert ana.linkedin == "https://linkedin.com/in/ana"


def test_prefill(reset_data):
    cands = K.list_candidatos()
    pf = K.candidato_to_prefill(cands[0])
    assert pf.nombre == "Ana Test"
    assert pf.estado_relacion == "identificado"
    assert pf.temperatura == "frío"


def test_normalize_url():
    assert K._normalize_url("linkedin.com/in/x") == "https://linkedin.com/in/x"
    assert K._normalize_url("(búsqueda directa)") == ""
    assert K._normalize_url("https://rocketreach.co/x") == "https://rocketreach.co/x"


def test_append_section_roundtrip(reset_data):
    before = len(K.list_candidatos())
    tabla = (
        "| # | Nombre | Rol actual | LinkedIn | Conexión contigo | Valor | Confidence |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 1 | Nuevo Uno | CEO — X | linkedin.com/in/n | búsqueda | valioso | confirmed |"
    )
    K.append_candidatos_section("Búsqueda test", tabla)
    after = K.list_candidatos()
    assert len(after) == before + 1
    assert any(c.nombre == "Nuevo Uno" for c in after)
