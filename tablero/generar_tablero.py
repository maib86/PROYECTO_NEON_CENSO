#!/usr/bin/env python3
# =====================================================================================
#  GENERADOR DEL TABLERO DE AVANCE
# =====================================================================================
#  Lee las vistas v_tab_* de la base (rol de solo lectura) y escribe un archivo HTML
#  autocontenido con el avance del operativo: resumen, por equipo, por persona, por
#  día, mapa de puntos y últimos movimientos.
#
#  USO
#    Con la base:        DATABASE_URL_TABLERO="postgresql://tablero_lectura:CLAVE@HOST/neondb?sslmode=require" \
#                        py tablero/generar_tablero.py --salida tablero/salida/index.html
#    Con datos de prueba: py tablero/generar_tablero.py --fixture tablero/fixture_demo.json --salida tablero/salida/demo.html
#
#  Lee SOLO la variable DATABASE_URL_TABLERO (rol tablero_lectura), nunca DATABASE_URL
#  (propietario). Si la conexión no es tablero_lectura, se detiene sin generar nada (D-14).
#
#  El HTML resultante no contiene credenciales ni consulta nada: es una foto del
#  avance al momento de generarse. Se puede abrir desde cualquier navegador.
#
#  DEPENDENCIAS: psycopg2-binary (solo si se conecta a la base).
# =====================================================================================

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

CR_TZ = timezone(timedelta(hours=-6))

VISTAS = {
    "resumen":     "SELECT * FROM mgn.v_tab_resumen",
    "encuestador": "SELECT * FROM mgn.v_tab_encuestador",
    "diario":      "SELECT * FROM mgn.v_tab_diario",
    "puntos":      "SELECT * FROM mgn.v_tab_puntos",
    "movimientos": "SELECT * FROM mgn.v_tab_movimientos",
}

ESTADOS = [
    # clave, etiqueta, color (paleta de estado), símbolo
    ("visitada",      "Visitada",       "#0ca30c", "✓"),
    ("revisita",      "Revisita",       "#ec835a", "↻"),
    ("no_localizada", "No localizada",  "#fab219", "?"),
    ("rechazo",       "Rechazo",        "#d03b3b", "✕"),
    ("pendiente",     "Pendiente",      "#898781", "·"),
]
ROL_TABLERO = "tablero_lectura"
ESTADO_COLOR = {k: c for k, _, c, _ in ESTADOS}
ESTADO_LABEL = {k: l for k, l, _, _ in ESTADOS}

LOTE_COLOR = {"A": "#2a78d6", "B": "#eb6834"}   # categóricos 1 y 2, orden fijo


# -------------------------------------------------------------------------------------
#  Obtención de datos
# -------------------------------------------------------------------------------------

def leer_base(url):
    import psycopg2
    import psycopg2.extras
    datos = {}
    with psycopg2.connect(url) as con:
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT current_user AS u")
            usuario = cur.fetchone()["u"]
            if usuario != ROL_TABLERO:
                sys.exit(f"La conexión es '{usuario}', no '{ROL_TABLERO}'. "
                         "El tablero solo lee con el rol de solo lectura.")
            for clave, sql in VISTAS.items():
                cur.execute(sql)
                filas = [dict(r) for r in cur.fetchall()]
                for f in filas:
                    for k, v in f.items():
                        if hasattr(v, "isoformat"):
                            f[k] = v.isoformat()
                        elif v is not None and type(v).__name__ == "Decimal":
                            f[k] = float(v)
                datos[clave] = filas
    return datos


def leer_fixture(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------------------------------------------
#  Utilidades de render
# -------------------------------------------------------------------------------------

def esc(s):
    return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def json_en_script(obj, **kw):
    """JSON seguro dentro de <script>: '<' como \\u003c impide que un dato cierre la
    etiqueta con '</script>' o abra '<!--' (D-14)."""
    return json.dumps(obj, **kw).replace("<", "\\u003c")


def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")


def fecha_corta(iso):
    if not iso:
        return "—"
    try:
        d = datetime.fromisoformat(str(iso))
        if d.tzinfo:
            d = d.astimezone(CR_TZ)
        return d.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso)[:16]


