"""Ricalcola OGNI numero della diagnosi alias. Sola lettura, non tocca nulla.
   uso: python RIPRODUCI.py   (dalla cartella scratchpad)"""
import sys; sys.path.insert(0,'.')
from tool import *
from prova import sofa_fixtures, deduci, nome_di, PART, G25
from tiebreak import candidati_tb, crudo
from guardia import bloccato, canonico
import pandas as pd, json, glob

ALIAS_NUOVI = {
 'AC Sparta Praha':197,'AIK':272,'Araz Naxçıvan':44360,'Aris Thessaloniki':605,
 'Beşiktaş JK':114,'ETO FC Győr':6055,'FC Bayern München':27,'FC København':190,
 'FCI Levadia Tallinn':5771,'FK Austria Wien':14,'FK Crvena Zvezda':159,
 'Ferencváros TC':279,"Hapoel Be'er Sheva":2976,'KF Ballkani':28082,
 'KF Shkëndija':1167,'Klaksvíkar Ítróttarfelag':6170,'Nõmme Kalju':22783,
 'Oleksandria':18303,'Olympique Lyonnais':1041,'Royale Union Saint-Gilloise':3948,
 'SK Rapid Wien':170,'SK Slavia Praha':62,'Sporting Braga':1075,'Zirə FK':46710,
 'Ħamrun Spartans FC':17149,'AFC Ajax':610,'Athletic Club':621,
 'FK Radnički 1923':4645,'FK Žalgiris':602,'Feyenoord':234,'SS Virtus':10613,
 'Olympique lyonnais':1041,'Thonon Évian GG FC':14171,'Internazionale':46,
 'FC Südtirol-Alto Adige':4554,'Lille OSC':1082,'Man Utd':985,'Nottm Forest':703,
 'Espanol':714,
}
print(f'[1] alias proposti: {len(ALIAS_NUOVI)}')

# --- [2] FALSO POSITIVO Espanol: ricomposizione snapshot <-> games.csv
G['d2']=pd.to_datetime(G['date']).dt.date
COD={'serie_a':'IT1','premier_league':'GB1','la_liga':'ES1','bundesliga':'L1','ligue_1':'FR1'}
tot=ok=0; mai=0; scarto=[]
for lg,cc in COD.items():
    d=pd.read_csv(f'/home/user/Polymarket-oracle/data/{lg}_matches.csv', parse_dates=['date'])
    g=G[G.competition_id==cc]
    idx={(r.d2,int(r.home_club_id),int(r.away_club_id)):(r.home_club_goals,r.away_club_goals) for _,r in g.iterrows()}
    for _,r in d.iterrows():
        k=(r['date'].date(), A.aggancia(r.home_team), A.aggancia(r.away_team)); tot+=1
        if k not in idx: mai+=1
        elif idx[k]==(r.home_goals,r.away_goals): ok+=1
        else: scarto.append((lg,str(r['date'].date()),r.home_team,r.away_team,idx[k],(r.home_goals,r.away_goals)))
print(f'[2] snapshot 5 leghe: {tot} partite, ricomposte in games.csv {ok} ({100*ok/tot:.2f}%), coppia mai trovata {mai}, punteggio diverso {len(scarto)}')
print(f"    'Espanol' -> {A.candidati('Espanol')} = {[nome_di(c) for c in A.candidati('Espanol')]}  (giusto: 714 RCD Espanyol Barcelona)")
print(f'    partite La Liga coinvolte: {mai}')
for s in scarto: print('    R1 (campo vs tribunale):', s)

# --- [3] AUTOTEST del matcher sul registro
c={'se':0,'amb':0,'ass':0}; c2=dict(c)
for cid,nm in zip(CN.club_id, CN.name):
    for f,acc in ((A.candidati,c),(candidati_tb,c2)):
        x=f(nm); acc['se' if x==[cid] else ('ass' if not x else 'amb')]+=1
print(f"[3] autotest registro ({len(CN)} nomi): ORA se-stesso {c['se']} ({100*c['se']/len(CN):.2f}%), ambigui {c['amb']}, assenti {c['ass']}"
      f" | CON SPAREGGIO se-stesso {c2['se']} ({100*c2['se']/len(CN):.2f}%), ambigui {c2['amb']}")

# --- [4] SofaScore: controllo per FIXTURE su tutti i 212 nomi
_o=A.aggancia; A.aggancia=lambda n: ALIAS_NUOVI.get(n,_o(n))
nomi=sorted(set(PART.Squadra)|set(PART.Avversario))
conc=disc=senza=0; vot=0; tots=0
for n in nomi:
    v,u,t=deduci(n); tots+=t
    p=ALIAS_NUOVI.get(n,_o(n))
    if not v: senza+=1; continue
    top=v.most_common(1)[0]; vot+=top[1]
    if top[0]==p and len(v)==1: conc+=1
    else: disc+=1
