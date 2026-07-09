"""Metriche di valutazione e confronto con il mercato.

Due domande diverse:

  1. "Le probabilita' del modello sono CALIBRATE?"  -> Brier score e log-loss.
     Misurano quanto le probabilita' stimate corrispondono alla frequenza reale.
     Non dipendono da alcun mercato: si calcolano sempre.

  2. "Il modello ha un VANTAGGIO rispetto al mercato?"  -> stesse metriche
     calcolate anche sulle probabilita' implicite nelle quote di CHIUSURA dei
     bookmaker (dopo aver tolto il margine), e confrontate con quelle del modello.
     Le quote di chiusura sono lo stimatore piu' efficiente che esista: batterle
     e' molto difficile ed e' il vero traguardo, non un requisito minimo.

Convenzioni:
  - 1X2: probabilita' in ordine (casa, pareggio, ospite); esito reale in {H,D,A}.
  - Over/Under 2.5: probabilita' di Over; esito reale = 1 se Over, 0 se Under.
"""

from __future__ import annotations

import numpy as np

_OUTCOME_INDEX = {"H": 0, "D": 1, "A": 2}


# ---------------------------------------------------------------------- #
# Conversione quote -> probabilita' (rimozione del margine / "devigging")
# ---------------------------------------------------------------------- #
def devig_1x2(odds_home, odds_draw, odds_away):
    """Quote 1X2 -> probabilita' implicite normalizzate (somma = 1).

    Metodo moltiplicativo: prob_grezza = 1/quota, poi si normalizza dividendo
    per la somma (che vale >1 per via del margine del bookmaker). Semplice e
    standard; alternative piu' raffinate (Shin, power) le valuteremo se servira'.
    """
    inv = np.array([1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away])
    return inv / inv.sum()


def devig_binary(odds_over, odds_under):
    """Quote Over/Under -> (prob_over, prob_under) normalizzate."""
    inv = np.array([1.0 / odds_over, 1.0 / odds_under])
    inv = inv / inv.sum()
    return inv[0], inv[1]


# ---------------------------------------------------------------------- #
# Metriche 1X2 (multiclasse a 3 esiti)
# ---------------------------------------------------------------------- #
def log_loss_1x2(probs: np.ndarray, outcomes: list[str]) -> float:
    """Log-loss medio. probs: array (N, 3) in ordine (H, D, A). Minore = meglio."""
    probs = np.clip(np.asarray(probs, dtype=float), 1e-15, 1.0)
    y = np.array([_OUTCOME_INDEX[o] for o in outcomes])
    picked = probs[np.arange(len(y)), y]
    return float(-np.mean(np.log(picked)))


def brier_1x2(probs: np.ndarray, outcomes: list[str]) -> float:
    """Brier score multiclasse (range 0..2). Minore = meglio."""
    probs = np.asarray(probs, dtype=float)
    y = np.zeros_like(probs)
    for row, o in enumerate(outcomes):
        y[row, _OUTCOME_INDEX[o]] = 1.0
    return float(np.mean(np.sum((probs - y) ** 2, axis=1)))


# ---------------------------------------------------------------------- #
# Metriche Over/Under (binario)
# ---------------------------------------------------------------------- #
def log_loss_binary(prob_over: np.ndarray, is_over: np.ndarray) -> float:
    p = np.clip(np.asarray(prob_over, dtype=float), 1e-15, 1 - 1e-15)
    y = np.asarray(is_over, dtype=float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier_binary(prob_over: np.ndarray, is_over: np.ndarray) -> float:
    p = np.asarray(prob_over, dtype=float)
    y = np.asarray(is_over, dtype=float)
    return float(np.mean((p - y) ** 2))


# ---------------------------------------------------------------------- #
# Baseline di riferimento
# ---------------------------------------------------------------------- #
def base_rates_1x2(outcomes: list[str]) -> np.ndarray:
    """Frequenze empiriche (H,D,A) come baseline "banale" costante."""
    counts = np.array([sum(1 for o in outcomes if o == k) for k in "HDA"], dtype=float)
    return counts / counts.sum()
