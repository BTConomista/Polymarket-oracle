"""Fase 50 (Track B) — MEGA-SWEEP del path DC (senza quote): combo mai provate.

Sul path DC le leve sono state validate una alla volta: φ35 (Fase 35), covariata
stakes (Fase 32), midweek (Fase 36-bis), iperparametri (Fasi 2b/4d/8, PRIMA che
esistesse la φ35). Mai provate INSIEME, e la taratura di emivita/shrinkage non e'
mai stata rifatta con la φ35 attiva (le leve potrebbero interagire: la φ35 cambia
la verosimiglianza dei pareggi, l'ottimo di memoria/regolarizzazione puo' spostarsi).

Griglia (config ufficiale = base, tutte walk-forward 6 stagioni, cache per-stagione):

  phi35            draw_balance                  (riferimento Fase 35, ricalcolato)
  phi35_stakes     + covariata stakes            (mai provata con φ35)
  phi35_midweek    + covariata midweek           (mai provata con φ35)
  phi35_stk_mw     + stakes + midweek            (mai provate nemmeno tra loro)
  stk_mw           stakes + midweek senza φ35    (isolare l'interazione covariate)
  phi35_hl270      φ35 + emivita 270g            (ri-taratura memoria con φ35)
  phi35_hl540      φ35 + emivita 540g
  phi35_shr075     φ35 + shrinkage 0.75          (ri-taratura regolarizzazione)
  phi35_shr3       φ35 + shrinkage 3.0

Confronto per-mercato (1X2, pareggio, O/U 2.5, GG/NG) vs la config UFFICIALE
(cache db_base), bootstrap appaiato; gap 1X2 col mercato per ogni variante.

Uso:  python scripts/_run_fase50_dc_sweep.py    (genera le cache mancanti, Pool 4)
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
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
B, SEED = 10_000, 50
_IDX = {"H": 0, "D": 1, "A": 2}

BASE = dict(half_life_days=SERIE_A["half_life_days"], shrinkage=SERIE_A["shrinkage"],
            shots_blend=SERIE_A["shots_blend"], blend_signal=SERIE_A["blend_signal"],
            promoted_prior=(SERIE_A["promoted_prior"], SERIE_A["promoted_prior"]))

VARIANTS: dict[str, dict] = {
    "phi35":         {"draw_balance": True},
    "phi35_stakes":  {"draw_balance": True, "covariates": ("stakes",)},
    "phi35_midweek": {"draw_balance": True, "covariates": ("midweek",)},
    "phi35_stk_mw":  {"draw_balance": True, "covariates": ("stakes", "midweek")},
    "stk_mw":        {"covariates": ("stakes", "midweek")},
    "phi35_hl270":   {"draw_balance": True, "half_life_days": 270.0},
    "phi35_hl540":   {"draw_balance": True, "half_life_days": 540.0},
    "phi35_shr075":  {"draw_balance": True, "shrinkage": 0.75},
    "phi35_shr3":    {"draw_balance": True, "shrinkage": 3.0},
}


def _worker(args):
    name, season = args
    fp = CACHE / f"db_f50_{name}_{season}.csv"
    if fp.exists():
        return name, season, "cache"
    t0 = time.time()
    cfg = dict(BASE); cfg.update(VARIANTS[name])
    df = run_backtest("serie_a", season, cfg.pop("half_life_days"),
                      verbose=False, **cfg)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return name, season, f"{time.time()-t0:.0f}s"


def _load(name):
    fr = []
    for s in SEASONS:
        fp = (CACHE / f"db_base_{s}.csv" if name == "base"
              else CACHE / f"db_f50_{name}_{s}.csv")
        d = pd.read_csv(fp); d["season"] = s
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def _ll_rows(df):
    """Log-loss per-riga di 1X2, pareggio (binario), O/U 2.5, GG/NG."""
    P = np.clip(df[["m_home", "m_draw", "m_away"]].to_numpy(), 1e-15, 1)
    y = np.array([_IDX[o] for o in df.result])
    x2 = -np.log(P[np.arange(len(y)), y])
    pd_ = np.clip(df.m_draw.to_numpy(), 1e-15, 1 - 1e-15)
    ydr = (df.result == "D").to_numpy(float)
    dr = -(ydr * np.log(pd_) + (1 - ydr) * np.log(1 - pd_))
    po = np.clip(df.m_over.to_numpy(), 1e-15, 1 - 1e-15)
    yov = df.is_over.to_numpy(float)
    ov = -(yov * np.log(po) + (1 - yov) * np.log(1 - po))
    pg = np.clip(df.m_btts.to_numpy(), 1e-15, 1 - 1e-15)
    ygg = df.is_btts.to_numpy(float)
    gg = -(ygg * np.log(pg) + (1 - ygg) * np.log(1 - pg))
    return {"x2": x2, "draw": dr, "ou": ov, "gg": gg}


def _market_x2(df):
    ll = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            ll[i] = -np.log(max(p[_IDX[r.result]], 1e-15))
    return ll


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def main():
    jobs = [(n, s) for n in VARIANTS for s in SEASONS
            if not (CACHE / f"db_f50_{n}_{s}.csv").exists()]
    print(f"backtest da eseguire: {len(jobs)} (config x stagione)", flush=True)
    if jobs:
        with Pool(4) as pool:
            for n, s, msg in pool.imap_unordered(_worker, jobs):
                print(f"  {n} {s}: {msg}", flush=True)

    base = _load("base").sort_values(["season", "date", "home_team"]).reset_index(drop=True)
    ll_base = _ll_rows(base)
    mkt = _market_x2(base)
    rng = np.random.default_rng(SEED)

    print("\n" + "=" * 96)
    print(f"FASE 50 (Track B) — sweep path DC, walk-forward {len(SEASONS)} stagioni "
          f"(n={len(base)}; riferimento = config ufficiale)")
    print("=" * 96)
    print(f"  {'variante':<16}{'1X2':>9}{'Δ':>9}{'P':>5}{'pari Δ':>9}{'O/U Δ':>9}"
          f"{'GG Δ':>9}{'gap-mkt 1X2':>13}{'CI95 Δ1X2':>22}")
    ok = np.isfinite(mkt)
    gap_base = float(np.nanmean(ll_base['x2'][ok] - mkt[ok]))
    print(f"  {'base (uff.)':<16}{ll_base['x2'].mean():>9.4f}{'—':>9}{'—':>5}"
          f"{'—':>9}{'—':>9}{'—':>9}{gap_base:>+13.4f}")
    summary: dict = {"base__x2": float(ll_base["x2"].mean()), "base__gap": gap_base}
    for name in VARIANTS:
        df = _load(name).sort_values(["season", "date", "home_team"]).reset_index(drop=True)
        assert (df.home_team.values == base.home_team.values).all(), name
        ll = _ll_rows(df)
        dx2, lo, hi, p = _boot(ll["x2"] - ll_base["x2"], rng)
        ddr = float((ll["draw"] - ll_base["draw"]).mean())
        dov = float((ll["ou"] - ll_base["ou"]).mean())
        dgg = float((ll["gg"] - ll_base["gg"]).mean())
        gap = float(np.nanmean(ll["x2"][ok] - mkt[ok]))
        flag = " ✓" if hi < 0 else ""
        print(f"  {name:<16}{ll['x2'].mean():>9.4f}{dx2:>+9.4f}{p:>5.0%}{ddr:>+9.4f}"
              f"{dov:>+9.4f}{dgg:>+9.4f}{gap:>+13.4f}   [{lo:+.4f},{hi:+.4f}]{flag}")
        summary[f"{name}__x2"] = float(ll["x2"].mean())
        summary[f"{name}__x2_delta"] = dx2
        summary[f"{name}__x2_ci_lo"] = lo; summary[f"{name}__x2_ci_hi"] = hi
        summary[f"{name}__x2_p"] = p
        summary[f"{name}__draw_delta"] = ddr; summary[f"{name}__ou_delta"] = dov
        summary[f"{name}__gg_delta"] = dgg; summary[f"{name}__gap"] = gap

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase50_dc_sweep", "league": "serie_a",
         "variant": "dc_sweep_phi35_x_covariate_x_iperparametri",
         "seasons": SEASONS, "bootstrap_B": B, "bootstrap_seed": SEED,
         "variants": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                          for kk, vv in v.items()} for k, v in VARIANTS.items()}},
        {"n_matches": int(len(base)), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase50_dc_sweep).")


if __name__ == "__main__":
    main()
