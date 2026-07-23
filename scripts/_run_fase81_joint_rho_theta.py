"""Fase 81-bis — Check congiunto ρ×θ (Serie A e Liga): assi sostituti o additivi?

Il mega-sweep (Fase 81) trova su Serie A e Liga guadagni sia spingendo ρ molto
negativo sia alzando θ — ma entrambe le costanti CONCENTRANO la distribuzione
(ρ<0 alza 0-0/1-1, la dp θ>1 stringe le marginali): il sospetto è che siano lo
STESSO fenomeno (sotto-dispersione/deficit-pareggio) espresso su due leve.
Griglia congiunta ρ×θ sui tre mercati chiave: se a θ ottimo il vantaggio di
ρ−0.14/−0.22 sparisce, gli assi sono sostituti e si adotta SOLO θ (una leva,
non due). Riusa le inversioni in cache della Fase 81.

Uso:  python scripts/_run_fase81_joint_rho_theta.py    (~2 min)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log            # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from scripts._run_fase81_mega_sweep_mi import (      # noqa: E402
    SEASONS, _load, _invert_rho, _row_ll, _boot)

RHOS_J = [-0.22, -0.14, -0.06]
THETAS_J = [1.00, 1.10, 1.20, 1.30]
LEAGUES_J = ["serie_a", "la_liga"]
MKJ = ["x2", "gg", "cs"]
SEED = 8100


def main() -> None:
    rng = np.random.default_rng(SEED)
    for league in LEAGUES_J:
        df = _load(league)
        test = np.isin(df.season.values, SEASONS[1:])
        hg = df.home_goals.astype(int).values
        ag = df.away_goals.astype(int).values
        lls = {}
        for rho in RHOS_J:
            lam, mu = _invert_rho(df, league, rho)
            for th in THETAS_J:
                key = (rho, th)
                out = {mk: np.zeros(len(df)) for mk in MKJ}
                for k in range(len(df)):
                    M = mi.score_matrix(lam[k], mu[k], rho,
                                        dp_theta=(th if th != 1.0 else None))
                    r = _row_ll(M, hg[k], ag[k])
                    for mk in MKJ:
                        out[mk][k] = r[mk]
                lls[key] = out

        print("\n" + "=" * 78)
        print(f"FASE 81-bis — {league.upper()}: griglia congiunta ρ×θ (test n={test.sum()})")
        print("=" * 78)
        summary = {}
        for mk in MKJ:
            print(f"  [{mk}]  colonne=θ {THETAS_J}")
            for rho in RHOS_J:
                row = f"    ρ={rho:+.2f} "
                for th in THETAS_J:
                    row += f"  {lls[(rho, th)][mk][test].mean():.4f}"
                print(row)
            best = min(lls, key=lambda k2: lls[k2][mk][test].mean())
            ref = (-0.06, 1.00)
            d = lls[best][mk][test] - lls[ref][mk][test]
            mean, lo, hi, p = _boot(d, rng)
            # il punto chiave: a θ fissato al suo ottimo, ρ<−0.06 aiuta ancora?
            th_best = best[1]
            d_rho = (lls[(-0.22, th_best)][mk][test]
                     - lls[(-0.06, th_best)][mk][test]).mean()
            print(f"    best {best}: Δ vs (−0.06,1.0) {mean:+.4f} "
                  f"[{lo:+.4f},{hi:+.4f}] P{p:.0%} | a θ={th_best}: "
                  f"Δ(ρ−0.22 vs −0.06) = {d_rho:+.4f}")
            summary[mk] = {"best": list(best), "delta": mean, "ci": [lo, hi],
                           "p": p, "rho_gain_at_best_theta": float(d_rho)}

        all_m = loader.load_league(league)
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase81_joint_rho_theta", "league": league,
             "rhos": RHOS_J, "thetas": THETAS_J, "seasons": SEASONS},
            {"n_test": int(test.sum()), **summary},
            experiment_log.data_fingerprint(all_m)))
    print("\nRun registrati (source=fase81_joint_rho_theta).")


if __name__ == "__main__":
    main()
