"""Test della fonte player-scores (valori rosa reali, Fase 67).

Famiglie di controlli:
  1. aggancio club -> nomi canonici completo (zero orfani, pena ValueError);
  2. assegnazione stagioni per FINESTRA DI DATE: la coda COVID della 2019-20
     (partite di luglio/agosto 2020) NON deve traboccare nella 2020-21;
  3. copertura degli snapshot dopo il refill: 100% (o quasi) sulle stagioni
     concluse, buchi ammessi solo nella stagione in corso (2526).
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data import database, player_scores

LEAGUES = ["serie_a", "premier_league", "la_liga"]
# Retrocesse al termine della 2019-20 (finita ad agosto 2020 causa COVID):
# con l'assegnazione per mese le loro ultime gare finirebbero nella 2020-21.
RELEGATED_1920 = {
    "serie_a": {"Brescia", "Lecce", "Spal"},
    "premier_league": {"Bournemouth", "Norwich", "Watford"},
    "la_liga": {"Espanol", "Leganes", "Mallorca"},
}


@pytest.fixture(scope="module")
def rosters() -> dict[str, pd.DataFrame]:
    if not (player_scores.DATA_DIR / "appearances.csv.gz").exists():
        pytest.skip("dataset player-scores non importato (workflow Actions)")
    out = {}
    for lg in LEAGUES:
        snap = database.read_snapshot(database.snapshot_path(lg))
        snap["season"] = snap["season"].astype(str)
        out[lg] = player_scores.league_rosters(lg, snap)   # ValueError se orfani
    return out


def test_club_tutti_agganciati(rosters):
    """league_rosters solleva ValueError sugli orfani: se arriva qui, zero."""
    for lg, r in rosters.items():
        assert len(r) > 4000, f"{lg}: rosa sospettosamente piccola"
        assert r["season"].nunique() == 9


def test_coda_covid_non_trabocca(rosters):
    """Le retrocesse della 2019-20 NON devono avere una cella 2020-21."""
    for lg, r in rosters.items():
        teams_2021 = set(r.loc[r["season"] == "2021", "team"])
        leaked = RELEGATED_1920[lg] & teams_2021
        assert not leaked, f"{lg}: coda COVID traboccata nella 2021: {leaked}"


@pytest.mark.parametrize("league", LEAGUES)
def test_snapshot_copertura_post_refill(league):
    snap = database.read_snapshot(database.snapshot_path(league))
    snap["season"] = snap["season"].astype(str)
    both = snap["home_squad_value"].notna() & snap["away_squad_value"].notna()
    per = both.groupby(snap["season"]).mean()
    concluse = per.drop(index="2526", errors="ignore")
    assert (concluse >= 0.95).all(), f"{league}: {concluse[concluse < 0.95]}"
    if "2526" in per.index:                     # stagione in corso: buchi onesti
        assert per["2526"] >= 0.40, f"{league}: 2526 a {per['2526']:.0%}"
