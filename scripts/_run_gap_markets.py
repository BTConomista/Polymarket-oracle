"""Fase 15-bis — Gap col mercato PER MERCATO, stagione per stagione.

La Fase 9 aveva scomposto il gap per mercato solo in AGGREGATO (pool 6 stagioni)
e per stagione solo sull'1X2. Qui la matrice completa: ogni mercato x ogni
stagione, con la config ufficiale. Domande a cui risponde:
  - il "quasi-zero" del mercato 12 (no pari) regge in OGNI stagione o e' una
    media che nasconde stagioni storte?
  - il gap del pareggio (visibile in 1X/2X vs 12) e' stabile nel tempo?
  - l'Over/Under ha un trend?

Convenzioni identiche ad analyze_gap.py: gap = model_ll - market_ll (>0 = il
mercato e' migliore). Per GG/NG non esistono quote nei dati: si riporta il gap
vs BASELINE (in-sample, quindi severa: vedi audit Fase 15) e lo si marca.

Uso:  python scripts/_run_gap_markets.py     (6 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, markets
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
MARKET_ORDER = ["1X2", "1X (casa o pari)", "2X (ospite o pari)", "12 (no pari)",
                "Over/Under 2.5", "GG/NG"]


def _worker(season):
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    return season, df


def main():
    with Pool(6) as pool:
        res = pool.map(_worker, SEASONS)
    dfs = dict(res)

    # Registro replicabile (regola Fase 15: nessuna analisi senza run).
    fp = experiment_log.data_fingerprint(loader.load_league("serie_a"))
    for s, df in dfs.items():
        cfg = {"source": "gap_markets", "league": "serie_a", "test_season": s,
               **{k: v for k, v in CFG.items() if k != "promoted_prior"},
               "promoted_prior": 0.23}
        experiment_log.append_run(experiment_log.make_record(
            cfg, experiment_log.compute_metrics(df), fp))

    # Gap per (mercato, stagione). GG/NG: vs baseline (niente quote), marcato.
    gaps = {mk: {} for mk in MARKET_ORDER}
    for s in SEASONS:
        mm = markets.compute_market_metrics(dfs[s])
        for mk in MARKET_ORDER:
            d = mm[mk]
            gaps[mk][s] = d["model_ll"] - d.get("market_ll", d["baseline_ll"])

    print("=" * 92)
    print("GAP COL MERCATO PER MERCATO E STAGIONE — config ufficiale; "
          "gap>0 = mercato migliore")
    print("=" * 92)
    print(f"{'mercato':<22}" + "".join(f"{s:>9}" for s in SEASONS)
          + f"{'MEDIA':>10}{'min..max':>16}")
    for mk in MARKET_ORDER:
        row = [gaps[mk][s] for s in SEASONS]
        tag = mk if mk != "GG/NG" else "GG/NG (vs BASE)"
        print(f"{tag:<22}" + "".join(f"{g:>+9.4f}" for g in row)
              + f"{np.mean(row):>+10.4f}"
              + f"{min(row):>+8.4f}..{max(row):+.4f}")
    print("\nNote: 380 partite/stagione, quote 1X2 e O/U complete; le doppie")
    print("chance usano il mercato DERIVATO dalle 1X2 devigate (benchmark")
    print("indiretto); GG/NG non ha quote -> gap vs baseline in-sample (severa).")


if __name__ == "__main__":
    main()
