# Registro de decisiones

Formato: fecha · decisión · contexto · alternativas descartadas · consecuencias.
Las entradas no se borran. Una decisión revertida se reemplaza con una entrada nueva.

---

## D-01 · 2026-10-08 · PostGIS gestionado en nube en lugar de PostgreSQL en estación institucional

**Contexto.** Se necesitaba edición compartida entre dos personas desde sus casas, sin
permisos de TI. Exponer un PostgreSQL de escritorio requiere abrir el puerto 5432 en el
firewall institucional, IP fija y equipo encendido 24/7.

**Alternativas descartadas.** PostgreSQL local expuesto (inviable sin TI; estación no es
servidor). Túneles inversos (evasión del perímetro: no aceptable). GeoPackage en carpeta
sincronizada (corrupción con edición concurrente). Mergin Maps (sin plan gratuito general).
QGIS Cloud Free (excluye uso gubernamental). QFieldCloud Community (sin colaboración privada).

**Consecuencias.** Solo tráfico saliente; cero instalaciones; datos del piloto deben ser
públicos; respaldo propio obligatorio (ventana de restauración de 6 h).

## D-02 · 2026-10-08 · Neon sobre Supabase

**Contexto.** Ambos ofrecen PostGIS en plan gratuito.
**Descartado.** Supabase pausa proyectos gratuitos tras 7 días sin actividad y requiere
reactivación manual; conexión directa solo IPv6 en plan gratuito.
**Consecuencias.** Neon suspende cómputo pero revive solo. Apagar *connection pooling* para
QGIS y `pg_dump`.

## D-03 · 2026-10-08 · Reparto del trabajo impuesto por Row Level Security

**Contexto.** Dos personas con partes disjuntas. Un acuerdo verbal se rompe sin aviso.
**Descartado.** Disciplina sin control; tablas separadas por persona (rompe la capa única).
**Consecuencias.** Un rol por persona, nunca compartido. Políticas con USING y WITH CHECK.
El propietario omite RLS: las pruebas se hacen con roles de edición.

## D-04 · 2026-10-08 · Llave primaria entera IDENTITY; identificador de origen aparte

**Contexto.** QGIS requiere llave entera única para editar PostGIS de forma confiable. El
origen traía identificador de texto.
**Consecuencias.** `id bigint IDENTITY`; `id_origen text`.

## D-05 · 2026-10-08 · Carga por tabla de paso, no importación directa

**Contexto.** La importación directa obliga a coincidencia exacta de nombres/tipos y no
permite asignar el reparto ni reparar geometrías.
**Consecuencias.** `carga_temporal` → `INSERT ... SELECT` con `ST_Multi(ST_MakeValid())` y
expresión de reparto. Restricción de validez y roles se crean después de cargar.

## D-06 · 2026-10-08 · Reparto por lote de UPM (A/B) en el piloto, no por provincia

**Contexto.** El archivo de prueba es de un solo distrito; la capa definitiva de
asentamientos se reparte por provincia. El mecanismo es el mismo; cambia la columna.
**Consecuencias.** Lote A = UPM 001,002,003,006,010 (709); Lote B = resto (723).

## D-07 · 2026-10-13 · Capa de visita como tabla de puntos separada

**Contexto.** El formulario de campo vive en el centroide de la finca.
**Descartado.** Agregar campos al polígono (riesgo de mover vértices desde el celular;
peso excesivo en QField; impide revisitas).
**Consecuencias.** `mgn.finca_visita` con FK a `deteccion_cambio`, hereda `lote` para RLS.
`UNIQUE(finca_id)` en el piloto; se retira para revisitas.

## D-08 · 2026-10-13 · `ST_PointOnSurface` en lugar de `ST_Centroid`

**Contexto.** El centroide puede caer fuera en polígonos cóncavos o con islas.
**Consecuencias.** Punto garantizado dentro. Verificado: 1.432/1.432 dentro de su polígono.

## D-09 · 2026-10-13 · Tablero como HTML estático generado por un script, leído con rol de solo lectura

