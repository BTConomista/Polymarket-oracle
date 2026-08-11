import sys, json, unicodedata as ud
sys.path.insert(0,"/home/user/Polymarket-oracle")
import pandas as pd
from pathlib import Path
R = Path("/home/user/Polymarket-oracle")
def scr(c):
    try: return ud.name(c).split()[0]
    except ValueError: return "?"
def isstr(s): return pd.api.types.is_string_dtype(s) or s.dtype==object

fonti={}
def add(k,vals):
    s={str(v) for v in vals if isinstance(v,str) and v.strip()}
    if s: fonti[k]=fonti.get(k,set())|s

KEYS=("team","casa","ospite","club","squadra","home","away","opponent","name","nome","avversar")
paths=[]
for pat in ("data/*.csv","data/**/*.csv","data/**/*.csv.gz","files/**/*.csv","files/**/*.csv.gz"):
    paths += list(R.glob(pat))
paths=sorted(set(paths))
for p in paths:
    try: d=pd.read_csv(p,low_memory=False)
    except Exception: continue
    for c in d.columns:
        if any(x in str(c).lower() for x in KEYS) and isstr(d[c]):
            add(str(p.relative_to(R))+":"+str(c), d[c].dropna())
for p in sorted(R.glob("files/**/*.json"))+sorted(R.glob("data/**/*.json")):
    try: j=json.loads(p.read_text())
    except Exception: continue
    s=set()
    def w(o):
        if isinstance(o,dict): [w(v) for v in o.values()]
        elif isinstance(o,list): [w(v) for v in o]
        elif isinstance(o,str): s.add(o)
    w(j)
    if s: add(str(p.relative_to(R)), s)

tot=set()
for v in fonti.values(): tot|=v
print("colonne/fonti:",len(fonti)," stringhe uniche:",len(tot))
mix=[]
for n in sorted(tot):
    sc={scr(c) for c in n if c.isalpha()}
    if len(sc)>1 and "LATIN" in sc and (sc & {"CYRILLIC","GREEK"}):
        mix.append((n,sorted(sc)))
print("\nMIXED latin+cyr/greek:",len(mix))
for n,sc in mix: print("  ",repr(n),sc)
nonlat=[n for n in tot if any(c.isalpha() for c in n) and not ({scr(c) for c in n if c.isalpha()} & {"LATIN"})]
cg=[n for n in nonlat if {scr(c) for c in n if c.isalpha()} & {"CYRILLIC","GREEK"}]
print("\nnomi SENZA latino ma con cirillico/greco:",len(cg))
for n in sorted(cg)[:60]: print("  ",repr(n))
