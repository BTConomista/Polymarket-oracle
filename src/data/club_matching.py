"""Aggancia i nomi di club di Wikipedia ai `club_id` del nostro dataset.

IL PROBLEMA. Le due fonti chiamano le stesse squadre in modo diverso, e non per
capriccio: noi abbiamo la **denominazione ufficiale** («Associazione Sportiva
Roma», «Olympique Marseille», «SSC Napoli»), Wikipedia quella **corrente**
(«Roma», «Marseille», «Napoli»). Senza un aggancio, i due strati del database
restano due elenchi che parlano delle stesse squadre senza sapere di farlo.

IL METODO, in tre passi e in quest'ordine:
1. **alias curati a mano** (`ALIAS`) — pochi, ciascuno verificato;
2. **corrispondenza esatta** fra insiemi di token normalizzati;
3. **sottoinsieme**: i token di Wikipedia contenuti in quelli nostri
   (`{roma} ⊆ {associazione, sportiva, roma}`), accettata **solo se univoca**.

**Un aggancio ambiguo non si sceglie a caso: si lascia vuoto.** È la lezione di
`TEAM_ALIASES` (§5 del `CLAUDE.md`, caso «Hellas Verona» → «Verona»): un join
che indovina è peggio di un join che dichiara di non sapere, perché l'errore
non si vede più a valle.

RESA MISURATA sul primo lotto: **75,2% univoco**, 3,1% ambiguo, 21,8% senza
aggancio — di cui **il 17% sono squadre riserve** (Real Madrid B, Bayern Munich
II, Jong Ajax), che nel nostro dataset in larga parte **non esistono**: non è
un difetto dell'aggancio, è un'assenza a monte.

⚠️ Due bug pagati scrivendo questo, entrambi silenziosi:
- **`sporting` fra le stopword** annullava «Sporting CP» (che resta senza
  token, quindi senza candidati). Le sigle societarie si tolgono, i nomi
  distintivi no;
- **`ø`, `ł`, `đ` non sono decomposti da NFKD**: «Brøndby» non diventava
  «brondby». Servono in mappatura esplicita.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

CLUB_NAMES = (
    Path(__file__).resolve().parents[2] / "files" / "player_scores" / "club_names.csv.gz"
)

# Caratteri che NFKD non decompone: vanno tradotti a mano.
_TRADUZIONE = str.maketrans({
    "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
    "ß": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "ð": "d", "þ": "th", "ı": "i",
})

# Sigle e parole societarie che NON distinguono un club da un altro.
# ⚠️ Non aggiungere qui parole che fanno parte del nome (es. "sporting").
_STOPWORD = {
    "fc", "cf", "ac", "sc", "as", "ss", "us", "usc", "afc", "cfc", "sv", "tsv",
    "vfb", "vfl", "fk", "sk", "nk", "hk", "bk", "if", "ff", "ca", "cd", "ud",
    "rc", "rcd", "sd", "cs", "cp", "sl", "uc", "acf", "ssc", "ogc", "cfr",
    "club", "calcio", "futebol", "football", "futbol", "fussball", "sport",
    "sportif", "sportiva", "associazione", "asociacion", "de", "di", "del",
    "della", "the", "team",
}

# Alias curati: solo casi VERIFICATI uno per uno contro `club_names.csv.gz`.
# Chiave = nome come appare su Wikipedia, valore = nome nel nostro dataset.
ALIAS: dict[str, str] = {
    "Olympiacos": "Olympiakos Syndesmos Filathlon Peiraios",
    "Rennes": "Stade Rennais FC",
    "Zenit Saint Petersburg": "AO FK Zenit Sankt-Peterburg",
    "SC Freiburg II": "SC Freiburg",          # riserve → prima squadra
    "Bayern Munich II": "Bayern Munich",
    # --- FALSI POSITIVI trovati dall'audit del 01/08/2026. Erano il difetto
    # peggiore dell'aggancio, perche' uscivano etichettati «univoco»: non un
    # mancato aggancio, ma una CERTEZZA sbagliata (regola R6).
    "Brest": "Stade Brestois 29",       # andava alla Dynamo Brest (Bielorussia):
                                        # 0/108 conferme contro lo strato 1, 80/108
                                        # col club giusto
    "PAOK": "Panthessalonikios Athlitikos Omilos Konstantinoupoliton",
                                        # andava al PAOK Kristonis (dilettanti), che
                                        # in `appearances` non compare MAI: 0/50
    "AEK Athens": "Athlitiki Enosi Konstantinoupoleos",   # 41/41 conferme
    # --- Nomi ABBREVIATI di football-data.co.uk (coppe 2025-26, 02/08/2026).
    # Servono per riconoscere i club di SECONDA divisione nelle coppe nazionali:
    # football-data li scrive corti ("QPR", "Sheffield Weds"), il registro
    # player-scores per esteso. Ognuno verificato singolarmente: aggancio
    # univoco (1 solo candidato) contro `club_names.csv.gz`.
    "Blackburn": "Blackburn Rovers",
    "Oxford": "Oxford United",
    "Preston": "Preston North End",
    "QPR": "Queens Park Rangers",
    "Sheffield Weds": "Sheffield Wednesday",
    "West Brom": "West Bromwich Albion",
    "Ceuta": "AD Ceuta FC",
    "Santander": "Racing Santander",
    "Sp Gijon": "Sporting Gijon",
    "Braunschweig": "Eintracht Braunschweig",
    "Karlsruhe": "Karlsruher SC",
    "Nurnberg": "1.FC Nuremberg",
    "Preussen Munster": "Preußen Münster",
    # --- Nomi ABBREVIATI di football-data per la PRIMA divisione 2025-26.
    # Stesso motivo dei precedenti, e stessa verifica (1 solo candidato).
    "Inter": "Inter Milan",
    "Verona": "Hellas Verona",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves": "Wolverhampton Wanderers",
    "Ath Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atletico de Madrid",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "Hamburg": "Hamburger SV",
    "M'gladbach": "Borussia Monchengladbach",
    "Mainz": "1.FSV Mainz 05",
    "Paris SG": "Paris Saint-Germain",
    # ⚠️ I club di Ligue 2 (Annecy, Boulogne, Dunkerque, Grenoble, Laval,
    # Le Mans, Pau, Rodez) NON hanno un alias perche' non esistono nel
    # registro: player-scores non copre ne' la Ligue 2 ne' la Coupe de France.
    # Per la coppa francese la divisione viene da Wikipedia, che la scrive
    # accanto a ogni nome (vedi `coupe_de_france.py`).
}

# Nomi che NON vanno agganciati: sono squadre RISERVE, che nel nostro dataset in
# larga parte non esistono. Agganciarle alla prima squadra e' peggio di lasciarle
# vuote — attribuisce presenze di terza divisione al club maggiore. `normalizza`
# torna un frozenset, quindi «Bilbao Athletic» e «Athletic Bilbao» collassano
# sullo stesso insieme: senza questo elenco l'ordine dei token non protegge.
NON_AGGANCIARE: frozenset[str] = frozenset({
    "bilbao athletic", "real madrid castilla", "barcelona atletic",
    "barcelona b", "real madrid b", "atletico madrid b", "sevilla atletico",
    "villarreal b", "celta b", "athletic bilbao b",
    # football-data chiama cosi' la riserva della Real Sociedad, che gioca in
    # Segunda: stesso motivo di tutte le altre, non va agganciata alla prima.
    "sociedad b", "real sociedad b",
})


def normalizza(nome: str) -> frozenset[str]:
    """Nome di club → insieme di token confrontabile."""
    if not isinstance(nome, str):
        return frozenset()
    s = nome.translate(_TRADUZIONE)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\b(saint|sankt)\b", "st", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return frozenset(
        t for t in s.split() if t and t not in _STOPWORD and not t.isdigit()
    )


class Agganciatore:
    """Costruisce l'indice una volta e aggancia molti nomi in fretta."""

    def __init__(self, club_names: pd.DataFrame | None = None) -> None:
        if club_names is None:
            club_names = pd.read_csv(CLUB_NAMES)
        self.nomi = club_names
        self._per_id: dict[int, frozenset[str]] = {}
        self._inverso: dict[str, set[int]] = defaultdict(set)
        for cid, nome in zip(club_names["club_id"], club_names["name"]):
            ts = normalizza(nome)
            if not ts:
                continue
            self._per_id[int(cid)] = ts
            for t in ts:
                self._inverso[t].add(int(cid))
        self._alias = {normalizza(k): normalizza(v) for k, v in ALIAS.items()}

    def candidati(self, nome: str) -> list[int]:
        """I `club_id` compatibili. Lista vuota = nessuno; >1 = ambiguo."""
        if isinstance(nome, str) and nome.strip().lower() in NON_AGGANCIARE:
            return []
        ts = normalizza(nome)
        ts = self._alias.get(ts, ts)
        if not ts or not all(t in self._inverso for t in ts):
            return []
        comuni = set.intersection(*[self._inverso[t] for t in ts])
        esatti = [c for c in comuni if self._per_id[c] == ts]
        return sorted(esatti) if esatti else sorted(comuni)

    def aggancia(self, nome: str) -> int | None:
        """Il `club_id`, **solo se univoco**. `None` se assente o ambiguo."""
        c = self.candidati(nome)
        return c[0] if len(c) == 1 else None

    def aggancia_serie(self, nomi: pd.Series) -> pd.DataFrame:
        """Aggancia una colonna intera, con lo **stato** di ogni riga.

        Lo stato non è decorazione: `ambiguo` e `assente` sono esiti diversi e
        vanno trattati diversamente a valle (uno è un limite dell'aggancio,
        l'altro un'assenza nel dataset a monte).
        """
        unici = {n: self.candidati(n) for n in nomi.dropna().unique()}
        stato, ident = [], []
        for n in nomi:
            c = unici.get(n, [])
            if len(c) == 1:
                stato.append("univoco")
                ident.append(c[0])
            elif len(c) > 1:
                stato.append("ambiguo")
                ident.append(None)
            else:
                stato.append("assente")
                ident.append(None)
        return pd.DataFrame(
            {"club_id_agganciato": ident, "aggancio": stato}, index=nomi.index
        )
