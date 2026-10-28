"""FASE 05 · juzga la meseta a partir de resultados/xauusd_ruptura_donchian_eficiencia_meseta.csv y dibuja el mapa (SVG).
Umbral del Reto: MESETA si todos los vecinos inmediatos tienen PF >= 1,3, >= 30 operaciones y >= 70 % del PF actual."""
import itertools, os
import numpy as np, pandas as pd
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOM = "xauusd_ruptura_donchian_eficiencia"
df = pd.read_csv(os.path.join(RAIZ, "resultados", NOM + "_meseta.csv"))
EJES = ["N_DON", "MULT_ATR", "N_SWING", "VIDA_MAX"]
ACT = dict(N_DON=55, MULT_ATR=3.0, N_SWING=20, VIDA_MAX=10)
val = {e: sorted(df[e].unique()) for e in EJES}
idx = {e: val[e].index(ACT[e]) for e in EJES}
tab = {tuple(round(r[e], 6) for e in EJES): r for _, r in df.iterrows()}
def fila(pos): return tab[tuple(round(val[e][p], 6) for e, p in zip(EJES, pos))]
c = fila([idx[e] for e in EJES]); pf0 = c.pf
print(f"{len(df)} combinaciones. Actual: PF {pf0:.2f}, {int(c.operaciones)} ops, DD {c.dd_pct:.1f} %")
print(f"Toda la rejilla: PF min {df.pf.min():.2f} · mediana {df.pf.median():.2f} · max {df.pf.max():.2f} · "
      f"PF>=1,3 en {(df.pf>=1.3).mean()*100:.0f} % · PF>1 en {(df.pf>1).mean()*100:.0f} % · ops min {df.operaciones.min()}")
def vecinos(modo):
    out = []
    for d in itertools.product((-1, 0, 1), repeat=4):
        if not any(d): continue
        if modo == "ejes" and sum(abs(x) for x in d) != 1: continue
        pos = [idx[e] + x for e, x in zip(EJES, d)]
        if all(0 <= p < 5 for p in pos): out.append(fila(pos))
    return out
def juzga(vs):
    ok = [(v.pf >= 1.3) and (v.operaciones >= 30) and (v.pf >= 0.7 * pf0) for v in vs]
    return all(ok), sum(ok), len(vs), min(v.pf for v in vs), min(v.operaciones for v in vs)
for modo, txt in (("ejes", "vecinos inmediatos (1 paso en un eje)"), ("todos", "cubo completo (todos los pasos y diagonales)")):
    ok, n, tot, mn, mo = juzga(vecinos(modo))
    print(f"{txt}: {n}/{tot} cumplen · PF mínimo {mn:.2f} · ops mínimas {mo} → {'MESETA' if ok else 'PICO'}")
print("\nPF por eje (los otros tres en su valor actual):")
for e in EJES:
    print(" ", e, [f"{val[e][p]}: {fila([p if k==e else idx[k] for k in EJES]).pf:.2f}" for p in range(5)])
print("\nTop 5 por PF (solo informativo, NO se elige): ")
print(df.sort_values("pf", ascending=False).head(5).round(2).to_string(index=False))
# ---- mapa SVG: 6 pares de ejes, resto en su valor actual ----
pares = list(itertools.combinations(range(4), 2))
def color(pf):
    if pf < 1.0: return "#b2182b"
    if pf < 1.3: return "#f4a582"
    if pf < 1.6: return "#a6d96a"
    return "#1a9850"
S, P, W = 40, 70, 5
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{3*(W*S+P+20)}" height="{2*(W*S+P+30)+30}" font-family="sans-serif" font-size="11">',
       '<rect width="100%" height="100%" fill="white"/>',
       f'<text x="10" y="18" font-size="13">Fase 05 · meseta (dentro de muestra) · PF · rojo &lt;1 · naranja &lt;1,3 · verde claro &lt;1,6 · verde ≥1,6 · borde negro = combinación actual</text>']
for n, (a, b) in enumerate(pares):
    ox, oy = (n % 3) * (W*S+P+20) + P, (n // 3) * (W*S+P+30) + 50
    svg.append(f'<text x="{ox}" y="{oy-8}">{EJES[a]} (→) × {EJES[b]} (↓)</text>')
    for i in range(5):
        for j in range(5):
            pos = [idx[e] for e in EJES]; pos[a] = i; pos[b] = j
            r = fila(pos); cur = (i == idx[EJES[a]] and j == idx[EJES[b]])
            svg.append(f'<rect x="{ox+i*S}" y="{oy+j*S}" width="{S}" height="{S}" fill="{color(r.pf)}" stroke="{"black" if cur else "white"}" stroke-width="{3 if cur else 1}"/>')
            svg.append(f'<text x="{ox+i*S+S/2}" y="{oy+j*S+S/2+4}" text-anchor="middle">{r.pf:.2f}</text>')
        svg.append(f'<text x="{ox+i*S+S/2}" y="{oy+W*S+14}" text-anchor="middle">{val[EJES[a]][i]:g}</text>')
        svg.append(f'<text x="{ox-6}" y="{oy+i*S+S/2+4}" text-anchor="end">{val[EJES[b]][i]:g}</text>')
svg.append('</svg>')
open(os.path.join(RAIZ, "resultados", NOM + "_meseta.svg"), "w", encoding="utf-8").write("\n".join(svg))
print("\nMapa: resultados/" + NOM + "_meseta.svg")
