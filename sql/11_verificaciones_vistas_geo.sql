-- =====================================================================================
--  Verificaciones de sql/11_vistas_geo_tablero.sql (spec S08c, pasos 1 y 1b). Solo lectura.
--  Cuenta administradora:  py sim/psql.py -f sql/11_verificaciones_vistas_geo.sql -- -a
-- =====================================================================================
\pset pager off
SET TIME ZONE 'America/Costa_Rica';
SELECT now() AS hora_consulta, current_user;

-- Conteos (el spec esperaba 33 con estado distinto de pendiente: son 33 concluidas + 6 revisitas)
SELECT count(*) AS total,
       count(*) FILTER (WHERE estado_visita <> 'pendiente') AS con_estado_no_pendiente,
       count(*) FILTER (WHERE estado_visita IN ('visitada','no_localizada','rechazo')) AS concluidas,
       count(*) FILTER (WHERE estado_visita = 'revisita') AS revisitas,
       count(*) FILTER (WHERE geom IS NULL) AS geom_nulas,
       count(*) FILTER (WHERE ugm IS NULL) AS sin_ugm,
       count(*) FILTER (WHERE lon IS NULL) AS sin_punto,
       count(DISTINCT id) AS ids_distintos
FROM mgn.v_tab_geo_poligonos;

-- Polígonos por UGM
SELECT count(*) AS n_ugm, min(n) AS min_pol, max(n) AS max_pol
FROM (SELECT ugm, count(*) n FROM mgn.v_tab_geo_poligonos WHERE ugm IS NOT NULL GROUP BY ugm) x;

-- Tamaño del GeoJSON (umbral del spec: 1,5 MB)
SELECT sum(length(geom::text)) AS bytes_poligonos FROM mgn.v_tab_geo_poligonos;
SELECT count(*) AS n_ugm_vista, sum(length(geom::text)) AS bytes_ugm FROM mgn.v_tab_geo_ugm;

-- Columnas: sin observaciones ni posicion_registro
SELECT count(*) AS columnas_vedadas FROM information_schema.columns
WHERE table_schema = 'mgn' AND table_name IN ('v_tab_geo_poligonos','v_tab_geo_ugm')
  AND column_name IN ('observaciones','posicion_registro');

-- Permisos de tablero_lectura sobre las vistas nuevas y sobre sim.ugm (debe faltar)
SELECT grantee, table_schema, table_name, privilege_type FROM information_schema.role_table_grants
WHERE grantee = 'tablero_lectura' AND table_name IN ('v_tab_geo_poligonos','v_tab_geo_ugm','ugm')
ORDER BY 2, 3;

-- Diagnóstico de los polígonos sin UGM: ¿tocan alguna UGM (borde) o caen en un hueco?
WITH sin AS (SELECT d.id, d.codigo_upm, d.geom FROM mgn.deteccion_cambio d
             JOIN mgn.v_tab_geo_poligonos v ON v.id = d.id WHERE v.ugm IS NULL)
SELECT count(*) AS sin_ugm,
       count(*) FILTER (WHERE EXISTS (SELECT 1 FROM sim.ugm u WHERE ST_Intersects(u.geom, s.geom))) AS intersecan_alguna_ugm,
       count(*) FILTER (WHERE EXISTS (SELECT 1 FROM sim.ugm u WHERE ST_Covers(u.geom, ST_PointOnSurface(s.geom)))) AS punto_cubierto_en_borde,
       count(DISTINCT codigo_upm) AS upm
FROM sin s;

WITH sin AS (SELECT d.id, d.geom FROM mgn.deteccion_cambio d
             JOIN mgn.v_tab_geo_poligonos v ON v.id = d.id WHERE v.ugm IS NULL)
SELECT s.id,
       round(ST_Area(s.geom)) AS area_m2,
       (SELECT round(ST_Distance(u.geom, ST_PointOnSurface(s.geom))::numeric, 1)
          FROM sim.ugm u ORDER BY u.geom <-> ST_PointOnSurface(s.geom) LIMIT 1) AS dist_ugm_mas_cercana_m,
       (SELECT u.cod_distrito FROM sim.ugm u ORDER BY u.geom <-> ST_PointOnSurface(s.geom) LIMIT 1) AS distrito_ugm_cercana
FROM sin s ORDER BY s.id;
