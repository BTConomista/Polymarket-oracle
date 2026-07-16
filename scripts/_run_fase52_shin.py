"""Fase 52 (C) — Il tilt casa/trasferta e' un artefatto del devig? Test di Shin.

Caveat dichiarato in Fase 51: il dp_lvl batte la chiusura *devigata
moltiplicativamente*; un devig piu' raffinato potrebbe assorbire parte del bias.
Il candidato canonico e' il devig di **Shin (1992-93)**: modella una quota di
scommettitori informati (z) e corregge il favourite-longshot bias in modo
non-proporzionale. Confronto appaiato 1X2:

  market       devig moltiplicativo                         [benchmark storico]
  shin         devig di Shin (z per riga, Σp=1)             (mai provato)
  shin_temp    Shin + temperatura T (LFO)                   (sharpening su Shin)
  dp_lvl       double-Poisson + livelli (Fase 51)
  dp_lvl_T     dp_lvl + temperatura sopra (LFO)             (sanity: T→1?)

Se dp_lvl batte anche Shin, il tilt NON e' un artefatto del devig moltiplicativo.

Uso:  python scripts/_run_fase52_shin.py    (cache db_base + implied_rates)
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
_OI = {"H": 0, "D": 1, "A": 2}
VARIANTS = ["market", "shin", "shin_temp", "dp_lvl", "dp_lvl_T"]


def shin_devig(odds_home: float, odds_draw: float, odds_away: float) -> np.ndarray:
    """Devig di Shin per un mercato a 3 esiti: trova z (quota di insider) tale che
    le probabilita' p_i = [sqrt(z^2 + 4(1-z)·pi_i^2/PI) - z] / (2(1-z)) sommino a 1
    (pi_i = 1/quota, PI = Σ pi_i). z=0 -> devig moltiplicativo."""
    pi = np.array([1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away])
    PI = pi.sum()

    def p_of(z):
        return (np.sqrt(z * z + 4.0 * (1.0 - z) * pi * pi / PI) - z) / (2.0 * (1.0 - z))

    lo, hi = 0.0, 0.3
    for _ in range(60):
        z = 0.5 * (lo + hi)
        if p_of(z).sum() > 1.0:
            lo = z
        else:
            hi = z
    p = p_of(0.5 * (lo + hi))
    return p / p.sum()


def _fit_temp(P, y):
    def nll(t):
        Q = P ** t; Q = Q / Q.sum(1, keepdims=True)
        return -float(np.mean(np.log(np.clip(Q[np.arange(len(y)), y], 1e-15, 1))))
    return float(minimize_scalar(nll, bounds=(0.7, 1.4), method="bounded",
                                 options={"xatol": 1e-4}).x)


def _apply_temp(P, t):
    Q = P ** t
    return Q / Q.sum(1, keepdims=True)


def _ll(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))


def main():
    t0 = time.time()
    df = C.load_with_rates()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]

    # precalcolo Shin e mercato per tutte le righe (nessun parametro)
    P_mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                      for r in df.itertuples()])
    P_shin = np.array([shin_devig(r.odds_home, r.odds_draw, r.odds_away)
                       for r in df.itertuples()])
    y_all = np.array([_OI[r] for r in df.result])
    season = df.season.values
    print(f"devig Shin calcolato ({time.time()-t0:.0f}s); "
          f"scostamento medio |shin−molt| = {np.abs(P_shin-P_mkt).mean():.4f}", flush=True)

    acc = {v: [] for v in VARIANTS}
    per_season: dict = {}
    pars = {"theta": [], "T_shin": [], "T_dp": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past_m = np.isin(season, seasons[:i]); cur_m = season == s
        past = df[past_m]; cur = df[cur_m]
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        theta = C.fit_theta(past.mlam.values, past.mmu.values, phg, pag)
        c_l = C.fit_level(past.mlam.values, phg)
        c_m = C.fit_level(past.mmu.values, pag)
        T_shin = _fit_temp(P_shin[past_m], y_all[past_m])
        # dp_lvl del PASSATO per fittare la temperatura sopra dp_lvl
        P_dp_past = C.p1x2(C.dp_matrices(past.mlam.values * np.exp(c_l),
                                         past.mmu.values * np.exp(c_m), C.RHO, theta))
        T_dp = _fit_temp(P_dp_past, y_all[past_m])
        pars["theta"].append(theta); pars["T_shin"].append(T_shin); pars["T_dp"].append(T_dp)

        P_dp = C.p1x2(C.dp_matrices(cur.mlam.values * np.exp(c_l),
                                    cur.mmu.values * np.exp(c_m), C.RHO, theta))
        preds = {
            "market": P_mkt[cur_m],
            "shin": P_shin[cur_m],
            "shin_temp": _apply_temp(P_shin[cur_m], T_shin),
            "dp_lvl": P_dp,
            "dp_lvl_T": _apply_temp(P_dp, T_dp),
        }
        row = {}
        for v, P in preds.items():
            ll = _ll(P, y_all[cur_m])
            acc[v].append(ll)
            row[v] = float(ll.mean())
        per_season[s] = row

    for v in acc:
        acc[v] = np.concatenate(acc[v])
    rng = np.random.default_rng(SEED)
    n = len(acc["market"])

    print("\n" + "=" * 96)
    print(f"FASE 52 (C) — devig di Shin vs moltiplicativo vs dp_lvl (1X2, n={n})")
    print(f"parametri medi: θ={np.mean(pars['theta']):.3f}  T_shin={np.mean(pars['T_shin']):.3f}"
          f"  T_sopra_dp={np.mean(pars['T_dp']):.3f}")
    print("=" * 96)
    summary: dict = {"theta_mean": float(np.mean(pars["theta"])),
                     "T_shin_mean": float(np.mean(pars["T_shin"])),
                     "T_dp_mean": float(np.mean(pars["T_dp"])),
                     "market__ll": float(acc["market"].mean())}
    print(f"  {'variante':<12}{'1X2':>9}{'Δ vs molt.':>12}{'CI95':>22}{'P(batte)':>10}{'stagioni':>10}")
    print(f"  {'market':<12}{acc['market'].mean():>9.4f}")
    for v in VARIANTS[1:]:
        mean, lo, hi, p = C.boot(acc[v] - acc["market"], rng)
        n_seas = sum(1 for s in per_season if per_season[s][v] < per_season[s]["market"])
        flag = " ✓CI" if hi < 0 else ""
        print(f"  {v:<12}{acc[v].mean():>9.4f}{mean:>+12.4f}   [{lo:+.4f},{hi:+.4f}]"
              f"{p:>10.0%}{n_seas:>6}/{len(per_season)}{flag}")
        summary[f"{v}__ll"] = float(acc[v].mean())
        summary[f"{v}__delta"] = mean; summary[f"{v}__p"] = p
        summary[f"{v}__ci_lo"] = lo; summary[f"{v}__ci_hi"] = hi
    # confronto chiave: dp_lvl vs Shin (il caveat della Fase 51)
    mean, lo, hi, p = C.boot(acc["dp_lvl"] - acc["shin"], rng)
    print(f"\n  dp_lvl − shin:  Δ={mean:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  P(dp_lvl migliore)={p:.0%}")
    summary["dplvl_vs_shin__delta"] = mean
    summary["dplvl_vs_shin__ci_lo"] = lo; summary["dplvl_vs_shin__ci_hi"] = hi
    summary["dplvl_vs_shin__p"] = p

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_shin", "league": "serie_a",
         "variant": "shin_devig_vs_dp_lvl", "rho": C.RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_shin). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
