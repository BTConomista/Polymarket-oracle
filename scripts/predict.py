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


def _show_markets(d: dict, titolo: str, rho: float = 0.0, matchday: int | None = None) -> None:
    """Stampa TUTTI i mercati Tier 1 da un dizionario price_markets (forma
    instradata per-mercato: φ35 su esiti/pareggio, τ sui totali — Fase 44).

    Se `matchday` e' passato, mostra anche la GG/NG col NUDGE stagionale di fine
    stagione (Fase 48): alza μ per il solo GG/NG col profilo della giornata. OFF
    di default (guadagno ~90% probabile, CI include lo zero): riga informativa."""
    print(f"\n----- {titolo} -----")
    print(f"  Gol attesi:  casa λ={d['lam']:.2f}   ospite μ={d['mu']:.2f}")
    print(f"  1X2:            1 {d['home_win']:6.1%}   X {d['draw']:6.1%}   2 {d['away_win']:6.1%}")
    print(f"  Doppia chance:  1X {d['dc_1x']:6.1%}   X2 {d['dc_2x']:6.1%}   12 {d['dc_12']:6.1%}")
    print(f"  Over/Under:     O1.5 {d['over_1.5']:5.1%}  O2.5 {d['over_2.5']:5.1%}  O3.5 {d['over_3.5']:5.1%}")
    print(f"  GG/NG:          GG {d['btts']:6.1%}   NG {1-d['btts']:6.1%}")
    if matchday is not None:
        f = mi.season_mu_factor(matchday)
        gg_n = mi.btts_season(d["lam"], d["mu"], matchday, rho)
        print(f"    └ +nudge stag. (g.{matchday}, μ×{f:.3f}):  GG {gg_n:6.1%}   "
              f"NG {1-gg_n:6.1%}   [opt-in, utile solo nel finale]")
    print(f"  Multigol:       0-1 {d['mg_0_1']:5.1%}  2-3 {d['mg_2_3']:5.1%}  4+ {d['mg_4plus']:5.1%}")
    print(f"  Total-squadra:  casa O1.5 {d['home_ov_1.5']:5.1%}   ospite O1.5 {d['away_ov_1.5']:5.1%}")
    print(f"  Clean sheet:    casa {d['cs_home']:6.1%}   ospite {d['cs_away']:6.1%}")
    print(f"  Vince a zero:   casa {d['wtn_home']:6.1%}   ospite {d['wtn_away']:6.1%}")
    print(f"  Scarto >=2:     casa {d['home_by_2plus']:6.1%}   ospite {d['away_by_2plus']:6.1%}")
    print("  Risultati esatti piu' probabili:  "
          + "   ".join(f"{i}-{j} {pr:.1%}" for i, j, pr in _top_scores(d["score_matrix"])))


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
    ap.add_argument("--matchday", type=int, default=None,
                    help="giornata (1-38): mostra il nudge stagionale GG/NG di fine "
                         "stagione (Fase 48; utile solo nel finale 35-38)")
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
    # Modello DC con φ35 (draw_balance): fornisce λ,μ, rho e (φ0,κ) per il routing.
    m = DixonColesModel(**kw, draw_balance=True).fit(allm, as_of_date=as_of, promoted_teams=prom)
    print("Forza stimata (log-scala, 0 = media lega):")
    for t in (args.home, args.away):
        print(f"  {t:<14} attacco {m.attack.get(t, 0.0):+.3f}   difesa {m.defense.get(t, 0.0):+.3f}")
    print(f"  vantaggio-casa globale γ = {m.home_advantage:+.3f}   "
          f"[φ35: φ0={m.draw_phi0:.3f}, κ={m.draw_kappa:.3f}]")
    lam_dc, mu_dc = m.expected_goals(args.home, args.away)
    d_dc = mi.price_markets(lam_dc, mu_dc, rho=m.rho, phi0=m.draw_phi0, kappa=m.draw_kappa)
    _show_markets(d_dc, "Modello 1: DC gol+xG + φ35 (forma instradata per-mercato)",
                  rho=m.rho, matchday=args.matchday)

    print("\n" + "=" * 74)
    print("MODELLO 2 — market-implied (richiede le quote del match)")
    print("=" * 74)
    if args.odds is None:
        print("  Non attivato: passa --odds H D A OVER UNDER per invertirle in λ,μ del")
        print("  mercato e prezzarne TUTTI i mercati (routing φ35/τ per-mercato).")
    else:
        oH, oD, oA, oOv, oUn = args.odds
        pH, pD, pA = metrics.devig_1x2(oH, oD, oA)
        pO, _ = metrics.devig_binary(oOv, oUn)
        lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, rho=-0.06)
        # φ del mercato: valori rappresentativi (Fase 39); il guadagno di un fit
        # esatto e' trascurabile (Fase 44).
        d = mi.price_markets(lam, mu, rho=-0.06, phi0=0.30, kappa=1.5)
        print(f"  quote devigate:  casa {pH:.1%}  pari {pD:.1%}  ospite {pA:.1%}  Over2.5 {pO:.1%}")
        _show_markets(d, "Modello 2: market-implied + φ35 (forma instradata per-mercato)",
                      rho=-0.06, matchday=args.matchday)


if __name__ == "__main__":
    main()
