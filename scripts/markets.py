"""Grande operazione di backtesting multi-mercato e multi-config.

Valuta il modello su TUTTI i mercati derivabili dalla matrice dei punteggi
(1X2, Over/Under 2.5, GG/NG, doppie chance 1X/2X/12), confrontando diverse
CONFIGURAZIONI del modello, su piu' stagioni, contro mercato e baseline.

Uso:
    python scripts/markets.py                       # config base vs ufficiale, 6 stagioni
    python scripts/markets.py --seasons 2425 2526   # stagioni specifiche

E' un backtest onesto: per GG/NG non ci sono quote nei dati (colonna mercato
vuota); le doppie chance usano quote derivate dalle 1X2.
"""

from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.backtest import run_backtest
from src.evaluation import markets

DEFAULT_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]

# Configurazioni da confrontare (il "combinazioni di dati e modelli" richiesto).
CONFIGS: dict[str, dict] = {
    "gol (base)": dict(half_life_days=730, shrinkage=1.5, shots_blend=1.0,
                       blend_signal="xg"),
    "ufficiale (gol+xG)": dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
                               blend_signal="xg"),
}

MARKET_ORDER = ["1X2", "Over/Under 2.5", "GG/NG",
                "1X (casa o pari)", "2X (ospite o pari)", "12 (no pari)"]


def _evaluate(task: tuple[str, str]) -> dict:
    """Un backtest (config, stagione) -> metriche per-mercato."""
    config_name, season = task
    cfg = CONFIGS[config_name]
    df = run_backtest("serie_a", season, verbose=False, **cfg)
    return {"config": config_name, "season": season,
            "markets": markets.compute_market_metrics(df)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest multi-mercato.")
    parser.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    tasks = [(c, s) for c in CONFIGS for s in args.seasons]
    print(f"Grande backtest: {len(CONFIGS)} config x {len(args.seasons)} stagioni "
          f"x tutti i mercati = {len(tasks)} run su {args.workers} processi...\n")

    with Pool(args.workers) as pool:
        results = pool.map(_evaluate, tasks)

    # Media per (config, mercato) sulle stagioni.
    def avg(config_name: str, market: str, key: str) -> float:
        vals = [r["markets"][market].get(key, np.nan)
                for r in results if r["config"] == config_name]
        vals = [v for v in vals if np.isfinite(v)]
        return float(np.mean(vals)) if vals else np.nan

    cfg_names = list(CONFIGS)
    print("=" * 78)
    print(f"LOG-LOSS MEDIO SU {len(args.seasons)} STAGIONI (piu' basso = meglio)")
    print("=" * 78)
    header = f"{'mercato':<22}" + "".join(f"{c:>20}" for c in cfg_names) \
        + f"{'mercato':>10}{'baseline':>10}"
    print(header)
    print("-" * len(header))
    for mk in MARKET_ORDER:
        row = f"{mk:<22}"
        for c in cfg_names:
            row += f"{avg(c, mk, 'model_ll'):>20.4f}"
        mkt = avg(cfg_names[0], mk, "market_ll")
        base = avg(cfg_names[0], mk, "baseline_ll")
        row += (f"{mkt:>10.4f}" if np.isfinite(mkt) else f"{'—':>10}")
        row += f"{base:>10.4f}"
        print(row)

    print("\nNote:")
    print("  - 'mercato' e 'baseline' sono uguali per tutte le config (non dipendono")
    print("    dal modello); per GG/NG non ci sono quote nei dati (—).")
    print("  - doppie chance: quote derivate dalle 1X2 devigate.")
    print("  - un modello e' UTILE se batte la baseline; e' FORTE se si avvicina al")
    print("    mercato; nessuno di questi lo batte (atteso).")


if __name__ == "__main__":
    main()
