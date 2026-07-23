"""Fase 79 — Le prime leve per-lega mai testate su Premier e La Liga:
φ35 (equilibrio-pareggio) e le covariate di congestione (rest_full, midweek).

Perche' QUESTE due leve (dalla rosa, PANCHINA.md):
  - φ35 e' l'unico pezzo del motore titolare con cella ⬜ su Premier/Liga
    (nota ✱2): il draw-bias di MERCATO non si replica in Premier (Fase 53,
    w_D=0.93) e l'EDA della Fase 79 lo conferma sul lato FREQUENZE (equilibrate:
    reale-mercato +0.032 SA, +0.022 Liga, −0.009 Premier). Ma la φ35 corregge
    il deficit del MODELLO Poisson-DC, non del mercato: la domanda aperta e'
    se il deficit-pareggio del DC nelle equilibrate esista anche la'. Il fit
    per-lega di (φ0, κ) risponde; su Premier potrebbe uscire φ0≈0.
  - rest_full/midweek: colonne pronte dalla Fase 59, mai testate fuori Serie A
    (PANCHINA #9/#12, "il test per-lega piu' facile in lista"). L'EDA 79 mostra
    che la Premier e' la lega PIU' congestionata (riposo <=3g nel 21.6% delle
    partite, 36.3% a dicembre vs 15.0% Serie A): se la covariata paga da
    qualche parte, e' li'.

Metodo (identico alla Fase 35/57 per confrontabilita'):
  - walk-forward sulle 6 stagioni di test 2021→2526, config ufficiale per-lega
    (LEAGUE_CONFIGS: δ Premier 0.33, Liga 0.22; il resto comune);
  - varianti: base | phi_equilibrio (--draw-balance) | cov_rest_full | cov_midweek;
  - Δ log-loss 1X2 (e O/U per le covariate) vs base, bootstrap appaiato
    B=10.000; regola pre-dichiarata: adottabile solo se CI95<0;
  - calibrazione P(pari) per quartile |λ−μ| del MODELLO (dove agisce la φ35);
  - parametri fittati per stagione: (φ0, κ) e β delle covariate → il SEGNO
    per-lega e' il risultato principale, non solo il Δ.

Uso:  OMP_NUM_THREADS=1 python scripts/_run_fase79_leve_per_lega.py   (~40 min)
"""
from __future__ import annotations

import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import LEAGUE_CONFIGS                 # noqa: E402
from src.data import loader                           # noqa: E402
from src.evaluation import experiment_log, metrics    # noqa: E402
from src.models.dixon_coles import DixonColesModel    # noqa: E402
from scripts.backtest import run_backtest, promoted_teams  # noqa: E402

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
LEAGUES = ["premier_league", "la_liga"]
VARIANTS = {
    "base":            {},
    "phi_equilibrio":  {"draw_balance": True},
    "cov_rest_full":   {"covariates": ("rest_full",)},
    "cov_midweek":     {"covariates": ("midweek",)},
}
B, SEED = 10_000, 79
_IDX = {"H": 0, "D": 1, "A": 2}
CACHE = Path(__file__).resolve().parents[1] / "outputs"


def _cfg(league: str) -> dict:
    c = LEAGUE_CONFIGS[league]
    return dict(half_life_days=c["half_life_days"], shrinkage=c["shrinkage"],
                shots_blend=c["shots_blend"], blend_signal=c["blend_signal"],
                promoted_prior=(c["promoted_prior"], c["promoted_prior"]))


def _worker(args):
    league, name, season = args
    fp = CACHE / f"db79_{league}_{name}_{season}.csv"
    if fp.exists():
        return league, name, season, pd.read_csv(fp, parse_dates=["date"])
    cfg = _cfg(league)
    df = run_backtest(league, season, cfg["half_life_days"],
                      shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                      blend_signal=cfg["blend_signal"],
                      promoted_prior=cfg["promoted_prior"],
                      verbose=False, **VARIANTS[name])
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return league, name, season, df


def _ll_1x2(df):
    P = np.clip(df[["m_home", "m_draw", "m_away"]].to_numpy(), 1e-15, 1)
    y = np.array([_IDX[o] for o in df.result])
    return -np.log(P[np.arange(len(y)), y])


def _ll_ou(df):
    p = np.clip(df["m_over"].to_numpy(), 1e-15, 1 - 1e-15)
    y = df["is_over"].to_numpy()
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _market_1x2_ll(df):
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


def _fitted_params(league: str) -> dict:
    """Un fit a inizio-stagione per variante: il SEGNO dei parametri per-lega."""
    all_m = loader.load_league(league)
    cfg = _cfg(league)
    out = {"phi0": [], "kappa": [], "beta_rest_full": [], "beta_midweek": []}
    for s in SEASONS:
        cur = all_m[all_m["season"].astype(str) == s]
        as_of = cur["date"].min()
        prom = promoted_teams(all_m, s)
        m1 = DixonColesModel(draw_balance=True, **cfg)
        m1.fit(all_m, as_of_date=as_of, promoted_teams=prom)
        out["phi0"].append(float(m1.draw_phi0))
        out["kappa"].append(float(m1.draw_kappa))
        m2 = DixonColesModel(covariates=("rest_full",), **cfg)
        m2.fit(all_m, as_of_date=as_of, promoted_teams=prom)
        out["beta_rest_full"].append(float(m2.beta["rest_full"]))
        m3 = DixonColesModel(covariates=("midweek",), **cfg)
        m3.fit(all_m, as_of_date=as_of, promoted_teams=prom)
        out["beta_midweek"].append(float(m3.beta["midweek"]))
    return out


