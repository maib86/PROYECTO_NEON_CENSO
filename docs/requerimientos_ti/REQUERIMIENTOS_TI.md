# Requerimientos para producción derivados del piloto de edición concurrente

Piloto NEON-CENSO · Unidad de Cartografía · Instituto Nacional de Estadística y Censos (INEC)

Versión 2 · 15 de octubre de 2026 · Estado: entregable v2, pendiente de revisión. La versión 2
corrige la comunicación de la versión 1 (vocabulario único, D-25; identificadores; separadores)
sin cambiar su contenido técnico.

Cada cifra de este documento tiene una fila en `docs/requerimientos_ti/CIFRAS.csv` (columna
`id`, citada aquí entre corchetes, por ejemplo [C23]) con el archivo y la línea de donde salió.
`py docs/requerimientos_ti/verificar_cifras.py` comprueba que cada valor está, literal, en su
archivo de origen. Las cifras se escriben con coma decimal y punto de miles; el literal de
consola de cada una (a veces con punto decimal) está en `CIFRAS.csv`. Una sola unidad de
tamaño: MB de 1.048.576 bytes. Lo que no se midió dice «sin medir» y aparece en el anexo D.
Los términos siguen el vocabulario del anexo E.

---

## 1. Resumen ejecutivo

**Qué se probó.** Una capa vectorial única en una base de datos PostgreSQL con PostGIS, en la
nube y con datos públicos, editada a la vez por las cuentas de dos equipos de campo desde QGIS
escritorio y desde QField en un celular, con el reparto del trabajo impuesto por la base de
datos (control por fila (RLS, seguridad a nivel de fila)), auditoría automática de quién y
cuándo, y un tablero de avance HTML con regeneración automática. Se usaron 1.432 polígonos de
prueba públicos del distrito 20205 [C01, C02], repartidos en dos lotes de trabajo de 709 y 723
polígonos [C06, C07]. La escala se ensayó aparte con 50.794 polígonos UGM (proxy) del SNIT [C23].

**Qué quedó demostrado.** (a) La base de datos impide guardar fuera del lote de trabajo propio:
`UPDATE 1` en el lote de trabajo propio, `UPDATE 0` en el ajeno, `INSERT` ajeno rechazado
[C12, C13, C14]. (b) Con conexión directa desde el celular, las visitas entraron con la cuenta
del equipo A [C56]; la política la aplica la base de datos a la conexión. La prueba negativa
desde el celular (intentar guardar un polígono del lote de trabajo B) está preparada y no se
ha hecho. (c) El tablero lee solo vistas con una cuenta de solo lectura, no contiene
credenciales ni texto libre y se publicó con las visitas de campo [C15, C91, C69]. (d) Con
50.794 polígonos, 25 conexiones simultáneas guardaron sin errores y la red, no la base de
datos, fue el factor dominante [C25, C43].

**Qué no quedó demostrado.** La edición sin señal y su sincronización (requiere un plan de
QFieldCloud que admita PostGIS, D-22); la identidad individual de cada censista en campo
(`@cloud_username`); el comportamiento con 90.000 fincas (lo que se dice es extrapolación
[C24, C34]); el costo del control por fila a escala; tiempos desde la red institucional; la
regularidad de la regeneración automática (una sola ejecución por horario observada, casi 3 h
después de configurada [C89, C96]). El piloto corrió con dos personas y un celular.

**Qué se pide.** Las cinco decisiones de la sección 7 (modalidad de QFieldCloud, identidades de
campo, historial de visitas, cuestionario real, dónde corre el tablero) y los recursos del
siguiente paso (sección 8): una cuenta QFieldCloud de prueba con PostGIS, un servidor PostGIS
institucional para replicar la estructura y un equipo de campo real para una prueba acotada.
Los 20 requerimientos técnicos que se proponen para producción están en la sección 6.

---

## 2. Arquitectura probada

```
  QGIS escritorio ──┐   cuenta del equipo A o B (edit_lote_a / edit_lote_b)
                    │   conexión TLS (sslmode=require), sin pooling
  QField (celular) ─┤   conexión directa por pg_service (D-22, parte 1)
                    ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ PostgreSQL 18.6 + PostGIS 3.6.4 (Neon, plan gratuito)        │
  │  mgn.deteccion_cambio  polígonos de prueba, EPSG:5367        │
  │  mgn.finca_visita      un punto por polígono (formulario)    │
  │  Control por fila: lectura total · guardado por lote_trabajo │
  │  Sello automático de auditoría · hora de visita si es NULL   │
  │  Vistas v_tab_*  ── únicas legibles por la cuenta del tablero│
  └──────────────────────────────────────────────────────────────┘
                    │  cuenta del tablero (tablero_lectura), clave cifrada
                    ▼
  Regeneración automática (GitHub Actions: por horario y manual)
                    │  HTML estático, sin credenciales ni consultas al abrirse
                    ▼
  Tablero en GitHub Pages (público: aceptable solo con datos públicos)
```

