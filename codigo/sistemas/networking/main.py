from nicegui import ui

from core.engine import discovery
from sistemas.networking.config import APP_PORT, validate_data_path
from sistemas.networking.storage.watcher import start_watcher
from sistemas.networking.ui.asistente import render_asistente
from sistemas.networking.ui.buscar_gente import render_buscar_gente
from sistemas.networking.ui.candidatos import render_candidatos
from sistemas.networking.ui.comentar import render_comentar
from sistemas.networking.ui.contactos_listado import render_contactos_listado
from sistemas.networking.ui.detalle import render_detalle
from sistemas.networking.ui.documentos import render_biblioteca, render_estrategia
from sistemas.networking.ui.inicio import render_inicio

# Leer la ficha del sistema y registrar sus agentes ANTES de definir las páginas: el coach
# del asistente se pide al registro por su id. En la plataforma esto lo hacía su
# `apps/web/app.py`; aquí el punto de entrada es este fichero, así que le toca a él.
discovery.load_all()


@ui.page("/")
def raiz() -> None:
    # La app vive bajo /networking; abrir la dirección pelada daba 404.
    ui.navigate.to("/networking")


@ui.page("/networking")
def index() -> None:
    render_inicio()


@ui.page("/networking/conversacion/{slug}")
def conversacion(slug: str, preparar: str = "") -> None:
    render_inicio(slug, preparar)


@ui.page("/networking/contactos")
def contactos_listado() -> None:
    render_contactos_listado()


@ui.page("/networking/candidatos")
def candidatos() -> None:
    render_candidatos()


@ui.page("/networking/estrategia")
def estrategia() -> None:
    render_estrategia()


@ui.page("/networking/biblioteca")
def biblioteca() -> None:
    render_biblioteca()


@ui.page("/networking/asistente")
def asistente() -> None:
    render_asistente()


@ui.page("/networking/comentar")
def comentar() -> None:
    render_comentar()


@ui.page("/networking/buscar-gente")
def buscar_gente() -> None:
    render_buscar_gente()


@ui.page("/networking/contacto/{slug}")
def contacto(slug: str) -> None:
    render_detalle(slug)


def run() -> None:
    validate_data_path()
    start_watcher()
    ui.run(
        host="127.0.0.1",
        port=APP_PORT,
        title="Agente de Networking",
        reload=True,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    run()
