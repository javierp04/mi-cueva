"""Fase 02 (AED) · xauusd_ruptura_donchian_eficiencia
Sin pre-registro: mide retornos a 1, 5 y 20 velas tras la condición frente a cualquier vela.
Solo usa el primer 70 % de las velas (dentro de muestra); el 30 % final queda reservado para la fase 04.
"""
import pandas as pd, numpy as np

CSV = 'datos/XAUUSD.csv'
d = pd.read_csv(CSV, header=None, names=['f','h','o','h_','l','c','tv','v','sp'],
                usecols=[0,1,2,3,4,5], dtype={0:str,1:str})
d.columns = ['f','h','o','hi','lo','c']
d.index = pd.to_datetime(d['f'] + ' ' + d['h'], format='%Y.%m.%d %H:%M')
n1 = len(d); print('velas M1:', n1, d.index[0], '->', d.index[-1])
m = d.resample('30min').agg({'o':'first','hi':'max','lo':'min','c':'last'}).dropna()
print('velas M30:', len(m))
gap = m.index.to_series().diff()
print('huecos > 1 dia:', int((gap > pd.Timedelta('1D')).sum()), '| mayor hueco:', gap.max())
cut = int(len(m) * 0.70)
print('corte 70 %:', m.index[cut-1], '(se reservan', len(m)-cut, 'velas)')
m = m.iloc[:cut].copy()

# indicadores (supuestos de la ficha)
ll = m.lo.rolling(7).min(); hh = m.hi.rolling(7).max()
k = ((m.c - ll) / (hh - ll) * 100).rolling(3).mean()
eff = (m.c - m.c.shift(50)).abs() / m.c.diff().abs().rolling(50).sum()
trig = (k > k.shift()) & (eff > eff.shift())
act = trig & ~trig.shift(fill_value=False)
don = m.hi.rolling(55).max()
tr = pd.concat([m.hi-m.lo, (m.hi-m.c.shift()).abs(), (m.lo-m.c.shift()).abs()], axis=1).max(axis=1)
atr = tr.rolling(30).mean()

def fwd(h, base):  # retorno desde 'base' hasta h velas despues, en unidades de ATR
    return (m.c.shift(-h) - base) / atr

res = []
for h in (1, 5, 20):
    r = fwd(h, m.c)
    cond = r[act].dropna(); allv = r.dropna()
    res.append((f'tras activación, +{h}', len(cond), cond.mean(), (cond>0).mean(), allv.mean(), (allv>0).mean()))
print('\nA) Retorno en ATR(30) tras la activación (cierre de la vela) vs cualquier vela')
for r in res: print('%-26s n=%5d  media=%+.3f  %%>0=%.1f  | cualquier vela media=%+.3f  %%>0=%.1f' % (r[0], r[1], r[2], r[3]*100, r[4], r[5]*100))

# B) ruptura: tras activación, primera vela dentro de 10 que toca el nivel congelado (don de la vela de señal)
idx = np.flatnonzero(act.values)
ev = []
hi = m.hi.values; c = m.c.values; a = atr.values; dv = don.values
for i in idx:
    if np.isnan(dv[i]) or np.isnan(a[i]): continue
    lvl = dv[i]
    for j in range(i+1, min(i+11, len(m)-21)):
        if hi[j] >= lvl:
            e = max(lvl, m.o.values[j])  # gap: entra a la apertura
            ev.append((m.index[j], [(c[j+h]-e)/a[i] for h in (1,5,20)]))
            break
print('\nB) Activaciones:', len(idx), '| con ruptura del nivel dentro de 10 velas:', len(ev), '(%.0f %%)' % (len(ev)/max(1,len(idx))*100))
E = np.array([x[1] for x in ev]); yrs = pd.Series([x[0].year for x in ev])
for q, h in enumerate((1,5,20)):
    print(f'  entrada en el nivel, +{h} velas: media={E[:,q].mean():+.3f} ATR  %>0={(E[:,q]>0).mean()*100:.1f}')
# linea base: entrar en cualquier vela (cierre) con el mismo ATR
for h in (1,5,20):
    r = fwd(h, m.c).dropna(); print(f'  cualquier vela, +{h}: media={r.mean():+.3f} ATR  %>0={(r>0).mean()*100:.1f}')
# C) por año a +20 velas
df = pd.DataFrame({'y': yrs.values, 'r20': E[:,2]})
g = df.groupby('y')['r20'].agg(['count','mean'])
base = fwd(20, m.c).dropna(); bg = base.groupby(base.index.year).mean()
g['base'] = bg
print('\nC) Por año, retorno +20 velas tras ruptura (ATR) vs cualquier vela')
print(g.round(3).to_string())
print('años con media > base:', int((g['mean'] > g['base']).sum()), 'de', len(g))

# D) Control: ruptura del canal de 55 SIN el disparo (¿aporta algo el estocástico + eficiencia?)
prev = don.shift(1).values; o_ = m.o.values
brk = np.flatnonzero((hi >= prev) & ~np.isnan(prev) & ~np.isnan(a))
brk = brk[brk < len(m)-21]
# solo la primera vela de cada ruptura (la anterior no rompía)
first = [j for j in brk if not (hi[j-1] >= prev[j-1] if not np.isnan(prev[j-1]) else False)]
Ec = np.array([[(c[j+h]-max(prev[j], o_[j]))/a[j-1] for h in (1,5,20)] for j in first])
print('\nD) CONTROL: toda ruptura del canal de 55 sin disparo:', len(first), 'casos')
for q, h in enumerate((1,5,20)):
    print(f'  +{h} velas: media={Ec[:,q].mean():+.3f} ATR  %>0={(Ec[:,q]>0).mean()*100:.1f}   (con disparo: {E[:,q].mean():+.3f})')
