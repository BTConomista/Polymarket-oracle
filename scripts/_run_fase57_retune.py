"""Fase 57 — Ri-taratura degli iperparametri PER LEGA (§7: mai copiare i numeri).

Il tracer (Fase 56) ha usato la config Serie A cosi' com'e'. Qui si ri-tara ogni
iperparametro sui dati di CIASCUNA lega, una leva alla volta (§1.2), tenendo le
altre al default Serie A. γ (vantaggio-casa) NON e' un iperparametro: il DC lo
fitta dai dati (la EDA mostra γ_Liga 0.27 >> γ_SerieA 0.15, e il modello si adatta
gia'). Le leve genuine:

  δ (promoted_prior)  griglia {0, 0.15, 0.23, 0.33, 0.45}
      EDA (Fase 55): δ_attacco = 0.33 Premier, 0.22 Liga, 0.23 Serie A.
      Ipotesi §7 VERIFICATA sui dati: le promosse di Premier sono piu' deboli.
  emivita             griglia {180, 365, 540, 730}
      EDA: autocorr forze 0.82 Liga vs 0.74 Premier/Serie A -> Liga rose piu'
      stabili -> forse memoria piu' lunga.
  shrinkage           griglia {0.75, 1.5, 3.0}

Il default Serie A (δ=0.23, emivita=365, shrink=1.5) riusa la cache del tracer.
Si sceglie il minimo log-loss 1X2 walk-forward (= min gap, mercato fisso), con la
disciplina CI della Fase 17 (un minimo entro il rumore del default NON giustifica
il cambio). Output: config consigliata per lega + Δ gap vs tracer.

Uso:  python scripts/_run_fase57_retune.py    (snapshot Premier/Liga; Pool 4)
"""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import SERIE_A                       # noqa: E402
from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from scripts.backtest import run_backtest            # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
LEAGUES = ["premier_league", "la_liga"]
NAMES = {"premier_league": "Premier League", "la_liga": "La Liga"}
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
B, SEED = 10_000, 57
_OI = {"H": 0, "D": 1, "A": 2}
DEF = dict(half_life=365.0, shrink=1.5, delta=0.23)

# griglie (una leva alla volta attorno al default). Ridotte all'essenziale dopo
# aver constatato il costo (~2 min/backtest su queste leghe): δ e' la leva-chiave
# indicata dalla EDA (Fase 55); emivita/shrinkage erano PIATTI in Serie A (Fase 8),
# qui un solo valore alternativo ciascuno come sanity (emivita 730 = ipotesi
# "rose Liga piu' stabili" della EDA).
GRID = {
    "delta": [0.0, 0.15, 0.23, 0.33, 0.45],
    "half_life": [365.0, 730.0],
    "shrink": [1.5, 3.0],
}


def _cfg_to_path(league, hl, shrink, delta):
    # il default coincide con la cache del tracer (db_{league}_{season}.csv)
    if (hl, shrink, delta) == (DEF["half_life"], DEF["shrink"], DEF["delta"]):
        return lambda s: CACHE / f"db_{league}_{s}.csv"
    tag = f"hl{hl:.0f}_sh{shrink}_d{delta}".replace(".", "p")
    return lambda s: CACHE / f"rt_{league}_{tag}_{s}.csv"


def _worker(args):
    league, season, hl, shrink, delta = args
    fp = _cfg_to_path(league, hl, shrink, delta)(season)
    if fp.exists():
        return "cache"
    prior = (delta, delta) if delta else None
    df = run_backtest(league, season, hl, shrinkage=shrink,
                      shots_blend=SERIE_A["shots_blend"],
                      blend_signal=SERIE_A["blend_signal"],
                      promoted_prior=prior, verbose=False)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return "done"


def _load_cfg(league, hl, shrink, delta):
    pathfn = _cfg_to_path(league, hl, shrink, delta)
    fr = []
    for s in TEST_SEASONS:
        d = pd.read_csv(pathfn(s)); d["season"] = s
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def _model_ll(df):
    P = np.clip(df[["m_home", "m_draw", "m_away"]].to_numpy(), 1e-15, 1)
    y = np.array([_OI[o] for o in df.result])
    return -np.log(P[np.arange(len(y)), y])


def _market_ll(df):
    mkt = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            mkt[i] = -np.log(max(p[_OI[r.result]], 1e-15))
    return mkt


