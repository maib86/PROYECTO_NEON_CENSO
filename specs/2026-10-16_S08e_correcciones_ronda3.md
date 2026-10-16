# S08e — Correcciones de la ronda 3 y lámina de preguntas frecuentes

## Objetivo
Aplicar al deck v4, al guion de demostración y al documento TI los hallazgos de
`docs/presentacion/auditoria/informe_ronda3.md` (10 ALTOS sostenidos, 31 MEDIOS, los BAJOS
que quepan), y agregar la lámina de respaldo L23 «Preguntas frecuentes». Sin cambiar el
sistema visual ni el catálogo de cuatro estados (D-26). Resultado: deck v4.1, 23 láminas.

Hora límite: **14:15**. Prioridad si no alcanza: 1) ALTOS + L23, 2) MEDIOS M-01…M-23,
3) MEDIOS de diseño (M-24…M-31), 4) BAJOS.

## Decisiones que registra
- D-30 · Las 20 visitas del lote de trabajo B cargadas por script [C17] se declaran en pantalla
  (L02) y en la demostración; «prueba negativa» pasa a «prueba de bloqueo» en láminas y guion;
  las flechas y resultados permitido/bloqueado se dibujan en color neutro con palabra, no en
  verde/rojo (D-26); versión mínima de PostgreSQL propuesta: 15 (req. 1 exige
  `security_invoker`); se agregan al anexo E: «cuenta de base de datos (por equipo)»,
  «identidad de campo (por persona)», «archivo de conexión (pg_service)», «zona de equipo»
  (definición), «número de polígono». Leyenda de L04 ampliada con «D-xx = decisión
  registrada del piloto; req. N = requerimiento propuesto en NEON-TI-01; PENDIENTE DE TI =
  espera un recurso o una revisión de TI; nada está aprobado».

## Entradas
`docs/presentacion/auditoria/informe_ronda3.md` (manda); deck v4; `guion_demostracion.md`;
`REQUERIMIENTOS_TI.md` v4; `CIFRAS.csv`; `DECISIONES.md` D-18 (sim 208 MB / 225 MB total).

## Pasos

### 1. Verificaciones previas — 10 min
a) Conteo real del guion §4: con lote A, UPM 20205003, UGM 16691, ¿cuántos de los 15
guardados desde QGIS caen ahí? Consultar la vista `v_tab_geo_poligonos` (solo lectura) y
escribir el número y la lista de ids (A-04). b) Qué requerimiento habla de red interna/VPN/TLS
(M-23); si ninguno, L17 cita «propuesta de migración» sin número. c) Sesión de la prueba
cruzada `UPDATE 1/0` (B-10): la que diga la evidencia. d) Confirmar en `REQUERIMIENTOS_TI.md`
que req. 1 pide `security_invoker` (A-10). Evidencia en `docs/evidencia/s08e/01_verificaciones.txt`.

### 2. ALTOS — 40 min
A-01 L02 y guion §1: línea «Incidencias = no localizada + rechazo + revisita; las dos primeras
cuentan también como concluidas; por eso 33 + 1.393 + 22 no suma 1.432».
A-02 L09 y guion §6: «El filtro “Encuestador” del tablero muestra hoy la cuenta que guardó;
el campo por persona queda vacío sin QFieldCloud (D-10)». No se toca el tablero.
A-03 L02 y guion §3: «Las 20 visitas del lote de trabajo B se cargaron por script para probar
el reparto; las 19 del lote de trabajo A son guardados reales desde QGIS (15) y desde el
celular (4) [C17]». L01: «2 personas, 1 celular» se mantiene.
A-04 guion §4: conteo del paso 1a y lista de ids; quitar «57 a 75».
A-05 L13 fila 4: «Cuenta de base de datos por equipo de campo → se mantiene por zona de equipo
(req. 16); identidad de campo por persona, añadida (req. 15)». L18 y L20 con los mismos
términos.
A-06 L13 fila nueva: «Dentro de una zona de equipo, el reparto entre censistas no lo impone la
base de datos: depende de la identidad por persona (decisión 2, paso a)». L23 pregunta 5.
A-07 L12 línea: «Hoy: cuentas personales de Neon y GitHub, solo con datos públicos; en
producción, cuentas institucionales administradas por TI (paso b)». Recortar o difuminar el
nombre de usuario en las capturas de L02 (URL del QR se mantiene) y L11. L23 pregunta 1.
A-08 L21 §7.5: agregar «y cómo accede un supervisor desde el celular (VPN institucional o
portal con inicio de sesión)». L23 pregunta 2.
A-09 L01 línea bajo la franja: «Se hizo fuera del INEC y con datos públicos porque el piloto
no contaba con acceso a infraestructura institucional; nada de esto se propone como entorno
de producción (D-01)».
A-10 L17 fila 1: «PostgreSQL 15 o superior con PostGIS (req. 1 exige una función de la
versión 15); versión por confirmar con TI». Documento §migración y req. 12 igual.

