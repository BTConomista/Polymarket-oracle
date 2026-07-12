"""Fase 18 — Rho DINAMICO: la correzione sui punteggi bassi per-partita.

Il rho di Dixon-Coles e' un numero unico per tutte le partite. Ipotesi
strutturale (l'ultima mai provata sul pareggio): la correlazione dei punteggi
bassi dipende dalla partita — un match da 1.8 gol attesi ha dinamiche di
0-0/1-1 diverse da uno da 3.5. Fase 18: rho_match = rho + rho_slope*(lam+mu -
centro), con rho_slope stimato nella verosimiglianza (vedi dixon_coles.py).

REGOLA DI DECISIONE (dichiarata PRIMA di vedere i numeri, disciplina Fase 17):
si adotta SOLO se il CI95 bootstrap del Δ pooled esclude lo zero. Dopo ~30
test sulle stesse 6 stagioni, un CI che sfiora lo zero = "non concluso".

Uso:  python scripts/_run_dynrho.py     (12 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics
from src.models.dixon_coles import DixonColesModel
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
PC = ["m_home", "m_draw", "m_away"]
B, SEED = 10_000, 18


def _worker(task):
    variant, season = task            # "base" | "dynrho"
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"],
                      dynamic_rho=(variant == "dynrho"), verbose=False)
    df["season"] = season
    return variant, season, df


def ll_rows(probs, outcomes):
    idx = [{"H": 0, "D": 1, "A": 2}[o] for o in outcomes]
    return -np.log(np.clip(probs[np.arange(len(outcomes)), idx], 1e-15, 1.0))


def main():
    tasks = [(v, s) for v in ("base", "dynrho") for s in SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    dfs = {(v, s): df for v, s, df in res}

    all_matches = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_matches)
    for (v, s), df in dfs.items():
        cfg = {"source": "fase18_dynrho", "league": "serie_a", "test_season": s,
               **{k: x for k, x in CFG.items() if k != "promoted_prior"},
               "promoted_prior": 0.23, "dynamic_rho": v == "dynrho"}
        experiment_log.append_run(experiment_log.make_record(
            cfg, experiment_log.compute_metrics(df), fp))

    # Diagnostico strutturale: segno/entita' di rho_slope su un fit full-data
    # per stagione (fino alla fine della stagione precedente, come il primo
    # fit del walk-forward): il parametro esiste davvero o e' al bound?
    print("=" * 88)
    print("RHO DINAMICO — diagnostico del parametro (fit al via di ogni stagione)")
    print("=" * 88)
    for s in SEASONS:
        start = all_matches.loc[all_matches["season"] == s, "date"].min()
        m = DixonColesModel(half_life_days=CFG["half_life_days"],
                            shrinkage=CFG["shrinkage"],
                            shots_blend=CFG["shots_blend"],
                            blend_signal=CFG["blend_signal"],
                            promoted_prior=CFG["promoted_prior"],
                            dynamic_rho=True)
        m.fit(all_matches, as_of_date=start)
        print(f"  {s}: rho={m.rho:+.4f}  rho_slope={m.rho_slope:+.4f}  "
              f"centro={m.rho_center:.2f} gol")

    # Confronto walk-forward: Δ per stagione + pooled con CI bootstrap.
    print("\n" + "=" * 88)
    print("RHO DINAMICO vs UFFICIALE — 1X2 log-loss walk-forward; Δ<0 = meglio")
    print("=" * 88)
    print(f"  {'stag.':<7}{'base':>10}{'dinamico':>10}{'Δ':>10}")
    diffs = []
    for s in SEASONS:
        b, d = dfs[("base", s)], dfs[("dynrho", s)]
        assert (b["home_team"].to_numpy() == d["home_team"].to_numpy()).all()
        out = b["result"].tolist()
        lb = ll_rows(b[PC].to_numpy(), out)
        ld = ll_rows(d[PC].to_numpy(), out)
        diffs.append(ld - lb)
        print(f"  {s:<7}{lb.mean():>10.4f}{ld.mean():>10.4f}{ld.mean()-lb.mean():>+10.4f}")
    d_all = np.concatenate(diffs)
    rng = np.random.default_rng(SEED)
    means = d_all[rng.integers(0, len(d_all), (B, len(d_all)))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    print(f"\n  POOLED (n={len(d_all)}): Δ {d_all.mean():+.4f}  "
          f"CI95 [{lo:+.4f}, {hi:+.4f}]  P(Δ<0)={float((means < 0).mean()):.1%}")
    adopted = hi < 0
    print(f"  REGOLA PRE-DICHIARATA: adozione solo se CI95 < 0 -> "
          f"{'ADOTTARE' if adopted else 'NON adottare'}.")

    # O/U (secondario): il rho tocca i punteggi bassi, quindi anche l'under.
    d_ou = []
    for s in SEASONS:
        b, d = dfs[("base", s)], dfs[("dynrho", s)]
        y = b["is_over"].to_numpy().astype(float)
        pb = np.clip(b["m_over"].to_numpy(), 1e-15, 1 - 1e-15)
        pd_ = np.clip(d["m_over"].to_numpy(), 1e-15, 1 - 1e-15)
        d_ou.append(-(y * np.log(pd_) + (1 - y) * np.log(1 - pd_))
                    + (y * np.log(pb) + (1 - y) * np.log(1 - pb)))
    d_ou = np.concatenate(d_ou)
    means_ou = d_ou[rng.integers(0, len(d_ou), (B, len(d_ou)))].mean(axis=1)
    lo_ou, hi_ou = np.percentile(means_ou, [2.5, 97.5])
    print(f"  O/U 2.5 (secondario): Δ {d_ou.mean():+.4f}  "
          f"CI95 [{lo_ou:+.4f}, {hi_ou:+.4f}]")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase18_dynrho", "league": "serie_a",
         "variant": "delta_summary", "bootstrap_B": B, "bootstrap_seed": SEED,
         **{k: x for k, x in CFG.items() if k != "promoted_prior"},
         "promoted_prior": 0.23},
        {"n_matches": int(len(d_all)),
         "x2_delta_mean": float(d_all.mean()),
         "x2_delta_ci_lo": float(lo), "x2_delta_ci_hi": float(hi),
         "x2_delta_p_neg": float((means < 0).mean()),
         "ou_delta_mean": float(d_ou.mean()),
         "ou_delta_ci_lo": float(lo_ou), "ou_delta_ci_hi": float(hi_ou)}, fp))


if __name__ == "__main__":
    main()
