# Evidencia de escala: simulación con la capa UGM (S04)

Fecha de las mediciones: 2026-10-15 (14:39 a 14:54, hora de Costa Rica).
Encargo: `specs/2026-10-15_S04_simulacion_ugm.md`. Decisión: D-18.
Salidas literales completas (redactadas, sin host ni claves): `docs/evidencia/s04/01` a `12`.
Scripts que las producen: `sim/` (credenciales tomadas de `.env` por variables libpq; ninguna
en la línea de comandos).

## Condiciones de la medición

| Elemento | Valor |
|---|---|
| Servidor | Neon, plan gratuito, PostgreSQL 18.6 (aarch64), `max_connections` = 901 (evidencia 12) |
| Cliente | Estación Windows 11 del piloto, conexión doméstica/institucional a Internet; psql 18 |
| GDAL | 3.9.2 (QGIS 3.34.11, `C:\Program Files\QGIS 3.34.11\bin`) |
| Latencia de red de referencia | `SELECT 1` x 50, una conexión: p50 96,3 ms · p95 110,4 ms · máx 145,2 ms |
| Proxy | 50.794 UGM del SNIT (no 90.000): 56 % de la escala objetivo |
| Rol de las pruebas de escritura | `neondb_owner` (omite RLS; `sim` no tiene RLS ni roles de edición) |

La latencia de red (~96 ms por ida y vuelta) domina casi todos los tiempos de cliente que
siguen. Desde la red institucional o desde la nube de TI las cifras pueden ser distintas.

## Mediciones

### Origen y carga (pasos 2 a 4)

| Medición | Comando | Resultado literal | Evidencia |
|---|---|---|---|
| Inventario del origen | `ogrinfo -so -al -nomd datos_prueba/ugm/ugm.gpkg` | `Layer name: ugm` · `Geometry: Multi Polygon` · `Feature Count: 50794` · `PROJCRS["CR-SIRGAS / CRTM05"` (`ID["EPSG",8908]`) | 02 |
| Perfil del origen | `ogrinfo -sql "SELECT count(*) ..., sum(ST_IsValid(geom)=0) invalidas ..."` | `n = 50794` · `id_distintos = 50794` · `distritos = 492` · `cantones = 84` · `provincias = 7` · `invalidas = 0` · `multipartes = 1` | 02 |
| Transformación 8908 → 5367 | `projinfo -s EPSG:8908 -t EPSG:5367 --summary` | `unknown id, Inverse of Costa Rica TM 2005 + Inverse of CR05 to CR-SIRGAS (1) + Costa Rica TM 2005, 0.5 m, Costa Rica - onshore and offshore.` | 11 |
| Base antes de cargar | `pg_database_size(current_database())` | `17 MB` · `17842176` | 01 |
| `mgn` antes | suma de `pg_total_relation_size`, esquema `mgn` | `1536 kB` · `1572864` | 01 |
| Carga a la tabla de paso | `ogr2ogr -f PostgreSQL PG: ugm.gpkg ugm -nln sim.carga_temporal -t_srs EPSG:5367 -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco SPATIAL_INDEX=GIST -gt 10000` | `rc=0 · tiempo de pared: 31.80 s` | 03 |
| Verificación de la tabla de paso | `SELECT count(*), count(DISTINCT id), min/max(ST_SRID(geom)), ... NOT ST_IsValid` | `50794 \| 50794 \| 5367 \| 5367 \| 0` | 03 |
| Base tras `ogr2ogr` | `sql_tamanos.sql` | base `212 MB` (`222027776`); `carga_temporal` `195 MB` (`204087296`) | 03 |
| Umbral de 450 MB | comparación | 212 MB < 450 MB: no se aplicó `DROP SCHEMA sim CASCADE` | 03 |
| `INSERT ... SELECT` a `sim.ugm` con `ST_Multi(ST_MakeValid(geom))` | `\timing` en `sim/sql_ugm.sql` | `INSERT 0 50794` · `Time: 5688,683 ms (00:05,689)` | 03 |
| Índice GiST de `sim.ugm` | `\timing` | `Time: 438,356 ms` | 03 |
| `VALIDATE CONSTRAINT chk_geom_valida` | `\timing` | `Time: 1322,822 ms (00:01,323)` | 03 |
| Script `sim.ugm` completo (con índices, CHECK, ANALYZE, verificaciones y borrado de la tabla de paso) | `psql -f sim/sql_ugm.sql` | `rc=0 · tiempo de pared: 11.83 s` | 03 |
| Verificación de `sim.ugm` | conteo, SRID, inválidas, por lote | `50794 \| 50794`; `5367 \| MULTIPOLYGON`; inválidas `0`; lotes 1–7: 14375, 8911, 5353, 4285, 6542, 6838, 4490 | 03 |
| Áreas | `sum(ST_Area(geom))` frente a `sum(area_m2)` del origen | `5036045.85` ha frente a `5035926.33` ha (diferencia 0,002 %) | 03 |
| Base tras crear `sim.ugm` y borrar la tabla de paso | `sql_tamanos.sql` | base `209 MB` (`218963968`); `sim.ugm` `191 MB` | 03 |

