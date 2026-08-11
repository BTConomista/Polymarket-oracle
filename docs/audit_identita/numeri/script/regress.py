import pandas as pd, sys
from collections import defaultdict
sys.path.insert(0,'/home/user/Polymarket-oracle')
import src.data.club_matching as cm
from src.data.club_matching import Agganciatore, normalizza

NUOVI={
 'AC Sparta Praha':'AC Sparta Prague','AIK':'Allmänna Idrottsklubben','Araz Naxçıvan':'Araz-Nakhchivan ',
 'Aris Thessaloniki':'Aris Thessalonikis','Beşiktaş JK':'Beşiktaş Jimnastik Kulübü','ETO FC Győr':'ETO FC',
 'FC Bayern München':'Bayern Munich','FC København':'FC Copenhagen','FCI Levadia Tallinn':'Levadia Tallinn',
 'FK Austria Wien':'Austria Vienna','FK Crvena Zvezda':'Red Star Belgrade','Ferencváros TC':'Ferencvárosi TC',
 "Hapoel Be'er Sheva":'Hapoel Beer Sheva','KF Ballkani':'FC Ballkani','KF Shkëndija':'Shkendija Tetovo',
 'Klaksvíkar Ítróttarfelag':'KÍ Klaksvík','Nõmme Kalju':'Kalju FC','Oleksandria':'FC Oleksandriya',
 'Olympique Lyonnais':'Olympique Lyon','Royale Union Saint-Gilloise':'Union Saint-Gilloise',
 'SK Rapid Wien':'Rapid Vienna','SK Slavia Praha':'SK Slavia Prague','Sporting Braga':'SC Braga',
 'AFC Ajax':'Ajax Amsterdam','Athletic Club':'Athletic Bilbao','FK Radnički 1923':'FK Radnicki 1923 Kragujevac',
 'FK Žalgiris':'FK Zalgiris Vilnius','Feyenoord':'Feyenoord Rotterdam','SS Virtus':'AC Virtus Acquaviva',
}
print('nuovi alias proposti:',len(NUOVI))

base=Agganciatore()
names=pd.read_csv('/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz')
id2n=names.set_index('club_id')['name'].to_dict()

# 0) i target esistono ESATTAMENTE nel registro?
insieme=set(names['name'])
for k,v in NUOVI.items():
    if v not in insieme: print('  ⚠ target NON presente alla lettera:',repr(v))

# 1) collisioni di CHIAVE con alias esistenti
chiavi_vecchie=defaultdict(list)
for k in cm.ALIAS: chiavi_vecchie[normalizza(k)].append(k)
for k in NUOVI:
    nk=normalizza(k)
    if nk in chiavi_vecchie:
        print('  ⚠ COLLISIONE chiave con alias esistente:',repr(k),'->',chiavi_vecchie[nk])
# collisioni fra i nuovi stessi
nuove=defaultdict(list)
for k in NUOVI: nuove[normalizza(k)].append(k)
for nk,ks in nuove.items():
    if len(ks)>1: print('  ⚠ due nuovi alias con la STESSA chiave normalizzata:',ks)

print()
print('chiavi normalizzate dei nuovi alias:')
for k in NUOVI: print(f'   {k!r:40s} -> {sorted(normalizza(k))}')

# 2) applica e verifica unicita'
cm.ALIAS.update(NUOVI)
dopo=Agganciatore()
print()
print('esito dopo la patch (deve essere 1 candidato ciascuno):')
for k,v in NUOVI.items():
    c=dopo.candidati(k)
    flag='' if len(c)==1 else '  ⚠⚠'
    print(f'   {k!r:40s} {len(c)} {[id2n.get(x) for x in c][:4]}{flag}')
