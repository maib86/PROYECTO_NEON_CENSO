# Proyecto de campo QField por lote

Secuencia completa para editar un lote desde el celular con QField y QFieldCloud.
Decisiones de base: D-10 (identidad por `@cloud_username`), D-16 (`fecha_visita`), D-17
(`.qgs` sin credenciales) y D-19 (un proyecto por lote, rol del lote en el secreto
`pg_service`).

Marcadores: `<<<LOTE>>>` = `A` o `B` (mayúscula en archivos y filtros);
`<<<lote>>>` = `a` o `b` (minúscula en servicio y rol).

| Paso | Quién | Dónde |
|---|---|---|
| 1. Servicio `pg_service` | Claude Code (automático) | Estación |
| 2. Proyecto `.qgs` | Claude Code (automático) | Estación (PyQGIS) |
| 3. Revisión en QGIS y QFieldSync | Persona | QGIS escritorio |
| 4. Proyecto y secreto en QFieldCloud | Persona | QFieldCloud (web) y QGIS |
| 5. Celular | Persona | QField |
| 6. Sincronización y comprobación | Persona y Claude Code | QField, base |

Los pasos 3 a 5 son de interfaz gráfica: solo los puede hacer una persona (regla de
automatización, motivo a). Requieren cuenta de QFieldCloud con el proyecto creado.

## 1. Servicio `pg_service`

```bash
py campo/escribir_pg_service.py <<<lote>>>
psql "service=neon_lote_<<<lote>>>" -X -c "select current_user"
```

Esperado: `edit_lote_<<<lote>>>`. Detalle y plantilla: `docs/guia/pg_service.md`.

## 2. Proyecto de campo

```bash
"/c/Program Files/QGIS 3.34.11/bin/python-qgis-ltr.bat" campo/construir_proyecto_campo.py <<<LOTE>>>
"/c/Program Files/QGIS 3.34.11/bin/python-qgis-ltr.bat" campo/verificar_proyecto_campo.py <<<LOTE>>>
```

Salida: `campo/NEON_campo_lote_<<<LOTE>>>.qgs`. La verificación debe terminar en
`Resultado: 0 fallas`. Contenido del proyecto:

- SRC del proyecto EPSG:5367.
- `finca_visita (lote <<<LOTE>>>)`: `mgn.finca_visita`, filtro `"lote" = '<<<LOTE>>>'`, editable.
  QFieldSync: «offline editing» (`QFieldSync/cloud_action = offline`).
- `deteccion_cambio (lote <<<LOTE>>>, referencia)`: `mgn.deteccion_cambio`, mismo filtro,
  capa de solo lectura. QFieldSync: «offline editing» (copia en el paquete; la capa de solo
  lectura impide editarla en el celular).
- Formulario de `finca_visita`:

| Campo | Widget / regla |
|---|---|
| `estado_visita` | Lista de valores: `pendiente`, `visitada`, `no_localizada`, `rechazo`, `revisita` (D-15) |
| `encuestador` | Por defecto `coalesce(@cloud_username, "encuestador")`, aplicar al actualizar |
| `fecha_visita` | Fecha y hora. Por defecto `if("fecha_visita" IS NULL AND "estado_visita" <> 'pendiente', now(), "fecha_visita")`, aplicar al actualizar |
| `precision_gnss_m` | Por defecto `coalesce(@position_horizontal_accuracy, "precision_gnss_m")`, aplicar al actualizar |
| `observaciones` | Texto multilínea |
| `id`, `finca_id`, `lote`, `codigo_upm`, `creado_por`, `fecha_creacion`, `editado_por`, `fecha_edicion` | Solo lectura |

Por qué «aplicar al actualizar»: las filas ya existen (un punto por finca, `sql/06`); en
campo se actualizan y no se crean. Sin esa opción, ningún valor por defecto se evaluaría.
`fecha_visita` conserva el valor existente: toma la hora del dispositivo solo la primera vez
que la finca deja de estar `pendiente`, y el trigger de la base la respeta (`sql/09`, D-16).
`encuestador` y `precision_gnss_m`, en cambio, se reescriben en cada edición desde QField
(solo conservan el valor cuando la variable viene vacía, como en QGIS escritorio): una
revisita deja el `encuestador` de la última edición con la fecha de la primera (D-19,
pendiente de decisión).

