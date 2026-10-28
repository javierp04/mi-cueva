"""Gráficos PNG de las fases 04 y 05 (los pide el método: resultados/<idea>_equity.png y _meseta.png).
No cambia ningún cálculo: reutiliza el motor de la fase 04 y la tabla de la fase 05.
Uso: python codigo/xauusd_ruptura_donchian_eficiencia_graficos.py"""
import importlib.util, itertools, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "resultados")
NOM = "xauusd_ruptura_donchian_eficiencia"

# ---- Fase 04: curva de equity (dentro y fuera de muestra, con la pérdida flotante) ----
spec = importlib.util.spec_from_file_location("bt", os.path.join(RAIZ, "codigo", NOM + ".py"))
bt = importlib.util.module_from_spec(spec); spec.loader.exec_module(bt)
m = bt.cargar_csv(); v = bt.velas_m30(m); ind = bt.indicadores(v)
n = len(v["t"]); corte = int(n * bt.FRAC_IS)
ops1, eq1 = bt.simular(m, v, ind, 0, corte, "IS")
ops2, eq2 = bt.simular(m, v, ind, corte, n, "OOS")
r1, r2 = bt.metricas(ops1, eq1), bt.metricas(ops2, eq2)
t = v["t"].astype("datetime64[s]").astype("datetime64[ms]").astype(object)
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(t[:corte], eq1, color="#7a7a7a", lw=1, label=f"Dentro de muestra · PF {r1['pf']:.2f} · caída {r1['dd_pct']:.1f} %")
ax.plot(t[corte:], eq2 + (0), color="#1a9850", lw=1.2, label=f"Fuera de muestra · PF {r2['pf']:.2f} · {r2['operaciones']} ops · caída {r2['dd_pct']:.2f} %")
ax.axvline(t[corte], color="k", ls="--", lw=0.8)
ax.set_title("XAUUSD ruptura Donchian con eficiencia (M30) · equity con costes · cada tramo parte de 100.000")
ax.set_ylabel("USD"); ax.grid(alpha=.3); ax.legend(loc="upper left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, NOM + "_equity.png"), dpi=130); plt.close(fig)

# ---- Fase 05: mapa de calor de la meseta (pares de ejes; los otros dos en su valor actual) ----
df = pd.read_csv(os.path.join(OUT, NOM + "_meseta.csv"))
EJES = ["N_DON", "MULT_ATR", "N_SWING", "VIDA_MAX"]
ACT = dict(N_DON=55, MULT_ATR=3.0, N_SWING=20, VIDA_MAX=10)
val = {e: sorted(df[e].unique()) for e in EJES}
cmap = ListedColormap(["#b2182b", "#f4a582", "#a6d96a", "#1a9850"]); norm = BoundaryNorm([0, 1.0, 1.3, 1.6, 9], cmap.N)
fig, axs = plt.subplots(2, 3, figsize=(14, 8.5))
for ax, (a, b) in zip(axs.flat, itertools.combinations(range(4), 2)):
    M = np.zeros((5, 5))
    for i, va in enumerate(val[EJES[a]]):
        for j, vb in enumerate(val[EJES[b]]):
            q = df
            for k, e in enumerate(EJES):
                x = va if k == a else vb if k == b else ACT[e]
                q = q[np.isclose(q[e], x)]
            M[j, i] = q.pf.iloc[0]
    ax.imshow(M, cmap=cmap, norm=norm, origin="upper")
    for j in range(5):
        for i in range(5): ax.text(i, j, f"{M[j,i]:.2f}", ha="center", va="center", fontsize=9)
    ia, ib = val[EJES[a]].index(ACT[EJES[a]]), val[EJES[b]].index(ACT[EJES[b]])
    ax.add_patch(plt.Rectangle((ia-.5, ib-.5), 1, 1, fill=False, ec="k", lw=3))
    ax.set_xticks(range(5), [f"{x:g}" for x in val[EJES[a]]]); ax.set_yticks(range(5), [f"{x:g}" for x in val[EJES[b]]])
    ax.set_xlabel(EJES[a]); ax.set_ylabel(EJES[b])
fig.suptitle("Fase 05 · meseta (dentro de muestra) · factor de beneficio · borde negro = combinación actual\n"
             "rojo < 1 · naranja < 1,3 · verde claro < 1,6 · verde ≥ 1,6")
fig.tight_layout(); fig.savefig(os.path.join(OUT, NOM + "_meseta.png"), dpi=130); plt.close(fig)
print("OOS", {k: round(r2[k], 2) for k in ("pf", "pf_sin_mejor", "dd_pct")}, r2["operaciones"], "| IS", round(r1["pf"], 2), r1["operaciones"])
