# =====================================================================================
#  Construye el proyecto de campo QField de un lote (PyQGIS, QGIS 3.34.11)
# =====================================================================================
#  USO (Python de QGIS, no `py`):
#    "C:\Program Files\QGIS 3.34.11\bin\python-qgis-ltr.bat" campo/construir_proyecto_campo.py [A|B]
#  Salida: campo/NEON_campo_lote_<L>.qgs
#
#  Requisito: el servicio libpq neon_lote_<l> en %APPDATA%\postgresql\.pg_service.conf
#  (py campo/escribir_pg_service.py <l>). El proyecto guarda SOLO service='neon_lote_<l>':
#  sin host, usuario ni clave. En QFieldCloud el mismo servicio se carga como secreto
#  pg_service (D-19).
#
#  Capas:
#    finca_visita      editable, filtro "lote" = '<L>', QFieldSync: offline editing.
#    deteccion_cambio  referencia, solo lectura, filtro "lote" = '<L>', QFieldSync:
#                      offline (copia en el paquete) + capa de solo lectura en QGIS.
#  Formulario de finca_visita: ver configurar_formulario().
# =====================================================================================

import re
import sys
from pathlib import Path

from qgis.core import (
    QgsApplication, QgsCoordinateReferenceSystem, QgsDataSourceUri, QgsDefaultValue,
    QgsEditorWidgetSetup, QgsProject, QgsVectorLayer, QgsWkbTypes,
)

RAIZ = Path(__file__).resolve().parent.parent

# Estados de visita: los cinco de D-15 (provisional). Etiqueta = valor; no se inventan
# rótulos hasta tener el cuestionario real.
ESTADOS = ["pendiente", "visitada", "no_localizada", "rechazo", "revisita"]

SOLO_LECTURA = ["id", "finca_id", "lote", "codigo_upm",
                "creado_por", "fecha_creacion", "editado_por", "fecha_edicion"]

# Valores por defecto. Las filas ya existen (un punto por finca, sql/06): en campo se
# ACTUALIZAN, no se crean. Un valor por defecto solo se evalúa al actualizar si tiene
# «aplicar al actualizar»; por eso las tres expresiones lo llevan, escritas para no
# borrar lo que ya hay:
#   encuestador       la cuenta de QFieldCloud; si no hay (QGIS escritorio), conserva.
#   precision_gnss_m  la precisión horizontal del GNSS; si no hay posición, conserva.
#   fecha_visita      now() del dispositivo SOLO si está vacía y el estado ya no es
#                     pendiente; una fecha existente nunca se sobrescribe (D-16).
POR_DEFECTO = {
    "encuestador": ("coalesce(@cloud_username, \"encuestador\")", True),
    "precision_gnss_m": ("coalesce(@position_horizontal_accuracy, \"precision_gnss_m\")", True),
    "fecha_visita": ("if(\"fecha_visita\" IS NULL AND \"estado_visita\" <> 'pendiente', "
                     "now(), \"fecha_visita\")", True),
}


def capa_pg(servicio, tabla, tipo, lote, nombre):
    uri = QgsDataSourceUri()
    uri.setConnection(servicio, "", "", "")  # solo el servicio: sin base, usuario ni clave
    uri.setDataSource("mgn", tabla, "geom", f"\"lote\" = '{lote}'", "id")
    uri.setSrid("5367")
    uri.setWkbType(tipo)
    capa = QgsVectorLayer(uri.uri(False), nombre, "postgres")
    if not capa.isValid():
        sys.exit(f"Capa no válida: {tabla} ({capa.error().summary()}). "
                 f"¿Existe el servicio {servicio} en .pg_service.conf?")
    return capa


def configurar_formulario(capa):
    campos = capa.fields()

    def idx(nombre):
        i = campos.indexOf(nombre)
        if i < 0:
            sys.exit(f"Falta el campo {nombre} en finca_visita")
        return i

    capa.setEditorWidgetSetup(idx("estado_visita"), QgsEditorWidgetSetup(
        "ValueMap", {"map": [{e: e} for e in ESTADOS]}))
    capa.setEditorWidgetSetup(idx("observaciones"), QgsEditorWidgetSetup(
        "TextEdit", {"IsMultiline": True, "UseHtml": False}))
    capa.setEditorWidgetSetup(idx("fecha_visita"), QgsEditorWidgetSetup(
        "DateTime", {"allow_null": True, "calendar_popup": True,
                     "field_format": "yyyy-MM-dd HH:mm:ss",
                     "display_format": "dd/MM/yyyy HH:mm"}))

    for campo, (expresion, al_actualizar) in POR_DEFECTO.items():
        capa.setDefaultValueDefinition(idx(campo), QgsDefaultValue(expresion, al_actualizar))

    form = capa.editFormConfig()
    for campo in SOLO_LECTURA:
        form.setReadOnly(idx(campo), True)
    capa.setEditFormConfig(form)


def quitar_usuario(archivo):
    """El repositorio es público: vacía saveUser y saveUserFull (cuenta y nombre de
    quien ejecuta el script), que QGIS escribe siempre en el encabezado del .qgs."""
    texto = archivo.read_text(encoding="utf-8")
    texto = re.sub(r'(saveUser(?:Full)?)="[^"]*"', lambda m: m.group(1) + '=""', texto)
    archivo.write_text(texto, encoding="utf-8", newline="\n")


def main():
    lote = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
    if lote not in ("A", "B"):
        sys.exit("Lote inválido: use A o B.")
    servicio = f"neon_lote_{lote.lower()}"
    salida = RAIZ / "campo" / f"NEON_campo_lote_{lote}.qgs"

    app = QgsApplication([], False)
    app.initQgis()
    try:
        proyecto = QgsProject.instance()
        proyecto.setTitle(f"NEON censo — campo lote {lote}")
        proyecto.setCrs(QgsCoordinateReferenceSystem("EPSG:5367"))
        metadatos = proyecto.metadata()
        metadatos.setAuthor("")  # QGIS pone el nombre de la cuenta de Windows
        proyecto.setMetadata(metadatos)

        referencia = capa_pg(servicio, "deteccion_cambio", QgsWkbTypes.MultiPolygon, lote,
                             f"deteccion_cambio (lote {lote}, referencia)")
        referencia.setReadOnly(True)
        referencia.setCustomProperty("QFieldSync/action", "offline")
        referencia.setCustomProperty("QFieldSync/cloud_action", "offline")

        visita = capa_pg(servicio, "finca_visita", QgsWkbTypes.Point, lote,
                         f"finca_visita (lote {lote})")
        configurar_formulario(visita)
        visita.setCustomProperty("QFieldSync/action", "offline")
        visita.setCustomProperty("QFieldSync/cloud_action", "offline")

        proyecto.addMapLayers([referencia, visita])
        if not proyecto.write(str(salida)):
            sys.exit(f"No se pudo escribir {salida}: {proyecto.error()}")
        quitar_usuario(salida)
        print(f"Escrito: {salida.relative_to(RAIZ)}")
        print(f"  {visita.name()}: {visita.featureCount()} objetos, "
              f"SRC {visita.crs().authid()}, filtro {visita.subsetString()}")
        print(f"  {referencia.name()}: {referencia.featureCount()} objetos, "
              f"SRC {referencia.crs().authid()}, solo lectura {referencia.readOnly()}")
    finally:
        app.exitQgis()


if __name__ == "__main__":
    main()
