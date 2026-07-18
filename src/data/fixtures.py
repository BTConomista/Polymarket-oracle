"""Calendario di CLUB completo -> congestione vera (fatica di calendario).

PERCHE' ESISTE (vedi docs/DIARIO.md, Fase 4c/4e). Il modello gol+xG e' al tetto
dei dati attuali; l'unico segnale rimasto "indipendente dai risultati" e' la
CONGESTIONE: una squadra reduce da una trasferta di Champions il mercoledi' e'
affaticata la domenica. Il riposo calcolato dalle SOLE date di Serie A
(``loader.add_rest_days``) NON vede coppe ed Europa, cioe' proprio le partite
infrasettimanali che causano fatica ASIMMETRICA: quando tutta la lega gioca
infrasettimana il riposo cala per entrambe e la *differenza* e' ~0. Serve quindi
il calendario COMPLETO di club.

COSA FORNISCE, a livello di SINGOLA PARTITA di Serie A dello schema interno:

    home_rest_days_full, away_rest_days_full
        giorni dall'ULTIMA partita di club di quella squadra in QUALSIASI
        competizione (Serie A, Coppa Italia, Champions/Europa/Conference), cap a
        ``cap`` giorni, usando SOLO partite precedenti (niente look-ahead).
        NaN alla primissima partita nota della squadra. Stessa semantica di
        ``add_rest_days``, ma sul calendario completo invece che sulla sola lega.

    home_midweek_europe, away_midweek_europe   (opzionale, utile)
        1 se la squadra ha giocato una gara EUROPEA o di COPPA (non-Serie-A) nei
        ``europe_window`` giorni precedenti (default 4); 0 altrimenti.

FONTI (vedi sources.py). FBref/Transfermarkt "per squadra" non sono raggiungibili
dall'ambiente cloud (proxy): usiamo openfootball (mirror GitHub) per le coppe
europee e la Coppa Italia. Le partite di Serie A NON si scaricano: si derivano
dallo snapshot congelato (esatte, nomi gia' canonici, copertura 100%).

TABELLA GREZZA VERSIONATA: ``data/club_fixtures.csv`` -- una riga per
(squadra, partita di club): ``season, team, date, competition, home_away,
opponent``. I nomi squadra sono CANONICALIZZATI via ``sources.TEAM_ALIASES``; i
club di Serie A non agganciati vengono LOGGATi (mai ignorati: bug reale gia'
capitato con "Verona").

ONESTA' SULLA COPERTURA (openfootball, verificata al momento della scrittura):
    - Champions League: 2017-18 -> 2025-26 (tutte le 9 stagioni);
    - Europa League:    dal 2020-21 (MANCANO 2017-18, 2018-19, 2019-20);
    - Conference:       dal 2021-22 (competizione nata allora);
    - preliminari UEFA: solo stagioni recenti (2024-25 ->);
    - Coppa Italia:     2020-21 -> 2024-25 (mancano 2017-20 e 2025-26).
Dove una competizione non e' coperta, quelle partite semplicemente non entrano
nel calendario: ``rest_days_full`` degrada in modo controllato verso il valore
solo-Serie-A (mai in direzione sbagliata), e ``midweek_europe`` puo' essere un
falso 0 in quelle stagioni. Nessun numero inventato. La copertura reale per
stagione e' calcolabile con ``coverage_report`` e documentata nel diario.

Cache OFFLINE-FIRST: i file grezzi sono salvati in data/raw/ e riscaricati solo
con force=True (coerente con understat.py/transfermarkt.py). I backtest leggono
lo snapshot congelato e NON scaricano nulla.
"""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from . import sources

log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CLUB_FIXTURES_PATH = _DATA_DIR / "club_fixtures.csv"

# Schema della tabella grezza versionata.
FIXTURE_COLUMNS: list[str] = [
    "season", "team", "date", "competition", "home_away", "opponent",
]

# Colonne aggiunte allo schema interno da questa fonte.
REST_FULL_COLUMNS: list[str] = [
    "home_rest_days_full", "away_rest_days_full",
    "home_midweek_europe", "away_midweek_europe",
]

