import sys
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
from collections import Counter, defaultdict
import pandas as pd
from src.data.club_matching import normalizza, Agganciatore
from fonti import fonti
F = fonti()
reg = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")

print("=== token di UN SOLO carattere generati dai nomi (rumore da punteggiatura/omoglifi) ===")
c = Counter(); esempi = defaultdict(set)
for src, nomi in F.items():
    for n in nomi:
        for t in normalizza(n):
            if len(t) == 1:
                c[t] += 1; esempi[t].add(f"[{src}] {n}")
for t, k in c.most_common():
    print(f"  token {t!r}: {k} nomi  es={sorted(esempi[t])[:4]}")

print("\n=== quanti club del REGISTRO sono raggiungibili da un token monocarattere ===")
ag = Agganciatore(reg)
for t in sorted(c):
    print(f"  {t!r}: {len(ag._inverso.get(t, ()))} club_id nell'indice inverso")