El pico de almacenamiento, entre el `INSERT` y el borrado de la tabla de paso, no se midió.
Estimación por suma: 212 MB + 191 MB ≈ 403 MB, por debajo del umbral de 450 MB del spec. El
límite de 0,5 GB del plan gratuito de Neon viene de la oferta del proveedor; no se verificó en
este encargo.

### Capa de visita a escala (paso 5)

| Medición | Comando | Resultado literal | Evidencia |
|---|---|---|---|
| `INSERT` de un punto por UGM (`ST_PointOnSurface`) | `\timing` en `sim/sql_finca_visita.sql` | `INSERT 0 50794` · `Time: 1277,801 ms (00:01,278)` | 04 |
| Script completo (tabla, triggers, índices, ANALYZE, verificación) | `psql -f sim/sql_finca_visita.sql` | `tiempo de pared: 4.52 s` | 04 |
| Puntos dentro de su polígono | `count(*) FILTER (WHERE ST_Within(v.geom, u.geom))` | `poligonos 50794 \| puntos 50794 \| dentro 50794` | 04 |
| Conteo por lote | `GROUP BY lote` | 1: 14375 · 2: 8911 · 3: 5353 · 4: 4285 · 5: 6542 · 6: 6838 · 7: 4490 (todo `pendiente`) | 04 |

### a) Tamaños (paso 6a)

| Relación | Tabla + TOAST | Índices | Total | Evidencia |
|---|---|---|---|---|
| `sim.ugm` | 188 MB | 3864 kB | 192 MB (`200810496`) | 09 |
| `sim.finca_visita` | 8688 kB | 7912 kB | 16 MB (`16998400`) | 09 |
| `mgn.deteccion_cambio` | 728 kB | 256 kB | 984 kB | 09 |
| `mgn.finca_visita` | 272 kB | 280 kB | 552 kB | 09 |
| Base completa | | | 225 MB (`236109824`) | 09 |
| Esquema `sim` | | | 208 MB (`217808896`) | 10 |

`sim.finca_visita` se midió después de los 7.200 UPDATE de la prueba de concurrencia y de su
reversión, sin `VACUUM`: incluye versiones muertas de filas. Es una cota superior de la capa
recién creada.

Extrapolación lineal a 90.000 objetos (estimación, no medición): polígonos ≈ 192 MB × 90.000 /
50.794 ≈ 340 MB; puntos ≈ 16 MB × 1,77 ≈ 28 MB. Con geometría de complejidad similar a la de
las UGM, no cabe con holgura en el plan gratuito (0,5 GB, según el proveedor). La complejidad real de las fincas
puede ser distinta.

### b) Consultas del tablero (paso 6b), rol `tablero_lectura`

