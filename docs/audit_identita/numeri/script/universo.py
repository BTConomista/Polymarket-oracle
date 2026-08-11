import sys, unicodedata as ud, re
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data.club_matching import _TRADUZIONE

def buttato(c):
    if ord(c) in _TRADUZIONE: return False
    base = "".join(x for x in ud.normalize("NFKD", c) if not ud.combining(x)).lower()
    return not (base and re.fullmatch(r"[a-z0-9 ]+", base))

fam = {"LATIN": [], "GREEK": [], "CYRILLIC": []}
for cp in range(0x20, 0x2500):
    c = chr(cp)
    if not c.isalpha(): continue
    try: n = ud.name(c)
    except ValueError: continue
    f = n.split()[0]
    if f in fam and buttato(c): fam[f].append((c, n))

print(f"LATIN alfabetici che normalizza() BUTTA (U+0020..U+24FF): {len(fam['LATIN'])}")
for c, n in fam["LATIN"]:
    print(f"  U+{ord(c):04X} {c}  {n}")
print(f"\nGREEK: {len(fam['GREEK'])}   CYRILLIC: {len(fam['CYRILLIC'])} (interi alfabeti, non traducibili 1:1)")
