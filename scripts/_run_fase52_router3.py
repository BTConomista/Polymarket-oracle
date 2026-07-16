"""Fase 52 (B) — Router v3: la double-Poisson estesa a tutto il listino + tripla GG.

La Fase 51 ha adottato la dp solo come lettura 1X2 (sharpen_1x2). Ma nella
batteria la dp vinceva anche su risultato esatto (−0.0078), multigol e pareggio.
Qui si estende per famiglia e si prova la TRIPLA mai composta sul GG:

  ROUTER v2 (attuale): esiti/esatto → φ35 su tassi lvl; GG → φ35+k34; totali → τ
  ROUTER v3:           esiti/esatto/pareggio → dp_lvl + φ35 (φ rifittata su base dp)
                       GG → dp + ricalibrazione-μ k34 + φ35   (TRIPLA, mai provata)
                       totali/marginali → dp sui tassi grezzi (dp era ≥ τ su mg)

Confronto per-mercato e in media sui 20 Tier 1, bootstrap appaiato v3 − v2.

Uso:  python scripts/_run_fase52_router3.py    (cache db_base + implied_rates)
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

_MKTS: dict = {
    "over_0.5": (lambda h, a: h + a >= 1, "tau"),
    "over_1.5": (lambda h, a: h + a >= 2, "tau"),
    "over_2.5": (lambda h, a: h + a >= 3, "tau"),
    "over_3.5": (lambda h, a: h + a >= 4, "tau"),
    "over_4.5": (lambda h, a: h + a >= 5, "tau"),
    "mg_0_1": (lambda h, a: h + a <= 1, "tau"),
    "mg_2_3": (lambda h, a: (h + a >= 2) & (h + a <= 3), "tau"),
    "mg_4plus": (lambda h, a: h + a >= 4, "tau"),
    "home_ov_0.5": (lambda h, a: h >= 1, "tau"),
    "home_ov_1.5": (lambda h, a: h >= 2, "tau"),
    "away_ov_0.5": (lambda h, a: a >= 1, "tau"),
    "away_ov_1.5": (lambda h, a: a >= 2, "tau"),
    "odd_total": (lambda h, a: (h + a) % 2 == 1, "tau"),
    "cs_home": (lambda h, a: a == 0, "tau"),
    "cs_away": (lambda h, a: h == 0, "tau"),
    "btts": (lambda h, a: (h >= 1) & (a >= 1), "gg"),
    "home_win": (lambda h, a: h > a, "phi"),
    "draw": (lambda h, a: h == a, "phi"),
    "home_by_2plus": (lambda h, a: h - a >= 2, "phi"),
    "wtn_home": (lambda h, a: (h > 0) & (a == 0), "phi"),
}


def _knee_basis(md_):
    md_ = np.asarray(md_, float)
    s = (md_ - 19.5) / 18.5
    tail = np.maximum(0.0, md_ - 34.0) / 4.0
    return np.column_stack([np.ones_like(md_), s, tail])


def _fit_k34(rate, y, md_):
    X = _knee_basis(md_)
    base = np.asarray(rate, float); y = np.asarray(y, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(3), jac=grad, method="L-BFGS-B").x


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


def _derive_all(M):
    """Probabilita' (N,) di ogni mercato Tier 1 dalle matrici (N,11,11)."""
    i = C.K.reshape(-1, 1); j = C.K.reshape(1, -1); tot = i + j
    tri = np.tril(np.ones((C.MAXG + 1, C.MAXG + 1)), -1)
    ph = (M * tri[None]).sum(axis=(1, 2))
    pd_ = np.trace(M, axis1=1, axis2=2)
    return {
        "over_0.5": M[:, tot >= 1].sum(1), "over_1.5": M[:, tot >= 2].sum(1),
        "over_2.5": M[:, tot >= 3].sum(1), "over_3.5": M[:, tot >= 4].sum(1),
        "over_4.5": M[:, tot >= 5].sum(1),
        "mg_0_1": M[:, tot <= 1].sum(1),
        "mg_2_3": M[:, (tot >= 2) & (tot <= 3)].sum(1),
        "mg_4plus": M[:, tot >= 4].sum(1),
        "home_ov_0.5": M[:, i.ravel() >= 1, :].sum(axis=(1, 2)),
        "home_ov_1.5": M[:, i.ravel() >= 2, :].sum(axis=(1, 2)),
        "away_ov_0.5": M[:, :, j.ravel() >= 1].sum(axis=(1, 2)),
        "away_ov_1.5": M[:, :, j.ravel() >= 2].sum(axis=(1, 2)),
        "odd_total": M[:, (tot % 2) == 1].sum(1),
        "cs_home": M[:, :, 0].sum(1), "cs_away": M[:, 0, :].sum(1),
        "btts": M[:, 1:, 1:].sum(axis=(1, 2)),
        "home_win": ph, "draw": pd_,
        "home_by_2plus": M[:, (i - j) >= 2].sum(1),
        "wtn_home": M[:, 1:, 0].sum(1),
    }


