"""
FASE 04 · Backtest · US100 ADX(75) subiendo + extensión 1,382 del día (M15, solo compras)
Implementa el pseudocódigo de la fase 03 de fichas/us100_adx_fib_dia.md.
Motor derivado de codigo/us100_ruptura_donchian_eficiencia.py (mismo motor, ya validado);
cambia solo lo propio de esta regla: ADX(75) de Wilder, rising(.,5), nivel fib_day(1,382) congelado,
vigencia 4 velas, stop inicial 2,5 x ATR_ORDEN (ATR fotografiado en la vela de señal), lote por ese
stop y trailing 3 x ATR(30) de la vela recién cerrada. No optimiza nada: todo viene de la ficha.

Uso:  python codigo/us100_adx_fib_dia.py
Salidas (carpeta resultados/):
  us100_adx_fib_dia_m15_operaciones.csv · us100_adx_fib_dia_m15_equity.png
  us100_adx_fib_dia_m15_reporte.md · us100_adx_fib_dia_m15_resultados.json
"""
import json
import math
import os
import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "datos", "us100_1m_mt5.csv")      # OHLC M1
CSV_SPREAD = os.path.join(RAIZ, "datos", "US100.csv")      # última columna = spread (puntos de 0,1)
OUT = os.path.join(RAIZ, "resultados")
NOM = "us100_adx_fib_dia_m15"

# ---- Parámetros de la ficha (no se tocan) ----
CAPITAL = 100_000.0
RIESGO = 0.01 * CAPITAL          # 1 % del capital inicial = 1.000
N_ADX, K_RISING = 75, 5          # ADX(75) de Wilder; rising(adx, 5)
N_ATR = 30                       # ATR(30) = SMA del rango verdadero
FIB = 0.382                      # nivel = MAX_AYER + 0,382 x rango de ayer (= MIN_AYER + 1,382 x rango)
MULT_SL = 2.5                    # stop inicial = 2,5 x ATR_ORDEN
MULT_TRAIL = 3.0                 # trailing = cierre - 3 x ATR(30) de la vela recién cerrada
VIDA_MAX = 4                     # la orden vive 4 velas (la de colocación incluida)
STOPS_LEVEL = 5                  # puntos enteros (dato del bróker para US100)
APERTURA, CIERRE = 61, 1439      # 01:01 incluido, 23:59 excluido (minutos desde 00:00)
# ---- Símbolo US100 (datos del trader, supuestos 24 a 28 de la ficha) ----
PUNTO = 0.1                      # 1 punto = 0,1 unidades de índice
OZ_LOTE = 1.0                    # 1 lote = 1 USD por unidad de índice (contract_size 1)
PASO, LOTE_MIN, LOTE_MAX = 0.01, 0.01, 300.0
COMISION_LOTE = 0.0
SWAP_LARGO_ANUAL = 0.069         # -6,9 % anual sobre el nocional (cuesta), base 365
SPREAD_FALTANTE = 5              # puntos (mediana), solo si falta el dato
FRAC_IS = 0.70


def cargar_csv():
    ts, o, h, l, c = [], [], [], [], []
    for ch in pd.read_csv(CSV, chunksize=1_000_000,
                          usecols=["fecha", "open", "high", "low", "close"], dtype={"fecha": str}):
        t = pd.to_datetime(ch["fecha"], format="%Y-%m-%dT%H:%M:%SZ")
        ts.append(t.values.astype("datetime64[m]"))
        o.append(ch["open"].values); h.append(ch["high"].values)
        l.append(ch["low"].values); c.append(ch["close"].values)
    ts = np.concatenate(ts)
    # spread por minuto desde US100.csv (mismas filas; se comprueba la fecha una por una)
    cols = ["f", "hr", "o", "h", "l", "c", "tv", "v", "sp"]
    tss, sp = [], []
    for ch in pd.read_csv(CSV_SPREAD, header=None, names=cols, chunksize=1_000_000,
                          usecols=["f", "hr", "sp"], dtype={"f": str, "hr": str}):
        t = pd.to_datetime(ch["f"] + " " + ch["hr"], format="%Y.%m.%d %H:%M")
        tss.append(t.values.astype("datetime64[m]"))
        sp.append(ch["sp"].values.astype(np.float64))
    tss, sp = np.concatenate(tss), np.concatenate(sp)
    assert len(tss) == len(ts) and np.all(tss == ts), "las fechas de US100.csv y us100_1m_mt5.csv no coinciden"
    sp = np.where(np.isnan(sp), SPREAD_FALTANTE, sp)
    return dict(ts=ts, o=np.concatenate(o), h=np.concatenate(h),
                l=np.concatenate(l), c=np.concatenate(c), sp=sp)


