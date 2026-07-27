"""Riempie le celle `squad_value` vuote con i valori Transfermarkt (regola R2).

Sorgente: `data/squad_value_2526_transfermarkt.csv` (prodotto e
VALIDATO da `recupero_squad_value_tm.py`: il rapporto con la fonte primaria e'
misurato sui club dove esistono entrambi i valori, e riportato riga per riga).

Garanzie (se una salta, lo script si ferma senza scrivere):
  1. riempie SOLO celle vuote: rifiuta di sovrascrivere un valore esistente
     (la fonte primaria resta primaria — R2);
  2. ogni (stagione, squadra) del file deve esistere nello snapshot;
  3. e' idempotente: se e' gia' tutto pieno, non fa nulla;
  4. il valore finisce identico su TUTTE le righe in cui quella squadra compare
     in quella stagione (in casa e fuori), come per gli altri valori rosa.

Uso:
    python scripts/applica_squad_value_tm.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SORGENTE = DATA / "squad_value_2526_transfermarkt.csv"
SNAPSHOTS = {"bundesliga": DATA / "bundesliga_matches.csv",
             "ligue_1": DATA / "ligue_1_matches.csv"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = pd.read_csv(SORGENTE, dtype={"season": str})
    print(f"Sorgente: {len(src)} celle (stagione, squadra) da Transfermarkt")

    for league, path in SNAPSHOTS.items():
        rows = src[src.league == league]
        if rows.empty:
            continue
        df = pd.read_csv(path, dtype={"season": str}, parse_dates=["date"])
        print(f"\n=== {league} ({len(rows)} celle) ===")
        n_before = int(df[["home_squad_value", "away_squad_value"]].isna().sum().sum())
        touched = 0
        for r in rows.itertuples():
            for side in ("home", "away"):
                col = f"{side}_squad_value"
                mask = ((df.season == r.season) & (df[f"{side}_team"] == r.team))
                if not mask.any():
                    raise SystemExit(
                        f"ERRORE: {r.team} non compare in {league} {r.season} "
                        f"come {side}. Mi fermo.")
                gia_pieno = mask & df[col].notna()
                if gia_pieno.any():
                    valori = df.loc[gia_pieno, col].unique()
                    raise SystemExit(
                        f"ERRORE: {r.team} {r.season} ha gia' un {col} "
                        f"({valori[:3]}): la fonte primaria non si sovrascrive. "
                        f"Mi fermo.")
                if not args.dry_run:
                    df.loc[mask, col] = float(r.squad_value_tm)
                touched += int(mask.sum())
            print(f"  {r.team:14s} {r.squad_value_tm/1e6:7.1f} M€  "
                  f"({int(((df.season == r.season) & ((df.home_team == r.team) | (df.away_team == r.team))).sum())} partite)")

        n_after = int(df[["home_squad_value", "away_squad_value"]].isna().sum().sum())
        print(f"  celle-partita riempite: {touched}; "
              f"NaN residui: {n_before} -> {n_after}")
        if args.dry_run:
            print("  --dry-run: non scrivo")
            continue
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(path, index=False)
        print(f"  -> {path.relative_to(ROOT)} aggiornato")
    return 0


if __name__ == "__main__":
    sys.exit(main())