`tablero_lectura` no lee la tabla: `SELECT count(*) FROM sim.finca_visita` → `ERROR:  permission denied for table finca_visita` (05).

Comando: `py sim/psql.py --rol tablero -f sim/sql_medir_vistas.sql` (`EXPLAIN (ANALYZE, BUFFERS)`
y, con `\timing` y `\o NUL`, `SELECT *` completo con la salida descartada).

| Vista | Ejecución en servidor, todo pendiente | Cliente (servidor + red + recepción), todo pendiente | Ejecución en servidor, con 7.200 visitas | Cliente, con 7.200 visitas |
|---|---|---|---|---|
| `v_tab_resumen` | 21.650 ms | 118,712 ms | 23.122 ms | 123,924 ms |
| `v_tab_encuestador` | 4.022 ms | 102,410 ms | 8.747 ms | 106,740 ms |
| `v_tab_diario` | 4.409 ms | 101,873 ms | 9.994 ms | 105,699 ms |
| `v_tab_puntos` (50.794 filas) | 144.985 ms | 1504,458 ms (00:01,504) | 114.144 ms | 1231,009 ms (00:01,231) |
| `v_tab_movimientos` | 4.056 ms | 102,445 ms | 11.869 ms | 114,667 ms |

Todas las lecturas de buffers fueron `shared hit` (en caché), salvo `v_tab_puntos` en la
primera medición: `shared hit=1324 read=16 dirtied=2`. Separadores decimales literales: `EXPLAIN`
usa punto y `	iming` usa coma (21.650 ms = 21,65 ms; 1504,458 ms = 1,5 s). La medición «con 7.200 visitas» se hizo
con las filas de la prueba de concurrencia antes de revertirlas (05).

### c) Concurrencia (paso 6c)

Comando: `py sim/prueba_concurrencia.py medir 1 10 25`. Una conexión por hilo, 200 UPDATE
por conexión en autocommit (cada UPDATE es una transacción), filas disjuntas entre hilos y
entre corridas, conexiones abiertas antes de iniciar el cronómetro. Evidencia 06.

| Conexiones | UPDATE | Pared | op/s | p50 | p95 | máx | Errores |
|---|---|---|---|---|---|---|---|
| 1 | 200 | 21.11 s | 9.5 | 97.3 ms | 136.4 ms | 257.1 ms | 0 |
| 10 | 2000 | 24.20 s | 82.6 | 101.2 ms | 180.0 ms | 412.1 ms | 0 |
| 25 | 5000 | 24.26 s | 206.1 | 104.1 ms | 179.3 ms | 493.2 ms | 0 |

Reversión: `py sim/prueba_concurrencia.py revertir` → `UPDATE 7200`; `Después: no pendientes 0
· con encuestador 0 · con fecha_visita 0 · total 50794`. `editado_por` y `fecha_edicion` de esas
7.200 filas quedan con el sello de la prueba (los fija el trigger).

### d) Tablero (paso 6d)

`generar_tablero.py` recibió `--esquema` (por defecto `mgn`). Con el fixture, el HTML por defecto
es idéntico al de la versión anterior (`diff` con `rc=0`; en esa corrida coincidió hasta la hora
de generación; evidencia 12). El tablero se generó con 7.200 visitas presentes, antes de revertirlas. No se publicó.

