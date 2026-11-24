from __future__ import annotations

from pathlib import Path

from core import identity
from sistemas.networking.config import DATA_PATH
from sistemas.networking.storage import perfiles
from sistemas.networking.storage.contactos import Contacto

#: El espacio de trabajo al que pertenece este código: su identidad es la suya.
ESPACIO = "networking"


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _bloque(titulo: str, contenido: str) -> str:
    contenido = contenido.strip()
    if not contenido:
        return ""
    return f"\n## {titulo}\n\n{contenido}\n"


def _contacto_md(c: Contacto) -> str:
    return _read_optional(c.path)


def prompt_asistente(pregunta: str) -> str:
    """Primer turno del asistente general (consulta libre con contexto del proyecto)."""
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    estilo = identity.style(ESPACIO)
    pendientes = _read_optional(DATA_PATH / "pendientes.md")

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque("Mis pendientes (plan de acción)", pendientes),
    ]

    instrucciones = """
Eres mi coach de comunicación y networking profesional (ver CLAUDE.md para tu rol completo). Te hago una consulta general — puede ser estrategia, "¿qué hago hoy?", a quién contactar, dudas, o pedirme criterio.

REGLAS:
- Responde en español, conciso y accionable. Recomienda en vez de interrogar.
- Si me falta prep para algo (ej: narrativa sin cerrar, validación pendiente), dímelo antes.
- Sé honesto: si no sabes algo o te falta info, dilo. No inventes.
- Si propones acciones concretas, ordénalas por valor.

MI CONSULTA:
""".strip()

    return instrucciones + "\n\n" + pregunta.strip() + "\n" + "".join(bloques)


def prompt_primer_mensaje(c: Contacto) -> str:
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    narrativa = identity.narrative(ESPACIO)
    estilo = identity.style(ESPACIO)
    plantilla = _read_optional(DATA_PATH / "plantillas" / "primer-contacto.md")
    contacto = _contacto_md(c)

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi pitch / narrativa", narrativa),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque("Guía de primer contacto (principios, no plantilla)", plantilla),
        _bloque("El contacto al que voy a escribir", contacto),
    ]

    instrucciones = """
Eres mi coach de comunicación profesional. Necesito redactar un PRIMER MENSAJE a un contacto nuevo.

OBJETIVO del primer mensaje: abrir una conversación, NUNCA pedir trabajo directamente.

TAREA: ofréceme 2-3 alternativas de mensaje con tonos o ángulos distintos. Para cada alternativa:

- Una etiqueta corta del ángulo o tono (ej. "Pregunta concreta + curiosidad", "Punto de conexión académico", "Comentario sobre algo que ha publicado").
- Una frase muy breve explicando por qué este ángulo encaja con este contacto en particular.
- El mensaje completo, listo para enviar, respetando MI estilo de comunicación (longitudes máximas, lista negra de palabras, tono cercano-profesional, sin corporate-ese).

REGLAS DURAS:
- Cada mensaje debe tener un ángulo de conexión real basado en los datos del contacto. Sin ángulo concreto, NO inventes uno: dilo explícitamente.
- Respeta las longitudes máximas de mi estilo (5 líneas en LinkedIn, 1 párrafo en email).
- NUNCA uses las palabras de la lista negra de mi estilo.
- Si faltan datos críticos del contacto para personalizar, dilo arriba antes de las alternativas.

FORMATO DE SALIDA: Markdown estricto, usando estos encabezados:

### Opción 1 — <etiqueta>
**Por qué este ángulo:** ...
**Mensaje:**
> ...

### Opción 2 — <etiqueta>
...

### Opción 3 — <etiqueta>
...

(Si solo merece la pena dar 2, da 2. No fuerces 3 si una sería floja.)
""".strip()

    return instrucciones + "\n" + "".join(bloques)


