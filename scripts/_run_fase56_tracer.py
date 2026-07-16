"""Fase 56 — Tracer bullet: il DC con la config UFFICIALE Serie A su Premier/Liga.

Metodo §1 (tracer bullet prima dei moduli): prima di ri-tarare qualsiasi cosa,
si prende il modello Serie A COSI' COM'E' (config ufficiale: emivita 365g,
shrinkage 1.5, blend xG α=0.75, prior neopromosse δ=0.23) e lo si fa girare
walk-forward sulle due leghe nuove. Domanda: dove atterra il gap col mercato,
partendo da numeri NON tarati per queste leghe? E' la baseline onesta contro cui
misurare il guadagno della ri-taratura (Fase 57).

Genera anche la cache per-lega db_{league}_{season}.csv (predizioni per-partita)
riusata dalla ri-taratura, cosi' non si rifitta il DC ogni volta.

Uso:  python scripts/_run_fase56_tracer.py    (snapshot Premier/Liga; Pool 4)
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
B, SEED = 10_000, 56
_OI = {"H": 0, "D": 1, "A": 2}


def _worker(args):
    league, season = args
    fp = CACHE / f"db_{league}_{season}.csv"
    if fp.exists():
        return league, season, "cache"
    df = run_backtest(league, season, SERIE_A["half_life_days"],
                      shrinkage=SERIE_A["shrinkage"], shots_blend=SERIE_A["shots_blend"],
                      blend_signal=SERIE_A["blend_signal"],
                      promoted_prior=(SERIE_A["promoted_prior"], SERIE_A["promoted_prior"]),
                      verbose=False)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return league, season, f"{len(df)} gare"


def _load(league):
    fr = []
    for s in TEST_SEASONS:
        d = pd.read_csv(CACHE / f"db_{league}_{s}.csv"); d["season"] = s
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def _metrics(df):
    P = np.clip(df[["m_home", "m_draw", "m_away"]].to_numpy(), 1e-15, 1)
    y = np.array([_OI[o] for o in df.result])
    model = -np.log(P[np.arange(len(y)), y])
    mkt = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            mkt[i] = -np.log(max(p[_OI[r.result]], 1e-15))
    # baseline in-sample (freq. della stagione di test), onesta come Serie A
    base = np.zeros(len(df))
    for s in df.season.unique():
        m = df.season == s
        fr = np.array([(df[m].result == k).mean() for k in "HDA"])
        base[m] = -np.log(np.clip(fr[[_OI[o] for o in df[m].result]], 1e-15, 1))
    ou_model = np.clip(df.m_over.to_numpy(), 1e-15, 1 - 1e-15)
    yov = df.is_over.to_numpy(float)
    ou_ll = -(yov * np.log(ou_model) + (1 - yov) * np.log(1 - ou_model))
    return model, mkt, base, ou_ll


def main():
    t0 = time.time()
    jobs = [(lg, s) for lg in LEAGUES for s in TEST_SEASONS
            if not (CACHE / f"db_{lg}_{s}.csv").exists()]
    print(f"backtest da eseguire: {len(jobs)}", flush=True)
    if jobs:
        with Pool(4) as pool:
            for lg, s, msg in pool.imap_unordered(_worker, jobs):
                print(f"  {lg} {s}: {msg} ({time.time()-t0:.0f}s)", flush=True)

    rng = np.random.default_rng(SEED)
    print("\n" + "=" * 82)
    print("FASE 56 — TRACER: DC config-Serie-A (NON tarata) su Premier/Liga, "
          f"walk-forward {len(TEST_SEASONS)} stagioni")
    print("  (riferimento Serie A ufficiale: modello 0.9797, mercato 0.9632, gap +0.0165)")
    print("=" * 82)
    print(f"  {'lega':<16}{'modello':>9}{'mercato':>9}{'baseline':>10}"
          f"{'gap 1X2':>10}{'CI95 gap':>20}{'O/U mod':>9}")
    for lg in LEAGUES:
        df = _load(lg)
        model, mkt, base, ou = _metrics(df)
        ok = np.isfinite(mkt)
        gap = model[ok] - mkt[ok]
        m = gap[rng.integers(0, len(gap), (B, len(gap)))].mean(1)
        lo, hi = np.percentile(m, [2.5, 97.5])
        print(f"  {NAMES[lg]:<16}{model.mean():>9.4f}{mkt[ok].mean():>9.4f}"
              f"{base.mean():>10.4f}{gap.mean():>+10.4f}   [{lo:+.4f},{hi:+.4f}]"
              f"{ou.mean():>9.4f}")
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase56_tracer", "league": lg,
             "variant": "dc_config_serie_a_non_tarata",
             "config": {k: SERIE_A[k] for k in SERIE_A},
             "test_seasons": TEST_SEASONS, "bootstrap_B": B, "bootstrap_seed": SEED},
            {"n_matches": int(len(df)), "model_ll": float(model.mean()),
             "market_ll": float(mkt[ok].mean()), "baseline_ll": float(base.mean()),
             "gap_1x2": float(gap.mean()), "gap_ci_lo": float(lo),
             "gap_ci_hi": float(hi), "ou_model_ll": float(ou.mean())},
            experiment_log.data_fingerprint(loader.load_league(lg))))
    print(f"\nRun registrati (source=fase56_tracer). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