def barras_horizontales(filas, campo_label, campo_valor, color_por=None, ancho=560):
    """Barras horizontales finas con etiqueta directa. filas ya ordenadas."""
    if not filas:
        return '<p class="vacio">Sin datos todavía.</p>'
    maxv = max(float(f[campo_valor]) for f in filas) or 1
    alto_fila, h_barra = 30, 14
    alto = alto_fila * len(filas) + 8
    lab_w = 150
    plot_w = ancho - lab_w - 60
    out = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Barras">']
    for i, f in enumerate(filas):
        y = i * alto_fila + 8
        v = float(f[campo_valor])
        w = max(0, (v / maxv) * plot_w)
        color = LOTE_COLOR.get(f.get(color_por), "#2a78d6") if color_por else "#2a78d6"
        label = esc(f[campo_label])
        out.append(f'<text x="{lab_w-8}" y="{y+h_barra-3}" text-anchor="end" class="lbl">{label}</text>')
        out.append(f'<rect x="{lab_w}" y="{y}" width="{w:.1f}" height="{h_barra}" rx="3" fill="{color}">'
                   f'<title>{label}: {fmt_int(v)}</title></rect>')
        out.append(f'<text x="{lab_w + w + 6:.1f}" y="{y+h_barra-3}" class="val">{fmt_int(v)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def barras_diarias(filas, ancho=560, alto=180):
    """Barras agrupadas por día, una serie por lote."""
    if not filas:
        return '<p class="vacio">Sin visitas registradas todavía.</p>'
    dias = sorted({f["dia"] for f in filas})
    lotes = sorted({f["lote"] for f in filas})
    val = {(f["dia"], f["lote"]): float(f["visitas"]) for f in filas}
    maxv = max(val.values()) or 1
    m_l, m_r, m_t, m_b = 36, 10, 10, 28
    pw, ph = ancho - m_l - m_r, alto - m_t - m_b
    gw = pw / max(len(dias), 1)
    bw = max(4, min(22, (gw - 8) / max(len(lotes), 1) - 2))
    out = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Visitas por día">']
    # líneas de rejilla (3)
    for k in range(1, 4):
        yy = m_t + ph - ph * k / 3
        out.append(f'<line x1="{m_l}" x2="{ancho-m_r}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/>')
        out.append(f'<text x="{m_l-6}" y="{yy+4:.1f}" text-anchor="end" class="tick">{fmt_int(round(maxv*k/3))}</text>')
    out.append(f'<line x1="{m_l}" x2="{ancho-m_r}" y1="{m_t+ph}" y2="{m_t+ph}" class="axis"/>')
    for i, d in enumerate(dias):
        x0 = m_l + i * gw + (gw - (bw + 2) * len(lotes)) / 2
        for j, l in enumerate(lotes):
            v = val.get((d, l), 0)
            h = ph * v / maxv
            x = x0 + j * (bw + 2)
            y = m_t + ph - h
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" '
                       f'fill="{LOTE_COLOR.get(l, "#2a78d6")}"><title>{esc(d)} · Lote {esc(l)}: {fmt_int(v)}</title></rect>')
        etiqueta = str(d)[5:] if len(str(d)) >= 10 else str(d)
        out.append(f'<text x="{m_l + i*gw + gw/2:.1f}" y="{alto-8}" text-anchor="middle" class="tick">{esc(etiqueta)}</text>')
    out.append("</svg>")
    return "\n".join(out)


