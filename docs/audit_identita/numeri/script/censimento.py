import sys, unicodedata as ud
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
from collections import defaultdict
from src.data.club_matching import _TRADUZIONE, normalizza
from fonti import fonti

F = fonti()

def esito(c: str) -> str:
    """Che fine fa il carattere `c` dentro normalizza()."""
    if ord(c) in _TRADUZIONE:
        return "tradotto"
    d = ud.normalize("NFKD", c)
    base = "".join(x for x in d if not ud.combining(x)).lower()
    if base and all("a" <= x <= "z" or "0" <= x <= "9" or x == " " for x in base):
        return "decomposto"
    return "BUTTATO"

occ = defaultdict(lambda: defaultdict(set))   # char -> fonte -> nomi
for src, nomi in F.items():
    for n in nomi:
        for c in n:
            if ord(c) > 127:
                occ[c][src].add(n)

righe = []
for c, per_src in occ.items():
    e = esito(c)
    alfab = ud.category(c).startswith("L")
    tot = sum(len(v) for v in per_src.values())
    righe.append((e, alfab, c, tot, per_src))

print("=== CARATTERI NON-ASCII, per esito ===")
for e in ("BUTTATO", "tradotto", "decomposto"):
    sel = [r for r in righe if r[0] == e]
    print(f"\n--- {e}: {len(sel)} caratteri distinti ---")
    for _, alfab, c, tot, per_src in sorted(sel, key=lambda r: -r[3]):
        try: nome = ud.name(c)
        except ValueError: nome = "?"
        marchio = "LETTERA" if alfab else "       "
        esempi = sorted({n for v in per_src.values() for n in v})[:3]
        print(f"  {'U+%04X'%ord(c)} {c!r:6s} {marchio} occ={tot:5d} {nome[:42]:42s} "
              f"fonti={sorted(per_src)} es={esempi}")
