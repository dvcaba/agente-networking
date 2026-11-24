"""Proveedores de contexto para fichas ``simple``.

Una ficha ``simple`` puede pedir contexto de su sistema (``context: [sobre-mi.objetivos]``).
Aquí se registran los proveedores (clave -> función que devuelve texto) y se resuelven a la
hora de construir el prompt. Mantiene el modelo dirigido-por-datos sin que la ficha ejecute
código: solo referencia claves ya registradas.

Cada proveedor recibe **de qué sistema se le pregunta**. Antes no lo recibía, y con una
identidad por sistema (D8) eso ya no vale: «tus objetivos» no es lo mismo en Contenido que
en Networking, y sin saber quién pregunta no hay forma de dar la respuesta correcta.
"""

from __future__ import annotations

from collections.abc import Callable

_PROVIDERS: dict[str, Callable[[str], str]] = {}


def register_context(key: str, fn: Callable[[str], str]) -> None:
    """Registra un proveedor. 'sobre-mi.objetivos' -> función(sistema) que da el texto."""
    _PROVIDERS[key] = fn


def resolve_context(keys: list[str], sistema: str = "") -> str:
    """Resuelve las claves a texto y las une, preguntando por ese sistema.

    Las claves desconocidas se ignoran: una ficha que pide un contexto que no existe se
    queda sin él, pero no deja de funcionar.
    """
    partes: list[str] = []
    for k in keys:
        fn = _PROVIDERS.get(k)
        if fn is None:
            continue
        try:
            texto = fn(sistema)
        except Exception:  # noqa: BLE001 — un proveedor roto no debe tumbar al agente
            continue
        if texto:
            partes.append(str(texto))
    return "\n\n".join(partes)
