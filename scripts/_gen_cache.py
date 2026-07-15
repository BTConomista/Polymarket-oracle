"""Rigenera la cache dei backtest ufficiali (outputs/db_base_{stagione}.csv).

La cache e' l'output di run_backtest con la config UFFICIALE (config.SERIE_A),
una stagione per file: e' il punto di partenza di tutti gli script _run_* che
non rifittano il DC (market-implied, routing, profilo stagionale, ...). Il
container e' effimero: dopo un riavvio la cache va rigenerata (stessi dati
congelati + stesso codice = stessi numeri, riproducibilita' §5).

Uso:  python scripts/_gen_cache.py [stagione ...]     (default: tutte e 8)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import SERIE_A                     # noqa: E402
from scripts.backtest import run_backtest          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]


def _one(season: str) -> str:
    fp = CACHE / f"db_base_{season}.csv"
    if fp.exists():
        return f"{season}: gia' in cache"
    df = run_backtest(
        "serie_a", season, SERIE_A["half_life_days"],
        shrinkage=SERIE_A["shrinkage"], shots_blend=SERIE_A["shots_blend"],
        blend_signal=SERIE_A["blend_signal"],
        promoted_prior=(SERIE_A["promoted_prior"], SERIE_A["promoted_prior"]),
        verbose=False)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return f"{season}: {len(df)} partite -> {fp.name}"


def main() -> None:
    seasons = sys.argv[1:] or SEASONS
    with Pool(min(4, len(seasons))) as pool:
        for msg in pool.imap_unordered(_one, seasons):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