def velas_m15(m):
    ts = m["ts"].astype("int64")                    # minutos desde 1970
    clave = ts // 15
    cambios = np.flatnonzero(np.diff(clave)) + 1
    cs = np.concatenate(([0], cambios))             # inicio de cada vela (índice M1)
    ce = np.concatenate((cambios, [len(ts)]))       # fin (excluido)
    return dict(
        t=(clave[cs] * 15).astype("datetime64[m]"), cs=cs, ce=ce,
        o=m["o"][cs], h=np.maximum.reduceat(m["h"], cs),
        l=np.minimum.reduceat(m["l"], cs), c=m["c"][ce - 1])


def rma_wilder(x, n, inicio):
    """Media de Wilder: semilla = media simple de x[inicio:inicio+n]; después r = r + (x - r)/n."""
    out = np.full(len(x), np.nan)
    k = inicio + n - 1
    if k >= len(x):
        return out
    out[k] = np.mean(x[inicio:inicio + n])
    for t in range(k + 1, len(x)):
        out[t] = out[t - 1] + (x[t] - out[t - 1]) / n
    return out


def adx_wilder(h, l, c, n):
    """ADX de Wilder clásico: TR, +DM, -DM suavizados con Wilder (semilla = media de las n primeras),
    DX = 100 |+DI - -DI| / (+DI + -DI), ADX = Wilder de DX con semilla = media de los n primeros DX."""
    N = len(h)
    up = np.full(N, np.nan); dn = np.full(N, np.nan); tr = np.full(N, np.nan)
    up[1:] = h[1:] - h[:-1]
    dn[1:] = l[:-1] - l[1:]
    tr[1:] = np.maximum.reduce([h[1:] - l[1:], np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])])
    pdm = np.where((up > dn) & (up > 0), up, 0.0); pdm[0] = np.nan
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0); mdm[0] = np.nan
    s_tr, s_p, s_m = rma_wilder(tr, n, 1), rma_wilder(pdm, n, 1), rma_wilder(mdm, n, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi, mdi = 100 * s_p / s_tr, 100 * s_m / s_tr
        dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    dx = np.where(np.isnan(dx), np.nan, dx)
    dx0 = np.where((pdi + mdi) == 0, 0.0, dx)       # (+DI + -DI) = 0 -> DX = 0 (no ocurre en la práctica)
    return rma_wilder(dx0, n, n)                    # primer DX válido en el índice n


def indicadores(v):
    h, l, c = v["h"], v["l"], v["c"]
    sc = pd.Series(c)
    cp = sc.shift(1)
    tr = pd.concat([pd.Series(h) - pd.Series(l), (pd.Series(h) - cp).abs(), (pd.Series(l) - cp).abs()],
                   axis=1).max(axis=1)
    tr.iloc[0] = np.nan
    atr = tr.rolling(N_ATR, min_periods=N_ATR).mean().values
    adx = adx_wilder(h, l, c, N_ADX)
    sadx = pd.Series(adx)
    disparo = (sadx > sadx.shift(K_RISING)).fillna(False)            # rising(adx(75),5): mayor que hace 5 velas
    act = disparo & (~disparo.shift(1, fill_value=False).astype(bool))
    # nivel fib_day: AYER = día anterior con velas (día del servidor), todas sus velas, sobre Bid
    dia = v["t"].astype("int64") // 1440
    d_ini = np.concatenate(([0], np.flatnonzero(np.diff(dia)) + 1))
    dmax = np.maximum.reduceat(h, d_ini)
    dmin = np.minimum.reduceat(l, d_ini)
    idx_dia = np.repeat(np.arange(len(d_ini)), np.diff(np.concatenate((d_ini, [len(h)]))))
    nivel = np.full(len(h), np.nan)
    ok = idx_dia >= 1
    mx, mn = dmax[idx_dia[ok] - 1], dmin[idx_dia[ok] - 1]
    nivel[ok] = mx + FIB * (mx - mn)
    return dict(atr=atr, adx=adx, act=act.values, nivel=nivel)


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
    dia_vela = v["t"].astype("int64") // 1440       # día (desde 1970) de cada vela M15
    n_velas = len(cs)
    atr, act, nivel_v = ind["atr"], ind["act"], ind["nivel"]

    ops = []
    pos = None
    orden = None            # dict(nivel, vida, atr)
    senal = None            # (nivel, atr)
    realizado = 0.0
    eq = np.empty(c1 - c0)

    def comprar(i, j, precio, nivel, atr_o, origen):
        """Paso 4. Devuelve la posición o None si se descarta."""
        dist = MULT_SL * atr_o
        if int(round(dist / PUNTO)) < STOPS_LEVEL:
            return None
        sl = precio - dist
        lote = math.floor(RIESGO / (dist * OZ_LOTE) / PASO + 1e-9) * PASO
        lote = round(min(max(lote, LOTE_MIN), LOTE_MAX), 2)
        return dict(i=i, j=j, precio=precio, stop=sl, stop0=sl, lote=lote, atr_ent=atr_o, nivel=nivel,
                    origen=origen, swap=0.0, noches=0)

    def cerrar(p, i, k, px, motivo):
        nonlocal realizado
        bruto = (px - p["precio"]) * OZ_LOTE * p["lote"] - COMISION_LOTE * p["lote"]
        realizado += bruto                       # el swap ya se sumó a 'realizado' al cobrarse cada noche
        ops.append(dict(
            segmento=etiqueta, entrada=str(m["ts"][p["j"]]).replace("T", " "),
            salida=str(m["ts"][k]).replace("T", " "), origen=p["origen"], nivel=round(p["nivel"], 3),
            precio_entrada_ask=round(p["precio"], 3), atr_orden=round(p["atr_ent"], 3),
            stop_inicial=round(p["stop0"], 3), precio_salida_bid=round(px, 3),
            lote=p["lote"], pnl_bruto_usd=round(bruto, 2), swap_usd=round(p["swap"], 2),
            noches=p["noches"], pnl_usd=round(bruto + p["swap"], 2),
            velas_dentro=int(i - p["i"]), motivo=motivo))

    for i in range(c0, c1):
        s, e = cs[i], ce[i]
        # 1. vida de la orden
        if orden is not None:
            orden["vida"] += 1
        j_compra, px_compra = -1, 0.0
        niv_c, atr_c, origen_c = 0.0, 0.0, ""
        if pos is None:
            # 2a/2b: orden viva
            if orden is not None and orden["vida"] >= VIDA_MAX + 1:
                abiertos = np.flatnonzero(mk[s:e])
                if abiertos.size:
                    j0 = s + int(abiertos[0])
                    if ao[j0] >= orden["nivel"]:        # el fill va primero
                        j_compra, px_compra = j0, ao[j0]
                        niv_c, atr_c, origen_c = orden["nivel"], orden["atr"], "A_apertura"
                    else:
                        orden = None                    # vencida: se borra
            elif orden is not None and senal is not None and mk[s] and ao[s] >= orden["nivel"]:
                j_compra, px_compra = s, ao[s]          # 2a: llena antes del reemplazo
                niv_c, atr_c, origen_c = orden["nivel"], orden["atr"], "A_apertura"
            # 2c: señal pendiente
            if j_compra < 0 and senal is not None:
                if mk[s]:
                    nivel_s, atr_s = senal
                    orden = None                        # borrado confirmado (mercado abierto)
                    ask = ao[s]
                    if ask >= nivel_s:                  # caso B: a mercado
                        j_compra, px_compra = s, ask
                        niv_c, atr_c, origen_c = nivel_s, atr_s, "B"
                    elif int(round((nivel_s - ask) / PUNTO)) < STOPS_LEVEL:
                        pass                            # caso C: rechazada, no queda orden viva
                    else:                               # caso A: orden en espera
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
                    niv_c, atr_c, origen_c = niv, orden["atr"], "A"
            # 4. compra
            if j_compra >= 0:
                orden = None
                senal = None                            # una compra consume la señal (no queda señal vieja)
                pos = comprar(i, j_compra, px_compra, niv_c, atr_c, origen_c)
                if pos is not None:
                    # minuto de la compra: gana el stop
                    j = j_compra
                    if ml[j] <= pos["stop"]:
                        px = pos["stop"]
                        if px_compra == ao[j]:
                            px = min(px, mo[j])
                        cerrar(pos, i, j, px, "stop")
                        pos = None
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
                tr = cC[i] - MULT_TRAIL * atr[i]
                if tr > pos["stop"]:
                    pos["stop"] = tr
        # 6. señal al cierre
        if pos is None and act[i] and not np.isnan(nivel_v[i]) and not np.isnan(atr[i]):
            senal = (nivel_v[i], atr[i])
        # fin de segmento
        if i == c1 - 1 and pos is not None:
            cerrar(pos, i, e - 1, mc[e - 1], "fin_segmento")
            pos = None
        # SWAP: posición abierta al pasar la medianoche del servidor (noches de lunes a viernes)
        if pos is not None and i + 1 < n_velas:
            for d in range(int(dia_vela[i]), int(dia_vela[i + 1])):
                if (d + 3) % 7 <= 4:                    # la noche que empieza al terminar ese día L-V
                    sw = -SWAP_LARGO_ANUAL / 365.0 * cC[i] * pos["lote"] * OZ_LOTE
                    pos["swap"] += sw
                    pos["noches"] += 1
                    realizado += sw
        flot = 0.0 if pos is None else (cC[i] - pos["precio"]) * OZ_LOTE * pos["lote"]
        eq[i - c0] = CAPITAL + realizado + flot
    return ops, eq


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
    cb = np.concatenate(([CAPITAL], CAPITAL + np.cumsum(bruto))) if n else np.array([CAPITAL])
    pb = np.maximum.accumulate(cb)
    ddb = float(((pb - cb) / pb).max() * 100)
    return dict(operaciones=n, pf=pf_de(pnl), pf_sin_mejor=pf_sin_mejor(pnl), dd_pct=dd,
                dd_cerradas_pct=ddc, pf_sin_swap=pf_de(bruto), pf_sin_swap_sin_mejor=pf_sin_mejor(bruto),
                dd_cerradas_sin_swap_pct=ddb,
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
    ax.set_title("US100 ADX(75) + extensión 1,382 del día · equity por vela M15 (capital 100.000, spread y swap)")
    ax.set_ylabel("USD")
    ax.legend(loc="upper left", frameon=False)
    ax.text(0.99, 0.02, "cada tramo parte de 100.000 · corte " + corte_txt, transform=ax.transAxes,
            ha="right", fontsize=8, color="#555")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def verificar_a_mano(m, ops_df, indices):
    """Cordura del motor: reconstruye operaciones por otro camino (velas con resample de pandas, ADX con
    ewm de pandas, nivel desde el máximo/mínimo diario de las M1, swap con la última M1 antes de cada
    medianoche, stop barrido minuto a minuto) y compara con lo que anotó el motor."""
    d = pd.DataFrame({"o": m["o"], "h": m["h"], "l": m["l"], "c": m["c"], "sp": m["sp"] * PUNTO},
                     index=pd.DatetimeIndex(m["ts"].astype("datetime64[ns]")))
    r = d.resample("15min", label="left", closed="left").agg(
        {"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    cp = r["c"].shift(1)
    tr = pd.concat([r.h - r.l, (r.h - cp).abs(), (r.l - cp).abs()], axis=1).max(axis=1)
    tr.iloc[0] = np.nan
    r["atr"] = tr.rolling(30).mean()
    # ADX por ewm (alpha = 1/75): otra forma de calcular Wilder; difiere del motor solo en la semilla
    up, dn = r.h.diff(), -r.l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=r.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=r.index)
    a = 1 / 75
    atr_w = tr.ewm(alpha=a, adjust=False, min_periods=75).mean()
    pdi = 100 * pdm.ewm(alpha=a, adjust=False, min_periods=75).mean() / atr_w
    mdi = 100 * mdm.ewm(alpha=a, adjust=False, min_periods=75).mean() / atr_w
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    adx = dx.ewm(alpha=a, adjust=False, min_periods=75).mean()
    disp = (adx > adx.shift(5))
    r["act"] = disp & ~disp.shift(fill_value=False)
    # nivel desde las M1 (otro camino que el de velas M15): máximo/mínimo del día anterior con datos
    dd1 = d.resample("D").agg({"h": "max", "l": "min"}).dropna()
    L = []
    for ix in indices:
        op = ops_df.loc[ix]
        te, ts_ = pd.Timestamp(op["entrada"]), pd.Timestamp(op["salida"])
        L.append(f"Operación #{ix} ({op['segmento']}, origen {op['origen']}): entrada {op['entrada']} · salida {op['salida']} · motivo {op['motivo']} · noches {op['noches']}")
        vela_e = te.floor("15min")
        pos = r.index.get_loc(vela_e)
        # señal candidata: B -> la vela anterior; A -> la última activación en las 4 velas previas a la de entrada
        rango = [pos - 1] if op["origen"] == "B" else list(range(pos - 1, pos - 5, -1))
        sig = next((q for q in rango if bool(r["act"].iloc[q])), None)
        if sig is None:
            L.append("  - Señal: ninguna activación en las velas previas con el ADX a mano -> DIFERENTE")
            continue
        t_sig = r.index[sig]
        ayer = dd1.index[dd1.index.get_loc(t_sig.normalize()) - 1]
        niv = dd1.loc[ayer, "l"] + 1.382 * (dd1.loc[ayer, "h"] - dd1.loc[ayer, "l"])
        atr_s = r["atr"].iloc[sig]
        L.append(f"  - Señal a mano: activación del ADX(75) en la vela {t_sig}; ayer = {ayer.date()} (máx {dd1.loc[ayer, 'h']:.1f}, mín {dd1.loc[ayer, 'l']:.1f}) "
                 f"-> nivel = mín + 1,382 x rango = {niv:.3f} (motor {op['nivel']}) -> {'OK' if abs(niv - op['nivel']) < 5e-3 else 'DIFERENTE'}")
        L.append(f"  - ATR(30) en la vela de señal a mano {atr_s:.3f} (motor {op['atr_orden']}) -> {'OK' if abs(atr_s - op['atr_orden']) < 5e-3 else 'DIFERENTE'}")
        # entrada: a mano, minuto a minuto desde la apertura de la vela siguiente a la señal
        ini = r.index[sig + 1]
        tram = d.loc[ini: te]
        mk_ = (tram.index.dayofweek <= 4) & ((tram.index.hour * 60 + tram.index.minute) >= APERTURA) & \
              ((tram.index.hour * 60 + tram.index.minute) < CIERRE)
        tram = tram[mk_]
        fila = d.loc[te]
        if op["origen"] == "B":
            ask0 = fila.o + fila.sp
            L.append(f"  - Entrada a mercado: primer minuto de la vela {vela_e} ({te}) tiene Ask de apertura {ask0:.1f} >= nivel {niv:.3f}; "
                     f"el motor compró a {op['precio_entrada_ask']} -> {'OK' if te == vela_e and ask0 >= niv and abs(ask0 - op['precio_entrada_ask']) < 5e-3 else 'DIFERENTE'}")
        else:
            previos = tram[tram.index < te]
            sin_toque = bool(((previos.h + previos.sp) < niv).all()) if len(previos) else True
            ask_ap = fila.o + fila.sp
            px_ok = abs(op["precio_entrada_ask"] - niv) < 5e-3 or abs(op["precio_entrada_ask"] - ask_ap) < 5e-3
            L.append(f"  - Entrada con orden en espera: ningún minuto abierto antes de {te} alcanza el nivel (Ask máximo < {niv:.3f}): {sin_toque}; "
                     f"en {te} el Ask máximo es {fila.h + fila.sp:.1f} (Ask apertura {ask_ap:.1f}); precio del motor {op['precio_entrada_ask']} -> "
                     f"{'OK' if sin_toque and (fila.h + fila.sp) >= niv and px_ok else 'DIFERENTE'}")
        precio = op["precio_entrada_ask"]
        sl = precio - 2.5 * atr_s
        dist = precio - sl
        lote = round(min(max(math.floor(RIESGO / dist / PASO + 1e-9) * PASO, LOTE_MIN), LOTE_MAX), 2)
        L.append(f"  - Stop inicial a mano: {precio} - 2,5 x {atr_s:.3f} = {sl:.3f} (motor {op['stop_inicial']}) -> {'OK' if abs(sl - op['stop_inicial']) < 5e-3 else 'DIFERENTE'}; "
                 f"lote a mano: 1.000 / {dist:.3f} = {RIESGO / dist:.3f} -> {lote} (motor {op['lote']}) -> {'OK' if abs(lote - op['lote']) < 1e-9 else 'DIFERENTE'}")
        # gestión del stop con pandas
        stop = sl
        sal_t, sal_p = None, None
        if fila.l <= stop:
            sal_t, sal_p = te, min(stop, fila.o) if abs(precio - (fila.o + fila.sp)) < 5e-3 else stop
        else:
            for q in range(pos, len(r)):
                t0 = r.index[q]
                tramo = d.loc[t0: t0 + pd.Timedelta(minutes=29)]
                if q == pos:
                    tramo = tramo[tramo.index > te]
                mkt = (tramo.index.dayofweek <= 4) & ((tramo.index.hour * 60 + tramo.index.minute) >= APERTURA) & \
                      ((tramo.index.hour * 60 + tramo.index.minute) < CIERRE)
                tramo = tramo[mkt]
                tocados = tramo[tramo.l <= stop]
                if len(tocados):
                    f = tocados.iloc[0]
                    sal_t = tocados.index[0]
                    sal_p = f.o if f.o < stop else stop
                    break
                cierre, at = r["c"].iloc[q], r["atr"].iloc[q]
                if not np.isnan(at) and cierre - 3 * at > stop:
                    stop = cierre - 3 * at
        ok_t = (str(sal_t) == str(ts_))
        L.append(f"  - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = {sal_t} a {sal_p:.3f} "
                 f"(motor {op['salida']} a {op['precio_salida_bid']}) -> {'OK' if ok_t and abs(sal_p - op['precio_salida_bid']) < 5e-3 else 'DIFERENTE'}")
        # swap con la última M1 antes de cada medianoche L-V entre entrada y salida
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
                 f"(motor: bruto {op['pnl_bruto_usd']:,.2f} + swap {op['swap_usd']:,.2f} ({op['noches']} noches) = {op['pnl_usd']:,.2f}) -> {'OK' if ok_r else 'DIFERENTE'}")
    return L


def grupo(g):
    p = g["pnl_usd"].values
    if len(p) == 0:
        return dict(n=0, pf=0.0, pnl=0.0, gan=0.0, media=0.0, desv=0.0)
    return dict(n=len(p), pf=pf_de(p), pnl=float(p.sum()), gan=float((p > 0).mean() * 100),
                media=float(p.mean()), desv=float((g["precio_entrada_ask"] - g["nivel"]).mean()))


def main():
    print("Leyendo CSV...", flush=True)
    m = cargar_csv()
    ts = m["ts"]
    assert np.all(np.diff(ts.astype("int64")) > 0), "CSV no estrictamente creciente en el tiempo"
    v = velas_m15(m)
    n = len(v["t"])
    print(f"M1: {len(ts):,}  M15: {n:,}  {ts[0]} -> {ts[-1]}", flush=True)
    ind = indicadores(v)
    corte = int(n * FRAC_IS)
    print(f"Corte 70/30 en la vela {corte}: {v['t'][corte]}", flush=True)
    res, todas, eqs = {}, [], {}
    for etq, a, b in (("IS", 0, corte), ("OOS", corte, n)):
        ops, eq = simular(m, v, ind, a, b, etq)
        r = metricas(ops, eq)
        r["desde"], r["hasta"] = str(v["t"][a]), str(v["t"][b - 1])
        r["velas_m15"] = b - a
        res[etq] = r
        todas += ops
        eqs[etq] = (v["t"][a:b], eq)
        print(etq, json.dumps(r, indent=1, default=str), flush=True)
    os.makedirs(OUT, exist_ok=True)
    df = pd.DataFrame(todas)
    df.to_csv(os.path.join(OUT, NOM + "_operaciones.csv"), index=False)
    grafico_equity(os.path.join(OUT, NOM + "_equity.png"), *eqs["IS"], *eqs["OOS"], str(v["t"][corte]))
    res["meta"] = dict(velas_m1=len(ts), velas_m15=n, primera=str(ts[0]), ultima=str(ts[-1]),
                       corte=str(v["t"][corte]), spread_cero_o_faltante=int((m["sp"] <= 0).sum()),
                       spread_mediano=float(np.median(m["sp"])),
                       activaciones_is=int(ind["act"][:corte].sum()), activaciones_oos=int(ind["act"][corte:].sum()))

    oos = df[df.segmento == "OOS"].reset_index(drop=True)
    ini = pd.Timestamp(res["OOS"]["desde"])
    lim = ini + pd.DateOffset(years=3)
    ent = pd.to_datetime(oos["entrada"])
    p3, resto = oos[ent < lim], oos[ent >= lim]
    anios = por_anio(oos)
    anios_is = por_anio(df[df.segmento == "IS"])
    anios_oos_anios = (pd.Timestamp(res["OOS"]["hasta"]) - ini).days / 365.25
    ops_por_anio = len(oos) / anios_oos_anios
    ops_mes = ops_por_anio / 12
    # A (ruptura: orden en espera que se llena) frente a B (mercado)
    oosA, oosB = oos[oos.origen.isin(["A", "A_apertura"])], oos[oos.origen == "B"]
    oosA_nivel, oosA_gap = oos[oos.origen == "A"], oos[oos.origen == "A_apertura"]
    isd = df[df.segmento == "IS"]
    gA, gB, gAn, gAg = grupo(oosA), grupo(oosB), grupo(oosA_nivel), grupo(oosA_gap)
    gAi, gBi = grupo(isd[isd.origen.isin(["A", "A_apertura"])]), grupo(isd[isd.origen == "B"])
    # operaciones que pasan un fin de semana (noche del viernes)
    fe = pd.to_datetime(oos["entrada"]); fs = pd.to_datetime(oos["salida"])
    def cruza_sabado(a, b):
        d0, d1 = pd.Timestamp(a).normalize(), pd.Timestamp(b).normalize()
        return any((d0 + pd.Timedelta(days=k)).dayofweek == 5 for k in range((d1 - d0).days + 1))
    fin_semana = int(sum(cruza_sabado(a_, b_) for a_, b_ in zip(oos["entrada"], oos["salida"])))
    fe = pd.to_datetime(oos["entrada"]); fs = pd.to_datetime(oos["salida"])
    dias_dentro = float(((fs - fe).dt.total_seconds() / 86400).mean())

    # ---- cordura a mano: una del caso B, una del caso A y una que cruza varias noches (distintas) ----
    elegidas = []
    def tomar(mask):
        for k in oos.index[mask]:
            if k not in elegidas:
                elegidas.append(k); return
    tomar((oos.origen == "B").values)
    tomar((oos.origen == "A").values)
    tomar(((oos.noches >= 2) & (oos.noches <= 6)).values)
    ids_glob = [int(df.index[(df.segmento == "OOS")][k]) for k in elegidas]
    lineas = verificar_a_mano(m, df, ids_glob)
    json.dump(dict(res=res, anios_oos=anios, anios_is=anios_is, ops_mes=ops_mes, ops_por_anio=ops_por_anio,
                   A_oos=gA, B_oos=gB, A_is=gAi, B_is=gBi, fin_semana_oos=fin_semana),
              open(os.path.join(OUT, NOM + "_resultados.json"), "w"), indent=1, default=str)

    o = res["OOS"]
    ok = lambda c: "✓" if c else "✕"
    c1, c2, c3, c4 = o["pf"] >= 1.3, o["operaciones"] >= 30, o["dd_pct"] < 20, o["pf_sin_mejor"] > 1
    puntos = sum([c1, c2, c3, c4])
    L = []
    L.append("# Reporte fase 04 · US100 ADX(75) subiendo + extensión 1,382 del día (M15, solo compras)\n")
    L.append(f"Código: `codigo/{NOM}.py` · Operaciones: `resultados/{NOM}_operaciones.csv` · "
             f"Curva: `resultados/{NOM}_equity.png` · Cifras: `{NOM}_resultados.json`.\n")
    L.append("## Datos")
    L.append(f"datos/us100_1m_mt5.csv (M1, Bid) con el spread por minuto de datos/US100.csv (última columna, puntos de 0,1; "
             f"las dos tablas coinciden fila a fila) · US100 · {res['meta']['primera']} a {res['meta']['ultima']} (hora del servidor) · "
             f"{fmt(res['meta']['velas_m1'], 0)} velas M1 · {fmt(res['meta']['velas_m15'], 0)} velas M15.")
    L.append(f"Spread mediano {fmt(res['meta']['spread_mediano'], 0)} puntos; minutos con spread 0 o ausente: {res['meta']['spread_cero_o_faltante']}.")
    L.append("Calidad: el informe del M1 (resultados/us100_1m_mt5_calidad.md) dice NO APTA por umbral provisional (5,5 % de minutos M1 "
             "faltantes dentro del horario; límite 5 %); el de las velas M15 (resultados/us100_15m_mt5_calidad.md) dice APTA CON AVISOS "
             "(2,8 % de velas M15 faltantes, sin rellenar). Las fases 02 y 03 ya decidieron conservar el M1 para resolver el orden del stop. "
             "Se corre con ese aviso: los minutos sin ticks (sobre todo 2011 a 2014) se tratan como ausentes, sin rellenar.\n")
    L.append(f"Corte 70/30 por velas M15 (int(n x 0,7) = {fmt(corte, 0)}): dentro de muestra {res['IS']['desde']} a {res['IS']['hasta']} "
             f"({fmt(res['IS']['velas_m15'], 0)} velas); fuera de muestra {res['OOS']['desde']} a {res['OOS']['hasta']} ({fmt(res['OOS']['velas_m15'], 0)} velas).")
    L.append(f"Activaciones del ADX en el tramo: dentro {res['meta']['activaciones_is']}, fuera {res['meta']['activaciones_oos']} (incluye las que ocurren con posición abierta, que se ignoran).\n")
    L.append("## Los 4 números, FUERA de muestra y con costes (spread + swap)")
    L.append("| Número | Resultado | Umbral | |\n|---|---|---|---|")
    L.append(f"| Factor de beneficio | {fmt(o['pf'])} | ≥ 1,3 | {ok(c1)} |")
    L.append(f"| Operaciones | {o['operaciones']} | ≥ 30 | {ok(c2)} |")
    L.append(f"| Caída máxima | {fmt(o['dd_pct'])} % | < 20 % | {ok(c3)} |")
    L.append(f"| Factor de beneficio sin la mejor operación | {fmt(o['pf_sin_mejor'])} | > 1 | {ok(c4)} |\n")
    L.append(f"Veredicto {puntos}/4 · {'APRUEBA el método' if puntos == 4 else 'NO APRUEBA'}.")
    L.append(f"Referencia sin swap (solo spread): factor de beneficio {fmt(o['pf_sin_swap'])}, sin la mejor {fmt(o['pf_sin_swap_sin_mejor'])}. "
             f"El swap sumó {fmt(o['swap_total'], 0)} USD en {o['operaciones']} operaciones (media {fmt(o['noches_medias'], 1)} noches por operación).")
    L.append(f"Encaje con MI_PLAN.md: la caída de {fmt(o['dd_pct'])} % {'SUPERA' if o['dd_pct'] > 6 else 'no supera'} el 6 % que el trader acepta en backtest "
             f"({'pasa el método pero no encaja con el plan' if o['dd_pct'] > 6 else 'encaja con el plan'}).\n")
    r_ = res["IS"]
    L.append("## Dentro de muestra (solo referencia, no cuenta para el veredicto)")
    L.append(f"Factor de beneficio {fmt(r_['pf'])} (sin swap {fmt(r_['pf_sin_swap'])}) · {r_['operaciones']} operaciones · caída {fmt(r_['dd_pct'])} % · sin la mejor {fmt(r_['pf_sin_mejor'])} · resultado neto {fmt(r_['pnl_total'], 0)} USD.\n")
    L.append("## Otros datos fuera de muestra")
    L.append(f"Resultado neto {fmt(o['pnl_total'], 0)} USD sobre 100.000 (bruto {fmt(o['pnl_bruto_total'], 0)} y swap {fmt(o['swap_total'], 0)}) · "
             f"ganadoras {fmt(o['pct_ganadoras'], 1)} % · media por operación {fmt(o['pnl_medio'], 0)} USD · mejor {fmt(o['mejor'], 0)} · peor {fmt(o['peor'], 0)} · "
             f"caída solo con operaciones cerradas {fmt(o['dd_cerradas_pct'])} % (la oficial usa también la pérdida flotante al cierre de cada vela M15).")
    mot = oos["motivo"].value_counts().to_dict()
    L.append(f"Motivos de salida fuera de muestra: {mot}. Duración media {fmt(dias_dentro, 1)} días; operaciones que pasan al menos un fin de semana: {fin_semana} de {o['operaciones']}.\n")
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
    L.append("\nPor año (dentro de muestra, solo referencia):")
    L.append("| Año | Operaciones | Factor de beneficio | Resultado USD |\n|---|---|---|---|")
    for a in anios_is:
        L.append(f"| {a['anio']} | {a['operaciones']} | {fmt(a['pf'])} | {fmt(a['pnl'], 0)} |")
    L.append("\n## (b) Caso A frente a caso B")
    L.append("A = la orden en espera se llena (incluye `A` = el precio sube hasta el nivel y se llena en el nivel, y `A_apertura` = una orden viva se llena a la apertura de una vela que abre ya pasada del nivel); "
             "B = entrada a mercado en la apertura siguiente a la señal con el Ask ya en el nivel o más allá. 'Sobreprecio' = precio de entrada menos nivel, en promedio.")
    L.append("| Grupo (fuera de muestra) | Operaciones | Factor de beneficio | Resultado USD | % ganadoras | Media USD | Sobreprecio medio (pts de índice) |\n|---|---|---|---|---|---|---|")
    for nom, g in (("A total", gA), ("  A (fill al nivel)", gAn), ("  A_apertura (fill con hueco)", gAg), ("B (mercado)", gB)):
        L.append(f"| {nom} | {g['n']} | {fmt(g['pf'])} | {fmt(g['pnl'], 0)} | {fmt(g['gan'], 1)} | {fmt(g['media'], 0)} | {fmt(g['desv'], 2)} |")
    L.append(f"Dentro de muestra (referencia): A {gAi['n']} operaciones, FB {fmt(gAi['pf'])}, {fmt(gAi['pnl'], 0)} USD; B {gBi['n']} operaciones, FB {fmt(gBi['pf'])}, {fmt(gBi['pnl'], 0)} USD.")
    L.append(f"\n## (c) Frecuencia\nFuera de muestra: {o['operaciones']} operaciones en {fmt(anios_oos_anios, 2)} años = {fmt(ops_por_anio, 1)} por año = "
             f"{fmt(ops_mes, 1)} al mes (MI_PLAN.md: unas 6 al mes). Dentro de muestra: {r_['operaciones']} operaciones.")
    L.append(f"\n## (d) Caída frente al plan\nCaída máxima fuera de muestra {fmt(o['dd_pct'])} % frente al 6 % que el trader acepta en backtest: "
             f"{'SUPERA, no encaja con el plan' if o['dd_pct'] > 6 else 'dentro del plan'}. Peor operación {fmt(o['peor'], 0)} USD (el plan arriesga 1 %; aquí 1.000 USD sobre 100.000).")
    L.append("\n## (e) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)")
    L.append("Se rehace cada operación con otro camino de cálculo (velas M15 con `resample` de pandas, ATR con `rolling`, ADX con `ewm` de pandas, "
             "nivel desde el máximo y mínimo diario de las M1, swap con la última M1 antes de cada medianoche y el stop barrido minuto a minuto), "
             "y se compara con lo que anotó el motor:\n")
    L += ["    " + t for t in lineas]
    L.append("\n## Costes y supuestos del backtest")
    L.append("- Spread real del CSV por minuto (Ask = Bid + spread × 0,1): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (la ficha). Aviso de la ficha (supuesto 30): el spread es de RoboForex medido de 2017-12 a 2026; antes es un perfil fabricado, y puede ser optimista.")
    L.append("- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M15 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor (la noche del viernes cuenta una vez), sin día triple. Se suma al resultado de cada operación y entra en el factor de beneficio y en la caída.")
    L.append("- Símbolo: punto 0,1; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 5 puntos; horario 01:01–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.")
    L.append("- ADX de Wilder clásico (semilla = media simple de los 75 primeros valores de TR/+DM/-DM y de los 75 primeros DX) sobre las velas M15 Bid completas; rising = mayor que hace 5 velas. Decisión de implementación: la ficha no fija la semilla; solo afecta a las primeras ~600 velas.")
    L.append("- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (motivo `fin_segmento`).")
    L.append("- Una compra consume la señal pendiente (si una orden vieja se llena en el primer tick, la señal nueva no se coloca nunca más tarde). El motor hermano dejaba la señal viva en ese caso; aquí se limpia.")
    L.append("- Equity: capital + resultado de operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M15; la caída máxima sale de esa curva.")
    L.append("- Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1.")
    L.append("- Todo lo demás: los 30 supuestos del pseudocódigo de la ficha.")
    open(os.path.join(OUT, NOM + "_reporte.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(lineas))
    print(f"VEREDICTO {puntos}/4 · ops/año OOS {ops_por_anio:.1f}")


if __name__ == "__main__":
    main()
