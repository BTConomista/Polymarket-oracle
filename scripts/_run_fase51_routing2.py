"""Fase 51 (B) — Routing v2: la ricalibrazione dei tassi instradata PER FAMIGLIA.

La Fase 50 (rates_recal) ha trovato che ricalibrazioni DIVERSE aiutano mercati
diversi: i LIVELLI di entrambi i tassi (lvl_both: λ×~0.986, μ×~1.023) aiutano
1X2/pareggio/risultato esatto; il profilo completo su μ (k34_mu) aiuta il GG/NG;
i totali stanno meglio con la τ pura sui tassi grezzi (ogni nudge li peggiora).
Il router della Fase 44 instradava solo la FORMA (φ35 vs τ); qui si instradano
anche i TASSI — combinazione mai valutata:

  ROUTER v2:  totali/marginali → τ, tassi grezzi        (come Fase 44)
              esiti/pareggio/ris.esatto → φ35, tassi lvl_both
              GG/NG → φ35, tassi k34_mu

Confronto sui 19 mercati Tier 1 (media dei log-loss, come Fase 44) e per-mercato:
router Fase 44 (tassi grezzi) vs ROUTER v2. Walk-forward 8 stagioni.

Uso:  python scripts/_run_fase51_routing2.py    (cache db_base)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 51
MAXG = mi.MAX_GOALS

# mercato -> (y(hg,ag), famiglia): tau = totale/marginale; phi = esito/joint.
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


def _add_matchday(df):
    df = df.sort_values("date").reset_index(drop=True)
    m = np.zeros(len(df), int)
    for _, g in df.groupby("season"):
        cnt: dict = {}
        for i in g.index:
            h, a = df.at[i, "home_team"], df.at[i, "away_team"]
            hi, ai = cnt.get(h, 0), cnt.get(a, 0)
            m[i] = int(round((hi + ai) / 2)) + 1
            cnt[h], cnt[a] = hi + 1, ai + 1
    df["matchday"] = m
    return df


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    df = df[ok].reset_index(drop=True)
    df = _add_matchday(df)
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    df["mlam"], df["mmu"] = lam, mu
    return df


def _basis(name, md_):
    md_ = np.asarray(md_, float)
    one = np.ones_like(md_)
    if name == "lvl":
        return np.column_stack([one])
    s = (md_ - 19.5) / 18.5
    tail = np.maximum(0.0, md_ - 34.0) / 4.0
    return np.column_stack([one, s, tail])


def _fit_recal(name, rate, y, md_):
    X = _basis(name, md_)
    base = np.asarray(rate, float); y = np.asarray(y, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(X.shape[1]), jac=grad, method="L-BFGS-B").x


def _ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    y = y.astype(float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def main():
    t0 = time.time()
    df = _load()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in SEASONS if s in set(df.season)]
    acc_v1 = {k: [] for k in _MKTS}
    acc_v2 = {k: [] for k in _MKTS}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        md_p, md_c = past.matchday.values, cur.matchday.values
        is_dr = (past.home_goals == past.away_goals).astype(float).values

        # tassi ricalibrati: livelli (esiti) e profilo-μ k34 (GG)
        c_lvl_l = _fit_recal("lvl", past.mlam.values, past.home_goals.values, md_p)
        c_lvl_m = _fit_recal("lvl", past.mmu.values, past.away_goals.values, md_p)
        c_k34_m = _fit_recal("k34", past.mmu.values, past.away_goals.values, md_p)
        lam_lvl = cur.mlam.values * float(np.exp(c_lvl_l[0]))
        mu_lvl = cur.mmu.values * float(np.exp(c_lvl_m[0]))
        mu_k34 = cur.mmu.values * np.exp(_basis("k34", md_c) @ c_k34_m)

        # φ35: sui tassi grezzi (v1) e sui tassi ricalibrati (v2, per base)
        phi_raw = mi.fit_balance_phi(past.mlam.values, past.mmu.values, is_dr, RHO)
        pl_lvl = past.mlam.values * float(np.exp(c_lvl_l[0]))
        pm_lvl = past.mmu.values * float(np.exp(c_lvl_m[0]))
        phi_lvl = mi.fit_balance_phi(pl_lvl, pm_lvl, is_dr, RHO)
        pm_k34 = past.mmu.values * np.exp(_basis("k34", md_p) @ c_k34_m)
        phi_k34 = mi.fit_balance_phi(past.mlam.values, pm_k34, is_dr, RHO)

        hg = cur.home_goals.astype(int).values
        ag = cur.away_goals.astype(int).values
        for k in range(len(cur)):
            l0, m0 = cur.mlam.values[k], cur.mmu.values[k]
            # --- router v1 (Fase 44): tassi grezzi, forma instradata -------- #
            d1 = mi.price_markets(l0, m0, RHO, phi0=phi_raw[0], kappa=phi_raw[1])
            # --- router v2: tassi per famiglia ------------------------------ #
            M_tau = mi.score_matrix(l0, m0, RHO)
            lv_l, lv_m = lam_lvl[k], mu_lvl[k]
            M_lvl = mi.score_matrix(lv_l, lv_m, RHO,
                                    diag_inflation=mi.balance_phi(lv_l, lv_m, *phi_lvl))
            k_m = mu_k34[k]
            M_gg = mi.score_matrix(l0, k_m, RHO,
                                   diag_inflation=mi.balance_phi(l0, k_m, *phi_k34))
            d_tau = mi.derive_markets(M_tau)
            d_lvl = mi.derive_markets(M_lvl)
            d_gg = mi.derive_markets(M_gg)
            for mk, (yf, fam) in _MKTS.items():
                yv = int(bool(yf(hg[k], ag[k])))
                p1 = d1[mk]
                p2 = {"tau": d_tau, "phi": d_lvl, "gg": d_gg}[fam][mk]
                acc_v1[mk].append(_ll_bin(np.array([p1]), np.array([yv]))[0])
                acc_v2[mk].append(_ll_bin(np.array([p2]), np.array([yv]))[0])
        print(f"  stagione {s} ({time.time()-t0:.0f}s)", flush=True)

    for d_ in (acc_v1, acc_v2):
        for mk in d_:
            d_[mk] = np.array(d_[mk])
    rng = np.random.default_rng(SEED)
    n = len(acc_v1["btts"])

    v1_mean = float(np.mean([acc_v1[mk].mean() for mk in _MKTS]))
    v2_mean = float(np.mean([acc_v2[mk].mean() for mk in _MKTS]))
    print("\n" + "=" * 92)
    print(f"FASE 51 (B) — router v2 (tassi per famiglia) vs router Fase 44 (n={n})")
    print("=" * 92)
    print(f"  media dei 20 mercati:  router-44 {v1_mean:.4f}   ROUTER v2 {v2_mean:.4f}"
          f"   Δ {v2_mean-v1_mean:+.4f}")
    print(f"\n  {'mercato':<16}{'router44':>10}{'v2':>10}{'Δ':>9}{'CI95':>22}{'P':>6}")
    summary: dict = {"router44_mean": v1_mean, "router_v2_mean": v2_mean}
    for mk in _MKTS:
        mean, lo, hi, p = _boot(acc_v2[mk] - acc_v1[mk], rng)
        flag = " ✓" if hi < 0 else (" ✗" if lo > 0 else "")
        print(f"  {mk:<16}{acc_v1[mk].mean():>10.4f}{acc_v2[mk].mean():>10.4f}"
              f"{mean:>+9.4f}   [{lo:+.4f},{hi:+.4f}]{p:>6.0%}{flag}")
        summary[f"{mk}__v1"] = float(acc_v1[mk].mean())
        summary[f"{mk}__v2"] = float(acc_v2[mk].mean())
        summary[f"{mk}__delta"] = mean; summary[f"{mk}__p"] = p

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase51_routing2", "league": "serie_a",
         "variant": "router_v2_tassi_per_famiglia", "rho": RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase51_routing2). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
