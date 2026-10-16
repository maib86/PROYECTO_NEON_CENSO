#!/usr/bin/env python3
# =====================================================================================
#  Proyecto de campo para la PRUEBA NEGATIVA desde el celular (S07, hallazgo A-09)
# =====================================================================================
#  Copia campo/paquete_movil/NEON_campo_lote_A.qgs y quita SOLO el filtro "lote" = 'A'
#  de la capa finca_visita, para que en QField se vean (y se intenten editar) los puntos
#  del lote de trabajo B con la cuenta del equipo A (servicio neon_lote_a).
#  Resultado esperado: la base de datos rechaza el guardado (control por fila).
#
#  Salida: campo/paquete_movil/NEON_campo_prueba_negativa.qgs  (fuera de git, D-22).
#  Solo para esta prueba; no reemplaza al proyecto de campo. Procedimiento en
#  docs/guia/qfield_campo.md, sección «Prueba negativa».
#  Uso: py campo/construir_prueba_negativa.py
# =====================================================================================
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "campo/paquete_movil/NEON_campo_lote_A.qgs"
SALIDA = RAIZ / "campo/paquete_movil/NEON_campo_prueba_negativa.qgs"


def main() -> int:
    if not ORIGEN.is_file():
        print(f"Falta {ORIGEN.relative_to(RAIZ)}: construir antes el paquete móvil (docs/guia/qfield_campo.md).")
        return 1
    txt = ORIGEN.read_text(encoding="utf-8")
    # Filtro de lote en finca_visita: atributo source (escapado) y <datasource> (sin escapar).
    patrones = [
        (r'(table=&quot;mgn&quot;\.&quot;finca_visita&quot; \(geom\)) sql=&quot;lote&quot; = \'A\'', r"\1 sql="),
        (r'(table="mgn"\."finca_visita" \(geom\)) sql="lote" = \'A\'', r"\1 sql="),
    ]
    cambios = 0
    for pat, rep in patrones:
        txt, n = re.subn(pat, rep, txt)
        cambios += n
    txt = txt.replace("finca_visita (lote A)", "finca_visita (todos los lotes, PRUEBA NEGATIVA)")
    txt = txt.replace("NEON censo — campo lote A", "NEON censo — PRUEBA NEGATIVA (cuenta del equipo A)")
    if cambios != 2:
        print(f"Se esperaban 2 filtros de finca_visita; se quitaron {cambios}. No se escribe nada.")
        return 1
    # Comprobaciones: el filtro de la capa de referencia sigue; sin host ni clave.
    assert "deteccion_cambio&quot; (geom) sql=&quot;lote&quot; = 'A'" in txt
    assert not re.search(r"host=|password=|neon\.tech|npg_", txt)
    assert txt.count("service='neon_lote_a'") >= 2
    SALIDA.write_text(txt, encoding="utf-8")
    print(f"Escrito: {SALIDA.relative_to(RAIZ)} · filtros de finca_visita quitados: {cambios} · servicio neon_lote_a · sin host ni clave")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
