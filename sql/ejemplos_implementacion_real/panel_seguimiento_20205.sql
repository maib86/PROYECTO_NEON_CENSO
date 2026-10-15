-- =====================================================================================
--  PANEL DE SEGUIMIENTO — Prueba distrito 20205
-- =====================================================================================
--  Ejecutar como neondb_owner en el SQL Editor de Neon.
--  Los bloques 1 a 4 crean las vistas una sola vez.
--  Después basta con las consultas del Bloque 5 para el día a día.
--
--  CÓMO DISTINGUE UNA EDICIÓN REAL
--  Al cargar, el trigger puso fecha_creacion = fecha_edicion en las 1.432 filas.
--  Por eso `fecha_edicion > fecha_creacion` identifica exactamente las filas que
--  alguien tocó después de la carga. Es el criterio que usan todas las vistas.
-- =====================================================================================


-- =====================================================================================
--  BLOQUE 1 — Vista de avance general (reemplaza la v_avance anterior)
-- =====================================================================================

CREATE OR REPLACE VIEW mgn.v_seguimiento AS
SELECT
    lote,
    count(*)                                                    AS total_poligonos,
    count(*) FILTER (WHERE fecha_edicion > fecha_creacion)      AS editados,
    round(
        100.0 * count(*) FILTER (WHERE fecha_edicion > fecha_creacion)
        / NULLIF(count(*), 0)
    , 1)                                                        AS avance_pct,
    count(*) FILTER (WHERE estado_revision = 'pendiente')       AS pendiente,
    count(*) FILTER (WHERE estado_revision = 'en_proceso')      AS en_proceso,
    count(*) FILTER (WHERE estado_revision = 'revisado')        AS revisado,
    count(*) FILTER (WHERE estado_revision = 'validado')        AS validado,
    count(*) FILTER (WHERE estado_revision = 'descartado')      AS descartado,
    max(fecha_edicion) FILTER (WHERE fecha_edicion > fecha_creacion)
                                                                AS ultima_edicion,
    string_agg(DISTINCT editado_por, ', ')
        FILTER (WHERE fecha_edicion > fecha_creacion)           AS editoras
FROM mgn.deteccion_cambio
GROUP BY lote
ORDER BY lote;

COMMENT ON VIEW mgn.v_seguimiento IS
    'Avance por lote: cuántos polígonos se tocaron, en qué estado están y quién editó.';


-- =====================================================================================
--  BLOQUE 2 — Actividad por persona y por día
-- =====================================================================================

CREATE OR REPLACE VIEW mgn.v_actividad_diaria AS
SELECT
    (fecha_edicion AT TIME ZONE 'America/Costa_Rica')::date AS dia,
    editado_por,
    count(*)                                                AS poligonos_tocados,
    min(fecha_edicion AT TIME ZONE 'America/Costa_Rica')::time(0) AS primera_hora,
    max(fecha_edicion AT TIME ZONE 'America/Costa_Rica')::time(0) AS ultima_hora
FROM mgn.deteccion_cambio
WHERE fecha_edicion > fecha_creacion
GROUP BY 1, 2
ORDER BY dia DESC, editado_por;

COMMENT ON VIEW mgn.v_actividad_diaria IS
    'Ritmo de trabajo: cuántos polígonos tocó cada quien cada día, en hora de Costa Rica.';


-- =====================================================================================
--  BLOQUE 3 — Últimos movimientos (las 30 ediciones más recientes)
-- =====================================================================================

CREATE OR REPLACE VIEW mgn.v_ultimos_movimientos AS
SELECT
    id,
    lote,
    codigo_upm,
    estado_revision,
    priority_cat,
    editado_por,
    to_char(fecha_edicion AT TIME ZONE 'America/Costa_Rica',
            'DD/MM HH24:MI')                AS cuando,
    observaciones
FROM mgn.deteccion_cambio
WHERE fecha_edicion > fecha_creacion
ORDER BY fecha_edicion DESC
LIMIT 30;

