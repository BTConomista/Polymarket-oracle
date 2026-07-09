"""Tuning di un iperparametro: prova piu' valori su piu' stagioni e confronta.

Principio: cambiare UNA cosa alla volta e misurare. Si sceglie quale
iperparametro spazzare (--sweep) e con quali valori (--values); l'altro resta
fisso. La valutazione avviene su piu' stagioni di test per non farci ingannare
dal rumore di una sola stagione.

Esegue la griglia in parallelo (una combinazione stagione x valore per processo).

Esempi:
    # tara lo shrinkage (emivita fissa a 180g)
    python scripts/tune.py --sweep shrinkage --values 0 1 1.5 3 10

    # tara l'emivita del decadimento (shrinkage fisso a 1.5); 0 = nessun decadimento
    python scripts/tune.py --sweep half_life_days --values 0 90 180 365 730
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

# Stagioni di test di default: le tre piu' recenti (7a, 8a, 9a), ognuna con
# training abbondante grazie alle stagioni precedenti.
DEFAULT_SEASONS = ["2324", "2425", "2526"]


def _evaluate(task: tuple[str, float | None, float]) -> dict:
    """Esegue un backtest (stagione, emivita, shrinkage) e ne calcola le
    metriche 1X2 (log-loss del modello e del mercato)."""
    season, half_life, shrinkage = task
    df = run_backtest("serie_a", season, half_life_days=half_life,
                      shrinkage=shrinkage, verbose=False)
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()

    mkt = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    has = ~np.isnan(mkt).any(axis=1)
    out_mkt = [outcomes[i] for i in range(len(df)) if has[i]]

    return {
        "season": season,
        "half_life": half_life,
        "shrinkage": shrinkage,
        "model_ll": metrics.log_loss_1x2(model, outcomes),
        "market_ll": metrics.log_loss_1x2(mkt[has], out_mkt),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tuning di un iperparametro.")
    parser.add_argument("--sweep", choices=["shrinkage", "half_life_days"],
                        default="shrinkage", help="iperparametro da spazzare")
    parser.add_argument("--values", type=float, nargs="+",
                        default=[0.0, 1.0, 1.5, 3.0, 10.0],
                        help="valori da provare (per half_life_days, 0 = nessun decadimento)")
    parser.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    parser.add_argument("--half-life", type=float, default=180.0,
                        help="emivita fissa quando si spazza lo shrinkage")
    parser.add_argument("--shrinkage", type=float, default=1.5,
                        help="shrinkage fisso quando si spazza l'emivita")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    def build(season: str, value: float) -> tuple[str, float | None, float]:
        if args.sweep == "shrinkage":
            return (season, args.half_life, value)
        # half_life_days: 0 (o negativo) = nessun decadimento (None).
        hl = None if value <= 0 else value
        return (season, hl, args.shrinkage)

    tasks = [build(s, v) for s in args.seasons for v in args.values]
    fixed = (f"emivita={args.half_life}g" if args.sweep == "shrinkage"
             else f"shrinkage={args.shrinkage}")
    print(f"Spazzo '{args.sweep}' su {len(args.seasons)} stagioni ({fixed} fisso), "
          f"{len(tasks)} backtest su {args.workers} processi...\n")

    with Pool(args.workers) as pool:
        results = pool.map(_evaluate, tasks)

    by = {(r["season"], r["half_life"], r["shrinkage"]): r for r in results}

    print(f"{args.sweep:>14}", end="")
    for s in args.seasons:
        print(f"{sources.season_label(s):>12}", end="")
    print(f"{'media':>10}")

    # Riga mercato (uguale per tutti i valori: dipende solo dalla stagione).
    first = args.values[0]
    market_vals = [by[build(s, first)]["market_ll"] for s in args.seasons]
    mline = f"{'MERCATO':>14}" + "".join(f"{m:>12.4f}" for m in market_vals)
    mline += f"{np.mean(market_vals):>10.4f}"
    print(mline)
    print("-" * (14 + 12 * len(args.seasons) + 10))

    best_val, best_mean = None, np.inf
    for v in args.values:
        vals = [by[build(s, v)]["model_ll"] for s in args.seasons]
        mean = float(np.mean(vals))
        label = "no-decay" if (args.sweep == "half_life_days" and v <= 0) else f"{v:g}"
        line = f"{label:>14}" + "".join(f"{x:>12.4f}" for x in vals)
        line += f"{mean:>10.4f}"
        print(line)
        if mean < best_mean:
            best_mean, best_val = mean, v

    print(f"\nMigliore '{args.sweep}' (media log-loss piu' bassa): {best_val:g} "
          f"-> {best_mean:.4f}")
    print("Nota: piu' basso = meglio. Confronta con la riga MERCATO in alto.")


if __name__ == "__main__":
    main()
