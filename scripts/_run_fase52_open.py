"""Fase 52 (F) — dp_lvl sulla linea di APERTURA: l'open affinato vale la chiusura?

La Fase 14 ha misurato: l'affilamento open→close vale ~+0.0020 di log-loss (la
chiusura e' meglio dell'apertura). La Fase 51 ha trovato che l'affinamento dp_lvl
vale ~−0.0016 sulla chiusura. Domanda mai posta: i bias (sotto-dispersione, tilt)
esistono gia' NELL'APERTURA? E se si': **l'apertura affinata raggiunge la
chiusura grezza?** Se dp_lvl(open) ≈ devig(close), l'affinamento recupera quasi
tutto quello che il mercato impara tra venerdi' e il calcio d'inizio.

Varianti (sulle sole righe con quote open 1X2+O/U complete):
  open_devig     apertura devigata                     [riferimento debole]
  close_devig    chiusura devigata                     [riferimento forte]
  dp_lvl_open    dp_lvl sui tassi invertiti dall'APERTURA (θ, livelli LFO su open)
  dp_lvl_close   dp_lvl sulla chiusura (Fase 51)

Uso:  python scripts/_run_fase52_open.py    (cache db_base + implied_rates)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from scripts import _fase52_common as C              # noqa: E402

B, SEED = 10_000, 52
_OI = {"H": 0, "D": 1, "A": 2}
VARIANTS = ["open_devig", "close_devig", "dp_lvl_open", "dp_lvl_close"]


def main():
    t0 = time.time()
    df = C.load_with_rates(require_open=True)
    has_open = np.isfinite(df["mlam_open"].to_numpy())
    df = df[has_open].reset_index(drop=True)
    print(f"dati pronti in {time.time()-t0:.0f}s (righe con open complete: {len(df)}; "
          f"stagioni: {sorted(set(df.season))})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]

    acc = {v: [] for v in VARIANTS}
    per_season: dict = {}
    pars = {"theta_o": [], "lvl_o": []}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        if len(past) < 300:
            continue
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        # fit su OPEN (per il path open) e su CLOSE (per il path close)
        th_o = C.fit_theta(past.mlam_open.values, past.mmu_open.values, phg, pag)
        cl_o = C.fit_level(past.mlam_open.values, phg)
        cm_o = C.fit_level(past.mmu_open.values, pag)
        th_c = C.fit_theta(past.mlam.values, past.mmu.values, phg, pag)
        cl_c = C.fit_level(past.mlam.values, phg)
        cm_c = C.fit_level(past.mmu.values, pag)
        pars["theta_o"].append(th_o); pars["lvl_o"].append((np.exp(cl_o), np.exp(cm_o)))

        y = np.array([_OI[o] for o in cur.result])
        P_open = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                             r.odds_away_open) for r in cur.itertuples()])
        P_close = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                            for r in cur.itertuples()])
        preds = {
            "open_devig": P_open,
            "close_devig": P_close,
            "dp_lvl_open": C.p1x2(C.dp_matrices(
                cur.mlam_open.values * np.exp(cl_o),
                cur.mmu_open.values * np.exp(cm_o), C.RHO, th_o)),
            "dp_lvl_close": C.p1x2(C.dp_matrices(
                cur.mlam.values * np.exp(cl_c),
                cur.mmu.values * np.exp(cm_c), C.RHO, th_c)),
        }
        row = {}
        for v, P in preds.items():
            ll = -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))
            acc[v].append(ll)
            row[v] = float(ll.mean())
        per_season[s] = row
        print(f"  {s}: " + "  ".join(f"{v} {row[v]:.4f}" for v in VARIANTS), flush=True)

    for v in acc:
        acc[v] = np.concatenate(acc[v])
    rng = np.random.default_rng(SEED)
    n = len(acc["open_devig"])

    print("\n" + "=" * 92)
    print(f"FASE 52 (F) — dp_lvl sull'APERTURA (n={n})")
    print(f"θ_open medio: {np.mean(pars['theta_o']):.3f}   livelli open medi: "
          f"λ×{np.mean([x[0] for x in pars['lvl_o']]):.4f} "
          f"μ×{np.mean([x[1] for x in pars['lvl_o']]):.4f}")
    print("=" * 92)
    summary: dict = {"theta_open_mean": float(np.mean(pars["theta_o"])),
                     **{f"{v}__ll": float(acc[v].mean()) for v in VARIANTS}}
    for v in VARIANTS:
        print(f"  {v:<14}{acc[v].mean():.4f}")
    print("\n  confronti appaiati chiave:")
    for a, b, lab in (("dp_lvl_open", "open_devig", "l'affinamento batte l'OPEN?"),
                      ("dp_lvl_open", "close_devig", "l'open affinato vale la CHIUSURA?"),
                      ("dp_lvl_close", "close_devig", "conferma Fase 51 su questo sottoinsieme"),
                      ("close_devig", "open_devig", "affilamento open->close (Fase 14)")):
        mean, lo, hi, p = C.boot(acc[a] - acc[b], rng)
        flag = " ✓CI" if hi < 0 else (" ✗CI" if lo > 0 else "")
        print(f"    {a} − {b}:  Δ={mean:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  "
              f"P={p:.0%}{flag}   ({lab})")
        summary[f"{a}_vs_{b}__delta"] = mean
        summary[f"{a}_vs_{b}__ci_lo"] = lo; summary[f"{a}_vs_{b}__ci_hi"] = hi
        summary[f"{a}_vs_{b}__p"] = p

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_open", "league": "serie_a",
         "variant": "dp_lvl_su_apertura", "rho": C.RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(n), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_open). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
