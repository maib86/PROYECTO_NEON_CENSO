# =====================================================================================
#  PASO 6c — Prueba de concurrencia sobre sim.finca_visita
# =====================================================================================
#  N conexiones simultáneas (hilos, una conexión por hilo), 200 UPDATE cada una, en
#  autocommit (cada UPDATE es su propia transacción, como un guardado de QField).
#  Las filas de cada hilo y de cada corrida son disjuntas. Mide operaciones por
#  segundo, latencia p50/p95/máx y errores. Antes, mide la latencia de `SELECT 1`
#  (ida y vuelta de red sin trabajo de base) como referencia.
#
#  USO
#    py sim/prueba_concurrencia.py medir 1 10 25      corridas con 1, 10 y 25 conexiones
#    py sim/prueba_concurrencia.py revertir           devuelve las filas a 'pendiente'
#
#  Rol: neondb_owner (omite RLS). sim no tiene RLS ni roles de edición (fuera de
#  alcance de S04): el costo de evaluar políticas no queda medido aquí.
#  Evidencia: docs/evidencia/s04/06_concurrencia.txt
# =====================================================================================

import statistics
import sys
import threading
import time

import psycopg2

from entorno import EVIDENCIA, env_pg, redactar, url_de

OPS = 200
ESTADOS = ["visitada", "visitada", "visitada", "no_localizada", "rechazo", "revisita"]
EV = EVIDENCIA / "06_concurrencia.txt"


def salida(texto):
    texto = redactar(texto)
    print(texto)
    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    with open(EV, "a", encoding="utf-8") as f:
        f.write(texto + "\n")


def conectar():
    try:
        con = psycopg2.connect(url_de("owner"), application_name="s04_concurrencia")
    except psycopg2.Error as e:                       # el mensaje puede traer el host
        raise SystemExit("Fallo de conexión: " + redactar(str(e)))
    con.autocommit = True
    return con


def pct(datos, p):
    datos = sorted(datos)
    k = (len(datos) - 1) * p / 100
    i = int(k)
    return datos[i] if i + 1 >= len(datos) else datos[i] + (datos[i + 1] - datos[i]) * (k - i)


def linea_base_red():
    con = conectar()
    cur = con.cursor()
    lat = []
    for _ in range(50):
        t0 = time.perf_counter()
        cur.execute("SELECT 1")
        cur.fetchone()
        lat.append((time.perf_counter() - t0) * 1000)
    con.close()
    salida(f"SELECT 1 x 50 (1 conexión): p50 {pct(lat, 50):.1f} ms · p95 {pct(lat, 95):.1f} ms "
           f"· máx {max(lat):.1f} ms")


def corrida(n, ids):
    """n hilos; ids: lista de n*OPS ids disjuntos."""
    conexiones = [conectar() for _ in range(n)]       # conexiones fuera del cronómetro
    barrera = threading.Barrier(n + 1)
    latencias = [[] for _ in range(n)]
    errores = [[] for _ in range(n)]

    def trabajador(w):
        cur = conexiones[w].cursor()
        mios = ids[w * OPS:(w + 1) * OPS]
        barrera.wait()
        for k, fid in enumerate(mios):
            t0 = time.perf_counter()
            try:
                cur.execute("UPDATE sim.finca_visita SET estado_visita = %s, encuestador = %s "
                            "WHERE id = %s", (ESTADOS[k % len(ESTADOS)], f"sim_c{n}_w{w}", fid))
                if cur.rowcount != 1:
                    errores[w].append(f"rowcount={cur.rowcount} id={fid}")
            except Exception as e:                    # se cuenta y se sigue
                errores[w].append(type(e).__name__ + ": " + str(e).strip()[:120])
            latencias[w].append((time.perf_counter() - t0) * 1000)

    hilos = [threading.Thread(target=trabajador, args=(w,)) for w in range(n)]
    for h in hilos:
        h.start()
    barrera.wait()
    t0 = time.perf_counter()
    for h in hilos:
        h.join()
    pared = time.perf_counter() - t0
    for c in conexiones:
        c.close()

    lat = [x for l in latencias for x in l]
    err = [x for l in errores for x in l]
    salida(f"{n:>2} conexiones · {len(lat)} UPDATE · pared {pared:.2f} s · "
           f"{len(lat) / pared:.1f} op/s · latencia p50 {pct(lat, 50):.1f} ms · "
           f"p95 {pct(lat, 95):.1f} ms · máx {max(lat):.1f} ms · media {statistics.mean(lat):.1f} ms · "
           f"errores {len(err)}" + (f" · ej.: {err[:3]}" if err else ""))


def medir(niveles):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM sim.finca_visita WHERE estado_visita <> 'pendiente'")
    previos = cur.fetchone()[0]
    if previos:
        sys.exit(f"Hay {previos} filas no pendientes en sim.finca_visita: revertir antes de medir.")
    cur.execute("SELECT id FROM sim.finca_visita ORDER BY id")
    todos = [r[0] for r in cur.fetchall()]
    cur.execute("SHOW max_connections")
    maxc = cur.fetchone()[0]
    con.close()

    salida(f"=== Prueba de concurrencia · {time.strftime('%Y-%m-%d %H:%M:%S')} (hora local) ===")
    salida(f"$ py sim/prueba_concurrencia.py medir {' '.join(map(str, niveles))}")
    salida(f"Filas disponibles: {len(todos)} · max_connections del servidor: {maxc} · "
           f"{OPS} UPDATE por conexión, autocommit, filas disjuntas")
    linea_base_red()
    desde = 0
    for n in niveles:
        ids = todos[desde:desde + n * OPS]
        desde += n * OPS
        corrida(n, ids)
    salida(f"Filas tocadas en total: {desde}\n")


def revertir():
    con = conectar()
    cur = con.cursor()
    salida("$ py sim/prueba_concurrencia.py revertir")
    cur.execute("UPDATE sim.finca_visita SET estado_visita = 'pendiente', encuestador = NULL, "
                r"fecha_visita = NULL WHERE encuestador LIKE 'sim\_c%'")
    salida(f"UPDATE {cur.rowcount}")
    cur.execute("SELECT count(*) FILTER (WHERE estado_visita <> 'pendiente'), "
                "count(*) FILTER (WHERE encuestador IS NOT NULL), "
                "count(*) FILTER (WHERE fecha_visita IS NOT NULL), count(*) FROM sim.finca_visita")
    np, enc, fv, tot = cur.fetchone()
    salida(f"Después: no pendientes {np} · con encuestador {enc} · con fecha_visita {fv} · total {tot}\n")
    con.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    env_pg("owner")                                   # registra host y clave para redactar
    if len(sys.argv) > 1 and sys.argv[1] == "medir":
        medir([int(x) for x in sys.argv[2:]] or [1, 10, 25])
    elif len(sys.argv) > 1 and sys.argv[1] == "revertir":
        revertir()
    else:
        sys.exit("Uso: py sim/prueba_concurrencia.py medir 1 10 25 | revertir")
