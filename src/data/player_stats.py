"""Statistiche PER GIOCATORE PER PARTITA — il primo dato "Tier B" del progetto.

Fonte: diretta.it/Flashscore, Serie A 2025-26, raccolta A MANO dall'utente il
31/07/2026 (niente scraping). Dati in `files/diretta_serie_a_2526/`.
⚠️ PRIMA DI USARE QUESTO MODULO leggi `files/diretta_serie_a_2526/README.md`
§1-bis: il dato a monte e' di Opta, il progetto NON rivendica alcuna licenza
su di esso, e la posizione di licenza e' dichiaratamente non risolta.

COSA C'E': 11.894 righe giocatore-partita x 97 statistiche (tocchi, passaggi
anche progressivi, dribbling, contrasti, recuperi, intercetti, falli
individuali, xG/xA/xGOT individuali, grandi occasioni, blocco portiere), su
379 delle 380 partite. Copre l'intero "Tier B" che il piano dava per
irraggiungibile (docs/PIANO_DATABASE_GIOCATORI.md §12).

PERIMETRO: una lega, una stagione. Non c'e' nulla per le altre 4 leghe ne' per
le 8 stagioni precedenti.

⏱️ REGOLA R8 — E' IL PUNTO PIU' FACILE DA SBAGLIARE.
Tutte e 97 le statistiche sono `post`: esistono solo a partita finita. Usarle
per prevedere la partita che le ha prodotte e' look-ahead. La forma normale
d'uso e' `team_form()`, che aggrega le partite PRECEDENTI. Le colonne grezze
di `load_player_matches()` NON vanno passate a un modello cosi' come sono.

Il modulo non e' letto da backtest.py ne' da alcun modello: e' l'infrastruttura
per il go/no-go descritto in docs/PIANO_DATABASE_GIOCATORI.md §12.3.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "files" / "diretta_serie_a_2526"
MATCHES_FILE = DATA_DIR / "partita_per_partita.csv.gz"
SEASON_FILE = DATA_DIR / "riepilogo_stagionale.csv.gz"
LEGEND_FILE = DATA_DIR / "legenda.csv"

LEAGUE = "serie_a"
SEASON = "2526"

# Le uniche colonne NON `post` (regola R8). Tutto il resto esiste solo a
# partita finita. `Titolare/Subentrato` e' `post` nel dato storico ma
# diventerebbe `pre` se raccolto dalla formazione ufficiale ~1h prima: qui
# arriva a posteriori, quindi resta `post`.
PRE_COLUMNS = ("Giornata", "Data", "Squadra", "Campo", "Avversario")
STATIC_COLUMNS = ("Giocatore", "Ruolo")

# Copertura attesa, verificata all'inserimento (31/07/2026). Sono guardie:
# se un giorno il file cambia sotto i piedi, il caricamento deve fallire
# rumorosamente invece di restituire in silenzio meno righe.
EXPECTED_ROWS = 11894
EXPECTED_TEAM_MATCHES = 758
EXPECTED_MATCHES = 379

# L'unica partita senza statistiche alla fonte (dichiarata dalla fonte stessa).
MISSING_MATCH = ("2025-12-27", "Lecce", "Como")


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():  # pragma: no cover - dipende dal checkout
        raise FileNotFoundError(
            f"{path} non trovato. I dati vivono in files/diretta_serie_a_2526/ "
            "e sono versionati: se manca, il checkout e' incompleto."
        )
    df = pd.read_csv(path)
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    return df


def load_player_matches(*, strict: bool = True) -> pd.DataFrame:
    """Una riga per giocatore-partita, con `data` come datetime.

    ⚠️ Le 97 statistiche qui dentro sono TUTTE `post` (R8): non passarle a un
    modello per la partita che le ha prodotte. Usa `team_form()`.

    Con ``strict`` (default) verifica la copertura attesa e alza se non torna.
    """
    df = _read(MATCHES_FILE)
    df["data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")

    if strict:
        if len(df) != EXPECTED_ROWS:
            raise ValueError(
                f"attese {EXPECTED_ROWS} righe giocatore-partita, trovate {len(df)}"
            )
        n_team_matches = df.groupby(["data", "Squadra", "Avversario"]).ngroups
        if n_team_matches != EXPECTED_TEAM_MATCHES:
            raise ValueError(
                f"attesi {EXPECTED_TEAM_MATCHES} team-partita, trovati {n_team_matches}"
            )
    return df


def load_season_totals() -> pd.DataFrame:
    """Una riga per giocatore-stagione (somme e medie).

    ⚠️ E' un DERIVATO del partita-per-partita, non una seconda misura: non
    usarlo come controllo incrociato di sé stesso. Ed e' un aggregato di FINE
    stagione, quindi utilizzabile solo RITARDATO (stagione precedente).
    ⚠️ I totali di Como e Lecce sono su 37 partite, non 38 (vedi MISSING_MATCH).
    """
    return _read(SEASON_FILE)


def load_legend() -> pd.DataFrame:
    """Mappa `codice fonte -> etichetta italiana` (es. BALL_RECOVERIES)."""
    return _read(LEGEND_FILE)


def statistic_columns(df: pd.DataFrame | None = None) -> list[str]:
    """Le colonne che sono STATISTICHE (tutte `post`), escluse le anagrafiche."""
    if df is None:
        df = load_player_matches(strict=False)
    skip = set(PRE_COLUMNS) | set(STATIC_COLUMNS) | {
        "data", "Risultato squadra", "Esito", "Titolare/Subentrato",
    }
    return [c for c in df.columns if c not in skip]


def join_to_snapshot(
    df: pd.DataFrame | None = None, snapshot: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Aggancia ogni riga alla partita corrispondente dello snapshot di lega.

    Aggiunge `home_team`, `away_team`, `home_goals`, `away_goals` e `in_casa`.
    Alza se anche una sola riga resta orfana: un join che perde righe in
    silenzio e' il modo in cui il progetto ha gia' pagato un bug (§7 del
    CLAUDE.md, caso "Hellas Verona").
    """
    if df is None:
        df = load_player_matches()
    if snapshot is None:
        # Import locale: evita un ciclo all'import del pacchetto. Si legge lo
        # SNAPSHOT congelato (offline-first, §5 del CLAUDE.md), non la rete.
        from . import database

        snapshot = database.read_snapshot(database.snapshot_path(LEAGUE))
    snap = snapshot.copy()
    snap["data"] = pd.to_datetime(snap["date"])
    snap = snap[snap["data"] >= pd.Timestamp("2025-07-01")]
    cols = ["data", "home_team", "away_team", "home_goals", "away_goals"]

    casa = df.merge(
        snap[cols], left_on=["data", "Squadra", "Avversario"],
        right_on=["data", "home_team", "away_team"], how="left",
    )
    trasferta = df.merge(
        snap[cols], left_on=["data", "Squadra", "Avversario"],
        right_on=["data", "away_team", "home_team"], how="left",
    )
    out = casa.copy()
    manca = out["home_team"].isna()
    for c in ("home_team", "away_team", "home_goals", "away_goals"):
        out.loc[manca, c] = trasferta.loc[manca, c]
    out["in_casa"] = out["Squadra"] == out["home_team"]

    orfane = out["home_team"].isna().sum()
    if orfane:
        raise ValueError(
            f"{orfane} righe giocatore-partita non agganciate allo snapshot "
            f"{LEAGUE}: il join deve essere totale, non parziale."
        )
    return out