**Contexto.** Un supervisor debe consultar el avance de noche desde el celular, sin
equipos del equipo encendidos. El HTML no puede contener credenciales.
**Descartado.** Página que consulta la base desde el navegador (expone credenciales).
Metabase/Grafana para el piloto (requieren servidor; opción válida para producción).
**Consecuencias.** Rol `tablero_lectura` con acceso solo a `v_tab_*`. Generador en Python.
Regeneración en GitHub Actions cada 30 min con secreto cifrado; GitHub Pages público
(aceptable solo con datos públicos). Producción: mismo script en cron institucional.

## D-10 · 2026-10-13 · Identidad en campo por atributo (`@cloud_username`), RLS solo para escritorio

**Contexto.** QFieldCloud en modo offline aplica deltas con una cuenta de servicio única;
`current_user` no distingue censistas. Direct Data Access preservaría RLS pero exige señal.
**Consecuencias.** Columna `encuestador` con valor por defecto `@cloud_username`. En campo,
el reparto se garantiza por proyecto/filtro por equipo, no por muro de base de datos.
Debe declararse así en los requerimientos para TI.

## D-11 · 2026-10-13 · Claude Code como ejecutor; Claude web como arquitecto y guía de interfaz

**Contexto.** El flujo por capturas de pantalla y copia manual de SQL funciona pero es
lento y deja la trazabilidad en la conversación, no en archivos.
**Consecuencias.** Todo lo ejecutable (SQL, Python, git, capturas, Actions) lo hace Claude
Code en `C:\PROYECTO_NEON_CENSO` con cuatro agentes y bitácora por sesión. QGIS/QField los
opera la persona con instrucciones exactas. Claude web conserva arquitectura, decisiones,
documentos para TI y acompañamiento de interfaz. La fuente de verdad son los archivos del
repositorio, no las conversaciones.

## D-12 · 2026-10-15 · Cliente psql de PostgreSQL 18 en el PATH de usuario; Python con `py`

**Contexto.** En la estación de trabajo, `psql` no respondía: no había ninguna entrada de
PostgreSQL en el PATH. Existen dos clientes en disco: `C:\Program Files\PostgreSQL\18\bin`
(18.6) y `C:\Program Files\QGIS 3.34.11\bin` (16.2). No hay instalación 17 (CLAUDE.md la
citaba por error). `python` lo intercepta el alias de Microsoft Store; `py` (lanzador)
resuelve a Python 3.13.5.
**Decisión.** Agregar `C:\Program Files\PostgreSQL\18\bin` al final del PATH de usuario
(sin permisos de administrador), con un comando idempotente que no duplica la entrada ni
falla con PATH vacío. El cliente 18.6 se usa contra el servidor Neon 16/17; psql es
compatible hacia atrás con servidores de versiones anteriores.
**Descartado.** Invocar psql por ruta completa en cada comando (rutas con espacios, más
propensas a error y no portables entre scripts, agentes y guía). psql de QGIS (cliente más
antiguo, 16.2, y la ruta cambia con cada actualización de QGIS). Solo `~/.bashrc` (no
alcanza a PowerShell ni queda documentado fuera del perfil personal).
**Consecuencias.** El cambio surte efecto al reiniciar Claude Code y las terminales. No se
desactiva el alias de la Store: todo comando Python del proyecto (scripts, pip, playwright,
guía, workflow local) se escribe con `py`. En GitHub Actions y en producción el ejecutable
sigue siendo `python`; la convención `py` aplica solo a esta estación Windows.

## D-13 · 2026-10-15 · Servidor Neon es PostgreSQL 18.6; respaldo con pg_dump en lugar de rama; clave de rol por variable de psql

**Contexto.** `SELECT version()` devolvió PostgreSQL 18.6, no 16/17 como asumía D-12. D-12
no se edita; esta entrada corrige el dato. Sin MCP de Neon no se puede crear una rama desde
Claude Code. El script `sql/06_centroides_visita.sql` traía la clave del rol de tablero como
marcador dentro del archivo.
**Decisión.** Cliente y servidor 18.6. Antes de cambios de esquema sin rama disponible:
`pg_dump -Fc -n mgn` a `respaldos/` (ignorado por `*.dump`) y ejecución en una sola
transacción (`-1 -v ON_ERROR_STOP=1`). Claves de roles nuevos por variable de psql
(`:'var'`), nunca en el archivo. Pruebas de roles con su propia conexión, no con `SET ROLE`.
**Descartado.** Rama de Neon creada a mano (posible; la persona puede elegirla en el
futuro). `pg_dump --schema-only` (no permite restaurar datos). `SET ROLE` (en PG16+ el
creador de un rol no puede asumirlo sin concesión explícita).
**Consecuencias.** La clave puede quedar en registros del servidor si estos registran DDL, y
en la lista de procesos local. Para producción, requerimiento TI: crear el rol sin clave y
fijarla con `\password` (hash SCRAM calculado en el cliente).

