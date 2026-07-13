"""Denoising CROSS-STAGIONE del market-implied (Punto 4 della roadmap post-audit).

Il motore market-implied (Fase 24/26) inverte le quote di OGNI partita in ISOLAMENTO:
nessun meccanismo che sfrutti l'informazione cross-stagione per ridurre il rumore o
correggere bias sistematici. Qui aggiungiamo due correzioni, entrambe **stimate sul
PASSATO e applicate al futuro** (leave-future-out, niente look-ahead):

  1. POWER-DEVIG (correzione del bias del margine bookmaker). Il devig moltiplicativo
     standard (metrics.devig_1x2: p_i ∝ 1/o_i) e' noto per distorcere la coda
     (favourite-longshot bias). La forma a potenza generalizza:

         p_i ∝ (1/o_i)^(1/eta) ,   poi normalizza

     eta = 1 riproduce il devig moltiplicativo; eta > 1 "appiattisce" verso
     l'uniforme (riduce la sovrastima dei favoriti), eta < 1 accentua. eta e' un
     SINGOLO parametro tarato sulla log-loss 1X2 delle stagioni passate: un bias
     lento e globale, quindi bassa varianza e lag trascurabile.

  2. RICALIBRAZIONE del mercato DERIVATO (correzione del bias sistematico su un
     mercato che il book non prezza, es. GG/NG). Se il market-implied sbaglia la
     GG/NG sempre nella stessa direzione (bias), una logistica a 2 parametri
     (Platt) imparata sul passato lo corregge:

         p_corr = sigmoide( a * logit(p_raw) + b )

     a<1 raffredda (meno sicuro), b sposta il livello. Anche qui: pochi parametri,
     stimati su tante partite passate -> variazione lenta, lag basso.

Trade-off bias/varianza/lag (da documentare nell'esperimento): tarare su TUTTO il
passato = minima varianza ma, se il bias deriva nel tempo, un filo di lag; tarare
con peso RECENTE (half-life sulle stagioni) segue la deriva ma con piu' varianza.
Le funzioni accettano pesi per-riga cosi' l'esperimento puo' confrontare le due vie.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize, minimize_scalar

_EPS = 1e-15


def power_devig(odds_home: float, odds_draw: float, odds_away: float,
                eta: float = 1.0) -> np.ndarray:
    """Quote 1X2 -> probabilita' con devig a POTENZA. eta=1 = moltiplicativo."""
    inv = np.array([1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away])
    inv = inv ** (1.0 / eta)
    return inv / inv.sum()


def fit_power_eta(odds: np.ndarray, outcomes: list[str],
                  weights: np.ndarray | None = None,
                  bounds: tuple[float, float] = (0.5, 2.0)) -> float:
    """Trova eta che minimizza la log-loss 1X2 (pesata) sulle quote passate.

    odds: array (N,3) di quote (home, draw, away). outcomes: "H"/"D"/"A".
    weights: peso per-riga (es. recency); None = uniforme. eta=1 = nessuna
    correzione (fallback se i dati sono pochi o gia' ottimi)."""
    idx = {"H": 0, "D": 1, "A": 2}
    y = np.array([idx[o] for o in outcomes])
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)

    def loss(eta: float) -> float:
        inv = (1.0 / odds) ** (1.0 / eta)
        P = inv / inv.sum(axis=1, keepdims=True)
        picked = np.clip(P[np.arange(len(y)), y], _EPS, 1.0)
        return float(-np.sum(w * np.log(picked)) / np.sum(w))

    if len(y) < 30:
        return 1.0
    res = minimize_scalar(loss, bounds=bounds, method="bounded")
    return float(res.x)


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return np.log(p / (1.0 - p))


def fit_derived_recal(p_raw: np.ndarray, y: np.ndarray,
                      weights: np.ndarray | None = None) -> tuple[float, float]:
    """Platt scaling per un mercato DERIVATO binario: stima (a, b) che minimizzano
    la log-loss di sigmoide(a*logit(p_raw)+b) sui dati passati. (1, 0) = identita'
    (fallback con pochi dati)."""
    if len(y) < 30:
        return 1.0, 0.0
    z = _logit(np.asarray(p_raw, float))
    y = np.asarray(y, float)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)

    def loss(params: np.ndarray) -> float:
        a, b = params
        p = 1.0 / (1.0 + np.exp(-(a * z + b)))
        p = np.clip(p, _EPS, 1.0 - _EPS)
        return float(-np.sum(w * (y * np.log(p) + (1 - y) * np.log(1 - p))) / np.sum(w))

    res = minimize(loss, np.array([1.0, 0.0]), method="L-BFGS-B",
                   bounds=[(0.1, 3.0), (-3.0, 3.0)])
    return float(res.x[0]), float(res.x[1])


def apply_derived_recal(p_raw: np.ndarray, a: float, b: float) -> np.ndarray:
    """Applica la correzione Platt: sigmoide(a*logit(p_raw)+b)."""
    z = _logit(np.asarray(p_raw, float))
    return 1.0 / (1.0 + np.exp(-(a * z + b)))


def recency_weights(seasons: list[str], season_order: list[str],
                    half_life: float = 2.0) -> np.ndarray:
    """Pesi per-riga con decadimento per stagione (half_life in numero di stagioni).
    half_life = inf -> tutte uguali (minima varianza, possibile lag su bias in
    deriva); piccola -> segue la deriva ma piu' rumorosa. Per il trade-off
    bias/varianza/lag del Punto 4."""
    if half_life is None or np.isinf(half_life):
        return np.ones(len(seasons))
    pos = {s: i for i, s in enumerate(season_order)}
    last = max(pos[s] for s in seasons)
    xi = np.log(2.0) / half_life
    return np.array([np.exp(-xi * (last - pos[s])) for s in seasons])
