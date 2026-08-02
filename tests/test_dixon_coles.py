"""Test del modello Dixon-Coles e delle metriche.

Verifichiamo proprieta' matematiche che DEVONO valere sempre, cosi' un domani
una modifica che rompe il modello viene subito segnalata.
"""

import math
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


def test_promoted_prior_weakens_newcomer():
    """Il prior di cold-start (Fase 7) fa partire una neopromossa senza storico
    come piu' debole della media (attacco<0, difesa>0), rendendo piu' probabile
    che una squadra forte le vinca. Con prior=None, la neopromossa e' sconosciuta
    -> media (retrocompatibilita')."""
    matches = _synthetic_matches(n_seasons=4)

    # Senza prior: "Neo" non ha storico -> trattata come media.
    base = DixonColesModel(half_life_days=None, shrinkage=1.5).fit(matches)
    p_base = base.predict_match("Forte", "Neo")

    # Con prior: "Neo" entra nel modello e parte dal prior (piu' debole).
    prior = DixonColesModel(half_life_days=None, shrinkage=1.5,
                            promoted_prior=(0.23, 0.23))
    prior.fit(matches, promoted_teams={"Neo"})
    assert "Neo" in prior.teams
    assert prior.attack["Neo"] < 0.0        # segna meno della media
    assert prior.defense["Neo"] > 0.0       # subisce piu' della media
    p_prior = prior.predict_match("Forte", "Neo")
    assert p_prior.prob_home_win > p_base.prob_home_win

    # Retrocompat: senza promoted_teams il prior non cambia le squadre note.
    same = DixonColesModel(half_life_days=None, shrinkage=1.5,
                           promoted_prior=(0.23, 0.23)).fit(matches)
    p_same = same.predict_match("Forte", "Debole")
    assert abs(p_same.prob_home_win - base.predict_match("Forte", "Debole").prob_home_win) < 1e-6


def test_promoted_prior_serialization_roundtrip():
    matches = _synthetic_matches(n_seasons=3)
    model = DixonColesModel(half_life_days=None, promoted_prior=(0.2, 0.25))
    model.fit(matches, promoted_teams={"Neo"})
    restored = DixonColesModel.from_dict(model.to_dict())
    assert restored.promoted_prior == (0.2, 0.25)
    p1 = model.predict_match("Forte", "Neo")
    p2 = restored.predict_match("Forte", "Neo")
    assert abs(p1.prob_home_win - p2.prob_home_win) < 1e-9


def test_draw_inflation_boosts_draws_and_roundtrips():
    """L'inflazione della diagonale (Fase 12b): su dati con ECCESSO di pareggi il
    fit trova phi>0 e alza P(pari); probabilita' valide; serializzazione ok.
    draw_inflation=False lascia phi=0 e il modello identico a prima."""
    # Dataset con molti pareggi (piu' di quanti ne preveda un Poisson indipendente).
    rng = np.random.default_rng(3)
    teams = ["A", "B", "C"]
    rows, day = [], pd.Timestamp("2021-01-01")
    for _ in range(60):
        h, a = rng.choice(teams, 2, replace=False)
        if rng.random() < 0.45:            # 45% pareggi forzati
            g = int(rng.integers(0, 3)); hg = ag = g
        else:
            hg, ag = int(rng.poisson(1.3)), int(rng.poisson(1.1))
        rows.append(dict(date=day, season="s", league="l", home_team=h, away_team=a,
                         home_goals=hg, away_goals=ag, result="H",
                         home_sot=0, away_sot=0, odds_home=np.nan, odds_draw=np.nan,
                         odds_away=np.nan, odds_over25=np.nan, odds_under25=np.nan))
        day += pd.Timedelta(days=3)
    df = pd.DataFrame(rows)
    df["result"] = np.where(df.home_goals > df.away_goals, "H",
                            np.where(df.home_goals < df.away_goals, "A", "D"))

    base = DixonColesModel(half_life_days=None, shots_blend=1.0).fit(df)
    infl = DixonColesModel(half_life_days=None, shots_blend=1.0,
                           draw_inflation=True).fit(df)
    assert base.draw_phi == 0.0
    assert infl.draw_phi > 0.0                       # eccesso di pareggi -> phi>0
    p0, p1 = base.predict_match("A", "B"), infl.predict_match("A", "B")
    assert p1.prob_draw > p0.prob_draw               # pareggio piu' probabile
    assert p1.prob_home_win + p1.prob_draw + p1.prob_away_win == pytest.approx(1.0, abs=1e-6)

    restored = DixonColesModel.from_dict(infl.to_dict())
    assert restored.draw_phi == pytest.approx(infl.draw_phi)
    assert restored.predict_match("A", "B").prob_draw == pytest.approx(p1.prob_draw, abs=1e-9)


