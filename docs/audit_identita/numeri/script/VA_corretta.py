"""Versione CORRETTA: de-confusione per PAROLA, non per nome."""
import re, unicodedata
import src.data.club_matching as CM

_OMOGLIFI = CM._OMOGLIFI if hasattr(CM, "_OMOGLIFI") else None

_MAPPA = {
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M",
    "О": "O", "Р": "P", "Т": "T", "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
}
_TAB = str.maketrans(_MAPPA)

def _scrittura(c):
    try:
        return unicodedata.name(c).split()[0]
    except ValueError:
        return "?"

def _deconfondi2(nome: str) -> str:
    """Traduce solo le PAROLE miste in cui il non-latino e' un omoglifo noto.

    Una parola interamente cirillica/greca ('ВІК', 'ΠΑΟΚ', 'Динамо') e' TESTO,
    non un omoglifo: tradurla lettera per lettera inventa un token.
    """
    def f(m):
        p = m.group(0)
        sc = {_scrittura(c) for c in p}
        if "LATIN" not in sc:
            return p                      # parola straniera vera: non si tocca
        est = [c for c in p if _scrittura(c) in {"CYRILLIC", "GREEK"}]
        if not est or any(c not in _MAPPA for c in est):
            return p                      # nessun omoglifo, o non tutti noti
        return p.translate(_TAB)
    return re.sub(r"[^\W\d_]+", f, nome, flags=re.UNICODE)

def normalizza2(nome):
    if not isinstance(nome, str):
        return frozenset()
    s = _deconfondi2(nome).translate(CM._TRADUZIONE)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return frozenset(t for t in s.split() if t and t not in CM._STOPWORD and not t.isdigit())
