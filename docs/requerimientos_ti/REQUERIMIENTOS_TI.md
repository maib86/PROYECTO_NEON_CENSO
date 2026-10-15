# Requerimientos para producción derivados del piloto de edición concurrente

Piloto NEON-CENSO · Unidad de Cartografía · Instituto Nacional de Estadística y Censos (INEC)

Versión 1 · 15 de octubre de 2026 · Estado: entregable v1, pendiente de revisión.

Cada cifra de este documento tiene una fila en `docs/requerimientos_ti/CIFRAS.csv` (columna
`id`, citada aquí entre corchetes, por ejemplo [C23]) con el archivo y la línea de donde salió.
`py docs/requerimientos_ti/verificar_cifras.py` comprueba que cada valor está, literal, en su
archivo de origen. Lo que no se midió dice «sin medir» y aparece en el anexo D.

---

## 1. Resumen ejecutivo

**Qué se probó.** Una capa vectorial única en PostgreSQL/PostGIS, en la nube y con datos
públicos, editada por dos roles a la vez desde QGIS escritorio y desde QField en un celular,
con el reparto del trabajo impuesto por la base (seguridad a nivel de fila, RLS), auditoría
automática de quién y cuándo, y un tablero de avance HTML que se regenera sin intervención.
Se usaron 1.432 polígonos públicos del distrito 20205 [C01, C02], repartidos en dos lotes de
709 y 723 fincas [C06, C07]. La escala se ensayó aparte con 50.794 polígonos públicos (UGM del
SNIT) [C23].

**Qué quedó demostrado.** (a) La base impide escribir fuera del lote propio: `UPDATE 1` en el
lote propio, `UPDATE 0` en el ajeno, `INSERT` ajeno rechazado [C12, C13, C14]. (b) El mismo
control funciona desde el celular con conexión directa: las visitas de campo quedaron con el
rol del lote [C56]. (c) El tablero lee solo vistas con un rol de solo lectura, no contiene
credenciales ni texto libre y se publicó con las visitas de campo [C15, C62, C69]. (d) A
50.794 objetos, 25 conexiones simultáneas escribieron sin errores y la red, no la base, fue el
factor dominante [C25, C43].

**Qué no quedó demostrado.** La edición sin señal y su sincronización (requiere un plan de
QFieldCloud que admita PostGIS, D-22); la identidad individual de cada censista en campo
(`@cloud_username`); el comportamiento a 90.000 fincas (lo que se dice es extrapolación
[C24, C34]); el costo del RLS a escala; tiempos desde la red institucional. El piloto corrió
con dos personas y un celular.

**Qué se pide.** Las decisiones de la sección 7 (modalidad de QFieldCloud, identidades de
campo, historial de visitas, cuestionario real, dónde corre el tablero) y los recursos del
siguiente paso (sección 8): una cuenta QFieldCloud de prueba con PostGIS, un servidor PostGIS
institucional para replicar el esquema y un equipo de campo real para una prueba acotada. Los
requerimientos técnicos para producción están en la sección 6.

---

## 2. Arquitectura probada

```
  QGIS escritorio ──┐   rol edit_lote_a / edit_lote_b (uno por lote)
                    │   conexión TLS (sslmode=require), sin pooling
  QField (celular) ─┤   conexión directa por pg_service (D-22, parte 1)
                    ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ PostgreSQL 18.6 + PostGIS 3.6.4 (Neon, plan gratuito)        │
  │  mgn.deteccion_cambio  polígonos, MultiPolygon EPSG:5367     │
  │  mgn.finca_visita      un punto por finca (formulario)       │
  │  RLS: lectura total · escritura acotada por columna `lote`   │
  │  Triggers: sello de auditoría · fecha de visita si es NULL   │
  │  Vistas v_tab_*  ── únicas legibles por tablero_lectura      │
  └──────────────────────────────────────────────────────────────┘
                    │  rol tablero_lectura (solo lectura, secreto cifrado)
                    ▼
  Generador Python (GitHub Actions, programado + manual)
                    │  HTML estático, sin credenciales ni consultas al abrirse
                    ▼
  Tablero en GitHub Pages (público: aceptable solo con datos públicos)
```

