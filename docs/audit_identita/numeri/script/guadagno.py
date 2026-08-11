import pandas as pd, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
import src.data.club_matching as cm
from src.data.club_matching import Agganciatore
B='/home/user/Polymarket-oracle/'
g=pd.read_csv(B+'files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Squadra','Avversario','Data','Campo'])
sq=sorted(set(g['Squadra'].unique())|set(g['Avversario'].dropna().unique()))

def misura(tag):
    a=Agganciatore()
    ok={n for n in sq if len(a.candidati(n))==1}
    p=pd.read_excel(B+'files/sofascore_coppe_europee_2526/originale_sofascore.xlsx',sheet_name='Partite')
    ent=((p['Casa'].isin(ok))&(p['Trasferta'].isin(ok))).sum()
    righe=g[g['Squadra'].isin(ok)&g['Avversario'].isin(ok)]
    print(f'{tag:35s} nomi {len(ok)}/{len(sq)} ({100*len(ok)/len(sq):.1f}%)  partite entrambe {ent}/{len(p)}  righe-giocatore {len(righe)}/{len(g)}')
    return ok

prima=misura('PRIMA (HEAD)')
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
cm.ALIAS.update(NUOVI)
d1=misura('DOPO i 29 alias proposti')
# + fix caratteri (difetto separato): schwa e H sbarrata
cm._TRADUZIONE.update(str.maketrans({'ə':'a','Ə':'a','ħ':'h','Ħ':'h'}))
d2=misura('+ fix caratteri (separato)')
# + Feyenoord risolto davvero
cm.ALIAS['Feyenoord']='SC Feyenoord Rotterdam'   # prova: peggiora?
d3=misura("+ alias Feyenoord->'SC Feyenoord Rotterdam'")
print()
print('nomi ancora non risolti dopo i 29 alias:',sorted(set(sq)-d1))
print('nomi ancora non risolti dopo il fix caratteri:',sorted(set(sq)-d2))