| Medición | Comando | Resultado literal | Evidencia |
|---|---|---|---|
| Generación | `py tablero/generar_tablero.py --esquema sim --salida tablero/salida/sim.html` (rol `tablero_lectura`) | `rc=0 · tiempo de pared: 3.21 s` · `Tablero escrito en tablero/salida/sim.html (4075 KB)` | 07 |
| Peso del HTML | `stat` | `4173444 bytes (3.98 MiB)` | 07 |
| 400 px, CPU sin freno, 1.ª (en frío) | `py tablero/capturar_tablero.py tablero/salida/sim.html --dir tablero/salida/sim --anchos 400` | `errores JS: []` · `carga_ms: 1793` · `dcl_ms: 1695` · `marcadores: 50794` · `nodos_dom: 51349` · `memoria_js_mb: 111` · `red_quieta_ms: 2318` · `scroll_horizontal: False` | 07 |
| 400 px, CPU sin freno, 2.ª | idem | `errores JS: []` · `carga_ms: 1270` · `dcl_ms: 1262` · `red_quieta_ms: 1798` | 07 |
| 400 px, CPU frenada 4x, 1.ª | `... --anchos 400 --cpu-lento 4` | `errores JS: []` · `carga_ms: 4684` · `memoria_js_mb: 87` · `red_quieta_ms: None` | 07 |
| 400 px, CPU frenada 4x, 2.ª | idem | `errores JS: []` · `carga_ms: 4775` · `memoria_js_mb: 82` · `red_quieta_ms: None` | 07 |

`carga_ms` es el evento `load`: incluye el script del mapa, que corre al final del `body`, con
los 50.794 marcadores ya creados. `red_quieta_ms: None` significa que con la CPU frenada no se
alcanzó `networkidle` en 60 s. La comprobación del freno: un bucle JS de 3·10⁷ iteraciones tardó
18–23 ms sin freno y 91–95 ms con freno 4x (evidencia 11).

### e) Paquete de campo (paso 6e)

Comando: `py sim/paquete_campo.py` (`ogr2ogr -f GPKG ... PG: sim.finca_visita sim.ugm`). Destino:
`sim/salida/`, ignorado por git. Evidencia 08.

| Contenido | Tiempo de exportación | Peso |
|---|---|---|
| `sim.finca_visita` + `sim.ugm` | 68.38 s | `218615808 bytes (208.5 MiB)` |
| Solo `sim.finca_visita` | 17.67 s | `6508544 bytes (6.2 MiB)` |

### Integridad de `mgn` (antes y después)

| Comprobación | Antes (01) | Después (10) |
|---|---|---|
| Polígonos / puntos | `1432 \| 1432` | `1432 \| 1432` |
| Estados (A) | no_localizada 5 · pendiente 694 · visitada 10 | igual |
| Estados (B) | no_localizada 5 · pendiente 703 · rechazo 5 · revisita 5 · visitada 5 | igual |
| Huella md5 de `finca_visita` (id, lote, estado, encuestador, fecha_visita, editado_por, fecha_edicion) | `a17c4a1b0adfbe75879f47e86b1628dc` | `a17c4a1b0adfbe75879f47e86b1628dc` |
| Huella md5 de geometrías de `deteccion_cambio` | `9803cdc910fcfd9dfb7df1d995a3c248` | `9803cdc910fcfd9dfb7df1d995a3c248` |

## Qué vale y qué no vale del proxy UGM

**Vale para:**
- **Carga:** volumen y complejidad geométrica reales de una capa nacional (50.794 polígonos
  válidos, reproyección, `ST_MakeValid`, índices).
- **Tamaño:** orden de magnitud del almacenamiento en la base y del paquete offline.
- **Concurrencia:** escrituras cortas y simultáneas sobre filas distintas de una tabla de ese
  tamaño, con triggers de auditoría activos.
- **Tablero:** costo de las vistas y del HTML con decenas de miles de puntos.

**No vale para:**
- **Tiempos de visita, rendimiento de censistas o duración del operativo:** las UGM no son
  fincas y no hubo trabajo de campo.
- **Cobertura:** las UGM cubren todo el territorio. Las fincas agropecuarias se concentran en
  zonas rurales y su reparto por provincia será otro.
- **Cifras a 90.000:** solo hay 50.794 objetos. Lo que se dice de 90.000 es extrapolación.
- **Costo de RLS:** las pruebas de escritura usaron el propietario, que omite RLS; `sim` no tiene
  políticas.
- **Tiempos desde la red institucional o desde QField:** todo se midió desde una estación del
  piloto, con ~96 ms de ida y vuelta.

