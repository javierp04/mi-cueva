"""Fase 02 (AED) v2 · xauusd_ruptura_donchian_eficiencia · con la hipótesis completa del trader (2026-10-28)
Filtro = rising(stochastic(7,3).k) · TRIGGER = rising(efficiency(50)) · activación = el trigger pasa de falso a verdadero
con el filtro verdadero en esa misma vela (supuesto). Orden stop en donchian(55).upper (incluye la vela de señal), colocada en la
apertura siguiente, viva 10 velas desde la de colocación incluida; si abre en o sobre el nivel, se llena a la apertura.
Retornos en unidades de ATR(30) de la vela de señal. Solo el primer 70 % de las velas; el 30 % final queda reservado.
"""
import pandas as pd, numpy as np
d = pd.read_csv('datos/XAUUSD.csv', header=None, usecols=[0,1,2,3,4,5], dtype={0:str,1:str})
d.columns = ['f','h','o','hi','lo','c']
d.index = pd.to_datetime(d['f'] + ' ' + d['h'], format='%Y.%m.%d %H:%M')
m = d.resample('30min').agg({'o':'first','hi':'max','lo':'min','c':'last'}).dropna()
cut = int(len(m) * 0.70); m = m.iloc[:cut].copy()
print('velas M30 dentro de muestra:', len(m), m.index[0], '->', m.index[-1])

ll = m.lo.rolling(7).min(); hh = m.hi.rolling(7).max()
k = ((m.c - ll) / (hh - ll) * 100).rolling(3).mean()
eff = (m.c - m.c.shift(50)).abs() / m.c.diff().abs().rolling(50).sum()
filt = k > k.shift(); trig = eff > eff.shift()
act = trig & ~trig.shift(fill_value=False) & filt          # activación (supuesto)
act2 = (trig & filt) & ~(trig & filt).shift(fill_value=False)  # variante: sube la combinación
don = m.hi.rolling(55).max()
tr = pd.concat([m.hi-m.lo, (m.hi-m.c.shift()).abs(), (m.lo-m.c.shift()).abs()], axis=1).max(axis=1)
atr = tr.rolling(30).mean()
o_ = m.o.values; hi = m.hi.values; c = m.c.values; a = atr.values; dv = don.values; yr = m.index.year.values
N = len(m)

def evento(i):
    """Orden armada en la vela i: devuelve (año, [retornos +1,+5,+20 en ATR]) o None si no se llena."""
    if np.isnan(dv[i]) or np.isnan(a[i]) or i + 31 >= N: return None
    lvl = dv[i]
    for j in range(i+1, i+11):                  # velas i+1 .. i+10
        if o_[j] >= lvl: e = o_[j]
        elif hi[j] >= lvl: e = lvl
        else: continue
        return yr[j], [(c[j+h]-e)/a[i] for h in (1,5,20)]
    return None

def correr(mask, nombre):
    idx = np.flatnonzero(mask.values); ev = [x for x in map(evento, idx) if x]
    E = np.array([x[1] for x in ev]); Y = np.array([x[0] for x in ev])
    print(f'\n{nombre}: {len(idx)} órdenes armadas, {len(ev)} llenadas ({len(ev)/max(1,len(idx))*100:.0f} %)')
    for q, h in enumerate((1,5,20)):
        print(f'  +{h:2d} velas desde el fill: media={E[:,q].mean():+.3f} ATR  mediana={np.median(E[:,q]):+.3f}  %>0={(E[:,q]>0).mean()*100:.1f}')
    return E, Y

E, Y = correr(act, 'REGLA (filtro + trigger)')
E2, _ = correr(act2, 'VARIANTE (sube la combinación filtro y trigger)')
Ef, _ = correr(filt & filt.notna(), 'CONTROL 1: solo filtro (cada vela con estocástico subiendo)')
Et, _ = correr(trig & ~trig.shift(fill_value=False), 'CONTROL 2: solo trigger (eficiencia empieza a subir)')
Ea, Ya = correr(pd.Series(True, index=m.index), 'CONTROL 3: orden armada en CADA vela')

print('\nLínea base, cualquier vela (cierre a cierre, en ATR):')
for h in (1,5,20):
    r = ((m.c.shift(-h) - m.c) / atr).dropna(); print(f'  +{h:2d}: media={r.mean():+.3f}  %>0={(r>0).mean()*100:.1f}')

df = pd.DataFrame({'y': Y, 'r': E[:,2]}).groupby('y')['r'].agg(['count','mean'])
dfa = pd.DataFrame({'y': Ya, 'r': Ea[:,2]}).groupby('y')['r'].mean()
df['control3'] = dfa
print('\nPor año, +20 velas desde el fill: regla vs control 3 (orden en cada vela)')
print(df.round(3).to_string())
print('años con regla > control 3:', int((df['mean'] > df['control3']).sum()), 'de', len(df))
