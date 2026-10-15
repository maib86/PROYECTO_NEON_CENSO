-- =====================================================================================
--  08 — VISITAS DE PRUEBA DEL LOTE B (SIMULADAS POR SCRIPT)
-- =====================================================================================
--  Registra 20 visitas de prueba en fincas del lote B para el criterio 4 de la Fase 2
--  ("visitas de prueba registradas por A y por B"). Para B la evidencia es simulada
--  por script; las de A se registran desde QGIS por la persona.
--
--  SE EJECUTA CON EL ROL DE EDICIÓN, NUNCA COMO PROPIETARIO:
--      psql "$DATABASE_URL_LOTE_B" -X -w -1 -v ON_ERROR_STOP=1 -f sql/08_visitas_prueba_lote_b.sql
--  Así pasa por RLS (pol_escritura_lote_b) y por los triggers igual que una edición
--  real: editado_por = edit_lote_b (fn_sello_auditoria) y fecha_visita = now()
--  (fn_fecha_visita_auto). Los cambios PERSISTEN. Para reponer el estado inicial:
--  sql/08_revertir_visitas_prueba_lote_b.sql.
--
--  SELECCIÓN REPRODUCIBLE: fincas del lote B ordenadas por id, una cada 36
--  (posiciones 1, 37, 73, …, 685): 20 fincas. k = 0..19 es el orden dentro de la
--  muestra.
--    · estado por k % 4: 0 visitada, 1 no_localizada, 2 rechazo, 3 revisita (5 de cada uno)
--    · observaciones cuando k % 3 = 0 (7 filas): texto de prueba que NO debe llegar
--      al tablero (D-14).
-- =====================================================================================


-- 1. Salvaguarda: solo con el rol de edición del lote B
DO $$
BEGIN
    IF current_user <> 'edit_lote_b' THEN
        RAISE EXCEPTION 'Este script se ejecuta como edit_lote_b, no como %', current_user;
    END IF;
END;
$$;


-- 2. Registrar las 20 visitas
WITH ordenadas AS (
    SELECT id, row_number() OVER (ORDER BY id) AS rn
    FROM mgn.finca_visita
    WHERE lote = 'B'
),
muestra AS (
    SELECT id, (rn - 1) / 36 AS k
    FROM ordenadas
    WHERE (rn - 1) % 36 = 0 AND rn <= 36 * 20
)
UPDATE mgn.finca_visita v
SET estado_visita = CASE m.k % 4
                        WHEN 0 THEN 'visitada'
                        WHEN 1 THEN 'no_localizada'
                        WHEN 2 THEN 'rechazo'
                        ELSE        'revisita'
                    END,
    encuestador   = 'edit_lote_b',
    observaciones = CASE WHEN m.k % 3 = 0
                         THEN 'PRUEBA 08: texto que no debe aparecer en el tablero'
                    END
FROM muestra m
WHERE v.id = m.id;


-- 3. Salvaguarda: exactamente 20 filas registradas por edit_lote_b; si no, la
--    transacción (-1) se revierte entera.
DO $$
DECLARE n integer;
BEGIN
    SELECT count(*) INTO n
    FROM mgn.finca_visita
    WHERE lote = 'B' AND encuestador = 'edit_lote_b' AND estado_visita <> 'pendiente';
    IF n <> 20 THEN
        RAISE EXCEPTION 'Se esperaban 20 visitas de prueba en el lote B y hay %', n;
    END IF;
END;
$$;


-- =====================================================================================
--  VERIFICACIÓN (después de confirmar)
-- =====================================================================================
--  Con $DATABASE_URL_TABLERO:
--    SELECT * FROM mgn.v_tab_resumen;
--      → A: 0 visitas, avance 0.0. B: 5/5/5/5, avance 2.1 (15 terminales / 723).
--    SELECT * FROM mgn.v_tab_encuestador;      → edit_lote_b | B | 20 | 5 | 15
--    SELECT * FROM mgn.v_tab_movimientos;      → 20 filas, sin columna observaciones
--  Con $DATABASE_URL (propietario):
--    SELECT editado_por, count(*) FROM mgn.finca_visita
--     WHERE lote='B' AND encuestador='edit_lote_b' GROUP BY 1;   → edit_lote_b | 20
--    SELECT count(*) FROM mgn.finca_visita
--     WHERE lote='A' AND (estado_visita<>'pendiente' OR encuestador IS NOT NULL
--           OR observaciones IS NOT NULL OR editado_por<>'neondb_owner');   → 0
-- =====================================================================================
