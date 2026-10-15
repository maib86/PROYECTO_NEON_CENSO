-- =====================================================================================
--  09 — fecha_visita: el trigger la asigna solo si llega NULL (D-16)
-- =====================================================================================
--  Encargo: specs/2026-10-15_S05_qfield_preparacion.md, paso 2.
--
--  Antes de aplicar se comprobó la definición viva de mgn.fn_fecha_visita_auto
--  (pg_get_functiondef, sesión 05): ya asignaba now() solo con
--  NEW.fecha_visita IS NULL (y estado distinto de 'pendiente'), igual que en sql/06.
--  Las 15 visitas de la sesión 02 con la misma hora no vinieron de una sobrescritura:
--  QGIS escritorio envía fecha_visita NULL y now() es la hora de la transacción de
--  guardado. Por eso este script NO cambia el comportamiento: lo reafirma de forma
--  idempotente y deja la regla documentada en la base (COMMENT ON FUNCTION).
--
--  Efecto en campo: QField envía fecha_visita = now() del dispositivo (valor por
--  defecto del formulario) y el trigger la conserva. Desde QGIS escritorio, si llega
--  NULL, queda la hora de guardado (así se declara en D-16).
--
--  Ejecutar como neondb_owner, en una sola transacción, con pg_dump previo (D-13):
--    pg_dump -Fc -n mgn -f respaldos/2026-10-15_mgn_antes_09.dump
--    psql -X -v ON_ERROR_STOP=1 -1 -f sql/09_fecha_visita_solo_si_nula.sql
--  Verificación (rol edit_lote_a, con ROLLBACK): sql/09_verificar_fecha_visita.sql
-- =====================================================================================

CREATE OR REPLACE FUNCTION mgn.fn_fecha_visita_auto()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- Solo si llega NULL: nunca se sobrescribe una fecha enviada por el cliente.
    IF NEW.estado_visita <> 'pendiente' AND NEW.fecha_visita IS NULL THEN
        NEW.fecha_visita := now();
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION mgn.fn_fecha_visita_auto() IS
    'D-16: asigna fecha_visita = now() solo si llega NULL y el estado no es pendiente. '
    'La fecha enviada por el cliente (QField: now() del dispositivo) se conserva.';
