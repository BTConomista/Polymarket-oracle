"""Fase 80 — La catena GG/NG del market-implied (φ35 + knee34) su Premier e
La Liga, con la Serie A rifatta sulla STESSA finestra come riferimento.

Perche' questo test (test C dello STUDIO_PREMIER_LIGA §5):
  - la voce #1 della panchina (GG/NG: market-implied → nudge-μ knee34 → φ(|λ−μ|),
    Fase 50: GG 0.6810, Δ −0.0010, P 98%) ha la promozione CONDIZIONATA proprio
    a "il guadagno riappare sul fronte per-lega di Premier/Liga (mai provato)";
  - il GG/NG e' l'unico mercato senza quote nei dati → senza tetto di
    efficienza dimostrato (principio §1.8): ogni miglioramento li' e' spendibile;
  - dopo la Fase 79 il prior e' asimmetrico: su Premier φ0 (path DC) fitta ZERO
    → aspettativa dichiarata PRIMA: la φ35 di mercato non paghera' in Premier,
    potrebbe pagare in Liga (fit-DC ≈ Serie A).

Metodo (replica ESATTA della Fase 50, ramo devig=prop — pow/frank chiusi):
  - per lega: righe con chiusura 1X2+O/U completa, stagioni 1920→2526
    (la chiusura O/U esiste solo dal 1920, Fase 73); walk-forward con la
    prima stagione solo-training → 6 stagioni di test 2021→2526;
  - inversione (λ,μ) dalla chiusura devigata (ρ=−0.06, cache su disco);
  - varianti: tau (liscia) | phi35 | k34 (nudge-μ) | phi35+k34, parametri
    fittati LEAVE-FUTURE-OUT sulle stagioni passate (mai la corrente);
  - metriche per-riga su GG/NG (headline), pareggio, ris. esatto, multigol,
    O/U 2.5; Δ vs tau con bootstrap appaiato B=10.000; regola: CI95<0.
  - le COSTANTI fittate per lega (φ0, κ, boost-38ª) sono parte del risultato
    (principio: valori per-lega se i backtest li chiedono, §7).

Uso:  python scripts/_run_fase80_ggng_mi_league.py     (~10-15 min, cache)
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
SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
LEAGUES = ["serie_a", "premier_league", "la_liga"]
RHO = -0.06
KNEE = 34.0
B, SEED = 10_000, 80
MAXG = mi.MAX_GOALS
MK = ["gg", "draw", "cs", "mg", "ou"]
LAB = {"gg": "GG/NG", "draw": "pareggio", "cs": "ris.esatto",
       "mg": "multigol", "ou": "O/U 2.5"}
VARIANTS = ["tau", "phi35", "k34", "phi35_k34"]


# ------------------------------------------------------------------ dati --- #
def _add_matchday(df):
    """Giornata approssimata dall'ordine cronologico (identica alla Fase 50)."""
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


def _load(league: str) -> pd.DataFrame:
    df = loader.load_league(league)
    df = df[df["season"].astype(str).isin(SEASONS)].copy()
    df["season"] = df["season"].astype(str)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over25", "odds_under25"]].to_numpy()).all(axis=1)
    df = df[ok].reset_index(drop=True)
    return _add_matchday(df)


def _invert(df: pd.DataFrame, league: str) -> pd.DataFrame:
    fp = CACHE / f"implied_rates80_{league}.csv"
    if fp.exists():
        cached = pd.read_csv(fp, parse_dates=["date"])
        if len(cached) == len(df):
            df["lam"], df["mu"] = cached["lam"].values, cached["mu"].values
            return df
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    df["lam"], df["mu"] = lam, mu
    CACHE.mkdir(parents=True, exist_ok=True)
    df[["date", "season", "home_team", "away_team", "lam", "mu"]].to_csv(fp, index=False)
    return df


# ---------------------------------------------- nudge stagionale (Fase 50) -- #
def _knee_basis(md_, knee: float = KNEE):
    md_ = np.asarray(md_, float)
    s = (md_ - 19.5) / 18.5
    tail = np.maximum(0.0, md_ - knee) / (38.0 - knee)
    return np.column_stack([np.ones_like(md_), s, tail])


def _fit_nudge(mu, away_goals, md_):
    X = _knee_basis(md_)
    base = np.asarray(mu, float); y = np.asarray(away_goals, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(3), jac=grad, method="L-BFGS-B").x


def _nudged(mu, md_, coef):
    if coef is None:
        return np.asarray(mu, float)
    return np.asarray(mu, float) * np.exp(_knee_basis(md_) @ coef)


# ------------------------------------------------------------- log-loss ----- #
def _row_ll(M, hg, ag):
    d = mi.derive_markets(M)
    out = {}
    y_gg = float(hg >= 1 and ag >= 1)
    p = min(max(d["btts"], 1e-15), 1 - 1e-15)
    out["gg"] = -(y_gg * np.log(p) + (1 - y_gg) * np.log(1 - p))
    y_dr = float(hg == ag)
    pdr = min(max(d["draw"], 1e-15), 1 - 1e-15)
    out["draw"] = -(y_dr * np.log(pdr) + (1 - y_dr) * np.log(1 - pdr))
    out["cs"] = -np.log(max(M[min(hg, MAXG), min(ag, MAXG)], 1e-15))
    tot = hg + ag
    pmg = [d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]][0 if tot <= 1 else (1 if tot <= 3 else 2)]
    out["mg"] = -np.log(max(pmg, 1e-15))
    y_ov = float(tot >= 3)
    po = min(max(d["over_2.5"], 1e-15), 1 - 1e-15)
    out["ou"] = -(y_ov * np.log(po) + (1 - y_ov) * np.log(1 - po))
    return out


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


