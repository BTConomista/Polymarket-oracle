import pandas as pd, numpy as np, sys, difflib
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
fin  = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/fin2.pkl')
uno  = fin[fin.partite==1].copy()

# indice partite per club
per_club = {c: g.sort_values('date') for c,g in tutte.groupby('club_id')}
FIN = 45
righe=[]
for _,r in uno.iterrows():
    g = per_club[r.club_id]; d=r.data_da
    w = g[(g.date>=d-pd.Timedelta(days=FIN))&(g.date<=d+pd.Timedelta(days=FIN))]
    altre = w[w.date!=d]
    pre = altre[altre.date<d]; post = altre[altre.date>d]
    dom_pre = pre.manager_key.mode().iat[0] if len(pre) else None
    dom_post= post.manager_key.mode().iat[0] if len(post) else None
    q_pre = (pre.manager_key==dom_pre).mean() if len(pre) else np.nan
    q_post= (post.manager_key==dom_post).mean() if len(post) else np.nan
    # X ricompare in quel club dopo la data?
    x_dopo = int(((g.manager_key==r.manager_key)&(g.date>d)).sum())
    x_prima= int(((g.manager_key==r.manager_key)&(g.date<d)).sum())
    x_club_tot = int((g.manager_key==r.manager_key).sum())
    # avversario quel giorno
    riga = g[(g.date==d)]
    avv = riga.manager_key_avv.iat[0] if len(riga) else None
    righe.append(dict(idx=_, dom_pre=dom_pre, dom_post=dom_post, q_pre=q_pre, q_post=q_post,
                      n_pre=len(pre), n_post=len(post), x_dopo=x_dopo, x_prima=x_prima,
                      x_club_tot=x_club_tot, avv_key=avv))
f = pd.DataFrame(righe).set_index('idx')
uno = uno.join(f)
uno['uguale_avversario'] = uno.manager_key==uno.avv_key
def sim(a,b):
    if not isinstance(a,str) or not isinstance(b,str): return 0.0
    return difflib.SequenceMatcher(None,a,b).ratio()
uno['sim_dom_pre']=[sim(a,b) for a,b in zip(uno.manager_key,uno.dom_pre)]

def classifica(r):
    if r.uguale_avversario or r.sim_dom_pre>0.75:
        return 'SOSPETTO_FONTE'
    if r.n_pre==0 or r.n_post==0:
        return 'BORDO'
    if r.dom_pre==r.dom_post and r.q_pre>=0.6 and r.q_post>=0.6:
        return 'VICE_DI_TURNO'
    if r.dom_pre!=r.dom_post:
        return 'TRAGHETTATORE'
    return 'AMBIGUO'
uno['classe2']=uno.apply(classifica,axis=1)
print(pd.crosstab(uno.classe2, uno.ruolo, dropna=False))
print()
print(pd.crosstab(uno.classe2, uno.classe))
uno.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno2.pkl')
# gli errori
print("\n--- VICE_DI_TURNO ma ruolo=titolare ---")
print(uno[(uno.classe2=='VICE_DI_TURNO')&(uno.ruolo=='titolare')][['club_name','allenatore','data_da','dom_pre','x_club_tot','x_partite_totali']].to_string())
print("\n--- ruolo=vice ma non VICE_DI_TURNO ---")
print(uno[(uno.ruolo=='vice')&(uno.classe2!='VICE_DI_TURNO')][['club_name','allenatore','data_da','classe2','dom_pre','dom_post','n_pre','n_post']].to_string())
