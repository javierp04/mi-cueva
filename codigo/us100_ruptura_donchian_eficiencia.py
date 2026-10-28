"""
FASE 04 · Backtest · US100 ruptura Donchian(55) con eficiencia (M30, solo compras)
Implementa el pseudocódigo de la fase 03 de fichas/us100_ruptura_donchian_eficiencia.md.
Motor derivado de codigo/xauusd_ruptura_donchian_eficiencia.py (mismo motor validado);
solo cambia lo propio de US100 y se añade el SWAP. No optimiza nada: todo viene de la ficha.

Uso:  python codigo/us100_ruptura_donchian_eficiencia.py
Salidas (carpeta resultados/):
  us100_ruptura_donchian_eficiencia_operaciones.csv
  us100_ruptura_donchian_eficiencia_equity.png
  us100_ruptura_donchian_eficiencia_reporte.md
  us100_ruptura_donchian_eficiencia_resultados.json
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
NOM = "us100_ruptura_donchian_eficiencia"

# ---- Parámetros de la ficha (no se tocan) ----
CAPITAL = 100_000.0
RIESGO = 0.01 * CAPITAL          # 1 % del capital inicial = 1.000
N_DON, N_SWING, N_ATR, N_EF = 55, 20, 30, 50
K_PER, K_SUAV = 7, 3
MULT_ATR = 3.0
VIDA_MAX = 10
STOPS_LEVEL = 5                  # puntos enteros (dato del bróker para US100)
APERTURA, CIERRE = 61, 1439      # 01:01 incluido, 23:59 excluido (minutos desde 00:00)
# ---- Símbolo US100 (datos del trader, supuestos 23 a 27 de la ficha) ----
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
    dia_vela = v["t"].astype("int64") // 1440       # día (desde 1970) de cada vela M30
    n_velas = len(cs)
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
        return dict(i=i, j=j, precio=precio, stop=sw, stop0=sw, lote=lote, atr_ent=atr[i],
                    swap=0.0, noches=0)

    def cerrar(p, i, k, px, motivo):
        nonlocal realizado
        bruto = (px - p["precio"]) * OZ_LOTE * p["lote"] - COMISION_LOTE * p["lote"]
        realizado += bruto                       # el swap ya se sumó a 'realizado' al cobrarse cada noche
        ops.append(dict(
            segmento=etiqueta, entrada=str(m["ts"][p["j"]]).replace("T", " "),
            salida=str(m["ts"][k]).replace("T", " "), precio_entrada_ask=round(p["precio"], 3),
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
    # caída sin swap (solo referencia): curva de cierres brutos
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
    # una curva por tramo (cada tramo se simula desde el capital inicial)
    ax.plot(tis.astype("datetime64[s]"), eis, color="#1f77b4", lw=0.9, label="dentro de muestra (70 %)")
    ax.plot(tos.astype("datetime64[s]"), eos, color="#d62728", lw=0.9, label="fuera de muestra (30 %)")
    ax.axvline(tos[0].astype("datetime64[s]"), color="#888", ls="--", lw=0.8)
    ax.axhline(CAPITAL, color="#bbb", lw=0.6)
    ax.set_title("US100 ruptura Donchian con eficiencia · equity por vela M30 (capital 100.000, spread y swap)")
    ax.set_ylabel("USD")
    ax.legend(loc="upper left", frameon=False)
    ax.text(0.99, 0.02, "cada tramo parte de 100.000 · corte " + corte_txt, transform=ax.transAxes,
            ha="right", fontsize=8, color="#555")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def verificar_a_mano(m, ops_df, indices):
    """Cordura del motor: reconstruye 3 operaciones con pandas (velas con resample, no con el motor)
    y compara stop inicial, lote, nivel de entrada, salida y swap. Devuelve líneas de texto."""
    d = pd.DataFrame({"o": m["o"], "h": m["h"], "l": m["l"], "c": m["c"], "sp": m["sp"] * PUNTO},
                     index=pd.DatetimeIndex(m["ts"].astype("datetime64[ns]")))
    r = d.resample("30min", label="left", closed="left").agg(
        {"o": "first", "h": "max", "l": "min", "c": "last"}).dropna()
    cp = r["c"].shift(1)
    tr = pd.concat([r.h - r.l, (r.h - cp).abs(), (r.l - cp).abs()], axis=1).max(axis=1)
    tr.iloc[0] = np.nan
    r["atr"] = tr.rolling(30).mean()
    r["don"] = r.h.rolling(55).max()
    r["swing_prev"] = r.l.shift(1).rolling(20).min()
    L = []
    for ix in indices:
        op = ops_df.loc[ix]
        te, ts_ = pd.Timestamp(op["entrada"]), pd.Timestamp(op["salida"])
        L.append(f"Operación #{ix} ({op['segmento']}): entrada {op['entrada']} · salida {op['salida']} · motivo {op['motivo']}")
        vela_e = te.floor("30min")
        pos = r.index.get_loc(vela_e)
        sw = r["swing_prev"].iloc[pos]
        L.append(f"  - Stop inicial a mano: mínimo de las 20 velas M30 previas a {vela_e} = {sw:.1f} "
                 f"(motor {op['stop_inicial']}) -> {'OK' if abs(sw - op['stop_inicial']) < 1e-6 else 'DIFERENTE'}")
        fila = d.loc[te]
        ask_alto = fila.h + fila.sp
        L.append(f"  - Minuto de entrada {te}: apertura {fila.o}, máximo {fila.h}, spread {fila.sp:.1f} -> "
                 f"Ask apertura {fila.o + fila.sp:.1f}, Ask máximo {ask_alto:.1f}; precio de entrada del motor {op['precio_entrada_ask']}")
        # nivel: máximo de 55 velas en alguna vela de señal de las 12 anteriores
        cand = r["don"].iloc[pos - 12:pos]
        hit = [(t, v_) for t, v_ in cand.items() if abs(v_ - op["precio_entrada_ask"]) < 1e-6]
        if hit:
            L.append(f"  - Nivel de entrada: coincide con el máximo de 55 velas a mano al cierre de {hit[-1][0]} = {hit[-1][1]:.1f} -> OK")
        else:
            gap = fila.o + fila.sp
            L.append(f"  - Nivel de entrada: ningún máximo de 55 velas previo coincide; la entrada fue a la apertura con hueco "
                     f"(Ask apertura {gap:.1f}) -> {'OK' if abs(gap - op['precio_entrada_ask']) < 1e-6 else 'DIFERENTE'}")
        dist = op["precio_entrada_ask"] - sw
        lote = round(min(max(math.floor(RIESGO / dist / PASO + 1e-9) * PASO, LOTE_MIN), LOTE_MAX), 2)
        L.append(f"  - Lote a mano: 1.000 / ({op['precio_entrada_ask']} - {sw:.1f}) = {RIESGO / dist:.3f} -> {lote} "
                 f"(motor {op['lote']}) -> {'OK' if abs(lote - op['lote']) < 1e-9 else 'DIFERENTE'}")
        # repetir la gestión del stop con pandas
        stop = sw
        sal_t, sal_p, swap, noches = None, None, 0.0, 0
        idx_r = list(range(pos, len(r)))
        for q in idx_r:
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
            cierre = r["c"].iloc[q]
            at = r["atr"].iloc[q]
            if not np.isnan(at) and cierre - 3 * at > stop:
                stop = cierre - 3 * at
            if q + 1 < len(r):
                d0, d1 = r.index[q].normalize(), r.index[q + 1].normalize()
                dd_ = d0
                while dd_ < d1:
                    if dd_.dayofweek <= 4:
                        swap += -SWAP_LARGO_ANUAL / 365.0 * cierre * op["lote"]
                        noches += 1
                    dd_ += pd.Timedelta(days=1)
        ok_t = (str(sal_t) == str(ts_))
        L.append(f"  - Salida a mano: primer minuto con Bid mínimo <= stop vigente = {sal_t} a {sal_p:.2f} "
                 f"(motor {op['salida']} a {op['precio_salida_bid']}) -> "
                 f"{'OK' if ok_t and abs(sal_p - op['precio_salida_bid']) < 0.0051 else 'DIFERENTE'}")
        bruto = (sal_p - op["precio_entrada_ask"]) * op["lote"]
        L.append(f"  - Resultado a mano: bruto {bruto:,.2f} + swap {swap:,.2f} ({noches} noches) = {bruto + swap:,.2f} "
                 f"(motor: bruto {op['pnl_bruto_usd']:,.2f} + swap {op['swap_usd']:,.2f} ({op['noches']} noches) = {op['pnl_usd']:,.2f})")
    return L


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
    res, todas, eqs = {}, [], {}
    for etq, a, b in (("IS", 0, corte), ("OOS", corte, n)):
        ops, eq = simular(m, v, ind, a, b, etq)
        r = metricas(ops, eq)
        r["desde"], r["hasta"] = str(v["t"][a]), str(v["t"][b - 1])
        r["velas_m30"] = b - a
        res[etq] = r
        todas += ops
        eqs[etq] = (v["t"][a:b], eq)
        print(etq, json.dumps(r, indent=1, default=str), flush=True)
    os.makedirs(OUT, exist_ok=True)
    df = pd.DataFrame(todas)
    df.to_csv(os.path.join(OUT, NOM + "_operaciones.csv"), index=False)
    grafico_equity(os.path.join(OUT, NOM + "_equity.png"), *eqs["IS"], *eqs["OOS"], str(v["t"][corte]))
    res["meta"] = dict(velas_m1=len(ts), velas_m30=n, primera=str(ts[0]), ultima=str(ts[-1]),
                       corte=str(v["t"][corte]), spread_cero_o_faltante=int((m["sp"] <= 0).sum()),
                       spread_mediano=float(np.median(m["sp"])))
    json.dump(res, open(os.path.join(OUT, NOM + "_resultados.json"), "w"), indent=1, default=str)

    # ---- tramos y frecuencia (solo fuera de muestra cuenta para el veredicto) ----
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

    # ---- cordura a mano: primeras 3 operaciones fuera de muestra con salida por stop ----
    ids = list(oos.index[:3])
    ids_glob = [int(df.index[(df.segmento == "OOS")][k]) for k in ids]
    lineas = verificar_a_mano(m, df, ids_glob)
    json.dump(dict(res=res, anios_oos=anios, anios_is=anios_is, ops_mes=ops_mes, ops_por_anio=ops_por_anio),
              open(os.path.join(OUT, NOM + "_resultados.json"), "w"), indent=1, default=str)

    o = res["OOS"]
    ok = lambda c: "✓" if c else "✕"
    c1, c2, c3, c4 = o["pf"] >= 1.3, o["operaciones"] >= 30, o["dd_pct"] < 20, o["pf_sin_mejor"] > 1
    puntos = sum([c1, c2, c3, c4])
    L = []
    L.append("# Reporte fase 04 · US100 ruptura Donchian con eficiencia (M30, solo compras)\n")
    L.append("Código: `codigo/us100_ruptura_donchian_eficiencia.py` · Operaciones: `resultados/us100_ruptura_donchian_eficiencia_operaciones.csv` · "
             "Curva: `resultados/us100_ruptura_donchian_eficiencia_equity.png` · Cifras: `..._resultados.json`.\n")
    L.append("## Datos")
    L.append(f"datos/us100_1m_mt5.csv (M1, Bid) con el spread por minuto de datos/US100.csv (última columna, puntos de 0,1; "
             f"las dos tablas coinciden fila a fila) · US100 · {res['meta']['primera']} a {res['meta']['ultima']} (hora del servidor) · "
             f"{fmt(res['meta']['velas_m1'], 0)} velas M1 · {fmt(res['meta']['velas_m30'], 0)} velas M30.")
    L.append(f"Spread mediano {fmt(res['meta']['spread_mediano'], 0)} puntos; minutos con spread 0 o ausente: {res['meta']['spread_cero_o_faltante']}.")
    L.append("Calidad: el informe del M1 (resultados/us100_1m_mt5_calidad.md) dice NO APTA por umbral provisional (5,5 % de minutos M1 "
             "faltantes dentro del horario; límite 5 %); el de las velas M30 (resultados/us100_30m_mt5_calidad.md) dice APTA CON AVISOS "
             "(2,8 % de velas M30 faltantes, sin rellenar). La fase 02 y la 03 ya decidieron conservar el M1 para resolver el orden del stop. "
             "Se corre con ese aviso: los minutos sin ticks (sobre todo 2011 a 2014) se tratan como ausentes, sin rellenar.\n")
    L.append(f"Corte 70/30 por velas M30 (int(n x 0,7) = {fmt(corte, 0)}): dentro de muestra {res['IS']['desde']} a {res['IS']['hasta']} "
             f"({fmt(res['IS']['velas_m30'], 0)} velas); fuera de muestra {res['OOS']['desde']} a {res['OOS']['hasta']} ({fmt(res['OOS']['velas_m30'], 0)} velas).\n")
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
    L.append(f"Factor de beneficio {fmt(r_['pf'])} (sin swap {fmt(r_['pf_sin_swap'])}) · {r_['operaciones']} operaciones · caída {fmt(r_['dd_pct'])} % · sin la mejor {fmt(r_['pf_sin_mejor'])}.\n")
    L.append("## Otros datos fuera de muestra")
    L.append(f"Resultado neto {fmt(o['pnl_total'], 0)} USD sobre 100.000 (bruto {fmt(o['pnl_bruto_total'], 0)} y swap {fmt(o['swap_total'], 0)}) · "
             f"ganadoras {fmt(o['pct_ganadoras'], 1)} % · media por operación {fmt(o['pnl_medio'], 0)} USD · mejor {fmt(o['mejor'], 0)} · peor {fmt(o['peor'], 0)} · "
             f"caída solo con operaciones cerradas {fmt(o['dd_cerradas_pct'])} % (la oficial usa también la pérdida flotante al cierre de cada vela M30).")
    mot = oos["motivo"].value_counts().to_dict()
    L.append(f"Motivos de salida fuera de muestra: {mot}.\n")
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
    L.append(f"\n## (b) Frecuencia\nFuera de muestra: {o['operaciones']} operaciones en {fmt(anios_oos_anios, 2)} años = {fmt(ops_por_anio, 1)} por año = "
             f"{fmt(ops_mes, 1)} al mes (MI_PLAN.md: unas 6 al mes).")
    L.append(f"\n## (c) Caída frente al plan\nCaída máxima fuera de muestra {fmt(o['dd_pct'])} % frente al 6 % que el trader acepta en backtest: "
             f"{'SUPERA, no encaja con el plan' if o['dd_pct'] > 6 else 'dentro del plan'}. Peor operación {fmt(o['peor'], 0)} USD (el riesgo del plan es 2.000 USD en la cuenta de 200.000; aquí se prueba 1.000 USD sobre 100.000, mismo 1 %).")
    L.append("\n## (d) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)")
    L.append("Se rehace cada operación con otro camino de cálculo (velas M30 con `resample` de pandas, ATR y canal con `rolling`, y el stop barrido minuto a minuto), "
             "y se compara con lo que anotó el motor:\n")
    L += ["    " + t for t in lineas]
    L.append("\n## Costes y supuestos del backtest")
    L.append("- Spread real del CSV por minuto (Ask = Bid + spread × 0,1): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (la ficha). Aviso de la ficha (supuesto 30): el spread es de RoboForex medido de 2017-12 a 2026; antes es un perfil fabricado, y puede ser optimista (10 a 15 % más barato que OANDA hoy).")
    L.append("- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M30 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor (la noche del viernes cuenta una vez), sin día triple. Se suma al resultado de cada operación y entra en el factor de beneficio y en la caída. Se cobra en la curva de equity en el momento en que pasa la medianoche.")
    L.append("- Símbolo: punto 0,1; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 5 puntos; horario 01:01–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.")
    L.append("- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (motivo `fin_segmento`).")
    L.append("- Equity: capital + resultado de operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M30; la caída máxima sale de esa curva.")
    L.append("- Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1.")
    L.append("- Todo lo demás: los 30 supuestos del pseudocódigo de la ficha.")
    pf3, pfr = pf_de(p3["pnl_usd"].values), pf_de(resto["pnl_usd"].values)
    L.append("\n## Lectura honesta")
    L.append(f"- Falla el factor de beneficio ({fmt(o['pf'])} frente a 1,3), también sin swap ({fmt(o['pf_sin_swap'])}): el swap empeora el resultado pero no es la causa.")
    L.append(f"- Un tramo sostiene el resultado: primeros 3 años fuera de muestra FB {fmt(pf3)} con {len(p3)} operaciones; el resto, FB {fmt(pfr)} con {len(resto)}. Por año, el mejor ({max(anios, key=lambda a: a['pf'])['anio']}) pesa mucho más que los demás.")
    L.append(f"- Frecuencia {fmt(ops_mes, 1)} al mes frente a las ~6 del plan; la caída {fmt(o['dd_pct'])} % supera el 6 % del plan; la posición puede pasar el fin de semana (la hipótesis no cierra el viernes).")
    L.append("- Coherente con la fase 02: la ventaja sobre la línea base era pequeña y el filtro y el disparo no aportaban sobre un control sin ellos.")
    open(os.path.join(OUT, NOM + "_reporte.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(lineas))
    print(f"VEREDICTO {puntos}/4 · ops/año OOS {ops_por_anio:.1f}")


if __name__ == "__main__":
    main()