# ------------------------------------------------------------------ main ---- #
def run_league(league: str, rng) -> None:
    t0 = time.time()
    df = _load(league)
    print(f"\ninversione quote {league} ({len(df)} righe)...", flush=True)
    df = _invert(df, league)
    print(f"  fatto in {time.time()-t0:.0f}s", flush=True)

    seasons = [s for s in SEASONS if s in set(df.season)]
    acc = {v: {m: [] for m in MK} for v in VARIANTS}
    fitted = {"phi0": [], "kappa": [], "phi0_k34": [], "kappa_k34": [],
              "boost38": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        pl, pm = past.lam.values, past.mu.values
        is_dr = (past.home_goals.values == past.away_goals.values).astype(float)

        coef = _fit_nudge(pm, past.away_goals.values, past.matchday.values)
        pm_n = _nudged(pm, past.matchday.values, coef)
        phi0, kappa = mi.fit_balance_phi(pl, pm, is_dr, RHO)
        phi0n, kappan = mi.fit_balance_phi(pl, pm_n, is_dr, RHO)
        fitted["phi0"].append(phi0); fitted["kappa"].append(kappa)
        fitted["phi0_k34"].append(phi0n); fitted["kappa_k34"].append(kappan)
        fitted["boost38"].append(float(np.exp(_knee_basis([38.0]) @ coef)[0]))

        mu_n = _nudged(cur.mu.values, cur.matchday.values, coef)
        hg = cur.home_goals.astype(int).values
        ag = cur.away_goals.astype(int).values
        for k in range(len(cur)):
            l, m0, mn = cur.lam.values[k], cur.mu.values[k], mu_n[k]
            mats = {
                "tau": mi.score_matrix(l, m0, RHO),
                "phi35": mi.score_matrix(
                    l, m0, RHO, diag_inflation=mi.balance_phi(l, m0, phi0, kappa)),
                "k34": mi.score_matrix(l, mn, RHO),
                "phi35_k34": mi.score_matrix(
                    l, mn, RHO, diag_inflation=mi.balance_phi(l, mn, phi0n, kappan)),
            }
            for v, M in mats.items():
                for mk, ll in _row_ll(M, hg[k], ag[k]).items():
                    acc[v][mk].append(ll)

    n = len(acc["tau"]["gg"])
    print("=" * 96)
    print(f"FASE 80 — {league.upper()}  (n={n}, {len(seasons)-1} stagioni test; "
          f"GG baseline-freq in-sample rif.)")
    print("=" * 96)
    summary: dict = {}
    for v in VARIANTS:
        summary[v] = {}
        line = f"  {v:<11}"
        for mk in MK:
            ll = float(np.mean(acc[v][mk]))
            summary[v][f"{mk}_ll"] = ll
            line += f"  {LAB[mk]} {ll:.4f}"
        print(line)
    print()
    for v in VARIANTS[1:]:
        line = f"  Δ {v:<10} vs tau:"
        for mk in MK:
            d = np.array(acc[v][mk]) - np.array(acc["tau"][mk])
            mean, lo, hi, p = _boot(d, rng)
            summary[v][f"{mk}_delta"] = mean
            summary[v][f"{mk}_ci"] = [lo, hi]
            summary[v][f"{mk}_p"] = p
            flag = "*" if hi < 0 else " "
            line += f"  {mk} {mean:+.4f} (P{p:.0%}){flag}"
        print(line)

    print(f"\n  costanti fittate LFO ({len(fitted['phi0'])} stagioni):")
    print(f"    phi0 (senza nudge)  {['%.3f' % v for v in fitted['phi0']]}  "
          f"media {np.mean(fitted['phi0']):.3f}")
    print(f"    kappa               {['%.2f' % v for v in fitted['kappa']]}  "
          f"media {np.mean(fitted['kappa']):.2f}")
    print(f"    phi0 (con k34)      media {np.mean(fitted['phi0_k34']):.3f}   "
          f"kappa media {np.mean(fitted['kappa_k34']):.2f}")
    print(f"    boost-μ alla 38ª    {['%.3f' % v for v in fitted['boost38']]}  "
          f"media {np.mean(fitted['boost38']):.3f}")

    all_m = loader.load_league(league)
    fp = experiment_log.data_fingerprint(all_m)
    for v in VARIANTS:
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase80_ggng_mi_league", "league": league, "variant": v,
             "seasons": SEASONS, "rho": RHO, "knee": KNEE},
            {"n_matches": n, **summary[v],
             "phi0_mean": float(np.mean(fitted["phi0"])),
             "kappa_mean": float(np.mean(fitted["kappa"])),
             "phi0_k34_mean": float(np.mean(fitted["phi0_k34"])),
             "boost38_mean": float(np.mean(fitted["boost38"]))},
            fp))


def main() -> None:
    rng = np.random.default_rng(SEED)
    for league in LEAGUES:
        run_league(league, rng)
    print("\nRun registrati in experiments/runs.jsonl (source=fase80_ggng_mi_league).")


if __name__ == "__main__":
    main()
