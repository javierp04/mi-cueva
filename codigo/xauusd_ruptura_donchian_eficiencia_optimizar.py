"""
FASE 05 · Optimización · XAUUSD ruptura Donchian con eficiencia (M30, solo compras)
Mide la meseta de parámetros SOLO dentro de muestra (el 70 % más antiguo) con el mismo motor y los
mismos costes de la fase 04 (codigo/xauusd_ruptura_donchian_eficiencia.py). No añade parámetros.

Ejes (4, todos ya existentes en la regla):
  N_DON     canal Donchian        (55)
  MULT_ATR  multiplicador trailing (3.0)
  N_SWING   swing del stop inicial (20)
  VIDA_MAX  vigencia de la orden   (10)
Cada eje: 5 valores centrados en el actual -> 625 combinaciones.

Uso:
  python codigo/xauusd_ruptura_donchian_eficiencia_optimizar.py          (rejilla completa)
  python codigo/xauusd_ruptura_donchian_eficiencia_optimizar.py prueba   (una combinación, para medir el tiempo)
Salidas (resultados/): xauusd_ruptura_donchian_eficiencia_meseta.csv y _meseta.svg
"""
import importlib.util
import itertools
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "resultados")
NOM = "xauusd_ruptura_donchian_eficiencia"

EJES = {
    "N_DON": [41, 48, 55, 62, 69],
    "MULT_ATR": [2.4, 2.7, 3.0, 3.3, 3.6],
    "N_SWING": [14, 17, 20, 23, 26],
    "VIDA_MAX": [6, 8, 10, 12, 14],
}
ACTUAL = {"N_DON": 55, "MULT_ATR": 3.0, "N_SWING": 20, "VIDA_MAX": 10}
WORKERS = 6

_bt = None
_datos = None


def _cargar():
    """Carga el motor de la fase 04 y los datos una sola vez por proceso."""
    global _bt, _datos
    if _bt is None:
        spec = importlib.util.spec_from_file_location("bt", os.path.join(RAIZ, "codigo", NOM + ".py"))
        _bt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_bt)
        m = _bt.cargar_csv()
        v = _bt.velas_m30(m)
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
        r = correr(ACTUAL)
        print(r, f"{time.time() - t:.1f} s (incluye carga del CSV)")
        t = time.time()
        correr({**ACTUAL, "N_DON": 62})
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
    df = pd.DataFrame(filas)
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(os.path.join(OUT, NOM + "_meseta.csv"), index=False)
    print("listo:", f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
