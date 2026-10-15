-- =====================================================================================
--  07 — AJUSTES A LAS VISTAS DEL TABLERO (D-14, D-15)
-- =====================================================================================
--  Aplica sobre lo creado por 06_centroides_visita.sql:
--    · D-15: avance_pct cuenta solo estados terminales (visitada, no_localizada,
--      rechazo). 'revisita' es incidencia, no avance.
--    · D-14: v_tab_movimientos deja de exponer `observaciones` (texto libre).
--      Ninguna vista v_tab_* expone `posicion_registro`.
--    · D-14: `cuando` incluye el año (DD/MM/AAAA HH24:MI).
--    · `persona` se mantiene = coalesce(encuestador, editado_por): solo nombres de
--      usuario (@cloud_username en campo, rol de base en escritorio).
--
--  v_tab_resumen y v_tab_puntos se reemplazan con CREATE OR REPLACE (mismas
--  columnas y tipos). v_tab_movimientos pierde una columna, y PostgreSQL no permite
--  quitar columnas con CREATE OR REPLACE VIEW: se borra y se vuelve a crear, y por
--  eso hay que volver a dar el GRANT a tablero_lectura (el DROP lo elimina).
--
--  EJECUCIÓN: como neondb_owner, en UNA transacción:
--      psql "$DATABASE_URL" -X -w -1 -v ON_ERROR_STOP=1 -f sql/07_ajustes_vistas_tablero.sql
--  Ninguna tabla cambia; solo vistas. Requiere confirmación explícita por el DROP VIEW.
-- =====================================================================================


-- 1. Resumen por lote: avance solo con estados terminales (D-15)
CREATE OR REPLACE VIEW mgn.v_tab_resumen AS
SELECT
    lote,
    count(*)                                                 AS fincas,
    count(*) FILTER (WHERE estado_visita = 'visitada')       AS visitadas,
    count(*) FILTER (WHERE estado_visita = 'no_localizada')  AS no_localizadas,
    count(*) FILTER (WHERE estado_visita = 'rechazo')        AS rechazos,
    count(*) FILTER (WHERE estado_visita = 'revisita')       AS revisitas,
    count(*) FILTER (WHERE estado_visita = 'pendiente')      AS pendientes,
    round(100.0 * count(*) FILTER (WHERE estado_visita IN
                                   ('visitada','no_localizada','rechazo'))
          / NULLIF(count(*),0), 1)                           AS avance_pct,
    max(fecha_visita)                                        AS ultima_visita
FROM mgn.finca_visita
GROUP BY lote
ORDER BY lote;


-- 2. Puntos para el mapa: `cuando` con año (D-14)
CREATE OR REPLACE VIEW mgn.v_tab_puntos AS
SELECT
    v.id,
    v.finca_id,
    v.lote,
    v.codigo_upm,
    v.estado_visita,
    coalesce(v.encuestador, CASE WHEN v.estado_visita <> 'pendiente'
                                 THEN v.editado_por END)     AS persona,
    to_char(v.fecha_visita AT TIME ZONE 'America/Costa_Rica',
            'DD/MM/YYYY HH24:MI')                            AS cuando,
    ST_Y(ST_Transform(v.geom, 4326))                         AS lat,
    ST_X(ST_Transform(v.geom, 4326))                         AS lon
FROM mgn.finca_visita v;


-- 3. Últimos movimientos: sin observaciones, `cuando` con año (D-14);
--    LIMIT 25 provisional (D-15)
DROP VIEW mgn.v_tab_movimientos;

CREATE VIEW mgn.v_tab_movimientos AS
SELECT
    v.finca_id,
    v.lote,
    v.codigo_upm,
    v.estado_visita,
    coalesce(v.encuestador, v.editado_por)                   AS persona,
    to_char(v.fecha_edicion AT TIME ZONE 'America/Costa_Rica',
            'DD/MM/YYYY HH24:MI')                            AS cuando
FROM mgn.finca_visita v
WHERE v.estado_visita <> 'pendiente'
ORDER BY v.fecha_edicion DESC
LIMIT 25;

GRANT SELECT ON mgn.v_tab_movimientos TO tablero_lectura;


-- =====================================================================================
--  VERIFICACIÓN (después de confirmar la transacción)
-- =====================================================================================
--  a) Columnas de v_tab_movimientos: no debe aparecer `observaciones`.
--     SELECT column_name FROM information_schema.columns
--      WHERE table_schema='mgn' AND table_name='v_tab_movimientos' ORDER BY ordinal_position;
--  b) Ninguna vista v_tab_* expone observaciones ni posicion_registro → 0 filas:
--     SELECT table_name, column_name FROM information_schema.columns
--      WHERE table_schema='mgn' AND table_name LIKE 'v_tab_%'
--        AND column_name IN ('observaciones','posicion_registro');
--  c) Resumen sin cambios en el estado actual (todo pendiente): A 709 / B 723, 0.0.
--     SELECT * FROM mgn.v_tab_resumen;
--  d) Con la conexión propia de DATABASE_URL_TABLERO (psql "$DATABASE_URL_TABLERO"):
--     SELECT current_user;                               → tablero_lectura
--     SELECT count(*) FROM mgn.v_tab_resumen;            → 2
--     SELECT count(*) FROM mgn.v_tab_encuestador;        → 0
--     SELECT count(*) FROM mgn.v_tab_diario;             → 0
--     SELECT count(*) FROM mgn.v_tab_puntos;             → 1432
--     SELECT count(*) FROM mgn.v_tab_movimientos;        → 0 (legible tras el GRANT)
--     SELECT count(*) FROM mgn.finca_visita;             → permission denied
--  e) Fórmula de avance, como neondb_owner, en UNA sesión que termina en ROLLBACK
--     (los roles de edición no tienen SELECT sobre las vistas). Nada queda escrito:
--     BEGIN;
--     SELECT avance_pct FROM mgn.v_tab_resumen WHERE lote='A';          -- 0.0
--     UPDATE mgn.finca_visita SET estado_visita='revisita'
--      WHERE id=(SELECT min(id) FROM mgn.finca_visita WHERE lote='A');   -- UPDATE 1
--     SELECT avance_pct, revisitas FROM mgn.v_tab_resumen WHERE lote='A'; -- 0.0 | 1
--     UPDATE mgn.finca_visita SET estado_visita='visitada'
--      WHERE id=(SELECT min(id) FROM mgn.finca_visita WHERE lote='A');   -- UPDATE 1
--     SELECT avance_pct, visitadas FROM mgn.v_tab_resumen WHERE lote='A'; -- 0.1 | 1
--     ROLLBACK;
--     Después: SELECT count(*) FROM mgn.finca_visita WHERE estado_visita<>'pendiente'; → 0
-- =====================================================================================