def prompt_continuar_conversacion(c: Contacto) -> str:
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    narrativa = identity.narrative(ESPACIO)
    estilo = identity.style(ESPACIO)
    plantilla_post_cafe = _read_optional(DATA_PATH / "plantillas" / "post-cafe.md")
    plantilla_post_entrevista = _read_optional(
        DATA_PATH / "plantillas" / "post-entrevista.md"
    )
    contacto = _contacto_md(c)

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi pitch / narrativa", narrativa),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque("Guía de mensaje post-café / post-llamada", plantilla_post_cafe),
        _bloque("Guía de mensaje post-entrevista", plantilla_post_entrevista),
        _bloque("El contacto (incluye histórico completo)", contacto),
    ]

    instrucciones = """
Eres mi coach de comunicación profesional. El contacto ACABA DE RESPONDERME. Su respuesta es la última entrada del histórico, marcada como "Respondió" (la fecha de hoy o muy reciente). Necesito redactar MI SIGUIENTE MENSAJE en respuesta a lo que me ha dicho.

PASO 1 — DIAGNÓSTICO:
Lee toda la conversación previa (no solo la última respuesta) y determina:

1. ¿Qué tipo de respuesta me ha dado? Posibilidades habituales:
   - **Acepta propuesta de café / llamada** → confirmar fecha, hora, canal concreto.
   - **Hace pregunta técnica concreta** → responder con sustancia + abrir continuación.
   - **"Estoy liado, hablamos en X"** → aceptar el timing, no presionar.
   - **Quiere saber más antes de comprometerse** → dar información sin pedir nada aún.
   - **Cierre cortés** (no quiere seguir) → agradecer educado, dejar puerta abierta sin insistir.
   - **Propone otra persona / contacto** → agradecer + abrir ese siguiente paso.
   - **Acaba de tener entrevista conmigo** → aplicar plantilla post-entrevista.
   - **Acaba de tener café/llamada conmigo** → aplicar plantilla post-café (<24h).
   - **Respuesta neutra / breve** → mantener viva la conversación con algo de sustancia, sin forzar.

2. ¿Qué quiere o necesita realmente esta persona en su respuesta? ¿Tiene una pregunta abierta sin responder? ¿Una acción pendiente?

3. ¿Cuál es el siguiente paso natural en la relación? (ej: cerrar fecha de café, dar info y dejar la pelota en su tejado, agradecer y bajar intensidad...)

PASO 2 — REDACCIÓN:
Ofréceme 2-3 alternativas con tonos o ángulos distintos. Para cada alternativa:

- Una etiqueta corta del ángulo/tono.
- Una frase breve explicando por qué encaja con su respuesta concreta.
- El mensaje completo, listo para enviar, respetando MI estilo (longitudes, lista negra de palabras).

REGLAS DURAS:
- Cada alternativa debe responder específicamente a lo que el contacto ha dicho (no es genérica).
- Si la respuesta del contacto incluía una pregunta concreta, MI mensaje debe responderla con sustancia (no eludirla).
- Si la respuesta fue un cierre cortés, NO inventes razones para seguir. Mejor un cierre digno por mi parte.
- Respeta los timings de los recursos (post-café <24h, post-entrevista mismo día / siguiente).
- Mantén el tono cercano-profesional, sin corporate-ese.

FORMATO DE SALIDA: Markdown estricto.

## Diagnóstico
- **Tipo de respuesta detectado**: ...
- **Qué necesita o pide**: ...
- **Siguiente paso natural en la relación**: ...

### Opción 1 — <etiqueta>
**Por qué este ángulo:** ...
**Mensaje:**
> ...

### Opción 2 — <etiqueta>
...

(Si solo merece la pena 2 alternativas, da 2.)
""".strip()

    return instrucciones + "\n" + "".join(bloques)


