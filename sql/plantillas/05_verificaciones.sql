-- =====================================================================================
--  PLANTILLA 05 — VERIFICACIONES
-- =====================================================================================
--  Consultas de control agrupadas por momento de uso. No se ejecuta de corrido:
--  se abre, se copia la consulta que hace falta y se ejecuta sola.
--
--  CAMBIA SEGÚN EL CASO: solo los nombres.
-- =====================================================================================


-- =====================================================================================
--  A. DESPUÉS DE CREAR LA ESTRUCTURA (tras 01_estructura.sql)
-- =====================================================================================

-- A.1 — ¿La tabla quedó registrada con el sistema de coordenadas correcto?
--       Debe devolver una fila con el EPSG elegido.
SELECT f_table_schema, f_table_name, type, srid
FROM geometry_columns
WHERE f_table_name = '<<<TABLA>>>';

-- A.2 — ¿Qué columnas quedaron, con qué tipo?
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = '<<<ESQUEMA>>>' AND table_name = '<<<TABLA>>>'
ORDER BY ordinal_position;

-- A.3 — ¿Los índices se crearon?
--       Deben aparecer al menos el espacial y el de la columna de reparto.
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = '<<<ESQUEMA>>>' AND tablename = '<<<TABLA>>>';


-- =====================================================================================
--  B. DESPUÉS DE CARGAR LOS DATOS (tras 02_carga.sql)
-- =====================================================================================
--  LAS CINCO OBLIGATORIAS. Si alguna falla, NO continuar con los usuarios:
--  vaciar con TRUNCATE, corregir el INSERT y volver a cargar.
-- =====================================================================================

-- B.1 — Total cargado. Debe coincidir con la capa de origen.
SELECT count(*) AS total FROM <<<ESQUEMA>>>.<<<TABLA>>>;

-- B.2 — Reparto. Deben aparecer todos los valores previstos y ninguno de más.
SELECT <<<COLUMNA_REPARTO>>>, count(*)
FROM <<<ESQUEMA>>>.<<<TABLA>>>
GROUP BY <<<COLUMNA_REPARTO>>>
ORDER BY <<<COLUMNA_REPARTO>>>;

-- B.3 — Geometrías inválidas. Debe dar 0.
SELECT count(*) AS invalidas
FROM <<<ESQUEMA>>>.<<<TABLA>>> WHERE NOT ST_IsValid(geom);

-- B.4 — Sistema de coordenadas. Debe dar una sola fila con el EPSG elegido.
SELECT DISTINCT ST_SRID(geom) AS srid FROM <<<ESQUEMA>>>.<<<TABLA>>>;

-- B.5 — PRUEBA DE FUEGO DE LA REPROYECCIÓN.
--       El área debe parecerse a la conocida de la capa. Un número absurdo
--       (millones de hectáreas o fracciones diminutas) significa que la
--       reproyección no se aplicó. Es la verificación que más errores atrapa.
SELECT round((sum(ST_Area(geom)) / 10000.0)::numeric, 2) AS hectareas
FROM <<<ESQUEMA>>>.<<<TABLA>>>;

-- B.6 — Control adicional: ¿hay identificadores de origen duplicados?
--       Un resultado distinto de 0 suele significar que la carga se ejecutó
--       dos veces.
SELECT count(*) AS id_duplicados FROM (
    SELECT id_origen FROM <<<ESQUEMA>>>.<<<TABLA>>>
    GROUP BY id_origen HAVING count(*) > 1
) d;


-- =====================================================================================
--  C. DESPUÉS DE CREAR USUARIOS Y POLÍTICAS (tras 03_usuarios_y_acceso.sql)
-- =====================================================================================

-- C.1 — ¿Se crearon todos los usuarios?
SELECT rolname, rolcanlogin
FROM pg_roles WHERE rolname LIKE 'edit%' ORDER BY rolname;

-- C.2 — ¿Están todas las políticas?
--       Debe haber 1 de lectura + 1 de escritura por persona.
SELECT policyname, cmd, roles::text, qual::text
FROM pg_policies
WHERE tablename = '<<<TABLA>>>'
ORDER BY policyname;

-- C.3 — ¿Row Level Security está realmente activo en la tabla?
--       rowsecurity debe decir true. Si dice false, las políticas existen
--       pero no se aplican: falta el ALTER TABLE ... ENABLE ROW LEVEL SECURITY.
SELECT relname, relrowsecurity AS rls_activo
FROM pg_class
WHERE relname = '<<<TABLA>>>';


-- =====================================================================================
--  D. CONTROL SEMANAL (durante el trabajo)
-- =====================================================================================
--  Las cuatro deben dar 0. Si alguna no da 0, conviene avisar al equipo antes
--  de que siga editando sobre un problema.
-- =====================================================================================

SELECT count(*) AS invalidas
FROM <<<ESQUEMA>>>.<<<TABLA>>> WHERE NOT ST_IsValid(geom);

SELECT count(*) AS sin_reparto
FROM <<<ESQUEMA>>>.<<<TABLA>>> WHERE <<<COLUMNA_REPARTO>>> IS NULL;

SELECT count(*) AS src_incorrecto
FROM <<<ESQUEMA>>>.<<<TABLA>>> WHERE ST_SRID(geom) <> <<<EPSG>>>;

SELECT count(*) AS geometrias_vacias
FROM <<<ESQUEMA>>>.<<<TABLA>>> WHERE ST_IsEmpty(geom);


-- =====================================================================================
--  E. PRUEBA MANUAL DEL CONTROL DE ACCESO (opcional, para quien quiera verlo)
-- =====================================================================================
--  Permite comprobar el control de acceso desde el SQL Editor, sin montar QGIS
--  en dos máquinas. SET ROLE hace que la sesión actúe como ese usuario.
--
--  IMPORTANTE: ejecutar las cuatro líneas JUNTAS, de una sola vez. Si se ejecuta
--  solo el UPDATE sin el SET ROLE, correría como propietario, que ignora las
--  políticas, y no probaría nada.
-- =====================================================================================

/*
-- Debe FALLAR con un error de row-level security policy:
BEGIN;
SET ROLE <<<USUARIO_1>>>;
UPDATE <<<ESQUEMA>>>.<<<TABLA>>>
   SET estado_revision = 'en_proceso'
 WHERE <<<COLUMNA_REPARTO>>> = '<<<VALOR_2>>>';
ROLLBACK;
*/

/*
-- Debe FUNCIONAR (y el ROLLBACK deshace el cambio, así que no deja rastro):
BEGIN;
SET ROLE <<<USUARIO_1>>>;
UPDATE <<<ESQUEMA>>>.<<<TABLA>>>
   SET estado_revision = 'en_proceso'
 WHERE <<<COLUMNA_REPARTO>>> = '<<<VALOR_1>>>';
ROLLBACK;
*/
