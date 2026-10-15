# SPEC S04 — Simulación a escala con la capa UGM (desatendida)

Fecha: 2026-10-15 · Plazo del piloto: 2026-10-16 15:00
Objetivo: medir el comportamiento del diseño con ~90.000 unidades (proxy de fincas) y
dejar cifras verificadas para el documento de TI. Nada se publica.
Modo: desatendido. La persona solo aprueba el paso 0 y se retira.

## 0. Permisos para correr sin supervisión (con la persona presente)
Proponer y, tras su aprobación, agregar a `.claude/settings.json` (allow):
`ogrinfo *`, `ogr2ogr *`, `psql *`, `pg_dump *`, `py sim/*`, `py tablero/generar_tablero.py *`,
`py tablero/capturar_tablero.py *`, `git add *`, `git commit *`. Mantener los deny de lectura
de `.env`. Mostrar el diff, esperar el «sí» y no volver a preguntar en todo el encargo.
Ubicar ogr2ogr/ogrinfo (`C:\Program Files\QGIS 3.34.11\bin`) y reportar versión; si hace
falta PATH, usar ruta completa en los scripts (no tocar el PATH del sistema).

## 1. Reglas del encargo
- Todo en el esquema `sim`. Prohibido escribir en `mgn` ni crear roles nuevos.
- PREAUTORIZADO, solo para este encargo: `DROP SCHEMA sim CASCADE`, únicamente si el
  almacenamiento supera el umbral del paso 3. Ningún otro DROP.
- Credenciales: cargar `.env` desde Python y pasarlas por variables de entorno (PGHOST,
  PGUSER, PGPASSWORD…) a los subprocesos. Nunca en la línea de comandos ni en la salida.
- Cada medición se toma con el comando exacto y su resultado literal.
- Si algo falla dos veces, se documenta y se sigue con el paso siguiente; no se improvisa
  fuera de alcance.

## 2. Inventario del origen (sin tocar la base)
`ogrinfo -so` sobre `datos_prueba/ugm/ugm.gpkg`: nombre de capa(s), SRC, tipo de
geometría, número de objetos, campos. Completar `datos_prueba/ugm/LEEME.txt` con esos datos
y fecha; la URL de descarga queda como «PENDIENTE: la indica la persona» (no inventar).

## 3. Presupuesto de almacenamiento
Antes de cargar: `pg_database_size(current_database())` y tamaño de `mgn`. Umbral: si
tras la carga la base supera 450 MB, `DROP SCHEMA sim CASCADE`, registrar la cifra y
repetir la carga solo con geometría + campos jerárquicos (provincia, cantón, distrito, id),
sin otros atributos. Si aun así supera, cargar únicamente los puntos (paso 5) y documentar.

## 4. Carga (D-18)
`ogr2ogr` → `sim.carga_temporal`: `-t_srs EPSG:5367`, `-nlt PROMOTE_TO_MULTI`,
`-lco GEOMETRY_NAME=geom`, `-lco SPATIAL_INDEX=GIST`. Medir tiempo de pared.
Luego `sim.ugm` con la estructura de las plantillas (id IDENTITY, id_origen, columna de
reparto `lote` = código de provincia, NOT NULL + CHECK, geometría `MultiPolygon, 5367`),
`INSERT … SELECT` con `ST_Multi(ST_MakeValid())`. Medir tiempo. Borrar `carga_temporal`.

## 5. Capa de visita a escala
`sim.finca_visita` con la misma estructura que `mgn.finca_visita` y `ST_PointOnSurface`.
Medir: tiempo de creación; puntos dentro de su polígono (= total); conteo por lote.

## 6. Mediciones para TI
a) Tamaños: tabla, índices y total de `sim.ugm` y `sim.finca_visita`; base completa.
b) Consultas del tablero: crear `sim.v_tab_*` equivalentes, `GRANT SELECT` a
   tablero_lectura, `EXPLAIN (ANALYZE, BUFFERS)` y tiempo de cada una.
c) Concurrencia: `sim/prueba_concurrencia.py` con 1, 10 y 25 conexiones simultáneas, 200
   UPDATE cada una sobre filas disjuntas de `sim.finca_visita`; medir operaciones por
   segundo, latencia p50/p95 y errores. Al terminar devolver las filas a `pendiente`.
d) Tablero: agregar a `generar_tablero.py` el parámetro `--esquema` (por defecto `mgn`, sin
   cambiar el comportamiento publicado). Generar `tablero/salida/sim.html` con
   tablero_lectura: tiempo de generación, peso del HTML, y con `capturar_tablero.py` a
   400 px tiempo hasta render y errores JS. No se publica.
e) Paquete de campo: exportar `sim.finca_visita` + `sim.ugm` a un GeoPackage temporal
   (ignorado por git) y reportar su peso, como cota del paquete offline de QField.

## 7. Entregables
- `docs/requerimientos_ti/evidencia_escala.md`: tabla de mediciones (comando y resultado
  literal) + sección «Qué vale y qué no vale del proxy UGM» (sirve para carga, tamaño,
  concurrencia y tablero; no para tiempos de visita ni cobertura) + hallazgos (p. ej., si
  el mapa con ~90.000 marcadores no es viable en celular, decirlo con la cifra).
- `docs/DECISIONES.md`: D-18 (UGM del SNIT en esquema `sim` como proxy de ~90.000 fincas).
- `.env.example`: marcador de host genérico `HOST` (observación del revisor en S03).
- revisor-auditoria revisa `evidencia_escala.md` contra las salidas literales.
- Bitácora `docs/sesiones/2026-10-15_sesion-04.md`, commit y push. Resumen de 10 líneas.

## Criterios de aceptación
- [ ] Inventario del origen documentado; URL marcada como pendiente.
- [ ] `sim.finca_visita` con un punto dentro de cada polígono (conteos iguales).
- [ ] Mediciones a–e con comando y resultado literal; las que no se pudieron, con la causa.
- [ ] `mgn` intacto: conteos 1432/1432 y estados de visita iguales a antes del encargo.
- [ ] Revisor sin bloqueantes; commit y push hechos.

## Fuera de alcance
Roles nuevos, RLS por provincia, publicar el tablero sim, pg_service, QField, D-16 en SQL.
`sim` se conserva hasta S06; su borrado se decide después de la presentación.