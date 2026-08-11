import sys, json, re, unicodedata, collections
sys.path.insert(0,'/home/user/Polymarket-oracle')
import pandas as pd
import src.data.club_matching as cm

U=json.load(open('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/VER_U.json'))
print(collections.Counter(f for v in U.values() for f in v))

def canonico(nome):
    s=str(nome).translate(cm._TRADUZIONE)
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c)).lower()
    s=re.sub(r'\b(saint|sankt)\b','st',s)
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    return ' '.join(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())

BLOCCO={canonico(x) for x in cm.NON_AGGANCIARE}
print('blocklist canonica:', sorted(BLOCCO))
print('collisioni canoniche fra voci blocklist:', len(cm.NON_AGGANCIARE), '->', len(BLOCCO))

A=cm.Agganciatore()
CL=pd.read_csv('files/player_scores/clubs.csv.gz')
nome_di=dict(zip(CL.club_id,CL.name))
dom=dict(zip(CL.club_id,CL.domestic_competition_id))

prima={n:A.candidati(n) for n in U}
# DOPO: guardia canonica
orig=cm.NON_AGGANCIARE
def candidati_dopo(nome):
    if isinstance(nome,str) and canonico(nome) in BLOCCO: return []
    ts=cm.normalizza(nome); ts=A._alias.get(ts,ts)
    if not ts or not all(t in A._inverso for t in ts): return []
    comuni=set.intersection(*[A._inverso[t] for t in ts])
    esatti=[c for c in comuni if A._per_id[c]==ts]
    return sorted(esatti) if esatti else sorted(comuni)
dopo={n:candidati_dopo(n) for n in U}

diff=[(n,prima[n],dopo[n],U[n]) for n in U if prima[n]!=dopo[n]]
print(f'\nnomi con esito cambiato: {len(diff)}')
for n,a,b,f in sorted(diff):
    print(f'  {n!r:40} {f}  {a}->{b}  {[nome_di.get(x) for x in a]} dom={[dom.get(x) for x in a]}')
