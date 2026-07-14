"""Fase 43 — Spremere la dipendenza dei punteggi: batteria di forme (copule incluse).

Migliorare il Poisson bivariato (Fase 42, solo correlazione positiva, sovra-disperde
i totali) provando strutture di dipendenza piu' flessibili sui marginali del MERCATO:

  1. τ  (Dixon-Coles rho=-0.06)                 [attuale base]
  2. φ35 (τ + inflazione diagonale |λ−μ|)        [attuale migliore, Fase 39]
  3. biv (Poisson bivariato, λ3)                 [Fase 42]
  4. frank_g  (copula di Frank, θ globale)       [NUOVO: dipendenza di QUALSIASI segno]
  5. frank_b  (copula di Frank, θ = a + b·|λ−μ|) [NUOVO: dipendenza condizionata]
  6. frank_b + φ  (copula + inflazione diagonale)[NUOVO: dipendenza flessibile + pareggi]

Tutti i parametri fittati WALK-FORWARD (stagioni passate) e applicati al test.
Mercati sensibili: GG/NG, risultato esatto, multigol, pareggio, O/U 2.5 (sanity totali).

Uso:  python scripts/_run_copula.py    (usa i backtest in cache)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402
from src.models import market_implied as mi        # noqa: E402
from src.models import bivariate_poisson as bp     # noqa: E402
from src.models import copula_scores as cop        # noqa: E402
from scipy.optimize import minimize                # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO_MI = -0.06
B, SEED = 10_000, 43
MAXG = mi.MAX_GOALS


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
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO_MI)
    df["mlam"], df["mmu"] = lam, mu
    return df


def _apply_phi(M, phi):
    if phi == 0:
        return M
    M = M.copy(); idx = np.arange(M.shape[0]); M[idx, idx] *= 1.0 + phi
    return M / M.sum()


def _fit_phi_on(base_mats, lams, mus, is_draw, w):
    """Fit (φ0,κ) dell'inflazione diagonale |λ−μ| dato un insieme di matrici base."""
    d_match = np.clip(np.array([np.trace(M) for M in base_mats]), 1e-9, 1 - 1e-9)
    bal = np.abs(lams - mus)

    def nll(p):
        phi = p[0] * np.exp(-p[1] * bal)
        return -np.sum(w * (np.log1p(phi * is_draw) - np.log1p(phi * d_match)))
    r = minimize(nll, [0.1, 1.0], method="L-BFGS-B", bounds=[(0.0, 2.0), (0.0, 5.0)])
    return float(r.x[0]), float(r.x[1])