_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# Riga-data openfootball: "  Wed Sep 18 2019" oppure "  Tue Oct 1" (anno ereditato).
_DATE_RE = re.compile(
    r"^\s*[A-Z][a-z]{2}\s+([A-Z][a-z]{2})\s+(\d{1,2})(?:\s+(\d{4}))?\s*$"
)
# Riga-partita competizioni UEFA: "[hh:mm] Casa (CCC) v Ospite (CCC) [risultato]".
_EURO_RE = re.compile(
    r"^(?:\s*\d{1,2}[:.]\d{2}\s+)?(.+?)\s+\((\w{3})\)\s+v\s+(.+?)\s+\((\w{3})\)"
    r"(?:\s+.*)?$"
)
# Riga-partita Coppa Italia (dominio, senza codici paese): il punteggio separa
# casa e ospite -> "[hh:mm] Casa <sp> D-D [a.e.t.] [(..)]  Ospite".
_LEADING_TIME_RE = re.compile(r"^\s*\d{1,2}[:.]\d{2}\s+")
_CUP_RE = re.compile(
    r"^(.+?)\s{2,}\d{1,2}-\d{1,2}"
    r"(?:\s+a\.e\.t\.)?"
    r"(?:\s+\d{1,2}-\d{1,2}\s*(?:pen\.?|dcr)?)?"
    r"(?:\s*\([^)]*\))*"
    r"\s{2,}(.+?)\s*$"
)


# --------------------------------------------------------------------------- #
# Download (con cache offline)
# --------------------------------------------------------------------------- #
def _cache_path(kind: str, season_code: str, comp: str, league_key: str = "serie_a") -> Path:
    # La Serie A mantiene il nome-file storico (senza lega nel path): le altre
    # leghe lo aggiungono per non collidere in cache (Fase 59).
    prefix = "fixtures" if league_key == "serie_a" else f"fixtures_{league_key}"
    return RAW_DIR / f"{prefix}_{kind}_{season_code}_{comp}.txt"


