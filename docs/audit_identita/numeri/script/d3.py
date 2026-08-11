import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
p=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p2.pkl')
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
h=tutte[tutte.casa]
print("non agganciate per turno:"); print(p[p.gid2.isna()].Turno.value_counts().head(12))
print("\nagganciate per competizione:"); print(pd.crosstab(p.Competizione,p.gid2.notna()))
# la tabella alias RICAVATA dal ponte
v=p.dropna(subset=['gid2']).merge(h[['game_id','club_id','club_name','avversario_id','avversario_name']],left_on='gid2',right_on='game_id')
a=pd.concat([v[['Casa','club_id','club_name']].rename(columns={'Casa':'sofa','club_id':'id','club_name':'nostro'}),
             v[['Trasferta','avversario_id','avversario_name']].rename(columns={'Trasferta':'sofa','avversario_id':'id','avversario_name':'nostro'})])
g=a.groupby('sofa').agg(n=('id','size'),n_id=('id','nunique'),id=('id','first'),nostro=('nostro','first'))
print("\n=== tabella alias squadre RICAVATA dal ponte allenatori ===")
print("nomi SofaScore agganciati:",len(g)," di cui AMBIGUI (>1 club_id):",int((g.n_id>1).sum()))
print("club_id distinti:",g.id.nunique())
amb=g[g.n_id>1]
if len(amb): print(amb.to_string())
# copertura delle 96 squadre delle nostre 5 leghe 2025-26
nostre=set(tutte[(tutte.season==2025)&tutte.is_top5].club_id)
print("nostre squadre 2025-26:",len(nostre),"| coperte dall'alias ricavato:",len(nostre&set(g.id)))
# quante combaciavano per nome esatto (il 13/96 del README)
esatto=set(g[g.index==g.nostro].id)
print("di quelle, nomi identici fra SofaScore e noi:",len(esatto&nostre))
print("\nesempi di alias ricavati (non identici):")
print(g[(g.index!=g.nostro)&(g.id.isin(nostre))].head(12).to_string())