| Elemento | Decisión que lo sostiene |
|---|---|
| Base gestionada en la nube, solo tráfico saliente, sin instalaciones | D-01, D-02 |
| Reparto impuesto por RLS con un rol por lote; pruebas con roles de edición | D-03, D-06 |
| Llave entera `id` IDENTITY; identificador de origen aparte; carga por tabla de paso | D-04, D-05 |
| Capa de visita de puntos separada; punto garantizado dentro (`ST_PointOnSurface`) | D-07, D-08 |
| Tablero estático, rol de solo lectura, sin texto libre ni posición GNSS | D-09, D-14 |
| Identidad en campo por atributo; reparto en campo por proyecto y rol del lote | D-10, D-19 |
| Estados de visita y fórmula de avance (provisionales hasta el cuestionario real) | D-15 |
| Hora de visita: la pone el formulario de QField; en escritorio es la hora de guardado | D-16, D-20 |
| Zona de sesión fijada en la base (`America/Costa_Rica`) | D-23 |
| Campo en dos partes: conexión directa hoy; QFieldCloud offline después | D-22 |

**Quién ve qué.** Los roles de edición leen toda la capa y escriben solo su lote. El rol del
tablero no lee tablas: `permission denied for table finca_visita` [C15]; solo las cinco vistas
`v_tab_*` [C84], que no exponen `observaciones` ni posición GNSS (D-14). El propietario omite el RLS
y no se usa para editar.

---

## 3. Evidencia por fase

Fases según `ESPECIFICACION.md`. Resultado literal tal como quedó en el archivo de evidencia.

### Fase 1 — Edición concurrente desde escritorio (completada)

| Criterio | Resultado literal | Evidencia |
|---|---|---|
| Capa cargada, válida y repartida | `1.432` polígonos, `709` lote A, `723` lote B [C01, C06, C07] | `docs/sesiones/2026-10-13_sesion-00.md` |
| RLS por lote, con roles de edición | prueba cruzada desde QGIS por dos personas: exitosa | `docs/sesiones/2026-10-13_sesion-00.md` |
| Guía de replicación y plantillas | `docs/guia/Guia_replicacion_PostGIS.md`; `sql/plantillas/01`–`05` | repositorio |

### Fase 2 — Capa de visita y tablero (completada el 15/10/2026; regeneración programada sin observar)

| Criterio | Resultado literal | Evidencia |
|---|---|---|
| Un punto por finca, dentro de su polígono | `1.432/1.432` [C08] | `docs/DECISIONES.md` (D-08); sesión 02 |
| RLS en la capa de puntos | `UPDATE 1` propio · `UPDATE 0` ajeno · `new row violates row-level security policy` [C12–C14] | `docs/sesiones/2026-10-15_sesion-02.md` |
| Rol del tablero solo con vistas | `permission denied for table finca_visita` [C15] | sesión 02 |
| Visitas de prueba A y B | A: 15 desde QGIS por la persona [C16]; B: 20 simuladas por script [C17] | `ESPECIFICACION.md`; sesión 02 |
| Tablero con datos reales, 1100 y 400 px | capturas sin defectos | `docs/evidencia/2026-10-15_tablero_1100.png`, `_400.png` |
| Regeneración automática | workflow en verde (`38800395636`) [C20]; cron `*/30 * * * *` configurado [C11]. **Tras la regeneración manual de las 16:46 [C62] no se registraba ninguna ejecución por `schedule`** [C68]: las tres ejecuciones registradas fueron manuales | `docs/evidencia/s06/01_tablero_publicado.txt` |
| HTML publicado sin credenciales | `HTTP 200` [C21]; escaneo de host y claves `0` | sesión 03; `docs/evidencia/s06/01_tablero_publicado.txt` |

### Fase 3, parte 1 (D-22) — QField con conexión directa, sin QFieldCloud

