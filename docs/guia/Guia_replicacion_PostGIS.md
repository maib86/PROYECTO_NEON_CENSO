# Guía de replicación — Capa vectorial compartida en PostGIS

**13 de octubre de 2026**

Cómo montar desde cero una base de datos PostGIS en la nube para que varias personas editen una misma capa vectorial desde QGIS, cada una sobre su parte asignada, sin generar versiones paralelas y sin instalar servidores ni pedir permisos de TI.

Esta guía está escrita a partir de una implementación real ya validada. Los archivos SQL que la acompañan vienen en dos versiones: **plantillas parametrizadas** para adaptar a cualquier caso, y los **archivos originales** de esa implementación como ejemplo trabajado.

---

## Cómo usar este paquete

El archivo comprimido trae dos carpetas y un `LEEME.txt`.

**`plantillas/`** — los cinco archivos SQL para adaptar al caso propio. Son los que se usan.

| Archivo | Qué hace | ¿Cambia según el caso? |
| --- | --- | --- |
| `01_estructura.sql` | Extensión PostGIS, esquema, tabla, índices, trigger de auditoría | **Sí, mucho** |
| `02_carga.sql` | Pasa los datos de la tabla de paso a la definitiva | **Sí, mucho** |
| `03_usuarios_y_acceso.sql` | Un usuario por persona y el control de acceso por fila | **Sí**, según cuántas personas |
| `04_panel_seguimiento.sql` | Vistas de avance, actividad y últimos movimientos | Solo nombres |
| `05_verificaciones.sql` | Consultas de control, para usar durante todo el proceso | Solo nombres |

**`ejemplo_implementacion_real/`** — los archivos tal como quedaron en la implementación que ya funciona (1.432 polígonos de detección de cambio, distrito 20205, repartidos entre dos personas). Sirven como referencia de cómo se ve una plantilla ya completada. **No ejecutar estos**: están atados a esa capa concreta.

### La convención de los marcadores

En las plantillas, todo lo que hay que sustituir está marcado así:

`<<<ALGO_EN_MAYUSCULAS>>>`

Antes de ejecutar cualquier archivo, buscá la secuencia `<<<` dentro de él y reemplazá cada aparición. Si queda alguna sin sustituir, el script falla con error de sintaxis — y eso es deliberado: es mucho mejor que falle ruidosamente a que corra con un valor equivocado y haya que deshacerlo después.

Una misma sustitución suele aparecer varias veces en el mismo archivo. Conviene usar «Reemplazar todo» del editor de texto, no ir una por una.

### Dónde se ejecuta cada cosa

Todo el SQL se ejecuta en el **SQL Editor de Neon**, dentro del navegador. No hace falta ningún programa de base de datos instalado. Los únicos pasos que se hacen en QGIS son la importación de la capa y la edición.

---

## Las seis decisiones que definen tu caso

Antes de tocar nada, hay que responder estas seis preguntas. Las respuestas son los valores que van en los marcadores `<<< >>>` de las plantillas. Conviene anotarlas en un archivo de texto y tenerlas a mano durante todo el proceso.

| # | Decisión | Qué define | En el ejemplo real |
| --- | --- | --- | --- |
| 1 | **¿Cuántas personas van a editar?** | Cuántos usuarios y cuántas políticas de acceso se crean | 2 |
| 2 | **¿Cómo se reparten el trabajo?** | El nombre de la columna de reparto y sus valores posibles | Por lote de UPM: `lote` con valores `A` y `B` |
| 3 | **¿Qué formato tiene la capa de origen?** | El procedimiento de importación y sus trampas | GeoJSON |
| 4 | **¿En qué sistema de coordenadas viene y en cuál debe quedar?** | La reproyección al importar | Venía en WGS84 (4326), quedó en CRTM05 (5367) |
| 5 | **¿Qué campos tiene la capa?** | Las columnas de la tabla y el mapeo de la carga | 25 campos del pipeline de detección |
| 6 | **¿Cómo se llaman el esquema y la tabla?** | Los nombres que se repiten en todos los archivos | Esquema `mgn`, tabla `deteccion_cambio` |

### La decisión 2 es la que de verdad importa

Las otras cinco son mecánicas. Esta es de diseño, y si se elige mal el sistema no funciona.

La columna de reparto tiene que cumplir tres condiciones:

