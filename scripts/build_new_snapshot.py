"""Costruisce lo snapshot congelato di Bundesliga e Ligue 1 (schema a 38 colonne).

Segue il PLAYBOOK (docs/PLAYBOOK_NUOVA_LEGA.md, passo 0) e riusa il codice di
PRODUZIONE senza modificarlo: `loader._normalize` (risultati + le 10 colonne
quota con la politica Fase 73), `understat.parse_season_xg` (xG/npxG/PPDA/deep),
`player_scores.add_squad_values` (valore rosa), `transfermarkt.add_absences`
(assenze stimate), `fixtures.*` (congestione vera). Le leghe nuove sono
registrate a runtime da `scripts/nuove_leghe.registra()`.

Differenze rispetto a Premier/Liga (Fase 54): niente bundle caricati a mano —
le fonti si scaricano direttamente (`scripts/fetch_sources.py`), perche'
in questa sessione football-data.co.uk e understat.com sono raggiungibili.

Uscite (nel cantiere, non negli alberi ufficiali):
    data/{lega}_matches.csv          snapshot 38 colonne
    data/club_fixtures_{lega}.csv    calendario di club completo

Uso:
    python scripts/build_new_snapshot.py                  # tutto
    python scripts/build_new_snapshot.py --step core      # solo base+xG
    python scripts/build_new_snapshot.py --leagues bundesliga
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402
from src.data import fixtures as fx_mod  # noqa: E402
from src.data import loader, sources, understat  # noqa: E402

FONTI = ROOT / "data" / "fonti"
OUTDIR = ROOT / "data"
CACHE = FONTI / "openfootball"

# Ordine colonne UFFICIALE del progetto (== data/serie_a_matches.csv).
SNAP_COLUMNS = [
    "date", "season", "league", "home_team", "away_team", "home_goals",
    "away_goals", "result", "home_sot", "away_sot", "odds_home", "odds_draw",
    "odds_away", "odds_over25", "odds_under25", "home_xg", "away_xg",
    "home_npxg", "home_ppda", "home_deep", "away_npxg", "away_ppda",
    "away_deep", "home_squad_value", "away_squad_value",
    "home_absent_count_est", "home_absent_value_est", "away_absent_count_est",
    "away_absent_value_est", "odds_home_open", "odds_draw_open",
    "odds_away_open", "odds_over25_open", "odds_under25_open",
    "home_rest_days_full", "away_rest_days_full", "home_midweek_europe",
    "away_midweek_europe",
]


def _understat_json(league: str, season: str) -> dict:
    year = 2000 + int(season[:2])
    return json.loads((FONTI / "understat" / f"{league}_{year}.json").read_text())


# --------------------------------------------------------------------------- #
# 1. Base: risultati + quote + xG
# --------------------------------------------------------------------------- #
def build_core(league_key: str) -> pd.DataFrame:
    league = nuove_leghe.NEW_LEAGUES[league_key]
    frames = []
    for season in sources.SEASONS:
        raw = pd.read_csv(FONTI / "football_data" / f"{league_key}_{season}.csv",
                          encoding="latin-1")
        norm = loader._normalize(raw, season, league)

        data = _understat_json(league_key, season)
        xg = understat.parse_season_xg(data, season)
        key = ["season", "home_team", "away_team"]
        if xg.duplicated(subset=key).any():
            raise ValueError(f"{league_key} {season}: xG con chiavi duplicate")
        n0 = len(norm)
        norm = norm.merge(xg.rename(columns={"date": "ud_date"}), on=key,
                          how="left", validate="one_to_one")
        assert len(norm) == n0, "il join xG ha perso/duplicato partite"

        # Controlli rumorosi (mai in silenzio): orfane e squadre disallineate
        orph = xg.merge(norm[key], on=key, how="left", indicator=True)
        orph = orph[orph["_merge"] == "left_only"]
        fd_teams = set(norm.home_team) | set(norm.away_team)
        ud_teams = set(xg.home_team) | set(xg.away_team)
        if fd_teams != ud_teams:
            raise ValueError(
                f"{league_key} {season}: insiemi squadre DIVERSI tra "
                f"football-data e Understat -> alias mancante. "
                f"solo FD: {sorted(fd_teams - ud_teams)}; "
                f"solo UD: {sorted(ud_teams - fd_teams)}")
        cov = norm["home_xg"].notna().mean()
        print(f"  {league_key} {season}: {len(norm):3d} gare, {len(fd_teams)} squadre, "
              f"xG {cov:6.1%}, quote chiusura 1X2 {norm.odds_home.notna().mean():6.1%}"
              + (f"  [{len(orph)} orfane UD]" if len(orph) else ""))
        norm = norm.drop(columns=["ud_date"], errors="ignore")
        frames.append(norm)

    df = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
    return df


# --------------------------------------------------------------------------- #
# 2. Calendario di club completo (congestione vera)
# --------------------------------------------------------------------------- #
def _of_text(league_key: str, season: str, kind: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{league_key}_{kind}_{season}.txt"
    if not dest.exists():
        url = nuove_leghe.openfootball_url(league_key, season, kind)
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                dest.write_bytes(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            dest.write_text("")   # lacuna di copertura: dichiarata, non inventata
            print(f"    [copertura assente] {league_key} {kind} {season}")
    return dest.read_text(encoding="utf-8", errors="replace")


def build_fixtures(matches: pd.DataFrame, league_key: str) -> pd.DataFrame:
    """Come `fixtures.build_club_fixtures`, ma con i percorsi openfootball delle
    leghe nuove (la Francia usa uno schema di file diverso, vedi nuove_leghe)."""
    teams = set(matches.home_team) | set(matches.away_team)
    seasons = sorted(matches.season.astype(str).unique())
    cc = nuove_leghe.UEFA_CODES[league_key]
    own = nuove_leghe.NEW_LEAGUES[league_key].name

    rows = fx_mod._league_rows(matches, own)

    # preludio: massima serie 2016-17 + seconda serie 1617..penultima
    text = _of_text(league_key, "1617", "top")
    if text.strip():
        raw = fx_mod.parse_cup(text, "1617", f"{own} 2016-17")
        rows += fx_mod._cup_team_rows(raw, teams)
    for code in ["1617"] + seasons[:-1]:
        text = _of_text(league_key, code, "second")
        if text.strip():
            raw = fx_mod.parse_cup(text, code, nuove_leghe.SECOND_TIER_NAMES[league_key])
            rows += fx_mod._cup_team_rows(raw, teams)

    # coppe europee (file condivisi tra leghe: filtro sul codice paese)
    for code in seasons:
        for comp, comp_name in sources.EUROPE_COMPETITIONS.items():
            path = fx_mod.download_openfootball(code, comp, "europe", force=False)
            if path is None:
                continue
            raw = fx_mod.parse_europe(path.read_text(encoding="utf-8", errors="replace"),
                                      code, comp_name, cc)
            if not raw.empty:
                rows += fx_mod._uefa_team_rows(raw, teams, cc)
        # coppa nazionale
        text = _of_text(league_key, code, "cup")
        if text.strip():
            raw = fx_mod.parse_cup(text, code, nuove_leghe.DOMESTIC_CUP_NAMES[league_key])
            if not raw.empty:
                rows += fx_mod._cup_team_rows(raw, teams)

    fx = pd.DataFrame(rows, columns=fx_mod.FIXTURE_COLUMNS)
    fx["date"] = pd.to_datetime(fx["date"]).dt.normalize()
    fx = fx.drop_duplicates(subset=["season", "team", "date", "competition", "opponent"])
    return fx.sort_values(["date", "team", "competition"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 3. Arricchimenti (valore rosa, assenze)
# --------------------------------------------------------------------------- #
def add_squad_values(df: pd.DataFrame, league_key: str) -> pd.DataFrame:
    from src.data import player_scores
    # `add_squad_values` ripristina l'ordine colonne originale (`out[matches.columns]`):
    # su uno snapshot NUOVO, che quelle colonne non le ha ancora, le perderebbe.
    # Le si crea prima, vuote, nella posizione ufficiale.
    out = df.copy()
    for c in ("home_squad_value", "away_squad_value"):
        if c not in out.columns:
            out[c] = float("nan")
    return player_scores.add_squad_values(out, league_key)


def add_absences(df: pd.DataFrame, league_key: str) -> pd.DataFrame:
    from src.data import transfermarkt
    squads = pd.concat(
        [understat.parse_season_players(_understat_json(league_key, s), s)
         for s in sources.SEASONS], ignore_index=True)
    print(f"  rose Understat: {len(squads)} righe (giocatore, squadra)")
    return transfermarkt.add_absences(df, league_key, squads=squads)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=list(nuove_leghe.NEW_LEAGUES))
    ap.add_argument("--step", default="all",
                    choices=["all", "core", "fixtures", "squad", "absences"])
    args = ap.parse_args()

    logging.basicConfig(level=logging.WARNING, format="  [%(levelname)s] %(message)s")
    nuove_leghe.registra()
    # cache openfootball/Transfermarkt dentro il cantiere (niente scritture
    # negli alberi ufficiali del progetto)
    fx_mod.RAW_DIR = CACHE
    from src.data import transfermarkt
    transfermarkt.RAW_DIR = FONTI / "transfermarkt"
    transfermarkt.RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)

    for key in args.leagues:
        print(f"\n=== {nuove_leghe.NEW_LEAGUES[key].name} ===")
        snap_path = OUTDIR / f"{key}_matches.csv"

        if args.step in ("all", "core") or not snap_path.exists():
            df = build_core(key)
        else:
            df = pd.read_csv(snap_path, dtype={"season": str}, parse_dates=["date"])

        if args.step in ("all", "squad"):
            print("  valore rosa (player-scores)...")
            df = add_squad_values(df, key)
            both = df.home_squad_value.notna() & df.away_squad_value.notna()
            print(f"    copertura valore rosa (entrambi i lati): {both.mean():.1%}")

        if args.step in ("all", "absences"):
            print("  assenze stimate (Transfermarkt + rose Understat)...")
            df = add_absences(df, key)

        if args.step in ("all", "fixtures"):
            print("  calendario di club completo (congestione)...")
            fx = build_fixtures(df, key)
            fx_out = OUTDIR / f"club_fixtures_{key}.csv"
            fx_mod.write_club_fixtures(fx, fx_out)
            print(f"    {len(fx)} righe (squadra, partita) -> {fx_out.name}")
            df = fx_mod.add_rest_days_full(
                df, fx, own_competition=nuove_leghe.NEW_LEAGUES[key].name)
            print(fx_mod.coverage_report(
                fx, own_competition=nuove_leghe.NEW_LEAGUES[key].name).to_string(index=False))

        missing = [c for c in SNAP_COLUMNS if c not in df.columns]
        if missing and args.step == "all":
            raise ValueError(f"colonne mancanti nello snapshot: {missing}")
        df = df[[c for c in SNAP_COLUMNS if c in df.columns]]
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(snap_path, index=False)
        print(f"  -> {snap_path.relative_to(ROOT)}: {len(df)} partite, "
              f"{df.season.nunique()} stagioni, {len(df.columns)} colonne")
    return 0


if __name__ == "__main__":
    sys.exit(main())
