# S08d — Presentación v4 en dos partes, guion de demostración, documento TI v4 y entrega

## Objetivo
Construir la presentación v4 (22 láminas) a partir de `docs/presentacion/guion_v4.md`,
que es la fuente de contenido de cada lámina: qué va en pantalla, qué captura o esquema,
qué cifras, qué píldora, y las notas del orador («Qué pasa detrás», «Frase de cierre»,
«Pregunta probable»). Reutilizar el motor visual y las láminas de la v3 (mismo HTML
autocontenido, mismos estilos, estados D-26, vocabulario D-25/D-27, marcas `data-cifra`).
Producir además el guion de demostración con los ids reales, el documento TI v4 con su PDF,
las cifras nuevas, los verificadores en verde y `ENTREGA_2026-10-19/` regenerada.

Hora límite dura: **13:00**. A esa hora se entrega lo que esté verde; lo que falte se
reporta. Prioridad si el tiempo no alcanza: 1) deck v4, 2) guion de demostración,
3) documento TI v4 + PDF, 4) capturas y ENTREGA.

## Entradas
- `docs/presentacion/guion_v4.md` (manda sobre el deck v3 en orden y contenido).
- `docs/presentacion/capturas_persona/`: 01, 02, 04, 05, 06, 07, 08, 08b, 09 (no existe 03).
- Deck v3 (`docs/presentacion/`), `CIFRAS.csv`, `REQUERIMIENTOS_TI.md` v3,
  `docs/presentacion/auditoria/respuesta_ronda2.md`, bitácoras de las sesiones 08, 09 y 10,
  `docs/evidencia/s08b/`, `docs/evidencia/s08c/`, `docs/evidencia/s08/01`.

## Decisiones que registra (docs/DECISIONES.md)
- D-29 · Presentación v4 en dos partes («Qué está corriendo» / «Qué hace falta para el
  censo»), abierta con el tablero en vivo; 22 láminas construidas desde un guion escrito por
  un revisor sin contexto previo; cada lámina lleva en notas del orador la explicación de
  qué mecanismo actúa detrás de lo que se ve. Dato nuevo registrado: QFieldCloud corre en
  servidores del INEC (dicho por el encargado del censo, 16/10); que su instancia admita
  capas PostGIS es inferencia PENDIENTE DE TI. Entregable del documento: NEON-TI-01 v4.
  Descartado: rehacer el sistema visual (sin tiempo; la v3 ya fue auditada dos rondas).

## Pasos

### 1. Guion de demostración con ids reales — 15 min
Con `DATABASE_URL_TABLERO` o la cuenta administradora en solo lectura, obtener de
`mgn.finca_visita` (unida a `deteccion_cambio` para UPM y UGM) la lista de polígonos con
estado distinto de pendiente y `editado_por = 'edit_lote_a'`, separando: guardados desde
QGIS (precision_gnss_m NULL; 15 esperados) y desde QField (precision_gnss_m no nulo;
4 esperados: 1396, 1398, 1405, 1406 u otros según la base). Más el 258 (lote B, prueba
negativa). Escribir `docs/presentacion/guion_demostracion.md` (fuera del repositorio):
la sección §4 del guion (3 minutos) con los ids concretos a buscar, qué dice cada ficha
(estado, fecha, precisión, cuenta), y la línea para el 258: «se editó y guardó en el
celular; la base de datos no cambió la fila: UPDATE 0». Evidencia: la consulta y su salida
en `docs/evidencia/s08d/01_ids_demostracion.txt`.

### 2. Cifras nuevas — 10 min
Agregar a `CIFRAS.csv` (C108 en adelante), con archivo y línea de origen: 39 guardados
con estado distinto de pendiente; 33 concluidas y 2,3 %; 22 incidencias / 6 revisitas
(si no existen ya); 1.186.359 bytes = 1,13 MB del HTML; 44 UGM; 23 sin UGM; 7 vistas
(5 + 2); 403.490 bytes del respaldo; consumo de Neon 1,63 CU-h, 0,26 GB, 0,43 GB
(fuente: captura 08b, anotar «lectura de consola, 16/10»); prueba negativa SUPERADA
(evidencia s08b); 4 ejecuciones por horario ya existen (C100, C101). Las cifras de
consumo de Neon se marcan como lectura de pantalla, no de script.

### 3. Presentación v4 — 90 min
`docs/presentacion/PRESENTACION_NEON_CENSO_2026-10-19.html` (v4; conservar la v3 como
`_v3.html`). Construir las 22 láminas siguiendo el guion lámina por lámina:
- Título, texto en pantalla y cifras exactamente como el guion; cada cifra con `data-cifra`.
- Capturas de la persona insertadas desde `capturas_persona/` con las llamadas numeradas
  que el guion indica (superponer rótulos, no editar las imágenes). Capturas por script:
  tablero publicado a 1100 px con las cuatro llamadas de L02; salida literal de la
  reproducción `UPDATE 0 / UPDATE 1` para L10 (desde `docs/evidencia/s08b/03`).
