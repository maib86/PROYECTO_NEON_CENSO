-- =====================================================================================
--  sim.v_tab_* — equivalentes a mgn.v_tab_* (sql/06 + sql/07: D-14, D-15)
--  Ejecutar como neondb_owner: py sim/psql.py -f sim/sql_vistas_tablero.sql -- -1
-- =====================================================================================

CREATE VIEW sim.v_tab_resumen AS
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
FROM sim.finca_visita
GROUP BY lote
ORDER BY lote;

CREATE VIEW sim.v_tab_encuestador AS
SELECT
    coalesce(encuestador, editado_por)                       AS persona,
    lote,
    count(*)                                                 AS visitas,
    count(*) FILTER (WHERE estado_visita = 'visitada')       AS visitadas,
    count(*) FILTER (WHERE estado_visita IN ('no_localizada','rechazo','revisita'))
                                                             AS incidencias,
    min(fecha_visita)                                        AS primera,
    max(fecha_visita)                                        AS ultima
FROM sim.finca_visita
WHERE estado_visita <> 'pendiente'
GROUP BY 1, 2
ORDER BY visitas DESC;

CREATE VIEW sim.v_tab_diario AS
SELECT
    (fecha_visita AT TIME ZONE 'America/Costa_Rica')::date   AS dia,
    lote,
    count(*)                                                 AS visitas
FROM sim.finca_visita
WHERE estado_visita <> 'pendiente' AND fecha_visita IS NOT NULL
GROUP BY 1, 2
ORDER BY dia, lote;

CREATE VIEW sim.v_tab_puntos AS
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
FROM sim.finca_visita v;

CREATE VIEW sim.v_tab_movimientos AS
SELECT
    v.finca_id,
    v.lote,
    v.codigo_upm,
    v.estado_visita,
    coalesce(v.encuestador, v.editado_por)                   AS persona,
    to_char(v.fecha_edicion AT TIME ZONE 'America/Costa_Rica',
            'DD/MM/YYYY HH24:MI')                            AS cuando
FROM sim.finca_visita v
WHERE v.estado_visita <> 'pendiente'
ORDER BY v.fecha_edicion DESC
LIMIT 25;

-- Mismo modelo que mgn: tablero_lectura solo ve las vistas, no las tablas.
GRANT USAGE ON SCHEMA sim TO tablero_lectura;
GRANT SELECT ON sim.v_tab_resumen, sim.v_tab_encuestador, sim.v_tab_diario,
                sim.v_tab_puntos, sim.v_tab_movimientos
    TO tablero_lectura;
