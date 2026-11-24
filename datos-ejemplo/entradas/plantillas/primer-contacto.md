# Guía: primer contacto

> Versión revisada 2026-05-24. Cada principio sourceado contra `research/networking/02-cold-outreach-empirico.md`. Calibración tonal: `estilo.md` Bloque 3.
>
> **No es plantilla para rellenar huecos.** Son principios y estructura que el agente usa para crear cada mensaje desde cero, personalizado al contacto concreto.

---

## Objetivo

**Abrir una conversación**, no pedir trabajo. Pedir trabajo en primer contacto activa rechazo defensivo. Si el receptor percibe que vas detrás de un favor, casi siempre no contesta.

---

## Calibra el modo antes de redactar

La aproximación cambia según con quién contactes (`research/networking/01-fundamentos.md` §2.1):

| Modo | Cuándo | Aproximación |
|---|---|---|
| **Dormant tie** | Conocido con historial >2 años sin contacto | Ver `dormant-tie-reactivation.md`. Otra mecánica, NO uses esta. |
| **Warm intro** | Hay contacto común mutuo que puede hacer intro | Pide al mutual intro primero. Tu "primer mensaje" real es el segundo. |
| **Cold target banca/Big4/seguros** | Senior en sector regulado | **Strong ties pesan más** (Pellizzari 2010, Bian 1997). Prioriza warm-via-intro sobre cold. Si cold, máxima personalización de signal. |
| **Cold target IA pura senior** | Senior en sector digital (scaleups, AI labs, IA aplicada) | Weak/medium ties + LinkedIn funcionan (Rajkumar 2022 — efecto fuerte en sectores digitales). Cold con signal-based es viable. |

---

## Longitudes objetivo (sourced)

- **LinkedIn DM primer mensaje**: **<400 caracteres** (+22% response rate vs media — LinkedIn first-party data). 3-5 líneas, ~50-80 palabras.
- **Email primer contacto**: **<80-125 palabras** (Boomerang 40M + Lavender 1B + Instantly 2026). 4-6 líneas + saludo + firma.

Si supera, sobra algo.

---

## Estructura — 4 elementos

### 1. Punto de conexión real específico (3-10 palabras)
Algo que demuestra que NO es masivo: post reciente concreto, contacto común por nombre, universidad compartida, sector, decisión de su empresa, paper.

**Sourcing**: signal-based personalization **triplica** response rate vs superficial (Lavender 1B). Combinado con subject personalizado: +160% (Backlinko 12M). Activa Liking + Unity simultáneamente.

**Si no hay punto de conexión real → no es buen contacto para mensaje frío.** Busca puente humano antes.

### 2. Razón concreta de por qué le escribes a esta persona específica (1-2 líneas)
Algo que NO valdría para 100 personas distintas.

### 3. Petición pequeña y específica (1 frase)
Pregunta corta, opinión sobre algo concreto, o invitación a café 15-20 min.

**Sourcing**: soft CTAs rinden **3× mejor** que hard CTAs — 4.2% vs 1.4% (Prospeo 304K emails).

**Nunca**: "¿podemos hablar?" a secas, "¿reservemos 30 min el martes?" (hard CTA), "tengo unas preguntas que hacerte" (labor para el receptor).

### 4. Salida fácil (1 frase corta)
"Si no es buen momento, sin problema", "lo que te encaje", "te leo".

**Sourcing**: reducir coste social de no responder mejora response rate empíricamente. Explicit out + soft CTA combinados son el patrón con mayor reply rate.

---

## Anti-patrones AI-era 2026

Se identifican como "template AI-generated" en segundos (arxiv 2501.15654, 2025: usuarios frecuentes de ChatGPT detectan AI text con alta precisión):

- ❌ Frases blacklist `estilo.md` ("Encantado de conectar", "Vi tu perfil y me parece muy interesante", "Sería un placer", "Quedo a tu disposición", "Aporta valor", etc.).
- ❌ Auto-presentación larga antes de ofrecer algo concreto al receptor.
- ❌ Personalización solo en `{first_name}` + `{company}` — sin signal específico equivale a template.
- ❌ Em-dashes superfluos en cadena (firma típica LLM mal disimulado).
- ❌ Mensaje largo contando todo tu CV.
- ❌ Adjuntar CV en primer mensaje sin que te lo pidan.
- ❌ Pedir trabajo o referral en primer mensaje.

---

## Lo que SÍ funciona (sourced)

- ✅ **Signal-based personalization** (post reciente, decisión empresa, paper, movimiento). Triplica response rate (Lavender 1B).
- ✅ **Dar antes de pedir** ("estoy investigando X, me he encontrado con esto que igual te interesa..."). Grant 2013.
- ✅ **Contacto común mencionado por nombre** ("X me sugirió que te escribiera") **solo si X lo hizo realmente** (Lebherz 2009: name-dropping fake rebaja credibilidad).
- ✅ **Pregunta específica sobre su trabajo/sector**, no sobre el tuyo.
- ✅ **Unity explícita** ("ambos en intersección X" / "ambos venimos de Y"). Tier 1 en networking profesional.

---

## Ejemplo — target banca regulada

> Hola Ana, leí tu post de la semana pasada sobre cómo estáis abordando el DPIA para el modelo de scoring en BBVA. Lo pregunto en concreto porque estoy implementando ahora mismo un sistema high-risk Annex III en mi empresa y me he encontrado con un tema parecido al que mencionas sobre [punto específico]. ¿Tu equipo lo está atacando con [enfoque X] o tenéis otro ángulo? Un café cuando te venga, sin compromiso.

**Por qué funciona**: 65 palabras (<400 chars LinkedIn-óptimo). Signal-based (post + banco + punto específico). Una pregunta abierta. Soft CTA. Unity implícita (ambos AI Solutions Architects implementando EU AI Act). Salida fácil.

## Ejemplo — target AI pura senior

> Hola Marc, leí tu charla en MLOps Community sobre patterns de eval para agentes multi-paso. La pregunta concreta: en tu stack usáis LLM-as-judge para el critic agent o lo tenéis con métricas deterministas? Estoy montando algo parecido sobre LangGraph y nos hemos topado con drift en el judge. Te leo si te apetece comentarlo, sin presión.

Misma estructura, vocabulario técnico más denso, sin layer de governance (el target es IA pura, no banca regulada).

---

## Tonalidad

Aplicar `estilo.md` Bloque 3:
- Tú, no usted. Saludo simple.
- Vocabulario "concreto", "en concreto", "honestamente".
- Cierre: "Un saludo", "Gracias", "Te leo".
- Sin muletillas corporate.
