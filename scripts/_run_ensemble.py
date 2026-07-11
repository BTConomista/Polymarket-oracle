"""Fase 12a — Ensemble di emivite (ultimo tweak economico non testato).

Idea: mescolare un modello a memoria CORTA (reattivo/forma) e uno a memoria
LUNGA (forza stabile) puo' battere la singola emivita 365g? Si mescolano le
PROBABILITA' 1X2 (stessa matrice di test, righe allineate). Tutti col prior.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import sources
from src.evaluation import metrics
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
HLS = [180.0, 365.0, 730.0]
PC = ["m_home", "m_draw", "m_away"]
CFG = dict(shrinkage=1.5, shots_blend=0.75, blend_signal="xg",
           promoted_prior=(0.23, 0.23))


def _worker(task):
    hl, s = task
    df = run_backtest("serie_a", s, hl, shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    return hl, s, df


def ll(df, probs):
    return metrics.log_loss_1x2(probs, df["result"].tolist())


def main():
    tasks = [(hl, s) for hl in HLS for s in SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    P = {(hl, s): df for hl, s, df in res}

    def probs(hl, s):
        return P[(hl, s)][PC].to_numpy()

    def season_ll(fn):
        return {s: ll(P[(365.0, s)], fn(s)) for s in SEASONS}

    variants = {
        "singola 180g": lambda s: probs(180.0, s),
        "singola 365g (ATTUALE)": lambda s: probs(365.0, s),
        "singola 730g": lambda s: probs(730.0, s),
        "blend 180+730 (50/50)": lambda s: 0.5 * probs(180.0, s) + 0.5 * probs(730.0, s),
        "blend 180+365+730 (1/3)": lambda s: (probs(180.0, s) + probs(365.0, s)
                                              + probs(730.0, s)) / 3.0,
        "blend 365+730 (50/50)": lambda s: 0.5 * probs(365.0, s) + 0.5 * probs(730.0, s),
    }
    base = {s: ll(P[(365.0, s)], probs(365.0, s)) for s in SEASONS}
    base_m = np.mean(list(base.values()))

    print("=" * 84)
    print(f"ENSEMBLE EMIVITE — 1X2 log-loss (ATTUALE 365g = {base_m:.4f}); Δ<0 = meglio")
    print("=" * 84)
    print(f"{'variante':<28}" + "".join(f"{s:>8}" for s in SEASONS) + f"{'MEDIA':>9}{'Δ':>9}{'migl.':>7}")
    for name, fn in variants.items():
        vals = {s: ll(P[(365.0, s)], fn(s)) for s in SEASONS}
        m = np.mean(list(vals.values()))
        imp = sum(vals[s] < base[s] - 1e-9 for s in SEASONS)
        print(f"{name:<28}" + "".join(f"{vals[s]:>8.4f}" for s in SEASONS)
              + f"{m:>9.4f}{m-base_m:>+9.4f}{imp:>5}/6")
    print("\n(Δ vs singola 365g. I blend mescolano le probabilita' 1X2, righe allineate.)")


if __name__ == "__main__":
    main()
