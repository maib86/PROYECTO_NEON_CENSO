# SPEC S07 — Corrección de comunicación del deck y del documento TI (ronda 1)

Fecha: 2026-10-15 · Entrega: 2026-10-16 08:00 (re-auditoría externa en la mañana;
cierre 15:00). Modo: desatendido; solo el push espera confirmación.
Insumo obligatorio: docs/presentacion/auditoria/informe_ronda1.md (51 hallazgos:
A-01…A-09, M-01…M-23, B-01…B-19, más la tabla de huecos por audiencia). Leerlo completo
antes de tocar nada. Cada hallazgo se atiende o se rechaza con razón; ninguno se ignora.

## 0. Pendientes operativos (antes de corregir texto)
a) Regeneración automática: `gh api repos/{owner}/{repo}/actions/workflows/tablero.yml`
   (state), `gh run list --workflow tablero.yml --event schedule --limit 5`. Si sigue en 0:
   revisar que el cron esté en main, sintaxis, y si el repositorio tiene el workflow
   deshabilitado o en cola; anotar causa o «sin causa visible; GitHub puede retrasar o
   omitir schedules en repositorios nuevos» con la cita de la documentación de GitHub.
   Si ya hubo ejecuciones por schedule: registrar la primera (fecha, id) y actualizar
   deck, documento y CIFRAS.
b) Tablero publicado: confirmar que ya muestra la etiqueta corregida («de ellas N
   revisitas sin cerrar»); si no, `gh workflow run` y esperar. Rehacer la captura de L07
   con la etiqueta visible.
c) Prueba negativa desde el celular (A-09): construir
   campo/paquete_movil/NEON_campo_prueba_negativa.qgs igual al proyecto de campo pero SIN
   filtro de lote en finca_visita (solo para esta prueba; no se versiona; la guía lo
   explica). La persona intentará mañana editar un punto del lote B desde QField con
   edit_lote_a. Hasta entonces, el deck dice «la política la aplica la base de datos; la
   prueba negativa desde el celular está pendiente».

## 1. Vocabulario único (D-25). Se aplica a láminas, notas del orador, REQUERIMIENTOS_TI.md
y PDF. Agregar una tabla «Vocabulario» al documento (anexo) y una línea en CLAUDE.md.
| Concepto | Término único | Nunca |
|---|---|---|
| La base PostgreSQL/PostGIS | «base de datos» (siempre completo en títulos; «la base de datos» en cuerpo) | «la base» sola |
| Objetos del piloto | «polígonos de prueba» (1.432, distrito 20205) | finca, objeto, UGM para estos |
| Objetos de producción | «fincas» | — |
| Capa UGM | «polígonos UGM (proxy)» | fincas, objetos |
| Unidad de reparto del piloto | «lote de trabajo A/B» | lote, parte, zona, equipo |
| Unidad de reparto en producción | «zona de equipo (por definir: provincia o UPM)» | zona a secas |
| Rol dueño de la base | «cuenta administradora» | propietario, neondb_owner |
| Roles edit_lote_a/b | «cuenta del equipo A/B» (en tablas técnicas puede ir el nombre entre paréntesis) | rol, usuario |
| Operación de guardado | «guardados» / «guardados por segundo» | escrituras |
| Control por fila | «control por fila (RLS)» en 1.ª aparición; después «control por fila» | RLS solo |
| Regeneración del tablero | «regeneración automática» | cron, schedule, workflow, programa |
| Hardware | «computadora» | equipo |
| Personas | «equipo de campo» | equipo |
| Estado terminal de visita | «visita concluida» | cerrada |
| Fase terminada | «completada» | cerrada |
| Ventana de Neon | «solo se puede volver atrás 6 horas» | restauración de 6 h |
| Revisor | «revisión automática independiente (programa, sin acceso a la conversación)» | agente |
Siglas: expandir en la primera aparición en lámina (PostGIS, RLS, GNSS, UPM, UGM, SNIT,
MDM, QFieldCloud, GitHub Actions/Pages, p95, op/s). Fuera de lámina: TOAST, EXPLAIN,
\timing, ogr2ogr, p50, «Pared», «*/30 * * * *», «schedule», «hash», «endpoint». «D-01» en L02
con la expansión «decisión registrada n.º 1».

