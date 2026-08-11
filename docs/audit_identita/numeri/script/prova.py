import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad')
from tool import *
import pandas as pd

SOFA = pd.read_csv('/home/user/Polymarket-oracle/files/sofascore_coppe_europee_2526/giocatori.csv.gz',
                   usecols=['Squadra','Avversario','Competizione','Turno','Data','Campo'])
PART = SOFA.drop_duplicates(['Data','Squadra','Avversario'])[['Data','Competizione','Turno','Squadra','Campo','Avversario']]
G['date'] = pd.to_datetime(G['date'])
G25 = G[G.season==2025]

def sofa_fixtures(nome):
    """Le partite SofaScore di quel nome: data, competizione, avversario (+ suo club_id)."""
    m = PART[(PART.Squadra==nome)|(PART.Avversario==nome)].copy()
    out=[]
    for _,r in m.iterrows():
        avv = r.Avversario if r.Squadra==nome else r.Squadra
        out.append((str(r.Data)[:10], r.Competizione, r.Turno, avv, A.aggancia(avv)))
    return sorted(set(out))

def verifica(nome, cid):
    """Quante partite SofaScore di `nome` trovano riscontro in games.csv per `cid`:
    stessa data (±1g) e stesso avversario agganciato."""
    fx = sofa_fixtures(nome)
    g = G25[(G25.home_club_id==cid)|(G25.away_club_id==cid)].copy()
    ok, tot, dett = 0, 0, []
    for data, comp, turno, avv, avvid in fx:
        if avvid is None: continue
        tot += 1
        d = pd.to_datetime(data, dayfirst=True)
        hit = g[(abs((g.date-d).dt.days)<=1) &
                ((g.home_club_id==avvid)|(g.away_club_id==avvid))]
        if len(hit): ok+=1; dett.append((data,comp,avv,'OK',COMPN.get(hit.iloc[0].competition_id)))
        else: dett.append((data,comp,avv,'--',''))
    return ok, tot, dett

from collections import Counter

def deduci(nome, comp_filtro=('CL','CLQ','EL','ELQ','ECL','ECLQ','UCOL','UKLQ')):
    """IDENTIFICA il club SENZA usare la stringa: per ogni partita SofaScore di
    `nome` con avversario gia' agganciato, cerca in games.csv la gara di quella
    data che coinvolge l'avversario e prende l'ALTRO club. Vota."""
    fx = sofa_fixtures(nome)
    voti = Counter(); usate = 0
    for data, comp, turno, avv, avvid in fx:
        if avvid is None: continue
        d = pd.to_datetime(data, dayfirst=True)
        g = G25[(abs((G25.date-d).dt.days)<=1) &
                ((G25.home_club_id==avvid)|(G25.away_club_id==avvid))]
        if len(g)==0: continue
        usate += 1
        for _,r in g.iterrows():
            altro = r.away_club_id if r.home_club_id==avvid else r.home_club_id
            voti[int(altro)] += 1
    return voti, usate, len(fx)

def nome_di(cid):
    m = CN[CN.club_id==cid]
    return m['name'].iloc[0] if len(m) else '?'
