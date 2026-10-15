-- Tamaños de la base y de cada relación de sim (paso 3 y 6a).
SELECT pg_size_pretty(pg_database_size(current_database())) AS base,
       pg_database_size(current_database())                 AS base_bytes;
SELECT n.nspname AS esquema, c.relname AS tabla,
       pg_size_pretty(pg_table_size(c.oid))          AS tabla_y_toast,
       pg_size_pretty(pg_indexes_size(c.oid))        AS indices,
       pg_size_pretty(pg_total_relation_size(c.oid)) AS total,
       pg_total_relation_size(c.oid)                 AS total_bytes
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname IN ('sim','mgn') AND c.relkind = 'r'
ORDER BY n.nspname, c.relname;
