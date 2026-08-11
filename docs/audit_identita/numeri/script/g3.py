import pandas as pd, numpy as np, sys, difflib
sys.path.insert(0,'/home/user/Polymarket-oracle')
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
p=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p2.pkl')
glob=set(tutte.manager_key.unique())
miss=set(k for k in set(p.k_casa)|set(p.k_tras) if k not in glob)
nj=p[p.gid2.isna()]
tocca=nj[nj.k_casa.isin(miss)|nj.k_tras.isin(miss)]
print("partite non agganciate: %d; di queste con almeno un allenatore FUORI dal nostro universo: %d (%.0f%%)"%(len(nj),len(tocca),100*len(tocca)/len(nj)))
print("le altre %d non si agganciano perche' la PARTITA non e' in games.csv"%(len(nj)-len(tocca)))
# le 184: quante coinvolgono una nostra squadra top5 2025-26?
nostre=set(tutte[(tutte.season==2025)&tutte.is_top5].manager_key)
print("non agganciate con almeno un allenatore di una nostra lega 2025-26:",int((nj.k_casa.isin(nostre)|nj.k_tras.isin(nostre)).sum()))
# match per cognome sui 37
def cog(k): return k.split()[-1] if k else ''
cogs={}
for k in glob: cogs.setdefault(cog(k),[]).append(k)
ok=0
for k in sorted(miss):
    c=cogs.get(cog(k),[])
    if len(c)==1: ok+=1
print("\ndei %d nomi mancanti, quanti hanno UN SOLO omonimo di cognome nel nostro universo: %d"%(len(miss),ok))
for k in ['adolf hutter','hans dieter flick','ioan ovidiu sabau']:
    print("  ",k,"->",cogs.get(cog(k)))
