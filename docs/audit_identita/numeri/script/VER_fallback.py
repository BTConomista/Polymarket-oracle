"""Misura la variante 'fallback SIMMETRICO': se dopo le stopword non resta
nulla, si tengono i token grezzi -- e lo si fa anche costruendo l'indice."""
import sys, re, unicodedata
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as cm
from fonti import fonti

reg = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")
F = fonti()
orig = cm.normalizza

def stato(ag, nomi):
    out = {}
    for src, ns in nomi.items():
        for n in sorted(ns):
            c = ag.candidati(n)
            out[(src, n)] = ("univoco", c[0]) if len(c) == 1 else (("ambiguo", None) if c else ("assente", None))
    return out

def riassunto(d, tag):
    from collections import Counter
    c = Counter(v[0] for v in d.values())
    print(f"{tag}: {dict(c)}")

A = stato(cm.Agganciatore(reg), F)
riassunto(A, "PRIMA")

def normalizza2(nome):
    if not isinstance(nome, str):
        return frozenset()
    s = cm._deconfondi(nome).translate(cm._TRADUZIONE)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    grezzi = [t for t in s.split() if t and not t.isdigit()]
    puliti = [t for t in grezzi if t not in cm._STOPWORD]
    return frozenset(puliti) if puliti else frozenset(grezzi)

cm.normalizza = normalizza2
B = stato(cm.Agganciatore(reg), F)
riassunto(B, "DOPO ")
cambi = [(k, A[k], B[k]) for k in A if A[k] != B[k]]
print(f"\nnomi che cambiano: {len(cambi)}")
for k, a, b in cambi[:60]:
    print(f"  [{k[0]}] {k[1]!r}: {a} -> {b}")
