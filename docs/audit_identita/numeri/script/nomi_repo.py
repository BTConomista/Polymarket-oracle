import pandas as pd, json, glob, sys, gzip
sys.path.insert(0,'/home/user/Polymarket-oracle')
B='/home/user/Polymarket-oracle/'
nomi=set()
def add(it,src):
    for x in it:
        if isinstance(x,str) and x.strip(): nomi.add((x.strip(),src))
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(B+f'data/{lg}_matches.csv',usecols=['home_team','away_team'])
    add(d['home_team'].unique(),'snapshot'); add(d['away_team'].unique(),'snapshot')
for f in glob.glob(B+'data/club_fixtures*.csv'):
    d=pd.read_csv(f)
    for c in d.columns:
        if 'team' in c or 'club' in c or 'opponent' in c: add(d[c].dropna().unique(),'fixtures')
p=pd.read_csv(B+'data/coppe_2526/partite.csv')
print('coppe partite cols',p.columns.tolist())
for c in p.columns:
    if p[c].dtype==object and c.lower() in ('casa','trasferta','squadra','avversario','club'): add(p[c].dropna().unique(),'coppe')
sq=json.load(open(B+'data/squadre_smarkets_2026_27.json'))
def walk(o):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
    elif isinstance(o,str): nomi.add((o.strip(),'smarkets'))
walk(sq)
ag=pd.read_csv(B+'data/coppe_2526/aggancio_squadre.csv')
print('aggancio_squadre cols',ag.columns.tolist())
for c in ag.columns:
    if ag[c].dtype==object: add(ag[c].dropna().unique(),'aggancio_squadre')
print('nomi raccolti:',len(nomi))
import pickle; pickle.dump(nomi,open('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/nomi.pkl','wb'))
