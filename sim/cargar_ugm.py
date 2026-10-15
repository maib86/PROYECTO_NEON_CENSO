# =====================================================================================
#  PASOS 3 y 4 — Presupuesto de almacenamiento y carga de la capa UGM al esquema sim
# =====================================================================================
#  USO
#    py sim/cargar_ugm.py temporal [--solo-jerarquia]   ogr2ogr -> sim.carga_temporal
#    py sim/cargar_ugm.py ugm                           sim.ugm desde carga_temporal
#
#  Credenciales: de .env, por variables libpq (entorno.py). Nada en la línea de comandos.
#  Evidencia literal: docs/evidencia/s04/03_carga.txt
# =====================================================================================

import sys

from entorno import OGR2OGR, RAIZ, ejecutar, psql

GPKG = str(RAIZ / "datos_prueba" / "ugm" / "ugm.gpkg")
EV = "03_carga.txt"


def temporal(solo_jerarquia=False):
    psql(archivo=RAIZ / "sim" / "sql_tamanos.sql", evidencia=EV, titulo="Tamaños antes de cargar")
    psql("CREATE SCHEMA IF NOT EXISTS sim; "
         "COMMENT ON SCHEMA sim IS 'Simulación a escala S04 con la capa UGM del SNIT (D-18). "
         "No es dato del censo.';", evidencia=EV, titulo="Esquema sim")
    cmd = [OGR2OGR, "-f", "PostgreSQL", "PG:", GPKG, "ugm",
           "-nln", "sim.carga_temporal", "-t_srs", "EPSG:5367", "-nlt", "PROMOTE_TO_MULTI",
           "-lco", "GEOMETRY_NAME=geom", "-lco", "SPATIAL_INDEX=GIST",
           "-gt", "10000", "-progress"]
    if solo_jerarquia:
        cmd += ["-select", "id,nomb_ugep,nomb_ugec,nomb_uged,cod_uged"]
    ejecutar(cmd, evidencia=EV, titulo="ogr2ogr -> sim.carga_temporal"
             + (" (solo jerarquía)" if solo_jerarquia else ""))
    psql("SELECT count(*) AS objetos, count(DISTINCT id) AS id_distintos, "
         "min(ST_SRID(geom)) AS srid_min, max(ST_SRID(geom)) AS srid_max, "
         "count(*) FILTER (WHERE NOT ST_IsValid(geom)) AS invalidas FROM sim.carga_temporal;",
         evidencia=EV, titulo="Verificación de carga_temporal")
    psql(archivo=RAIZ / "sim" / "sql_tamanos.sql", evidencia=EV, titulo="Tamaños tras ogr2ogr")


def ugm():
    psql(archivo=RAIZ / "sim" / "sql_ugm.sql", evidencia=EV,
         titulo="sim.ugm: estructura de plantilla + INSERT ... SELECT", extra=["--echo-queries"])
    psql(archivo=RAIZ / "sim" / "sql_tamanos.sql", evidencia=EV, titulo="Tamaños tras crear sim.ugm")


if __name__ == "__main__":
    etapa = sys.argv[1] if len(sys.argv) > 1 else ""
    if etapa == "temporal":
        temporal("--solo-jerarquia" in sys.argv)
    elif etapa == "ugm":
        ugm()
    else:
        sys.exit(__doc__ or "Etapa: temporal | ugm")
