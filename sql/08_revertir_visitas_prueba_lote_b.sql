-- =====================================================================================
--  08 (REVERSIÓN) — DEVOLVER A PENDIENTE LAS 20 VISITAS DE PRUEBA DEL LOTE B
-- =====================================================================================
--  Repone el estado de formulario de las mismas 20 fincas que marca
--  08_visitas_prueba_lote_b.sql (misma selección: lote B por id, una cada 36).
--
--  SE EJECUTA CON EL ROL DE EDICIÓN, NUNCA COMO PROPIETARIO:
--      psql "$DATABASE_URL_LOTE_B" -X -w -1 -v ON_ERROR_STOP=1 -f sql/08_revertir_visitas_prueba_lote_b.sql
--
--  LÍMITE: devuelve estado_visita, encuestador, fecha_visita y observaciones a su
--  valor inicial, pero NO la auditoría: editado_por queda en edit_lote_b y
--  fecha_edicion en el momento de la reversión (fn_sello_auditoria las pone en todo
--  UPDATE). Reponerlas exigiría actuar como propietario y saltarse el trigger.
--
--  NO SE EJECUTÓ en la sesión 02. Queda para reponer el estado inicial.
-- =====================================================================================


DO $$
BEGIN
    IF current_user <> 'edit_lote_b' THEN
        RAISE EXCEPTION 'Este script se ejecuta como edit_lote_b, no como %', current_user;
    END IF;
END;
$$;


WITH ordenadas AS (
    SELECT id, row_number() OVER (ORDER BY id) AS rn
    FROM mgn.finca_visita
    WHERE lote = 'B'
),
muestra AS (
    SELECT id
    FROM ordenadas
    WHERE (rn - 1) % 36 = 0 AND rn <= 36 * 20
)
UPDATE mgn.finca_visita v
SET estado_visita = 'pendiente',
    encuestador   = NULL,
    fecha_visita  = NULL,
    observaciones = NULL
FROM muestra m
WHERE v.id = m.id;


-- Salvaguarda: las 20 de la muestra quedaron pendientes; si no, se revierte todo.
DO $$
DECLARE n integer;
BEGIN
    WITH ordenadas AS (
        SELECT id, row_number() OVER (ORDER BY id) AS rn
        FROM mgn.finca_visita WHERE lote = 'B'
    )
    SELECT count(*) INTO n
    FROM mgn.finca_visita v
    JOIN ordenadas o ON o.id = v.id
    WHERE (o.rn - 1) % 36 = 0 AND o.rn <= 36 * 20
      AND v.estado_visita = 'pendiente' AND v.encuestador IS NULL
      AND v.fecha_visita IS NULL AND v.observaciones IS NULL;
    IF n <> 20 THEN
        RAISE EXCEPTION 'Se esperaban 20 fincas repuestas a pendiente y hay %', n;
    END IF;
END;
$$;


-- VERIFICACIÓN: con $DATABASE_URL_TABLERO, SELECT * FROM mgn.v_tab_resumen;
--   → si no hay otras visitas en B: 723 pendientes, avance 0.0.