def test_draw_balance_conditioned_on_lambda_mu_diff():
    """Fase 35: l'inflazione-pareggio condizionata all'equilibrio phi(lam,mu)=
    phi0*exp(-kappa*|lam-mu|). Su dati con eccesso di pareggi tra squadre
    pari-livello, il fit trova phi0>0; le probabilita' restano valide; il
    round-trip conserva phi0/kappa. draw_balance=False lascia phi0=0. Non si
    combina con draw_inflation ne' con dynamic_rho (ValueError)."""
    rng = np.random.default_rng(7)
    teams = ["A", "B", "C"]                    # forze simili -> match equilibrati
    rows, day = [], pd.Timestamp("2021-01-01")
    for _ in range(80):
        h, a = rng.choice(teams, 2, replace=False)
        if rng.random() < 0.45:                # eccesso di pareggi
            g = int(rng.integers(0, 3)); hg = ag = g
        else:
            hg, ag = int(rng.poisson(1.2)), int(rng.poisson(1.1))
        rows.append(dict(date=day, season="s", league="l", home_team=h, away_team=a,
                         home_goals=hg, away_goals=ag, result="H",
                         home_sot=0, away_sot=0, odds_home=np.nan, odds_draw=np.nan,
                         odds_away=np.nan, odds_over25=np.nan, odds_under25=np.nan))
        day += pd.Timedelta(days=3)
    df = pd.DataFrame(rows)
    df["result"] = np.where(df.home_goals > df.away_goals, "H",
                            np.where(df.home_goals < df.away_goals, "A", "D"))

    base = DixonColesModel(half_life_days=None, shots_blend=1.0).fit(df)
    bal = DixonColesModel(half_life_days=None, shots_blend=1.0, draw_balance=True).fit(df)
    assert base.draw_phi0 == 0.0
    assert bal.draw_phi0 > 0.0                        # eccesso di pareggi -> phi0>0
    p0, p1 = base.predict_match("A", "B"), bal.predict_match("A", "B")
    assert p1.prob_draw > p0.prob_draw               # squadre equilibrate -> piu' pari
    assert p1.prob_home_win + p1.prob_draw + p1.prob_away_win == pytest.approx(1.0, abs=1e-6)

    restored = DixonColesModel.from_dict(bal.to_dict())
    assert restored.draw_phi0 == pytest.approx(bal.draw_phi0)
    assert restored.draw_kappa == pytest.approx(bal.draw_kappa)
    assert restored.predict_match("A", "B").prob_draw == pytest.approx(p1.prob_draw, abs=1e-9)

    with pytest.raises(ValueError):
        DixonColesModel(draw_balance=True, draw_inflation=True)
    with pytest.raises(ValueError):
        DixonColesModel(draw_balance=True, dynamic_rho=True)
    # draw_inflation + dynamic_rho: incoerenti (phi fittato sul rho scalare,
    # applicato col rho dinamico) -> vietato per simmetria con le guardie sopra.
    with pytest.raises(ValueError):
        DixonColesModel(draw_inflation=True, dynamic_rho=True)


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


def test_dynamic_rho_off_identico_al_classico():
    """Con dynamic_rho=False (default) il modello deve essere IDENTICO a prima
    (rho_slope=0, rho_center=0): regressione sulla Fase 18."""
    matches = _synthetic_matches(n_seasons=3)
    base = DixonColesModel(half_life_days=None).fit(matches)
    assert base.rho_slope == 0.0 and base.rho_center == 0.0
    p = base.predict_match("A", "B")
    assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-9)


def test_dynamic_rho_fitta_slope_e_prevede_coerente():
    matches = _synthetic_matches(n_seasons=4)
    dyn = DixonColesModel(half_life_days=None, dynamic_rho=True).fit(matches)
    # Il centro e' la media (pesata) dei gol totali del training.
    assert dyn.rho_center == pytest.approx(
        (matches.home_goals + matches.away_goals).mean(), abs=0.2)
    assert -0.15 <= dyn.rho_slope <= 0.15            # entro i bound del fit
    p = dyn.predict_match("A", "B")
    assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-9)
    assert 0.0 < p.prob_draw < 1.0


