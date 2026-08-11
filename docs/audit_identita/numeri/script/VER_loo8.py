import sys
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as cm
from fonti import fonti

F = {k: v for k, v in fonti().items()
     if k not in ("club_names.csv.gz", "carriere_wikipedia/tappe")}
reg = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")
BASE = set(cm._STOPWORD)

def misura(sw):
    cm._STOPWORD = sw
    ag = cm.Agganciatore(reg)
    out = {}
    for src, nomi in F.items():
        for n in sorted(nomi):
            c = ag.candidati(n)
            out[(src, n)] = "univoco" if len(c) == 1 else ("ambiguo" if c else "assente")
    return out

rif = misura(BASE)
tot = len(rif)
print(f"RIFERIMENTO 8 fonti: {sum(1 for v in rif.values() if v=='univoco')}/{tot} univoci, "
      f"{sum(1 for v in rif.values() if v=='ambiguo')} ambigui, "
      f"{sum(1 for v in rif.values() if v=='assente')} assenti")
righe=[]
for w in sorted(BASE):
    o = misura(BASE - {w})
    d = sum(1 for k in rif if o[k]=="univoco") - sum(1 for k in rif if rif[k]=="univoco")
    righe.append((d, w))
for d, w in sorted(righe):
    if d: print(f"  senza {w!r}: Delta = {d:+d}")
print("neutre:", sum(1 for d,w in righe if d==0), "su", len(righe))