| Criterio | Resultado literal | Evidencia |
|---|---|---|
| Proyecto de campo sin credenciales | `Resultado: 0 fallas` en 41 comprobaciones [C83]; solo `service='neon_lote_a'` [C53] | `docs/sesiones/2026-10-15_sesion-05.md` |
| Escritura desde el celular con el rol del lote | tras las 3 primeras visitas de campo, lote A: `18` no pendientes, `18` editadas por `edit_lote_a` (15 de QGIS + 3 de campo) [C56]; con la cuarta (id 1394), `edit_lote_a: 19` en el tablero publicado [C67] | `docs/evidencia/s05/05_prueba_qfield_directa.txt` |
| Hora real de la visita desde el formulario | primero, desfase `06:00:13.645059` [C57] (zona de sesión `GMT` [C58]); tras D-23, visita 1394 guardada `00:00:25.46969` después [C59] | `docs/evidencia/s05/05_…`, `06_…`, `07_visita_tras_d23.txt` |
| Precisión GNSS registrada | `1.5` [C54]; `1.600000023841858` [C60] | `docs/evidencia/s05/05_…`, `07_…` |
| Visitas de campo en el tablero publicado, sin `observaciones` | las 4 visitas en «Últimos movimientos» (fincas `1396, 1405, 1398, 1406`) [C70]; `observaciones` 0 [C69]; `generado 15/10/2026 16:46` [C62] | `docs/evidencia/s06/01_tablero_publicado.txt` |

### Fase 3, parte 2 (D-22) — QFieldCloud con PostGIS y edición offline: no probada

| Criterio | Estado | Causa |
|---|---|---|
| Proyecto publicado en QFieldCloud en modo offline | pendiente | el plan Community no admite capas PostGIS (D-22) |
| `encuestador = @cloud_username` | pendiente: llega NULL sin sesión de QFieldCloud | ídem |
| Secreto `pg_service` en QFieldCloud (no en el dispositivo) | pendiente | ídem; hoy la clave está en el celular |
| Edición sin señal → sincronización → tablero; tiempo hasta aparecer | pendiente; tiempo **sin medir** | ídem |
| Identidad individual en `v_tab_encuestador` | pendiente: hoy la identidad es el rol, por equipo | ídem |

---

## 4. Escala

Fuente: `docs/requerimientos_ti/evidencia_escala.md` (S04, D-18) y sus salidas literales en
`docs/evidencia/s04/`. Proxy: 50.794 UGM del SNIT, el 56 % de 90.000 [C23, C24]. Todas las
mediciones desde una estación del piloto, con latencia de red de 96,3 ms (p50) [C25].

Separadores decimales literales de la evidencia: `EXPLAIN` y los scripts de Python usan punto
(23.122 ms = 23,1 ms; 31.80 s = 31,8 s; 208.5 MiB = 208,5 MiB) y `	iming` de psql usa coma
(1504,458 ms = 1,5 s). Se conservan tal cual para que cada valor se encuentre en su archivo.

### 4.1 Medido con 50.794

| Medición | Resultado | Cifra |
|---|---|---|
| Carga con `ogr2ogr` a la tabla de paso | 31.80 s | C27 |
| `INSERT … SELECT` con `ST_MakeValid` | `Time: 5688,683 ms` | C28 |
| Puntos de visita dentro de su polígono | poligonos 50794 &#124; puntos 50794 &#124; dentro 50794 | C29 |
| Tamaño de los polígonos (`sim.ugm`, total) | 192 MB | C30 |
| Tamaño de los puntos (`sim.finca_visita`, cota superior) | 16 MB | C31 |
| Base completa antes / después | 17 MB / 225 MB | C32, C33 |
| Vistas agregadas del tablero (servidor, máximo) | 23.122 ms | C38 |
| `v_tab_puntos`, 50.794 filas (servidor / cliente) | 144.985 ms / 1504,458 ms | C39, C40 |
| Concurrencia 1 conexión | 200 UPDATE · 9.5 op/s · p95 136.4 ms · 0 errores | C41 |
| Concurrencia 10 conexiones | 2000 UPDATE · 82.6 op/s · p95 180.0 ms · 0 errores | C42 |
| Concurrencia 25 conexiones | 5000 UPDATE · 206.1 op/s · p95 179.3 ms · 0 errores | C43 |
| HTML del tablero con un marcador por punto | 3,98 MiB · 51.349 nodos DOM | C44, C45 |
| Carga del tablero con CPU frenada 4x | 4,7–4,8 s | C46 |
| Paquete de campo con polígonos / solo puntos | 208.5 MiB / 6.2 MiB (unas 34 veces menos) | C47–C49 |
| Cambio de área al reproyectar EPSG:8908 → 5367 | 0,002 % | C51 |

### 4.2 Extrapolado o estimado (no medido)

