# SPEC S06 — Documento para TI y presentación de la unidad (Fase 4)

Fecha: 2026-10-15 · Entrega: 2026-10-16 15:00 · Presentación: lunes 2026-10-19
Audiencias: Unidad de Cartografía, encargados del censo y, en reunión aparte, TI.
Objetivo: dos entregables generados desde los archivos del repositorio, con cada cifra
trazable a su archivo de origen. Modo: desatendido salvo el push (ask).

## 0. Antes de empezar
- `.gitignore`: agregar `docs/presentacion/` ANTES de cualquier otra cosa. Verificar con
  `git status --ignored` que `docs/presentacion/referencia/` y `activos/` no aparecen como
  nuevos. D-24: la presentación, el logo y la muestra son material interno y no se
  versionan en el repositorio público; el documento para TI sí.
- Tablero publicado: `gh run list --workflow tablero.yml --limit 3`; descargar
  https://maib86.github.io/PROYECTO_NEON_CENSO/ y verificar que `observaciones` y
  `prueba qfield` dan 0, que aparecen las visitas de campo (lote A > 15) y que la hora de
  generación es posterior a las 16:30 de hoy. Anotar resultado literal. Si el cron no corrió
  todavía, `gh workflow run tablero.yml` y esperar.
- Leer completo: ESPECIFICACION.md, docs/DECISIONES.md (D-01 a D-23),
  docs/requerimientos_ti/insumos_piloto.md, docs/requerimientos_ti/evidencia_escala.md,
  todas las bitácoras en docs/sesiones/, docs/evidencia/. Nada se escribe de memoria.

## 1. Banco de cifras (primero, antes de redactar)
`docs/requerimientos_ti/CIFRAS.csv` con columnas: `id, valor, unidad, descripcion,
archivo_origen, linea_o_consulta, sesion`. Toda cifra que vaya a aparecer en el documento
o en la presentación nace aquí. `docs/requerimientos_ti/verificar_cifras.py`: para cada
fila comprueba que `valor` aparece en `archivo_origen`; sale con código 1 si alguna falla.
Si una cifra deseada no existe en ningún archivo, no se inventa: el texto dice
«sin medir» y queda en la lista de pendientes.

## 2. Documento para TI: `docs/requerimientos_ti/REQUERIMIENTOS_TI.md`
Voz institucional, neutra, sin nombres de personas. Secciones:
1. Resumen ejecutivo (media página): qué se probó, qué quedó demostrado, qué no, qué se pide.
2. Arquitectura probada: esquema de texto (QGIS/QField → PostGIS con RLS y auditoría →
   generador → tablero estático) y las decisiones que la sostienen (referencia D-xx).
3. Evidencia por fase: tabla con criterio, resultado literal, archivo de evidencia. Fases
   1 a 3 según ESPECIFICACION.md; Fase 3 dividida por D-22.
4. Escala: tabla de mediciones de evidencia_escala.md; distinguir «medido con 50.794» de
   «extrapolado a 90.000»; sección «qué vale y qué no vale del proxy UGM».
5. Limitaciones del piloto y su causa: tabla de 4 columnas — limitación · por qué existió
   (qué no teníamos) · qué hace falta para levantarla · evidencia. Mínimo: edición offline
   y @cloud_username (plan Community, D-22); reparto en campo por proyecto (D-10, D-19);
   hora desde escritorio = hora de guardado (D-16/D-20); escala 50.794 vs 90.000 (D-18);
   datos públicos, tablero público y nube gratuita con 6 h de restauración (D-01, D-09);
   dos personas y un celular; credenciales en el dispositivo sin MDM; una fila por finca
   (D-21); encabezado del tablero («30 cerradas · 15 visitadas · 20 incidencias»: las
   incidencias incluyen 5 revisitas no cerradas; corregir la etiqueta en esta sesión si es
   un cambio de una línea en generar_tablero.py, y anotarlo).
6. Requerimientos para producción: los de insumos_piloto.md numerados, cada uno con origen,
   más los que surjan de 5. Agrupar: base de datos · identidad y acceso · campo · tablero ·
   operación y respaldo.
7. Decisiones que debe tomar el INEC (no el piloto): modalidad de QFieldCloud (SaaS,
   organización o instancia propia) y plan con PostGIS offline; gestión de identidades de
   campo; historial completo de visitas; cuestionario real (reemplaza D-15); dónde corre el
   generador del tablero y dónde se publica.
8. Siguiente paso propuesto: (a) cuenta QFieldCloud de prueba del INEC → prueba offline
   (D-22 parte 2); (b) réplica del esquema en servidores del INEC con la guía de
   replicación; (c) prueba de campo con un equipo real. Con lo que cada paso necesita.
9. Anexos: lista D-01…D-24 (una línea cada una); glosario (RLS, trigger, pg_service,
   QFieldCloud, GitHub Actions, Pages); inventario del repositorio.
Exportar también a `docs/presentacion/REQUERIMIENTOS_TI.pdf` (md → HTML con el mismo
sistema visual de la muestra → PDF con playwright), para entregar en mano.

