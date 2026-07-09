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


def _evaluate(task: tuple[str, float | None, float, float]) -> dict:
    """Esegue un backtest (stagione, emivita, shrinkage, shots_blend) e ne calcola
    le metriche 1X2 (log-loss del modello e del mercato)."""
    season, half_life, shrinkage, shots_blend = task
    df = run_backtest("serie_a", season, half_life_days=half_life,
                      shrinkage=shrinkage, shots_blend=shots_blend, verbose=False)
    outcomes = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()

    mkt = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    has = ~np.isnan(mkt).any(axis=1)
    out_mkt = [outcomes[i] for i in range(len(df)) if has[i]]

    # Over/Under 2.5 (binario): utile perche' riguarda direttamente il volume gol.
    is_over = df["is_over"].to_numpy()
    ou_mkt = np.full(len(df), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_over, r.odds_under]).all():
            ou_mkt[i], _ = metrics.devig_binary(r.odds_over, r.odds_under)
    has_ou = ~np.isnan(ou_mkt)

    return {
        "season": season,
        "half_life": half_life,
        "shrinkage": shrinkage,
        "shots_blend": shots_blend,
        "model_ll": metrics.log_loss_1x2(model, outcomes),
        "market_ll": metrics.log_loss_1x2(mkt[has], out_mkt),
        "ou_model_ll": metrics.log_loss_binary(df["m_over"].to_numpy(), is_over),
        "ou_market_ll": metrics.log_loss_binary(ou_mkt[has_ou], is_over[has_ou]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tuning di un iperparametro.")
    parser.add_argument("--sweep",
                        choices=["shrinkage", "half_life_days", "shots_blend"],
                        default="shrinkage", help="iperparametro da spazzare")
    parser.add_argument("--values", type=float, nargs="+",
                        default=[0.0, 1.0, 1.5, 3.0, 10.0],
                        help="valori da provare (per half_life_days, 0 = nessun decadimento)")
    parser.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    parser.add_argument("--half-life", type=float, default=730.0,
                        help="emivita fissa quando non e' quella spazzata")
    parser.add_argument("--shrinkage", type=float, default=1.5,
                        help="shrinkage fisso quando non e' quello spazzato")
    parser.add_argument("--shots-blend", type=float, default=1.0,
                        help="shots_blend fisso quando non e' quello spazzato")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    def build(season: str, value: float) -> tuple[str, float | None, float, float]:
        hl, shr, sb = args.half_life, args.shrinkage, args.shots_blend
        if args.sweep == "shrinkage":
            shr = value
        elif args.sweep == "shots_blend":
            sb = value
        else:  # half_life_days: 0 (o negativo) = nessun decadimento (None).
            hl = None if value <= 0 else value
        return (season, hl, shr, sb)

    tasks = [build(s, v) for s in args.seasons for v in args.values]
    fixed_bits = []
    if args.sweep != "half_life_days":
        fixed_bits.append(f"emivita={args.half_life}g")
    if args.sweep != "shrinkage":
        fixed_bits.append(f"shrinkage={args.shrinkage}")
    if args.sweep != "shots_blend":
        fixed_bits.append(f"shots_blend={args.shots_blend}")
    print(f"Spazzo '{args.sweep}' su {len(args.seasons)} stagioni "
          f"({', '.join(fixed_bits)} fissi), "
          f"{len(tasks)} backtest su {args.workers} processi...\n")

    with Pool(args.workers) as pool:
        results = pool.map(_evaluate, tasks)

    by = {(r["season"], r["half_life"], r["shrinkage"], r["shots_blend"]): r
          for r in results}

    def print_table(title: str, model_key: str, market_key: str) -> float:
        """Stampa una tabella (righe=valori, colonne=stagioni) e ritorna il
        miglior valore dell'iperparametro per quella metrica."""
        print(f"\n=== {title} (log-loss; piu' basso = meglio) ===")
        header = f"{args.sweep:>14}" + "".join(
            f"{sources.season_label(s):>12}" for s in args.seasons) + f"{'media':>10}"
        print(header)
        market_vals = [by[build(s, args.values[0])][market_key] for s in args.seasons]
        print(f"{'MERCATO':>14}" + "".join(f"{m:>12.4f}" for m in market_vals)
              + f"{np.mean(market_vals):>10.4f}")
        print("-" * (14 + 12 * len(args.seasons) + 10))
        best_v, best_m = None, np.inf
        for v in args.values:
            vals = [by[build(s, v)][model_key] for s in args.seasons]
            mean = float(np.mean(vals))
            label = "no-decay" if (args.sweep == "half_life_days" and v <= 0) else f"{v:g}"
            print(f"{label:>14}" + "".join(f"{x:>12.4f}" for x in vals)
                  + f"{mean:>10.4f}")
            if mean < best_m:
                best_m, best_v = mean, v
        print(f"  -> migliore per {title}: {best_v:g} ({best_m:.4f})")
        return best_v

    print_table("1X2", "model_ll", "market_ll")
    print_table("OVER/UNDER 2.5", "ou_model_ll", "ou_market_ll")


if __name__ == "__main__":
    main()