| Elemento | Decisión que lo sostiene |
|---|---|
| Base de datos gestionada en la nube, solo tráfico saliente, sin instalaciones | D-01, D-02 |
| Reparto impuesto por el control por fila, con una cuenta por lote de trabajo; pruebas con las cuentas de los equipos A y B | D-03, D-06 |
| Llave entera `id` IDENTITY; identificador de origen aparte; carga por tabla de paso | D-04, D-05 |
| Capa de visita de puntos separada; punto garantizado dentro (`ST_PointOnSurface`) | D-07, D-08 |
| Tablero estático, cuenta de solo lectura, sin texto libre ni posición GNSS | D-09, D-14 |
| Identidad en campo por atributo; reparto en campo por proyecto y cuenta del equipo de campo | D-10, D-19 |
| Estados de visita y fórmula de avance (provisionales hasta el cuestionario real) | D-15 |
| Hora de visita: la pone el formulario de QField; en escritorio es la hora de guardado | D-16, D-20 |
| Zona horaria de sesión fijada en la base de datos (`America/Costa_Rica`) | D-23 |
| Campo en dos partes: conexión directa hoy; QFieldCloud sin señal después | D-22 |

**Quién ve qué.** Las cuentas de los equipos A y B leen toda la capa y guardan solo en su lote
de trabajo. La cuenta del tablero no lee tablas: `permission denied for table finca_visita`
[C15]; solo las cinco vistas `v_tab_*` [C84], que no exponen `observaciones` ni posición GNSS
(D-14). La cuenta administradora no está sujeta al control por fila: se usa para cambios de
estructura, la carga inicial y la simulación de escala, nunca para editar la capa del piloto
ni para probar el reparto.

**Identificadores.** En este documento, una visita se nombra por el número de su polígono de
prueba (columna `finca_id`). Cuando se cita el identificador de la fila de visita (columna
`id`), se rotula «id de fila».

---

## 3. Evidencia por fase

Fases según `ESPECIFICACION.md`. El resultado literal de consola está en el archivo de
evidencia y en `CIFRAS.csv`; aquí se escribe con la convención del documento.

### Fase 1 — Edición concurrente desde escritorio (completada)

| Criterio | Resultado | Evidencia |
|---|---|---|
| Capa cargada, válida y repartida | 1.432 polígonos de prueba: 709 en el lote de trabajo A y 723 en el B [C01, C06, C07] | `docs/sesiones/2026-10-13_sesion-00.md` |
| Control por fila, con las cuentas de los equipos A y B | prueba cruzada desde QGIS por dos personas: exitosa | `docs/sesiones/2026-10-13_sesion-00.md` |
| Guía de replicación y plantillas | `docs/guia/Guia_replicacion_PostGIS.md`; `sql/plantillas/01`–`05` | repositorio |

### Fase 2 — Capa de visita y tablero (completada el 15/10/2026; frecuencia de la regeneración automática sin demostrar)

| Criterio | Resultado | Evidencia |
|---|---|---|
| Un punto por polígono, dentro de él | 1.432 de 1.432 [C08] | `docs/DECISIONES.md` (D-08); sesión 02 |
| Control por fila en la capa de puntos | `UPDATE 1` propio · `UPDATE 0` ajeno · `new row violates row-level security policy` [C12–C14] | `docs/sesiones/2026-10-15_sesion-02.md` |
| Cuenta del tablero solo con vistas | `permission denied for table finca_visita` [C15] | sesión 02 |
| Visitas de prueba A y B | A: 15 desde QGIS por la persona [C16]; B: 20 simuladas por script [C17] | `ESPECIFICACION.md`; sesión 02 |
| Tablero con datos reales, 1.100 y 400 px | capturas sin defectos | `docs/evidencia/2026-10-15_tablero_1100.png`, `_400.png` |
| Regeneración automática | configurada cada 30 min [C10]; ejecución manual en verde (`38800395636`) [C20]. Hasta las 16:47 no hubo ninguna por horario [C68]; la primera, `38822130963`, llegó el 15/10/2026 a las 17:12 [C89, C90], casi 3 h después de configurada [C96] | `docs/evidencia/s06/01_tablero_publicado.txt`; `docs/evidencia/s07/01_regeneracion_y_tablero.txt` |
| HTML publicado sin credenciales | `HTTP 200` [C21]; cero apariciones de servidor y claves | sesión 03; `docs/evidencia/s07/01_regeneracion_y_tablero.txt` |

