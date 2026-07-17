"""Test delle STIME dichiarate (data/estimates/, Fase 62-bis).

Due famiglie di controlli:
  1. integrita' del file pubblicato (schema, chiavi, plausibilita', aggancio
     1:1 alle partite degli snapshot);
  2. NON-contaminazione: le stime NON devono mai finire nelle colonne quota
     degli snapshot (regola data/estimates/README.md — mai mischiare stima
     e dato di mercato).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import database, loader


@pytest.fixture(scope="module")
def estimates() -> pd.DataFrame:
    if not (loader.ESTIMATES_DIR / "ou_close_2017_19.csv").exists():
        pytest.skip("stime non generate (scripts/build_estimates.py)")
    return loader.read_ou_close_estimates()


def test_schema_e_copertura(estimates):
    assert list(estimates.columns) == ["league", "season", "date", "home_team",
                                       "away_team", "p_over25_close_est"]
    # SOLO le stagioni senza chiusura O/U reale: mai sovrapporsi ai dati veri.
    assert set(estimates["season"].unique()) == {"1718", "1819"}
    assert set(estimates["league"].unique()) == {"serie_a", "premier_league",
                                                 "la_liga"}
    # ~760 per lega (2 stagioni x 380; 1 partita Liga senza input -> saltata)
    per_lega = estimates.groupby("league").size()
    assert (per_lega >= 755).all() and (per_lega <= 760).all()


def test_probabilita_plausibili(estimates):
    p = estimates["p_over25_close_est"]
    assert p.between(0.05, 0.95).all()          # O/U 2.5: mai prob. estreme
    assert 0.45 < p.mean() < 0.60               # media di lega ~50-55% Over


def test_aggancio_uno_a_uno_con_gli_snapshot(estimates):
    """Ogni stima corrisponde ESATTAMENTE a una partita dello snapshot
    (stessa chiave di join del progetto: season, home_team, away_team)."""
    for lg, grp in estimates.groupby("league"):
        snap = database.read_snapshot(database.snapshot_path(lg))
        snap["season"] = snap["season"].astype(str)
        old = snap[snap["season"].isin(["1718", "1819"])]
        merged = grp.merge(old, on=["season", "home_team", "away_team"],
                           how="left", validate="one_to_one", indicator=True)
        assert (merged["_merge"] == "both").all(), \
            f"{lg}: stime senza partita corrispondente nello snapshot"


def test_snapshot_non_contaminati(estimates):
    """Guardia: negli snapshot l'O/U di apertura 2017-19 deve restare NaN
    (il dato reale NON esiste; la stima vive SOLO in data/estimates/)."""
    for lg in ["serie_a", "premier_league", "la_liga"]:
        snap = database.read_snapshot(database.snapshot_path(lg))
        snap["season"] = snap["season"].astype(str)
        old = snap[snap["season"].isin(["1718", "1819"])]
        assert old["odds_over25_open"].isna().all(), \
            f"{lg}: odds_over25_open 2017-19 valorizzato — contaminazione?"
        assert "p_over25_close_est" not in snap.columns, \
            f"{lg}: colonna di stima dentro lo snapshot — vietato"


@pytest.fixture(scope="module")
def squad_est() -> pd.DataFrame:
    path = loader.ESTIMATES_DIR / "squad_value_2017_26.csv"
    if not path.exists():
        pytest.skip("stime squad_value non generate (scripts/build_estimates.py)")
    return pd.read_csv(path, dtype={"season": str})


def test_squad_value_schema_e_metodi(squad_est):
    assert list(squad_est.columns) == ["league", "season", "team",
                                       "squad_value_est", "method",
                                       "expected_median_err_pct"]
    assert set(squad_est["method"].unique()) <= {"anchored", "regression"}
    # l'errore atteso e' dichiarato riga per riga e coerente col metodo
    per_m = squad_est.groupby("method")["expected_median_err_pct"].nunique()
    assert (per_m == 1).all()
    assert squad_est["squad_value_est"].between(5e6, 1.5e9).all()


def test_squad_value_copre_esattamente_i_buchi(squad_est):
    """Le stime coprono ESATTAMENTE le celle (stagione, squadra) NaN degli
    snapshot: ne' una di piu' (sovrascriverebbe dati veri) ne' una di meno."""
    for lg, grp in squad_est.groupby("league"):
        snap = database.read_snapshot(database.snapshot_path(lg))
        snap["season"] = snap["season"].astype(str)
        home = snap[["season", "home_team", "home_squad_value"]].rename(
            columns={"home_team": "team", "home_squad_value": "v"})
        away = snap[["season", "away_team", "away_squad_value"]].rename(
            columns={"away_team": "team", "away_squad_value": "v"})
        ts = pd.concat([home, away]).groupby(["season", "team"])["v"].first()
        holes = set(ts[ts.isna()].index)
        est_cells = set(zip(grp["season"], grp["team"]))
        assert est_cells == holes, f"{lg}: stime != buchi dello snapshot"


def test_squad_value_non_contamina_gli_snapshot(squad_est):
    """I buchi negli snapshot devono RESTARE NaN (la stima vive solo qui)."""
    for lg in squad_est["league"].unique():
        snap = database.read_snapshot(database.snapshot_path(lg))
        assert "squad_value_est" not in snap.columns


def test_stima_diversa_dalla_linea_prematch(estimates):
    """La stima deve MUOVERSI rispetto alla linea pre-match (se coincidesse
    sempre, il builder starebbe ricopiando l'input invece di stimare)."""
    snap = database.read_snapshot(database.snapshot_path("serie_a"))
    snap["season"] = snap["season"].astype(str)
    old = snap[snap["season"].isin(["1718", "1819"])]
    m = estimates[estimates["league"] == "serie_a"].merge(
        old, on=["season", "home_team", "away_team"], validate="one_to_one")
    inv = 1 / m["odds_over25"] + 1 / m["odds_under25"]
    p_line = (1 / m["odds_over25"]) / inv
    diff = (m["p_over25_close_est"] - p_line).abs()
    assert (diff > 1e-4).mean() > 0.95
    assert diff.mean() < 0.10                   # ...ma senza strappi assurdi