def test_dynamic_rho_serialization_roundtrip():
    matches = _synthetic_matches(n_seasons=3)
    dyn = DixonColesModel(half_life_days=None, dynamic_rho=True).fit(matches)
    restored = DixonColesModel.from_dict(dyn.to_dict())
    assert restored.rho_slope == pytest.approx(dyn.rho_slope)
    assert restored.rho_center == pytest.approx(dyn.rho_center)
    a, b = dyn.predict_match("A", "B"), restored.predict_match("A", "B")
    assert a.prob_draw == pytest.approx(b.prob_draw, abs=1e-9)


def test_add_stakes_solo_a_fine_stagione():
    """La posta in palio 'decisa' (settled=1) deve comparire solo nel finale:
    a inizio stagione tutte in corsa (0), verso la 38a alcune decise."""
    from src.data import loader
    m = loader.load_league("serie_a")
    assert {"home_settled", "away_settled"} <= set(m.columns)
    assert m["home_settled"].isin([0.0, 1.0]).all()
    # per una stagione: quota decise a inizio (g<=25) vs fine (g>=36)
    s = m[m["season"] == "2223"].sort_values("date").reset_index(drop=True)
    g = np.minimum(np.arange(len(s)) // 10 + 1, 38)
    early = s["home_settled"].to_numpy()[g <= 25].mean()
    late = s["home_settled"].to_numpy()[g >= 36].mean()
    assert early == 0.0          # nessuna decisa a inizio/meta' stagione
    assert late > early          # alcune decise nel finale


def test_stakes_covariata_usabile():
    """Il modello deve accettare la covariata 'stakes' senza errori."""
    from src.data import loader
    m = loader.load_league("serie_a", ["2122", "2223"])
    model = DixonColesModel(half_life_days=365, shrinkage=1.5,
                            covariates=("stakes",)).fit(m)
    assert "stakes" in model.beta
    p = model.predict_match(m.iloc[-1]["home_team"], m.iloc[-1]["away_team"],
                            features=m.iloc[-1].to_dict())
    assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-6)


def test_add_style_luck_rolling_no_lookahead():
    """PPDA/deep/luck rolling: colonne presenti, prima gara di ogni squadra NaN,
    luck (gol-xG) di media ~0."""
    from src.data import loader
    m = loader.load_league("serie_a")
    for c in ["home_ppda_roll", "away_ppda_roll", "home_deep_roll",
              "away_deep_roll", "home_luck", "away_luck"]:
        assert c in m.columns
    # la prima partita in assoluto ha entrambe le squadre senza storico -> NaN
    first = m.sort_values("date").iloc[0]
    assert pd.isna(first["home_ppda_roll"]) and pd.isna(first["away_luck"])
    assert abs(m["home_luck"].mean()) < 0.3          # gol-xG ~ 0


def test_style_luck_covariate_usabile():
    from src.data import loader
    m = loader.load_league("serie_a", ["2122", "2223"])
    model = DixonColesModel(half_life_days=365, shrinkage=1.5,
                            covariates=("ppda", "deep", "luck")).fit(m)
    for c in ("ppda", "deep", "luck"):
        assert c in model.beta


def test_promoted_prior_lands_exactly_on_prior():
    """Il docstring promette: «una neopromossa con 0 partite finisce ESATTAMENTE
    sul prior». Regressione dall'audit Fase 92: il vincolo di identificabilita'
    (media attacco = 0) si scaricava sulle squadre senza dati — le uniche senza
    curvatura di verosimiglianza — e l'attacco atterrava fra -0.28 e -0.39 invece
    di -0.23, con un valore diverso per stagione. La difesa era esatta: e'
    l'asimmetria fra le due colonne che smaschera il difetto."""
    import numpy as np
    import pandas as pd
    from src.models.dixon_coles import DixonColesModel
    rng = np.random.default_rng(0)
    teams = [f"T{i}" for i in range(8)]
    rows = []
    d0 = pd.Timestamp("2024-08-01")
    for k, (h, a) in enumerate([(h, a) for h in teams for a in teams if h != a]):
        rows.append(dict(date=d0 + pd.Timedelta(days=k), home_team=h, away_team=a,
                         home_goals=int(rng.poisson(1.4)), away_goals=int(rng.poisson(1.1))))
    df = pd.DataFrame(rows)
    delta = 0.23
    m = DixonColesModel(half_life_days=365, shrinkage=1.5, promoted_prior=(delta, delta))
    m.fit(df, as_of_date=df["date"].max() + pd.Timedelta(days=1),
          promoted_teams={"NUOVA"})                     # zero partite nei dati
    assert m.attack["NUOVA"] == pytest.approx(-delta, abs=1e-3), \
        f"attacco {m.attack['NUOVA']:.4f} invece di {-delta}"
    assert m.defense["NUOVA"] == pytest.approx(+delta, abs=1e-3), \
        f"difesa {m.defense['NUOVA']:.4f} invece di {delta}"


