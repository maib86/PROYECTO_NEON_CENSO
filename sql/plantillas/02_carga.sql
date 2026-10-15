-- =====================================================================================
--  PLANTILLA 02 — CARGA DE LA CAPA
-- =====================================================================================
--  Pasa los datos de la tabla de paso (creada por QGIS al importar) a la tabla
--  definitiva, haciendo tres cosas en el camino:
--     · unificar las geometrías simples y multiparte,
--     · reparar geometrías inválidas,
--     · asignar el valor de reparto a cada registro.
--
--  ANTES DE EJECUTAR ESTE ARCHIVO
--  Hay que haber importado la capa a <<<ESQUEMA>>>.carga_temporal desde el
--  Administrador de BBDD de QGIS (ver la guía, Paso 3).
--
--  POR QUÉ UNA TABLA DE PASO Y NO IMPORTAR DIRECTO
--  Importar directo a la tabla definitiva parece más corto, pero obliga a que los
--  nombres y tipos de la capa de origen coincidan exactamente con los de la tabla,
--  y no deja lugar para asignar el reparto ni para reparar geometrías. La tabla de
--  paso desacopla las dos cosas: QGIS escribe lo que trae, y el INSERT decide cómo
--  entra. Es un paso más que ahorra varias vueltas.
-- =====================================================================================


-- =====================================================================================
--  PASO 2.1 — Ver qué nombres de columna quedaron en la tabla de paso
-- =====================================================================================
--  NO CAMBIA, salvo el nombre del esquema.
--  El importador de QGIS puede alterar nombres (pasarlos a minúscula, recortarlos).
--  Esta consulta muestra exactamente qué hay, que es lo que debe usarse en el INSERT.
-- =====================================================================================

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = '<<<ESQUEMA>>>' AND table_name = 'carga_temporal'
ORDER BY ordinal_position;


-- =====================================================================================
--  PASO 2.2 — Insertar en la tabla definitiva
-- =====================================================================================
--  CAMBIA SEGÚN EL CASO: todo el mapeo de columnas.
--
--  CÓMO SE LEE ESTE INSERT
--  La lista de arriba (entre paréntesis después del nombre de la tabla) son las
--  columnas DESTINO, tal como se definieron en 01_estructura.sql.
--  La lista del SELECT son las columnas ORIGEN, tal como aparecieron en el paso 2.1.
--  Van emparejadas por posición: la primera con la primera, la segunda con la segunda.
--  Si el orden no coincide, los datos entran en la columna equivocada sin dar error.
--  Conviene revisarlo dos veces.
--
--  LA ASIGNACIÓN DEL REPARTO
--  El CASE WHEN es lo que decide a quién le toca cada registro. Hay tres formas
--  habituales de escribirlo, según cómo se repartieron:
--
--  (a) El dato ya viene en la capa (lo más simple):
--        provincia_origen
--
--  (b) Se deriva de otro campo (ejemplo: por los últimos 3 dígitos de un código):
--        CASE WHEN right(codigo_upm, 3) IN ('001','002','003') THEN 'A'
--             ELSE 'B' END
--
--  (c) Se deriva de la ubicación geográfica, cruzando contra otra capa:
--        (SELECT p.nombre FROM <<<ESQUEMA>>>.provincias p
--          WHERE ST_Intersects(p.geom, ST_Centroid(t.geom)) LIMIT 1)
--
--  LAS DOS FUNCIONES DE LA GEOMETRÍA
--    ST_MakeValid  repara autointersecciones y otros defectos que traen muchas
--                  capas heredadas. Sin esto, la restricción de validez del paso 2.4
--                  rechazaría la carga.
--    ST_Multi      convierte geometrías simples a multiparte, para que todas tengan
--                  el mismo tipo. Quitarlo solo si la tabla se declaró como Polygon
--                  simple, lo cual no se recomienda.
-- =====================================================================================

INSERT INTO <<<ESQUEMA>>>.<<<TABLA>>> (
    id_origen,
    <<<COLUMNA_REPARTO>>>,
    <<<ATRIBUTO_1>>>,
    <<<ATRIBUTO_2>>>,
    <<<ATRIBUTO_3>>>,
    geom
)
SELECT
    <<<CAMPO_ID_EN_ORIGEN>>>,

    -- Asignación del reparto: reemplazar por la forma (a), (b) o (c) de arriba.
    <<<EXPRESION_DE_REPARTO>>>,

    <<<CAMPO_1_EN_ORIGEN>>>,
    <<<CAMPO_2_EN_ORIGEN>>>::integer,
    <<<CAMPO_3_EN_ORIGEN>>>,

    ST_Multi(ST_MakeValid(geom))
FROM <<<ESQUEMA>>>.carga_temporal;


-- =====================================================================================
--  PASO 2.3 — Verificación obligatoria
-- =====================================================================================
--  NO CAMBIA, salvo nombres. Las cinco deben pasar antes de seguir.
--  Si alguna falla, NO continuar: vaciar la tabla con
--      TRUNCATE <<<ESQUEMA>>>.<<<TABLA>>>;
--  corregir el INSERT y volver a ejecutarlo.
-- =====================================================================================

-- 1) El total debe coincidir con la cantidad de objetos de la capa de origen.
SELECT count(*) AS total FROM <<<ESQUEMA>>>.<<<TABLA>>>;

-- 2) El reparto debe mostrar todos los valores previstos, ninguno de más.
SELECT <<<COLUMNA_REPARTO>>>, count(*)
FROM <<<ESQUEMA>>>.<<<TABLA>>>
GROUP BY <<<COLUMNA_REPARTO>>>
ORDER BY <<<COLUMNA_REPARTO>>>;

-- 3) Debe dar 0.
SELECT count(*) AS invalidas
FROM <<<ESQUEMA>>>.<<<TABLA>>> WHERE NOT ST_IsValid(geom);

-- 4) Debe dar una sola fila, con el EPSG elegido.
SELECT DISTINCT ST_SRID(geom) AS srid FROM <<<ESQUEMA>>>.<<<TABLA>>>;

-- 5) PRUEBA DE FUEGO DE LA REPROYECCIÓN.
--    El área total calculada debe parecerse al área conocida de la capa.
--    Si da un número absurdo (millones de hectáreas, o fracciones diminutas),
--    la reproyección no se aplicó y hay que rehacer la importación.
--    Esta es la verificación que más errores atrapa.
SELECT round((sum(ST_Area(geom)) / 10000.0)::numeric, 2) AS hectareas_calculadas
FROM <<<ESQUEMA>>>.<<<TABLA>>>;


-- =====================================================================================
--  PASO 2.4 — Cerrar la carga
-- =====================================================================================
--  Ejecutar SOLO cuando las cinco verificaciones pasaron.
--
--  La restricción de validez se agrega ahora y no en 01_estructura.sql a propósito:
--  si existiera durante la carga, una sola geometría defectuosa abortaría las miles
--  de filas restantes. Agregada después, protege las ediciones futuras sin haber
--  estorbado la carga inicial.
-- =====================================================================================

ALTER TABLE <<<ESQUEMA>>>.<<<TABLA>>>
    ADD CONSTRAINT chk_geom_valida CHECK (ST_IsValid(geom)) NOT VALID;

ALTER TABLE <<<ESQUEMA>>>.<<<TABLA>>>
    VALIDATE CONSTRAINT chk_geom_valida;

DROP TABLE <<<ESQUEMA>>>.carga_temporal;


-- =====================================================================================
--  SIGUIENTE PASO: 03_usuarios_y_acceso.sql
-- =====================================================================================
