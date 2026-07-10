"""Costruisce l'archivio interno dei dati (snapshot CSV + database SQLite).

Due modalita':

    python scripts/build_database.py            # offline: costruisce il DB dallo
                                                # snapshot congelato gia' versionato
    python scripts/build_database.py --enrich   # arricchisce lo snapshot ESISTENTE
                                                # (xG, valori rosa, assenze) senza
                                                # toccare la base football-data
    python scripts/build_database.py --refresh  # riscarica TUTTO dalle fonti,
                                                # arricchisce, aggiorna lo snapshot
                                                # e ricostruisce il DB

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
    parser.add_argument("--enrich", action="store_true",
                        help="arricchisce lo snapshot esistente (xG, rose, assenze)")
    parser.add_argument("--league", default="serie_a")
    args = parser.parse_args()

    if args.refresh or not database.SNAPSHOT_PATH.exists():
        print("Carico i dati dalle fonti (download)...")
        matches = loader.load_league(args.league, force_download=args.refresh)
        path = database.write_snapshot(matches)
        print(f"  snapshot aggiornato: {path}  ({len(matches)} partite)")
    elif args.enrich:
        # Arricchisce lo snapshot esistente SENZA riscaricare la base
        # football-data: la base resta congelata, si aggiungono/ricalcolano
        # solo le colonne xG / valori rosa / assenze.
        print(f"Arricchisco lo snapshot congelato: {database.SNAPSHOT_PATH}")
        matches = loader.enrich(database.read_snapshot())
        path = database.write_snapshot(matches)
        print(f"  snapshot arricchito: {path}  ({len(matches)} partite)")
    else:
        print(f"Uso lo snapshot congelato: {database.SNAPSHOT_PATH}")
        matches = database.read_snapshot()

    if "home_xg" in matches.columns:
        both_sq = (matches["home_squad_value"].notna()
                   & matches["away_squad_value"].notna())
        print("\nCopertura arricchimento per stagione:")
        print("  stagione   xG      rose(entrambe)")
        for season, grp in matches.groupby("season"):
            xg = grp["home_xg"].notna().mean()
            sq = both_sq[grp.index].mean()
            print(f"  {season}       {xg:6.1%}  {sq:6.1%}")

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
