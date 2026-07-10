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

# Normalizzazione nomi squadra.
#
# Il provider a volte cambia il nome della stessa squadra tra una stagione e
# l'altra (es. "Hellas Verona" vs "Verona"). Se non li unifichiamo, il modello le
# tratta come squadre DIVERSE e perde tutto lo storico: errore grave e silenzioso.
# Mappa {nome_come_appare: nome_canonico}. Aggiungere qui eventuali nuove varianti.
TEAM_ALIASES: dict[str, str] = {
    "Hellas Verona": "Verona",
    # Varianti usate da Understat (fonte xG). Verificate estraendo TUTTI i nomi
    # distinti delle 9 stagioni e confrontandoli con i nomi canonici: queste tre
    # sono le uniche differenze.
    "AC Milan": "Milan",
    "Parma Calcio 1913": "Parma",
    "SPAL 2013": "Spal",
    # Varianti comuni in altre fonti (difensivo: non costano nulla e prevengono
    # il bug "squadra sconosciuta" se una fonte cambia stile).
    "Internazionale": "Inter",
    "AS Roma": "Roma",
    "SSC Napoli": "Napoli",
}


def canonical_team(name: str) -> str:
    """Nome canonico di una squadra (applica gli alias noti)."""
    return TEAM_ALIASES.get(name, name)


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


# --------------------------------------------------------------------------- #
# Fonte xG: Understat (via mirror GitHub)
# --------------------------------------------------------------------------- #
# La fonte originale (understat.com) non e' raggiungibile dall'ambiente cloud
# (policy di rete, verificato: 403 host_not_allowed). Usiamo lo STESSO repo
# mirror gia' usato per football-data, che pubblica i JSON di lega di Understat
# (datesData/teamsData/playersData) per stagione, aggiornati da un workflow
# giornaliero. In locale basta sostituire UNDERSTAT_URL con quello ufficiale.
UNDERSTAT_OFFICIAL_URL = "https://understat.com/league/{league}/{year}"
UNDERSTAT_MIRROR_URL = (
    "https://raw.githubusercontent.com/Mentaturan/ScoutFootball_for_World_Cup"
    "/main/data/raw/understat/{league}/{year}.json"
)
UNDERSTAT_URL = UNDERSTAT_MIRROR_URL

# Nome del campionato nello stile Understat (chiave interna -> nome Understat).
UNDERSTAT_LEAGUES: dict[str, str] = {
    "serie_a": "Serie_A",
}


def understat_year(season_code: str) -> int:
    """Anno di inizio stagione nello stile Understat ("1718" -> 2017)."""
    return 2000 + int(season_code[:2])


def understat_url(season_code: str, league_key: str = "serie_a") -> str:
    """URL del JSON Understat per una stagione."""
    return UNDERSTAT_URL.format(
        league=UNDERSTAT_LEAGUES[league_key], year=understat_year(season_code)
    )


# --------------------------------------------------------------------------- #
# Fonte valori di mercato e infortuni: Transfermarkt (via mirror GitHub)
# --------------------------------------------------------------------------- #
# Anche transfermarkt.com e' bloccato dall'ambiente cloud. Usiamo il datalake
# GitHub "salimt/football-datasets" (storico valutazioni giocatore, profili,
# infortuni; ~93k giocatori). Tabelle usate:
#   - player_market_value: storico valutazioni (player_id, data, valore in EUR);
#   - player_profiles:     anagrafica (nome, ruolo) per il match sui nomi;
#   - player_injuries:     infortuni con date di inizio/fine.
TRANSFERMARKT_MIRROR_URL = (
    "https://raw.githubusercontent.com/salimt/football-datasets/main"
    "/datalake/transfermarkt/{table}/{table}.csv"
)

TRANSFERMARKT_TABLES: list[str] = [
    "player_market_value",           # storico valutazioni (id, data, EUR)
    "player_profiles",               # anagrafica/ruolo (per il match sui nomi)
    "player_injuries",               # infortuni (date inizio/fine)
    "player_teammates_played_with",  # coppie compagni: amplia la mappa nome->id
]


def transfermarkt_url(table: str) -> str:
    """URL di una tabella del mirror Transfermarkt."""
    if table not in TRANSFERMARKT_TABLES:
        raise KeyError(f"Tabella Transfermarkt sconosciuta: {table}")
    return TRANSFERMARKT_MIRROR_URL.format(table=table)
