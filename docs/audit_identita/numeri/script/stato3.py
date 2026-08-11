import sys,json
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data.club_matching import Agganciatore
A=Agganciatore()
sq=json.load(open('data/squadre_smarkets_2026_27.json'))
nomi=[]
for lg,v in sq['per_lega'].items():
    print(lg, len(v))
    nomi+= v if isinstance(v,list) else list(v)
nomi=sorted(set(nomi))
print(len(nomi))
ass=[n for n in nomi if len(A.candidati(n))==0]
amb=[n for n in nomi if len(A.candidati(n))>1]
print('assenti',ass); print('ambigui',amb)
print(f"{100*(len(nomi)-len(ass)-len(amb))/len(nomi):.1f}%")
