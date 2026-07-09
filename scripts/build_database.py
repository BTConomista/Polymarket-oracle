"""Costruisce l'archivio interno dei dati (snapshot CSV + database SQLite).

Due modalita':

    python scripts/build_database.py            # offline: costruisce il DB dallo
                                                # snapshot congelato gia' versionato
    python scripts/build_database.py --refresh  # riscarica dalle fonti, aggiorna
                                                # lo snapshot e ricostruisce il DB

Lo snapshot (data/serie_a_matches.csv) e' versionato in git: e' la fonte di
verita' congelata, cosi' terzi e sessioni future hanno esattamente gli stessi
dati. Il database SQLite (data/football.db) e' rigenerabile e non versionato.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, loader
from src.evaluation import experiment_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Costruisce l'archivio dati interno.")
    parser.add_argument("--refresh", action="store_true",
                        help="riscarica dalle fonti e aggiorna lo snapshot")
    parser.add_argument("--league", default="serie_a")
    args = parser.parse_args()

    if args.refresh or not database.SNAPSHOT_PATH.exists():
        print("Carico i dati dalle fonti (download)...")
        matches = loader.load_league(args.league, force_download=args.refresh)
        path = database.write_snapshot(matches)
        print(f"  snapshot aggiornato: {path}  ({len(matches)} partite)")
    else:
        print(f"Uso lo snapshot congelato: {database.SNAPSHOT_PATH}")
        matches = database.read_snapshot()

    fingerprint = experiment_log.data_fingerprint(matches)
    db_path = database.build_db(matches, fingerprint)

    meta = database.read_meta(db_path)
    print(f"\nDatabase costruito: {db_path}")
    print(f"  partite:   {meta['n_matches']}")
    print(f"  stagioni:  {meta['n_seasons']}  ({meta['seasons']})")
    print(f"  impronta:  {meta['data_fingerprint']}")
    print("\nEsempio di query:")
    print("  sqlite3 data/football.db \"SELECT season, COUNT(*) FROM matches GROUP BY season\"")


if __name__ == "__main__":
    main()
