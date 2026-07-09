"""Tuning dello shrinkage: prova piu' valori su piu' stagioni e confronta.

Cambiare UNA cosa alla volta e misurare: qui isoliamo l'effetto dello shrinkage
(regolarizzazione verso la media) sul log-loss 1X2, valutandolo su piu' stagioni
di test per non farci ingannare dal rumore di una sola stagione.

Esegue la griglia in parallelo (una combinazione stagione x shrinkage per
processo) per contenere i tempi.

Uso:
    python scripts/tune_shrinkage.py
    python scripts/tune_shrinkage.py --shrinkages 0 1 3 10 --seasons 2425 2526
"""

from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.backtest import run_backtest
from src.evaluation import metrics
from src.data import sources


def _evaluate(task: tuple[str, float]) -> dict:
    """Esegue un backtest (stagione, shrinkage) e ne calcola le metriche 1X2."""
    season, shrinkage = task
    df = run_backtest("serie_a", season, half_life_days=180.0,
                      shrinkage=shrinkage, verbose=False)
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()

    # Probabilita' di mercato (devig) sulle righe con quote valide.
    mkt = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    has = ~np.isnan(mkt).any(axis=1)
    out_mkt = [outcomes[i] for i in range(len(df)) if has[i]]

    return {
        "season": season,
        "shrinkage": shrinkage,
        "model_ll": metrics.log_loss_1x2(model, outcomes),
        "model_brier": metrics.brier_1x2(model, outcomes),
        "market_ll": metrics.log_loss_1x2(mkt[has], out_mkt),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tuning shrinkage.")
    parser.add_argument("--shrinkages", type=float, nargs="+",
                        default=[0.0, 1.0, 3.0, 10.0])
    parser.add_argument("--seasons", nargs="+", default=["2425", "2526"])
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    tasks = [(s, sh) for s in args.seasons for sh in args.shrinkages]
    print(f"Eseguo {len(tasks)} backtest ({len(args.seasons)} stagioni x "
          f"{len(args.shrinkages)} shrinkage) su {args.workers} processi...\n")

    with Pool(args.workers) as pool:
        results = pool.map(_evaluate, tasks)

    # Tabella: righe = shrinkage, colonne = stagioni (log-loss del modello).
    by = {(r["season"], r["shrinkage"]): r for r in results}
    print(f"{'shrinkage':>10}", end="")
    for s in args.seasons:
        print(f"{sources.season_label(s):>14}", end="")
    print(f"{'media':>10}")

    market_line = f"{'MERCATO':>10}"
    for s in args.seasons:
        mkt = by[(s, args.shrinkages[0])]["market_ll"]
        market_line += f"{mkt:>14.4f}"
    mkt_mean = np.mean([by[(s, args.shrinkages[0])]["market_ll"] for s in args.seasons])
    market_line += f"{mkt_mean:>10.4f}"
    print(market_line)
    print("-" * (10 + 14 * len(args.seasons) + 10))

    best_sh, best_mean = None, np.inf
    for sh in args.shrinkages:
        line = f"{sh:>10.1f}"
        vals = []
        for s in args.seasons:
            ll = by[(s, sh)]["model_ll"]
            vals.append(ll)
            line += f"{ll:>14.4f}"
        mean = float(np.mean(vals))
        line += f"{mean:>10.4f}"
        if mean < best_mean:
            best_mean, best_sh = mean, sh
        print(line)

    print(f"\nMigliore shrinkage (media log-loss piu' bassa): {best_sh} "
          f"-> {best_mean:.4f}")
    print("Nota: piu' basso = meglio. Confronta con la riga MERCATO in alto.")


if __name__ == "__main__":
    main()
