"""Scaricamento e normalizzazione dei dati partita.

Responsabilita' del modulo:
  1. scaricare i CSV grezzi (con cache locale in data/raw/);
  2. tradurli in uno SCHEMA INTERNO PULITO, indipendente dalle idiosincrasie del
     provider (nomi colonna che cambiano di stagione in stagione, formati data,
     quote presenti o assenti).

Il resto del progetto (modello, valutazione) lavora SOLO su questo schema pulito,
non sui CSV grezzi. Cosi' se un domani cambiamo fonte dati, si riscrive solo
questo file.

Schema interno (un DataFrame pandas con queste colonne):
    date         datetime   data della partita
    season       str        codice stagione (es. "2425")
    league       str        chiave campionato (es. "serie_a")
    home_team    str
    away_team    str
    home_goals   int
    away_goals   int
    result       str        "H" / "D" / "A"
    odds_home    float      quota 1 (migliore disponibile, vedi sotto)  -- puo' essere NaN
    odds_draw    float      quota X
    odds_away    float      quota 2
    odds_over25  float      quota Over 2.5
    odds_under25 float      quota Under 2.5

Colonne di ARRICCHIMENTO (vedi understat.py e transfermarkt.py; NaN se la
fonte non copre la partita/squadra):
    home_xg, away_xg           float  expected goals (Understat)
    home_npxg, away_npxg       float  xG senza rigori
    home_ppda, away_ppda       float  passaggi avversari per azione difensiva
    home_deep, away_deep       float  passaggi profondi completati
    home_squad_value, away_squad_value  float  valore rosa a inizio stagione (EUR)
    home_absent_count_est, away_absent_count_est  float  n. assenti STIMATO
    home_absent_value_est, away_absent_value_est  float  valore assenti STIMATO (EUR)

Politica sulle quote: per ogni mercato prendiamo la MIGLIORE fonte disponibile in
ordine di preferenza (quote di CHIUSURA medie -> chiusura Bet365 -> pre-match
medie -> pre-match Bet365). Le quote di chiusura sono lo stimatore di mercato
piu' efficiente; sono pero' assenti nelle stagioni piu' vecchie, dove ripieghiamo
sulle pre-match. Le quote servono in fase di VALUTAZIONE (benchmark di mercato),
non per stimare il modello.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import sources
from .sources import League

# Cartella di cache dei CSV grezzi.
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Ordine di preferenza delle colonne per ciascun mercato.
# Il primo nome presente (e valorizzato) nella riga viene usato.
_ODDS_PREFERENCE: dict[str, list[str]] = {
    "odds_home":   ["AvgCH", "B365CH", "AvgH", "BbAvH", "B365H"],
    "odds_draw":   ["AvgCD", "B365CD", "AvgD", "BbAvD", "B365D"],
    "odds_away":   ["AvgCA", "B365CA", "AvgA", "BbAvA", "B365A"],
    "odds_over25": ["AvgC>2.5", "B365C>2.5", "Avg>2.5", "BbAv>2.5", "B365>2.5"],
    "odds_under25": ["AvgC<2.5", "B365C<2.5", "Avg<2.5", "BbAv<2.5", "B365<2.5"],
}


def _cache_path(season_code: str, league: League) -> Path:
    return RAW_DIR / f"{league.key}_{season_code}.csv"


def download_season(
    season_code: str, league: League, *, force: bool = False
) -> Path:
    """Scarica il CSV grezzo di una stagione, con cache su disco.

    Ritorna il percorso del file locale. Se il file esiste gia' e ``force`` e'
    False, non riscarica.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = _cache_path(season_code, league)
    if dest.exists() and not force:
        return dest

    url = sources.csv_url(season_code, league)
    # pandas legge direttamente da URL; centralizziamo qui la lettura remota.
    raw = pd.read_csv(url, encoding="latin-1")
    raw.to_csv(dest, index=False)
    return dest


