import sys, json, pickle
sys.path.insert(0, "/home/user/Polymarket-oracle")
import pandas as pd
from pathlib import Path
R = Path("/home/user/Polymarket-oracle")
def isstr(s): return pd.api.types.is_string_dtype(s) or s.dtype == object
KEYS = ("team","casa","ospite","club","squadra","home","away","opponent","nome","avversar")
nomi = set()
paths = sorted(set(list(R.glob("data/**/*.csv")) + list(R.glob("data/**/*.csv.gz"))
                   + list(R.glob("files/**/*.csv")) + list(R.glob("files/**/*.csv.gz"))))
for p in paths:
    try: d = pd.read_csv(p, low_memory=False)
    except Exception: continue
    for c in d.columns:
        if any(x in str(c).lower() for x in KEYS) and isstr(d[c]):
            nomi |= {str(v) for v in d[c].dropna().unique()}
j = json.loads((R / "data/squadre_smarkets_2026_27.json").read_text())
def w(o):
    if isinstance(o, dict): [w(v) for v in o.values()]
    elif isinstance(o, list): [w(v) for v in o]
    elif isinstance(o, str): nomi.add(o)
w(j)
nomi |= {str(x) for x in pd.read_csv(R / "files/player_scores/club_names.csv.gz").name.dropna()}
pickle.dump(nomi, open("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/NOMI.pkl", "wb"))
print("nomi:", len(nomi))
