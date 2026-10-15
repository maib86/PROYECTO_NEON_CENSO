-- =====================================================================================
--  PLANTILLA 03 — USUARIOS Y CONTROL DE ACCESO
-- =====================================================================================
--  Crea un usuario por persona y hace que la base IMPONGA el reparto del trabajo.
--
--  QUÉ LOGRA ESTE ARCHIVO
--  Después de ejecutarlo:
--    · Todas las personas VEN la capa completa (contexto geográfico completo).
--    · Cada una solo puede EDITAR los registros de su parte asignada.
--    · El intento de editar fuera de su parte es rechazado por la base, no por
--      disciplina ni por acuerdo verbal.
--    · Nadie puede reetiquetar un registro para pasarlo a otra parte.
--
--  POR QUÉ ESTO Y NO SOLO UN ACUERDO ENTRE PERSONAS
--  Un acuerdo verbal se rompe por error, por cansancio o por un clic equivocado, y
--  cuando se rompe nadie se entera hasta mucho después. La regla en la base se rompe
--  con un mensaje de error en el momento. Para un entregable que alguien va a
--  auditar, esa diferencia es la que vale.
--
--  CUÁNDO SE EJECUTA: después de 02_carga.sql, con los datos ya adentro.
-- =====================================================================================


-- =====================================================================================
--  BLOQUE 1 — Crear un usuario por persona
-- =====================================================================================
--  CAMBIA SEGÚN EL CASO: la cantidad de líneas y los nombres.
--  Hay que crear UNA línea CREATE ROLE por cada persona que va a editar.
--
--  LAS CONTRASEÑAS
--  16 caracteres o más, distintas entre sí, sin tildes, sin eñes y sin espacios.
--  Anotarlas antes de ejecutar: PostgreSQL no las muestra después.
--
--  REGLA QUE NO SE NEGOCIA: NUNCA COMPARTIR UN USUARIO ENTRE DOS PERSONAS.
--  El campo editado_por guarda el usuario de la conexión. Si dos personas entran
--  con el mismo, ese campo deja de significar algo y se pierde toda la trazabilidad:
--  ya no se puede responder quién tocó qué. Es gratis crear un usuario más.
--
--  NOMBRES SUGERIDOS: edit_<parte>, en minúscula y sin tildes.
--    edit_limon, edit_guanacaste, edit_norte, edit_sur, edit_lote_a...
-- =====================================================================================

CREATE ROLE <<<USUARIO_1>>> LOGIN PASSWORD '<<<CONTRASENA_1>>>';
CREATE ROLE <<<USUARIO_2>>> LOGIN PASSWORD '<<<CONTRASENA_2>>>';
CREATE ROLE <<<USUARIO_3>>> LOGIN PASSWORD '<<<CONTRASENA_3>>>';
-- Agregar o quitar líneas según la cantidad de personas.


-- =====================================================================================
--  BLOQUE 2 — Permisos básicos
-- =====================================================================================
--  CAMBIA SEGÚN EL CASO: solo la lista de usuarios al final de cada línea.
--  Hay que nombrarlos todos, separados por coma, en las cuatro sentencias.
--
--  QUÉ HACE CADA UNA
--    USAGE ON SCHEMA ....... permite "entrar" al esquema. Sin esto no ven nada.
--    SELECT/INSERT/...  .... permite leer y escribir la tabla. El control fino
--                            lo pone el Bloque 3; esto es el permiso de base.
--    USAGE ON SEQUENCE ..... permite CREAR registros nuevos. Si falta, pueden
--                            modificar lo existente pero no dibujar polígonos
--                            nuevos, y el error que da no es nada evidente.
--    SELECT ON geometry_columns ... QGIS lee ese catálogo para listar las capas
--                            disponibles. Sin esto la capa no aparece en el árbol.
--
--  EL NOMBRE DE LA SECUENCIA se arma solo: <tabla>_<columna>_seq. Para una tabla
--  llamada deteccion_cambio con llave id, es deteccion_cambio_id_seq.
-- =====================================================================================

GRANT USAGE ON SCHEMA <<<ESQUEMA>>>
    TO <<<USUARIO_1>>>, <<<USUARIO_2>>>, <<<USUARIO_3>>>;

GRANT SELECT, INSERT, UPDATE, DELETE ON <<<ESQUEMA>>>.<<<TABLA>>>
    TO <<<USUARIO_1>>>, <<<USUARIO_2>>>, <<<USUARIO_3>>>;

GRANT USAGE, SELECT ON SEQUENCE <<<ESQUEMA>>>.<<<TABLA>>>_id_seq
    TO <<<USUARIO_1>>>, <<<USUARIO_2>>>, <<<USUARIO_3>>>;

