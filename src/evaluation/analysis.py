"""Analisi degli errori: DOVE il modello perde rispetto al mercato.

Queste funzioni servono a capire *perche'* il modello e' meno bravo del mercato,
per orientare il lavoro successivo (feature engineering) verso i punti deboli
reali invece che tirare a indovinare.

Non introducono nuove metriche "di punteggio": scompongono quelle esistenti
(log-loss) per gruppi di partite e per fascia di probabilita' (calibrazione).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_OUTCOME_INDEX = {"H": 0, "D": 1, "A": 2}


def per_match_log_loss(probs: np.ndarray, outcomes: list[str]) -> np.ndarray:
    """Log-loss di OGNI partita (non la media): array lungo N.

    Utile per confrontare modello e mercato partita per partita e per raggruppare.
    """
    probs = np.clip(np.asarray(probs, dtype=float), 1e-15, 1.0)
    y = np.array([_OUTCOME_INDEX[o] for o in outcomes])
    return -np.log(probs[np.arange(len(y)), y])


def reliability_table(
    probs: np.ndarray, hits: np.ndarray, n_bins: int = 10
) -> pd.DataFrame:
    """Tabella di calibrazione (reliability diagram in forma tabellare).

    Dato un insieme di coppie (probabilita' assegnata, evento accaduto 0/1),
    raggruppa per fascia di probabilita' e confronta la probabilita' MEDIA
    assegnata con la FREQUENZA reale. Se il modello e' calibrato, le due colonne
    coincidono in ogni fascia.

    Args:
        probs: probabilita' assegnate (in [0,1]), gia' "appiattite".
        hits: 1 se l'evento associato e' accaduto, 0 altrimenti.
        n_bins: numero di fasce (default 10 = decili).
    """
    probs = np.asarray(probs, dtype=float)
    hits = np.asarray(hits, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(probs, edges) - 1, 0, n_bins - 1)

    rows = []
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            continue
        rows.append({
            "fascia": f"{edges[b]:.1f}-{edges[b+1]:.1f}",
            "n": int(mask.sum()),
            "prob_media": round(float(probs[mask].mean()), 3),
            "freq_reale": round(float(hits[mask].mean()), 3),
            "scarto": round(float(probs[mask].mean() - hits[mask].mean()), 3),
        })
    return pd.DataFrame(rows)


def flatten_1x2(probs: np.ndarray, outcomes: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Trasforma predizioni 1X2 in coppie (prob, hit) per la calibrazione.

    Ogni partita genera 3 coppie (una per esito): la probabilita' assegnata a
    quell'esito e se quell'esito si e' verificato.
    """
    probs = np.asarray(probs, dtype=float)
    flat_probs = probs.reshape(-1)
    hits = np.zeros_like(probs)
    for row, o in enumerate(outcomes):
        hits[row, _OUTCOME_INDEX[o]] = 1.0
    return flat_probs, hits.reshape(-1)


def gap_by_group(
    ll_model: np.ndarray, ll_market: np.ndarray, mask: np.ndarray
) -> dict:
    """Confronto modello vs mercato su un sottoinsieme di partite.

    Ritorna n, log-loss medio del modello, del mercato e il divario (gap>0 =
    il mercato e' migliore su quel gruppo).
    """
    m = np.asarray(mask, dtype=bool)
    if m.sum() == 0:
        return {"n": 0, "modello": np.nan, "mercato": np.nan, "gap": np.nan}
    mod = float(ll_model[m].mean())
    mkt = float(ll_market[m].mean())
    return {"n": int(m.sum()), "modello": mod, "mercato": mkt, "gap": mod - mkt}
