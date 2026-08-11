import pandas as pd, sys
from collections import defaultdict
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data.club_matching import Agganciatore
BASE='/home/user/Polymarket-oracle/'
p=pd.read_excel(BASE+'files/sofascore_coppe_europee_2526/originale_sofascore.xlsx',sheet_name='Partite')
p['data']=pd.to_datetime(p['Data'],format='%d.%m.%Y')
a=Agganciatore()
nomi=sorted(set(p['Casa'])|set(p['Trasferta']))
cand={n:a.candidati(n) for n in nomi}
cid={n:c[0] for n,c in cand.items() if len(c)==1}
ignoti=[n for n in nomi if len(cand[n])!=1]
g=pd.read_csv(BASE+'files/player_scores/games.csv.gz',
    usecols=['game_id','competition_id','season','date','home_club_id','away_club_id','home_club_goals','away_club_goals','stadium'])
gu=g[g['competition_id'].isin({'CL','CLQ','EL','ELQ','UCOL','ECLQ'})&(g['season']==2025)].copy()
gu['date']=pd.to_datetime(gu['date'])
names=pd.read_csv(BASE+'files/player_scores/club_names.csv.gz').set_index('club_id')['name'].to_dict()
per_club=defaultdict(list)
for r in gu.itertuples():
    per_club[r.home_club_id].append(r); per_club[r.away_club_id].append(r)

def ricostruisci(nome, mappa, tol=1):
    out=[]
    sub=p[(p['Casa']==nome)|(p['Trasferta']==nome)]
    for r in sub.itertuples():
        casa = r.Casa==nome
        avv = r.Trasferta if casa else r.Casa
        if avv not in mappa: out.append(None); continue
        ac=mappa[avv]; trovati=set()
        for row in per_club[ac]:
            if abs((row.date-r.data).days)>tol: continue
            if casa and row.away_club_id==ac and row.home_club_goals==r._7 and row.away_club_goals==r._8:
                trovati.add(row.home_club_id)
            if (not casa) and row.home_club_id==ac and row.home_club_goals==r._7 and row.away_club_goals==r._8:
                trovati.add(row.away_club_id)
        out.append(sorted(trovati))
    return out

mappa=dict(cid)
for giro in (1,2,3):
    nuovi={}
    print(f'--- giro {giro} ---')
    for n in ignoti:
        if n in mappa: continue
        res=ricostruisci(n,mappa)
        c=defaultdict(int)
        for t in res:
            if t:
                for x in t: c[x]+=1
        if len(c)==1:
            k=list(c)[0]; nuovi[n]=k
            print(f'  {n!r:45s} -> {names[k]}({k})  conferme {c[k]}/{len(res)}')
        elif len(c)>1:
            print(f'  {n!r:45s} AMBIGUO {dict(c)}')
        else:
            print(f'  {n!r:45s} nessun candidato ({sum(1 for t in res if t is not None)} partite usabili)')
    mappa.update(nuovi)
    if not nuovi: break
print()
print('risolti:',len([n for n in ignoti if n in mappa]),'/',len(ignoti))