## Hallazgos

1. **El mapa con todos los puntos no es viable en celular.** Con 50.794 marcadores, el HTML
   pesa 3,98 MiB, el DOM tiene 51.349 nodos y la página usa entre 82 y 111 MB de memoria JS.
   La carga tarda 1,3–1,8 s en la CPU de la estación y 4,7–4,8 s con la CPU frenada 4x
   (aproximación a un celular). Con freno, la página no llega a reposo de red en 60 s. A 400 px
   el mapa de Costa Rica se ve como una mancha gris: los estados no se distinguen
   (`tablero/salida/sim/captura_400.png`, no versionada). A 90.000 la carga sería mayor (estimación,
no medida).
   Requerimiento para TI: el mapa necesita agregación (por distrito o por grilla), carga por
   zona o un renderizador en canvas o teselas vectoriales, y no un marcador SVG por finca. La
   elección queda abierta.
2. **El tablero asume dos lotes (A y B).** Con lotes 1–7, todos se pintan del mismo azul y la
   leyenda sigue diciendo «Lote A / Lote B». El gráfico «Visitas por persona» agrega una fila
   por persona y lote (46 filas con 36 hilos de prueba). Con ~500 censistas no sería legible. Hay que
   rediseñar la paleta por lote y la vista por persona (p. ej., top N o agregado por
   supervisor).
3. **La red domina la latencia y la base no fue el cuello de botella.** Un UPDATE (~97–104 ms
   de p50) cuesta casi lo mismo que una ida y vuelta (`SELECT 1` p50 96,3 ms). El rendimiento
   creció casi en proporción a las conexiones (9,5 → 82,6 → 206,1 op/s), con p95 ≤ 180 ms y
   0 errores con 25 conexiones simultáneas.
4. **Las vistas del tablero no son problema; la transferencia de puntos sí pesa.** Agregados:
   ≤ 23 ms en el servidor. `v_tab_puntos`: 114–145 ms en el servidor y 1,2–1,5 s en el
   cliente, por la transferencia de 50.794 filas.
5. **El almacenamiento es el límite del plan gratuito, no del diseño.** `sim.ugm` ocupa 192 MB
   (188 MB son tabla + TOAST: geometría y atributos). Estimación, no medición: la extrapolación
   a 90.000 polígonos de complejidad similar (≈ 340 MB) más el pico de carga con tabla de paso
   superarían el límite de 0,5 GB del plan gratuito (según el proveedor). En producción se
   necesita almacenamiento institucional dimensionado con la geometría real de las fincas. Una
   opción es cargar sin tabla de paso para evitar el pico doble.
6. **El paquete offline debe llevar puntos, no polígonos.** Con polígonos pesa 208,5 MiB; solo
   con puntos, 6,2 MiB (unas 34 veces menos). Esto confirma D-07 (capa de puntos separada para el
   formulario) y D-08 (`ST_PointOnSurface`). Los polígonos de contexto deberían ir recortados por zona de trabajo o
   como teselas.
7. **El origen viene en CR-SIRGAS (EPSG:8908), no en CR05 (5367).** La reproyección usa una
   transformación con precisión declarada de 0,5 m. El área total cambió 0,002 %. En
   producción conviene definir el SRC oficial del marco de fincas antes de cargar.

### Estimación por proporción del pico de carga (S08, auditoría N-03)

Pico a 90.000 ≈ 403 MB × 90.000 / 50.794 ≈ 714 MB (estimado por proporción, sin medir). Límite del plan: 0,5 GB ≈ 512 MB.
La cifra 403 no es proporcional del todo por construcción: incluye ≈ 17 MB de la base de datos previa (C32), que no crecen con la capa; escalando solo los ≈ 386 MB que crecen con la capa y sumando los 17 MB fijos, ≈ 701 MB. Si el proveedor usa 1.000 en vez de 1.024, el límite es ≈ 477 MB. En todos los casos el pico estimado supera el límite.
