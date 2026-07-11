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
from src.evaluation import experiment_log
from src.data import loader, sources

# Stagioni di test di default: le tre piu' recenti (7a, 8a, 9a), ognuna con
# training abbondante grazie alle stagioni precedenti.
DEFAULT_SEASONS = ["2324", "2425", "2526"]

# Segnale secondario del blend e covariate, fissi durante uno sweep. Impostati in
# main(); i processi worker li ereditano al fork (Linux).
_BLEND_SIGNAL = "sot"
_COVARIATES: tuple[str, ...] = ()
_PROMOTED_PRIOR: tuple[float, float] | None = None


def _evaluate(task: tuple[str, float | None, float, float]) -> dict:
    """Esegue un backtest (stagione, emivita, shrinkage, shots_blend) e ne calcola
    tutte le metriche (via experiment_log.compute_metrics, fonte di verita' unica)."""
    season, half_life, shrinkage, shots_blend = task
    df = run_backtest("serie_a", season, half_life_days=half_life,
                      shrinkage=shrinkage, shots_blend=shots_blend,
                      blend_signal=_BLEND_SIGNAL, covariates=_COVARIATES,
                      promoted_prior=_PROMOTED_PRIOR, verbose=False)
    m = experiment_log.compute_metrics(df)
    return {
        "season": season,
        "half_life": half_life,
        "shrinkage": shrinkage,
        "shots_blend": shots_blend,
        "metrics": m,
        "model_ll": m["x2_model_logloss"],
        "market_ll": m["x2_market_logloss"],
        "ou_model_ll": m["ou_model_logloss"],
        "ou_market_ll": m["ou_market_logloss"],
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
    parser.add_argument("--half-life", type=float, default=365.0,
                        help="emivita fissa quando non e' quella spazzata")
    parser.add_argument("--shrinkage", type=float, default=1.5,
                        help="shrinkage fisso quando non e' quello spazzato")
    parser.add_argument("--shots-blend", type=float, default=0.75,
                        help="shots_blend fisso quando non e' quello spazzato "
                             "(default 0.75, config ufficiale)")
    parser.add_argument("--blend-signal", default="xg", choices=["sot", "xg", "npxg"],
                        help="segnale secondario del blend (default xg=xG reale)")
    parser.add_argument("--covariates", nargs="*", default=[],
                        choices=["squad_value", "absence", "rest", "rest_full"],
                        help="covariate di partita fisse (Fase 4c/4e)")
    parser.add_argument("--promoted-prior", type=float, default=None, metavar="DELTA",
                        help="prior di cold-start neopromosse fisso (Fase 7): "
                             "attacco -DELTA / difesa +DELTA. Assente = off.")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    global _BLEND_SIGNAL, _COVARIATES, _PROMOTED_PRIOR
    _BLEND_SIGNAL = args.blend_signal
    _COVARIATES = tuple(args.covariates)
    _PROMOTED_PRIOR = ((args.promoted_prior, args.promoted_prior)
                       if args.promoted_prior is not None else None)

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

    # Registra ogni backtest del tuning nel log (seriale: niente scritture
    # concorrenti). Ogni run resta cosi' replicabile e verificabile.
    fingerprint = experiment_log.data_fingerprint(loader.load_league("serie_a"))
    for r in results:
        config = {
            "league": "serie_a", "test_season": r["season"],
            "half_life_days": r["half_life"], "shrinkage": r["shrinkage"],
            "shots_blend": r["shots_blend"], "blend_signal": _BLEND_SIGNAL,
            "covariates": list(_COVARIATES),
            "promoted_prior": args.promoted_prior, "source": "tune.py",
        }
        experiment_log.append_run(
            experiment_log.make_record(config, r["metrics"], fingerprint))

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
