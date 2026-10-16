# SPEC S08 — Ronda 3 de comunicación y cierre de entregables

Fecha: 2026-10-16 · Entrega: 2026-10-16 12:00 (ronda 3 externa antes de las 15:00).
Modo: desatendido; solo el push espera confirmación.
Insumos obligatorios: docs/presentacion/auditoria/informe_ronda2.md (24 defectos nuevos
N-01…N-24 y 11 parciales), respuesta_ronda1.md, y el resultado de la prueba negativa que la
persona pega en el prompt. Cada N-xx y cada parcial se atiende o se rechaza con razón.

## 0. Confirmaciones de la persona (se aplican tal cual)
- Siglas: UGM = unidades geoestadísticas mínimas; UPM = unidades primarias de muestreo;
  SNIT = Sistema Nacional de Información Territorial; MDM = gestión de dispositivos móviles.
  Fuente en CIFRAS/anexo E: «confirmado por la persona responsable, sesión 08».
- Distrito 20205 = Piedades Sur, cantón San Ramón, provincia Alajuela (División Territorial
  Administrativa; confirmado por la persona). Va en L05 y en el documento.
- D-27: etiqueta del tablero «N incidencias, de ellas M revisitas pendientes» (reemplaza «sin
  cerrar»; cierra el conflicto M-19). Aplicar en generar_tablero.py, fixture y pruebas.

## 1. Prueba negativa desde el celular (resultado pegado en el prompt)
Si HECHA: verificar como cuenta administradora que la fila del lote B indicada no cambió
(estado, editado_por, fecha_edicion iguales a antes) y registrar el mensaje que mostró QField.
L04 fila «Prueba negativa» → PROBADO; L08 recuadro → «intentó guardar un polígono del lote
B desde el celular: ninguna fila cambió»; L13 fila nueva; documento §1(b), §3, §5. Evidencia
en docs/evidencia/s08/. Si NO HECHA: quitar toda fecha («16/10») y dejar «pendiente» (N-14).

## 2. Defectos medios de la ronda 2
- N-01: una sola formulación para la regeneración automática en L04, L13 y documento (§3, §5,
  anexo D): «se ejecutó sola una vez; frecuencia no demostrada», píldora MEDIDO con esa nota
  (no NO PROBADO). Antes, actualizar el dato: `gh run list --event schedule` y, si ya hay
  varias ejecuciones, decir cuántas y con qué intervalos.
- N-02: L08 separar «desfase de 6 h: corregido (D-23)» de «25 s: tiempo normal entre visita y
  guardado», sin flecha.
- N-03: L10 y documento §4.2: mostrar la estimación que sostiene «no alcanza»: pico a 90.000
  = 403 × 90.000 / 50.794 ≈ 714 MB (rotulado «estimado por proporción, sin medir») frente a
  «0,5 GB ≈ 512 MB». Si la cifra 403 no es proporcional por construcción, decirlo y reformular
  el recuadro como margen insuficiente. Fila nueva en CIFRAS.
- N-04: L07 «Repositorio público (D-01: datos públicos), alojado en una cuenta personal porque
  el piloto no tenía cuenta institucional; para producción, repositorio del INEC (req. 19)».
  Nota del orador igual.

## 3. Defectos bajos N-05…N-24 y parciales
Aplicar todos según la dirección del informe. En particular: «teselas» en deck y documento
(N-05, agregar a D-25); caja de L11 sin verde (N-06); publicar antes de capturar para que L07
coincida con la página del QR y rotular «regeneración manual de las 17:54» o la que
corresponda (N-07, N-21); «3a/3b/3c» (N-08, B-02); L16 columna de estado y fila c con estado
«Pendiente de la Unidad y del censo» o sin píldora (N-09); L10 título «las consultas del
tablero respondieron en milisegundos» (N-17); «sustituto» por «proxy» en la 1.ª aparición
(N-18); L12 «el mapa del tablero con un marcador por punto» (N-16); L13 fila de la prueba
negativa y fuente de «sin horario garantizado» (N-13, N-15); L11 «en la capa de simulación»
(N-22); encabezados de tabla y rótulos de tarjeta ≥ 11 px (M-23); columnas «Tiempo total» y
«mediana» de L11 con fila en CIFRAS y presentes en el documento §4.1, o fuera (M-13); pies con
líneas de sesión-02 recalculadas con el archivo vigente (M-14, B-07).

## 4. Publicación y coherencia final
- Push (confirmado) para que el tablero publicado lleve D-27 y el singular; después, captura
  nueva de L07 desde la página publicada, no local.
- verificar_cifras.py, verificar_vocabulario.py (agregar «proxy», «sin cerrar», «mosaicos» a
  prohibidos) y capturar_laminas.py en verde. PDF regenerado. Revisión automática
  independiente con foco en los N-xx.
- docs/presentacion/auditoria/respuesta_ronda2.md: tabla N-01…N-24 y parciales → acción.
- Copia de entrega: docs/presentacion/ENTREGA_2026-10-19/ con el deck, el PDF, CIFRAS.csv y
  las 18 capturas (carpeta ignorada por git).
- D-27 en DECISIONES; ESPECIFICACION Fase 4 «entregables v3»; bitácora sesión 08; commit;
  push confirmado. Resumen de 10 líneas y lista de rechazos con razón.

## Criterios de aceptación
- [ ] N-01…N-04 resueltos; N-05…N-24 y parciales atendidos o rechazados con razón.
- [ ] Captura de L07 tomada de la página publicada con D-27 visible.
- [ ] Prueba negativa reflejada igual en L04, L08, L13 y documento.
- [ ] Verificadores en verde; PDF v3; carpeta ENTREGA completa.

## Fuera de alcance
QFieldCloud (D-22 parte 2); borrado de sim (después del lunes); cambios de contenido.