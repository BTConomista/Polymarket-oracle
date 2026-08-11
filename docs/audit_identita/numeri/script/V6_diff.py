import sys, json
sys.path.insert(0,"/home/user/Polymarket-oracle")
sys.path.insert(0,"/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
from pathlib import Path
import src.data.club_matching as CM
from V3_patch import normalizza_patched
R=Path("/home/user/Polymarket-oracle")
cn=pd.read_csv(R/"files/player_scores/club_names.csv.gz")

def isstr(s): return pd.api.types.is_string_dtype(s) or s.dtype==object
KEYS=("team","casa","ospite","club","squadra","home","away","opponent","nome","avversar")
nomi=set()
paths=sorted(set(list(R.glob("data/**/*.csv"))+list(R.glob("data/**/*.csv.gz"))+list(R.glob("files/**/*.csv"))+list(R.glob("files/**/*.csv.gz"))))
for p in paths:
    try: d=pd.read_csv(p,low_memory=False)
    except Exception: continue
    for c in d.columns:
        if any(x in str(c).lower() for x in KEYS) and isstr(d[c]):
            nomi |= {str(v) for v in d[c].dropna().unique()}
j=json.loads((R/"data/squadre_smarkets_2026_27.json").read_text())
def w(o):
    if isinstance(o,dict): [w(v) for v in o.values()]
    elif isinstance(o,list): [w(v) for v in o]
    elif isinstance(o,str): nomi.add(o)
w(j)
nomi |= set(cn.name.dropna().astype(str))
print("nomi unici sotto test:", len(nomi))

A0=CM.Agganciatore(cn)                      # prima
CM.normalizza = normalizza_patched
A1=CM.Agganciatore(cn)                      # dopo
CM.normalizza = A0.__class__.__module__ and None  # placeholder
import importlib; importlib.reload(CM)      # ripristina il modulo pulito
A0b=CM.Agganciatore(cn)

def stato(c):
    return "univoco" if len(c)==1 else ("ambiguo" if len(c)>1 else "assente")

diff=[]
for n in nomi:
    c0=A0b.candidati(n)
    # per il "dopo" devo usare la normalizza patchata anche dentro candidati
    c1=None
    diff.append((n,c0))
# rifaccio pulito: patch attiva -> A1 usa normalizza_patched perche' candidati chiama CM.normalizza
CM.normalizza = normalizza_patched
A1=CM.Agganciatore(cn)
cambi=[]
for n in nomi:
    c1=A1.candidati(n)
    c0=dict(diff).get(n)
    if c0!=c1: cambi.append((n,c0,c1))
print("\nnomi con candidati CAMBIATI:", len(cambi))
for n,c0,c1 in sorted(cambi)[:80]:
    print(f"  {n!r}: {stato(c0)}{c0} -> {stato(c1)}{c1}")
