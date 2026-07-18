"""Fonte valori rosa: dataset "player-scores" (Transfermarkt via Kaggle, Fase 67).

Sostituisce il datalake `salimt` come fonte dei valori rosa: stesso dato a
monte (Transfermarkt) ma con lo storico valutazioni COMPLETO (~508k valutazioni,
31.5k giocatori — Milinkovic-Savic, Gerard Moreno ecc. inclusi) e, soprattutto,
con le PRESENZE per club (appearances): rose reali per id interno, per TUTTE
e tre le leghe (anche la Serie A, le cui rose Understat non erano piu'
rigenerabili) e SENZA alcun matching per nome dei giocatori — l'unico aggancio
per nome e' quello dei ~110 club, enumerato in sources.TEAM_ALIASES.

I file vivono in files/player_scores/*.csv.gz, importati dal workflow GitHub
Actions `.github/workflows/import_dataset.yml` (l'ambiente cloud non raggiunge
Kaggle/HF: il runner Actions si', Fase 67). Dataset CC0, aggiornato
settimanalmente a monte (dcaribou/transfermarkt-datasets).

DEFINIZIONE INVARIATA rispetto a transfermarkt.py (Fase 4a): valore rosa =
somma, sui giocatori della rosa stagionale, dell'ultima valutazione <= 1
settembre dell'anno di inizio; valutazioni piu' vecchie di MAX_VALUE_AGE_DAYS
scartate; pubblicato solo se i giocatori valutati coprono almeno MIN_COVERAGE
dei minuti stagionali. La rosa qui e' "chi ha giocato >=1 minuto in campionato"
(appearances della lega domestica) — stessa filosofia della rosa Understat.

Le stagioni sono assegnate per FINESTRA DI DATE dello snapshot (min/max data
di ogni stagione), non per mese: la coda COVID della 2019-20 (partite fino al
2 agosto 2020) finirebbe altrimenti nella stagione successiva.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import sources
from .transfermarkt import MAX_VALUE_AGE_DAYS, MIN_COVERAGE, SQUAD_VALUE_COLUMNS

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "files" / "player_scores"

# competition_id del dataset -> chiave lega interna
COMPETITION_IDS: dict[str, str] = {
    "IT1": "serie_a", "GB1": "premier_league", "ES1": "la_liga",
}
SEASON_START = "09-01"          # come transfermarkt.SEASON_START


def _require(name: str) -> Path:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} non trovato: importa il dataset col workflow GitHub "
            f"Actions (.github/workflows/import_dataset.yml — push del file "
            f".github/import-dataset-trigger)")
    return path


def season_windows(matches: pd.DataFrame) -> dict[str, tuple]:
    """{codice stagione: (prima data, ultima data)} dallo snapshot."""
    g = matches.groupby(matches["season"].astype(str))["date"]
    return {s: (pd.Timestamp(lo), pd.Timestamp(hi))
            for s, (lo, hi) in g.agg(["min", "max"]).iterrows()}


def league_rosters(league_key: str, matches: pd.DataFrame) -> pd.DataFrame:
    """Rose stagionali dalla tabella appearances: una riga per
    (season, team, player_id) con i minuti giocati in campionato.

    La stagione e' assegnata per appartenenza alla finestra di date dello
    snapshot (esatta anche per la coda COVID della 2019-20)."""
    comp = {c for c, lg in COMPETITION_IDS.items() if lg == league_key}
    app = pd.read_csv(
        _require("appearances.csv.gz"),
        usecols=["player_id", "player_club_id", "date",
                 "competition_id", "minutes_played"])
    app = app[app["competition_id"].isin(comp)].copy()
    app["date"] = pd.to_datetime(app["date"])

    app["season"] = pd.NA
    for code, (lo, hi) in season_windows(matches).items():
        inside = app["date"].between(lo, hi)
        app.loc[inside, "season"] = code
    n_out = int(app["season"].isna().sum())
    if n_out:
        log.info("player_scores %s: %d presenze fuori dalle finestre di "
                 "stagione dello snapshot (scartate)", league_key, n_out)
    app = app.dropna(subset=["season"])

    clubs = pd.read_csv(_require("clubs.csv.gz"), usecols=["club_id", "name"])
    name_of = dict(zip(clubs["club_id"], clubs["name"]))
    snapshot_teams = set(matches["home_team"]) | set(matches["away_team"])

    roster = app.groupby(["season", "player_club_id", "player_id"],
                         as_index=False)["minutes_played"].sum()
    roster["team"] = [sources.canonical_team(name_of.get(c, f"?{c}"))
                      for c in roster["player_club_id"]]
    orphan = sorted(set(roster.loc[~roster["team"].isin(snapshot_teams),
                                   "team"]))
    if orphan:
        # club non agganciato = alias mancante: rumoroso, mai silenzioso
        raise ValueError(
            f"player_scores {league_key}: club non agganciati agli snapshot "
            f"(alias mancante in TEAM_ALIASES?): {orphan}")
    return roster[["season", "team", "player_id", "minutes_played"]]


def _valuations() -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """{player_id: (date crescenti, valori EUR)} — analogo di
    transfermarkt._load_valuations, dalla tabella player_valuations."""
    val = pd.read_csv(
        _require("player_valuations.csv.gz"),
        usecols=["player_id", "date", "market_value_in_eur"])
    val["date"] = pd.to_datetime(val["date"])
    val = val.dropna(subset=["date", "market_value_in_eur"]).sort_values("date")
    return {int(pid): (g["date"].to_numpy(), g["market_value_in_eur"].to_numpy(float))
            for pid, g in val.groupby("player_id")}


def _value_asof(valuations, pid: int, when: pd.Timestamp) -> float:
    entry = valuations.get(pid)
    if entry is None:
        return float("nan")
    dates, values = entry
    i = int(np.searchsorted(dates, np.datetime64(when), side="right")) - 1
    if i < 0 or (when - pd.Timestamp(dates[i])).days > MAX_VALUE_AGE_DAYS:
        return float("nan")
    return float(values[i])


def team_season_values(
    league_key: str, matches: pd.DataFrame, *,
    min_coverage: float = MIN_COVERAGE,
) -> pd.DataFrame:
    """Valore rosa a inizio stagione per ogni (season, team) — stessa
    definizione (e stesse soglie di onesta') di transfermarkt.team_season_values."""
    roster = league_rosters(league_key, matches)
    valuations = _valuations()

    rows = []
    for (season, team), grp in roster.groupby(["season", "team"]):
        asof = pd.Timestamp(f"20{str(season)[:2]}-{SEASON_START}")
        values = np.array([_value_asof(valuations, int(p), asof)
                           for p in grp["player_id"]])
        minutes = grp["minutes_played"].fillna(0).to_numpy(float)
        covered = np.isfinite(values)
        coverage = (minutes[covered].sum() / minutes.sum()
                    if minutes.sum() > 0 else 0.0)
        total = float(np.nansum(values)) if covered.any() else float("nan")
        if coverage < min_coverage:
            log.warning("Valore rosa NON pubblicato per %s %s %s: copertura "
                        "%.0f%% sotto la soglia del %.0f%%", league_key,
                        season, team, coverage * 100, min_coverage * 100)
            total = float("nan")
        rows.append({"season": str(season), "team": team, "squad_value": total,
                     "value_coverage": round(float(coverage), 4),
                     "n_players": int(len(grp)),
                     "n_valued": int(covered.sum())})
    return pd.DataFrame(rows)


def add_squad_values(matches: pd.DataFrame, league_key: str) -> pd.DataFrame:
    """RIEMPIE home/away_squad_value dello snapshot da questa fonte (tutte le
    celle, non solo i buchi: fonte unica e coerente per le 3 leghe)."""
    out = matches.copy()
    out = out.drop(columns=[c for c in SQUAD_VALUE_COLUMNS if c in out.columns])
    out["season"] = out["season"].astype(str)
    values = team_season_values(league_key, out)

    n_before = len(out)
    for side in ("home", "away"):
        lookup = values.rename(columns={
            "team": f"{side}_team", "squad_value": f"{side}_squad_value",
        })[["season", f"{side}_team", f"{side}_squad_value"]]
        out = out.merge(lookup, on=["season", f"{side}_team"],
                        how="left", validate="many_to_one")
    assert len(out) == n_before, "il join valori rosa ha perso/duplicato partite"

    covered = out["home_squad_value"].notna() & out["away_squad_value"].notna()
    log.info("player_scores %s: %d/%d partite con valore rosa su entrambi i "
             "lati", league_key, int(covered.sum()), n_before)
    # Ordine colonne originale (il drop+merge sposterebbe le squad_value in
    # fondo; lo snapshot ha un ordine stabile e testato).
    return out[list(matches.columns)]
