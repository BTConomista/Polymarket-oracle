"""Applica la riparazione PROPOSTA senza toccare il repo: monkeypatch di normalizza."""
import re, unicodedata
import src.data.club_matching as CM

_OMOGLIFI = str.maketrans({
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M",
    "О": "O", "Р": "P", "Т": "T", "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
})

def _scritture(s):
    out = set()
    for c in s:
        if c.isalpha():
            try: out.add(unicodedata.name(c).split()[0])
            except ValueError: pass
    return out

def _deconfondi(nome):
    sc = _scritture(nome)
    if "LATIN" in sc and sc & {"CYRILLIC", "GREEK"}:
        return nome.translate(_OMOGLIFI)
    return nome

def normalizza_patched(nome):
    if not isinstance(nome, str):
        return frozenset()
    s = _deconfondi(nome).translate(CM._TRADUZIONE)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return frozenset(t for t in s.split() if t and t not in CM._STOPWORD and not t.isdigit())

def applica():
    CM.normalizza = normalizza_patched
