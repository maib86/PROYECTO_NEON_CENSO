# Insumos del piloto para los requerimientos de TI

Hallazgos del piloto que no se aplican en él pero deben quedar en el documento de
requerimientos para producción (Fase 4). Cada uno indica su origen.

| # | Requerimiento | Origen |
|---|---|---|
| 1 | Vistas del tablero con `security_invoker = true` y políticas propias para el rol del tablero cuando la lectura deba restringirse (por zona o confidencialidad). En el piloto las vistas corren como su dueño y omiten RLS, lo que es aceptable solo con lectura total. | Revisión sesión 02; D-14 |
| 2 | Coherencia `lote` ↔ `finca_id` en la capa de visita (FK compuesta `(finca_id, lote)` o trigger que copie el lote del polígono) antes de retirar `UNIQUE(finca_id)` para revisitas; de lo contrario un rol podría registrar visitas de fincas ajenas con su propio lote. | Revisión sesión 02; D-07, D-14 |
| 3 | Claves de roles de base fijadas con `\password` (hash SCRAM calculado en el cliente), no en texto dentro de sentencias SQL que pueden quedar en registros. | D-13 |
| 4 | Ninguna vista que alimente un tablero publicado expone texto libre ni posición GNSS de las personas. | D-14 |
| 5 | `encuestador` restringido a nombres de usuario válidos (CHECK, dominio o FK contra la lista de cuentas de campo). En el piloto es texto libre que los roles de edición pueden modificar: "persona solo como nombre de usuario" es convención, no restricción de la base. | Revisión 2 de sesión 02; D-14 |
| 6 | Tablero de producción agregado por zona (distrito o grilla, con carga por zona o renderizador en canvas o teselas), no un marcador por finca; paleta y vista por persona que no supongan dos lotes (p. ej., top N o agregado por supervisor). Con 50.794 marcadores el HTML pesó 3,98 MiB y el mapa fue ilegible a 400 px. | S04, hallazgos 1 y 2 de `evidencia_escala.md` |
| 7 | Paquete de campo restringido a la zona del equipo: solo los puntos de visita de esa zona y los polígonos de contexto recortados a ella (o como teselas). Con todos los polígonos el paquete pesó 208,5 MiB; solo con puntos, 6,2 MiB. | S04, hallazgo 6 de `evidencia_escala.md`; D-19 (un proyecto por equipo) |
