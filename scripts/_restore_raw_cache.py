"""Ricostruisce la cache data/raw/ dai CSV grezzi congelati in files/.

Perche' esiste (Fase 14): il mirror GitHub storico di football-data e' SPARITO
(404 — verificato luglio 2026), quindi `--refresh`/`--open-odds` non possono
piu' scaricare i grezzi dal cloud. I CSV ORIGINALI football-data (9 stagioni,
tutte le colonne quote incluse apertura e chiusura) sono versionati in `files/`
coi nomi di download del browser ("I1.csv", "I1 (1).csv", ...): questo script
li identifica dalla COLONNA DELLE DATE (non dal nome, che non e' affidabile) e
li copia in data/raw/ coi nomi che il loader si aspetta (serie_a_<codice>.csv).

Uso:  python scripts/_restore_raw_cache.py
Poi:  python scripts/build_database.py --open-odds   (aggancio quote apertura)
"""
from __future__ import annotations

import glob
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import sources
from src.data.loader import RAW_DIR

FILES_DIR = Path(__file__).resolve().parents[1] / "files"


def season_of(csv_path: Path) -> str:
    """Codice stagione (es. "1718") dedotto dalle date del CSV grezzo."""
    df = pd.read_csv(csv_path, encoding="latin-1", usecols=["Date"])
    dates = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")
    lo = dates.min()
    start = lo.year if lo.month >= 7 else lo.year - 1
    return f"{str(start)[2:]}{str(start + 1)[2:]}"


def main() -> None:
    paths = sorted(FILES_DIR.glob("I1*.csv"))
    if not paths:
        raise SystemExit(f"Nessun CSV grezzo in {FILES_DIR} (attesi I1*.csv).")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    seen: dict[str, Path] = {}
    for p in paths:
        code = season_of(p)
        if code in seen:
            raise SystemExit(f"Stagione {code} duplicata: {seen[code].name} e {p.name}")
        seen[code] = p
        dest = RAW_DIR / f"serie_a_{code}.csv"
        shutil.copyfile(p, dest)
        print(f"  {p.name:<12} -> {dest.relative_to(RAW_DIR.parents[1])}")

    missing = set(sources.SEASONS) - set(seen)
    if missing:
        raise SystemExit(f"Stagioni mancanti in files/: {sorted(missing)}")
    print(f"Cache ricostruita: {len(seen)} stagioni ({min(seen)}..{max(seen)}).")


if __name__ == "__main__":
    main()