A.aggancia=_o
print(f'[4] sofascore: {len(nomi)} nomi | verdetto-fixture concorde {conc}, discorde {disc}, senza verdetto {senza}'
      f' | conferme {vot}/{tots} partite-squadra')

# --- [5] coppe: controllo contro il club_id GIA NOTO (fonte player-scores)
CP=pd.read_csv('/home/user/Polymarket-oracle/data/coppe_2526/partite.csv')
rows=[CP[['casa','home_club_id']].rename(columns={'casa':'n','home_club_id':'cid'}),
      CP[['ospite','away_club_id']].rename(columns={'ospite':'n','away_club_id':'cid'})]
d=pd.concat(rows).dropna().drop_duplicates()
for et,f in [('ORA',lambda n:A.aggancia(n)),('SPAREGGIO',lambda n:(lambda c:c[0] if len(c)==1 else None)(candidati_tb(n)))]:
    v=[f(n) for n in d.n]
    g=sum(1 for x,y in zip(v,d.cid) if x==y); s=sum(1 for x,y in zip(v,d.cid) if x and x!=y)
    print(f'[5] coppe, {len(d)} coppie (nome, club_id noto) — {et}: giusti {g} ({100*g/len(d):.1f}%), SBAGLIATI {s}, vuoti {sum(1 for x in v if not x)}')

# --- [6] Coupe de France: assenza a monte
lungo=pd.concat([CP[['competizione','casa','divisione_casa']].rename(columns={'casa':'sq','divisione_casa':'div'}),
                 CP[['competizione','ospite','divisione_ospite']].rename(columns={'ospite':'sq','divisione_ospite':'div'})])
lungo['stato']=[('univoco' if len(A.candidati(n))==1 else 'ambiguo' if A.candidati(n) else 'assente') for n in lungo.sq]
ass=lungo[lungo.stato=='assente'].drop_duplicates('sq')
cdf=ass[ass.competizione=='Coupe de France']
print(f'[6] coppe assenti {len(ass)} | Coupe de France {len(cdf)} ({100*len(cdf)/len(ass):.1f}%)'
      f' | di questi div>=4 o oltremare {int(((cdf["div"]>=4)|(cdf["div"].isna())).sum())} ({100*((cdf["div"]>=4)|(cdf["div"].isna())).mean():.1f}%),'
      f' div>=3 {int(((cdf["div"]>=3)|(cdf["div"].isna())).sum())} ({100*((cdf["div"]>=3)|(cdf["div"].isna())).mean():.1f}%), div<=2 {int((cdf["div"]<=2).sum())}')
print(f'    player-scores, competizioni francesi presenti: {list(COMP[COMP.country_name=="France"].competition_id)}  -> niente FR2, niente Coupe de France')

# --- [7] Red Star FC
print(f"[7] 'Red Star FC' -> ORA {A.candidati('Red Star FC')} ({[nome_di(c) for c in A.candidati('Red Star FC')]}), guardia canonica lo blocca: {bloccato('Red Star FC')}"
      f" | costo: 'FC Lusitanos' verrebbe bloccato = {bloccato('FC Lusitanos')}")

# --- [8] guadagno
P=pd.read_excel('/home/user/Polymarket-oracle/files/sofascore_coppe_europee_2526/originale_sofascore.xlsx', sheet_name='Partite')
NOSTRE=set()
for lg in COD:
    d0=pd.read_csv(f'/home/user/Polymarket-oracle/data/{lg}_matches.csv')
    ult=d0[d0.season==d0.season.max()]
    NOSTRE|={A.aggancia(n) for n in set(ult.home_team)|set(ult.away_team)}
NOSTRE={c for c in NOSTRE if c} | {714}
def gn(n): return ALIAS_NUOVI.get(n, A.aggancia(n))
for et,f in [('PRIMA',A.aggancia),('DOPO',gn)]:
    tocc=sum(1 for _,r in P.iterrows() if f(r.Casa) in NOSTRE or f(r.Trasferta) in NOSTRE)
    sq={x for _,r in P.iterrows() for x in (f(r.Casa),f(r.Trasferta)) if x in NOSTRE}
    due=sum(1 for _,r in P.iterrows() if f(r.Casa) and f(r.Trasferta))
    print(f'[8] sofascore {et}: partite che toccano una nostra squadra 2025-26 {tocc}/912 | nostre squadre trovate {len(sq)}/96 | partite con ENTRAMBE agganciate {due}/912 ({100*due/912:.1f}%)')
