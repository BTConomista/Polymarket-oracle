"""Fase 51 (D) — Le implicazioni ECONOMICHE dei risultati nuovi (ROI a chiusura).

Tre strategie, tutte a quota di CHIUSURA (puntata unitaria), walk-forward:

  1. PARI-EQUILIBRIO coi tassi del MERCATO: la strategia della Fase 40 (scommetti
     il pareggio se |λ−μ| < 0.5, soglia FISSA pre-dichiarata) usava i tassi del DC;
     qui i tassi (migliori) del mercato — mai ricalcolata.
  2. PARI-EQUILIBRIO + FILTRO dp_lvl: come sopra, ma solo se anche il motore
     dp_lvl (51-C: batte la chiusura, CI conclusivo) da' al pari piu' probabilita'
     del mercato (edge>0).
  3. VALUE-BET 1X2 con dp_lvl (edge > 0.03, per esito): il conto della Fase 40
     rifatto col primo motore che batte la chiusura in log-loss. Domanda onesta:
     un edge di log-loss di −0.0016 sopravvive al margine (~5%)?

Uso:  python scripts/_run_fase51_roi.py    (cache db_base)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 51
MAXG = mi.MAX_GOALS
_K = np.arange(MAXG + 1)
_LOGFACT = gammaln(_K + 1.0)
_OI = {"H": 0, "D": 1, "A": 2}
BAL_THR = 0.5          # Fase 40, soglia fissa pre-dichiarata
EDGE = 0.03            # Fase 40, soglia value-bet


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    df = df[ok].reset_index(drop=True)
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    df["mlam"], df["mmu"] = lam, mu
    return df


def _dp_pmf(rates, theta):
    r = np.asarray(rates, float).reshape(-1, 1)
    lo = np.full(len(r), 0.2); hi = np.full(len(r), 5.0)
    for _ in range(45):
        c = 0.5 * (lo + hi)
        lamc = c.reshape(-1, 1) * r
        q = np.exp(theta * (_K * np.log(lamc) - lamc - _LOGFACT))
        q = q / q.sum(1, keepdims=True)
        mean = (q * _K).sum(1)
        too_low = mean < r.ravel()
        lo = np.where(too_low, c, lo); hi = np.where(too_low, hi, c)
    return q


def _matrices(lam, mu, rho, theta):
    qh, qa = _dp_pmf(lam, theta), _dp_pmf(mu, theta)
    M = qh[:, :, None] * qa[:, None, :]
    M[:, 0, 0] *= 1.0 - lam * mu * rho
    M[:, 0, 1] *= 1.0 + lam * rho
    M[:, 1, 0] *= 1.0 + mu * rho
    M[:, 1, 1] *= 1.0 - rho
    M = np.clip(M, 0.0, None)
    return M / M.sum(axis=(1, 2), keepdims=True)


def _p1x2(M):
    tri = np.tril(np.ones((MAXG + 1, MAXG + 1)), -1)
    return np.column_stack([(M * tri[None]).sum(axis=(1, 2)),
                            np.trace(M, axis1=1, axis2=2),
                            (M * tri.T[None]).sum(axis=(1, 2))])


def _fit_theta(lam, mu, hg, ag):
    n = np.arange(len(hg))

    def nll(theta):
        M = _matrices(lam, mu, RHO, theta)
        return -float(np.mean(np.log(np.clip(M[n, hg, ag], 1e-15, None))))
    return float(minimize_scalar(nll, bounds=(0.6, 1.8), method="bounded",
                                 options={"xatol": 1e-3}).x)


def _roi(returns, rng):
    if len(returns) == 0:
        return 0.0, 0.0, 0.0, 0.5, 0
    m = returns[rng.integers(0, len(returns), (B, len(returns)))].mean(1)
    return (float(returns.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m > 0).mean()), len(returns))


def main():
    t0 = time.time()
    df = _load()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in SEASONS if s in set(df.season)]

    ret1, ret2 = [], []                       # pari-equilibrio, + filtro dp_lvl
    ret3 = {"H": [], "D": [], "A": []}        # value-bet 1X2 dp_lvl per esito
    seas_roi1 = {}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        theta = _fit_theta(past.mlam.values, past.mmu.values,
                           past.home_goals.astype(int).values,
                           past.away_goals.astype(int).values)
        c_l = float(np.log(past.home_goals.sum() / past.mlam.sum()))
        c_m = float(np.log(past.away_goals.sum() / past.mmu.sum()))
        P_dp = _p1x2(_matrices(cur.mlam.values * np.exp(c_l),
                               cur.mmu.values * np.exp(c_m), RHO, theta))
        P_mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                          for r in cur.itertuples()])
        odds = cur[["odds_home", "odds_draw", "odds_away"]].to_numpy()
        y = np.array([_OI[r] for r in cur.result])
        bal = np.abs(cur.mlam.values - cur.mmu.values)

        m1 = bal < BAL_THR
        r1 = np.where(y[m1] == 1, odds[m1, 1] - 1.0, -1.0)
        ret1.append(r1)
        seas_roi1[s] = (float(r1.mean()) if len(r1) else 0.0, int(m1.sum()))
        m2 = m1 & (P_dp[:, 1] > P_mkt[:, 1])
        ret2.append(np.where(y[m2] == 1, odds[m2, 1] - 1.0, -1.0))
        for k, o in enumerate("HDA"):
            mk = (P_dp[:, k] - P_mkt[:, k]) > EDGE
            ret3[o].append(np.where(y[mk] == k, odds[mk, k] - 1.0, -1.0))

    rng = np.random.default_rng(SEED)
    ret1 = np.concatenate(ret1); ret2 = np.concatenate(ret2)
    for o in ret3:
        ret3[o] = np.concatenate(ret3[o])

    print("\n" + "=" * 90)
    print("FASE 51 (D) — implicazioni economiche (ROI a quota di chiusura, puntata unitaria)")
    print("=" * 90)
    summary: dict = {}
    m, lo, hi, p, n = _roi(ret1, rng)
    print(f"\n  1) PARI se |λ_mkt−μ_mkt| < {BAL_THR} (Fase 40 coi tassi del mercato):")
    print(f"     n={n}  ROI {m:+.1%}  CI95 [{lo:+.1%}, {hi:+.1%}]  P(ROI>0)={p:.0%}")
    print("     per stagione: " + "  ".join(f"{s} {v[0]:+.1%}(n={v[1]})"
                                            for s, v in seas_roi1.items()))
    summary.update(roi_eq=m, roi_eq_ci_lo=lo, roi_eq_ci_hi=hi, roi_eq_p=p, roi_eq_n=n)
    m, lo, hi, p, n = _roi(ret2, rng)
    print(f"\n  2) come 1) + filtro edge dp_lvl (P_dp(pari) > P_mkt(pari)):")
    print(f"     n={n}  ROI {m:+.1%}  CI95 [{lo:+.1%}, {hi:+.1%}]  P(ROI>0)={p:.0%}")
    summary.update(roi_eq_dp=m, roi_eq_dp_ci_lo=lo, roi_eq_dp_ci_hi=hi,
                   roi_eq_dp_p=p, roi_eq_dp_n=n)
    print(f"\n  3) VALUE-BET 1X2 con dp_lvl (edge > {EDGE}):")
    lab = {"H": "casa", "D": "pari", "A": "trasferta"}
    for o in "HDA":
        m, lo, hi, p, n = _roi(ret3[o], rng)
        print(f"     {lab[o]:<10} n={n:>4}  ROI {m:+.1%}  CI95 [{lo:+.1%}, {hi:+.1%}]"
              f"  P(ROI>0)={p:.0%}")
        summary[f"roi_vb_{o}"] = m; summary[f"roi_vb_{o}_n"] = n
        summary[f"roi_vb_{o}_p"] = p

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase51_roi", "league": "serie_a",
         "variant": "roi_pari_equilibrio_mercato_e_dp_lvl",
         "bal_threshold": BAL_THR, "edge": EDGE, "rho": RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(df)), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase51_roi). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
