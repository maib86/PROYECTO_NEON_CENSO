# =====================================================================================
#  Escribe el servicio libpq de un lote en %APPDATA%\postgresql\.pg_service.conf
# =====================================================================================
#  USO
#    py campo/escribir_pg_service.py            (servicio neon_lote_a, DATABASE_URL_LOTE_A)
#    py campo/escribir_pg_service.py b          (servicio neon_lote_b, DATABASE_URL_LOTE_B)
#
#  Nombre con punto inicial: es el archivo por usuario que libpq (psql, QGIS) lee en
#  Windows sin variables de entorno. Sin el punto haría falta PGSERVICEFILE.
#  Lee la URL del rol de edición desde .env y escribe el bloque [neon_lote_x] con
#  host, port, dbname, user, password y sslmode=require. El archivo queda FUERA del
#  repositorio (perfil de Windows del usuario). Si ya existe, se reemplaza solo el
#  bloque de ese servicio; los demás servicios se conservan.
#  No imprime ningún valor: solo la ruta, el nombre del servicio y las claves escritas.
# =====================================================================================

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "sim"))
from entorno import leer_env  # noqa: E402


def main():
    lote = (sys.argv[1] if len(sys.argv) > 1 else "a").lower()
    if lote not in ("a", "b"):
        sys.exit("Lote inválido: use a o b.")
    servicio = f"neon_lote_{lote}"
    u = urlparse(leer_env()[f"DATABASE_URL_LOTE_{lote.upper()}"])
    if u.hostname.split(".")[0].endswith("-pooler"):
        sys.exit("La URL usa el host -pooler: corregir .env (D-02).")
    valores = {
        "host": u.hostname,
        "port": str(u.port or 5432),
        "dbname": u.path.lstrip("/"),
        "user": unquote(u.username),
        "password": unquote(u.password),
        "sslmode": "require",
    }
    bloque = f"[{servicio}]\n" + "".join(f"{k}={v}\n" for k, v in valores.items())

    destino = Path(os.environ["APPDATA"]) / "postgresql" / ".pg_service.conf"
    destino.parent.mkdir(parents=True, exist_ok=True)
    previo = destino.read_text(encoding="utf-8") if destino.exists() else ""
    # Quita el bloque anterior del mismo servicio (hasta el siguiente [encabezado]).
    patron = re.compile(rf"^\[{servicio}\]\n(?:(?!\[).*\n?)*", re.MULTILINE)
    resto = patron.sub("", previo).rstrip("\n")
    nuevo = (resto + "\n\n" if resto else "") + bloque
    destino.write_text(nuevo, encoding="utf-8", newline="\n")

    otros = re.findall(r"^\[([^\]]+)\]", resto, re.MULTILINE)
    print(r"Archivo: %APPDATA%\postgresql\.pg_service.conf")  # sin la cuenta de Windows
    print(f"Servicio escrito: {servicio} · claves: {', '.join(valores)}")
    print(f"Otros servicios conservados: {', '.join(otros) if otros else 'ninguno'}")


if __name__ == "__main__":
    main()
