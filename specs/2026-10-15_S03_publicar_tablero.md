# SPEC S03 — Publicar el tablero y cerrar la Fase 2

Fecha: 2026-10-15 · Plazo del piloto: 2026-10-16 15:00 (presentación lunes)
Objetivo: cumplir los criterios 6 y 7 de la Fase 2 y marcar la Fase 2 como COMPLETADA.
Principio: automatizar todo; detenerse solo ante riesgo alto (publicar en repositorio
público, reescribir historial) mostrando el comando exacto.

## 0. Decisiones que se registran (sin trabajo asociado hoy)
- D-16 · `fecha_visita` la fija el trigger solo si llega NULL; en QField la pone el
  formulario con now() del dispositivo; desde QGIS queda la hora de guardado y se declara
  así. Se implementa en S05 (sql/09).
- D-17 · `NEON.qgz` sale del repositorio (contiene el host; QGIS puede guardar la clave en
  texto plano). Vuelve en S05 cuando use pg_service.
- LIMIT 25 en movimientos se mantiene. Defectos latentes del tablero: pendientes.

## 1. Carpeta de specs y reglas en CLAUDE.md
- Estructura: agregar `specs/` (convención `specs/AAAA-MM-DD_SNN_nombre.md`; un spec = un
  encargo = un /clear).
- «Estado actual», punto 4: «specs/ — el encargo vigente; si el prompt dice "ejecutá
  specs/X", ese archivo manda».
- «Reglas que no se negocian», agregar: «Automatización por defecto. Se propone primero la
  vía más automatizable y reproducible. Un paso manual solo por: (a) solo lo puede hacer una
  persona; (b) decisión de diseño; (c) riesgo alto (borrar, cambiar políticas, rotar
  credenciales, publicar en público, gastar), con el comando exacto a la vista. Se dice cuál
  aplica.»

## 2. Limpieza antes del primer push
1. `git rm --cached NEON.qgz`; `*.qgz` a .gitignore.
2. Si `py -m pip install git-filter-repo` funciona: `git filter-repo --path NEON.qgz
   --invert-paths` (riesgo alto: mostrar y esperar confirmación). Si no, no reescribir y
   anotar que el host figura en el historial, sin credenciales.
3. Escaneo estricto del historial completo contra los valores reales de `.env`, sin
   imprimirlos: claves = 0, host = 0, identificador de endpoint (`ep-…`) = 0.
   `git log -p --all > hist.txt` y luego, con `py -I`, leer `.env`, extraer de cada
   `postgresql://usuario:CLAVE@HOST/...` la clave, el host y el endpoint, e imprimir solo
   `hist.count(valor)` sumado por tipo. Resultado esperado: `0 | 0 | 0`.
   (Corregido el 2026-10-15: el escaneo por patrón
   `git log -p --all | grep -ciE "npg_|password=|postgresql://[^ ]*:[^ ]*@"` da falsos
   positivos con los marcadores de la documentación —`CLAVE`, `<CLAVE>`, `CONTRASENA`— y no
   sirve como criterio; se conserva solo como inspección auxiliar.)

## 3. Workflow
`.github/workflows/tablero.yml`: usa `python` (no `py`); instala psycopg2-binary; secreto
DATABASE_URL_TABLERO; ejecuta tablero/generar_tablero.py; publica con
upload-pages-artifact + deploy-pages; cron `*/30 * * * *` y workflow_dispatch. Corregir lo
que falte. Probar el generador local una vez más.

## 4. Publicación
Comprobar `gh --version` y `gh auth status`.
Con gh autenticado:
1. `gh repo create PROYECTO_NEON_CENSO --public --source=. --remote=origin` (riesgo alto:
   mostrar y esperar confirmación).
2. `git push -u origin main`.
3. Secreto sin imprimirlo: `grep '^DATABASE_URL_TABLERO=' .env | cut -d= -f2- | tr -d "'\""
   | gh secret set DATABASE_URL_TABLERO`.
4. Pages: `gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow`.
5. `gh workflow run tablero.yml` y `gh run watch`.
Sin gh (o sin autenticación): si se puede instalar con winget sin administrador, instalar y
pedir a la persona solo `gh auth login`. Si no, detenerse y darle en orden: crear repo
público vacío; Claude Code hace el push; Settings → Secrets → DATABASE_URL_TABLERO;
Settings → Pages → GitHub Actions; Actions → Run workflow.

## 5. Verificación (criterio 7)
URL https://<usuario>.github.io/<repo>/ : HTTP 200; hora de generación de hoy en
America/Costa_Rica; `grep -ciE "neon\.tech|npg_|postgresql://|observaciones|PRUEBA 08"`
sobre el HTML descargado = 0; A 2,1 % (15/709) y B 2,1 % (15/723); revisor-auditoria sin
bloqueantes; segunda ejecución del workflow en verde.

## 6. Cierre
ESPECIFICACION: criterios 6 y 7 [x], Fase 2 COMPLETADA con fecha. DECISIONES: D-16, D-17.
Bitácora con URL pública y resultados literales. Commit y push. Resumen de 10 líneas.

## Criterios de aceptación
- [ ] Historial sin credenciales (escaneo estricto contra `.env`: claves 0, host 0,
      endpoint 0); NEON.qgz fuera del repositorio.
- [ ] Tablero en URL pública con datos de hoy, sin credenciales ni host.
- [ ] Workflow en verde dos veces; cron activo.
- [ ] Fase 2 COMPLETADA; D-16 y D-17; CLAUDE.md con specs/ y la regla de automatización.

## Fuera de alcance
pg_service, sql/09, UGM, QField, documento TI.