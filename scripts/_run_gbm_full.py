"""Punto 1+2 della roadmap post-audit — GBM col SET DI FEATURE COMPLETO.

La Fase 22 aveva provato il GBM con un set ridotto di covariate ({forma, rest_full,
valore, assenze, midweek}). MAI testate insieme, nello stesso modello: stakes
(Fase 32, il lead piu' forte, non-lineare), luck/ppda/deep (Fase 33). Qui il GBM
riceve il SET COMPLETO, SENZA feature selection preventiva, per vedere se la
combinazione non-lineare (effetti-soglia che si sommano) produce un guadagno REALE
o solo overfitting rispetto al numero di feature.

Confronti (walk-forward per stagione, GBM calibrato Platt, headline 1X2 + GG/NG):
  - feature-set:  dc  |  dc+cov_RIDOTTO (Fase 22)  |  dc+cov_COMPLETO (+stakes+luck+ppda+deep)
  - overfitting:  log-loss TRAIN vs TEST per ciascun set (gap grande = overfit);
  - dove vive il segnale: sottoinsieme MISMATCH stakes (una decisa/una in corsa);
  - feature importance (permutazione) sul set completo, stagione 2526.

Uso:  python scripts/_run_gbm_full.py     (8 backtest DC + GBM; ~minuti; serve sklearn)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                        # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from scripts.backtest import run_backtest          # noqa: E402

FEAT_SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
CACHE = Path(__file__).resolve().parents[1] / "outputs"
B, SEED = 10_000, 12
_OI = {"H": 0, "D": 1, "A": 2}


def _dc_backtest(season):
    fp = CACHE / f"dc_bt_{season}.csv"
    if fp.exists():
        return pd.read_csv(fp, parse_dates=["date"])
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return df


def dc_block(df, cov):
    m = df.merge(cov, on=["date", "home_team", "away_team"], how="left")
    lam, mu = m.exp_home_goals, m.exp_away_goals
    d = pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_ph": m.m_home, "dc_pd": m.m_draw, "dc_pa": m.m_away,
        "dc_pover": m.m_over, "dc_pbtts": m.m_btts})
    return d, m


def cov_reduced(m):   # il set della Fase 22
    return pd.DataFrame({
        "home_form": m.home_form, "away_form": m.away_form,
        "home_rest": m.home_rest_days_full, "away_rest": m.away_rest_days_full,
        "home_logval": np.log(m.home_squad_value.astype(float)),
        "away_logval": np.log(m.away_squad_value.astype(float)),
        "home_absent": m.home_absent_value_est, "away_absent": m.away_absent_value_est,
        "home_midweek": m.home_midweek_europe, "away_midweek": m.away_midweek_europe})


def cov_full(m):      # + stakes, luck, ppda, deep (mai nel GBM)
    r = cov_reduced(m)
    extra = pd.DataFrame({
        "home_settled": m.home_settled, "away_settled": m.away_settled,
        "stakes_mismatch": (m.home_settled != m.away_settled).astype(float),
        "home_luck": m.home_luck, "away_luck": m.away_luck,
        "home_ppda": m.home_ppda_roll, "away_ppda": m.away_ppda_roll,
        "home_deep": m.home_deep_roll, "away_deep": m.away_deep_roll})
    return pd.concat([r, extra], axis=1)


def ll_multi(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))


def ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.inspection import permutation_importance

    with Pool(min(8, len(FEAT_SEASONS))) as pool:
        dfs = dict(zip(FEAT_SEASONS, pool.map(_dc_backtest, FEAT_SEASONS)))
    all_m = loader.load_league("serie_a")
    covcols = ["date", "home_team", "away_team", "home_form", "away_form",
               "home_rest_days_full", "away_rest_days_full", "home_squad_value",
               "away_squad_value", "home_absent_value_est", "away_absent_value_est",
               "home_midweek_europe", "away_midweek_europe", "home_settled", "away_settled",
               "home_luck", "away_luck", "home_ppda_roll", "away_ppda_roll",
               "home_deep_roll", "away_deep_roll"]
    cov = all_m[covcols]

    blk = {}
    for s in FEAT_SEASONS:
        d, m = dc_block(dfs[s], cov)
        blk[s] = {"dc": d, "dc+cov_rid": pd.concat([d, cov_reduced(m)], axis=1),
                  "dc+cov_full": pd.concat([d, cov_full(m)], axis=1), "m": m}

    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
    FEATSETS = ["dc", "dc+cov_rid", "dc+cov_full"]

    def targets(df, market):
        res = df.result.to_numpy()
        if market == "1X2":
            return np.array([_OI[o] for o in res]), "multi"
        return (df.is_btts.to_numpy().astype(int), "bin") if market == "GG/NG" else None

    def run_market(market):
        """Ritorna per feature-set: (test_ll_rows, train_ll_mean, mismatch_ll_rows)."""
        out = {fs: {"test": [], "train": [], "mm": []} for fs in FEATSETS}
        dc_test = []
        for s in TEST_SEASONS:
            i = FEAT_SEASONS.index(s)
            ytr, kind = targets(pd.concat([dfs[t] for t in FEAT_SEASONS[:i]], ignore_index=True), market)
            yte, _ = targets(dfs[s], market)
            mism = (blk[s]["m"].home_settled != blk[s]["m"].away_settled).to_numpy()
            for fs in FEATSETS:
                Xtr = pd.concat([blk[t][fs] for t in FEAT_SEASONS[:i]], ignore_index=True)
                Xte = blk[s][fs]
                base = HistGradientBoostingClassifier(**kw)
                clf = CalibratedClassifierCV(base, method="sigmoid", cv=3).fit(Xtr, ytr)
                if kind == "multi":
                    Pte = clf.predict_proba(Xte); Ptr = clf.predict_proba(Xtr)
                    out[fs]["test"].append(ll_multi(Pte, yte))
                    out[fs]["train"].append(ll_multi(Ptr, ytr).mean())
                    out[fs]["mm"].append(ll_multi(Pte[mism], yte[mism]))
                else:
                    pte = clf.predict_proba(Xte)[:, 1]; ptr = clf.predict_proba(Xtr)[:, 1]
                    out[fs]["test"].append(ll_bin(pte, yte))
                    out[fs]["train"].append(ll_bin(ptr, ytr).mean())
                    out[fs]["mm"].append(ll_bin(pte[mism], yte[mism]))
            # DC di riferimento (stesso mercato)
            if market == "1X2":
                dc_test.append(ll_multi(dfs[s][["m_home", "m_draw", "m_away"]].to_numpy(), yte))
            else:
                dc_test.append(ll_bin(dfs[s].m_btts.to_numpy(), yte))
        agg = {fs: {"test": np.concatenate(out[fs]["test"]),
                    "train": float(np.mean(out[fs]["train"])),
                    "mm": np.concatenate(out[fs]["mm"])} for fs in FEATSETS}
        return agg, np.concatenate(dc_test)

    rng = np.random.default_rng(SEED)
    all_m_fp = experiment_log.data_fingerprint(all_m)
    summary = {}
    for market in ["1X2", "GG/NG"]:
        agg, dc = run_market(market)
        print("=" * 92)
        print(f"GBM SET COMPLETO — mercato {market} (walk-forward, calibrato); DC rif. = {dc.mean():.4f}")
        print("=" * 92)
        print(f"  {'feature-set':<14}{'test LL':>10}{'train LL':>10}{'overfit':>9}"
              f"{'Δ vs dc':>10}{'CI95 (vs dc-feat)':>22}{'mismatch LL':>13}")
        base_test = agg["dc"]["test"]
        for fs in FEATSETS:
            t = agg[fs]["test"]
            d = t - base_test
            mean, lo, hi, pmig = boot(d, rng) if fs != "dc" else (0, 0, 0, 0)
            over = agg[fs]["test"].mean() - agg[fs]["train"]
            ci = f"[{lo:+.4f}, {hi:+.4f}]" if fs != "dc" else "—"
            print(f"  {fs:<14}{t.mean():>10.4f}{agg[fs]['train']:>10.4f}{over:>+9.4f}"
                  f"{mean:>+10.4f}{ci:>22}{agg[fs]['mm'].mean():>13.4f}")
            summary[f"{market}_{fs}_test"] = float(t.mean())
            summary[f"{market}_{fs}_train"] = float(agg[fs]["train"])
            summary[f"{market}_{fs}_mismatch"] = float(agg[fs]["mm"].mean())
        # confronto diretto full vs ridotto
        dfull = agg["dc+cov_full"]["test"] - agg["dc+cov_rid"]["test"]
        mean, lo, hi, pmig = boot(dfull, rng)
        print(f"\n  full vs ridotto: Δ={mean:+.4f} CI[{lo:+.4f},{hi:+.4f}] P(full meglio)={pmig:.0%}")
        print(f"  mismatch (dove vive stakes): dc={agg['dc']['mm'].mean():.4f}  "
              f"ridotto={agg['dc+cov_rid']['mm'].mean():.4f}  full={agg['dc+cov_full']['mm'].mean():.4f}"
              f"  (n={len(agg['dc']['mm'])})")
        summary[f"{market}_full_vs_rid_delta"] = mean
        summary[f"{market}_full_vs_rid_ci_lo"] = lo
        summary[f"{market}_full_vs_rid_ci_hi"] = hi
        print()

    # --- Feature importance (permutazione) sul set completo, 1X2, stagione 2526 ---
    print("=" * 92)
    print("FEATURE IMPORTANCE (permutazione, neg-log-loss) — 1X2, dc+cov_full, train<2526 test=2526")
    print("=" * 92)
    i = FEAT_SEASONS.index("2526")
    ytr = np.array([_OI[o] for o in pd.concat([dfs[t] for t in FEAT_SEASONS[:i]], ignore_index=True).result])
    yte = np.array([_OI[o] for o in dfs["2526"].result])
    Xtr = pd.concat([blk[t]["dc+cov_full"] for t in FEAT_SEASONS[:i]], ignore_index=True)
    Xte = blk["2526"]["dc+cov_full"]
    clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw), method="sigmoid", cv=3).fit(Xtr, ytr)
    imp = permutation_importance(clf, Xte, yte, scoring="neg_log_loss",
                                 n_repeats=8, random_state=SEED)
    order = np.argsort(imp.importances_mean)[::-1]
    print(f"  {'feature':<18}{'importanza (Δ neg-log-loss)':>28}")
    for k in order[:14]:
        print(f"  {Xte.columns[k]:<18}{imp.importances_mean[k]:>+18.5f} ± {imp.importances_std[k]:.5f}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "gbm_full", "league": "serie_a", "variant": "full_vs_reduced",
         "model": "HistGradientBoosting_calibrated", "bootstrap_B": B, "bootstrap_seed": SEED,
         **{k: v for k, v in CFG.items() if k != "promoted_prior"}, "promoted_prior": 0.23},
        {"n_test": int(len(base_test)), **summary}, all_m_fp))
    print("\nRun registrato in experiments/runs.jsonl (source=gbm_full).")


if __name__ == "__main__":
    main()
