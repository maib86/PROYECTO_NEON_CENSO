"""Exporta REQUERIMIENTOS_TI.md a HTML y PDF con el sistema visual de la presentación interna.

Uso (desde la raíz del repositorio):
    py docs/requerimientos_ti/exportar_pdf.py

Salidas (docs/presentacion/ está ignorada por git, D-24):
    docs/presentacion/REQUERIMIENTOS_TI.html
    docs/presentacion/REQUERIMIENTOS_TI.pdf
Requiere: py -m pip install markdown playwright; py -m playwright install chromium.
El logo se toma de docs/presentacion/activos/inec_logo.png si existe (no se versiona).
"""
import base64
import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
MD = RAIZ / "docs/requerimientos_ti/REQUERIMIENTOS_TI.md"
SALIDA = RAIZ / "docs/presentacion"
LOGO = SALIDA / "activos/inec_logo.png"

CSS = """
:root{--navy:#002F87;--red:#D7282F;--ink:#111827;--paper:#FBFAF8;--rule:#D8D4CC;
  --graphite-ink:#6B7280;--graphite-tinte:#4B5563;--red-ink:#A81D23;
  --sans:"Inter","DM Sans","Segoe UI",system-ui,Arial,sans-serif;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
@page{size:A4;margin:16mm 15mm 16mm 15mm}
html{background:var(--paper)}
body{font-family:var(--serif);color:var(--ink);font-size:10.5pt;line-height:1.42;margin:0}
.head{display:flex;align-items:center;gap:12px;border-bottom:2px solid var(--ink);padding:0 0 8px;margin:0 0 14px}
.head img{height:34px}
.head .who{font-family:var(--sans);font-size:7.5pt;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--graphite-ink);line-height:1.5}
.head .sp{flex:1}
.mark{font-family:var(--mono);font-size:8.5pt;font-weight:700;color:var(--navy);border:1.5px solid var(--navy);padding:2px 8px}
h1{font-weight:400;font-size:21pt;line-height:1.12;margin:0 0 6px}
h2{font-weight:400;font-size:15pt;margin:20px 0 8px;padding-top:6px;border-top:1px solid var(--rule);break-after:avoid}
h3{font-family:var(--sans);font-size:8.5pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--red-ink);margin:14px 0 6px;break-after:avoid}
p{margin:0 0 8px}
hr{border:0;border-top:1px solid var(--rule);margin:12px 0}
code{font-family:var(--mono);font-size:.86em;color:var(--navy)}
pre{font-family:var(--mono);font-size:7.6pt;line-height:1.35;background:#fff;border:1px solid var(--rule);padding:10px;white-space:pre;break-inside:avoid}
pre code{color:var(--ink);font-size:inherit}
table{border-collapse:collapse;width:100%;font-size:8.6pt;margin:4px 0 10px;break-inside:auto}
tr{break-inside:avoid}
th{font-family:var(--sans);font-size:7pt;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--graphite-ink);text-align:left;padding:0 8px 4px 0;border-bottom:1.5px solid var(--ink);vertical-align:bottom}
td{padding:5px 8px 5px 0;border-bottom:1px solid var(--rule);vertical-align:top}
strong{color:var(--ink)}
ol,ul{margin:0 0 8px;padding-left:20px}
li{margin:0 0 4px}
"""


def main() -> int:
    texto = MD.read_text(encoding="utf-8")
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code"])
    logo = ""
    if LOGO.is_file():
        logo = '<img alt="INEC" src="data:image/png;base64,' + base64.b64encode(LOGO.read_bytes()).decode() + '">'
    html = f"""<!DOCTYPE html><html lang="es-CR"><head><meta charset="utf-8">
<title>Requerimientos para producción · Piloto NEON-CENSO</title><style>{CSS}</style></head><body>
<div class="head">{logo}<div class="who">INEC · Unidad de Cartografía<br>Piloto NEON-CENSO</div><div class="sp"></div><div class="mark">NEON-TI-01 · v2</div></div>
{cuerpo}</body></html>"""
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta_html = SALIDA / "REQUERIMIENTOS_TI.html"
    ruta_pdf = SALIDA / "REQUERIMIENTOS_TI.pdf"
    ruta_html.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pag = nav.new_page()
        pag.goto(ruta_html.as_uri())
        pag.pdf(path=str(ruta_pdf), format="A4", print_background=True,
                display_header_footer=True, header_template="<span></span>",
                footer_template='<div style="font-size:7pt;font-family:Segoe UI,Arial;color:#6B7280;width:100%;text-align:center">'
                                'Requerimientos para producción · Piloto NEON-CENSO · página <span class="pageNumber"></span> de <span class="totalPages"></span></div>',
                margin={"top": "16mm", "bottom": "16mm", "left": "15mm", "right": "15mm"})
        nav.close()
    print(f"HTML: {ruta_html.relative_to(RAIZ)} ({ruta_html.stat().st_size} bytes)")
    print(f"PDF:  {ruta_pdf.relative_to(RAIZ)} ({ruta_pdf.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
