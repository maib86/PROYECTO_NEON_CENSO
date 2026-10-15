"""Comprueba que cada cifra de CIFRAS.csv aparece, literal, en su archivo de origen.

Uso (desde la raíz del repositorio):
    py docs/requerimientos_ti/verificar_cifras.py

Para cada fila:
  - el archivo_origen existe;
  - el valor aparece literal en el archivo;
  - si linea_o_consulta es «L<n>», el valor aparece literal en esa línea.
Sale con código 1 si alguna fila falla. No lee la base ni .env.
"""
import csv
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CSV = Path(__file__).resolve().parent / "CIFRAS.csv"
COLUMNAS = ["id", "valor", "unidad", "descripcion", "archivo_origen", "linea_o_consulta", "sesion"]


def main() -> int:
    with CSV.open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        if lector.fieldnames != COLUMNAS:
            print(f"FALLA columnas: {lector.fieldnames} (se esperaba {COLUMNAS})")
            return 1
        filas = list(lector)

    fallas = 0
    ids = set()
    for fila in filas:
        cid, valor, origen = fila["id"], fila["valor"], fila["archivo_origen"]
        motivo = None
        if cid in ids:
            motivo = "id repetido"
        ids.add(cid)
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

    # Cada cita [Cnn] o [Cnn–Cmm] del documento para TI debe existir en el banco.
    doc = Path(__file__).resolve().parent / "REQUERIMIENTOS_TI.md"
    if doc.is_file():
        citas = set()
        for grupo in re.findall(r"\[(C\d+(?:[,–\- ]+C\d+)*)\]", doc.read_text(encoding="utf-8")):
            for a, b in re.findall(r"C(\d+)(?:[–-]C(\d+))?", grupo):
                citas.update(f"C{n:02d}" for n in range(int(a), int(b or a) + 1))
        for c in sorted(citas - ids):
            fallas += 1
            print(f"FALLA cita {c} en REQUERIMIENTOS_TI.md sin fila en CIFRAS.csv")
        print(f"citas en REQUERIMIENTOS_TI.md: {len(citas)}")

    print(f"\n{len(filas)} cifras · {fallas} fallas")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