def main():
    t0 = time.time()
    # config da valutare (una leva alla volta), ORDINATE: prima δ (leva-chiave,
    # emivita 365 veloce), poi shrinkage, infine emivita 730 (la piu' lenta).
    configs: list = []
    for d in GRID["delta"]:
        c = (DEF["half_life"], DEF["shrink"], d)
        if c not in configs:
            configs.append(c)
    for sh in GRID["shrink"]:
        c = (DEF["half_life"], sh, DEF["delta"])
        if c not in configs:
            configs.append(c)
    for hl in GRID["half_life"]:
        c = (hl, DEF["shrink"], DEF["delta"])
        if c not in configs:
            configs.append(c)

    jobs = [(lg, s, hl, sh, d) for (hl, sh, d) in configs for lg in LEAGUES
            for s in TEST_SEASONS if not _cfg_to_path(lg, hl, sh, d)(s).exists()]
    print(f"backtest da eseguire: {len(jobs)} (config x lega x stagione)", flush=True)
    if jobs:
        with Pool(4) as pool:
            done = 0
            for _ in pool.imap_unordered(_worker, jobs):
                done += 1
                if done % 12 == 0:
                    print(f"  {done}/{len(jobs)} ({time.time()-t0:.0f}s)", flush=True)

    rng = np.random.default_rng(SEED)
    for lg in LEAGUES:
        mkt = _market_ll(_load_cfg(lg, DEF["half_life"], DEF["shrink"], DEF["delta"]))
        ok = np.isfinite(mkt)
        def_ll = _model_ll(_load_cfg(lg, DEF["half_life"], DEF["shrink"], DEF["delta"]))
        def_gap = float((def_ll[ok] - mkt[ok]).mean())

        print("\n" + "=" * 78)
        print(f"FASE 57 — RI-TARATURA {NAMES[lg]} (walk-forward {len(TEST_SEASONS)} stagioni)")
        print(f"  default Serie A: gap {def_gap:+.4f} (modello {def_ll.mean():.4f})")
        print("=" * 78)
        summary = {"default_gap": def_gap, "default_ll": float(def_ll.mean())}
        best = {"gap": def_gap, "cfg": ("default", DEF["half_life"], DEF["shrink"], DEF["delta"])}
        for lever, grid in GRID.items():
            print(f"\n  --- {lever} ---")
            for v in grid:
                hl = v if lever == "half_life" else DEF["half_life"]
                sh = v if lever == "shrink" else DEF["shrink"]
                d = v if lever == "delta" else DEF["delta"]
                ll = _model_ll(_load_cfg(lg, hl, sh, d))
                gap = float((ll[ok] - mkt[ok]).mean())
                dd = ll[ok] - def_ll[ok]
                m = dd[rng.integers(0, len(dd), (B, len(dd)))].mean(1)
                p_better = float((m < 0).mean())
                is_def = (hl, sh, d) == (DEF["half_life"], DEF["shrink"], DEF["delta"])
                mark = "  (default)" if is_def else ""
                sig = " *" if not is_def and np.percentile(m, 97.5) < 0 else ""
                print(f"    {lever}={v:<7}  modello {ll.mean():.4f}  gap {gap:+.4f}  "
                      f"Δ vs def {dd.mean():+.4f}  P(migliora) {p_better:.0%}{sig}{mark}")
                summary[f"{lever}_{v}_gap"] = gap
                summary[f"{lever}_{v}_delta_vs_def"] = float(dd.mean())
                summary[f"{lever}_{v}_p_better"] = p_better
                if gap < best["gap"] - 1e-9:
                    best = {"gap": gap, "cfg": (lever, hl, sh, d)}
        print(f"\n  => migliore: {best['cfg'][0]} -> gap {best['gap']:+.4f} "
              f"(Δ {best['gap']-def_gap:+.4f} vs default)")
        summary["best_lever"] = best["cfg"][0]
        summary["best_gap"] = best["gap"]

        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase57_retune", "league": lg, "variant": "ritaratura_iperparametri",
             "grid": GRID, "test_seasons": TEST_SEASONS,
             "bootstrap_B": B, "bootstrap_seed": SEED},
            {"n_matches": int(ok.sum()), **summary},
            experiment_log.data_fingerprint(loader.load_league(lg))))
    print(f"\nRun registrati (source=fase57_retune). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
