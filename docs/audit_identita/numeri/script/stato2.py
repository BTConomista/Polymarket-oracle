import sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd
from src.data.club_matching import Agganciatore
A=Agganciatore()
def stato(n):
    c=A.candidati(n)
    return 'univoco' if len(c)==1 else ('ambiguo' if len(c)>1 else 'assente')
cp=pd.read_csv('data/coppe_2526/partite.csv')
nomi=sorted(set(cp['casa'].dropna().tolist()+cp['ospite'].dropna().tolist()))
print(len(nomi))
from collections import Counter
c=Counter(stato(n) for n in nomi)
print(c, f"{100*c['univoco']/len(nomi):.1f}%")
# smarkets
import json
sq=json.load(open('data/squadre_smarkets_2026_27.json'))
print(type(sq), list(sq)[:5] if isinstance(sq,dict) else sq[:5])