def prompt_buscar_gente(query: str) -> str:
    """Research focalizado: buscar gente concreta en la web para una petición."""
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("A qué tipo de gente me conviene conocer (úsalo como criterio)", perfiles.texto()),
    ]
    instrucciones = f"""
Eres mi agente de research de networking. Busca en la web (WebSearch / WebFetch) gente concreta que encaje con esta petición y con mi perfil/objetivos (abajo):

PETICIÓN: {query.strip()}

REGLAS:
- Búsqueda web REAL (snippets públicos de LinkedIn + páginas corporativas + prensa). NO inventes nombres.
- Devuelve entre 5 y 10 personas NOMBRADAS, reales y verificables. Si no encuentras con confianza, incluye menos. Mejor 5 sólidos que 10 inventados.
- Confidence honesto por persona: confirmed (fuente pública lo verifica) / inferred (plausible por timing/empresa) / speculative (vínculo débil).
- NO scrapees LinkedIn (solo lo indexado públicamente).
- Prioriza GENTE NUEVA, sin relación previa conmigo. NO propongas a nadie que siga trabajando en mis antiguas empresas (están en mi perfil): no busco volver a ellas. Un antiguo compañero solo vale si ya está en otra empresa y puede hacer de puente.

FORMATO DE SALIDA — devuelve SOLO una tabla markdown con EXACTAMENTE estas 7 columnas, sin texto antes ni después:

| # | Nombre | Rol actual | LinkedIn | Conexión contigo | Valor | Confidence |
|---|---|---|---|---|---|---|
| 1 | Nombre Apellido | Rol — Empresa | linkedin.com/in/... | de dónde / por qué encaja | por qué es valioso para el target | confirmed |
""".strip()
    return instrucciones + "\n" + "".join(bloques)


_COMENTARIO_INSTRUCCIONES = """
Eres mi coach de comunicación profesional. Voy a comentar PÚBLICAMENTE en un post de LinkedIn (Tier 3 — presencia ambiente). El objetivo NO es pedir nada ni vender — es aportar una perspectiva valiosa que me posicione positivamente en el radar del autor y su audiencia.

TAREA: ofréceme 2-3 comentarios alternativos con ángulos distintos. Para cada uno:
- Etiqueta corta del ángulo.
- Frase breve de por qué encaja con ESTE post concreto.
- El comentario completo, listo para publicar, respetando MI estilo y MUY breve (2-4 frases).

REGLAS DURAS (de la guía de comentario público):
- Cada comentario debe REFERENCIAR algo específico del post (demostrar que lo leí).
- Aportar sustancia: experiencia concreta, matiz, dato, o pregunta que abre conversación. NUNCA halago vacío ("gran post", "de acuerdo").
- Mi ángulo (intersección IA + governance + finanzas) solo si es relevante al post, sin forzarlo.
- NO pedir nada (ni conexión, ni café, ni trabajo).
- NO auto-promo, NO corregir agresivamente al autor, NO corporate-ese, NO emojis salvo que el tono del autor lo pida.
- Si el post es puro anuncio sin enganche genuino, DILO: mejor no comentar que comentar vacío.

FORMATO DE SALIDA: Markdown estricto.

### Opción 1 — <etiqueta>
**Por qué este ángulo:** ...
**Comentario:**
> ...

### Opción 2 — <etiqueta>
...

(Si solo merece la pena 2, da 2. Si el post no da pie a comentario sustantivo, dilo y no fuerces.)
""".strip()


def prompt_comentario_post_standalone(post_text: str, autor_info: str = "") -> str:
    """Comentar un post sin que el autor sea un contacto registrado."""
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    narrativa = identity.narrative(ESPACIO)
    estilo = identity.style(ESPACIO)
    plantilla = _read_optional(DATA_PATH / "plantillas" / "comentario-publico.md")

    if autor_info.strip():
        autor_bloque = _bloque("Quién publica el post / contexto", autor_info)
    else:
        autor_bloque = (
            "\n## Autor del post\n\n(No especificado — sin contexto del autor.)\n"
        )

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi pitch / narrativa", narrativa),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque("Guía de comentario público (principios, no plantilla)", plantilla),
        autor_bloque,
        _bloque("EL POST sobre el que voy a comentar", post_text),
    ]
    return _COMENTARIO_INSTRUCCIONES + "\n" + "".join(bloques)


