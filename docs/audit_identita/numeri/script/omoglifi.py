import sys, unicodedata as ud, re
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
from src.data.club_matching import normalizza
from fonti import fonti
F = fonti()

def script(c):
    try: n = ud.name(c)
    except ValueError: return "?"
    return n.split()[0]

print("=== (1) MIXED-SCRIPT: nomi che mescolano LATIN e un altro alfabeto ===")
for src, nomi in F.items():
    for n in sorted(nomi):
        sc = {script(c) for c in n if c.isalpha()}
        if len(sc) > 1:
            print(f"  [{src}] {n!r}  script={sorted(sc)}  -> {sorted(normalizza(n))}")

print("\n=== (2) nomi che normalizza() riduce a INSIEME VUOTO ===")
for src, nomi in F.items():
    v = [n for n in nomi if not normalizza(n)]
    if v: print(f"  [{src}] {len(v)}: {v}")

print("\n=== (3) nomi con >=1 carattere alfabetico BUTTATO (token spezzato/perso) ===")
def buttati(n):
    out = []
    for c in n:
        if ord(c) < 128 or not c.isalpha(): continue
        s = n_c = c
        from src.data.club_matching import _TRADUZIONE
        if ord(c) in _TRADUZIONE: continue
        d = ud.normalize("NFKD", c)
        base = "".join(x for x in d if not ud.combining(x)).lower()
        if base and re.fullmatch(r"[a-z0-9 ]+", base): continue
        out.append(c)
    return out
tot = 0
for src, nomi in F.items():
    hit = [(n, buttati(n)) for n in sorted(nomi) if buttati(n)]
    tot += len(hit)
    if hit:
        print(f"  --- {src}: {len(hit)} nomi")
        for n, b in hit:
            print(f"      {n!r} butta {b} -> {sorted(normalizza(n))}")
print(f"  TOTALE nomi colpiti: {tot}")

print("\n=== (4) apostrofo tipografico: si comporta come l'ASCII? ===")
for a in ["CD l’Alcora", "CD l'Alcora", "Club Atlético Newell’s Old Boys", "France d’Aizenay"]:
    print(f"   {a!r} -> {sorted(normalizza(a))}")