# --------------------------------------------------------------------------- #
# La regola non negoziabile n.1 del progetto: NIENTE LOOK-AHEAD.
# Audit Fase 92: nessun test passava `as_of_date` a fit(), e mutando il filtro
# da `date < as_of` a `date <= as_of` la suite restava tutta verde MENTRE il
# log-loss migliorava del 40% del gap col mercato — una contaminazione futura si
# sarebbe presentata come una scoperta.
# --------------------------------------------------------------------------- #
def _toy_two_eras():
    """Due ere opposte: prima A domina, dopo la data di taglio domina B."""
    import pandas as pd
    rows, d0 = [], pd.Timestamp("2024-01-01")
    for k in range(30):                       # era 1: A segna tanto, B poco
        rows.append(dict(date=d0 + pd.Timedelta(days=k), home_team="A", away_team="B",
                         home_goals=4, away_goals=0))
    cut = d0 + pd.Timedelta(days=100)
    for k in range(30):                       # era 2 (dopo il taglio): invertita
        rows.append(dict(date=cut + pd.Timedelta(days=k), home_team="A", away_team="B",
                         home_goals=0, away_goals=4))
    return pd.DataFrame(rows), cut


def test_fit_ignores_matches_on_and_after_as_of_date():
    """Le partite CON DATA >= as_of_date non devono entrare nella stima."""
    import pandas as pd
    from src.models.dixon_coles import DixonColesModel
    df, cut = _toy_two_eras()
    m = DixonColesModel(half_life_days=None).fit(df, as_of_date=cut)
    lam, mu = m.expected_goals("A", "B")
    # con i soli dati dell'era 1, A deve segnare MOLTO piu' di B
    assert lam > 3 * mu, f"lam={lam:.3f} mu={mu:.3f}: sembra aver visto il futuro"

    # la partita ESATTAMENTE sulla data di taglio non deve entrare (filtro <, non <=)
    edge = pd.DataFrame([dict(date=cut, home_team="A", away_team="B",
                              home_goals=0, away_goals=9)])
    m2 = DixonColesModel(half_life_days=None).fit(pd.concat([df, edge]), as_of_date=cut)
    assert m2.expected_goals("A", "B") == pytest.approx(m.expected_goals("A", "B"), abs=1e-6), \
        "una partita datata esattamente as_of_date e' entrata nel fit"


def test_fit_on_full_history_sees_the_reversal():
    """Controprova: senza taglio, la stessa serie deve dare il risultato OPPOSTO.
    Senza questo, il test sopra passerebbe anche con un modello che ignora i dati."""
    from src.models.dixon_coles import DixonColesModel
    df, cut = _toy_two_eras()
    m = DixonColesModel(half_life_days=None).fit(df)         # tutta la storia
    lam, mu = m.expected_goals("A", "B")
    assert lam == pytest.approx(mu, rel=0.2), \
        f"lam={lam:.3f} mu={mu:.3f}: le due ere opposte dovrebbero compensarsi"


def test_time_decay_halves_weight_at_half_life():
    """L'emivita: peso 0.5 esatto a half_life giorni, monotonia, e None = nessun
    decadimento. Audit Fase 92: invertendo il segno dell'esponente o azzerando xi
    la suite restava verde."""
    import numpy as np
    import pandas as pd
    from src.models.dixon_coles import DixonColesModel
    as_of = pd.Timestamp("2025-01-01")
    dates = pd.Series([as_of - pd.Timedelta(days=d) for d in [0, 365, 730]])
    w = DixonColesModel(half_life_days=365)._time_weights(dates, as_of)
    assert w[0] == pytest.approx(1.0)
    assert w[1] == pytest.approx(0.5, abs=1e-9)      # esattamente meta'
    assert w[2] == pytest.approx(0.25, abs=1e-9)
    assert w[0] > w[1] > w[2]                        # monotonia: piu' vecchio = meno peso
    wn = DixonColesModel(half_life_days=None)._time_weights(dates, as_of)
    assert np.allclose(wn, 1.0)


# --------------------------------------------------------------------- #
# Le covariate: il termine che si poteva rendere inerte senza accorgersene
# --------------------------------------------------------------------- #
def _modello_con_covariata(beta: float = 0.5, media: float = 0.0,
                           dev: float = 1.0) -> DixonColesModel:
    """Un modello con UNA covariata e i parametri messi a mano.

    Non lo si fitta di proposito: qui non si vuole verificare che la stima
    funzioni, ma che la FORMULA sia quella dichiarata. Con beta, media e
    deviazione noti il contributo si calcola a mano e si inchioda.
    """
    m = DixonColesModel(covariates=("squad_value",))
    m.beta = {"squad_value": beta}
    m.cov_mean = {"squad_value": media}
    m.cov_std = {"squad_value": dev}
    return m