| Elemento | Estimación | Cifra |
|---|---|---|
| Polígonos a 90.000 con complejidad similar | ≈ 340 MB | C34 |
| Puntos a 90.000 | ≈ 28 MB | C35 |
| Pico de almacenamiento durante la carga con tabla de paso (50.794) | ≈ 403 MB, estimado por suma; pico **sin medir** | C37 |
| Límite del plan gratuito | 0,5 GB según el proveedor; **sin verificar** | C36 |

Con 90.000 polígonos de complejidad similar y el pico de la carga, el plan gratuito no
alcanza: producción necesita almacenamiento institucional dimensionado con la geometría real
de las fincas (sin medir hasta tener la capa).

### 4.3 Qué vale y qué no vale del proxy UGM

**Vale para:** volumen y complejidad geométrica de una capa nacional; orden de magnitud de
almacenamiento y del paquete offline; escrituras cortas y simultáneas sobre filas distintas
con triggers activos; costo de las vistas y del HTML con decenas de miles de puntos.

**No vale para:** tiempos de visita, rendimiento de censistas ni duración del operativo (las
UGM no son fincas); cobertura (las fincas se concentran en zona rural); cifras a 90.000
(extrapolación); costo del RLS (las escrituras usaron el propietario, que lo omite); tiempos
desde la red institucional o desde QField.

---

## 5. Limitaciones del piloto y su causa

| Limitación | Por qué existió (qué no se tenía) | Qué hace falta para levantarla | Evidencia |
|---|---|---|---|
| Edición offline, sincronización e identidad `@cloud_username` no probadas | Cuenta QFieldCloud Community: no admite capas PostGIS | Cuenta o instancia QFieldCloud del INEC con PostGIS offline (decisión 7.1) y prueba D-22 parte 2 | D-22; `docs/evidencia/s05/05_…` (`encuestador` NULL) |
| Reparto en campo por proyecto y rol del lote, no por persona | QFieldCloud aplica cambios con la conexión del proyecto; no hay usuario de base por censista (hipótesis D-19 sin verificar en QFieldCloud) | Verificar `editado_por` tras sincronizar; identidad individual por atributo restringido (req. 5, 15) | D-10, D-19 |
| Hora de visita desde escritorio = hora de guardado | QGIS escritorio envía `fecha_visita` NULL; `now()` es la hora de la transacción: 15 visitas con `13:02:30.279335` [C18] | Registrar visitas solo desde el formulario de campo, que pone la hora del dispositivo | D-16, D-20; sesión 02 |
| Escala: 50.794 objetos, no 90.000 | No existe aún la capa de fincas del censo; se usó un proxy público | Capa real de fincas (o una muestra provincial) cargada en la infraestructura del INEC | D-18; `evidencia_escala.md` |
| Datos públicos, tablero público, nube gratuita con 6 h de restauración | Sin infraestructura institucional ni permisos de TI para el piloto | Servidor PostGIS institucional, web interna con autenticación, respaldo programado y restauración probada | D-01, D-09 [C09] |
| Dos personas y un celular | Alcance del piloto | Prueba de campo con un equipo real (sección 8c) | `ESPECIFICACION.md` §2 |
| Credenciales de base en el dispositivo, sin MDM | Conexión directa sin QFieldCloud (D-22, parte 1) | Secreto en el servidor de QFieldCloud o MDM institucional (req. 10) | D-22 |
| Una fila por finca: la revisita reescribe persona y precisión, conserva la primera fecha | `UNIQUE(finca_id)` en el piloto | Una fila por visita, con coherencia `lote` ↔ `finca_id` (req. 2, 8) | D-07, D-21 |
| Regeneración del tablero cada 30 min configurada pero no observada | GitHub no ejecutó el cron en el plazo del piloto: 0 ejecuciones por `schedule` [C68]; causa sin diagnosticar | Cron institucional con monitoreo y alerta si no corre (req. 14) | `docs/evidencia/s06/01_tablero_publicado.txt` |
| Encabezado del tablero: «22 incidencias» no distinguía las revisitas sin cerrar [C65] | La etiqueta sumaba revisitas a no localizadas y rechazos | Corregido en S06 (`tablero/generar_tablero.py`, líneas 264 y 309): «N incidencias, de ellas M revisitas sin cerrar». Visible en la próxima regeneración | sesión 06 |
| Costo del RLS a escala y tiempos desde la red institucional, sin medir | Pruebas de escala con el propietario, desde la estación del piloto | Repetir la prueba de concurrencia con roles de edición, desde la red y la nube de TI (req. 17) | `evidencia_escala.md` |
| Estados de visita y fórmula de avance provisionales | Sin cuestionario real del censo | Cuestionario real (decisión 7.4) | D-15 |

