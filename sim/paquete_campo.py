# =====================================================================================
#  PASO 6e — Paquete de campo: cota del peso del paquete offline de QField
# =====================================================================================
#  Exporta sim.finca_visita + sim.ugm a un GeoPackage temporal (sim/salida/, ignorado
#  por git: *.gpkg) y, aparte, solo los puntos. Reporta los pesos.
#  USO: py sim/paquete_campo.py
#  Evidencia: docs/evidencia/s04/08_paquete_campo.txt
# =====================================================================================

from entorno import OGR2OGR, SALIDA, ejecutar

EV = "08_paquete_campo.txt"
SALIDA.mkdir(parents=True, exist_ok=True)
AMBAS = SALIDA / "paquete_campo_sim.gpkg"
PUNTOS = SALIDA / "paquete_campo_sim_solo_puntos.gpkg"
for f in (AMBAS, PUNTOS):
    if f.exists():
        f.unlink()

ejecutar([OGR2OGR, "-f", "GPKG", str(AMBAS), "PG:", "sim.finca_visita", "sim.ugm"],
         evidencia=EV, titulo="sim.finca_visita + sim.ugm -> GeoPackage")
ejecutar([OGR2OGR, "-f", "GPKG", str(PUNTOS), "PG:", "sim.finca_visita"],
         evidencia=EV, titulo="Solo sim.finca_visita -> GeoPackage")
lineas = []
for f in (AMBAS, PUNTOS):
    b = f.stat().st_size
    lineas.append(f"{f.name}: {b} bytes ({b / 1048576:.1f} MiB)")
texto = "\n".join(lineas)
print(texto)
with open(__import__("entorno").EVIDENCIA / EV, "a", encoding="utf-8") as fh:
    fh.write("## Pesos\n" + texto + "\n\n")