## D-14 · 2026-10-15 · Tablero: lectura solo con `tablero_lectura`, salida escapada, sin texto libre ni posición GNSS

**Contexto.** La revisión independiente de la sesión 02 encontró que `generar_tablero.py`
leía `DATABASE_URL` (propietario en el `.env` local), que `persona` entraba sin escapar en el
popup del mapa y que el JSON dentro de `<script>` no escapaba `</`. Además, las vistas
exponían `observaciones` (texto libre) en un tablero que D-09 prevé público.
**Decisión.** `generar_tablero.py` y el workflow leen solo `DATABASE_URL_TABLERO` (el secreto
de Actions se llama igual) y el generador se detiene si `current_user` no es
`tablero_lectura`. En el HTML, `persona` y demás datos se escapan en el popup y todo JSON
dentro de `<script>` escapa `<` como la secuencia JSON `\u003c`. Las vistas `v_tab_*` no exponen
`observaciones` ni `posicion_registro`. `persona` solo como nombre de usuario de rol
(`@cloud_username` en campo, rol de base en escritorio), nunca nombre real. `cuando` con año
(`DD/MM/AAAA HH24:MI`). Aplicación en la base: `sql/07_ajustes_vistas_tablero.sql`.
**Descartado.** Mantener `observaciones` ocultas solo por CSS en pantallas pequeñas (siguen en
el HTML publicado). Dejar en el popup el texto sin escapar (un rol de edición podría inyectar
código en la página pública).
**Consecuencias.** Requerimientos para TI (no se aplican en el piloto): vistas con
`security_invoker = true` y políticas para el rol del tablero cuando la lectura deba
restringirse; coherencia `lote` ↔ `finca_id` (FK compuesta o trigger) al retirar
`UNIQUE(finca_id)`. Registrados en `docs/requerimientos_ti/insumos_piloto.md`.

## D-15 · 2026-10-15 · Estados de visita, fórmula de avance y movimientos (PROVISIONAL)

**Contexto.** Los valores de `estado_visita`, la fórmula de `avance_pct` y el `LIMIT 25` de
`v_tab_movimientos` venían del script 06 sin decisión registrada. El cuestionario real del
censo todavía no está definido.
**Decisión (provisional hasta tener el cuestionario real).** Cinco estados: `pendiente`,
`visitada`, `no_localizada`, `rechazo`, `revisita`. `avance_pct` cuenta solo estados
terminales (`visitada`, `no_localizada`, `rechazo`); `revisita` es incidencia, no avance.
`v_tab_movimientos` muestra los últimos 25.
**Descartado.** Contar todo estado distinto de `pendiente` como avance (versión del 06:
inflaba el avance con fincas que hay que volver a visitar).
**Consecuencias.** Al llegar el cuestionario real se revisan estados, fórmula y límite, con
una entrada nueva que reemplace a esta.

## D-16 · 2026-10-15 · `fecha_visita`: la fija el trigger solo si llega NULL

**Contexto.** En la sesión 02, las 15 visitas del lote A guardadas por lote desde QGIS
quedaron con la misma `fecha_visita`: `trg_fecha_visita_auto` usa `now()`, que es la hora de
la transacción de guardado, no la de cada visita.
**Decisión.** El trigger asigna `fecha_visita` solo cuando llega NULL. En QField la pone el
formulario con `now()` del dispositivo (hora real de la visita). Desde QGIS escritorio queda la
hora de guardado y así se declara. Se implementa en S05
(`sql/09`); hoy solo se registra.
**Descartado.** Mantener la sobrescritura incondicional por el trigger (pierde la hora real
en campo con edición sin señal y sincronización posterior).
**Consecuencias.** La hora de visita confiable es la de QField; la de escritorio es hora de guardado.

