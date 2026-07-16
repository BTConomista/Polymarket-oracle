"""Costruisce lo snapshot congelato di Premier League / La Liga dai BUNDLE (Fase 54).

Il provider football-data non e' raggiungibile dall'ambiente (403 dal proxy) e il
mirror storico e' sparito. I dati grezzi sono stati caricati a mano come bundle
JSON in files/ (un dict {nome_file: contenuto}):

    files/football_data_{league}_bundle.json   CSV football-data per stagione
    files/understat_{league}_bundle.json        JSON Understat per stagione

Questo script li fonde nello STESSO schema interno della Serie A (loader._normalize
+ understat.parse_season_xg) e scrive lo snapshot congelato e versionato
data/{league}_matches.csv, che load_league legge offline. Nessuna rete.

Controlli d'integrita' (falliscono rumorosamente, mai in silenzio, come per la
Serie A): join per (season, home_team, away_team) con nomi canonici; i gol del
grezzo devono coincidere con quelli dell'xG dove agganciato; copertura per
stagione stampata; righe Understat orfane elencate (spia di alias mancante).

Uso:  python scripts/build_league_snapshot.py [premier_league] [la_liga]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, loader, sources         # noqa: E402
from src.data import understat                          # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / "files"
XG_COLS = understat.XG_COLUMNS


def _fd_season(name: str) -> str:
    """'premier_league_1718.csv' -> '1718'."""
    return name.rsplit("_", 1)[-1].replace(".csv", "")


def _build(league_key: str) -> pd.DataFrame:
    league = sources.LEAGUES[league_key]
    fd_bundle = json.load(open(FILES / f"football_data_{league_key}_bundle.json"))
    ud_bundle = json.load(open(FILES / f"understat_{league_key}_bundle.json"))
    # mappa anno-understat -> contenuto, per agganciare per stagione
    ud_by_year = {int(k.rsplit("_", 1)[-1].replace(".json", "")):
                  (v if isinstance(v, dict) else json.loads(v))
                  for k, v in ud_bundle.items()}

    frames = []
    for name in sorted(fd_bundle):
        season = _fd_season(name)
        raw = pd.read_csv(io.StringIO(fd_bundle[name]))
        # 1) risultati + quote (riusa ESATTAMENTE la normalizzazione Serie A)
        norm = loader._normalize(raw, season, league)
        # 2) xG dal bundle Understat dell'anno corrispondente (se presente)
        year = sources.understat_year(season)
        if year in ud_by_year:
            xg = understat.parse_season_xg(ud_by_year[year], season)
            key = ["season", "home_team", "away_team"]
            dup = xg.duplicated(subset=key)
            if dup.any():
                raise ValueError(f"{league_key} {season}: xG con chiavi duplicate")
            n0 = len(norm)
            norm = norm.merge(xg.rename(columns={"date": "understat_date"}),
                              on=key, how="left", validate="one_to_one")
            assert len(norm) == n0, "join xG ha perso/duplicato partite"
            # orfane lato Understat = alias mancante (spia): elencale
            orph = xg.merge(norm[key], on=key, how="left", indicator=True)
            orph = orph[orph["_merge"] == "left_only"]
            for _, r in orph.iterrows():
                print(f"    [orfana UD] {season} {r.home_team}-{r.away_team}")
            cov = norm["home_xg"].notna().mean()
            print(f"  {league_key} {season}: {len(norm)} gare, xG {cov:5.1%}"
                  f"{' ('+str(len(orph))+' orfane)' if len(orph) else ''}")
            norm = norm.drop(columns=["understat_date"], errors="ignore")
        else:
            for c in XG_COLS:
                norm[c] = float("nan")
            print(f"  {league_key} {season}: {len(norm)} gare, xG assente (no bundle)")
        frames.append(norm)

    df = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
    # colonne di arricchimento Serie-A-only assenti qui: le lasciamo fuori dallo
    # snapshot (load_league non le richiede per Premier/Liga).
    return df


def main() -> None:
    keys = sys.argv[1:] or ["premier_league", "la_liga"]
    for key in keys:
        print(f"\n=== {sources.LEAGUES[key].name} ===")
        df = _build(key)
        out = database.snapshot_path(key)
        database.write_snapshot(df, out)
        xg_cov = df["home_xg"].notna().mean() if "home_xg" in df else 0.0
        odds_cov = df["odds_home"].notna().mean()
        print(f"  -> {out.name}: {len(df)} partite, {df.season.nunique()} stagioni "
              f"({sorted(df.season.unique())[0]}-{sorted(df.season.unique())[-1]}); "
              f"copertura xG {xg_cov:.1%}, quote {odds_cov:.1%}")


if __name__ == "__main__":
    main()
