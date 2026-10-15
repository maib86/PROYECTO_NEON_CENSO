-- =====================================================================================
--  PLANTILLA 04 — PANEL DE SEGUIMIENTO
-- =====================================================================================
--  Crea cuatro vistas para saber, en cualquier momento, quién editó qué, cuánto
--  y cuándo. Se ejecuta una sola vez; después el seguimiento es una consulta.
--
--  CAMBIA SEGÚN EL CASO: solo los nombres (esquema, tabla, columna de reparto,
--  usuarios y zona horaria). La lógica no cambia.
--
--  CÓMO DISTINGUE UNA EDICIÓN REAL DE LA CARGA INICIAL
--  Al cargar, el trigger de auditoría dejó fecha_creacion = fecha_edicion en todas
--  las filas. Por eso la condición
--        fecha_edicion > fecha_creacion
--  identifica exactamente las filas que alguien tocó DESPUÉS de la carga.
--  Es el criterio que usan las cuatro vistas. Sin él, el panel mostraría el 100%
--  de avance desde el primer día.
-- =====================================================================================


-- =====================================================================================
--  VISTA 1 — Avance general por parte asignada
-- =====================================================================================

CREATE OR REPLACE VIEW <<<ESQUEMA>>>.v_seguimiento AS
SELECT
    <<<COLUMNA_REPARTO>>>,
    count(*)                                                    AS total_registros,
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
        FILTER (WHERE fecha_edicion > fecha_creacion)           AS personas
FROM <<<ESQUEMA>>>.<<<TABLA>>>
GROUP BY <<<COLUMNA_REPARTO>>>
ORDER BY <<<COLUMNA_REPARTO>>>;


-- =====================================================================================
--  VISTA 2 — Actividad por persona y por día
-- =====================================================================================
--  CAMBIA SEGÚN EL CASO: la zona horaria, si el equipo no está en Costa Rica.
--  PostgreSQL guarda todo en UTC; la conversión es solo para leerlo.
-- =====================================================================================

CREATE OR REPLACE VIEW <<<ESQUEMA>>>.v_actividad_diaria AS
SELECT
    (fecha_edicion AT TIME ZONE '<<<ZONA_HORARIA>>>')::date       AS dia,
    editado_por,
    count(*)                                                      AS registros_tocados,
    min(fecha_edicion AT TIME ZONE '<<<ZONA_HORARIA>>>')::time(0) AS primera_hora,
    max(fecha_edicion AT TIME ZONE '<<<ZONA_HORARIA>>>')::time(0) AS ultima_hora
FROM <<<ESQUEMA>>>.<<<TABLA>>>
WHERE fecha_edicion > fecha_creacion
GROUP BY 1, 2
ORDER BY dia DESC, editado_por;


-- =====================================================================================
--  VISTA 3 — Últimos movimientos
-- =====================================================================================

CREATE OR REPLACE VIEW <<<ESQUEMA>>>.v_ultimos_movimientos AS
SELECT
    id,
    <<<COLUMNA_REPARTO>>>,
    estado_revision,
    editado_por,
    to_char(fecha_edicion AT TIME ZONE '<<<ZONA_HORARIA>>>',
            'DD/MM HH24:MI')                AS cuando,
    observaciones
FROM <<<ESQUEMA>>>.<<<TABLA>>>
WHERE fecha_edicion > fecha_creacion
ORDER BY fecha_edicion DESC
LIMIT 30;


-- =====================================================================================
--  VISTA 4 — Avance desagregado
-- =====================================================================================
--  Útil cuando cada parte asignada tiene subdivisiones (cantones dentro de una
--  provincia, UPM dentro de un lote) y se quiere detectar zonas rezagadas.
--  CAMBIA SEGÚN EL CASO: <<<COLUMNA_DETALLE>>> es la subdivisión.
--  Si no hay subdivisión útil, omitir esta vista entera.
-- =====================================================================================

