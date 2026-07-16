"""Fase 53 (tracer) — I bias del mercato si replicano su Premier e La Liga?

La validazione piu' forte possibile dei risultati delle Fasi 50-52: se la
sotto-dispersione (θ>1), il tilt casa/trasferta dei tassi impliciti e il
draw-bias compaiono anche in ALTRE leghe, sono proprieta' dei mercati
calcistici — non un artefatto della Serie A (o di 50 fasi di test sulla stessa
finestra). Tracer VOLUTAMENTE senza port del DC (metodo §1.3): l'analisi
market-side richiede solo quote di chiusura + risultati, che l'utente ha
caricato in `files/football_data_{premier_league,la_liga}_bundle.json`
(8 stagioni ciascuna, formato football-data; stesse preferenze-colonna del
loader Serie A, §5).

Per ogni lega, walk-forward (test = ultime 7 stagioni):
  - θ (double-Poisson), livelli λ/μ, pesi per-classe w_D/w_A — fittati LFO;
  - market (devig molt.) vs shin vs dp vs dp_lvl, appaiato con CI;
  - ROI pari-equilibrio (|λ−μ| < 0.5, soglia fissa Fase 40).

Confronto finale con la Serie A (θ=1.205, livelli 0.973/1.022, w_D=1.09).

Uso:  python scripts/_run_fase53_crossleague.py    (bundle in files/)
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from scripts import _fase52_common as C              # noqa: E402
from scripts._run_fase52_shin import shin_devig      # noqa: E402
from scipy.optimize import minimize                  # noqa: E402

B, SEED = 10_000, 53
_OI = {"H": 0, "D": 1, "A": 2}
LEAGUES = {
    "premier_league": "files/football_data_premier_league_bundle.json",
    "la_liga": "files/football_data_la_liga_bundle.json",
}
ROOT = Path(__file__).resolve().parents[1]


def _pick(df: pd.DataFrame, prefs: list[str]) -> pd.Series:
    """Prima colonna disponibile e finita per riga, nell'ordine di preferenza
    del loader Serie A (fonte unica delle convenzioni-quota, §5)."""
    out = pd.Series(np.nan, index=df.index)
    for c in prefs:
        if c in df.columns:
            take = out.isna() & pd.to_numeric(df[c], errors="coerce").notna()
            out[take] = pd.to_numeric(df[c], errors="coerce")[take]
    return out


def _load_league(bundle_fp: str) -> pd.DataFrame:
    bundle = json.load(open(ROOT / bundle_fp))
    fr = []
    for name in sorted(bundle):
        season = name.rsplit("_", 1)[-1].replace(".csv", "")
        raw = pd.read_csv(io.StringIO(bundle[name]))
        d = pd.DataFrame({
            "season": season,
            "date": pd.to_datetime(raw["Date"], dayfirst=True, format="mixed"),
            "home_team": raw["HomeTeam"], "away_team": raw["AwayTeam"],
            "home_goals": raw["FTHG"], "away_goals": raw["FTAG"],
            "result": raw["FTR"],
        })
        for tgt, prefs in loader._ODDS_PREFERENCE.items():
            d[tgt] = _pick(raw, prefs).values
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over25", "odds_under25"]].to_numpy()).all(axis=1)
    df = df[ok & df.home_goals.notna()].reset_index(drop=True)
    return df.sort_values("date").reset_index(drop=True)


def _invert(df, league: str) -> pd.DataFrame:
    fp = C.CACHE / f"implied_rates_{league}.csv"
    key = ["date", "home_team", "away_team"]
    if fp.exists():
        df = df.merge(pd.read_csv(fp, parse_dates=["date"]), on=key, how="left")
    if "mlam" not in df.columns:
        df["mlam"] = np.nan; df["mmu"] = np.nan
    todo = ~np.isfinite(df["mlam"].to_numpy())
    for i in np.where(todo)[0]:
        r = df.iloc[i]
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, C.RHO)
        df.iloc[i, df.columns.get_loc("mlam")] = lam
        df.iloc[i, df.columns.get_loc("mmu")] = mu
    df[key + ["mlam", "mmu"]].to_csv(fp, index=False)
    return df


def _fit_wclass(P, y):
    def nll(x):
        w = np.array([1.0, x[0], x[1]])
        Q = P * w; Q = Q / Q.sum(1, keepdims=True)
        return -float(np.mean(np.log(np.clip(Q[np.arange(len(y)), y], 1e-15, 1))))
    r = minimize(nll, [1.0, 1.0], method="L-BFGS-B", bounds=[(0.5, 2), (0.5, 2)])
    return np.array([1.0, r.x[0], r.x[1]])


def _analyze(league: str, df: pd.DataFrame, rng) -> dict:
    seasons = sorted(set(df.season))
    acc = {v: [] for v in ("market", "shin", "dp", "dp_lvl")}
    pars = {"theta": [], "lvl_l": [], "lvl_m": [], "w": []}
    roi_eq = []

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        phg = past.home_goals.astype(int).values
        pag = past.away_goals.astype(int).values
        theta = C.fit_theta(past.mlam.values, past.mmu.values, phg, pag)
        c_l = C.fit_level(past.mlam.values, phg)
        c_m = C.fit_level(past.mmu.values, pag)
        P_past = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                           for r in past.itertuples()])
        y_past = np.array([_OI[o] for o in past.result])
        w = _fit_wclass(P_past, y_past)
        pars["theta"].append(theta)
        pars["lvl_l"].append(float(np.exp(c_l))); pars["lvl_m"].append(float(np.exp(c_m)))
        pars["w"].append(w)

        y = np.array([_OI[o] for o in cur.result])
        P_mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                          for r in cur.itertuples()])
        P_shin = np.array([shin_devig(r.odds_home, r.odds_draw, r.odds_away)
                           for r in cur.itertuples()])
        preds = {
            "market": P_mkt,
            "shin": P_shin,
            "dp": C.p1x2(C.dp_matrices(cur.mlam.values, cur.mmu.values, C.RHO, theta)),
            "dp_lvl": C.p1x2(C.dp_matrices(cur.mlam.values * np.exp(c_l),
                                           cur.mmu.values * np.exp(c_m), C.RHO, theta)),
        }
        for v, P in preds.items():
            acc[v].append(-np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1)))
        bal = np.abs(cur.mlam.values - cur.mmu.values)
        m1 = bal < 0.5
        roi_eq.append(np.where(y[m1] == 1, cur.odds_draw.values[m1] - 1.0, -1.0))

    for v in acc:
        acc[v] = np.concatenate(acc[v])
    roi_eq = np.concatenate(roi_eq)
    n = len(acc["market"])

    print("\n" + "=" * 92)
    print(f"FASE 53 — {league.upper()} (n={n}, {len(seasons)-1} stagioni di test)")
    print(f"θ medio={np.mean(pars['theta']):.3f}   livelli λ×{np.mean(pars['lvl_l']):.4f} "
          f"μ×{np.mean(pars['lvl_m']):.4f}   w_D={np.mean([w[1] for w in pars['w']]):.3f} "
          f"w_A={np.mean([w[2] for w in pars['w']]):.3f}")
    print(f"  (Serie A: θ=1.205, λ×0.9726, μ×1.0224, w_D=1.094, w_A=1.033)")
    print("=" * 92)
    out: dict = {"n_matches": int(n),
                 "theta_mean": float(np.mean(pars["theta"])),
                 "lvl_lam_mean": float(np.mean(pars["lvl_l"])),
                 "lvl_mu_mean": float(np.mean(pars["lvl_m"])),
                 "w_draw_mean": float(np.mean([w[1] for w in pars["w"]])),
                 "w_away_mean": float(np.mean([w[2] for w in pars["w"]])),
                 "market__ll": float(acc["market"].mean())}
    print(f"  {'variante':<10}{'1X2':>9}{'Δ vs mercato':>14}{'CI95':>24}{'P(batte)':>10}")
    print(f"  {'market':<10}{acc['market'].mean():>9.4f}")
    for v in ("shin", "dp", "dp_lvl"):
        mean, lo, hi, p = C.boot(acc[v] - acc["market"], rng)
        flag = " ✓CI" if hi < 0 else ""
        print(f"  {v:<10}{acc[v].mean():>9.4f}{mean:>+14.4f}   [{lo:+.4f},{hi:+.4f}]"
              f"{p:>10.0%}{flag}")
        out[f"{v}__ll"] = float(acc[v].mean())
        out[f"{v}__delta"] = mean; out[f"{v}__p"] = p
        out[f"{v}__ci_lo"] = lo; out[f"{v}__ci_hi"] = hi
    m = roi_eq[rng.integers(0, len(roi_eq), (B, len(roi_eq)))].mean(1)
    out["roi_eq"] = float(roi_eq.mean()); out["roi_eq_n"] = int(len(roi_eq))
    out["roi_eq_p"] = float((m > 0).mean())
    print(f"\n  ROI pari-equilibrio (|λ−μ|<0.5): {roi_eq.mean():+.1%}  n={len(roi_eq)}  "
          f"CI[{np.percentile(m,2.5):+.1%},{np.percentile(m,97.5):+.1%}]  "
          f"P(>0)={(m>0).mean():.0%}   (Serie A: +3.2%)")
    return out


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    for league, fp in LEAGUES.items():
        df = _load_league(fp)
        print(f"\n{league}: {len(df)} partite con quote complete "
              f"({sorted(set(df.season))[0]}-{sorted(set(df.season))[-1]}); "
              f"inversione... ({time.time()-t0:.0f}s)", flush=True)
        df = _invert(df, league)
        summary = _analyze(league, df, rng)
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase53_crossleague", "league": league,
             "variant": "bias_mercato_cross_lega_tracer", "rho": C.RHO,
             "bootstrap_B": B, "bootstrap_seed": SEED,
             "data_bundle": fp},
            summary,
            experiment_log.data_fingerprint(df)))
    print(f"\nRun registrati (source=fase53_crossleague, una per lega). "
          f"Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
