"""Test del simulatore di stagione (Fase 89): classifica, spareggi, Monte Carlo.

Il test piu' importante e' quello sugli SCONTRI DIRETTI: nella Liga 2025-26
Levante e Mallorca chiudono entrambe a 42 punti e la regola ufficiale (scontri
diretti PRIMA della differenza reti) decide che retrocede Mallorca — il che
cambia la composizione della lega 2026-27. Un ordinamento per sola differenza
reti darebbe la risposta sbagliata.
"""
import itertools

import numpy as np
import pandas as pd
import pytest

from src.models.season_sim import (
    final_table, league_tiebreak, round_robin, simulate_season,
)


def _matches(rows):
    """rows: (home, away, hg, ag) -> DataFrame nello schema interno minimo."""
    return pd.DataFrame(
        [{"date": pd.Timestamp("2025-08-01") + pd.Timedelta(days=i),
          "home_team": h, "away_team": a, "home_goals": hg, "away_goals": ag}
         for i, (h, a, hg, ag) in enumerate(rows)])


# ------------------------------------------------------- classifica di base --
def test_final_table_points_and_goals():
    df = _matches([("A", "B", 2, 0), ("B", "A", 1, 1)])
    t = final_table(df, "serie_a")
    assert t.loc["A", "pts"] == 4 and t.loc["B", "pts"] == 1
    assert t.loc["A", "gf"] == 3 and t.loc["A", "ga"] == 1
    assert t.loc["A", "gd"] == 2 and t.loc["B", "gd"] == -2
    assert list(t.index) == ["A", "B"]


# ------------------------------------------------------------- gli spareggi --
def test_tiebreak_head_to_head_wins_over_goal_difference():
    """A e B a pari punti (8), SOLE due in testa: A vince gli scontri diretti
    (4 punti a 1) ma B ha la differenza reti migliore (+5 vs +1).
    Serie A/Liga (scontri diretti) -> A davanti; Premier (DR) -> B davanti."""
    rows = [
        ("A", "B", 1, 0), ("B", "A", 0, 0),     # scontri diretti: A 4, B 1
        ("A", "C", 0, 0), ("C", "A", 0, 0),
        ("A", "D", 0, 0), ("D", "A", 0, 0),
        ("B", "C", 4, 0), ("C", "B", 0, 0),
        ("B", "D", 3, 0), ("D", "B", 1, 0),
        ("C", "D", 0, 0), ("D", "C", 0, 0),
    ]
    df = _matches(rows)
    t_it = final_table(df, "serie_a")
    t_en = final_table(df, "premier_league")
    assert t_it.loc["A", "pts"] == t_it.loc["B", "pts"]        # davvero a pari punti
    assert t_it.loc["B", "gd"] > t_it.loc["A", "gd"]           # B ha la DR migliore
    assert list(t_it.index).index("A") < list(t_it.index).index("B")   # h2h: A
    assert list(t_en.index).index("B") < list(t_en.index).index("A")   # DR: B


def test_tiebreak_rules_per_league():
    assert league_tiebreak("serie_a")[0] == "h2h"
    assert league_tiebreak("la_liga")[0] == "h2h"
    assert league_tiebreak("premier_league")[0] == "gd"
    assert league_tiebreak("lega_ignota") == ("gd", "gf")


def test_real_case_levante_mallorca_la_liga_2526():
    """Caso reale: entrambe 42 punti; Levante vince gli scontri diretti (4-1) e
    resta in Liga, Mallorca retrocede. Con la sola differenza reti (Mallorca -10
    vs Levante -14) l'ordine sarebbe INVERTITO."""
    pytest.importorskip("pandas")
    from src.data import loader
    df = loader.load_league("la_liga")
    season = df[df["season"] == "2526"]
    if season.empty:
        pytest.skip("snapshot La Liga 2526 non disponibile")
    t = final_table(season, "la_liga")
    pos = list(t.index)
    assert t.loc["Levante", "pts"] == t.loc["Mallorca", "pts"], "il caso non e' piu' a pari punti"
    assert t.loc["Mallorca", "gd"] > t.loc["Levante", "gd"], "la DR non e' piu' a favore di Mallorca"
    assert pos.index("Levante") < pos.index("Mallorca"), "gli scontri diretti non sono applicati"


# ------------------------------------------------------------- girone doppio --
def test_round_robin_is_complete_and_symmetric():
    teams = ["A", "B", "C", "D"]
    fx = round_robin(teams)
    assert len(fx) == 4 * 3                      # n*(n-1)
    assert len(set(fx)) == len(fx)               # nessun doppione
    for h, a in itertools.combinations(teams, 2):
        assert (h, a) in fx and (a, h) in fx     # andata e ritorno


# ---------------------------------------------------------------- Monte Carlo --
class _StubModel:
    """Modello finto: la squadra 'A' vince sempre 1-0 in casa e in trasferta."""
    fitted = True
    max_goals = 3
    attack = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}

    def predict_match(self, home, away):
        M = np.zeros((4, 4))
        if home == "A":
            M[1, 0] = 1.0
        elif away == "A":
            M[0, 1] = 1.0
        else:
            M[0, 0] = 1.0          # fra le altre sempre 0-0
        return type("P", (), {"score_matrix": M})()


def test_simulate_season_degenerate_model():
    teams = ["A", "B", "C"]
    out = simulate_season(_StubModel(), round_robin(teams), teams,
                          league_key="serie_a", n_sims=200, seed=1)
    i = out["teams"].index("A")
    assert out["champion_prob"][i] == 1.0                 # A vince sempre
    assert out["champion_prob"].sum() == pytest.approx(1.0)
    assert out["points"][:, i].min() == 12                # 4 partite vinte
    assert out["tie_rate"] == 0.0
    assert (out["rank"][:, i] == 1).all()


def test_simulate_season_shapes_and_normalisation():
    teams = ["A", "B", "C", "D"]
    out = simulate_season(_StubModel(), round_robin(teams), teams, n_sims=50, seed=3)
    assert out["points"].shape == (50, 4)
    assert out["rank"].shape == (50, 4)
    assert out["champion_prob"].sum() == pytest.approx(1.0)
    # ogni simulazione assegna le posizioni 1..4 esattamente una volta
    for s in range(50):
        assert sorted(out["rank"][s]) == [1, 2, 3, 4]


def test_simulate_season_rejects_unknown_team():
    """Guardia (Fase 89): una squadra assente dal modello non deve passare in
    silenzio — erediterebbe attacco medio ma difesa 0, che NON e' la media."""
    class _Partial(_StubModel):
        attack = {"A": 0.0, "B": 0.0}          # manca "C"
    with pytest.raises(ValueError, match="assenti dal modello"):
        simulate_season(_Partial(), round_robin(["A", "B", "C"]), ["A", "B", "C"],
                        n_sims=10, seed=0)
