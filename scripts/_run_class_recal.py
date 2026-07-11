"""Fase 10 — Ricalibrazione per-classe 1X2 (casa/pari/ospite), walk-forward.

Motivata dall'analisi del gap (Fase 9): il divario col mercato e' concentrato nel
PAREGGIO, e la calibrazione media mostra casa sovrastimata / pari sottostimato.
Il temperature scaling globale (Fase 6) non poteva correggerlo; 3 moltiplicatori
per classe si'.

I pesi (w_H, w_D, w_A) si tarano SOLO sulle stagioni precedenti (leave-future-out)
e si applicano alla stagione di test. Modello = ufficiale ATTUALE (gol+xG+prior).
Registra ogni stagione ricalibrata in experiments/runs.jsonl.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import calibration, experiment_log, metrics
from scripts.backtest import run_backtest

CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
MIN_PRIOR = 2
PC = ["m_home", "m_draw", "m_away"]


def mkt_1x2_ll(df):
    probs, ok = [], []
    for _, r in df.iterrows():
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            probs.append(metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away))
            ok.append(r.result)
    return metrics.log_loss_1x2(np.array(probs), ok)


def main():
    pred_seasons = list(sources.SEASONS)[1:]
    all_matches = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_matches)

    preds = {}
    for s in pred_seasons:
        print(f"backtest {s} ...", flush=True)
        preds[s] = run_backtest("serie_a", s, CFG["half_life_days"],
                                shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                                blend_signal=CFG["blend_signal"],
                                promoted_prior=CFG["promoted_prior"], verbose=False)

    rows = []
    for i, s in enumerate(pred_seasons):
        if i < MIN_PRIOR:
            continue
        prior = pd.concat([preds[pred_seasons[j]] for j in range(i)], ignore_index=True)
        w = calibration.fit_class_recalibration(prior[PC].to_numpy(),
                                                prior["result"].tolist())
        df = preds[s]
        base = metrics.log_loss_1x2(df[PC].to_numpy(), df["result"].tolist())
        recal_probs = calibration.apply_class_recalibration(df[PC].to_numpy(), w)
        recal = metrics.log_loss_1x2(recal_probs, df["result"].tolist())
        mkt = mkt_1x2_ll(df)

        df_cal = df.copy()
        df_cal[PC] = recal_probs
        m_cal = experiment_log.compute_metrics(df_cal)
        cfg = {**{k: v for k, v in CFG.items() if k != "promoted_prior"},
               "test_season": s, "league": "serie_a", "promoted_prior": 0.23,
               "calibration": "class_recal", "weights": [round(x, 4) for x in w],
               "source": "class_recal"}
        experiment_log.append_run(experiment_log.make_record(cfg, m_cal, fp))

        rows.append(dict(season=s, w=w, base=base, recal=recal, mkt=mkt))
        print(f"[{s}] w=(H {w[0]:.3f}, D {w[1]:.3f}, A {w[2]:.3f})  "
              f"1X2 {base:.4f}->{recal:.4f} ({recal-base:+.4f})  "
              f"gap {base-mkt:+.4f}->{recal-mkt:+.4f}", flush=True)

    print("\n" + "=" * 80)
    print("RICALIBRAZIONE PER-CLASSE 1X2 — pesi tarati sul passato, applicati al futuro")
    print("=" * 80)
    print(f"{'stag.':<7}{'w_H':>7}{'w_D':>7}{'w_A':>7}{'base':>10}{'recal':>10}"
          f"{'Δ':>9}{'gap base':>10}{'gap recal':>11}")
    agg = dict(base=0.0, recal=0.0, mkt=0.0)
    for r in rows:
        print(f"{r['season']:<7}{r['w'][0]:>7.3f}{r['w'][1]:>7.3f}{r['w'][2]:>7.3f}"
              f"{r['base']:>10.4f}{r['recal']:>10.4f}{r['recal']-r['base']:>+9.4f}"
              f"{r['base']-r['mkt']:>+10.4f}{r['recal']-r['mkt']:>+11.4f}")
        agg["base"] += r["base"]; agg["recal"] += r["recal"]; agg["mkt"] += r["mkt"]
    n = len(rows)
    print("-" * 80)
    print(f"{'MEDIA':<7}{'':>21}{agg['base']/n:>10.4f}{agg['recal']/n:>10.4f}"
          f"{(agg['recal']-agg['base'])/n:>+9.4f}{(agg['base']-agg['mkt'])/n:>+10.4f}"
          f"{(agg['recal']-agg['mkt'])/n:>+11.4f}")
    print("\nΔ < 0 = ricalibrazione migliora; w_D>1 = pari alzato, w_H<1 = casa abbassata.")


if __name__ == "__main__":
    main()
