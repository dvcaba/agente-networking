"""Registro de uso: qué has usado y cuándo.

Existe por una razón concreta. El revisor de coherencia tiene que poder decirte «esto no lo
usas», y hasta ahora no había ni un dato con el que sostenerlo. Decir «no se ha usado en
tres meses» cuando en realidad nadie estaba mirando es exactamente el tipo de dato falso
que esta plataforma no se puede permitir (§7): sin registro, la única respuesta honesta era
«no lo sé», y con esto pasa a ser «desde tal día, no».

Es un fichero de texto, una línea por ejecución, en tu máquina. No es telemetría, no sale
de aquí, y si se corrompe o se borra no rompe nada: se pierde el aviso, no el trabajo.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.engine.paths import ROOT

FICHERO = ".uso/registro.jsonl"


def fichero() -> Path:
    return Path(os.getenv("AGENT_PLATFORM_USO") or (ROOT / FICHERO))


def registrar(agent_id: str, *, cuando: datetime | None = None) -> None:
    """Apunta que se ha usado algo. No lanza nunca: esto va dentro de una ejecución real,
    y un fallo al escribir el registro no puede tumbar el trabajo que sí te importa."""
    try:
        f = fichero()
        f.parent.mkdir(parents=True, exist_ok=True)
        marca = (cuando or datetime.now(tz=timezone.utc)).astimezone(timezone.utc).isoformat()
        with f.open("a", encoding="utf-8") as salida:
            salida.write(json.dumps({"id": agent_id, "when": marca}) + "\n")
    except OSError:
        pass


def _lineas() -> list[dict]:
    f = fichero()
    if not f.exists():
        return []
    salida = []
    for linea in f.read_text(encoding="utf-8").splitlines():
        try:
            dato = json.loads(linea)
        except ValueError:
            continue  # una línea rota no invalida el resto del registro
        if isinstance(dato, dict) and dato.get("id") and dato.get("when"):
            salida.append(dato)
    return salida


def _fecha(texto: str) -> datetime | None:
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        return None


def ultimas_veces() -> dict[str, datetime]:
    """La última vez que se usó cada pieza."""
    salida: dict[str, datetime] = {}
    for dato in _lineas():
        cuando = _fecha(dato["when"])
        if cuando and (dato["id"] not in salida or cuando > salida[dato["id"]]):
            salida[dato["id"]] = cuando
    return salida


def desde() -> datetime | None:
    """Desde cuándo hay registro. Sin esto no se puede distinguir «no lo usas» de «todavía
    no lo sé», que es la diferencia entre un aviso útil y uno inventado."""
    fechas = [f for f in (_fecha(d["when"]) for d in _lineas()) if f]
    return min(fechas) if fechas else None
