"""Fase 24 — DC calcolato DAL MERCATO: lambda,mu impliciti -> mercati senza quote.

Idea nuova (nessuna fase precedente l'ha fatta): finora il DC stima lambda,mu dai
GOL; il mercato li stima meglio (batte il DC di +0.0165 sull'1X2). E se
INVERTISSIMO il mercato per ricavare i lambda,mu IMPLICITI nelle quote, e ci
facessimo girare sopra la matrice dei punteggi del DC?

Sui mercati CON quote (1X2, O/U) l'inversione riproduce il mercato -> gap ~0
banale, nessuna novita'. Il valore e' tutto nel DERIVARE i mercati che il book
NON prezza — sopra tutti il GG/NG (nessuna quota nei dati, l'unico mercato con
"spazio", principio 8). Se lambda,mu del mercato + struttura DC battono il nostro
GG/NG (0.6898) e la baseline (0.6871), abbiamo uno stimatore migliore usando
l'informazione superiore del mercato su un mercato non prezzato.

Metodo: per ogni partita, devig 1X2 + O/U -> probabilita' target; si trova
(lambda,mu) che le riproduce meglio via la matrice a Poisson indipendenti
(rho=0: il mercato 1X2+O/U non vincola rho). Da quella matrice si legge P(GG).
Confronto: GG/NG da mercato-impliciti vs DC-da-gol vs baseline, CI bootstrap.
Sensibilita': anche con un rho della diagonale (correzione dei punteggi bassi).

Uso:  python scripts/_run_dc_from_market.py     (6 backtest DC + inversione; minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics

TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
MAXG = 10
B, SEED = 10_000, 24
_K = np.arange(MAXG + 1)
_LOGFACT = gammaln(_K + 1.0)


def _worker(season):
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


def score_matrix(lam, mu, rho=0.0):
    ph = np.exp(_K * np.log(lam) - lam - _LOGFACT)
    pa = np.exp(_K * np.log(mu) - mu - _LOGFACT)
    M = np.outer(ph, pa)
    if rho:
        M[0, 0] *= 1.0 - lam * mu * rho
        M[0, 1] *= 1.0 + lam * rho
        M[1, 0] *= 1.0 + mu * rho
        M[1, 1] *= 1.0 - rho
        M = np.clip(M, 0.0, None)
    return M / M.sum()


def probs_from_matrix(M):
    pH = np.tril(M, -1).sum()
    pD = np.trace(M)
    pA = np.triu(M, 1).sum()
    i = _K.reshape(-1, 1); j = _K.reshape(1, -1)
    pOver = M[(i + j) >= 3].sum()
    pGG = M[1:, 1:].sum()
    return pH, pD, pA, pOver, pGG


def invert_market(pH, pD, pA, pOver, rho=0.0):
    """Trova (lambda,mu) che riproduce meglio le prob. di mercato (1X2 + O/U)."""
    def loss(x):
        lam, mu = x
        qH, qD, qA, qO, _ = probs_from_matrix(score_matrix(lam, mu, rho))
        return (qH - pH) ** 2 + (qD - pD) ** 2 + (qA - pA) ** 2 + (qO - pOver) ** 2
    # init: totale gol ~ da O/U, tilt ~ da 1X2
    tot0 = 2.5 + (pOver - 0.5) * 2.0
    tilt = np.clip(0.5 + (pH - pA) * 0.6, 0.15, 0.85)
    x0 = [max(0.2, tot0 * tilt), max(0.2, tot0 * (1 - tilt))]
    r = minimize(loss, x0, method="L-BFGS-B", bounds=[(0.1, 4.5), (0.1, 4.5)])
    return r.x


def ll_bin(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def main():
    with Pool(min(6, len(TEST_SEASONS))) as pool:
        dfs = dict(pool.map(_worker, TEST_SEASONS))
    all_m = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase24_dc_from_market", "league": "serie_a",
             "test_season": s, "variant": "dc_features",
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, experiment_log.compute_metrics(df), fp))

    # rho medio: usiamo un valore rappresentativo per la sensibilita' (Fase 18
    # diagnostica: rho DC ~ -0.06). 0 = Poisson indipendenti (primario).
    RHO_SENS = -0.06

    print("=" * 88)
    print("DC DAL MERCATO — GG/NG derivato dai lambda,mu impliciti nelle quote")
    print("log-loss GG/NG, piu' basso = meglio")
    print("=" * 88)
    print(f"  {'stag.':<7}{'mkt-impl':>10}{'mkt+rho':>10}{'DC-gol':>10}"
          f"{'base(in)':>10}{'Δ vs DC':>10}")
    d_all, dc_all = [], []
    gg_mkt, gg_mktr, gg_dc, gg_base = [], [], [], []
    for s in TEST_SEASONS:
        df = dfs[s]
        y = df["is_btts"].to_numpy().astype(int)
        p_impl, p_implr = [], []
        for r in df.itertuples():
            pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            pOver, _ = metrics.devig_binary(r.odds_over, r.odds_under)
            lam, mu = invert_market(pH, pD, pA, pOver, rho=0.0)
            p_impl.append(probs_from_matrix(score_matrix(lam, mu, 0.0))[4])
            lam2, mu2 = invert_market(pH, pD, pA, pOver, rho=RHO_SENS)
            p_implr.append(probs_from_matrix(score_matrix(lam2, mu2, RHO_SENS))[4])
        p_impl = np.array(p_impl); p_implr = np.array(p_implr)
        p_dc = df["m_btts"].to_numpy()
        ll_m = ll_bin(p_impl, y); ll_mr = ll_bin(p_implr, y)
        ll_d = ll_bin(p_dc, y); ll_b = ll_bin(np.full(len(y), y.mean()), y)
        d_all.append(ll_m - ll_d); dc_all.append(ll_d)
        gg_mkt.append(ll_m.mean()); gg_mktr.append(ll_mr.mean())
        gg_dc.append(ll_d.mean()); gg_base.append(ll_b.mean())
        print(f"  {s:<7}{ll_m.mean():>10.4f}{ll_mr.mean():>10.4f}{ll_d.mean():>10.4f}"
              f"{ll_b.mean():>10.4f}{ll_m.mean()-ll_d.mean():>+10.4f}")

    d = np.concatenate(d_all)
    rng = np.random.default_rng(SEED)
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    print("-" * 88)
    print(f"  {'MEDIA':<7}{np.mean(gg_mkt):>10.4f}{np.mean(gg_mktr):>10.4f}"
          f"{np.mean(gg_dc):>10.4f}{np.mean(gg_base):>10.4f}"
          f"{np.mean(gg_mkt)-np.mean(gg_dc):>+10.4f}")
    print(f"\n  GG/NG da mercato-impliciti vs DC-da-gol: Δ {d.mean():+.4f}  "
          f"CI95 [{lo:+.4f}, {hi:+.4f}]  P(mercato meglio)={float((m<0).mean()):.1%}")
    print(f"  Battono la baseline ({np.mean(gg_base):.4f})? "
          f"mkt-impl {np.mean(gg_mkt)<np.mean(gg_base)}, "
          f"DC-gol {np.mean(gg_dc)<np.mean(gg_base)}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase24_dc_from_market", "league": "serie_a",
         "variant": "gg_from_market_summary", "bootstrap_B": B,
         "bootstrap_seed": SEED, "rho_sens": RHO_SENS, "promoted_prior": 0.23},
        {"n_matches": int(len(d)),
         "gg_market_implied_logloss": float(np.mean(gg_mkt)),
         "gg_market_implied_rho_logloss": float(np.mean(gg_mktr)),
         "gg_dc_goals_logloss": float(np.mean(gg_dc)),
         "gg_baseline_logloss": float(np.mean(gg_base)),
         "delta_market_minus_dc": float(d.mean()),
         "ci_lo": float(lo), "ci_hi": float(hi),
         "p_market_better": float((m < 0).mean())}, fp))

    print("\nNota: su 1X2/O/U l'inversione riproduce il mercato (gap ~0 banale);")
    print("il valore e' derivare il GG/NG, che il book NON prezza, dai lambda,mu")
    print("del mercato. Se batte il DC-da-gol, e' informazione del mercato usata")
    print("su un mercato non prezzato (utile e non circolare).")


if __name__ == "__main__":
    main()