COMMENT ON VIEW mgn.v_ultimos_movimientos IS
    'Las 30 ediciones más recientes, con quién y cuándo.';


-- =====================================================================================
--  BLOQUE 4 — Avance por UPM dentro de cada lote
-- =====================================================================================

CREATE OR REPLACE VIEW mgn.v_avance_upm AS
SELECT
    lote,
    codigo_upm,
    count(*)                                               AS total,
    count(*) FILTER (WHERE fecha_edicion > fecha_creacion) AS editados,
    round(
        100.0 * count(*) FILTER (WHERE fecha_edicion > fecha_creacion)
        / NULLIF(count(*), 0)
    , 1)                                                   AS pct
FROM mgn.deteccion_cambio
GROUP BY lote, codigo_upm
ORDER BY lote, codigo_upm;

COMMENT ON VIEW mgn.v_avance_upm IS
    'Avance desagregado por UPM. Útil para ver si alguna quedó rezagada.';


-- Permisos de lectura para ambas editoras
GRANT SELECT ON mgn.v_seguimiento,
                mgn.v_actividad_diaria,
                mgn.v_ultimos_movimientos,
                mgn.v_avance_upm
    TO edit_lote_a, edit_lote_b;


-- =====================================================================================
--  BLOQUE 5 — CONSULTAS DEL DÍA A DÍA
-- =====================================================================================
--  Guardar esta consulta en el SQL Editor de Neon con el botón "Save".
--  Nombre sugerido: "Panel de seguimiento"
-- =====================================================================================

/*
SELECT * FROM mgn.v_seguimiento;
SELECT * FROM mgn.v_actividad_diaria;
SELECT * FROM mgn.v_ultimos_movimientos;
*/


-- =====================================================================================
--  BLOQUE 6 — ¿Está conectada en este momento?
-- =====================================================================================
--  pg_stat_activity solo muestra conexiones ACTIVAS ahora mismo. Si ella cerró QGIS,
--  no aparece, aunque haya trabajado toda la mañana. Para saber si trabajó, usar las
--  vistas de arriba; esta consulta responde únicamente "¿está adentro en este instante?".
--
--  Nota: según los privilegios del rol, algunas columnas pueden venir vacías.
--  Eso no impide ver que la sesión existe.
-- =====================================================================================

/*
SELECT
    usename                                             AS usuario,
    client_addr                                         AS ip_origen,
    state                                               AS estado,
    to_char(backend_start AT TIME ZONE 'America/Costa_Rica',
            'DD/MM HH24:MI')                            AS conectada_desde,
    to_char(state_change  AT TIME ZONE 'America/Costa_Rica',
            'DD/MM HH24:MI')                            AS ultimo_movimiento
FROM pg_stat_activity
WHERE datname = 'neondb'
  AND usename LIKE 'edit\_%'
ORDER BY backend_start;
*/


-- =====================================================================================
--  BLOQUE 7 — Verificación de integridad (correr una vez por semana)
-- =====================================================================================
--  Las cuatro deben dar 0. Si alguna no da 0, avisar antes de seguir editando.
-- =====================================================================================

/*
-- Geometrías inválidas
SELECT count(*) AS invalidas FROM mgn.deteccion_cambio WHERE NOT ST_IsValid(geom);

-- Filas sin lote asignado (no debería poder ocurrir: hay un CHECK)
SELECT count(*) AS sin_lote FROM mgn.deteccion_cambio WHERE lote IS NULL;

-- SRC distinto de CRTM05
SELECT count(*) AS src_incorrecto FROM mgn.deteccion_cambio WHERE ST_SRID(geom) <> 5367;

-- Polígonos duplicados por identificador de origen
SELECT count(*) AS id_duplicados FROM (
    SELECT id_origen FROM mgn.deteccion_cambio
    GROUP BY id_origen HAVING count(*) > 1
) d;
*/
