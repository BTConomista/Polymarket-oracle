import sys, json, glob, re, unicodedata
sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd
import src.data.club_matching as cm

U = {}  # nome -> set(fonti)
def add(n, f):
    if isinstance(n,str) and n.strip():
        U.setdefault(n, set()).add(f)

# 1. snapshot 5 leghe (tutte le stagioni)
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(f'data/{lg}_matches.csv')
    for n in set(d.home_team)|set(d.away_team): add(n,'snapshot')
# 2. club_fixtures (avversari di coppa/Europa)
for f in glob.glob('data/club_fixtures*.csv'):
    d=pd.read_csv(f)
    for c in d.columns:
        if d[c].dtype==object and c.lower() in ('team','opponent','home_team','away_team','club','avversario'):
            for n in d[c].dropna().unique(): add(n,'fixtures')
# 3. coppe nazionali
cp=pd.read_csv('data/coppe_2526/partite.csv')
for n in set(cp.casa)|set(cp.ospite): add(n,'coppe')
for f in ['data/coppe_2526/aggancio_squadre.csv']:
    d=pd.read_csv(f)
    for n in d.nome_diretta.dropna().unique(): add(n,'coppe_diretta')
# 4. sofascore coppe europee
s=pd.read_csv('files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Squadra','Avversario'])
for n in set(s.Squadra.dropna())|set(s.Avversario.dropna()): add(n,'sofascore')
try:
    P=pd.read_excel('files/sofascore_coppe_europee_2526/originale_sofascore.xlsx', sheet_name='Partite')
    for c in P.columns:
        if c in ('Casa','Trasferta'):
            for n in P[c].dropna().unique(): add(n,'sofascore_partite')
except Exception as e: print('xlsx:',e)
# 5. smarkets
j=json.load(open('data/squadre_smarkets_2026_27.json'))
def raccogli(o):
    if isinstance(o,dict):
        for k,v in o.items():
            raccogli(v)
    elif isinstance(o,list):
        for v in o: raccogli(v)
    elif isinstance(o,str): add(o,'smarkets')
raccogli({k:v for k,v in j.items() if k not in ('cosa','perche','fonte')})
# 6. registro stesso
CN=pd.read_csv('files/player_scores/club_names.csv.gz')
for n in CN.name.dropna().unique(): add(n,'registro')

print('universo:', len(U), 'nomi')
json.dump({k:sorted(v) for k,v in U.items()}, open('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/VER_U.json','w'))
