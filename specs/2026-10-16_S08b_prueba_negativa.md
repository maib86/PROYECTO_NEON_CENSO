# S08b — Verificar en la base de datos la prueba negativa desde el celular

## Objetivo
Determinar con evidencia de la base de datos si la edición hecha desde QField
(cuenta del equipo A, proyecto de prueba negativa) sobre el polígono 258 del lote
de trabajo B fue bloqueada por el control por fila. Documentar el resultado.
No tocar presentación, PDF ni REQUERIMIENTOS_TI (van en S08c, al final).

## Contexto dado por la persona
- Polígono de prueba (finca_id) 258, lote de trabajo B.
- Editado y guardado desde QField el 16/10/2026 con el proyecto de prueba
  negativa (service neon_lote_a). QField no mostró error.
- QField no mostró error. Comportamiento esperado: UPDATE silencioso con 0 filas
  (igual que en escritorio, sesión 02, C13).

## Decisiones que registra
Ninguna nueva. Si el resultado es «bloqueada», es evidencia de D-03/D-22 parte 1.

## Pasos
1. Con la cuenta administradora (DATABASE_URL), consultar la fila:
   SELECT id, finca_id, lote, estado_visita, encuestador, fecha_visita,
          precision_gnss_m, editado_por, fecha_edicion, fecha_creacion
   FROM mgn.finca_visita WHERE finca_id = 258;
   Guardar salida literal en docs/evidencia/s08b/01_fila_258.txt, con la hora de
   la consulta en America/Costa_Rica.
2. Criterio:
   - fecha_edicion anterior al 16/10/2026 y editado_por ≠ edit_lote_a para una
     fila del lote B → la edición no entró: PRUEBA SUPERADA.
   - fecha_edicion del 16/10/2026 con editado_por = edit_lote_a, o el campo
     <<CAMPO>> con el valor que puso la persona → el control por fila NO bloqueó:
     PUNTO DE DETENCIÓN. Reportar y no seguir.
3. Confirmación global: SELECT count(*) FROM mgn.finca_visita
   WHERE lote = 'B' AND editado_por = 'edit_lote_a';  → debe ser 0.
   Y: SELECT count(*) FROM mgn.finca_visita WHERE fecha_edicion::date = '2026-10-16';
   Guardar en docs/evidencia/s08b/02_conteos.txt.
4. Reproducción controlada con la cuenta del equipo A, en su propia conexión
   (service neon_lote_a, nunca SET ROLE, D-13), dentro de una transacción:
   BEGIN; UPDATE mgn.finca_visita SET estado_visita = estado_visita
   WHERE finca_id = 258; ROLLBACK;
   Resultado esperado: UPDATE 0. Guardar en docs/evidencia/s08b/03_update_0.txt.
   Repetir la misma consulta con finca_id de un polígono del lote A (p. ej. 1396)
   para contraste: UPDATE 1, también con ROLLBACK.
5. Documentar:
   - ESPECIFICACION.md, Fase 3: nuevo subcriterio marcado [x] «Prueba negativa
     desde el celular: edición del polígono 258 (lote B) con la cuenta del equipo A,
     bloqueada por la base de datos (UPDATE 0, fila intacta). Evidencia s08b.»
   - docs/sesiones/2026-10-16_sesion-09.md con la plantilla.
   - Commit: «test(campo): verificar prueba negativa desde el celular — polígono 258
     del lote B bloqueado por control por fila».
6. Comprobar que el commit no contiene credenciales (grep de neon.tech, npg_,
   postgresql://).

## Puntos de detención
- Paso 2, resultado «NO bloqueó»: detenerse, reportar, no modificar datos.
- Ningún UPDATE fuera de transacción con ROLLBACK. Ningún DELETE/DROP.

## Criterios de aceptación
- Tres archivos de evidencia con salida literal y hora de Costa Rica.
- Fila 258 intacta; conteo lote B con edit_lote_a = 0; UPDATE 0 reproducido
  y UPDATE 1 de contraste.
- ESPECIFICACION.md actualizada; bitácora escrita; commit sin credenciales.
- Resumen de 10 líneas para Claude web, incluyendo el veredicto en una palabra:
  SUPERADA o FALLÓ.

## Fuera de alcance
Deck, PDF, REQUERIMIENTOS_TI, CIFRAS.csv, capturas: S08c, al final. Push: solo
si la persona lo pide.