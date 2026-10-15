#!/usr/bin/env python3
# =====================================================================================
#  CAPTURAS DEL TABLERO (criterio 5 de la Fase 2)
# =====================================================================================
#  Abre un HTML ya generado en Chromium headless y guarda capturas de página completa
#  a 1100 px (escritorio) y 400 px (celular). Informa errores de JavaScript, diálogos,
#  marcadores del mapa, teselas cargadas, elementos que desbordan el ancho y la letra
#  efectiva mínima de los gráficos SVG (que se escalan con el ancho; debe ser >= 11 px).
#  Las cifras de consola no sustituyen la revisión visual de las capturas.
#
#  USO
#    py tablero/capturar_tablero.py tablero/salida/index.html --dir tablero/salida
#    py tablero/capturar_tablero.py tablero/salida/sim.html --dir tablero/salida/sim --anchos 400 --cpu-lento 4
#  Tiempos que informa: carga_ms (evento load: incluye el script del mapa, que corre al
#  final del body, es decir, todos los marcadores dibujados), dcl_ms (DOMContentLoaded),
#  red_quieta_ms (hasta networkidle, con teselas; None si no se alcanza en 60 s), además
#  de nodos del DOM y memoria JS. --cpu-lento N frena la CPU N veces (CDP) para
#  aproximar un celular.
#
#  No toca la base ni lee credenciales: solo abre el archivo local. El mapa base
#  (teselas de OpenStreetMap) y Leaflet se cargan de internet.
#
#  DEPENDENCIAS: playwright (navegador: py -m playwright install chromium).
# =====================================================================================

import argparse
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ANCHOS = [1100, 400]


def capturar(html, carpeta, anchos=ANCHOS, cpu_lento=1):
    url = Path(html).resolve().as_uri()
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for ancho in anchos:
            pg = nav.new_page(viewport={"width": ancho, "height": 900},
                              device_scale_factor=1, timezone_id="America/Costa_Rica")
            pg.set_default_timeout(180000)
            if cpu_lento > 1:
                pg.context.new_cdp_session(pg).send("Emulation.setCPUThrottlingRate",
                                                    {"rate": cpu_lento})
            errores, dialogos = [], []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.on("dialog", lambda d: (dialogos.append(d.message), d.dismiss()))
            t0 = time.perf_counter()
            pg.goto(url, wait_until="load")
            try:
                pg.wait_for_load_state("networkidle", timeout=60000)
                red_quieta_ms = round((time.perf_counter() - t0) * 1000)
            except Exception:
                red_quieta_ms = None
            pg.wait_for_timeout(1500)            # teselas del mapa
            info = pg.evaluate("""() => {
                const vw = document.documentElement.clientWidth;
                const anchos = [...document.querySelectorAll('body *')]
                    .filter(e => { const c = e.closest('.leaflet-container');
                                   return !c || c === e; })          // el mapa recorta su interior
                    .filter(e => e.getBoundingClientRect().right > vw + 1)
                    .map(e => e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : ''));
                const tiles = [...document.querySelectorAll('img.leaflet-tile')];
                // Letra efectiva de los gráficos SVG: font-size × escala del viewBox.
                const efectivas = [...document.querySelectorAll('svg.chart text')].map(t => {
                    const svg = t.ownerSVGElement;
                    const esc = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
                    return parseFloat(getComputedStyle(t).fontSize) * esc;
                });
                const nv = performance.getEntriesByType('navigation')[0];
                return {
                    carga_ms: Math.round(nv.loadEventEnd),
                    dcl_ms: Math.round(nv.domContentLoadedEventEnd),
                    letra_svg_min_px: efectivas.length ? Math.round(Math.min(...efectivas) * 10) / 10 : null,
                    scroll_horizontal: document.documentElement.scrollWidth > vw,
                    desbordan: [...new Set(anchos)].slice(0, 10),
                    marcadores: document.querySelectorAll('path.leaflet-interactive').length,
                    teselas: tiles.length,
                    teselas_cargadas: tiles.filter(t => t.complete && t.naturalWidth > 0).length,
                    alto: document.documentElement.scrollHeight,
                    nodos_dom: document.getElementsByTagName('*').length,
                    memoria_js_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null,
                };
            }""")
            salida = carpeta / f"captura_{ancho}.png"
            pg.screenshot(path=str(salida), full_page=True)
            info["red_quieta_ms"] = red_quieta_ms
            if cpu_lento > 1:
                info["cpu_lento"] = cpu_lento
            print(f"{ancho}px -> {salida} | errores JS: {errores} | dialogos: {dialogos} | {info}")
            pg.close()
        nav.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--dir", default="tablero/salida")
    ap.add_argument("--anchos", type=int, nargs="+", default=ANCHOS)
    ap.add_argument("--cpu-lento", type=float, default=1,
                    help="Factor de freno de CPU (CDP); 1 = sin freno")
    a = ap.parse_args()
    capturar(a.html, a.dir, a.anchos, a.cpu_lento)


if __name__ == "__main__":
    main()
