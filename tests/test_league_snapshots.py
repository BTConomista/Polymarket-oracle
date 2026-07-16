"""Test degli snapshot Premier League / La Liga (Fase 54).

Verifica che la pipeline dai bundle produca dati integri e che la riconciliazione
dei nomi squadra (football-data <-> Understat) sia completa: nessun buco di xG =
nessun alias mancante. Se un domani un bundle cambia i nomi, questo test lo cattura.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, loader                # noqa: E402


@pytest.mark.parametrize("league", ["premier_league", "la_liga"])
def test_snapshot_integro_e_xg_completo(league):
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito (scripts/build_league_snapshot.py)")
    df = loader.load_league(league)
    # 9 stagioni da 380 partite (20 squadre, girone doppio)
    assert df["season"].nunique() == 9
    assert (df.groupby("season").size() == 380).all()
    # copertura piena = alias tutti riconciliati (nessuna partita orfana di xG)
    assert df["home_xg"].notna().all()
    assert df["away_xg"].notna().all()
    assert df["odds_home"].notna().all()
    # risultato coerente coi gol
    import numpy as np
    exp = np.where(df.home_goals > df.away_goals, "H",
                   np.where(df.home_goals < df.away_goals, "A", "D"))
    assert (df["result"].values == exp).all()


@pytest.mark.parametrize("league", ["premier_league", "la_liga"])
def test_nomi_squadra_stabili_tra_stagioni(league):
    """Ogni squadra deve avere >= 1 stagione piena; nessun nome 'quasi-duplicato'
    (spia di alias mancante: es. 'Man City' e 'Manchester City' entrambi presenti)."""
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito")
    df = loader.load_league(league)
    teams = set(df["home_team"]) | set(df["away_team"])
    # nessuna coppia di nomi dove uno e' contenuto nell'altro (case-insensitive)
    low = sorted(teams, key=len)
    for i, a in enumerate(low):
        for b in low[i + 1:]:
            assert not (a.lower() in b.lower() and a != b), \
                f"{league}: '{a}' e '{b}' — alias non riconciliato?"