def prompt_comentario_post(c: Contacto, post_text: str) -> str:
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    narrativa = identity.narrative(ESPACIO)
    estilo = identity.style(ESPACIO)
    plantilla = _read_optional(DATA_PATH / "plantillas" / "comentario-publico.md")
    contacto = _contacto_md(c)

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi pitch / narrativa", narrativa),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque("Guía de comentario público (principios, no plantilla)", plantilla),
        _bloque("El contacto (autor del post)", contacto),
        _bloque("EL POST sobre el que voy a comentar", post_text),
    ]

    instrucciones = """
Eres mi coach de comunicación profesional. Voy a comentar PÚBLICAMENTE en un post de LinkedIn de un contacto (Tier 3 — presencia ambiente). El objetivo NO es pedir nada ni vender — es aportar una perspectiva valiosa que me posicione positivamente en su radar y el de su audiencia.

TAREA: ofréceme 2-3 comentarios alternativos con ángulos distintos. Para cada uno:
- Etiqueta corta del ángulo.
- Frase breve de por qué encaja con ESTE post concreto.
- El comentario completo, listo para publicar, respetando MI estilo y MUY breve (2-4 frases).

REGLAS DURAS (de la guía de comentario público):
- Cada comentario debe REFERENCIAR algo específico del post (demostrar que lo leí).
- Aportar sustancia: experiencia concreta, matiz, dato, o pregunta que abre conversación. NUNCA halago vacío ("gran post", "de acuerdo").
- Mi ángulo (intersección IA + governance + finanzas) solo si es relevante al post, sin forzarlo.
- NO pedir nada (ni conexión, ni café, ni trabajo).
- NO auto-promo, NO corregir agresivamente al autor, NO corporate-ese, NO emojis salvo que el tono del autor lo pida.
- Si el post es puro anuncio sin enganche genuino, DILO: mejor no comentar que comentar vacío.

FORMATO DE SALIDA: Markdown estricto.

### Opción 1 — <etiqueta>
**Por qué este ángulo:** ...
**Comentario:**
> ...

### Opción 2 — <etiqueta>
...

(Si solo merece la pena 2, da 2. Si el post no da pie a comentario sustantivo, dilo y no fuerces.)
""".strip()

    return instrucciones + "\n" + "".join(bloques)


def prompt_reactivacion_dormant_tie(c: Contacto) -> str:
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    narrativa = identity.narrative(ESPACIO)
    estilo = identity.style(ESPACIO)
    plantilla = _read_optional(
        DATA_PATH / "plantillas" / "dormant-tie-reactivation.md"
    )
    contacto = _contacto_md(c)

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi pitch / narrativa", narrativa),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque(
            "Guía de reactivación de dormant tie (principios, no plantilla)",
            plantilla,
        ),
        _bloque("El contacto a reactivar", contacto),
    ]

    instrucciones = """
Eres mi coach de comunicación profesional. Necesito redactar un MENSAJE DE REACTIVACIÓN a un dormant tie — un conocido con quien tengo historial pero llevo tiempo (típicamente >2 años) sin contacto.

CONTEXTO CRÍTICO (mecánica distinta del primer contacto frío):
- NO soy un desconocido para esta persona. Hay confianza histórica.
- El objetivo NO es pedir nada. Es reabrir la conversación con curiosidad genuina.
- Regla dura: PING primero, ASK después. NUNCA pedir favor/trabajo en el primer mensaje de reactivación.
- Principio estratégico: NO busco volver a la empresa donde coincidimos. Reactivo para construir puente hacia cosas NUEVAS (colaboración, intro a un tercero, conocimiento, amistad).

TAREA: ofréceme 2-3 alternativas de mensaje de reactivación con ángulos distintos. Para cada una:
- Etiqueta corta del ángulo.
- Frase breve de por qué encaja con este contacto concreto.
- El mensaje completo, listo para enviar, respetando MI estilo (longitud objetivo <70 palabras, lista negra de palabras, tono cálido-pero-no-falso).

REGLAS DURAS (de la guía de reactivación):
- Apertura que reconoce el gap temporal SIN culpabilizar ("hace tiempo que no hablamos"), nunca "siento no haber escrito antes".
- Razón concreta de por qué me acuerdo de esta persona AHORA: algo específico (un post suyo, un cambio profesional, un tema que compartíamos). Si NO hay signal concreto en los datos del contacto, DILO arriba y pídeme que aporte uno antes de redactar — NO inventes el signal.
- Curiosidad genuina o algo que ofrezco, NO un ask.
- Salida abierta y ligera.
- Idioma: español por defecto. Si el contacto es UK / internacional, ofréceme TAMBIÉN una variante en inglés.

FORMATO DE SALIDA: Markdown estricto.

(Si falta el signal concreto:)
## Falta contexto
- Necesito que me digas: ...

(Cuando haya con qué redactar:)

### Opción 1 — <etiqueta>
**Por qué este ángulo:** ...
**Mensaje:**
> ...

### Opción 2 — <etiqueta>
...

(Si solo merece la pena 2 alternativas, da 2.)
""".strip()

    return instrucciones + "\n" + "".join(bloques)


