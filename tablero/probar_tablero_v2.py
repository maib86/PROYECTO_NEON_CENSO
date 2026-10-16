#!/usr/bin/env python3
# =====================================================================================
#  PRUEBAS AUTOMÁTICAS DEL TABLERO V2 (spec S08c, paso 7)
# =====================================================================================
#  1. Texto del HTML: términos vedados = 0 en el HTML completo, tamaño < 2,5 MB. Única
#     excepción: \bproxy\b, cuya sola coincidencia admitida es la clase interna
#     «leaflet-proxy» de la biblioteca embebida (sesión 10). Nombres técnicos de cuenta = 0.
#  2. Playwright a 1100 y 400 px: errores de consola, indicadores = resumen_bd, línea de
#     ubicación, ausencia de selects de provincia/cantón/distrito, filtros por lote de
#     trabajo y por UGM, buscador (258 → lote de trabajo B), ficha sin el término vedado,
#     cambio manual a «Mapa claro», hash de la URL, reinicio de niveles inferiores, Estado
#     ortogonal, movimientos solo con guardados, encuestadores y actividad contra los datos,
#     y vocabulario D-25 sobre el texto renderizado (página, fichas y tooltips) con
#     verificar_vocabulario.revisar. Capturas en --dir.
#
#  USO
#    py tablero/probar_tablero_v2.py tablero/salida/v2/index.html --dir docs/evidencia/s08c
#    py tablero/probar_tablero_v2.py https://… --dir docs/evidencia/s08c --prefijo publicado_
#  Sale con código 1 si alguna prueba falla. No toca la base de datos.
# =====================================================================================

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs" / "requerimientos_ti"))
from generar_tablero import fmt_incidencias  # noqa: E402
from verificar_vocabulario import revisar  # noqa: E402

VEDADOS = [r"observaciones", r"posicion_registro", r"sin cerrar", r"\bproxy\b", r"mosaico",
           r"\bfincas?\b", r"neon\.tech", r"npg_", r"postgres(ql)?://", r"\bla base\b(?! de datos)",
           r"neondb_owner|edit_lote_[ab]"]
LIMITE_BYTES = int(2.5 * 1024 * 1024)
UBICACION = "Alajuela › San Ramón › Piedades Sur (20205)"

resultados = []


def ok(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond), detalle))
    print(f"[{'OK' if cond else 'FALLA'}] {nombre}" + (f" · {detalle}" if detalle else ""))


def sin_biblioteca(html):
    return re.sub(r"<!--[^>]*Inicio de biblioteca embebida\. -->.*?<!-- Fin de biblioteca embebida\. -->",
                  " ", html, flags=re.S)


def pruebas_texto(html):
    b = len(html.encode("utf-8"))
    ok("Tamaño del HTML < 2,5 MB", b < LIMITE_BYTES, f"{b} bytes ({b / 1048576:.2f} MB)")
    resto = sin_biblioteca(html)
    for pat in VEDADOS:
        n_todo = len(re.findall(pat, html, re.I))
        n_resto = len(re.findall(pat, resto, re.I))
        det = f"HTML completo {n_todo} · fuera de la biblioteca embebida {n_resto}"
        if pat == r"\bproxy\b":
            ctx = [html[max(0, m.start() - 8):m.end()] for m in re.finditer(pat, html, re.I)]
            det += f" · coincidencias: {ctx}"
            cumple = n_resto == 0 and n_todo <= 1 and all(c.endswith("leaflet-proxy") for c in ctx)
            ok(f"grep -i {pat}: solo «leaflet-proxy» de la biblioteca", cumple, det)
        else:
            ok(f"grep -i {pat} = 0", n_todo == 0, det)
    datos = json.loads(re.search(r'<script id="datos" type="application/json">(.*?)</script>',
                                 html, re.S).group(1))
    return datos


def total(pg):
    return int(pg.evaluate("() => document.getElementById('indicadores').dataset.total"))


