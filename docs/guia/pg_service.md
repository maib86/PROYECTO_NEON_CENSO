# Servicio de conexión libpq (`pg_service`)

Un servicio libpq guarda los datos de conexión fuera del proyecto QGIS. El proyecto solo
dice `service='neon_lote_a'`; host, usuario y clave viven en un archivo del perfil del
usuario, fuera del repositorio. Así el `.qgs` se puede versionar (D-17, D-19).

## Ruta en Windows

```
%APPDATA%\postgresql\.pg_service.conf
```

El nombre lleva **punto inicial**. Es el archivo por usuario que libpq (psql, QGIS) lee en
Windows sin configurar nada más. Un archivo llamado `pg_service.conf` (sin punto) no se lee
salvo que la variable de entorno `PGSERVICEFILE` apunte a él.

## Plantilla (sin valores)

```
[neon_lote_<<<LOTE>>>]
host=<<<HOST_SIN_POOLER>>>
port=5432
dbname=<<<BASE>>>
user=edit_lote_<<<LOTE>>>
password=<<<CLAVE_DEL_ROL>>>
sslmode=require
```

- `<<<LOTE>>>`: `a` o `b`.
- `<<<HOST_SIN_POOLER>>>`: host de Neon **sin** el sufijo `-pooler` (D-02).
- Un bloque por lote. Varios bloques pueden convivir en el mismo archivo.
- El archivo contiene la clave: no se copia al repositorio, no se adjunta en correos.

## Escritura automática desde `.env`

```bash
py campo/escribir_pg_service.py a
```

Lee `DATABASE_URL_LOTE_A` de `.env`, escribe el bloque `[neon_lote_a]` y conserva los demás
servicios del archivo (si el servicio ya existía, reemplaza solo su bloque). No imprime
valores: solo la ruta, el servicio y los nombres de las claves. Para el lote B: `b`.

## Verificación

```bash
psql "service=neon_lote_a" -X -c "select current_user"
```

Resultado esperado: `edit_lote_a`.

## En QFieldCloud

El mismo bloque se carga como secreto del proyecto, de tipo `pg_service`
(ver `docs/guia/qfield_campo.md`, paso 4). QFieldCloud lo usa para aplicar los cambios que
llegan de los celulares, con el rol del lote: el RLS actúa también en campo (D-19).
