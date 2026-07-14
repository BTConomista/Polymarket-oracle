"""Poisson BIVARIATO (Karlis-Ntzoufras 2003) — correlazione ESPLICITA tra i gol.

L'unica famiglia di modelli sui punteggi mai implementata (Fase 42). Idea: i gol
di casa X e ospite Y condividono una componente comune:

    X = W1 + W3,   Y = W2 + W3,   con W1~Pois(λ1), W2~Pois(λ2), W3~Pois(λ3)

W3 e' la parte "comune" (meteo, arbitro, ritmo partita, campo): induce
CORRELAZIONE POSITIVA Cov(X,Y)=λ3≥0. Marginali: X~Pois(λ1+λ3), Y~Pois(λ2+λ3).

Per confrontarlo con gli altri modelli sulla STESSA scala, lo costruiamo
PRESERVANDO i marginali (λ, μ) dati (dal DC o dal mercato): λ1=λ−λ3, λ2=μ−λ3,
λ3=covarianza. Cosi' λ3 e' un parametro di FORMA sui λ,μ dati, confrontabile con
il rho di Dixon-Coles e con la φ(|λ−μ|) della Fase 35.

LIMITE STRUTTURALE NOTO (Fasi 12b/18): λ3≥0 puo' solo AGGIUNGERE correlazione
POSITIVA. Nel calcio la correlazione dei punteggi e' ≈0 o leggermente negativa
(per questo Dixon-Coles usa la correzione τ con rho<0). Quindi ci si aspetta λ3→0
o guadagno nullo — ma e' l'unico modo di dimostrarlo coi nostri dati. Onesta'.

Joint PMF (convoluzione sul termine comune W3):
    P(X=x, Y=y) = Σ_{k=0}^{min(x,y)} Pois(k; λ3) · Pois(x−k; λ1) · Pois(y−k; λ2)
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

MAX_GOALS = 10
_K = np.arange(MAX_GOALS + 1)
_LOGFACT = gammaln(_K + 1.0)


def _poisson_pmf(rate: float) -> np.ndarray:
    if rate <= 0:
        p = np.zeros(MAX_GOALS + 1); p[0] = 1.0; return p
    return np.exp(_K * np.log(rate) - rate - _LOGFACT)


def bp_matrix(lam: float, mu: float, lam3: float) -> np.ndarray:
    """Matrice P(gol_casa=i, gol_ospite=j) del Poisson bivariato che PRESERVA i
    marginali (lam, mu). lam3 = covarianza (>=0). lam3=0 -> Poisson indipendenti.
    lam3 viene troncato a < min(lam, mu) per tenere λ1,λ2 > 0."""
    lam3 = float(np.clip(lam3, 0.0, min(lam, mu) - 1e-6)) if lam3 > 0 else 0.0
    lam1, lam2 = lam - lam3, mu - lam3
    p1, p2, p3 = _poisson_pmf(lam1), _poisson_pmf(lam2), _poisson_pmf(lam3)
    M = np.zeros((MAX_GOALS + 1, MAX_GOALS + 1))
    for k in range(MAX_GOALS + 1):
        if p3[k] < 1e-15:
            break
        # contributo del termine comune W3=k: sposta di k entrambe le squadre
        M[k:, k:] += p3[k] * np.outer(p1[:MAX_GOALS + 1 - k], p2[:MAX_GOALS + 1 - k])
    s = M.sum()
    return M / s if s > 0 else M


def fit_lam3(lams, mus, home_goals, away_goals, weights=None,
             bounds: tuple[float, float] = (0.0, 0.6)) -> float:
    """Stima il λ3 GLOBALE (covarianza) che massimizza la verosimiglianza pesata
    dei punteggi osservati, dati i marginali (lam, mu) per partita. Ritorna λ3>=0;
    λ3=0 = nessuna correlazione aggiunta (fallback onesto se il calcio non la vuole)."""
    lams = np.asarray(lams, float); mus = np.asarray(mus, float)
    hg = np.asarray(home_goals, int); ag = np.asarray(away_goals, int)
    w = np.ones(len(lams)) if weights is None else np.asarray(weights, float)
    hc = np.minimum(hg, MAX_GOALS); ac = np.minimum(ag, MAX_GOALS)

    def neg_ll(lam3: float) -> float:
        ll = 0.0
        for k in range(len(lams)):
            M = bp_matrix(lams[k], mus[k], lam3)
            ll += w[k] * np.log(max(M[hc[k], ac[k]], 1e-15))
        return -ll

    res = minimize_scalar(neg_ll, bounds=bounds, method="bounded")
    return float(res.x)


def correlation(lam: float, mu: float, lam3: float) -> float:
    """Correlazione di Pearson indotta: λ3 / sqrt(λ·μ)."""
    return float(lam3 / np.sqrt(lam * mu)) if lam > 0 and mu > 0 else 0.0
