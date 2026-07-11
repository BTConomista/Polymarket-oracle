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
from scipy.optimize import minimize, minimize_scalar

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


# ---------------------------------------------------------------------------- #
# Ricalibrazione per-classe 1X2 (Fase 10)
#
# A differenza del temperature scaling (che scala TUTTE le classi in modo
# uniforme e non puo' spostare massa tra esiti), qui ogni classe (casa/pari/
# ospite) ha il proprio moltiplicatore. Serve a correggere una miscalibrazione
# DIREZIONALE: il diagnostico (scripts/analyze.py) mostra casa un filo
# sovrastimata e PAREGGIO sottostimato, ed e' li' che vive il grosso del gap col
# mercato (Fase 9). q_i ∝ w_i * p_i, poi rinormalizzato. Solo i rapporti tra i
# w contano (w=(c,c,c) non cambia nulla): si fissa w_ospite=1 (2 parametri).
# ---------------------------------------------------------------------------- #
def apply_class_recalibration(probs: np.ndarray, weights) -> np.ndarray:
    """q_i ∝ w_i * p_i, rinormalizzato. weights: (w_H, w_D, w_A) > 0."""
    probs = np.clip(np.asarray(probs, dtype=float), _EPS, 1.0)
    w = np.asarray(weights, dtype=float)
    scaled = probs * w[None, :]
    return scaled / scaled.sum(axis=1, keepdims=True)


def fit_class_recalibration(
    probs: np.ndarray,
    outcomes: list[str],
    bounds: tuple[float, float] = (0.5, 2.0),
) -> tuple[float, float, float]:
    """Trova (w_H, w_D, w_A) che minimizzano la log-loss 1X2 (w_A fissato a 1,
    poi il vettore e' normalizzato a media geometrica 1 per leggibilita').

    Con dati gia' calibrati -> pesi ~ (1, 1, 1). Con pochi dati fallback (1,1,1).
    """
    probs = np.clip(np.asarray(probs, dtype=float), _EPS, 1.0)
    if len(outcomes) == 0:
        return (1.0, 1.0, 1.0)

    def loss(x: np.ndarray) -> float:
        return metrics.log_loss_1x2(
            apply_class_recalibration(probs, [x[0], x[1], 1.0]), outcomes)

    res = minimize(loss, np.array([1.0, 1.0]), method="L-BFGS-B",
                   bounds=[bounds, bounds])
    w = np.array([res.x[0], res.x[1], 1.0])
    return tuple(float(v) for v in w / np.exp(np.mean(np.log(w))))
