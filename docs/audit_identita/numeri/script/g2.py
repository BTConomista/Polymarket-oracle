import pandas as pd, numpy as np, sys, difflib
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
p=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p2.pkl')
glob=set(tutte.manager_key.unique())
kk=pd.concat([p.k_casa,p.k_tras]).dropna()
u=sorted(set(kk)); miss=[k for k in u if k not in glob]
print("chiavi SofaScore non presenti in games.csv:",len(miss))
cnt=kk.value_counts()
print("celle coinvolte:",int(cnt[miss].sum()))
print("\nquante hanno un quasi-omonimo in games.csv (>=0.90) -> candidati variante di grafia:")
n=0
for k in miss:
    c=difflib.get_close_matches(k,glob,n=1,cutoff=0.90)
    if c: n+=1; print(f"   {k:28s} ~ {c[0]:28s} (celle {int(cnt[k])})")
print("totale candidati variante:",n,"su",len(miss))
print("\nprimi 15 senza alcun candidato (allenatori davvero fuori dal dataset):")
print([k for k in miss if not difflib.get_close_matches(k,glob,n=1,cutoff=0.90)][:15])
