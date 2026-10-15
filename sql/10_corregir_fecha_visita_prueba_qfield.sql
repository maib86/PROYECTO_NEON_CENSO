-- =====================================================================================
--  10 — Corrige fecha_visita de las 3 visitas de prueba de QField (D-23)
-- =====================================================================================
--  Las visitas 1396, 1403 y 1404 (lote A, sesión 05, conexión directa) se guardaron
--  antes de D-23: el formulario envió now() del dispositivo sin zona y la sesión era
--  UTC, así que la hora local de Costa Rica quedó registrada como UTC (6 h atrasada).
--  Corrección: fecha_visita + 6 horas, solo en esas 3 filas.
--
--  Ejecutar con el rol edit_lote_a (no con el propietario): fn_sello_auditoria pone
--  editado_por = current_user, y así se conserva edit_lote_a. fecha_edicion pasa a ser
--  la hora de esta corrección.
--  EJECUTADO UNA VEZ (sesión 05). NO re-ejecutar: sumaría otras 6 horas.
--  Salvaguarda: si el UPDATE no afecta exactamente 3 filas, la transacción se aborta.
--    psql "service=neon_lote_a" -X -v ON_ERROR_STOP=1 -f sql/10_corregir_fecha_visita_prueba_qfield.sql
-- =====================================================================================

BEGIN;

SELECT 'ANTES' AS momento, id, estado_visita, fecha_visita, fecha_edicion, editado_por,
       fecha_edicion - fecha_visita AS edicion_menos_visita
  FROM mgn.finca_visita WHERE id IN (1396, 1403, 1404) ORDER BY id;

DO $$
DECLARE n integer;
BEGIN
    UPDATE mgn.finca_visita
       SET fecha_visita = fecha_visita + interval '6 hours'
     WHERE id IN (1396, 1403, 1404) AND lote = 'A';
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n <> 3 THEN
        RAISE EXCEPTION 'Se esperaban 3 filas y se afectaron %: se aborta', n;
    END IF;
    RAISE NOTICE 'filas corregidas: %', n;
END $$;

SELECT 'DESPUÉS' AS momento, id, estado_visita, fecha_visita, fecha_edicion, editado_por
  FROM mgn.finca_visita WHERE id IN (1396, 1403, 1404) ORDER BY id;

COMMIT;
