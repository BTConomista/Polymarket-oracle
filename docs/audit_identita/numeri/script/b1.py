import pandas as pd, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
m = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/mandati.pkl')
print("mandati totali", len(m))
uno = m[m.partite==1]
print("mandati di 1 sola partita", len(uno))
prev = uno.precedente; nxt = uno.successivo
bordo = prev.isna() | nxt.isna()
sand = (~bordo) & (prev==nxt)
ponte = (~bordo) & (prev!=nxt)
print("  BORDO (manca prec o succ):", int(bordo.sum()))
print("  SANDWICH A-X-A:", int(sand.sum()))
print("  PONTE A-X-B:", int(ponte.sum()))
# controllo: sand deve coincidere con interruzione&partite==1
print("  check sand==interruzione:", int((uno.interruzione & (~bordo)).sum()), int(sand.sum()), (uno.interruzione==sand).all())
# quante partite ha X in tutto il dataset e mandato massimo
tot_x = tutte.groupby('manager_key').size()
maxman = m.groupby('manager_key').partite.max()
nman = m.groupby('manager_key').size()
uno = uno.copy()
uno['x_partite_totali']=uno.manager_key.map(tot_x)
uno['x_mandato_max']=uno.manager_key.map(maxman)
uno['x_mandati']=uno.manager_key.map(nman)
for nome,mask in [('SANDWICH',sand),('PONTE',ponte),('BORDO',bordo)]:
    s=uno[mask]
    print(f"{nome}: n={len(s)}  X mai altrove (1 sola partita in tutto il dataset)={int((s.x_partite_totali==1).sum())}  X con un mandato >=5 partite altrove={int((s.x_mandato_max>=5).sum())}")
uno.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno.pkl')
