from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sistemas.networking.config import DATA_PATH
from sistemas.networking.storage.contactos import NuevoContactoInput, slugify

# Lista de candidatos identificados (gente del research, aún no son contactos).
_CANDIDATES_FILENAME = "candidatos.md"
_LISTA_MARKER = "# Lista completa por categoría"

# Mapeo categoría → tipo de contacto (taxonomía existente) + origen específico
# (de dónde conoces a la persona). El origen va al campo "conexión". Las categorías que
# añade «Buscar gente» (6, 7…) son gente nueva: sin origen fijo.
_CAT_TIPO: dict[str, str] = {
    "1": "Técnico empresa target",
    "2": "Alumni / formación",
    "3": "Alumni / formación",
    "4": "Alumni / formación",
    "5": "Ex-colega",
}
_CAT_ORIGEN: dict[str, str] = {
    "1": "Gente nueva — empresa/sector target (sin conexión previa)",
    "2": "Alumni — tu primera formación (máster, posgrado…)",
    "3": "Alumni — tu segunda formación",
    "4": "Alumni — tu tercera formación",
    "5": "Puente — antiguo compañero que ya está en otra empresa",
}


@dataclass
class Candidato:
    numero: str
    nombre: str
    rol: str
    linkedin: str
    conexion: str
    valor: str
    confidence: str
    categoria: str
    cat_num: str

    @property
    def origen(self) -> str:
        return _CAT_ORIGEN.get(self.cat_num, "")

    @property
    def tipo_contacto(self) -> str:
        return _CAT_TIPO.get(self.cat_num, "")


def candidates_path() -> Path:
    return DATA_PATH / _CANDIDATES_FILENAME


def _clean_cell(s: str) -> str:
    return s.replace("**", "").replace("`", "").strip()


def _normalize_url(s: str) -> str:
    s = _clean_cell(s)
    if not s or s.startswith("("):
        return ""
    if "linkedin.com" in s or "rocketreach" in s:
        return s if s.startswith("http") else f"https://{s}"
    if s.startswith("http"):
        return s
    return ""


def list_candidatos() -> list[Candidato]:
    path = candidates_path()
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")

    idx = text.find(_LISTA_MARKER)
    if idx == -1:
        return []
    body = text[idx + len(_LISTA_MARKER):]

    out: list[Candidato] = []
    # Cada sección de categoría arranca con "## N. <título>".
    sections = re.split(r"^##\s+", body, flags=re.MULTILINE)
    for sec in sections:
        header = re.match(r"(\d+)\.\s*(.+)", sec)
        if not header:
            continue
        cat_num = header.group(1)
        cat_title = header.group(2).splitlines()[0].strip()

        for line in sec.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            parts = line.split("|")
            if len(parts) < 9:  # 7 columnas → 9 trozos con bordes vacíos
                continue
            cells = [c.strip() for c in parts[1:-1]]
            if not re.fullmatch(r"\d+", cells[0]):
                continue  # fila cabecera o separador
            nombre = _clean_cell(cells[1])
            if not nombre:
                continue
            out.append(
                Candidato(
                    numero=cells[0],
                    nombre=nombre,
                    rol=_clean_cell(cells[2]),
                    linkedin=_normalize_url(cells[3]),
                    conexion=_clean_cell(cells[4]),
                    valor=_clean_cell(cells[5]),
                    confidence=_clean_cell(cells[6]).split("(")[0].strip(),
                    categoria=cat_title,
                    cat_num=cat_num,
                )
            )
    return out


def candidato_to_prefill(c: Candidato) -> NuevoContactoInput:
    conexion_parts = [p for p in (c.origen, c.conexion) if p]
    conexion = ". ".join(conexion_parts)
    contexto_parts = []
    if c.valor:
        contexto_parts.append(f"**Por qué es valioso**: {c.valor}")
    if c.confidence:
        contexto_parts.append(f"**Confidence de la conexión**: {c.confidence}")
    contexto_parts.append(f"**Categoría research**: {c.categoria}")
    return NuevoContactoInput(
        nombre=c.nombre,
        rol=c.rol,
        linkedin=c.linkedin,
        tipo_contacto=c.tipo_contacto,
        conexion=conexion,
        contexto="\n\n".join(contexto_parts),
        temperatura="frío",
        estado_relacion="identificado",
    )


def candidato_slug(c: Candidato) -> str:
    return slugify(c.nombre)


def append_candidatos_section(titulo: str, contenido_md: str) -> Path:
    """Añade una nueva sección numerada de candidatos (de una búsqueda) a candidatos.md.
    La app es quien escribe; el agente solo devuelve la tabla."""
    import re

    path = candidates_path()
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = "# Candidatos\n\n# Lista completa por categoría\n"

    if _LISTA_MARKER not in text:
        text = text.rstrip() + f"\n\n{_LISTA_MARKER}\n"

    nums = [int(m) for m in re.findall(r"^##\s+(\d+)\.", text, re.MULTILINE)]
    n = (max(nums) + 1) if nums else 1
    section = f"\n## {n}. {titulo}\n\n{contenido_md.strip()}\n"

    marker_acciones = "# Próximas acciones"
    idx = text.find(marker_acciones)
    if idx != -1:
        new_text = text[:idx].rstrip() + "\n" + section + "\n" + text[idx:]
    else:
        new_text = text.rstrip() + "\n" + section

    path.write_text(new_text, encoding="utf-8")
    return path
