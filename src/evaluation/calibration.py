"""Ricalibrazione post-hoc delle probabilita' 1X2 — temperature scaling.

Diagnostico (scripts/analyze.py): il modello e' calibrato SULLA MEDIA, ma perde
contro il mercato dove e' molto sicuro e nelle fasce estreme di probabilita'
(le sue probabilita' sono un po' troppo "compresse"/"gonfiate"). Il temperature
scaling e' la correzione post-hoc piu' economica: un SOLO parametro T, applicato
ai log-prob e rinormalizzato, senza toccare il modello ne' aggiungere dati.

    q_i ∝ p_i ** (1/T)     (equiv. a T sui logit)

- T = 1  -> nessun cambiamento.
- T > 1  -> "raffredda": probabilita' piu' vicine all'uniforme (meno sicuro).
- T < 1  -> "scalda": probabilita' piu' nette (piu' sicuro).

T si TARA sui dati passati (log-loss minima) e si applica al futuro: nessun
look-ahead. Le metriche restano quelle della fonte unica (metrics.log_loss_1x2).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar

from . import metrics

_EPS = 1e-15


def apply_temperature(probs: np.ndarray, temperature: float) -> np.ndarray:
    """Applica il temperature scaling a probabilita' (N, K) e rinormalizza.

    temperature <= 0 non ha senso: si ritorna l'input invariato.
    """
    probs = np.clip(np.asarray(probs, dtype=float), _EPS, 1.0)
    if temperature is None or temperature <= 0 or temperature == 1.0:
        return probs / probs.sum(axis=1, keepdims=True)
    scaled = probs ** (1.0 / temperature)
    return scaled / scaled.sum(axis=1, keepdims=True)


def fit_temperature(
    probs: np.ndarray,
    outcomes: list[str],
    bounds: tuple[float, float] = (0.25, 4.0),
) -> float:
    """Trova il T che minimizza la log-loss 1X2 sui dati forniti.

    probs: array (N, 3) in ordine (H, D, A). outcomes: lista di "H"/"D"/"A".
    Ritorna il T ottimo entro ``bounds`` (default: da 4x piu' netto a 4x piu'
    morbido). Con pochi dati o dati gia' calibrati, T ~ 1.
    """
    probs = np.clip(np.asarray(probs, dtype=float), _EPS, 1.0)
    if len(outcomes) == 0:
        return 1.0

    def loss(t: float) -> float:
        return metrics.log_loss_1x2(apply_temperature(probs, t), outcomes)

    res = minimize_scalar(loss, bounds=bounds, method="bounded")
    return float(res.x)