def prompt_follow_up(c: Contacto) -> str:
    perfil = identity.profile(ESPACIO)
    objetivos = identity.goals(ESPACIO)
    narrativa = identity.narrative(ESPACIO)
    estilo = identity.style(ESPACIO)
    plantilla_follow_up = _read_optional(DATA_PATH / "plantillas" / "follow-up.md")
    plantilla_post_cafe = _read_optional(DATA_PATH / "plantillas" / "post-cafe.md")
    plantilla_post_entrevista = _read_optional(
        DATA_PATH / "plantillas" / "post-entrevista.md"
    )
    contacto = _contacto_md(c)

    bloques = [
        _bloque("Mi perfil", perfil),
        _bloque("Mis objetivos", objetivos),
        _bloque("Mi pitch / narrativa", narrativa),
        _bloque("Mi estilo de comunicación", estilo),
        _bloque("Guía de follow-up tras silencio", plantilla_follow_up),
        _bloque("Guía de mensaje post-café / post-llamada", plantilla_post_cafe),
        _bloque("Guía de mensaje post-entrevista", plantilla_post_entrevista),
        _bloque("El contacto (incluye histórico completo)", contacto),
    ]

    instrucciones = """
Eres mi coach de comunicación profesional. Necesito redactar un MENSAJE DE SEGUIMIENTO a un contacto con el que ya he tenido alguna interacción previa.

PASO 1 — DIAGNÓSTICO (antes de redactar):
Lee el histórico del contacto que viene abajo y determina:

1. ¿Qué tipo de mensaje toca exactamente?
   - **Recordatorio suave** (silencio tras primer mensaje, 3-7 días): plantilla follow-up.
   - **Segundo follow-up** (silencio tras un follow-up previo, 7-14 días): plantilla follow-up, tono aún más ligero.
   - **Respuesta a su respuesta** (la última interacción fue una respuesta del contacto): no es follow-up, es continuar la conversación.
   - **Post-café / post-llamada** (última interacción fue una conversación): plantilla post-café, en <24h.
   - **Post-entrevista** (última interacción fue una entrevista formal): plantilla post-entrevista, el mismo día o el día siguiente.
   - **Re-activación** (silencio >30 días): retomar contacto con un buen pretexto.

2. ¿Cuántos follow-ups frías he enviado ya sin respuesta?
   - Si he enviado 2 follow-ups frías sin respuesta → DETÉN y dime claramente que toca dejar respirar. NO redactes mensaje a no ser que yo te lo pida explícitamente.
   - Si la última fue una respuesta del contacto, no aplica esta regla.

3. ¿Cuántos días han pasado desde la última interacción?

PASO 2 — REDACCIÓN:
Cuando esté claro el tipo, ofréceme 2-3 alternativas con tonos o ángulos distintos. Para cada alternativa:

- Una etiqueta corta del ángulo/tono.
- Una frase breve explicando por qué encaja con la conversación previa.
- El mensaje completo, listo para enviar, respetando MI estilo (longitudes máximas, lista negra de palabras).

REGLAS DURAS:
- Cada alternativa debe REFERENCIAR de forma natural algún elemento concreto del histórico (no obligar al contacto a "rescatar" mentalmente quién soy).
- Sin tono de reproche ni recordatorio del tiempo pasado ("hace una semana que no me respondes...").
- Siempre salida fácil.
- Si la situación claramente NO es "toca follow-up" (caso de dejar respirar), DILO arriba y NO inventes mensaje.

FORMATO DE SALIDA: Markdown estricto.

## Diagnóstico
- **Tipo detectado**: ...
- **Días desde última interacción**: ...
- **Decisión**: redacto / mejor esperar (con justificación)

(Si la decisión es "redacto":)

### Opción 1 — <etiqueta>
**Por qué este ángulo:** ...
**Mensaje:**
> ...

### Opción 2 — <etiqueta>
...

(Si solo merece la pena 2 alternativas, da 2.)
""".strip()

    return instrucciones + "\n" + "".join(bloques)