## D-17 · 2026-10-15 · `NEON.qgz` fuera del repositorio hasta usar pg_service

**Contexto.** El proyecto QGIS contiene el host de Neon y QGIS puede guardar la clave en
texto plano dentro del `.qgz`. El repositorio pasa a ser público (GitHub Pages, S03).
**Decisión.** `NEON.qgz` sale del índice y de todo el historial (`git filter-repo --path
NEON.qgz --invert-paths --force`, confirmado por la persona); `*.qgz` y `*.qgs` en
`.gitignore`. El archivo sigue solo en la máquina local. Vuelve al repositorio en S05, cuando
la conexión use `pg_service` (sin host ni clave en el proyecto).
**Descartado.** Versionarlo tal cual (expone el host en un repositorio público). Quitarlo
solo del último commit (seguiría en el historial).
**Consecuencias.** Los hashes de todos los commits anteriores cambiaron (respaldo previo en
`respaldos/2026-10-15_repo_antes_filter_repo.bundle`, ignorado por git). Hasta S05, quien
replique arma su proyecto QGIS con la guía.

## D-18 · 2026-10-15 · Capa UGM del SNIT en el esquema `sim` como proxy de las fincas

**Contexto.** El documento para TI necesita cifras de carga, tamaño, concurrencia, tablero
y paquete de campo a la escala de producción (~90.000 fincas). El piloto solo tiene 1.432
polígonos, y las fincas del censo no están disponibles.
**Decisión.** Usar la capa pública UGM del SNIT (`datos_prueba/ugm/ugm.gpkg`, 50.794
polígonos, EPSG:8908, reproyectada a 5367) como proxy, cargada con `ogr2ogr` en un esquema
aparte, `sim` (`sim.ugm`, `sim.finca_visita`, `sim.v_tab_*`), con la misma estructura que
`mgn`. La columna de reparto `lote` es el código de provincia (`'1'`…`'7'`). `sim` no tiene
RLS ni roles de edición propios; `tablero_lectura` solo tiene `USAGE` sobre el esquema y
`SELECT` sobre las vistas. Nada de `sim` se publica.
**Descartado.** Generar polígonos sintéticos (no reflejan geometría real). Duplicar los
1.432 polígonos de `mgn` (sin variedad geométrica, y repetidos). Cargar en `mgn`, que
mezclaría la simulación con el piloto.
**Consecuencias.** La capa tiene 50.794 objetos, el 56 % de 90.000: las cifras a 90.000
son extrapolaciones, no mediciones. Las UGM no son fincas: el proxy sirve para carga,
tamaño, concurrencia y tablero, no para tiempos de visita ni cobertura (ver
`docs/requerimientos_ti/evidencia_escala.md`). `sim` ocupa 208 MB de la base (225 MB en
total) y se conserva hasta S06; su borrado se decide después de la presentación.

## D-19 · 2026-10-15 · Un proyecto QFieldCloud por lote, con el rol de su lote en el secreto pg_service

