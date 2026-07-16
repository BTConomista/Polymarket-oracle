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
      python scripts/build_league_snapshot.py --fixtures [premier_league] [la_liga]
        assembla il calendario di club completo (Fase 59, generalizza la Fase 4e:
        coppe europee gia' scaricate per la Serie A + coppe nazionali via
        openfootball/{england,espana}) e aggiunge rest_days_full/midweek_europe
        allo snapshot. RICHIEDE rete (raw.githubusercontent.com/openfootball/*,
        cache offline in data/raw/ dopo il primo download).
      python scripts/build_league_snapshot.py --enrich [premier_league] [la_liga]
        aggiunge home/away_squad_value e le colonne di assenze stimate (Fase 59,
        generalizza la Fase 4a: il mirror Understat per-stagione e' sparito, le
        rose vengono quindi dal bundle GIA' caricato in files/, non da rete;
        Transfermarkt invece e' raggiunto via rete -- mirror diverso, ancora
        vivo -- cache offline in data/raw/ dopo il primo download, ~100MB).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, fixtures as fixtures_mod, loader, sources  # noqa: E402
from src.data import transfermarkt, understat            # noqa: E402

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


def _squads_from_bundle(league_key: str) -> pd.DataFrame:
    """Rose (season, team, player_id, player_name, position, minutes) da TUTTE
    le stagioni del bundle Understat gia' caricato in files/ (Fase 59: stessa
    fonte/stesso bundle dell'xG, Fase 54 -- nessuna rete)."""
    ud_bundle = json.load(open(FILES / f"understat_{league_key}_bundle.json"))
    frames = []
    for name, content in ud_bundle.items():
        year = int(name.rsplit("_", 1)[-1].replace(".json", ""))
        data = content if isinstance(content, dict) else json.loads(content)
        # "1718" -> 2017; sources.understat_year fa l'inverso, quindi si cerca
        # la stagione le cui SEASONS map a questo year (stesso anno di inizio).
        season = next(c for c in sources.SEASONS
                     if sources.understat_year(c) == year)
        frames.append(understat.parse_season_players(data, season))
    return pd.concat(frames, ignore_index=True)


def _add_enrichment(key: str) -> None:
    """Aggiunge home/away_squad_value + assenze stimate allo snapshot ESISTENTE
    (Fase 59, generalizza la Fase 4a). Le rose vengono dal bundle locale (niente
    rete); le valutazioni/infortuni Transfermarkt vengono scaricati (rete,
    cache offline dopo il primo download)."""
    snap = database.read_snapshot(database.snapshot_path(key))
    squads = _squads_from_bundle(key)
    print(f"Rose dal bundle: {len(squads)} righe (giocatore, squadra) su "
          f"{squads['season'].nunique()} stagioni")
    matches = transfermarkt.add_squad_values(snap, key, squads=squads)
    matches = transfermarkt.add_absences(matches, key, squads=squads)
    database.write_snapshot(matches, database.snapshot_path(key))
    both_sq = matches["home_squad_value"].notna() & matches["away_squad_value"].notna()
    print(f"  -> {database.snapshot_path(key).name} aggiornato: "
          f"{both_sq.sum()}/{len(matches)} partite con valore rosa su entrambi i lati")


def _refresh_odds(key: str) -> None:
    """Ricalcola TUTTE le quote (chiusura + apertura) dello snapshot dai bundle
    football-data (Fase 61: chiusura Pinnacle PSC* per le prime 2 stagioni),
    senza toccare xG/rose/congestione."""
    snap = database.read_snapshot(database.snapshot_path(key))
    fd_bundle = json.load(open(FILES / f"football_data_{key}_bundle.json"))
    raw_by_season = {_fd_season(name): pd.read_csv(io.StringIO(fd_bundle[name]))
                     for name in sorted(fd_bundle)}
    matches = loader.refresh_odds(snap, raw_by_season)
    database.write_snapshot(matches, database.snapshot_path(key))
    print(f"  -> {database.snapshot_path(key).name} aggiornato (quote ricalcolate)")


def _add_fixtures(key: str) -> None:
    """Assembla il calendario di club completo e aggiunge rest_days_full/
    midweek_europe allo snapshot ESISTENTE (Fase 59). Come per la Serie A
    (build_database.py --fixtures): la base football-data/Understat resta
    congelata, si aggiungono solo le 4 colonne di congestione."""
    snap = database.read_snapshot(database.snapshot_path(key))
    print(f"Assemblo il calendario di club completo ({sources.LEAGUES[key].name})...")
    fx = fixtures_mod.build_club_fixtures(snap, league_key=key, force=False)
    fx_path = fixtures_mod.write_club_fixtures(fx, fixtures_mod.club_fixtures_path(key))
    print(f"  calendario di club: {fx_path}  ({len(fx)} righe squadra-partita)")
    matches = fixtures_mod.add_rest_days_full(
        snap, fx, own_competition=sources.own_league_competition(key)
    )
    database.write_snapshot(matches, database.snapshot_path(key))
    print(f"  -> {database.snapshot_path(key).name} aggiornato con congestione vera")
    print("Copertura calendario extra (coppe/Europa) per stagione:")
    print(fixtures_mod.coverage_report(
        fx, own_competition=sources.own_league_competition(key)
    ).to_string(index=False))


def main() -> None:
    args = sys.argv[1:]
    do_fixtures = "--fixtures" in args
    do_enrich = "--enrich" in args
    do_refresh_odds = "--refresh-odds" in args
    keys = [a for a in args if a not in ("--fixtures", "--enrich", "--refresh-odds")] \
        or ["premier_league", "la_liga"]

    if do_refresh_odds:
        for key in keys:
            print(f"\n=== {sources.LEAGUES[key].name} (quote ricalcolate) ===")
            _refresh_odds(key)
        return

    if do_enrich:
        for key in keys:
            print(f"\n=== {sources.LEAGUES[key].name} (valore rosa + assenze) ===")
            _add_enrichment(key)
        return

    if do_fixtures:
        for key in keys:
            print(f"\n=== {sources.LEAGUES[key].name} (congestione vera) ===")
            _add_fixtures(key)
        return

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
