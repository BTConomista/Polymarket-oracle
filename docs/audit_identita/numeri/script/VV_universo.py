import sys; sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd, glob, json, os
os.chdir('/home/user/Polymarket-oracle')
nomi=set()
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(f'data/{lg}_matches.csv')
    nomi|=set(d.home_team)|set(d.away_team)
# coppe
cp=pd.read_csv('data/coppe_2526/partite.csv')
nomi|=set(cp.casa.dropna())|set(cp.ospite.dropna())
# smarkets squadre
try:
    s=json.load(open('data/squadre_smarkets_2026_27.json'))
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if isinstance(v,str): nomi.add(v)
                nomi.add(k) if isinstance(k,str) else None
                walk(v)
        elif isinstance(o,list):
            for v in o:
                if isinstance(v,str): nomi.add(v)
                else: walk(v)
    walk(s)
except Exception as e: print('smk',e)
# sofascore
try:
    P=pd.read_excel('files/sofascore_coppe_europee_2526/originale_sofascore.xlsx', sheet_name='Partite')
    nomi|=set(P.Casa.dropna())|set(P.Trasferta.dropna())
except Exception as e: print('sofa',e)
# registro
CN=pd.read_csv('files/player_scores/club_names.csv.gz')
nomi|=set(CN.name.dropna())
nomi={n for n in nomi if isinstance(n,str)}
print('universo nomi:',len(nomi))
json.dump(sorted(nomi), open('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/VV_nomi.json','w'))
