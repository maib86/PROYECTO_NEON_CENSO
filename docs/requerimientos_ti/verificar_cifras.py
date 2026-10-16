"""Comprueba que cada cifra de CIFRAS.csv aparece, literal, en su archivo de origen, y que cada
cifra citada en el documento para TI y en las láminas tiene su fila.

Uso (desde la raíz del repositorio):
    py docs/requerimientos_ti/verificar_cifras.py [--laminas RUTA.html]

Para cada fila de CIFRAS.csv:
  - el archivo_origen existe;
  - el valor aparece literal en el archivo;
  - si linea_o_consulta es «L<n>», el valor aparece literal en esa línea.
Citas:
  - cada [Cnn] o [Cnn–Cmm] de REQUERIMIENTOS_TI.md tiene fila;
  - en la presentación (D-25), cada data-cifra="Cnn" y cada [Cnn] del texto o de las notas
    tiene fila; si la fila trae valor_pantalla y el elemento cita una sola cifra, el texto en
    pantalla es exactamente valor_pantalla;
  - en el texto visible de las láminas y en las notas (fuera de código, <span class="sig">, y
    sin contar números de sección como «§7.1» ni rótulos de versión como «v4.1»)
    no hay punto decimal («31.80 s»), cifras de 5 o más dígitos sin punto de miles («50794»)
    ni la unidad MiB (una sola unidad: MB).
La presentación está fuera del repositorio (D-24): si no existe, esa parte se omite y se dice.
Sale con código 1 si algo falla. No lee la base ni .env.
"""
import argparse
import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CSV = Path(__file__).resolve().parent / "CIFRAS.csv"
DOC = Path(__file__).resolve().parent / "REQUERIMIENTOS_TI.md"
LAMINAS = RAIZ / "docs/presentacion/PRESENTACION_NEON_CENSO_2026-10-19.html"
COLUMNAS = ["id", "valor", "unidad", "descripcion", "archivo_origen", "linea_o_consulta", "sesion",
            "valor_pantalla"]
VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
# Códigos que no son cantidades y se escriben sin punto de miles.
SIN_MILES = {"20205"}


def citas_en(texto: str) -> set:
    """Ids de [Cnn], [Cnn, Cmm] y [Cnn–Cmm] en un texto."""
    ids = set()
    for grupo in re.findall(r"\[(C\d+(?:[,–\- ]+C\d+)*)\]", texto):
        for a, b in re.findall(r"C(\d+)(?:[–-]C(\d+))?", grupo):
            ids.update(f"C{n:02d}" for n in range(int(a), int(b or a) + 1))
    return ids


