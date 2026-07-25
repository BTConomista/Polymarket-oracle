"""Fase 92 — Dove vive DAVVERO il gap col mercato: la scomposizione esatta.

Per 80 fasi il progetto ha ripetuto che «il gap col mercato vive quasi tutto nel
PAREGGIO», titolo di un intero arco narrativo e motivazione di tre leve
(inflazione della diagonale Fase 12b, rho dinamico Fase 18, phi(|lambda-mu|)
Fase 35). L'audit della Fase 92 ha mostrato che la lettura era ROVESCIATA.

L'errore era logico, non numerico. Il ragionamento originale (Fase 9) diceva:
  «il mercato 12 non richiede di stimare la MASSA del pareggio, solo chi vince;
   il suo gap e' quasi nullo (+0.0020) -> il termine "chi vince" e' ~0 ->
   il grosso del gap e' il pareggio».
Ma `P(12) = P(1) + P(2) = 1 - P(X)` e' un'IDENTITA': prezzare il "12" E'
prezzare la massa del pareggio. Quel +0.0020 non dice che sappiamo prezzare chi
vince: dice che sappiamo prezzare il pareggio.

La scomposizione corretta e' la chain rule del log-loss:

    LL(1X2) = LL(pari vs non-pari)  +  P(non-pari) * LL(casa vs ospite | non-pari)
              \\_____ massa-pareggio _____/   \\______ discriminazione ______/

Il primo termine E' esattamente il mercato "12". Il secondo e' cio' che il
mercato "12" NON misura.

Uso:
  python scripts/_run_fase92_gap_decomposition.py
  python scripts/_run_fase92_gap_decomposition.py --league premier_league
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import league_config              # noqa: E402
from src.evaluation import metrics                # noqa: E402
from scripts.backtest import run_backtest         # noqa: E402

SEASONS = ("2021", "2122", "2223", "2324", "2425", "2526")
IDX = {"H": 0, "D": 1, "A": 2}


def decompose(P: np.ndarray, yi: np.ndarray) -> tuple[float, float, float]:
    """(totale, massa-pareggio, discriminazione) del log-loss 1X2.

    massa-pareggio  = log-loss BINARIO pari/non-pari  (= il mercato "12")
    discriminazione = -log P(esito | non-pari), sommato sui soli non-pari e
                      diviso per TUTTE le partite (cioe' gia' pesato da
                      P(non-pari)), cosi' i due termini ricompongono il totale.
    """
    n = len(P)
    total = float(np.mean(-np.log(P[np.arange(n), yi])))
    px = P[:, 1]
    is_draw = (yi == 1).astype(float)
    draw_mass = float(np.mean(-(is_draw * np.log(px) + (1 - is_draw) * np.log(1 - px))))
    m = yi != 1
    cond = np.where(yi[m] == 0, P[m, 0] / (1 - P[m, 1]), P[m, 2] / (1 - P[m, 1]))
    discrim = float(np.sum(-np.log(cond)) / n)
    return total, draw_mass, discrim


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--league", default="serie_a")
    ap.add_argument("--seasons", nargs="*", default=list(SEASONS))
    args = ap.parse_args(argv)

    cfg = league_config(args.league)
    d = pd.concat([run_backtest(args.league, S, cfg["half_life_days"],
                                shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                                blend_signal=cfg["blend_signal"],
                                promoted_prior=(cfg["promoted_prior"],) * 2, verbose=False)
                   for S in args.seasons], ignore_index=True)
    d = d.dropna(subset=["odds_home", "odds_draw", "odds_away"])

    M = d[["m_home", "m_draw", "m_away"]].to_numpy()
    K = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in d.itertuples()])
    yi = np.array([IDX[v] for v in d["result"]])

    print(f"### {args.league} — {len(d)} partite, stagioni {args.seasons}\n")
    print("LL(1X2) = LL(pari/non-pari) + LL(casa vs ospite | non-pari)")
    res = {}
    for lab, P in [("MODELLO", M), ("MERCATO", K)]:
        t, dm, dc = decompose(P, yi)
        res[lab] = (t, dm, dc)
        print(f"  {lab:8}  totale {t:.6f} = massa-pareggio {dm:.6f} + discriminazione {dc:.6f}"
              f"   (ricompone: {dm+dc:.6f})")

    gt = res["MODELLO"][0] - res["MERCATO"][0]
    gd = res["MODELLO"][1] - res["MERCATO"][1]
    gc = res["MODELLO"][2] - res["MERCATO"][2]
    print(f"\n  GAP TOTALE             {gt:+.6f}")
    print(f"    massa-pareggio       {gd:+.6f}   ({gd/gt*100:5.1f}%)   <- e' il mercato '12'")
    print(f"    discriminazione      {gc:+.6f}   ({gc/gt*100:5.1f}%)   <- il grosso del gap")

    p12_m = M[:, 0] + M[:, 2]
    print(f"\n  verifica dell'identita' P(12) = 1 - P(X): scarto max "
          f"{np.abs(p12_m - (1 - M[:, 1])).max():.2e}")
    print("  -> il mercato '12' NON misura 'chi vince': misura la massa del pareggio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