**Contexto.** D-10 supuso que en campo el RLS no protege, porque QFieldCloud aplica los
cambios con una cuenta única. Hipótesis (sin verificar hasta la prueba de campo): QFieldCloud
aplica los cambios con la conexión que define el proyecto; si esa conexión es un servicio
libpq cuyo rol es el de edición del lote, el RLS sigue actuando sobre lo que se sincroniza.
Se comprueba con `editado_por = edit_lote_a` tras la primera sincronización
(`docs/guia/qfield_campo.md`, paso 6).
**Decisión.** Un proyecto QFieldCloud por lote. Cada proyecto usa solo
`service='neon_lote_<l>'` (sin host, usuario ni clave en el `.qgs`), y el servicio se carga en
QFieldCloud como secreto `pg_service` con el rol de ese lote (`edit_lote_a`, `edit_lote_b`).
El RLS protege por equipo también en campo. La identidad individual sigue llegando por
atributo: `encuestador = @cloud_username` (D-10). En el piloto solo se prepara el lote A
(`campo/NEON_campo_lote_A.qgs`); el lote B se documenta como réplica
(`docs/guia/qfield_campo.md`).
**Descartado.** Un solo proyecto con el rol propietario o con un rol común (el muro de la base
desaparece en campo; queda solo el filtro del proyecto). Guardar host, usuario y clave en el
proyecto (no se puede versionar en un repositorio público, D-17).
**Consecuencias.** Mejora D-10, no la edita: el reparto en campo pasa a ser por equipo con muro
de base; dentro de un equipo, la persona sigue siendo un atributo. `NEON_campo_lote_A.qgs`
vuelve a entrar al repositorio (excepción `!campo/*.qgs`). `NEON.qgz` sigue fuera: esto
reemplaza el punto de D-17 que preveía su regreso en S05; el proyecto versionado es el de
campo, construido por script.
Como las filas de `finca_visita` ya existen y en campo se actualizan, los valores por defecto
del formulario llevan «aplicar al actualizar». `fecha_visita` se llena con `now()` del
dispositivo solo si está vacía y el estado deja de ser `pendiente`: nunca se sobrescribe
(D-16). `encuestador` y `precision_gnss_m` sí se sobrescriben en cada edición desde QField
(solo conservan el valor si la variable viene vacía, como en QGIS escritorio): una revisita o
una edición de otra persona deja el `encuestador` de la última edición con la fecha de la
primera. Comportamiento conocido del piloto, pendiente de decisión de la persona.
`deteccion_cambio` va como «offline editing» más capa de solo lectura: para una capa PostGIS
no hay acción de copia de solo lectura, y «acceso directo» haría que el celular se conecte a
la base. Que QField aplique «aplicar al actualizar» igual que PyQGIS se comprueba en campo. El archivo de servicio por usuario en Windows es
`%APPDATA%\postgresql\.pg_service.conf` (con punto inicial; sin el punto, libpq no lo lee
sin `PGSERVICEFILE`).

## D-20 · 2026-10-15 · Corrección de la premisa de D-16: el trigger nunca sobrescribió `fecha_visita`

**Contexto.** D-16 atribuyó las 15 visitas del lote A con la misma `fecha_visita` (sesión 02)
a una sobrescritura incondicional del trigger, y descartó «mantenerla». En S05, antes de
aplicar `sql/09`, la definición viva (`pg_get_functiondef`) y `sql/06` muestran que
`mgn.fn_fecha_visita_auto` siempre asignó `now()` solo con `NEW.fecha_visita IS NULL` (y
estado distinto de `pendiente`).
**Corrección.** La causa real: QGIS escritorio envía `fecha_visita` NULL y `now()` es la hora
de la transacción de guardado, la misma para todo lo guardado a la vez. La decisión de D-16
(asignar solo si llega NULL) ya se cumplía. `sql/09` la reafirma de forma idempotente y la
documenta con `COMMENT ON FUNCTION`; no cambia el comportamiento. La hora real de la visita
la aporta el formulario de QField (D-19).
**Consecuencias.** D-16 sigue vigente en su decisión; su contexto y su alternativa descartada
quedan corregidos por esta entrada.

## D-21 · 2026-10-15 · Piloto: `encuestador` y precisión de la última edición; `fecha_visita` de la primera visita

**Contexto.** Con un punto por finca (`UNIQUE(finca_id)`, D-07) y valores por defecto con
«aplicar al actualizar» (D-19), una revisita o una edición de otra persona reescribe
`encuestador` y `precision_gnss_m`, mientras que `fecha_visita` conserva la primera.
**Decisión.** En el piloto, `encuestador` y `precision_gnss_m` reflejan la última edición y
`fecha_visita` la primera visita con estado distinto de `pendiente`. La inconsistencia queda
declarada: una fila puede combinar la persona de la última edición con la fecha de la primera.
**Consecuencias.** En producción cada visita es una fila (retiro de `UNIQUE(finca_id)`, D-07),
con su persona, fecha y precisión propias. Requerimiento TI 8.

## D-22 · 2026-10-15 · Fase 3 dividida: hoy conexión directa por pg_service en el dispositivo; offline con QFieldCloud después