1. **Cada registro cae en un solo valor.** Si un polígono pudiera pertenecer a dos personas, el control de acceso no sabe a quién dejárselo.
2. **Todos los registros tienen un valor.** Ninguno puede quedar en nulo, porque esa fila no la podría editar nadie.
3. **El reparto es estable.** Si las personas se intercambian zonas cada semana, hay que reasignar a mano cada vez. Funciona, pero es trabajo.

Lo más natural es repartir por geografía — provincia, cantón, distrito, UPM, zona — porque suele ser cómo la gente ya se divide el trabajo y además garantiza que nunca editen el mismo objeto.

Si el reparto **no** es geográfico sino temático (una persona revisa un tipo de objeto y otra revisa otro), funciona igual: la columna de reparto es el tipo, no la ubicación.

### Un caso que esta guía no cubre

Si dos personas necesitan editar **el mismo objeto** — no partes distintas de la capa, sino el mismo polígono — este diseño no aplica. Ahí hace falta un sistema de versionado con resolución de conflictos, que es otra herramienta y otro costo. El reparto por columna resuelve el caso de «nos dividimos el trabajo», que es el más común.

---

## Qué hay que instalar

Prácticamente nada. Esta es la confusión más común y conviene deshacerla antes de empezar.

PostgreSQL y PostGIS son el **servidor** de base de datos, y va a estar en la nube. QGIS trae incorporado su propio **cliente** de PostgreSQL, que es lo único que hace falta para conectarse a una base que corre en otro lado. Es la misma relación que hay entre un navegador y un servidor web: nadie instala Apache en su laptop para visitar una página.

| Componente | Quien monta la base | Quienes solo editan |
| --- | --- | --- |
| QGIS 3.28 o superior | Necesario | Necesario |
| Navegador web | Necesario | No |
| Cuenta en Neon | Una, propia | No |
| Servidor PostgreSQL | **No** | **No** |
| Extensión PostGIS | **No** | **No** |
| pgAdmin | Opcional | No |

No hay que abrir tiquetes con TI de ningún lado. Todo lo que se usa ya está instalado o se crea desde un navegador.

### La única excepción: los respaldos

El comando `pg_dump`, que hace respaldos completos, viene con la instalación de PostgreSQL. Sin ella no está disponible. Hay tres salidas, de menor a mayor esfuerzo:

- **Exportar desde QGIS a GeoPackage.** No requiere instalar nada. Guarda geometrías y atributos completos. Es lo recomendable para quien no tiene PostgreSQL local.
- **Instalar solo las herramientas de cliente** de PostgreSQL. En el instalador de Windows se marca únicamente *Command Line Tools*: unos 50 MB, sin servidor.
- **Instalar pgAdmin**, que trae `pg_dump` incluido.

La diferencia práctica: el GeoPackage guarda **los datos**; `pg_dump` guarda **los datos más la estructura** — tabla, usuarios, políticas, vistas, triggers. Para no perder el trabajo, el GeoPackage alcanza. Para restaurar todo tal cual tras un desastre, `pg_dump` es superior.

### Por qué esto importa más de lo que parece

