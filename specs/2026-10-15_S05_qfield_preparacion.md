# SPEC S05 — Preparar el proyecto de campo QField (lote A)

Fecha: 2026-10-15 · Plazo del piloto: 2026-10-16 15:00
Objetivo: dejar listo, sin credenciales en archivos versionados, el proyecto QGIS que la
persona sube a QFieldCloud para editar el lote A desde el celular. Claude Code prepara;
la carga a QFieldCloud y la prueba en el celular las hace la persona, guiada desde Claude web.

## 0. Permisos
Volver `git push *` a «ask» en `.claude/settings.json` (publicar en repo público = riesgo
alto). Mostrar el diff.

## 1. Decisiones que se registran
- D-19 · Un proyecto QFieldCloud por lote, cada uno con el rol de su lote en el secreto
  pg_service: el RLS protege también en campo, por equipo; la identidad individual llega
  por `encuestador = @cloud_username`. Mejora D-10 (no la edita). Piloto: solo lote A;
  lote B se documenta como réplica.
- Requerimientos TI desde S04 a `insumos_piloto.md`: tablero de producción agregado por
  zona (no un marcador por finca); paquete de campo restringido a la zona del equipo.

## 2. D-16 en la base: `sql/09_fecha_visita_solo_si_nula.sql`
`CREATE OR REPLACE` de la función de `trg_fecha_visita_auto` para que solo asigne
`fecha_visita` si llega NULL. pg_dump previo de `mgn` (D-13); una transacción.
Verificación con `DATABASE_URL_LOTE_A` y ROLLBACK: (a) UPDATE con fecha explícita de ayer
→ conserva esa fecha; (b) UPDATE de estado sin fecha → recibe now(). 0 residuos.

## 3. pg_service
- Escribir desde Python, sin imprimir valores, `%APPDATA%\postgresql\pg_service.conf` con
  el servicio `neon_lote_a` (host sin -pooler, port 5432, dbname, sslmode=require,
  user edit_lote_a, password) tomado de `DATABASE_URL_LOTE_A`. Fuera del repositorio.
  Si el archivo existe, agregar el bloque sin borrar los otros.
- Verificar: `psql "service=neon_lote_a" -X -c "select current_user"` → edit_lote_a.
- `docs/guia/pg_service.md`: plantilla con marcadores (sin valores) y la ruta en Windows.

## 4. Proyecto de campo `campo/NEON_campo_lote_A.qgs` (PyQGIS)
Ubicar el Python de QGIS 3.34.11 y construir el proyecto por script (`campo/construir_proyecto_campo.py`):
- Capas con fuente `service='neon_lote_a'`, sin host, usuario ni clave:
  `mgn.finca_visita` (geom, editable, filtro `"lote" = 'A'`) y `mgn.deteccion_cambio`
  (referencia, solo lectura, filtro `"lote" = 'A'`). SRC del proyecto EPSG:5367.
- Formulario de `finca_visita`: `estado_visita` como lista de valores (los 5 de D-15);
  valores por defecto `encuestador = @cloud_username`, `fecha_visita = now()`,
  `precision_gnss_m = @position_horizontal_accuracy` (sin «aplicar al actualizar» en fecha);
  `observaciones` texto multilínea; `id`, `finca_id`, `lote`, `codigo_upm` y campos de
  auditoría solo lectura.
- QFieldSync: `finca_visita` en «offline editing»; `deteccion_cambio` en la acción de solo
  lectura que corresponda. Si no se puede fijar por script, dejarlo anotado: la persona lo
  configura en la interfaz.
- Escaneo del .qgs: 0 coincidencias de `neon.tech`, `npg_`, `password`, `user=`; sí debe
  aparecer `service='neon_lote_a'`. Versionar `campo/*.qgs` (excepción en .gitignore) y el
  script. NEON.qgz sigue fuera.

## 5. Guía de réplica
`docs/guia/qfield_campo.md`: secuencia completa (pg_service, proyecto, QFieldSync, secreto
en QFieldCloud, celular, sincronización) con marcadores; incluye cómo replicar para el
lote B (servicio `neon_lote_b`).

## 6. Cierre
revisor-auditoria (foco: credenciales fuera del .qgs y del repo; formulario; D-16).
Bitácora `2026-10-15_sesion-05.md`, commit. Pedir confirmación antes del push. Resumen de
10 líneas. Detenerse: lo siguiente lo hace la persona en QGIS/QFieldCloud.

## Criterios de aceptación
- [ ] sql/09 aplicado y verificado (a y b).
- [ ] `service=neon_lote_a` responde edit_lote_a; pg_service.conf fuera del repo.
- [ ] `.qgs` sin credenciales ni host, con formulario y valores por defecto.
- [ ] D-19 y requerimientos de S04 registrados; push confirmado por la persona.

## Fuera de alcance
Proyecto del lote B, subida a QFieldCloud, prueba en celular, documento TI.