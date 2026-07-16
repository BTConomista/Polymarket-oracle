"""Fase 51 (C) — Si batte la CHIUSURA sull'1X2? Il test appaiato delle vie di sharpening.

La batteria delle forme (51-A) trova che la double-Poisson (sotto-dispersione,
θ≈1.20 stabile 7/7 fit) porta l'1X2 del motore market-implied a 0.9615 — SOTTO la
lettura diretta del mercato devigato (0.9625). Sarebbe la prima volta che qualcosa
"batte la chiusura" in log-loss. Ma serve il confronto APPAIATO, sulla stessa
finestra, contro TUTTE le vie di sharpening/ricalibrazione del mercato — alcune mai
provate (la temperatura sul MERCATO; la Fase 6 la provò solo sul modello):

  market      lettura diretta (devig moltiplicativo)               [riferimento]
  mkt_temp    temperatura T fittata LFO sulle prob del mercato     (mai provata)
  mkt_wclass  ricalibrazione per-classe w_D,w_A (Fase 50-ter)
  dp          matrice double-Poisson (θ LFO) sui tassi grezzi      (51-A)
  dp_lvl      double-Poisson + livelli dei tassi (lvl_both, 50)    (combo nuova)
  dp_wclass   double-Poisson + ricalibrazione per-classe sopra     (combo nuova)

Bootstrap appaiato vs `market`; per-stagione; regola pre-dichiarata di onesta':
il verdetto principale usa TUTTE le 7 stagioni di test, ma si riporta anche il
sottoinsieme con fit >= 2 stagioni (lezione 50-ter: il primo fit e' sottile).

Uso:  python scripts/_run_fase51_beat_close.py    (cache db_base)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
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
VARIANTS = ["market", "mkt_temp", "mkt_wclass", "dp", "dp_lvl", "dp_wclass"]


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
    if theta == 1.0:
        q = np.exp(_K * np.log(r) - r - _LOGFACT)
        return q / q.sum(1, keepdims=True)
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
    ph = (M * tri[None]).sum(axis=(1, 2))
    pd_ = np.trace(M, axis1=1, axis2=2)
    pa = (M * tri.T[None]).sum(axis=(1, 2))
    return np.column_stack([ph, pd_, pa])


def _fit_theta(lam, mu, hg, ag):
    n = np.arange(len(hg))

    def nll(theta):
        M = _matrices(lam, mu, RHO, theta)
        return -float(np.mean(np.log(np.clip(M[n, hg, ag], 1e-15, None))))
    return float(minimize_scalar(nll, bounds=(0.6, 1.8), method="bounded",
                                 options={"xatol": 1e-3}).x)


def _fit_lvl(rate, y):
    return float(np.log(np.sum(y) / np.sum(rate)))


def _fit_temp(P, y):
    def nll(t):
        Q = P ** t; Q = Q / Q.sum(1, keepdims=True)
        return -float(np.mean(np.log(np.clip(Q[np.arange(len(y)), y], 1e-15, 1))))
    return float(minimize_scalar(nll, bounds=(0.7, 1.4), method="bounded",
                                 options={"xatol": 1e-4}).x)


def _fit_wclass(P, y):
    def nll(x):
        w = np.array([1.0, x[0], x[1]])
        Q = P * w; Q = Q / Q.sum(1, keepdims=True)
        return -float(np.mean(np.log(np.clip(Q[np.arange(len(y)), y], 1e-15, 1))))
    r = minimize(nll, [1.0, 1.0], method="L-BFGS-B", bounds=[(0.5, 2), (0.5, 2)])
    return np.array([1.0, r.x[0], r.x[1]])


def _apply_w(P, w):
    Q = P * w
    return Q / Q.sum(1, keepdims=True)


def _ll(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def main():
    t0 = time.time()
    df = _load()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in SEASONS if s in set(df.season)]

    acc = {v: [] for v in VARIANTS}
    acc_ge2 = {v: [] for v in VARIANTS}     # solo test con fit >= 2 stagioni
    per_season: dict = {}
    pars = {"theta": [], "T": [], "w": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        pl, pm = past.mlam.values, past.mmu.values
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        P_past = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                           for r in past.itertuples()])
        y_past = np.array([_OI[r] for r in past.result])

        theta = _fit_theta(pl, pm, phg, pag)
        T = _fit_temp(P_past, y_past)
        w = _fit_wclass(P_past, y_past)
        c_l = _fit_lvl(pl, phg); c_m = _fit_lvl(pm, pag)
        pars["theta"].append(theta); pars["T"].append(T); pars["w"].append(w)

        P_cur = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                          for r in cur.itertuples()])
        y_cur = np.array([_OI[r] for r in cur.result])
        cl, cm = cur.mlam.values, cur.mmu.values

        Pt = P_cur ** T; Pt = Pt / Pt.sum(1, keepdims=True)
        P_dp = _p1x2(_matrices(cl, cm, RHO, theta))
        P_dpl = _p1x2(_matrices(cl * np.exp(c_l), cm * np.exp(c_m), RHO, theta))
        preds = {
            "market": P_cur,
            "mkt_temp": Pt,
            "mkt_wclass": _apply_w(P_cur, w),
            "dp": P_dp,
            "dp_lvl": P_dpl,
            "dp_wclass": _apply_w(P_dp, w),
        }
        row = {}
        for v, P in preds.items():
            ll = _ll(P, y_cur)
            acc[v].append(ll)
            if i >= 2:
                acc_ge2[v].append(ll)
            row[v] = float(ll.mean())
        per_season[s] = row
        print(f"  {s}: mkt {row['market']:.4f}  temp {row['mkt_temp']:.4f}  "
              f"wcl {row['mkt_wclass']:.4f}  dp {row['dp']:.4f}  dp_lvl {row['dp_lvl']:.4f}"
              f"  dp_wcl {row['dp_wclass']:.4f}   (θ={theta:.3f} T={T:.3f})", flush=True)

    for d_ in (acc, acc_ge2):
        for v in d_:
            d_[v] = np.concatenate(d_[v]) if d_[v] else np.array([])
    rng = np.random.default_rng(SEED)

    print("\n" + "=" * 96)
    print(f"FASE 51 (C) — battere la chiusura 1X2? (walk-forward, n={len(acc['market'])})")
    print(f"parametri medi: θ={np.mean(pars['theta']):.3f}  T={np.mean(pars['T']):.3f}  "
          f"w_D={np.mean([w[1] for w in pars['w']]):.3f}  "
          f"w_A={np.mean([w[2] for w in pars['w']]):.3f}")
    print("=" * 96)
    summary: dict = {"theta_mean": float(np.mean(pars["theta"])),
                     "temp_mean": float(np.mean(pars["T"]))}
    print(f"  {'variante':<12}{'1X2':>9}{'Δ vs mercato':>14}{'CI95':>22}{'P(batte)':>10}"
          f"{'  (fit>=2 stag.)':>18}")
    print(f"  {'market':<12}{acc['market'].mean():>9.4f}")
    summary["market__ll"] = float(acc["market"].mean())
    wins = {}
    for v in VARIANTS[1:]:
        mean, lo, hi, p = _boot(acc[v] - acc["market"], rng)
        m2 = float((acc_ge2[v] - acc_ge2["market"]).mean())
        n_seas = sum(1 for s in per_season if per_season[s][v] < per_season[s]["market"])
        wins[v] = n_seas
        flag = " ✓CI" if hi < 0 else ""
        print(f"  {v:<12}{acc[v].mean():>9.4f}{mean:>+14.4f}   [{lo:+.4f},{hi:+.4f}]"
              f"{p:>10.0%}{m2:>+13.4f}{flag}   ({n_seas}/{len(per_season)} stag.)")
        summary[f"{v}__ll"] = float(acc[v].mean())
        summary[f"{v}__delta"] = mean; summary[f"{v}__p"] = p
        summary[f"{v}__ci_lo"] = lo; summary[f"{v}__ci_hi"] = hi
        summary[f"{v}__delta_ge2"] = m2
        summary[f"{v}__seasons_beat"] = n_seas

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase51_beat_close", "league": "serie_a",
         "variant": "sharpening_vs_chiusura_1x2", "rho": RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(acc["market"])), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase51_beat_close). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