### Fase 3, parte 1 (D-22) — QField con conexión directa, sin QFieldCloud

| Criterio | Resultado | Evidencia |
|---|---|---|
| Proyecto de campo sin credenciales | `Resultado: 0 fallas` en 41 comprobaciones [C83]; solo `service='neon_lote_a'` [C53] | `docs/sesiones/2026-10-15_sesion-05.md` |
| Guardado desde el celular con la cuenta del equipo A | tras las 3 primeras visitas de campo, lote de trabajo A: 18 polígonos visitados, los 18 guardados por la cuenta del equipo A (15 desde QGIS y 3 desde el celular) [C56]; con la cuarta (polígono 1396, id de fila 1394 [C80]), 19 en el tablero publicado [C67] | `docs/evidencia/s05/05_prueba_qfield_directa.txt` |
| Prueba negativa desde el celular | **no hecha**: proyecto sin filtro de lote de trabajo preparado (`campo/construir_prueba_negativa.py`); la persona la ejecuta el 16/10 | `docs/guia/qfield_campo.md` |
| Hora real de la visita desde el formulario | primero, desfase de 6 h [C57] (zona de sesión `GMT` [C58]); tras D-23, la cuarta visita se guardó 25 s después de hecha [C59] | `docs/evidencia/s05/05_…`, `06_…`, `07_visita_tras_d23.txt` |
| Precisión GNSS registrada | 1,5 m en las tres primeras [C54]; 1,6 m en la cuarta [C60] | `docs/evidencia/s05/05_…`, `07_…` |
| Visitas de campo en el tablero publicado, sin `observaciones` | las 4 en «Últimos movimientos» (polígonos 1396, 1405, 1398, 1406) [C70]; `observaciones` 0 [C69]; generado el 15/10/2026 a las 17:54 [C91] | `docs/evidencia/s06/01_…`; `docs/evidencia/s07/01_…` |

### Fase 3, parte 2 (D-22) — QFieldCloud con PostGIS y edición sin señal: no probada

| Criterio | Estado | Causa |
|---|---|---|
| Proyecto publicado en QFieldCloud para edición sin señal | pendiente | el plan Community no admite capas PostGIS (D-22) |
| `encuestador = @cloud_username` | pendiente: queda vacío sin sesión de QFieldCloud | ídem |
| Clave en el servidor de QFieldCloud (no en el celular) | pendiente | ídem; hoy la clave está en el celular |
| Edición sin señal → sincronización → tablero; tiempo hasta aparecer | pendiente; tiempo **sin medir** | ídem |
| Identidad individual en `v_tab_encuestador` | pendiente: hoy la identidad es la cuenta del equipo de campo | ídem |

---

## 4. Escala

Fuente: `docs/requerimientos_ti/evidencia_escala.md` (S04, D-18) y sus salidas literales en
`docs/evidencia/s04/`. Proxy: 50.794 polígonos UGM del SNIT, el 56 % del tamaño de producción
[C23, C24]. Todas las mediciones desde una computadora del piloto, con 96,3 ms de ida y vuelta
de red (mediana) [C25]. Las mediciones de guardado usaron la cuenta administradora.

### 4.1 Medido con 50.794

