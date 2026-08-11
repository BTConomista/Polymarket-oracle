"""Prototipo: spareggio con forma CRUDA + fallback sul VALORE dell'alias."""
import re, unicodedata
from collections import defaultdict
import pandas as pd
from src.data.club_matching import ALIAS, NON_AGGANCIARE, _TRADUZIONE, _STOPWORD, normalizza, CLUB_NAMES

def crudo(nome, tieni_cifre=True):
    if not isinstance(nome, str):
        return frozenset()
    s = nome.translate(_TRADUZIONE)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [t for t in s.split() if t]
    if not tieni_cifre:
        toks = [t for t in toks if not t.isdigit()]
    return frozenset(toks)

class Proto:
    def __init__(self, alias=None, tieni_cifre=True):
        alias = ALIAS if alias is None else alias
        self.tc = tieni_cifre
        df = pd.read_csv(CLUB_NAMES)
        self._per_id, self._crudo_id = {}, {}
        self._inverso = defaultdict(set)
        for cid, nome in zip(df["club_id"], df["name"]):
            ts = normalizza(nome)
            if not ts: continue
            cid = int(cid)
            self._per_id[cid] = ts
            self._crudo_id[cid] = crudo(nome, tieni_cifre)
            for t in ts: self._inverso[t].add(cid)
        self._alias = {normalizza(k): normalizza(v) for k, v in alias.items()}
        self._alias_grezzo = {normalizza(k): v for k, v in alias.items()}

    def candidati(self, nome, spareggio=True, fallback_alias=True):
        if isinstance(nome, str) and nome.strip().lower() in NON_AGGANCIARE:
            return []
        ts0 = normalizza(nome)
        ts = self._alias.get(ts0, ts0)
        if not ts or not all(t in self._inverso for t in ts): return []
        comuni = set.intersection(*[self._inverso[t] for t in ts])
        esatti = [c for c in comuni if self._per_id[c] == ts]
        pool = esatti if esatti else sorted(comuni)
        if spareggio and len(pool) > 1:
            forme = [crudo(nome, self.tc)]
            if fallback_alias and ts0 in self._alias_grezzo:
                forme.append(crudo(self._alias_grezzo[ts0], self.tc))
            for f in forme:
                stretti = [c for c in pool if self._crudo_id[c] == f]
                if len(stretti) == 1:
                    return stretti
        return sorted(pool)

    def aggancia(self, nome, **kw):
        c = self.candidati(nome, **kw)
        return c[0] if len(c) == 1 else None
