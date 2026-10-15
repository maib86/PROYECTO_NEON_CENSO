# =====================================================================================
#  PASO 6d — Tablero de la simulación (no se publica)
# =====================================================================================
#  Genera tablero/salida/sim.html con el rol tablero_lectura (DATABASE_URL_TABLERO de
#  .env, pasada por variable de entorno al subproceso) y lo abre con
#  capturar_tablero.py a 400 px, sin freno y con la CPU frenada 4x.
#  USO: py sim/tablero_sim.py
#  Evidencia: docs/evidencia/s04/07_tablero_sim.txt
# =====================================================================================

import os
import subprocess
import time

from entorno import RAIZ, EVIDENCIA, env_pg, redactar, url_de

EV = EVIDENCIA / "07_tablero_sim.txt"
HTML = "tablero/salida/sim.html"


def correr(cmd, env):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=RAIZ, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    seg = time.perf_counter() - t0
    texto = redactar(f"$ {' '.join(cmd)}\n# rc={p.returncode} · tiempo de pared: {seg:.2f} s\n"
                     f"{p.stdout}{p.stderr}")
    print(texto)
    with open(EV, "a", encoding="utf-8") as f:
        f.write(texto.rstrip() + "\n\n")
    return p.returncode


env = dict(os.environ, PYTHONIOENCODING="utf-8")
env_gen = dict(env, DATABASE_URL_TABLERO=url_de("tablero"))
env_pg("tablero")  # registra host y clave del rol tablero para redactar
EVIDENCIA.mkdir(parents=True, exist_ok=True)
correr(["py", "tablero/generar_tablero.py", "--esquema", "sim", "--salida", HTML], env_gen)
peso = (RAIZ / HTML).stat().st_size
with open(EV, "a", encoding="utf-8") as f:
    f.write(f"Peso de {HTML}: {peso} bytes ({peso / 1048576:.2f} MiB)\n\n")
print(f"Peso de {HTML}: {peso} bytes ({peso / 1048576:.2f} MiB)")
# Dos repeticiones de cada configuración: la primera arranca en frío (Leaflet sin caché).
for _ in range(2):
    correr(["py", "tablero/capturar_tablero.py", HTML, "--dir", "tablero/salida/sim", "--anchos", "400"], env)
for _ in range(2):
    correr(["py", "tablero/capturar_tablero.py", HTML, "--dir", "tablero/salida/sim_cpu4", "--anchos", "400",
            "--cpu-lento", "4"], env)
