import pandas as pd, numpy as np, sys, difflib
sys.path.insert(0,'/home/user/Polymarket-oracle')
tutte = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
fin  = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/fin2.pkl')
uno  = fin[fin.partite==1].copy()
K=5
per_club = {c: g.sort_values(['date','game_id']).reset_index(drop=True) for c,g in tutte.groupby('club_id')}
def sim(a,b):
    if not isinstance(a,str) or not isinstance(b,str): return 0.0
    return difflib.SequenceMatcher(None,a,b).ratio()
righe=[]
for i,r in uno.iterrows():
    g=per_club[r.club_id]; pos=g.index[(g.date==r.data_da)&(g.manager_key==r.manager_key)]
    p=int(pos[0])
    pre=g.iloc[max(0,p-K):p]; post=g.iloc[p+1:p+1+K]
    dom_pre = pre.manager_key.mode().iat[0] if len(pre) else None
    dom_post= post.manager_key.mode().iat[0] if len(post) else None
    q_pre=(pre.manager_key==dom_pre).mean() if len(pre) else np.nan
    q_post=(post.manager_key==dom_post).mean() if len(post) else np.nan
    gap_pre=(r.data_da-pre.date.iat[-1]).days if len(pre) else np.nan
    gap_post=(post.date.iat[0]-r.data_da).days if len(post) else np.nan
    righe.append(dict(idx=i,dom_pre=dom_pre,dom_post=dom_post,q_pre=q_pre,q_post=q_post,
        n_pre=len(pre),n_post=len(post),gap_pre=gap_pre,gap_post=gap_post,
        avv_key=g.manager_key_avv.iat[p],
        x_club_tot=int((g.manager_key==r.manager_key).sum()),
        comp=g.competition_id.iat[p],
        comp_pre_diversa=int(g.competition_id.iat[p] not in set(pre.competition_id)) if len(pre) else np.nan))
f=pd.DataFrame(righe).set_index('idx'); uno=uno.join(f)
uno['uguale_avversario']=uno.manager_key==uno.avv_key
uno['sim_dom_pre']=[sim(a,b) for a,b in zip(uno.manager_key,uno.dom_pre)]
def classifica(r):
    if r.uguale_avversario or r.sim_dom_pre>0.75: return 'SOSPETTO_FONTE'
    if r.n_pre==0 or r.n_post==0: return 'BORDO'
    if r.dom_pre==r.dom_post and r.q_pre>=0.6 and r.q_post>=0.6: return 'VICE_DI_TURNO'
    if r.dom_pre!=r.dom_post: return 'TRAGHETTATORE'
    return 'AMBIGUO'
uno['classe2']=uno.apply(classifica,axis=1)
ct=pd.crosstab(uno.classe2,uno.ruolo,dropna=False); print(ct); print()
print("gap mediano per classe:"); print(uno.groupby('classe2')[['gap_pre','gap_post']].median())
print("\n--- VICE_DI_TURNO ma ruolo=titolare ---")
print(uno[(uno.classe2=='VICE_DI_TURNO')&(uno.ruolo=='titolare')][['club_name','allenatore','data_da','dom_pre','x_club_tot','gap_pre','gap_post']].to_string())
print("\n--- ruolo=vice ma classe2 diversa ---")
print(uno[(uno.ruolo=='vice')&(uno.classe2!='VICE_DI_TURNO')][['club_name','allenatore','data_da','classe2','dom_pre','dom_post','q_pre','q_post','gap_pre','gap_post']].to_string())
print("\n--- SOSPETTO_FONTE ---")
print(uno[uno.classe2=='SOSPETTO_FONTE'][['club_name','allenatore','data_da','dom_pre','sim_dom_pre','uguale_avversario','ruolo']].to_string())
uno.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno3.pkl')
