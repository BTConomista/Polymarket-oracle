"""Test del simulatore di stagione (Fase 89): classifica, spareggi, Monte Carlo.

Il test piu' importante e' quello sugli SCONTRI DIRETTI: nella Liga 2025-26
Levante, Osasuna e Mallorca chiudono TUTTE E TRE a 42 punti, e la regola
ufficiale (classifica avulsa fra le squadre a pari punti, PRIMA della differenza
reti generale) le ordina 16a/17a/18a facendo retrocedere Mallorca — il che cambia
la composizione della lega 2026-27. Con la sola differenza reti l'ordine sarebbe
invertito e retrocederebbe Levante.

NB (audit Fase 90): il caso e' una parita' a TRE, non il duello Levante-Mallorca
"4-1" raccontato inizialmente; il test lo verifica su tutte e tre le squadre,
altrimenti passerebbe anche con una avulsa implementata male.
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


def test_real_case_three_way_tie_la_liga_2526():
    """Caso reale: Levante, Osasuna e Mallorca tutte a 42 punti. La classifica
    avulsa fra le tre (Levante 7 - Osasuna 5 - Mallorca 3) le ordina in
    quell'ordine; con la sola differenza reti generale (Osasuna -6, Mallorca -10,
    Levante -14) l'ordine sarebbe ESATTAMENTE INVERTITO e retrocederebbe Levante."""
    pytest.importorskip("pandas")
    from src.data import loader
    df = loader.load_league("la_liga")
    season = df[df["season"] == "2526"]
    if season.empty:
        pytest.skip("snapshot La Liga 2526 non disponibile")
    t = final_table(season, "la_liga")
    pos = list(t.index)
    tied = ["Levante", "Osasuna", "Mallorca"]
    assert {int(t.loc[x, "pts"]) for x in tied} == {42}, "il caso non e' piu' una parita' a tre"
    # la differenza reti generale darebbe l'ordine opposto: e' cio' che rende
    # il caso una prova vera della avulsa
    assert t.loc["Osasuna", "gd"] > t.loc["Mallorca", "gd"] > t.loc["Levante", "gd"]
    assert pos.index("Levante") < pos.index("Osasuna") < pos.index("Mallorca"), \
        "la classifica avulsa a TRE non e' applicata correttamente"
    assert pos[-3:] == ["Mallorca", "Girona", "Oviedo"], "retrocesse sbagliate"


def test_rank_is_consistent_with_champion():
    """`rank` deve dire 1 esattamente per la squadra che `champion_prob` premia:
    la vetta segue gli spareggi di lega, la chiave punti->DR->gol no."""
    teams = ["A", "B", "C"]
    out = simulate_season(_StubModel(), round_robin(teams), teams,
                          league_key="serie_a", n_sims=100, seed=5)
    firsts = (out["rank"] == 1).argmax(axis=1)
    assert (out["rank"] == 1).sum(axis=1).min() == 1     # un solo primo per stagione
    i = out["teams"].index("A")
    assert (firsts == i).all()


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

    def predict_match(self, home, away, features=None):
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


# --- il ramo degli spareggi DENTRO la simulazione (audit Fase 92) ------------
# Lo stub principale fa vincere sempre A 1-0: tie_rate=0 e `_resolve_sim_tie`
# non parte MAI. Serve un modello che FORZI la parita' in testa, altrimenti
# 30 righe di codice (e il fix rank/campione della Fase 90) restano non eseguite.
# I risultati sono gli STESSI del fixture gia' validato per final_table sopra:
# A e B chiudono a 8 punti, A vince gli scontri diretti (4 a 1), B ha la
# differenza reti generale migliore (+5 contro +1).
_TIE_SCORES = {
    ("A", "B"): (1, 0), ("B", "A"): (0, 0),
    ("A", "C"): (0, 0), ("C", "A"): (0, 0),
    ("A", "D"): (0, 0), ("D", "A"): (0, 0),
    ("B", "C"): (4, 0), ("C", "B"): (0, 0),
    ("B", "D"): (3, 0), ("D", "B"): (1, 0),
    ("C", "D"): (0, 0), ("D", "C"): (0, 0),
}


