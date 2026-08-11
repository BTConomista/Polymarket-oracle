import pandas as pd, sys, itertools
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data.club_matching import Agganciatore

BASE='/home/user/Polymarket-oracle/'
p=pd.read_excel(BASE+'files/sofascore_coppe_europee_2526/originale_sofascore.xlsx',sheet_name='Partite')
p['data']=pd.to_datetime(p['Data'],format='%d.%m.%Y')
a=Agganciatore()
nomi=sorted(set(p['Casa'])|set(p['Trasferta']))
print('nomi in Partite:',len(nomi))
cand={n:a.candidati(n) for n in nomi}
cid={n:c[0] for n,c in cand.items() if len(c)==1}
ignoti=[n for n in nomi if len(cand[n])!=1]
print('ignoti:',len(ignoti))

g=pd.read_csv(BASE+'files/player_scores/games.csv.gz',
    usecols=['game_id','competition_id','season','date','home_club_id','away_club_id','home_club_goals','away_club_goals','stadium'])
UEFA={'CL','CLQ','EL','ELQ','UCOL','ECLQ'}
gu=g[g['competition_id'].isin(UEFA)&(g['season']==2025)].copy()
gu['date']=pd.to_datetime(gu['date'])
print('partite UEFA 2025 in games.csv:',len(gu))

names=pd.read_csv(BASE+'files/player_scores/club_names.csv.gz').set_index('club_id')['name'].to_dict()

# indice per (club_id) -> righe
from collections import defaultdict
per_club=defaultdict(list)
for r in gu.itertuples():
    per_club[r.home_club_id].append(r)
    per_club[r.away_club_id].append(r)

def ricostruisci(nome, tol=1, usa_punteggio=True):
    """Per ogni partita del nome ignoto, cerca in games.csv la gara di quella
    data (+-tol) che coinvolge l'avversario gia' agganciato; ritorna l'altro club."""
    out=[]
    sub=p[(p['Casa']==nome)|(p['Trasferta']==nome)]
    for r in sub.itertuples():
        casa = r.Casa==nome
        avv = r.Trasferta if casa else r.Casa
        if avv not in cid:  # avversario non agganciato -> non usabile
            out.append((r.data.date(), avv, None, 'avv-ignoto')); continue
        ac=cid[avv]
        trovati=set()
        for row in per_club[ac]:
            if abs((row.date-r.data).days)>tol: continue
            # il nostro nome deve stare dal lato giusto
            if casa:
                if row.away_club_id!=ac: continue
                altro=row.home_club_id
                gh,ga=r._7, r._8   # Gol casa, Gol trasferta
                if usa_punteggio and (row.home_club_goals!=gh or row.away_club_goals!=ga): continue
            else:
                if row.home_club_id!=ac: continue
                altro=row.away_club_id
                gh,ga=r._7, r._8
                if usa_punteggio and (row.home_club_goals!=gh or row.away_club_goals!=ga): continue
            trovati.add(altro)
        out.append((r.data.date(), avv, sorted(trovati), 'ok'))
    return out

print()
print('=== 31 nomi ignoti ===')
riepilogo={}
for n in ignoti:
    res=ricostruisci(n)
    cands=defaultdict(int)
    usabili=0
    for d,avv,t,st in res:
        if st!='ok' or t is None: continue
        if len(t)==1:
            usabili+=1; cands[t[0]]+=1
        elif len(t)>1:
            usabili+=1
            for x in t: cands[x]+=1
    riepilogo[n]=dict(cands)
    tot=len(res)
    print(f'{n!r:45s} partite={tot:3d} usabili={usabili:3d} -> ' +
          ', '.join(f'{names.get(k,k)}({k}):{v}' for k,v in sorted(cands.items(),key=lambda x:-x[1])))
