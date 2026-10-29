"""
FASE 04 · Backtest · US30 compra LIMIT en HMA(30)+1 ATR(14) tras CRUCE_BAJA del MACD(10,50,9) en sesion asiatica (M30)
Implementa el pseudocodigo de la fase 03 de fichas/us30_macd_hma_asia.md (28 supuestos). No optimiza nada.
Motor derivado de codigo/us100_adx_fib_dia_m15.py (validado contra el motor del trader); cambia solo lo propio
de esta regla: velas M30, MACD/HMA/ATR con las definiciones exactas del trader, filtro de sesion asiatica,
orden LIMIT de compra (casos A/B/C), cancelacion por CRUCE_ALZA, stop 2 x ATR(30), trailing 2,5 x ATR(30)
y cierre forzado a las 48 velas.

Uso:  python codigo/us30_macd_hma_asia.py [--corto]     (--corto = solo 6.000 velas del tramo fuera de muestra)
Salidas (carpeta resultados/):
  us30_macd_hma_asia_operaciones.csv · _equity.png · _reporte.md · _resultados.json
"""
import json
import math
import os
import sys
import time
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "datos", "us30_1m_mt5.csv")       # OHLC M1
CSV_SPREAD = os.path.join(RAIZ, "datos", "US30.csv")       # TSV; ultima columna = spread (puntos de 0,01)
OUT = os.path.join(RAIZ, "resultados")
NOM = "us30_macd_hma_asia"

# ---- Parametros de la ficha (no se tocan) ----
CAPITAL = 100_000.0
RIESGO = 0.01 * CAPITAL          # 1 % del capital inicial = 1.000
MACD_F, MACD_L, MACD_S = 10, 50, 9
HMA_N = 30
N_ATR_NIVEL, N_ATR_SL = 14, 30   # ATR(14) para el nivel; ATR(30) para stop, lote y trailing
OFFSET_ATR = 1.0                 # nivel = HMA(30) + 1 x ATR(14)
MULT_SL = 2.0                    # stop inicial = 2 x ATR_ORDEN
MULT_TRAIL = 2.5                 # trailing = cierre - 2,5 x ATR(30) de la vela recien cerrada
VIDA_MAX = 15                    # la orden vive 15 velas (la de colocacion incluida)
VELAS_FORZADO = 49               # entrada en F; se cierra en la apertura de F+49 (48 velas completas despues de F)
STOPS_LEVEL = 150                # puntos enteros
APERTURA, CIERRE = 60, 1439      # 01:00 incluido, 23:59 excluido (minutos desde 00:00)
ASIA_DESDE, ASIA_HASTA = 9 * 60, 15 * 60   # 09:00-15:00 Asia/Tokyo
# ---- Simbolo US30 (SUPUESTOS de la ficha, los mismos de US100: 24 a 26) ----
PUNTO = 0.01
OZ_LOTE = 1.0
PASO, LOTE_MIN, LOTE_MAX = 0.01, 0.01, 300.0
COMISION_LOTE = 0.0
SWAP_LARGO_ANUAL = 0.069
FRAC_IS = 0.70


# ------------------------------------------------------------------ datos
def cargar_csv():
    ts, o, h, l, c = [], [], [], [], []
    for ch in pd.read_csv(CSV, chunksize=1_000_000, usecols=["fecha", "open", "high", "low", "close"],
                          dtype={"fecha": str}):
        t = pd.to_datetime(ch["fecha"], format="%Y-%m-%dT%H:%M:%SZ")
        ts.append(t.values.astype("datetime64[m]"))
        o.append(ch["open"].values); h.append(ch["high"].values)
        l.append(ch["low"].values); c.append(ch["close"].values)
    ts = np.concatenate(ts)
    tss, sp, cc = [], [], []
    for ch in pd.read_csv(CSV_SPREAD, sep="\t", chunksize=1_000_000,
                          dtype={"<DATE>": str, "<TIME>": str}):
        t = pd.to_datetime(ch["<DATE>"] + " " + ch["<TIME>"], format="%Y.%m.%d %H:%M:%S")
        tss.append(t.values.astype("datetime64[m]"))
        sp.append(ch["<SPREAD>"].values.astype(np.float64))
        cc.append(ch["<CLOSE>"].values.astype(np.float64))
    tss, sp, cc = np.concatenate(tss), np.concatenate(sp), np.concatenate(cc)
    # alineacion POR FECHA: cada minuto del M1 curado debe existir en US30.csv
    pos = np.searchsorted(tss, ts)
    pos = np.clip(pos, 0, len(tss) - 1)
    hay = tss[pos] == ts
    info = dict(filas_spread_archivo=int(len(tss)), filas_m1=int(len(ts)), m1_con_spread=int(hay.sum()),
                m1_sin_spread=int((~hay).sum()), spread_primera=str(tss[0]),
                filas_spread_no_usadas=int(len(tss) - hay.sum()))
    # cierre de ambos archivos en los minutos que coinciden (cordura de la alineacion)
    c_m1 = np.concatenate(c)
    info["m1_cierre_distinto_al_spread_file"] = int((np.abs(c_m1[hay] - cc[pos[hay]]) > 1e-6).sum())
    spm = np.where(hay, sp[pos], np.nan)
    med = float(np.nanmedian(spm))
    info["spread_mediano_pts"] = med
    spm = np.where(np.isnan(spm), med, spm)
    return dict(ts=ts, o=np.concatenate(o), h=np.concatenate(h), l=np.concatenate(l), c=c_m1, sp=spm), info


def velas_m30(m):
    ts = m["ts"].astype("int64")                    # minutos desde 1970
    clave = ts // 30
    cambios = np.flatnonzero(np.diff(clave)) + 1
    cs = np.concatenate(([0], cambios))
    ce = np.concatenate((cambios, [len(ts)]))
    return dict(t=(clave[cs] * 30).astype("datetime64[m]"), cs=cs, ce=ce,
                o=m["o"][cs], h=np.maximum.reduceat(m["h"], cs),
                l=np.minimum.reduceat(m["l"], cs), c=m["c"][ce - 1])


# ------------------------------------------------------------------ indicadores (definiciones del trader)
def ema_sma(x, n):
    """EMA con semilla SMA de los n primeros valores validos y alpha 2/(n+1)."""
    out = np.full(len(x), np.nan)
    ok = np.flatnonzero(~np.isnan(x))
    if len(ok) < n:
        return out
    p = ok[0]
    k = p + n - 1
    out[k] = np.mean(x[p:k + 1])
    a = 2.0 / (n + 1)
    for t in range(k + 1, len(x)):
        out[t] = out[t - 1] + (x[t] - out[t - 1]) * a
    return out


