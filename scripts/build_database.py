"""Costruisce l'archivio interno dei dati (snapshot CSV + database SQLite).

Due modalita':

    python scripts/build_database.py            # offline: costruisce il DB dallo
                                                # snapshot congelato gia' versionato
    python scripts/build_database.py --enrich   # arricchisce lo snapshot ESISTENTE
                                                # (xG, valori rosa, assenze) senza
                                                # toccare la base football-data
    python scripts/build_database.py --fixtures # assembla il CALENDARIO DI CLUB
                                                # completo (Serie A + coppe +
                                                # Europa) in data/club_fixtures.csv
                                                # e aggiunge le colonne
                                                # rest_days_full/midweek_europe
                                                # allo snapshot (congestione vera)
    python scripts/build_database.py --open-odds # aggancia le quote PRE-chiusura
                                                # (colonne *_open, Fase 14) allo
                                                # snapshot dai CSV grezzi (cache
                                                # data/raw/, scarica se mancanti)
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
    parser.add_argument("--fixtures", action="store_true",
                        help="assembla il calendario di club completo e aggiunge "
                             "le colonne rest_days_full/midweek_europe allo snapshot")
    parser.add_argument("--open-odds", action="store_true",
                        help="aggancia le quote pre-chiusura (colonne *_open) allo "
                             "snapshot dai CSV grezzi football-data (Fase 14)")
    parser.add_argument("--league", default="serie_a")
    args = parser.parse_args()

    if args.refresh or not database.SNAPSHOT_PATH.exists():
        print("Carico i dati dalle fonti (download)...")
        matches = loader.load_league(args.league, force_download=args.refresh)
        # Il riposo solo-Serie-A viene ricalcolato al load; qui aggiungiamo anche
        # la CONGESTIONE VERA dal calendario di club completo, cosi' un refresh
        # non perde le colonne rest_days_full/midweek_europe.
        if args.league == "serie_a":
            from src.data import fixtures as fixtures_mod
            fx = fixtures_mod.build_club_fixtures(matches, force=args.refresh)
            fixtures_mod.write_club_fixtures(fx)
            matches = fixtures_mod.add_rest_days_full(matches, fx)
        # Il riposo solo-Serie-A si ricalcola al load (non si versiona): lo si
        # toglie dallo snapshot per non congelarlo (rest_days_full invece SI').
        matches = matches.drop(
            columns=["home_rest_days", "away_rest_days"], errors="ignore"
        )
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
    elif args.fixtures:
        # Assembla il CALENDARIO DI CLUB completo (Serie A dallo snapshot +
        # coppe/Europa da openfootball) e aggiunge le colonne di congestione
        # calcolate sul calendario COMPLETO. La base football-data resta congelata.
        from src.data import fixtures as fixtures_mod
        print("Assemblo il calendario di club completo (Serie A + coppe + Europa)...")
        snap = database.read_snapshot()
        fx = fixtures_mod.build_club_fixtures(snap, force=False)
        fx_path = fixtures_mod.write_club_fixtures(fx)
        print(f"  calendario di club: {fx_path}  ({len(fx)} righe squadra-partita)")
        matches = fixtures_mod.add_rest_days_full(snap, fx)
        path = database.write_snapshot(matches)
        print(f"  snapshot aggiornato con congestione vera: {path}")
        print("\nCopertura calendario extra (coppe/Europa) per stagione:")
        print(fixtures_mod.coverage_report(fx).to_string(index=False))
    elif args.open_odds:
        # Aggancia le quote PRE-chiusura (linea "di apertura") allo snapshot
        # esistente, dai CSV grezzi. La base congelata NON viene toccata: si
        # aggiungono solo le colonne *_open (impronta dati invariata).
        print(f"Aggancio le quote di apertura allo snapshot: {database.SNAPSHOT_PATH}")
        matches = loader.add_open_odds(database.read_snapshot())
        path = database.write_snapshot(matches)
        print(f"  snapshot aggiornato con quote di apertura: {path}")
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
