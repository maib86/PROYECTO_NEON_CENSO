#!/usr/bin/env python3
# =====================================================================================
#  GENERADOR DEL TABLERO DE AVANCE — VERSIÓN 2 (spec S08c, D-28)
# =====================================================================================
#  Una sola página con mapa Leaflet (imagen satelital con cambio automático a mapa
#  claro), polígonos de prueba por estado, contornos de UGM, filtros jerárquicos e
#  indicadores que se recalculan en el navegador sobre el subconjunto filtrado.
#
#  USO (desde la raíz del repositorio)
#    Con la base de datos:  py tablero/generar_tablero.py --v2 --salida tablero/salida/v2/index.html
#    Sin base de datos:     py tablero/generar_tablero.py --v2 --fixture
#    Rehacer el fixture:    py tablero/generar_tablero.py --v2 --volcar-fixture tablero/fixtures/fixture_v2.json
#
#  Lee SOLO DATABASE_URL_TABLERO (rol tablero_lectura) y se detiene si la conexión es
#  otra (D-14). Lee las vistas mgn.v_tab_geo_poligonos, mgn.v_tab_geo_ugm y
#  mgn.v_tab_resumen. Los datos van en un JSON embebido (<script type="application/json">)
#  con '<' escapado; Leaflet 1.9.4 va embebido desde tablero/vendor/ (sin CDN).
#  El HTML no contiene credenciales ni consulta nada al abrirse (D-09).
# =====================================================================================

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from generar_tablero import CR_TZ, ROL_TABLERO, esc, fmt_int, json_en_script

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / "plantilla_v2.html"
LEAFLET = AQUI / "vendor" / "leaflet-1.9.4"
FIXTURE_V2 = AQUI / "fixtures" / "fixture_v2.json"
SALIDA_V2 = AQUI / "salida" / "v2" / "index.html"

ESQUEMA = "mgn"
TOLERANCIA_M = 2
SRID_ORIGEN = 5367

# Cinco estados de D-15; colores del spec S08c §4 (modo oscuro fijo).
# Nombres técnicos de cuenta → rótulo D-25. Se convierten antes de embeber: el HTML público
# no lleva nombres de cuenta de la base de datos.
CUENTAS = {"neondb_owner": "cuenta administradora",
           "edit_lote_a": "cuenta del equipo A", "edit_lote_b": "cuenta del equipo B"}


def rotulo(c):
    return CUENTAS.get(c, c) if c else c


ESTADOS_V2 = [
    {"clave": "pendiente",     "etiqueta": "Pendiente",     "color": "#E2E8F0", "terminal": False, "incidencia": False},
    {"clave": "visitada",      "etiqueta": "Visitada",      "color": "#22C55E", "terminal": True,  "incidencia": False},
    {"clave": "no_localizada", "etiqueta": "No localizada", "color": "#8B5CF6", "terminal": True,  "incidencia": True},
    {"clave": "rechazo",       "etiqueta": "Rechazo",       "color": "#EF4444", "terminal": True,  "incidencia": True},
    {"clave": "revisita",      "etiqueta": "Revisita",      "color": "#F59E0B", "terminal": False, "incidencia": True},
]


# -------------------------------------------------------------------------------------
#  Obtención de datos
# -------------------------------------------------------------------------------------

def _normalizar(fila):
    for k, v in list(fila.items()):
        if hasattr(v, "astimezone"):
            fila[k] = v.astimezone(CR_TZ).isoformat(timespec="seconds")
        elif v is not None and type(v).__name__ == "Decimal":
            fila[k] = float(v)
    return fila


def leer_base(url):
    """Las tres vistas tal como salen de la base de datos (filas como dict)."""
    import psycopg2
    import psycopg2.extras
    con = psycopg2.connect(url)
    try:
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT current_user AS u")
            usuario = cur.fetchone()["u"]
            if usuario != ROL_TABLERO:
                sys.exit(f"La conexión es '{usuario}', no '{ROL_TABLERO}'. "
                         "El tablero solo lee con el rol de solo lectura.")
            cur.execute("SET TIME ZONE 'America/Costa_Rica'")
            cur.execute(f"SELECT * FROM {ESQUEMA}.v_tab_geo_poligonos ORDER BY id")
            poligonos = [_normalizar(dict(r)) for r in cur.fetchall()]
            cur.execute(f"SELECT * FROM {ESQUEMA}.v_tab_geo_ugm ORDER BY ugm")
            ugm = [_normalizar(dict(r)) for r in cur.fetchall()]
            cur.execute(f"SELECT * FROM {ESQUEMA}.v_tab_resumen ORDER BY lote")
            resumen = [_normalizar(dict(r)) for r in cur.fetchall()]
    finally:
        con.close()
    return {"poligonos": poligonos, "ugm": ugm, "resumen": resumen}


def anonimizar(vistas):
    """Copia para el fixture: encuestador → encuestador_01…; editado_por queda (son cuentas)."""
    nombres = sorted({p["encuestador"] for p in vistas["poligonos"] if p.get("encuestador")})
    alias = {n: f"encuestador_{i:02d}" for i, n in enumerate(nombres, 1)}
    copia = json.loads(json.dumps(vistas, default=str))
    for p in copia["poligonos"]:
        if p.get("encuestador"):
            p["encuestador"] = alias[p["encuestador"]]
    return copia


