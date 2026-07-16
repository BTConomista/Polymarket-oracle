"""Fase 51 (E) — Due simmetrie mancanti: GBM bespoke sul PAREGGIO e recal O/U del mercato.

1. Il Track C della Fase 50 (GBM bespoke per mercato) non includeva il PAREGGIO —
   proprio il mercato dove il progetto ha trovato l'unico edge di calibrazione
   (Fasi 35/40). Qui si chiude la simmetria: GBM binario pari/no-pari, feature
   DC-block + mercato (|λ−μ|, prob pari devigata) + la predizione dell'engine
   φ35, calibrato (Platt cv=3), vs l'engine market-implied+φ35.
2. Il 50-ter ricalibrava per-classe il mercato 1X2; l'O/U 2.5 mai:
   q_over ∝ w·p_over devigata, w fittato leave-future-out (regola >= 2 stagioni).

Uso:  python scripts/_run_fase51_draw_ou.py    (cache db_base; sklearn extra)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 51
FEATS = ["home_form", "away_form", "home_rest_days_full", "away_rest_days_full",
         "home_squad_value", "away_squad_value", "home_absent_value_est",
         "away_absent_value_est", "home_settled", "away_settled"]


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    df = df[ok].reset_index(drop=True)
    allm = loader.load_league("serie_a")
    df = df.merge(allm[["date", "home_team", "away_team", *FEATS]],
                  on=["date", "home_team", "away_team"], how="left")
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    pD_m = np.zeros(len(df)); pO_m = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
        pD_m[i], pO_m[i] = pD, pO
    df["mlam"], df["mmu"] = lam, mu
    df["p_draw_mkt"], df["p_over_mkt"] = pD_m, pO_m
    return df


def _engine_draw(df, phi_by_season):
    out = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        phi0, kappa = phi_by_season[r.season]
        M = mi.score_matrix(r.mlam, r.mmu, RHO,
                            diag_inflation=mi.balance_phi(r.mlam, r.mmu, phi0, kappa))
        out[i] = float(np.trace(M))
    return out


def _features(df, eng_draw):
    lam, mu = df.exp_home_goals.values, df.exp_away_goals.values
    return pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu, "dc_balance": np.abs(lam - mu),
        "dc_pd": df.m_draw, "dc_ph": df.m_home, "dc_pa": df.m_away,
        "mlam": df.mlam, "mmu": df.mmu, "m_balance": np.abs(df.mlam - df.mmu),
        "m_tot": df.mlam + df.mmu,
        "p_draw_mkt": df.p_draw_mkt, "eng_draw": eng_draw,
        "home_form": df.home_form, "away_form": df.away_form,
        "home_logval": np.log(df.home_squad_value.astype(float)),
        "away_logval": np.log(df.away_squad_value.astype(float)),
        "home_settled": df.home_settled.astype(float),
        "away_settled": df.away_settled.astype(float),
    })


def _ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def main():
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.ensemble import HistGradientBoostingClassifier

    t0 = time.time()
    df = _load()
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in SEASONS if s in set(df.season)]

    phi_by_season: dict = {seasons[0]: (0.0, 0.0)}
    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        is_dr = (past.home_goals == past.away_goals).astype(float).values
        phi_by_season[s] = mi.fit_balance_phi(past.mlam.values, past.mmu.values,
                                              is_dr, RHO)
    eng = _engine_draw(df, phi_by_season)

    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
    ll_eng, ll_gbm, ll_mkt = [], [], []
    ll_ou_raw, ll_ou_rec, w_over_l = [], [], []

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past_idx = df.season.isin(seasons[:i]).to_numpy()
        cur_idx = (df.season == s).to_numpy()
        past, cur = df[past_idx], df[cur_idx]
        ytr = (past.home_goals == past.away_goals).astype(int).values
        ycu = (cur.home_goals == cur.away_goals).astype(int).values

        clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                     method="sigmoid", cv=3)
        p_gbm = clf.fit(_features(past, eng[past_idx]), ytr
                        ).predict_proba(_features(cur, eng[cur_idx]))[:, 1]
        ll_eng.append(_ll_bin(eng[cur_idx], ycu.astype(float)))
        ll_gbm.append(_ll_bin(p_gbm, ycu.astype(float)))
        ll_mkt.append(_ll_bin(cur.p_draw_mkt.values, ycu.astype(float)))

        # O/U 2.5: recal per-classe binaria del mercato (>= 2 stagioni di fit)
        if i >= 2:
            y_ou_tr = ((past.home_goals + past.away_goals) >= 3).astype(float).values
            p_tr = past.p_over_mkt.values

            def nll(w):
                q = np.clip(w * p_tr / (w * p_tr + (1 - p_tr)), 1e-15, 1 - 1e-15)
                return float(-np.mean(y_ou_tr * np.log(q) + (1 - y_ou_tr) * np.log(1 - q)))
            w = float(minimize_scalar(nll, bounds=(0.5, 2.0), method="bounded",
                                      options={"xatol": 1e-4}).x)
            w_over_l.append(w)
            y_ou = ((cur.home_goals + cur.away_goals) >= 3).astype(float).values
            p_cu = cur.p_over_mkt.values
            q_cu = w * p_cu / (w * p_cu + (1 - p_cu))
            ll_ou_raw.append(_ll_bin(p_cu, y_ou))
            ll_ou_rec.append(_ll_bin(q_cu, y_ou))
        print(f"  stagione {s} ({time.time()-t0:.0f}s)", flush=True)

    ll_eng = np.concatenate(ll_eng); ll_gbm = np.concatenate(ll_gbm)
    ll_mkt = np.concatenate(ll_mkt)
    ll_ou_raw = np.concatenate(ll_ou_raw); ll_ou_rec = np.concatenate(ll_ou_rec)
    rng = np.random.default_rng(SEED)

    print("\n" + "=" * 88)
    print(f"FASE 51 (E) — pareggio bespoke e recal O/U (n={len(ll_eng)})")
    print("=" * 88)
    mean, lo, hi, p = _boot(ll_gbm - ll_eng, rng)
    print(f"  PAREGGIO:  mercato {ll_mkt.mean():.4f}   engine φ35 {ll_eng.mean():.4f}   "
          f"GBM bespoke {ll_gbm.mean():.4f}")
    print(f"    Δ (GBM − engine) = {mean:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  P(migliora)={p:.0%}")
    mean2, lo2, hi2, p2 = _boot(ll_ou_rec - ll_ou_raw, rng)
    print(f"\n  O/U 2.5:  mercato {ll_ou_raw.mean():.4f}   recal w_over {ll_ou_rec.mean():.4f}"
          f"   (w medio {np.mean(w_over_l):.3f})")
    print(f"    Δ (recal − mercato) = {mean2:+.4f}  CI[{lo2:+.4f},{hi2:+.4f}]  "
          f"P(migliora)={p2:.0%}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase51_draw_ou", "league": "serie_a",
         "variant": "gbm_bespoke_pareggio_e_recal_ou", "rho": RHO,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(ll_eng)),
         "draw_market": float(ll_mkt.mean()), "draw_engine": float(ll_eng.mean()),
         "draw_gbm": float(ll_gbm.mean()), "draw_gbm_delta": mean,
         "draw_gbm_ci_lo": lo, "draw_gbm_ci_hi": hi, "draw_gbm_p": p,
         "ou_market": float(ll_ou_raw.mean()), "ou_recal": float(ll_ou_rec.mean()),
         "ou_recal_delta": mean2, "ou_recal_ci_lo": lo2, "ou_recal_ci_hi": hi2,
         "ou_recal_p": p2, "w_over_mean": float(np.mean(w_over_l))},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase51_draw_ou). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