def main() -> None:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    jobs = [(lg, name, s) for lg in LEAGUES for name in VARIANTS for s in SEASONS]
    with Pool(4) as pool:
        res = pool.map(_worker, jobs)

    rng = np.random.default_rng(SEED)
    key = ["season", "home_team", "away_team"]
    for league in LEAGUES:
        by_var = {name: pd.concat([df for lg, n, s, df in res
                                   if lg == league and n == name],
                                  ignore_index=True).sort_values(key)
                  .reset_index(drop=True) for name in VARIANTS}
        base = by_var["base"]
        n = len(base)
        ll = {name: _ll_1x2(by_var[name]) for name in VARIANTS}
        llou = {name: _ll_ou(by_var[name]) for name in VARIANTS}
        mkt = _market_1x2_ll(base)
        has = np.isfinite(mkt)

        print("\n" + "=" * 92)
        print(f"FASE 79 — {league.upper()}  (n={n}, 6 stagioni walk-forward; "
              f"mercato 1X2 rif. {mkt[has].mean():.4f})")
        print("=" * 92)
        print(f"  {'variante':<16}{'1X2 LL':>10}{'Δ1X2':>10}{'CI95':>22}{'P':>6}"
              f"{'  |  O/U LL':>11}{'ΔO/U':>10}")
        summary = {}
        for name in VARIANTS:
            if name == "base":
                print(f"  {name:<16}{ll[name].mean():>10.4f}{'—':>10}{'—':>22}"
                      f"{'—':>6}{llou[name].mean():>11.4f}{'—':>10}")
                summary[name] = {"x2_ll": float(ll[name].mean()),
                                 "ou_ll": float(llou[name].mean())}
                continue
            d = ll[name] - ll["base"]
            mean, lo, hi, p = _boot(d, rng)
            dou = float((llou[name] - llou["base"]).mean())
            verd = "  <-- CI<0" if hi < 0 else ""
            print(f"  {name:<16}{ll[name].mean():>10.4f}{mean:>+10.4f}"
                  f"   [{lo:+.4f},{hi:+.4f}]{p:>6.0%}"
                  f"{llou[name].mean():>11.4f}{dou:>+10.4f}{verd}")
            summary[name] = {"x2_ll": float(ll[name].mean()),
                             "delta_1x2": mean, "ci_lo": lo, "ci_hi": hi,
                             "p_improve": p, "ou_ll": float(llou[name].mean()),
                             "delta_ou": dou}

        # Calibrazione pareggio per quartile |lam-mu| del modello (base).
        bal = (base.exp_home_goals - base.exp_away_goals).abs()
        is_draw = (base.result == "D").astype(float).to_numpy()
        mkt_draw = np.full(n, np.nan)
        for i, r in enumerate(base.itertuples()):
            if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
                mkt_draw[i] = metrics.devig_1x2(r.odds_home, r.odds_draw,
                                                r.odds_away)[1]
        q = pd.qcut(bal, 4, labels=["equil", "medio-b", "medio-a", "sbil"])
        print(f"\n  P(pari) per quartile |λ−μ| del modello:")
        print(f"    {'quartile':<9}{'n':>5}{'reale':>8}{'base':>8}{'phiEq':>8}"
              f"{'mercato':>9}")
        for lab in ["equil", "medio-b", "medio-a", "sbil"]:
            m = (q == lab).to_numpy()
            print(f"    {lab:<9}{m.sum():>5}{is_draw[m].mean():>8.3f}"
                  f"{base.m_draw.to_numpy()[m].mean():>8.3f}"
                  f"{by_var['phi_equilibrio'].m_draw.to_numpy()[m].mean():>8.3f}"
                  f"{np.nanmean(mkt_draw[m & np.isfinite(mkt_draw)]):>9.3f}")

        pars = _fitted_params(league)
        print(f"\n  Parametri fittati (un fit a inizio stagione, {len(SEASONS)} stagioni):")
        print(f"    phi0  {['%.3f' % v for v in pars['phi0']]}  media {np.mean(pars['phi0']):.3f}")
        print(f"    kappa {['%.3f' % v for v in pars['kappa']]}  media {np.mean(pars['kappa']):.3f}")
        print(f"    beta_rest_full {['%+.4f' % v for v in pars['beta_rest_full']]}  media {np.mean(pars['beta_rest_full']):+.4f}")
        print(f"    beta_midweek   {['%+.4f' % v for v in pars['beta_midweek']]}  media {np.mean(pars['beta_midweek']):+.4f}")

        all_m = loader.load_league(league)
        fp = experiment_log.data_fingerprint(all_m)
        for name in VARIANTS:
            cfg = _cfg(league)
            rec_cfg = {"source": "fase79_leve_per_lega", "league": league,
                       "variant": name, "seasons": SEASONS,
                       **{k: v for k, v in cfg.items() if k != "promoted_prior"},
                       "promoted_prior": cfg["promoted_prior"][0]}
            mets = {"n_matches": n, **summary[name],
                    "market_1x2_ll": float(mkt[has].mean())}
            if name == "phi_equilibrio":
                mets["phi0_by_season"] = pars["phi0"]
                mets["kappa_by_season"] = pars["kappa"]
            if name == "cov_rest_full":
                mets["beta_by_season"] = pars["beta_rest_full"]
            if name == "cov_midweek":
                mets["beta_by_season"] = pars["beta_midweek"]
            experiment_log.append_run(
                experiment_log.make_record(rec_cfg, mets, fp))
    print("\nRun registrati in experiments/runs.jsonl (source=fase79_leve_per_lega).")


if __name__ == "__main__":
    main()
