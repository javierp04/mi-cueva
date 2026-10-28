"""
FASE 04 · Backtest · XAUUSD ruptura Donchian(55) con eficiencia (M30, solo compras)
Implementa el pseudocódigo de la fase 03 de fichas/xauusd_ruptura_donchian_eficiencia.md.
No optimiza nada: todos los parámetros vienen de la ficha.

Uso:  python codigo/xauusd_ruptura_donchian_eficiencia.py
Salidas (carpeta resultados/):
  xauusd_ruptura_donchian_eficiencia_operaciones.csv
  xauusd_ruptura_donchian_eficiencia_equity.svg
  xauusd_ruptura_donchian_eficiencia_reporte.md
  xauusd_ruptura_donchian_eficiencia_resultados.json
"""
import json
import math
import os
import sys
import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "datos", "XAUUSD.csv")
OUT = os.path.join(RAIZ, "resultados")
NOM = "xauusd_ruptura_donchian_eficiencia"

# ---- Parámetros de la ficha (no se tocan) ----
CAPITAL = 100_000.0
RIESGO = 0.01 * CAPITAL          # 1 % del capital inicial = 1.000
N_DON, N_SWING, N_ATR, N_EF = 55, 20, 30, 50
K_PER, K_SUAV = 7, 3
MULT_ATR = 3.0
VIDA_MAX = 10
STOPS_LEVEL = 4                  # puntos enteros
APERTURA, CIERRE = 65, 1439      # 01:05 incluido, 23:59 excluido (minutos desde 00:00)
# ---- Supuestos del símbolo (declarados) ----
PUNTO = 0.01                     # 1 punto = 0,01 USD (el CSV tiene 2 decimales)
OZ_LOTE = 100.0                  # 100 oz por lote
PASO, LOTE_MIN, LOTE_MAX = 0.01, 0.01, 100.0
COMISION_LOTE = 0.0              # supuesto: sin comisión (el coste es el spread real del CSV)
FRAC_IS = 0.70


def cargar_csv():
    ts, o, h, l, c, sp = [], [], [], [], [], []
    cols = ["f", "hr", "o", "h", "l", "c", "tv", "v", "sp"]
    for ch in pd.read_csv(CSV, header=None, names=cols, chunksize=1_000_000,
                          usecols=["f", "hr", "o", "h", "l", "c", "sp"],
                          dtype={"f": str, "hr": str}):
        t = pd.to_datetime(ch["f"] + " " + ch["hr"], format="%Y.%m.%d %H:%M")
        ts.append(t.values.astype("datetime64[m]"))
        o.append(ch["o"].values); h.append(ch["h"].values)
        l.append(ch["l"].values); c.append(ch["c"].values)
        sp.append(ch["sp"].values.astype(np.int32))
    return dict(ts=np.concatenate(ts), o=np.concatenate(o), h=np.concatenate(h),
                l=np.concatenate(l), c=np.concatenate(c), sp=np.concatenate(sp))


def velas_m30(m):
    ts = m["ts"].astype("int64")                    # minutos desde 1970
    clave = ts // 30
    cambios = np.flatnonzero(np.diff(clave)) + 1
    cs = np.concatenate(([0], cambios))             # inicio de cada vela (índice M1)
    ce = np.concatenate((cambios, [len(ts)]))       # fin (excluido)
    return dict(
        t=(clave[cs] * 30).astype("datetime64[m]"), cs=cs, ce=ce,
        o=m["o"][cs], h=np.maximum.reduceat(m["h"], cs),
        l=np.minimum.reduceat(m["l"], cs), c=m["c"][ce - 1])


