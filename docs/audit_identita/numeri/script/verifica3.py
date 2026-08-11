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
NUOVI={'AC Sparta Praha':197,'AFC Ajax':610,'AIK':272,'Araz Naxçıvan':44360,'Aris Thessaloniki':605,
'Athletic Club':621,'Beşiktaş JK':114,'ETO FC Győr':6055,'FC Bayern München':27,'FC København':190,
'FCI Levadia Tallinn':5771,'FK Austria Wien':14,'FK Crvena Zvezda':159,'FK Radnički 1923':4645,
'FK Žalgiris':602,'Ferencváros TC':279,'Feyenoord':234,"Hapoel Be'er Sheva":2976,'KF Ballkani':28082,
'KF Shkëndija':1167,'Klaksvíkar Ítróttarfelag':6170,'Nõmme Kalju':22783,'Oleksandria':18303,
'Olympique Lyonnais':1041,'Royale Union Saint-Gilloise':3948,'SK Rapid Wien':170,'SK Slavia Praha':62,
'SS Virtus':10613,'Sporting Braga':1075,'Zirə FK':46710,'Ħamrun Spartans FC':17149}
mappa=dict(cid); mappa.update(NUOVI)
g=pd.read_csv(BASE+'files/player_scores/games.csv.gz',
    usecols=['game_id','competition_id','season','date','home_club_id','away_club_id','home_club_goals','away_club_goals','stadium'])
gu=g[g['competition_id'].isin({'CL','CLQ','EL','ELQ','UCOL','ECLQ'})&(g['season']==2025)].copy()
gu['date']=pd.to_datetime(gu['date'])
names=pd.read_csv(BASE+'files/player_scores/club_names.csv.gz').set_index('club_id')['name'].to_dict()
idx={}
for r in gu.itertuples():
    idx.setdefault((r.home_club_id,r.away_club_id),[]).append(r)

# CONTROLLO PIENO su tutti i 212: ogni partita-squadra deve ricomporsi
tot=0; conf=0; disc=0; senza=0
per_nome=defaultdict(lambda:[0,0,0])
for r in p.itertuples():
    for lato in ('Casa','Trasferta'):
        n=getattr(r,lato); alt=r.Trasferta if lato=='Casa' else r.Casa
        tot+=1
        if n not in mappa or alt not in mappa:
            senza+=1; per_nome[n][2]+=1; continue
        h=mappa[r.Casa]; aw=mappa[r.Trasferta]
        righe=[x for x in idx.get((h,aw),[]) if abs((x.date-r.data).days)<=1]
        ok=[x for x in righe if x.home_club_goals==r._7 and x.away_club_goals==r._8]
        if ok: conf+=1; per_nome[n][0]+=1
        elif righe: disc+=1; per_nome[n][1]+=1
        else: senza+=1; per_nome[n][2]+=1
print(f'partite-squadra: {tot}  conferme {conf} ({100*conf/tot:.1f}%)  discordi {disc}  senza riscontro {senza}')
print()
print('conteggi per i 31 nomi nuovi (conferme / partite):')
for n in sorted(NUOVI):
    c,d,s=per_nome[n]
    print(f'  {n!r:45s} {c}/{c+d+s}   discordi={d} senza={s}')

print()
print('=== le 6 partite-squadra senza riscontro ===')
for r in p.itertuples():
    for lato in ('Casa','Trasferta'):
        n=getattr(r,lato)
        if n not in mappa or r.Casa not in mappa or r.Trasferta not in mappa:
            print(' non mappato', r.Data, r.Casa, r.Trasferta); continue
        h=mappa[r.Casa]; aw=mappa[r.Trasferta]
        righe=[x for x in idx.get((h,aw),[]) if abs((x.date-r.data).days)<=1]
        ok=[x for x in righe if x.home_club_goals==r._7 and x.away_club_goals==r._8]
        if not ok and not righe and lato=='Casa':
            print(f'  {r.Data} {r.Competizione[:12]:12s} {r.Turno[:22]:22s} {r.Casa} {r._7}-{r._8} {r.Trasferta}')
print()
print('=== partite di Sporting Braga e SK Slavia Praha ===')
for nome in ['Sporting Braga','SK Slavia Praha','Klaksvíkar Ítróttarfelag']:
    sub=p[(p['Casa']==nome)|(p['Trasferta']==nome)]
    print(nome, len(sub))
    for r in sub.itertuples():
        avv = r.Trasferta if r.Casa==nome else r.Casa
        print(f'   {r.Data} {r.Casa} {r._7}-{r._8} {r.Trasferta}   [avv baseline agganciato: {avv in cid}]')
