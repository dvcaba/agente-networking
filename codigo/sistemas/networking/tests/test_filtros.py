from __future__ import annotations

from pathlib import Path

from sistemas.networking.storage.contactos import Contacto
from sistemas.networking.ui import contactos_listado as L


def _c(slug: str, **kw) -> Contacto:
    return Contacto(slug=slug, nombre=slug.upper(), path=Path("/x"), **kw)


# --- Filtros del listado ---

def test_filtro_tier():
    cs = [_c("a", tier=1), _c("b", tier=3)]
    assert {c.slug for c in L._aplicar_filtros(cs, L.FiltrosListado(tiers=[1]))} == {"a"}


def test_filtro_estado():
    cs = [_c("a", estado_relacion="contactado"), _c("b", estado_relacion="dormido")]
    out = L._aplicar_filtros(cs, L.FiltrosListado(estados=["contactado"]))
    assert {c.slug for c in out} == {"a"}


def test_filtro_salidas_al_menos_una():
    cs = [_c("a", salidas=["empleo", "amistad"]), _c("b", salidas=["conocimiento"])]
    out = L._aplicar_filtros(cs, L.FiltrosListado(salidas=["amistad"]))
    assert {c.slug for c in out} == {"a"}


def test_archivados_excluidos_por_defecto():
    cs = [_c("a"), _c("b", archivado=True)]
    assert {c.slug for c in L._aplicar_filtros(cs, L.FiltrosListado())} == {"a"}
    todos = L._aplicar_filtros(cs, L.FiltrosListado(incluir_archivados=True))
    assert {c.slug for c in todos} == {"a", "b"}


def test_grupo_key():
    assert L._grupo_key(_c("a", tier=1), "Prioridad") == "1 · Alta (trato cercano)"
    assert L._grupo_key(_c("b", estado_relacion="dormido"), "Estado") == "dormido"
    assert L._grupo_key(_c("c"), "Prioridad") == "Sin prioridad"