def pruebas_filtros(pg, tag, datos, url):
    """Hash, reinicio de niveles, Estado ortogonal y tablas contra los datos embebidos."""
    from datetime import date, timedelta
    regs = datos["registros"]
    pg.goto(url.split("#")[0] + "#lote=B", wait_until="load")
    pg.wait_for_timeout(1500)
    ok(f"{tag}: abrir con #lote=B → Total 723 y select en B",
       total(pg) == 723 and pg.input_value("#f-lote") == "B", f"{total(pg)} · {pg.input_value('#f-lote')}")
    if not pg.is_visible("#f-lote"):
        pg.click("#btn-filtros")
    pg.select_option("#f-est", "visitada")
    pg.wait_for_timeout(200)
    pg.select_option("#f-lote", "A")
    pg.wait_for_timeout(200)
    esperado = sum(1 for r in regs if r["lote"] == "A" and r["est"] == "visitada")
    ok(f"{tag}: Estado no se reinicia al cambiar lote de trabajo",
       pg.input_value("#f-est") == "visitada" and total(pg) == esperado, f"{total(pg)} vs {esperado}")
    upm = next(r["upm"] for r in regs if r["lote"] == "A")
    pg.select_option("#f-upm", upm)
    pg.wait_for_timeout(200)
    ok(f"{tag}: cambiar UPM reinicia lote de trabajo (nivel inferior)", pg.input_value("#f-lote") == "",
       f"lote={pg.input_value('#f-lote')!r}")
    pg.click("#limpiar")
    pg.wait_for_timeout(200)
    pg.select_option("#f-lote", "B")
    pg.wait_for_timeout(300)
    filas = pg.eval_on_selector_all("#tabla-movimientos tbody tr", "rs => rs.map(r => r.innerText)")
    ok(f"{tag}: movimientos del lote de trabajo B sin pendientes y no más de 25",
       bool(filas) and len(filas) <= 25 and not any("Pendiente" in f for f in filas), f"{len(filas)} filas")
    pg.click("#limpiar")
    pg.wait_for_timeout(300)
    guard = pg.eval_on_selector_all("#tabla-encuestadores tbody tr td:nth-child(3)",
                                    "ts => ts.map(t => Number(t.innerText.split('.').join('')))")
    esperado = sum(1 for r in regs if r["est"] != "pendiente")
    ok(f"{tag}: encuestadores: suma de guardados = {esperado}", sum(guard) == esperado, str(guard))
    nombres = pg.eval_on_selector_all("#tabla-encuestadores tbody tr td:first-child", "ts => ts.map(t => t.innerText)")
    ok(f"{tag}: ningún guardado como «sin encuestador registrado»",
       "sin encuestador registrado" not in nombres, str(nombres))
    fin = date.fromisoformat(datos["meta"]["generado_en"][:10])
    dias = {(fin - timedelta(days=i)).isoformat() for i in range(14)}
    esperado = sum(1 for r in regs if r["est"] in ("visitada", "no_localizada", "rechazo")
                   and r.get("fv") and r["fv"][:10] in dias)
    txt = pg.inner_text("#actividad .vacio")
    ok(f"{tag}: actividad diaria = {esperado} concluidas en 14 días", txt.startswith(f"{esperado} "), txt)


