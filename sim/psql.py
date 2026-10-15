# =====================================================================================
#  psql con credenciales tomadas de .env (sin exponerlas)
# =====================================================================================
#  USO
#    py sim/psql.py [--rol owner|tablero|lote_a] [--evidencia ARCHIVO.txt] [--titulo T] -c "SQL"
#    py sim/psql.py [--rol owner|tablero|lote_a] [--evidencia ARCHIVO.txt] -f script.sql
#  Opciones de psql adicionales después de "--" (p. ej. -- -1 para una transacción).
# =====================================================================================

import argparse
import sys

from entorno import psql


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rol", default="owner", choices=["owner", "tablero", "lote_a"])
    ap.add_argument("--evidencia")
    ap.add_argument("--titulo")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-c", dest="sql")
    g.add_argument("-f", dest="archivo")
    a, extra = ap.parse_known_args()
    extra = [e for e in extra if e != "--"]
    rc, _, _ = psql(sql=a.sql, archivo=a.archivo, rol=a.rol,
                    evidencia=a.evidencia, titulo=a.titulo, extra=extra)
    sys.exit(rc)


if __name__ == "__main__":
    main()
