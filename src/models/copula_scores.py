"""Copule sui marginali Poisson — dipendenza FLESSIBILE (anche negativa) tra i gol.

Generalizza il Poisson bivariato (Fase 42), che poteva solo aggiungere correlazione
POSITIVA e sovra-disperdeva i totali. Una copula impone la dipendenza **preservando
esattamente i marginali Poisson** (proprietà fondamentale delle copule) e ammette
**qualsiasi segno** di dipendenza. La matrice congiunta si ottiene per differenze
della CDF-copula (rettangolo):

    P(X=x, Y=y) = C(Fx(x),  Fy(y))  − C(Fx(x−1), Fy(y))
                − C(Fx(x),  Fy(y−1)) + C(Fx(x−1), Fy(y−1))

con Fx, Fy le CDF marginali Poisson e C la CDF-copula (Fx(−1)=0).

Famiglia: **Frank** (forma chiusa, θ∈ℝ; θ→0 = indipendenza; θ>0 dipendenza positiva,
θ<0 negativa). θ può essere globale o funzione di |λ−μ| (Fase 43).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import poisson

MAX_GOALS = 10
_K = np.arange(MAX_GOALS + 1)


def _frank_C(u, v, theta):
    """CDF della copula di Frank. Vettorizzata: u,v,theta possono essere array.
    theta→0 → indipendenza (u·v), gestito elemento per elemento."""
    u = np.asarray(u, float); v = np.asarray(v, float)
    th = np.broadcast_to(np.asarray(theta, float), np.broadcast(u, v).shape).copy()
    out = u * v                                   # default: indipendenza (θ≈0)
    m = np.abs(th) >= 1e-8
    if m.any():
        thm = th[m]
        e1 = np.expm1(-thm)
        num = np.expm1(-thm * u[m]) * np.expm1(-thm * v[m])
        out = out.copy()
        out[m] = -1.0 / thm * np.log1p(num / e1)
    return out


def _cell_prob(lams, mus, thetas, xs, ys):
    """P(X=x, Y=y) NORMALIZZATA per ogni partita, vettorizzata (copula di Frank).
    Usa solo i 4 angoli della CDF -> veloce per il fit (niente matrice intera)."""
    lams = np.asarray(lams, float); mus = np.asarray(mus, float)
    th = np.clip(np.broadcast_to(np.asarray(thetas, float), lams.shape), -25.0, 25.0)
    xs = np.asarray(xs, int); ys = np.asarray(ys, int)
    Fx1 = poisson.cdf(xs, lams); Fx0 = poisson.cdf(xs - 1, lams)
    Fy1 = poisson.cdf(ys, mus); Fy0 = poisson.cdf(ys - 1, mus)
    P = (_frank_C(Fx1, Fy1, th) - _frank_C(Fx0, Fy1, th)
         - _frank_C(Fx1, Fy0, th) + _frank_C(Fx0, Fy0, th))
    Z = _frank_C(poisson.cdf(MAX_GOALS, lams), poisson.cdf(MAX_GOALS, mus), th)
    return np.clip(P, 1e-15, None) / np.clip(Z, 1e-9, None)


def frank_matrix(lam: float, mu: float, theta: float) -> np.ndarray:
    """Matrice P(gol_casa=i, gol_ospite=j) con marginali Poisson(λ), Poisson(μ) e
    dipendenza data dalla copula di Frank (parametro θ). Marginali preservati."""
    theta = float(np.clip(theta, -25.0, 25.0))
    # CDF marginali con F(−1)=0 in testa: Fx_pad[k] = CDF(k−1)
    Fx = np.concatenate([[0.0], poisson.cdf(_K, lam)])
    Fy = np.concatenate([[0.0], poisson.cdf(_K, mu)])
    U, V = np.meshgrid(Fx, Fy, indexing="ij")     # (G+2, G+2)
    C = _frank_C(U, V, theta)
    M = C[1:, 1:] - C[:-1, 1:] - C[1:, :-1] + C[:-1, :-1]
    M = np.clip(M, 0.0, None)
    s = M.sum()
    return M / s if s > 0 else M


def fit_theta(lams, mus, home_goals, away_goals, weights=None,
              bounds: tuple[float, float] = (-12.0, 12.0)) -> float:
    """θ GLOBALE della copula di Frank per MLE pesata sui punteggi osservati."""
    lams = np.asarray(lams, float); mus = np.asarray(mus, float)
    hg = np.minimum(np.asarray(home_goals, int), MAX_GOALS)
    ag = np.minimum(np.asarray(away_goals, int), MAX_GOALS)
    w = np.ones(len(lams)) if weights is None else np.asarray(weights, float)

    def neg_ll(theta: float) -> float:
        p = _cell_prob(lams, mus, theta, hg, ag)
        return -float(np.sum(w * np.log(p)))

    return float(minimize_scalar(neg_ll, bounds=bounds, method="bounded").x)


def fit_theta_balance(lams, mus, home_goals, away_goals, weights=None):
    """θ CONDIZIONATO all'equilibrio: θ_partita = a + b·|λ−μ|. Ritorna (a, b)."""
    lams = np.asarray(lams, float); mus = np.asarray(mus, float)
    bal = np.abs(lams - mus)
    hg = np.minimum(np.asarray(home_goals, int), MAX_GOALS)
    ag = np.minimum(np.asarray(away_goals, int), MAX_GOALS)
    w = np.ones(len(lams)) if weights is None else np.asarray(weights, float)

    def neg_ll(p: np.ndarray) -> float:
        a, b = p
        prob = _cell_prob(lams, mus, a + b * bal, hg, ag)
        return -float(np.sum(w * np.log(prob)))

    r = minimize(neg_ll, np.array([0.0, 0.0]), method="Nelder-Mead",
                 options={"xatol": 1e-3, "fatol": 1e-6, "maxiter": 300})
    return float(r.x[0]), float(r.x[1])
