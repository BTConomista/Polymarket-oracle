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
# (policy di rete). Si usava un mirror su GitHub con lo STESSO formato.
#
# ATTENZIONE — MIRROR SPARITO (verificato 2026-07, Fase 14): il repo
# Mentaturan/... non esiste piu' su GitHub (404 reale, fuori dal proxy); vale
# anche per l'xG Understat (UNDERSTAT_URL, stesso repo). Il progetto NON ne
# dipende per i calcoli: lo snapshot congelato e' versionato, e i CSV grezzi
# ORIGINALI football-data (tutte le colonne quote) sono congelati in
# data/football_data_raw/ (versionata) e `python scripts/_restore_raw_cache.py`
# ricostruisce da li' la cache data/raw/.
# AGGIORNAMENTO Fase 100/101-bis: la fonte UFFICIALE e' tornata raggiungibile
# anche da qui (200 verificato; e' cosi' che Bundesliga e Ligue 1 sono state
# scaricate). Il mirror invece resta 404. Fino alla Fase 101-bis il default era
# ancora il mirror morto: `--refresh` puntava all'unica delle due URL che NON
# risponde. Ora il default e' l'ufficiale, e il mirror resta solo come
# riferimento storico del formato.
OFFICIAL_BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
MIRROR_BASE_URL = (  # MORTO (404, riverificato alla Fase 101-bis)
    "https://raw.githubusercontent.com/Mentaturan/ScoutFootball_for_World_Cup"
    "/main/data/raw/football_data/{season}/{code}.csv"
)

