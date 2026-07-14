"""Fase 46 — Ensemble dei PREDITTORI STANDALONE (senza quote): DC + GBM + bivariato.

Sul path SENZA quote abbiamo tre predittori indipendenti: il Dixon-Coles (matrice
dai gol+xG), il Poisson bivariato (stessa matrice + correlazione λ3) e il GBM (che
predice ogni mercato direttamente dalle feature). Domanda: **combinarli batte il
migliore singolo?** Fasi 16/23 dicono di no CONTRO IL MERCATO, ma la combinazione
INTRA-standalone (senza quote) non e' mai stata testata a fondo.

Attesa onesta: DC e bivariato sono quasi identici (λ3≈0.11 minuscolo) → ensembling
ridondante; il GBM e' l'unica vista diversa ma da solo perde. Un ensemble puo' al
piu' ridurre la varianza. Test su 1X2 (3-classi), Over 2.5 e GG/NG, walk-forward
(stagioni passate → stagione di test), con CI bootstrap appaiato ENSEMBLE − MIGLIOR
SINGOLO per mercato.

Uso:  python scripts/_run_ensemble_standalone.py   (cache db_base + feature loader; no backtest)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                        # noqa: E402
from src.evaluation import experiment_log          # noqa: E402
from src.models import market_implied as mi        # noqa: E402
from src.models import bivariate_poisson as bp     # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO_DC = -0.05
B, SEED = 10_000, 46
_OI = {"H": 0, "D": 1, "A": 2}
FEATS = ["home_form", "away_form", "home_rest_days_full", "away_rest_days_full",
         "home_squad_value", "away_squad_value",
         "home_absent_value_est", "away_absent_value_est"]


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    allm = loader.load_league("serie_a")
    df = df.merge(allm[["date", "home_team", "away_team", *FEATS]],
                  on=["date", "home_team", "away_team"], how="left")
    df["home_logval"] = np.log(df.home_squad_value.astype(float))
    df["away_logval"] = np.log(df.away_squad_value.astype(float))
    return df


def _gbm_features(df):
    lam, mu = df.exp_home_goals.values, df.exp_away_goals.values
    return pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_ph": df.m_home, "dc_pd": df.m_draw, "dc_pa": df.m_away,
        "dc_pover": df.m_over, "dc_pbtts": df.m_btts,
        "home_form": df.home_form, "away_form": df.away_form,
        "home_rest": df.home_rest_days_full, "away_rest": df.away_rest_days_full,
        "home_logval": df.home_logval, "away_logval": df.away_logval,
        "home_absent": df.home_absent_value_est, "away_absent": df.away_absent_value_est})


def _ll_multi(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))


def _ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def _combine(a, b, c, binary):
    """mean, log-linear pool, DC+GBM (2 modelli diversi). a=DC b=biv c=GBM."""
    eps = 1e-12
    mean = (a + b + c) / 3.0
    lp = np.exp((np.log(a + eps) + np.log(b + eps) + np.log(c + eps)) / 3.0)
    dcg = (a + c) / 2.0
    if not binary:
        mean = mean / mean.sum(axis=1, keepdims=True)
        lp = lp / lp.sum(axis=1, keepdims=True)
        dcg = dcg / dcg.sum(axis=1, keepdims=True)
    return mean, lp, dcg


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV

    df = _load()
    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)

    keys = ["dc", "biv", "gbm", "mean", "logpool", "dc_gbm"]
    acc = {mk: {k: [] for k in keys} for mk in ("x1x2", "over", "btts")}
    l3_hist = []

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])].reset_index(drop=True)
        cur = df[df.season == s].reset_index(drop=True)

        y1 = np.array([_OI[o] for o in cur.result])
        yo = cur.is_over.astype(int).values
        yb = cur.is_btts.astype(int).values

        # DC (dalla cache = matrice τ derivata)
        dc_1x2 = cur[["m_home", "m_draw", "m_away"]].to_numpy()
        dc_over, dc_btts = cur.m_over.values, cur.m_btts.values

        # bivariato: λ3 walk-forward
        l3 = bp.fit_lam3(past.exp_home_goals.values, past.exp_away_goals.values,
                         past.home_goals.values, past.away_goals.values)
        l3_hist.append(l3)
        biv_1x2 = np.zeros((len(cur), 3)); biv_over = np.zeros(len(cur)); biv_btts = np.zeros(len(cur))
        dl, dm = cur.exp_home_goals.values, cur.exp_away_goals.values
        for k in range(len(cur)):
            d = mi.derive_markets(bp.bp_matrix(dl[k], dm[k], l3))
            biv_1x2[k] = [d["home_win"], d["draw"], d["away_win"]]
            biv_over[k], biv_btts[k] = d["over_2.5"], d["btts"]

        # GBM calibrato, walk-forward
        Xtr, Xte = _gbm_features(past), _gbm_features(cur)
        ytr1 = np.array([_OI[o] for o in past.result])
        gbm_1x2 = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                         method="sigmoid", cv=3).fit(Xtr, ytr1).predict_proba(Xte)
        gbm_over = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                          method="sigmoid", cv=3).fit(
            Xtr, past.is_over.astype(int)).predict_proba(Xte)[:, 1]
        gbm_btts = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                          method="sigmoid", cv=3).fit(
            Xtr, past.is_btts.astype(int)).predict_proba(Xte)[:, 1]

        m1, lp1, dg1 = _combine(dc_1x2, biv_1x2, gbm_1x2, binary=False)
        mo, lpo, dgo = _combine(dc_over, biv_over, gbm_over, binary=True)
        mb, lpb, dgb = _combine(dc_btts, biv_btts, gbm_btts, binary=True)

        acc["x1x2"]["dc"].append(_ll_multi(dc_1x2, y1))
        acc["x1x2"]["biv"].append(_ll_multi(biv_1x2, y1))
        acc["x1x2"]["gbm"].append(_ll_multi(gbm_1x2, y1))
        acc["x1x2"]["mean"].append(_ll_multi(m1, y1))
        acc["x1x2"]["logpool"].append(_ll_multi(lp1, y1))
        acc["x1x2"]["dc_gbm"].append(_ll_multi(dg1, y1))
        for mk, dcp, bvp, gbp, me, lp, dg, y in [
                ("over", dc_over, biv_over, gbm_over, mo, lpo, dgo, yo),
                ("btts", dc_btts, biv_btts, gbm_btts, mb, lpb, dgb, yb)]:
            acc[mk]["dc"].append(_ll_bin(dcp, y))
            acc[mk]["biv"].append(_ll_bin(bvp, y))
            acc[mk]["gbm"].append(_ll_bin(gbp, y))
            acc[mk]["mean"].append(_ll_bin(me, y))
            acc[mk]["logpool"].append(_ll_bin(lp, y))
            acc[mk]["dc_gbm"].append(_ll_bin(dg, y))

    for mk in acc:
        for k in acc[mk]:
            acc[mk][k] = np.concatenate(acc[mk][k])

    rng = np.random.default_rng(SEED)
    print("=" * 84)
    print("FASE 46 — ensemble dei predittori standalone (DC + bivariato + GBM), senza quote")
    print(f"λ3 bivariato medio: {np.mean(l3_hist):.3f}   n partite: {len(acc['x1x2']['dc'])}")
    print("=" * 84)
    labels = {"x1x2": "1X2 (3-classi)", "over": "Over 2.5", "btts": "GG/NG"}
    singles, ensembles = ["dc", "biv", "gbm"], ["mean", "logpool", "dc_gbm"]
    summ = {}
    for mk in ("x1x2", "over", "btts"):
        means = {k: float(acc[mk][k].mean()) for k in keys}
        best = min(singles, key=lambda k: means[k])
        print(f"\n  {labels[mk]}:")
        print("    singoli:   " + "   ".join(f"{k} {means[k]:.4f}" for k in singles)
              + f"   (migliore: {best})")
        summ[mk] = {"best_single": best, **{f"ll_{k}": means[k] for k in keys}}
        for e in ensembles:
            mean, lo, hi, pneg = _boot(acc[mk][e] - acc[mk][best], rng)
            flag = "meglio (CI<0)" if hi < 0 else ("nel rumore" if lo < 0 < hi else "peggio")
            print(f"    {e:<9} {means[e]:.4f}   Δ vs {best}: {mean:+.4f} "
                  f"[{lo:+.4f},{hi:+.4f}]  P(aiuta)={1-pneg:.0%}  {flag}")
            summ[mk][f"delta_{e}_vs_best"] = mean

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase46_ensemble", "league": "serie_a", "variant": "standalone_ensemble",
         "rho_dc": RHO_DC, "lam3_mean": float(np.mean(l3_hist)),
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(acc["x1x2"]["dc"])),
         **{f"{mk}__{k}": v for mk, r in summ.items() for k, v in r.items()
            if not isinstance(v, str)}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase46_ensemble).")


if __name__ == "__main__":
    main()
