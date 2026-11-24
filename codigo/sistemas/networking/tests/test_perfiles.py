from __future__ import annotations

from sistemas.networking.storage import perfiles

_NOTA = """# Perfiles

### 1. Riesgo de modelos en banca — prioridad ALTA
- **Búsquedas para «Buscar gente»:**
  - `Head of Model Risk en Zúrich`
  - `AI risk en aseguradoras suizas`

### 2. Comunidades — prioridad ALTA
- **Búsquedas:**
  - `Organizadores de AI Tinkerers`
- texto normal con `código` que no es búsqueda
"""


def test_sin_nota_no_hay_busquedas():
    assert perfiles.busquedas() == [] or perfiles.ruta().exists()


def test_lee_las_busquedas_por_perfil():
    ruta = perfiles.ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(_NOTA, encoding="utf-8")
    try:
        bs = perfiles.busquedas()
        assert [b.texto for b in bs] == [
            "Head of Model Risk en Zúrich", "AI risk en aseguradoras suizas",
            "Organizadores de AI Tinkerers",
        ]
        assert bs[0].perfil == "Riesgo de modelos en banca — prioridad ALTA"
        assert bs[2].perfil == "Comunidades — prioridad ALTA"
    finally:
        ruta.unlink()
