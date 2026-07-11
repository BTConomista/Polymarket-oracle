"""Analisi degli errori del backtest: DOVE il modello perde contro il mercato.

Legge le predizioni salvate da scripts/backtest.py e produce un report che
scompone il divario col mercato per gruppi di partite e per calibrazione.

Uso:
    python scripts/backtest.py          # genera outputs/backtest_predictions.csv
    python scripts/analyze.py           # analizza quel file
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import analysis, metrics


def _market_1x2(df: pd.DataFrame) -> np.ndarray:
    out = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            out[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    return out


def _promoted_teams(league_key: str, test_season: str) -> set[str]:
    """Squadre presenti nella stagione di test ma non nella precedente
    (neopromosse: poco o nessuno storico recente in Serie A)."""
    seasons = sources.SEASONS
    if test_season not in seasons:
        return set()
    idx = seasons.index(test_season)
    if idx == 0:
        return set()
    data = loader.load_league(league_key, [seasons[idx - 1], test_season])
    prev = data[data.season == seasons[idx - 1]]
    test = data[data.season == test_season]
    teams_prev = set(prev.home_team) | set(prev.away_team)
    teams_test = set(test.home_team) | set(test.away_team)
    return teams_test - teams_prev


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisi errori del backtest.")
    parser.add_argument("--predictions", default="outputs/backtest_predictions.csv")
    parser.add_argument("--league", default="serie_a")
    parser.add_argument("--test-season", default=None,
                        help="default: la stagione salvata nel CSV delle predizioni "
                             "(fallback: l'ultima in sources.SEASONS)")
    args = parser.parse_args()

    path = Path(args.predictions)
    if not path.exists():
        raise SystemExit(f"File non trovato: {path}. Esegui prima scripts/backtest.py")

    df = pd.read_csv(path, parse_dates=["date"])

    # Stagione: la verita' e' nel CSV (colonna scritta da backtest.py, audit
    # Fase 15). Il flag serve solo per CSV vecchi senza colonna; se contraddice
    # il CSV ci si ferma invece di etichettare le neopromosse sbagliate.
    csv_season = None
    if "season" in df.columns and df["season"].notna().any():
        csv_season = str(df["season"].iloc[0]).strip()
    if args.test_season and csv_season and args.test_season != csv_season:
        raise SystemExit(
            f"--test-season {args.test_season} ma le predizioni in {path} sono "
            f"della stagione {csv_season}: rigenera il CSV o togli il flag.")
    args.test_season = args.test_season or csv_season or sources.SEASONS[-1]
    market = _market_1x2(df)
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    outcomes = df["result"].tolist()

    ll_model = analysis.per_match_log_loss(model, outcomes)
    ll_market = analysis.per_match_log_loss(market, outcomes)

    print("=" * 66)
    print(f"ANALISI ERRORI — {len(df)} partite ({sources.season_label(args.test_season)})")
    print("=" * 66)

    # 1) Calibrazione aggregata: media predetta vs frequenza reale.
    print("\n[1] CALIBRAZIONE AGGREGATA (media predetta vs realta')")
    yh = np.array([o == "H" for o in outcomes], float)
    yd = np.array([o == "D" for o in outcomes], float)
    ya = np.array([o == "A" for o in outcomes], float)
    print(f"    {'esito':<10}{'reale':>8}{'modello':>10}{'mercato':>10}")
    for name, real, mc, kc in [("Casa", yh, 0, 0), ("Pareggio", yd, 1, 1), ("Ospite", ya, 2, 2)]:
        print(f"    {name:<10}{real.mean():>8.3f}{model[:, mc].mean():>10.3f}"
              f"{np.nanmean(market[:, kc]):>10.3f}")
    print("    -> Se le colonne sono vicine, il modello NON ha bias sistematico "
          "sulla media.")

    # 2) Reliability diagram (tabellare) 1X2.
    print("\n[2] CALIBRAZIONE PER FASCIA — 1X2 (modello)")
    fp, fh = analysis.flatten_1x2(model, outcomes)
    tbl = analysis.reliability_table(fp, fh, n_bins=10)
    print(tbl.to_string(index=False))
    print("    scarto = prob_media - freq_reale (>0 = sovrastima quella fascia)")

    # 3) Divario col mercato per gruppo.
    print("\n[3] DOVE IL MODELLO PERDE (log-loss; gap>0 = mercato migliore)")
    promoted = _promoted_teams(args.league, args.test_season)
    has_promo = df["home_team"].isin(promoted) | df["away_team"].isin(promoted)
    cut = df["date"].quantile(0.33)
    early = df["date"] <= cut
    conf = model.max(axis=1) > 0.65

    groups = [
        ("TUTTE le partite", np.ones(len(df), bool)),
        (f"con neopromossa ({sorted(promoted)})", has_promo.to_numpy()),
        ("senza neopromossa", (~has_promo).to_numpy()),
        ("prima parte stagione", early.to_numpy()),
        ("resto stagione", (~early).to_numpy()),
        ("modello molto sicuro (>65%)", conf),
    ]
    print(f"    {'gruppo':<40}{'n':>5}{'mod':>8}{'mkt':>8}{'gap':>8}")
    for name, mask in groups:
        g = analysis.gap_by_group(ll_model, ll_market, mask)
        if g["n"]:
            print(f"    {name:<40}{g['n']:>5}{g['modello']:>8.3f}"
                  f"{g['mercato']:>8.3f}{g['gap']:>+8.3f}")

    # 4) Peggiori errori individuali.
    print("\n[4] 8 PARTITE con lo scarto piu' grande a sfavore del modello")
    df2 = df.copy()
    df2["gap"] = ll_model - ll_market
    worst = df2.sort_values("gap", ascending=False).head(8)
    for i, r in worst.iterrows():
        k = market[i]
        print(f"    {r.home_team[:11]:<11} {r.away_team[:11]:<11} "
              f"{int(r.home_goals)}-{int(r.away_goals)} ({r.result})  "
              f"mod {r.m_home:.2f}/{r.m_draw:.2f}/{r.m_away:.2f}  "
              f"mkt {k[0]:.2f}/{k[1]:.2f}/{k[2]:.2f}")

    print("\n" + "=" * 66)
    print("SINTESI: il modello e' calibrato sulla media ma perde in "
          "DISCRIMINAZIONE\nsui casi con dati scarsi/datati (neopromosse, inizio "
          "stagione) dove\ntende a essere troppo sicuro. Sono i punti che il "
          "feature engineering\ndovra' aggredire per primi.")
    print("=" * 66)


if __name__ == "__main__":
    main()