def team_form(
    df: pd.DataFrame | None = None,
    columns: list[str] | None = None,
    window: int = 5,
) -> pd.DataFrame:
    """⏱️ LA FORMA SICURA (R8): media delle N partite PRECEDENTI, per squadra.

    Per ogni squadra-partita restituisce la media, sulle ``window`` partite
    **precedenti** di quella squadra, delle statistiche indicate — sommate
    sull'undici schierato. La riga della partita corrente e' esclusa per
    costruzione (``shift(1)``), quindi il risultato e' utilizzabile come
    feature `pre`.

    La prima partita di ogni squadra esce NaN: e' corretto, non un buco da
    riempire con zero.
    """
    if df is None:
        df = load_player_matches()
    if columns is None:
        columns = ["Palloni toccati", "Passaggi totali", "Dribbling riusciti",
                   "Contrasti", "Palle intercettate", "Goal previsti (xG)"]
    mancanti = [c for c in columns if c not in df.columns]
    if mancanti:
        raise KeyError(f"colonne assenti nel dataset: {mancanti}")

    per_partita = (
        df.groupby(["data", "Squadra"], as_index=False)[columns].sum()
        .sort_values(["Squadra", "data"])
    )
    rolling = (
        per_partita.groupby("Squadra")[columns]
        .apply(lambda g: g.shift(1).rolling(window, min_periods=1).mean())
        .reset_index(level=0, drop=True)
    )
    out = per_partita[["data", "Squadra"]].copy()
    for c in columns:
        out[f"{c} (media {window} prec.)"] = rolling[c]
    return out
