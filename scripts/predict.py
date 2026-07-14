"""Tool di predizione: tutti i mercati di una singola partita, con i due modelli.

Modello 1 — Dixon-Coles gol+xG (config ufficiale, src/config.py): predice DA SOLO
  a partire dai dati storici (stima forza attacco/difesa di ogni squadra, gol attesi
  λ,μ, matrice dei punteggi → OGNI mercato in modo coerente). Opzionale φ(|λ−μ|)
  della Fase 35 per la calibrazione del pareggio nelle partite equilibrate.

Modello 2 — market-implied (Fase 26/39): NON predice da solo, RICHIEDE le quote
  1X2+O/U del match; le inverte in λ,μ del mercato e ne deriva i mercati sui gol
  (utile soprattutto per quelli che il book non prezza: GG/NG, risultato esatto).
  Si attiva passando --odds.

Esempi:
  python scripts/predict.py Roma Fiorentina
  python scripts/predict.py Roma Fiorentina --date 2026-08-24
  python scripts/predict.py Roma Fiorentina --odds 1.85 3.60 4.20 2.00 1.80
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import SERIE_A                     # noqa: E402
from src.data import loader                        # noqa: E402
from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402
from src.models.dixon_coles import DixonColesModel  # noqa: E402
from scripts.backtest import promoted_teams        # noqa: E402


def _top_scores(M: np.ndarray, n: int = 6):
    flat = np.argsort(-M, axis=None)[:n]
    return [(int(i), int(j), float(M[i, j]))
            for i, j in (np.unravel_index(k, M.shape) for k in flat)]


def _show(pred, titolo: str) -> None:
    p = pred
    print(f"\n----- {titolo} -----")
    print(f"  Gol attesi:  casa λ={p.exp_home_goals:.2f}   ospite μ={p.exp_away_goals:.2f}")
    print(f"  1X2:            casa {p.prob_home_win:6.1%}   pari {p.prob_draw:6.1%}   ospite {p.prob_away_win:6.1%}")
    print(f"  Doppia chance:  1X   {p.prob_1x:6.1%}   X2   {p.prob_2x:6.1%}   12   {p.prob_12:6.1%}")
    print(f"  Over/Under 2.5: Over {p.prob_over_2_5:6.1%}   Under {p.prob_under_2_5:6.1%}")
    print(f"  GG/NG:          GG   {p.prob_btts_yes:6.1%}   NG   {p.prob_btts_no:6.1%}")
    print("  Risultati esatti piu' probabili:  "
          + "   ".join(f"{i}-{j} {pr:.1%}" for i, j, pr in _top_scores(p.score_matrix)))


def main() -> None:
    ap = argparse.ArgumentParser(description="Predice tutti i mercati di una partita.")
    ap.add_argument("home"); ap.add_argument("away")
    ap.add_argument("--league", default="serie_a")
    ap.add_argument("--date", default=None,
                    help="momento della predizione (YYYY-MM-DD); default: dopo l'ultima gara nota")
    ap.add_argument("--odds", nargs=5, type=float, default=None,
                    metavar=("H", "D", "A", "OVER", "UNDER"),
                    help="quote 1X2 + Over/Under 2.5 -> attiva il market-implied (Modello 2)")
    ap.add_argument("--no-draw-balance", action="store_true",
                    help="non mostrare la variante Fase 35 φ(|λ−μ|)")
    args = ap.parse_args()

    allm = loader.load_league(args.league)
    as_of = pd.Timestamp(args.date) if args.date else allm["date"].max() + pd.Timedelta(days=1)
    teams = set(allm["home_team"]) | set(allm["away_team"])
    for t in (args.home, args.away):
        if t not in teams:
            raise SystemExit(f"Squadra sconosciuta: {t!r}. Esempi: {sorted(teams)[:8]}...")
    prom = promoted_teams(allm, str(allm["season"].iloc[-1]))

    print("=" * 74)
    print(f"MODELLO 1 — Dixon-Coles gol+xG  |  {args.home} - {args.away}")
    print(f"allenato fino a {allm['date'].max().date()}, predizione as_of {as_of.date()}")
    print(f"config ufficiale: {SERIE_A}")
    print("=" * 74)

    kw = dict(half_life_days=SERIE_A["half_life_days"], shrinkage=SERIE_A["shrinkage"],
              shots_blend=SERIE_A["shots_blend"], blend_signal=SERIE_A["blend_signal"],
              promoted_prior=(SERIE_A["promoted_prior"], SERIE_A["promoted_prior"]))
    m = DixonColesModel(**kw).fit(allm, as_of_date=as_of, promoted_teams=prom)
    print("Forza stimata (log-scala, 0 = media lega):")
    for t in (args.home, args.away):
        print(f"  {t:<14} attacco {m.attack.get(t, 0.0):+.3f}   difesa {m.defense.get(t, 0.0):+.3f}")
    print(f"  vantaggio-casa globale γ = {m.home_advantage:+.3f}")
    _show(m.predict_match(args.home, args.away), "Modello 1a: base (config ufficiale)")

    if not args.no_draw_balance:
        mb = DixonColesModel(**kw, draw_balance=True).fit(allm, as_of_date=as_of, promoted_teams=prom)
        print(f"\n  [Fase 35: φ0={mb.draw_phi0:.3f}, κ={mb.draw_kappa:.3f} — boost pari solo se |λ−μ| piccolo]")
        _show(mb.predict_match(args.home, args.away), "Modello 1b: + φ(|λ−μ|) Fase 35")

    print("\n" + "=" * 74)
    print("MODELLO 2 — market-implied (richiede le quote del match)")
    print("=" * 74)
    if args.odds is None:
        print("  Non attivato: passa --odds H D A OVER UNDER per invertirle in λ,μ del")
        print("  mercato e derivarne i mercati (specialmente GG/NG e risultato esatto).")
    else:
        oH, oD, oA, oOv, oUn = args.odds
        pH, pD, pA = metrics.devig_1x2(oH, oD, oA)
        pO, _ = metrics.devig_binary(oOv, oUn)
        d = mi.markets_from_odds(pH, pD, pA, pO, rho=-0.06)
        print(f"  quote devigate:  casa {pH:.1%}  pari {pD:.1%}  ospite {pA:.1%}  Over2.5 {pO:.1%}")
        print(f"  -> λ,μ impliciti nel mercato:  casa {d['lam']:.2f}   ospite {d['mu']:.2f}")
        print(f"  1X2:  casa {d['home_win']:.1%}  pari {d['draw']:.1%}  ospite {d['away_win']:.1%}")
        print(f"  O/U 2.5: Over {d['over_2.5']:.1%}   GG/NG: GG {d['btts']:.1%}   "
              f"multigol 2-3 {d['mg_2_3']:.1%}")


if __name__ == "__main__":
    main()
