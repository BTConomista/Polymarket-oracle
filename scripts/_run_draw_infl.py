"""Fase 12b — Inflazione della diagonale (draw_inflation): il cambio di classe.

Confronta modello ATTUALE vs ATTUALE+inflazione-diagonale, walk-forward, 6
stagioni, su tutti i mercati (l'inflazione tocca l'intera matrice dei punteggi:
1X2, O/U, GG/NG). Riporta 1X2 log-loss, calibrazione del pareggio e gap vs mercato.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, markets, metrics
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
MK = ["1X2", "1X (casa o pari)", "2X (ospite o pari)", "12 (no pari)",
      "Over/Under 2.5", "GG/NG"]


def _worker(task):
    infl, s = task
    df = run_backtest("serie_a", s, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], draw_inflation=infl,
                      verbose=False)
    df["season"] = s
    return infl, s, df


def main():
    tasks = [(infl, s) for infl in (False, True) for s in SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    P = {(infl, s): df for infl, s, df in res}
    fp = experiment_log.data_fingerprint(loader.load_league("serie_a"))

    print("=" * 86)
    print("INFLAZIONE DIAGONALE — 1X2 log-loss e calibrazione pareggio (6 stagioni)")
    print("=" * 86)
    print(f"{'stag.':<7}{'base':>9}{'+infl':>9}{'Δ':>9}"
          f"{'P(pari)base':>13}{'P(pari)infl':>13}{'reale':>8}")
    agg = {"b": 0.0, "i": 0.0}
    for s in SEASONS:
        b, i = P[(False, s)], P[(True, s)]
        bll = metrics.log_loss_1x2(b[["m_home", "m_draw", "m_away"]].to_numpy(), b["result"].tolist())
        ill = metrics.log_loss_1x2(i[["m_home", "m_draw", "m_away"]].to_numpy(), i["result"].tolist())
        real = (b["result"] == "D").mean()
        # registra la variante inflazione
        m_i = experiment_log.compute_metrics(i)
        cfg = {**{k: v for k, v in CFG.items() if k != "promoted_prior"},
               "test_season": s, "league": "serie_a", "promoted_prior": 0.23,
               "draw_inflation": True, "source": "draw_infl"}
        experiment_log.append_run(experiment_log.make_record(cfg, m_i, fp))
        agg["b"] += bll; agg["i"] += ill
        print(f"{s:<7}{bll:>9.4f}{ill:>9.4f}{ill-bll:>+9.4f}"
              f"{b['m_draw'].mean():>13.3f}{i['m_draw'].mean():>13.3f}{real:>8.3f}")
    n = len(SEASONS)
    print("-" * 86)
    print(f"{'MEDIA':<7}{agg['b']/n:>9.4f}{agg['i']/n:>9.4f}{(agg['i']-agg['b'])/n:>+9.4f}")

    # Multi-mercato (pool 6 stagioni): gap vs mercato base vs +infl
    print("\n" + "=" * 86)
    print("MULTI-MERCATO — gap vs mercato (pool 6 stagioni; GG/NG vs baseline)")
    print("=" * 86)
    print(f"{'variante':<12}" + "".join(f"{m.split(' ')[0]:>12}" for m in MK))
    for name, infl in [("base", False), ("+inflazione", True)]:
        pool_df = pd.concat([P[(infl, s)] for s in SEASONS], ignore_index=True)
        mm = markets.compute_market_metrics(pool_df)
        cells = [mm[m]["model_ll"] - mm[m].get("market_ll", mm[m]["baseline_ll"]) for m in MK]
        print(f"{name:<12}" + "".join(f"{c:>+12.4f}" for c in cells))


if __name__ == "__main__":
    main()