def indicadores(v):
    h, l, c = pd.Series(v["h"]), pd.Series(v["l"]), pd.Series(v["c"])
    cp = c.shift(1)
    tr = pd.concat([h - l, (h - cp).abs(), (l - cp).abs()], axis=1).max(axis=1)
    tr.iloc[0] = np.nan
    atr = tr.rolling(N_ATR, min_periods=N_ATR).mean()
    hh, ll = h.rolling(K_PER, min_periods=K_PER).max(), l.rolling(K_PER, min_periods=K_PER).min()
    rng = hh - ll
    kcrudo = 100 * (c - ll) / rng
    kcrudo = kcrudo.where(rng > 0).ffill()          # rango 0: repito el K crudo anterior
    k = kcrudo.rolling(K_SUAV, min_periods=K_SUAV).mean()
    camino = c.diff().abs().rolling(N_EF, min_periods=N_EF).sum()
    ef = (c - c.shift(N_EF)).abs() / camino
    ef = ef.where(camino > 0, 0.0).where(camino.notna())
    filtro = (k > k.shift(1)).fillna(False)
    disparo = (ef > ef.shift(1)).fillna(False)
    act = filtro & disparo & (~disparo.shift(1, fill_value=False).astype(bool))
    don = h.rolling(N_DON, min_periods=N_DON).max()
    swing = l.shift(1).rolling(N_SWING, min_periods=N_SWING).min()
    return dict(atr=atr.values, act=act.values, don=don.values, swing=swing.values)


def primer(mask):
    """Índice del primer True o -1."""
    i = int(np.argmax(mask)) if mask.size else 0
    return i if mask.size and mask[i] else -1