### 3. L23 · Preguntas frecuentes — 15 min
Lámina de respaldo después de L22, con ancla en el índice; no se proyecta salvo pregunta.
Pregunta en negrita, respuesta en una o dos líneas, referencia entre paréntesis:
1. ¿A nombre de quién queda GitHub? — En producción GitHub no es necesario: el script corre en
un servidor del INEC y la página queda en la intranet. Si TI quiere versionar el código en
GitHub, en una organización institucional administrada por TI, nunca en una cuenta personal
(req. 14).
2. ¿Cómo abren la página los encargados? ¿Se envía por WhatsApp? — Hoy cualquiera con el
enlace la abre; es aceptable solo porque los datos son públicos (D-09). En producción:
intranet del INEC con usuario institucional; desde el celular, por VPN institucional o portal
con inicio de sesión. El enlace puede circular; sin usuario no se entra (req. 19).
3. ¿Y si se agregan datos confidenciales? — La página ya excluye texto libre y posición GNSS
(D-14). Lo confidencial es dónde vive: web interna con inicio de sesión, o una herramienta de
tableros en servidores del INEC con permisos por zona. Una página privada en GitHub sigue
siendo una nube externa: no se recomienda con secreto estadístico (req. 19).
4. ¿Se puede montar en SQL Server? — Guarda geometrías, pero perdería el control por fila tal
como está probado, PostGIS y la integración con QFieldCloud. Propuesta: PostgreSQL con
PostGIS institucional (req. 12, 13).
5. ¿Puede haber equipos del 1 al 500? — Sí: misma columna de reparto y una política por equipo,
generadas por script. Falta definir la zona de equipo (UPM, UGM o región) y cuántos equipos
reales habrá; dentro de un equipo, el reparto entre personas es la decisión 2 (req. 16).
6. ¿Cómo se reparte el campo? ¿Cada persona necesita los dos archivos? — Solo en el piloto.
En producción cada equipo recibe desde QFieldCloud del INEC un proyecto con su zona; la clave
queda en el servidor (D-19, req. 9, 10).
7. ¿Por qué Neon y no los servidores del INEC desde el inicio? — El piloto no tenía acceso a
infraestructura de TI. Todo lo construido es PostgreSQL estándar y se migra restaurando un
respaldo de 403.490 bytes (D-01, L17).
Notas del orador de L11, L17 y L19 remiten a L23. Sin cifras nuevas salvo las ya en CIFRAS.csv.

### 4. MEDIOS — 60 min
Aplicar M-01…M-31 con la dirección del informe. Precisiones:
- M-11 L07: 1396 primero y destacado («caso completo: visita 16:29:35, guardado 16:30:01»);
  las otras tres ordenadas por hora de visita; nota al cuerpo en tamaño de cuerpo.
- M-13: «prueba de bloqueo» en L04, L10, L22 y guion; «Resultado: bloqueado, como se
  esperaba» en lugar de «SUPERADA» en pantalla (en bitácoras no se cambia).
- M-14: flechas y «UPDATE 0 / UPDATE 1» en gris oscuro o azul institucional, con rótulo
  «bloqueado» / «permitido».
- M-16: píldora gris «PENDIENTE DEL INEC» solo en L21 y L22, agregada a la leyenda de L04
  con «decisión de la Unidad o del censo, no de TI».
- M-17: kicker «PARTE 2 · PROPUESTA DE LA UNIDAD PARA REVISIÓN · …» en L13–L23; L13 columna
  «Propuesta para el censo».
- M-18: no se renombra el estado; la leyenda de L04 dice «nada está aprobado».
- M-27: código y nombres de archivo salen del cuerpo de L08, L09, L10, L11, L17, L22 (quedan
  en notas y pies); en el cuerpo, el concepto en palabras («el archivo de conexión», «la
  expresión que lee la precisión del GNSS»).
- M-28/M-29: L03 solo esquema + tabla de 6 filas más legibles (las otras 5 a notas); L09 una
  captura; tamaño base del cuerpo ≥ 18 px equivalente; redistribuir verticalmente.
- M-30: L06 y L09: rótulo «captura ilustrativa» en el cuerpo, o quitar la captura si no cabe.

### 5. BAJOS — 20 min
B-01…B-26 según quepan; B-22: la atribución «encargado del censo» se cambia por «según se
informó a la Unidad el 16/10». B-27 no es hallazgo.

### 6. Documento TI v4.1 — 15 min
Mismos cambios de vocabulario (anexo E), A-05, A-10, M-09, M-23; sección «Migración» con la
línea de cuentas institucionales; `exportar_pdf.py`; regenerar PDF. Rótulo «v4.1».

### 7. Verificaciones y entrega — 20 min
Verificadores de cifras y vocabulario en verde (deck, notas, documento, guion); grep de
credenciales y prohibidos = 0; `capturar_laminas.py` → 23 láminas, 0 errores; grep en el
deck de «SUPERADA», «prueba negativa», «tramo», «PostgreSQL 14» = 0 en texto visible.
`ENTREGA_2026-10-19/` regenerada. DECISIONES (D-30), bitácora
`docs/sesiones/2026-10-16_sesion-12.md`. Commit «docs(presentacion): correcciones de la
ronda 3 y lámina de preguntas frecuentes — deck v4.1». Push solo con confirmación.

## Puntos de detención
Solo lectura en la base de datos. Push con confirmación. 14:15: entregar lo verde.

## Criterios de aceptación
- 10 ALTOS resueltos; L23 presente; MEDIOS resueltos o listados como no aplicados con motivo.
- Verificadores en verde; 23 capturas; documento v4.1 y PDF.
- Resumen de 10 líneas con: hallazgos resueltos / parciales / no aplicados por código, y qué
  quedó fuera.

## Fuera de alcance
Tablero publicado; catálogo de estados (D-26); borrado de `sim`.