import sys; sys.path.insert(0,'.')
from tool import *
import unicodedata, json, pandas as pd
from collections import Counter
from src.data.club_matching import _TRADUZIONE

def residui(s):
    s = str(s).translate(_TRADUZIONE)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return [c for c in s if not (c.isascii() and (c.isalnum() or c==' '))]

fonti = {}
sn=[]
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(f'/home/user/Polymarket-oracle/data/{lg}_matches.csv'); sn+=d.home_team.tolist()+d.away_team.tolist()
fonti['snapshot']=set(sn)
sofa=pd.read_csv('/home/user/Polymarket-oracle/files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Squadra','Avversario'])
fonti['sofascore']=set(sofa.Squadra)|set(sofa.Avversario)
cp=pd.read_csv('/home/user/Polymarket-oracle/data/coppe_2526/partite.csv')
fonti['coppe']=set(cp.casa.dropna())|set(cp.ospite.dropna())
sq=json.load(open('/home/user/Polymarket-oracle/data/squadre_smarkets_2026_27.json'))
fonti['smarkets']=set(x for v in sq['per_lega'].values() for x in v)
fonti['registro']=set(CN['name'])

for f,ns in fonti.items():
    c=Counter()
    for n in ns:
        for ch in residui(n): c[ch]+= 1
    print(f, dict(sorted(c.items(), key=lambda kv:-kv[1])))
