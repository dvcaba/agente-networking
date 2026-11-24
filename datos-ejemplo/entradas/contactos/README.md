# Contactos

Cada archivo `.md` de esta carpeta representa **un contacto** de tu networking.

## Convenciones

- **Nombre del archivo**: `nombre-apellido.md` en kebab-case (minúsculas, guiones, sin acentos).
  - Ej: `ana-lopez.md`, `juan-perez-gomez.md`.
- **Un archivo = una persona**.
- **No borrar archivos**: aunque un contacto se enfríe o quede inactivo, su histórico es valioso.

## Estructura interna

Cada archivo sigue el formato definido en `CLAUDE.md` (sección "Formato estándar del archivo de un contacto"):

- Datos del contacto
- Estado actual (temperatura + próxima acción + fecha)
- Histórico cronológico de interacciones

## Cómo se rellenan

Tú no editas estos archivos a mano (aunque puedes). El agente los crea y los actualiza cuando le pides cosas como:

- *"Voy a contactar a Ana López, [datos]…"* → crea el archivo nuevo
- *"Ana me ha respondido [...]"* → añade entrada al histórico
- *"Marca a Carlos como caliente, vamos a entrevista"* → actualiza el estado
