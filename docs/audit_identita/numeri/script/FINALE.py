import sys; sys.path.insert(0,'.')
from tool import *
from prova import nome_di
import re, unicodedata, json, pandas as pd
import src.data.club_matching as cm

# (1) fix caratteri
TR = dict(cm._TRADUZIONE); TR.update({ord('ə'):'a', ord('Ə'):'a', ord('ħ'):'h', ord('Ħ'):'h'})
cm._TRADUZIONE = TR
def normalizza(nome):
    if not isinstance(nome,str): return frozenset()
    s = nome.translate(TR); s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'\b(saint|sankt)\b','st',s); s = re.sub(r'[^a-z0-9 ]',' ',s)
    return frozenset(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())
cm.normalizza = normalizza

# (2) 36 alias
ALIAS36 = {
 'AC Sparta Praha':'AC Sparta Prague','AIK':'Allmänna Idrottsklubben','Araz Naxçıvan':'Araz-Nakhchivan',
 'Aris Thessaloniki':'Aris Thessalonikis','Beşiktaş JK':'Beşiktaş Jimnastik Kulübü','ETO FC Győr':'ETO FC',
 'FC Bayern München':'Bayern Munich','FC København':'FC Copenhagen','FCI Levadia Tallinn':'Levadia Tallinn',
 'FK Austria Wien':'Austria Vienna','FK Crvena Zvezda':'Red Star Belgrade','Ferencváros TC':'Ferencvárosi TC',
 "Hapoel Be'er Sheva":'Hapoel Beer Sheva','KF Ballkani':'FC Ballkani','KF Shkëndija':'Shkendija Tetovo',
 'Klaksvíkar Ítróttarfelag':'KÍ Klaksvík','Nõmme Kalju':'Kalju FC','Oleksandria':'FC Oleksandriya',
 'Olympique Lyonnais':'Olympique Lyon','Royale Union Saint-Gilloise':'Union Saint-Gilloise',
 'SK Rapid Wien':'Rapid Vienna','SK Slavia Praha':'SK Slavia Prague','Sporting Braga':'SC Braga',
 'AFC Ajax':'Ajax Amsterdam','Athletic Club':'Athletic Bilbao','FK Radnički 1923':'FK Radnicki 1923 Kragujevac',
 'FK Žalgiris':'FK Zalgiris Vilnius','Feyenoord':'Feyenoord Rotterdam','SS Virtus':'AC Virtus Acquaviva',
 'Thonon Évian GG FC':'Thonon Évian Grand Genève FC','Internazionale':'Inter Milan',
 'FC Südtirol-Alto Adige':'FC Südtirol','Lille OSC':'LOSC Lille','Man Utd':'Manchester United',
 'Nottm Forest':'Nottingham Forest','Espanol':'RCD Espanyol Barcelona',
}
cm.ALIAS.update(ALIAS36)

# (3) guardia canonica  (4) spareggio crudo, anche sul valore dell'alias
def canonico(nome):
    s = str(nome).translate(TR); s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r'\b(saint|sankt)\b','st',s); s = re.sub(r'[^a-z0-9 ]',' ',s)
    return ' '.join(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())
BLOCCO = {canonico(x) for x in cm.NON_AGGANCIARE}
def crudo(nome):
    s = str(nome).translate(TR); s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return ' '.join(sorted(re.sub(r'[^a-z0-9]+',' ',s).split()))
CRUDO = {int(c):crudo(n) for c,n in zip(CN.club_id, CN.name)}
A3 = cm.Agganciatore()
def candidati(n):
    if canonico(n) in BLOCCO: return []
    c = A3.candidati(n)
    if len(c) <= 1: return c
    for q in (crudo(n), crudo(cm.ALIAS.get(n,''))):
        if not q: continue
        ex=[i for i in c if CRUDO.get(i)==q]
        if len(ex)==1: return ex
    return c
def aggancia(n):
    c=candidati(n); return c[0] if len(c)==1 else None
