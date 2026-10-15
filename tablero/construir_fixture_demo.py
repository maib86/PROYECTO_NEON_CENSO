#!/usr/bin/env python3
"""Construye un fixture de prueba a partir del GeoJSON real: un punto por polígono
(ST_PointOnSurface equivalente), reparto A/B por UPM, y visitas simuladas de 3 días.
Solo para verificar el tablero sin tocar la base."""
import json, random, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from shapely.geometry import shape

src, dst = sys.argv[1], sys.argv[2]
random.seed(20205)
CR = timezone(timedelta(hours=-6))
d = json.load(open(src, encoding="utf-8"))
A = {"001", "002", "003", "006", "010"}

pts = []
for i, f in enumerate(d["features"], start=1):
    g = shape(f["geometry"])
    p = g.representative_point()          # equivalente a ST_PointOnSurface
    upm = f["properties"]["codigo_upm"]
    pts.append({"finca_id": i, "lote": "A" if upm[-3:] in A else "B", "codigo_upm": upm,
                "estado_visita": "pendiente", "persona": None, "cuando": None,
                "lat": p.y, "lon": p.x, "_t": None})

# Simular visitas: 3 días, dos personas, ~30% del total
personas = {"A": "edit_lote_a", "B": "edit_lote_b"}
hoy = datetime.now(CR).replace(hour=0, minute=0, second=0, microsecond=0)
estados = ["visitada"] * 8 + ["no_localizada", "revisita", "rechazo"]
for p in random.sample(pts, int(len(pts) * 0.30)):
    dia = hoy - timedelta(days=random.choice([0, 1, 2]))
    t = dia + timedelta(hours=random.randint(7, 17), minutes=random.randint(0, 59))
    p["estado_visita"] = random.choice(estados)
    p["persona"] = personas[p["lote"]]
    p["cuando"] = t.strftime("%d/%m %H:%M")
    p["_t"] = t

# Vistas
resumen = []
for l in ("A", "B"):
    s = [p for p in pts if p["lote"] == l]
    c = lambda e: sum(1 for p in s if p["estado_visita"] == e)
    hechas = len(s) - c("pendiente")
    resumen.append({"lote": l, "fincas": len(s), "visitadas": c("visitada"), "no_localizadas": c("no_localizada"),
                    "rechazos": c("rechazo"), "revisitas": c("revisita"), "pendientes": c("pendiente"),
                    "avance_pct": round(100.0 * hechas / len(s), 1),
                    "ultima_visita": max((p["_t"] for p in s if p["_t"]), default=None).isoformat()})

enc = defaultdict(lambda: {"visitas": 0, "visitadas": 0, "incidencias": 0, "ts": []})
for p in pts:
    if p["_t"]:
        e = enc[(p["persona"], p["lote"])]
        e["visitas"] += 1
        e["visitadas"] += p["estado_visita"] == "visitada"
        e["incidencias"] += p["estado_visita"] in ("no_localizada", "rechazo", "revisita")
        e["ts"].append(p["_t"])
encuestador = [{"persona": k[0], "lote": k[1], "visitas": v["visitas"], "visitadas": v["visitadas"],
                "incidencias": v["incidencias"], "primera": min(v["ts"]).isoformat(), "ultima": max(v["ts"]).isoformat()}
               for k, v in enc.items()]

dia = defaultdict(int)
for p in pts:
    if p["_t"]:
        dia[(p["_t"].date().isoformat(), p["lote"])] += 1
diario = [{"dia": k[0], "lote": k[1], "visitas": v} for k, v in sorted(dia.items())]

mov = sorted([p for p in pts if p["_t"]], key=lambda p: p["_t"], reverse=True)[:25]
movimientos = [{"finca_id": p["finca_id"], "lote": p["lote"], "codigo_upm": p["codigo_upm"], "estado_visita": p["estado_visita"],
                "persona": p["persona"], "cuando": p["cuando"], "observaciones": None} for p in mov]

puntos = [{k: v for k, v in p.items() if k != "_t"} | {"id": p["finca_id"]} for p in pts]

json.dump({"resumen": resumen, "encuestador": encuestador, "diario": diario, "puntos": puntos, "movimientos": movimientos},
          open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
dentro = sum(1 for f, p in zip(d["features"], pts) if shape(f["geometry"]).contains(__import__("shapely.geometry", fromlist=["Point"]).Point(p["lon"], p["lat"])))
print(f"fixture: {len(pts)} puntos, {dentro} dentro de su polígono, {sum(1 for p in pts if p['_t'])} visitas simuladas")