def main():
    t0 = time.time()
    df = C.load_with_rates()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]
    acc_v2 = {k: [] for k in _MKTS}
    acc_v3 = {k: [] for k in _MKTS}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        md_p, md_c = past.matchday.values, cur.matchday.values
        pl, pm = past.mlam.values, past.mmu.values
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        is_dr = (phg == pag).astype(float)
        cl, cm = cur.mlam.values, cur.mmu.values
        hg = cur.home_goals.astype(int).values
        ag = cur.away_goals.astype(int).values

        # fit comuni
        theta = C.fit_theta(pl, pm, phg, pag)
        c_l = C.fit_level(pl, phg); c_m = C.fit_level(pm, pag)
        c_k34 = _fit_k34(pm, pag, md_p)
        mu_k34_p = pm * np.exp(_knee_basis(md_p) @ c_k34)
        mu_k34_c = cm * np.exp(_knee_basis(md_c) @ c_k34)

        # --- ROUTER v2 (Fase 51-B) --------------------------------------- #
        pl_lvl, pm_lvl = pl * np.exp(c_l), pm * np.exp(c_m)
        phi_lvl = mi.fit_balance_phi(pl_lvl, pm_lvl, is_dr, C.RHO)
        phi_k34 = mi.fit_balance_phi(pl, mu_k34_p, is_dr, C.RHO)
        M2_tau = C.dp_matrices(cl, cm, C.RHO, 1.0)
        cl_lvl, cm_lvl = cl * np.exp(c_l), cm * np.exp(c_m)
        M2_out = _apply_phi(C.dp_matrices(cl_lvl, cm_lvl, C.RHO, 1.0),
                            cl_lvl, cm_lvl, *phi_lvl)
        M2_gg = _apply_phi(C.dp_matrices(cl, mu_k34_c, C.RHO, 1.0),
                           cl, mu_k34_c, *phi_k34)
        d2 = {"tau": _derive_all(M2_tau), "phi": _derive_all(M2_out),
              "gg": _derive_all(M2_gg)}

        # --- ROUTER v3 (dp ovunque + tripla GG) --------------------------- #
        Mp_dplvl = C.dp_matrices(pl_lvl, pm_lvl, C.RHO, theta)
        phi_dplvl = _fit_phi_on(Mp_dplvl, pl_lvl, pm_lvl, is_dr)
        Mp_dpk34 = C.dp_matrices(pl, mu_k34_p, C.RHO, theta)
        phi_dpk34 = _fit_phi_on(Mp_dpk34, pl, mu_k34_p, is_dr)
        M3_tot = C.dp_matrices(cl, cm, C.RHO, theta)
        M3_out = _apply_phi(C.dp_matrices(cl_lvl, cm_lvl, C.RHO, theta),
                            cl_lvl, cm_lvl, *phi_dplvl)
        M3_gg = _apply_phi(C.dp_matrices(cl, mu_k34_c, C.RHO, theta),
                           cl, mu_k34_c, *phi_dpk34)
        d3 = {"tau": _derive_all(M3_tot), "phi": _derive_all(M3_out),
              "gg": _derive_all(M3_gg)}

        for mk, (yf, fam) in _MKTS.items():
            yv = yf(hg, ag).astype(float)
            acc_v2[mk].append(C.ll_bin(d2[fam][mk], yv))
            acc_v3[mk].append(C.ll_bin(d3[fam][mk], yv))
        print(f"  stagione {s} ({time.time()-t0:.0f}s)", flush=True)

    for d_ in (acc_v2, acc_v3):
        for mk in d_:
            d_[mk] = np.concatenate(d_[mk])
    rng = np.random.default_rng(SEED)
    n = len(acc_v2["btts"])

    v2_mean = float(np.mean([acc_v2[mk].mean() for mk in _MKTS]))
    v3_mean = float(np.mean([acc_v3[mk].mean() for mk in _MKTS]))
    print("\n" + "=" * 92)
    print(f"FASE 52 (B) — router v3 (dp ovunque + tripla GG) vs router v2 (n={n})")
    print("=" * 92)
    print(f"  media dei 20 mercati:  v2 {v2_mean:.4f}   v3 {v3_mean:.4f}   Δ {v3_mean-v2_mean:+.4f}")
    print(f"\n  {'mercato':<16}{'v2':>10}{'v3':>10}{'Δ':>9}{'CI95':>22}{'P':>6}")
    summary: dict = {"v2_mean": v2_mean, "v3_mean": v3_mean}
    for mk in _MKTS:
        mean, lo, hi, p = C.boot(acc_v3[mk] - acc_v2[mk], rng)
        flag = " ✓" if hi < 0 else (" ✗" if lo > 0 else "")
        print(f"  {mk:<16}{acc_v2[mk].mean():>10.4f}{acc_v3[mk].mean():>10.4f}"
              f"{mean:>+9.4f}   [{lo:+.4f},{hi:+.4f}]{p:>6.0%}{flag}")
        summary[f"{mk}__v2"] = float(acc_v2[mk].mean())
        summary[f"{mk}__v3"] = float(acc_v3[mk].mean())
        summary[f"{mk}__delta"] = mean; summary[f"{mk}__p"] = p

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_router3", "league": "serie_a",
         "variant": "router_v3_dp_ovunque_tripla_gg", "rho": C.RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_router3). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