def simular(m, v, ind, c0, c1, etiqueta):
    """Pseudocódigo de la fase 03 sobre las velas [c0, c1). Devuelve (operaciones, equity por vela)."""
    mo, mh, ml, mc = m["o"], m["h"], m["l"], m["c"]
    sp = m["sp"] * PUNTO
    ao, ah = mo + sp, mh + sp                       # Ask = Bid + spread del minuto
    tmin = (m["ts"].astype("int64") % 1440)
    dow = ((m["ts"].astype("int64") // 1440) + 3) % 7   # 0 = lunes (1970-01-01 fue jueves)
    mk = (dow <= 4) & (tmin >= APERTURA) & (tmin < CIERRE)
    cs, ce, cC = v["cs"], v["ce"], v["c"]
    atr, act, don, swing = ind["atr"], ind["act"], ind["don"], ind["swing"]

    ops = []
    pos = None
    orden = None            # dict(nivel, vida, atr)
    senal = None            # (nivel, atr)
    realizado = 0.0
    eq = np.empty(c1 - c0)

    def comprar(i, j, precio):
        """Paso 4. Devuelve la posición o None si se descarta."""
        sw = swing[i]
        if np.isnan(sw):
            return None
        dist = precio - sw
        if int(round(dist / PUNTO)) < STOPS_LEVEL:
            return None
        lote = math.floor(RIESGO / (dist * OZ_LOTE) / PASO + 1e-9) * PASO
        lote = round(min(max(lote, LOTE_MIN), LOTE_MAX), 2)
        return dict(i=i, j=j, precio=precio, stop=sw, stop0=sw, lote=lote, atr_ent=atr[i])

    def cerrar(p, i, k, px, motivo):
        nonlocal realizado
        pnl = (px - p["precio"]) * OZ_LOTE * p["lote"] - COMISION_LOTE * p["lote"]
        realizado += pnl
        ops.append(dict(
            segmento=etiqueta, entrada=str(m["ts"][p["j"]]).replace("T", " "),
            salida=str(m["ts"][k]).replace("T", " "), precio_entrada_ask=round(p["precio"], 3),
            stop_inicial=round(p["stop0"], 3), precio_salida_bid=round(px, 3),
            lote=p["lote"], pnl_usd=round(pnl, 2), velas_dentro=int(i - p["i"]), motivo=motivo))

    for i in range(c0, c1):
        s, e = cs[i], ce[i]
        # 1. vida de la orden
        if orden is not None:
            orden["vida"] += 1
        j_compra, px_compra = -1, 0.0
        if pos is None:
            # 2a/2b: orden viva
            if orden is not None and orden["vida"] >= VIDA_MAX + 1:
                abiertos = np.flatnonzero(mk[s:e])
                if abiertos.size:
                    j0 = s + int(abiertos[0])
                    if ao[j0] >= orden["nivel"]:        # el fill va primero
                        j_compra, px_compra = j0, ao[j0]
                    else:
                        orden = None                    # vencida: se borra
            elif orden is not None and senal is not None and mk[s] and ao[s] >= orden["nivel"]:
                j_compra, px_compra = s, ao[s]          # 2a: llena antes del reemplazo
            # 2c: señal pendiente
            if j_compra < 0 and senal is not None:
                if mk[s]:
                    nivel_s, atr_s = senal
                    orden = None                        # borrado confirmado (mercado abierto)
                    ask = ao[s]
                    if ask >= nivel_s:
                        j_compra, px_compra = s, ask
                    elif int(round((nivel_s - ask) / PUNTO)) < STOPS_LEVEL:
                        pass                            # rechazada: no queda orden viva
                    else:
                        orden = dict(nivel=nivel_s, vida=1, atr=atr_s)
                senal = None
            # 3. toque durante la vela
            if j_compra < 0 and orden is not None and orden["vida"] <= VIDA_MAX:
                niv = orden["nivel"]
                cond = mk[s:e] & ((ao[s:e] >= niv) | (ah[s:e] >= niv))
                f = primer(cond)
                if f >= 0:
                    j = s + f
                    j_compra = j
                    px_compra = ao[j] if ao[j] >= niv else niv
            # 4. compra
            if j_compra >= 0:
                orden = None
                pos = comprar(i, j_compra, px_compra)
                if pos is not None:
                    # minuto de la compra: gana el stop
                    j = j_compra
                    if ml[j] <= pos["stop"]:
                        px = pos["stop"]
                        if px_compra == ao[j]:
                            px = min(px, mo[j])
                        cerrar(pos, i, j, px, "stop")
                        pos = None
                    else:
                        pass
                if pos is not None:
                    desde = j_compra + 1
                else:
                    desde = None
            else:
                desde = None
        else:
            desde = s
        # 5a. posición abierta: minutos siguientes de la vela
        if pos is not None and desde is not None and desde < e:
            st = pos["stop"]
            cond = mk[desde:e] & (ml[desde:e] <= st)
            f = primer(cond)
            if f >= 0:
                k = desde + f
                px = mo[k] if mo[k] < st else st
                cerrar(pos, i, k, px, "stop" if px == st else "stop_gap")
                pos = None
        # 5b. trailing al cierre
        if pos is not None:
            if not np.isnan(atr[i]):
                tr = cC[i] - MULT_ATR * atr[i]
                if tr > pos["stop"]:
                    pos["stop"] = tr
        # 6. señal al cierre
        if pos is None and act[i] and not np.isnan(don[i]) and not np.isnan(atr[i]):
            senal = (don[i], atr[i])
        # fin de segmento
        if i == c1 - 1 and pos is not None:
            cerrar(pos, i, e - 1, mc[e - 1], "fin_segmento")
            pos = None
        flot = 0.0 if pos is None else (cC[i] - pos["precio"]) * OZ_LOTE * pos["lote"]
        eq[i - c0] = CAPITAL + realizado + flot
    return ops, eq


def metricas(ops, eq):
    pnl = np.array([o["pnl_usd"] for o in ops], dtype=float)
    n = len(pnl)
    gan, per = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    pf = gan / per if per > 0 else (math.inf if gan > 0 else 0.0)
    if n:
        sin = np.delete(pnl, int(np.argmax(pnl)))
        g2, p2 = sin[sin > 0].sum(), -sin[sin < 0].sum()
        pf2 = g2 / p2 if p2 > 0 else (math.inf if g2 > 0 else 0.0)
    else:
        pf2 = 0.0
    eqc = np.concatenate(([CAPITAL], eq))
    pico = np.maximum.accumulate(eqc)
    dd = float(((pico - eqc) / pico).max() * 100)
    # caída solo con operaciones cerradas (referencia)
    cerr = np.concatenate(([CAPITAL], CAPITAL + np.cumsum(pnl))) if n else np.array([CAPITAL])
    pc = np.maximum.accumulate(cerr)
    ddc = float(((pc - cerr) / pc).max() * 100)
    return dict(operaciones=n, pf=pf, pf_sin_mejor=pf2, dd_pct=dd, dd_cerradas_pct=ddc,
                ganadoras=int((pnl > 0).sum()), pct_ganadoras=float((pnl > 0).mean() * 100) if n else 0,
                pnl_total=float(pnl.sum()), mejor=float(pnl.max()) if n else 0,
                peor=float(pnl.min()) if n else 0,
                pnl_medio=float(pnl.mean()) if n else 0)


def svg_equity(path, tis, eis, tos, eos):
    W, H, M = 980, 420, 60
    ts_all = np.concatenate((tis, tos)).astype("datetime64[D]").astype("int64")
    e_all = np.concatenate((eis, eos))
    x0, x1 = ts_all.min(), ts_all.max()
    y0, y1 = e_all.min(), e_all.max()
    X = lambda t: M + (t - x0) / (x1 - x0) * (W - 2 * M)
    Y = lambda y: H - M - (y - y0) / (y1 - y0) * (H - 2 * M)

    def poly(t, e, col):
        t = t.astype("datetime64[D]").astype("int64")
        idx = np.linspace(0, len(t) - 1, min(len(t), 1500)).astype(int)
        pts = " ".join(f"{X(t[k]):.1f},{Y(e[k]):.1f}" for k in idx)
        return f'<polyline fill="none" stroke="{col}" stroke-width="1.4" points="{pts}"/>'
    corte = X(tos.astype("datetime64[D]").astype("int64")[0])
    anio0 = int(str(tis[0])[:4]); anio1 = int(str(tos[-1])[:4])
    marcas = "".join(
        f'<text x="{X(np.datetime64(f"{a}-01-01").astype("int64")):.0f}" y="{H-M+18}" font-size="10" fill="#555">{a}</text>'
        for a in range(anio0 + 1, anio1 + 1, 4))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">
<rect width="100%" height="100%" fill="#fff"/>
<text x="{M}" y="22" font-size="14" fill="#111">XAUUSD ruptura Donchian con eficiencia · equity (cierre de cada vela M30, capital 100.000, con spread)</text>
<line x1="{corte:.1f}" y1="{M-10}" x2="{corte:.1f}" y2="{H-M}" stroke="#999" stroke-dasharray="4"/>
<text x="{corte+4:.1f}" y="{M}" font-size="11" fill="#555">corte 70/30 (fuera de muestra a la derecha)</text>
{poly(tis, eis, "#1f77b4")}{poly(tos, eos, "#d62728")}
<line x1="{M}" y1="{H-M}" x2="{W-M}" y2="{H-M}" stroke="#333"/><line x1="{M}" y1="{M-10}" x2="{M}" y2="{H-M}" stroke="#333"/>
<text x="6" y="{Y(y1)+4:.0f}" font-size="10" fill="#555">{y1:,.0f}</text><text x="6" y="{Y(y0)+4:.0f}" font-size="10" fill="#555">{y0:,.0f}</text>
{marcas}
<text x="{W-300}" y="{M-30}" font-size="11" fill="#1f77b4">azul: dentro de muestra</text>
<text x="{W-170}" y="{M-30}" font-size="11" fill="#d62728">rojo: fuera de muestra</text>
</svg>'''
    open(path, "w", encoding="utf-8").write(svg)


def main():
    print("Leyendo CSV...", flush=True)
    m = cargar_csv()
    ts = m["ts"]
    assert np.all(np.diff(ts.astype("int64")) > 0), "CSV no estrictamente creciente en el tiempo"
    v = velas_m30(m)
    n = len(v["t"])
    print(f"M1: {len(ts):,}  M30: {n:,}  {ts[0]} -> {ts[-1]}", flush=True)
    ind = indicadores(v)
    corte = int(n * FRAC_IS)
    print(f"Corte 70/30 en la vela {corte}: {v['t'][corte]}", flush=True)
    res, todas = {}, []
    eqs = {}
    for etq, a, b in (("IS", 0, corte), ("OOS", corte, n)):
        ops, eq = simular(m, v, ind, a, b, etq)
        r = metricas(ops, eq)
        r["desde"], r["hasta"] = str(v["t"][a]), str(v["t"][b - 1])
        res[etq] = r
        todas += ops
        eqs[etq] = (v["t"][a:b], eq)
        print(etq, json.dumps(r, indent=1, default=str), flush=True)
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(todas).to_csv(os.path.join(OUT, NOM + "_operaciones.csv"), index=False)
    svg_equity(os.path.join(OUT, NOM + "_equity.svg"), *eqs["IS"], *eqs["OOS"])
    res["meta"] = dict(velas_m1=len(ts), velas_m30=n, primera=str(ts[0]), ultima=str(ts[-1]),
                       corte=str(v["t"][corte]))
    json.dump(res, open(os.path.join(OUT, NOM + "_resultados.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
