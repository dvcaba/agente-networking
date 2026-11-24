from __future__ import annotations

from sistemas.networking.bridge import prompts as P
from sistemas.networking.storage.contactos import Contacto


def _contacto(tmp_path):
    p = tmp_path / "c.md"
    p.write_text("# Ana\n\n## Datos\n- **Empresa**: ACME\n", encoding="utf-8")
    return Contacto(slug="ana", nombre="Ana", path=p)


def test_prompt_primer_mensaje_incluye_contexto(tmp_path):
    out = P.prompt_primer_mensaje(_contacto(tmp_path))
    assert "Ana Prueba" in out  # de perfil.md (fixture)
    assert "PRIMER MENSAJE" in out


def test_prompt_reactivacion_usa_plantilla(tmp_path):
    out = P.prompt_reactivacion_dormant_tie(_contacto(tmp_path))
    assert "REACTIVACIÓN" in out
    assert "dormant-tie" in out  # nombre de la plantilla en el bloque


def test_prompt_comentario_standalone_inyecta_post():
    out = P.prompt_comentario_post_standalone("Post sobre DPIA en banca", "Autora X")
    assert "Post sobre DPIA en banca" in out
    assert "Autora X" in out


def test_prompt_comentario_standalone_sin_autor():
    out = P.prompt_comentario_post_standalone("Post Y")
    assert "No especificado" in out


def test_prompt_buscar_gente_incluye_query():
    out = P.prompt_buscar_gente("AI Risk en banca suiza")
    assert "AI Risk en banca suiza" in out
    assert "WebSearch" in out


def test_prompt_asistente_incluye_consulta_y_contexto():
    out = P.prompt_asistente("¿Qué hago hoy?")
    assert "¿Qué hago hoy?" in out
    assert "Ana Prueba" in out
