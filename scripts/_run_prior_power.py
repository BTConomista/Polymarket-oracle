"""Fase 19 — Potenza statistica sul prior neopromosse: finestra estesa a 8 stagioni.

La Fase 17 ha mostrato che il Δ del prior (V4-V3, -0.0010) ha CI95
[-0.0025, +0.0004]: probabile (~93%) ma non conclusivo. Non perche' l'effetto
oscilli, ma perche' 6 stagioni di partite-promosse sono poche. Qui si estende
la finestra di test alle stagioni 1819 e 1920 (mai usate: il dataset parte dal
1718, che resta solo-training) -> 8 stagioni, ~3040 partite, ~50% in piu' di
partite-promosse. Stesso bootstrap appaiato della Fase 17.

CAVEAT DICHIARATO: delta=0.23 e' la stima storica della Fase 7, che include
anche le stagioni 2018-2020 -> per le due stagioni aggiunte il valore del
prior non e' leave-future-out. E' un test di POTENZA sull'effetto della
config adottata, non una nuova stima onesta di delta. La domanda e': con
il 33% di dati in piu', il CI si stringe abbastanza da concludere?

Uso:  python scripts/_run_prior_power.py     (16 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log
from scripts.backtest import promoted_teams, run_backtest

SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
BASE = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75, blend_signal="xg")
PC = ["m_home", "m_draw", "m_away"]
B, SEED = 10_000, 19


def _worker(task):
    version, season = task            # "V4" (prior 0.23) | "V3" (senza)
    prior = (0.23, 0.23) if version == "V4" else None
    df = run_backtest("serie_a", season, BASE["half_life_days"],
                      shrinkage=BASE["shrinkage"], shots_blend=BASE["shots_blend"],
                      blend_signal=BASE["blend_signal"], promoted_prior=prior,
                      verbose=False)
    df["season"] = season
    return version, season, df


def ll_rows(probs, outcomes):
    idx = [{"H": 0, "D": 1, "A": 2}[o] for o in outcomes]
    return -np.log(np.clip(probs[np.arange(len(outcomes)), idx], 1e-15, 1.0))


def boot(d, rng):
    means = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float((means < 0).mean())


def main():
    tasks = [(v, s) for v in ("V4", "V3") for s in SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    dfs = {(v, s): df for v, s, df in res}

    all_matches = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_matches)
    for (v, s), df in dfs.items():
        cfg = {"source": "fase19_prior_power", "league": "serie_a",
               "test_season": s, **BASE,
               "promoted_prior": 0.23 if v == "V4" else None}
        experiment_log.append_run(experiment_log.make_record(
            cfg, experiment_log.compute_metrics(df), fp))

    print("=" * 88)
    print("PRIOR NEOPROMOSSE, FINESTRA ESTESA (8 stagioni) — Δ = V4-V3; Δ<0 = aiuta")
    print("=" * 88)
    print(f"  {'stag.':<7}{'V3 base':>10}{'V4 prior':>10}{'Δ':>10}"
          f"{'Δ promosse':>13}{'n prom.':>9}")
    d_all, d_prom = [], []
    for s in SEASONS:
        v4, v3 = dfs[("V4", s)], dfs[("V3", s)]
        assert (v4["home_team"].to_numpy() == v3["home_team"].to_numpy()).all()
        out = v4["result"].tolist()
        d = ll_rows(v4[PC].to_numpy(), out) - ll_rows(v3[PC].to_numpy(), out)
        promoted = promoted_teams(all_matches, s)
        mask = (v4["home_team"].isin(promoted)
                | v4["away_team"].isin(promoted)).to_numpy()
        d_all.append(d)
        d_prom.append(d[mask])
        print(f"  {s:<7}"
              f"{ll_rows(v3[PC].to_numpy(), out).mean():>10.4f}"
              f"{ll_rows(v4[PC].to_numpy(), out).mean():>10.4f}"
              f"{d.mean():>+10.4f}{d[mask].mean():>+13.4f}{mask.sum():>9}")

    rng = np.random.default_rng(SEED)
    print(f"\n  {'pool':<26}{'media':>10}{'CI95':>24}{'P(aiuta)':>10}{'n':>7}")
    rows = {}
    for name, key, chunks in [("TUTTE le partite (8 stag.)", "all", d_all),
                              ("solo partite promosse", "prom", d_prom),
                              ("TUTTE, sole 6 stag. F17", "all6", d_all[2:]),
                              ("promosse, sole 6 stag.", "prom6", d_prom[2:])]:
        d = np.concatenate(chunks)
        mean, lo, hi, p_neg = boot(d, rng)
        rows |= {f"{key}_mean": mean, f"{key}_ci_lo": lo, f"{key}_ci_hi": hi,
                 f"{key}_p_neg": p_neg, f"{key}_n": int(len(d))}
        sig = "*" if hi < 0 or lo > 0 else " "
        print(f"  {name:<26}{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]{sig}"
              f"{p_neg:>9.1%}{len(d):>7}")
    print("\n  * = CI95 che non attraversa lo zero.")
    print("  CAVEAT: delta=0.23 include informazione 2018-2020 -> per 1819/1920")
    print("  il prior non e' leave-future-out (test di potenza, non nuova stima).")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase19_prior_power", "league": "serie_a",
         "variant": "ci_summary", "bootstrap_B": B, "bootstrap_seed": SEED,
         **BASE, "promoted_prior": 0.23, "seasons": SEASONS},
        {"n_matches": rows["all_n"], **rows}, fp))


if __name__ == "__main__":
    main()