**Contexto.** Fuentes indicadas por la persona: el plan Community de QFieldCloud no admite
capas PostGIS (community.qfield.org/t/1816) y el secreto `pg_service` se usa solo en el
servidor (community.qfield.org/t/831). El flujo de D-19 (secreto `pg_service` en QFieldCloud)
no se puede probar con la cuenta disponible.
**Decisión.** La Fase 3 se divide en dos.
1. Hoy: QField con conexión directa a Neon por `pg_service` en el dispositivo, con internet y
   sin QFieldCloud. La identidad llega por el rol (`editado_por`) y el RLS se aplica en el
   celular. Paquete en `campo/paquete_movil/` (fuera del repositorio): copia de
   `NEON_campo_lote_A.qgs` y `pg_service.conf` (sin punto inicial) con el servicio
   `neon_lote_a`.
2. Lunes: solicitar al INEC una cuenta QFieldCloud de prueba que soporte PostGIS, para validar
   la edición offline.
**Descartado.** Esperar la cuenta del INEC para empezar la Fase 3 (el plazo del piloto es
2026-10-16 15:00).
**Consecuencias.** La prueba de hoy no valida la edición offline ni el flujo de D-19, que
queda pendiente de la cuenta del INEC. El dispositivo guarda la clave de `edit_lote_a`: solo
aceptable en el piloto. Requerimientos TI 9 (plan del INEC con PostGIS offline) y 10
(credenciales en el dispositivo solo con MDM en producción).

## D-23 · 2026-10-15 · Zona de sesión fijada en la base: `America/Costa_Rica`

**Contexto.** En la prueba de la sesión 05 (D-22, parte 1), las tres visitas desde QField
quedaron con `fecha_visita` 6 h atrasada. Causa: el formulario envía `now()` del dispositivo
sin zona horaria y la sesión por defecto era UTC (`SHOW timezone` con una conexión nueva de
`edit_lote_a`: `GMT`), así que la hora local de Costa Rica se guardó como UTC.
**Decisión.** La base fija la zona de sesión:
`ALTER DATABASE neondb SET timezone TO 'America/Costa_Rica'`. Las tres filas de prueba (1396,
1403, 1404) se corrigen con `fecha_visita + 6 horas` (`sql/10`, ejecutado una vez con
`edit_lote_a` para conservar `editado_por`).
**Descartado.** Confiar la zona al cliente (`PGTZ`, `options` en `pg_service.conf` o
expresión con zona en el formulario): depende de cada dispositivo y configuración, y un
cliente mal configurado vuelve a desplazar las horas sin aviso.
**Consecuencias.** Toda conexión nueva sin zona propia trabaja en `America/Costa_Rica`
(verificado: `America/Costa_Rica` con `edit_lote_a` por servicio). Las sesiones abiertas
antes del cambio conservan la zona anterior hasta reconectar. `fecha_edicion` de las tres
filas pasó a la hora de la corrección. Requerimiento TI 11.

## D-24 · 2026-10-15 · Presentación, logo y muestra fuera del repositorio público; el documento para TI sí se versiona

**Contexto.** La Fase 4 produce dos entregables: el documento de requerimientos para TI y una
presentación para la Unidad de Cartografía y los encargados del censo. La presentación usa el
logo institucional y copia el sistema visual de una presentación interna previa (la muestra),
que no es material público. El repositorio es público (S03).
**Decisión.** `docs/presentacion/` entra en `.gitignore` antes de crear cualquier archivo ahí:
presentación, muestra (`referencia/`), logo (`activos/`), fuentes de la presentación, capturas
de láminas y el PDF del documento quedan solo en la estación. Se versionan
`docs/requerimientos_ti/REQUERIMIENTOS_TI.md`, `CIFRAS.csv`, `verificar_cifras.py` y
`exportar_pdf.py`.
**Descartado.** Versionar la presentación con el logo (material institucional en un
repositorio público). Versionar la muestra (es de otro proyecto de la Unidad).
**Consecuencias.** La presentación no se puede reconstruir desde el repositorio: depende de la
muestra y del logo locales. Sus cifras sí son trazables: cada una tiene fila en `CIFRAS.csv`.
El PDF se regenera con `py docs/requerimientos_ti/exportar_pdf.py`.

## D-25 · 2026-10-15 · Vocabulario único en la presentación y el documento para TI

