"""Database interno dei dati raccolti (durevole, portabile, riproducibile).

Motivazione: finora i dati vivevano solo come CSV scaricati al volo da un mirror
esterno (che potrebbe cambiare o sparire). Per poter lavorare anche in sessioni
future e permettere a terzi di rieseguire gli stessi calcoli, congeliamo i dati
in un archivio interno con DUE artefatti complementari:

  1. SNAPSHOT CSV  (data/serie_a_matches.csv)  -- versionato in git.
     Testo, diffabile, portabile: e' la FONTE DI VERITA' congelata. Chiunque
     cloni il repo ha esattamente gli stessi dati, senza rete.

  2. DATABASE SQLite  (data/football.db)  -- NON versionato (rigenerabile).
     Artefatto queryable con SQL, ricostruito dallo snapshot in un comando
     (`python scripts/build_database.py`). Comodo per interrogazioni ad hoc.

Perche' SQLite: per questa scala (migliaia di partite) e' la scelta giusta -- un
singolo file, zero server, query SQL vere, incluso in Python. Non Postgres
(sovradimensionato ora), non solo CSV grezzi (niente query/integrita').

Lo schema e' volutamente semplice (una tabella `matches` che rispecchia lo schema
interno del loader, piu' una tabella `meta` con la provenienza). Aggiungere una
nuova fonte dati domani = aggiungere colonne/tabelle qui, guidati dai dati reali.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SNAPSHOT_PATH = _DATA_DIR / "serie_a_matches.csv"
DB_PATH = _DATA_DIR / "football.db"


def snapshot_path(league_key: str = "serie_a") -> Path:
    """Percorso dello snapshot congelato di una lega (data/{league}_matches.csv).

    Retro-compatibile: serie_a resta data/serie_a_matches.csv. Premier/La Liga
    (Fase 54) usano lo stesso schema, costruiti dai bundle in files/."""
    return _DATA_DIR / f"{league_key}_matches.csv"


# ---------------------------------------------------------------------- #
# Snapshot CSV (fonte di verita' congelata, versionata)
# ---------------------------------------------------------------------- #
def write_snapshot(matches: pd.DataFrame, path: Path = SNAPSHOT_PATH) -> Path:
    """Scrive lo snapshot congelato dei dati (formato CSV, testo diffabile)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    matches.sort_values(["date", "home_team"]).to_csv(path, index=False)
    return path


def read_snapshot(path: Path = SNAPSHOT_PATH) -> pd.DataFrame:
    """Legge lo snapshot congelato (offline, senza rete)."""
    if not path.exists():
        raise FileNotFoundError(
            f"Snapshot non trovato: {path}. Eseguire prima "
            f"`python scripts/build_database.py --refresh`."
        )
    # season come stringa ("2021" non deve diventare int 2021).
    df = pd.read_csv(path, parse_dates=["date"], dtype={"season": str})
    return df


# ---------------------------------------------------------------------- #
# Database SQLite (artefatto queryable, rigenerabile)
# ---------------------------------------------------------------------- #
def build_db(matches: pd.DataFrame, fingerprint: str, db_path: Path = DB_PATH) -> Path:
    """(Ri)costruisce il database SQLite dai dati normalizzati.

    Crea la tabella `matches` e una tabella `meta` con la provenienza
    (numero partite, impronta dei dati, momento di costruzione).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    out = matches.copy()
    out["date"] = out["date"].astype(str)  # SQLite non ha un tipo date nativo

    with sqlite3.connect(db_path) as conn:
        out.to_sql("matches", conn, index=False)
        # Indici utili per le query piu' comuni.
        conn.execute("CREATE INDEX idx_matches_season ON matches(season)")
        conn.execute("CREATE INDEX idx_matches_date ON matches(date)")
        conn.execute("CREATE INDEX idx_matches_home ON matches(home_team)")
        conn.execute("CREATE INDEX idx_matches_away ON matches(away_team)")
        # Tabella di provenienza.
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        meta = {
            "n_matches": str(len(matches)),
            "n_seasons": str(matches["season"].nunique()),
            "data_fingerprint": fingerprint,
            "seasons": ",".join(sorted(matches["season"].unique())),
            "note": "Serie A, schema football-data.co.uk (via mirror). "
                    "Ricostruibile con scripts/build_database.py.",
        }
        conn.executemany("INSERT INTO meta VALUES (?, ?)", list(meta.items()))
    return db_path


def load_matches(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Legge le partite dal database SQLite (schema interno del loader)."""
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database non trovato: {db_path}. Eseguire "
            f"`python scripts/build_database.py`."
        )
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql("SELECT * FROM matches", conn, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def read_meta(db_path: Path = DB_PATH) -> dict:
    """Legge la tabella di provenienza del database."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT key, value FROM meta").fetchall()
    return dict(rows)
