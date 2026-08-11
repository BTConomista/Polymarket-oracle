import sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd, re, unicodedata
from src.data.club_matching import Agganciatore, normalizza, _TRADUZIONE

CN = pd.read_csv('/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz')
CLUBS = pd.read_csv('/home/user/Polymarket-oracle/files/player_scores/clubs.csv.gz')
G = pd.read_csv('/home/user/Polymarket-oracle/files/player_scores/games.csv.gz')
COMP = pd.read_csv('/home/user/Polymarket-oracle/files/player_scores/competitions.csv.gz')
COMPN = dict(zip(COMP.competition_id, COMP.name))
COMPC = dict(zip(COMP.competition_id, COMP.country_name))
A = Agganciatore()

def piatto(s):
    s = str(s).translate(_TRADUZIONE)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9 ]',' ', s)

CN['_p'] = CN['name'].map(piatto)
CN['_t'] = CN['name'].map(normalizza)

def cerca(frag):
    """Sottostringa piatta sui nomi del registro."""
    f = piatto(frag).strip()
    m = CN[CN['_p'].str.contains(re.escape(f), regex=True, na=False)]
    return m[['club_id','name','domestic_competition_id']]

def token(nome, minov=1):
    """Club che condividono almeno minov token col nome dato."""
    ts = normalizza(nome)
    out=[]
    for cid,nm,tt in zip(CN.club_id, CN.name, CN._t):
        ov = len(ts & tt)
        if ov>=minov: out.append((ov,cid,nm))
    return sorted(out, reverse=True)[:25]

def storia(cid, ultime=None):
    """Competizioni e stagioni in cui quel club_id compare in games.csv."""
    g = G[(G.home_club_id==cid)|(G.away_club_id==cid)]
    if len(g)==0: return 'MAI in games.csv'
    r = g.groupby('competition_id').agg(n=('game_id','size'), s0=('season','min'), s1=('season','max'))
    r['nome'] = [COMPN.get(i,i) for i in r.index]
    r['paese'] = [COMPC.get(i) for i in r.index]
    return r.sort_values('n', ascending=False)

def info(cid):
    row = CLUBS[CLUBS.club_id==cid]
    if len(row)==0: return None
    r=row.iloc[0]
    return dict(club_id=cid, name=r['name'], dom=r.domestic_competition_id, stadio=r.stadium_name, last=r.last_season, url=r.url)
