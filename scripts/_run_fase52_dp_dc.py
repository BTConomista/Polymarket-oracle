"""Fase 52 (D) — La double-Poisson sul path DC (senza quote): la sotto-dispersione regge?

La Fase 51 ha trovato θ≈1.2 sui tassi del MERCATO. Ipotesi fisica: la
sotto-dispersione osservata = (sotto-dispersione vera dei gol) − (rumore di stima
dei tassi). I tassi del DC sono PIU' rumorosi di quelli del mercato → l'attesa e'
θ_DC < θ_mkt (il rumore aggiunge dispersione apparente). Se θ_DC > 1 comunque,
la dp migliora anche il fallback senza quote (oggi: DC+φ35 0.9790, +midweek 0.9786).

Varianti (tassi del DC dalla cache ufficiale, ρ=−0.05):
  tau       matrice Poisson+ρ dai tassi DC                [≈ backtest ufficiale]
  phi35     + φ(|λ−μ|) (Fase 35, rifittata LFO)
  dp        matrice double-Poisson (θ_DC LFO)
  dp_phi    dp + φ35 (rifittata su base dp)

Mercati: 1X2, pareggio, risultato esatto, GG/NG. Bootstrap appaiato vs tau.

Uso:  python scripts/_run_fase52_dp_dc.py    (cache db_base)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log            # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from scripts import _fase52_common as C              # noqa: E402

B, SEED = 10_000, 52
RHO_DC = -0.05
_OI = {"H": 0, "D": 1, "A": 2}
MK = ["x2", "draw", "cs", "gg"]
LAB = {"x2": "1X2", "draw": "pareggio", "cs": "ris.esatto", "gg": "GG/NG"}
VARIANTS = ["tau", "phi35", "dp", "dp_phi"]


def _fit_phi_on(M_base, lam, mu, is_draw):
    d_match = np.clip(np.trace(M_base, axis1=1, axis2=2), 1e-9, 1 - 1e-9)
    bal = np.abs(lam - mu)

    def nll(p):
        phi = p[0] * np.exp(-p[1] * bal)
        return -np.sum(np.log1p(phi * is_draw) - np.log1p(phi * d_match))
    r = minimize(nll, [0.1, 1.0], method="L-BFGS-B",
                 bounds=[(0.0, 2.0), (0.0, 5.0)])
    return float(r.x[0]), float(r.x[1])


def _apply_phi(M, lam, mu, phi0, kappa):
    phi = (phi0 * np.exp(-kappa * np.abs(lam - mu))).reshape(-1, 1)
    M = M.copy()
    idx = np.arange(M.shape[1])
    M[:, idx, idx] *= 1.0 + phi
    return M / M.sum(axis=(1, 2), keepdims=True)


def _mkt_ll(M, hg, ag, res):
    n = np.arange(len(hg))
    out = {}
    P3 = np.clip(C.p1x2(M), 1e-15, 1)
    yi = np.array([_OI[o] for o in res])
    out["x2"] = -np.log(P3[n, yi])
    out["draw"] = C.ll_bin(np.trace(M, axis1=1, axis2=2), (hg == ag).astype(float))
    out["cs"] = -np.log(np.clip(M[n, np.minimum(hg, C.MAXG), np.minimum(ag, C.MAXG)],
                                1e-15, None))
    out["gg"] = C.ll_bin(M[:, 1:, 1:].sum(axis=(1, 2)),
                         ((hg >= 1) & (ag >= 1)).astype(float))
    return out


def main():
    t0 = time.time()
    df = C.load_with_rates()          # servono solo i tassi DC + esiti, ma riusa la cache
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]
    acc = {v: {mk: [] for mk in MK} for v in VARIANTS}
    thetas = []

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        pl, pm = past.exp_home_goals.values, past.exp_away_goals.values
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        is_dr = (phg == pag).astype(float)
        cl, cm = cur.exp_home_goals.values, cur.exp_away_goals.values
        hg = cur.home_goals.astype(int).values
        ag = cur.away_goals.astype(int).values

        theta = C.fit_theta(pl, pm, phg, pag, rho=RHO_DC)
        thetas.append(theta)
        phi_tau = mi.fit_balance_phi(pl, pm, is_dr, RHO_DC)
        Mp_dp = C.dp_matrices(pl, pm, RHO_DC, theta)
        phi_dp = _fit_phi_on(Mp_dp, pl, pm, is_dr)

        M_tau = C.dp_matrices(cl, cm, RHO_DC, 1.0)
        M_dp = C.dp_matrices(cl, cm, RHO_DC, theta)
        mats = {
            "tau": M_tau,
            "phi35": _apply_phi(M_tau, cl, cm, *phi_tau),
            "dp": M_dp,
            "dp_phi": _apply_phi(M_dp, cl, cm, *phi_dp),
        }
        for v, M in mats.items():
            r = _mkt_ll(M, hg, ag, cur.result.values)
            for mk in MK:
                acc[v][mk].append(r[mk])
        print(f"  stagione {s} (θ_DC={theta:.3f}; {time.time()-t0:.0f}s)", flush=True)

    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.concatenate(acc[v][mk])
    rng = np.random.default_rng(SEED)
    n = len(acc["tau"]["x2"])

    print("\n" + "=" * 88)
    print(f"FASE 52 (D) — double-Poisson sul path DC (n={n})")
    print(f"θ_DC medio: {np.mean(thetas):.3f}   (θ_mercato: 1.205 — attesa: θ_DC piu' basso)")
    print("=" * 88)
    print(f"  {'variante':<10}" + "".join(f"{LAB[mk]:>12}" for mk in MK))
    best = {mk: min(VARIANTS, key=lambda v: acc[v][mk].mean()) for mk in MK}
    for v in VARIANTS:
        print(f"  {v:<10}" + "".join(
            f"{acc[v][mk].mean():>11.4f}" + ("*" if best[mk] == v else " ") for mk in MK))
    print("\n  Δ vs tau, bootstrap appaiato:")
    summary: dict = {"theta_dc_mean": float(np.mean(thetas))}
    for v in VARIANTS[1:]:
        for mk in MK:
            mean, lo, hi, p = C.boot(acc[v][mk] - acc["tau"][mk], rng)
            summary[f"{v}__{mk}_delta"] = mean; summary[f"{v}__{mk}_p"] = p
            summary[f"{v}__{mk}_ci_lo"] = lo; summary[f"{v}__{mk}_ci_hi"] = hi
        print(f"    {v:<8} 1X2 Δ={summary[f'{v}__x2_delta']:+.4f} (P={summary[f'{v}__x2_p']:.0%})"
              f"   esatto Δ={summary[f'{v}__cs_delta']:+.4f} (P={summary[f'{v}__cs_p']:.0%})"
              f"   GG Δ={summary[f'{v}__gg_delta']:+.4f} (P={summary[f'{v}__gg_p']:.0%})")
    summary.update({f"{v}__{mk}": float(acc[v][mk].mean())
                    for v in VARIANTS for mk in MK})

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_dp_dc", "league": "serie_a",
         "variant": "double_poisson_su_tassi_dc", "rho": RHO_DC,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_dp_dc). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