---

## 6. Requerimientos para producción

Numeración continua: 1 a 11 vienen de `docs/requerimientos_ti/insumos_piloto.md`; 12 en
adelante surgen de la sección 5 de este documento y de los hallazgos de S04, como indica su origen.

### 6.1 Base de datos

| # | Requerimiento | Origen |
|---|---|---|
| 1 | Vistas del tablero con `security_invoker = true` y políticas propias para el rol del tablero cuando la lectura deba restringirse por zona o confidencialidad. | Sesión 02; D-14 |
| 2 | Coherencia `lote` ↔ `finca_id` en la capa de visita (FK compuesta o trigger) antes de retirar `UNIQUE(finca_id)`. | Sesión 02; D-07, D-14 |
| 8 | Cada visita es una fila, con su persona, fecha y precisión propias. | D-21; D-07 |
| 11 | Zona de sesión fijada a nivel de base (`ALTER DATABASE … SET timezone`), no confiada al cliente. | D-23 |
| 12 | Almacenamiento dimensionado con la geometría real de las fincas, con margen para el pico de carga; carga sin tabla de paso duplicada o en lotes. | S04, hallazgo 5; [C34, C37] |
| 13 | Sistema de referencia oficial del marco de fincas definido antes de cargar (el proxy venía en EPSG:8908). | S04, hallazgo 7; [C51] |
| 16 | Columna de reparto con N valores (provincia, UPM o zona de equipo), `NOT NULL` + `CHECK` o FK a una tabla de zonas; un rol de edición por equipo. | D-03, D-06; S04, lotes 1–7 [C85] |

### 6.2 Identidad y acceso

| # | Requerimiento | Origen |
|---|---|---|
| 3 | Claves de roles fijadas con `\password` (hash SCRAM en el cliente), no en sentencias SQL. | D-13 |
| 5 | `encuestador` restringido a nombres de usuario válidos (CHECK, dominio o FK a la lista de cuentas de campo). | Sesión 02; D-14 |
| 15 | Una cuenta por persona en campo (QFieldCloud o el sistema de identidades del INEC), nunca compartida; la identidad individual llega por atributo y se valida contra el req. 5. | D-10, D-19; `ESPECIFICACION.md` §4, restricción 4 |

### 6.3 Campo

| # | Requerimiento | Origen |
|---|---|---|
| 7 | Paquete de campo restringido a la zona del equipo: puntos de visita de esa zona y polígonos recortados o como teselas. | S04, hallazgo 6; D-19; [C47, C48] |
| 9 | Plan de QFieldCloud del INEC que admita capas PostGIS con edición offline. | D-22; D-19 |
| 10 | Credenciales de base en el dispositivo solo con gestión de dispositivos móviles (MDM). | D-22 |
| 18 | Hora de la visita tomada del dispositivo por el formulario de campo; la edición desde escritorio se declara como hora de guardado. | D-16, D-20, D-23 |

### 6.4 Tablero

| # | Requerimiento | Origen |
|---|---|---|
| 4 | Ninguna vista que alimente un tablero publicado expone texto libre ni posición GNSS. | D-14 |
| 6 | Tablero agregado por zona (distrito o grilla; canvas o teselas), no un marcador por finca; paleta y vista por persona que no supongan dos lotes. | S04, hallazgos 1 y 2; [C44–C46, C50] |
| 19 | Tablero de producción en web interna con autenticación (estadística confidencial); nunca en un sitio público. | D-09; `ESPECIFICACION.md` §2 |

### 6.5 Operación y respaldo