class _TieModel:
    """Ogni incontro ha un punteggio DETERMINISTICO (probabilita' 1)."""
    fitted = True
    max_goals = 5
    attack = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}

    def predict_match(self, home, away, features=None):
        M = np.zeros((6, 6))
        hg, ag = _TIE_SCORES[(home, away)]
        M[hg, ag] = 1.0
        return type("P", (), {"score_matrix": M})()


def test_simulated_tie_is_resolved_by_league_rule():
    """A e B finiscono a pari punti in testa: la Serie A usa la classifica avulsa
    (A avanti, 4 punti a 1 negli scontri diretti), la Premier la differenza reti
    generale (B avanti, +5 contro +1). Senza questo test il ramo `_resolve_sim_tie`
    non veniva MAI eseguito e le mutazioni che lo cancellano passavano."""
    teams = ["A", "B", "C", "D"]
    fx = round_robin(teams)
    out_it = simulate_season(_TieModel(), fx, teams, league_key="serie_a",
                             n_sims=40, seed=1)
    out_en = simulate_season(_TieModel(), fx, teams, league_key="premier_league",
                             n_sims=40, seed=1)
    ia, ib = teams.index("A"), teams.index("B")
    assert out_it["tie_rate"] == 1.0, "il fixture non produce piu' la parita' in testa"
    assert out_it["points"][:, ia].max() == out_it["points"][:, ib].max() == 8
    assert out_it["champion_prob"][ia] == 1.0, "classifica avulsa non applicata (Serie A)"
    assert out_en["champion_prob"][ib] == 1.0, "differenza reti non applicata (Premier)"
    # e `rank` deve seguire il campione, non la sola differenza reti
    assert (out_it["rank"][:, ia] == 1).all()
    assert (out_en["rank"][:, ib] == 1).all()


# --- la deriva di forza in-stagione (Fase 94) --------------------------------
def _toy_league(seed=0):
    """Campionato giocattolo a 6 squadre con forze chiaramente diverse."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(6)]
    strength = {t: 1.8 - 0.22 * i for i, t in enumerate(teams)}   # T0 la piu' forte
    rows, d0 = [], pd.Timestamp("2024-08-01")
    for k, (h, a) in enumerate([(h, a) for h in teams for a in teams if h != a]):
        for rep in range(6):                     # storico sufficiente a stimare
            rows.append(dict(date=d0 + pd.Timedelta(days=k * 6 + rep),
                             home_team=h, away_team=a,
                             home_goals=int(rng.poisson(strength[h])),
                             away_goals=int(rng.poisson(strength[a]))))
    return teams, pd.DataFrame(rows)


def test_drift_zero_is_identical_to_no_drift():
    """drift_sd=0 non deve cambiare NULLA rispetto al comportamento storico."""
    from src.models.dixon_coles import DixonColesModel
    teams, df = _toy_league()
    m = DixonColesModel(half_life_days=None).fit(df)
    fx = round_robin(teams)
    a = simulate_season(m, fx, teams, n_sims=300, seed=7)
    b = simulate_season(m, fx, teams, n_sims=300, seed=7, drift_sd=0.0)
    assert np.array_equal(a["champion_prob"], b["champion_prob"])
    assert np.array_equal(a["points"], b["points"])


def test_drift_widens_the_table_and_flattens_the_favourite():
    """La deriva e' INCERTEZZA in piu': deve (a) allargare la dispersione dei
    punti finali e (b) abbassare la probabilita' del favorito. E' la correzione
    del difetto misurato alla Fase 94 (classifica simulata troppo schiacciata,
    favorito troppo sicuro)."""
    from src.models.dixon_coles import DixonColesModel
    teams, df = _toy_league()
    m = DixonColesModel(half_life_days=None).fit(df)
    fx = round_robin(teams)
    base = simulate_season(m, fx, teams, n_sims=2000, seed=11, drift_sd=0.0)
    drift = simulate_season(m, fx, teams, n_sims=2000, seed=11,
                            drift_sd=0.35, n_drift_draws=100)
    sd_base = base["points"].std(axis=1).mean()
    sd_drift = drift["points"].std(axis=1).mean()
    assert sd_drift > sd_base, \
        f"la deriva non allarga la classifica ({sd_drift:.2f} vs {sd_base:.2f})"
    assert drift["champion_prob"].max() < base["champion_prob"].max(), \
        "la deriva non abbassa la probabilita' del favorito"
    # e resta una distribuzione di probabilita' valida
    assert drift["champion_prob"].sum() == pytest.approx(1.0)
