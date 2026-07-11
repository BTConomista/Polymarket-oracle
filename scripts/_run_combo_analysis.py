"""Fase 11 — Analisi delle COMBINAZIONI di feature off-di-default.

Finora le feature opzionali (covariate + ricalibrazioni post-hoc) sono state
valutate quasi sempre DA SOLE. Qui si testano le loro COMBINAZIONI, per vedere se
qualche mix supera il rumore in modo consistente sul modello ATTUALE (col prior).

Livello-modello (covariate, entrano nel fit congiunto):
  squad_value, absence, rest_full   -> tutti i 2^3 = 8 sottoinsiemi.
Post-hoc:
  ricalibrazione per-classe strutturale (pesi fissi w~casa 0.96 / pari 1.04 /
  ospite 1.00, robusti dalla Fase 10) applicata sopra ciascun modello.

Base = config ufficiale ATTUALE (emivita 365, shrinkage 1.5, α 0.75, xG, prior
0.23). Metrica principale: 1X2 log-loss walk-forward, 6 stagioni; si riportano
media, Δ vs ufficiale, e n. stagioni migliorate (consistenza).
"""
from __future__ import annotations

import itertools
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import calibration, markets, metrics
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
COV_OPTS = ["squad_value", "absence", "rest_full"]
COVSETS = [tuple(c) for k in range(len(COV_OPTS) + 1)
           for c in itertools.combinations(COV_OPTS, k)]
RECAL_W = (0.96, 1.04, 1.00)  # strutturale, Fase 10 (casa giu', pari su)
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
PC = ["m_home", "m_draw", "m_away"]


def _worker(task):
    ci, season = task
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"], covariates=COVSETS[ci],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return ci, season, df


def ll(df, probs=None):
    p = df[PC].to_numpy() if probs is None else probs
    return metrics.log_loss_1x2(p, df["result"].tolist())


def label(cov):
    return "ufficiale (solo prior)" if not cov else "+" + "+".join(cov)


def main():
    tasks = [(ci, s) for ci in range(len(COVSETS)) for s in SEASONS]
    print(f"Eseguo {len(tasks)} backtest ({len(COVSETS)} combo covariate x "
          f"{len(SEASONS)} stagioni)...", flush=True)
    dfs = {ci: {} for ci in range(len(COVSETS))}
    with Pool(5) as pool:
        for k, (ci, s, df) in enumerate(pool.imap_unordered(_worker, tasks), 1):
            dfs[ci][s] = df
            print(f"  [{k:>2}/{len(tasks)}] {label(COVSETS[ci]):<34} {s}", flush=True)

    base_ll = {s: ll(dfs[0][s]) for s in SEASONS}  # ufficiale (covset vuoto)
    base_mean = np.mean(list(base_ll.values()))

    print("\n" + "=" * 96)
    print(f"COMBINAZIONI — 1X2 log-loss walk-forward (base ufficiale = {base_mean:.4f}); "
          "Δ<0 = meglio")
    print("=" * 96)
    print(f"{'combinazione':<34}{'RAW media':>11}{'Δ':>9}{'migl.':>7}"
          f"{'+RECAL media':>14}{'Δ':>9}{'migl.':>7}")
    summary = []
    for ci, cov in enumerate(COVSETS):
        raw = {s: ll(dfs[ci][s]) for s in SEASONS}
        rec = {s: ll(dfs[ci][s],
                     calibration.apply_class_recalibration(dfs[ci][s][PC].to_numpy(), RECAL_W))
               for s in SEASONS}
        raw_m, rec_m = np.mean(list(raw.values())), np.mean(list(rec.values()))
        raw_imp = sum(raw[s] < base_ll[s] - 1e-9 for s in SEASONS)
        rec_imp = sum(rec[s] < base_ll[s] - 1e-9 for s in SEASONS)
        summary.append((label(cov), raw_m, rec_m, raw_imp, rec_imp))
        print(f"{label(cov):<34}{raw_m:>11.4f}{raw_m-base_mean:>+9.4f}{raw_imp:>5}/6"
              f"{rec_m:>14.4f}{rec_m-base_mean:>+9.4f}{rec_imp:>5}/6")

    # migliore combinazione complessiva
    best = min(summary, key=lambda r: min(r[1], r[2]))
    best_val = min(best[1], best[2])
    tag = "RAW" if best[1] <= best[2] else "+RECAL"
    print("-" * 96)
    print(f"MIGLIORE: {best[0]} ({tag})  media {best_val:.4f}  "
          f"Δ {best_val-base_mean:+.4f} vs ufficiale")

    # multi-mercato per la combinazione migliore vs ufficiale
    print("\n" + "=" * 96)
    print("MULTI-MERCATO — combinazione migliore vs ufficiale (pool 6 stagioni, gap vs mercato)")
    print("=" * 96)
    MK = ["1X2", "1X (casa o pari)", "2X (ospite o pari)", "12 (no pari)",
          "Over/Under 2.5", "GG/NG"]
    best_ci = summary.index(best)
    for name, ci in [("ufficiale", 0), (f"MIGLIORE ({best[0]})", best_ci)]:
        pool_df = pd.concat([dfs[ci][s] for s in SEASONS], ignore_index=True)
        mm = markets.compute_market_metrics(pool_df)
        cells = []
        for mk in MK:
            d = mm[mk]
            cells.append(d["model_ll"] - d.get("market_ll", d["baseline_ll"]))
        print(f"{name:<28}" + "".join(f"{c:>+11.4f}" for c in cells))
    print("  " + "".join(f"{m.split(' ')[0]:>11}" for m in MK).rjust(28 + 11 * len(MK)))


if __name__ == "__main__":
    main()
