from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

from sistemas.networking.config import DATA_PATH

Temperatura = Literal["frío", "tibio", "caliente", "desconocido"]

_TEMPERATURAS_VALIDAS: tuple[Temperatura, ...] = ("frío", "tibio", "caliente")
_TEMPERATURA_ALIAS = {
    "frio": "frío",
    "frío": "frío",
    "tibio": "tibio",
    "caliente": "caliente",
}


PAISES_PREDEFINIDOS: tuple[str, ...] = (
    "España",
    "Reino Unido",
    "Suiza",
    "USA",
    "Alemania",
    "Países Bajos",
    "Irlanda",
)

TIPOS_CONTACTO_PREDEFINIDOS: tuple[str, ...] = (
    "Recruiter / Headhunter",
    "Ex-colega",
    "Técnico empresa target",
    "Decision maker",
    "Alumni / formación",
    "Ecosistema (regulador / research / policy)",
)

# Campos del modelo conceptual (ver docs/modelo-conceptual.md).
# tier = profundidad de inversión (NO tope de cabezas).
TIERS: tuple[int, ...] = (1, 2, 3, 4)
TIER_LABELS: dict[int, str] = {
    1: "1 · Alta (trato cercano)",
    2: "2 · Media",
    3: "3 · Ligera (presencia ambiente)",
    4: "4 · En pausa",
}

# estado_relacion = lifecycle. Lo marcas tú a mano (sin umbral automático).
ESTADOS_RELACION: tuple[str, ...] = (
    "identificado",
    "contactado",
    "en conversación",
    "latente",
    "dormido",
    "descartado",
)

# salidas = lista ABIERTA (estas son sugerencias, se admite texto libre).
SALIDAS_PREDEFINIDAS: tuple[str, ...] = (
    "empleo",
    "colaboración / freelance",
    "co-fundar / montar algo",
    "conocimiento",
    "amistad",
    "relocalización",
    "intro a tercero",
)


@dataclass
class Contacto:
    slug: str
    nombre: str
    path: Path
    empresa: str | None = None
    rol: str | None = None
    pais: str | None = None
    tipo_contacto: str | None = None
    linkedin: str | None = None
    email: str | None = None
    conexion: str | None = None
    puntos_conexion: str | None = None
    contexto: str | None = None
    temperatura: Temperatura = "desconocido"
    tier: int | None = None
    estado_relacion: str | None = None
    salidas: list[str] = field(default_factory=list)
    proxima_accion: str | None = None
    proxima_fecha: date | None = None
    archivado: bool = False
    creado_fecha: date | None = None
    ultima_interaccion_fecha: date | None = None
    ultima_interaccion_titulo: str | None = None
    historico_raw: str = ""


def contactos_dir() -> Path:
    return DATA_PATH / "contactos"


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    hyphenated = re.sub(r"[\s_]+", "-", lowered)
    cleaned = re.sub(r"[^a-z0-9-]", "", hyphenated)
    return re.sub(r"-+", "-", cleaned).strip("-")


def normalize_text(s: str | None) -> str:
    if not s:
        return ""
    nf = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nf if not unicodedata.combining(c)).lower()


def buscar_contactos(query: str, limit: int = 8) -> list[Contacto]:
    q = normalize_text(query).strip()
    if len(q) < 2:
        return []
    out: list[Contacto] = []
    for c in list_contactos():
        if c.archivado:
            continue
        haystack = " ".join(
            normalize_text(x) for x in (c.nombre, c.empresa, c.rol, c.pais) if x
        )
        if q in haystack:
            out.append(c)
            if len(out) >= limit:
                break
    return out


def _normalize_temperatura(raw: str | None) -> Temperatura:
    if not raw:
        return "desconocido"
    cleaned = raw.strip().lower().split("/")[0].split()[0] if raw.strip() else ""
    return _TEMPERATURA_ALIAS.get(cleaned, "desconocido")


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


_BOOL_TRUE = {"sí", "si", "yes", "true", "1", "x"}


def _parse_bool(raw: str | None) -> bool:
    if not raw:
        return False
    return raw.strip().lower() in _BOOL_TRUE


def _parse_tier(raw: str | None) -> int | None:
    if not raw:
        return None
    match = re.search(r"[1-4]", raw)
    return int(match.group()) if match else None


