import pandas as pd, numpy as np, sys, difflib
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
m = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/mandati.pkl')
fin = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/fin.pkl')

tot_x = tutte.groupby('manager_key').size()
maxman = m.groupby('manager_key').partite.max()
# per ogni mandato, la data_a del precedente e la data_da del successivo (stesso club)
m2 = m.sort_values(['club_id','data_da']).copy()
m2['prec_data_a'] = m2.groupby('club_id')['data_a'].shift()
m2['succ_data_da'] = m2.groupby('club_id')['data_da'].shift(-1)
m2['prec_partite'] = m2.groupby('club_id')['partite'].shift()
m2['succ_partite'] = m2.groupby('club_id')['partite'].shift(-1)
key = ['club_id','manager_key','data_da']
fin = fin.merge(m2[key+['prec_data_a','succ_data_da','prec_partite','succ_partite']], on=key, how='left')

fin['gap_prima']=(fin.data_da-fin.prec_data_a).dt.days
fin['gap_dopo']=(fin.succ_data_da-fin.data_a).dt.days
fin['x_partite_totali']=fin.manager_key.map(tot_x)
fin['x_mandato_max']=fin.manager_key.map(maxman)
def sim(a,b):
    if not isinstance(a,str) or not isinstance(b,str): return np.nan
    return difflib.SequenceMatcher(None,a,b).ratio()
fin['sim_prec']=[sim(a,b) for a,b in zip(fin.manager_key,fin.precedente)]

uno = fin[fin.partite==1].copy()
print("=== mandati di 1 partita nel perimetro:", len(uno))
bordo = uno.precedente.isna()|uno.successivo.isna()
sand = (~bordo)&(uno.precedente==uno.successivo)
ponte = (~bordo)&(uno.precedente!=uno.successivo)
uno['classe']=np.where(bordo,'BORDO',np.where(sand,'SANDWICH','PONTE'))
print(pd.crosstab(uno.classe, uno.ruolo, dropna=False))
print()
for c in ['SANDWICH','PONTE','BORDO']:
    s=uno[uno.classe==c]
    print(c, 'n=%d'%len(s),
          'gap_prima mediana=%s'%s.gap_prima.median(),
          'gap_dopo mediana=%s'%s.gap_dopo.median(),
          'X-mai-altrove=%d'%int((s.x_partite_totali==1).sum()),
          'X-mandato>=5 altrove=%d'%int((s.x_mandato_max>=5).sum()),
          'sim_nome>0.7 col prec=%d'%int((s.sim_prec>0.7).sum()))
uno.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno_perim.pkl')
fin.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/fin2.pkl')
print()
print(uno[uno.classe=='SANDWICH'][['club_name','allenatore','data_da','precedente','ruolo','gap_prima','gap_dopo','x_partite_totali','x_mandato_max']].head(25).to_string())
