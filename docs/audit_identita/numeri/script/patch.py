import sys; sys.path.insert(0,'.')
from tool import *
import re, unicodedata, json, pandas as pd
import src.data.club_matching as cm

def make_norm(extra_tr=None, togli_apostrofo=False):
    tr = dict(cm._TRADUZIONE)
    if extra_tr:
        for k,v in extra_tr.items(): tr[ord(k)]=v
    def norm(nome):
        if not isinstance(nome,str): return frozenset()
        s = nome.translate(tr)
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
        if togli_apostrofo: s = s.replace("'","").replace("’","")
        s = re.sub(r'\b(saint|sankt)\b','st',s)
        s = re.sub(r'[^a-z0-9 ]',' ',s)
        return frozenset(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())
    return norm

def valuta(norm, etichetta):
    old = cm.normalizza
    cm.normalizza = norm
    Ag = cm.Agganciatore()
    res={}
    for f,ns in FONTI.items():
        st={'univoco':0,'ambiguo':0,'assente':0}
        for n in sorted(ns):
            c=Ag.candidati(n)
            st['univoco' if len(c)==1 else ('ambiguo' if len(c)>1 else 'assente')]+=1
        res[f]=st
    cm.normalizza = old
    print(etichetta, {f:f"{100*v['univoco']/sum(v.values()):.1f}% (amb {v['ambiguo']}, ass {v['assente']})" for f,v in res.items()})
    return Ag

sn=[]
for lg in ['serie_a','premier_league','la_liga','bundesliga','ligue_1']:
    d=pd.read_csv(f'/home/user/Polymarket-oracle/data/{lg}_matches.csv'); sn+=d.home_team.tolist()+d.away_team.tolist()
sofa=pd.read_csv('/home/user/Polymarket-oracle/files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Squadra','Avversario'])
cp=pd.read_csv('/home/user/Polymarket-oracle/data/coppe_2526/partite.csv')
sq=json.load(open('/home/user/Polymarket-oracle/data/squadre_smarkets_2026_27.json'))
FONTI={'snapshot':set(sn),'sofascore':set(sofa.Squadra)|set(sofa.Avversario),
       'coppe':set(cp.casa.dropna())|set(cp.ospite.dropna()),
       'smarkets':set(x for v in sq['per_lega'].values() for x in v)}

valuta(cm.normalizza, 'BASE      ')
valuta(make_norm({'ə':'a','Ə':'a','ħ':'h','Ħ':'h'}), '+char     ')
valuta(make_norm({'ə':'a','Ə':'a','ħ':'h','Ħ':'h'}, togli_apostrofo=True), '+char+apos')