BASE_URL = OFFICIAL_BASE_URL


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
#
# Premier League e La Liga (Fase 54): il provider originale non e' raggiungibile
# (403 dal proxy) e il mirror storico e' sparito (vedi sopra). I dati grezzi
# sono stati CARICATI a mano come "bundle" JSON in files/ (football-data +
# Understat, 9 stagioni ciascuna, 2017-18 -> 2025-26): stesso formato/era della
# Serie A. Da questi bundle si costruisce lo snapshot congelato
# data/{league}_matches.csv (scripts/build_league_snapshot.py), esattamente come
# per la Serie A. Nessuna dipendenza di rete: 100% offline e riproducibile.
#
# Bundesliga e Ligue 1: aggiunte dopo che il provider originale e' tornato
# raggiungibile (200), quindi SENZA bundle manuali — scaricate direttamente da
# football-data (D1/F1) e Understat, e verificate riga per riga contro la fonte.
LEAGUES: dict[str, League] = {
    "serie_a": League(key="serie_a", code="I1", name="Serie A"),
    "premier_league": League(key="premier_league", code="E0", name="Premier League"),
    "la_liga": League(key="la_liga", code="SP1", name="La Liga"),
    "bundesliga": League(key="bundesliga", code="D1", name="Bundesliga"),
    "ligue_1": League(key="ligue_1", code="F1", name="Ligue 1"),
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
    # Varianti usate dal calendario di club completo (openfootball, vedi
    # fixtures.py): nomi ESTESI di coppa/Europa. Enumerate estraendo TUTTI i nomi
    # (ITA) delle competizioni europee 2017-18 -> 2025-26 e tutti i nomi della
    # Coppa Italia 2020-21 -> 2024-25, poi confrontate coi 32 nomi canonici dello
    # snapshot. Ogni club di Serie A comparso nelle fonti e' qui: i mancati
    # aggancio vengono comunque LOGGATi da fixtures.py (mai ignorati in silenzio).
    "ACF Fiorentina": "Fiorentina",
    "Atalanta BC": "Atalanta",
    "Bologna FC": "Bologna",
    "Bologna FC 1909": "Bologna",
    "FC Internazionale Milano": "Inter",
    "Juventus FC": "Juventus",
    "Lazio Roma": "Lazio",
    "SS Lazio": "Lazio",
    "AC Monza": "Monza",
    "AC Pisa": "Pisa",
    "Pisa SC": "Pisa",
    "Benevento Calcio": "Benevento",
    "Brescia Calcio": "Brescia",
    "Cagliari Calcio": "Cagliari",
    "Como 1907": "Como",
    "Empoli FC": "Empoli",
    "FC Crotone": "Crotone",
    "Frosinone Calcio": "Frosinone",
    "Genoa CFC": "Genoa",
    "Sassuolo Calcio": "Sassuolo",
    "Spezia Calcio": "Spezia",
    "Torino FC": "Torino",
    "US Cremonese": "Cremonese",
    "US Lecce": "Lecce",
    "US Salernitana 1919": "Salernitana",
    "Udinese Calcio": "Udinese",
    "Venezia FC": "Venezia",
    "SPAL 2013 Ferrara": "Spal",
    # --- Premier League (Fase 54): nomi Understat -> nomi football-data (canonici).
    # Le 6 uniche differenze, verificate estraendo TUTTI i nomi delle 9 stagioni da
    # entrambe le fonti (files/*_premier_league_bundle.json) e confrontandoli.
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "West Bromwich Albion": "West Brom",
    "Wolverhampton Wanderers": "Wolves",
    # --- La Liga (Fase 54): le 11 differenze Understat -> football-data. Ogni
    # coppia verificata per IDENTITA' (non per ordinamento): es. "Atletico Madrid"
    # (Ath Madrid) e' distinta da "Real Madrid", presente identica in entrambe.
    "Athletic Club": "Ath Bilbao",
    "Atletico Madrid": "Ath Madrid",
    "Real Betis": "Betis",
    "Celta Vigo": "Celta",
    "Espanyol": "Espanol",
    "SD Huesca": "Huesca",
    "Deportivo La Coruna": "La Coruna",
    "Real Oviedo": "Oviedo",
    "Real Sociedad": "Sociedad",
    "Real Valladolid": "Valladolid",
    "Rayo Vallecano": "Vallecano",
    # --- Calendario di club (openfootball, Fase 59): varianti "FC/CF/Hotspur"
    # usate nelle competizioni europee/coppe nazionali per i club di Premier
    # League e La Liga, generalizzando la Fase 4e (Coppa Italia/coppe europee)
    # oltre la sola Serie A. Enumerate estraendo TUTTI i nomi (ENG/ESP) delle
    # competizioni europee e delle coppe nazionali 2018-19 -> 2024-25 e
    # confrontandole coi 32+32 nomi canonici dei due snapshot.
    "Liverpool FC": "Liverpool",
    "Chelsea FC": "Chelsea",
    "Tottenham Hotspur": "Tottenham",
    "Tottenham Hotspur FC": "Tottenham",
    "West Ham United": "West Ham",
    "Arsenal FC": "Arsenal",
    "Manchester City FC": "Man City",
    "Manchester United FC": "Man United",
    "Newcastle United FC": "Newcastle",
    "Leicester City": "Leicester",
    "Everton FC": "Everton",
    "Aston Villa FC": "Aston Villa",
    "Brighton & Hove Albion": "Brighton",
    "Crystal Palace FC": "Crystal Palace",
    "Wolverhampton Wanderers FC": "Wolves",
    "Southampton FC": "Southampton",
    "Leeds United": "Leeds",
    "Fulham FC": "Fulham",
    "Brentford FC": "Brentford",
    "Burnley FC": "Burnley",
    "Nottingham Forest FC": "Nott'm Forest",
    "AFC Bournemouth": "Bournemouth",
    "FC Barcelona": "Barcelona",
    "Real Madrid CF": "Real Madrid",
    "Sevilla FC": "Sevilla",
    "Atlético Madrid": "Ath Madrid",
    "Atletico de Madrid": "Ath Madrid",
    "Club Atlético de Madrid": "Ath Madrid",
    "Athletic Club de Bilbao": "Ath Bilbao",
    "Real Betis Balompié": "Betis",
    "Villarreal CF": "Villarreal",
    "Valencia CF": "Valencia",
    "RC Celta de Vigo": "Celta",
    "RCD Espanyol de Barcelona": "Espanol",
    "CA Osasuna": "Osasuna",
    "Getafe CF": "Getafe",
    "SD Eibar": "Eibar",
    "Real Sociedad de Fútbol": "Sociedad",
    "Granada CF": "Granada",
    "Girona FC": "Girona",
    # --- Dataset player-scores (Fase 67, files/player_scores/): nomi FORMALI
    # dei club usati da clubs.csv, enumerati contro gli snapshot fino a zero
    # club non agganciati (stesso metodo delle Fasi 54/59).
    "Associazione Sportiva Roma": "Roma",
    "Bologna Football Club 1909": "Bologna",
    "Chievo Verona": "Chievo",
    "FC Empoli": "Empoli",
    "Inter Milan": "Inter",
    "Pisa Sporting Club": "Pisa",
    "SPAL": "Spal",
    "Società Sportiva Lazio S.p.A.": "Lazio",
    "UC Sampdoria": "Sampdoria",
    "US Sassuolo": "Sassuolo",
    "Cardiff City": "Cardiff",
    "Huddersfield Town": "Huddersfield",
    "Ipswich Town": "Ipswich",
    "Luton Town": "Luton",
    "Norwich City": "Norwich",
    "Stoke City": "Stoke",
    "Sunderland AFC": "Sunderland",
    "Swansea City": "Swansea",
    "Watford FC": "Watford",
    "Athletic Bilbao": "Ath Bilbao",
    "Atlético de Madrid": "Ath Madrid",
    "CD Leganés": "Leganes",
    "Celta de Vigo": "Celta",
    "Cádiz CF": "Cadiz",
    "Deportivo Alavés": "Alaves",
    "Deportivo de La Coruña": "La Coruna",
    "Elche CF": "Elche",
    "Levante UD": "Levante",
    "Málaga CF": "Malaga",
    "RCD Espanyol Barcelona": "Espanol",
    "RCD Mallorca": "Mallorca",
    "Real Valladolid CF": "Valladolid",
    "UD Almería": "Almeria",
    "UD Las Palmas": "Las Palmas",
    # --- Calendari preludio 2016-17 (Fase 68): varianti del file openfootball
    # espana/2016-17 non ancora coperte dagli alias sopra.
    "CD Alavés": "Alaves",
    "RC Celta": "Celta",
    "Espanyol Barcelona": "Espanol",
    "Deportivo La Coruña": "La Coruna",
    # --- Bundesliga: nomi Understat / openfootball / UEFA /
    # player-scores -> nome canonico (= nome football-data).
    # Verificati per IDENTITA' sui nomi distinti delle 9 stagioni di
    # ogni fonte; i mancati aggancio vengono comunque loggati, mai
    # ignorati in silenzio.
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
    "Bayern München": "Bayern Munich",
    "Bor. Mönchengladbach": "M'gladbach",
    "1. Fußballclub Heidenheim 1846": "Heidenheim",
    "1.FC Heidenheim 1846": "Heidenheim",
    "1.FC Köln": "FC Koln",
    "1.FC Nuremberg": "Nurnberg",
    "1.FC Union Berlin": "Union Berlin",
    "1.FSV Mainz 05": "Mainz",
    # --- Ligue 1: nomi Understat / openfootball / UEFA /
    # player-scores -> nome canonico (= nome football-data).
    # Verificati per IDENTITA' sui nomi distinti delle 9 stagioni di
    # ogni fonte; i mancati aggancio vengono comunque loggati, mai
    # ignorati in silenzio.
    "Clermont Foot": "Clermont",
    "Paris Saint Germain": "Paris SG",
    "Saint-Etienne": "St Etienne",
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
    "Havre AC": "Le Havre",
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
    "Paris Saint-Germain FC": "Paris SG",
    "Racing Club de Lens": "Lens",
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
# Fonte xG: Understat
# --------------------------------------------------------------------------- #
# STORIA (aggiornata Fase 104, docs/MANUALE_SOPRAVVIVENZA.md). Il mirror
# GitHub (Mentaturan/ScoutFootball_for_World_Cup, STESSO repo usato per
# football-data, vedi sopra) e' MORTO: 404 reale, riverificato in modo
# indipendente il 2026-07-28 (curl diretto e via WebFetch, non un problema di
# proxy/sessione: raw.githubusercontent.com risponde 200 su un repo vero come
# torvalds/linux). La fonte ufficiale (understat.com) e' invece raggiungibile
# dalla Fase 100 (era 403 prima), ma NON sull'URL "pagina" (quella e' resa via
# JS lato client, il body HTML non contiene i dati) -- serve l'endpoint XHR
# interno, GET /main/getLeagueData/{league}/{year} con header
# X-Requested-With: XMLHttpRequest (senza -> 404) e risposta SEMPRE gzip
# (Content-Encoding: gzip anche senza Accept-Encoding, va decompressa a mano
# con urllib -- vedi understat.download_season). Stessa struttura JSON del
# mirror (teams/players/dates): verificato Fase 104 scaricando live Ligue 1
# 2025 e Bundesliga 2024 e riparsandoli con parse_season_xg.
UNDERSTAT_OFFICIAL_URL = "https://understat.com/main/getLeagueData/{league}/{year}"
UNDERSTAT_MIRROR_URL = (  # MORTO (404, riverificato Fase 104): resta come riferimento storico
    "https://raw.githubusercontent.com/Mentaturan/ScoutFootball_for_World_Cup"
    "/main/data/raw/understat/{league}/{year}.json"
)
UNDERSTAT_URL = UNDERSTAT_OFFICIAL_URL

# Nome del campionato nello stile Understat (chiave interna -> nome Understat).
UNDERSTAT_LEAGUES: dict[str, str] = {
    "serie_a": "Serie_A",
    "premier_league": "EPL",
    "la_liga": "La_liga",
    "bundesliga": "Bundesliga",
    "ligue_1": "Ligue_1",
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


# --------------------------------------------------------------------------- #
# Fonte calendario di CLUB completo: openfootball (via mirror GitHub)
# --------------------------------------------------------------------------- #
# Serve per la CONGESTIONE vera (fatica): il riposo calcolato sulle sole date di
# Serie A non vede coppe ed Europa -- proprio le partite infrasettimanali che
# causano fatica asimmetrica (vedi docs/DIARIO.md, Fase 4c/4e). Le fonti "per
# squadra, multi-competizione" tipiche (FBref "Scores & Fixtures", Transfermarkt)
# NON sono raggiungibili dall'ambiente cloud (proxy, come gia' per xG e valori
# rosa). Usiamo i dataset testuali di openfootball, pubblici e raggiungibili via
# raw.githubusercontent.com, che coprono per stagione:
#   - competizioni UEFA per club (Champions/Europa/Conference + preliminari)
#     nel repo openfootball/champions-league;
#   - Coppa Italia nel repo openfootball/italy (file cup.txt).
# Le partite di Serie A NON si scaricano: si derivano dallo snapshot congelato
# (esatte, nomi gia' canonici). In locale si puo' puntare a una fonte per-squadra
# piu' completa (es. FBref) semplicemente cambiando questi URL e il parser.
OPENFOOTBALL_EUROPE_OFFICIAL = "https://github.com/openfootball/champions-league"
OPENFOOTBALL_ITALY_OFFICIAL = "https://github.com/openfootball/italy"
OPENFOOTBALL_EUROPE_URL = (
    "https://raw.githubusercontent.com/openfootball/champions-league"
    "/master/{season}/{comp}.txt"
)
OPENFOOTBALL_ITALY_URL = (
    "https://raw.githubusercontent.com/openfootball/italy"
    "/master/{season}/{comp}.txt"
)
# Coppe NAZIONALI per lega (Fase 59): stesso formato testuale della Coppa
# Italia, ma repo openfootball diverso per paese. Verificato raggiungibile
# (200) e col formato atteso per ogni (repo, stagione, file) elencato sotto.
OPENFOOTBALL_DOMESTIC_URL = (
    "https://raw.githubusercontent.com/openfootball/{repo}/master/{path}.txt"
)

# Competizioni europee per club (codice file openfootball -> nome canonico).
# "*q" = turni preliminari/qualificazioni (presenti solo nelle stagioni recenti).
EUROPE_COMPETITIONS: dict[str, str] = {
    "cl": "Champions League",
    "clq": "Champions League (qual.)",
    "el": "Europa League",
    "elq": "Europa League (qual.)",
    "conf": "Conference League",
    "confq": "Conference League (qual.)",
}

# Coppe nazionali italiane (per ora solo la Coppa Italia). Alias storico di
# DOMESTIC_CUP_COMPETITIONS["serie_a"] (stesso oggetto): mantenuto per
# retrocompatibilita' (test/codice esistenti lo referenziano direttamente).
ITALY_CUP_COMPETITIONS: dict[str, str] = {
    "cup": "Coppa Italia",
}

# Repo openfootball che ospita i dati DOMESTICI (campionato/coppe) di ogni lega.
OPENFOOTBALL_DOMESTIC_REPO: dict[str, str] = {
    "serie_a": "italy",
    "premier_league": "england",
    "la_liga": "espana",
    "bundesliga": "deutschland",
    "ligue_1": "france",
}

# Forma del PERCORSO dentro il repo domestico. Quasi tutti i repo openfootball
# usano "{stagione}/{file}.txt"; il repo francese e' un mono-repo con schema
# diverso ("france/{stagione}_{file}.txt"). Verificato scaricando i file.
OPENFOOTBALL_DOMESTIC_PATH: dict[str, str] = {
    "ligue_1": "france/{season}_{comp}",
}
DEFAULT_DOMESTIC_PATH = "{season}/{comp}"


def _domestic_path(league_key: str, season_label: str, comp: str) -> str:
    """Percorso del file dentro il repo domestico della lega."""
    tmpl = OPENFOOTBALL_DOMESTIC_PATH.get(league_key, DEFAULT_DOMESTIC_PATH)
    return tmpl.format(season=season_label, comp=comp)

# Coppe nazionali per lega (Fase 59, verificate una per una sul mirror):
#   - Premier: FA Cup (facup, 2018-19->2024-25) + EFL Cup (eflcup, stesse stagioni);
#   - La Liga: Copa del Rey (cup, 2020-21->2024-25, stessa finestra della Coppa
#     Italia -- il dataset copre entrambe le coppe "minori" solo dal 2020-21).
DOMESTIC_CUP_COMPETITIONS: dict[str, dict[str, str]] = {
    "serie_a": ITALY_CUP_COMPETITIONS,
    "premier_league": {"facup": "FA Cup", "eflcup": "EFL Cup"},
    "la_liga": {"cup": "Copa del Rey"},
    "bundesliga": {"cup": "DFB-Pokal"},
    "ligue_1": {"frcup": "Coupe de France"},
}

# Codice paese UEFA (usato nei file delle competizioni europee, es. "(ITA)") per
# ogni lega: filtra i club di QUELLA lega dentro Champions/Europa/Conference.
UEFA_COUNTRY_CODE: dict[str, str] = {
    "serie_a": "ITA", "premier_league": "ENG", "la_liga": "ESP",
    "bundesliga": "GER", "ligue_1": "FRA",
}

# Codici paese UEFA EXTRA che vanno trattati come la lega, oltre a quello
# "ufficiale" sopra (Fase 104, docs/audit_5_leghe/numeri/caccia_calendari.md
# §6a: "il bug del Monaco"). openfootball etichetta l'AS Monaco a volte "FRA"
# a volte "MCO" nello stesso repo (champions-league, dal 2011-12): con solo
# "FRA" il filtro perdeva 26 righe europee del Monaco su 54, comprese intere
# fasi a gironi di Champions. Il Monaco gioca in Ligue 1 dal punto di vista del
# progetto (e' nello snapshot ligue_1), quindi le sue partite europee contano
# come "extra" per ligue_1 a prescindere da quale codice openfootball usa.
UEFA_COUNTRY_CODE_EXTRA: dict[str, tuple[str, ...]] = {
    "ligue_1": ("MCO",),
}


def uefa_country_codes(league_key: str) -> frozenset[str]:
    """Insieme dei codici paese UEFA da considerare per ``league_key`` (il
    codice "ufficiale" di ``UEFA_COUNTRY_CODE`` + eventuali extra)."""
    return frozenset({UEFA_COUNTRY_CODE[league_key],
                       *UEFA_COUNTRY_CODE_EXTRA.get(league_key, ())})

# Competizioni presenti nel calendario di club SOLO grazie al recupero
# Wikipedia (Fase 100/103, docs/audit_5_leghe/numeri/caccia_calendari.md §7):
# supercoppe nazionali, Supercoppa UEFA, Mondiale/Intercontinentale per club,
# Coupe de la Ligue francese. Openfootball non le scarica (nessun URL/parser
# dedicato in questo modulo): non ricompaiono da sole se si rilancia
# build_club_fixtures senza rifare l'integrazione (scripts/integra_calendari_
# coppa.py). Trattarle come "extra" ai fini di midweek_europe/rest_days_full
# e' la scelta coerente con la semantica gia' in uso
# (fixtures.add_rest_days_full: is_extra = competition != own_competition):
# non sono il campionato, quindi affaticano allo stesso modo di una coppa.
EXTRA_CUP_COMPETITIONS: dict[str, dict[str, str]] = {
    "serie_a": {
        "supercoppa": "Supercoppa Italiana",
        "uefasc": "UEFA Super Cup",
        "cwc": "FIFA Club World Cup",
    },
    "premier_league": {
        "communityshield": "FA Community Shield",
        "uefasc": "UEFA Super Cup",
        "cwc": "FIFA Club World Cup",
    },
    "la_liga": {
        "supercopa": "Supercopa de Espana",
        "uefasc": "UEFA Super Cup",
        "cwc": "FIFA Club World Cup",
        "icc": "FIFA Intercontinental Cup",
    },
    "bundesliga": {
        "dflsupercup": "DFL-Supercup",
        "uefasc": "UEFA Super Cup",
        "cwc": "FIFA Club World Cup",
    },
    "ligue_1": {
        "trophee": "Trophee des Champions",
        "coupeligue": "Coupe de la Ligue",
        "uefasc": "UEFA Super Cup",
        "cwc": "FIFA Club World Cup",
        "icc": "FIFA Intercontinental Cup",
    },
}

# Nome canonico usato nel calendario di club per le partite della lega stessa
# (derivate dallo snapshot, non scaricate). Per compatibilita' col codice/test
# storici, la Serie A resta "Serie A"; le altre leghe usano League.name.
SERIE_A_COMPETITION = "Serie A"


def own_league_competition(league_key: str) -> str:
    """Nome-competizione usato nel calendario di club per le partite di
    campionato di ``league_key`` (derivate dallo snapshot, non da openfootball)."""
    if league_key == "serie_a":
        return SERIE_A_COMPETITION
    return LEAGUES[league_key].name


def openfootball_season_label(season_code: str) -> str:
    """Converte "1920" -> "2019-20" (cartelle openfootball: anno pieno-anno 2c)."""
    start = 2000 + int(season_code[:2])
    return f"{start}-{str(start + 1)[2:]}"


def openfootball_europe_url(season_code: str, comp: str) -> str:
    """URL del file openfootball di una competizione europea per una stagione."""
    if comp not in EUROPE_COMPETITIONS:
        raise KeyError(f"Competizione europea sconosciuta: {comp}")
    return OPENFOOTBALL_EUROPE_URL.format(
        season=openfootball_season_label(season_code), comp=comp
    )


def openfootball_italy_url(season_code: str, comp: str) -> str:
    """URL del file openfootball di una coppa nazionale per una stagione."""
    if comp not in ITALY_CUP_COMPETITIONS:
        raise KeyError(f"Coppa nazionale sconosciuta: {comp}")
    return OPENFOOTBALL_ITALY_URL.format(
        season=openfootball_season_label(season_code), comp=comp
    )


# Calendari "PRELUDIO" (Fase 68): file openfootball dei CAMPIONATI (non coppe)
# usati SOLO per radicare il riposo delle prime partite nel calendario di club:
#   - massima serie 2016-17 (l'ultima prima della finestra dati);
#   - seconda serie 1617..2425 (l'ultima stagione di ogni neopromossa prima
#     del suo esordio nella finestra).
# Tutti verificati raggiungibili (200) sul mirror raw.githubusercontent.
PRELUDE_TOP_FILES: dict[str, str] = {
    "serie_a": "1-seriea", "premier_league": "1-premierleague", "la_liga": "1-liga",
    "bundesliga": "1-bundesliga", "ligue_1": "fr1",
}
SECOND_TIER_FILES: dict[str, str] = {
    "serie_a": "2-serieb", "premier_league": "2-championship", "la_liga": "2-liga2",
    "bundesliga": "2-bundesliga2", "ligue_1": "fr2",
}
SECOND_TIER_NAMES: dict[str, str] = {
    "serie_a": "Serie B", "premier_league": "Championship",
    "la_liga": "Segunda División",
    "bundesliga": "2. Bundesliga", "ligue_1": "Ligue 2",
}
PRELUDE_SEASON = "1617"


def prelude_competition(league_key: str) -> str:
    """Etichetta-competizione del campionato 2016-17 nel calendario di club
    (distinta dal campionato in finestra, che ha regole di conteggio proprie)."""
    return f"{own_league_competition(league_key)} 2016-17"


def openfootball_league_url(league_key: str, season_code: str, tier: str) -> str:
    """URL del file openfootball di un CAMPIONATO (tier 'top' o 'second')."""
    files = PRELUDE_TOP_FILES if tier == "top" else SECOND_TIER_FILES
    if league_key not in files:
        raise KeyError(f"Lega sconosciuta per il preludio: {league_key}")
    repo = OPENFOOTBALL_DOMESTIC_REPO[league_key]
    return OPENFOOTBALL_DOMESTIC_URL.format(
        repo=repo, path=_domestic_path(
            league_key, openfootball_season_label(season_code), files[league_key]))


def openfootball_domestic_cup_url(league_key: str, season_code: str, comp: str) -> str:
    """URL del file openfootball di una coppa nazionale, per QUALSIASI lega
    supportata (Fase 59: generalizza openfootball_italy_url a Premier/Liga)."""
    cups = DOMESTIC_CUP_COMPETITIONS.get(league_key, {})
    if comp not in cups:
        raise KeyError(f"Coppa nazionale sconosciuta per {league_key}: {comp}")
    repo = OPENFOOTBALL_DOMESTIC_REPO[league_key]
    return OPENFOOTBALL_DOMESTIC_URL.format(
        repo=repo, path=_domestic_path(
            league_key, openfootball_season_label(season_code), comp))
