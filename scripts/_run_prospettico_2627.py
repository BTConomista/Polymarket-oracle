"""Anteprima prospettica 2026-27 (giornata 1) — SOLO previsioni DC del modello.

Test prospettico (out-of-sample vero): si congelano le previsioni PRIMA del
calcio d'inizio e si controllano DOPO — nessun senno di poi possibile. Questo
script produce la parte fattibile OGGI dalla sessione di sviluppo: la previsione
del Dixon-Coles (che non richiede quote esterne) per un insieme di partite
plausibili di apertura, tra squadre presenti nei nostri dati (fino a 2025-26).

⚠️  LIMITI DICHIARATI (vedi experiments/prospettico_2026_27.md):
  - i CALENDARI 2026-27 non sono verificabili in modo affidabile da qui
    (WebFetch bloccato, snippet di ricerca su stagioni future speculativi):
    le partite qui sono PLAUSIBILI, non ufficiali;
  - i dati si fermano a 2025-26 → forze "vecchie" di un'estate di mercato;
  - niente quote → niente market-implied (il Modello 2). Solo il DC-da-solo.
  Questa e' un'ANTEPRIMA illustrativa, NON il test prospettico scorato.

Uso:  python scripts/_run_prospettico_2627.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import LEAGUE_CONFIGS                # noqa: E402
from src.data import loader                          # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from src.models.dixon_coles import DixonColesModel   # noqa: E402
from scripts.backtest import promoted_teams          # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "prospettico_2026_27_dc.csv"
AS_OF = "2026-08-15"     # prima del primo turno (Premier 21/8, Liga 15/8, SA 23/8)

# Partite PLAUSIBILI di apertura, tra squadre presenti nei nostri dati.
# Premier: dagli annunci ufficiali (skysports/premierleague) filtrate sulle
# squadre note; Serie A / La Liga: NON reperite in modo affidabile da qui ->
# lasciate ai calendari veri (slot nel .md). Nomi = come nello snapshot.
FIXTURES = {
    "premier_league": [
        ("Newcastle", "Liverpool"),
        ("Man City", "Bournemouth"),
        ("Brighton", "Aston Villa"),
        ("Fulham", "Chelsea"),
        ("Brentford", "Tottenham"),
        ("Everton", "Crystal Palace"),
        ("Nott'm Forest", "Leeds"),
    ],
}


def fit_league(league: str, as_of: pd.Timestamp) -> DixonColesModel:
    cfg = LEAGUE_CONFIGS[league]
    allm = loader.load_league(league)
    prom = promoted_teams(allm, str(allm["season"].iloc[-1]))
    delta = cfg["promoted_prior"]
    m = DixonColesModel(
        half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
        shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
        promoted_prior=(delta, delta), draw_balance=True,
    ).fit(allm, as_of_date=as_of, promoted_teams=prom)
    return m, set(allm["home_team"]) | set(allm["away_team"])


def main() -> None:
    as_of = pd.Timestamp(AS_OF)
    rows = []
    print(f"Anteprima DC 2026-27 giornata 1 (as_of {AS_OF}, dati fino a 2025-26)")
    print("⚠️  partite PLAUSIBILI (non ufficiali), DC-da-solo, niente quote\n")
    for league, fixtures in FIXTURES.items():
        cfg = LEAGUE_CONFIGS[league]
        m, teams = fit_league(league, as_of)
        print(f"=== {league} (δ={cfg['promoted_prior']}) ===")
        print(f"  {'partita':32s} {'1':>6s} {'X':>6s} {'2':>6s} {'O2.5':>6s} {'GG':>6s}")
        for home, away in fixtures:
            if home not in teams or away not in teams:
                print(f"  {home}-{away}: SALTATA (squadra non nei dati)")
                continue
            lam, mu = m.expected_goals(home, away)
            d = mi.price_markets(lam, mu, rho=m.rho, phi0=m.draw_phi0,
                                 kappa=m.draw_kappa, dp_theta=mi.DP_THETA_DC)
            print(f"  {home+'-'+away:32s} {d['home_win']:6.1%} {d['draw']:6.1%} "
                  f"{d['away_win']:6.1%} {d['over_2.5']:6.1%} {d['btts']:6.1%}")
            rows.append({
                "league": league, "home": home, "away": away,
                "as_of": AS_OF, "lam": round(lam, 3), "mu": round(mu, 3),
                "p_home": round(d["home_win"], 4), "p_draw": round(d["draw"], 4),
                "p_away": round(d["away_win"], 4),
                "p_over25": round(d["over_2.5"], 4), "p_btts": round(d["btts"], 4),
                "model": "DC_gol_xg_phi35_router_v3", "note": "anteprima_illustrativa",
            })
        print()
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Previsioni congelate in {OUT.relative_to(ROOT)} ({len(rows)} partite).")
    print("NB: anteprima, non il test scorato. Vedi experiments/prospettico_2026_27.md")


if __name__ == "__main__":
    main()
