"""Punto 2b — `midweek_europe` come covariata del sotto-modello GOL Dixon-Coles.

Il flag `home/away_midweek_europe` (gara europea/coppa infrasettimana, Fase 4e)
esiste nei dati ma non era mai stato una covariata del DC. E' un DUMMY di
congestione (soglia sì/no), potenzialmente piu' robusto del `rest_full` continuo
(gradiente sui giorni). Domanda: aiuta? e spiega varianza che `rest_full` non
cattura (o e' ridondante/collineare)?

Confronto walk-forward 6 stagioni (stessi split, bootstrap appaiato):
    base  |  +midweek  |  +rest_full  |  +rest_full & midweek
Piu' un test di RIDONDANZA: fit a inizio stagione con ENTRAMBE -> i beta di
rest_full e midweek sopravvivono o si annullano a vicenda (collinearita')?

Uso:  python scripts/_run_midweek_cov.py     (18 backtest; base in cache; ~minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402
from src.models.dixon_coles import DixonColesModel  # noqa: E402
from scripts.backtest import run_backtest, promoted_teams  # noqa: E402

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
VARIANTS = {
    "base": (),
    "midweek": ("midweek",),
    "rest_full": ("rest_full",),
    "rest_full+midweek": ("rest_full", "midweek"),
}
CACHE = Path(__file__).resolve().parents[1] / "outputs"
B, SEED = 10_000, 22
_IDX = {"H": 0, "D": 1, "A": 2}


def _worker(args):
    name, season = args
    fp = CACHE / (f"db_base_{season}.csv" if name == "base" else f"mw_{name}_{season}.csv")
    if fp.exists():
        return name, season, pd.read_csv(fp, parse_dates=["date"])
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], covariates=VARIANTS[name],
                      verbose=False)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return name, season, df


def _ll(df):
    P = np.clip(df[["m_home", "m_draw", "m_away"]].to_numpy(), 1e-15, 1)
    y = np.array([_IDX[o] for o in df.result])
    return -np.log(P[np.arange(len(y)), y])


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    jobs = [(name, s) for name in VARIANTS for s in SEASONS]
    with Pool(4) as pool:
        res = pool.map(_worker, jobs)
    key = ["season", "home_team", "away_team"]
    by = {name: pd.concat([df for n, s, df in res if n == name], ignore_index=True)
          .sort_values(key).reset_index(drop=True) for name in VARIANTS}
    n = len(by["base"])
    ll = {name: _ll(by[name]) for name in VARIANTS}
    mkt = np.full(n, np.nan)
    b0 = by["base"]
    for i, r in enumerate(b0.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt[i] = -np.log(max(metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)[_IDX[r.result]], 1e-15))
    rng = np.random.default_rng(SEED)

    print("=" * 84)
    print(f"PUNTO 2b — midweek_europe come covariata DC ({n} partite, 6 stagioni walk-forward)")
    print(f"mercato 1X2 log-loss (rif.) = {mkt[np.isfinite(mkt)].mean():.4f}")
    print("=" * 84)
    print(f"  {'variante':<20}{'1X2 log-loss':>14}{'Δ vs base':>12}{'CI95 Δ':>22}{'P(mig)':>8}")
    summary = {}
    for name in VARIANTS:
        if name == "base":
            print(f"  {name:<20}{ll[name].mean():>14.4f}{'—':>12}{'—':>22}{'—':>8}")
            summary[name] = float(ll[name].mean())
            continue
        mean, lo, hi, pmig = _boot(ll[name] - ll["base"], rng)
        verd = " VIVA" if hi < 0 else (" promettente" if mean < 0 else "")
        print(f"  {name:<20}{ll[name].mean():>14.4f}{mean:>+12.4f}   [{lo:+.4f}, {hi:+.4f}]{pmig:>8.0%}{verd}")
        summary[name] = float(ll[name].mean())
        summary[f"delta_{name}"] = mean

    # --- Ridondanza: beta a inizio stagione con ENTRAMBE le covariate ---
    print("\n" + "=" * 84)
    print("RIDONDANZA — beta stimati a inizio stagione con covariate=(rest_full, midweek)")
    print("(se midweek e' ridondante con rest_full, il suo beta ~0 o instabile)")
    print("=" * 84)
    all_m = loader.load_league("serie_a")
    brf, bmw = [], []
    for s in SEASONS:
        as_of = all_m[all_m.season.astype(str) == s].date.min()
        prom = promoted_teams(all_m, s)
        mdl = DixonColesModel(half_life_days=CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                              shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                              promoted_prior=CFG["promoted_prior"],
                              covariates=("rest_full", "midweek"))
        mdl.fit(all_m, as_of_date=as_of, promoted_teams=prom)
        brf.append(mdl.beta["rest_full"]); bmw.append(mdl.beta["midweek"])
        print(f"  {s}:  beta_rest_full={mdl.beta['rest_full']:+.4f}   beta_midweek={mdl.beta['midweek']:+.4f}")
    print(f"  media: beta_rest_full={np.mean(brf):+.4f}   beta_midweek={np.mean(bmw):+.4f}")

    fp = experiment_log.data_fingerprint(all_m)
    for name in VARIANTS:
        experiment_log.append_run(experiment_log.make_record(
            {"source": "punto2b_midweek", "league": "serie_a", "variant": name,
             **{k: v for k, v in CFG.items() if k != "promoted_prior"}, "promoted_prior": 0.23},
            {"n_matches": n, "x2_model_logloss": summary[name],
             "delta_vs_base": summary.get(f"delta_{name}"),
             "beta_rest_full_mean": float(np.mean(brf)), "beta_midweek_mean": float(np.mean(bmw))}, fp))
    print("\nRun registrati (source=punto2b_midweek).")


if __name__ == "__main__":
    main()
