"""Fase 50 (seguito) — Ricalibrazione per-classe del MERCATO stesso (bias H/D/A).

La ricalibrazione dei tassi (fase50_rates_recal) ha misurato un bias sistematico
dei tassi impliciti: λ del mercato ALTO (~1.5%), μ BASSO (~2%) — il bias-casa dei
book sopravvive al devig moltiplicativo. Domanda mai posta: le probabilita' 1X2
del MERCATO stesso si migliorano con una ricalibrazione per-classe walk-forward?

    q_i ∝ w_i · p_mkt,i      con w_H ≡ 1 e (w_D, w_A) fittati sulle stagioni passate

E' l'analogo della Fase 10 (ricalibrazione per-classe del modello) applicato al
mercato: se il bias e' stabile, "batte la chiusura" in log-loss. Regola
PRE-DICHIARATA: il fit richiede >= 2 stagioni di training (>=760 partite) — il fit
su una sola stagione e' rumore (w_D 1.13 dal solo 1819 → +0.0109 sul 1920).

Uso:  python scripts/_run_fase50_market_recal.py    (cache db_base)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
MIN_TRAIN_SEASONS = 2          # regola pre-dichiarata (vedi docstring)
B, SEED = 10_000, 50
_OI = {"H": 0, "D": 1, "A": 2}


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away"]].to_numpy()).all(axis=1)
    return df[ok].reset_index(drop=True)


def _fit_w(P, y):
    def nll(x):
        w = np.array([1.0, x[0], x[1]])
        Q = P * w; Q = Q / Q.sum(1, keepdims=True)
        return -np.mean(np.log(np.clip(Q[np.arange(len(y)), y], 1e-15, 1)))
    r = minimize(nll, [1.0, 1.0], method="L-BFGS-B", bounds=[(0.5, 2), (0.5, 2)])
    return np.array([1.0, r.x[0], r.x[1]])


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def main():
    df = _load()
    P = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in df.itertuples()])
    y = np.array([_OI[r] for r in df.result])
    season = df.season.values

    print("=" * 78)
    print("FASE 50 — ricalibrazione per-classe del MERCATO (walk-forward, "
          f">={MIN_TRAIN_SEASONS} stagioni di fit)")
    print("=" * 78)
    raw_all, rec_all, ws = [], [], []
    for i, s in enumerate(SEASONS):
        if i < MIN_TRAIN_SEASONS:
            continue
        past = np.isin(season, SEASONS[:i]); cur = season == s
        if not cur.any():
            continue
        w = _fit_w(P[past], y[past])
        Q = P[cur] * w; Q = Q / Q.sum(1, keepdims=True)
        n = int(cur.sum())
        ll_raw = -np.log(np.clip(P[cur][np.arange(n), y[cur]], 1e-15, 1))
        ll_rec = -np.log(np.clip(Q[np.arange(n), y[cur]], 1e-15, 1))
        raw_all.append(ll_raw); rec_all.append(ll_rec); ws.append(w)
        print(f"  {s}: mercato {ll_raw.mean():.4f} -> recal {ll_rec.mean():.4f} "
              f"(Δ {ll_rec.mean()-ll_raw.mean():+.4f})   w_D={w[1]:.3f} w_A={w[2]:.3f}")

    raw = np.concatenate(raw_all); rec = np.concatenate(rec_all)
    rng = np.random.default_rng(SEED)
    mean, lo, hi, p = _boot(rec - raw, rng)
    wins = sum(float(r.mean()) < float(b.mean()) for r, b in zip(rec_all, raw_all))
    print(f"\n  POOLED (n={len(raw)}): mercato {raw.mean():.4f} -> recal {rec.mean():.4f}")
    print(f"  Δ = {mean:+.4f}  CI95 [{lo:+.4f}, {hi:+.4f}]  P(migliora) = {p:.0%}  "
          f"({wins}/{len(rec_all)} stagioni)")
    print(f"  pesi medi: w_D={np.mean([w[1] for w in ws]):.3f}  "
          f"w_A={np.mean([w[2] for w in ws]):.3f}  (pari e trasferta sotto-prezzate)")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase50_market_recal", "league": "serie_a",
         "variant": "recal_per_classe_del_mercato",
         "min_train_seasons": MIN_TRAIN_SEASONS, "seasons": SEASONS,
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(raw)), "market_ll": float(raw.mean()),
         "recal_ll": float(rec.mean()), "delta": mean,
         "ci_lo": lo, "ci_hi": hi, "p_improve": p,
         "seasons_improved": int(wins), "seasons_total": len(rec_all),
         "w_draw_mean": float(np.mean([w[1] for w in ws])),
         "w_away_mean": float(np.mean([w[2] for w in ws]))},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase50_market_recal).")


if __name__ == "__main__":
    main()