def _parse_dates(raw_dates: pd.Series) -> pd.Series:
    """Interpreta le date football-data (gg/mm/aaaa nelle stagioni recenti,
    gg/mm/aa in quelle vecchie). Proviamo i formati espliciti per evitare
    l'inferenza riga-per-riga (lenta e con warning); ripieghiamo su dateutil
    solo per eventuali residui."""
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        parsed = pd.to_datetime(raw_dates, format=fmt, errors="coerce")
        if parsed.notna().mean() > 0.9:
            return parsed
    return pd.to_datetime(raw_dates, dayfirst=True, errors="coerce")


def _pick_odds(row: pd.Series, candidates: list[str]) -> float:
    """Ritorna la prima quota disponibile e valida tra le colonne candidate."""
    for col in candidates:
        if col in row.index:
            val = row[col]
            if pd.notna(val) and val > 1.0:
                return float(val)
    return float("nan")


def _normalize(raw: pd.DataFrame, season_code: str, league: League) -> pd.DataFrame:
    """Traduce un CSV grezzo nello schema interno pulito."""
    # Righe valide: devono avere le squadre e i gol finali.
    raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()

    out = pd.DataFrame()
    out["date"] = _parse_dates(raw["Date"])
    out["season"] = season_code
    out["league"] = league.key
    out["home_team"] = raw["HomeTeam"].astype(str).str.strip().map(sources.canonical_team)
    out["away_team"] = raw["AwayTeam"].astype(str).str.strip().map(sources.canonical_team)
    out["home_goals"] = raw["FTHG"].astype(int)
    out["away_goals"] = raw["FTAG"].astype(int)
    out["result"] = raw["FTR"].astype(str).str.strip()

    # Tiri in porta (HST/AST): segnale meno rumoroso dei gol per stimare la
    # forza delle squadre (vedi models/dixon_coles.py, blend gol/tiri). Puo'
    # mancare in qualche riga/stagione: in quel caso resta NaN.
    out["home_sot"] = pd.to_numeric(raw.get("HST"), errors="coerce")
    out["away_sot"] = pd.to_numeric(raw.get("AST"), errors="coerce")

    for target, candidates in _ODDS_PREFERENCE.items():
        out[target] = raw.apply(lambda r: _pick_odds(r, candidates), axis=1)

    out = out.dropna(subset=["date"])
    out = out.sort_values("date").reset_index(drop=True)
    return out


def enrich(matches: pd.DataFrame, *, force_download: bool = False) -> pd.DataFrame:
    """Arricchisce le partite con le colonne da fonti esterne.

    In ordine: xG di Understat (add_xg), valori rosa Transfermarkt
    (add_squad_values) e assenze stimate da infortuni (add_absences).
    E' idempotente: le colonne gia' presenti vengono ricalcolate.
    Le leghe non coperte da Understat vengono restituite invariate.
    """
    leagues = set(matches["league"].unique())
    if not leagues <= set(sources.UNDERSTAT_LEAGUES):
        return matches

    from . import transfermarkt, understat

    matches = understat.add_xg(matches, force=force_download)
    matches = transfermarkt.add_squad_values(matches, force=force_download)
    matches = transfermarkt.add_absences(matches, force=force_download)
    return matches


def add_rest_days(matches: pd.DataFrame, cap: int = 14) -> pd.DataFrame:
    """Aggiunge home_rest_days / away_rest_days: giorni dall'ultima partita di
    ciascuna squadra (fatica / congestione di calendario).

    Feature derivata, deterministica e INDIPENDENTE dai risultati: cattura la
    stanchezza, che il modello gol/xG non puo' dedurre. Rispetta la cronologia
    (usa solo partite precedenti -> niente look-ahead). Prima partita di una
    squadra nei dati -> NaN (covariata neutra). Cap a ``cap`` giorni: oltre due
    settimane il recupero e' completo, conta solo la congestione.
    """
    df = matches.sort_values("date").reset_index(drop=True)
    last_seen: dict[str, pd.Timestamp] = {}
    home_rest, away_rest = [], []
    for _, r in df.iterrows():
        d = r["date"]
        for team, out in ((r["home_team"], home_rest), (r["away_team"], away_rest)):
            prev = last_seen.get(team)
            out.append(min((d - prev).days, cap) if prev is not None else float("nan"))
        last_seen[r["home_team"]] = d
        last_seen[r["away_team"]] = d
    df["home_rest_days"] = home_rest
    df["away_rest_days"] = away_rest
    return df


