from __future__ import annotations

from sistemas.networking.storage import watcher as W


class _Event:
    is_directory = False
    src_path = ""
    dest_path = ""


def _evt(src="", dest=""):
    e = _Event()
    e.src_path = src
    e.dest_path = dest
    return e


def test_handler_bumps_on_md():
    v0 = W.get_version()
    W._MdHandler().on_any_event(_evt(src="/x/a.md"))
    assert W.get_version() == v0 + 1


def test_handler_ignores_non_md():
    v0 = W.get_version()
    W._MdHandler().on_any_event(_evt(src="/x/a.txt"))
    assert W.get_version() == v0


def test_handler_atomic_save_via_dest():
    v0 = W.get_version()
    W._MdHandler().on_any_event(_evt(src="/x/.tmp123", dest="/x/b.md"))
    assert W.get_version() == v0 + 1


def test_handler_ignora_directorios():
    v0 = W.get_version()
    e = _evt(src="/x/dir")
    e.is_directory = True
    W._MdHandler().on_any_event(e)
    assert W.get_version() == v0
