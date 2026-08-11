import sys
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as cm
from fonti import fonti

F = {k: v for k, v in fonti().items() if k != "club_names.csv.gz"}
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
    vuoti = sum(1 for x in reg.name if not cm.normalizza(x))
    return out, vuoti

rif, vuoti_rif = misura(BASE)
tot = len(rif)
print(f"riferimento: {sum(1 for v in rif.values() if v=='univoco')}/{tot} univoci, "
      f"{sum(1 for v in rif.values() if v=='ambiguo')} ambigui, "
      f"{sum(1 for v in rif.values() if v=='assente')} assenti; "
      f"club del registro senza token: {vuoti_rif}")

print("\n=== LEAVE-ONE-OUT: togliere una stopword alla volta (Delta univoci sulle 8 fonti) ===")
righe = []
for w in sorted(BASE):
    o, v = misura(BASE - {w})
    d = sum(1 for k in rif if o[k] == "univoco") - sum(1 for k in rif if rif[k] == "univoco")
    cambi = [(k, rif[k], o[k]) for k in rif if rif[k] != o[k]]
    righe.append((d, w, v, cambi))
for d, w, v, cambi in sorted(righe, key=lambda r: (r[0], r[1])):
    if d or cambi or v != vuoti_rif:
        print(f"  senza {w!r}: Delta univoci = {d:+d}, club-senza-token {vuoti_rif}->{v}")
        for k, a, b in cambi[:8]:
            print(f"      {k[1]!r} [{k[0]}]: {a} -> {b}")
neutre = [w for d, w, v, c in righe if d == 0 and not c and v == vuoti_rif]
print(f"\n  stopword NEUTRE sull'universo misurato ({len(neutre)}/{len(BASE)}): {sorted(neutre)}")

cm._STOPWORD = BASE
print("\n=== (c-bis) parole di _STOPWORD che sono NOME PORTANTE di un club nel registro ===")
ag = cm.Agganciatore(reg)
for w in sorted(BASE):
    esatti = reg[reg.name.str.lower().str.split().apply(lambda t: t == [w] if isinstance(t, list) else False)]
    quasi = [n for n in reg.name if isinstance(n, str)
             and w in n.lower().replace(".", " ").split()
             and not (set(cm.normalizza(n)))]
    if len(esatti) or quasi:
        print(f"  {w!r}: nome esatto={list(esatti.name)}, club che restano senza token={quasi}")
