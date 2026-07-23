"""Fase 81 — MEGA-SWEEP del motore market-implied PER-LEGA: la mappa completa
delle costanti (ρ, θ, φ0×κ, knee) su Serie A, Premier e La Liga.

Idea (utente): "spremere questi dati con un mega backtest che copra quante più
opzioni possibili per un singolo modello, assegnando vari valori a una singola
costante". Il modello giusto è il TITOLARE (market-implied): non ha fit
walk-forward costosi, quindi si può tracciare la CURVA DI RISPOSTA completa di
ogni costante, per lega e per mercato — decine di valori, non i 2-3 punti
delle fasi passate. Le curve dicono (a) dove sta l'ottimo per lega, (b) quanto
è piatta la valle (= quanto conta davvero la costante), (c) se le leghe
chiedono numeri diversi (§7).

Gli assi (un asse alla volta, il resto al riferimento ρ=−0.06, θ=1, φ=0):
  ρ     ∈ {−0.14 … +0.02} (9 valori)  — correzione punteggi bassi; RICHIEDE
          la ri-inversione delle quote per ogni ρ (coerenza inversione↔matrice)
  θ     ∈ {1.00 … 1.30} (7 valori)    — double-Poisson mean-preserving (F51)
  φ0×κ  ∈ {0…0.7}×{0.5…5} (31 combo)  — boost-pareggio φ0·exp(−κ|λ−μ|) (F39)
  knee  ∈ {25,28,31,34,37} (5 valori) — profilo stagionale del tasso-ospite,
          coefficienti SEMPRE fittati leave-future-out (come F80)

Metriche per-riga su 6 mercati: 1X2, GG/NG, pareggio, ris. esatto, multigol,
O/U 2.5. Stagioni 1920→2526 (chiusure reali); la 1920 è solo-training/storia,
le metriche sono sulle 6 stagioni di test 2021→2526 (finestra standard).

ONESTÀ della selezione: una variante a costante FISSA è un modello legittimo
valutato out-of-sample, ma SCEGLIERE a posteriori il minimo della curva è
selezione in-sample. Perciò per ogni asse si valuta anche il selettore
walk-forward "lfo": per ogni stagione di test sceglie il valore col log-loss
migliore sulle stagioni PASSATE (1920 inclusa). Se nemmeno il selettore paga,
la costante di riferimento è già ottima (valle piatta).

Uso:  python scripts/_run_fase81_mega_sweep_mi.py     (~10-15 min; cache ρ)
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
RHO_REF = -0.06
B, SEED = 10_000, 81
MAXG = mi.MAX_GOALS
MK = ["x2", "gg", "draw", "cs", "mg", "ou"]
LAB = {"x2": "1X2", "gg": "GG/NG", "draw": "pareggio", "cs": "ris.esatto",
       "mg": "multigol", "ou": "O/U 2.5"}

RHOS = [-0.22, -0.18, -0.14, -0.12, -0.10, -0.08, -0.06, -0.04, -0.02, 0.00, 0.02]
THETAS = [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50]
PHI0S = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7]
KAPPAS = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
KNEES = [25.0, 28.0, 31.0, 34.0, 37.0]


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


def _load(league: str) -> pd.DataFrame:
    df = loader.load_league(league)
    df = df[df["season"].astype(str).isin(SEASONS)].copy()
    df["season"] = df["season"].astype(str)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over25", "odds_under25"]].to_numpy()).all(axis=1)
    return _add_matchday(df[ok].reset_index(drop=True))


def _invert_rho(df: pd.DataFrame, league: str, rho: float):
    """(λ,μ) impliciti con correzione ρ coerente tra inversione e matrice."""
    fp = CACHE / f"implied_rates81_{league}_rho{rho:+.2f}.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(df):
            return c["lam"].values, c["mu"].values
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, rho)
    CACHE.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


# ------------------------------------------------------ nudge (come F80) --- #
def _knee_basis(md_, knee: float):
    md_ = np.asarray(md_, float)
    s = (md_ - 19.5) / 18.5
    tail = np.maximum(0.0, md_ - knee) / (38.0 - knee)
    return np.column_stack([np.ones_like(md_), s, tail])


def _fit_nudge(mu, away_goals, md_, knee: float):
    X = _knee_basis(md_, knee)
    base = np.asarray(mu, float); y = np.asarray(away_goals, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(3), jac=grad, method="L-BFGS-B").x


# ------------------------------------------------------------- log-loss ----- #
def _row_ll(M, hg, ag):
    d = mi.derive_markets(M)
    out = {}
    pH = float(np.tril(M, -1).sum()); pD = float(np.trace(M))
    pA = float(np.triu(M, 1).sum())
    p3 = max([pH, pD, pA][0 if hg > ag else (1 if hg == ag else 2)], 1e-15)
    out["x2"] = -np.log(p3)
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


def _eval_variant(df, lam, mu, rho, theta=None, phi0=0.0, kappa=0.0):
    """LL per-riga (tutte le righe, anche 1920: servono al selettore lfo)."""
    hg = df.home_goals.astype(int).values
    ag = df.away_goals.astype(int).values
    out = {mk: np.zeros(len(df)) for mk in MK}
    for k in range(len(df)):
        infl = mi.balance_phi(lam[k], mu[k], phi0, kappa) if phi0 > 0 else 0.0
        M = mi.score_matrix(lam[k], mu[k], rho,
                            diag_inflation=infl,
                            dp_theta=(theta if theta and theta != 1.0 else None))
        for mk, v in _row_ll(M, hg[k], ag[k]).items():
            out[mk][k] = v
    return out


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def _lfo_pick(lls: dict, values: list, df, ref_value, mk: str):
    """Selettore walk-forward: per ogni stagione di test usa il valore col
    LL medio migliore sulle stagioni passate (prima stagione → riferimento)."""
    season = df.season.values
    pick_ll = np.zeros(len(df))
    picks = {}
    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = np.isin(season, SEASONS[:i])
        cur = season == s
        best = ref_value if not past.any() else min(
            values, key=lambda v: lls[v][mk][past].mean())
        picks[s] = best
        pick_ll[cur] = lls[best][mk][cur]
    return pick_ll, picks


def _report_axis(name, values, lls, df, ref_value, rng, league, extra=None):
    """Tabella LL (test) per valore × mercato + Δ del best e del lfo vs rif."""
    test = np.isin(df.season.values, SEASONS[1:])
    print(f"\n  --- asse {name} (rif. {ref_value}) ---")
    hdr = f"    {'valore':<12}" + "".join(f"{LAB[mk]:>11}" for mk in MK)
    print(hdr)
    curves = {}
    for v in values:
        row = f"    {str(v):<12}"
        curves[str(v)] = {}
        for mk in MK:
            ll = float(lls[v][mk][test].mean())
            curves[str(v)][mk] = ll
            row += f"{ll:>11.4f}"
        print(row)
    summary = {"curves": curves, "best": {}, "lfo": {}}
    for mk in MK:
        best_v = min(values, key=lambda v: lls[v][mk][test].mean())
        d_best = lls[best_v][mk][test] - lls[ref_value][mk][test]
        mb, lob, hib, pb = _boot(d_best, rng) if best_v != ref_value else (0, 0, 0, 0)
        pick_ll, picks = _lfo_pick(lls, values, df, ref_value, mk)
        d_lfo = pick_ll[test] - lls[ref_value][mk][test]
        ml, lol, hil, pl_ = _boot(d_lfo, rng)
        summary["best"][mk] = {"value": best_v, "delta": mb, "ci": [lob, hib], "p": pb}
        summary["lfo"][mk] = {"delta": ml, "ci": [lol, hil], "p": pl_,
                              "picks": picks}
        star_b = "*" if hib < 0 else " "
        star_l = "*" if hil < 0 else " "
        print(f"      {LAB[mk]:<11} best={best_v!s:<6} Δ{mb:+.4f} (P{pb:.0%}){star_b}"
              f"  | lfo Δ{ml:+.4f} (P{pl_:.0%}){star_l} picks={list(picks.values())}")
    if extra:
        summary.update(extra)
    return summary


# ------------------------------------------------------------------ main ---- #
def run_league(league: str, rng) -> None:
    t0 = time.time()
    df = _load(league)
    n_test = int(np.isin(df.season.values, SEASONS[1:]).sum())
    print("\n" + "=" * 100)
    print(f"FASE 81 — {league.upper()}  ({len(df)} righe, {n_test} di test 2021→2526)")
    print("=" * 100)

    # ---- asse ρ (ri-inversione per ogni valore) ---------------------------- #
    lls_rho = {}
    for rho in RHOS:
        lam, mu = _invert_rho(df, league, rho)
        lls_rho[rho] = _eval_variant(df, lam, mu, rho)
    sum_rho = _report_axis("ρ", RHOS, lls_rho, df, RHO_REF, rng, league)

    lam, mu = _invert_rho(df, league, RHO_REF)

    # ---- asse θ (double-Poisson, ρ=rif) ------------------------------------ #
    lls_th = {th: _eval_variant(df, lam, mu, RHO_REF, theta=th) for th in THETAS}
    sum_th = _report_axis("θ", THETAS, lls_th, df, 1.00, rng, league)

    # ---- griglia φ0×κ (ρ=rif) --------------------------------------------- #
    combos = [(0.0, 0.0)] + [(p, k) for p in PHI0S[1:] for k in KAPPAS]
    lls_phi = {c: _eval_variant(df, lam, mu, RHO_REF, phi0=c[0], kappa=c[1])
               for c in combos}
    sum_phi = _report_axis("φ0×κ", combos, lls_phi, df, (0.0, 0.0), rng, league)

    # ---- asse knee (nudge-μ, coefficienti SEMPRE LFO) ---------------------- #
    season = df.season.values
    lls_kn = {}
    boost38 = {}
    for kn in KNEES:
        mu_n = mu.copy()
        b38 = []
        for i, s in enumerate(SEASONS):
            if i == 0:
                continue
            past = np.isin(season, SEASONS[:i]); cur = season == s
            coef = _fit_nudge(mu[past], df.away_goals.values[past],
                              df.matchday.values[past], kn)
            mu_n[cur] = mu[cur] * np.exp(_knee_basis(df.matchday.values[cur], kn) @ coef)
            b38.append(float(np.exp(_knee_basis([38.0], kn) @ coef)[0]))
        boost38[kn] = float(np.mean(b38))
        lls_kn[kn] = _eval_variant(df, lam, mu_n, RHO_REF)
    lls_kn["none"] = lls_rho[RHO_REF]
    sum_kn = _report_axis("knee", KNEES + ["none"], lls_kn, df, "none", rng,
                          league, extra={"boost38": boost38})
    print(f"    boost-μ 38ª per knee: " + "  ".join(
        f"k{int(k)}:{v:.3f}" for k, v in boost38.items()))

    # ---- registro ---------------------------------------------------------- #
    all_m = loader.load_league(league)
    fp = experiment_log.data_fingerprint(all_m)
    for axis, summ in [("rho", sum_rho), ("theta", sum_th),
                       ("phi_grid", sum_phi), ("knee", sum_kn)]:
        # le chiavi-tuple della griglia φ non sono serializzabili → stringhe
        summ = {k: ({str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v)
                for k, v in summ.items()}
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase81_mega_sweep_mi", "league": league, "axis": axis,
             "seasons": SEASONS, "rho_ref": RHO_REF},
            {"n_test": n_test, **summ}, fp))
    print(f"\n  {league}: completata in {time.time()-t0:.0f}s")


def main() -> None:
    rng = np.random.default_rng(SEED)
    for league in LEAGUES:
        run_league(league, rng)
    print("\nRun registrati in experiments/runs.jsonl (source=fase81_mega_sweep_mi).")


if __name__ == "__main__":
    main()
