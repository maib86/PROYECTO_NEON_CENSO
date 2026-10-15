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
#
#  No toca la base ni lee credenciales: solo abre el archivo local. El mapa base
#  (teselas de OpenStreetMap) y Leaflet se cargan de internet.
#
#  DEPENDENCIAS: playwright (navegador: py -m playwright install chromium).
# =====================================================================================

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

ANCHOS = [1100, 400]


def capturar(html, carpeta):
    url = Path(html).resolve().as_uri()
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for ancho in ANCHOS:
            pg = nav.new_page(viewport={"width": ancho, "height": 900},
                              device_scale_factor=1, timezone_id="America/Costa_Rica")
            errores, dialogos = [], []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.on("dialog", lambda d: (dialogos.append(d.message), d.dismiss()))
            pg.goto(url, wait_until="networkidle")
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
                return {
                    letra_svg_min_px: efectivas.length ? Math.round(Math.min(...efectivas) * 10) / 10 : null,
                    scroll_horizontal: document.documentElement.scrollWidth > vw,
                    desbordan: [...new Set(anchos)].slice(0, 10),
                    marcadores: document.querySelectorAll('path.leaflet-interactive').length,
                    teselas: tiles.length,
                    teselas_cargadas: tiles.filter(t => t.complete && t.naturalWidth > 0).length,
                    alto: document.documentElement.scrollHeight,
                };
            }""")
            salida = carpeta / f"captura_{ancho}.png"
            pg.screenshot(path=str(salida), full_page=True)
            print(f"{ancho}px -> {salida} | errores JS: {errores} | dialogos: {dialogos} | {info}")
            pg.close()
        nav.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--dir", default="tablero/salida")
    a = ap.parse_args()
    capturar(a.html, a.dir)


if __name__ == "__main__":
    main()
