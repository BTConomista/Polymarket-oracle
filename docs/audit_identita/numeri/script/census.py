import sys, json, glob, unicodedata
from collections import Counter
import pandas as pd
sys.path.insert(0,'/home/user/Polymarket-oracle')

nomi = Counter()   # nome -> fonte(s)
origine = {}

def add(vals, fonte):
    for v in vals:
        if isinstance(v,str) and v.strip():
            nomi[v]+=1
            origine.setdefault(v,set()).add(fonte)

B='/home/user/Polymarket-oracle/'
# 1. registro
reg = pd.read_csv(B+'files/player_scores/club_names.csv.gz')
add(reg['name'].dropna().unique(), 'registro')

# 2. sofascore coppe europee
for f in sorted(glob.glob(B+'files/sofascore_coppe_europee_2526/*.csv.gz')):
    d = pd.read_csv(f, low_memory=False)
    for col in ('Squadra','Casa','Trasferta','Avversario'):
        if col in d.columns: add(d[col].dropna().unique(), 'sofascore')

# 3. smarkets 2026-27
j = json.load(open(B+'data/squadre_smarkets_2026_27.json'))
for lega, lst in j['per_lega'].items(): add(lst, 'smarkets')

# 4. coppe nazionali
for f in sorted(glob.glob(B+'data/coppe_2526/*.csv')):
    d = pd.read_csv(f, low_memory=False)
    for col in d.columns:
        if any(k in col.lower() for k in ('squadra','casa','trasferta','club','avversario')):
            if d[col].dtype==object: add(d[col].dropna().unique(), 'coppe:'+f.split('/')[-1]+':'+col)

# 5. snapshot 5 leghe
for lg in ('serie_a','premier_league','la_liga','bundesliga','ligue_1'):
    d = pd.read_csv(B+f'data/{lg}_matches.csv', low_memory=False)
    for col in ('home_team','away_team'):
        if col in d.columns: add(d[col].dropna().unique(), 'snapshot')

print('nomi distinti totali:', len(nomi))

# caratteri che sopravvivono a NFKD (dopo _TRADUZIONE) e sono lettere
from src.data.club_matching import _TRADUZIONE
sopravvissuti = Counter()
esempi = {}
for n in nomi:
    s = n.translate(_TRADUZIONE)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    for c in s:
        if c.isalpha() and not ('a'<=c<='z'):
            sopravvissuti[c]+=1
            esempi.setdefault(c,set()).add((n, tuple(sorted(origine[n]))))
for c,k in sopravvissuti.most_common():
    print(repr(c), hex(ord(c)), unicodedata.name(c,'?'), 'occorrenze-nome:',k, list(esempi[c])[:6])
