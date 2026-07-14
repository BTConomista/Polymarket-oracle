import numpy as np
import pytest

from src.models import bivariate_poisson as bp


def test_matrice_normalizzata():
    M = bp.bp_matrix(1.6, 1.1, 0.2)
    assert M.sum() == pytest.approx(1.0, abs=1e-9)
    assert (M >= 0).all()


def test_lam3_zero_e_poisson_indipendente():
    """λ3=0 -> marginali indipendenti: M = outer(Pois(λ), Pois(μ))."""
    M = bp.bp_matrix(1.7, 1.2, 0.0)
    ind = np.outer(bp._poisson_pmf(1.7), bp._poisson_pmf(1.2))
    ind /= ind.sum()
    assert np.abs(M - ind).max() < 1e-9


def test_marginali_preservati():
    """Il bivariato preserva i marginali (λ, μ) qualunque sia λ3."""
    lam, mu = 1.8, 1.0
    for lam3 in (0.0, 0.15, 0.35):
        M = bp.bp_matrix(lam, mu, lam3)
        row = M.sum(axis=1); col = M.sum(axis=0)
        pl, pm = bp._poisson_pmf(lam), bp._poisson_pmf(mu)
        pl /= pl.sum(); pm /= pm.sum()
        assert np.abs(row - pl).max() < 1e-3
        assert np.abs(col - pm).max() < 1e-3


def test_lam3_positivo_induce_correlazione():
    """λ3>0 -> correlazione positiva: piu' massa dove entrambe segnano tanto/poco."""
    M0 = bp.bp_matrix(1.5, 1.5, 0.0)
    Mc = bp.bp_matrix(1.5, 1.5, 0.4)
    i = np.arange(bp.MAX_GOALS + 1)
    def cov(M):
        ex = (i[:, None] * M).sum(); ey = (i[None, :] * M).sum()
        exy = (np.outer(i, i) * M).sum()
        return exy - ex * ey
    assert cov(Mc) > cov(M0) + 1e-6
    assert bp.correlation(1.5, 1.5, 0.4) > 0


def test_fit_recupera_lam3():
    """Su dati generati CON correlazione il fit trova λ3>0; su dati indipendenti ~0."""
    rng = np.random.default_rng(0)
    n = 800
    lams = rng.uniform(1.0, 1.8, n); mus = rng.uniform(0.8, 1.5, n)
    # dati correlati: componente comune W3~Pois(0.3)
    w3 = rng.poisson(0.3, n)
    hg = rng.poisson(np.clip(lams - 0.3, 0.1, None)) + w3
    ag = rng.poisson(np.clip(mus - 0.3, 0.1, None)) + w3
    lam3 = bp.fit_lam3(lams, mus, hg, ag)
    assert lam3 > 0.1
    # dati indipendenti -> λ3 ~ 0
    hgi = rng.poisson(lams); agi = rng.poisson(mus)
    lam3i = bp.fit_lam3(lams, mus, hgi, agi)
    assert lam3i < 0.1
