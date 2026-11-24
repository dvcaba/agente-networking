"""Lo que produce un sistema, guardado como documento en su carpeta ``salidas/``.

Hasta ahora una ejecución se pintaba en pantalla y se perdía al cerrar: ni el runner ni el
ejecutor de procesos escribían un solo fichero. Por eso ``salidas/`` estaba vacía en tres de
los cuatro sistemas, y por eso el chat no podía enseñarte «lo último que hizo esta pieza» —
no había nada que enseñar.

Dos reglas, y las dos salen de lo que duele:

1. **El documento dice quién lo hizo.** El nombre del fichero lleva la fecha, la pieza y de
   qué va; dentro va la ficha entera (pieza, sistema, proceso del que salió si vino de uno,
   y qué se le pidió). Sin eso, cuatro investigadores escribiendo en la misma carpeta dejan
   notas huérfanas y no hay forma de saber cuál es de quién.
2. **Se guarda solo; se tira a mano.** Borrar lo que sobra cuesta un clic; darte cuenta a
   los tres días de que perdiste una tasación buena no tiene arreglo (D24).

Las claves ``title`` y ``date`` van en inglés a propósito, aunque el resto esté en español:
son las que ya leen la ingesta y ``espacio.titulo()``. Inventar aquí unas propias en español
obligaría a que esos dos sitios entendieran dos vocabularios, que es justo el desorden que
la plataforma intenta no tener.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path

import yaml

from core import espacio

#: Tope del nombre de fichero: un título largo entero deja rutas impracticables.
_LARGO_NOMBRE = 60


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    if len(texto) <= _LARGO_NOMBRE:
        return texto
    # Se corta por la última palabra entera: «...sin-reacondiciona» se lee como un error
    # de escritura, no como un recorte.
    return texto[:_LARGO_NOMBRE].rsplit("-", 1)[0].strip("-")


def titulo_de(resultado: dict, entrada: dict | None = None) -> str:
    """Cómo llamar a esto. Su primer encabezado; si no tiene, lo que se le pidió."""
    texto = str((resultado or {}).get("text") or "")
    for linea in texto.splitlines():
        if linea.strip().startswith("#"):
            return linea.lstrip("#").strip()[:120]
    for valor in (entrada or {}).values():
        if isinstance(valor, str) and valor.strip():
            return valor.strip()[:120]
    return ""


def guardar(spec, entrada: dict, resultado, *, cuando: datetime | None = None) -> Path | None:
    """Escribe lo que acaba de producir una pieza. Devuelve la ruta, o None si no había qué.

    No se guarda lo que falló ni lo que no trae texto: un documento vacío en ``salidas/`` es
    ruido que hay que abrir para descubrir que no dice nada.
    """
    if not isinstance(resultado, dict) or not resultado.get("success"):
        return None
    texto = str(resultado.get("text") or "").strip()
    if not texto:
        return None
    sistema = spec.path[0] if getattr(spec, "path", None) else None
    if not sistema:
        return None

    cuando = cuando or datetime.now().astimezone()
    titulo = titulo_de(resultado, entrada)
    ficha = {
        "title": titulo or spec.display_title,
        "date": cuando.strftime("%Y-%m-%d"),
        "hora": cuando.strftime("%H:%M"),
        "agente": spec.name,
        "agente_nombre": spec.display_title,
        "sistema": sistema,
        # Un proceso deja rastro de sus pasos; un especialista suelto, no. Es la forma
        # honesta de saber de dónde salió esto sin preguntárselo a nadie.
        "tipo": "proceso" if resultado.get("steps") else "especialista",
        "peticion": {k: str(v)[:300] for k, v in (entrada or {}).items() if v},
    }
    if fuentes := resultado.get("sources"):
        ficha["sources"] = [s.get("url") for s in fuentes if isinstance(s, dict) and s.get("url")]

    destino = espacio.salidas_dir(sistema)
    destino.mkdir(parents=True, exist_ok=True)
    # Si el título ya empieza por el nombre de la pieza, no se repite: la tasación de
    # coches se guardaba como «...-tasacion-tasacion-seat-leon-...».
    cuerpo = _slug(titulo)
    if cuerpo.startswith(f"{_slug(spec.name)}-"):
        cuerpo = cuerpo[len(_slug(spec.name)) + 1:]
    nombre = f"{cuando.strftime('%Y-%m-%d-%H%M')}-{spec.name}-{cuerpo}".rstrip("-")
    ruta = destino / f"{nombre}.md"
    if ruta.exists():  # dos ejecuciones en el mismo minuto no se pisan
        ruta = destino / f"{nombre}-2.md"
    cabecera = yaml.safe_dump(ficha, allow_unicode=True, sort_keys=False).strip()
    ruta.write_text(f"---\n{cabecera}\n---\n\n{texto}\n", encoding="utf-8")
    return ruta


def guardar_conversacion(spec, pregunta: str, respuesta: str, *, sesion: str | None = None,
                         cuando: datetime | None = None) -> Path | None:
    """Lo que sale de un chat, en UN documento por conversación que va creciendo.

    Las piezas simples se usan conversando, no rellenando un formulario: es ahí donde de
    verdad producen. Pero un documento por turno llenaría la carpeta de ruido —preguntas de
    seguimiento como «¿y si el margen fuera 900?» no son entregables sueltos—, así que los
    turnos de una misma conversación se van añadiendo al mismo fichero. El hilo se reconoce
    por su ``sesion``; sin ella, cada turno abre documento.
    """
    respuesta = (respuesta or "").strip()
    if not respuesta:
        return None
    sistema = spec.path[0] if getattr(spec, "path", None) else None
    if not sistema:
        return None

    cuando = cuando or datetime.now().astimezone()
    destino = espacio.salidas_dir(sistema)
    destino.mkdir(parents=True, exist_ok=True)
    turno = f"\n\n### {pregunta.strip()}\n\n{respuesta}\n" if pregunta.strip() else f"\n\n{respuesta}\n"

    if sesion:
        for ruta in espacio.ficheros(destino):
            if ruta.suffix.lower() != ".md":
                continue
            if str(espacio.frontmatter(ruta).get("sesion") or "") == sesion:
                with ruta.open("a", encoding="utf-8") as f:
                    f.write(turno)
                return ruta

    ficha = {
        "title": (pregunta.strip() or titulo_de({"text": respuesta}))[:120] or spec.display_title,
        "date": cuando.strftime("%Y-%m-%d"),
        "hora": cuando.strftime("%H:%M"),
        "agente": spec.name,
        "agente_nombre": spec.display_title,
        "sistema": sistema,
        "tipo": "conversacion",
    }
    if sesion:
        ficha["sesion"] = sesion
    cuerpo = _slug(str(ficha["title"]))
    if cuerpo.startswith(f"{_slug(spec.name)}-"):
        cuerpo = cuerpo[len(_slug(spec.name)) + 1:]
    nombre = f"{cuando.strftime('%Y-%m-%d-%H%M')}-{spec.name}-{cuerpo}".rstrip("-")
    ruta = destino / f"{nombre}.md"
    if ruta.exists():
        ruta = destino / f"{nombre}-2.md"
    cabecera = yaml.safe_dump(ficha, allow_unicode=True, sort_keys=False).strip()
    ruta.write_text(f"---\n{cabecera}\n---\n{turno.lstrip()}", encoding="utf-8")
    return ruta


def de_la_pieza(sistema: str, agente: str, *, maximo: int = 3) -> list[Path]:
    """Las últimas salidas firmadas por esta pieza, de la más nueva a la más vieja.

    Se filtra por la firma del documento y no por el nombre del fichero: el nombre se puede
    cambiar al ordenar la carpeta, y entonces la atribución se perdería en silencio.
    """
    salida = []
    for p in sorted(espacio.ficheros(espacio.salidas_dir(sistema)), reverse=True):
        if p.suffix.lower() != ".md":
            continue
        if str(espacio.frontmatter(p).get("agente") or "") == agente:
            salida.append(p)
        if len(salida) >= maximo:
            break
    return salida
