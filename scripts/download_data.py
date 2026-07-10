"""Scarica in locale i CSV storici (cache in data/raw/).

Uso:
    python scripts/download_data.py                # tutte le stagioni di Serie A
    python scripts/download_data.py --force        # riscarica ignorando la cache

I dati sono rigenerabili, quindi data/raw/ e' escluso dal versionamento git.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Rende importabile il package "src" quando si lancia lo script direttamente.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Scarica i dati storici.")
    parser.add_argument("--league", default="serie_a", help="chiave campionato")
    parser.add_argument("--force", action="store_true", help="riscarica tutto")
    args = parser.parse_args()

    league = sources.LEAGUES[args.league]
    print(f"Campionato: {league.name}  ({len(sources.SEASONS)} stagioni)")
    for code in sources.SEASONS:
        path = loader.download_season(code, league, force=args.force)
        n = sum(1 for _ in open(path)) - 1
        print(f"  {sources.season_label(code)}: {n} partite  ->  {path.name}")

    if args.league in sources.UNDERSTAT_LEAGUES:
        from src.data import transfermarkt, understat

        print("\nUnderstat (xG):")
        for code in sources.SEASONS:
            path = understat.download_season(code, args.league, force=args.force)
            print(f"  {sources.season_label(code)}  ->  {path.name}")

        print("\nTransfermarkt (datalake):")
        for table in sources.TRANSFERMARKT_TABLES:
            path = transfermarkt.download_table(table, force=args.force)
            print(f"  {table}  ->  {path.name}")

    print("Fatto.")


if __name__ == "__main__":
    main()
