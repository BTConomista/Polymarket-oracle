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
    return combined
