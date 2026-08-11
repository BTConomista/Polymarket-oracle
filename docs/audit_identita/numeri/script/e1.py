import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
pd.set_option('display.width',250)
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
m=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/mandati.pkl')
print("distribuzione partite fra le 836 interruzioni:")
print(m[m.interruzione].partite.value_counts().sort_index().head(10).to_dict())
print("interruzioni con >1 partita:",int((m.interruzione&(m.partite>1)).sum()))
# quante PERSONE dietro gli 11 nomi in conflitto (lower bound via cricche stesso-giorno)
conf=A.conflitti_identita(tutte)
print("\n=== quante PERSONE dietro le 29 righe ===")
for k,s in conf.groupby('manager_key'):
    club=set(s.club_a)|set(s.club_b)
    # massimo numero di club distinti nello STESSO giorno
    mx=max(len(set(g.club_a)|set(g.club_b)) for _,g in s.groupby(s.date_a))
    print(f"  {k:20s} righe={len(s):2d} club coinvolti={len(club)} max club nello stesso giorno={mx}")
print("=> 11 chiavi, ognuna >=2 persone, nessuna >=3 => almeno 22 persone dietro 11 chiavi")
# ricuci: cosa succede sui casi patologici
r=A.panchine(tutte,ricuci=True)
print("\nmandati: senza ricuci %d, con ricuci %d (assorbiti %d)"%(len(m),len(r),len(m)-len(r)))
for club,nome in [(40,'Bordeaux'),(703,'Forest')]:
    pass
bx=m[m.club_name.str.contains('Bordeaux',na=False)&m.data_da.between('2018-08-01','2019-01-31')]
print("\nBORDEAUX senza ricuci:"); print(bx[['manager_key','data_da','data_a','partite','interruzione']].to_string())
cid=bx.club_id.iloc[0]
print("BORDEAUX con ricuci:"); print(r[(r.club_id==cid)&r.data_da.between('2018-06-01','2019-06-30')][['manager_key','data_da','data_a','partite','interruzioni','partite_altrui']].to_string())
fx=m[m.club_name.str.contains('Nottingham',na=False)&m.data_da.between('2024-09-01','2024-12-31')]
print("\nFOREST senza ricuci:"); print(fx[['manager_key','data_da','data_a','partite','interruzione']].to_string())
cid=fx.club_id.iloc[0]
print("FOREST con ricuci:"); print(r[(r.club_id==cid)&r.data_da.between('2024-06-01','2025-06-30')][['manager_key','data_da','data_a','partite','interruzioni','partite_altrui']].to_string())