En el plan gratuito de Neon la ventana de restauración es de **6 horas como máximo**, con tope de 1 GB de historial ([documentación de Neon](https://neon.com/docs/introduction/restore-window)). Los planes pagos llegan a 7 o 30 días.

Eso significa que si alguien detecta un problema al día siguiente, Neon ya no puede devolver el estado anterior. El respaldo propio no es una recomendación de buenas prácticas: es el único seguro real del trabajo.

---

## Paso 1 — Crear la base en Neon

**¿Cambia según el caso?** No. Este paso es idéntico siempre.

Unos 10 minutos, entero desde el navegador.

1. Entrar a **neon.com** y crear una cuenta. **Que la cree la persona que va a ser dueña de la base**: el dueño de la cuenta es el dueño de los datos.
2. Pulsar **Create project** y llenar:
    - **Project name:** un nombre descriptivo y definitivo. Conviene no ponerle `prueba_` si va a quedarse, porque cambiarlo después es incómodo.
    - **Postgres version:** la más alta que ofrezca.
    - **Region:** `AWS US East (Ohio)` o la más cercana. Con volúmenes de miles de registros la latencia es irrelevante, pero conviene no elegir Europa.
    - **Services:** dejar encendido solo **Postgres database**. Apagar Object storage, Functions, AI gateway y Neon Auth — no se usan y consumen cuota.
3. **Create project.**

### La pantalla que aparece después: ignorarla

Neon muestra una pantalla sobre «conectar tu agente de código» con un texto para pegar en herramientas de programación. **No sirve para este flujo** y además ese texto suele contener una llave de API de la cuenta, que es una credencial. Pulsar **Go to project** y seguir.

### Obtener las credenciales

1. Botón verde **Connect**, arriba a la izquierda.
2. **Apagar el interruptor «Connection pooling».** Esto es importante. El *pooler* está pensado para aplicaciones web con cientos de conexiones simultáneas; con QGIS estorba, y además `pg_dump` falla contra él. Al apagarlo, el host cambia: desaparece el `-pooler` de la dirección. **Ese es el host correcto.**
3. Pulsar **Show password** y **Copy snippet**.
4. Pegar en un archivo de texto y guardarlo. Neon no vuelve a mostrar la contraseña.

De la cadena copiada salen los cinco datos que se usan en todo lo que sigue:

```
postgresql://USUARIO:CONTRASENA@HOST/BASE?sslmode=require
```

| Dato | Dónde está | Valor típico |
| --- | --- | --- |
| Usuario | Entre `//` y `:` | `neondb_owner` |
| Contraseña | Entre `:` y `@` | empieza con `npg_` |
| Servidor (host) | Entre `@` y `/` | `ep-algo-algo.region.aws.neon.tech` |
| Base de datos | Después de la última `/` | `neondb` |
| Puerto | No aparece; siempre el mismo | `5432` |
| Modo SSL | Al final | `require` |

**El error más común al copiar la contraseña** es pasarse e incluir el `@` y las primeras letras del host. La contraseña es exactamente lo que está entre los dos puntos y la arroba, ni un carácter más.

### Dos cosas que conviene no hacer

- **No pulsar «Reset password»** una vez configurado todo: invalida la contraseña y hay que rehacer las conexiones de todas las personas.
- **No enviar la contraseña en capturas de pantalla.** Si por accidente queda expuesta, se resuelve con *Reset password* y avisando a quienes la usaban.

---

## Paso 2 — Crear la estructura

**¿Cambia según el caso?** **Sí, mucho.** Es el paso que más trabajo de adaptación requiere.

Archivo: **`plantillas/01_estructura.sql`**

Se ejecuta en el **SQL Editor de Neon**, en el menú izquierdo del proyecto. Crea la extensión PostGIS, el esquema, la tabla, los índices y el trigger de auditoría.

### Qué hay que sustituir

| Marcador | Qué poner |
| --- | --- |
| `<<<ESQUEMA>>>` | Nombre del esquema de trabajo, p. ej. `mgn` |
| `<<<TABLA>>>` | Nombre de la tabla, descriptivo del contenido |
| `<<<COLUMNA_REPARTO>>>` | La columna que divide el trabajo (decisión 2) |
| `<<<'VALOR_1','VALOR_2'...>>>` | Un valor por persona que va a editar |
| `<<<ATRIBUTO_N>>>` | Las columnas reales de la capa, con su tipo |
| `<<<TIPO_GEOMETRIA>>>` | `MultiPolygon`, `MultiLineString` o `Point` |
| `<<<EPSG>>>` | El código del sistema de coordenadas destino |
| `<<<PREFIJO>>>` | Prefijo corto para los nombres de índice |

### Tres reglas que no se negocian

Estas valen para cualquier caso, y saltarse alguna produce fallas confusas más adelante.

**1. Llave primaria entera única.** QGIS la necesita para editar una capa PostGIS de forma confiable. Si la capa de origen trae un identificador de texto, se conserva en la columna `id_origen` y **no** se usa como llave primaria. La plantilla ya lo resuelve.

**2. La columna de reparto va `NOT NULL` y con `CHECK`.** Un nulo ahí deja un registro que nadie puede editar. El `CHECK` impide que aparezcan valores no previstos.

**3. La geometría se declara con tipo y sistema explícitos.** `geometry(MultiPolygon, 5367)`, no `geometry` a secas. Declararlo obliga a que todo lo que entre esté en el mismo sistema, y eso es lo que evita que los cálculos de área den números sin sentido.

### Nombres de columna prohibidos

Hay palabras reservadas de SQL que no se pueden usar como nombre de columna sin complicarse. Las que más aparecen en capas vectoriales:

`count`, `order`, `group`, `user`, `table`, `column`, `select`, `from`, `where`, `check`, `end`, `all`, `any`, `case`, `default`, `limit`, `offset`, `union`, `desc`, `asc`

Si la capa de origen trae alguna, hay que renombrarla al definir la tabla. En la implementación real, el campo `count` del archivo pasó a llamarse `conteo`.

### Verificación

Al final del archivo hay una consulta que debe devolver una fila con el EPSG elegido. Si devuelve otro número o no devuelve nada, algo quedó mal y conviene resolverlo antes de cargar datos.

**No seguir de largo hasta el final del archivo.** La restricción de validez geométrica y los usuarios se crean *después* de cargar los datos, y están en los archivos 02 y 03. Crearlos antes hace que la carga pelee contra ellos.

---

## Paso 3 — Preparar y cargar la capa

**¿Cambia según el caso?** **Sí.** El procedimiento general es el mismo, pero cada formato de origen trae sus propias trampas.

Archivo: **`plantillas/02_carga.sql`**

### Qué cambia según el formato de origen

| Formato | Qué tener en cuenta |
| --- | --- |
| **GeoPackage (.gpkg)** | El caso más limpio. Trae su sistema de coordenadas declarado. Puede contener varias capas: hay que elegir cuál. |
| **GeoJSON** | Casi siempre viene en WGS84 (EPSG:4326), aunque no lo diga. Suele mezclar geometrías simples y multiparte — ver la trampa de abajo. |
| **Shapefile (.shp)** | **Nombres de campo recortados a 10 caracteres** (`priority_cat` llega como `priority_c`). Problemas de tildes: hay que forzar UTF-8. Son cuatro archivos que viajan juntos: `.shp`, `.shx`, `.dbf`, `.prj`. |

### La trampa de las geometrías mezcladas

Esto apareció en la implementación real y cuesta una tarde si no se sabe.

Si la capa mezcla polígonos simples y multiparte, QGIS mira el primer objeto, crea la columna como `Polygon`, y al llegar al primer multiparte la base lo rechaza con:

`Geometry type (MultiPolygon) does not match column type (Polygon)`

La importación se aborta completa — no quedan datos a medias.

**La solución**, antes de importar: *Procesos → Caja de herramientas* (`Ctrl+Alt+T`), buscar `multiparte` y ejecutar **«Promover a multiparte»** sobre la capa. Cuidado de no elegir «De multiparte a partes simples», que es la operación inversa. Se importa la capa resultante.

Es muy común en salidas de procesamiento ráster y de detección automática.

### La importación en QGIS

Menú **Base de datos → Administrador de BBDD**. En el árbol izquierdo: *PostGIS → la conexión → el esquema*. Botón **Importar capa/archivo**.

| Campo | Valor |
| --- | --- |
| Entrada | la capa (ya promovida a multiparte, si hizo falta) |
| Esquema | el esquema de trabajo |
| Tabla | `carga_temporal` — **escribirlo a mano** |
| Clave primaria | **desmarcada** |
| Columna de geometría | marcada, `geom` |
| SRID de origen | marcada, el de la capa |
| SRID de destino | marcada, **el EPSG elegido** |
| Codificación | marcada, `UTF-8` |
| Crear índice espacial | marcada |

Las etiquetas exactas varían entre versiones de QGIS. Lo que importa son las tres decisiones de abajo.

### Las tres cosas que hay que acertar

**1. Hay que marcar las DOS casillas de SRID.** Marcar solo la de origen no reproyecta nada. Si el destino queda igual al origen, la carga después falla porque la tabla exige otro sistema.

**2. «Clave primaria» va desmarcada.** Si se marca, QGIS crea una columna `id` que puede chocar con un campo `id` que ya traiga la capa.

**3. La tabla se llama `carga_temporal`, escrito a mano.** El desplegable ofrece la tabla definitiva; elegirla salta la reproyección y la asignación del reparto.

### Por qué una tabla de paso

Importar directo a la tabla definitiva parece más corto, pero obliga a que nombres y tipos coincidan exactamente, y no deja lugar para asignar el reparto ni reparar geometrías. La tabla de paso desacopla las dos cosas: QGIS escribe lo que trae, y el `INSERT` del archivo 02 decide cómo entra. Es un paso más que ahorra varias vueltas.

### Verificar antes de seguir

El archivo 02 trae cinco verificaciones obligatorias. **La quinta es la más importante**: compara el área total calculada con la conocida de la capa. Si da un número absurdo, la reproyección no se aplicó y hay que rehacer la importación. Es la que más errores atrapa.

---

## Paso 4 — Usuarios y control de acceso

**¿Cambia según el caso?** **Sí**, según cuántas personas van a editar. La estructura se repite: una línea y una política por persona.

Archivo: **`plantillas/03_usuarios_y_acceso.sql`**

### Qué logra este paso

Después de ejecutarlo:

- Todas las personas **ven** la capa completa, con el contexto geográfico entero.
- Cada una solo puede **editar** los registros de su parte asignada.
- Intentar editar fuera de su parte es rechazado **por la base**, no por disciplina ni por acuerdo verbal.
- Nadie puede reetiquetar un registro para pasárselo a otra persona.

Un acuerdo verbal se rompe por error, por cansancio o por un clic equivocado, y cuando se rompe nadie se entera hasta mucho después. La regla en la base se rompe con un mensaje de error en el momento. Para un entregable que alguien va a auditar, esa diferencia es la que vale.

### Cómo escalar a N personas

Tres cosas se repiten por cada persona:

1. Una línea `CREATE ROLE`
2. Su nombre agregado a las cuatro sentencias `GRANT`
3. Una política de escritura propia

La plantilla viene con tres personas como ejemplo. Para dos, se borran las líneas sobrantes; para cinco, se duplican los bloques.

**Si una persona tiene varias partes asignadas**, su política usa `IN` en lugar de igualdad:

`USING (provincia IN ('Limón','Heredia'))`

### La regla que no se negocia

**Nunca compartir un usuario entre dos personas.** El campo `editado_por` guarda el usuario de la conexión. Si dos personas entran con el mismo, ese campo deja de significar algo y se pierde toda la trazabilidad: ya no se puede responder quién tocó qué. Crear un usuario más no cuesta nada.

### Las contraseñas

16 caracteres o más, distintas entre sí, sin tildes, sin eñes y sin espacios. **Anotarlas antes de ejecutar**: PostgreSQL no las muestra después.

### Una distinción que confunde: `USING` y `WITH CHECK`

Ambas aparecen en cada política y hacen cosas distintas:

- `USING` decide qué filas **existentes** puede tocar la persona.
- `WITH CHECK` decide cómo pueden **quedar** las filas después de tocarlas.

Hacen falta las dos. Sin `WITH CHECK`, alguien podría cambiar el valor de reparto de una fila suya y regalársela a otra persona — o al revés, apropiarse de una ajena cambiándole la etiqueta.

### El propietario ignora las políticas

Esto es deliberado y tiene una consecuencia práctica importante.

El rol dueño de la tabla (`neondb_owner` en Neon) **no** está sujeto al control de acceso. Sirve como vía administrativa para corregir una asignación mal hecha sin desarmar nada.

Pero significa que **probar el sistema conectado como propietario no prueba nada**: el propietario puede editar todo. La prueba del Paso 6 se hace obligatoriamente con los usuarios de edición.

---

## Paso 5 — Conectar QGIS y repartir credenciales

**¿Cambia según el caso?** No. Este procedimiento es idéntico siempre; solo cambian los valores.

Cada persona lo hace en su propia máquina, con su propio usuario. Toma menos de cinco minutos y no requiere instalar nada.

### Crear la conexión

En el panel **Navegador** de QGIS: clic derecho en **PostgreSQL** → **Nueva conexión**. Si no se ve ese panel: *Ver → Paneles → Navegador*.

También sirve *Capa → Administrador de fuentes de datos* (`Ctrl+L`) → PostgreSQL → **Nueva**.

| Campo | Valor |
| --- | --- |
| Nombre | el que se quiera |
| **Servicio** | **dejar vacío** |
| **Anfitrión** | el host de Neon, **sin `-pooler`** |
| Puerto | `5432` |
| Base de datos | `neondb` |
| Modo SSL | `requerir` |
| Session ROLE | dejar vacío |
| Usuario | el usuario de esa persona |
| Contraseña | la suya, marcando las dos casillas de **Guardar** |

Marcar también **«Permitir guardar/cargar proyectos de QGIS en la base de datos»**. Sirve para que todas abran el mismo proyecto con la misma simbología.

**Probar conexión** debe dar verde → **Aceptar**.

Para cargar la capa: *Capa → Administrador de fuentes de datos → PostgreSQL* → la conexión → el esquema → la tabla → **Añadir**.

### Los dos errores que se cometen siempre

**El host va en «Anfitrión», no en «Servicio».** El campo *Servicio* es para nombres definidos en un archivo `pg_service.conf` local. Poner el host ahí hace que QGIS lo busque en ese archivo, no lo encuentre y falle con «Falló la conexión» sin más explicación.

**La contraseña termina antes de la arroba.** Al copiarla de la cadena de conexión es fácil pasarse e incluir `@ep`, que ya es el host. El síntoma es `password authentication failed`.

### Configuración del proyecto (en todas las máquinas)

Tres ajustes que evitan la mayoría de los problemas posteriores:

1. **Transacciones automáticas.** *Proyecto → Propiedades → Fuentes de datos* → marcar **Grupos de transacciones automáticas**. Hace que las ediciones vayan como transacciones reales contra la base. Es la diferencia entre perder o no perder trabajo si se cae la conexión.
2. **Autorrefresco.** Clic derecho en la capa → *Propiedades → Representación* → **Actualizar capa a intervalos** → `60` segundos. Así se ven los cambios de las demás sin recargar a mano.
3. **Filtro de trabajo.** Clic derecho en la capa → *Filtrar* → la condición de su parte, p. ej. `"provincia" = 'Limón'`. Para ver el panorama completo, se borra el filtro.

### Cómo repartir las credenciales

**La contraseña va por un canal distinto al resto de los datos.** Los parámetros de conexión por correo, la contraseña por mensaje o llamada. Así, quien intercepte uno de los dos no tiene nada utilizable.

Nunca enviar credenciales en capturas de pantalla: quedan en el historial de quien las recibe y es fácil olvidar que están ahí.

---

## Paso 6 — Verificar que el reparto funciona

**¿Cambia según el caso?** No. Las mismas cuatro pruebas, con los valores propios.

No saltarse este paso. Es la diferencia entre creer que el sistema funciona y saberlo.

### Antes de probar: conectarse con el usuario de edición

Si quien montó la base sigue conectada como `neondb_owner`, **la prueba no sirve**: el propietario ignora el control de acceso y puede editar todo. Hay que editar la conexión de QGIS y cambiarla al usuario de edición correspondiente.

Conviene conservar la conexión del propietario aparte, con otro nombre, para tareas administrativas.

### Las cuatro pruebas

**1. Cada persona edita lo suyo.** Seleccionar un registro de su parte, activar edición, cambiar `estado_revision` a `en_proceso`, guardar. Debe funcionar sin error.

**2. El control de acceso bloquea lo ajeno.** Intentar editar un registro de la parte de otra persona y guardar. **Debe fallar**, con un mensaje que menciona `row-level security policy`. Ese error es el éxito de la prueba, no un problema.

**3. Los cambios se ven entre personas.** Esperar el refresco o pulsar `F5`. Abrir la tabla de atributos y buscar el registro que editó la otra persona. Debe verse el cambio, con su usuario en `editado_por` y la hora.

**4. El panel refleja la actividad.** Ejecutar `SELECT * FROM esquema.v_seguimiento;` y comprobar que aparecen las dos partes con sus respectivas personas.

### Si no hay dos personas disponibles para probar

El archivo `plantillas/05_verificaciones.sql`, sección E, trae una prueba que se hace desde el SQL Editor sin montar QGIS en dos máquinas. Usa `SET ROLE` para que la sesión actúe como otro usuario, dentro de una transacción que se deshace al final.

Hay que ejecutar las cuatro líneas juntas: si se ejecuta solo el `UPDATE` sin el `SET ROLE`, correría como propietario y no probaría nada.

---

## Seguimiento, rutina y respaldos

**¿Cambia según el caso?** Solo los nombres.

Archivo: **`plantillas/04_panel_seguimiento.sql`**. Se ejecuta una vez y crea cuatro vistas; después el seguimiento es una consulta de una línea.

### Las tres preguntas que responde el panel

| Pregunta | Consulta |
| --- | --- |
| ¿Cuánto lleva cada persona? | `SELECT * FROM esquema.v_seguimiento;` |
| ¿A qué ritmo trabajan? | `SELECT * FROM esquema.v_actividad_diaria;` |
| ¿Qué se tocó último? | `SELECT * FROM esquema.v_ultimos_movimientos;` |

Conviene pegarlas juntas en el SQL Editor de Neon y guardarlas con **Save** bajo el nombre «Panel de seguimiento». Quedan en la pestaña *Saved* y se abren con un clic.

### Cómo distingue el trabajo real de la carga inicial

Al cargar, el trigger dejó `fecha_creacion = fecha_edicion` en todos los registros. Por eso la condición `fecha_edicion > fecha_creacion` identifica exactamente lo que alguien tocó después de la carga. Sin ese criterio, el panel mostraría 100% de avance desde el primer día.

### ¿Está conectada alguien ahora?

Hay una consulta para eso en el archivo 04, pero conviene saber qué responde y qué no: **`pg_stat_activity` solo muestra conexiones activas en este instante**. Si alguien trabajó toda la mañana y cerró QGIS, no aparece. Para saber si trabajó, el panel; para saber si está adentro ahora mismo, esa consulta.

### Rutina diaria

- Guardar cambios cada 15 o 20 minutos, no al final del día. Si se cae el internet a mitad de una edición sin guardar, esa transacción se revierte.
- Marcar el avance en `estado_revision`. Es lo que permite saber dónde va el trabajo sin preguntar.
- **No hay paso de consolidación.** No hay versiones que unir. Al final del día el trabajo de todas está en la misma tabla.

### Respaldo

Este es el punto que más conviene no saltarse, por lo dicho sobre la ventana de 6 horas del plan gratuito.

**Con PostgreSQL instalado**, al terminar cada jornada:

```
pg_dump "postgresql://USUARIO:CLAVE@HOST/BASE?sslmode=require" --schema=ESQUEMA --format=custom --file="respaldo_AAAAMMDD.dump"
```

Usar el host **sin** `-pooler`: `pg_dump` falla contra el pooler.

**Sin PostgreSQL instalado**: exportar desde QGIS. Clic derecho en la capa → *Exportar → Guardar objetos como* → GeoPackage, con la fecha en el nombre.

En ambos casos, conservar los últimos diez.

### Limitación conocida del diseño

El panel registra **la última edición** de cada registro, no el historial completo. Si alguien cambia un estado hoy y lo vuelve a cambiar mañana, el primer cambio se pierde.

Para la mayoría de los casos alcanza: responde quién, cuánto y cuándo. Si el entregable exige historial completo — qué valor tenía antes y cuál tiene ahora, en cada cambio — hace falta una tabla de bitácora con su propio trigger. No viene en este paquete, y se agrega sin tocar nada de lo existente.

---

## Problemas frecuentes

Los marcados con ● aparecieron realmente durante la implementación que originó esta guía.

| Síntoma | Causa | Solución |
| --- | --- | --- |
| ● «Falló la conexión» al probar, sin más detalle | El host se puso en el campo *Servicio* en vez de *Anfitrión* | Vaciar *Servicio* y pegar el host en *Anfitrión* |
| ● `password authentication failed` | Al copiar la contraseña se incluyeron el `@` y las primeras letras del host | La contraseña termina antes de la arroba |
| ● `Geometry type (MultiPolygon) does not match column type (Polygon)` | La capa mezcla geometrías simples y multiparte | Ejecutar «Promover a multiparte» antes de importar, y borrar la tabla de paso que quedó |
| ● No aparece la opción PostgreSQL en la ventana | Se abrió el *Administrador de BBDD* en vez del *Administrador de fuentes de datos* | Son ventanas distintas con nombres parecidos. La conexión se crea en la segunda |
| `Connection timed out` | La red bloquea la salida por el puerto 5432, o el host está mal copiado | Revisar el host carácter por carácter. Si solo falla en la red institucional, pedir a TI que habilite la salida a ese host |
| La capa carga pero no deja activar la edición | QGIS no detectó la llave primaria | Verificar que la columna de clave primaria sea el entero. Quitar la capa y volver a añadirla eligiéndola |
| `new row violates row-level security policy` | Se intentó editar un registro de otra persona | Es el control de acceso funcionando. Si el registro está mal clasificado, lo corrige quien administra la base |
| No se crean registros nuevos, solo se editan los existentes | Falta el permiso sobre la secuencia | Ejecutar el `GRANT USAGE, SELECT ON SEQUENCE` del archivo 03 |
| El área total da un número absurdo | La reproyección no se aplicó al importar | Rehacer la importación marcando **las dos** casillas de SRID |
| No se ven los cambios de las demás | El autorrefresco no está activo | `F5`, o activar *Actualizar capa a intervalos* |
| QGIS se pone lento al navegar | Se carga toda la capa en cada redibujado | Aplicar el filtro por la parte asignada. Verificar que el índice espacial existe |
| La edición no se guarda y no aparece error | Las transacciones automáticas están desactivadas | Activarlas en las propiedades del proyecto |
| `pg_dump` falla o se corta | Se está usando el host con `-pooler` | Usar el host directo, sin `-pooler` |
| Todo funciona pero nadie queda bloqueado nunca | Se está probando conectado como propietario | El propietario ignora el control de acceso. Probar con los usuarios de edición |

### Qué tener a mano antes de pedir ayuda

Tres datos hacen que el diagnóstico sea inmediato: **el mensaje de error exacto**, **qué usuario estaba conectado** y **qué operación se intentaba**. Sin eso, se adivina.

---

## Resumen: qué cambia según el caso

Tabla de consulta rápida para la próxima vez que haya que montar esto.

| Paso | ¿Cambia? | Qué hay que decidir o ajustar |
| --- | --- | --- |
| **1. Crear la base en Neon** | **No** | Nada. Mismo procedimiento siempre |
| **2. Crear la estructura** | **Sí, mucho** | Esquema, tabla, columna de reparto y sus valores, todas las columnas de atributos con su tipo, tipo de geometría, código EPSG |
| **3. Cargar la capa** | **Sí** | Formato de origen, SRC de origen, mapeo de columnas, expresión que asigna el reparto |
| **4. Usuarios y acceso** | **Sí** | Un usuario y una política por persona |
| **5. Conectar QGIS** | **No** | Mismo procedimiento; solo cambian los valores |
| **6. Verificar el reparto** | **No** | Mismas cuatro pruebas |
| **7. Panel de seguimiento** | Solo nombres | Esquema, tabla, columna de reparto, usuarios, zona horaria |
| **8. Respaldos** | **No** | Mismo procedimiento |

### Si cambia el número de personas

Solo se toca el archivo 03, en tres lugares: la cantidad de `CREATE ROLE`, la lista de usuarios en las cuatro sentencias `GRANT`, y una política de escritura por persona. Nada más en todo el sistema depende de cuántas sean.

### Si cambia la forma de repartir el trabajo

Se toca el nombre de la columna de reparto y sus valores posibles — aparece en los archivos 01, 02, 03 y 04. Es la decisión de diseño del sistema, y conviene pensarla antes de escribir nada.

### Si cambia la capa pero el reparto se mantiene

Se reescriben las columnas de atributos del archivo 01 y el mapeo del 02. Los archivos 03, 04 y 05 siguen igual salvo los nombres de esquema y tabla.

### Lo que nunca cambia

Cuatro decisiones de diseño valen para todos los casos, y saltarse cualquiera produce fallas confusas más adelante:

1. **Llave primaria entera única.** QGIS la necesita para editar.
2. **La columna de reparto va `NOT NULL` con `CHECK`.** Un nulo deja un registro huérfano.
3. **La geometría se declara con tipo y EPSG explícitos.** Es lo que evita áreas sin sentido.
4. **Un usuario por persona, nunca compartido.** Es lo que sostiene la trazabilidad.

### Dónde conviene dedicar el tiempo

El montaje completo toma alrededor de una hora la primera vez y unos veinte minutos las siguientes. La parte que más rinde pensar con calma es la **decisión 2** — cómo se reparte el trabajo. Todo lo demás es mecánico y se corrige fácil; esa decisión, mal tomada, obliga a reasignar registros a mano durante todo el proyecto.
