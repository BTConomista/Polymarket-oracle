"""Fase 52 (E) — θ condizionato: la sotto-dispersione e' uniforme o varia col contesto?

La dp della Fase 51 usa un θ GLOBALE (1.205). Se la sotto-dispersione variasse
col contesto — piu' forte nelle partite chiuse? nelle sbilanciate? nel finale? —
un θ(x) a 2 parametri la catturerebbe. Tre condizionamenti, fittati LFO sulla
verosimiglianza congiunta dei punteggi (tassi del mercato, livelli inclusi):

  theta_const   θ costante                        [riferimento, Fase 51]
  theta_vol     θ = θ0 + θ1·(λ+μ − 2.6)           (volume di gol atteso)
  theta_bal     θ = θ0 + θ1·(|λ−μ| − 0.8)         (equilibrio)
  theta_tail    θ = θ0 + θ1·coda34(md)            (fase della stagione)

Mercati: 1X2 e risultato esatto (i piu' sensibili alla forma). Se nessun
condizionamento batte il costante → la sotto-dispersione e' una proprieta'
UNIFORME dei punteggi (robustezza), non un effetto di contesto.

Uso:  python scripts/_run_fase52_theta_cond.py    (cache db_base + implied_rates)
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
from scripts import _fase52_common as C              # noqa: E402

B, SEED = 10_000, 52
_OI = {"H": 0, "D": 1, "A": 2}
VARIANTS = ["theta_const", "theta_vol", "theta_bal", "theta_tail"]


def _xvar(name, lam, mu, md):
    if name == "theta_vol":
        return (lam + mu) - 2.6
    if name == "theta_bal":
        return np.abs(lam - mu) - 0.8
    if name == "theta_tail":
        return np.maximum(0.0, np.asarray(md, float) - 34.0) / 4.0
    return np.zeros(len(lam))


def _fit_theta_cond(lam, mu, hg, ag, x):
    n = np.arange(len(hg))

    def nll(p):
        theta = np.clip(p[0] + p[1] * x, 0.6, 1.8)
        M = C.dp_matrices(lam, mu, C.RHO, np.round(theta, 2))
        return -float(np.mean(np.log(np.clip(M[n, hg, ag], 1e-15, None))))
    r = minimize(nll, [1.2, 0.0], method="Nelder-Mead",
                 options={"xatol": 1e-3, "fatol": 1e-6, "maxiter": 60})
    return float(r.x[0]), float(r.x[1])


def main():
    t0 = time.time()
    df = C.load_with_rates()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]
    acc = {v: {"x2": [], "cs": []} for v in VARIANTS}
    pars: dict = {v: [] for v in VARIANTS}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        c_l = C.fit_level(past.mlam.values, phg)
        c_m = C.fit_level(past.mmu.values, pag)
        pl, pm = past.mlam.values * np.exp(c_l), past.mmu.values * np.exp(c_m)
        cl = cur.mlam.values * np.exp(c_l); cm = cur.mmu.values * np.exp(c_m)
        hg = cur.home_goals.astype(int).values
        ag = cur.away_goals.astype(int).values
        yi = np.array([_OI[o] for o in cur.result])
        n_c = np.arange(len(cur))

        for v in VARIANTS:
            if v == "theta_const":
                th0 = C.fit_theta(pl, pm, phg, pag)
                theta_cur: np.ndarray | float = th0
                pars[v].append((th0, 0.0))
            else:
                xp = _xvar(v, pl, pm, past.matchday.values)
                th0, th1 = _fit_theta_cond(pl, pm, phg, pag, xp)
                xc = _xvar(v, cl, cm, cur.matchday.values)
                theta_cur = np.round(np.clip(th0 + th1 * xc, 0.6, 1.8), 2)
                pars[v].append((th0, th1))
            M = C.dp_matrices(cl, cm, C.RHO, theta_cur)
            P3 = np.clip(C.p1x2(M), 1e-15, 1)
            acc[v]["x2"].append(-np.log(P3[n_c, yi]))
            acc[v]["cs"].append(-np.log(np.clip(
                M[n_c, np.minimum(hg, C.MAXG), np.minimum(ag, C.MAXG)], 1e-15, None)))
        print(f"  stagione {s} ({time.time()-t0:.0f}s)", flush=True)

    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.concatenate(acc[v][mk])
    rng = np.random.default_rng(SEED)
    n = len(acc["theta_const"]["x2"])

    print("\n" + "=" * 88)
    print(f"FASE 52 (E) — θ condizionato al contesto (tassi lvl del mercato, n={n})")
    for v in VARIANTS:
        t0m = np.mean([p[0] for p in pars[v]]); t1m = np.mean([p[1] for p in pars[v]])
        print(f"  {v:<12} θ0={t0m:.3f}  θ1={t1m:+.3f}")
    print("=" * 88)
    summary: dict = {}
    print(f"  {'variante':<14}{'1X2':>9}{'Δ':>9}{'P':>6}{'ris.esatto':>12}{'Δ':>9}{'P':>6}")
    ref = acc["theta_const"]
    print(f"  {'theta_const':<14}{ref['x2'].mean():>9.4f}{'—':>9}{'':>6}"
          f"{ref['cs'].mean():>12.4f}")
    summary["theta_const__x2"] = float(ref["x2"].mean())
    summary["theta_const__cs"] = float(ref["cs"].mean())
    for v in VARIANTS[1:]:
        dx, lox, hix, px = C.boot(acc[v]["x2"] - ref["x2"], rng)
        dc_, loc, hic, pc = C.boot(acc[v]["cs"] - ref["cs"], rng)
        print(f"  {v:<14}{acc[v]['x2'].mean():>9.4f}{dx:>+9.4f}{px:>6.0%}"
              f"{acc[v]['cs'].mean():>12.4f}{dc_:>+9.4f}{pc:>6.0%}")
        summary[f"{v}__x2"] = float(acc[v]["x2"].mean())
        summary[f"{v}__x2_delta"] = dx; summary[f"{v}__x2_p"] = px
        summary[f"{v}__cs_delta"] = dc_; summary[f"{v}__cs_p"] = pc
        summary[f"{v}__theta1_mean"] = float(np.mean([p[1] for p in pars[v]]))

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_theta_cond", "league": "serie_a",
         "variant": "theta_condizionato_contesto", "rho": C.RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_theta_cond). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