def add_form(matches: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Aggiunge home_form / away_form: punti per partita nelle ultime ``window``
    gare di ciascuna squadra PRIMA di questa (stato di forma recente).

    Feature derivata dai risultati recenti: cattura eventuale momentum che la
    forza pesata nel tempo non vedesse. Rispetta la cronologia (solo partite
    precedenti -> niente look-ahead), scorre tra le stagioni. Squadra con nessuna
    gara precedente -> NaN (covariata neutra). Punti: vittoria 3, pari 1, sconf. 0.
    """
    from collections import deque
    df = matches.sort_values("date").reset_index(drop=True)
    recent: dict[str, deque] = {}
    home_form, away_form = [], []
    for _, r in df.iterrows():
        for team, out in ((r["home_team"], home_form), (r["away_team"], away_form)):
            dq = recent.get(team)
            out.append(sum(dq) / len(dq) if dq else float("nan"))
        # Aggiorna DOPO aver letto (no look-ahead): punti di QUESTA gara.
        hg, ag = r["home_goals"], r["away_goals"]
        hp = 3 if hg > ag else (1 if hg == ag else 0)
        recent.setdefault(r["home_team"], deque(maxlen=window)).append(hp)
        recent.setdefault(r["away_team"], deque(maxlen=window)).append(3 - hp if hp != 1 else 1)
    df["home_form"] = home_form
    df["away_form"] = away_form
    return df


def load_league(
    league_key: str = "serie_a",
    season_codes: list[str] | None = None,
    *,
    force_download: bool = False,
) -> pd.DataFrame:
    """Carica e normalizza una o piu' stagioni di un campionato.

    Args:
        league_key: chiave in sources.LEAGUES (default "serie_a").
        season_codes: stagioni da caricare (default: tutte in sources.SEASONS).
        force_download: se True riscarica dalle fonti ignorando lo snapshot.

    Comportamento OFFLINE-FIRST: se esiste lo snapshot congelato
    (data/serie_a_matches.csv, versionato in git) lo si usa senza rete, cosi' i
    calcoli sono riproducibili identici da chiunque. Si scarica dalle fonti solo
    con force_download=True o se lo snapshot manca.

    Ritorna un unico DataFrame ordinato per data, nello schema interno.
    """
    league = sources.LEAGUES[league_key]
    seasons = season_codes if season_codes is not None else sources.SEASONS

    # Import locale per evitare qualsiasi ciclo di import.
    from . import database
    if (not force_download and league_key == "serie_a"
            and database.SNAPSHOT_PATH.exists()):
        df = database.read_snapshot()
        # Riposo e forma calcolati su TUTTE le stagioni (per avere le partite
        # precedenti a cavallo tra stagioni), poi si filtra a quelle richieste.
        df = add_rest_days(df)
        df = add_form(df)
        wanted = {str(s) for s in seasons}
        df = df[df["season"].isin(wanted)]
        return df.sort_values("date").reset_index(drop=True)

    frames: list[pd.DataFrame] = []
    for code in seasons:
        path = download_season(code, league, force=force_download)
        raw = pd.read_csv(path, encoding="latin-1")
        frames.append(_normalize(raw, code, league))

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)
    combined = enrich(combined, force_download=force_download)
    combined = add_rest_days(combined)
    combined = add_form(combined)
    return combined