GRANT SELECT ON geometry_columns, geography_columns, spatial_ref_sys
    TO <<<USUARIO_1>>>, <<<USUARIO_2>>>, <<<USUARIO_3>>>;


-- =====================================================================================
--  BLOQUE 3 — Row Level Security: el reparto, impuesto por la base
-- =====================================================================================
--  CAMBIA SEGÚN EL CASO: una política de escritura por persona.
--
--  CÓMO FUNCIONA
--  Row Level Security filtra qué FILAS ve y toca cada usuario. Se escriben dos
--  clases de política:
--
--    · UNA de lectura, para todos: deja ver la capa completa.
--    · UNA de escritura POR PERSONA: la acota a su parte.
--
--  Las políticas se combinan con O lógico, por eso la de lectura garantiza que
--  el SELECT siga devolviendo todo pese a las de escritura.
--
--  USING vs WITH CHECK (la distinción que más confunde):
--    USING      decide qué filas EXISTENTES puede tocar.
--    WITH CHECK decide cómo pueden QUEDAR las filas después de tocarlas.
--  Hacen falta las dos. Sin WITH CHECK, alguien podría cambiar el valor de reparto
--  de una fila suya y "regalársela" a otra persona, o al revés, apropiarse de una
--  ajena cambiándole la etiqueta.
-- =====================================================================================

ALTER TABLE <<<ESQUEMA>>>.<<<TABLA>>> ENABLE ROW LEVEL SECURITY;

-- Lectura de la capa completa, para todas las personas.
CREATE POLICY pol_lectura_total
    ON <<<ESQUEMA>>>.<<<TABLA>>>
    FOR SELECT
    TO <<<USUARIO_1>>>, <<<USUARIO_2>>>, <<<USUARIO_3>>>
    USING (true);

-- Escritura acotada. UN bloque como este por cada persona.
CREATE POLICY pol_escritura_<<<USUARIO_1>>>
    ON <<<ESQUEMA>>>.<<<TABLA>>>
    FOR ALL
    TO <<<USUARIO_1>>>
    USING      (<<<COLUMNA_REPARTO>>> = '<<<VALOR_1>>>')
    WITH CHECK (<<<COLUMNA_REPARTO>>> = '<<<VALOR_1>>>');

CREATE POLICY pol_escritura_<<<USUARIO_2>>>
    ON <<<ESQUEMA>>>.<<<TABLA>>>
    FOR ALL
    TO <<<USUARIO_2>>>
    USING      (<<<COLUMNA_REPARTO>>> = '<<<VALOR_2>>>')
    WITH CHECK (<<<COLUMNA_REPARTO>>> = '<<<VALOR_2>>>');

CREATE POLICY pol_escritura_<<<USUARIO_3>>>
    ON <<<ESQUEMA>>>.<<<TABLA>>>
    FOR ALL
    TO <<<USUARIO_3>>>
    USING      (<<<COLUMNA_REPARTO>>> = '<<<VALOR_3>>>')
    WITH CHECK (<<<COLUMNA_REPARTO>>> = '<<<VALOR_3>>>');

-- SI UNA PERSONA TIENE VARIAS PARTES, se usa IN en vez de igualdad:
--    USING      (<<<COLUMNA_REPARTO>>> IN ('Limón','Heredia'))
--    WITH CHECK (<<<COLUMNA_REPARTO>>> IN ('Limón','Heredia'))

-- NOTA SOBRE EL PROPIETARIO
-- El rol dueño de la tabla (en Neon, neondb_owner) IGNORA estas políticas por
-- diseño. Eso es deliberado: deja una vía administrativa para corregir una
-- asignación mal hecha sin desarmar nada. Consecuencia práctica importante:
-- probar el sistema conectado como propietario no prueba nada, porque el
-- propietario puede todo. La prueba se hace con los usuarios de edición.
--
-- Si se quisiera que las políticas apliquen también al propietario:
--    ALTER TABLE <<<ESQUEMA>>>.<<<TABLA>>> FORCE ROW LEVEL SECURITY;


-- =====================================================================================
--  VERIFICACIÓN
-- =====================================================================================

-- Deben aparecer todos los usuarios creados.
SELECT rolname FROM pg_roles WHERE rolname LIKE 'edit%' ORDER BY rolname;

-- Deben aparecer: 1 política de lectura + 1 de escritura por persona.
SELECT policyname, cmd, roles::text
FROM pg_policies
WHERE tablename = '<<<TABLA>>>'
ORDER BY policyname;


-- =====================================================================================
--  SIGUIENTE PASO: 04_panel_seguimiento.sql
-- =====================================================================================
