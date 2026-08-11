import pandas as pd, numpy as np, sys, difflib
sys.path.insert(0,'/home/user/Polymarket-oracle')
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
m=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/mandati.pkl')
uno=m[m.partite==1].copy(); K=5; G=45; V=21
per={c:g.sort_values(['date','game_id']).reset_index(drop=True) for c,g in tutte.groupby('club_id')}
res=[]
for i,r in uno.iterrows():
    g=per[r.club_id]; p=int(g.index[(g.date==r.data_da)&(g.manager_key==r.manager_key)][0])
    pre=g.iloc[max(0,p-K):p]; post=g.iloc[p+1:p+1+K]
    dpre=pre.manager_key.mode().iat[0] if len(pre) else None
    dpost=post.manager_key.mode().iat[0] if len(post) else None
    qpre=(pre.manager_key==dpre).mean() if len(pre) else 0
    qpost=(post.manager_key==dpost).mean() if len(post) else 0
    gp=(r.data_da-pre.date.iat[-1]).days if len(pre) else 9999
    gd=(post.date.iat[0]-r.data_da).days if len(post) else 9999
    sim=difflib.SequenceMatcher(None,r.manager_key,dpre).ratio() if isinstance(dpre,str) else 0
    if dpre==r.manager_key or dpost==r.manager_key: c='TITOLARE_SPEZZATO'
    elif 0.75<sim<1.0 or r.manager_key==g.manager_key_avv.iat[p]: c='SOSPETTO_FONTE'
    elif gp>G and gd>G: c='ISOLATA_FUORI_COPERTURA'
    elif dpre==dpost and qpre>=0.6 and qpost>=0.6 and gp<=V and gd<=V: c='STAND_IN'
    elif dpre!=dpost and min(gp,gd)<=V: c='TRAGHETTATORE'
    else: c='AMBIGUO'
    res.append(c)
uno['classe']=res
print("=== 3.609 mandati di UNA sola partita, TUTTO il dataset ===")
print(uno.classe.value_counts().to_string())
print("\n incrocio con la colonna `interruzione` del modulo:")
print(pd.crosstab(uno.classe,uno.interruzione))
print("\n=== e sui soli 412 'interruzione & 1 partita' ===")
print(uno[uno.interruzione].classe.value_counts().to_string())
