SELECT current_user;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM sim.v_tab_resumen;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM sim.v_tab_encuestador;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM sim.v_tab_diario;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM sim.v_tab_puntos;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM sim.v_tab_movimientos;
-- Tiempo de cliente (servidor + red + recepción), salida descartada
\timing on
\o NUL
SELECT * FROM sim.v_tab_resumen;
SELECT * FROM sim.v_tab_encuestador;
SELECT * FROM sim.v_tab_diario;
SELECT * FROM sim.v_tab_puntos;
SELECT * FROM sim.v_tab_movimientos;
\o
\timing off
SELECT count(*) AS filas_puntos FROM sim.v_tab_puntos;
