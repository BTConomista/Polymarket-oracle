"""Regressione PROSPETTICA: che succede a un nome misto in cui il cirillico e' VERO?

Simula la fonte da cui i 5 casi vengono davvero (Wikipedia, tappe.csv):
prendo ogni nome del registro che aggancia UNIVOCO oggi e gli antepongo una
parola cirillica autentica (il caso «Динамо Kyiv»). Se dopo la riparazione
l'aggancio non e' piu' univoco (o e' univoco su un altro club), e' una
regressione.
"""
import sys, importlib
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as CM
from V3_patch import normalizza_patched

cn = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")
PREFISSI = ["Динамо", "Спартак", "Зенит", "Локомотив", "Шахтар", "Ολυμπιακός", "ΠΑΟΚ"]

importlib.reload(CM)
A0 = CM.Agganciatore(cn)
nomi = [str(n) for n in cn.name.dropna()]
univoci = [n for n in nomi if len(A0.candidati(n)) == 1]
print("club che agganciano univoco a se stessi:", len(univoci))

prova = [f"{p} {n}" for n in univoci for p in PREFISSI[:2]]
prima = {q: tuple(A0.candidati(q)) for q in prova}

CM.normalizza = normalizza_patched
A1 = CM.Agganciatore(cn)
dopo = {q: tuple(A1.candidati(q)) for q in prova}

def st(c): return "univoco" if len(c) == 1 else ("ambiguo" if len(c) > 1 else "assente")
peggiorati = [q for q in prova if st(prima[q]) == "univoco" and st(dopo[q]) != "univoco"]
cambiati_id = [q for q in prova if st(prima[q]) == "univoco" and st(dopo[q]) == "univoco"
               and prima[q] != dopo[q]]
migliorati = [q for q in prova if st(prima[q]) != "univoco" and st(dopo[q]) == "univoco"]
print(f"nomi misti simulati: {len(prova)}")
print(f"  univoco -> NON univoco (REGRESSIONE): {len(peggiorati)}")
for q in peggiorati[:15]:
    print(f"     {q!r}: {prima[q]} -> {dopo[q]}  token dopo={sorted(normalizza_patched(q))}")
print(f"  univoco -> univoco su ALTRO id: {len(cambiati_id)}")
for q in cambiati_id[:15]: print(f"     {q!r}: {prima[q]} -> {dopo[q]}")
print(f"  non univoco -> univoco: {len(migliorati)}")
for q in migliorati[:15]: print(f"     {q!r}: {prima[q]} -> {dopo[q]}")

# token spuri introdotti: quali finiscono per esistere nell'indice?
inv = A1._inverso
spuri = {}
for q in prova:
    t0 = CM.normalizza.__wrapped__ if False else None
for q in prova[:0]: pass
import collections
c = collections.Counter()
for q in prova:
    importlib_tokens = normalizza_patched(q)
    c.update(t for t in importlib_tokens if len(t) <= 3)
print("\ntoken corti piu' frequenti dopo la riparazione (candidati spuri):", c.most_common(12))
print("quali di questi ESISTONO nell'indice del registro:",
      [t for t, _ in c.most_common(12) if t in inv])
