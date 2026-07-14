"""Fase 42 — Poisson bivariato: la correlazione esplicita aiuta i mercati sui gol?

Il bivariato (src/models/bivariate_poisson.py) aggiunge una covarianza λ3 tra i gol
delle due squadre, preservando i marginali (λ, μ) dati. E' l'unica famiglia di
modelli sui punteggi mai implementata. Test sui mercati che dipendono dalla
CORRELAZIONE (GG/NG, risultato esatto, multigol, pareggio), confrontando la forma
bivariata contro quelle attuali, su DUE sorgenti di marginali:

  - marginali del DC (gol+xG):  DC-τ (rho, attuale)   vs  DC-biv (λ3)
  - marginali del MERCATO:      mkt-rho (attuale) / mkt-φ35 (Fase 39) / mkt-biv (λ3)

λ3 e' fittato WALK-FORWARD (sulle stagioni passate) e applicato alla stagione di
test. Attesa onesta (Fasi 12b/18): nel calcio la correlazione e' ≈0/negativa e il
bivariato puo' solo aggiungere correlazione POSITIVA -> λ3→0 probabile. Ma e' l'unico
modo di dimostrarlo coi nostri dati.

Uso:  python scripts/_run_bivariate.py    (usa i backtest in cache)
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

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO_DC, RHO_MI = -0.05, -0.06
B, SEED = 10_000, 42
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


def _market_ll(mats, hg, ag):
    """log-loss per-riga di GG/NG, risultato esatto, multigol, pareggio (1X2 draw)."""
    y_gg = ((hg >= 1) & (ag >= 1)).astype(float)
    tot = hg + ag; y_mg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
    y_draw = (hg == ag).astype(float)
    gg, cs, mg, dr = [], [], [], []
    for k, M in enumerate(mats):
        d = mi.derive_markets(M)
        p = np.clip(d["btts"], 1e-15, 1 - 1e-15)
        gg.append(-(y_gg[k] * np.log(p) + (1 - y_gg[k]) * np.log(1 - p)))
        cs.append(-np.log(max(M[hc[k], ac[k]], 1e-15)))
        pmg = np.clip([d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]][y_mg[k]], 1e-15, 1)
        mg.append(-np.log(pmg))
        pd_ = np.clip(d["draw"], 1e-15, 1 - 1e-15)
        dr.append(-(y_draw[k] * np.log(pd_) + (1 - y_draw[k]) * np.log(1 - pd_)))
    return dict(gg=np.array(gg), cs=np.array(cs), mg=np.array(mg), draw=np.array(dr))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    rng = np.random.default_rng(SEED)
    # accumulatori per-riga (stagioni 1..5, walk-forward)
    acc = {v: {m: [] for m in ("gg", "cs", "mg", "draw")}
           for v in ("dc_rho", "dc_biv", "mkt_rho", "mkt_phi", "mkt_biv")}
    l3dc, l3mkt, phis = [], [], []

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]
        cur = df[df.season == s]
        hg, ag = cur.home_goals.to_numpy(), cur.away_goals.to_numpy()
        # fit λ3 (DC e mercato) e φ35 (mercato) sulle stagioni passate
        l3_dc = bp.fit_lam3(past.exp_home_goals.values, past.exp_away_goals.values,
                            past.home_goals.values, past.away_goals.values)
        l3_mk = bp.fit_lam3(past.mlam.values, past.mmu.values,
                            past.home_goals.values, past.away_goals.values)
        phi0, kappa = mi.fit_balance_phi(past.mlam.values, past.mmu.values,
                                         (past.home_goals == past.away_goals).values, RHO_MI)
        l3dc.append(l3_dc); l3mkt.append(l3_mk); phis.append((phi0, kappa))

        dl, dm = cur.exp_home_goals.values, cur.exp_away_goals.values
        ml, mm = cur.mlam.values, cur.mmu.values
        mats = {
            "dc_rho": [mi.score_matrix(dl[k], dm[k], RHO_DC) for k in range(len(cur))],
            "dc_biv": [bp.bp_matrix(dl[k], dm[k], l3_dc) for k in range(len(cur))],
            "mkt_rho": [mi.score_matrix(ml[k], mm[k], RHO_MI) for k in range(len(cur))],
            "mkt_phi": [mi.score_matrix(ml[k], mm[k], RHO_MI,
                        diag_inflation=mi.balance_phi(ml[k], mm[k], phi0, kappa))
                        for k in range(len(cur))],
            "mkt_biv": [bp.bp_matrix(ml[k], mm[k], l3_mk) for k in range(len(cur))],
        }
        for v, M in mats.items():
            r = _market_ll(M, hg, ag)
            for mk in ("gg", "cs", "mg", "draw"):
                acc[v][mk].append(r[mk])
    for v in acc:
        for mk in acc[v]:
            acc[v][mk] = np.concatenate(acc[v][mk])

    print("=" * 80)
    print("FASE 42 — Poisson bivariato (correlazione λ3) sui mercati sensibili")
    print(f"λ3 medio: DC={np.mean(l3dc):.3f}  mercato={np.mean(l3mkt):.3f}   "
          f"(0 = nessuna correlazione aggiunta)")
    print("=" * 80)
    labels = {"gg": "GG/NG", "cs": "risultato esatto", "mg": "multigol", "draw": "pareggio"}

    print("\n  MARGINALI DEL DC:")
    print(f"  {'mercato':<18}{'DC-τ (rho)':>12}{'DC-biv (λ3)':>14}{'Δ':>10}")
    for mk in ("gg", "cs", "mg", "draw"):
        a, b = acc["dc_rho"][mk], acc["dc_biv"][mk]
        print(f"  {labels[mk]:<18}{a.mean():>12.4f}{b.mean():>14.4f}{(b-a).mean():>+10.4f}")

    print("\n  MARGINALI DEL MERCATO:")
    print(f"  {'mercato':<18}{'mkt-rho':>10}{'mkt-φ35':>10}{'mkt-biv':>10}{'Δ biv-rho':>12}{'CI95':>20}")
    summ = {}
    for mk in ("gg", "cs", "mg", "draw"):
        a, ph, b = acc["mkt_rho"][mk], acc["mkt_phi"][mk], acc["mkt_biv"][mk]
        mean, lo, hi, _ = _boot(b - a, rng)
        print(f"  {labels[mk]:<18}{a.mean():>10.4f}{ph.mean():>10.4f}{b.mean():>10.4f}"
              f"{mean:>+12.4f}   [{lo:+.4f},{hi:+.4f}]")
        summ[mk] = dict(mkt_rho=float(a.mean()), mkt_phi=float(ph.mean()),
                        mkt_biv=float(b.mean()), delta_biv_rho=mean)

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase42_bivariate", "league": "serie_a", "variant": "bivariate_poisson",
         "rho_dc": RHO_DC, "rho_mi": RHO_MI, "lam3_dc_mean": float(np.mean(l3dc)),
         "lam3_mkt_mean": float(np.mean(l3mkt)), "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(acc["mkt_rho"]["gg"])),
         **{f"{mk}__{k}": v for mk, r in summ.items() for k, v in r.items()}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase42_bivariate).")


if __name__ == "__main__":
    main()