- Esquemas SVG inline (L03, L06, L09, L10, L11, L17, L18): cajas y flechas como el guion,
  tipografía y colores del sistema visual v3; sin logotipos de terceros.
- Tabla «Función de cada pieza» en L03 (dos columnas en pantalla; la tercera en notas).
- Notas del orador por lámina: «Qué pasa detrás», «Frase de cierre», «Pregunta probable»,
  en el mismo mecanismo de notas de la v3.
- Píldoras de estado solo las cuatro de D-26; rojo solo NO PROBADO / riesgo.
- Marcadores «[DATO NO DISPONIBLE: …]» del guion: no se muestran; la línea se omite y se
  anota en la bitácora.
- Las cifras del tablero v2 citadas en el guion como «brief, sesión 10» usan las filas
  del paso 2.

### 4. Documento TI v4 y PDF — 30 min
`REQUERIMIENTOS_TI.md` → v4 (rótulo «NEON-TI-01 · v4» en encabezado, portada y
`exportar_pdf.py`):
- §1(b), §3, §5: prueba negativa desde el celular «hecha» (sesión 09, UPDATE 0, fila
  intacta; límite: no registra el intento).
- Sección nueva «Migración desde el piloto» (según L17 del guion): qué hace hoy Neon;
  qué es propio y estándar; los seis puntos de migración; cada uno con el requerimiento
  que lo cubre.
- §7.1 y req. 9: dato del 16/10 (QFieldCloud en servidores del INEC) como contexto;
  verificación de PostGIS en esa instancia como PENDIENTE DE TI.
- Tablero: vistas 5 + 2, tablero v2 (D-28), nota de escala a 90.000 (teselas o
  agregación) en req. 6 y 14.
- Anexo A: D-28 y D-29. Anexo E: sin términos nuevos salvo «zona de equipo» ya existente.
- Regenerar PDF y HTML del documento.

### 5. Verificaciones — 20 min
- `py docs/requerimientos_ti/verificar_cifras.py` → 0 fallas (deck v4 y documento v4).
- `py docs/requerimientos_ti/verificar_vocabulario.py` → prohibidos 0 (deck, notas,
  documento, guion_demostracion.md).
- `py docs/presentacion/capturar_laminas.py` → 22 láminas, 0 fallas, 0 errores JS;
  capturas a `docs/presentacion/ENTREGA_2026-10-19/laminas/`.
- Grep sobre deck, PDF y documento: `neon\.tech`, `npg_`, `postgres(ql)?://` = 0;
  «sin cerrar», «proxy», «mosaico» = 0; «la base» sin « de datos» = 0.
- `revisor-auditoria` sobre el deck v4 con tres preguntas: ¿cada lámina responde la
  pregunta del guion sin conocer el proyecto?; ¿alguna cifra en pantalla no está en
  CIFRAS.csv?; ¿algo presentado como hecho está en la lista §3 del guion («lo que no se
  puede afirmar»)? Corregir hallazgos altos y medios antes de entregar.

### 6. Entrega — 15 min
`docs/presentacion/ENTREGA_2026-10-19/`: deck v4, PDF v4, `CIFRAS.csv`, 22 capturas,
`guion_v4.md`, `guion_demostracion.md`, `respuesta_ronda2.md`, bitácora 10.
Versionar lo que corresponde (`REQUERIMIENTOS_TI.md`, `CIFRAS.csv`, `exportar_pdf.py`,
DECISIONES, ESPECIFICACION, bitácora); `docs/presentacion/` sigue fuera (D-24).
Commit «docs(presentacion): presentación v4 en dos partes y documento TI v4 — guion con
“qué pasa detrás” y dato de QFieldCloud del INEC». Push solo con confirmación.
Bitácora `docs/sesiones/2026-10-16_sesion-11.md`.

## Puntos de detención
- Solo lectura en la base de datos. Ningún cambio de esquema ni de datos.
- Push solo con confirmación explícita.
- 13:00: entregar lo verde y reportar lo demás.

## Criterios de aceptación
- 22 láminas que siguen el guion en orden y contenido; notas del orador completas.
- Verificadores en verde; grep de credenciales y vocabulario en 0; revisión independiente
  sin altos ni medios abiertos.
- Documento v4 con rótulo v4 en todas sus salidas y sección de migración.
- `guion_demostracion.md` con ids reales y evidencia.
- Resumen de 10 líneas para Claude web con: número de láminas, hallazgos de la revisión,
  qué quedó fuera por tiempo.

## Fuera de alcance
Cambios al tablero publicado; borrado de `sim`; D-22 parte 2; cotizaciones de producción.