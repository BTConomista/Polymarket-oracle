"""Invariante della double-Poisson applicata ai cartellini (Fase 125).

Il test che conta e' uno solo, ed e' un'IDENTITA': con theta = 1 la
double-Poisson **e'** la Poisson. Se un giorno la tabella-griglia,
l'arrotondamento dei tassi o la bisezione si rompessero, il modo in cui te ne
accorgi non e' un numero che cambia -- e' questa uguaglianza che smette di
valere. Senza, un difetto della griglia si presenterebbe come "i cartellini
sono meno sotto-dispersi di quanto pensassimo": una conclusione, non un bug.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _run_fase125_cartellini import _ll_dp, _ll_poisson  # noqa: E402


def test_theta_uno_coincide_con_poisson():
    rng = np.random.default_rng(0)
    lam = rng.uniform(0.8, 4.0, size=3000)
    y = rng.poisson(lam)
    assert abs(_ll_dp(y, lam, 1.0) - _ll_poisson(y, lam)) < 2e-3


def test_theta_maggiore_di_uno_premia_i_dati_sotto_dispersi():
    """Costruito apposta: conteggi con varianza MINORE della media. Un theta>1
    deve adattarsi meglio della Poisson, altrimenti il segno e' invertito."""
    rng = np.random.default_rng(1)
    lam = np.full(4000, 2.0)
    # binomiale con stessa media e varianza 2*(1-2/8) = 1.5 < 2
    y = rng.binomial(8, 0.25, size=4000)
    assert y.var() < y.mean()
    assert _ll_dp(y, lam, 1.3) > _ll_poisson(y, lam)


def test_theta_minore_di_uno_penalizza_gli_stessi_dati():
    rng = np.random.default_rng(2)
    lam = np.full(4000, 2.0)
    y = rng.binomial(8, 0.25, size=4000)
    assert _ll_dp(y, lam, 0.95) < _ll_dp(y, lam, 1.3)
