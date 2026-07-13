"""Modello MARKET-IMPLIED: dal mercato ai mercati che il book non prezza (Fase 24/26).

Idea (Fase 24, primo risultato positivo dell'arco modelli): il mercato stima i
gol attesi lambda,mu MEGLIO del nostro Dixon-Coles-da-gol (batte il DC di +0.0165
sull'1X2). Se INVERTIAMO le quote 1X2 (+ Over/Under 2.5) per ricavare i lambda,mu
IMPLICITI, e ci facciamo girare sopra la matrice dei punteggi del DC, possiamo
DERIVARE ogni mercato basato sui gol — inclusi quelli che il book NON prezza
(GG/NG, risultati esatti, multigol, total-squadra, ...) — a livello-mercato e in
modo coerente.

Sui mercati con quote (1X2, O/U 2.5) l'inversione riproduce il mercato (banale);
il valore e' tutto nei mercati DERIVATI non prezzati.

Contenuto:
  - ``score_matrix(lam, mu, rho)``  : matrice P(gol_casa=i, gol_ospite=j) col
    termine di correzione Dixon-Coles sui 4 punteggi bassi;
  - ``implied_lambda_mu(...)``      : inverte 1X2 (+O/U) -> (lam, mu) ai minimi
    quadrati;
  - ``derive_markets(M)``           : da una matrice, tutte le probabilita' dei
    mercati sui gol (dizionario piatto).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

MAX_GOALS = 10
_K = np.arange(MAX_GOALS + 1)
_LOGFACT = gammaln(_K + 1.0)


def score_matrix(lam: float, mu: float, rho: float = 0.0) -> np.ndarray:
    """Matrice P(gol_casa=i, gol_ospite=j) con correzione Dixon-Coles (rho sui
    4 punteggi bassi). rho=0 = Poisson indipendenti. Normalizzata."""
    ph = np.exp(_K * np.log(lam) - lam - _LOGFACT)
    pa = np.exp(_K * np.log(mu) - mu - _LOGFACT)
    M = np.outer(ph, pa)
    if rho:
        M[0, 0] *= 1.0 - lam * mu * rho
        M[0, 1] *= 1.0 + lam * rho
        M[1, 0] *= 1.0 + mu * rho
        M[1, 1] *= 1.0 - rho
        M = np.clip(M, 0.0, None)
    return M / M.sum()


def _1x2_over(M: np.ndarray) -> tuple[float, float, float, float]:
    """(P(casa), P(pari), P(ospite), P(Over 2.5)) da una matrice."""
    pH = float(np.tril(M, -1).sum())
    pD = float(np.trace(M))
    pA = float(np.triu(M, 1).sum())
    i = _K.reshape(-1, 1); j = _K.reshape(1, -1)
    pOver = float(M[(i + j) >= 3].sum())
    return pH, pD, pA, pOver


def implied_lambda_mu(p_home: float, p_draw: float, p_away: float,
                      p_over: float | None = None, rho: float = 0.0
                      ) -> tuple[float, float]:
    """Trova (lam, mu) che riproduce meglio le probabilita' di mercato via la
    matrice dei punteggi. Target: 1X2 (sempre) + Over 2.5 (se fornito).
    Minimi quadrati con inizializzazione informata (totale gol dall'O/U, tilt
    dal 1X2). rho e' fissato (il mercato 1X2+O/U non lo vincola)."""
    def loss(x):
        lam, mu = x
        qH, qD, qA, qO = _1x2_over(score_matrix(lam, mu, rho))
        e = (qH - p_home) ** 2 + (qD - p_draw) ** 2 + (qA - p_away) ** 2
        if p_over is not None:
            e += (qO - p_over) ** 2
        return e
    tot0 = 2.5 + ((p_over - 0.5) * 2.0 if p_over is not None else 0.0)
    tilt = float(np.clip(0.5 + (p_home - p_away) * 0.6, 0.15, 0.85))
    x0 = [max(0.2, tot0 * tilt), max(0.2, tot0 * (1.0 - tilt))]
    r = minimize(loss, x0, method="L-BFGS-B", bounds=[(0.1, 4.5), (0.1, 4.5)])
    return float(r.x[0]), float(r.x[1])


def derive_markets(M: np.ndarray) -> dict:
    """Da una matrice dei punteggi, le probabilita' di TUTTI i mercati sui gol.
    Dizionario piatto (chiavi = nomi mercato -> prob dell'esito 'si'/positivo).
    Include la matrice sotto 'score_matrix' per il log-loss sul risultato esatto."""
    i = _K.reshape(-1, 1); j = _K.reshape(1, -1)
    tot = i + j
    home = _K.reshape(-1, 1) * np.ones((1, MAX_GOALS + 1))
    away = np.ones((MAX_GOALS + 1, 1)) * _K.reshape(1, -1)
    pH, pD, pA, _ = _1x2_over(M)
    d = {
        "home_win": pH, "draw": pD, "away_win": pA,
        "over_0.5": float(M[tot >= 1].sum()),
        "over_1.5": float(M[tot >= 2].sum()),
        "over_2.5": float(M[tot >= 3].sum()),
        "over_3.5": float(M[tot >= 4].sum()),
        "over_4.5": float(M[tot >= 5].sum()),
        "btts": float(M[1:, 1:].sum()),
        "home_ov_0.5": float(M[home >= 1].sum()),
        "home_ov_1.5": float(M[home >= 2].sum()),
        "away_ov_0.5": float(M[away >= 1].sum()),
        "away_ov_1.5": float(M[away >= 2].sum()),
        "odd_total": float(M[(tot % 2) == 1].sum()),
        "home_by_2plus": float(M[(i - j) >= 2].sum()),
        "away_by_2plus": float(M[(j - i) >= 2].sum()),
        # multigol (bande di gol totali): 0-1, 2-3, 4+
        "mg_0_1": float(M[tot <= 1].sum()),
        "mg_2_3": float(M[(tot >= 2) & (tot <= 3)].sum()),
        "mg_4plus": float(M[tot >= 4].sum()),
        "score_matrix": M,
    }
    return d


def markets_from_odds(p_home, p_draw, p_away, p_over=None, rho=0.0) -> dict:
    """Comodo: inverte le quote e deriva tutti i mercati in un colpo."""
    lam, mu = implied_lambda_mu(p_home, p_draw, p_away, p_over, rho)
    out = derive_markets(score_matrix(lam, mu, rho))
    out["lam"], out["mu"] = lam, mu
    return out