CREATE OR REPLACE VIEW <<<ESQUEMA>>>.v_avance_detalle AS
SELECT
    <<<COLUMNA_REPARTO>>>,
    <<<COLUMNA_DETALLE>>>,
    count(*)                                               AS total,
    count(*) FILTER (WHERE fecha_edicion > fecha_creacion) AS editados,
    round(
        100.0 * count(*) FILTER (WHERE fecha_edicion > fecha_creacion)
        / NULLIF(count(*), 0)
    , 1)                                                   AS pct
FROM <<<ESQUEMA>>>.<<<TABLA>>>
GROUP BY <<<COLUMNA_REPARTO>>>, <<<COLUMNA_DETALLE>>>
ORDER BY <<<COLUMNA_REPARTO>>>, <<<COLUMNA_DETALLE>>>;


-- =====================================================================================
--  PERMISOS — que todas las personas puedan ver el avance
-- =====================================================================================
--  CAMBIA SEGÚN EL CASO: la lista de usuarios.
--  Compartir el panel suele ser buena idea: cada quien ve cómo va el conjunto sin
--  tener que preguntar.
-- =====================================================================================

GRANT SELECT ON <<<ESQUEMA>>>.v_seguimiento,
                <<<ESQUEMA>>>.v_actividad_diaria,
                <<<ESQUEMA>>>.v_ultimos_movimientos,
                <<<ESQUEMA>>>.v_avance_detalle
    TO <<<USUARIO_1>>>, <<<USUARIO_2>>>, <<<USUARIO_3>>>;


-- =====================================================================================
--  CONSULTAS DEL DÍA A DÍA
-- =====================================================================================
--  Guardar estas tres en el SQL Editor de Neon con el botón "Save", bajo el nombre
--  "Panel de seguimiento". Quedan en la pestaña Saved y se abren con un clic.
-- =====================================================================================

/*
SELECT * FROM <<<ESQUEMA>>>.v_seguimiento;
SELECT * FROM <<<ESQUEMA>>>.v_actividad_diaria;
SELECT * FROM <<<ESQUEMA>>>.v_ultimos_movimientos;
*/


-- =====================================================================================
--  ¿ESTÁ CONECTADA ALGUNA PERSONA EN ESTE MOMENTO?
-- =====================================================================================
--  ADVERTENCIA SOBRE QUÉ RESPONDE ESTA CONSULTA
--  pg_stat_activity solo muestra conexiones ACTIVAS en este instante. Si alguien
--  trabajó toda la mañana y cerró QGIS, no aparece. NO sirve para saber si trabajó;
--  para eso están las vistas de arriba. Sirve únicamente para "¿está adentro ahora?".
--
--  Según los privilegios del rol, algunas columnas pueden venir vacías. Eso no
--  impide ver que la sesión existe.
-- =====================================================================================

/*
SELECT
    usename                                             AS usuario,
    client_addr                                         AS ip_origen,
    state                                               AS estado,
    to_char(backend_start AT TIME ZONE '<<<ZONA_HORARIA>>>',
            'DD/MM HH24:MI')                            AS conectada_desde
FROM pg_stat_activity
WHERE datname = '<<<BASE_DE_DATOS>>>'
  AND usename LIKE 'edit%'
ORDER BY backend_start;
*/


-- =====================================================================================
--  LIMITACIÓN CONOCIDA DE ESTE DISEÑO
-- =====================================================================================
--  Estas vistas registran LA ÚLTIMA edición de cada registro, no el historial
--  completo. Si alguien cambia un estado hoy y lo vuelve a cambiar mañana, el
--  primer cambio se pierde.
--
--  Para la mayoría de los casos alcanza: responde quién, cuánto y cuándo.
--  Si el entregable exige historial completo (qué valor tenía antes y qué valor
--  tiene ahora, en cada cambio), hace falta una tabla de bitácora con su propio
--  trigger. No viene en este paquete; se agrega sin tocar nada de lo existente.
-- =====================================================================================