def pruebas_navegador(url, rb, carpeta, prefijo, datos):
    from playwright.sync_api import sync_playwright
    carpeta.mkdir(parents=True, exist_ok=True)
    esperado_inc = fmt_incidencias(rb["incidencias"], rb["revisitas"])
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for ancho in (1100, 400):
            pg = nav.new_page(viewport={"width": ancho, "height": 900}, device_scale_factor=1,
                              timezone_id="America/Costa_Rica")
            errores = []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
            pg.goto(url, wait_until="load")
            pg.wait_for_timeout(3500)
            tag = f"{ancho} px"
            ind = pg.evaluate("() => ({...document.getElementById('indicadores').dataset})")
            ok(f"{tag}: Total = resumen_bd.total", int(ind["total"]) == rb["total"], f"{ind['total']} vs {rb['total']}")
            ok(f"{tag}: concluidas = resumen_bd", int(ind["concluidas"]) == rb["concluidas"], f"{ind['concluidas']} vs {rb['concluidas']}")
            ok(f"{tag}: incidencias = resumen_bd", int(ind["incidencias"]) == rb["incidencias"], f"{ind['incidencias']} vs {rb['incidencias']}")
            ok(f"{tag}: revisitas = resumen_bd", int(ind["revisitas"]) == rb["revisitas"], f"{ind['revisitas']} vs {rb['revisitas']}")
            etiqueta = pg.inner_text("#ind-incidencias .d")
            ok(f"{tag}: etiqueta D-27 igual a fmt_incidencias", etiqueta == esperado_inc, f"«{etiqueta}»")
            ubic = pg.inner_text("#ubicacion-texto")
            ok(f"{tag}: línea de ubicación exacta", ubic == UBICACION, f"«{ubic}»")
            sels = pg.evaluate("() => [...document.querySelectorAll('select')].map(s => s.id)")
            ok(f"{tag}: sin select de provincia, cantón ni distrito",
               not any(s in sels for s in ("f-cprov", "f-ccant", "f-cdist")), f"selects: {sels}")
            ok(f"{tag}: selects UPM, UGM, lote de trabajo, encuestador y estado",
               all(s in sels for s in ("f-upm", "f-ugm", "f-lote", "f-encv", "f-est")))
            scroll = pg.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
            ok(f"{tag}: sin desplazamiento horizontal de la página", not scroll)
            pg.screenshot(path=str(carpeta / f"{prefijo}captura_{ancho}.png"), full_page=True)
            if ancho == 400:
                pg.click("#btn-filtros")
            # Lote de trabajo A / B
            for lote, esperado in (("A", 709), ("B", 723)):
                pg.select_option("#f-lote", lote)
                pg.wait_for_timeout(300)
                t = int(pg.evaluate("() => document.getElementById('indicadores').dataset.total"))
                ok(f"{tag}: lote de trabajo {lote} → Total {esperado}", t == esperado, str(t))
            pg.select_option("#f-lote", "")
            # Una UGM: Total = su conteo en la opción
            opt = pg.evaluate("""() => { const o = [...document.querySelectorAll('#f-ugm option')].find(o => o.value && o.value !== '__nulo__');
                                         return {v: o.value, t: o.textContent}; }""")
            pg.select_option("#f-ugm", opt["v"])
            pg.wait_for_timeout(300)
            n_opt = int(re.search(r"\(([\d.]+)\)$", opt["t"]).group(1).replace(".", ""))
            t = int(pg.evaluate("() => document.getElementById('indicadores').dataset.total"))
            n_datos = sum(1 for r in datos["registros"] if r["ugm"] == opt["v"])
            ok(f"{tag}: UGM {opt['v']} → Total = su conteo en los datos", t == n_opt == n_datos,
               f"{t} vs «{opt['t']}» vs {n_datos}")
            ok(f"{tag}: estado del filtro en el hash", f"ugm={opt['v']}" in pg.evaluate("() => location.hash"),
               pg.evaluate("() => location.hash"))
            if ancho == 1100:
                pg.screenshot(path=str(carpeta / f"{prefijo}captura_{ancho}_filtro_ugm.png"), full_page=False)
            pg.click("#limpiar")
            pg.wait_for_timeout(300)
            # Buscador 258
            pg.fill("#buscar", "258")
            pg.press("#buscar", "Enter")
            pg.wait_for_timeout(1200)
            pop = pg.inner_text(".leaflet-popup-content") if pg.query_selector(".leaflet-popup-content") else ""
            ok(f"{tag}: buscar 258 abre su ficha con lote de trabajo B",
               "Polígono 258" in pop and re.search(r"Lote de trabajo\s+B", pop) is not None, pop.replace("\n", " | ")[:160])
            pg.screenshot(path=str(carpeta / f"{prefijo}captura_{ancho}_ficha_258.png"), full_page=False)
            # Ficha de un polígono visitado
            vid = pg.evaluate("() => TABLERO.datos.registros.find(r => r.est === 'visitada').id")
            pg.evaluate(f"() => TABLERO.irA({vid})")
            pg.wait_for_timeout(800)
            pop = pg.inner_text(".leaflet-popup-content")
            ok(f"{tag}: ficha de un polígono visitado sin el término vedado",
               "Visitada" in pop and "observaciones" not in pop.lower(), f"id {vid}")
            # Vocabulario D-25 del texto renderizado: página, todas las fichas y tooltips
            texto = pg.evaluate("""() => { const t = [];
                TABLERO.mapa.eachLayer(l => { const tt = l.getTooltip && l.getTooltip(), pp = l.getPopup && l.getPopup();
                  if (tt) t.push(String(tt.getContent())); if (pp) t.push(String(pp.getContent())); });
                const d = document.createElement('div'); d.innerHTML = t.join(' ').split('<').join(' <');
                return document.body.innerText + ' ' + d.textContent; }""")
            fallas, _ = revisar(f"renderizado {ancho}", texto)
            ok(f"{tag}: vocabulario D-25 en página, fichas y tooltips = 0 prohibidos", not fallas, "; ".join(fallas[:3]))
            ok(f"{tag}: sin nombres técnicos de cuenta en el texto",
               re.search(r"neondb_owner|edit_lote_[ab]", texto) is None)
            # Búsqueda inexistente
            if not pg.is_visible("#buscar"):
                pg.click("#btn-filtros")          # a 400 px el panel se pliega tras buscar
            pg.fill("#buscar", "999999")
            pg.press("#buscar", "Enter")
            pg.wait_for_timeout(300)
            ok(f"{tag}: id inexistente → «sin resultados»", pg.inner_text("#busqueda-msg") == "sin resultados")
            # Cambio manual a Mapa claro
            pg.keyboard.press("Escape")
            pg.hover(".leaflet-control-layers")
            pg.wait_for_timeout(300)
            pg.get_by_label("Mapa claro").check()
            pg.wait_for_timeout(1500)
            claro = pg.evaluate("() => TABLERO.mapa.hasLayer(TABLERO.capas.osm) && !TABLERO.mapa.hasLayer(TABLERO.capas.esri)")
            ok(f"{tag}: cambio manual a «Mapa claro»", claro)
            info = pg.evaluate("""() => ({sat: TABLERO.mapa.hasLayer(TABLERO.capas.esri),
                teselas: [...document.querySelectorAll('img.leaflet-tile')].filter(t => t.complete && t.naturalWidth > 0).length})""")
            print(f"     teselas cargadas tras el cambio: {info['teselas']}")
            pruebas_filtros(pg, tag, datos, url)
            ok(f"{tag}: 0 errores de consola", not errores, str(errores[:3]))
            pg.close()
        nav.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="Ruta local o URL https")
    ap.add_argument("--dir", default="docs/evidencia/s08c")
    ap.add_argument("--prefijo", default="")
    a = ap.parse_args()
    if a.html.startswith("http"):
        import urllib.request
        with urllib.request.urlopen(a.html) as r:
            html = r.read().decode("utf-8")
        url = a.html
    else:
        html = Path(a.html).read_text(encoding="utf-8")
        url = Path(a.html).resolve().as_uri()
    datos = pruebas_texto(html)
    print(f"     resumen_bd: {datos['resumen_bd']} · generado_en: {datos['meta']['generado_en']}")
    pruebas_navegador(url, datos["resumen_bd"], Path(a.dir), a.prefijo, datos)
    fallas = [r for r in resultados if not r[1]]
    print(f"\nResultado: {len(resultados) - len(fallas)} de {len(resultados)} pruebas OK · {len(fallas)} fallas")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
