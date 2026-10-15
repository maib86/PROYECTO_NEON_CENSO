# =====================================================================================
#  ENTORNO DE LA SIMULACIÓN S04 — credenciales y ejecución de comandos
# =====================================================================================
#  Lee .env desde Python (nunca lo imprime) y traduce la URL elegida a variables
#  libpq (PGHOST, PGUSER, PGPASSWORD, PGDATABASE, PGSSLMODE...). Los subprocesos
#  (psql, ogr2ogr, pg_dump) las heredan: ninguna credencial va en la línea de
#  comandos ni en la salida. Toda salida pasa por `redactar`, que reemplaza clave,
#  host y endpoint reales por marcadores (el nombre de rol no es secreto y se muestra).
#
#  Las evidencias literales se escriben en docs/evidencia/s04/ (ya redactadas); otra
#  carpeta con la variable EVIDENCIA_SESION (p. ej. s05).
# =====================================================================================

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

RAIZ = Path(__file__).resolve().parent.parent
EVIDENCIA = RAIZ / "docs" / "evidencia" / os.environ.get("EVIDENCIA_SESION", "s04")
SALIDA = RAIZ / "sim" / "salida"
GDAL_BIN = Path(r"C:\Program Files\QGIS 3.34.11\bin")
OGR2OGR = str(GDAL_BIN / "ogr2ogr.exe")
OGRINFO = str(GDAL_BIN / "ogrinfo.exe")

ROLES = {"owner": "DATABASE_URL", "tablero": "DATABASE_URL_TABLERO",
         "lote_a": "DATABASE_URL_LOTE_A"}

_secretos = []

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def leer_env():
    vals = {}
    for linea in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        vals[k.strip()] = v.strip().strip("'").strip('"')
    return vals


def url_de(rol):
    return leer_env()[ROLES[rol]]


def env_pg(rol="owner"):
    """Copia de os.environ con las variables libpq del rol. Registra los secretos."""
    u = urlparse(url_de(rol))
    q = parse_qs(u.query)
    env = dict(os.environ)
    env.update({
        "PGHOST": u.hostname, "PGPORT": str(u.port or 5432),
        "PGUSER": unquote(u.username), "PGPASSWORD": unquote(u.password),
        "PGDATABASE": u.path.lstrip("/"), "PGSSLMODE": q.get("sslmode", ["require"])[0],
        "PGCLIENTENCODING": "UTF8", "PGTZ": "America/Costa_Rica",
        "LC_MESSAGES": "C", "LANG": "C",
    })
    if "channel_binding" in q:
        env["PGCHANNELBINDING"] = q["channel_binding"][0]
    for k in ("PGPASSWORD", "PGHOST"):
        if env[k] not in _secretos:
            _secretos.append(env[k])
    ep = env["PGHOST"].split(".")[0]
    if ep not in _secretos:
        _secretos.append(ep)
    return env


def redactar(texto):
    for s in _secretos:
        if s:
            texto = texto.replace(s, "[REDACTADO]")
    return texto


def ejecutar(cmd, rol="owner", evidencia=None, titulo=None, entrada=None,
             mostrar_entrada=False):
    """Ejecuta cmd con las variables libpq del rol, mide tiempo de pared y deja la
    salida literal (redactada) en pantalla y, si se pide, en docs/evidencia/s04/."""
    env = env_pg(rol) if rol else dict(os.environ)
    env.setdefault("PROJ_DATA", str(GDAL_BIN.parent / "share" / "proj"))
    env.setdefault("GDAL_DATA", str(GDAL_BIN.parent / "apps" / "gdal" / "share" / "gdal"))
    t0 = time.perf_counter()
    p = subprocess.run(cmd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", input=entrada)
    seg = time.perf_counter() - t0
    visible = " ".join(f'"{c}"' if " " in c else c for c in cmd)
    if mostrar_entrada:
        visible += " <<'SQL'\n" + entrada.strip() + "\nSQL"
    texto = (f"$ {visible}\n# rol: {rol or 'sin base'} · rc={p.returncode} · tiempo de pared: {seg:.2f} s\n"
             f"{p.stdout}{p.stderr}")
    texto = redactar(texto)
    print(texto)
    if evidencia:
        EVIDENCIA.mkdir(parents=True, exist_ok=True)
        with open(EVIDENCIA / evidencia, "a", encoding="utf-8") as f:
            if titulo:
                f.write(f"## {titulo}\n")
            f.write(texto.rstrip() + "\n\n")
    return p.returncode, seg, p.stdout


def psql(sql=None, archivo=None, rol="owner", evidencia=None, titulo=None, extra=()):
    """SQL en línea se pasa por stdin en UTF-8 (en Windows, -c convierte los acentos a
    la página de códigos ANSI y el servidor rechaza los bytes). La evidencia muestra
    el SQL completo."""
    cmd = ["psql", "-X", "-w", "-v", "ON_ERROR_STOP=1", *extra]
    if archivo:
        cmd += ["-f", str(archivo)]
        return ejecutar(cmd, rol=rol, evidencia=evidencia, titulo=titulo)
    return ejecutar(cmd + ["-f", "-"], rol=rol, evidencia=evidencia, titulo=titulo,
                    entrada=sql, mostrar_entrada=True)


if __name__ == "__main__":
    sys.exit("Módulo auxiliar: usar sim/psql.py o los scripts de la simulación.")