| Medición | Resultado | Cifra |
|---|---|---|
| Carga con `ogr2ogr` a la tabla de paso | 31,8 s | C27 |
| `INSERT … SELECT` con `ST_MakeValid` | 5,7 s | C28 |
| Puntos de visita dentro de su polígono | 50.794 de 50.794 | C29 |
| Tamaño de los polígonos (`sim.ugm`, con índices) | 192 MB | C30 |
| Tamaño de los puntos (`sim.finca_visita`, máximo) | 16 MB | C31 |
| Base de datos completa antes / después | 17 MB / 225 MB | C32, C33 |
| Vistas agregadas del tablero (servidor, máximo) | 23,1 ms | C38 |
| `v_tab_puntos`, 50.794 filas (servidor / recibido en la computadora) | 145 ms / 1,5 s | C39, C40 |
| Guardados simultáneos, 1 conexión | 200 guardados · 9,5 por segundo · p95 136,4 ms · 0 errores | C41 |
| Guardados simultáneos, 10 conexiones | 2.000 guardados · 82,6 por segundo · p95 180,0 ms · 0 errores | C42 |
| Guardados simultáneos, 25 conexiones | 5.000 guardados · 206,1 por segundo · p95 179,3 ms · 0 errores | C43 |
| HTML del tablero con un marcador por punto | 3,98 MB · 51.349 elementos de la página | C44, C45 |
| Carga del tablero con el procesador frenado 4 veces | 4,7–4,8 s | C46 |
| Paquete de campo con polígonos / solo puntos | 208,5 MB / 6,2 MB (unas 34 veces menos) | C47–C49 |
| Cambio de área al reproyectar EPSG:8908 → 5367 | 0,002 % | C51 |

p95: el 95 % de los guardados tardó menos que ese valor. Los 7.200 guardados de prueba se
deshicieron a propósito al terminar [C52].

### 4.2 Extrapolado o estimado (no medido)

| Elemento | Estimación | Cifra |
|---|---|---|
| Polígonos con 90.000 fincas de complejidad similar | ≈ 340 MB | C34 |
| Puntos con 90.000 fincas | ≈ 28 MB | C35 |
| Pico de almacenamiento durante la carga con tabla de paso (50.794) | ≈ 403 MB, estimado por suma; pico **sin medir** | C37 |
| Límite del plan gratuito | 0,5 GB según el proveedor; **sin verificar** | C36 |

Con 90.000 polígonos de complejidad similar y el pico de la carga, el plan gratuito no
alcanza: producción necesita almacenamiento institucional dimensionado con la geometría real
de las fincas (sin medir hasta tener la capa).

### 4.3 Qué vale y qué no vale del proxy

**Vale para:** volumen y complejidad geométrica de una capa nacional; orden de magnitud de
almacenamiento y del paquete para trabajar sin señal; guardados cortos y simultáneos sobre
filas distintas con el sello automático activo; costo de las vistas y del HTML con decenas de
miles de puntos.

**No vale para:** tiempos de visita, rendimiento de censistas ni duración del operativo (los
polígonos UGM no son fincas); cobertura (las fincas se concentran en áreas rurales); cifras con
90.000 fincas (extrapolación); costo del control por fila (los guardados usaron la cuenta
administradora, que no está sujeta a él); tiempos desde la red institucional o desde QField.

---

## 5. Limitaciones del piloto y su causa

