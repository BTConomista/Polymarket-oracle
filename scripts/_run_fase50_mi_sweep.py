"""Fase 50 (Track A) — MEGA-SWEEP del motore market-implied: combo mai provate.

Le leve positive del progetto sul motore market-implied sono state validate una
alla volta, mai COMBINATE:
  - φ(|λ−μ|) sui λ,μ del mercato (Fase 39: miglior GG/NG, P 96%);
  - nudge stagionale del tasso-ospite μ (Fasi 48/49: GG/NG ~90-95%, validato pero'
    sui λ,μ del DC, MAI sui λ,μ del mercato);
  - power-devig (Fase 38: testato SOLO da solo, eta≈1 → neutro);
  - copula di Frank + φ (Fase 43: miglior punto-stima GG, pareggio statistico).

Griglia walk-forward (8 stagioni, test=ultime 7), tutte le combinazioni:

  devig    : prop (moltiplicativo) | pow (potenza, eta fittato LFO sull'1X2 passato)
  forma    : tau (ρ=−0.06) | phi35 (+φ(|λ−μ|) fittata LFO) | frank (θ=a+b|λ−μ| + φ)
  nudge μ  : none | knee31 (base Fase 48) | knee34 (finestra stretta Fase 49),
             coefficienti Poisson-MLE fittati LFO sui λ,μ DEL MERCATO (nuovo)

(la forma frank e' limitata a devig=prop, nudge∈{none,knee31}: e' il candidato di
punta della Fase 43, il resto della griglia frank costerebbe ore per un pareggio
statistico gia' noto). Mercati valutati per-riga: GG/NG, risultato esatto, multigol,
pareggio, O/U 2.5. Confronti chiave: ogni combo vs il riferimento phi35 (Fase 39),
bootstrap appaiato.

Uso:  python scripts/_run_fase50_mi_sweep.py    (usa i backtest in cache db_base)
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
from src.models import market_denoise as md          # noqa: E402
from src.models import copula_scores as cop          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 50
MAXG = mi.MAX_GOALS
MK = ["gg", "cs", "mg", "draw", "ou"]
LAB = {"gg": "GG/NG", "cs": "ris.esatto", "mg": "multigol",
       "draw": "pareggio", "ou": "O/U 2.5"}


# ------------------------------------------------------------------ dati --- #
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
    return _add_matchday(df)


def _invert(df, etas: dict[str, float]):
    """(λ,μ) impliciti per riga; l'1X2 e' devigato con l'eta della STAGIONE della
    riga (fittato walk-forward: eta=1 per la prima, senza look-ahead)."""
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        eta = etas.get(r.season, 1.0)
        if eta == 1.0:
            pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        else:
            pH, pD, pA = md.power_devig(r.odds_home, r.odds_draw, r.odds_away, eta)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    return lam, mu


# ------------------------------------------------------- nudge stagionale --- #
def _knee_basis(md_, knee: float):
    md_ = np.asarray(md_, float)
    s = (md_ - 19.5) / 18.5
    tail = np.maximum(0.0, md_ - knee) / (38.0 - knee)
    return np.column_stack([np.ones_like(md_), s, tail])


def _fit_nudge(mu, away_goals, md_, knee: float):
    """MLE Poisson (offset ln μ) del profilo stagionale del tasso-ospite,
    come Fase 48/49 ma sui λ,μ del MERCATO."""
    X = _knee_basis(md_, knee)
    base = np.asarray(mu, float); y = np.asarray(away_goals, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(3), jac=grad, method="L-BFGS-B").x


def _nudged(mu, md_, coef, knee):
    if coef is None:
        return np.asarray(mu, float)
    return np.asarray(mu, float) * np.exp(_knee_basis(md_, knee) @ coef)


# ------------------------------------------------------------- forma frank -- #
def _fit_phi_on(base_mats, lams, mus, is_draw):
    d_match = np.clip(np.array([np.trace(M) for M in base_mats]), 1e-9, 1 - 1e-9)
    bal = np.abs(lams - mus)

    def nll(p):
        phi = p[0] * np.exp(-p[1] * bal)
        return -np.sum(np.log1p(phi * is_draw) - np.log1p(phi * d_match))
    r = minimize(nll, [0.1, 1.0], method="L-BFGS-B",
                 bounds=[(0.0, 2.0), (0.0, 5.0)])
    return float(r.x[0]), float(r.x[1])


def _apply_phi(M, phi):
    if phi == 0:
        return M
    M = M.copy(); idx = np.arange(M.shape[0]); M[idx, idx] *= 1.0 + phi
    return M / M.sum()


# ------------------------------------------------------------- log-loss ----- #
def _row_ll(M, hg, ag):
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
    return out


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


# ------------------------------------------------------------------ main ---- #
KNEES = {"k31": 31.0, "k34": 34.0}
# (devig, forma, nudge) — frank limitato a prop × {none, k31} (vedi docstring).
VARIANTS = ([(dv, f, n) for dv in ("prop", "pow") for f in ("tau", "phi35")
             for n in ("none", "k31", "k34")]
            + [("prop", "frank", "none"), ("prop", "frank", "k31")])


def _vname(v):
    dv, f, n = v
    return f"{dv}-{f}" + ("" if n == "none" else f"+{n}")


def main():
    t0 = time.time()
    df = _load()
    seasons = [s for s in SEASONS if s in set(df.season)]
    test_seasons = seasons[1:]

    # eta del power-devig, walk-forward (fit sull'1X2 delle stagioni passate).
    etas_pow: dict[str, float] = {}
    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        odds = past[["odds_home", "odds_draw", "odds_away"]].to_numpy()
        etas_pow[s] = md.fit_power_eta(odds, past.result.tolist())

    print(f"inversione quote ({len(df)} righe x 2 devig)...", flush=True)
    lam_p, mu_p = _invert(df, {})
    lam_w, mu_w = _invert(df, etas_pow)
    df["lam_prop"], df["mu_prop"] = lam_p, mu_p
    df["lam_pow"], df["mu_pow"] = lam_w, mu_w
    print(f"  fatto in {time.time()-t0:.0f}s; eta medi {np.mean(list(etas_pow.values())):.3f}",
          flush=True)

    acc = {v: {m: [] for m in MK} for v in VARIANTS}
    fitted = {"phi": [], "nudge38": {}, "frank": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        hg_c = cur.home_goals.astype(int).values
        ag_c = cur.away_goals.astype(int).values
        md_c = cur.matchday.values

        # ---- fit walk-forward dei parametri, per devig e per nudge ---------- #
        params: dict = {}
        for dv in ("prop", "pow"):
            pl = past[f"lam_{dv}"].values; pm = past[f"mu_{dv}"].values
            phg = past.home_goals.values; pag = past.away_goals.values
            is_dr = (phg == pag).astype(float)
            for n in ("none", "k31", "k34"):
                coef = (None if n == "none"
                        else _fit_nudge(pm, pag, past.matchday.values, KNEES[n]))
                pm_n = _nudged(pm, past.matchday.values, coef, KNEES.get(n, 0.0))
                phi0, kappa = mi.fit_balance_phi(pl, pm_n, is_dr, RHO)
                params[(dv, n)] = (coef, phi0, kappa)
                if n != "none" and dv == "prop":
                    fitted["nudge38"].setdefault(n, []).append(
                        float(np.exp(_knee_basis([38.0], KNEES[n]) @ coef)[0]))
                if n == "none":
                    fitted["phi"].append((dv, phi0, kappa))
        # frank (solo prop): θ=a+b|λ−μ| + φ sopra la copula, per nudge none/k31
        frank_par: dict = {}
        pl = past.lam_prop.values
        phg = past.home_goals.values; pag = past.away_goals.values
        is_dr = (phg == pag).astype(float)
        for n in ("none", "k31"):
            coef = params[("prop", n)][0]
            pm_n = _nudged(past.mu_prop.values, past.matchday.values,
                           coef, KNEES.get(n, 0.0))
            a, b = cop.fit_theta_balance(pl, pm_n, phg, pag)
            base_fb = [cop.frank_matrix(pl[k], pm_n[k], a + b * abs(pl[k] - pm_n[k]))
                       for k in range(len(past))]
            fphi0, fkappa = _fit_phi_on(base_fb, pl, pm_n, is_dr)
            frank_par[n] = (a, b, fphi0, fkappa)
            if n == "none":
                fitted["frank"].append((a, b, fphi0, fkappa))

        # ---- valutazione della stagione di test ----------------------------- #
        for v in VARIANTS:
            dv, form, n = v
            lam_c = cur[f"lam_{dv}"].values
            coef, phi0, kappa = params[(dv, n)]
            mu_c = _nudged(cur[f"mu_{dv}"].values, md_c, coef, KNEES.get(n, 0.0))
            for k in range(len(cur)):
                l, m = lam_c[k], mu_c[k]
                if form == "tau":
                    M = mi.score_matrix(l, m, RHO)
                elif form == "phi35":
                    M = mi.score_matrix(l, m, RHO,
                                        diag_inflation=mi.balance_phi(l, m, phi0, kappa))
                else:                                   # frank_b + φ
                    a, b, fphi0, fkappa = frank_par[n]
                    M = _apply_phi(cop.frank_matrix(l, m, a + b * abs(l - m)),
                                   fphi0 * np.exp(-fkappa * abs(l - m)))
                r = _row_ll(M, hg_c[k], ag_c[k])
                for mk in MK:
                    acc[v][mk].append(r[mk])
        print(f"  stagione {s} valutata ({time.time()-t0:.0f}s)", flush=True)

    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.array(acc[v][mk])
    n_rows = len(acc[VARIANTS[0]]["gg"])
    rng = np.random.default_rng(SEED)

    # ------------------------------------------------------------- report --- #
    print("\n" + "=" * 100)
    print(f"FASE 50 (Track A) — mega-sweep market-implied, walk-forward "
          f"{len(test_seasons)} stagioni (n={n_rows})")
    print(f"eta power-devig medio: {np.mean(list(etas_pow.values())):.3f}; "
          f"nudge x38 medio: "
          + ", ".join(f"{k}={np.mean(vs):.3f}" for k, vs in fitted["nudge38"].items()))
    print("=" * 100)
    header = f"  {'variante':<18}" + "".join(f"{LAB[mk]:>12}" for mk in MK)
    print(header)
    best = {mk: min(VARIANTS, key=lambda v: acc[v][mk].mean()) for mk in MK}
    for v in VARIANTS:
        cells = "".join(
            f"{acc[v][mk].mean():>11.4f}" + ("*" if best[mk] == v else " ")
            for mk in MK)
        print(f"  {_vname(v):<18}" + cells)
    print("  (*) migliore del mercato-colonna")

    # Confronti chiave vs il riferimento phi35 (= Fase 39), bootstrap appaiato.
    REF = ("prop", "phi35", "none")
    print(f"\n  Δ vs riferimento {_vname(REF)} (Fase 39), bootstrap appaiato:")
    key_pairs = [v for v in VARIANTS if v != REF]
    summary: dict = {}
    for v in key_pairs:
        deltas = {mk: _boot(acc[v][mk] - acc[REF][mk], rng) for mk in MK}
        gg = deltas["gg"]
        flag = " ✓CI" if gg[2] < 0 else ""
        print(f"    {_vname(v):<18} GG Δ={gg[0]:+.4f} CI[{gg[1]:+.4f},{gg[2]:+.4f}] "
              f"P={gg[3]:.0%}{flag}   pareggio Δ={deltas['draw'][0]:+.4f} "
              f"(P={deltas['draw'][3]:.0%})   O/U Δ={deltas['ou'][0]:+.4f}")
        for mk in MK:
            mean, lo, hi, p = deltas[mk]
            summary[f"{_vname(v)}__{mk}_delta"] = mean
            summary[f"{_vname(v)}__{mk}_p"] = p
            if mk == "gg":
                summary[f"{_vname(v)}__gg_ci_lo"] = lo
                summary[f"{_vname(v)}__gg_ci_hi"] = hi

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase50_mi_sweep", "league": "serie_a",
         "variant": "mi_mega_sweep_devig_x_forma_x_nudge",
         "rho": RHO, "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED,
         "eta_pow_mean": float(np.mean(list(etas_pow.values()))),
         "variants": [_vname(v) for v in VARIANTS]},
        {"n_matches": int(n_rows),
         **{f"{_vname(v)}__{mk}": float(acc[v][mk].mean())
            for v in VARIANTS for mk in MK},
         **{f"best__{mk}": _vname(best[mk]) for mk in MK},
         **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase50_mi_sweep). Tempo totale {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
