"""Configuración de tests.

CRÍTICO: fijamos AGENT_DATA_PATH a un directorio temporal ANTES de importar
sistemas.networking.config, para que los tests no toquen los datos reales de data/.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="agente-networking-test-"))
os.environ["AGENT_DATA_PATH"] = str(_TMP)

# Espacio de prueba: la biblioteca y la identidad de networking viven DENTRO del sistema,
# así que aislar los tests es apuntar la raíz de sistemas a un temporal. Antes se apuntaba
# la biblioteca común; sin traducirlo, estos tests escribirían en la carpeta real.
_SISTEMAS = Path(tempfile.mkdtemp(prefix="agente-networking-sistemas-"))
# Y los datos del sistema, que ya no viven junto al código (mis-datos/ o datos-ejemplo/):
# sin esto, la configuración apuntaría a tus datos reales.
os.environ["AGENT_DATOS_NETWORKING"] = str(_SISTEMAS / "networking")


@pytest.fixture(autouse=True)
def _espacio_de_prueba(monkeypatch):
    monkeypatch.setenv("AGENT_PLATFORM_SISTEMAS", str(_SISTEMAS))
    monkeypatch.setenv("AGENT_DATOS_NETWORKING", str(_SISTEMAS / "networking"))


_CANDIDATOS_MD = """# Candidatos

# Lista completa por categoría

## 1. Categoría test

| # | Nombre | Rol actual | LinkedIn | Conexión contigo | Valor | Confidence |
|---|---|---|---|---|---|---|
| 1 | Ana Test | Head of AI — ACME | linkedin.com/in/ana | ex-colega | muy valiosa | confirmed |
| 2 | Beto Test | Lead — BBVA | (búsqueda directa) | alumni | medio | inferred |
"""


def _crear_fixtures_estaticos() -> None:
    # La identidad (perfil/narrativa/estilo/objetivos) vive en `identidad/`, dentro del
    # propio sistema: puedes querer una voz distinta en cada uno (D8). Aquí se crean los
    # datos de trabajo de networking y su biblioteca de prueba.
    docs = {
        "pendientes.md": "# Pendientes\n\n- [ ] algo\n",
        "candidatos.md": _CANDIDATOS_MD,
    }
    for nombre, contenido in docs.items():
        (_TMP / nombre).write_text(contenido, encoding="utf-8")

    plantillas = _TMP / "plantillas"
    plantillas.mkdir(exist_ok=True)
    for nombre in (
        "primer-contacto", "dormant-tie-reactivation", "follow-up",
        "post-cafe", "post-entrevista", "comentario-publico",
    ):
        (plantillas / f"{nombre}.md").write_text(
            f"# Guía: {nombre}\n\nPrincipios de la guía de {nombre}.\n", encoding="utf-8"
        )

    investigacion = _SISTEMAS / "networking" / "biblioteca" / "investigacion"
    investigacion.mkdir(parents=True, exist_ok=True)
    (investigacion / "01-fundamentos.md").write_text(
        "# Fundamentos\n\nGranovetter, weak ties.\n", encoding="utf-8"
    )
    propio = _SISTEMAS / "networking" / "identidad"
    propio.mkdir(parents=True, exist_ok=True)
    # Los tests de prompts comprueban que tu perfil llega al prompt: antes lo leían de tu
    # perfil REAL y dependían de tus datos sin decirlo.
    (propio / "profile.md").write_text(
        "# Perfil\n\nAna Prueba — Arquitecta de IA (prueba).\n", encoding="utf-8"
    )
    (_TMP / "contactos").mkdir(exist_ok=True)


_crear_fixtures_estaticos()


@pytest.fixture
def reset_data() -> Path:
    """Deja contactos/ vacío y candidatos.md en estado conocido antes del test."""
    contactos = _TMP / "contactos"
    if contactos.exists():
        shutil.rmtree(contactos)
    contactos.mkdir(parents=True, exist_ok=True)
    (_TMP / "candidatos.md").write_text(_CANDIDATOS_MD, encoding="utf-8")
    return _TMP