class Laminas(HTMLParser):
    """Recoge, por lámina, los elementos con data-cifra (con su texto), el texto visible fuera de
    código y las notas del orador."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pila = []          # (tag, abre_cifra, es_sig, es_oculto)
        self.lamina = "—"
        self.cifras = []        # (lámina, [ids], texto)
        self.abiertas = []      # [ids, partes]
        self.visible = {}       # lámina -> texto visible fuera de .sig
        self.notas = {}         # lámina -> data-note

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        clases = (a.get("class") or "").split()
        if tag == "section" and "slide" in clases:
            self.lamina = a.get("id", "—")
            self.notas[self.lamina] = a.get("data-note", "")
        if tag in VACIOS:
            return
        abre = "data-cifra" in a
        if abre:
            self.abiertas.append([a["data-cifra"].split(), []])
        self.pila.append((tag, abre, "sig" in clases, tag in ("style", "script", "title", "head")))

    def handle_endtag(self, tag):
        while self.pila:
            t, abre, _, _ = self.pila.pop()
            if abre:
                ids, partes = self.abiertas.pop()
                self.cifras.append((self.lamina, ids, re.sub(r"\s+", " ", "".join(partes)).strip()))
            if t == tag:
                break

    def handle_data(self, data):
        if any(oc for _, _, _, oc in self.pila):
            return
        for _, partes in self.abiertas:
            partes.append(data)
        if not any(sig for _, _, sig, _ in self.pila):
            self.visible[self.lamina] = self.visible.get(self.lamina, "") + " " + data


def revisar_separadores(lamina: str, texto: str, origen: str) -> list:
    fallas = []
    texto = re.sub(r"\s+", " ", texto)
    for m in re.finditer(r"(?<![\d.,§])(?<!\bv)\d+\.\d{1,2}(?![\d.])", texto):
        fallas.append(f"FALLA {lamina} ({origen}): punto decimal «{m.group(0)}» (coma decimal en pantalla, D-25)")
    for m in re.finditer(r"(?<![\d.,])\d{5,}(?![\d.,])", texto):
        if m.group(0) not in SIN_MILES:
            fallas.append(f"FALLA {lamina} ({origen}): «{m.group(0)}» sin punto de miles (D-25)")
    for m in re.finditer(r"(?<![\d.,])\d{1,3}\.\d{3}\s?(?:ms|s|MB|m)\b", texto):
        fallas.append(f"FALLA {lamina} ({origen}): «{m.group(0)}» se lee como miles o como decimal (D-25)")
    for m in re.finditer(r"\bMiB\b", texto):
        fallas.append(f"FALLA {lamina} ({origen}): unidad MiB (una sola unidad en pantalla: MB, D-25)")
    return fallas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--laminas", type=Path, default=LAMINAS, help="HTML de la presentación")
    args = ap.parse_args()

    with CSV.open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        if lector.fieldnames != COLUMNAS:
            print(f"FALLA columnas: {lector.fieldnames} (se esperaba {COLUMNAS})")
            return 1
        filas = list(lector)

    fallas = 0
    ids = set()
    pantalla = {}
    for fila in filas:
        cid, valor, origen = fila["id"], fila["valor"], fila["archivo_origen"]
        motivo = None
        if cid in ids:
            motivo = "id repetido"
        ids.add(cid)
        pantalla[cid] = fila["valor_pantalla"]
        ruta = RAIZ / origen
        if motivo is None and not valor:
            motivo = "valor vacío"
        if motivo is None and not ruta.is_file():
            motivo = f"no existe {origen}"
        if motivo is None:
            lineas = ruta.read_text(encoding="utf-8").splitlines()
            if not any(valor in l for l in lineas):
                motivo = "valor ausente del archivo"
            else:
                m = re.fullmatch(r"L(\d+)", fila["linea_o_consulta"].strip())
                if m:
                    n = int(m.group(1))
                    if n < 1 or n > len(lineas) or valor not in lineas[n - 1]:
                        motivo = f"valor ausente de la línea {n}"
        if motivo:
            fallas += 1
            print(f"FALLA {cid}: {motivo} · «{valor}» · {origen}")
        else:
            print(f"ok    {cid}: «{valor}» · {origen}:{fila['linea_o_consulta']}")

    # Documento para TI: cada cita [Cnn] debe existir en el banco.
    if DOC.is_file():
        citas = citas_en(DOC.read_text(encoding="utf-8"))
        for c in sorted(citas - ids):
            fallas += 1
            print(f"FALLA cita {c} en REQUERIMIENTOS_TI.md sin fila en CIFRAS.csv")
        print(f"citas en REQUERIMIENTOS_TI.md: {len(citas)}")
        # Separadores del documento (y del PDF que sale de él), fuera de código y del anexo E.
        cuerpo = re.split(r"\n### E\. Vocabulario", DOC.read_text(encoding="utf-8"))[0]
        cuerpo = re.sub(r"`[^`]*`", " ", re.sub(r"```.*?```", " ", cuerpo, flags=re.S))
        cuerpo = re.sub(r"(?m)^#.*$", " ", cuerpo)          # títulos con número de sección («4.1»)
        for linea in revisar_separadores("documento", cuerpo, "REQUERIMIENTOS_TI.md"):
            fallas += 1
            print(linea)

    # Presentación (fuera del repositorio, D-24).
    if args.laminas.is_file():
        p = Laminas()
        p.feed(args.laminas.read_text(encoding="utf-8"))
        marcadas, usadas = 0, set()
        for lamina, cids, texto in p.cifras:
            marcadas += 1
            for c in cids:
                usadas.add(c)
                if c not in ids:
                    fallas += 1
                    print(f"FALLA {lamina}: data-cifra {c} sin fila en CIFRAS.csv · «{texto}»")
            if len(cids) == 1 and cids[0] in ids and pantalla[cids[0]] and texto != pantalla[cids[0]]:
                fallas += 1
                print(f"FALLA {lamina}: {cids[0]} muestra «{texto}»; valor_pantalla «{pantalla[cids[0]]}»")
        for lamina in p.notas:
            for origen, texto in (("texto", p.visible.get(lamina, "")), ("notas", p.notas[lamina])):
                for c in sorted(citas_en(texto) - ids):
                    fallas += 1
                    print(f"FALLA {lamina} ({origen}): cita [{c}] sin fila en CIFRAS.csv")
                usadas |= citas_en(texto)
                for linea in revisar_separadores(lamina, texto, origen):
                    fallas += 1
                    print(linea)
        print(f"láminas {len(p.notas)} · cifras marcadas {marcadas} · ids distintos {len(usadas)} "
              f"({args.laminas.name})")
    else:
        print(f"presentación no encontrada ({args.laminas}): se omite su revisión (D-24)")

    print(f"\n{len(filas)} cifras · {fallas} fallas")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
