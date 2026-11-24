"""Cliente Claude único de la plataforma (suscripción, no API key)."""

from .client import BLOCKED_DEFAULT, DEFAULT_MODEL, Response, ask, ask_stream, ask_sync

__all__ = ["ask", "ask_sync", "ask_stream", "Response", "DEFAULT_MODEL", "BLOCKED_DEFAULT"]
