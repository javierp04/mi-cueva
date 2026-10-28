"""
FASE 05 · Optimización · US100 ADX(75) subiendo + extensión 1,382 del día (M15, solo compras)
Mide la meseta de parámetros SOLO dentro de muestra (el 70 % más antiguo) con el mismo motor y los
mismos costes de la fase 04 (codigo/us100_adx_fib_dia_m15.py). No añade parámetros ni elige un óptimo:
mira si los vecinos del valor de la ficha también funcionan.

Ejes (4, todos ya existentes en la regla; 5 valores centrados en el actual -> 625 combinaciones):
  N_ADX      periodo del ADX            (75)
  K_RISING   ventana de rising          (5)
  FIB        nivel = máx. ayer + FIB x rango (0,382 = fib_day 1,382)
  MULT_SL    stop inicial en ATR        (2,5)

Uso:
  python codigo/us100_adx_fib_dia_optimizar.py          (rejilla completa)
  python codigo/us100_adx_fib_dia_optimizar.py prueba   (dos combinaciones, para medir el tiempo)
Salida (resultados/): us100_adx_fib_dia_meseta.csv
"""
import importlib.util
import itertools
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "resultados")
NOM = "us100_adx_fib_dia"

EJES = {
    "N_ADX": [60, 68, 75, 82, 90],
    "K_RISING": [3, 4, 5, 6, 7],
    "FIB": [0.282, 0.332, 0.382, 0.432, 0.482],
    "MULT_SL": [2.0, 2.25, 2.5, 2.75, 3.0],
}
ACTUAL = {"N_ADX": 75, "K_RISING": 5, "FIB": 0.382, "MULT_SL": 2.5}
WORKERS = 6

_bt = None
_datos = None


def _cargar():
    global _bt, _datos
    if _bt is None:
        spec = importlib.util.spec_from_file_location("bt", os.path.join(RAIZ, "codigo", NOM + "_m15.py"))
        _bt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_bt)
        m = _bt.cargar_csv()
        v = _bt.velas_m15(m)
        corte = int(len(v["t"]) * _bt.FRAC_IS)
        _datos = (m, v, corte)
    return _bt, _datos


def correr(comb):
    bt, (m, v, corte) = _cargar()
    for k, val in comb.items():
        setattr(bt, k, val)
    ind = bt.indicadores(v)
    ops, eq = bt.simular(m, v, ind, 0, corte, "IS")      # SOLO dentro de muestra
    r = bt.metricas(ops, eq)
    return {**comb, "operaciones": r["operaciones"], "pf": r["pf"], "pf_sin_mejor": r["pf_sin_mejor"],
            "dd_pct": r["dd_pct"], "pnl_total": r["pnl_total"]}


def main():
    nombres = list(EJES)
    combs = [dict(zip(nombres, vals)) for vals in itertools.product(*EJES.values())]
    if len(sys.argv) > 1 and sys.argv[1] == "prueba":
        t = time.time()
        print(correr(ACTUAL), f"{time.time() - t:.1f} s (incluye carga del CSV)")
        t = time.time()
        correr({**ACTUAL, "N_ADX": 82})
        print(f"una combinación más: {time.time() - t:.1f} s")
        return
    print(f"{len(combs)} combinaciones, {WORKERS} procesos", flush=True)
    t0 = time.time()
    filas = []
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        for n, r in enumerate(ex.map(correr, combs, chunksize=4), 1):
            filas.append(r)
            if n % 25 == 0:
                print(f"  {n}/{len(combs)}  ({time.time() - t0:.0f} s)", flush=True)
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(filas).to_csv(os.path.join(OUT, NOM + "_meseta.csv"), index=False)
    print("listo:", f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
