import sys, re, unicodedata as ud
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as cm
from fonti import fonti
F = {k: v for k, v in fonti().items() if k != "club_names.csv.gz"}
reg = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")
BASE = cm.normalizza

def _tok(nome, stop, minlen):
    s = nome.translate(cm._TRADUZIONE)
    s = ud.normalize("NFKD", s)
    s = "".join(c for c in s if not ud.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return frozenset(t for t in s.split()
                     if t and t not in stop and not t.isdigit() and len(t) >= minlen)

def var_fallback(nome):   # se l'insieme e' vuoto, riprova SENZA stopword
    if not isinstance(nome, str): return frozenset()
    t = _tok(nome, cm._STOPWORD, 1)
    return t if t else _tok(nome, frozenset(), 1)

def var_minlen2(nome):    # scarta i token di 1 carattere
    if not isinstance(nome, str): return frozenset()
    return _tok(nome, cm._STOPWORD, 2)

def misura(norm, etichetta):
    cm.normalizza = norm
    ag = cm.Agganciatore(reg)
    st = {}
    for src, nomi in F.items():
        for n in sorted(nomi):
            c = ag.candidati(n)
            st[(src, n)] = ("univoco" if len(c) == 1 else "ambiguo" if c else "assente", tuple(c))
    cm.normalizza = BASE
    return st

rif = misura(BASE, "rif")
for norm, et in [(var_fallback, "FALLBACK senza stopword se vuoto"), (var_minlen2, "SCARTA token di 1 carattere")]:
    o = misura(norm, et)
    du = sum(1 for k in o if o[k][0] == "univoco") - sum(1 for k in rif if rif[k][0] == "univoco")
    cam = [(k, rif[k], o[k]) for k in rif if rif[k] != o[k]]
    print(f"\n=== {et}: Delta univoci = {du:+d}, nomi cambiati = {len(cam)}")
    for k, a, b in cam[:20]:
        print(f"   [{k[0]}] {k[1]!r}: {a[0]}{list(a[1])} -> {b[0]}{list(b[1])}")
    if len(cam) > 20: print(f"   ... e altri {len(cam)-20}")
