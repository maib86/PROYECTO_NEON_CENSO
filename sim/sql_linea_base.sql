-- Línea base de mgn y del almacenamiento (antes y después del encargo S04).
SELECT now() AT TIME ZONE 'America/Costa_Rica' AS hora_cr;
SELECT (SELECT count(*) FROM mgn.deteccion_cambio) AS poligonos,
       (SELECT count(*) FROM mgn.finca_visita)     AS puntos;
SELECT lote, estado_visita, count(*) FROM mgn.finca_visita GROUP BY 1,2 ORDER BY 1,2;
SELECT md5(string_agg(id || '|' || lote || '|' || estado_visita || '|' ||
                      coalesce(encuestador,'') || '|' || coalesce(fecha_visita::text,'') || '|' ||
                      editado_por || '|' || fecha_edicion::text, ',' ORDER BY id)) AS huella_finca_visita
FROM mgn.finca_visita;
SELECT md5(string_agg(id || '|' || ST_AsBinary(geom)::text, ',' ORDER BY id)) AS huella_poligonos
FROM mgn.deteccion_cambio;
SELECT pg_size_pretty(pg_database_size(current_database())) AS base,
       pg_database_size(current_database())                 AS base_bytes;
SELECT n.nspname AS esquema,
       pg_size_pretty(sum(pg_total_relation_size(c.oid))) AS total,
       sum(pg_total_relation_size(c.oid))                 AS bytes
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname IN ('mgn','sim') AND c.relkind IN ('r','m')
GROUP BY 1 ORDER BY 1;
SELECT nspname FROM pg_namespace WHERE nspname = 'sim';
