"""Fase 50 (diagnostico) — SCOMPOSIZIONE del nudge-μ sul market-implied: livello o coda?

Il Track A (mega-sweep) trova che il nudge stagionale di μ fittato sui λ,μ DEL
MERCATO da' un moltiplicatore alla 38a < 1 (k31≈0.94) — l'opposto del DC (Fase 48:
×1.072). Sul mercato il profilo potrebbe quindi lavorare come RICALIBRAZIONE GLOBALE
di μ (livello c0 < 0: il μ implicito nelle quote e' leggermente alto) piu' che come
correzione di coda. Prima di raccontare il guadagno GG come "effetto stagionale",
va scomposto. Quattro varianti sopra la φ35 (riferimento Fase 39), walk-forward:

  phi35            nessun nudge                          (riferimento)
  +level           basis [1]        — solo livello: μ' = μ·exp(c0)
  +tail            basis [coda34]   — solo coda: μ' = μ·exp(c2·max(0,md−34)/4)
  +k34             basis [1,s,coda] — completo (il migliore del Track A)

Se il guadagno sta quasi tutto in +level → e' una ricalibrazione del μ di mercato
(bias del devig/inversione), non un fenomeno stagionale. Se sta in +tail → e' la
coda. Riporta anche i moltiplicatori fittati (livello e alla 38a).

Uso:  python scripts/_run_fase50_mi_decomp.py    (cache db_base)
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
    s = (md_ - 19.5) / 18.5
    tail = np.maximum(0.0, md_ - 34.0) / 4.0
    return {"level": np.column_stack([one]),
            "tail": np.column_stack([tail]),
            "k34": np.column_stack([one, s, tail])}[name]


def _fit(name, mu, y, md_):
    X = _basis(name, md_)
    base = np.asarray(mu, float); y = np.asarray(y, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(X.shape[1]), jac=grad, method="L-BFGS-B").x


def _ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
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
    VARIANTS = ["phi35", "level", "tail", "k34"]
    acc = {v: [] for v in VARIANTS}
    mults = {"level_c0": [], "k34_at38": [], "tail_at38": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        ycu = ((cur.home_goals >= 1) & (cur.away_goals >= 1)).astype(float).values
        is_dr = (past.home_goals == past.away_goals).astype(float).values

        coefs = {n: _fit(n, past.mmu.values, past.away_goals.values,
                         past.matchday.values) for n in ("level", "tail", "k34")}
        mults["level_c0"].append(float(np.exp(coefs["level"][0])))
        mults["k34_at38"].append(float(np.exp(_basis("k34", [38.0]) @ coefs["k34"])[0]))
        mults["tail_at38"].append(float(np.exp(_basis("tail", [38.0]) @ coefs["tail"])[0]))

        for v in VARIANTS:
            if v == "phi35":
                mu_pa, mu_cu = past.mmu.values, cur.mmu.values
            else:
                mu_pa = past.mmu.values * np.exp(_basis(v, past.matchday.values) @ coefs[v])
                mu_cu = cur.mmu.values * np.exp(_basis(v, cur.matchday.values) @ coefs[v])
            phi0, kappa = mi.fit_balance_phi(past.mlam.values, mu_pa, is_dr, RHO)
            gg = np.empty(len(cur))
            for k in range(len(cur)):
                l, m = cur.mlam.values[k], mu_cu[k]
                M = mi.score_matrix(l, m, RHO,
                                    diag_inflation=mi.balance_phi(l, m, phi0, kappa))
                gg[k] = mi.derive_markets(M)["btts"]
            acc[v].append(_ll_bin(gg, ycu))
        print(f"  stagione {s} ({time.time()-t0:.0f}s)", flush=True)

    for v in acc:
        acc[v] = np.concatenate(acc[v])
    rng = np.random.default_rng(SEED)

    print("\n" + "=" * 88)
    print(f"FASE 50 (diagnostico) — scomposizione del nudge-μ sul market-implied+φ35 "
          f"(GG/NG, n={len(acc['phi35'])})")
    print(f"moltiplicatori medi: livello exp(c0)={np.mean(mults['level_c0']):.4f}   "
          f"coda(38a, solo-coda)={np.mean(mults['tail_at38']):.4f}   "
          f"completo(38a)={np.mean(mults['k34_at38']):.4f}")
    print("=" * 88)
    summary: dict = {"level_c0_mean": float(np.mean(mults["level_c0"])),
                     "tail_at38_mean": float(np.mean(mults["tail_at38"])),
                     "k34_at38_mean": float(np.mean(mults["k34_at38"]))}
    print(f"  {'variante':<10}{'GG log-loss':>13}{'Δ vs phi35':>12}{'CI95':>22}{'P(mig)':>8}")
    print(f"  {'phi35':<10}{acc['phi35'].mean():>13.4f}{'—':>12}")
    summary["phi35__gg"] = float(acc["phi35"].mean())
    for v in ("level", "tail", "k34"):
        mean, lo, hi, p = _boot(acc[v] - acc["phi35"], rng)
        flag = " ✓CI" if hi < 0 else ""
        print(f"  {'+'+v:<10}{acc[v].mean():>13.4f}{mean:>+12.4f}"
              f"   [{lo:+.4f},{hi:+.4f}]{p:>8.0%}{flag}")
        summary[f"{v}__gg"] = float(acc[v].mean())
        summary[f"{v}__delta"] = mean
        summary[f"{v}__ci_lo"] = lo; summary[f"{v}__ci_hi"] = hi
        summary[f"{v}__p"] = p

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase50_mi_decomp", "league": "serie_a",
         "variant": "nudge_mu_livello_vs_coda", "rho": RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(acc["phi35"])), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase50_mi_decomp). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
