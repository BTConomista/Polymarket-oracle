"""Valutazione multi-mercato di un backtest.

Tutti i mercati derivano dalla STESSA matrice dei punteggi del modello, quindi
sono coerenti tra loro e "gratis". Qui li mettiamo tutti a confronto con realta',
mercato (dove abbiamo le quote) e baseline banale.

Mercati coperti:
  - 1X2            (multiclasse: casa / pareggio / ospite)    -> quote dirette
  - Over/Under 2.5 (binario)                                  -> quote dirette
  - GG/NG          (binario: entrambe segnano si'/no)         -> NIENTE quote
  - 1X / 2X / 12   (doppia chance, binari)  -> quote DERIVATE dalle 1X2

Nota onesta: per GG/NG non abbiamo quote nei dati (football-data non le include),
quindi c'e' solo modello vs realta' vs baseline. Per le doppie chance il "mercato"
e' ricavato dalle quote 1X2 devigate (1X = P(1)+P(X), ecc.): e' un benchmark
coerente ma indiretto.

Seconda nota onesta (audit Fase 15): le baseline usano le frequenze del campione
VALUTATO (in-sample) — la costante ottima a posteriori, un filo piu' forte della
baseline ex-ante giocabile davvero. Vale per tutti i mercati qui sotto; per il
GG/NG (che non ha quote) significa che il confronto "peggio della baseline" e'
severo: contro una baseline ex-ante il modello sarebbe un po' meno lontano.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import metrics


def _devig_1x2_rows(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Probabilita' di mercato 1X2 (devigate) per riga; maschera righe valide."""
    out = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            out[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    return out, ~np.isnan(out).any(axis=1)


def _binary(model_p, actual, market_p=None):
    """Metriche di un mercato binario. market_p None -> niente colonna mercato."""
    actual = np.asarray(actual, dtype=float)
    res = {
        "model_ll": metrics.log_loss_binary(model_p, actual),
        "model_brier": metrics.brier_binary(model_p, actual),
        "baseline_ll": metrics.log_loss_binary(
            np.full(len(actual), actual.mean()), actual),
    }
    if market_p is not None:
        has = np.isfinite(market_p)
        res["market_ll"] = metrics.log_loss_binary(market_p[has], actual[has])
        res["market_brier"] = metrics.brier_binary(market_p[has], actual[has])
    return res


def compute_market_metrics(df: pd.DataFrame) -> dict:
    """Metriche per tutti i mercati, da un DataFrame di backtest (una riga per
    partita, con le probabilita' del modello m_* e le quote odds_*)."""
    res = df["result"].tolist()
    out: dict[str, dict] = {}

    # --- 1X2 (multiclasse) ---
    model_1x2 = df[["m_home", "m_draw", "m_away"]].to_numpy()
    mkt_1x2, has = _devig_1x2_rows(df)
    o = [res[i] for i in range(len(df)) if has[i]]
    base = np.tile(metrics.base_rates_1x2(res), (len(df), 1))
    out["1X2"] = {
        "model_ll": metrics.log_loss_1x2(model_1x2, res),
        "model_brier": metrics.brier_1x2(model_1x2, res),
        "market_ll": metrics.log_loss_1x2(mkt_1x2[has], o),
        "market_brier": metrics.brier_1x2(mkt_1x2[has], o),
        "baseline_ll": metrics.log_loss_1x2(base, res),
    }

    # --- Over/Under 2.5 (binario) ---
    is_over = df["is_over"].to_numpy()
    mkt_over = np.full(len(df), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_over, r.odds_under]).all():
            mkt_over[i], _ = metrics.devig_binary(r.odds_over, r.odds_under)
    out["Over/Under 2.5"] = _binary(df["m_over"].to_numpy(), is_over, mkt_over)

    # --- GG/NG (binario, niente quote) ---
    out["GG/NG"] = _binary(df["m_btts"].to_numpy(), df["is_btts"].to_numpy())

    # --- Doppie chance (binari; mercato derivato dalle 1X2 devigate) ---
    H, D, A = df["m_home"].to_numpy(), df["m_draw"].to_numpy(), df["m_away"].to_numpy()
    mH, mD, mA = mkt_1x2[:, 0], mkt_1x2[:, 1], mkt_1x2[:, 2]
    r = np.array(res)
    dc = {
        "1X (casa o pari)": (H + D, np.isin(r, ["H", "D"]), mH + mD),
        "2X (ospite o pari)": (A + D, np.isin(r, ["A", "D"]), mA + mD),
        "12 (no pari)": (H + A, np.isin(r, ["H", "A"]), mH + mA),
    }
    for name, (mp, actual, mkt) in dc.items():
        out[name] = _binary(mp, actual.astype(float), mkt)

    return out
