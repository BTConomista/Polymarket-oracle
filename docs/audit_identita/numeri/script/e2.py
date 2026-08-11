import pandas as pd, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
pd.set_option('display.width',250)
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
m=A.panchine(tutte); r=A.panchine(tutte,ricuci=True)
print("righe club-partita totali:",len(tutte))
print("senza ricuci: sum(partite)=%d"%m.partite.sum())
print("con ricuci:   sum(partite)=%d + partite_altrui=%d = %d"%(r.partite.sum(),r.partite_altrui.sum(),r.partite.sum()+r.partite_altrui.sum()))
print("PARTITE PERSE:",len(tutte)-(r.partite.sum()+r.partite_altrui.sum()))
cid=int(m[m.club_name.str.contains('Nottingham',na=False)].club_id.iloc[0])
print("\nFOREST tutti i mandati 2023-2026, senza ricuci:")
print(m[(m.club_id==cid)&m.data_da.between('2023-06-01','2026-01-01')][['manager_key','data_da','data_a','partite','interruzione']].to_string())
print("FOREST con ricuci:")
print(r[(r.club_id==cid)&r.data_da.between('2023-06-01','2026-01-01')][['manager_key','data_da','data_a','partite','interruzioni','partite_altrui']].to_string())
# quanti club hanno il mandato SPEZZATO in due dallo stesso allenatore consecutivo dopo ricuci
r2=r.sort_values(['club_id','data_da'])
dup=(r2.manager_key==r2.groupby('club_id').manager_key.shift())
print("\nmandati CONSECUTIVI dello stesso allenatore dopo ricuci (non dovrebbero esistere):",int(dup.sum()))
print(r2[dup][['club_name','manager_key','data_da','data_a','partite']].head(15).to_string())
print("\nsenza ricuci lo stesso conteggio (dev'essere 0 per costruzione):",
      int((m.sort_values(['club_id','data_da']).manager_key==m.sort_values(['club_id','data_da']).groupby('club_id').manager_key.shift()).sum()))
