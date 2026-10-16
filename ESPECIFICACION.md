# ESPECIFICACIÓN — Piloto de edición concurrente y seguimiento de campo

Versión 1.0 · 13 de octubre de 2026

## 1. Propósito

Demostrar, con datos públicos y sin infraestructura institucional, un flujo completo de
edición concurrente de una capa vectorial (escritorio y campo), con control de acceso,
auditoría y tablero de avance, para derivar de ahí **requerimientos precisos** que TI
pueda evaluar y aprobar para un operativo nacional.

## 2. Alcance del piloto

| Dimensión | Piloto | Producción (referencia) |
|---|---|---|
| Datos | 1.432 polígonos públicos, distrito 20205 | ~90.000 fincas agropecuarias |
| Personas editando | 2 (`edit_lote_a`, `edit_lote_b`) | ~500 censistas + ~200 supervisores |
| Base de datos | Neon, plan gratuito | PostgreSQL/PostGIS institucional |
| Campo | QField + QFieldCloud (prueba 28 días o autoalojado) | QFieldCloud autoalojado |
| Tablero | HTML estático, GitHub Pages | Mismo script, cron + web interno (o Metabase) |
| Confidencialidad | Pública | Estadística confidencial: solo infraestructura INEC |

## 3. Estado por fase

### Fase 1 — Edición concurrente desde escritorio — COMPLETADA
- Base en Neon, esquema `mgn`, tabla `deteccion_cambio` (1.432 MultiPolygon, EPSG:5367).
- Roles `edit_lote_a` / `edit_lote_b`; RLS con lectura total y escritura por lote.
- Trigger de auditoría; vistas de seguimiento; prueba cruzada validada por dos personas.
- Guía de replicación y plantillas parametrizadas entregadas.

### Fase 2 — Capa de visita y tablero HTML — COMPLETADA (2026-10-15)
**Objetivo:** un supervisor consulta desde el celular, de noche, el avance del día.

Criterios de aceptación:
- [x] `mgn.finca_visita` creada: un punto por finca, **dentro** de su polígono (1.432/1.432).
- [x] RLS por lote funcionando también en la capa de puntos (probado con roles de edición).
- [x] Rol `tablero_lectura` que solo ve las cinco vistas `v_tab_*`.
- [x] Visitas de prueba registradas desde QGIS por A y por B.
      Nota: A desde QGIS por la persona (15 visitas con `edit_lote_a`); B simulado por script
      (`sql/08_visitas_prueba_lote_b.sql`, 20 visitas con `edit_lote_b`), no desde QGIS. Sesión 02.
- [x] `generar_tablero.py` produce el HTML con datos reales; capturas a 1100 y 400 px sin defectos.
      Evidencia: `docs/evidencia/2026-10-15_tablero_1100.png` y `_400.png` (sesión 02).
- [x] GitHub Actions regenera y publica el tablero cada 30 minutos sin intervención.
      Alcance (sesión 07): probado que regenera y publica sin intervención; la frecuencia de
      30 min no está demostrada (ver nota de la sesión 07).
      Evidencia: ejecuciones 38800395636 y 38800575730 en verde; cron `*/30` activo. URL:
      https://maib86.github.io/PROYECTO_NEON_CENSO/ (sesión 03).
      Nota (sesión 06): tras la regeneración manual de las 16:46 del 15/10 no se registraba
      ninguna ejecución por `schedule` (`docs/evidencia/s06/01_tablero_publicado.txt`). La
      regeneración programada está configurada pero sin observar; causa sin diagnosticar.
      Nota (sesión 07): primera ejecución por horario, `38822130963`, el 15/10 a las 17:12,
      casi 3 h después de crear el flujo; a las 17:58 seguía siendo la única
      (`docs/evidencia/s07/01_regeneracion_y_tablero.txt`). Sin causa visible en el
      repositorio; GitHub puede retrasar u omitir ejecuciones por horario. La frecuencia de
      30 min no está demostrada (req. 14).
- [x] El HTML publicado no contiene credenciales (verificado por `revisor-auditoria`, sesión 03).

Pendiente de la persona: campos temáticos del formulario de visita (cuestionario real).
Hasta entonces, solo campos estructurales: `estado_visita`, `encuestador`, `fecha_visita`,
`observaciones`, precisión GNSS, posición de registro.

### Fase 3 — Campo con QField — EN CURSO (dividida por D-22)
**Objetivo:** dos personas editan puntos en QField; el tablero refleja ambas fuentes.

Parte 1 (D-22): QField con conexión directa a Neon por `pg_service` en el dispositivo, sin
QFieldCloud. Parte 2: QFieldCloud con PostGIS y edición offline, pendiente de la cuenta del
INEC. Evidencia de la parte 1: `docs/evidencia/s05/05_prueba_qfield_directa.txt`, sesión 05.

