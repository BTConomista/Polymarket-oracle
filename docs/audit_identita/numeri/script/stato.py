import sys, json
sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd
from src.data.club_matching import Agganciatore

A = Agganciatore()

def report(nome, nomi):
    nomi = sorted(set(str(n) for n in nomi if isinstance(n,str) and n.strip()))
    st = {'univoco':[], 'ambiguo':[], 'assente':[]}
    for n in nomi:
        c = A.candidati(n)
        st['univoco' if len(c)==1 else ('ambiguo' if len(c)>1 else 'assente')].append(n)
    tot=len(nomi)
    print(f"== {nome}: {tot} nomi -> {100*len(st['univoco'])/tot:.1f}% univoci, {len(st['ambiguo'])} ambigui, {len(st['assente'])} assenti")
    return st

# 1. snapshot 5 leghe
sn=[]
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(f'data/{lg}_matches.csv')
    sn += d['home_team'].tolist()+d['away_team'].tolist()
r_snap = report('snapshot', sn)

# 4. sofascore
sofa = pd.read_csv('files/sofascore_coppe_europee_2526/giocatori.csv.gz', usecols=['Squadra','Avversario','Competizione'])
r_sofa = report('sofascore', sofa['Squadra'].tolist()+sofa['Avversario'].tolist())

# 5. coppe
cp = pd.read_csv('data/coppe_2526/partite.csv')
print(cp.columns.tolist())