def test_cov_term_valore_esatto():
    """beta * (z_casa - z_ospite), con z = (log(valore) - media) / dev.

    Valori scelti perche' il logaritmo venga tondo: e^2 e e^1 danno z grezzi 2 e
    1, quindi con media 0, dev 1 e beta 0.5 il termine vale 0.5*(2-1) = 0.5.

    Audit Fase 137: `_cov_term` non aveva alcun test: sostituirlo con
    `return 0.0` lasciava verde l'intera suite del modello. E' il termine da cui
    passano TUTTE le covariate di partita della Fase 4c (valore rosa, assenze,
    riposo, forma, posta in palio, PPDA, deep, fortuna), cioe' ogni esperimento
    che ha concluso «questo dato non aggiunge nulla»: se il termine fosse
    inerte, quelle conclusioni misurerebbero soltanto se stesse.
    """
    m = _modello_con_covariata(beta=0.5)
    feats = {"home_squad_value": math.e ** 2, "away_squad_value": math.e}
    assert m._cov_term(feats) == pytest.approx(0.5)

    # la standardizzazione entra davvero: con dev 2 il contributo si dimezza
    m2 = _modello_con_covariata(beta=0.5, media=0.0, dev=2.0)
    assert m2._cov_term(feats) == pytest.approx(0.25)

    # e la media si semplifica, perche' il termine e' una DIFFERENZA di z
    m3 = _modello_con_covariata(beta=0.5, media=10.0, dev=1.0)
    assert m3._cov_term(feats) == pytest.approx(0.5)


def test_cov_term_antisimmetrico_e_neutro_a_parita():
    """Due squadre col medesimo valore non devono spostare nulla, e invertirle
    deve invertire il segno: e' cio' che rende la covariata un VANTAGGIO
    RELATIVO e non un livello."""
    m = _modello_con_covariata(beta=0.5)
    pari = {"home_squad_value": 100.0, "away_squad_value": 100.0}
    assert m._cov_term(pari) == pytest.approx(0.0)

    a = {"home_squad_value": math.e ** 2, "away_squad_value": math.e}
    b = {"home_squad_value": math.e, "away_squad_value": math.e ** 2}
    assert m._cov_term(a) == pytest.approx(-m._cov_term(b))


def test_cov_term_spento_quando_non_c_e_nulla_da_dire():
    """Senza covariate, senza beta o senza feature il termine e' 0 — e dev'esserlo
    davvero, altrimenti un modello «senza covariate» non sarebbe piu' il modello
    base e ogni confronto con lui sarebbe falsato."""
    base = DixonColesModel()
    assert base._cov_term({"home_squad_value": 1e9, "away_squad_value": 1.0}) == 0.0

    m = _modello_con_covariata()
    assert m._cov_term(None) == 0.0
    # valore mancante -> z neutro (0), non NaN e non un'esplosione
    assert m._cov_term({"home_squad_value": math.e}) == pytest.approx(0.5)
    assert not math.isnan(m._cov_term({}))


def test_cov_term_entra_nei_tassi_con_segno_opposto():
    """La covariata alza il tasso della casa ESATTAMENTE quanto abbassa quello
    dell'ospite: lam = exp(... + cov), mu = exp(... - cov).

    E' il collegamento fra il termine e i gol attesi: senza questo test si
    potrebbe testare `_cov_term` da solo e non accorgersi che `expected_goals`
    ha smesso di usarlo.
    """
    m = _modello_con_covariata(beta=0.5)
    m.teams = ["Casa", "Ospite"]
    m.attack = {"Casa": 0.0, "Ospite": 0.0}
    m.defense = {"Casa": 0.0, "Ospite": 0.0}
    m.home_advantage = 0.0

    feats = {"home_squad_value": math.e ** 2, "away_squad_value": math.e}
    lam, mu = m.expected_goals("Casa", "Ospite", feats)
    assert lam == pytest.approx(math.exp(0.5))
    assert mu == pytest.approx(math.exp(-0.5))
    assert lam * mu == pytest.approx(1.0)          # il prodotto resta invariato

    # e senza feature si torna al modello base
    lam0, mu0 = m.expected_goals("Casa", "Ospite")
    assert lam0 == pytest.approx(1.0) and mu0 == pytest.approx(1.0)