# -------------------------------------------------------------------------------------
#  Armado del JSON embebido
# -------------------------------------------------------------------------------------

def resumen_bd(resumen):
    """Totales de v_tab_resumen con las definiciones del tablero v1 (D-15, D-27)."""
    tot = lambda c: sum(int(r[c]) for r in resumen)
    return {
        "total": tot("fincas"),
        "concluidas": tot("visitadas") + tot("no_localizadas") + tot("rechazos"),
        "incidencias": tot("no_localizadas") + tot("rechazos") + tot("revisitas"),
        "revisitas": tot("revisitas"),
    }


def armar_datos(vistas, generado):
    registros = []
    for p in vistas["poligonos"]:
        registros.append({
            "id": int(p["id"]),
            "cprov": p["cod_provincia"], "prov": p["provincia"],
            "ccant": p["cod_canton"], "cant": p["canton"],
            "cdist": p["cod_distrito"], "dist": p["distrito"],
            "upm": p["upm"], "ugm": p["ugm"], "lote": p["lote"],
            "est": p["estado_visita"], "enc": rotulo(p.get("encuestador")),
            "fv": p.get("fecha_visita"), "fe": p.get("fecha_edicion"),
            "ep": rotulo(p.get("editado_por")),
            "gnss": None if p.get("precision_gnss_m") is None else round(float(p["precision_gnss_m"]), 2),
            "prio": p.get("prioridad"), "area": p.get("area_m2"),
            "p": [round(float(p["lon"]), 6), round(float(p["lat"]), 6)],
            "g": p["geom"] if not isinstance(p["geom"], str) else json.loads(p["geom"]),
        })
    ugm = [{"codigo": u["ugm"], "g": u["geom"] if not isinstance(u["geom"], str) else json.loads(u["geom"])}
           for u in vistas["ugm"]]
    return {
        "meta": {
            "generado_en": generado.isoformat(timespec="seconds"),
            "zona": "America/Costa_Rica",
            "fuente": "base de datos del piloto (Neon)",
            "srid_origen": SRID_ORIGEN,
            "tolerancia_m": TOLERANCIA_M,
            "total": len(registros),
        },
        "estados": ESTADOS_V2,
        "registros": registros,
        "ugm": ugm,
        "resumen_bd": resumen_bd(vistas["resumen"]),
    }


# -------------------------------------------------------------------------------------
#  Render
# -------------------------------------------------------------------------------------

def render(datos):
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    js = (LEAFLET / "leaflet.js").read_text(encoding="utf-8")
    css = (LEAFLET / "leaflet.css").read_text(encoding="utf-8")
    if "</script" in js.lower() or "</style" in css.lower():
        sys.exit("La biblioteca embebida contiene una etiqueta de cierre: no se puede embeber.")
    gen = datetime.fromisoformat(datos["meta"]["generado_en"])
    distritos = sorted({r["cdist"] for r in datos["registros"]})
    reemplazos = {
        "GENERADO": esc(gen.strftime("%d/%m/%Y %H:%M")),
        "GENERADO_ISO": esc(datos["meta"]["generado_en"]),
        "TOTAL": fmt_int(datos["meta"]["total"]),
        "DISTRITO": esc(", ".join(distritos)),
        "LEAFLET_CSS": css,
        "LEAFLET_JS": js,
        "DATOS": json_en_script(datos, ensure_ascii=False, separators=(",", ":")),
    }
    # Una sola pasada: un dato que contenga «{{X}}» no se vuelve a sustituir.
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: reemplazos[m.group(1)], plantilla)


def escribir_atomico(ruta, texto):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    os.replace(tmp, ruta)


def main_v2(a):
    """a: argumentos de generar_tablero.py (--fixture, --salida, --volcar-fixture)."""
    if a.volcar or a.esquema != "mgn":
        sys.exit("--volcar y --esquema son de la versión 1; con --v2 usar --volcar-fixture (esquema mgn).")
    if a.fixture is not None:
        ruta = a.fixture or FIXTURE_V2
        with open(ruta, encoding="utf-8") as f:
            vistas = json.load(f)
    else:
        url = os.environ.get("DATABASE_URL_TABLERO")
        if not url:
            sys.exit("Falta DATABASE_URL_TABLERO (o usar --fixture).")
        vistas = leer_base(url)
        if a.volcar_fixture:
            escribir_atomico(a.volcar_fixture,
                             json.dumps(anonimizar(vistas), ensure_ascii=False, separators=(",", ":")))
            print(f"Fixture escrito en {a.volcar_fixture}")
    generado = datetime.now(CR_TZ).replace(microsecond=0)
    html = render(armar_datos(vistas, generado))
    salida = a.salida or SALIDA_V2
    escribir_atomico(salida, html)
    print(f"Tablero v2 escrito en {salida} ({len(html.encode('utf-8')) // 1024} KB)")
