"""Fase 70 (one-off, non rigenerabile automaticamente): inietta negli snapshot
i 13 valori rosa REALI 2025-26 recuperati manualmente da Transfermarkt (pagine
di competizione filtrate sulla stagione 2025/26, via Claude Cowork + estensione
Chrome, 21/07/2026 — non riverificati da questa sessione, il cui WebFetch era
fermo). Sostituisce le celle NaN negli snapshot e rimuove le righe corrispondenti
da data/estimates/squad_value_2017_26.csv (Fase 67 pattern: reale sostituisce
stima). Vedi docs/DIARIO.md Fase 70 per fonti e cross-check.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# (league, team) -> valore EUR, come mostrato sulla pagina competizione 25/26
REAL_VALUES = {
    ("serie_a", "Bologna"): 274_700_000,
    ("serie_a", "Como"): 405_200_000,
    ("serie_a", "Cremonese"): 69_030_000,
    ("serie_a", "Parma"): 189_000_000,
    ("serie_a", "Pisa"): 98_300_000,
    ("serie_a", "Udinese"): 200_000_000,
    ("premier_league", "Leeds"): 373_300_000,
    ("premier_league", "Sunderland"): 424_930_000,
    ("la_liga", "Celta"): 192_200_000,
    ("la_liga", "Elche"): 100_200_000,
    ("la_liga", "Espanol"): 127_850_000,
    ("la_liga", "Levante"): 109_900_000,
    ("la_liga", "Oviedo"): 56_400_000,
}
SEASON = "2526"

SNAPSHOT_PATHS = {
    "serie_a": ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga": ROOT / "data" / "la_liga_matches.csv",
}
ESTIMATES_PATH = ROOT / "data" / "estimates" / "squad_value_2017_26.csv"


def main() -> None:
    for lg, path in SNAPSHOT_PATHS.items():
        df = pd.read_csv(path, dtype={"season": str})
        n_before = df[["home_squad_value", "away_squad_value"]].isna().sum().sum()
        for (l2, team), value in REAL_VALUES.items():
            if l2 != lg:
                continue
            is_home = (df["season"] == SEASON) & (df["home_team"] == team)
            is_away = (df["season"] == SEASON) & (df["away_team"] == team)
            assert df.loc[is_home, "home_squad_value"].isna().all(), \
                f"{lg}/{team}: home_squad_value gia' valorizzato, non sovrascrivo"
            assert df.loc[is_away, "away_squad_value"].isna().all(), \
                f"{lg}/{team}: away_squad_value gia' valorizzato, non sovrascrivo"
            df.loc[is_home, "home_squad_value"] = value
            df.loc[is_away, "away_squad_value"] = value
        n_after = df[["home_squad_value", "away_squad_value"]].isna().sum().sum()
        df.to_csv(path, index=False)
        print(f"{lg}: NaN squad_value {n_before} -> {n_after}")

    est = pd.read_csv(ESTIMATES_PATH, dtype={"season": str})
    n_est_before = len(est)
    keep = ~est.apply(lambda r: (r["league"], r["team"]) in REAL_VALUES
                      and r["season"] == SEASON, axis=1)
    est = est[keep]
    est.to_csv(ESTIMATES_PATH, index=False)
    print(f"\nestimates: {n_est_before} -> {len(est)} righe "
          f"({n_est_before - len(est)} rimosse: reale sostituisce stima)")


if __name__ == "__main__":
    main()
