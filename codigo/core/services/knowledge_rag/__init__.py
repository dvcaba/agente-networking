"""Capacidad RAG reutilizable + factorías de agente.

- ``rag_agent``: lee del corpus de un dominio y responde CON CITAS.
- ``investigator_agent``: investiga en web (estado del arte), guarda una nota
  SOURCEADA en el ``knowledge/`` del dominio y la re-ingesta para el RAG.

La mecánica vive en core; el conocimiento es de cada dominio.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import yaml

from core.services import llm
from core.engine.agent_base import AgentSpec, InputField

from . import ingest as _ingest
from . import retrieve as _retrieve
from . import store as _store

__all__ = ["rag_agent", "investigator_agent", "ensure_ingested"]


def ensure_ingested(
    index_dir: Path,
    collection: str,
    sources: list[tuple[Path, str]],
    *,
    capa: str = "disciplina",
    columna: str = "",
) -> None:
    """Ingesta los corpus si la colección está vacía (primera vez)."""
    col = _store.get_collection(index_dir, collection)
    if col.count() == 0:
        _ingest.ingest(index_dir, collection, sources, capa=capa, columna=columna)


#: A partir de aquí un pasaje se marca como antiguo. No caduca ni se borra: se AVISA.
#: Un RAG con corpus rancio es el fallo peligroso —responde con citas, con seguridad y
#: desactualizado—, así que la vejez tiene que verse en la respuesta y no en un informe
#: que nadie mira. Cada cuánto refrescar sigue siendo decisión abierta (DISENO §10).
_MESES_PARA_ANTIGUA = 12


def antiguedad_meses(fecha: str) -> float | None:
    """Meses transcurridos desde ``fecha`` (ISO). None si no hay fecha o no se entiende."""
    if not fecha:
        return None
    try:
        d = datetime.fromisoformat(str(fecha)[:10]).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - d).days / 30.44


def es_antigua(fecha: str, umbral_meses: float = _MESES_PARA_ANTIGUA) -> bool:
    """True si el pasaje es lo bastante viejo como para avisar.

    Sin fecha NO se marca: marcar lo desconocido como viejo cansa, y un aviso que salta
    siempre acaba en que nadie lo mira.
    """
    meses = antiguedad_meses(fecha)
    return meses is not None and meses >= umbral_meses


def _slug(texto: str) -> str:
    """Nombre de fichero a partir del título de la nota: sin tildes ni eñes.

    ``isalnum`` daba por buena la «í» y el nombre acababa como
    «2026-09-12-artículo-50-del-eu-ai-act.md»; en Windows/WSL esa tilde se convierte en algo
    como «art├¡culo» que ya no se puede leer ni buscar. Es de donde venía el mojibake de los
    borradores del redactor.
    """
    plano = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plano).strip("-")[:50].rstrip("-") or "nota"


# ----------------------------------------------------------------------------- RAG
#: (índice, colección, [(carpeta, tipo), ...]): una colección que consultar y de dónde llenarla.
Layer = tuple[Path, str, list[tuple[Path, str]]]


#: Lo que un «consulta tus documentos» tiene obligado y prohibido hacer. Vive aquí, y no
#: escondido dentro de la función que arma el prompt, porque **la pantalla lo enseña**: este
#: molde no tiene instrucciones propias en su ficha, así que si estas reglas no se pueden
#: leer, no hay forma de juzgar si te puedes fiar de lo que responde.
REGLAS_DE_CITADO = (
    "Responde la pregunta del usuario USANDO SOLO los pasajes recuperados de "
    "su base de conocimiento. Cita con [n] el pasaje que respalda cada afirmación. "
    "Si los pasajes no cubren la pregunta, dilo claramente: 'No consta en mis "
    "fuentes'. No inventes ni uses conocimiento externo. Si te apoyas en un "
    "pasaje marcado como ANTIGUA, adviértelo en la respuesta. Si te apoyas en un "
    "pasaje marcado como TEXTO PROPIO, dilo («según lo que escribiste tú…»): es "
    "su postura, no algo que una fuente externa confirme."
)


def rag_agent(
    path: tuple[str, ...],
    name: str,
    description: str,
    *,
    index_dir: Path | None = None,
    collection: str = "",
    source_dirs: list[tuple[Path, str]] | None = None,
    layers: list[Layer] | Callable[[], list[Layer]] | None = None,
    fusion: str = "rrf",
    top_k: int = 6,
    model: str | None = None,
    title: str | None = None,
    starters: list[str] | None = None,
) -> AgentSpec:
    """Responde con citas desde una o varias colecciones.

    ``layers`` son las colecciones que consulta —en un sistema, un tema de la biblioteca
    cada una—. Puede ser un CALLABLE: se resuelve en cada consulta, así que un tema o un
    documento nuevo se ve sin reiniciar. Sin ``layers``, consulta una sola colección:
    ``index_dir`` + ``collection``, llenada desde ``source_dirs``.

    ``fusion`` es cómo se juntan los resultados de varias colecciones (ver
    :func:`retrieve.retrieve_capas`).
    """

    def _capas() -> list[Layer]:
        if layers is None:
            return [(index_dir, collection, source_dirs or [])]
        return layers() if callable(layers) else list(layers)

    def _prep(entrada: dict):
        """Prepara (prompt, sources, mensaje) desde la pregunta.

        Única implementación: ``_run`` y ``_stream`` pasan los dos por aquí. Antes había
        una copia en cada uno "para no divergir" y habían divergido — cuando se añadió la
        recuperación por capas, la del streaming se quedó consultando una sola colección,
        que es justo la que usa la web para los chats.
        """
        question = (entrada.get("question") or entrada.get("text") or "").strip()
        if not question:
            return None, None, "Falta 'question'."

        capas = _capas()
        for idx, col, fuentes in capas:
            ensure_ingested(idx, col, fuentes)
        hits = _retrieve.retrieve_capas(
            [(idx, col, None) for idx, col, _ in capas], question, top_k, fusion=fusion
        )
        if not hits:
            return None, [], "Todavía no hay documentos indexados en estas fuentes."

        bloques, sources = [], []
        for i, h in enumerate(hits, 1):
            m = h["meta"]
            etiqueta = f"[{i}] {m.get('title') or m.get('source')}"
            if m.get("kind") == "downloaded":
                etiqueta += " (documento autoritativo)"
            elif m.get("kind") == "propio":
                etiqueta += " (TEXTO PROPIO: lo escribió el usuario; no es una fuente externa)"
            vieja = es_antigua(m.get("date") or "")
            if vieja:
                etiqueta += (
                    f" (ANTIGUA: {int(antiguedad_meses(m.get('date')) or 0)} meses; "
                    "puede estar desactualizada)"
                )
            bloques.append(f"{etiqueta}\n{h['text']}")
            sources.append({
                "n": i,
                "title": m.get("title") or m.get("source"),
                "url": m.get("url") or "",
                "kind": m.get("kind") or "",
                "date": m.get("date") or "",
                "capa": m.get("capa") or "",
                "antigua": vieja,
            })
        prompt = (
            REGLAS_DE_CITADO
            + f"\n\nPREGUNTA:\n{question}\n\nPASAJES:\n\n"
            + "\n\n---\n\n".join(bloques)
        )
        return prompt, sources, None

    def _run(entrada: dict) -> dict:
        prompt, sources, mensaje = _prep(entrada)
        if prompt is None:
            if sources is None:  # falta la pregunta: es un error de uso
                return {"success": False, "error": mensaje, "text": ""}
            # corpus vacío: es una respuesta legítima, no un fallo
            return {"success": True, "text": mensaje, "sources": []}
        resp = llm.ask_sync(prompt, model=model) if model else llm.ask_sync(prompt)
        return {
            "success": resp.success,
            "error": resp.error,
            "text": resp.text,
            "sources": sources,
        }

    async def _stream(entrada: dict, out: dict):
        prompt, sources, mensaje = _prep(entrada)
        if prompt is None:  # nada que responder con el LLM
            out.update(success=sources is not None, sources=sources or [])
            if mensaje and sources is not None:
                yield mensaje  # caso "sin conocimiento": es una respuesta, no un error
            elif mensaje:
                out["error"] = mensaje
            return
        out["sources"] = sources
        kw = {"out": out}
        if model:
            kw["model"] = model
        async for chunk in llm.ask_stream(prompt, **kw):
            yield chunk

    return AgentSpec(
        path=path,
        name=name,
        description=description,
        run=_run,
        inputs=[InputField("question", "Pregunta", "", "Se responde solo desde las fuentes, citándolas")],
        title=title,
        chat=True,  # conversacional: pregunta -> respuesta con fuentes
        starters=starters,
        stream=_stream,
    )


# --------------------------------------------------------------------- Investigador
_INVESTIGATOR_SYSTEM = (
    "Eres un investigador del estado del arte. Tu salida alimenta una base de "
    "conocimiento que después se cita: por eso CADA afirmación relevante debe ir "
    "respaldada por una fuente real que hayas consultado con WebSearch/WebFetch. "
    "NO sintetices de memoria. Si no encuentras fuente, no lo afirmes."
)


_APERTURA = re.compile(r"---[ \t]*\n")
_CIERRE = re.compile(r"\n---[ \t]*(?:\n|$)")


def localizar_nota(texto: str) -> tuple[str, dict] | None:
    """Encuentra la nota (frontmatter + cuerpo) dentro de la respuesta del investigador.

    El modelo a veces escribe un preámbulo antes de la nota («Hay un desajuste de año
    fiscal, voy a buscar la fuente primaria…»), y hay que descartarlo. Antes se buscaba el
    frontmatter con ``^---`` a PRINCIPIO DE LÍNEA, y eso falló en real: el preámbulo acabó
    en «…primary source.---» con el ``---`` pegado a la frase. La regex no enganchaba y el
    guard tiraba una investigación correcta, con frontmatter y seis URLs, tumbando el
    workflow ``investment-pipeline`` entero.

    Ahora vale cualquier ``---`` seguido de salto de línea, esté donde esté. Lo que decide
    si es la nota no es la posición sino el contenido: el bloque tiene que ser YAML con
    ``title`` o ``sources``. Así una línea horizontal ``---`` del preámbulo no se confunde
    con la apertura.

    Devuelve ``(nota, frontmatter)`` con la nota normalizada a empezar por ``---``, o
    ``None`` si no hay nota reconocible.
    """
    for apertura in _APERTURA.finditer(texto):
        cierre = _CIERRE.search(texto, apertura.end())
        if cierre is None:
            return None
        try:
            fm = yaml.safe_load(texto[apertura.end():cierre.start()])
        except yaml.YAMLError:
            continue
        if isinstance(fm, dict) and ("title" in fm or "sources" in fm):
            return "---\n" + texto[apertura.end():].strip(), fm
    return None


def investigator_agent(
    path: tuple[str, ...],
    name: str,
    description: str,
    *,
    knowledge_dir: Path,
    index_dir: Path,
    collection: str,
    source_dirs: list[tuple[Path, str]],
    brief: str,
    model: str = "claude-opus-4-8",
    title: str | None = None,
    input_key: str = "topic",
    input_label: str = "Tema a investigar",
    input_help: str = "Estado del arte del dominio",
) -> AgentSpec:
    def _run(entrada: dict) -> dict:
        topic = (
            entrada.get(input_key) or entrada.get("topic") or entrada.get("text") or ""
        ).strip()
        if not topic:
            return {"success": False, "error": f"Falta '{input_key}'."}

        hoy = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        prompt = (
            f"CONTEXTO DEL DOMINIO (para enfocar):\n{brief}\n\n"
            f"TEMA A INVESTIGAR: {topic}\n\n"
            "Investiga el estado del arte con búsquedas web reales (varios ángulos), "
            "abre las fuentes y verifica. SÉ EFICIENTE: 4-8 búsquedas priorizando fuentes "
            "primarias; en cuanto tengas material triangulado suficiente, ESCRIBE la nota "
            "(no agotes búsquedas). Devuelve SOLO una nota markdown con este formato exacto:\n\n"
            "---\n"
            f'title: "<título conciso>"\n'
            f"date: {hoy}\n"
            "sources:\n"
            "  - https://...\n"
            "  - https://...\n"
            "---\n\n"
            "## <secciones>\n\n"
            "Cada afirmación con dato o claim lleva su fuente entre corchetes al final: "
            "[fuente: https://...]. Triangula los claims cuantitativos contra ≥2 fuentes. "
            "Si algo no lo pudiste verificar, no lo incluyas."
        )
        resp = llm.ask_sync(
            prompt,
            system=_INVESTIGATOR_SYSTEM,
            model=model,
            allowed_tools=["WebSearch", "WebFetch"],
            timeout=900,
        )
        if not resp.success:
            return {"success": False, "error": resp.error or "fallo del investigador"}

        encontrada = localizar_nota(resp.text)
        # Anti-síntesis: la nota debe traer URLs reales (frontmatter o cuerpo).
        fuentes = list(dict.fromkeys(re.findall(r'https?://[^\s\)\]>"\']+', resp.text)))
        if encontrada is None or not fuentes:
            return {
                "success": False,
                "error": "La nota no trae frontmatter+fuentes verificables; no se ingesta (anti-síntesis).",
                "preview": resp.text[:800],
            }

        nota, fm = encontrada  # desde el frontmatter, sin preámbulo
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        titulo = str(fm.get("title") or "")

        # La nota se FIRMA aquí, al escribirla, en vez de pedírselo al modelo en el prompt:
        # pedirlo no es garantizarlo. Sin firma, cuatro investigadores del mismo sistema
        # dejan notas huérfanas y no hay forma de saber cuál es de quién (D24).
        if "agente:" not in fm:
            firma = f"agente: {name}\n"
            if path:
                firma += f"sistema: {path[0]}\n"
            nota = nota.replace("---\n", "---\n" + firma, 1)

        ruta = knowledge_dir / f"{hoy}-{name}-{_slug(titulo or topic)}.md"
        ruta.write_text(nota, encoding="utf-8")

        n_chunks = _ingest.ingest(index_dir, collection, source_dirs)
        return {
            "success": True,
            "text": nota,  # el texto de la investigación, para que un paso siguiente lo use
            "note_path": str(ruta),
            "n_sources": len(fuentes),
            "ingested_chunks": n_chunks,
        }

    return AgentSpec(
        path=path,
        name=name,
        description=description,
        run=_run,
        inputs=[InputField(input_key, input_label, "", input_help)],
        title=title,
    )
