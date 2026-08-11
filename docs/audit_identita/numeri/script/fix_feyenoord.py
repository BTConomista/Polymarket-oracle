import pandas as pd, sys, glob, json
sys.path.insert(0,'/home/user/Polymarket-oracle')
import src.data.club_matching as cm
from src.data.club_matching import Agganciatore, normalizza
B='/home/user/Polymarket-oracle/'
id2n=pd.read_csv(B+'files/player_scores/club_names.csv.gz').set_index('club_id')['name'].to_dict()

# --- opzione: escludere dal REGISTRO le riserve/amatori omografe ---
class Agg2(Agganciatore):
    ESCLUSI={2826, 11495}
    def __init__(self, club_names=None):
        if club_names is None: club_names=pd.read_csv(cm.CLUB_NAMES)
        club_names=club_names[~club_names['club_id'].isin(self.ESCLUSI)]
        super().__init__(club_names)

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

# nomi del repo
nomi=set()
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(B+f'data/{lg}_matches.csv',usecols=['home_team','away_team'])
    nomi|=set(d['home_team'])|set(d['away_team'])
p=pd.read_csv(B+'data/coppe_2526/partite.csv'); nomi|=set(p['casa'].dropna())|set(p['ospite'].dropna())
ag=pd.read_csv(B+'data/coppe_2526/aggancio_squadre.csv'); nomi|=set(ag['nome_diretta'].dropna())
gsof=pd.read_csv(B+'files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Squadra','Avversario'])
nomi|=set(gsof['Squadra'])|set(gsof['Avversario'].dropna())
sq=json.load(open(B+'data/squadre_smarkets_2026_27.json'))
def walk(o):
    if isinstance(o,dict):
        [walk(v) for v in o.values()]
    elif isinstance(o,list): [walk(v) for v in o]
    elif isinstance(o,str): nomi.add(o.strip())
walk(sq)
nomi={n for n in nomi if isinstance(n,str) and n.strip()}
print('nomi repo:',len(nomi))

base=Agganciatore(); r0={n:base.candidati(n) for n in nomi}
cm.ALIAS.update(NUOVI)
cm._TRADUZIONE.update(str.maketrans({'ə':'a','Ə':'a','ħ':'h','Ħ':'h'}))
a1=Agganciatore(); r1={n:a1.candidati(n) for n in nomi}
a2=Agg2();        r2={n:a2.candidati(n) for n in nomi}
print()
print('Feyenoord:', [id2n.get(x) for x in r1['Feyenoord']], '->', [id2n.get(x) for x in r2['Feyenoord']])
print()
print('regressioni introdotte dall\'esclusione di 2826/11495 (rispetto ai 29 alias + fix caratteri):')
n=0
for k in nomi:
    if len(r1[k])==1 and (len(r2[k])!=1 or r2[k][0]!=r1[k][0]):
        n+=1; print('  ',repr(k), id2n.get(r1[k][0]),'->',[id2n.get(x) for x in r2[k]])
print('  totale:',n)
print()
print('regressioni rispetto a HEAD:')
n=0
for k in nomi:
    if len(r0[k])==1 and (len(r2[k])!=1 or r2[k][0]!=r0[k][0]):
        n+=1; print('  ',repr(k), id2n.get(r0[k][0]),'->',[id2n.get(x) for x in r2[k]])
print('  totale:',n)
# guadagno finale
sqs=sorted(set(gsof['Squadra'])|set(gsof['Avversario'].dropna()))
ok={x for x in sqs if len(r2[x])==1}
pt=pd.read_excel(B+'files/sofascore_coppe_europee_2526/originale_sofascore.xlsx',sheet_name='Partite')
ent=((pt['Casa'].isin(ok))&(pt['Trasferta'].isin(ok))).sum()
righe=gsof[gsof['Squadra'].isin(ok)&gsof['Avversario'].isin(ok)]
print()
print(f'FINALE: nomi {len(ok)}/{len(sqs)}  partite {ent}/912  righe {len(righe)}/{len(gsof)}')
