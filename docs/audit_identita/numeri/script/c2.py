import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
# 1. stessa chiave sulle due panchine
same=tutte[tutte.manager_key==tutte.manager_key_avv]
print("righe con manager_key == manager_key_avv:", len(same), "| partite:", same.game_id.nunique())
print(same[['date','club_name','avversario_name','allenatore','allenatore_avv']].head().to_string())
# 2. leak d'identita' negli omonimi
e=A.esperienza_prima('2023-01-01',tutte)
for k in ['michel','luis castro']:
    sub=tutte[(tutte.manager_key==k)&(tutte.date<'2023-01-01')]
    print(f"\n{k}: partite_prima={int(e.loc[k,'partite_prima'])}  club distinti={sub.club_id.nunique()}")
    print("   ripartizione per club:", sub.club_name.value_counts().to_dict())
# 3. quanti allenatori-partita del perimetro sono ASSENTI dall'output alla loro data (=debutto)
perim=tutte[tutte.is_top5 & tutte.season.isin(A.STAGIONI)]
prime=perim.groupby('manager_key').date.min()
deb=0; cens=0
for k,d in prime.items():
    ee=A.esperienza_prima(d,tutte,manager_keys=[k])
    if k not in ee.index: deb+=1
    elif bool(ee.loc[k,'censurata']): cens+=1
print(f"\nallenatori del perimetro ({len(prime)}): senza NESSUNA riga di output alla loro prima partita = {deb}; con censurata=True = {cens}")
