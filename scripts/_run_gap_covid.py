"""Gap col mercato: COVID vs post-COVID, e trend delle ultime stagioni.

Versione ATTUALE del modello (gol+xG+prior). Per ogni stagione e mercato calcola
il gap (model_ll - market_ll; GG/NG vs baseline) e i valori assoluti, poi
aggrega per periodo COVID/transizione/post-COVID e mostra il trend recente.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import markets
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
LABEL = {"2021": "2020-21", "2122": "2021-22", "2223": "2022-23",
         "2324": "2023-24", "2425": "2024-25", "2526": "2025-26"}
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
MK = ["1X2", "1X (casa o pari)", "2X (ospite o pari)", "12 (no pari)",
      "Over/Under 2.5", "GG/NG"]
SHORT = {"1X2": "1X2", "1X (casa o pari)": "1X", "2X (ospite o pari)": "2X",
         "12 (no pari)": "12", "Over/Under 2.5": "O/U2.5", "GG/NG": "GG/NG"}


def _worker(s):
    return s, run_backtest("serie_a", s, CFG["half_life_days"],
                           shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                           blend_signal=CFG["blend_signal"],
                           promoted_prior=CFG["promoted_prior"], verbose=False)


def gap(mm, mk):
    d = mm[mk]
    return d["model_ll"] - d.get("market_ll", d["baseline_ll"])


def main():
    with Pool(6) as pool:
        res = dict(pool.map(_worker, SEASONS))
    per = {s: markets.compute_market_metrics(res[s]) for s in SEASONS}

    # 1) Tabella gap per stagione x mercato
    print("=" * 78)
    print("GAP per STAGIONE x MERCATO (model_ll - market_ll; GG/NG vs baseline)")
    print("=" * 78)
    print(f"{'stagione':<10}" + "".join(f"{SHORT[m]:>9}" for m in MK))
    for s in SEASONS:
        print(f"{LABEL[s]:<10}" + "".join(f"{gap(per[s], m):>+9.4f}" for m in MK))

    # 2) Aggregati per periodo (stagioni equipopolate -> media = pool)
    groups = {"COVID (2020-21)": ["2021"],
              "transizione (2021-22)": ["2122"],
              "post-COVID (2022-26)": ["2223", "2324", "2425", "2526"]}
    print("\n" + "=" * 78)
    print("AGGREGATO per PERIODO")
    print("=" * 78)
    print(f"{'periodo':<24}" + "".join(f"{SHORT[m]:>9}" for m in MK))
    gm = {}
    for name, ss in groups.items():
        vals = [np.mean([gap(per[s], m) for s in ss]) for m in MK]
        gm[name] = vals
        print(f"{name:<24}" + "".join(f"{v:>+9.4f}" for v in vals))
    print("-" * (24 + 9 * len(MK)))
    diff = [gm["post-COVID (2022-26)"][i] - gm["COVID (2020-21)"][i] for i in range(len(MK))]
    print(f"{'Δ post − COVID':<24}" + "".join(f"{d:>+9.4f}" for d in diff))
    print("  (Δ < 0 = gap piu' piccolo dopo il COVID = modello piu' vicino al mercato)")

    # 3) Valori assoluti 1X2: dove si muove, modello o mercato?
    print("\n" + "=" * 78)
    print("1X2 ASSOLUTO — modello vs mercato per stagione")
    print("=" * 78)
    print(f"{'stagione':<10}{'modello':>10}{'mercato':>10}{'gap':>10}")
    for s in SEASONS:
        d = per[s]["1X2"]
        print(f"{LABEL[s]:<10}{d['model_ll']:>10.4f}{d['market_ll']:>10.4f}"
              f"{d['model_ll']-d['market_ll']:>+10.4f}")

    # 4) Trend ultime 3 stagioni per mercato
    print("\n" + "=" * 78)
    print("TREND ultime 3 stagioni (2023-24 -> 2024-25 -> 2025-26)")
    print("=" * 78)
    last3 = ["2324", "2425", "2526"]
    print(f"{'mercato':<10}" + "".join(f"{LABEL[s]:>10}" for s in last3)
          + f"{'Δ(25/26−23/24)':>16}")
    for m in MK:
        vals = [gap(per[s], m) for s in last3]
        arrow = "↓ meglio" if vals[-1] < vals[0] - 0.0005 else (
            "↑ peggio" if vals[-1] > vals[0] + 0.0005 else "≈ stabile")
        print(f"{SHORT[m]:<10}" + "".join(f"{v:>+10.4f}" for v in vals)
              + f"{vals[-1]-vals[0]:>+11.4f}  {arrow}")


if __name__ == "__main__":
    main()