## 2. Catálogo de estados y color (D-26)
Cuatro estados, definidos en L04 con leyenda y reutilizados sin variantes:
PROBADO (verde) · MEDIDO (azul; con nota «extrapolado» en texto, no en la píldora) ·
NO PROBADO (rojo) · PENDIENTE DE TI (ámbar). Rojo solo para «no probado / riesgo»: el
total 1.432 de L05, los remates de L02 y L16, la caja «Tablero» de L03 y los kickers pasan
a azul/neutro. L12: las dos tarjetas con el mismo tratamiento.

## 3. Cifras y trazabilidad
- Identificadores: un solo id (el de finca) en L06, L08, pies, documento y CIFRAS.csv;
  cuando sea id de fila, rotularlo. Resolver A-05 con la tabla real.
- Separadores: en pantalla y en el PDF, coma decimal y punto de miles, sin excepción
  (23,1 ms; 145 ms; 1,5 s; 31,8 s; 208,5 MiB). Una sola unidad (MB o MiB) en todo el deck.
  El literal de consola se conserva solo en CIFRAS.csv.
- Cifras no verificables señaladas por el informe (46 filas; 7 px; tiempos de pared, p50 y
  máx de L11; columna «Origen» de L06; «10 visitada · 5 no_localizada»; «campos
  estructurales»; «requerimientos 1 a 11»; números por recurso de L16): agregar la fila a
  CIFRAS.csv con archivo y línea, o quitar la cifra. verificar_cifras.py en verde.
- Toda frase que resuma un grupo se prueba con un contraejemplo antes de publicar.

## 4. Láminas a rehacer (una afirmación por lámina)
- L04: título que separe probado de pendiente; una fila por fase (2a, 2b); leyenda de estados.
- L06: título «Quién guardó y cuándo: lo sella la base de datos»; columna Origen con
  fuente o fuera; sin «—» (llenar o explicar); horas a segundos sin microsegundos ni
  «-06»; cuenta administradora en vez de neondb_owner; mismo id que L08.
- L08: «las 4 visitas del celular entraron con la cuenta del equipo A; la política la
  aplica la base de datos»; «desfase de 6 h → 25 s entre visita y guardado» en palabras;
  «18 de 18 con la cuenta del equipo A» como titular; precisión «1,5–1,6 m».
- L10: coma decimal; «56 % del tamaño de producción»; separadores uniformes; línea
  «a 90.000 el plan gratuito no alcanza; producción requiere almacenamiento dimensionado
  (req. 12)».
Ajustes del resto según el informe (M-01…M-23, B-01…B-19), incluidos: L07 captura con
etiqueta corregida y nota de que el repositorio es personal y público por D-01/D-24;
L15/L16 alineados con §7 (5 decisiones) y §8 (recursos) del documento; L17 explica qué es
la revisión automática y qué acredita «verde»; L18 con una línea bajo el título: «Probado =
funcionó con datos públicos · No validado = aún no ensayado con recursos del INEC»;
«se propone» en L14 y en las notas de L05 y L07; L13 «resolverla» (no «levantarla»).

## 5. Documento TI y PDF
Aplicar el mismo vocabulario, identificadores y separadores. Anexo «Vocabulario».
Regenerar PDF. Verificar que deck y documento dicen lo mismo en: conteo de decisiones (§7),
conteo de requerimientos (§6), estado de la regeneración automática, ids de visitas.

## 6. Respuesta a la auditoría y cierre
- docs/presentacion/auditoria/respuesta_ronda1.md: tabla con cada hallazgo (A/M/B) →
  acción tomada (resuelto / parcial / rechazado con razón) y lámina.
- Capturas nuevas de las 18 láminas; sin desbordes; verificar_cifras.py en verde.
- Revisión automática independiente sobre el deck v2 con foco en: vocabulario único
  (grep de los términos prohibidos de la tabla = 0 en láminas y notas), estados del
  catálogo, separadores.
- D-25, D-26 en DECISIONES. Bitácora sesión 07. Commit (sin docs/presentacion/); pedir
  confirmación para el push. Resumen de 10 líneas + lista de hallazgos rechazados.

## Criterios de aceptación
- [ ] grep de términos prohibidos = 0 en laminas y notas; siglas expandidas en 1.ª aparición.
- [ ] Cuatro estados, leyenda en L04; rojo solo en no probado/riesgo.
- [ ] Un id por visita en deck, documento y CSV; coma decimal en pantalla; una unidad.
- [ ] L04, L06, L08, L10 rehechas; L07 con captura de la etiqueta corregida.
- [ ] respuesta_ronda1.md completa; verificador en verde; documento y PDF coherentes.

## Fuera de alcance
Cambios de contenido técnico del piloto; QFieldCloud; borrado de sim.