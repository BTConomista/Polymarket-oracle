"""Configurazione delle fonti dati.

Questo e' l'UNICO punto in cui sono codificati gli URL e l'elenco delle stagioni.
Per aggiungere un campionato, una stagione o cambiare provider (es. tornare alla
fonte ufficiale football-data.co.uk quando raggiungibile) basta modificare qui,
senza toccare il resto del codice.

Formato dei dati: schema "football-data.co.uk" (colonne Date, HomeTeam, AwayTeam,
FTHG, FTAG, FTR, quote dei bookmaker, ecc.). Il mirror usato replica esattamente
quel formato.
"""

from __future__ import annotations

from dataclasses import dataclass

# Provider di default.
#
# La fonte originale (https://www.football-data.co.uk/mmz4281/{season}/{code}.csv)
# non e' raggiungibile dall'ambiente cloud in cui il progetto viene sviluppato
# (policy di rete). Usiamo un mirror su GitHub che replica lo STESSO formato e le
# STESSE colonne. Girando il progetto in locale si puo' semplicemente sostituire
# BASE_URL con quello ufficiale.
OFFICIAL_BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
MIRROR_BASE_URL = (
    "https://raw.githubusercontent.com/Mentaturan/ScoutFootball_for_World_Cup"
    "/main/data/raw/football_data/{season}/{code}.csv"
)

BASE_URL = MIRROR_BASE_URL


@dataclass(frozen=True)
class League:
    """Un campionato disponibile.

    Attributes:
        key: identificatore interno usato nel codice/CLI (es. "serie_a").
        code: codice della fonte football-data (es. "I1" = Serie A italiana).
        name: nome leggibile.
    """

    key: str
    code: str
    name: str


# Campionati supportati. Aggiungerne uno = aggiungere una riga qui.
LEAGUES: dict[str, League] = {
    "serie_a": League(key="serie_a", code="I1", name="Serie A"),
    # Esempi pronti per il futuro (stesso provider, stesso formato):
    # "premier_league": League("premier_league", "E0", "Premier League"),
    # "la_liga":        League("la_liga",        "SP1", "La Liga"),
}

# Le 9 stagioni piu' recenti di Serie A, codificate come nel provider:
# "1718" = stagione 2017-2018, ... "2526" = stagione 2025-2026 (l'ultima conclusa).
SEASONS: list[str] = [
    "1718", "1819", "1920", "2021", "2122",
    "2223", "2324", "2425", "2526",
]


def season_label(season_code: str) -> str:
    """Converte "2425" -> "2024-2025" per output leggibili."""
    start = int(season_code[:2])
    # Le stagioni del dataset partono dal 2017; assumiamo l'era 2000+.
    year = 2000 + start
    return f"{year}-{year + 1}"


def csv_url(season_code: str, league: League) -> str:
    """URL del CSV per una data stagione e campionato."""
    return BASE_URL.format(season=season_code, code=league.code)