# -------------------------------------------------------------------------------------
#  Plantilla
# -------------------------------------------------------------------------------------

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surf:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10);--a:#2a78d6;--b:#eb6834}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--page:#0d0d0d;--surf:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);--a:#3987e5;--b:#d95926}}
:root[data-theme=dark]{color-scheme:dark;--page:#0d0d0d;--surf:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;
--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);--a:#3987e5;--b:#d95926}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:20px 16px 8px;max-width:1100px;margin:0 auto}
header h1{font-size:20px;margin:0 0 2px;font-weight:650}
header .sub{color:var(--ink2);font-size:13px}
main{max-width:1100px;margin:0 auto;padding:8px 16px 40px;display:grid;gap:14px;grid-template-columns:1fr}
@media(min-width:760px){main{grid-template-columns:1fr 1fr}.span2{grid-column:1/-1}}
.card{background:var(--surf);border:1px solid var(--ring);border-radius:10px;padding:14px 16px}
.card h2{font-size:14px;font-weight:600;margin:0 0 10px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}
.hero{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.hero .big{font-size:44px;font-weight:700;line-height:1}
.hero .ctx{color:var(--ink2)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-top:10px}
.tile{border:1px solid var(--ring);border-radius:8px;padding:10px 12px}
.tile .k{font-size:12px;color:var(--muted)}
.tile .v{font-size:22px;font-weight:650;font-variant-numeric:tabular-nums}
.tile .v small{font-size:12px;font-weight:400;color:var(--ink2);margin-left:4px}
.lote{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--ink2);margin:6px 0 2px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.chart{width:100%;height:auto;display:block}
.chart .lbl{font-size:12px;fill:var(--ink2)}
.chart .val{font-size:12px;fill:var(--ink);font-variant-numeric:tabular-nums}
.chart .tick{font-size:11px;fill:var(--muted)}
.chart .grid{stroke:var(--grid);stroke-width:1}
.chart .axis{stroke:var(--axis);stroke-width:1}
.chart rect:hover{opacity:.8}
#mapa{height:420px;border-radius:8px;border:1px solid var(--ring)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--muted);font-weight:500;border-bottom:1px solid var(--grid);padding:6px 6px}
td{padding:6px 6px;border-bottom:1px solid var(--grid);vertical-align:top}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:1px 8px;border-radius:999px;border:1px solid var(--ring)}
.pill i{width:8px;height:8px;border-radius:50%;display:inline-block}
.vacio{color:var(--muted);font-size:13px;margin:0}
footer{text-align:center;color:var(--muted);font-size:12px;padding:12px 16px 30px}
.leaflet-container{background:var(--page)}
@media(max-width:600px){td,th{padding:6px 4px}}
"""


def render(datos, generado):
    res = datos.get("resumen", [])
    enc = datos.get("encuestador", [])
    dia = datos.get("diario", [])
    pts = datos.get("puntos", [])
    mov = datos.get("movimientos", [])

    total = sum(int(r["fincas"]) for r in res)
    # Avance = solo estados terminales (D-15): revisita es incidencia, no avance.
    hechas = sum(int(r["visitadas"]) + int(r["no_localizadas"]) + int(r["rechazos"]) for r in res)
    pct = (100.0 * hechas / total) if total else 0.0
    visitadas = sum(int(r["visitadas"]) for r in res)
    incid = sum(int(r["no_localizadas"]) + int(r["rechazos"]) + int(r["revisitas"]) for r in res)
    ult = max((r.get("ultima_visita") or "" for r in res), default="")

    # --- resumen por lote
    tiles_lote = []
    for r in res:
        l = r["lote"]
        f = int(r["fincas"])
        cerradas = int(r["visitadas"]) + int(r["no_localizadas"]) + int(r["rechazos"])
        tiles_lote.append(f"""
        <div class="tile"><div class="k"><span class="lote" style="background:{LOTE_COLOR.get(l,'#2a78d6')}"></span>Lote {esc(l)}</div>
          <div class="v">{fmt_int(cerradas)}<small>de {fmt_int(f)} · {(100.0 * cerradas / f if f else 0.0):.1f}%</small></div>
          <div class="k">{fmt_int(r['visitadas'])} visitadas · {fmt_int(int(r['no_localizadas'])+int(r['rechazos'])+int(r['revisitas']))} incidencias</div>
        </div>""")

    # --- por persona
    enc_sorted = sorted(enc, key=lambda x: -float(x["visitas"]))
    svg_enc = barras_horizontales(enc_sorted, "persona", "visitas", color_por="lote")

    # --- diario
    svg_dia = barras_diarias(dia)
    tabla_dia = ""
    if dia:
        filas = "".join(f"<tr><td>{esc(d['dia'])}</td><td>Lote {esc(d['lote'])}</td><td class='num'>{fmt_int(d['visitas'])}</td></tr>" for d in dia)
        tabla_dia = f"<details><summary style='font-size:12px;color:var(--muted);cursor:pointer'>Ver como tabla</summary><table><tr><th>Día</th><th>Lote</th><th style='text-align:right'>Visitas</th></tr>{filas}</table></details>"

    # --- leyenda estados
    leg_est = "".join(f'<span><i style="background:{c};width:10px;height:10px;border-radius:50%;display:inline-block"></i>{s} {l}</span>'
                      for _, l, c, s in ESTADOS)

    # --- movimientos
    filas_mov = "".join(
        f"<tr><td>{esc(m['cuando'])}</td><td>{esc(m['persona'])}</td><td>{esc(m['finca_id'])} <span style='color:var(--muted)'>· L{esc(m['lote'])}</span></td>"
        f"<td><span class='pill'><i style='background:{ESTADO_COLOR.get(m['estado_visita'],'#898781')}'></i>{esc(ESTADO_LABEL.get(m['estado_visita'], m['estado_visita']))}</span></td></tr>"
        for m in mov) or "<tr><td colspan=4 class='vacio'>Sin movimientos todavía.</td></tr>"

    # --- puntos para el mapa
    puntos_js = json_en_script([
        {"i": p["finca_id"], "l": p["lote"], "e": p["estado_visita"], "p": p.get("persona") or "",
         "c": p.get("cuando") or "", "y": round(float(p["lat"]), 6), "x": round(float(p["lon"]), 6)}
        for p in pts if p.get("lat") is not None], ensure_ascii=False, separators=(",", ":"))
    colores_js = json_en_script(ESTADO_COLOR)
    labels_js = json_en_script(ESTADO_LABEL, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Avance del operativo</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>{CSS}</style></head>
<body>
<header>
  <h1>Avance del operativo de campo</h1>
  <div class="sub">Distrito 20205 · generado {esc(generado)} (hora de Costa Rica) · última visita registrada {esc(fecha_corta(ult))}</div>
</header>
<main>
  <section class="card span2">
    <h2>Avance general</h2>
    <div class="hero"><div class="big">{pct:.1f}%</div><div class="ctx">{fmt_int(hechas)} de {fmt_int(total)} fincas con visita cerrada · {fmt_int(visitadas)} visitadas · {fmt_int(incid)} incidencias</div></div>
    <div class="tiles">{''.join(tiles_lote)}</div>
  </section>

  <section class="card">
    <h2>Visitas por persona</h2>
    <div class="legend"><span><i class="lote" style="background:{LOTE_COLOR['A']}"></i>Lote A</span><span><i class="lote" style="background:{LOTE_COLOR['B']}"></i>Lote B</span></div>
    {svg_enc}
  </section>

  <section class="card">
    <h2>Visitas por día</h2>
    <div class="legend"><span><i class="lote" style="background:{LOTE_COLOR['A']}"></i>Lote A</span><span><i class="lote" style="background:{LOTE_COLOR['B']}"></i>Lote B</span></div>
    {svg_dia}
    {tabla_dia}
  </section>

  <section class="card span2">
    <h2>Mapa de fincas por estado</h2>
    <div class="legend">{leg_est}</div>
    <div id="mapa"></div>
  </section>

  <section class="card span2">
    <h2>Últimos movimientos</h2>
    <table><tr><th>Cuándo</th><th>Persona</th><th>Finca</th><th>Estado</th></tr>{filas_mov}</table>
  </section>
</main>
<footer>Tablero estático. No contiene credenciales ni consulta la base al abrirse. Se regenera de forma programada.</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
(function(){{
  var P={puntos_js}, C={colores_js}, N={labels_js};
  function h(s){{return String(s).replace(/[&<>"']/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c];}});}}
  var el=document.getElementById('mapa');
  if(typeof L==='undefined'){{ el.innerHTML='<p class="vacio" style="padding:14px">El mapa necesita conexión a internet para cargar la cartografía base. Las cifras de arriba no dependen de ello.</p>'; return; }}
  if(!P.length) return;
  var m=L.map('mapa',{{scrollWheelZoom:false}});
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap'}}).addTo(m);
  var g=L.featureGroup();
  P.forEach(function(p){{
    var pend=p.e==='pendiente';
    L.circleMarker([p.y,p.x],{{radius:pend?3:5,color:'#fcfcfb',weight:pend?0:1.5,fillColor:C[p.e]||'#898781',fillOpacity:pend?.55:.95}})
     .bindPopup('<b>Finca '+h(p.i)+'</b> · Lote '+h(p.l)+'<br>'+h(N[p.e]||p.e)+(p.p?'<br>'+h(p.p):'')+(p.c?' · '+h(p.c):''))
     .addTo(g);
  }});
  g.addTo(m); m.fitBounds(g.getBounds().pad(0.05));
}})();
</script>
</body></html>"""


# -------------------------------------------------------------------------------------
#  Principal
# -------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="tablero/index.html")
    ap.add_argument("--fixture", help="JSON con las cinco vistas, para probar sin base")
    ap.add_argument("--volcar", help="Guardar los datos leídos de la base en este JSON (para depurar)")
    a = ap.parse_args()

    if a.fixture:
        datos = leer_fixture(a.fixture)
    else:
        url = os.environ.get("DATABASE_URL_TABLERO")
        if not url:
            sys.exit("Falta DATABASE_URL_TABLERO (o usar --fixture).")
        datos = leer_base(url)
        if a.volcar:
            with open(a.volcar, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=1, default=str)

    generado = datetime.now(CR_TZ).strftime("%d/%m/%Y %H:%M")
    html = render(datos, generado)
    os.makedirs(os.path.dirname(a.salida) or ".", exist_ok=True)
    with open(a.salida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Tablero escrito en {a.salida} ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
