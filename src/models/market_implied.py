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
_EPS = 1e-9
_K = np.arange(MAX_GOALS + 1)
_LOGFACT = gammaln(_K + 1.0)


def _poisson_pmf(lam: float) -> np.ndarray:
    return np.exp(_K * np.log(lam) - lam - _LOGFACT)


def _nbinom_pmf(mean: float, size: float) -> np.ndarray:
    """PMF binomiale negativa con media ``mean`` e parametro di dispersione
    ``size`` (r): var = mean + mean^2/size. size -> inf ricade nella Poisson.
    Cattura l'over-dispersione dei gol."""
    p = size / (size + mean)
    return np.exp(gammaln(_K + size) - gammaln(size) - _LOGFACT
                  + size * np.log(p) + _K * np.log1p(-p))


def score_matrix(lam: float, mu: float, rho: float = 0.0,
                 diag_inflation: float = 0.0, nb_size: float | None = None
                 ) -> np.ndarray:
    """Matrice P(gol_casa=i, gol_ospite=j) attorno ai tassi (lam, mu).

    - ``rho``           : correzione Dixon-Coles sui 4 punteggi bassi (rho=0 =
      marginali indipendenti);
    - ``diag_inflation``: phi che alza TUTTA la diagonale dei pareggi (Fase 12b);
    - ``nb_size``       : se dato, usa marginali binomiali-negative con quel
      parametro di dispersione invece della Poisson (over-dispersione).
    Normalizzata."""
    if nb_size is not None:
        ph, pa = _nbinom_pmf(lam, nb_size), _nbinom_pmf(mu, nb_size)
    else:
        ph, pa = _poisson_pmf(lam), _poisson_pmf(mu)
    M = np.outer(ph, pa)
    if rho:
        M[0, 0] *= 1.0 - lam * mu * rho
        M[0, 1] *= 1.0 + lam * rho
        M[1, 0] *= 1.0 + mu * rho
        M[1, 1] *= 1.0 - rho
        M = np.clip(M, 0.0, None)
    if diag_inflation:
        idx = np.arange(M.shape[0])
        M[idx, idx] *= 1.0 + diag_inflation
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
        # doppia chance (dai 1X2)
        "dc_1x": pH + pD, "dc_2x": pA + pD, "dc_12": pH + pA,
        # clean sheet (la squadra NON subisce): casa = ospite segna 0; ospite = casa segna 0
        "cs_home": float(M[:, 0].sum()),
        "cs_away": float(M[0, :].sum()),
        # vince a zero (win to nil): vince E tiene la porta inviolata
        "wtn_home": float(M[1:, 0].sum()),   # casa >=1, ospite 0
        "wtn_away": float(M[0, 1:].sum()),   # ospite >=1, casa 0
        "score_matrix": M,
    }
    return d


# Mercati "puro-totale" o "puro-marginale" (dipendono da X+Y o da una sola squadra):
# la forma migliore è la τ PURA — l'inflazione diagonale/correlazione sovra-disperde
# i totali e li peggiora (Fasi 42/43). Tutti gli altri (esiti/pareggio/joint) usano
# la φ(|λ−μ|) (Fase 35). Routing di forma PER-MERCATO (meccanico, non fittato).
_TAU_MARKETS = frozenset({
    "over_0.5", "over_1.5", "over_2.5", "over_3.5", "over_4.5",
    "mg_0_1", "mg_2_3", "mg_4plus",
    "home_ov_0.5", "home_ov_1.5", "away_ov_0.5", "away_ov_1.5",
    "odd_total", "cs_home", "cs_away",
})


def price_markets(lam: float, mu: float, rho: float = 0.0,
                  phi0: float = 0.0, kappa: float = 0.0) -> dict:
    """Prezza OGNI mercato Tier 1 con la sua forma MIGLIORE (routing per-mercato,
    Fase 44): i mercati puro-totale/marginale dalla matrice τ (senza φ, che
    sovra-disperde i totali); esiti/pareggio/joint dalla matrice con φ(|λ−μ|).

    Rompe la coerenza tra le due famiglie (prezzi da matrici diverse) — accettabile
    per il pricing PER-MERCATO (non per un prezzo unico coerente). phi0=0 -> nessuna
    inflazione (tutto dalla τ)."""
    M_tau = score_matrix(lam, mu, rho)
    phi = balance_phi(lam, mu, phi0, kappa) if phi0 else 0.0
    M_phi = score_matrix(lam, mu, rho, diag_inflation=phi) if phi else M_tau
    d_tau, d_phi = derive_markets(M_tau), derive_markets(M_phi)
    out = {k: (d_tau[k] if k in _TAU_MARKETS else d_phi[k])
           for k in d_phi if k != "score_matrix"}
    out["score_matrix"] = M_phi            # risultato esatto: la diagonale conta
    out["lam"], out["mu"] = lam, mu
    return out


def markets_from_odds(p_home, p_draw, p_away, p_over=None, rho=0.0) -> dict:
    """Comodo: inverte le quote e deriva tutti i mercati in un colpo."""
    lam, mu = implied_lambda_mu(p_home, p_draw, p_away, p_over, rho)
    out = derive_markets(score_matrix(lam, mu, rho))
    out["lam"], out["mu"] = lam, mu
    return out


def balance_phi(lam: float, mu: float, phi0: float, kappa: float) -> float:
    """Inflazione-pareggio condizionata all'EQUILIBRIO (Fase 35/39):
    phi(lam,mu) = phi0 * exp(-kappa * |lam - mu|). Da passare come
    ``diag_inflation`` a ``score_matrix`` per applicarla ai lambda,mu del mercato."""
    return float(phi0 * np.exp(-kappa * abs(lam - mu)))


def fit_balance_phi(lams, mus, is_draw, rho: float = 0.0,
                    weights=None) -> tuple[float, float]:
    """Stima (phi0, kappa) di phi(lam,mu)=phi0*exp(-kappa*|lam-mu|) sui lambda,mu
    del MERCATO massimizzando la verosimiglianza pesata dei pareggi (Fase 39).

    Stessa verosimiglianza di DixonColesModel._fit_draw_balance, ma applicata ai
    lambda,mu impliciti nelle quote invece che a quelli stimati dai gol. Il termine
    dipendente da phi e' log(1+phi*[pari]) - log(1+phi*D_match), con D_match la
    prob. di pareggio base (matrice market-implied, rho fisso) per riga.
    phi0>=0, kappa>=0. Ritorna (phi0, kappa)."""
    lams = np.asarray(lams, float); mus = np.asarray(mus, float)
    is_draw = np.asarray(is_draw, float)
    bal = np.abs(lams - mus)
    w = np.ones(len(lams)) if weights is None else np.asarray(weights, float)
    # Prob. di pareggio base per riga (traccia della matrice market-implied).
    d_match = np.array([float(np.trace(score_matrix(l, m, rho)))
                        for l, m in zip(lams, mus)])
    d_match = np.clip(d_match, _EPS, 1.0 - _EPS)

    def neg_ll(p: np.ndarray) -> float:
        phi = p[0] * np.exp(-p[1] * bal)
        return -np.sum(w * (np.log1p(phi * is_draw) - np.log1p(phi * d_match)))

    r = minimize(neg_ll, np.array([0.1, 1.0]), method="L-BFGS-B",
                 bounds=[(0.0, 2.0), (0.0, 5.0)])
    return float(r.x[0]), float(r.x[1])