## 3. Revisión en QGIS y QFieldSync (persona)

1. QGIS 3.34 → Proyecto → Abrir → `campo/NEON_campo_lote_<<<LOTE>>>.qgs`. Las dos capas deben
   cargar sin pedir usuario ni clave (las toma del servicio).
2. Clic derecho en `finca_visita` → Propiedades → **QField**: comprobar que la acción en la nube
   sea «Offline editing». Repetir en `deteccion_cambio`. Si el complemento muestra otro valor,
   ajustarlo ahí (el script fija las propiedades `QFieldSync/action` y
   `QFieldSync/cloud_action`; la interfaz es la referencia final).
3. Abrir el formulario de una finca (herramienta Identificar → Editar) y comprobar la lista de
   estados y los campos de solo lectura. **No guardar** cambios de prueba en este paso.

**Advertencia.** Al guardar el proyecto desde QGIS o al subirlo con QFieldSync, QGIS vuelve a
escribir en el `.qgs` la cuenta de Windows (`saveUser`, `saveUserFull`) y el autor. Antes de
cualquier commit del `.qgs`, reconstruirlo con `construir_proyecto_campo.py` o correr
`verificar_proyecto_campo.py` y exigir `0 fallas`.

## 4. Proyecto y secreto en QFieldCloud (persona)

1. En QFieldCloud (web), crear el proyecto `NEON_campo_lote_<<<LOTE>>>`, privado.
2. En el proyecto → **Secrets** → agregar un secreto de tipo **pg_service**, con el bloque
   `[neon_lote_<<<lote>>>]` completo (plantilla en `docs/guia/pg_service.md`). El nombre del
   servicio debe coincidir con el del `.qgs`. Copiar el bloque desde
   `%APPDATA%\postgresql\.pg_service.conf`; nunca desde el repositorio.
3. En QGIS, con el complemento QFieldSync: QFieldCloud → iniciar sesión → elegir el proyecto
   → subir (sincronizar) el proyecto local `campo/NEON_campo_lote_<<<LOTE>>>.qgs`.
4. En la web, esperar a que el empaquetado («package») termine sin errores.
5. Agregar como colaboradoras solo las cuentas del equipo del lote <<<LOTE>>>.

## 5. Celular (persona)

1. QField → iniciar sesión con la cuenta de QFieldCloud de la persona.
2. Proyectos de QFieldCloud → descargar `NEON_campo_lote_<<<LOTE>>>`.
3. Activar el GNSS. Abrir una finca → editar → cambiar `estado_visita` a `visitada` →
   guardar. Comprobar que `fecha_visita`, `encuestador` y `precision_gnss_m` se llenaron solos.

## 6. Sincronización y comprobación

1. QField → sincronizar (subir cambios). En la web, el trabajo de aplicación de cambios debe
   terminar sin errores.
2. Comprobación en la base (Claude Code, solo lectura):

```sql
SELECT id, estado_visita, encuestador, fecha_visita, precision_gnss_m, editado_por
  FROM mgn.finca_visita
 WHERE lote = '<<<LOTE>>>' AND encuestador IS NOT NULL
 ORDER BY fecha_edicion DESC LIMIT 5;
```

Esperado: `encuestador` = cuenta de QFieldCloud de la persona; `fecha_visita` = hora del
celular (no la de la sincronización); `editado_por` = `edit_lote_<<<lote>>>` (rol del secreto).

## Réplica para el lote B

Mismos pasos con `<<<LOTE>>>` = `B` y `<<<lote>>>` = `b`:

```bash
py campo/escribir_pg_service.py b
psql "service=neon_lote_b" -X -c "select current_user"
"/c/Program Files/QGIS 3.34.11/bin/python-qgis-ltr.bat" campo/construir_proyecto_campo.py B
"/c/Program Files/QGIS 3.34.11/bin/python-qgis-ltr.bat" campo/verificar_proyecto_campo.py B
```

Proyecto QFieldCloud aparte (`NEON_campo_lote_B`), con su propio secreto `pg_service`
`[neon_lote_b]` (rol `edit_lote_b`) y solo las cuentas del equipo B. El piloto prepara solo
el lote A (D-19).