| Limitación | Por qué existió (qué no se tenía) | Qué hace falta para resolverla | Evidencia |
|---|---|---|---|
| Edición sin señal, sincronización e identidad `@cloud_username` no probadas | Cuenta QFieldCloud Community: no admite capas PostGIS | Cuenta o instancia QFieldCloud del INEC con PostGIS sin señal (decisión §7.1) y prueba D-22 parte 2 | D-22; `docs/evidencia/s05/05_…` (`encuestador` vacío) |
| Prueba negativa desde el celular no hecha | Se probó primero el caso positivo; la negativa se preparó en S07 | Ejecutarla con `campo/construir_prueba_negativa.py` y la guía | `docs/guia/qfield_campo.md` |
| Reparto en campo por proyecto y cuenta del equipo de campo, no por persona | QFieldCloud aplica cambios con la conexión del proyecto; no hay cuenta de base de datos por censista (supuesto D-19 sin verificar en QFieldCloud) | Verificar `editado_por` tras sincronizar; identidad individual por atributo restringido (req. 5, 15) | D-10, D-19 |
| Hora de visita desde escritorio = hora de guardado | QGIS escritorio deja `fecha_visita` vacía; `now()` es la hora de la transacción: 15 visitas a las 13:02:30 [C18] | Registrar visitas solo desde el formulario de campo, que pone la hora del celular | D-16, D-20; sesión 02 |
| Escala: 50.794 polígonos UGM (proxy), no 90.000 fincas | No existe aún la capa de fincas del censo | Capa real de fincas (o una muestra provincial) cargada en la infraestructura del INEC | D-18; `evidencia_escala.md` |
| Datos y tablero públicos; en el plan gratuito solo se puede volver atrás 6 horas [C09] | Sin infraestructura institucional ni permisos de TI para el piloto | Servidor PostGIS institucional, web interna con autenticación, respaldo programado y restauración probada | D-01, D-09 |
| Dos personas y un celular | Alcance del piloto | Prueba de campo con un equipo de campo real (sección 8c) | `ESPECIFICACION.md` §2 |
| Clave de la base de datos en el celular | Conexión directa sin QFieldCloud (D-22, parte 1) | Clave en el servidor de QFieldCloud o gestión de dispositivos móviles (MDM) institucional (req. 10) | D-22 |
| Una fila por polígono: la revisita reescribe persona y precisión, conserva la primera fecha | `UNIQUE(finca_id)` en el piloto | Una fila por visita, con coherencia lote de trabajo ↔ polígono (req. 2, 8) | D-07, D-21 |
| Regeneración automática irregular | Servicio gratuito de GitHub sin horario garantizado: configurada a las 14:14, la primera ejecución por horario llegó a las 17:12 [C90, C96] | Regeneración automática institucional con monitoreo y alerta si no ocurre (req. 14) | `docs/evidencia/s07/01_regeneracion_y_tablero.txt` |
| Encabezado del tablero: «22 incidencias» no distinguía las revisitas pendientes [C65] | La etiqueta sumaba revisitas a no localizadas y rechazos | Corregido en S06 y S07 (`tablero/generar_tablero.py`): «22 incidencias, de ellas 6 revisitas…», visible en el publicado de las 17:54 [C92]; el singular («1 revisita») y la misma redacción en las tarjetas de cada lote de trabajo se publican con el próximo envío al repositorio | sesiones 06 y 07 |
| Costo del control por fila a escala y tiempos desde la red institucional, sin medir | Pruebas de escala con la cuenta administradora, desde la computadora del piloto | Repetir la prueba de guardados simultáneos con las cuentas de los equipos de campo, desde la red y la nube de TI (req. 17) | `evidencia_escala.md` |
| Estados de visita y fórmula de avance provisionales | Sin cuestionario real del censo | Cuestionario real (decisión §7.4) | D-15 |

---

## 6. Requerimientos que se proponen para producción

Ninguno está aprobado: es la propuesta del piloto para revisión de TI. Numeración continua:
1 a 11 vienen de `docs/requerimientos_ti/insumos_piloto.md` [C95]; 12 en adelante surgen de la
sección 5 de este documento y de los hallazgos de S04, como indica su origen. En las tablas,
el nombre técnico va entre paréntesis.

### 6.1 Base de datos

| # | Requerimiento | Origen |
|---|---|---|
| 1 | Vistas del tablero con `security_invoker = true` y políticas propias para la cuenta del tablero cuando la lectura deba restringirse por zona de equipo o confidencialidad. | Sesión 02; D-14 |
| 2 | Coherencia lote de trabajo ↔ polígono en la capa de visita (FK compuesta o función que copie el valor) antes de retirar `UNIQUE(finca_id)`. | Sesión 02; D-07, D-14 |
| 8 | Cada visita es una fila, con su persona, fecha y precisión propias. | D-21; D-07 |
| 11 | Zona horaria de sesión fijada en la base de datos (`ALTER DATABASE … SET timezone`), no confiada al cliente. | D-23 |
| 12 | Almacenamiento dimensionado con la geometría real de las fincas, con margen para el pico de carga; carga sin tabla de paso duplicada o por partes. | S04, hallazgo 5; [C34, C37] |
| 13 | Sistema de referencia oficial del marco de fincas definido antes de cargar (el proxy venía en EPSG:8908). | S04, hallazgo 7; [C51] |
| 16 | Columna de reparto por zona de equipo (por definir: provincia o UPM), `NOT NULL` + `CHECK` o FK a una tabla de zonas de equipo; una cuenta por equipo de campo. | D-03, D-06; S04, provincias 1–7 como valores [C85] |

### 6.2 Identidad y acceso

| # | Requerimiento | Origen |
|---|---|---|
| 3 | Claves de las cuentas de la base de datos fijadas con `\password` (cifrado SCRAM calculado en el cliente), no escritas en sentencias SQL que pueden quedar en registros. | D-13 |
| 5 | `encuestador` restringido a nombres de cuenta válidos (CHECK, dominio o FK a la lista de cuentas de campo). | Sesión 02; D-14 |
| 15 | Una cuenta por persona en campo (QFieldCloud o el sistema de identidades del INEC), nunca compartida; la identidad individual llega por atributo y se valida contra el req. 5. | D-10, D-19; `ESPECIFICACION.md` §4, restricción 4 |

