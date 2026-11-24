"""Los sistemas: lo que montas para algo que haces de forma recurrente.

Cada sistema es una carpeta de ``sistemas/`` con su ``sistema.yaml``:

    system: inversion              identificador; tiene que coincidir con la carpeta
    label: Inversión y opciones    cómo se llama en pantalla
    purpose: …                     qué consigues con él, en una frase
    agents: […]                    sus especialistas
    workflows: […]                 sus procesos de varios pasos

Lo que el sistema SABE no se declara en la ficha: vive en su propia carpeta ``biblioteca/``
(D7). Un ``topics:`` heredado del modelo antiguo se rechaza al cargar, diciendo por qué.

La ficha es la lista COMPLETA del sistema, incluidos los especialistas hechos en código,
que se referencian con ``code_ref``: lo que no está en la ficha no existe.

Por dentro reutiliza el intérprete de fichas (:mod:`core.engine.blueprint`): un sistema se
traduce a la ficha que ese intérprete entiende.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from core import identity
from core.engine import registry
from core.engine.agent_base import AgentSpec
from core.engine.blueprint.build import build_domain
from core.engine.blueprint.context import register_context
from core.engine.blueprint.model import (
    BlueprintError,
    DomainBlueprint,
    domain_from_dict,
    validate,
)
from core.engine.paths import ROOT

SYSTEM_FILENAME = "sistema.yaml"


@dataclass(frozen=True)
class System:
    slug: str
    label: str
    purpose: str
    icon: str | None
    dir: Path
    blueprint: DomainBlueprint


def systems_dir() -> Path:
    """Raíz de los sistemas. ``AGENT_PLATFORM_SISTEMAS`` la cambia (los tests la usan)."""
    return Path(os.environ.get("AGENT_PLATFORM_SISTEMAS") or ROOT / "sistemas")


def to_blueprint_dict(data: dict) -> dict:
    """Traduce un ``sistema.yaml`` a la ficha que entiende el intérprete."""
    return {
        "domain": data.get("system", ""),
        "label": data.get("label", ""),
        "description": data.get("purpose", ""),
        "icon": data.get("icon"),
        "agents": data.get("agents") or [],
        "workflows": data.get("workflows") or [],
    }


def read(path: Path) -> System:
    """Lee y valida una ficha de sistema. Los errores dicen qué fichero y qué falta."""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    donde = str(path)
    if "knowledge" in data:
        raise BlueprintError(
            f"{donde}: un sistema no tiene 'knowledge'. Conecta temas de la biblioteca con "
            "'topics'."
        )
    bp = domain_from_dict(to_blueprint_dict(data))
    try:
        validate(bp)
    except BlueprintError as e:
        raise BlueprintError(f"{donde}: {e}") from e

    carpeta = path.parent.name
    if bp.domain != carpeta:
        raise BlueprintError(
            f"{donde}: 'system' es '{bp.domain}' pero la carpeta se llama '{carpeta}'. "
            "Tienen que coincidir."
        )
    proposito = str(data.get("purpose") or "").strip()
    if not proposito:
        raise BlueprintError(
            f"{donde}: falta 'purpose' (qué consigues con este sistema, en una frase)."
        )
    if data.get("topics"):
        raise BlueprintError(
            f"{donde}: 'topics' ya no existe. Lo que sabe un sistema vive en su propia "
            f"carpeta 'biblioteca/', no en temas compartidos."
        )
    return System(
        slug=bp.domain,
        label=bp.label,
        purpose=proposito,
        icon=bp.icon,
        dir=path.parent,
        blueprint=bp,
    )


def find() -> list[System]:
    raiz = systems_dir()
    return [read(f) for f in sorted(raiz.glob(f"*/{SYSTEM_FILENAME}"))] if raiz.exists() else []


def build(system: System) -> list[AgentSpec]:
    """Construye los especialistas y procesos de un sistema, sin registrarlos.

    Un especialista hecho en código trae su propia ruta. Tiene que ser la del sistema: si
    no, colgaría de otro sitio sin que nada lo avisara, como pasaba con
    'marketing.contenido' dentro de un área que ya no se llamaba así.
    """
    specs = build_domain(system.blueprint, base_dir=system.dir)
    esperados = {
        f"{system.slug}.{x.name}"
        for x in (*system.blueprint.agents, *system.blueprint.workflows)
    }
    for spec in specs:
        if spec.id not in esperados:
            raise BlueprintError(
                f"[{system.slug}] el especialista hecho en código '{spec.id}' no está en la "
                f"ruta del sistema. Debería ser uno de: {sorted(esperados)}."
            )
    return specs


def register_context_providers() -> None:
    """Contexto que una ficha puede pedir por nombre (``context: [sobre-mi.objetivos]``)."""
    register_context("sobre-mi.perfil", identity.profile)
    # Recortado igual que lo metía el investigador de marketing en su encargo: los
    # objetivos completos pasan de 10 000 caracteres y ahogarían el encargo.
    register_context("sobre-mi.objetivos", lambda s: identity.goals(s)[:2500])
    register_context("sobre-mi.narrativa", identity.narrative)
    register_context("sobre-mi.estilo", identity.style)


def load_all() -> list[System]:
    """Lee, construye y registra todos los sistemas."""
    register_context_providers()
    sistemas = find()
    for sistema in sistemas:
        for spec in build(sistema):
            registry.register(spec)
    return sistemas