def lwma(x, n):
    """Media ponderada, pesos 1..n (n para la vela mas reciente). NaN hasta tener n valores validos."""
    out = np.zeros(len(x))
    for k in range(n):
        sh = np.full(len(x), np.nan)
        sh[k:] = x[:len(x) - k] if k else x
        out += (n - k) * sh
    return out / (n * (n + 1) / 2.0)


def atr_sma(h, l, c, n):
    cp = np.concatenate(([np.nan], c[:-1]))
    tr = np.maximum.reduce([h - l, np.abs(h - cp), np.abs(l - cp)])
    tr[0] = h[0] - l[0]                              # primera barra: H - L
    return pd.Series(tr).rolling(n, min_periods=n).mean().values


def hma(c, n):
    n2, nr = n // 2, int(math.sqrt(n))
    return lwma(2 * lwma(c, n2) - lwma(c, n), nr)


def hora_asia(t):
    """True si la hora de apertura de la vela (hora del servidor = Nueva York + 7 h) cae en [09:00, 15:00) de Tokio."""
    idx = pd.DatetimeIndex(t.astype("datetime64[ns]")) - pd.Timedelta(hours=7)
    ny = idx.tz_localize("America/New_York", ambiguous=np.ones(len(idx), dtype=bool), nonexistent="shift_forward")
    tk = ny.tz_convert("Asia/Tokyo")
    mins = tk.hour * 60 + tk.minute
    return np.asarray((mins >= ASIA_DESDE) & (mins < ASIA_HASTA))


def indicadores(v):
    h, l, c = v["h"], v["l"], v["c"]
    main = ema_sma(c, MACD_F) - ema_sma(c, MACD_L)
    sig = ema_sma(main, MACD_S)
    val = ~np.isnan(sig)
    prev_ok = np.concatenate(([False], val[:-1]))
    pm, ps = np.concatenate(([np.nan], main[:-1])), np.concatenate(([np.nan], sig[:-1]))
    with np.errstate(invalid="ignore"):
        baja = val & prev_ok & (main < sig) & (pm >= ps)
        alza = val & prev_ok & (main > sig) & (pm <= ps)
    asia = hora_asia(v["t"])
    atr14, atr30 = atr_sma(h, l, c, N_ATR_NIVEL), atr_sma(h, l, c, N_ATR_SL)
    hm = hma(c, HMA_N)
    nivel = hm + OFFSET_ATR * atr14
    return dict(main=main, sig=sig, baja=baja, alza=alza, asia=asia, act=baja & asia, atr14=atr14, atr=atr30,
                hma=hm, nivel=nivel)


def primer(mask):
    i = int(np.argmax(mask)) if mask.size else 0
    return i if mask.size and mask[i] else -1