Criterios de aceptación:
- [ ] Proyecto QGIS con `finca_visita` (editable) y `deteccion_cambio` (referencia) publicado
      en QFieldCloud en modo **offline editing**.
  - [x] Proyecto construido por script (`campo/NEON_campo_lote_A.qgs`), con «offline editing»
        en QFieldSync, y usado en el celular por conexión directa (parte 1).
  - [ ] Publicado en QFieldCloud: pendiente de la cuenta del INEC (D-22).
- [ ] Formulario con valores por defecto: `encuestador = @cloud_username`,
      `fecha_visita = now()`, `precision_gnss_m = @position_horizontal_accuracy`.
  - [x] Configurado (D-19) y aplicado en el celular: `fecha_visita` distinta en cada una de
        las 3 visitas; `precision_gnss_m` con valor (1.5).
  - [x] Desfase de 6 h en `fecha_visita` (hora local guardada como UTC) corregido con D-23:
        zona de sesión fijada en la base; las 3 filas de prueba corregidas (`sql/10`).
  - [x] Visita repetida desde el celular tras D-23 (polígono 1396, id de fila 1394): `fecha_visita` 25 s antes de
        `fecha_edicion`, sin desfase.
  - [ ] `encuestador = @cloud_username`: NULL sin sesión de QFieldCloud (esperado); pendiente
        de la cuenta del INEC (D-22).
- [ ] Credenciales de base en QFieldCloud como secreto `pg_service`, no en el `.qgs`.
  - [x] No están en el `.qgs` (solo `service='neon_lote_a'`; escaneo 0).
  - [ ] Secreto `pg_service` en QFieldCloud: pendiente de la cuenta del INEC (D-22). En la
        parte 1 la clave vive en el dispositivo (solo piloto; requerimiento TI 10).
- [ ] Edición sin señal → sincronización → visible en tablero. Documentado el tiempo real
      entre sincronización y aparición.
  - [x] Edición con señal desde el celular escrita en la base con el rol del lote:
        `editado_por = edit_lote_a` en las 3 visitas (la política la aplica la base de datos a la conexión).
  - [x] `observaciones` presentes en la tabla y ausentes del tablero generado con datos
        actuales (0 coincidencias). Falta confirmar en el tablero publicado tras la próxima
        regeneración.
  - [ ] Edición sin señal y sincronización: pendiente de la cuenta del INEC (D-22).
- [ ] Identidad de campo visible en `v_tab_encuestador` por atributo, no por `current_user`.
  - [ ] Pendiente de la cuenta del INEC: sin QFieldCloud no hay `@cloud_username`. En la
        parte 1 la identidad es el rol (`editado_por`), por equipo y no por persona.

Decisión abierta: QFieldCloud en nube (prueba 28 días) vs autoalojado desde el piloto.

### Fase 4 — Requerimientos para TI — EN CURSO: entregables v3 generados tras la auditoría de comunicación ronda 2 (S08, D-27); ronda 3 externa y revisión de la persona pendientes
Entregables v1 (sesión 06): `docs/requerimientos_ti/REQUERIMIENTOS_TI.md` (versionado), con su
banco de cifras `CIFRAS.csv` y `verificar_cifras.py`; PDF y presentación del 2026-10-19 en
`docs/presentacion/` (fuera del repositorio, D-24). Pendiente: revisión de la persona.
Documento en `docs/requerimientos_ti/` con: arquitectura, dimensionamiento para 90.000
fincas / 700 personas, seguridad (TLS, roles, RLS, secretos, respaldos, MDM), costos
comparados (nube vs autoalojado), y evidencia del piloto por cada punto.

## 4. Restricciones técnicas (no negociables)

1. Llave primaria entera. 2. Columna de reparto NOT NULL + CHECK. 3. Geometría con tipo y
SRC explícitos. 4. Un usuario por persona. 5. Credenciales nunca en archivos versionados.
6. Toda afirmación sobre la base respaldada por una consulta con resultado.

## 5. Fuera de alcance del piloto

Edición simultánea del mismo objeto por dos personas; historial completo de cambios
(bitácora) — pendiente de decisión; integración con sistemas del INEC; datos reales.

## 6. Referencias

- `docs/guia/Guia_replicacion_PostGIS.md` — procedimiento completo.
- `docs/DECISIONES.md` — decisiones y su justificación.
- Neon, ventana de restauración (6 h en plan gratuito): https://neon.com/docs/introduction/restore-window
- QField, modos con PostGIS: https://docs.qfield.org/get-started/tutorials/advanced-setup-qfc/
- QField, variables: https://docs.qfield.org/reference/expression_variables/
- QFieldCloud, planes: https://qfield.cloud/pricing