def _mkt_ll(mats, hg, ag):
    y_gg = ((hg >= 1) & (ag >= 1)).astype(float)
    tot = hg + ag; y_mg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    y_ov = (tot >= 3).astype(float)
    hc, ac = np.minimum(hg, MAXG), np.minimum(ag, MAXG)
    y_dr = (hg == ag).astype(float)
    gg = cs = mg = dr = ov = None
    GG, CS, MG, DR, OV = [], [], [], [], []
    for k, M in enumerate(mats):
        d = mi.derive_markets(M)
        p = np.clip(d["btts"], 1e-15, 1 - 1e-15)
        GG.append(-(y_gg[k] * np.log(p) + (1 - y_gg[k]) * np.log(1 - p)))
        CS.append(-np.log(max(M[hc[k], ac[k]], 1e-15)))
        MG.append(-np.log(np.clip([d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]][y_mg[k]], 1e-15, 1)))
        pdr = np.clip(d["draw"], 1e-15, 1 - 1e-15)
        DR.append(-(y_dr[k] * np.log(pdr) + (1 - y_dr[k]) * np.log(1 - pdr)))
        po = np.clip(d["over_2.5"], 1e-15, 1 - 1e-15)
        OV.append(-(y_ov[k] * np.log(po) + (1 - y_ov[k]) * np.log(1 - po)))
    return dict(gg=np.array(GG), cs=np.array(CS), mg=np.array(MG), draw=np.array(DR), ou=np.array(OV))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    rng = np.random.default_rng(SEED)
    VARIANTS = ["tau", "phi35", "biv", "frank_g", "frank_b", "frank_b_phi"]
    MK = ["gg", "cs", "mg", "draw", "ou"]
    acc = {v: {m: [] for m in MK} for v in VARIANTS}
    params = {"lam3": [], "theta_g": [], "ab": [], "phi": []}

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]; cur = df[df.season == s]
        pl, pm = past.mlam.values, past.mmu.values
        phg, pag = past.home_goals.values, past.away_goals.values
        is_draw = (phg == pag).astype(float); w = np.ones(len(past))
        # fit parametri sulle stagioni passate
        l3 = bp.fit_lam3(pl, pm, phg, pag)
        phi0, kappa = mi.fit_balance_phi(pl, pm, is_draw, RHO_MI)
        th_g = cop.fit_theta(pl, pm, phg, pag)
        a, b = cop.fit_theta_balance(pl, pm, phg, pag)
        # φ sopra la copula: costruisci basi copula del training, poi fit φ
        base_fb = [cop.frank_matrix(pl[k], pm[k], a + b * abs(pl[k] - pm[k])) for k in range(len(past))]
        cphi0, ckappa = _fit_phi_on(base_fb, pl, pm, is_draw, w)
        params["lam3"].append(l3); params["theta_g"].append(th_g)
        params["ab"].append((a, b)); params["phi"].append((phi0, kappa))

        ml, mm = cur.mlam.values, cur.mmu.values
        hg, ag = cur.home_goals.values, cur.away_goals.values
        for k in range(len(cur)):
            mats = {
                "tau": mi.score_matrix(ml[k], mm[k], RHO_MI),
                "phi35": mi.score_matrix(ml[k], mm[k], RHO_MI,
                         diag_inflation=mi.balance_phi(ml[k], mm[k], phi0, kappa)),
                "biv": bp.bp_matrix(ml[k], mm[k], l3),
                "frank_g": cop.frank_matrix(ml[k], mm[k], th_g),
                "frank_b": cop.frank_matrix(ml[k], mm[k], a + b * abs(ml[k] - mm[k])),
            }
            fb = mats["frank_b"]
            mats["frank_b_phi"] = _apply_phi(fb, cphi0 * np.exp(-ckappa * abs(ml[k] - mm[k])))
            for v, M in mats.items():
                r = _mkt_ll([M], np.array([hg[k]]), np.array([ag[k]]))
                for mk in MK:
                    acc[v][mk].append(r[mk][0])
    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.array(acc[v][mk])

    print("=" * 92)
    print("FASE 43 — batteria di forme di dipendenza sui marginali del mercato (walk-forward)")
    print(f"parametri medi: λ3={np.mean(params['lam3']):.3f}  θ_glob={np.mean(params['theta_g']):+.3f}  "
          f"frank_b a={np.mean([x[0] for x in params['ab']]):+.3f} b={np.mean([x[1] for x in params['ab']]):+.3f}")
    print("=" * 92)
    lab = {"gg": "GG/NG", "cs": "ris.esatto", "mg": "multigol", "draw": "pareggio", "ou": "O/U 2.5"}
    print(f"  {'mercato':<12}" + "".join(f"{v:>12}" for v in VARIANTS))
    best = {}
    for mk in MK:
        vals = {v: acc[v][mk].mean() for v in VARIANTS}
        bv = min(vals, key=vals.get)
        best[mk] = bv
        print(f"  {lab[mk]:<12}" + "".join(
            (f"{vals[v]:>11.4f}" + ("*" if v == bv else " ")) for v in VARIANTS))
    # confronto chiave: la miglior copula vs φ35, sul GG e risultato esatto
    print("\n  Δ (miglior copula − φ35), bootstrap appaiato:")
    for mk in ("gg", "cs", "mg"):
        cand = min(["frank_g", "frank_b", "frank_b_phi"], key=lambda v: acc[v][mk].mean())
        mean, lo, hi, p = _boot(acc[cand][mk] - acc["phi35"][mk], rng)
        print(f"    {lab[mk]:<11} {cand:>12}: Δ={mean:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  P(<φ35)={p:.0%}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase43_copula", "league": "serie_a", "variant": "dependence_battery",
         "rho_mi": RHO_MI, "theta_g_mean": float(np.mean(params["theta_g"])),
         "frank_b_a": float(np.mean([x[0] for x in params["ab"]])),
         "frank_b_b": float(np.mean([x[1] for x in params["ab"]])),
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(acc["tau"]["gg"])),
         **{f"{v}__{mk}": float(acc[v][mk].mean()) for v in VARIANTS for mk in MK},
         **{f"best__{mk}": best[mk] for mk in MK}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase43_copula).")


if __name__ == "__main__":
    main()
