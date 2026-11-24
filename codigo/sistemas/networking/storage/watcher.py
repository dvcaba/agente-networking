from __future__ import annotations

import threading

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from sistemas.networking.config import DATA_PATH

# Contador de versión: cada cambio en un .md del data path lo incrementa.
# Los clientes (vía ui.timer en el header) comparan su versión vista y recargan.
_version = 0
_lock = threading.Lock()
_observer: Observer | None = None


def get_version() -> int:
    with _lock:
        return _version


def _bump() -> None:
    global _version
    with _lock:
        _version += 1


class _MdHandler(FileSystemEventHandler):
    def on_any_event(self, event) -> None:
        if getattr(event, "is_directory", False):
            return
        # src_path (modificación/creación/borrado) + dest_path (save atómico vía rename).
        paths = (
            getattr(event, "src_path", "") or "",
            getattr(event, "dest_path", "") or "",
        )
        if any(str(p).endswith(".md") for p in paths if p):
            _bump()


def start_watcher() -> None:
    """Arranca el observer una sola vez (idempotente)."""
    global _observer
    if _observer is not None:
        return
    obs = Observer()
    obs.schedule(_MdHandler(), str(DATA_PATH), recursive=True)
    obs.daemon = True
    obs.start()
    _observer = obs
