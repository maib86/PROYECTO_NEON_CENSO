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

### Fase 2 — Capa de visita y tablero HTML — EN CURSO
**Objetivo:** un supervisor consulta desde el celular, de noche, el avance del día.

Criterios de aceptación:
- [x] `mgn.finca_visita` creada: un punto por finca, **dentro** de su polígono (1.432/1.432).
- [x] RLS por lote funcionando también en la capa de puntos (probado con roles de edición).
- [x] Rol `tablero_lectura` que solo ve las cinco vistas `v_tab_*`.
- [ ] Visitas de prueba registradas desde QGIS por A y por B.
- [ ] `generar_tablero.py` produce el HTML con datos reales; capturas a 1100 y 400 px sin defectos.
- [ ] GitHub Actions regenera y publica el tablero cada 30 minutos sin intervención.
- [ ] El HTML publicado no contiene credenciales (verificado por `revisor-auditoria`).

Pendiente de la persona: campos temáticos del formulario de visita (cuestionario real).
Hasta entonces, solo campos estructurales: `estado_visita`, `encuestador`, `fecha_visita`,
`observaciones`, precisión GNSS, posición de registro.

### Fase 3 — Campo con QField — PENDIENTE
**Objetivo:** dos personas editan puntos en QField; el tablero refleja ambas fuentes.

Criterios de aceptación:
- [ ] Proyecto QGIS con `finca_visita` (editable) y `deteccion_cambio` (referencia) publicado
      en QFieldCloud en modo **offline editing**.
- [ ] Formulario con valores por defecto: `encuestador = @cloud_username`,
      `fecha_visita = now()`, `precision_gnss_m = @position_horizontal_accuracy`.
- [ ] Credenciales de base en QFieldCloud como secreto `pg_service`, no en el `.qgs`.
- [ ] Edición sin señal → sincronización → visible en tablero. Documentado el tiempo real
      entre sincronización y aparición.
- [ ] Identidad de campo visible en `v_tab_encuestador` por atributo, no por `current_user`.

Decisión abierta: QFieldCloud en nube (prueba 28 días) vs autoalojado desde el piloto.

### Fase 4 — Requerimientos para TI — PENDIENTE
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
