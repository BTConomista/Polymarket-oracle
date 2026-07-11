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
_ODDS_1X2 = ("odds_home", "odds_draw", "odds_away")
_ODDS_1X2_OPEN = ("odds_home_open", "odds_draw_open", "odds_away_open")
_ODDS_OU = ("odds_over", "odds_under")
_ODDS_OU_OPEN = ("odds_over_open", "odds_under_open")


def _market_1x2(df: pd.DataFrame,
                cols: tuple[str, str, str] = _ODDS_1X2) -> tuple[np.ndarray, np.ndarray]:
    out = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        odds = [r[c] for c in cols]
        if np.isfinite(odds).all():
            out[i] = metrics.devig_1x2(*odds)
    return out, ~np.isnan(out).any(axis=1)


def _market_over(df: pd.DataFrame,
                 cols: tuple[str, str] = _ODDS_OU) -> tuple[np.ndarray, np.ndarray]:
    out = np.full(len(df), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        odds = [r[c] for c in cols]
        if np.isfinite(odds).all():
            out[i], _ = metrics.devig_binary(*odds)
    return out, ~np.isnan(out)


def value_bet_roi(df: pd.DataFrame, threshold: float = 0.05,
                  odds_cols: tuple[str, str, str] = _ODDS_1X2) -> tuple[int, float]:
    """ROI illustrativo su value bet 1X2 (edge del modello > soglia).

    ``odds_cols`` sceglie la linea contro cui si scommette (chiusura di default;
    apertura per il test CLV della Fase 14): l'edge e' misurato vs quella linea
    e la scommessa e' pagata a QUELLA quota. Ritorna (numero scommesse, ROI %).
    ATTENZIONE: illustrativo, un backtest storico sovrastima quasi sempre la
    redditivita' reale.
    """
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    market, has = _market_1x2(df, odds_cols)
    stake = profit = 0.0
    n = 0
    for i in range(len(df)):
        if not has[i]:
            continue
        for k, key in enumerate("HDA"):
            if model[i, k] - market[i, k] > threshold:
                odds = df.iloc[i][odds_cols[k]]
                n += 1
                stake += 1.0
                profit += (odds - 1.0) if outcomes[i] == key else -1.0
    roi = 100.0 * profit / stake if stake else 0.0
    return n, roi


def clv_stats(df: pd.DataFrame, threshold: float = 0.05) -> tuple[int, float, float]:
    """Closing Line Value delle selezioni fatte alla linea di APERTURA.

    Per ogni value bet individuata contro la linea di apertura (edge del modello
    > soglia), misura se la CHIUSURA si e' mossa verso il modello:
    CLV = prob_chiusura(selezione) - prob_apertura(selezione), devigate.
    CLV > 0 = il mercato ha dato ragione al modello (prezzo preso migliore della
    chiusura): e' il test che i professionisti usano per distinguere edge da
    fortuna, PRIMA di guardare il ROI (rumorosissimo).

    Ritorna (n selezioni, CLV medio in punti di probabilita', quota di CLV>0).
    """
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    open_p, has_open = _market_1x2(df, _ODDS_1X2_OPEN)
    close_p, has_close = _market_1x2(df, _ODDS_1X2)
    clvs: list[float] = []
    for i in range(len(df)):
        if not (has_open[i] and has_close[i]):
            continue
        for k in range(3):
            if model[i, k] - open_p[i, k] > threshold:
                clvs.append(close_p[i, k] - open_p[i, k])
    if not clvs:
        return 0, float("nan"), float("nan")
    arr = np.array(clvs)
    return len(arr), float(arr.mean()), float((arr > 0).mean())


def compute_metrics(df: pd.DataFrame) -> dict:
    """Tutte le metriche di un backtest, in un dizionario piatto."""
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    market, has = _market_1x2(df)
    out_mkt = [outcomes[i] for i in range(len(df)) if has[i]]

    is_over = df["is_over"].to_numpy()
    model_over = df["m_over"].to_numpy()
    ou_mkt, has_ou = _market_over(df)

    # NOTA ONESTA (audit Fase 15): la baseline usa le frequenze della stagione
    # di test STESSA (in-sample), quindi e' la costante ottima a posteriori --
    # leggermente piu' forte della baseline ex-ante (frequenze delle sole
    # stagioni precedenti). Direzione conservativa per il modello; mantenuta
    # per continuita' con lo storico del registro (233+ run gia' scritte).
    base_1x2 = np.tile(metrics.base_rates_1x2(outcomes), (len(df), 1))
    base_over = np.full(len(df), float(is_over.mean()))
    n_bets, roi = value_bet_roi(df)

    # Metriche vs linea di APERTURA (Fase 14): solo se il df ha le colonne
    # *_open con almeno una riga valida (retrocompatibile: i backtest storici
    # non le hanno e il dizionario resta identico a prima).
    open_metrics: dict = {}
    if set(_ODDS_1X2_OPEN) <= set(df.columns):
        open_1x2, has_open = _market_1x2(df, _ODDS_1X2_OPEN)
        if has_open.any():
            out_open = [outcomes[i] for i in range(len(df)) if has_open[i]]
            n_open, roi_open = value_bet_roi(df, odds_cols=_ODDS_1X2_OPEN)
            clv_n, clv_mean, clv_pos = clv_stats(df)
            open_metrics.update({
                "x2_market_open_logloss": metrics.log_loss_1x2(open_1x2[has_open], out_open),
                "x2_market_open_brier": metrics.brier_1x2(open_1x2[has_open], out_open),
                # Modello sulle STESSE righe della linea di apertura (audit
                # Fase 15): senza queste, un gap modello-vs-apertura ricavato
                # dal registro confronterebbe insiemi di partite diversi.
                "x2_model_open_logloss": metrics.log_loss_1x2(model[has_open], out_open),
                "x2_model_open_brier": metrics.brier_1x2(model[has_open], out_open),
                "value_bet_open_n": n_open,
                "value_bet_open_roi_pct": roi_open,
                "clv_n": clv_n,
                "clv_mean_prob": clv_mean,
                "clv_positive_share": clv_pos,
            })
    if set(_ODDS_OU_OPEN) <= set(df.columns):
        ou_open, has_ou_open = _market_over(df, _ODDS_OU_OPEN)
        if has_ou_open.any():
            open_metrics.update({
                "ou_market_open_logloss": metrics.log_loss_binary(
                    ou_open[has_ou_open], is_over[has_ou_open]),
                "ou_market_open_brier": metrics.brier_binary(
                    ou_open[has_ou_open], is_over[has_ou_open]),
                # Modello sulle stesse righe (vedi nota sopra per l'1X2).
                "ou_model_open_logloss": metrics.log_loss_binary(
                    model_over[has_ou_open], is_over[has_ou_open]),
                "ou_model_open_brier": metrics.brier_binary(
                    model_over[has_ou_open], is_over[has_ou_open]),
            })

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
    } | open_metrics


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
