"""Fase 02 (AED) · us30_macd_hma_asia
Trigger = cross_below(macd(10,50).main, macd(10,50,9).signal) con in_session(asia) (09:00-15:00 Asia/Tokyo, fin excluido).
Orden LIMIT de compra en hma(30) + 1 x ATR(14) al cierre de la vela de señal, colocada en la apertura siguiente, viva 15 velas
(la de colocación incluida); la activación inversa (cross_above del MACD) la cancela. Si el nivel ya está en el precio o por encima
(orden no válida como pendiente) se compra a mercado en la apertura siguiente (caso M); si espera y el precio baja al nivel, se llena (caso L).
Mide el retorno (en ATR(30) de la vela de señal) a 1, 5 y 20 velas desde el fill, contra «cualquier vela» y dos controles.
Velas M30 de datos/us30_30m_mt5.csv (hora del servidor = Nueva York + 7 h). Solo el primer 70 % de las velas; el 30 % final queda reservado.
Uso: python codigo/us30_macd_hma_asia_aed.py
"""
import numpy as np, pandas as pd

d = pd.read_csv('datos/us30_30m_mt5.csv', parse_dates=['fecha'])
d['fecha'] = d['fecha'].dt.tz_localize(None)            # la etiqueta «UTC» del CSV curado es en realidad la hora del servidor
corte = int(len(d) * 0.70)
d = d.iloc[:corte].reset_index(drop=True)
print('velas M30 dentro de muestra:', len(d), d.fecha.iloc[0], '->', d.fecha.iloc[-1])
o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
N = len(d)

def ema_sma(x, n):                                      # semilla SMA de los primeros n valores válidos, alpha 2/(n+1)
    out = np.full(len(x), np.nan); ok = np.flatnonzero(~np.isnan(x))
    if len(ok) < n: return out
    k = ok[0] + n - 1; out[k] = np.mean(x[ok[0]:k + 1]); a = 2 / (n + 1)
    for t in range(k + 1, len(x)): out[t] = out[t-1] + a * (x[t] - out[t-1])
    return out