def _parse_salidas(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _normalize_estado(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = raw.strip().lower()
    for e in ESTADOS_RELACION:
        if cleaned.startswith(e):
            return e
    return None


_FIELD_LINE = re.compile(r"^\s*[-*]\s*\*\*(?P<key>[^*]+?)\*\*\s*:\s*(?P<value>.*)$")


def _extract_section(text: str, header: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(header)}\s*$(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _extract_fields(section: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in section.splitlines():
        match = _FIELD_LINE.match(line)
        if match:
            key = match.group("key").strip().lower()
            value = match.group("value").strip()
            fields[key] = value
    return fields


def _history_entries(historico_section: str) -> list[tuple[date, str]]:
    if not historico_section:
        return []
    raw = re.findall(
        r"^###\s+(\d{4}-\d{2}-\d{2})\s*(?:[—-]\s*(.*))?$",
        historico_section,
        re.MULTILINE,
    )
    out: list[tuple[date, str]] = []
    for raw_date, title in raw:
        d = _parse_date(raw_date)
        if d:
            out.append((d, (title or "").strip()))
    return out


def _last_history_entry(historico_section: str) -> tuple[date | None, str | None]:
    entries = _history_entries(historico_section)
    if not entries:
        return None, None
    latest = max(entries, key=lambda e: e[0])
    return latest[0], (latest[1] or None)


def _first_history_entry(historico_section: str) -> date | None:
    entries = _history_entries(historico_section)
    if not entries:
        return None
    return min(entries, key=lambda e: e[0])[0]


def parse_contacto(path: Path) -> Contacto:
    text = path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    nombre = title_match.group(1).strip() if title_match else path.stem

    datos = _extract_fields(_extract_section(text, "Datos"))
    estado = _extract_fields(_extract_section(text, "Estado"))
    contexto_section = _extract_section(text, "Contexto pegado").strip() or None
    historico = _extract_section(text, "Histórico")
    last_date, last_title = _last_history_entry(historico)
    creado_date = _first_history_entry(historico)

    return Contacto(
        slug=path.stem,
        nombre=nombre,
        path=path,
        empresa=datos.get("empresa") or None,
        rol=datos.get("rol") or None,
        pais=datos.get("país") or None,
        tipo_contacto=datos.get("tipo de contacto") or None,
        linkedin=datos.get("linkedin") or None,
        email=datos.get("email") or None,
        conexion=datos.get("cómo le conocí / por qué le contacto") or None,
        puntos_conexion=datos.get("puntos de conexión") or None,
        contexto=contexto_section,
        temperatura=_normalize_temperatura(estado.get("temperatura")),
        tier=_parse_tier(estado.get("tier")),
        estado_relacion=_normalize_estado(
            estado.get("estado relación") or estado.get("estado relacion")
        ),
        salidas=_parse_salidas(estado.get("salidas")),
        proxima_accion=estado.get("próxima acción") or None,
        proxima_fecha=_parse_date(estado.get("próxima fecha")),
        archivado=_parse_bool(estado.get("archivado")),
        creado_fecha=creado_date,
        ultima_interaccion_fecha=last_date,
        ultima_interaccion_titulo=last_title,
        historico_raw=historico,
    )


def list_contactos() -> list[Contacto]:
    base = contactos_dir()
    if not base.exists():
        return []
    contactos: list[Contacto] = []
    for path in sorted(base.glob("*.md")):
        # Saltar README y archivos meta que empiezan por "_".
        if path.name.lower() == "readme.md" or path.name.startswith("_"):
            continue
        contactos.append(parse_contacto(path))
    return contactos


@dataclass
class NuevoContactoInput:
    nombre: str
    empresa: str = ""
    rol: str = ""
    pais: str = ""
    tipo_contacto: str = ""
    linkedin: str = ""
    email: str = ""
    conexion: str = ""
    puntos_conexion: str = ""
    contexto: str = ""
    temperatura: Temperatura = "frío"
    tier: int | None = None
    estado_relacion: str = ""
    salidas: list[str] = field(default_factory=list)
    proxima_accion: str = ""
    proxima_fecha: str = ""

    @property
    def slug(self) -> str:
        return slugify(self.nombre)


@dataclass
class EditContactoInput:
    empresa: str = ""
    rol: str = ""
    pais: str = ""
    tipo_contacto: str = ""
    linkedin: str = ""
    email: str = ""
    conexion: str = ""
    puntos_conexion: str = ""
    contexto: str = ""
    temperatura: Temperatura = "frío"
    tier: int | None = None
    estado_relacion: str = ""
    salidas: list[str] = field(default_factory=list)
    proxima_accion: str = ""
    proxima_fecha: str = ""


class ContactoExistenteError(Exception):
    pass


def _field_line(label: str, value: str) -> str:
    stripped = value.strip()
    return f"- **{label}**: {stripped}" if stripped else f"- **{label}**:"


def _render_template(data: NuevoContactoInput, hoy: date) -> str:
    lines = [
        f"# {data.nombre.strip()}",
        "",
        "## Datos",
        _field_line("Empresa", data.empresa),
        _field_line("Rol", data.rol),
        _field_line("País", data.pais),
        _field_line("Tipo de contacto", data.tipo_contacto),
        _field_line("LinkedIn", data.linkedin),
        _field_line("Email", data.email),
        _field_line("Cómo le conocí / por qué le contacto", data.conexion),
        _field_line("Puntos de conexión", data.puntos_conexion),
        "",
    ]
    contexto_stripped = data.contexto.strip()
    if contexto_stripped:
        lines.extend(["## Contexto pegado", "", contexto_stripped, ""])
    lines.extend(
        [
            "## Estado",
            _field_line("Temperatura", data.temperatura),
            _field_line("Tier", str(data.tier) if data.tier else ""),
            _field_line("Estado relación", data.estado_relacion),
            _field_line("Salidas", ", ".join(data.salidas)),
            _field_line("Próxima acción", data.proxima_accion),
            _field_line("Próxima fecha", data.proxima_fecha),
            _field_line("Archivado", "no"),
            "",
            "## Histórico",
            "",
            f"### {hoy.isoformat()} — Creado",
            "Contacto registrado, sin interacción aún.",
            "",
        ]
    )
    return "\n".join(lines)


def esta_incompleto(c: Contacto) -> bool:
    sin_actividad_clara = not c.empresa and not c.rol
    sin_motivo = not c.conexion
    return sin_actividad_clara or sin_motivo


def create_contacto(data: NuevoContactoInput, *, today: date | None = None) -> Path:
    if not data.nombre.strip():
        raise ValueError("El nombre es obligatorio.")
    if data.temperatura not in _TEMPERATURAS_VALIDAS:
        raise ValueError(f"Temperatura inválida: {data.temperatura}")

    base = contactos_dir()
    base.mkdir(parents=True, exist_ok=True)

    slug = data.slug
    if not slug:
        raise ValueError(f"No se puede derivar slug del nombre: {data.nombre!r}")

    target = base / f"{slug}.md"
    if target.exists():
        raise ContactoExistenteError(f"Ya existe un contacto en {target}")

    content = _render_template(data, today or date.today())
    target.write_text(content, encoding="utf-8")
    return target


class ContactoNoEncontradoError(Exception):
    pass


def get_contacto(slug: str) -> Contacto:
    path = contactos_dir() / f"{slug}.md"
    if not path.exists():
        raise ContactoNoEncontradoError(f"No existe contacto: {slug}")
    return parse_contacto(path)


def _set_estado_field(text: str, label: str, value: str) -> str:
    """Pone `- **<label>**: <value>` en la sección Estado, creando la línea si falta."""
    estado_pattern = re.compile(
        r"(^##\s+Estado\s*$)(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    line_pattern = re.compile(
        rf"^(\s*[-*]\s*\*\*{re.escape(label)}\*\*\s*:).*$", re.MULTILINE
    )

    match = estado_pattern.search(text)
    if not match:
        return text

    estado_header, estado_body = match.group(1), match.group(2)
    if line_pattern.search(estado_body):
        new_body = line_pattern.sub(lambda m: f"{m.group(1)} {value}", estado_body)
    else:
        lines = estado_body.rstrip("\n").splitlines()
        lines.append(f"- **{label}**: {value}")
        new_body = "\n".join(lines) + "\n\n"
    return text[: match.start()] + estado_header + new_body + text[match.end() :]


def _set_archivado_field(text: str, value: str) -> str:
    return _set_estado_field(text, "Archivado", value)


def set_estado_relacion(slug: str, estado: str) -> None:
    if estado not in ESTADOS_RELACION:
        raise ValueError(f"Estado de relación inválido: {estado}")
    path = contactos_dir() / f"{slug}.md"
    if not path.exists():
        raise ContactoNoEncontradoError(f"No existe contacto: {slug}")
    text = path.read_text(encoding="utf-8")
    path.write_text(_set_estado_field(text, "Estado relación", estado), encoding="utf-8")


def set_archivado(slug: str, archivado: bool) -> None:
    path = contactos_dir() / f"{slug}.md"
    if not path.exists():
        raise ContactoNoEncontradoError(f"No existe contacto: {slug}")
    text = path.read_text(encoding="utf-8")
    new_text = _set_archivado_field(text, "sí" if archivado else "no")
    path.write_text(new_text, encoding="utf-8")


def borrar_contacto(slug: str) -> None:
    path = contactos_dir() / f"{slug}.md"
    if not path.exists():
        raise ContactoNoEncontradoError(f"No existe contacto: {slug}")
    path.unlink()


def _append_interaccion_to_text(
    text: str, fecha: date, titulo: str, contenido: str
) -> str:
    titulo_clean = titulo.strip() or "Interacción"
    contenido_clean = contenido.strip()
    entry_lines = [f"### {fecha.isoformat()} — {titulo_clean}"]
    if contenido_clean:
        entry_lines.extend(["", contenido_clean])
    entry = "\n".join(entry_lines) + "\n"

    if re.search(r"^##\s+Histórico\s*$", text, re.MULTILINE):
        if not text.endswith("\n"):
            text = text + "\n"
        return text + "\n" + entry

    if not text.endswith("\n"):
        text = text + "\n"
    return text + "\n## Histórico\n\n" + entry


def append_interaccion(
    slug: str, fecha: date, titulo: str, contenido: str
) -> None:
    path = contactos_dir() / f"{slug}.md"
    if not path.exists():
        raise ContactoNoEncontradoError(f"No existe contacto: {slug}")
    if not titulo.strip():
        raise ValueError("El título de la interacción es obligatorio.")
    text = path.read_text(encoding="utf-8")
    new_text = _append_interaccion_to_text(text, fecha, titulo, contenido)
    path.write_text(new_text, encoding="utf-8")


def update_contacto(slug: str, data: EditContactoInput) -> None:
    if data.temperatura not in _TEMPERATURAS_VALIDAS:
        raise ValueError(f"Temperatura inválida: {data.temperatura}")

    path = contactos_dir() / f"{slug}.md"
    if not path.exists():
        raise ContactoNoEncontradoError(f"No existe contacto: {slug}")

    text = path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    nombre = title_match.group(1).strip() if title_match else slug

    estado_section = _extract_section(text, "Estado")
    archivado_match = re.search(
        r"^\s*[-*]\s*\*\*Archivado\*\*\s*:\s*(.*)$",
        estado_section,
        re.MULTILINE,
    )
    archivado_value = (
        archivado_match.group(1).strip() if archivado_match else "no"
    )

    historico_match = re.search(r"^##\s+Histórico\s*$", text, re.MULTILINE)
    if historico_match:
        historico_part = text[historico_match.start():].rstrip() + "\n"
    else:
        historico_part = "## Histórico\n"

    lines = [
        f"# {nombre}",
        "",
        "## Datos",
        _field_line("Empresa", data.empresa),
        _field_line("Rol", data.rol),
        _field_line("País", data.pais),
        _field_line("Tipo de contacto", data.tipo_contacto),
        _field_line("LinkedIn", data.linkedin),
        _field_line("Email", data.email),
        _field_line("Cómo le conocí / por qué le contacto", data.conexion),
        _field_line("Puntos de conexión", data.puntos_conexion),
        "",
    ]
    contexto_stripped = data.contexto.strip()
    if contexto_stripped:
        lines.extend(["## Contexto pegado", "", contexto_stripped, ""])
    lines.extend(
        [
            "## Estado",
            _field_line("Temperatura", data.temperatura),
            _field_line("Tier", str(data.tier) if data.tier else ""),
            _field_line("Estado relación", data.estado_relacion),
            _field_line("Salidas", ", ".join(data.salidas)),
            _field_line("Próxima acción", data.proxima_accion),
            _field_line("Próxima fecha", data.proxima_fecha),
            _field_line("Archivado", archivado_value),
            "",
        ]
    )

    new_text = "\n".join(lines) + historico_part
    path.write_text(new_text, encoding="utf-8")
