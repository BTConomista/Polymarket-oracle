import numpy as np
import pytest
from scipy.stats import poisson

from src.models import copula_scores as cop


def test_normalizzata_e_marginali_preservati():
    lam, mu = 1.7, 1.1
    for theta in (-6.0, -1.0, 0.0, 2.0, 6.0):
        M = cop.frank_matrix(lam, mu, theta)
        assert M.sum() == pytest.approx(1.0, abs=1e-9)
        assert (M >= 0).all()
        # marginali = Poisson(λ), Poisson(μ)
        row, col = M.sum(1), M.sum(0)
        assert np.abs(row - poisson.pmf(cop._K, lam)).max() < 1e-3
        assert np.abs(col - poisson.pmf(cop._K, mu)).max() < 1e-3


def test_theta_zero_indipendenza():
    M = cop.frank_matrix(1.6, 1.2, 0.0)
    ind = np.outer(poisson.pmf(cop._K, 1.6), poisson.pmf(cop._K, 1.2))
    ind /= ind.sum()                       # stessa rinormalizzazione (troncamento a MAX_GOALS)
    assert np.abs(M - ind).max() < 1e-9


def test_segno_dipendenza():
    """θ>0 -> correlazione positiva; θ<0 -> negativa."""
    i = cop._K
    def corr(M):
        ex = (i[:, None] * M).sum(); ey = (i[None, :] * M).sum()
        exy = (np.outer(i, i) * M).sum()
        vx = (i[:, None] ** 2 * M).sum() - ex ** 2
        vy = (i[None, :] ** 2 * M).sum() - ey ** 2
        return (exy - ex * ey) / np.sqrt(vx * vy)
    assert corr(cop.frank_matrix(1.5, 1.3, 5.0)) > 0.05
    assert corr(cop.frank_matrix(1.5, 1.3, -5.0)) < -0.05


def test_fit_recupera_segno():
    rng = np.random.default_rng(0)
    n = 700
    lams = rng.uniform(1.0, 1.8, n); mus = rng.uniform(0.9, 1.5, n)
    # genera dati con dipendenza NEGATIVA via copula di Frank (θ<0)
    hg, ag = [], []
    for k in range(n):
        M = cop.frank_matrix(lams[k], mus[k], -5.0)
        flat = M.ravel() / M.sum()
        idx = rng.choice(len(flat), p=flat)
        hg.append(idx // M.shape[1]); ag.append(idx % M.shape[1])
    theta = cop.fit_theta(lams, mus, hg, ag)
    assert theta < -0.5           # ritrova il segno negativo