### 6.3 Campo

| # | Requerimiento | Origen |
|---|---|---|
| 7 | Paquete de campo restringido a la zona de equipo: puntos de visita de esa zona de equipo y polígonos recortados o como teselas. | S04, hallazgo 6; D-19; [C47, C48] |
| 9 | Plan de QFieldCloud del INEC que admita capas PostGIS con edición sin señal. | D-22; D-19 |
| 10 | Claves de la base de datos en el celular solo con gestión de dispositivos móviles (MDM). | D-22 |
| 18 | Hora de la visita tomada del celular por el formulario de campo; la edición desde escritorio se declara como hora de guardado. | D-16, D-20, D-23 |

### 6.4 Tablero

| # | Requerimiento | Origen |
|---|---|---|
| 4 | Ninguna vista que alimente un tablero publicado expone texto libre ni posición GNSS. | D-14 |
| 6 | Tablero agregado por distrito o cuadrícula (dibujado como imagen o por teselas), no un marcador por finca; paleta y vista por persona que no supongan dos lotes de trabajo. | S04, hallazgos 1 y 2; [C44–C46, C50] |
| 19 | Tablero de producción en web interna con autenticación (estadística confidencial); nunca en un sitio público. | D-09; `ESPECIFICACION.md` §2 |

### 6.5 Operación y respaldo

| # | Requerimiento | Origen |
|---|---|---|
| 14 | Regeneración automática del tablero en servidores institucionales, con monitoreo: alerta si una regeneración no ocurre o falla. | Sesiones 06 y 07 [C68, C96] |
| 17 | Prueba de carga con las cuentas de los equipos de campo (control por fila activo), desde la red institucional y con el número de conexiones previsto en el operativo. | S04, «no vale para»; [C43] |
| 20 | Respaldo programado de la base de datos (no depender de poder volver atrás solo 6 horas) y restauración probada en un entorno aparte. En el piloto se hicieron `pg_dump` antes de aplicar `sql/06`, `07` y `09` (no antes del cambio de zona horaria de D-23 ni de `sql/10`); la restauración **no se probó**. | D-01, D-13; [C09] |

---

## 7. Decisiones que debe tomar el INEC

Son cinco. El piloto no las puede tomar; de ellas dependen los requerimientos citados.

1. **Modalidad de QFieldCloud** (como servicio, como organización o en instancia propia) y plan
   que admita PostGIS con edición sin señal. Requerimientos 9, 10, 15.
2. **Gestión de identidades de campo:** de dónde salen las cuentas de los censistas y
   supervisores, cómo se dan de alta y de baja, y con qué se valida `encuestador`.
   Requerimientos 5, 15.
3. **Historial completo de visitas:** una fila por visita (recomendado por D-21) o solo el
   último estado. Requerimientos 2, 8.
4. **Cuestionario real:** campos temáticos del formulario, estados de visita y fórmula de
   avance. Reemplaza la decisión provisional D-15. Hoy el formulario solo tiene estado, hora,
   persona, precisión GNSS y observaciones.
5. **Dónde corre la regeneración automática del tablero y dónde se publica:** servidores
   institucionales, web interna y control de acceso. Requerimientos 14, 19.

---

## 8. Siguiente paso propuesto

En orden de dependencia: (c) necesita (a) y (b).

| Paso | Qué valida | Qué necesita |
|---|---|---|
| (a) Cuenta QFieldCloud de prueba del INEC → prueba sin señal (D-22, parte 2) | Edición sin señal, sincronización, `@cloud_username`, clave en el servidor, cuenta del equipo de campo tras sincronizar (D-19) y tiempo hasta el tablero | Cuenta o instancia con PostGIS (decisión §7.1); un celular; el proyecto `campo/NEON_campo_lote_A.qgs` y la guía `docs/guia/qfield_campo.md` |
| (b) Réplica de la estructura en servidores del INEC | Que el procedimiento funciona fuera de Neon y con la red institucional; repetir las mediciones de S04 con las cuentas de los equipos de campo | Servidor PostgreSQL/PostGIS institucional, cuenta administradora para la carga, acceso de red desde QGIS; `docs/guia/Guia_replicacion_PostGIS.md` y `sql/plantillas/` |
| (c) Prueba de campo con un equipo de campo real | Reparto por zona de equipo, carga de trabajo real, usabilidad del formulario, precisión GNSS en condiciones de campo | Cuestionario real (§7.4), criterio de reparto (provincia o UPM), un equipo de campo de prueba con sus celulares, y los pasos (a) y (b) |

