# PROYECTO_NEON_CENSO — Memoria del proyecto para Claude Code

## Qué es esto

Piloto de **edición concurrente de capas vectoriales** para un operativo de campo del INEC:
PostgreSQL + PostGIS en Neon (nube, plan gratuito), edición desde QGIS escritorio y QField
en campo, control de acceso por fila, auditoría, y un tablero HTML de avance.

El piloto corre con **datos públicos** (1.432 polígonos de detección de cambio, distrito 20205).
Su propósito es producir **evidencia y requerimientos precisos para TI** antes de escalar a
producción: ~90.000 fincas agropecuarias, ~500 censistas, ~200 supervisores, en infraestructura
institucional.

Idioma de trabajo: **español**. Voz institucional, neutra. Sin emojis en documentos.

## Estado actual — leer SIEMPRE al iniciar

1. `ESPECIFICACION.md` — alcance, fases y criterios de aceptación.
2. `docs/sesiones/` — la sesión más reciente dice exactamente dónde quedó todo.
3. `docs/DECISIONES.md` — por qué las cosas son como son. No se revierte una decisión
   registrada sin registrar la nueva.

## Estructura

```
sql/                      Scripts SQL. Numerados en orden de ejecución.
  plantillas/             Versión parametrizada (<<<MARCADORES>>>) para replicar.
  ejemplos_.../           Scripts tal como se ejecutaron en el piloto. NO re-ejecutar.
  06_centroides_visita.sql  Siguiente paso pendiente (ver sesión más reciente).
tablero/                  Generador del tablero HTML (Python) + fixture de prueba.
.github/workflows/        Regeneración automática del tablero en GitHub Actions.
docs/guia/                Guía de replicación (fuente de verdad del procedimiento).
docs/sesiones/            Bitácora por sesión. Una por sesión de trabajo.
docs/requerimientos_ti/   Documento de requerimientos para producción (fase final).
datos_prueba/             GeoJSON de origen del piloto.
```

## Reglas que no se negocian

**Credenciales.** Viven solo en `.env` (ignorado por git). Nunca en código, en SQL, en
documentos, en commits ni en la salida de un comando. Si un comando las imprimiría, no se
ejecuta. `.env.example` muestra la forma sin valores.

**Base de datos.** Se accede con `psql "$DATABASE_URL"` (rol `neondb_owner`) o con
`$DATABASE_URL_TABLERO` (rol `tablero_lectura`, solo lectura). Antes de cualquier
`DROP`, `TRUNCATE`, `DELETE` sin `WHERE`, `ALTER ... DROP` o cambio de políticas RLS:
**detenerse y pedir confirmación explícita**, mostrando el SQL exacto. Si el MCP de Neon
está disponible, los cambios de esquema se prueban primero en una rama (branch) de Neon y
solo después se aplican a `production`.

**Verificación.** Nada se da por hecho. Todo cambio en la base termina con la consulta que
lo demuestra (conteo, SRID, RLS activo, etc.) y su resultado queda en la bitácora de sesión.
El esquema de referencia: `sql/plantillas/05_verificaciones.sql`.

**Trazabilidad.** Cada cambio significativo = un commit con mensaje en español, en
imperativo, que diga QUÉ y POR QUÉ (`feat(sql): crear capa finca_visita — un punto por finca
para el formulario de campo`). Decisiones de diseño van a `docs/DECISIONES.md` con fecha.
Al cerrar cada sesión se escribe `docs/sesiones/AAAA-MM-DD_sesion-NN.md` con la plantilla.

**Sin inventar.** Los campos del cuestionario del censo, los nombres de equipos, los
umbrales operativos: solo si la persona los da. Si falta un dato, se pregunta; no se rellena.

**Lo que Claude Code NO hace.** QGIS y QField son interfaces gráficas que opera la persona.
Cuando un paso ocurre ahí, Claude Code produce la instrucción exacta (menú, campo, valor) y
espera la confirmación o la captura. No simula que lo hizo.

## Entorno

- Windows. Shell: Git Bash (o PowerShell). `psql` debe estar en PATH de usuario
  (`C:\Program Files\PostgreSQL\18\bin`). Cliente psql 18.6 contra servidor Neon 16/17
  (compatible hacia atrás; ver D-12).
- Python: invocar **siempre con `py`** (`py script.py`, `py -m pip ...`), nunca `python`:
  en esta máquina `python` lo intercepta el alias de Microsoft Store (ver D-12).
  Python 3.12+ con `psycopg2-binary`, `shapely`, `pyproj`, `playwright` (para capturas
  del tablero; navegador con `py -m playwright install chromium`).
- Host de Neon **sin** sufijo `-pooler`. `sslmode=require` siempre.
- Zona horaria del operativo: `America/Costa_Rica`.

## Convenciones técnicas (resumen; detalle en docs/guia)

- Llave primaria entera `id` (IDENTITY). Identificador de origen en `id_origen`.
- Columna de reparto `lote` (`A`/`B`), `NOT NULL` + `CHECK`. RLS: lectura total, escritura
  acotada por lote. El propietario omite RLS: **probar siempre con los roles de edición**.
- Geometría con tipo y SRC explícitos: `geometry(MultiPolygon, 5367)` / `geometry(Point, 5367)`.
- Auditoría por trigger (`fn_sello_auditoria`). Desde QField, la identidad llega por
  atributo (`encuestador` = `@cloud_username`), no por `current_user`.
- El tablero lee solo vistas `v_tab_*` con el rol `tablero_lectura`.

## Agentes del proyecto (`.claude/agents/`)

| Agente | Para qué | Nunca |
|---|---|---|
| `ingeniero-bd` | SQL, PostGIS, migraciones, verificaciones contra Neon | Ejecutar destructivos sin confirmación |
| `desarrollador-tablero` | Generador HTML, Python, capturas, GitHub Actions | Tocar la base en escritura |
| `revisor-auditoria` | Revisión independiente de lo hecho contra la spec y las reglas | Editar archivos |
| `documentador` | Bitácora de sesión, decisiones, guía, requerimientos TI | Inventar datos |

Flujo normal: `ingeniero-bd` o `desarrollador-tablero` hacen → `revisor-auditoria` revisa
→ `documentador` registra. El revisor no ve la conversación: se le pasa el diff o los
archivos, no las conclusiones.

## Al cerrar sesión

1. Verificaciones ejecutadas y resultados anotados.
2. Commit de todo lo cambiado.
3. `docs/sesiones/AAAA-MM-DD_sesion-NN.md` escrito con: qué se hizo, qué se verificó,
   decisiones nuevas, qué queda pendiente y cuál es el siguiente paso exacto.
4. Resumen de 10 líneas para pegar en el proyecto de Claude web.
