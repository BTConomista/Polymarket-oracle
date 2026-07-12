"""Ricostruisce la cache data/raw/ dai CSV grezzi congelati in data/football_data_raw/.

Perche' esiste (Fase 14): il mirror GitHub storico di football-data e' SPARITO
(404 — verificato luglio 2026), quindi `--refresh`/`--open-odds` non possono
piu' scaricare i grezzi dal cloud. I CSV ORIGINALI football-data (9 stagioni,
tutte le colonne quote incluse apertura e chiusura) sono la fonte grezza
congelata VERSIONATA in data/football_data_raw/ (serie_a_<codice>.csv). Questo
script li copia nella cache di lavoro data/raw/ (rigenerabile, in .gitignore),
che e' quella che il loader legge davvero.

Sicurezza: la stagione dedotta dalle DATE del file deve coincidere col nome
(serie_a_<codice>.csv) — un file rinominato male o corrotto fa fallire lo script
invece di sporcare la cache in silenzio.

Uso:  python scripts/_restore_raw_cache.py
Poi:  python scripts/build_database.py --open-odds   (aggancio quote apertura)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import sources
from src.data.loader import RAW_DIR

FROZEN_DIR = Path(__file__).resolve().parents[1] / "data" / "football_data_raw"


def season_of(csv_path: Path) -> str:
    """Codice stagione (es. "1718") dedotto dalle date del CSV grezzo."""
    df = pd.read_csv(csv_path, encoding="latin-1", usecols=["Date"])
    dates = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")
    lo = dates.min()
    start = lo.year if lo.month >= 7 else lo.year - 1
    return f"{str(start)[2:]}{str(start + 1)[2:]}"


def main() -> None:
    paths = sorted(FROZEN_DIR.glob("serie_a_*.csv"))
    if not paths:
        raise SystemExit(f"Nessun CSV grezzo in {FROZEN_DIR} (attesi serie_a_*.csv).")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    for p in paths:
        code_name = p.stem.replace("serie_a_", "")
        code_dates = season_of(p)
        if code_name != code_dates:
            raise SystemExit(
                f"Incoerenza in {p.name}: nome dice stagione {code_name}, "
                f"le date dicono {code_dates}. File rinominato male o corrotto.")
        seen.add(code_name)
        dest = RAW_DIR / f"serie_a_{code_name}.csv"
        shutil.copyfile(p, dest)
        print(f"  {p.name} -> {dest.relative_to(RAW_DIR.parents[1])}")

    missing = set(sources.SEASONS) - seen
    if missing:
        raise SystemExit(f"Stagioni mancanti in {FROZEN_DIR.name}: {sorted(missing)}")
    print(f"Cache ricostruita: {len(seen)} stagioni ({min(seen)}..{max(seen)}).")


if __name__ == "__main__":
    main()