## 3. Presentación: `docs/presentacion/PRESENTACION_NEON_CENSO_2026-10-19.html`
- Autocontenida, sin red: copiar el `<style>`, la estructura `.slide/.shead/.sbody/.sfoot`,
  el HUD, la barra, las notas del orador (#notes) y la navegación por teclado de
  `docs/presentacion/referencia/PRESENTACION_IPG_UNIDAD_CARTOGRAFIA_2026-09-03.html`.
  Logo `activos/inec_logo.png` incrustado en base64 en `.shead`. Marca `NEON-PRES-01`.
  Encabezado de comentario igual al de la muestra: material interno, cada cifra en
  CIFRAS.csv, verificada por verificar_cifras.py.
- Pie de cada lámina (`.sfoot .src`): archivo(s) de origen de las cifras de esa lámina.
- Notas del orador en cada lámina: lo que se dice, en 3–5 frases, incluida la limitación
  que corresponde cuando la lámina muestra un resultado.
- Nada de nombres de personas; usuarios de rol (`edit_lote_a`) solo donde sean el dato.
- Láminas (ajustar a 16–20):
   1. Portada: título, «Unidad de Cartografía · 19 de octubre de 2026», marca interna.
   2. Qué se buscaba: una capa, varias personas, cada una su parte, con auditoría y avance
      visible; y por qué se hizo fuera de la infraestructura (D-01).
   3. Cómo funciona: esquema (SVG inline) QGIS/QField → PostGIS (RLS, trigger) → generador
      → tablero; quién ve qué.
   4. Qué se probó y qué no (mapa de fases con tags si/no/cond).
   5. Escritorio: 1.432 fincas, dos lotes, el reparto impuesto por la base (UPDATE 1/0,
      INSERT ajeno rechazado) — resultado literal.
   6. Auditoría: quién, cuándo, desde dónde; ejemplo real de filas (sin observaciones).
   7. Tablero: captura 1100 px, URL pública y QR (generar con `py -m pip install qrcode`
      → SVG incrustado); regeneración cada 30 min; sin credenciales.
   8. Campo: QField con conexión directa; 4 visitas; control por lote también en el
      celular; precisión GNSS; hora corregida (D-23).
   9. Lo que el campo NO probó todavía y por qué (plan Community; D-22): offline,
      @cloud_username, sincronización.
  10. Escala, medido: 50.794 UGM, carga, tamaños, vistas en ms.
  11. Escala, concurrencia: 1/10/25 conexiones, op/s, p95, 0 errores; la red pesa más
      que la base.
  12. Escala, hallazgos de diseño: mapa ilegible con 50.794 puntos → agregar por zona;
      paquete 208,5 MiB vs 6,2 MiB → paquete por equipo.
  13. Limitaciones del piloto y su causa (la tabla de 4 columnas, versión corta).
  14. Qué cambia para producción: requerimientos agrupados (una lámina, 5 bloques).
  15. Qué necesita el piloto de la unidad y del censo: cuestionario real, equipo de prueba,
      criterio de reparto (provincia/UPM), decisión sobre historial.
  16. Qué necesita de TI: cuenta QFieldCloud de prueba, servidor PostGIS, cron y web
      interna, gestión de identidades.
  17. Cómo se verificó: repositorio, bitácoras, revisor independiente, CIFRAS.csv.
  18. Cierre: «Probado. No validado.» y los tres siguientes pasos.
- Verificación: `docs/presentacion/capturar_laminas.py` (playwright, 1340×780) genera una
  PNG por lámina en `docs/presentacion/laminas/` y falla si en alguna `.sbody` el
  scrollHeight supera el clientHeight (texto desbordado) o hay errores JS.
  `verificar_cifras.py` debe pasar. revisor-auditoria revisa las PNG y el documento:
  cifras contra CIFRAS.csv, ninguna afirmación sin archivo, limitaciones completas,
  ausencia de nombres de personas y de credenciales.

## 4. Cierre
- D-24 en DECISIONES. ESPECIFICACION: Fase 4 «en curso: entregables v1 generados; revisión
  de la persona pendiente». Bitácora sesión 06 con el resultado del paso 0 y las rutas.
- Commit (sin docs/presentacion/). Pedir confirmación para el push.
- Resumen de 10 líneas + lista de cifras marcadas «sin medir».

## Criterios de aceptación
- [ ] docs/presentacion/ ignorado; referencia y logo fuera de git.
- [ ] CIFRAS.csv completo y verificar_cifras.py en verde.
- [ ] REQUERIMIENTOS_TI.md con las 9 secciones y PDF generado.
- [ ] Presentación de 16–20 láminas, sin desbordes, con notas, QR y pies de origen.
- [ ] Revisor sin bloqueantes; tablero publicado verificado tras regeneración.

## Fuera de alcance
QFieldCloud (D-22 parte 2), borrado de `sim` (se decide después del lunes), cambios de
diseño del tablero más allá de la etiqueta del encabezado.