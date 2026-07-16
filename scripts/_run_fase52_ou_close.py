"""Fase 52 (A) — Si batte la chiusura anche sull'O/U 2.5? (il "banale" della Fase 26)

La Fase 26 aveva liquidato la lettura via matrice dei mercati PREZZATI come
"banale: riproduce il mercato". Ma la matrice non riproduce il devig binario:
l'inversione fonde l'informazione di DUE mercati (1X2 + O/U) e la forma vincola
la distribuzione. Indizio dai numeri delle Fasi 41/51: matrice ~0.679 vs devig
~0.682. Qui il confronto APPAIATO mai fatto, con le varianti della Fase 51:

  ou_devig     devig binario diretto delle quote O/U        [riferimento]
  ou_temp      + temperatura T binaria (LFO)                (sharpening puro)
  matrix_tau   O/U dalla matrice Poisson+ρ (tassi grezzi)   (fusione 1X2+O/U)
  matrix_dp    matrice double-Poisson (θ LFO)               (+ sotto-dispersione)
  matrix_dplvl matrice dp + livelli dei tassi (LFO)         (la dp_lvl di Fase 51)

Uso:  python scripts/_run_fase52_ou_close.py    (cache db_base + implied_rates)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from scripts import _fase52_common as C              # noqa: E402

B, SEED = 10_000, 52
VARIANTS = ["ou_devig", "ou_temp", "matrix_tau", "matrix_dp", "matrix_dplvl"]


def _p_over_matrix(M):
    i = C.K.reshape(-1, 1); j = C.K.reshape(1, -1)
    return M[:, (i + j) >= 3].sum(1)


def _fit_temp_bin(p, y):
    z = np.log(np.clip(p, 1e-12, 1 - 1e-12) / np.clip(1 - p, 1e-12, 1))

    def nll(t):
        q = 1.0 / (1.0 + np.exp(-t * z))
        return float(np.mean(C.ll_bin(q, y)))
    return float(minimize_scalar(nll, bounds=(0.7, 1.4), method="bounded",
                                 options={"xatol": 1e-4}).x)


def main():
    t0 = time.time()
    df = C.load_with_rates()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]

    acc = {v: [] for v in VARIANTS}
    per_season: dict = {}
    pars = {"theta": [], "T": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        y_ou_p = ((phg + pag) >= 3).astype(float)
        p_dev_p = np.array([metrics.devig_binary(r.odds_over, r.odds_under)[0]
                            for r in past.itertuples()])
        theta = C.fit_theta(past.mlam.values, past.mmu.values, phg, pag)
        T = _fit_temp_bin(p_dev_p, y_ou_p)
        c_l = C.fit_level(past.mlam.values, phg)
        c_m = C.fit_level(past.mmu.values, pag)
        pars["theta"].append(theta); pars["T"].append(T)

        y_ou = ((cur.home_goals + cur.away_goals) >= 3).astype(float).values
        p_dev = np.array([metrics.devig_binary(r.odds_over, r.odds_under)[0]
                          for r in cur.itertuples()])
        z = np.log(np.clip(p_dev, 1e-12, 1) / np.clip(1 - p_dev, 1e-12, 1))
        preds = {
            "ou_devig": p_dev,
            "ou_temp": 1.0 / (1.0 + np.exp(-T * z)),
            "matrix_tau": _p_over_matrix(
                C.dp_matrices(cur.mlam.values, cur.mmu.values, C.RHO, 1.0)),
            "matrix_dp": _p_over_matrix(
                C.dp_matrices(cur.mlam.values, cur.mmu.values, C.RHO, theta)),
            "matrix_dplvl": _p_over_matrix(
                C.dp_matrices(cur.mlam.values * np.exp(c_l),
                              cur.mmu.values * np.exp(c_m), C.RHO, theta)),
        }
        row = {}
        for v, p in preds.items():
            ll = C.ll_bin(p, y_ou)
            acc[v].append(ll)
            row[v] = float(ll.mean())
        per_season[s] = row
        print(f"  {s}: " + "  ".join(f"{v} {row[v]:.4f}" for v in VARIANTS), flush=True)

    for v in acc:
        acc[v] = np.concatenate(acc[v])
    rng = np.random.default_rng(SEED)
    n = len(acc["ou_devig"])

    print("\n" + "=" * 92)
    print(f"FASE 52 (A) — battere la chiusura O/U 2.5? (walk-forward, n={n})")
    print(f"parametri medi: θ={np.mean(pars['theta']):.3f}  T_ou={np.mean(pars['T']):.3f}")
    print("=" * 92)
    summary: dict = {"theta_mean": float(np.mean(pars["theta"])),
                     "temp_ou_mean": float(np.mean(pars["T"])),
                     "ou_devig__ll": float(acc["ou_devig"].mean())}
    print(f"  {'variante':<14}{'O/U ll':>9}{'Δ vs devig':>12}{'CI95':>22}{'P(batte)':>10}{'stagioni':>10}")
    print(f"  {'ou_devig':<14}{acc['ou_devig'].mean():>9.4f}")
    for v in VARIANTS[1:]:
        mean, lo, hi, p = C.boot(acc[v] - acc["ou_devig"], rng)
        n_seas = sum(1 for s in per_season if per_season[s][v] < per_season[s]["ou_devig"])
        flag = " ✓CI" if hi < 0 else ""
        print(f"  {v:<14}{acc[v].mean():>9.4f}{mean:>+12.4f}   [{lo:+.4f},{hi:+.4f}]"
              f"{p:>10.0%}{n_seas:>6}/{len(per_season)}{flag}")
        summary[f"{v}__ll"] = float(acc[v].mean())
        summary[f"{v}__delta"] = mean; summary[f"{v}__p"] = p
        summary[f"{v}__ci_lo"] = lo; summary[f"{v}__ci_hi"] = hi
        summary[f"{v}__seasons_beat"] = n_seas

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_ou_close", "league": "serie_a",
         "variant": "beat_close_ou25", "rho": C.RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_ou_close). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
