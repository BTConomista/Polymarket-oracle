"""STIMA della linea O/U per le 8 partite con quote corrotte (regola R6).

Il dato vero non è recuperabile (vedi report 7 §1: football-data è la fonte
corrotta stessa, BetExplorer ha ritirato le quote di quelle stagioni, OddsPortal
è escluso dal suo robots.txt, la ricerca web non trova archivi). Resta la
strada che il progetto usa in questi casi: **stimare, con un errore misurato e
dichiarato, tenendo la stima FUORI dallo snapshot**.

Metodo. Per quelle 8 partite l'**1X2 di apertura è integro** (è una colonna
diversa, da un altro provider). L'1X2 e l'O/U descrivono la stessa
distribuzione di gol: invertendo il solo 1X2 nei tassi (λ, μ) con il motore di
produzione e leggendo dalla matrice la P(Over 2.5) si ottiene una stima che non
usa affatto la riga corrotta. È esattamente il ragionamento con cui, in fase di
audit, si è dimostrato QUALE dei due lati fosse rotto.

Errore atteso: misurato sulle partite della STESSA epoca (2017-19, 5 leghe) dove
la linea O/U è integra — lì la stima si può confrontare col dato vero.

Uscita: `cantiere/data/stime_ou_corrotte.csv` (probabilità, mai quote), con
l'errore atteso scritto riga per riga.

Uso: python cantiere/scripts/stima_ou_corrotte.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.evaluation import metrics  # noqa: E402
from src.models import market_implied as mi  # noqa: E402

DATA = ROOT / "cantiere" / "data"
SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": DATA, "ligue_1": DATA}
EPOCA = ["1718", "1819"]      # l'era Betbrain: stessa fonte, stessa semantica
RHO = -0.06


def p_over_da_1x2(oh: float, od: float, oa: float) -> float:
    """P(Over 2.5) implicata dal SOLO 1X2, via inversione nei tassi e matrice."""
    pH, pD, pA = metrics.devig_1x2(oh, od, oa)
    lam, mu = mi.implied_lambda_mu(pH, pD, pA, None, RHO)
    _, _, _, p_over = mi._1x2_over(mi.score_matrix(lam, mu, RHO))
    return float(p_over)


def main() -> int:
    # ---- 1. errore atteso, misurato dove la linea O/U è integra -------------
    err = []
    for league, d in SNAP.items():
        df = pd.read_csv(d / f"{league}_matches.csv", dtype={"season": str},
                         parse_dates=["date"])
        df = df[df.season.isin(EPOCA)].dropna(
            subset=["odds_home_open", "odds_draw_open", "odds_away_open",
                    "odds_over25_open", "odds_under25_open"])
        for r in df.itertuples():
            vero, _ = metrics.devig_binary(r.odds_over25_open, r.odds_under25_open)
            err.append((league, p_over_da_1x2(r.odds_home_open, r.odds_draw_open,
                                              r.odds_away_open), vero))
    e = pd.DataFrame(err, columns=["league", "stima", "vero"])
    e["scarto"] = e.stima - e.vero
    mae_grezzo = float(e.scarto.abs().mean())
    bias = float(e.scarto.mean())

    # correzione del bias, fittata LEAVE-ONE-LEAGUE-OUT (mai in-sample)
    bias_lolo = {lg: float(e[e.league != lg].scarto.mean()) for lg in e.league.unique()}
    e["scarto_corr"] = e.apply(
        lambda r: (r.stima - bias_lolo[r.league]) - r.vero, axis=1)
    mae_corr = float(e.scarto_corr.abs().mean())

    # baseline: la media della lega-stagione (sapere solo "quanto si segna qui")
    e["baseline"] = e.groupby("league").vero.transform("mean")
    mae_base = float((e.baseline - e.vero).abs().mean())

    print(f"ERRORE ATTESO (2017-19, {len(e)} partite con linea O/U integra):")
    print(f"  stima grezza da 1X2      MAE {mae_grezzo:.4f}  (bias {bias:+.4f})")
    print(f"  stima DEBIASATA (LOLO)   MAE {mae_corr:.4f}  <- quella usata")
    print(f"  baseline media di lega   MAE {mae_base:.4f}")
    print(f"  p90 |errore| debiasato   {e.scarto_corr.abs().quantile(0.9):.4f}")
    for lg, g in e.groupby("league"):
        print(f"    {lg:16s} MAE {g.scarto_corr.abs().mean():.4f}  (n={len(g)}, "
              f"correzione {-bias_lolo[lg]:+.4f})")
    mae = mae_corr

    # ---- 2. la stima per le righe corrotte ---------------------------------
    reg = pd.read_csv(DATA / "correzioni_dichiarate.csv", dtype={"season": str})
    corr = reg[(reg.stato == "applicata") & (reg.colonna == "odds_over25_open")]
    rows = []
    for r in corr.itertuples():
        df = pd.read_csv(SNAP[r.league] / f"{r.league}_matches.csv",
                         dtype={"season": str}, parse_dates=["date"])
        m = df[(df.season == r.season) & (df.home_team == r.home_team)
               & (df.away_team == r.away_team)]
        if m.empty:
            raise SystemExit(f"partita non trovata: {r.home_team}-{r.away_team}")
        m = m.iloc[0]
        p = p_over_da_1x2(m.odds_home_open, m.odds_draw_open, m.odds_away_open) \
            - bias_lolo[r.league]
        rows.append({
            "league": r.league, "season": r.season, "date": r.date,
            "home_team": r.home_team, "away_team": r.away_team,
            "p_over25_open_est": round(p, 4), "p_under25_open_est": round(1 - p, 4),
            "metodo": ("inversione 1X2 apertura -> (lambda,mu) -> matrice DC (rho=-0.06), "
                       "meno il bias medio fittato leave-one-league-out"),
            "correzione_bias": round(-bias_lolo[r.league], 4),
            "mae_atteso": round(mae, 4),
            "motivo": "linea O/U originale corrotta (overround impossibile), dato vero non recuperabile",
        })
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "stime_ou_corrotte.csv", index=False)
    print(f"\nSTIME prodotte ({len(out)} partite):")
    print(out[["league", "season", "home_team", "away_team",
               "p_over25_open_est"]].to_string(index=False))
    print(f"\n-> {(DATA / 'stime_ou_corrotte.csv').relative_to(ROOT)}")
    print("   ⚠️  probabilità STIMATE, non quote: restano FUORI dagli snapshot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