# ------------------------------------------------------------------ motor (pseudocodigo de la fase 03)
def simular(m, v, ind, c0, c1, etiqueta):
    mo, mh, ml, mc = m["o"], m["h"], m["l"], m["c"]
    sp = m["sp"] * PUNTO
    ao, al = mo + sp, ml + sp                        # Ask = Bid + spread del minuto
    tmin = (m["ts"].astype("int64") % 1440)
    dow = ((m["ts"].astype("int64") // 1440) + 3) % 7   # 0 = lunes
    mk = (dow <= 4) & (tmin >= APERTURA) & (tmin < CIERRE)
    cs, ce, cC = v["cs"], v["ce"], v["c"]
    dia_vela = v["t"].astype("int64") // 1440
    n_velas = len(cs)
    atr, act, alza, nivel_v = ind["atr"], ind["act"], ind["alza"], ind["nivel"]
    PT = 1.0 / PUNTO

    cnt = dict(senales=0, caso_B=0, caso_C_rechazo=0, caso_A_colocada=0, senal_perdida_mercado_cerrado=0,
               ordenes_vencidas=0, ordenes_canceladas_alza=0, ordenes_reemplazadas=0, descartes_stops_level=0,
               cancelacion_inversa_sin_mercado=0)
    ops, pos, orden, senal, cancel_pend = [], None, None, None, False
    realizado = 0.0
    eq = np.empty(c1 - c0)

    def comprar(i, j, precio, nivel, atr_o, origen):
        dist = MULT_SL * atr_o
        if int(round(dist * PT)) < STOPS_LEVEL:
            cnt["descartes_stops_level"] += 1
            return None
        sl = precio - dist
        lote = math.floor(RIESGO / (dist * OZ_LOTE) / PASO + 1e-9) * PASO
        lote = round(min(max(lote, LOTE_MIN), LOTE_MAX), 2)
        return dict(i=i, j=j, precio=precio, stop=sl, stop0=sl, lote=lote, atr_ent=atr_o, nivel=nivel,
                    origen=origen, swap=0.0, noches=0)

    def cerrar(p, i, k, px, motivo):
        nonlocal realizado
        bruto = (px - p["precio"]) * OZ_LOTE * p["lote"] - COMISION_LOTE * p["lote"]
        realizado += bruto
        ops.append(dict(
            segmento=etiqueta, entrada=str(m["ts"][p["j"]]).replace("T", " "),
            salida=str(m["ts"][k]).replace("T", " "), origen=p["origen"], nivel=round(p["nivel"], 3),
            precio_entrada_ask=round(p["precio"], 3), atr_orden=round(p["atr_ent"], 3),
            stop_inicial=round(p["stop0"], 3), precio_salida_bid=round(px, 3),
            lote=p["lote"], pnl_bruto_usd=round(bruto, 2), swap_usd=round(p["swap"], 2),
            noches=p["noches"], pnl_usd=round(bruto + p["swap"], 2),
            velas_dentro=int(i - p["i"]), motivo=motivo))

    def motivo_stop(p, gap):
        base = "trailing" if p["stop"] > p["stop0"] + 1e-9 else "stop_inicial"
        return base + ("_gap" if gap else "")

    for i in range(c0, c1):
        s, e = cs[i], ce[i]
        # 1. vida de la orden
        if orden is not None:
            orden["vida"] += 1
        j_compra, px_compra = -1, 0.0
        niv_c, atr_c, origen_c = 0.0, 0.0, ""
        desde = None
        if pos is None:
            # 2b / 2c: orden viva (vencida, cancelacion o reemplazo): el fill va primero
            if orden is not None:
                if orden["vida"] >= VIDA_MAX + 1:                 # vencida: borrado en cada tick con mercado abierto
                    abiertos = np.flatnonzero(mk[s:e])
                    if abiertos.size:
                        j0 = s + int(abiertos[0])
                        if ao[j0] <= orden["nivel"]:
                            j_compra, px_compra = j0, ao[j0]
                            niv_c, atr_c, origen_c = orden["nivel"], orden["atr"], "A_apertura"
                        else:
                            orden = None
                            cnt["ordenes_vencidas"] += 1
                elif (senal is not None or cancel_pend) and mk[s]:
                    if ao[s] <= orden["nivel"]:
                        j_compra, px_compra = s, ao[s]
                        niv_c, atr_c, origen_c = orden["nivel"], orden["atr"], "A_apertura"
                    elif cancel_pend:
                        orden = None
                        cnt["ordenes_canceladas_alza"] += 1
                elif cancel_pend and not mk[s]:
                    cnt["cancelacion_inversa_sin_mercado"] += 1   # la orden queda viva hasta vencer
            cancel_pend = False
            # 2d: senal pendiente
            if j_compra < 0 and senal is not None:
                if mk[s]:
                    nivel_s, atr_s = senal
                    if orden is not None:
                        cnt["ordenes_reemplazadas"] += 1
                    orden = None                                  # borrado confirmado (mercado abierto)
                    ask = ao[s]
                    if ask <= nivel_s:                            # caso B: a mercado
                        j_compra, px_compra = s, ask
                        niv_c, atr_c, origen_c = nivel_s, atr_s, "B"
                        cnt["caso_B"] += 1
                    elif int(round((ask - nivel_s) * PT)) < STOPS_LEVEL:
                        cnt["caso_C_rechazo"] += 1                # rechazada, no queda orden viva
                    else:                                         # caso A: orden en espera
                        orden = dict(nivel=nivel_s, vida=1, atr=atr_s)
                        cnt["caso_A_colocada"] += 1
                else:
                    cnt["senal_perdida_mercado_cerrado"] += 1
                senal = None
            # 3. toque durante la vela (Ask baja hasta el nivel)
            if j_compra < 0 and orden is not None and orden["vida"] <= VIDA_MAX:
                niv = orden["nivel"]
                f = primer(mk[s:e] & (al[s:e] <= niv))
                if f >= 0:
                    j = s + f
                    j_compra = j
                    if ao[j] <= niv:
                        px_compra, origen_c = ao[j], "A_apertura"
                    else:
                        px_compra, origen_c = niv, "A"
                    niv_c, atr_c = niv, orden["atr"]
            # 4. compra
            if j_compra >= 0:
                orden = None
                senal = None
                pos = comprar(i, j_compra, px_compra, niv_c, atr_c, origen_c)
                if pos is not None:
                    j = j_compra
                    if ml[j] <= pos["stop"]:                      # mismo minuto: gana el stop
                        px = pos["stop"]
                        if px_compra == ao[j]:
                            px = min(px, mo[j])
                        cerrar(pos, i, j, px, motivo_stop(pos, False))
                        pos = None
                if pos is not None:
                    desde = j_compra + 1
        else:
            desde = s
            # 2a: cierre forzado a las 48 velas completas despues de la de entrada
            if i - pos["i"] >= VELAS_FORZADO:
                abiertos = np.flatnonzero(mk[s:e])
                if abiertos.size:
                    k = s + int(abiertos[0])
                    cerrar(pos, i, k, mo[k], "48_velas")
                    pos = None
                    desde = None
        # 5a. posicion abierta: minutos de la vela
        if pos is not None and desde is not None and desde < e:
            st = pos["stop"]
            f = primer(mk[desde:e] & (ml[desde:e] <= st))
            if f >= 0:
                k = desde + f
                gap = mo[k] < st
                px = mo[k] if gap else st
                cerrar(pos, i, k, px, motivo_stop(pos, gap))
                pos = None
        # 5b. trailing al cierre
        if pos is not None and not np.isnan(atr[i]):
            tr = cC[i] - MULT_TRAIL * atr[i]
            if tr > pos["stop"]:
                pos["stop"] = tr
        # 6. al cierre de la vela
        if alza[i] and orden is not None:
            cancel_pend = True
        if pos is None and act[i] and not np.isnan(nivel_v[i]) and not np.isnan(atr[i]):
            senal = (nivel_v[i], atr[i])
            cnt["senales"] += 1
        if i == c1 - 1 and pos is not None:
            cerrar(pos, i, e - 1, mc[e - 1], "fin_segmento")
            pos = None
        # swap: posicion abierta al pasar la medianoche del servidor (noches lun-vie)
        if pos is not None and i + 1 < n_velas:
            for d in range(int(dia_vela[i]), int(dia_vela[i + 1])):
                if (d + 3) % 7 <= 4:
                    sw = -SWAP_LARGO_ANUAL / 365.0 * cC[i] * pos["lote"] * OZ_LOTE
                    pos["swap"] += sw
                    pos["noches"] += 1
                    realizado += sw
        flot = 0.0 if pos is None else (cC[i] - pos["precio"]) * OZ_LOTE * pos["lote"]
        eq[i - c0] = CAPITAL + realizado + flot
    return ops, eq, cnt


# ------------------------------------------------------------------ metricas
def pf_de(pnl):
    pnl = np.asarray(pnl, dtype=float)
    g, p = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    return g / p if p > 0 else (math.inf if g > 0 else 0.0)


def pf_sin_mejor(pnl):
    pnl = np.asarray(pnl, dtype=float)
    if len(pnl) == 0:
        return 0.0
    return pf_de(np.delete(pnl, int(np.argmax(pnl))))


def metricas(ops, eq):
    pnl = np.array([o["pnl_usd"] for o in ops], dtype=float)
    bruto = np.array([o["pnl_bruto_usd"] for o in ops], dtype=float)
    swp = np.array([o["swap_usd"] for o in ops], dtype=float)
    n = len(pnl)
    eqc = np.concatenate(([CAPITAL], eq))
    pico = np.maximum.accumulate(eqc)
    dd = float(((pico - eqc) / pico).max() * 100)
    cerr = np.concatenate(([CAPITAL], CAPITAL + np.cumsum(pnl))) if n else np.array([CAPITAL])
    pc = np.maximum.accumulate(cerr)
    ddc = float(((pc - cerr) / pc).max() * 100)
    return dict(operaciones=n, pf=pf_de(pnl), pf_sin_mejor=pf_sin_mejor(pnl), dd_pct=dd, dd_cerradas_pct=ddc,
                pf_sin_swap=pf_de(bruto), pf_sin_swap_sin_mejor=pf_sin_mejor(bruto),
                ganadoras=int((pnl > 0).sum()), pct_ganadoras=float((pnl > 0).mean() * 100) if n else 0,
                pnl_total=float(pnl.sum()), pnl_bruto_total=float(bruto.sum()), swap_total=float(swp.sum()),
                mejor=float(pnl.max()) if n else 0, peor=float(pnl.min()) if n else 0,
                pnl_medio=float(pnl.mean()) if n else 0,
                noches_medias=float(np.mean([o["noches"] for o in ops])) if n else 0)


def por_anio(df):
    filas = []
    for a, g in df.groupby(df["entrada"].str[:4]):
        p = g["pnl_usd"].values
        filas.append(dict(anio=a, operaciones=len(p), pf=pf_de(p), pf_sin_mejor=pf_sin_mejor(p),
                          pf_sin_swap=pf_de(g["pnl_bruto_usd"].values), pnl=float(p.sum()),
                          pct_ganadoras=float((p > 0).mean() * 100)))
    return filas


def grupo(g):
    p = g["pnl_usd"].values
    if len(p) == 0:
        return dict(n=0, pf=0.0, pnl=0.0, gan=0.0, media=0.0, desv=0.0)
    return dict(n=len(p), pf=pf_de(p), pnl=float(p.sum()), gan=float((p > 0).mean() * 100),
                media=float(p.mean()), desv=float((g["precio_entrada_ask"] - g["nivel"]).mean()))


def fmt(x, d=2):
    if isinstance(x, float) and math.isinf(x):
        return "inf"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def grafico_equity(path, tis, eis, tos, eos, corte_txt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5), dpi=130)
    ax.plot(tis.astype("datetime64[s]"), eis, color="#1f77b4", lw=0.9, label="dentro de muestra (70 %)")
    ax.plot(tos.astype("datetime64[s]"), eos, color="#d62728", lw=0.9, label="fuera de muestra (30 %)")
    ax.axvline(tos[0].astype("datetime64[s]"), color="#888", ls="--", lw=0.8)
    ax.axhline(CAPITAL, color="#bbb", lw=0.6)
    ax.set_title("US30 MACD cruza a la baja en Asia + limit HMA(30)+1 ATR · equity por vela M30 (capital 100.000, spread y swap)")
    ax.set_ylabel("USD")
    ax.legend(loc="upper left", frameon=False)
    ax.text(0.99, 0.02, "cada tramo parte de 100.000 · corte " + corte_txt, transform=ax.transAxes,
            ha="right", fontsize=8, color="#555")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ------------------------------------------------------------------ verificacion a mano (otro camino: pandas)
def ema_pd(x, n):
    """EMA con semilla SMA hecha con pandas: la semilla reemplaza al valor n-esimo y ewm(adjust=False) hace la recursion."""
    p = x.first_valid_index()
    p = x.index.get_loc(p)
    k = p + n - 1
    y = x.iloc[k:].copy()
    y.iloc[0] = x.iloc[p:k + 1].mean()
    return y.ewm(alpha=2.0 / (n + 1), adjust=False).mean().reindex(x.index)


def lw_pd(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return x.rolling(n).apply(lambda a: float(np.dot(a, w) / w.sum()), raw=True)


def a_tokio(ts_srv):
    dt = ts_srv.to_pydatetime() - pd.Timedelta(hours=7)
    return dt.replace(tzinfo=ZoneInfo("America/New_York")).astimezone(ZoneInfo("Asia/Tokyo"))


def verificar_a_mano(m, ops_df, indices):
    d = pd.DataFrame({"o": m["o"], "h": m["h"], "l": m["l"], "c": m["c"], "sp": m["sp"] * PUNTO},
                     index=pd.DatetimeIndex(m["ts"].astype("datetime64[ns]")))
    r = d.resample("30min", label="left", closed="left").agg({"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    cp = r["c"].shift(1)
    tr = pd.concat([r.h - r.l, (r.h - cp).abs(), (r.l - cp).abs()], axis=1).max(axis=1)
    tr.iloc[0] = r.h.iloc[0] - r.l.iloc[0]
    r["atr30"] = tr.rolling(30).mean()
    r["atr14"] = tr.rolling(14).mean()
    main = ema_pd(r["c"], 10) - ema_pd(r["c"], 50)
    sig = ema_pd(main, 9)
    r["main"], r["sig"] = main, sig
    r["baja"] = (main < sig) & (main.shift(1) >= sig.shift(1))
    L = []
    for ix in indices:
        op = ops_df.loc[ix]
        te, ts_ = pd.Timestamp(op["entrada"]), pd.Timestamp(op["salida"])
        L.append(f"Operacion #{ix} ({op['segmento']}, origen {op['origen']}): entrada {op['entrada']} · salida {op['salida']} · "
                 f"motivo {op['motivo']} · noches {op['noches']}")
        vela_e = te.floor("30min")
        p = r.index.get_loc(vela_e)
        rango = [p - 1] if op["origen"] == "B" else list(range(p - 1, p - 1 - VIDA_MAX, -1))
        sg = None
        for q in rango:
            tk = a_tokio(r.index[q])
            en_asia = ASIA_DESDE <= tk.hour * 60 + tk.minute < ASIA_HASTA
            if bool(r["baja"].iloc[q]) and en_asia:
                sg = q
                break
        if sg is None:
            L.append("  - Senal: ninguna vela previa con cruce a la baja y sesion asiatica a mano -> DIFERENTE")
            continue
        t_sig = r.index[sg]
        tk = a_tokio(t_sig)
        L.append(f"  - Senal a mano: vela {t_sig} (hora servidor) = {tk:%Y-%m-%d %H:%M} en Tokio (dentro de 09:00-15:00); MACD principal "
                 f"{r['main'].iloc[sg]:.3f} < senal {r['sig'].iloc[sg]:.3f} y en la vela anterior {r['main'].iloc[sg-1]:.3f} >= {r['sig'].iloc[sg-1]:.3f} -> OK")
        sl_ = r["c"].iloc[sg - 100: sg + 1]
        hm_ = lw_pd(2 * lw_pd(sl_, 15) - lw_pd(sl_, 30), 5).iloc[-1]
        niv = hm_ + r["atr14"].iloc[sg]
        atr_s = r["atr30"].iloc[sg]
        L.append(f"  - Nivel a mano: HMA(30) = {hm_:.3f} + ATR(14) {r['atr14'].iloc[sg]:.3f} = {niv:.3f} (motor {op['nivel']}) -> "
                 f"{'OK' if abs(niv - op['nivel']) < 5e-3 else 'DIFERENTE'}; ATR(30) de la vela de senal {atr_s:.3f} (motor {op['atr_orden']}) -> "
                 f"{'OK' if abs(atr_s - op['atr_orden']) < 5e-3 else 'DIFERENTE'}")
        fila = d.loc[te]
        ask_ap = fila.o + fila.sp
        if op["origen"] == "B":
            ok_e = te == vela_e and p == sg + 1 and ask_ap <= niv and abs(ask_ap - op["precio_entrada_ask"]) < 5e-3
            L.append(f"  - Entrada a mercado (caso B): primer minuto de la vela siguiente ({te}); Ask de apertura {ask_ap:.2f} <= nivel {niv:.3f}; "
                     f"el motor compro a {op['precio_entrada_ask']} -> {'OK' if ok_e else 'DIFERENTE'}")
        else:
            previos = d.loc[r.index[sg + 1]: te - pd.Timedelta(minutes=1)]
            mkp = (previos.index.dayofweek <= 4) & ((previos.index.hour * 60 + previos.index.minute) >= APERTURA) & \
                  ((previos.index.hour * 60 + previos.index.minute) < CIERRE)
            previos = previos[mkp]
            sin_toque = bool(((previos.l + previos.sp) > niv).all()) if len(previos) else True
            esperado = ask_ap if ask_ap <= niv else niv
            ok_e = sin_toque and (fila.l + fila.sp) <= niv and abs(esperado - op["precio_entrada_ask"]) < 5e-3
            L.append(f"  - Entrada con orden en espera (caso A): ningun minuto abierto anterior toca el nivel: {sin_toque}; en {te} el Ask minimo "
                     f"{fila.l + fila.sp:.2f} <= {niv:.3f}; precio esperado {esperado:.3f}, motor {op['precio_entrada_ask']} -> {'OK' if ok_e else 'DIFERENTE'}")
        precio = op["precio_entrada_ask"]
        dist = MULT_SL * atr_s
        sl = precio - dist
        lote = round(min(max(math.floor(RIESGO / dist / PASO + 1e-9) * PASO, LOTE_MIN), LOTE_MAX), 2)
        L.append(f"  - Stop inicial a mano: {precio} - 2 x {atr_s:.3f} = {sl:.3f} (motor {op['stop_inicial']}) -> "
                 f"{'OK' if abs(sl - op['stop_inicial']) < 5e-3 else 'DIFERENTE'}; lote: 1.000 / {dist:.3f} = {RIESGO / dist:.3f} -> {lote} "
                 f"(motor {op['lote']}) -> {'OK' if abs(lote - op['lote']) < 1e-9 else 'DIFERENTE'}")
        stop, stop0 = sl, sl
        sal_t, sal_p, mot = None, None, None
        if fila.l <= stop:
            sal_t, sal_p, mot = te, stop, "stop_inicial"
        else:
            for q in range(p, len(r)):
                t0 = r.index[q]
                tramo = d.loc[t0: t0 + pd.Timedelta(minutes=29)]
                mkt = (tramo.index.dayofweek <= 4) & ((tramo.index.hour * 60 + tramo.index.minute) >= APERTURA) & \
                      ((tramo.index.hour * 60 + tramo.index.minute) < CIERRE)
                tramo_ab = tramo[mkt]
                if q - p >= VELAS_FORZADO and len(tramo_ab):
                    sal_t, sal_p, mot = tramo_ab.index[0], tramo_ab.o.iloc[0], "48_velas"
                    break
                if q == p:
                    tramo_ab = tramo_ab[tramo_ab.index > te]
                tocados = tramo_ab[tramo_ab.l <= stop]
                if len(tocados):
                    f = tocados.iloc[0]
                    sal_t = tocados.index[0]
                    sal_p = f.o if f.o < stop else stop
                    mot = ("trailing" if stop > stop0 + 1e-9 else "stop_inicial") + ("_gap" if f.o < stop else "")
                    break
                at = r["atr30"].iloc[q]
                if not np.isnan(at) and r["c"].iloc[q] - MULT_TRAIL * at > stop:
                    stop = r["c"].iloc[q] - MULT_TRAIL * at
        ok_t = (str(sal_t) == str(ts_))
        L.append(f"  - Salida a mano (trailing = cierre - 2,5 x ATR(30) de cada vela; 48 velas = apertura de la vela F+49): {sal_t} a {sal_p:.3f}, "
                 f"motivo {mot} (motor {op['salida']} a {op['precio_salida_bid']}, {op['motivo']}) -> "
                 f"{'OK' if ok_t and abs(sal_p - op['precio_salida_bid']) < 5e-3 and mot == op['motivo'] else 'DIFERENTE'}")
        swap, noches = 0.0, 0
        dia = te.normalize()
        while dia < ts_.normalize():
            if dia.dayofweek <= 4:
                cl = d["c"].loc[:dia + pd.Timedelta(hours=23, minutes=59)].iloc[-1]
                swap += -SWAP_LARGO_ANUAL / 365.0 * cl * op["lote"]
                noches += 1
            dia += pd.Timedelta(days=1)
        bruto = (sal_p - precio) * op["lote"]
        ok_r = abs(bruto - op["pnl_bruto_usd"]) < 0.02 and abs(swap - op["swap_usd"]) < 0.02 and noches == op["noches"]
        L.append(f"  - Resultado a mano: bruto {bruto:,.2f} + swap {swap:,.2f} ({noches} noches) = {bruto + swap:,.2f} "
                 f"(motor: bruto {op['pnl_bruto_usd']:,.2f} + swap {op['swap_usd']:,.2f} ({op['noches']} noches) = {op['pnl_usd']:,.2f}) -> "
                 f"{'OK' if ok_r else 'DIFERENTE'}")
    return L


def prueba_sin_futuro(m, v, ind, corte, n_prueba=15000):
    """Indicadores y operaciones calculados SOLO con las velas hasta K deben coincidir con los de la serie completa."""
    K = min(len(v["t"]), corte + n_prueba)
    vk = {k: (a[:K] if isinstance(a, np.ndarray) else a) for k, a in v.items()}
    ik = indicadores(vk)
    res = {}
    for k in ("main", "sig", "atr14", "atr", "hma", "nivel"):
        a, b = ik[k], ind[k][:K]
        res[k] = bool(np.allclose(a, b, equal_nan=True, rtol=0, atol=1e-9))
    for k in ("baja", "alza", "asia", "act"):
        res[k] = bool(np.array_equal(ik[k], ind[k][:K]))
    ops_k, _, _ = simular(m, vk, ik, corte, K, "OOS")
    ops_f, _, _ = simular(m, v, {**ind, "act": ind["act"]}, corte, K, "OOS")
    ops_k = [o for o in ops_k if o["motivo"] != "fin_segmento"]
    ops_f = [o for o in ops_f if o["motivo"] != "fin_segmento"]
    res["operaciones_iguales"] = ops_k == ops_f
    res["n_ops_comparadas"] = len(ops_k)
    res["velas_comparadas"] = K - corte
    return res


# ------------------------------------------------------------------ principal
def main():
    corto = "--corto" in sys.argv
    t0 = time.time()
    print("Leyendo CSV...", flush=True)
    m, info = cargar_csv()
    print(json.dumps(info), flush=True)
    ts = m["ts"]
    assert np.all(np.diff(ts.astype("int64")) > 0), "CSV no estrictamente creciente"
    v = velas_m30(m)
    n = len(v["t"])
    print(f"M1: {len(ts):,}  M30: {n:,}  {ts[0]} -> {ts[-1]}  ({time.time()-t0:.0f}s)", flush=True)
    ind = indicadores(v)
    corte = int(n * FRAC_IS)
    print(f"Corte 70/30 en la vela {corte}: {v['t'][corte]}", flush=True)
    if corto:
        a, b = corte, corte + 6000
        t1 = time.time()
        ops, eq, cnt = simular(m, v, ind, a, b, "OOS")
        print(f"corto: {len(ops)} ops en {b-a} velas, {time.time()-t1:.1f}s", flush=True)
        print(cnt)
        return
    res, todas, eqs, cnts = {}, [], {}, {}
    for etq, a, b in (("IS", 0, corte), ("OOS", corte, n)):
        t1 = time.time()
        ops, eq, cnt = simular(m, v, ind, a, b, etq)
        r = metricas(ops, eq)
        r["desde"], r["hasta"] = str(v["t"][a]), str(v["t"][b - 1])
        r["velas_m30"] = b - a
        res[etq] = r
        cnts[etq] = cnt
        todas += ops
        eqs[etq] = (v["t"][a:b], eq)
        print(etq, f"{time.time()-t1:.0f}s", json.dumps(r, default=str), flush=True)
    os.makedirs(OUT, exist_ok=True)
    df = pd.DataFrame(todas)
    df.to_csv(os.path.join(OUT, NOM + "_operaciones.csv"), index=False)
    grafico_equity(os.path.join(OUT, NOM + "_equity.png"), *eqs["IS"], *eqs["OOS"], str(v["t"][corte]))
    res["meta"] = dict(velas_m1=len(ts), velas_m30=n, primera=str(ts[0]), ultima=str(ts[-1]), corte=str(v["t"][corte]),
                       spread_mediano=float(np.median(m["sp"])), spread_p95=float(np.percentile(m["sp"], 95)),
                       spread_max=float(m["sp"].max()),
                       activaciones_is=int(ind["act"][:corte].sum()), activaciones_oos=int(ind["act"][corte:].sum()),
                       **info)

    oos = df[df.segmento == "OOS"].reset_index(drop=True)
    isd = df[df.segmento == "IS"]
    ini = pd.Timestamp(res["OOS"]["desde"])
    lim = ini + pd.DateOffset(years=3)
    ent = pd.to_datetime(oos["entrada"])
    p3, resto = oos[ent < lim], oos[ent >= lim]
    anios = por_anio(oos)
    anios_is = por_anio(isd)
    anios_oos_anios = (pd.Timestamp(res["OOS"]["hasta"]) - ini).days / 365.25
    ops_por_anio = len(oos) / anios_oos_anios
    ops_mes = ops_por_anio / 12
    oosA, oosB = oos[oos.origen.isin(["A", "A_apertura"])], oos[oos.origen == "B"]
    gA, gB = grupo(oosA), grupo(oosB)
    gAn, gAg = grupo(oos[oos.origen == "A"]), grupo(oos[oos.origen == "A_apertura"])
    gAi, gBi = grupo(isd[isd.origen.isin(["A", "A_apertura"])]), grupo(isd[isd.origen == "B"])

    def cruza_sabado(a, b):
        d0, d1 = pd.Timestamp(a).normalize(), pd.Timestamp(b).normalize()
        return any((d0 + pd.Timedelta(days=k)).dayofweek == 5 for k in range((d1 - d0).days + 1))
    fin_semana = int(sum(cruza_sabado(a_, b_) for a_, b_ in zip(oos["entrada"], oos["salida"])))
    dias_dentro = float(((pd.to_datetime(oos["salida"]) - pd.to_datetime(oos["entrada"])).dt.total_seconds() / 86400).mean())

    # tres operaciones para reconstruir a mano (fuera de muestra): una B que sale por stop/trailing, una B que sale por 48 velas,
    # y una A si existe (si no, una B con 2 a 6 noches)
    elegidas = []

    def tomar(mask):
        for k in oos.index[mask]:
            if k not in elegidas:
                elegidas.append(k)
                return
    tomar(((oos.origen == "B") & oos.motivo.str.startswith(("trailing", "stop"))).values)
    tomar(((oos.origen == "B") & (oos.motivo == "48_velas")).values)
    if (oos.origen != "B").any():
        tomar((oos.origen != "B").values)
    else:
        tomar(((oos.noches >= 2) & (oos.noches <= 6)).values)
    while len(elegidas) < 3:
        tomar(np.ones(len(oos), dtype=bool))
    ids_glob = [int(df.index[(df.segmento == "OOS")][k]) for k in elegidas]
    lineas = verificar_a_mano(m, df, ids_glob)
    sf = prueba_sin_futuro(m, v, ind, corte)
    print(json.dumps(sf), flush=True)

    mot_oos = oos["motivo"].value_counts().to_dict()
    mot_is = isd["motivo"].value_counts().to_dict()
    json.dump(dict(res=res, contadores=cnts, anios_oos=anios, anios_is=anios_is, ops_mes=ops_mes, ops_por_anio=ops_por_anio,
                   A_oos=gA, B_oos=gB, A_is=gAi, B_is=gBi, fin_semana_oos=fin_semana, motivos_oos=mot_oos,
                   motivos_is=mot_is, sin_futuro=sf),
              open(os.path.join(OUT, NOM + "_resultados.json"), "w"), indent=1, default=str)

    o = res["OOS"]
    ok = lambda c: "✓" if c else "✕"
    c1, c2, c3, c4 = o["pf"] >= 1.3, o["operaciones"] >= 30, o["dd_pct"] < 20, o["pf_sin_mejor"] > 1
    puntos = sum([c1, c2, c3, c4])
    falla = [t for t, c in (("factor de beneficio", c1), ("operaciones", c2), ("caida maxima", c3), ("sin la mejor", c4)) if not c]
    L = []
    L.append("# Reporte fase 04 · US30 MACD(10,50,9) cruza a la baja en sesión asiática + limit en HMA(30) + 1 ATR (M30, solo compras)\n")
    L.append(f"Código: `codigo/{NOM}.py` · Operaciones: `resultados/{NOM}_operaciones.csv` · Curva: `resultados/{NOM}_equity.png` · "
             f"Cifras: `resultados/{NOM}_resultados.json`.\n")
    L.append("> AVISO: el símbolo US30 (punto 0,01; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300) y el swap largo (−6,9 % anual) "
             "son SUPUESTOS de la ficha, tomados de US100 (supuestos 24 y 25). El spread viene de `datos/US30.csv` (supuesto 26: por confirmar de qué bróker). "
             "Si el bróker real difiere, el resultado cambia.\n")
    L.append("## Datos")
    L.append(f"`datos/us30_1m_mt5.csv` (M1, Bid; la columna `fecha` dice UTC pero es hora del servidor y se usó tal cual) con el spread por minuto "
             f"de la última columna de `datos/US30.csv` (TSV, puntos de 0,01). Alineación por fecha: de {fmt(info['filas_m1'], 0)} minutos del M1 curado, "
             f"{fmt(info['m1_con_spread'], 0)} tienen su minuto en US30.csv y {fmt(info['m1_sin_spread'], 0)} no (esos usarían la mediana, "
             f"{fmt(info['spread_mediano_pts'], 0)} puntos). US30.csv tiene {fmt(info['filas_spread_archivo'], 0)} filas, empieza el {info['spread_primera'].replace('T', ' ')} y "
             f"{fmt(info['filas_spread_no_usadas'], 0)} filas no se usan (2009-2010 y el resto del recorte). "
             f"Cierre del M1 distinto al de US30.csv en el mismo minuto: {info['m1_cierre_distinto_al_spread_file']} casos.")
    L.append(f"US30 · {res['meta']['primera']} a {res['meta']['ultima']} (hora del servidor) · {fmt(res['meta']['velas_m1'], 0)} velas M1 · "
             f"{fmt(res['meta']['velas_m30'], 0)} velas M30 (armadas con todas las M1). Spread mediano {fmt(res['meta']['spread_mediano'], 0)} puntos "
             f"({fmt(res['meta']['spread_mediano'] * PUNTO, 2)} unidades), percentil 95 {fmt(res['meta']['spread_p95'], 0)}, máximo {fmt(res['meta']['spread_max'], 0)}.")
    L.append("Calidad: el M1 (resultados/us30_1m_mt5_calidad.md) da NO APTA por el 6,6 % de minutos faltantes (límite 5 %) y el M30 "
             "(resultados/us30_30m_mt5_calidad.md) APTA CON AVISOS (3,6 % de velas faltantes, sin rellenar). La ficha (supuesto 28) decidió usarlo igual, "
             "como en US100. Aviso: los huecos se tratan como ausentes y los resultados pueden cambiar con datos completos.\n")
    L.append(f"Corte 70/30 por velas M30 (int(n × 0,7) = {fmt(corte, 0)}): dentro de muestra {res['IS']['desde']} a {res['IS']['hasta']} "
             f"({fmt(res['IS']['velas_m30'], 0)} velas); fuera de muestra {res['OOS']['desde']} a {res['OOS']['hasta']} ({fmt(res['OOS']['velas_m30'], 0)} velas). "
             f"Cada tramo parte de 100.000.")
    L.append(f"Activaciones (cruce a la baja con sesión asiática): dentro {res['meta']['activaciones_is']}, fuera {res['meta']['activaciones_oos']} "
             f"(incluye las que ocurren con posición abierta, que se ignoran).\n")
    L.append("## Los 4 números, FUERA de muestra y con costes (spread + swap)")
    L.append("| Número | Resultado | Umbral | |\n|---|---|---|---|")
    L.append(f"| Factor de beneficio | {fmt(o['pf'])} | ≥ 1,3 | {ok(c1)} |")
    L.append(f"| Operaciones | {o['operaciones']} | ≥ 30 | {ok(c2)} |")
    L.append(f"| Caída máxima | {fmt(o['dd_pct'])} % | < 20 % | {ok(c3)} |")
    L.append(f"| Factor de beneficio sin la mejor operación | {fmt(o['pf_sin_mejor'])} | > 1 | {ok(c4)} |\n")
    L.append(f"Veredicto {puntos}/4 · {'APRUEBA' if puntos == 4 else 'NO APRUEBA'}" + (f" (falla: {', '.join(falla)})." if falla else "."))
    L.append(f"Referencia sin swap (solo spread): factor de beneficio {fmt(o['pf_sin_swap'])}, sin la mejor {fmt(o['pf_sin_swap_sin_mejor'])}. "
             f"El swap sumó {fmt(o['swap_total'], 0)} USD en {o['operaciones']} operaciones (media {fmt(o['noches_medias'], 1)} noches por operación).")
    L.append(f"Encaje con MI_PLAN.md: la caída de {fmt(o['dd_pct'])} % {'SUPERA' if o['dd_pct'] > 6 else 'no supera'} el 6 % que el trader acepta en backtest "
             f"({'el método puede pasar, pero no encaja con el plan' if o['dd_pct'] > 6 else 'encaja con el plan'}).\n")
    r_ = res["IS"]
    L.append("## Dentro de muestra (solo referencia, no cuenta para el veredicto)")
    L.append(f"Factor de beneficio {fmt(r_['pf'])} (sin swap {fmt(r_['pf_sin_swap'])}) · {r_['operaciones']} operaciones · caída {fmt(r_['dd_pct'])} % · "
             f"sin la mejor {fmt(r_['pf_sin_mejor'])} · resultado neto {fmt(r_['pnl_total'], 0)} USD.\n")
    L.append("## Otros datos fuera de muestra")
    L.append(f"Resultado neto {fmt(o['pnl_total'], 0)} USD sobre 100.000 (bruto {fmt(o['pnl_bruto_total'], 0)} y swap {fmt(o['swap_total'], 0)}) · "
             f"ganadoras {fmt(o['pct_ganadoras'], 1)} % · media por operación {fmt(o['pnl_medio'], 0)} USD · mejor {fmt(o['mejor'], 0)} · peor {fmt(o['peor'], 0)} · "
             f"caída solo con operaciones cerradas {fmt(o['dd_cerradas_pct'])} % (la oficial usa también la pérdida flotante al cierre de cada vela M30).")
    L.append(f"Orden de salidas fuera de muestra: {mot_oos}. Dentro de muestra: {mot_is}. (`stop_inicial` = el stop de 2 × ATR(30) sin que el trailing lo haya subido; "
             f"`trailing` = el stop subido por el trailing; `_gap` = la vela abrió ya por debajo del stop; `48_velas` = cierre forzado; `fin_segmento` = cierre técnico al terminar el tramo.) "
             f"Duración media {fmt(dias_dentro, 2)} días; operaciones que pasan un fin de semana: {fin_semana} de {o['operaciones']}.\n")
    L.append("## (a) Resultado por tramo")
    L.append("Fuera de muestra, primeros 3 años frente al resto (corte " + str(lim.date()) + "):")
    L.append("| Tramo | Operaciones | Factor de beneficio | Sin la mejor | Resultado USD |\n|---|---|---|---|---|")
    for nom, g in (("Primeros 3 años OOS", p3), ("Resto OOS", resto)):
        p = g["pnl_usd"].values
        L.append(f"| {nom} | {len(p)} | {fmt(pf_de(p))} | {fmt(pf_sin_mejor(p))} | {fmt(float(p.sum()), 0)} |")
    L.append("\nPor año (fuera de muestra; el año de entrada de la operación):")
    L.append("| Año | Operaciones | Factor de beneficio | Sin la mejor | FB sin swap | Resultado USD | % ganadoras |\n|---|---|---|---|---|---|---|")
    for a in anios:
        L.append(f"| {a['anio']} | {a['operaciones']} | {fmt(a['pf'])} | {fmt(a['pf_sin_mejor'])} | {fmt(a['pf_sin_swap'])} | {fmt(a['pnl'], 0)} | {fmt(a['pct_ganadoras'], 1)} |")
    perd = [a["anio"] for a in anios if a["pnl"] < 0]
    L.append(f"\nAños fuera de muestra que pierden: {', '.join(perd) if perd else 'ninguno'}.")
    L.append("\nPor año (dentro de muestra, solo referencia):")
    L.append("| Año | Operaciones | Factor de beneficio | Resultado USD |\n|---|---|---|---|")
    for a in anios_is:
        L.append(f"| {a['anio']} | {a['operaciones']} | {fmt(a['pf'])} | {fmt(a['pnl'], 0)} |")
    L.append("\n## (b) Entradas a mercado (caso B) frente a limit que esperó (caso A)")
    L.append("B = compra a mercado en la apertura siguiente a la señal porque el Ask ya está en el nivel o por debajo (la limit de compra en hma(30) + 1 ATR casi siempre queda por encima del precio). "
             "A = la orden limit queda en espera y se llena después (`A` = el Ask baja hasta el nivel; `A_apertura` = una vela abre ya por debajo del nivel y se llena a esa apertura). "
             "'Entrada menos nivel' = precio de entrada menos nivel, en promedio (unidades de índice).")
    L.append("| Grupo (fuera de muestra) | Operaciones | Factor de beneficio | Resultado USD | % ganadoras | Media USD | Entrada menos nivel |\n|---|---|---|---|---|---|---|")
    for nom, g in (("A total (limit que esperó)", gA), ("  A (fill al nivel)", gAn), ("  A_apertura (fill con hueco)", gAg), ("B (mercado)", gB)):
        L.append(f"| {nom} | {g['n']} | {fmt(g['pf'])} | {fmt(g['pnl'], 0)} | {fmt(g['gan'], 1)} | {fmt(g['media'], 0)} | {fmt(g['desv'], 2)} |")
    L.append(f"Dentro de muestra (referencia): A {gAi['n']} operaciones, FB {fmt(gAi['pf'])}, {fmt(gAi['pnl'], 0)} USD; B {gBi['n']} operaciones, FB {fmt(gBi['pf'])}, {fmt(gBi['pnl'], 0)} USD.")
    L.append("\nContadores del motor (qué pasó con cada señal):")
    L.append("| Contador | Dentro de muestra | Fuera de muestra |\n|---|---|---|")
    for k in cnts["OOS"]:
        L.append(f"| {k} | {cnts['IS'][k]} | {cnts['OOS'][k]} |")
    L.append(f"\n## (c) Frecuencia\nFuera de muestra: {o['operaciones']} operaciones en {fmt(anios_oos_anios, 2)} años = {fmt(ops_por_anio, 1)} por año = "
             f"{fmt(ops_mes, 1)} al mes (MI_PLAN.md: unas 6 al mes). Dentro de muestra: {r_['operaciones']} operaciones.")
    L.append(f"\n## (d) Caída frente al plan\nCaída máxima fuera de muestra {fmt(o['dd_pct'])} % frente al 6 % que el trader acepta en backtest: "
             f"{'SUPERA, no encaja con el plan' if o['dd_pct'] > 6 else 'dentro del plan'}. Peor operación {fmt(o['peor'], 0)} USD (el plan arriesga 1 %: 1.000 USD sobre 100.000).")
    L.append("\n## (e) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)")
    L.append("Se rehace cada operación con otro camino de cálculo (velas M30 con `resample` de pandas, ATR con `rolling`, EMA con semilla SMA hecha con `ewm` de pandas, "
             "LWMA/HMA con `rolling.apply` sobre una ventana local, sesión asiática con `zoneinfo` de Python, swap con la última M1 antes de cada medianoche y el stop barrido minuto a minuto) "
             "y se compara con lo que anotó el motor:\n")
    L += ["    " + t for t in lineas]
    L.append("\n## (f) Comprobación de que el motor no mira el futuro")
    L.append(f"Se recalcularon todos los indicadores usando SOLO las velas hasta la {fmt(sf['velas_comparadas'], 0)}ª del tramo fuera de muestra (se descartan las posteriores) y se corrió el motor con ellos: "
             f"MACD principal y señal, ATR(14), ATR(30), HMA, nivel, CRUCE_BAJA, CRUCE_ALZA, ASIA y ACTIVACIÓN coinciden con los de la serie completa "
             f"({'todos iguales' if all(v_ for k_, v_ in sf.items() if k_ not in ('n_ops_comparadas', 'velas_comparadas', 'operaciones_iguales')) else 'HAY DIFERENCIAS: ' + str(sf)}), "
             f"y las {sf['n_ops_comparadas']} operaciones cerradas en ese tramo son idénticas ({'sí' if sf['operaciones_iguales'] else 'NO'}). Además, por construcción: el nivel y el ATR de la señal se calculan con datos hasta el cierre "
             "de la vela de señal inclusive y la orden se coloca en el primer tick de la vela siguiente; el trailing se calcula al cierre y vale desde la apertura siguiente; el cierre forzado usa la apertura de la vela F+49.")
    L.append("\n## Costes y supuestos del backtest")
    L.append("- Spread real del CSV por minuto (Ask = Bid + spread × 0,01): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (ficha). Aviso: el spread de `US30.csv` es de otro origen que el M1 y puede ser optimista o pesimista; en minutos de baja liquidez llega a 22 unidades.")
    L.append("- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M30 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor, sin día triple. Entra en el factor de beneficio y en la caída.")
    L.append("- Símbolo (supuesto): punto 0,01; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 150 puntos (1,5 unidades); horario 01:00–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.")
    L.append("- Indicadores sobre Bid, definiciones del trader: EMA con semilla SMA y alpha 2/(n+1); MACD(10,50,9); HMA(30) = LWMA(2·LWMA(15) − LWMA(30), 5); ATR = SMA del rango verdadero con la primera barra H − L. Sesión asiática: hora de apertura de la vela, servidor = Nueva York + 7 h (con el cambio de hora de EE. UU.), pasada a Asia/Tokyo, en [09:00, 15:00).")
    L.append("- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (`fin_segmento`).")
    L.append("- Una compra consume la señal pendiente. Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1. Equity: capital + operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M30.")
    L.append("- Todo lo demás: los 28 supuestos del pseudocódigo de la ficha. El cierre a las 48 velas cuenta velas de la serie completa, también las de horas cerradas.")
    open(os.path.join(OUT, NOM + "_reporte.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(lineas))
    print(f"VEREDICTO {puntos}/4 · ops/año OOS {ops_por_anio:.1f} · ops/mes {ops_mes:.1f} · {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
