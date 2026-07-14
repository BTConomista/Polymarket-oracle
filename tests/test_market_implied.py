"""Test del modello market-implied (Fase 24/26)."""

import numpy as np
import pytest

from src.models import market_implied as mi


def test_score_matrix_normalizzata_e_rho():
    M0 = mi.score_matrix(1.5, 1.1, rho=0.0)
    assert M0.sum() == pytest.approx(1.0, abs=1e-9)
    assert (M0 >= 0).all()
    # rho<0 alza la massa su 0-0 e 1-1 (correzione Dixon-Coles)
    Mr = mi.score_matrix(1.5, 1.1, rho=-0.08)
    assert Mr.sum() == pytest.approx(1.0, abs=1e-9)
    assert Mr[0, 0] > M0[0, 0]
    assert Mr[1, 1] > M0[1, 1]


def test_inversione_recupera_lambda_mu():
    """Da lambda,mu noti -> prob -> inversione deve recuperarli."""
    for lam, mu, rho in [(1.6, 1.0, 0.0), (2.1, 0.7, -0.06), (1.0, 1.0, 0.0)]:
        pH, pD, pA, pO = mi._1x2_over(mi.score_matrix(lam, mu, rho))
        lam2, mu2 = mi.implied_lambda_mu(pH, pD, pA, pO, rho=rho)
        assert lam2 == pytest.approx(lam, abs=0.03)
        assert mu2 == pytest.approx(mu, abs=0.03)


def test_over25_derivato_uguale_al_target():
    """L'inversione con O/U come target deve riprodurre l'Over 2.5."""
    pH, pD, pA, pO = 0.45, 0.27, 0.28, 0.52
    m = mi.markets_from_odds(pH, pD, pA, pO, rho=0.0)
    assert m["over_2.5"] == pytest.approx(pO, abs=0.02)
    # e le 1X2 devono avvicinarsi ai target
    assert m["home_win"] == pytest.approx(pH, abs=0.03)


def test_derive_markets_coerenti():
    m = mi.derive_markets(mi.score_matrix(1.7, 1.2, rho=-0.05))
    # monotonia degli Over: over_0.5 >= over_1.5 >= ... >= over_4.5
    ov = [m[f"over_{x}"] for x in ("0.5", "1.5", "2.5", "3.5", "4.5")]
    assert all(ov[i] >= ov[i + 1] - 1e-12 for i in range(len(ov) - 1))
    # 1X2 somma a 1
    assert m["home_win"] + m["draw"] + m["away_win"] == pytest.approx(1.0, abs=1e-9)
    # multigol partiziona: mg_0_1 + mg_2_3 + mg_4plus = 1
    assert m["mg_0_1"] + m["mg_2_3"] + m["mg_4plus"] == pytest.approx(1.0, abs=1e-9)
    # over_2.5 == mg_4plus (entrambi = totale >= 4? no: over_2.5 = tot>=3)
    assert m["over_3.5"] == pytest.approx(m["mg_4plus"], abs=1e-12)
    # tutte le prob in [0,1]
    for k, v in m.items():
        if k != "score_matrix":
            assert 0.0 <= v <= 1.0


def test_btts_coerente_con_matrice():
    M = mi.score_matrix(1.4, 1.3, rho=0.0)
    m = mi.derive_markets(M)
    # GG = 1 - P(casa 0) - P(ospite 0) + P(0-0)
    p_home0 = M[0, :].sum(); p_away0 = M[:, 0].sum(); p00 = M[0, 0]
    assert m["btts"] == pytest.approx(1 - p_home0 - p_away0 + p00, abs=1e-9)


def test_diag_inflation_alza_i_pareggi():
    M0 = mi.score_matrix(1.5, 1.3, rho=0.0)
    Mi = mi.score_matrix(1.5, 1.3, rho=0.0, diag_inflation=0.15)
    assert Mi.sum() == pytest.approx(1.0, abs=1e-9)
    p_draw0 = float(np.trace(M0)); p_drawi = float(np.trace(Mi))
    assert p_drawi > p_draw0                     # piu' massa sui pareggi


def test_balance_phi_fit_e_forma():
    """Fase 39: fit_balance_phi su lam,mu del mercato con eccesso di pareggi tra
    squadre pari-livello trova phi0>0; balance_phi decresce con |lam-mu| e boosta
    i pareggi solo dove le squadre sono vicine."""
    rng = np.random.default_rng(1)
    lams, mus, is_draw = [], [], []
    # Partite EQUILIBRATE con pareggi ben SOPRA la base Poisson (~0.30) -> phi0>0.
    for _ in range(300):
        lams.append(1.1); mus.append(1.1)
        is_draw.append(1.0 if rng.random() < 0.55 else 0.0)
    # Partite SBILANCIATE con pochi pareggi -> il boost deve svanire (kappa>0).
    for _ in range(300):
        lams.append(1.9); mus.append(0.6)
        is_draw.append(1.0 if rng.random() < 0.15 else 0.0)
    phi0, kappa = mi.fit_balance_phi(lams, mus, is_draw, rho=-0.06)
    assert phi0 > 0.0 and kappa > 0.0
    # boost maggiore per squadre equilibrate
    assert mi.balance_phi(1.3, 1.3, phi0, kappa) > mi.balance_phi(2.3, 0.5, phi0, kappa)
    # applicando phi ai pari, P(pareggio) sale per un match equilibrato
    M0 = mi.score_matrix(1.3, 1.3, rho=-0.06)
    Mb = mi.score_matrix(1.3, 1.3, rho=-0.06,
                         diag_inflation=mi.balance_phi(1.3, 1.3, phi0, kappa))
    assert float(np.trace(Mb)) > float(np.trace(M0))


def test_nbinom_over_dispersa_vs_poisson():
    """La NB con size finito ha varianza > Poisson (piu' massa sulle code)."""
    Mp = mi.score_matrix(1.6, 1.6, nb_size=None)      # Poisson
    Mnb = mi.score_matrix(1.6, 1.6, nb_size=5.0)      # over-dispersa
    assert Mnb.sum() == pytest.approx(1.0, abs=1e-9)
    # coda alta (totale >= 5) piu' pesante con la NB
    i = mi._K.reshape(-1, 1); j = mi._K.reshape(1, -1)
    tail_p = float(Mp[(i + j) >= 5].sum()); tail_nb = float(Mnb[(i + j) >= 5].sum())
    assert tail_nb > tail_p
    # size molto grande -> ~Poisson
    Mbig = mi.score_matrix(1.6, 1.6, nb_size=1e6)
    assert np.abs(Mbig - Mp).max() < 1e-3
