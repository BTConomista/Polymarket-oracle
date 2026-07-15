"""Fase 50 (seguito) — RICALIBRAZIONE dei TASSI del market-implied (λ e μ).

Il diagnostico della scomposizione (fase50_mi_decomp) ha mostrato che il nudge-μ
del Track A funziona da RICALIBRAZIONE adattiva del tasso-ospite del mercato, non
da effetto-stagione. Il controllo per-stagione dei livelli rivela l'asimmetria:

    gol_casa / λ_mkt  < 1 in 6/8 stagioni (media ~0.97: λ del mercato ALTO ~3%)
    gol_ospite / μ_mkt > 1 in 6/8 stagioni (media ~1.02: μ del mercato BASSO ~2%)

cioe' il bias-casa del mercato (i book caricano la squadra di casa) sopravvive al
devig e finisce nei tassi invertiti. MAI testato: ricalibrare ENTRAMBI i tassi
walk-forward (livello o profilo stagionale completo) sopra la φ35. Varianti:

  phi35        riferimento (Fase 39)
  lvl_mu       μ·exp(c0)                (gia' nel diagnostico, qui su 5 mercati)
  lvl_both     λ·exp(c0_h), μ·exp(c0_a) (livelli separati per casa e ospite)
  k34_mu       profilo [1,s,coda34] su μ (il migliore del Track A)
  k34_both     profilo su λ E μ         (l'analogo della V2 di Fase 47, sul mercato)

Tutti i parametri fittati LEAVE-FUTURE-OUT; la φ(|λ−μ|) rifittata sui tassi
ricalibrati. Mercati: GG/NG, ris.esatto, multigol, pareggio, O/U 2.5 + 1X2.

Uso:  python scripts/_run_fase50_rates_recal.py    (cache db_base)
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
B, SEED = 10_000, 50
MAXG = mi.MAX_GOALS
MK = ["gg", "cs", "mg", "draw", "ou", "x2"]
LAB = {"gg": "GG/NG", "cs": "ris.esatto", "mg": "multigol", "draw": "pareggio",
       "ou": "O/U 2.5", "x2": "1X2"}
_OI = {"H": 0, "D": 1, "A": 2}


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


def _fit(name, rate, y, md_):
    X = _basis(name, md_)
    base = np.asarray(rate, float); y = np.asarray(y, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(X.shape[1]), jac=grad, method="L-BFGS-B").x


def _row_ll(M, hg, ag, res):
    d = mi.derive_markets(M)
    out = {}
    y_gg = float(hg >= 1 and ag >= 1)
    p = min(max(d["btts"], 1e-15), 1 - 1e-15)
    out["gg"] = -(y_gg * np.log(p) + (1 - y_gg) * np.log(1 - p))
    out["cs"] = -np.log(max(M[min(hg, MAXG), min(ag, MAXG)], 1e-15))
    tot = hg + ag
    pmg = [d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]][0 if tot <= 1 else (1 if tot <= 3 else 2)]
    out["mg"] = -np.log(max(pmg, 1e-15))
    y_dr = float(hg == ag)
    pdr = min(max(d["draw"], 1e-15), 1 - 1e-15)
    out["draw"] = -(y_dr * np.log(pdr) + (1 - y_dr) * np.log(1 - pdr))
    y_ov = float(tot >= 3)
    po = min(max(d["over_2.5"], 1e-15), 1 - 1e-15)
    out["ou"] = -(y_ov * np.log(po) + (1 - y_ov) * np.log(1 - po))
    p3 = np.clip([d["home_win"], d["draw"], d["away_win"]], 1e-15, 1)
    out["x2"] = -np.log(p3[_OI[res]])
    return out


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


VARIANTS = ["phi35", "lvl_mu", "lvl_both", "k34_mu", "k34_both"]


def main():
    t0 = time.time()
    df = _load()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in SEASONS if s in set(df.season)]
    acc = {v: {mk: [] for mk in MK} for v in VARIANTS}
    lvls = {"lam": [], "mu": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        hg_c = cur.home_goals.astype(int).values
        ag_c = cur.away_goals.astype(int).values
        res_c = cur.result.values
        md_p, md_c = past.matchday.values, cur.matchday.values
        is_dr = (past.home_goals == past.away_goals).astype(float).values

        # fit walk-forward dei fattori per variante
        fits = {}
        for v in VARIANTS:
            if v == "phi35":
                lam_pa, mu_pa = past.mlam.values, past.mmu.values
                lam_cu, mu_cu = cur.mlam.values, cur.mmu.values
            else:
                kind = "lvl" if v.startswith("lvl") else "k34"
                c_mu = _fit(kind, past.mmu.values, past.away_goals.values, md_p)
                mu_pa = past.mmu.values * np.exp(_basis(kind, md_p) @ c_mu)
                mu_cu = cur.mmu.values * np.exp(_basis(kind, md_c) @ c_mu)
                if v.endswith("both"):
                    c_lam = _fit(kind, past.mlam.values, past.home_goals.values, md_p)
                    lam_pa = past.mlam.values * np.exp(_basis(kind, md_p) @ c_lam)
                    lam_cu = cur.mlam.values * np.exp(_basis(kind, md_c) @ c_lam)
                    if v == "lvl_both":
                        lvls["lam"].append(float(np.exp(c_lam[0])))
                        lvls["mu"].append(float(np.exp(c_mu[0])))
                else:
                    lam_pa, lam_cu = past.mlam.values, cur.mlam.values
            phi0, kappa = mi.fit_balance_phi(lam_pa, mu_pa, is_dr, RHO)
            fits[v] = (lam_cu, mu_cu, phi0, kappa)

        for v in VARIANTS:
            lam_cu, mu_cu, phi0, kappa = fits[v]
            for k in range(len(cur)):
                l, m = lam_cu[k], mu_cu[k]
                M = mi.score_matrix(l, m, RHO,
                                    diag_inflation=mi.balance_phi(l, m, phi0, kappa))
                r = _row_ll(M, hg_c[k], ag_c[k], res_c[k])
                for mk in MK:
                    acc[v][mk].append(r[mk])
        print(f"  stagione {s} ({time.time()-t0:.0f}s)", flush=True)

    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.array(acc[v][mk])
    rng = np.random.default_rng(SEED)
    n = len(acc["phi35"]["gg"])

    print("\n" + "=" * 100)
    print(f"FASE 50 (seguito) — ricalibrazione dei tassi del market-implied (n={n})")
    if lvls["lam"]:
        print(f"livelli medi walk-forward: λ×{np.mean(lvls['lam']):.4f}   μ×{np.mean(lvls['mu']):.4f}")
    print("=" * 100)
    print(f"  {'variante':<10}" + "".join(f"{LAB[mk]:>12}" for mk in MK))
    best = {mk: min(VARIANTS, key=lambda v: acc[v][mk].mean()) for mk in MK}
    for v in VARIANTS:
        print(f"  {v:<10}" + "".join(
            f"{acc[v][mk].mean():>11.4f}" + ("*" if best[mk] == v else " ") for mk in MK))
    print("\n  Δ vs phi35, bootstrap appaiato (GG e 1X2):")
    summary: dict = {}
    for v in VARIANTS[1:]:
        for mk in ("gg", "x2", "draw"):
            mean, lo, hi, p = _boot(acc[v][mk] - acc["phi35"][mk], rng)
            summary[f"{v}__{mk}_delta"] = mean; summary[f"{v}__{mk}_p"] = p
            summary[f"{v}__{mk}_ci_lo"] = lo; summary[f"{v}__{mk}_ci_hi"] = hi
            if mk in ("gg", "x2"):
                flag = " ✓CI" if hi < 0 else ""
                print(f"    {v:<10} {LAB[mk]:<9} Δ={mean:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  "
                      f"P={p:.0%}{flag}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase50_rates_recal", "league": "serie_a",
         "variant": "ricalibrazione_tassi_market_implied", "rho": RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED,
         "lam_level_mean": (float(np.mean(lvls["lam"])) if lvls["lam"] else None),
         "mu_level_mean": (float(np.mean(lvls["mu"])) if lvls["mu"] else None)},
        {"n_matches": int(n),
         **{f"{v}__{mk}": float(acc[v][mk].mean()) for v in VARIANTS for mk in MK},
         **{f"best__{mk}": best[mk] for mk in MK}, **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase50_rates_recal). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
