"""
FASE 06 · Robustez · US100 ADX(75) subiendo + extensión 1,382 del día (M15, solo compras)
Regla y parámetros de la fase 04/05, sin cambios. Semilla fija 42.
  a. Costes x2: fuera de muestra con el spread del CSV multiplicado por 2 (la prueba oficial). Aparte, informativa:
     spread x2 y swap x2 a la vez (costes de la fase 04: spread y swap; sin comisión ni deslizamiento).
  b. Monte Carlo del orden: 1.000 barajas de las operaciones fuera de muestra; caída máxima de cada una.
  c. Remuestreo: 1.000 muestras con reemplazo; factor de beneficio de cada una.
  d. Años malos: resultado por año en todo el periodo.
Umbrales provisionales del Reto: a) PF >= 1,1 · b) caída p95 < 30 % · c) PF p5 > 1 · d) >= mitad de años ganadores y PF sin el mejor año > 1.
Uso: python codigo/us100_adx_fib_dia_robustez.py
"""
import importlib.util, json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "resultados")
NOM = "us100_adx_fib_dia"
spec = importlib.util.spec_from_file_location("bt", os.path.join(RAIZ, "codigo", NOM + "_m15.py"))
bt = importlib.util.module_from_spec(spec); spec.loader.exec_module(bt)
CAP = bt.CAPITAL
rng = np.random.default_rng(42)

m = bt.cargar_csv(); v = bt.velas_m15(m); ind = bt.indicadores(v)
n = len(v["t"]); corte = int(n * bt.FRAC_IS)

def pf(p):
    g, l = p[p > 0].sum(), -p[p < 0].sum()
    return g / l if l > 0 else np.inf
def dd_cerradas(p):
    e = np.concatenate(([CAP], CAP + np.cumsum(p))); pico = np.maximum.accumulate(e)
    return ((pico - e) / pico).max() * 100

res = {}
# --- base: fuera de muestra con costes de la fase 04 (reproduce la fase 04) ---
ops, eq = bt.simular(m, v, ind, corte, n, "OOS")
base = bt.metricas(ops, eq)
pnl = np.array([o["pnl_usd"] for o in ops])
res["base_oos"] = dict(pf=base["pf"], ops=base["operaciones"], dd=base["dd_pct"])
print(f"Base fuera de muestra: PF {base['pf']:.2f} · {base['operaciones']} ops · caída {base['dd_pct']:.2f} %")

# --- a. costes x2 ---
m2 = dict(m); m2["sp"] = m["sp"] * 2
ops2, eq2 = bt.simular(m2, v, ind, corte, n, "OOS")
r2 = bt.metricas(ops2, eq2)
a_ok = r2["pf"] >= 1.1
res["a_costes_x2"] = dict(pf=r2["pf"], ops=r2["operaciones"], dd=r2["dd_pct"], ok=bool(a_ok), spread_medio_puntos=float(m["sp"].mean()))
print(f"a. Costes x2: PF {r2['pf']:.2f} · {r2['operaciones']} ops · caída {r2['dd_pct']:.2f} %  (spread medio {m['sp'].mean():.1f} puntos) → {'✓' if a_ok else '✕'}")

# a2. informativa (no cuenta para el veredicto): spread x2 y swap x2
swap0 = bt.SWAP_LARGO_ANUAL; bt.SWAP_LARGO_ANUAL = swap0 * 2
ops3, eq3 = bt.simular(m2, v, ind, corte, n, "OOS"); r3 = bt.metricas(ops3, eq3); bt.SWAP_LARGO_ANUAL = swap0
res["a2_spread_y_swap_x2_informativa"] = dict(pf=r3["pf"], ops=r3["operaciones"], dd=r3["dd_pct"])
print(f"a2. (informativa) spread x2 y swap x2: PF {r3['pf']:.2f} · {r3['operaciones']} ops · caída {r3['dd_pct']:.2f} %")

# --- b. Monte Carlo del orden ---
K = 1000
dds, curvas = np.empty(K), []
for k in range(K):
    p = rng.permutation(pnl); dds[k] = dd_cerradas(p)
    if k < 200: curvas.append(CAP + np.concatenate(([0], np.cumsum(p))))