def lwma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return pd.Series(x).rolling(n).apply(lambda v: np.dot(v, w) / w.sum(), raw=True).values
def hma(x, n): return lwma(2 * lwma(x, n // 2) - lwma(x, n), int(np.sqrt(n)))
def atr(n):
    pc = np.r_[np.nan, c[:-1]]; tr = np.maximum.reduce([h - l, np.abs(h - pc), np.abs(l - pc)]); tr[0] = h[0] - l[0]
    return pd.Series(tr).rolling(n).mean().values

main = ema_sma(c, 10) - ema_sma(c, 50); sig = ema_sma(main, 9)
below = main < sig; cb = np.r_[False, below[1:] & ~below[:-1]] & ~np.isnan(sig)
cb &= ~np.r_[True, np.isnan(sig[:-1])]                 # hace falta la vela anterior con señal válida
above = main > sig; ca = np.r_[False, above[1:] & ~above[:-1]] & ~np.isnan(sig)
H, A14, A30 = hma(c, 30), atr(14), atr(30)
nivel = H + 1.0 * A14
# in_session(asia): hora de apertura de la vela (servidor = Nueva York + 7 h) leída en Asia/Tokyo
ny = d.fecha - pd.Timedelta(hours=7)
utc = ny.dt.tz_localize('America/New_York', ambiguous='NaT', nonexistent='shift_forward').dt.tz_convert('UTC')
tok = utc.dt.tz_convert('Asia/Tokyo'); asia = ((tok.dt.hour >= 9) & (tok.dt.hour < 15)).values
yr = d.fecha.dt.year.values
STOPS = 150 * 0.01                                      # 150 puntos; punto 0,01 (supuesto: precios con 2 decimales)

def evento(i, VIDA=15):
    L = nivel[i]
    if np.isnan(L) or np.isnan(A30[i]) or i + VIDA + 21 >= N: return None
    if L >= o[i+1]:                                     # nivel en el precio o por encima: no hay pendiente válida, compra a mercado
        e, j, caso = o[i+1], i+1, 'M'
        return yr[j], [(c[j+k] - e) / A30[i] for k in (1, 5, 20)], caso
    if o[i+1] - L < STOPS: return None                  # stops level: pendiente a menos de 150 puntos, se rechaza
    for j in range(i+1, i+1+VIDA):
        if j > i+1 and ca[j-1]: return None             # activación inversa: cancela la orden
        if l[j] <= L:
            e = min(L, o[j])
            return yr[j], [(c[j+k] - e) / A30[i] for k in (1, 5, 20)], 'L'
    return None

def correr(mask, nombre):
    idx = np.flatnonzero(np.asarray(mask)); ev = [x for x in map(evento, idx) if x]
    print(f'\n{nombre}: {len(idx)} órdenes armadas, {len(ev)} llenadas ({len(ev)/max(1,len(idx))*100:.1f} %)')
    if not ev: return None, None
    E = np.array([x[1] for x in ev]); Y = np.array([x[0] for x in ev]); C = np.array([x[2] for x in ev])
    for q, k in enumerate((1, 5, 20)):
        print(f'  +{k:2d} velas desde el fill: media={E[:,q].mean():+.3f} ATR  mediana={np.median(E[:,q]):+.3f}  %>0={(E[:,q]>0).mean()*100:.1f}')
    for caso, txt in (('M', 'nivel en el precio o por encima: compra a mercado'), ('L', 'espera y el precio baja al nivel')):
        z = C == caso
        if z.sum(): print(f'    caso {caso} · {txt}: {z.sum()} casos · +20 media={E[z,2].mean():+.3f} mediana={np.median(E[z,2]):+.3f} %>0={(E[z,2]>0).mean()*100:.1f}')
    return E, Y

reg = cb & asia
E, Y = correr(reg, 'REGLA (cruce a la baja del MACD en sesión asiática)')
Ec1, Yc1 = correr(asia & ~np.isnan(nivel), 'CONTROL 1: orden armada en CADA vela de sesión asiática (mismo nivel, sin MACD)')
Ec2, Yc2 = correr(cb, 'CONTROL 2: cruce a la baja del MACD en CUALQUIER hora (sin filtro de sesión)')
print('\nLínea base, cualquier vela (cierre a cierre, en ATR(30)):')
s = pd.Series(c); a30 = pd.Series(A30)
for k in (1, 5, 20):
    r = ((s.shift(-k) - s) / a30).dropna(); print(f'  +{k:2d}: media={r.mean():+.3f}  mediana={r.median():+.3f}  %>0={(r>0).mean()*100:.1f}')
ra = ((s.shift(-20) - s) / a30); ra = ra[asia].dropna(); print(f'  +20 solo velas de sesión asiática: media={ra.mean():+.3f}  mediana={ra.median():+.3f}  %>0={(ra>0).mean()*100:.1f}')
if E is not None:
    df = pd.DataFrame({'y': Y, 'r': E[:,2]}).groupby('y')['r'].agg(['count', 'mean'])
    df['control1'] = pd.DataFrame({'y': Yc1, 'r': Ec1[:,2]}).groupby('y')['r'].mean()
    r20 = ((s.shift(-20) - s) / a30); df['base'] = r20.groupby(yr).mean()
    print('\nPor año, +20 velas desde el fill: regla, control 1 y línea base')
    print(df.round(3).to_string())
    sub = df[df['count'] >= 30]
    print('años con ≥ 30 casos:', len(sub), '· regla > línea base en', int((sub['mean'] > sub['base']).sum()), '· regla > control 1 en', int((sub['mean'] > sub['control1']).sum()))
print('\nFrecuencia: activaciones en el tramo', int(reg.sum()), '=', round(reg.sum() / (N / 48 / 252), 1), 'por año (aprox.)')
