# agente-networking

Construir y cuidar tus relaciones profesionales: **a quién contactar, qué decirle y cuándo
volver a escribir**. El empleo es una salida posible, no la única — también colaboración,
freelance, co-fundar, compartir conocimiento o relocalización.

**Qué no hace, por diseño:** no automatiza envíos, no scrapea LinkedIn y no aplica a ofertas
en tu nombre. Tú envías y tú hablas; el agente razona, investiga, redacta, hace seguimiento y
mantiene el histórico.

## Arrancar

```bash
uv venv --python 3.12 ~/.venvs/agente-networking
uv pip install --python ~/.venvs/agente-networking/bin/python -e "./codigo[dev]"

~/.venvs/agente-networking/bin/python -m sistemas.networking.main   # http://127.0.0.1:8080
cd codigo && ~/.venvs/agente-networking/bin/python -m pytest      # pruebas
```

El entorno vive en `~/.venvs/`, fuera de la carpeta del proyecto: en WSL, instalar dentro de
`C:\` (`/mnt/c/...`) tarda muchísimo o se queda colgado. Tarda unos segundos en escuchar. No
uses el `python` del `PATH`: en WSL puede ser un shim de pyenv-win que no arranca y parece que
el proyecto está roto.

Variables (todas opcionales, en un `.env` en la raíz):

| Variable | Para qué | Por defecto |
|---|---|---|
| `AGENT_DATOS_NETWORKING` | Dónde están tus datos | `mis-datos/` si existe; si no, `datos-ejemplo/` |
| `APP_PORT` | Puerto de la web | `8080` |

## Qué hay dentro

Tres carpetas: el **código** y dos juegos de **datos**, para poder compartir la herramienta
sin lo tuyo:

```
agente-networking/
  codigo/                todo lo necesario para que funcione la app             → se comparte
    sistemas/networking/   el agente: pantallas, prompts, CLAUDE.md
    core/, apps/web/       el motor: fichas de agente, búsqueda con citas
  datos-ejemplo/         una persona inventada + plantillas para rellenar      → se comparte
  mis-datos/             TUS datos (fuera de git, no se comparte nunca)

mis-datos/ y datos-ejemplo/ tienen la misma forma:
  identidad/     quién eres: perfil, objetivos, tu pitch, cómo escribes
  entradas/      contactos, candidatos, estrategia, pendientes, plantillas de mensajes
  biblioteca/    lo que sabe el agente: investigación y libros
  .indice/       el índice de búsqueda de la biblioteca (se regenera solo)
```

La app usa `mis-datos/` si existe y, si no, `datos-ejemplo/`. Así, quien descarga el
proyecto puede probarlo enseguida, y para usarlo con lo suyo copia `datos-ejemplo/` como
`mis-datos/` y rellena las plantillas: lo explica `datos-ejemplo/LEEME.md`.

**Qué se comparte y qué no:**
- **Se comparte**: el código, las plantillas de mensajes y la investigación general sobre
  networking, sin nada personal.
- **No se comparte**: tu identidad, contactos, candidatos, estrategia, pendientes, CV, los
  estudios hechos a tu medida (salarios, sector) y los libros (tienen derechos de autor;
  `datos-ejemplo/biblioteca/oficial/LIBROS.md` dice cuáles son para que cada uno ponga su copia).

**Inicio** es la pantalla principal y funciona como un chat: arriba, los avisos en frases («Marc te
ha contestado», «Con Lucía la relación se está enfriando»), cada tipo en su apartado y **sin
tope**: Te han contestado, Tenías apuntado, Esperan un recordatorio, Se están enfriando y Gente
nueva por escribir (que incluye tus candidatos). Debajo, tus conversaciones, primero las que te necesitan. En cada conversación pegas lo que te
contestan en LinkedIn, el agente te propone 2-3 respuestas y, al pulsar «Lo he enviado», queda
apuntado en la ficha. Quién tiene el turno y qué merece aviso lo decide
`storage/conversacion.py` a partir del histórico de cada ficha; no hay otro almacén.

El resto: listado de contactos, ficha de contacto, candidatos, buscar gente, comentar un post,
asistente, biblioteca y estrategia.

**Tus datos son ficheros Markdown.** Puedes leerlos y editarlos a mano sin la aplicación, y la
aplicación se da cuenta sola (vigila los ficheros). Esto es a propósito: si un día el programa
estorba, los datos siguen siendo tuyos y legibles.

## De dónde viene

Esto era el sistema `networking` de **`agent-platform`**, sacado fuera el 2026-10-12 para
poder usarlo y compartirlo sin arrastrar la plataforma entera. La decisión, con su precio, está
en `agent-platform/docs/decisiones.md` D25 y D26.

- La copia que queda en la plataforma es una **foto congelada** de ese día. **Lo que vale está
  aquí.**
- El motor (`core/`, `apps/web/`) se copió **idéntico** y conviene no tocarlo: así, el día que
  la plataforma esté lista para reabsorber esto, lo único que haya que reconciliar es el
  código propio del networking.
- Por eso las carpetas se siguen llamando `sistemas/networking/`: la copia es fiel a propósito.
  Reordenarlas es una mejora pendiente, no un accidente.

**Lo único que se cambió al sacarlo** (todo lo demás es copia literal):

1. `main.py` llama a `discovery.load_all()` antes de definir las páginas. En la plataforma eso
   lo hacía su `apps/web/app.py`; aquí el punto de entrada es `main.py`, así que sin esa línea
   el registro de agentes quedaba vacío y el asistente no podía existir.
2. `ui/asistente.py` pedía el agente `marketing.networking.assistant`, un id del modelo viejo.
   El registro los indexa como `<sistema>.<nombre>`, así que ese id no resolvía nunca y la
   pantalla devolvía error 500. Ahora pide `networking.assistant`. **El mismo fallo está en la
   plataforma** (anotado en sus decisiones, apartado «Abiertas»); aquí está arreglado.
3. `core/espacio.py` acepta `AGENT_DATOS_<SISTEMA>` para que los datos de un sistema vivan
   fuera de su carpeta de código (2026-10-14). Sin esa variable se comporta igual que en la
   plataforma. Es el único cambio en el motor.

**Comprobado ejecutando** el 2026-10-13: las 8 pantallas responden 200, los 43 tests pasan y
el arranque no deja ni un error en el log.

## Pendiente

- Las carpetas `sistemas/networking/` son herencia de la plataforma (ver arriba).
- No existe `salidas/`: se crea cuando el agente produzca su primer documento.