p95 = np.percentile(dds, 95); b_ok = p95 < 30
res["b_montecarlo_orden"] = dict(dd_p50=float(np.percentile(dds, 50)), dd_p95=float(p95), dd_max=float(dds.max()),
                                 dd_real_cerradas=float(dd_cerradas(pnl)), ok=bool(b_ok))
print(f"b. Monte Carlo del orden: caída mediana {np.percentile(dds,50):.1f} % · p95 {p95:.1f} % · peor {dds.max():.1f} % "
      f"(real, solo cerradas: {dd_cerradas(pnl):.1f} %) → {'✓' if b_ok else '✕'}")

# --- c. remuestreo con reemplazo ---
pfs = np.array([pf(rng.choice(pnl, size=len(pnl), replace=True)) for _ in range(K)])
p5 = np.percentile(pfs, 5); c_ok = p5 > 1
res["c_remuestreo"] = dict(pf_p5=float(p5), pf_p50=float(np.percentile(pfs, 50)), pf_p95=float(np.percentile(pfs, 95)), ok=bool(c_ok))
print(f"c. Remuestreo: PF p5 {p5:.2f} · mediana {np.percentile(pfs,50):.2f} · p95 {np.percentile(pfs,95):.2f} → {'✓' if c_ok else '✕'}")

# --- d. años malos (todo el periodo; cada tramo con la regla tal cual) ---
opsA, _ = bt.simular(m, v, ind, 0, corte, "IS")
todo = pd.DataFrame(opsA + ops)
todo["anio"] = pd.to_datetime(todo["entrada"]).dt.year
por = todo.groupby("anio")["pnl_usd"].agg(["sum", "count"])
pfa = todo.groupby("anio")["pnl_usd"].apply(lambda s: pf(s.values))
gan = int((por["sum"] > 0).sum()); tot = len(por)
mejor = por["sum"].idxmax()
sin = todo[todo["anio"] != mejor]["pnl_usd"].values
pf_sin = pf(sin)
d_ok = gan >= tot / 2 and pf_sin > 1
res["d_anios"] = dict(anios=tot, ganadores=gan, mejor_anio=int(mejor), pf_sin_mejor_anio=float(pf_sin),
                      perdedores={int(a): float(x) for a, x in por["sum"][por["sum"] <= 0].items()}, ok=bool(d_ok))
print(f"d. Años: {gan}/{tot} ganan · mejor año {mejor} · PF sin el mejor año {pf_sin:.2f} → {'✓' if d_ok else '✕'}")
print("   años perdedores:", {int(a): round(float(x)) for a, x in por['sum'][por['sum'] <= 0].items()} or "ninguno")
print(por.assign(pf=pfa).round(2).to_string())

X = sum([a_ok, b_ok, c_ok, d_ok]); res["veredicto"] = f"{X}/4"; print("Veredicto robustez:", res["veredicto"])
json.dump(res, open(os.path.join(OUT, NOM + "_robustez.json"), "w"), indent=1, default=float)

# --- gráficas ---
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for c in curvas: ax[0].plot(c, color="#999", lw=.4, alpha=.5)
ax[0].plot(CAP + np.concatenate(([0], np.cumsum(pnl))), color="#1a9850", lw=1.8, label="orden real")
ax[0].set_title(f"Monte Carlo del orden · 200 de 1.000 barajas · caída p95 {p95:.1f} %"); ax[0].set_xlabel("operación"); ax[0].set_ylabel("USD"); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].bar(por.index.astype(str), por["sum"], color=["#1a9850" if x > 0 else "#b2182b" for x in por["sum"]])
ax[1].set_title("Resultado por año (USD, 1 % de riesgo sobre 100.000)"); ax[1].tick_params(axis="x", rotation=60); ax[1].grid(alpha=.3, axis="y")
fig.tight_layout(); fig.savefig(os.path.join(OUT, NOM + "_robustez.png"), dpi=130)
