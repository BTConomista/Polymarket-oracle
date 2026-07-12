"""Fase 21 — Gradient boosting sul GG/NG (primo modello di famiglia diversa).

Il Dixon-Coles e' forte sugli esiti (1X2) ma **peggio della baseline sul
GG/NG** (Fase 5): la sua struttura quasi-indipendente cattura male la
CORRELAZIONE dei due punteggi (entrambe segnano / almeno una no). Il GG/NG e'
anche l'unico mercato SENZA quote nei dati -> l'unico dove il tetto di
efficienza (Fasi 14/16/20) non e' dimostrato: c'e' spazio reale.

Idea (principio 8 in CLAUDE.md): un modello DIVERSO, valutato SU QUESTO MERCATO.
Gradient boosting che predice P(GG) direttamente, con feature = output del DC
(gol attesi lam/mu, P(GG), P(over) — tutti walk-forward, nessun look-ahead) PIU'
le covariate pre-partita (forma, riposo, valore rosa, assenze). Cosi' il GBM
puo' imparare la correzione di correlazione non-lineare che al DC manca.

Onesta' del backtest:
  - walk-forward per STAGIONE: per la stagione S il GBM e' allenato SOLO sulle
    stagioni precedenti (1819..S-1); le feature del DC sono a loro volta
    walk-forward (il DC vede solo il passato di ogni partita) -> niente
    look-ahead ne' nelle feature ne' nel target;
  - HistGradientBoosting gestisce i NaN nativamente (valore-rosa 84%);
  - confronto a tre: GBM vs DC (m_btts) vs baseline. Baseline in-sample
    (severa, vedi audit Fase 15) E ex-ante (frequenza del training).

REGOLA DI ADOZIONE (dichiarata PRIMA dei numeri): il GBM entra come modello
ufficiale del GG/NG solo se batte il DC con CI95 del Δ < 0 E almeno pareggia
la baseline (che il DC non batteva).

Uso:  python scripts/_run_gbm_btts.py     (8 backtest DC + GBM; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log

# run_backtest importato dopo (serve solo nel worker); sklearn nel main.
from scripts.backtest import run_backtest

# Stagioni con feature DC disponibili (1718 e' solo-training del DC).
FEAT_SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
B, SEED = 10_000, 21


def _worker(season):
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


def ll_binary_rows(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def build_features(df: pd.DataFrame, cov: pd.DataFrame) -> pd.DataFrame:
    """Feature pre-partita (no look-ahead) per il GBM: output DC + covariate."""
    m = df.merge(cov, on=["date", "home_team", "away_team"], how="left")
    lam, mu = m.exp_home_goals, m.exp_away_goals
    feat = pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu,
        "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_p_btts": m.m_btts, "dc_p_over": m.m_over,
        "home_form": m.home_form, "away_form": m.away_form,
        "home_rest": m.home_rest_days_full, "away_rest": m.away_rest_days_full,
        "home_logval": np.log(m.home_squad_value.astype(float)),
        "away_logval": np.log(m.away_squad_value.astype(float)),
        "home_absent": m.home_absent_value_est, "away_absent": m.away_absent_value_est,
    })
    return feat


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier

    with Pool(min(8, len(FEAT_SEASONS))) as pool:
        dfs = dict(pool.map(_worker, FEAT_SEASONS))

    all_m = loader.load_league("serie_a")
    cov = all_m[["date", "home_team", "away_team", "home_form", "away_form",
                 "home_rest_days_full", "away_rest_days_full",
                 "home_squad_value", "away_squad_value",
                 "home_absent_value_est", "away_absent_value_est"]]

    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        c = {"source": "fase21_gbm_btts", "league": "serie_a", "test_season": s,
             "variant": "dc_features", **{k: v for k, v in CFG.items()
             if k != "promoted_prior"}, "promoted_prior": 0.23}
        experiment_log.append_run(experiment_log.make_record(
            c, experiment_log.compute_metrics(df), fp))

    X_all = {s: build_features(dfs[s], cov) for s in FEAT_SEASONS}
    y_all = {s: dfs[s]["is_btts"].to_numpy().astype(int) for s in FEAT_SEASONS}

    print("=" * 84)
    print("GRADIENT BOOSTING sul GG/NG — GBM vs Dixon-Coles vs baseline "
          "(log-loss, piu' basso = meglio)")
    print("=" * 84)
    print(f"  {'stag.':<7}{'GBM':>9}{'DC':>9}{'base(in)':>10}{'base(ex)':>10}"
          f"{'Δ GBM-DC':>11}{'GBM-base':>10}")
    diffs, dc_diffs, gbm_lls, dc_lls, base_lls = [], [], [], [], []
    for s in TEST_SEASONS:
        i = FEAT_SEASONS.index(s)
        Xtr = pd.concat([X_all[t] for t in FEAT_SEASONS[:i]], ignore_index=True)
        ytr = np.concatenate([y_all[t] for t in FEAT_SEASONS[:i]])
        clf = HistGradientBoostingClassifier(
            max_iter=200, max_depth=3, learning_rate=0.05,
            l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
        clf.fit(Xtr, ytr)
        p_gbm = clf.predict_proba(X_all[s])[:, 1]
        y = y_all[s]
        p_dc = dfs[s]["m_btts"].to_numpy()
        base_in = y.mean()                        # in-sample (severa)
        base_ex = ytr.mean()                      # ex-ante (frequenza training)
        ll_g = ll_binary_rows(p_gbm, y)
        ll_d = ll_binary_rows(p_dc, y)
        ll_bi = ll_binary_rows(np.full(len(y), base_in), y)
        ll_be = ll_binary_rows(np.full(len(y), base_ex), y)
        diffs.append(ll_g - ll_d)
        gbm_lls.append(ll_g.mean()); dc_lls.append(ll_d.mean())
        base_lls.append(ll_bi.mean())
        print(f"  {s:<7}{ll_g.mean():>9.4f}{ll_d.mean():>9.4f}{ll_bi.mean():>10.4f}"
              f"{ll_be.mean():>10.4f}{ll_g.mean()-ll_d.mean():>+11.4f}"
              f"{ll_g.mean()-ll_bi.mean():>+10.4f}")

    d_all = np.concatenate(diffs)
    rng = np.random.default_rng(SEED)
    means = d_all[rng.integers(0, len(d_all), (B, len(d_all)))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    print("-" * 84)
    print(f"  {'MEDIA':<7}{np.mean(gbm_lls):>9.4f}{np.mean(dc_lls):>9.4f}"
          f"{np.mean(base_lls):>10.4f}{'':>10}"
          f"{np.mean(gbm_lls)-np.mean(dc_lls):>+11.4f}"
          f"{np.mean(gbm_lls)-np.mean(base_lls):>+10.4f}")
    print(f"\n  Δ GBM-DC pooled (n={len(d_all)}): {d_all.mean():+.4f}  "
          f"CI95 [{lo:+.4f}, {hi:+.4f}]  P(GBM meglio)={float((means<0).mean()):.1%}")
    beats_dc = hi < 0
    beats_base = np.mean(gbm_lls) < np.mean(base_lls)
    print(f"  REGOLA PRE-DICHIARATA: adozione GG/NG solo se CI95<0 E batte la "
          f"baseline -> {'ADOTTARE' if (beats_dc and beats_base) else 'NON adottare'}")
    print(f"    (batte DC con CI95<0: {beats_dc}; batte baseline in media: {beats_base})")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase21_gbm_btts", "league": "serie_a",
         "variant": "gbm_vs_dc_summary", "model": "HistGradientBoosting",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(d_all)),
         "gbm_btts_logloss": float(np.mean(gbm_lls)),
         "dc_btts_logloss": float(np.mean(dc_lls)),
         "baseline_btts_logloss": float(np.mean(base_lls)),
         "gbm_minus_dc_mean": float(d_all.mean()),
         "gbm_minus_dc_ci_lo": float(lo), "gbm_minus_dc_ci_hi": float(hi),
         "gbm_minus_dc_p_neg": float((means < 0).mean())}, fp))


if __name__ == "__main__":
    main()
