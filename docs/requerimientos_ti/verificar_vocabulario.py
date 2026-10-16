"""Busca en las láminas, las notas del orador y REQUERIMIENTOS_TI.md los términos que el
vocabulario único (D-25) prohíbe, y lista para revisión a mano los que solo se permiten en
ciertos sentidos.

Uso (desde la raíz del repositorio):
    py docs/requerimientos_ti/verificar_vocabulario.py [--laminas RUTA.html] [--html PAGINA.html]

FALLA: término prohibido (debe ser 0). REVISAR: término permitido solo en un sentido
(«fincas» para producción, «programa» para la revisión automática, «parte», «UGM»); se
imprime con su contexto para decidir a mano.
En el documento se omiten el anexo E (la propia tabla de vocabulario, que nombra los términos
prohibidos) y el código entre comillas invertidas (nombres técnicos, D-25). En las láminas se
omite el código (<span class="sig">) y el texto de la captura del tablero (es una imagen).
La presentación está fuera del repositorio (D-24): si no existe, se omite y se dice.
Sale con código 1 si hay alguna FALLA.
"""
import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOC = Path(__file__).resolve().parent / "REQUERIMIENTOS_TI.md"
LAMINAS = RAIZ / "docs/presentacion/PRESENTACION_NEON_CENSO_2026-10-19.html"

# (expresión, término único que corresponde). Sin distinguir mayúsculas.
PROHIBIDOS = [
    (r"\bbases?\b(?! de datos)", "«base de datos», nunca «la base» sola"),
    (r"\bpropietari[oa]s?\b", "«cuenta administradora»"),
    (r"neondb_owner", "«cuenta administradora»"),
    (r"\broles?\b", "«cuenta del equipo A/B» / «cuenta del tablero»"),
    (r"\busuarios?\b", "«cuenta»"),
    (r"\bescrituras?\b", "«guardados»"),
    (r"\bcron\b|\bschedule\b|(?<![/.])\bworkflows?\b", "«regeneración automática»"),
    (r"\bcerrad[oa]s?\b|\bcerrar\b", "«visita concluida» / fase «completada»"),
    (r"\bsin cerrar\b", "«revisitas pendientes» (D-27)"),
    (r"\bproxy\b", "«sustituto» / «polígonos UGM (sustituto)» (D-25, S08)"),
    (r"\bmosaicos?\b", "«teselas» (D-25, S08)"),
    (r"\bobjetos?\b", "«polígonos de prueba» / «polígonos UGM (sustituto)»"),
    (r"\bagentes?\b", "«revisión automática independiente»"),
    (r"restauraci[oó]n de (solo )?6|6 h de restauraci[oó]n", "«solo se puede volver atrás 6 horas»"),
    (r"\bTOAST\b|\bEXPLAIN\b|\\timing|\bogr2ogr\b|\bp50\b|\bpared\b|\*/30|\bhash\b|\bendpoint\b|\bop/s\b",
     "fuera de lámina y del documento (D-25)"),
    (r"\blotes?\b(?! de trabajo)", "«lote de trabajo A/B»"),
    (r"\bzonas?\b(?! de equipo| horaria| de sesión)", "«zona de equipo (por definir)» o «zona horaria»"),
    (r"(?<!zona de )(?<!zonas de )\bequipos?\b(?! de campo| [AB]\b)", "«equipo de campo» (personas) / «computadora»"),
]
REVISAR = [r"\bfincas?\b", r"\bprograma\b", r"\bpartes?\b", r"\bUGM\b"]


class Texto(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pila, self.lamina = [], "—"
        self.texto, self.notas = {}, {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section" and "slide" in (a.get("class") or ""):
            self.lamina = a.get("id", "—")
            self.notas[self.lamina] = a.get("data-note", "")
        if tag in ("img", "br", "meta", "link", "input", "hr"):
            return
        oculto = tag in ("style", "script", "title", "head") or "sig" in (a.get("class") or "").split()
        self.pila.append((tag, oculto))

    def handle_endtag(self, tag):
        while self.pila:
            t, _ = self.pila.pop()
            if t == tag:
                break

    def handle_data(self, data):
        if not any(o for _, o in self.pila):
            self.texto[self.lamina] = self.texto.get(self.lamina, "") + " " + data


def revisar(nombre: str, texto: str) -> tuple:
    texto = re.sub(r"\s+", " ", texto)
    fallas, dudas = [], []
    for pat, sug in PROHIBIDOS:
        for m in re.finditer(pat, texto, re.I):
            ctx = texto[max(0, m.start() - 40):m.end() + 40]
            fallas.append(f"FALLA   {nombre}: «{m.group(0)}» → {sug} · …{ctx}…")
    # «RLS» solo como expansión: «control por fila (RLS…»; después, «control por fila».
    rls = [m.start() for m in re.finditer(r"\bRLS\b", texto)]
    buenas = [m.start() + len("control por fila (") for m in re.finditer(r"control por fila \(RLS", texto, re.I)]
    for pos in rls:
        if pos not in buenas:
            fallas.append(f"FALLA   {nombre}: «RLS» fuera de «control por fila (RLS)» · …{texto[max(0, pos - 40):pos + 40]}…")
    for pat in REVISAR:
        for m in re.finditer(pat, texto, re.I):
            dudas.append(f"REVISAR {nombre}: «{m.group(0)}» · …{texto[max(0, m.start() - 50):m.end() + 50]}…")
    return fallas, dudas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--laminas", type=Path, default=LAMINAS)
    ap.add_argument("--sin-revisar", action="store_true", help="no imprimir la lista REVISAR")
    ap.add_argument("--html", type=Path, action="append", default=[],
                    help="otra página HTML (p. ej. tablero/plantilla_v2.html): todo su texto visible")
    args = ap.parse_args()
    fallas, dudas = [], []

    doc = DOC.read_text(encoding="utf-8")
    doc = re.split(r"\n### E\. Vocabulario", doc)[0]       # el anexo E nombra los términos prohibidos
    doc = re.sub(r"```.*?```", " ", doc, flags=re.S)        # bloques de código
    doc = re.sub(r"`[^`]*`", " ", doc)                      # código en línea
    f, d = revisar("REQUERIMIENTOS_TI.md", doc)
    fallas += f
    dudas += d

    if args.laminas.is_file():
        p = Texto()
        p.feed(args.laminas.read_text(encoding="utf-8"))
        texto_todo = " ".join(p.texto.get(l, "") for l in p.notas)
        notas_todo = " ".join(p.notas.values())
        for nombre, t in (("láminas", texto_todo), ("notas", notas_todo)):
            f, d = revisar(nombre, t)
            fallas += f
            dudas += d
    else:
        print(f"presentación no encontrada ({args.laminas}): se omite (D-24)")

    for ruta in args.html:
        p = Texto()
        p.feed(ruta.read_text(encoding="utf-8"))
        f, d = revisar(ruta.name, " ".join(p.texto.values()))
        fallas += f
        dudas += d

    for linea in fallas:
        print(linea)
    if not args.sin_revisar:
        for linea in dudas:
            print(linea)
    print(f"\nprohibidos: {len(fallas)} · para revisar a mano: {len(dudas)}")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
