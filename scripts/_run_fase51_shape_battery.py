"""Fase 51 (A) — Batteria di FORME mai provate: double-Poisson, Rue-Salvesen, zero-inflazione.

L'audit delle fasi (Fase 51) trova tre estensioni classiche a 1 parametro mai
testate nel progetto:

  1. **double-Poisson (Efron 1986)** — marginali ∝ Poisson(λ)^θ rinormalizzati e
     ri-scalati per PRESERVARE la media. θ>1 = SOTTO-dispersione, θ<1 = sovra.
     La Fase 27 aveva testato solo la binomiale negativa, che copre SOLO la
     sovra-dispersione (rigettata): l'altra metà dell'asse non era testabile con
     quella famiglia. I gol condizionati a tassi ben stimati sono spesso un filo
     sotto-dispersi: qui si fa il test.
  2. **Rue-Salvesen (2000)** — "le squadre giocano al livello dell'avversario":
     smorzamento della differenza di forza, λ' = λ·exp(−γΔ), μ' = μ·exp(+γΔ) con
     Δ = (ln λ − ln μ)/2. γ>0 avvicina i tassi (più pareggi/equilibrio), γ<0 li
     allarga. L'aggiustamento storico della famiglia DC, mai provato.
  3. **zero-inflazione dello 0-0** — massa extra esplicita sul solo 0-0:
     M[0,0]·(1+z), rinormalizzata. Il ρ tocca i 4 punteggi bassi e la φ35 tutta
     la diagonale; lo 0-0 da solo (famiglia NG/clean-sheet) mai.

Tutte fittate LEAVE-FUTURE-OUT sui tassi del MERCATO (il miglior motore, Fase 41),
da sole e COMPOSTE con la φ35 (φ rifittata sulla base di ciascuna forma).
Riferimenti: τ pura (Fase 26) e φ35 (Fase 39). Mercati: GG/NG, risultato esatto,
multigol, pareggio, O/U 2.5, 1X2. Walk-forward 8 stagioni (test = ultime 7).

Uso:  python scripts/_run_fase51_shape_battery.py    (cache db_base)
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
MK = ["gg", "cs", "mg", "draw", "ou", "x2"]
LAB = {"gg": "GG/NG", "cs": "ris.esatto", "mg": "multigol", "draw": "pareggio",
       "ou": "O/U 2.5", "x2": "1X2"}
_OI = {"H": 0, "D": 1, "A": 2}


# ------------------------------------------------------------------ dati --- #
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


# ------------------------------------------- double-Poisson (Efron 1986) --- #
def _dp_pmf(rates: np.ndarray, theta: float) -> np.ndarray:
    """PMF (N, MAXG+1) double-Poisson MEAN-PRESERVING: q_k ∝ Poisson(c·r)^θ
    rinormalizzata, con c risolto per riga (bisezione vettoriale) perché la
    media resti r. θ=1 → Poisson esatta (c=1)."""
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


def _matrices(lam, mu, rho, qh=None, qa=None):
    """Matrici (N, 11, 11) dai marginali (Poisson di default, o double-Poisson
    passati) con la correzione ρ di Dixon-Coles sui 4 punteggi bassi."""
    if qh is None:
        qh = _dp_pmf(lam, 1.0)
    if qa is None:
        qa = _dp_pmf(mu, 1.0)
    M = qh[:, :, None] * qa[:, None, :]
    M[:, 0, 0] *= 1.0 - lam * mu * rho
    M[:, 0, 1] *= 1.0 + lam * rho
    M[:, 1, 0] *= 1.0 + mu * rho
    M[:, 1, 1] *= 1.0 - rho
    M = np.clip(M, 0.0, None)
    return M / M.sum(axis=(1, 2), keepdims=True)


def _joint_ll(M, hg, ag):
    n = np.arange(len(hg))
    return float(np.mean(np.log(np.clip(M[n, hg, ag], 1e-15, None))))


def _fit_theta(lam, mu, hg, ag):
    def nll(theta):
        M = _matrices(lam, mu, RHO, _dp_pmf(lam, theta), _dp_pmf(mu, theta))
        return -_joint_ll(M, hg, ag)
    r = minimize_scalar(nll, bounds=(0.6, 1.8), method="bounded",
                        options={"xatol": 1e-3})
    return float(r.x)


# ------------------------------------------------- Rue-Salvesen (2000) ----- #
def _rs_rates(lam, mu, gamma):
    delta = 0.5 * (np.log(lam) - np.log(mu))
    return lam * np.exp(-gamma * delta), mu * np.exp(gamma * delta)


def _fit_gamma(lam, mu, hg, ag):
    def nll(gamma):
        l2, m2 = _rs_rates(lam, mu, gamma)
        return -float(np.mean(hg * np.log(l2) - l2 + ag * np.log(m2) - m2))
    r = minimize_scalar(nll, bounds=(-0.3, 0.5), method="bounded",
                        options={"xatol": 1e-4})
    return float(r.x)


# ------------------------------------------------- zero-inflazione 0-0 ----- #
def _fit_z(M00, Mobs, is00):
    """MLE di z: ll_i = ln(M_obs·(1+z·[0-0])) − ln(1+z·M_00). Chiusa data la
    matrice base (bastano M[0,0] e M[oss.] per riga)."""
    def nll(z):
        return -float(np.mean(np.log(Mobs * (1.0 + z * is00))
                              - np.log1p(z * M00)))
    r = minimize_scalar(nll, bounds=(-0.3, 1.0), method="bounded",
                        options={"xatol": 1e-4})
    return float(r.x)


def _apply_z(M, z):
    M = M.copy()
    M[:, 0, 0] *= 1.0 + z
    return M / M.sum(axis=(1, 2), keepdims=True)


# ------------------------------------------------------------- phi35 ------- #
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


# ------------------------------------------------------------- log-loss ---- #
def _mkt_ll(M, hg, ag, res):
    n = np.arange(len(hg))
    i = _K.reshape(-1, 1); j = _K.reshape(1, -1); tot = i + j
    out = {}
    p_gg = M[:, 1:, 1:].sum(axis=(1, 2))
    y_gg = ((hg >= 1) & (ag >= 1)).astype(float)
    p = np.clip(p_gg, 1e-15, 1 - 1e-15)
    out["gg"] = -(y_gg * np.log(p) + (1 - y_gg) * np.log(1 - p))
    out["cs"] = -np.log(np.clip(M[n, np.minimum(hg, MAXG), np.minimum(ag, MAXG)], 1e-15, None))
    m01 = M[:, tot <= 1].sum(1); m23 = M[:, (tot >= 2) & (tot <= 3)].sum(1)
    m4p = M[:, tot >= 4].sum(1)
    ymg = np.where(hg + ag <= 1, 0, np.where(hg + ag <= 3, 1, 2))
    pmg = np.choose(ymg, [m01, m23, m4p])
    out["mg"] = -np.log(np.clip(pmg, 1e-15, None))
    pD = np.trace(M, axis1=1, axis2=2)
    y_dr = (hg == ag).astype(float)
    p = np.clip(pD, 1e-15, 1 - 1e-15)
    out["draw"] = -(y_dr * np.log(p) + (1 - y_dr) * np.log(1 - p))
    pOv = M[:, tot >= 3].sum(1)
    y_ov = ((hg + ag) >= 3).astype(float)
    p = np.clip(pOv, 1e-15, 1 - 1e-15)
    out["ou"] = -(y_ov * np.log(p) + (1 - y_ov) * np.log(1 - p))
    pH = np.tril(np.ones((MAXG + 1, MAXG + 1)), -1)
    ph = (M * pH[None]).sum(axis=(1, 2)); pa = (M * pH.T[None]).sum(axis=(1, 2))
    P3 = np.clip(np.column_stack([ph, pD, pa]), 1e-15, 1)
    yi = np.array([_OI[o] for o in res])
    out["x2"] = -np.log(P3[n, yi])
    return out


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


VARIANTS = ["tau", "phi35", "dp", "dp_phi", "rs", "rs_phi", "zi", "zi_phi"]


def main():
    t0 = time.time()
    df = _load()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in SEASONS if s in set(df.season)]
    acc = {v: {mk: [] for mk in MK} for v in VARIANTS}
    pars = {"theta": [], "gamma": [], "z": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        pl, pm = past.mlam.values, past.mmu.values
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        is_dr = (phg == pag).astype(float)
        cl, cm = cur.mlam.values, cur.mmu.values
        chg = cur.home_goals.astype(int).values
        cag = cur.away_goals.astype(int).values
        cres = cur.result.values

        # --- fit dei 3 parametri di forma sul passato --------------------- #
        theta = _fit_theta(pl, pm, phg, pag)
        gamma = _fit_gamma(pl, pm, phg, pag)
        Mp_tau = _matrices(pl, pm, RHO)
        n_p = np.arange(len(past))
        z = _fit_z(Mp_tau[:, 0, 0],
                   Mp_tau[n_p, np.minimum(phg, MAXG), np.minimum(pag, MAXG)],
                   ((phg == 0) & (pag == 0)).astype(float))
        pars["theta"].append(theta); pars["gamma"].append(gamma); pars["z"].append(z)

        # --- basi del passato (per il fit della phi35 su ciascuna) -------- #
        rl, rm = _rs_rates(pl, pm, gamma)
        bases_past = {
            "tau": (Mp_tau, pl, pm),
            "dp": (_matrices(pl, pm, RHO, _dp_pmf(pl, theta), _dp_pmf(pm, theta)), pl, pm),
            "rs": (_matrices(rl, rm, RHO), rl, rm),
            "zi": (_apply_z(Mp_tau, z), pl, pm),
        }
        phis = {b: _fit_phi_on(Mb, lb, mb, is_dr)
                for b, (Mb, lb, mb) in bases_past.items()}

        # --- matrici della stagione di test ------------------------------- #
        rlc, rmc = _rs_rates(cl, cm, gamma)
        Mc_tau = _matrices(cl, cm, RHO)
        bases_cur = {
            "tau": (Mc_tau, cl, cm),
            "dp": (_matrices(cl, cm, RHO, _dp_pmf(cl, theta), _dp_pmf(cm, theta)), cl, cm),
            "rs": (_matrices(rlc, rmc, RHO), rlc, rmc),
            "zi": (_apply_z(Mc_tau, z), cl, cm),
        }
        mats = {
            "tau": bases_cur["tau"][0],
            "phi35": _apply_phi(Mc_tau, cl, cm, *phis["tau"]),
            "dp": bases_cur["dp"][0],
            "dp_phi": _apply_phi(bases_cur["dp"][0], cl, cm, *phis["dp"]),
            "rs": bases_cur["rs"][0],
            "rs_phi": _apply_phi(bases_cur["rs"][0], rlc, rmc, *phis["rs"]),
            "zi": bases_cur["zi"][0],
            "zi_phi": _apply_phi(bases_cur["zi"][0], cl, cm, *phis["zi"]),
        }
        for v, M in mats.items():
            r = _mkt_ll(M, chg, cag, cres)
            for mk in MK:
                acc[v][mk].append(r[mk])
        print(f"  stagione {s} (θ={theta:.3f} γ={gamma:+.3f} z={z:+.3f}; "
              f"{time.time()-t0:.0f}s)", flush=True)

    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.concatenate(acc[v][mk])
    rng = np.random.default_rng(SEED)
    n = len(acc["tau"]["gg"])

    print("\n" + "=" * 104)
    print(f"FASE 51 (A) — batteria di forme mai provate sui tassi del mercato (n={n})")
    print(f"parametri medi walk-forward: θ={np.mean(pars['theta']):.3f} "
          f"(θ>1 = sotto-dispersione)   γ_RS={np.mean(pars['gamma']):+.3f}   "
          f"z_00={np.mean(pars['z']):+.3f}")
    print("=" * 104)
    print(f"  {'variante':<10}" + "".join(f"{LAB[mk]:>12}" for mk in MK))
    best = {mk: min(VARIANTS, key=lambda v: acc[v][mk].mean()) for mk in MK}
    for v in VARIANTS:
        print(f"  {v:<10}" + "".join(
            f"{acc[v][mk].mean():>11.4f}" + ("*" if best[mk] == v else " ") for mk in MK))
    print("\n  Δ vs phi35 (riferimento Fase 39), bootstrap appaiato:")
    summary: dict = {"theta_mean": float(np.mean(pars["theta"])),
                     "gamma_mean": float(np.mean(pars["gamma"])),
                     "z_mean": float(np.mean(pars["z"]))}
    for v in ("dp", "dp_phi", "rs", "rs_phi", "zi", "zi_phi"):
        for mk in ("gg", "draw", "x2"):
            mean, lo, hi, p = _boot(acc[v][mk] - acc["phi35"][mk], rng)
            summary[f"{v}__{mk}_delta"] = mean; summary[f"{v}__{mk}_p"] = p
            summary[f"{v}__{mk}_ci_lo"] = lo; summary[f"{v}__{mk}_ci_hi"] = hi
        gg = (summary[f"{v}__gg_delta"], summary[f"{v}__gg_ci_lo"],
              summary[f"{v}__gg_ci_hi"], summary[f"{v}__gg_p"])
        print(f"    {v:<8} GG Δ={gg[0]:+.4f} CI[{gg[1]:+.4f},{gg[2]:+.4f}] P={gg[3]:.0%}"
              f"   pareggio Δ={summary[f'{v}__draw_delta']:+.4f} (P={summary[f'{v}__draw_p']:.0%})"
              f"   1X2 Δ={summary[f'{v}__x2_delta']:+.4f} (P={summary[f'{v}__x2_p']:.0%})")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase51_shape_battery", "league": "serie_a",
         "variant": "double_poisson_rue_salvesen_zero_inflation",
         "rho": RHO, "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n),
         **{f"{v}__{mk}": float(acc[v][mk].mean()) for v in VARIANTS for mk in MK},
         **{f"best__{mk}": best[mk] for mk in MK}, **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase51_shape_battery). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
