import pandas as pd, json, glob, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
import src.data.club_matching as cm
from src.data.club_matching import Agganciatore, normalizza
B='/home/user/Polymarket-oracle/'
nomi={}
def add(it,src):
    for x in it:
        if isinstance(x,str) and x.strip(): nomi.setdefault(x.strip(),set()).add(src)
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(B+f'data/{lg}_matches.csv',usecols=['home_team','away_team'])
    add(d['home_team'].unique(),'snapshot'); add(d['away_team'].unique(),'snapshot')
for f in glob.glob(B+'data/club_fixtures*.csv'):
    d=pd.read_csv(f)
    for c in d.columns:
        if d[c].dtype==object and any(k in c.lower() for k in ('team','club','opponent','avversario')): add(d[c].dropna().unique(),'fixtures')
p=pd.read_csv(B+'data/coppe_2526/partite.csv')
add(p['casa'].dropna().unique(),'coppe'); add(p['ospite'].dropna().unique(),'coppe')
ag=pd.read_csv(B+'data/coppe_2526/aggancio_squadre.csv'); add(ag['nome_diretta'].dropna().unique(),'coppe-aggancio')
sq=json.load(open(B+'data/squadre_smarkets_2026_27.json'))
def walk(o):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
    elif isinstance(o,str): nomi.setdefault(o.strip(),set()).add('smarkets')
walk(sq)
# sofascore
g=pd.read_csv(B+'files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Squadra','Avversario'])
add(g['Squadra'].unique(),'sofascore'); add(g['Avversario'].dropna().unique(),'sofascore')
# anagrafica 2026-27
for f in glob.glob(B+'data/stagione_2026_2027/*.csv'):
    try: d=pd.read_csv(f)
    except Exception: continue
    for c in d.columns:
        if d[c].dtype==object and any(k in c.lower() for k in ('squadra','team','club','nome')): add(d[c].dropna().unique(),'2026_27')
print('nomi totali:',len(nomi))

NUOVI={'AC Sparta Praha':'AC Sparta Prague','AIK':'Allmänna Idrottsklubben','Araz Naxçıvan':'Araz-Nakhchivan ',
 'Aris Thessaloniki':'Aris Thessalonikis','Beşiktaş JK':'Beşiktaş Jimnastik Kulübü','ETO FC Győr':'ETO FC',
 'FC Bayern München':'Bayern Munich','FC København':'FC Copenhagen','FCI Levadia Tallinn':'Levadia Tallinn',
 'FK Austria Wien':'Austria Vienna','FK Crvena Zvezda':'Red Star Belgrade','Ferencváros TC':'Ferencvárosi TC',
 "Hapoel Be'er Sheva":'Hapoel Beer Sheva','KF Ballkani':'FC Ballkani','KF Shkëndija':'Shkendija Tetovo',
 'Klaksvíkar Ítróttarfelag':'KÍ Klaksvík','Nõmme Kalju':'Kalju FC','Oleksandria':'FC Oleksandriya',
 'Olympique Lyonnais':'Olympique Lyon','Royale Union Saint-Gilloise':'Union Saint-Gilloise',
 'SK Rapid Wien':'Rapid Vienna','SK Slavia Praha':'SK Slavia Prague','Sporting Braga':'SC Braga',
 'AFC Ajax':'Ajax Amsterdam','Athletic Club':'Athletic Bilbao','FK Radnički 1923':'FK Radnicki 1923 Kragujevac',
 'FK Žalgiris':'FK Zalgiris Vilnius','Feyenoord':'Feyenoord Rotterdam','SS Virtus':'AC Virtus Acquaviva'}
chiavi={normalizza(k):k for k in NUOVI}

prima=Agganciatore()
res_prima={n:prima.candidati(n) for n in nomi}
cm.ALIAS.update(NUOVI)
dopo=Agganciatore()
res_dopo={n:dopo.candidati(n) for n in nomi}
id2n=pd.read_csv(B+'files/player_scores/club_names.csv.gz').set_index('club_id')['name'].to_dict()

print()
print('=== nomi del repo che finiscono su una CHIAVE dei nuovi alias ===')
for n,srcs in sorted(nomi.items()):
    nk=normalizza(n)
    if nk in chiavi:
        a,b=res_prima[n],res_dopo[n]
        st=lambda c:('vuoto' if len(c)!=1 else id2n.get(c[0]))
        marca='' if n in NUOVI else '   <-- NON e\' uno dei nomi SofaScore attesi'
        print(f'  {n!r:45s} {sorted(srcs)}  {st(a)} -> {st(b)}{marca}')

print()
print('=== REGRESSIONI: nome che PRIMA era univoco e ORA cambia o si perde ===')
reg=0
for n in nomi:
    a,b=res_prima[n],res_dopo[n]
    if len(a)==1 and (len(b)!=1 or b[0]!=a[0]):
        reg+=1; print('  ',repr(n),id2n.get(a[0]),'->',[id2n.get(x) for x in b])
print('  totale regressioni:',reg)
print()
print('=== nomi che PRIMA erano vuoti/ambigui e ORA sono univoci ===')
nuo=[(n,res_dopo[n][0]) for n in nomi if len(res_prima[n])!=1 and len(res_dopo[n])==1]
print('  totale:',len(nuo))
for n,c in sorted(nuo):
    extra='' if n in NUOVI else '   <-- effetto COLLATERALE (non e\' nella lista proposta)'
    print(f'  {n!r:45s} -> {id2n.get(c)}{extra}')
