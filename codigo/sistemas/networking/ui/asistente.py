"""Asistente (coach) de networking.

Usa el mismo chat que el resto de las pantallas (``render_chat_body``) sobre el agente
registrado ``networking.assistant``. Una sola implementación de chat, un solo coach.

El id pedía antes ``marketing.networking.assistant``, un nombre del modelo viejo (cuando
networking colgaba de un dominio «marketing»). El registro los indexa como
``<sistema>.<nombre>``, así que ese id no resolvía y la pantalla daba error 500.
"""
from __future__ import annotations

from apps.web.runner import render_chat_body
from core.engine.registry import get
from sistemas.networking.ui.layout import header


def render_asistente() -> None:
    header("asistente")
    render_chat_body(get("networking.assistant"))