**Contexto.** La auditoría de comunicación de la presentación (ronda 1, 51 hallazgos;
`docs/presentacion/auditoria/informe_ronda1.md`, fuera del repositorio por D-24) encontró
el mismo objeto con varios nombres («finca», «polígono», «objeto», «UGM»), términos con doble
lectura para un censo de fincas («lote», «propietario», «escrituras») y «la base» leída como
mapa base por la Unidad de Cartografía.
**Decisión.** Un término por concepto en láminas, notas del orador, `REQUERIMIENTOS_TI.md` y su
PDF: «base de datos» (nunca «la base» sola); «polígonos de prueba» (1.432, distrito 20205) para
los objetos del piloto y «fincas» solo para producción; «polígonos UGM (proxy)»; «lote de
trabajo A/B» en el piloto y «zona de equipo (por definir: provincia o UPM)» en producción;
«cuenta administradora» (rol dueño); «cuenta del equipo A/B» (roles de edición; en tablas
técnicas, el nombre del rol entre paréntesis); «guardados»; «control por fila (RLS)» en la
primera aparición; «regeneración automática»; «computadora»; «equipo de campo»; «visita
concluida»; fase «completada»; «solo se puede volver atrás 6 horas»; «revisión automática
independiente (programa, sin acceso a la conversación)». Siglas expandidas en su primera
aparición. Cifras en pantalla y en el PDF con coma decimal y punto de miles; una sola unidad,
MB (los MB de `pg_size_pretty` y los MiB de los scripts son la misma unidad de 1.048.576
bytes); el literal de consola queda solo en `CIFRAS.csv`. El tablero dice «visita concluida».
Tabla completa: anexo E de `REQUERIMIENTOS_TI.md`.
**Descartado.** Glosario aparte en una lámina (no corrige el uso inconsistente); conservar los
literales de consola en pantalla con una nota (la nota de L10 no evitó la doble lectura).
**Consecuencias.** `verificar_cifras.py` exige que cada cifra marcada en las láminas
(`data-cifra` o `[Cnn]`) tenga fila en `CIFRAS.csv` y, si la fila trae `valor_pantalla`, que
la pantalla diga eso; además falla ante un punto decimal en el texto visible.

## D-26 · 2026-10-15 · Catálogo de cuatro estados y uso del color en la presentación

**Contexto.** La ronda 1 contó doce etiquetas de estado para cuatro situaciones y el rojo con
cinco significados (total, problema, estado, énfasis y una caja del diagrama).
**Decisión.** Cuatro estados, definidos con leyenda en L04 y reutilizados sin variantes:
PROBADO (verde) · MEDIDO (azul; «extrapolado» va en el texto, no en la píldora) · NO PROBADO
(rojo) · PENDIENTE DE TI (ámbar). El rojo queda solo para «no probado / riesgo»; totales,
remates, encabezados de lámina, la caja del tablero en L03 y la barra de avance pasan a azul.
**Descartado.** Mantener «con señal», «hipótesis», «solo piloto», «en curso» como estados.
**Consecuencias.** Lo que antes era una condición del estado se dice en el texto de la fila.

## D-27 · 2026-10-16 · Etiqueta del tablero: «N incidencias, de ellas M revisitas pendientes»

**Contexto.** El spec S07 §0b pidió «revisitas sin cerrar» y D-25 prohíbe «cerrad-/cerrar»
(estado terminal = «visita concluida»). La auditoría de comunicación ronda 2 (M-19) señaló que
la captura de L07 decía «sin cerrar» y el texto de la lámina, «revisitas».
**Decisión.** El encabezado del tablero y las tarjetas por lote de trabajo dicen
«N incidencias, de ellas M revisitas pendientes» (singular: «1 revisita pendiente»; sin la
segunda parte si M es 0). Confirmado por la persona (sesión web del 15/10, spec S08 §0).
**Descartado.** «sin cerrar» (contradice D-25); «revisitas abiertas» (otro término nuevo).
**Consecuencias.** `tablero/generar_tablero.py` (`fmt_incidencias`) cambia; el tablero
publicado lo muestra tras el envío al repositorio y la regeneración siguiente.
`verificar_vocabulario.py` prohíbe además «sin cerrar», «proxy» (se usa «sustituto») y
«mosaicos» (se usa «teselas»), y el anexo E de `REQUERIMIENTOS_TI.md` los registra.

