-- =====================================================================================
--  11 · Vistas geográficas del tablero v2 (spec S08c, D-28)
-- =====================================================================================
--  mgn.v_tab_geo_poligonos: un registro por polígono de prueba, con su visita, su UPM,
--    su UGM (cruce espacial con la capa SNIT en sim.ugm) y la geometría simplificada
--    (ST_SimplifyPreserveTopology 2 m en EPSG:5367, luego 4326 con 6 decimales).
--  mgn.v_tab_geo_ugm: solo contorno y código de las UGM que contienen polígonos de
--    prueba (excepción acotada a D-18: ningún atributo de visita ni avance de sim).
--
--  mgn.deteccion_cambio no tiene columnas de provincia, cantón ni distrito: van como
--  literales del piloto (distrito 20205), declarados con COMMENT ON VIEW.
--  Código de UGM: sim.ugm.id_mgn (identificador del MGN en la capa del SNIT; la capa
--  no trae otra columna de código).
--
--  Columnas vedadas: observaciones y posicion_registro NO se exponen.
--  tablero_lectura solo recibe SELECT sobre las vistas (no sobre sim.ugm).
--
--  Ejecutar (cuenta administradora, una transacción):
--    py sim/psql.py -f sql/11_vistas_geo_tablero.sql -- -1
-- =====================================================================================

CREATE OR REPLACE VIEW mgn.v_tab_geo_poligonos AS
SELECT d.id                                   AS id,
       '2'::text                              AS cod_provincia,
       'Alajuela'::text                       AS provincia,
       '202'::text                            AS cod_canton,
       'San Ramón'::text                      AS canton,
       '20205'::text                          AS cod_distrito,
       'Piedades Sur'::text                   AS distrito,
       d.codigo_upm                           AS upm,
       u.id_mgn::text                         AS ugm,
       d.lote,
       d.priority_cat                         AS prioridad,
       round(ST_Area(d.geom))::int            AS area_m2,
       v.estado_visita,
       v.encuestador,
       v.fecha_visita,
       v.precision_gnss_m,
       v.editado_por,
       v.fecha_edicion,
       ST_X(ST_Transform(v.geom, 4326))       AS lon,
       ST_Y(ST_Transform(v.geom, 4326))       AS lat,
       ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(d.geom, 2), 4326), 6)::json AS geom
FROM mgn.deteccion_cambio d
JOIN mgn.finca_visita v ON v.finca_id = d.id
LEFT JOIN sim.ugm u ON ST_Contains(u.geom, ST_PointOnSurface(d.geom));

COMMENT ON VIEW mgn.v_tab_geo_poligonos IS
    'Tablero v2 (S08c, D-28). Provincia 2 Alajuela, cantón 202 San Ramón y distrito 20205 '
    'Piedades Sur son literales del piloto: mgn.deteccion_cambio no tiene esas columnas. '
    'UGM = sim.ugm.id_mgn por cruce espacial (punto interior del polígono). '
    'Sin observaciones ni posicion_registro.';

CREATE OR REPLACE VIEW mgn.v_tab_geo_ugm AS
SELECT u.id_mgn::text AS ugm,
       ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(u.geom, 2), 4326), 6)::json AS geom
FROM sim.ugm u
-- IN con el cruce desde los polígonos usa el índice GiST de sim.ugm: 0,3 s.
-- La forma con EXISTS recorría las 50.794 UGM (unos 50 s); mismo resultado.
WHERE u.id IN (SELECT u2.id FROM mgn.deteccion_cambio d
               JOIN sim.ugm u2 ON ST_Contains(u2.geom, ST_PointOnSurface(d.geom)));

COMMENT ON VIEW mgn.v_tab_geo_ugm IS
    'Tablero v2 (S08c, D-28). Solo contorno y código de las UGM del SNIT que contienen '
    'polígonos de prueba. Excepción acotada a D-18: ningún atributo de visita ni avance de sim.';

GRANT SELECT ON mgn.v_tab_geo_poligonos TO tablero_lectura;
GRANT SELECT ON mgn.v_tab_geo_ugm       TO tablero_lectura;
