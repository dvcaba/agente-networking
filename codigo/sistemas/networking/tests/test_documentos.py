from __future__ import annotations

import pytest

from sistemas.networking.storage import documentos as D


def test_estrategia_docs():
    relpaths = {d.relpath for d in D.estrategia_docs()}
    # Tu perfil vive en la biblioteca («Sobre mí»), con nombres en inglés.
    assert "profile.md" in relpaths
    # El resto de docs de estrategia siguen en los documentos de networking.
    assert "pendientes.md" in relpaths


def test_biblioteca_docs():
    """La biblioteca de Networking, sin temas por medio: la ruta es la del sistema."""
    docs = D.biblioteca_docs()
    rels = {d.relpath for d in docs}
    assert "biblioteca/investigacion/01-fundamentos.md" in rels
    assert any(r.startswith("plantillas/") for r in rels)
    assert "investigación" in {d.grupo for d in docs}


def test_un_documento_de_la_biblioteca_se_lee():
    texto = D.read_doc("biblioteca/investigacion/01-fundamentos.md")
    assert "Granovetter" in texto


def test_el_perfil_se_lee_de_la_identidad_del_sistema():
    assert "Arquitecta de IA (prueba)" in D.read_doc("profile.md")


def test_read_write():
    D.write_doc("_test_doc.md", "# Test\n\ncontenido escrito por test 42\n")
    assert "contenido escrito por test 42" in D.read_doc("_test_doc.md")


def test_path_traversal_blocked():
    with pytest.raises(ValueError):
        D.read_doc("../../etc/passwd")
    with pytest.raises(ValueError):
        D.write_doc("../escape.md", "x")
    with pytest.raises(ValueError):
        D.read_doc("biblioteca/../../etc/passwd")
