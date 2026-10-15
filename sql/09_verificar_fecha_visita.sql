-- =====================================================================================
--  09 — Verificación de D-16 con el rol edit_lote_a. TODO termina en ROLLBACK.
-- =====================================================================================
--  (a) UPDATE con fecha explícita de ayer  -> conserva esa fecha.
--  (b) UPDATE de estado sin fecha (fila con fecha NULL) -> recibe now().
--  Se toman dos fincas del lote A en 'pendiente' con fecha_visita NULL.
--  Ejecutar: psql (rol edit_lote_a) -X -v ON_ERROR_STOP=1 -f sql/09_verificar_fecha_visita.sql
-- =====================================================================================

SELECT current_user AS rol;

BEGIN;

CREATE TEMP TABLE _prueba ON COMMIT DROP AS
SELECT id, row_number() OVER (ORDER BY id) AS n
FROM mgn.finca_visita
WHERE lote = 'A' AND estado_visita = 'pendiente' AND fecha_visita IS NULL
ORDER BY id
LIMIT 2;

SELECT count(*) AS filas_de_prueba FROM _prueba;

-- (a) fecha explícita de ayer
UPDATE mgn.finca_visita f
   SET estado_visita = 'visitada',
       fecha_visita  = date_trunc('second', now()) - interval '1 day'
  FROM _prueba p
 WHERE f.id = p.id AND p.n = 1;

-- (b) cambio de estado sin fecha
UPDATE mgn.finca_visita f
   SET estado_visita = 'visitada'
  FROM _prueba p
 WHERE f.id = p.id AND p.n = 2;

SELECT p.n AS caso,
       f.estado_visita,
       f.fecha_visita = date_trunc('second', now()) - interval '1 day' AS a_conserva_ayer,
       f.fecha_visita = now()                                           AS b_recibe_now,
       f.editado_por
  FROM mgn.finca_visita f JOIN _prueba p USING (id)
 ORDER BY p.n;

ROLLBACK;

-- Residuos: ninguna de las fincas de prueba debe quedar modificada.
SELECT count(*) FILTER (WHERE estado_visita <> 'pendiente') AS lote_a_no_pendientes,
       count(*) FILTER (WHERE fecha_visita IS NOT NULL)     AS lote_a_con_fecha,
       count(*)                                             AS lote_a_total
  FROM mgn.finca_visita WHERE lote = 'A';