---

## 9. Anexos

### A. Decisiones registradas (`docs/DECISIONES.md`)

Resumen con el vocabulario del anexo E; el texto completo de cada decisión está en el archivo.

| Id | Decisión |
|---|---|
| D-01 | Base de datos PostGIS gestionada en la nube en lugar de una computadora institucional. |
| D-02 | Neon sobre Supabase. |
| D-03 | Reparto del trabajo impuesto por el control por fila. |
| D-04 | Llave primaria entera IDENTITY; identificador de origen aparte. |
| D-05 | Carga por tabla de paso, no importación directa. |
| D-06 | Reparto en dos lotes de trabajo (A/B) formados por UPM en el piloto, no por provincia. |
| D-07 | Capa de visita como tabla de puntos separada. |
| D-08 | `ST_PointOnSurface` en lugar de `ST_Centroid`. |
| D-09 | Tablero como HTML estático generado por un script, leído con una cuenta de solo lectura. |
| D-10 | Identidad en campo por atributo (`@cloud_username`); control por fila solo para escritorio. |
| D-11 | Claude Code como ejecutor; Claude web como arquitecto y guía de interfaz. |
| D-12 | Cliente psql de PostgreSQL 18 en el PATH de la cuenta de Windows; Python con `py`. |
| D-13 | Servidor Neon `18.6`; respaldo con `pg_dump` en lugar de rama; clave de cuenta por variable. |
| D-14 | Tablero: solo la cuenta del tablero, salida escapada, sin texto libre ni posición GNSS. |
| D-15 | Estados de visita, fórmula de avance y movimientos (provisional). |
| D-16 | `fecha_visita`: la fija la base de datos solo si queda vacía. |
| D-17 | `NEON.qgz` fuera del repositorio hasta usar pg_service. |
| D-18 | Capa de polígonos UGM del SNIT en el esquema `sim` como proxy de las fincas. |
| D-19 | Un proyecto QFieldCloud por lote de trabajo, con la cuenta de su equipo de campo en la clave del servidor. |
| D-20 | Corrección de la premisa de D-16: la base de datos nunca sobrescribió `fecha_visita`. |
| D-21 | Piloto: `encuestador` y precisión de la última edición; fecha de la primera visita. |
| D-22 | Fase 3 dividida: conexión directa hoy; sin señal con QFieldCloud después. |
| D-23 | Zona horaria de sesión fijada en la base de datos: `America/Costa_Rica`. |
| D-24 | Presentación, logo y muestra fuera del repositorio público; el documento para TI sí se versiona. |
| D-25 | Vocabulario único en la presentación y en este documento (anexo E). |
| D-26 | Catálogo de cuatro estados y uso del color en la presentación. |

### B. Glosario

- **Control por fila (RLS, Row Level Security):** políticas de la base de datos que deciden,
  fila por fila, qué puede leer o guardar cada cuenta. En el piloto: lectura total, guardado
  solo en el lote de trabajo propio.
- **Sello automático (trigger):** función que la base de datos ejecuta sola al insertar o
  actualizar; aquí sella quién y cuándo editó, y pone la hora de visita si queda vacía.
- **pg_service:** archivo de servicios de libpq que guarda los datos de conexión fuera del
  proyecto QGIS; el proyecto solo nombra el servicio (`service='neon_lote_a'`).
- **QFieldCloud:** servicio de QField para distribuir proyectos y sincronizar ediciones hechas
  sin señal. Su plan Community no admite capas PostGIS.
- **GitHub Actions:** servicio de GitHub que ejecuta scripts por horario o a mano; aquí hace la
  regeneración automática del tablero con una clave cifrada.
- **GitHub Pages:** alojamiento de páginas estáticas de GitHub; aquí publica el tablero.
- **UGM, SNIT, UPM, MDM:** unidades geoestadísticas mínimas; Sistema Nacional de Información
  Territorial; unidades primarias de muestreo; gestión de dispositivos móviles.
- **p95:** valor por debajo del cual quedó el 95 % de los tiempos medidos.

### C. Inventario del repositorio

