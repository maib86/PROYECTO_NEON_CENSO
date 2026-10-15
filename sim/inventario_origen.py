# =====================================================================================
#  PASO 2 — Inventario del origen (no toca la base)
# =====================================================================================
#  USO: py sim/inventario_origen.py
#  Deja la salida literal de ogrinfo en docs/evidencia/s04/02_inventario_origen.txt.
# =====================================================================================

from entorno import OGRINFO, RAIZ, ejecutar

GPKG = str(RAIZ / "datos_prueba" / "ugm" / "ugm.gpkg")
EV = "02_inventario_origen.txt"

ejecutar([OGRINFO, "--version"], rol=None, evidencia=EV, titulo="Versión de GDAL")
ejecutar([OGRINFO, "-so", "-al", "-nomd", GPKG], rol=None, evidencia=EV, titulo="ogrinfo -so")
ejecutar([OGRINFO, "-q", GPKG, "-sql",
          "SELECT count(*) n, count(DISTINCT id) id_distintos, count(DISTINCT id_mgn) id_mgn_distintos, "
          "count(DISTINCT cod_uged) distritos, count(DISTINCT nomb_ugec) cantones, "
          "count(DISTINCT nomb_ugep) provincias, sum(ST_IsValid(geom)=0) invalidas, "
          "sum(ST_NumGeometries(geom)>1) multipartes, min(fecha_act) fecha_min, max(fecha_act) fecha_max FROM ugm"],
         rol=None, evidencia=EV, titulo="Perfil de la capa")
ejecutar([OGRINFO, "-q", GPKG, "-sql",
          "SELECT substr(cod_uged,1,1) AS provincia, nomb_ugep, count(*) AS n FROM ugm "
          "GROUP BY provincia, nomb_ugep ORDER BY provincia"],
         rol=None, evidencia=EV, titulo="Objetos por provincia (primer dígito de cod_uged)")
