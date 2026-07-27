"""Configurazione delle leghe NUOVE (Bundesliga, Ligue 1) — modulo condiviso.

Questo file e' il "src/config.py + sources.py" provvisorio delle due leghe
nuove: vive nel cantiere finche' il lavoro non viene integrato secondo la
procedura del progetto (allora queste voci si spostano in `src/data/sources.py`
e `src/config.py`, senza cambiare una riga di codice del modello — CLAUDE.md §7).

Contiene:
  - la definizione delle leghe (codice football-data, nome Understat, codice
    paese UEFA, repo/percorsi openfootball, id competizione player-scores);
  - la mappa ALIAS nomi-squadra, verificata per IDENTITA' (vedi
    `verifica_alias()`: ogni fonte deve produrre ESATTAMENTE l'insieme di
    squadre dello snapshot, stagione per stagione);
  - `registra()` che inietta tutto nelle strutture di `src.data.sources` a
    runtime, cosi' il codice di produzione (loader, understat, fixtures,
    player_scores) funziona senza modifiche.

Perche' i percorsi openfootball sono qui e non in sources.py: la Francia usa
uno schema DIVERSO da tutte le altre leghe (`france/{stagione}_fr1.txt`: la
stagione sta nel NOME del file, non in una cartella), quindi la costante
`OPENFOOTBALL_DOMESTIC_URL` non basta — serve un builder per lega.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.sources import League  # noqa: E402

# --------------------------------------------------------------------------- #
# Definizione delle leghe
# --------------------------------------------------------------------------- #
NEW_LEAGUES: dict[str, League] = {
    "bundesliga": League(key="bundesliga", code="D1", name="Bundesliga"),
    "ligue_1": League(key="ligue_1", code="F1", name="Ligue 1"),
}
UNDERSTAT_NAMES = {"bundesliga": "Bundesliga", "ligue_1": "Ligue_1"}
UEFA_CODES = {"bundesliga": "GER", "ligue_1": "FRA"}
PLAYER_SCORES_COMPETITIONS = {"bundesliga": "L1", "ligue_1": "FR1"}
SECOND_TIER_NAMES = {"bundesliga": "2. Bundesliga", "ligue_1": "Ligue 2"}
DOMESTIC_CUP_NAMES = {"bundesliga": "DFB-Pokal", "ligue_1": "Coupe de France"}

# openfootball: URL per (lega, tipo). {lbl} = etichetta stagione "2023-24".
OPENFOOTBALL_URLS: dict[str, dict[str, str]] = {
    "bundesliga": {
        "top": "https://raw.githubusercontent.com/openfootball/deutschland/master/{lbl}/1-bundesliga.txt",
        "second": "https://raw.githubusercontent.com/openfootball/deutschland/master/{lbl}/2-bundesliga2.txt",
        "cup": "https://raw.githubusercontent.com/openfootball/deutschland/master/{lbl}/cup.txt",
    },
    "ligue_1": {
        "top": "https://raw.githubusercontent.com/openfootball/france/master/france/{lbl}_fr1.txt",
        "second": "https://raw.githubusercontent.com/openfootball/france/master/france/{lbl}_fr2.txt",
        "cup": "https://raw.githubusercontent.com/openfootball/france/master/france/{lbl}_frcup.txt",
    },
}

# --------------------------------------------------------------------------- #
# ALIAS nomi squadra -> nome canonico (= nome football-data)
# --------------------------------------------------------------------------- #
# Ogni voce e' stata verificata contro l'elenco dei 29 (Bundesliga) / 30
# (Ligue 1) nomi canonici estratti dalle 9 stagioni football-data, e il
# risultato e' controllato per IDENTITA' stagione per stagione da
# `verifica_alias()`: se un alias mancasse, l'insieme squadre di quella
# stagione non coinciderebbe e il controllo fallirebbe rumorosamente.
# Alcune voci sono DIFENSIVE (varianti senza accenti/con sigla diversa non
# incontrate nei file attuali): non costano nulla e prevengono il bug
# "squadra sconosciuta" se una fonte cambia stile — stessa pratica di
# sources.TEAM_ALIASES. Quelle effettivamente esercitate oggi sono 92 su 103.
BUNDESLIGA_ALIASES: dict[str, str] = {
    # --- Understat -> football-data
    "Arminia Bielefeld": "Bielefeld",
    "Bayer Leverkusen": "Leverkusen",
    "Borussia Dortmund": "Dortmund",
    "Borussia M.Gladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "FC Cologne": "FC Koln",
    "Fortuna Duesseldorf": "Fortuna Dusseldorf",
    "Greuther Fuerth": "Greuther Furth",
    "Hamburger SV": "Hamburg",
    "Hertha Berlin": "Hertha",
    "Nuernberg": "Nurnberg",
    "RasenBallsport Leipzig": "RB Leipzig",
    # --- openfootball (nomi ufficiali tedeschi) e player-scores
    "1. FC Köln": "FC Koln",
    "1. FC Union Berlin": "Union Berlin",
    "1. FC Nürnberg": "Nurnberg",
    "1. FC Heidenheim 1846": "Heidenheim",
    "1. FSV Mainz 05": "Mainz",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Borussia Mönchengladbach": "M'gladbach",
    "Borussia Monchengladbach": "M'gladbach",
    "DSC Arminia Bielefeld": "Bielefeld",
    "FC Bayern München": "Bayern Munich",
    "FC Bayern Munich": "Bayern Munich",
    "Bayern Munchen": "Bayern Munich",
    "FC Augsburg": "Augsburg",
    "FC Heidenheim": "Heidenheim",
    "FC Schalke 04": "Schalke 04",
    "FC St. Pauli": "St Pauli",
    "St. Pauli": "St Pauli",
    "Fortuna Düsseldorf": "Fortuna Dusseldorf",
    "Hannover 96": "Hannover",
    "Hertha BSC": "Hertha",
    "Mainz 05": "Mainz",
    "SC Freiburg": "Freiburg",
    "SC Paderborn 07": "Paderborn",
    "SV Darmstadt 98": "Darmstadt",
    "SV Werder Bremen": "Werder Bremen",
    "SpVgg Greuther Fürth": "Greuther Furth",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "1899 Hoffenheim": "Hoffenheim",
    "TSG Hoffenheim": "Hoffenheim",
    "VfB Stuttgart": "Stuttgart",
    "VfL Bochum 1848": "Bochum",
    "VfL Bochum": "Bochum",
    "VfL Wolfsburg": "Wolfsburg",
    "Bayer 04 Leverkusen Fußball": "Leverkusen",
    # --- coppe europee (openfootball/champions-league): nomi UEFA lunghi
    "Bayern München": "Bayern Munich",
    "Bor. Mönchengladbach": "M'gladbach",
    # --- player-scores: nomi FORMALI del dataset (enumerati fino a zero club
    # non agganciati, come le Fasi 67/59; l'errore di player_scores.league_rosters
    # li elenca tutti insieme, quindi la lista e' completa per costruzione).
    "1. Fußballclub Heidenheim 1846": "Heidenheim",
    "1.FC Heidenheim 1846": "Heidenheim",   # variante Transfermarkt web
    "1.FC Köln": "FC Koln",
    "1.FC Nuremberg": "Nurnberg",
    "1.FC Union Berlin": "Union Berlin",
    "1.FSV Mainz 05": "Mainz",
}
LIGUE1_ALIASES: dict[str, str] = {
    # --- Understat -> football-data
    "Clermont Foot": "Clermont",
    "Paris Saint Germain": "Paris SG",
    "Saint-Etienne": "St Etienne",
    # --- openfootball (nomi ufficiali francesi) e player-scores
    "AC Ajaccio": "Ajaccio",
    "AJ Auxerre": "Auxerre",
    "AS Monaco": "Monaco",
    "AS Monaco FC": "Monaco",
    "AS Saint-Étienne": "St Etienne",
    "AS Saint-Etienne": "St Etienne",
    "Amiens SC": "Amiens",
    "Angers SCO": "Angers",
    "Clermont Foot 63": "Clermont",
    "Dijon FCO": "Dijon",
    "EA Guingamp": "Guingamp",
    "En Avant Guingamp": "Guingamp",
    "ESTAC Troyes": "Troyes",
    "FC Girondins Bordeaux": "Bordeaux",
    "FC Girondins de Bordeaux": "Bordeaux",
    "Girondins Bordeaux": "Bordeaux",
    "FC Lorient": "Lorient",
    "FC Metz": "Metz",
    "FC Nantes": "Nantes",
    "FC Toulouse": "Toulouse",
    "Toulouse FC": "Toulouse",
    "LOSC Lille": "Lille",
    "Lille OSC": "Lille",
    "Le Havre AC": "Le Havre",
    "Havre AC": "Le Havre",        # nome usato nei file Ligue 2 openfootball
    "Montpellier HSC": "Montpellier",
    "Nîmes Olympique": "Nimes",
    "Nimes Olympique": "Nimes",
    "OGC Nice": "Nice",
    "Olympique Lyon": "Lyon",
    "Olympique Lyonnais": "Lyon",
    "Olympique Marseille": "Marseille",
    "Olympique de Marseille": "Marseille",
    "Paris Saint-Germain": "Paris SG",
    "RC Lens": "Lens",
    "RC Strasbourg": "Strasbourg",
    "RC Strasbourg Alsace": "Strasbourg",
    "SM Caen": "Caen",
    "Stade Brestois 29": "Brest",
    "Stade Brestois": "Brest",
    "Stade Rennais FC": "Rennes",
    "Stade Rennais": "Rennes",
    "Stade Reims": "Reims",
    "Stade de Reims": "Reims",
    "FC Paris": "Paris FC",
    # --- coppe europee (openfootball/champions-league): nomi UEFA lunghi
    "Paris Saint-Germain FC": "Paris SG",
    "Racing Club de Lens": "Lens",
}
ALIASES = {"bundesliga": BUNDESLIGA_ALIASES, "ligue_1": LIGUE1_ALIASES}


def registra() -> None:
    """Inietta le leghe nuove nelle strutture di `src.data.sources`.

    STORICO: serviva finche' il lavoro viveva in `cantiere/` e Bundesliga e
    Ligue 1 non erano ancora nel codice di produzione.

    Dall'integrazione (Fase 100) e' un NO-OP verificato: le voci vivono in
    `src/data/sources.py`, `src/config.py` e `src/data/player_scores.py`, e
    ogni `setdefault` qui sotto non tocca piu' nulla (controllato campo per
    campo nell'audit della Fase 101). Non viene rimossa perche' resta un
    CONTROLLO di coerenza a costo zero: il ciclo sugli alias solleva se un
    alias di produzione diverge da quello con cui i 25 script che la chiamano
    sono stati scritti — un fallimento rumoroso e' preferibile a numeri
    prodotti su una tabella di nomi diversa da quella attesa.
    """
    from src.data import player_scores, sources

    for key, lg in NEW_LEAGUES.items():
        sources.LEAGUES.setdefault(key, lg)
        sources.UNDERSTAT_LEAGUES.setdefault(key, UNDERSTAT_NAMES[key])
        sources.UEFA_COUNTRY_CODE.setdefault(key, UEFA_CODES[key])
        sources.SECOND_TIER_NAMES.setdefault(key, SECOND_TIER_NAMES[key])
        sources.DOMESTIC_CUP_COMPETITIONS.setdefault(key, {"cup": DOMESTIC_CUP_NAMES[key]})
        player_scores.COMPETITION_IDS.setdefault(
            PLAYER_SCORES_COMPETITIONS[key], key)
        for name, canon in ALIASES[key].items():
            if name in sources.TEAM_ALIASES and sources.TEAM_ALIASES[name] != canon:
                raise ValueError(
                    f"alias in conflitto con quelli esistenti: {name!r} -> "
                    f"{sources.TEAM_ALIASES[name]!r} vs {canon!r}")
            sources.TEAM_ALIASES[name] = canon


def openfootball_url(league_key: str, season_code: str, kind: str) -> str:
    """URL openfootball per (lega, stagione, tipo in {top, second, cup})."""
    from src.data import sources
    lbl = sources.openfootball_season_label(season_code)
    return OPENFOOTBALL_URLS[league_key][kind].format(lbl=lbl)
