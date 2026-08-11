import sys, re, unicodedata as ud
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
from collections import defaultdict
import pandas as pd
from src.data.club_matching import _STOPWORD, _TRADUZIONE, normalizza, Agganciatore
from fonti import fonti
F = fonti()
reg = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")

def token_grezzi(nome):
    s = nome.translate(_TRADUZIONE)
    s = ud.normalize("NFKD", s)
    s = "".join(c for c in s if not ud.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return [t for t in s.split() if t and not t.isdigit()]

print("=== (A) club del REGISTRO che perdono TUTTI i token (invisibili all'indice) ===")
vuoti = [(int(c), n) for c, n in zip(reg.club_id, reg.name) if not normalizza(n)]
print(f"  {len(vuoti)} su {len(reg)}: {vuoti}")
for cid, n in vuoti:
    print(f"    token grezzi di {n!r} = {token_grezzi(n)}  (tutti stopword)")

print("\n=== (A-bis) nomi delle ALTRE fonti che perdono tutti i token ===")
for src, nomi in F.items():
    if src == "club_names.csv.gz": continue
    v = [n for n in sorted(nomi) if not normalizza(n)]
    if v: print(f"  [{src}] {len(v)}: {v}")

print("\n=== (B) quanti club perderebbero tutti i token per OGNI stopword tolta/aggiunta ===")
# per ogni stopword: club in cui e' l'unico token non-stopword-restante? cioe' club
# che RESTANO senza token perche' quella parola e' in _STOPWORD
per_sw = defaultdict(list)
for cid, n in zip(reg.club_id, reg.name):
    tg = token_grezzi(n)
    resta = [t for t in tg if t not in _STOPWORD]
    if not resta and tg:
        for t in set(tg): per_sw[t].append(n)
for w, l in sorted(per_sw.items(), key=lambda x: -len(x[1])):
    print(f"  {w!r}: {len(l)} club  es={l[:4]}")

print("\n=== (C) stopword che sono NOME DISTINTIVO: club dove togliendola causa COLLISIONE ===")
# collisioni nel registro: frozenset uguale per club_id diversi
gr = defaultdict(list)
for cid, n in zip(reg.club_id, reg.name):
    ts = normalizza(n)
    if ts: gr[ts].append((int(cid), n))
coll = {k: v for k, v in gr.items() if len(v) > 1}
print(f"  gruppi di club che collassano sullo stesso insieme di token: {len(coll)}"
      f" ({sum(len(v) for v in coll.values())} club coinvolti su {len(reg)})")
# quante di queste collisioni sono CAUSATE da una stopword (i token grezzi differiscono)
causate = []
for k, v in coll.items():
    grezzi = {frozenset(token_grezzi(n)) for _, n in v}
    if len(grezzi) > 1:
        causate.append((k, v, grezzi))
print(f"  di cui CAUSATE dalle stopword (i token grezzi li distinguerebbero): {len(causate)}")
for k, v, g in causate[:25]:
    diff = set().union(*g) - set.intersection(*[set(x) for x in g])
    print(f"    {sorted(k)} <- {[n for _, n in v]}  differenza={sorted(diff)}")