def download_openfootball(
    season_code: str, comp: str, kind: str, *,
    league_key: str = "serie_a", force: bool = False,
) -> Path | None:
    """Scarica (con cache) un file openfootball. ``kind`` in {"europe","domestic",
    "league_top","league_second"} (``"italy"`` resta accettato come alias storico
    di ``"domestic"``+serie_a).

    Ritorna il percorso locale, o ``None`` se la competizione non e' presente per
    quella stagione (HTTP 404): NON e' un errore, e' una lacuna di copertura che
    logghiamo e documentiamo, non un numero da inventare.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if kind == "italy":
        kind, league_key = "domestic", "serie_a"
    dest = _cache_path(kind, season_code, comp, league_key)
    if dest.exists() and not force:
        return dest

    if kind == "europe":
        url = sources.openfootball_europe_url(season_code, comp)
    elif kind == "domestic":
        url = sources.openfootball_domestic_cup_url(league_key, season_code, comp)
    elif kind in ("league_top", "league_second"):
        url = sources.openfootball_league_url(
            league_key, season_code, "top" if kind == "league_top" else "second")
    else:
        raise ValueError(f"kind sconosciuto: {kind}")

    log.info("Scarico openfootball %s -> %s", url, dest)
    try:
        with urllib.request.urlopen(url) as resp:
            dest.write_bytes(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log.info("Copertura assente: %s %s (%s) non disponibile su openfootball",
                     season_code, comp, sources.openfootball_season_label(season_code))
            return None
        raise
    return dest


def _read_cached(kind: str, season_code: str, comp: str, *,
                  league_key: str = "serie_a", force: bool) -> str | None:
    path = download_openfootball(season_code, comp, kind, league_key=league_key, force=force)
    if path is None:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# Parsing (con parser di date "stateful": l'anno si eredita, con rollover)
# --------------------------------------------------------------------------- #
class _DateTracker:
    """Interpreta le date openfootball dove l'anno spesso e' omesso.

    Il formato NON e' globalmente cronologico: la fase a gironi elenca i gironi
    uno dopo l'altro, ognuno da Settembre a Dicembre (quindi un semplice
    "il mese e' tornato indietro -> +1 anno" sbaglia ai reset di girone). Regola
    robusta, per SEMESTRE di stagione:

      - anno esplicito nella riga -> si usa quello (ancora dura);
      - mesi Set-Dic -> anno di INIZIO (fase a gironi/campionato, sempre year0);
      - mesi Gen-Giu -> anno di FINE (year1: fasi a eliminazione);
      - Lug/Ago -> year0 (preliminari) PRIMA di entrare in year1; year1 solo se
        una data di year1 e' gia' stata vista (es. finali di Agosto 2020, COVID).

    ``seen_year1`` distingue l'Agosto dei preliminari (year0, prima di tutto) da
    un eventuale Agosto post-COVID (year1, dopo gli ottavi di Febbraio-Maggio).
    """

    def __init__(self, season_code: str) -> None:
        self.start_year = 2000 + int(season_code[:2])
        self._seen_year1 = False

    def parse(self, line: str) -> pd.Timestamp | None:
        m = _DATE_RE.match(line)
        if not m:
            return None
        mon_name, day, year = m.groups()
        month = _MONTHS[mon_name]
        if year is not None:
            y = int(year)
            if y > self.start_year:
                self._seen_year1 = True
        elif month <= 6:                       # Gen-Giu -> year1
            y = self.start_year + 1
            self._seen_year1 = True
        elif month >= 9:                       # Set-Dic -> year0
            y = self.start_year
        else:                                  # Lug/Ago: year1 solo se gia' entrati
            y = self.start_year + 1 if self._seen_year1 else self.start_year
        try:
            return pd.Timestamp(year=y, month=month, day=int(day))
        except ValueError:
            return None


def parse_europe(
    text: str, season_code: str, competition: str, country_code: str = "ITA",
) -> pd.DataFrame:
    """Estrae le partite di una competizione UEFA che coinvolgono un club di
    ``country_code`` (default "ITA", Serie A).

    Ritorna righe grezze: date, home_raw, home_cc, away_raw, away_cc, competition.
    Il filtro/aggancio ai nomi canonici avviene a valle (in ``_uefa_team_rows``,
    che va chiamata con LO STESSO ``country_code`` -- Fase 59: prima di
    generalizzare a Premier/Liga questo filtro era cablato su "ITA" e scartava
    silenziosamente ogni partita europea SENZA una squadra italiana, es.
    Manchester City-RB Leipzig: un club senza mai un'italiana in un turno
    (comune) restava a ZERO partite anche quando i dati le contenevano tutte).
    """
    tracker = _DateTracker(season_code)
    rows: list[dict] = []
    current_date: pd.Timestamp | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        d = tracker.parse(line)
        if d is not None:
            current_date = d
            continue
        m = _EURO_RE.match(line)
        if not m or current_date is None:
            continue
        home, hc, away, ac = (g.strip() for g in m.groups())
        if hc != country_code and ac != country_code:
            continue  # ci interessano solo le squadre della lega in oggetto
        rows.append({
            "season": season_code, "competition": competition,
            "date": current_date,
            "home_raw": home, "home_cc": hc, "away_raw": away, "away_cc": ac,
        })
    return pd.DataFrame(rows)


def _parse_cup_line(body: str) -> tuple[str, str] | None:
    """Estrae (casa, ospite) da una riga di Coppa Italia (senza orario).

    openfootball usa DUE formati per la stessa coppa a seconda della stagione:
      - "Casa   v   Ospite   D-D (..)"   (dal 2024-25, come le europee);
      - "Casa   D-D (..)   Ospite"       (2020-21 -> 2023-24, punteggio in mezzo).
    Gestiamo entrambi per riga (robusto anche a file misti).
    """
    if re.search(r"\sv\s", body):  # formato con " v "
        parts = re.split(r"\s+v\s+", body, maxsplit=1)
        if len(parts) != 2:
            return None
        home = parts[0].strip()
        away = re.sub(r"\s{2,}.*$", "", parts[1]).strip()  # via risultato/aggr.
        if home and away:
            return home, away
        return None
    m = _CUP_RE.match(body)  # formato con punteggio in mezzo
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None


def parse_cup(text: str, season_code: str, competition: str) -> pd.DataFrame:
    """Estrae le partite di una coppa nazionale (formato dominio, senza CCC)."""
    tracker = _DateTracker(season_code)
    rows: list[dict] = []
    current_date: pd.Timestamp | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        d = tracker.parse(line)
        if d is not None:
            current_date = d
            continue
        if current_date is None:
            continue
        body = _LEADING_TIME_RE.sub("", line).strip()
        pair = _parse_cup_line(body)
        if pair is None:
            continue
        home, away = pair
        rows.append({
            "season": season_code, "competition": competition,
            "date": current_date,
            "home_raw": home, "home_cc": "ITA", "away_raw": away, "away_cc": "ITA",
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Da righe grezze a righe "per squadra italiana" (una riga per club coinvolto)
# --------------------------------------------------------------------------- #
def _uefa_team_rows(
    raw: pd.DataFrame, snapshot_teams: set[str], country_code: str = "ITA",
) -> list[dict]:
    """Trasforma le partite grezze in righe per-squadra dello schema fixtures.

    Per ogni lato con codice paese ``country_code`` (default "ITA", Serie A)
    emette una riga (team canonico, opponent = altro lato canonico, home_away).
    I nomi di quel paese che NON agganciano un club dello snapshot vengono
    LOGGATi (probabile alias mancante) -- generalizzato Fase 59 per Premier
    ("ENG")/Liga ("ESP"), stessa logica, stesso schema.
    """
    out: list[dict] = []
    for r in raw.itertuples(index=False):
        home = sources.canonical_team(r.home_raw)
        away = sources.canonical_team(r.away_raw)
        for side_cc, team, opp, ha in (
            (r.home_cc, home, away, "H"),
            (r.away_cc, away, home, "A"),
        ):
            if side_cc != country_code:
                continue
            if team not in snapshot_teams:
                log.warning(
                    "Club %s NON agganciato (alias mancante?): %r -> %r "
                    "[%s %s, %s]",
                    country_code, r.home_raw if ha == "H" else r.away_raw, team,
                    r.season, r.competition, r.date.date(),
                )
                continue
            out.append({
                "season": r.season, "team": team, "date": r.date,
                "competition": r.competition, "home_away": ha, "opponent": opp,
            })
    return out


def _cup_team_rows(raw: pd.DataFrame, snapshot_teams: set[str]) -> list[dict]:
    """Come sopra per la Coppa Italia: entrambi i lati sono italiani, ma teniamo
    solo i lati che agganciano un club di Serie A (gli avversari di Serie B/C
    restano come ``opponent`` di contesto, non generano righe proprie)."""
    out: list[dict] = []
    for r in raw.itertuples(index=False):
        home = sources.canonical_team(r.home_raw)
        away = sources.canonical_team(r.away_raw)
        for team, opp, ha in ((home, away, "H"), (away, home, "A")):
            if team not in snapshot_teams:
                continue  # avversario non-Serie-A: nessuna riga propria
            out.append({
                "season": r.season, "team": team, "date": r.date,
                "competition": r.competition, "home_away": ha, "opponent": opp,
            })
    return out


def _league_rows(matches: pd.DataFrame, competition: str) -> list[dict]:
    """Righe di campionato derivate dallo snapshot (esatte, nomi gia' canonici),
    per QUALSIASI lega -- ``competition`` e' il nome usato nel calendario."""
    out: list[dict] = []
    for r in matches.itertuples(index=False):
        date = pd.Timestamp(r.date).normalize()
        out.append({
            "season": str(r.season), "team": r.home_team, "date": date,
            "competition": competition,
            "home_away": "H", "opponent": r.away_team,
        })
        out.append({
            "season": str(r.season), "team": r.away_team, "date": date,
            "competition": competition,
            "home_away": "A", "opponent": r.home_team,
        })
    return out


def _serie_a_rows(matches: pd.DataFrame) -> list[dict]:
    """Righe di Serie A derivate dallo snapshot. Alias storico di
    ``_league_rows(matches, sources.SERIE_A_COMPETITION)`` (retrocompatibilita'
    dei test/codice esistenti)."""
    return _league_rows(matches, sources.SERIE_A_COMPETITION)


def _prelude_rows(
    league_key: str, snapshot_teams: set[str], seasons: list[str],
    *, force: bool = False,
) -> list[dict]:
    """Righe di PRELUDIO (Fase 68): campionati fuori-finestra che radicano il
    riposo delle PRIME partite di ogni squadra con date reali:
      - massima serie 2016-17 (per le squadre presenti dalla prima stagione);
      - seconda serie 1617..penultima (l'ultima stagione di ogni neopromossa
        prima del suo esordio nella finestra).
    Solo i club dello snapshot generano righe (gli altri restano opponent);
    file mancanti = lacuna dichiarata, mai un errore."""
    rows: list[dict] = []
    text = _read_cached("league_top", sources.PRELUDE_SEASON, "top",
                        league_key=league_key, force=force)
    if text:
        raw = parse_cup(text, sources.PRELUDE_SEASON,
                        sources.prelude_competition(league_key))
        if not raw.empty:
            rows.extend(_cup_team_rows(raw, snapshot_teams))

    second_name = sources.SECOND_TIER_NAMES[league_key]
    prior = [sources.PRELUDE_SEASON] + seasons[:-1]   # 1617..penultima
    for code in prior:
        text = _read_cached("league_second", code, "second",
                            league_key=league_key, force=force)
        if not text:
            continue
        raw = parse_cup(text, code, second_name)
        if not raw.empty:
            rows.extend(_cup_team_rows(raw, snapshot_teams))
    return rows


# --------------------------------------------------------------------------- #
# Assemblaggio del calendario di club completo
# --------------------------------------------------------------------------- #
def build_club_fixtures(
    matches: pd.DataFrame, *, league_key: str = "serie_a", force: bool = False
) -> pd.DataFrame:
    """Assembla il calendario di club completo (schema FIXTURE_COLUMNS) per la
    lega ``league_key`` (default "serie_a", retrocompatibile).

    = campionato (dallo snapshot) + coppe europee (Champions/Europa/Conference,
    filtrate sul codice paese della lega) + coppa/e nazionale/i (da openfootball,
    Fase 59 generalizza la sola Coppa Italia della Fase 4e a Premier/Liga).
    Deduplica su (season, team, date, competition, opponent) e ordina per data.
    """
    snapshot_teams = set(matches["home_team"]) | set(matches["away_team"])
    seasons = sorted(matches["season"].astype(str).unique())
    country_code = sources.UEFA_COUNTRY_CODE[league_key]
    domestic_cups = sources.DOMESTIC_CUP_COMPETITIONS.get(league_key, {})

    rows: list[dict] = _league_rows(matches, sources.own_league_competition(league_key))
    rows.extend(_prelude_rows(league_key, snapshot_teams, seasons, force=force))

    for code in seasons:
        for comp in sources.EUROPE_COMPETITIONS:
            text = _read_cached("europe", code, comp, force=force)
            if not text:
                continue
            raw = parse_europe(text, code, sources.EUROPE_COMPETITIONS[comp], country_code)
            if not raw.empty:
                rows.extend(_uefa_team_rows(raw, snapshot_teams, country_code))
        for comp in domestic_cups:
            text = _read_cached("domestic", code, comp, league_key=league_key, force=force)
            if not text:
                continue
            raw = parse_cup(text, code, domestic_cups[comp])
            if not raw.empty:
                rows.extend(_cup_team_rows(raw, snapshot_teams))

    fx = pd.DataFrame(rows, columns=FIXTURE_COLUMNS)
    fx["date"] = pd.to_datetime(fx["date"]).dt.normalize()
    fx = fx.drop_duplicates(
        subset=["season", "team", "date", "competition", "opponent"]
    )
    fx = fx.sort_values(["date", "team", "competition"]).reset_index(drop=True)
    return fx


def club_fixtures_path(league_key: str = "serie_a") -> Path:
    """Percorso dello snapshot del calendario di club per una lega.

    La Serie A mantiene il nome storico ``club_fixtures.csv`` (== CLUB_FIXTURES_PATH,
    retrocompatibile); le altre leghe (Fase 59) usano
    ``club_fixtures_{lega}.csv``."""
    if league_key == "serie_a":
        return CLUB_FIXTURES_PATH
    return _DATA_DIR / f"club_fixtures_{league_key}.csv"


def write_club_fixtures(
    fixtures: pd.DataFrame, path: Path = CLUB_FIXTURES_PATH
) -> Path:
    """Scrive la tabella grezza versionata del calendario di club."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = fixtures.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)
    return path


def read_club_fixtures(path: Path = CLUB_FIXTURES_PATH) -> pd.DataFrame:
    """Legge la tabella grezza del calendario di club (offline)."""
    return pd.read_csv(path, parse_dates=["date"], dtype={"season": str})


# --------------------------------------------------------------------------- #
# Feature: riposo sul calendario COMPLETO (+ flag gara europea infrasettimanale)
# --------------------------------------------------------------------------- #
def add_rest_days_full(
    matches: pd.DataFrame,
    fixtures: pd.DataFrame,
    *,
    cap: int = 14,
    europe_window: int = 4,
    own_competition: str = sources.SERIE_A_COMPETITION,
) -> pd.DataFrame:
    """Aggiunge le colonne REST_FULL_COLUMNS alle partite dello schema interno.

    Per ogni partita di campionato alla data ``d``, e per ciascuna delle due
    squadre ``T``:
      - ``rest_days_full`` = min(giorni da (ultima partita di club di T con data
        < d, QUALSIASI competizione), cap). NaN se T non ha partite precedenti nel
        calendario. Uso di ``< d`` STRETTO -> nessun look-ahead e nessun
        auto-conteggio della partita stessa.
      - ``midweek_europe`` = 1 se T ha una partita EUROPEA/COPPA (competizione !=
        ``own_competition``, default "Serie A") con data in
        [d - europe_window, d - 1]; 0 altrimenti.

    ``own_competition`` (Fase 59) identifica il campionato "di casa" nel
    calendario di club, cosi' da poter distinguere le gare extra anche per
    Premier League ("Premier League") e La Liga ("La Liga").

    Idempotente: se le colonne esistono gia', vengono ricalcolate.
    """
    out = matches.copy()
    out = out.drop(columns=[c for c in REST_FULL_COLUMNS if c in out.columns])

    fx = fixtures.copy()
    fx["date"] = pd.to_datetime(fx["date"]).dt.normalize()
    fx["is_extra"] = fx["competition"] != own_competition

    # Per ogni squadra: date ordinate di TUTTE le partite di club, e (a parte) le
    # sole date delle partite europee/coppa (per il flag infrasettimanale).
    all_dates: dict[str, np.ndarray] = {}
    extra_dates: dict[str, np.ndarray] = {}
    for team, grp in fx.groupby("team"):
        d = np.sort(grp["date"].values)
        all_dates[team] = d
        extra_dates[team] = np.sort(grp.loc[grp["is_extra"], "date"].values)

    def _rest(team: str, day: np.datetime64) -> float:
        arr = all_dates.get(team)
        if arr is None:
            return float("nan")
        i = np.searchsorted(arr, day, side="left")  # arr[:i] sono < day (stretto)
        if i == 0:
            return float("nan")
        gap = (day - arr[i - 1]) / np.timedelta64(1, "D")
        return float(min(gap, cap))

    def _midweek(team: str, day: np.datetime64) -> int:
        arr = extra_dates.get(team)
        if arr is None or arr.size == 0:
            return 0
        lo = day - np.timedelta64(europe_window, "D")
        hi = day - np.timedelta64(1, "D")
        i = np.searchsorted(arr, lo, side="left")
        j = np.searchsorted(arr, hi, side="right")
        return int(j > i)

    hr, ar, hm, am = [], [], [], []
    for r in out.itertuples(index=False):
        day = np.datetime64(pd.Timestamp(r.date).normalize(), "D")
        hr.append(_rest(r.home_team, day))
        ar.append(_rest(r.away_team, day))
        hm.append(_midweek(r.home_team, day))
        am.append(_midweek(r.away_team, day))
    out["home_rest_days_full"] = hr
    out["away_rest_days_full"] = ar
    out["home_midweek_europe"] = hm
    out["away_midweek_europe"] = am
    return out


# --------------------------------------------------------------------------- #
# Copertura (onesta', documentabile)
# --------------------------------------------------------------------------- #
def coverage_report(
    fixtures: pd.DataFrame, own_competition: str = sources.SERIE_A_COMPETITION
) -> pd.DataFrame:
    """Copertura per stagione: n. partite extra (coppe/Europa) e squadre coinvolte."""
    fx = fixtures[fixtures["competition"] != own_competition]
    rows = []
    for season, grp in fx.groupby("season"):
        comps = grp.groupby("competition").size().to_dict()
        rows.append({
            "season": season,
            "extra_matches": len(grp),
            "teams_with_extra": grp["team"].nunique(),
            **comps,
        })
    return pd.DataFrame(rows).fillna(0).sort_values("season").reset_index(drop=True)