| Carpeta | Contenido |
|---|---|
| `sql/plantillas/` | Scripts parametrizados 01–05 para replicar (estructura, carga, cuentas y acceso, seguimiento, verificaciones). |
| `sql/` | Scripts 06–10 tal como se ejecutaron (capa de visita, ajustes de vistas, visitas de prueba, fecha de visita, corrección de zona horaria). |
| `sql/ejemplos_implementacion_real/` | Scripts de la Fase 1 tal como se ejecutaron. No se re-ejecutan. |
| `tablero/` | Generador del tablero, script de capturas, datos de prueba. |
| `.github/workflows/` | Regeneración automática y publicación del tablero. |
| `campo/` | Proyecto QGIS de campo del lote de trabajo A, construido y verificado por script, sin credenciales; script de la prueba negativa. |
| `sim/` | Scripts de la simulación a escala (S04). |
| `docs/guia/` | Guía de replicación, `pg_service` y QField en campo (con la prueba negativa). |
| `docs/evidencia/` | Salidas literales y capturas por sesión (S04 a S07). |
| `docs/sesiones/` | Bitácora de cada sesión de trabajo. |
| `docs/requerimientos_ti/` | Este documento, insumos, evidencia de escala, banco de cifras y sus verificadores (cifras y vocabulario). |
| `specs/` | Encargos de cada sesión. |

### D. Cifras sin medir

| Cifra deseada | Situación |
|---|---|
| Tiempo entre sincronización de QFieldCloud y aparición en el tablero | Sin medir: requiere la parte 2 de D-22. |
| Regularidad de la regeneración automática cada 30 min | Sin medir: una sola ejecución por horario observada, casi 3 h después de configurada [C89, C96]. |
| Costo del control por fila con guardados simultáneos a escala | Sin medir: las pruebas usaron la cuenta administradora. |
| Latencias desde la red institucional, la nube de TI o QField | Sin medir: todo desde la computadora del piloto. |
| Comportamiento con 90.000 fincas (tamaño, vistas, tablero, paquete) | Sin medir: solo extrapolación desde 50.794 [C34, C35]. |
| Pico de almacenamiento durante la carga | Sin medir: estimado por suma [C37]. |
| Límite real de almacenamiento del plan gratuito | Sin verificar: 0,5 GB según el proveedor [C36]. |
| Concurrencia por encima de 25 conexiones (operativo: ~700 personas) | Sin medir [C04, C05, C43]. |
| Tiempo de restauración de un respaldo | Sin medir: no se probó restaurar. |
| Tiempos de visita y rendimiento por censista | Sin medir: no hubo operativo real; el proxy no sirve para esto. |
| Costos comparados (nube frente a servidores propios) | Sin medir: no hay cotizaciones en el repositorio. |

### E. Vocabulario

Un término por concepto en este documento y en la presentación (D-25). La columna «Nunca»
lista lo que no se usa para ese concepto.

| Concepto | Término único | Nunca |
|---|---|---|
| La base PostgreSQL/PostGIS | «base de datos» (completo en títulos y en el cuerpo) | «la base» sola |
| Objetos del piloto | «polígonos de prueba» (1.432, distrito 20205) | finca, objeto, UGM |
| Objetos de producción | «fincas» | — |
| Capa del proxy de escala | «polígonos UGM (proxy)» | fincas, objetos |
| Unidad de reparto del piloto | «lote de trabajo A/B» | lote, parte, zona, equipo |
| Unidad de reparto en producción | «zona de equipo (por definir: provincia o UPM)» | zona a secas |
| Cuenta dueña de la base de datos | «cuenta administradora» | propietario, rol, nombre técnico de la cuenta |
| Cuentas `edit_lote_a` / `edit_lote_b` | «cuenta del equipo A/B» (en tablas técnicas, el nombre entre paréntesis) | rol, usuario |
| Cuenta `tablero_lectura` | «cuenta del tablero» | rol |
| Operación de guardado | «guardados» / «guardados por segundo» | escrituras, op/s |
| Control por fila | «control por fila (RLS)» en la primera aparición; después «control por fila» | RLS solo |
| Regeneración del tablero | «regeneración automática» | cron, schedule, workflow, programa |
| Hardware | «computadora» | equipo |
| Personas | «equipo de campo» | equipo a secas |
| Estado terminal de visita | «visita concluida» | cerrada |
| Fase terminada | «completada» | cerrada |
| Ventana de Neon | «solo se puede volver atrás 6 horas» | restauración de 6 h |
| Revisor | «revisión automática independiente (programa, sin acceso a la conversación)» | agente |
| Identificador de visita | número de polígono (`finca_id`); el `id` de la fila se rotula «id de fila» | id sin rótulo |
| Unidades | coma decimal, punto de miles, MB de 1.048.576 bytes | punto decimal, MiB |
