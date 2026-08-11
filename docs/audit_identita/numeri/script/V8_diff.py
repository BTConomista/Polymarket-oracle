import sys, pickle
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd, importlib
import src.data.club_matching as CM
from V3_patch import normalizza_patched

S = "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/"
nomi = sorted(pickle.load(open(S + "NOMI.pkl", "rb")))
cn = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")

importlib.reload(CM)
A0 = CM.Agganciatore(cn)
prima = {n: tuple(A0.candidati(n)) for n in nomi}

CM.normalizza = normalizza_patched
A1 = CM.Agganciatore(cn)
dopo = {n: tuple(A1.candidati(n)) for n in nomi}

def st(c): return "univoco" if len(c) == 1 else ("ambiguo" if len(c) > 1 else "assente")
cambi = [(n, prima[n], dopo[n]) for n in nomi if prima[n] != dopo[n]]
print("nomi testati:", len(nomi))
print("CAMBIATI:", len(cambi))
for n, a, b in cambi:
    print(f"  {n!r}: {st(a)}{a}  ->  {st(b)}{b}")

def conta(d):
    from collections import Counter
    return Counter(st(v) for v in d.values())
print("\nprima:", conta(prima))
print("dopo :", conta(dopo))
