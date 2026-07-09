"""Registro degli esperimenti: rende ogni backtest tracciabile e replicabile.

Perche' esiste: i risultati di un backtest (metriche, ROI) devono essere
verificabili anche in futuro, da noi o da terzi/AI esterne. Per questo ogni run
viene registrato in append su ``experiments/runs.jsonl`` con TUTTO cio' che serve
a riprodurlo e a fidarsi del numero:
  - configurazione del modello (emivita, shrinkage, shots_blend, stagione, ...);
  - metriche calcolate (log-loss/Brier di modello, mercato e baseline; ROI);
  - provenienza: commit git del codice e "impronta" dei dati usati (cosi' si
    accorge se la fonte dati a monte e' cambiata).

Questo modulo centralizza anche il CALCOLO delle metriche di un backtest
(``compute_metrics``), usato sia per stampare il report sia per registrarlo:
un'unica fonte di verita', niente numeri calcolati in due modi diversi.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import metrics

RUNS_PATH = Path(__file__).resolve().parents[2] / "experiments" / "runs.jsonl"


# ---------------------------------------------------------------------- #
# Provenienza (per la replicabilita')
# ---------------------------------------------------------------------- #
def git_commit() -> str:
    """Hash del commit git corrente (o 'unknown' se non disponibile)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2],
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def data_fingerprint(df: pd.DataFrame) -> str:
    """Impronta breve e stabile dei dati usati (per accorgersi se cambiano).

    Basata su colonne oggettive delle partite; indipendente dall'ordine.
    """
    cols = ["date", "home_team", "away_team", "home_goals", "away_goals"]
    present = [c for c in cols if c in df.columns]
    key = df[present].astype(str).agg("|".join, axis=1)
    joined = "\n".join(sorted(key.tolist()))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------- #
# Calcolo metriche di un backtest (fonte di verita' unica)
# ---------------------------------------------------------------------- #
def _market_1x2(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    out = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            out[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    return out, ~np.isnan(out).any(axis=1)


def _market_over(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    out = np.full(len(df), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_over, r.odds_under]).all():
            out[i], _ = metrics.devig_binary(r.odds_over, r.odds_under)
    return out, ~np.isnan(out)


def value_bet_roi(df: pd.DataFrame, threshold: float = 0.05) -> tuple[int, float]:
    """ROI illustrativo su value bet 1X2 (edge del modello > soglia).

    Ritorna (numero scommesse, ROI %). ATTENZIONE: illustrativo, un backtest
    storico sovrastima quasi sempre la redditivita' reale.
    """
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    market, has = _market_1x2(df)
    cols = ["odds_home", "odds_draw", "odds_away"]
    stake = profit = 0.0
    n = 0
    for i in range(len(df)):
        if not has[i]:
            continue
        for k, key in enumerate("HDA"):
            if model[i, k] - market[i, k] > threshold:
                odds = df.iloc[i][cols[k]]
                n += 1
                stake += 1.0
                profit += (odds - 1.0) if outcomes[i] == key else -1.0
    roi = 100.0 * profit / stake if stake else 0.0
    return n, roi


def compute_metrics(df: pd.DataFrame) -> dict:
    """Tutte le metriche di un backtest, in un dizionario piatto."""
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    market, has = _market_1x2(df)
    out_mkt = [outcomes[i] for i in range(len(df)) if has[i]]

    is_over = df["is_over"].to_numpy()
    model_over = df["m_over"].to_numpy()
    ou_mkt, has_ou = _market_over(df)

    base_1x2 = np.tile(metrics.base_rates_1x2(outcomes), (len(df), 1))
    base_over = np.full(len(df), float(is_over.mean()))
    n_bets, roi = value_bet_roi(df)

    return {
        "n_matches": int(len(df)),
        # 1X2
        "x2_model_logloss": metrics.log_loss_1x2(model, outcomes),
        "x2_model_brier": metrics.brier_1x2(model, outcomes),
        "x2_market_logloss": metrics.log_loss_1x2(market[has], out_mkt),
        "x2_market_brier": metrics.brier_1x2(market[has], out_mkt),
        "x2_baseline_logloss": metrics.log_loss_1x2(base_1x2, outcomes),
        "x2_baseline_brier": metrics.brier_1x2(base_1x2, outcomes),
        # Over/Under 2.5
        "ou_model_logloss": metrics.log_loss_binary(model_over, is_over),
        "ou_model_brier": metrics.brier_binary(model_over, is_over),
        "ou_market_logloss": metrics.log_loss_binary(ou_mkt[has_ou], is_over[has_ou]),
        "ou_market_brier": metrics.brier_binary(ou_mkt[has_ou], is_over[has_ou]),
        "ou_baseline_logloss": metrics.log_loss_binary(base_over, is_over),
        # Value bet (illustrativo)
        "value_bet_n": n_bets,
        "value_bet_roi_pct": roi,
    }


# ---------------------------------------------------------------------- #
# Scrittura del registro
# ---------------------------------------------------------------------- #
def make_record(config: dict, metrics_dict: dict, fingerprint: str,
                timestamp: str | None = None) -> dict:
    """Costruisce un record completo e replicabile."""
    return {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data_fingerprint": fingerprint,
        "config": config,
        "metrics": metrics_dict,
    }


def append_run(record: dict, path: Path = RUNS_PATH) -> None:
    """Aggiunge un record al registro (una riga JSON per run)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
