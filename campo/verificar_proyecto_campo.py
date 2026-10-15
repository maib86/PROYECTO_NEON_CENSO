# =====================================================================================
#  Verifica el proyecto de campo de un lote (PyQGIS). No escribe en la base.
# =====================================================================================
#  USO:
#    "C:\Program Files\QGIS 3.34.11\bin\python-qgis-ltr.bat" campo/verificar_proyecto_campo.py [A|B]
#
#  1. Escaneo del .qgs: 0 coincidencias de neon.tech, npg_, password, user=, host=;
#     service='neon_lote_<l>' presente; saveUser vacío.
#  2. Recarga el proyecto: capas válidas, SRC, filtro, solo lectura, QFieldSync.
#  3. Formulario: widgets, campos de solo lectura y valores por defecto.
#  4. Evalúa los valores por defecto sobre una copia en memoria de una finca pendiente
#     (no se guarda nada): estado pendiente -> fecha vacía; estado visitada -> now();
#     fecha previa -> se conserva.
#  Termina con rc=1 si alguna comprobación falla.
# =====================================================================================

import re
import sys
from pathlib import Path

from qgis.core import QgsApplication, QgsExpressionContextUtils, QgsProject
from qgis.PyQt.QtCore import QDateTime

RAIZ = Path(__file__).resolve().parent.parent
fallas = []


def comprobar(nombre, ok, detalle=""):
    print(f"[{'OK' if ok else 'FALLA'}] {nombre}{' · ' + detalle if detalle else ''}")
    if not ok:
        fallas.append(nombre)


def main():
    lote = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
    servicio = f"neon_lote_{lote.lower()}"
    archivo = RAIZ / "campo" / f"NEON_campo_lote_{lote}.qgs"
    texto = archivo.read_text(encoding="utf-8")

    for patron in ("neon.tech", "npg_", "password", "user=", "host=", "dbname="):
        n = len(re.findall(re.escape(patron), texto, re.IGNORECASE))
        # saveUser="" es un atributo de QGIS (vaciado por el constructor), no una conexión.
        if patron == "user=":
            n -= len(re.findall(r'saveUser=""', texto))
        comprobar(f"escaneo «{patron}» = 0", n == 0, str(n))
    n = texto.count(f"service='{servicio}'")
    comprobar(f"service='{servicio}' presente", n > 0, f"{n} veces")
    comprobar("saveUser y saveUserFull vacíos",
              not re.search(r'saveUser(?:Full)?="[^"]+"', texto))

    app = QgsApplication([], False)
    app.initQgis()
    try:
        proyecto = QgsProject.instance()
        comprobar("proyecto se lee", proyecto.read(str(archivo)))
        comprobar("SRC del proyecto EPSG:5367", proyecto.crs().authid() == "EPSG:5367",
                  proyecto.crs().authid())
        capas = {c.name(): c for c in proyecto.mapLayers().values()}
        visita = capas.get(f"finca_visita (lote {lote})")
        referencia = capas.get(f"deteccion_cambio (lote {lote}, referencia)")
        for capa, ro in ((visita, False), (referencia, True)):
            comprobar(f"{capa.name()} válida", capa.isValid(), f"{capa.featureCount()} objetos")
            comprobar(f"{capa.name()} filtro", capa.subsetString() == f"\"lote\" = '{lote}'",
                      capa.subsetString())
            comprobar(f"{capa.name()} solo lectura = {ro}", capa.readOnly() == ro)
            comprobar(f"{capa.name()} SRC 5367", capa.crs().authid() == "EPSG:5367")
            comprobar(f"{capa.name()} QFieldSync cloud_action",
                      capa.customProperty("QFieldSync/cloud_action") == "offline",
                      str(capa.customProperty("QFieldSync/cloud_action")))

        campos = visita.fields()
        idx = campos.indexOf
        w = visita.editorWidgetSetup(idx("estado_visita"))
        valores = [list(d.values())[0] for d in w.config().get("map", [])]
        comprobar("estado_visita: lista de valores D-15",
                  w.type() == "ValueMap" and valores ==
                  ["pendiente", "visitada", "no_localizada", "rechazo", "revisita"], str(valores))
        w = visita.editorWidgetSetup(idx("observaciones"))
        comprobar("observaciones multilínea",
                  w.type() == "TextEdit" and w.config().get("IsMultiline") is True)
        form = visita.editFormConfig()
        for campo in ("id", "finca_id", "lote", "codigo_upm", "creado_por",
                      "fecha_creacion", "editado_por", "fecha_edicion"):
            comprobar(f"{campo} solo lectura", form.readOnly(idx(campo)))
        for campo in ("estado_visita", "observaciones", "fecha_visita"):
            comprobar(f"{campo} editable", not form.readOnly(idx(campo)))
        for campo in ("encuestador", "fecha_visita", "precision_gnss_m"):
            d = visita.defaultValueDefinition(idx(campo))
            comprobar(f"por defecto {campo}", d.isValid(),
                      f"{d.expression()} · aplicar al actualizar={d.applyOnUpdate()}")

        # Evaluación en memoria sobre una finca pendiente con fecha vacía.
        f = next(visita.getFeatures(
            "\"estado_visita\" = 'pendiente' AND \"fecha_visita\" IS NULL"))
        QgsExpressionContextUtils.setProjectVariable(proyecto, "cloud_username", "prueba_campo")
        ctx = visita.createExpressionContext()

        def por_defecto(campo):
            ctx.setFeature(f)
            return visita.defaultValue(idx(campo), f, ctx)

        v = por_defecto("fecha_visita")
        comprobar("pendiente sin fecha -> fecha vacía", v is None or v == QDateTime() or
                  (hasattr(v, "isNull") and v.isNull()), repr(v))
        f["estado_visita"] = "visitada"
        v = por_defecto("fecha_visita")
        ahora = QDateTime.currentDateTime()
        comprobar("visitada sin fecha -> now()", isinstance(v, QDateTime) and
                  abs(v.secsTo(ahora)) < 60, v.toString("yyyy-MM-dd HH:mm:ss")
                  if isinstance(v, QDateTime) else repr(v))
        ayer = ahora.addDays(-1)
        f["fecha_visita"] = ayer
        v = por_defecto("fecha_visita")
        comprobar("fecha previa -> se conserva", isinstance(v, QDateTime) and v == ayer,
                  v.toString("yyyy-MM-dd HH:mm:ss") if isinstance(v, QDateTime) else repr(v))
        v = por_defecto("encuestador")
        comprobar("encuestador = @cloud_username", v == "prueba_campo", repr(v))
        comprobar("sin cambios pendientes en la capa", not visita.isModified())
    finally:
        app.exitQgis()

    print(f"\nResultado: {'0 fallas' if not fallas else str(len(fallas)) + ' fallas'}")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
