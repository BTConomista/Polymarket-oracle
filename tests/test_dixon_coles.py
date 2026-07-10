"""Test del modello Dixon-Coles e delle metriche.

Verifichiamo proprieta' matematiche che DEVONO valere sempre, cosi' un domani
una modifica che rompe il modello viene subito segnalata.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import metrics
from src.models.dixon_coles import DixonColesModel


def _synthetic_matches(n_seasons: int = 3, seed: int = 0) -> pd.DataFrame:
    """Genera partite finte con una gerarchia di forza nota.

    "Forte" segna tanto e subisce poco, "Debole" il contrario. Serve a verificare
    che il modello RECUPERI la gerarchia (Forte deve risultare piu' probabile).
    """
    rng = np.random.default_rng(seed)
    teams = ["Forte", "Media", "Debole"]
    strength = {"Forte": 1.6, "Media": 1.1, "Debole": 0.6}  # gol attesi base
    rows = []
    day = pd.Timestamp("2020-01-01")
    for _ in range(n_seasons):
        for home in teams:
            for away in teams:
                if home == away:
                    continue
                lam = strength[home] * 1.2      # vantaggio casa
                mu = strength[away] * 0.9
                rows.append({
                    "date": day,
                    "season": "syn",
                    "league": "syn",
                    "home_team": home,
                    "away_team": away,
                    "home_goals": int(rng.poisson(lam)),
                    "away_goals": int(rng.poisson(mu)),
                    "result": "H",  # ricalcolato sotto
                    # Tiri in porta: ~3x i gol attesi (conversione ~0.33).
                    "home_sot": int(rng.poisson(lam * 3.0)),
                    "away_sot": int(rng.poisson(mu * 3.0)),
                    "odds_home": np.nan, "odds_draw": np.nan, "odds_away": np.nan,
                    "odds_over25": np.nan, "odds_under25": np.nan,
                })
                day += pd.Timedelta(days=3)
    df = pd.DataFrame(rows)
    df["result"] = np.where(
        df.home_goals > df.away_goals, "H",
        np.where(df.home_goals < df.away_goals, "A", "D"))
    return df


def test_probabilities_sum_to_one():
    model = DixonColesModel(half_life_days=None).fit(_synthetic_matches())
    pred = model.predict_match("Forte", "Debole")
    assert pred.prob_home_win + pred.prob_draw + pred.prob_away_win == pytest.approx(1.0, abs=1e-6)
    assert pred.prob_over_2_5 + pred.prob_under_2_5 == pytest.approx(1.0, abs=1e-9)
    assert pred.score_matrix.sum() == pytest.approx(1.0, abs=1e-9)


def test_recovers_team_strength():
    """Il forte in casa contro il debole deve essere nettamente favorito."""
    model = DixonColesModel(half_life_days=None).fit(_synthetic_matches(n_seasons=6))
    strong_home = model.predict_match("Forte", "Debole")
    weak_home = model.predict_match("Debole", "Forte")
    assert strong_home.prob_home_win > strong_home.prob_away_win
    assert strong_home.prob_home_win > weak_home.prob_home_win
    assert model.attack["Forte"] > model.attack["Debole"]


def test_home_advantage_positive():
    model = DixonColesModel(half_life_days=None).fit(_synthetic_matches())
    # Con dati generati con vantaggio casa, il parametro deve risultare > 0.
    assert model.home_advantage > 0.0


def test_unknown_team_uses_average():
    """Una squadra mai vista non deve rompere la predizione (forza media)."""
    model = DixonColesModel(half_life_days=None).fit(_synthetic_matches())
    pred = model.predict_match("Neopromossa", "Forte")
    assert 0.0 <= pred.prob_home_win <= 1.0
    lam, mu = model.expected_goals("Neopromossa", "Neopromossa")
    assert lam > 0 and mu > 0


def test_serialization_roundtrip():
    model = DixonColesModel(half_life_days=90).fit(_synthetic_matches())
    restored = DixonColesModel.from_dict(model.to_dict())
    p1 = model.predict_match("Forte", "Media")
    p2 = restored.predict_match("Forte", "Media")
    assert p1.prob_home_win == pytest.approx(p2.prob_home_win, abs=1e-9)


def test_shrinkage_pulls_toward_average():
    """Con shrinkage>0 le stime di forza sono piu' vicine alla media (0):
    e' la regolarizzazione che riduce l'overconfidence sui dati scarsi."""
    matches = _synthetic_matches(n_seasons=2)
    plain = DixonColesModel(half_life_days=None, shrinkage=0.0).fit(matches)
    shrunk = DixonColesModel(half_life_days=None, shrinkage=5.0).fit(matches)

    def spread(model):
        vals = list(model.attack.values()) + list(model.defense.values())
        return np.std(vals)

    # La dispersione delle forze deve ridursi con lo shrinkage.
    assert spread(shrunk) < spread(plain)
    # L'ordine tra squadre deve comunque restare (Forte > Debole).
    assert shrunk.attack["Forte"] > shrunk.attack["Debole"]


def test_shots_blend_valid_and_backward_compatible():
    """Il blend gol/tiri produce probabilita' valide, e alpha=1 coincide col
    modello sui soli gol (retrocompatibilita')."""
    matches = _synthetic_matches(n_seasons=4)
    goals_only = DixonColesModel(half_life_days=None, shots_blend=1.0).fit(matches)
    blended = DixonColesModel(half_life_days=None, shots_blend=0.5).fit(matches)
    pure_shots = DixonColesModel(half_life_days=None, shots_blend=0.0).fit(matches)

    for model in (goals_only, blended, pure_shots):
        p = model.predict_match("Forte", "Debole")
        assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-6)
        assert p.prob_home_win > p.prob_away_win  # il forte in casa resta favorito

    # alpha=1 non deve nemmeno stimare il modello sul segnale secondario.
    assert goals_only.attack_sig == {}
    # alpha<1 deve averlo stimato e prodotto tassi di conversione plausibili.
    assert blended.attack_sig != {}
    assert 0.1 < blended.conv_home < 1.0


def test_rest_full_covariate_registered_and_usable():
    """La covariata `rest_full` (Fase 4e) e' registrata sulle colonne del
    calendario COMPLETO e il modello ci allena/predice producendo probabilita'
    valide. Colonne mancanti (NaN) -> contributo neutro, non rompe il fit."""
    from src.models.dixon_coles import _COVARIATES

    assert _COVARIATES["rest_full"] == (
        "home_rest_days_full", "away_rest_days_full", "identity")

    matches = _synthetic_matches(n_seasons=4)
    rng = np.random.default_rng(1)
    matches["home_rest_days_full"] = rng.integers(2, 15, len(matches)).astype(float)
    matches["away_rest_days_full"] = rng.integers(2, 15, len(matches)).astype(float)
    # Una riga senza il dato (NaN): deve degradare a neutro, non far esplodere il fit.
    matches.loc[matches.index[0], ["home_rest_days_full", "away_rest_days_full"]] = np.nan

    model = DixonColesModel(half_life_days=None, covariates=("rest_full",)).fit(matches)
    assert "rest_full" in model.beta and np.isfinite(model.beta["rest_full"])

    p = model.predict_match("Forte", "Debole",
                            features={"home_rest_days_full": 3.0,
                                      "away_rest_days_full": 10.0})
    assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-6)
    assert p.prob_home_win > p.prob_away_win  # il forte in casa resta favorito


def test_devig_sums_to_one():
    p = metrics.devig_1x2(2.0, 3.5, 4.0)
    assert p.sum() == pytest.approx(1.0, abs=1e-9)
    over, under = metrics.devig_binary(1.9, 1.95)
    assert over + under == pytest.approx(1.0, abs=1e-9)


def test_metrics_perfect_vs_wrong():
    """Una predizione perfetta deve avere log-loss migliore di una sbagliata."""
    perfect = np.array([[1.0, 0.0, 0.0]])
    wrong = np.array([[0.0, 0.0, 1.0]])
    assert metrics.log_loss_1x2(perfect, ["H"]) < metrics.log_loss_1x2(wrong, ["H"])