| # | Requerimiento | Origen |
|---|---|---|
| 14 | Generador del tablero en cron institucional con monitoreo: alerta si una regeneración no ocurre o falla. | Sesión 06 [C68] |
| 17 | Prueba de carga con roles de edición (RLS activo), desde la red institucional y con el número de conexiones previsto en el operativo. | S04, «no vale para»; [C43] |
| 20 | Respaldo programado de la base (no depender de una ventana de restauración de 6 h) y restauración probada en un entorno aparte. En el piloto se hicieron `pg_dump` antes de aplicar `sql/06`, `07` y `09` (no antes del cambio de zona de D-23 ni de `sql/10`); la restauración **no se probó**. | D-01, D-13; [C09] |

---

## 7. Decisiones que debe tomar el INEC

Estas decisiones no las puede tomar el piloto; de ellas dependen los requerimientos citados.

1. **Modalidad de QFieldCloud** (SaaS, organización o instancia propia) y plan que admita
   PostGIS con edición offline. Requerimientos 9, 10, 15.
2. **Gestión de identidades de campo:** de dónde salen las cuentas de los censistas y
   supervisores, cómo se dan de alta y de baja, y con qué se valida `encuestador`.
   Requerimientos 5, 15.
3. **Historial completo de visitas:** una fila por visita (recomendado por D-21) o solo el
   último estado. Requerimientos 2, 8.
4. **Cuestionario real:** campos temáticos del formulario, estados de visita y fórmula de
   avance. Reemplaza la decisión provisional D-15.
5. **Dónde corre el generador del tablero y dónde se publica:** servidor y cron
   institucionales, web interna y control de acceso. Requerimientos 14, 19.

---

## 8. Siguiente paso propuesto

| Paso | Qué valida | Qué necesita |
|---|---|---|
| (a) Cuenta QFieldCloud de prueba del INEC → prueba offline (D-22, parte 2) | Edición sin señal, sincronización, `@cloud_username`, secreto `pg_service` en el servidor, rol del lote tras sincronizar (D-19) y tiempo hasta el tablero | Cuenta o instancia con PostGIS (decisión 7.1); un celular; el proyecto `campo/NEON_campo_lote_A.qgs` y la guía `docs/guia/qfield_campo.md` |
| (b) Réplica del esquema en servidores del INEC | Que el procedimiento funciona fuera de Neon y con la red institucional; repetir las mediciones de S04 con roles de edición | Servidor PostgreSQL/PostGIS institucional, rol propietario para la carga, acceso de red desde QGIS; `docs/guia/Guia_replicacion_PostGIS.md` y `sql/plantillas/` |
| (c) Prueba de campo con un equipo real | Reparto por equipo, carga de trabajo real, usabilidad del formulario, precisión GNSS en condiciones de campo | Cuestionario real (7.4), criterio de reparto (provincia o UPM), un equipo de prueba con sus dispositivos, y los pasos (a) y (b) |

---

## 9. Anexos

### A. Decisiones registradas (`docs/DECISIONES.md`)

| Id | Decisión |
|---|---|
| D-01 | PostGIS gestionado en nube en lugar de PostgreSQL en estación institucional. |
| D-02 | Neon sobre Supabase. |
| D-03 | Reparto del trabajo impuesto por Row Level Security. |
| D-04 | Llave primaria entera IDENTITY; identificador de origen aparte. |
| D-05 | Carga por tabla de paso, no importación directa. |
| D-06 | Reparto por lote de UPM (A/B) en el piloto, no por provincia. |
| D-07 | Capa de visita como tabla de puntos separada. |
| D-08 | `ST_PointOnSurface` en lugar de `ST_Centroid`. |
| D-09 | Tablero como HTML estático generado por un script, leído con rol de solo lectura. |
| D-10 | Identidad en campo por atributo (`@cloud_username`), RLS solo para escritorio. |
| D-11 | Claude Code como ejecutor; Claude web como arquitecto y guía de interfaz. |
| D-12 | Cliente psql de PostgreSQL 18 en el PATH de usuario; Python con `py`. |
| D-13 | Servidor Neon 18.6; respaldo con `pg_dump` en lugar de rama; clave de rol por variable. |
| D-14 | Tablero: solo `tablero_lectura`, salida escapada, sin texto libre ni posición GNSS. |
| D-15 | Estados de visita, fórmula de avance y movimientos (provisional). |
| D-16 | `fecha_visita`: la fija el trigger solo si llega NULL. |
| D-17 | `NEON.qgz` fuera del repositorio hasta usar pg_service. |
| D-18 | Capa UGM del SNIT en el esquema `sim` como proxy de las fincas. |
| D-19 | Un proyecto QFieldCloud por lote, con el rol de su lote en el secreto pg_service. |
| D-20 | Corrección de la premisa de D-16: el trigger nunca sobrescribió `fecha_visita`. |
| D-21 | Piloto: `encuestador` y precisión de la última edición; fecha de la primera visita. |
| D-22 | Fase 3 dividida: conexión directa hoy; offline con QFieldCloud después. |
| D-23 | Zona de sesión fijada en la base: `America/Costa_Rica`. |
| D-24 | Presentación, logo y muestra fuera del repositorio público; el documento para TI sí se versiona. |

