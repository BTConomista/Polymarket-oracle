import sys, unicodedata as ud, re
sys.path.insert(0, "/home/user/Polymarket-oracle")
sys.path.insert(0, "/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd
import src.data.club_matching as cm
from fonti import fonti

F = fonti()
reg = pd.read_csv("/home/user/Polymarket-oracle/files/player_scores/club_names.csv.gz")

# ---------- LA RIPARAZIONE PROPOSTA ----------
def _base_da_nome_unicode() -> dict[int, str]:
    """Ogni 'LATIN <CAP|SMALL> LETTER X WITH ...' che NFKD non decompone -> 'x'."""
    fuori = {}
    pat = re.compile(r"^LATIN (?:CAPITAL|SMALL) LETTER ([A-Z]) WITH ")
    for cp in range(0x100, 0x2500):
        c = chr(cp)
        if not c.isalpha():
            continue
        try:
            n = ud.name(c)
        except ValueError:
            continue
        base = "".join(x for x in ud.normalize("NFKD", c) if not ud.combining(x)).lower()
        if base and re.fullmatch(r"[a-z0-9]+", base):
            continue           # NFKD basta gia'
        m = pat.match(n)
        if m:
            fuori[cp] = m.group(1).lower()
    return fuori

_ESPLICITI = {
    "ə": "a", "Ə": "a",     # schwa azero: traslitterazione standard, Zire->Zira
    "Ħ": "h", "ħ": "h",     # gia' coperto dal generativo, tenuto per leggibilita'
    "Ŋ": "n", "ŋ": "n", "Ð": "d", "Þ": "th", "Œ": "oe", "ẞ": "ss",
}

TRAD_NUOVA = dict(cm._TRADUZIONE)
TRAD_NUOVA.update(_base_da_nome_unicode())
TRAD_NUOVA.update({ord(k): v for k, v in _ESPLICITI.items()})

# de-confusione degli OMOGLIFI, applicata SOLO ai nomi a scrittura MISTA
_OMOGLIFI = str.maketrans({
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M",
    "О": "O", "Р": "P", "Т": "T", "Х": "X", "а": "a", "е": "e", "о": "o",
    "р": "p", "с": "c", "у": "y", "х": "x",
    "І": "I", "і": "i", "Ј": "J", "ј": "j", "Ѕ": "S", "ѕ": "s", "Ү": "Y",
    "Ғ": "F", "Ԛ": "Q", "ԛ": "q", "Ԝ": "W", "ԝ": "w", "ѐ": "e", "ї": "i",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
    "ο": "o", "ν": "v",
})

def _scritture(s: str) -> set[str]:
    out = set()
    for c in s:
        if not c.isalpha():
            continue
        try:
            out.add(ud.name(c).split()[0])
        except ValueError:
            pass
    return out

def deconfondi(nome: str) -> str:
    sc = _scritture(nome)
    if "LATIN" in sc and sc & {"CYRILLIC", "GREEK"}:
        return nome.translate(_OMOGLIFI)
    return nome

def normalizza_nuova(nome):
    if not isinstance(nome, str):
        return frozenset()
    s = deconfondi(nome).translate(TRAD_NUOVA)
    s = ud.normalize("NFKD", s)
    s = "".join(c for c in s if not ud.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return frozenset(t for t in s.split() if t and t not in cm._STOPWORD and not t.isdigit())

print(f"caratteri aggiunti alla _TRADUZIONE: {len(TRAD_NUOVA) - len(cm._TRADUZIONE)}"
      f"  (da {len(cm._TRADUZIONE)} a {len(TRAD_NUOVA)})")

# ---------- MISURA: aggancio PRIMA e DOPO ----------
def stati(norm):
    orig = cm.normalizza
    cm.normalizza = norm
    try:
        ag = cm.Agganciatore(reg)
        out = {}
        for src, nomi in F.items():
            if src == "club_names.csv.gz":
                continue
            s = {"univoco": 0, "ambiguo": 0, "assente": 0}
            det = {}
            for n in sorted(nomi):
                c = ag.candidati(n)
                k = "univoco" if len(c) == 1 else ("ambiguo" if c else "assente")
                s[k] += 1
                det[n] = (k, tuple(c))
            out[src] = (s, det)
        return out
    finally:
        cm.normalizza = orig

pre, post = stati(cm.normalizza), stati(normalizza_nuova)
print("\n=== AGGANCIO PRIMA / DOPO, fonte per fonte ===")
print(f"{'fonte':34s} {'n':>5s}  {'univoco':>16s} {'ambiguo':>13s} {'assente':>13s}")
for src in pre:
    a, b = pre[src][0], post[src][0]
    n = sum(a.values())
    print(f"{src:34s} {n:5d}  {a['univoco']:6d} -> {b['univoco']:<6d} "
          f"{a['ambiguo']:5d} -> {b['ambiguo']:<5d} {a['assente']:5d} -> {b['assente']:<5d}")
print("\n--- nomi che CAMBIANO stato ---")
for src in pre:
    for n, (k, c) in pre[src][1].items():
        k2, c2 = post[src][1][n]
        if (k, c) != (k2, c2):
            print(f"  [{src}] {n!r}: {k}{list(c)} -> {k2}{list(c2)}")

# ---------- il registro: club che diventano visibili ----------
vuoti_pre = sum(1 for n in reg.name if not cm.normalizza(n))
vuoti_post = sum(1 for n in reg.name if not normalizza_nuova(n))
print(f"\nclub del registro senza token: {vuoti_pre} -> {vuoti_post}")
tok_pre = {int(c): cm.normalizza(n) for c, n in zip(reg.club_id, reg.name)}
tok_post = {int(c): normalizza_nuova(n) for c, n in zip(reg.club_id, reg.name)}
cambiati = [(k, sorted(tok_pre[k]), sorted(tok_post[k])) for k in tok_pre if tok_pre[k] != tok_post[k]]
print(f"club del registro con token CAMBIATI: {len(cambiati)}")
for k, a, b in cambiati:
    print(f"   {k}: {a} -> {b}   ({reg.loc[reg.club_id==k,'name'].iloc[0]!r})")

print("\n=== CONTROLLO DI SICUREZZA: nomi delle fonti con TOKEN cambiati ===")
n_cam = 0
for src, nomi in F.items():
    for n in sorted(nomi):
        a, b = cm.normalizza(n), normalizza_nuova(n)
        if a != b:
            n_cam += 1
            print(f"  [{src}] {n!r}: {sorted(a)} -> {sorted(b)}")
print(f"  totale nomi con token cambiati: {n_cam}")

print("\n=== nuove COLLISIONI nel registro (club diversi, stesso insieme) ===")
from collections import defaultdict
def coll(norm):
    g = defaultdict(list)
    for c, n in zip(reg.club_id, reg.name):
        t = norm(n)
        if t: g[t].append(int(c))
    return {k: v for k, v in g.items() if len(v) > 1}
a, b = coll(cm.normalizza), coll(normalizza_nuova)
print(f"  gruppi in collisione: {len(a)} -> {len(b)}; nuovi: {[k for k in b if k not in a]}")

print("\n=== il caso greco: 'Οlympiacos Ζacharo' (omicron+zeta greche) ===")
cm_ag = cm.Agganciatore(reg)
orig = cm.normalizza
cm.normalizza = normalizza_nuova
ag2 = cm.Agganciatore(reg)
cm.normalizza = orig
for n in ["Οlympiacos Ζacharo", "Olympiacos Zacharo", "Olympiacos", "Cherkashchyna Сherkasy"]:
    print(f"  {n!r}: PRIMA {cm_ag.candidati(n)} {sorted(cm.normalizza(n))} | "
          f"DOPO {ag2.candidati(n)} {sorted(normalizza_nuova(n))}")
