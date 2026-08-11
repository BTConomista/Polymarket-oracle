import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
p=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p.pkl')
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
# --- prova finale R8 ---
r=p.dropna(subset=['Arbitro'])
d=r.groupby('Arbitro').agg(n=('Arbitro','size'),vmin=('Partite arbitro','min'),vmax=('Partite arbitro','max'))
d=d[d.n>1]; d['delta']=d.vmax-d.vmin; d['atteso_se_as_of']=d.n-1
print("=== prova R8 arbitro: crescita OSSERVATA vs crescita MINIMA se il dato fosse 'al momento della partita' ===")
print("arbitri con >1 partita:",len(d))
print("delta osservato: max=%d  mediana=%.0f  somma=%d"%(d.delta.max(),d.delta.median(),d.delta.sum()))
print("delta atteso se as-of-match: somma=%d  (ogni sua partita del file ne aggiunge >=1)"%d.atteso_se_as_of.sum())
print("arbitri con delta >= atteso:",int((d.delta>=d.atteso_se_as_of).sum()),"su",len(d))
print("il piu' esposto:",d.sort_values('n',ascending=False).head(3).to_string())

# --- allenatori: aggancio ---
print("\n=== allenatori SofaScore -> nostri ===")
nomi=pd.concat([p['Allenatore casa'],p['Allenatore trasferta']]).dropna()
p['k_casa']=p['Allenatore casa'].map(A.normalizza_nome); p['k_tras']=p['Allenatore trasferta'].map(A.normalizza_nome)
kk=pd.concat([p.k_casa,p.k_tras]).replace('',np.nan).dropna()
print("celle allenatore riempite: %d su %d"%(nomi.notna().sum(),2*len(p)))
print("nomi distinti (grezzi):",nomi.nunique()," chiavi distinte:",kk.nunique())
glob=set(tutte.manager_key.unique())
p2526=set(tutte[(tutte.season==2025)&tutte.is_top5].manager_key)
u=pd.Series(sorted(kk.unique()))
print("chiavi che esistono in games.csv (globale, 6.995 chiavi): %d/%d = %.1f%%"%(u.isin(glob).sum(),len(u),100*u.isin(glob).mean()))
print("chiavi che esistono fra gli allenatori delle nostre 5 leghe 2025-26 (%d): %d"%(len(p2526),u.isin(p2526).sum()))
cell=kk.isin(glob)
print("CELLE agganciate (non nomi): %d/%d = %.1f%%"%(cell.sum(),len(kk),100*cell.mean()))
p['ok2']=p.k_casa.isin(glob)&p.k_tras.isin(glob)
print("partite con ENTRAMBI gli allenatori agganciati: %d/912 = %.1f%%"%(p.ok2.sum(),100*p.ok2.mean()))
conf=A.conflitti_identita(tutte).manager_key.unique()
print("chiavi agganciate che sono OMONIMI dimostrati:",sorted(set(u[u.isin(glob)])&set(conf)))

# --- ponte partita->game_id via (data, allenatore casa, allenatore trasferta) ---
print("\n=== ponte partita->game_id SENZA nomi squadra ===")
h=tutte[tutte.casa].copy()
h['chiave']=h.date.dt.strftime('%Y-%m-%d')+'|'+h.manager_key+'|'+h.manager_key_avv
mappa=h.drop_duplicates('chiave').set_index('chiave').game_id
p['chiave']=p.Data.dt.strftime('%Y-%m-%d')+'|'+p.k_casa+'|'+p.k_tras
p['gid']=p.chiave.map(mappa)
print("agganciate per (data, all.casa, all.trasferta): %d/912 = %.1f%%"%(p.gid.notna().sum(),100*p.gid.notna().mean()))
# tolleranza +-1 giorno
mult={}
for off in (-1,0,1):
    hh=h.copy(); hh['chiave']=(hh.date+pd.Timedelta(days=off)).dt.strftime('%Y-%m-%d')+'|'+hh.manager_key+'|'+hh.manager_key_avv
    mult.update(hh.drop_duplicates('chiave').set_index('chiave').game_id.to_dict())
p['gid2']=p.chiave.map(mult)
print("con tolleranza +-1 giorno: %d/912 = %.1f%%"%(p.gid2.notna().sum(),100*p.gid2.notna().mean()))
# verifica: il punteggio coincide?
v=p.dropna(subset=['gid2']).merge(h[['game_id','gol_fatti','gol_subiti','club_name','avversario_name']],left_on='gid2',right_on='game_id')
ok=(v['Gol casa']==v.gol_fatti)&(v['Gol trasferta']==v.gol_subiti)
print("dei agganciati, punteggio 90' identico: %d/%d = %.1f%%"%(ok.sum(),len(v),100*ok.mean()))
print(v[~ok][['Data','Casa','Trasferta','Gol casa','Gol trasferta','gol_fatti','gol_subiti','club_name','avversario_name']].head(10).to_string())
p.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p2.pkl')