### B. Glosario

- **RLS (Row Level Security):** políticas de la base que deciden, fila por fila, qué puede
  leer o escribir cada rol. En el piloto: lectura total, escritura solo del lote propio.
- **Trigger:** función que la base ejecuta sola al insertar o actualizar; aquí sella quién y
  cuándo editó, y pone la hora de visita si llega vacía.
- **pg_service:** archivo de servicios de libpq que guarda los datos de conexión fuera del
  proyecto QGIS; el proyecto solo nombra el servicio (`service='neon_lote_a'`).
- **QFieldCloud:** servicio de QField para distribuir proyectos y sincronizar ediciones hechas
  sin señal. Su plan Community no admite capas PostGIS.
- **GitHub Actions:** ejecución programada o manual de scripts en servidores de GitHub; aquí
  regenera el tablero con un secreto cifrado.
- **GitHub Pages:** alojamiento de páginas estáticas de GitHub; aquí publica el tablero.

### C. Inventario del repositorio

| Carpeta | Contenido |
|---|---|
| `sql/plantillas/` | Scripts parametrizados 01–05 para replicar (estructura, carga, usuarios y acceso, seguimiento, verificaciones). |
| `sql/` | Scripts 06–10 tal como se ejecutaron (capa de visita, ajustes de vistas, visitas de prueba, fecha de visita, corrección de zona). |
| `sql/ejemplos_implementacion_real/` | Scripts de la Fase 1 tal como se ejecutaron. No se re-ejecutan. |
| `tablero/` | Generador del tablero, script de capturas, fixture de prueba. |
| `.github/workflows/` | Regeneración y publicación del tablero. |
| `campo/` | Proyecto QGIS de campo del lote A, construido y verificado por script, sin credenciales. |
| `sim/` | Scripts de la simulación a escala (S04). |
| `docs/guia/` | Guía de replicación, `pg_service` y QField en campo. |
| `docs/evidencia/` | Salidas literales y capturas por sesión (S04, S05, S06). |
| `docs/sesiones/` | Bitácora de cada sesión de trabajo. |
| `docs/requerimientos_ti/` | Este documento, insumos, evidencia de escala, banco de cifras y su verificador. |
| `specs/` | Encargos de cada sesión. |

### D. Cifras sin medir

| Cifra deseada | Situación |
|---|---|
| Tiempo entre sincronización de QFieldCloud y aparición en el tablero | Sin medir: requiere la parte 2 de D-22. |
| Ejecución real del cron cada 30 min | Sin medir: 0 ejecuciones por `schedule` observadas [C68]. |
| Costo del RLS con escrituras concurrentes a escala | Sin medir: las pruebas usaron el propietario. |
| Latencias desde la red institucional, la nube de TI o QField | Sin medir: todo desde la estación del piloto. |
| Comportamiento a 90.000 fincas (tamaño, vistas, tablero, paquete) | Sin medir: solo extrapolación desde 50.794 [C34, C35]. |
| Pico de almacenamiento durante la carga | Sin medir: estimado por suma [C37]. |
| Límite real de almacenamiento del plan gratuito | Sin verificar: 0,5 GB según el proveedor [C36]. |
| Concurrencia por encima de 25 conexiones (operativo: ~700 personas) | Sin medir [C04, C05, C43]. |
| Tiempo de restauración de un respaldo | Sin medir: no se probó restaurar. |
| Tiempos de visita y rendimiento por censista | Sin medir: no hubo operativo real; el proxy no sirve para esto. |
| Costos comparados (nube frente a autoalojado) | Sin medir: no hay cotizaciones en el repositorio. |