## D-28 · 2026-10-16 · Tablero v2: mapa satelital, contornos de UGM, filtros jerárquicos e indicadores en el navegador

**Contexto.** Para la demostración del 19/10 se necesita un tablero que se pueda recorrer en
vivo, en el celular y de noche, filtrando por UPM, UGM, lote de trabajo y encuestador (spec S08c).
**Decisión.** Una sola página con secciones y barra de filtros fija, en modo oscuro fijo. Los
indicadores, tablas y barras se calculan en el navegador sobre el subconjunto filtrado, a
partir de un JSON embebido (`<script type="application/json">` con `<` escapado). Hay dos
vistas nuevas, `mgn.v_tab_geo_poligonos` y `mgn.v_tab_geo_ugm`, con geometrías simplificadas
(`ST_SimplifyPreserveTopology` 2 m en 5367, luego 4326 con 6 decimales); el script es
`sql/11_vistas_geo_tablero.sql`. La UGM es un nivel de filtro y un contorno, obtenida por
cruce espacial con la capa SNIT en `sim.ugm`; código = `id_mgn`, confirmado por la persona.
Es una excepción explícita y acotada a «nada de sim se publica» (D-18): solo se publican
los contornos y códigos de las 44 UGM del distrito 20205 que contienen polígonos de prueba,
y ninguna visita ni cifra de `sim`. `tablero_lectura` recibe SELECT sobre las dos vistas,
no sobre `sim.ugm`. Un nivel jerárquico se muestra como select solo si tiene más de un
valor en los datos; si no, va como texto en la línea de ubicación. Leaflet 1.9.4 va
embebido (`tablero/vendor/`, sin CDN). La base por defecto es la imagen satelital Esri
World Imagery, con cambio automático a OSM si no cargan teselas. La proyección de días
restantes se calcula pero no se muestra.
Amplía D-09 (sigue siendo HTML estático sin credenciales, leído con `tablero_lectura`) y
respeta D-14, D-25 y D-27.
Decisiones de ejecución (sesión 10):
- Por debajo del zoom 15 cada polígono se dibuja como punto: la mediana es de 196 m² y a
  escala de distrito no se ve.
- `v_tab_geo_ugm` filtra con `IN` en lugar de `EXISTS`: 0,3 s frente a unos 50 s, con el
  mismo resultado.
- Encuestador visible: el campo `encuestador`; si está vacío y hubo guardado, la cuenta que
  guardó (como el `coalesce` de la v1); si no, «sin encuestador registrado» (el spec decía
  «sin usuario registrado»; D-25 prohíbe «usuario»). El generador convierte los nombres de
  cuenta en rótulos D-25 («cuenta administradora», «cuenta del equipo A/B») antes de
  embeberlos: el HTML no lleva nombres de cuenta de la base de datos. Sección «Equipos de
  campo».
- «Últimos 25 movimientos» y «Último guardado» solo cuentan polígonos con estado distinto de
  pendiente, como la v1; la carga inicial no es un movimiento.
- 39 polígonos tienen estado distinto de pendiente: 33 concluidas y 6 revisitas. El spec
  esperaba 33, que son las concluidas.
- 23 polígonos quedan «sin UGM». Su punto interior cae en huecos de la capa del SNIT, a
  entre 0,5 y 8,9 m de la UGM más cercana (todas del 20205); 22 tocan parcialmente una UGM
  y ninguno queda sobre el borde exacto. Se muestran como «sin UGM», como prevé el spec;
  no se asignan por cercanía.
**Descartado.** Pestañas, porque esconden contenido en el celular. CDN, porque la red de la
sala puede bloquearlo. Consultas desde el navegador (D-09). Selección múltiple, por tiempo.
Publicar las UGM con visitas simuladas: sería progreso inventado, y 50.794 polígonos no
caben en un HTML estático.
**Consecuencias.** El workflow genera con `--v2`. La v1 sigue disponible
(`generar_tablero.py` sin `--v2`) y se recupera con `git revert` del commit de publicación.
Para producción (~90.000 polígonos) el JSON embebido no escala: hace falta agregación del
lado del servidor o teselas vectoriales (nota para requerimientos TI).
