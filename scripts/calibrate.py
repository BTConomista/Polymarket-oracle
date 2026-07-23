"""Valida la ricalibrazione della confidenza (temperature scaling) walk-forward.

Per ogni stagione di test, il temperature T si TARA sulle predizioni
walk-forward delle stagioni PRECEDENTI (nessun look-ahead) e si applica alla
stagione di test. Confronta la log-loss 1X2 del modello prima e dopo.

Config del modello = ufficiale corrente, letta da ``src.config.SERIE_A``
(emivita, shrinkage, blend xG E prior neopromosse — la Fase 6 storica girava
senza prior perche' il prior non esisteva ancora; da allora la config ufficiale
lo include, Fase 7/8). Ogni stagione calibrata viene registrata in
experiments/runs.jsonl (config con calibration=temperature + T).

Uso:  python scripts/calibrate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import SERIE_A
from src.data import loader, sources
from src.evaluation import calibration, experiment_log
from scripts.backtest import run_backtest

HALF_LIFE = SERIE_A["half_life_days"]
SHRINK = SERIE_A["shrinkage"]
BLEND = SERIE_A["shots_blend"]
SIGNAL = SERIE_A["blend_signal"]
PRIOR = SERIE_A["promoted_prior"]
MIN_PRIOR_SEASONS = 2  # stagioni-predizione minime per tarare T
PROB_COLS = ["m_home", "m_draw", "m_away"]


def main() -> None:
    # La stagione piu' vecchia non e' backtestabile (nessuno storico prima):
    # le predizioni walk-forward partono dalla seconda stagione in poi.
    pred_seasons = list(sources.SEASONS)[1:]
    all_matches = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_matches)

    # 1) Predizioni walk-forward (baseline) per ogni stagione, una volta sola.
    preds: dict[str, pd.DataFrame] = {}
    for s in pred_seasons:
        print(f"backtest baseline {s} ...", flush=True)
        preds[s] = run_backtest("serie_a", s, HALF_LIFE, shrinkage=SHRINK,
                                 shots_blend=BLEND, blend_signal=SIGNAL,
                                 covariates=(),
                                 promoted_prior=(PRIOR, PRIOR) if PRIOR else None,
                                 verbose=False)

    # 2) Per ogni stagione di test: tara T sulle PRECEDENTI, applica, misura.
    rows = []
    for i, s in enumerate(pred_seasons):
        if i < MIN_PRIOR_SEASONS:
            continue
        prior = pd.concat([preds[pred_seasons[j]] for j in range(i)], ignore_index=True)
        T = calibration.fit_temperature(prior[PROB_COLS].to_numpy(),
                                         prior["result"].tolist())

        df = preds[s]
        m_base = experiment_log.compute_metrics(df)

        df_cal = df.copy()
        df_cal[PROB_COLS] = calibration.apply_temperature(df[PROB_COLS].to_numpy(), T)
        m_cal = experiment_log.compute_metrics(df_cal)

        # Registra la variante calibrata (config = ufficiale + calibrazione).
        config = {
            "league": "serie_a", "test_season": s,
            "half_life_days": HALF_LIFE, "shrinkage": SHRINK,
            "shots_blend": BLEND, "blend_signal": SIGNAL,
            "promoted_prior": PRIOR or None,
            "calibration": "temperature", "temperature": round(T, 4),
            "source": "calibrate_temperature",
        }
        experiment_log.append_run(experiment_log.make_record(config, m_cal, fp))

        rows.append({
            "season": s, "T": T,
            "base": m_base["x2_model_logloss"], "cal": m_cal["x2_model_logloss"],
            "base_brier": m_base["x2_model_brier"], "cal_brier": m_cal["x2_model_brier"],
            "market": m_base["x2_market_logloss"],
        })
        print(f"[{s}] T={T:.3f}  1X2 ll {m_base['x2_model_logloss']:.4f} -> "
              f"{m_cal['x2_model_logloss']:.4f}  (Δ {m_cal['x2_model_logloss']-m_base['x2_model_logloss']:+.4f})  "
              f"mercato {m_base['x2_market_logloss']:.4f}", flush=True)

    # 3) Riepilogo.
    print("\n" + "=" * 74)
    print("RICALIBRAZIONE CONFIDENZA (temperature) — 1X2 log-loss, piu' basso = meglio")
    print("=" * 74)
    print(f"{'stag.':<7}{'T':>7}{'base':>10}{'calibr.':>10}{'Δ':>10}"
          f"{'Δbrier':>10}{'mercato':>10}")
    agg = {"base": 0.0, "cal": 0.0, "market": 0.0, "dbr": 0.0}
    for r in rows:
        print(f"{r['season']:<7}{r['T']:>7.3f}{r['base']:>10.4f}{r['cal']:>10.4f}"
              f"{r['cal']-r['base']:>+10.4f}{r['cal_brier']-r['base_brier']:>+10.4f}"
              f"{r['market']:>10.4f}")
        agg["base"] += r["base"]; agg["cal"] += r["cal"]; agg["market"] += r["market"]
        agg["dbr"] += r["cal_brier"] - r["base_brier"]
    n = len(rows)
    print("-" * 74)
    print(f"{'MEDIA':<7}{'':>7}{agg['base']/n:>10.4f}{agg['cal']/n:>10.4f}"
          f"{(agg['cal']-agg['base'])/n:>+10.4f}{agg['dbr']/n:>+10.4f}{agg['market']/n:>10.4f}")
    print("\nΔ < 0 = la calibrazione MIGLIORA;  T>1 raffredda, T<1 scalda.")


if __name__ == "__main__":
    main()
