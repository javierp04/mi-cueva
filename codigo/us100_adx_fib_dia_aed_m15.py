"""Fase 02 (AED) · us100_adx_fib_dia
Trigger = rising(adx(75),5); orden stop en fib_day(1.382) = prev_day_low + 1.382*(prev_day_high - prev_day_low), congelada al armar, viva 4 velas.
Mide el retorno (en ATR(30) de la vela de señal) a 1, 5 y 20 velas desde el fill, contra «cualquier vela» y contra una orden armada en cada vela sin ADX.
Velas M15 (corrección del trader 2026-10-28: la temporalidad es M15). Solo el primer 70 % de las velas; el 30 % final queda reservado.
Uso: python codigo/us100_adx_fib_dia_aed.py
"""
import pandas as pd, numpy as np
d = pd.read_csv('datos/US100.csv', header=None, usecols=[0,1,2,3,4,5], dtype={0:str,1:str})
d.columns = ['f','h','o','hi','lo','c']
d.index = pd.to_datetime(d['f'] + ' ' + d['h'], format='%Y.%m.%d %H:%M')
m = d.resample('15min').agg({'o':'first','hi':'max','lo':'min','c':'last'}).dropna()
cut = int(len(m) * 0.70)
# día anterior (día del servidor) con todas las velas, antes del corte para no mirar el 30 % reservado
dia = m.index.normalize()
dh = m.hi.groupby(dia).max(); dl = m.lo.groupby(dia).min()
dias = dh.index
prev_h = pd.Series(dh.shift(1).values, index=dias); prev_l = pd.Series(dl.shift(1).values, index=dias)
nivel = prev_l.reindex(dia).values + 1.382 * (prev_h.reindex(dia).values - prev_l.reindex(dia).values)
m = m.iloc[:cut].copy(); nivel = nivel[:cut]
print('velas M15 dentro de muestra:', len(m), m.index[0], '->', m.index[-1])

# ADX de Wilder (75) sobre Bid
h, l, c = m.hi, m.lo, m.c
up, dn = h.diff(), -l.diff()
pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
a = 1/75
atr_w = tr.ewm(alpha=a, adjust=False, min_periods=75).mean()
pdi = 100 * pd.Series(pdm, index=m.index).ewm(alpha=a, adjust=False, min_periods=75).mean() / atr_w
mdi = 100 * pd.Series(mdm, index=m.index).ewm(alpha=a, adjust=False, min_periods=75).mean() / atr_w
dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
adx = dx.ewm(alpha=a, adjust=False, min_periods=75).mean()
sube = adx > adx.shift(5)                    # rising(adx(75),5): mayor que hace 5 velas
act = sube & ~sube.shift(fill_value=False)
atr = tr.rolling(30).mean()                   # ATR(30) = SMA del rango verdadero
valido = adx.notna() & adx.shift(5).notna()
act &= valido

o_, hi, c_, a_, yr = m.o.values, m.hi.values, m.c.values, atr.values, m.index.year.values
N = len(m)
def evento(i, VIDA=4):
    L = nivel[i]
    if np.isnan(L) or np.isnan(a_[i]) or i + VIDA + 21 >= N: return None
    if 0 < L - o_[i+1] < 5 * 0.1: return None   # stops level: nivel a menos de 5 puntos de la cotización, la orden se rechaza y no se reintenta
    for j in range(i+1, i+1+VIDA):             # velas i+1 .. i+4
        if o_[j] >= L: e, caso = o_[j], 'B'    # el precio ya estaba en el nivel o más allá: entrada a la apertura
        elif hi[j] >= L: e, caso = L, 'A'      # el precio sube hasta el nivel: ruptura, fill al nivel
        else: continue
        return yr[j], [(c_[j+k]-e)/a_[i] for k in (1,5,20)], caso
    return None
def correr(mask, nombre):
    idx = np.flatnonzero(np.asarray(mask)); ev = [x for x in map(evento, idx) if x]
    print(f'\n{nombre}: {len(idx)} órdenes armadas, {len(ev)} llenadas ({len(ev)/max(1,len(idx))*100:.1f} %)')
    if not ev: return None, None
    E = np.array([x[1] for x in ev]); Y = np.array([x[0] for x in ev]); C = np.array([x[2] for x in ev])
    for q, k in enumerate((1,5,20)):
        print(f'  +{k:2d} velas desde el fill: media={E[:,q].mean():+.3f} ATR  mediana={np.median(E[:,q]):+.3f}  %>0={(E[:,q]>0).mean()*100:.1f}')
    for caso, txt in (('A', 'sube hasta el nivel (ruptura, fill al nivel)'), ('B', 'ya estaba en el nivel o más allá (entrada a la apertura)')):
        z = C == caso
        if z.sum(): print(f'    caso {caso} · {txt}: {z.sum()} casos · +20 media={E[z,2].mean():+.3f} mediana={np.median(E[z,2]):+.3f} %>0={(E[z,2]>0).mean()*100:.1f}')
    return E, Y
E, Y = correr(act, 'REGLA (ADX(75) empieza a subir)')
Ec, Yc = correr(pd.Series(True, index=m.index), 'CONTROL: orden armada en CADA vela (mismo nivel, sin ADX)')
Es, Ys = correr(sube, 'CONTROL 2: toda vela con ADX subiendo (no solo el inicio)')
print('\nLínea base, cualquier vela (cierre a cierre, en ATR):')
for k in (1,5,20):
    r = ((m.c.shift(-k) - m.c) / atr).dropna(); print(f'  +{k:2d}: media={r.mean():+.3f}  mediana={r.median():+.3f}  %>0={(r>0).mean()*100:.1f}')
if E is not None:
    df = pd.DataFrame({'y': Y, 'r': E[:,2]}).groupby('y')['r'].agg(['count','mean'])
    df['control'] = pd.DataFrame({'y': Yc, 'r': Ec[:,2]}).groupby('y')['r'].mean()
    r20 = ((m.c.shift(-20) - m.c) / atr).dropna(); df['base'] = r20.groupby(r20.index.year).mean()
    print('\nPor año, +20 velas desde el fill: regla, control (orden en cada vela) y línea base')
    print(df.round(3).to_string())
    sub = df[df['count'] >= 30]
    print('años con ≥ 30 casos:', len(sub), '· regla > línea base en', int((sub['mean'] > sub['base']).sum()), '· regla > control en', int((sub['mean'] > sub['control']).sum()))
