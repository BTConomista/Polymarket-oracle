"""Applica le CORREZIONI DICHIARATE agli snapshot (regole R1 e R3 di REGOLE.md).

Nessun dato cambia a mano: il *cosa* e il *perche'* stanno in
`cantiere/data/correzioni_dichiarate.csv`, il *come* e' questo script.

Garanzie (se una salta, lo script si ferma senza scrivere nulla):
  1. ogni correzione deve trovare ESATTAMENTE una riga nello snapshot;
  2. il valore attuale della cella deve coincidere col `valore_prima` del
     registro — cosi' una correzione gia' applicata non viene riapplicata a
     un valore diverso, e un cambio a monte dei dati viene scoperto subito;
  3. sono applicate solo le righe con `stato == applicata`;
  4. e' idempotente: se la cella e' gia' al `valore_dopo`, la riga viene
     saltata e segnalata.

Uso:
    python cantiere/scripts/applica_correzioni.py            # applica
    python cantiere/scripts/applica_correzioni.py --dry-run  # mostra e basta
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "cantiere" / "data"
REGISTRO = DATA / "correzioni_dichiarate.csv"

# Solo gli snapshot del cantiere: le leghe gia' in repo non si toccano (R4).
SNAPSHOTS = {"bundesliga": DATA / "bundesliga_matches.csv",
             "ligue_1": DATA / "ligue_1_matches.csv"}
KEY = ["season", "home_team", "away_team"]


def _same(a, b) -> bool:
    """Confronto tollerante: NaN == NaN, numeri a meno di 1e-9, resto come stringa."""
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = pd.read_csv(REGISTRO, dtype={"season": str})
    attive = reg[reg.stato == "applicata"]
    print(f"Registro: {len(reg)} righe ({len(attive)} da applicare, "
          f"{len(reg) - len(attive)} proposte non applicate)")

    for league, path in SNAPSHOTS.items():
        rows = attive[attive.league == league]
        if rows.empty:
            continue
        df = pd.read_csv(path, dtype={"season": str}, parse_dates=["date"])
        print(f"\n=== {league} ({len(rows)} correzioni) ===")
        changes: list[tuple[int, str, object]] = []
        for r in rows.itertuples():
            mask = ((df.season == r.season) & (df.home_team == r.home_team)
                    & (df.away_team == r.away_team))
            n = int(mask.sum())
            if n != 1:
                raise SystemExit(
                    f"ERRORE: {r.home_team}-{r.away_team} {r.season} trova "
                    f"{n} righe (attesa 1). Mi fermo senza scrivere.")
            i = int(df.index[mask][0])
            attuale = df.at[i, r.colonna]
            if _same(attuale, r.valore_dopo):
                print(f"  [gia' applicata] {r.colonna}: {attuale}")
                continue
            if not _same(attuale, r.valore_prima):
                raise SystemExit(
                    f"ERRORE: {r.home_team}-{r.away_team} colonna {r.colonna}: "
                    f"valore attuale {attuale!r} != valore_prima atteso "
                    f"{r.valore_prima!r}. I dati sono cambiati a monte o la "
                    f"correzione e' gia' stata alterata. Mi fermo.")
            changes.append((i, r.colonna, r.valore_dopo))
            print(f"  {r.home_team}-{r.away_team} [{r.colonna}] "
                  f"{attuale!r} -> {r.valore_dopo!r}")

        if not changes:
            print("  nulla da fare (tutte gia' applicate)")
            continue
        if args.dry_run:
            print("  --dry-run: non scrivo")
            continue
        for i, col, val in changes:
            # rispetta il dtype della colonna (i gol sono interi)
            if pd.api.types.is_integer_dtype(df[col].dtype):
                df.at[i, col] = int(val)
            elif pd.api.types.is_float_dtype(df[col].dtype):
                df.at[i, col] = float(val)
            else:
                df.at[i, col] = val
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(path, index=False)
        print(f"  -> {path.relative_to(ROOT)} aggiornato ({len(changes)} celle)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
