"""Fase 39 — Market-implied + φ(|λ−μ|): la sintesi dei due risultati positivi.

Fase 26: i λ,μ del MERCATO (dalle quote 1X2+O/U) prezzano i mercati sui gol meglio
dei nostri. Fase 35: il pareggio e' un fenomeno di EQUILIBRIO, e φ(λ,μ)=φ0·exp(−κ|λ−μ|)
lo cattura. Combinazione mai provata (la Fase 27 aveva testato la forma — ρ, φ
costante, binomiale negativa — ma NON il φ condizionato all'equilibrio): applicare la
struttura-pareggio della Fase 35 ai λ,μ superiori del mercato, per i mercati che il
book NON prezza (GG/NG, risultato esatto, multigol).

Metodo: per ogni partita si inverte 1X2+O/U → (λ,μ). (φ0,κ) sono fittati
LEAVE-FUTURE-OUT sui λ,μ del mercato e i pareggi reali delle stagioni passate, poi
applicati come diag_inflation alla matrice della stagione di test. Confronto raw
(φ=0, = Fase 26) vs balance-φ, bootstrap appaiato per-riga.

Uso:  python scripts/_run_mi_balance.py    (usa i backtest in cache; solo inversioni)
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

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 39
MAXG = mi.MAX_GOALS


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    return df[ok].reset_index(drop=True)


def _implied(df):
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    return lam, mu


def _markets_ll(df, lam, mu, phi0, kappa):
    """log-loss per-riga di GG/NG, risultato esatto, multigol per la variante
    (phi0,kappa) (phi0=0 -> raw Fase 26)."""
    gg, cs, mg = [], [], []
    hg = df.home_goals.to_numpy(); ag = df.away_goals.to_numpy()
    y_gg = ((hg >= 1) & (ag >= 1)).astype(float)
    tot = hg + ag
    y_mg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    for k in range(len(df)):
        phi = mi.balance_phi(lam[k], mu[k], phi0, kappa) if phi0 else 0.0
        M = mi.score_matrix(lam[k], mu[k], RHO, diag_inflation=phi)
        d = mi.derive_markets(M)
        p = np.clip(d["btts"], 1e-15, 1 - 1e-15)
        gg.append(-(y_gg[k] * np.log(p) + (1 - y_gg[k]) * np.log(1 - p)))
        hc, ac = min(int(hg[k]), MAXG), min(int(ag[k]), MAXG)
        cs.append(-np.log(max(M[hc, ac], 1e-15)))
        pmg = np.clip([d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]][y_mg[k]], 1e-15, 1)
        mg.append(-np.log(pmg))
    return np.array(gg), np.array(cs), np.array(mg)


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    df["lam"], df["mu"] = _implied(df)
    df["is_draw"] = (df.home_goals == df.away_goals).astype(float)

    raw = {"gg": [], "cs": [], "mg": []}
    bal = {"gg": [], "cs": [], "mg": []}
    params = []
    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]
        cur = df[df.season == s]
        phi0, kappa = mi.fit_balance_phi(past.lam.values, past.mu.values,
                                         past.is_draw.values, RHO)
        params.append((phi0, kappa))
        g0, c0, m0 = _markets_ll(cur, cur.lam.values, cur.mu.values, 0.0, 0.0)
        g1, c1, m1 = _markets_ll(cur, cur.lam.values, cur.mu.values, phi0, kappa)
        raw["gg"].append(g0); raw["cs"].append(c0); raw["mg"].append(m0)
        bal["gg"].append(g1); bal["cs"].append(c1); bal["mg"].append(m1)
    for d in (raw, bal):
        for k in d:
            d[k] = np.concatenate(d[k])

    rng = np.random.default_rng(SEED)
    n = len(raw["gg"])
    print("=" * 84)
    print(f"FASE 39 — market-implied + φ(|λ−μ|) sui mercati non prezzati (LFO 5 stag., n={n})")
    print(f"φ0,κ medi: {np.mean([p[0] for p in params]):.3f}, {np.mean([p[1] for p in params]):.3f}")
    print("=" * 84)
    print(f"  {'mercato':<16}{'raw (Fase26)':>14}{'+ φ(|λ−μ|)':>14}{'Δ':>10}{'CI95 Δ':>22}{'P(mig)':>8}")
    summary = {}
    labels = {"gg": "GG/NG", "cs": "risultato esatto", "mg": "multigol"}
    for k in ("gg", "cs", "mg"):
        mean, lo, hi, pmig = _boot(bal[k] - raw[k], rng)
        verd = "VIVA" if hi < 0 else ("promett." if mean < 0 else "")
        print(f"  {labels[k]:<16}{raw[k].mean():>14.4f}{bal[k].mean():>14.4f}{mean:>+10.4f}"
              f"   [{lo:+.4f}, {hi:+.4f}]{pmig:>8.0%} {verd}")
        summary[f"{k}_raw"] = float(raw[k].mean()); summary[f"{k}_bal"] = float(bal[k].mean())
        summary[f"{k}_delta"] = mean; summary[f"{k}_ci_lo"] = lo; summary[f"{k}_ci_hi"] = hi

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase39_mi_balance", "league": "serie_a", "variant": "market_implied_balance_phi",
         "rho": RHO, "bootstrap_B": B, "bootstrap_seed": SEED,
         "phi0_mean": float(np.mean([p[0] for p in params])),
         "kappa_mean": float(np.mean([p[1] for p in params]))},
        {"n_matches": n, **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase39_mi_balance).")


if __name__ == "__main__":
    main()
