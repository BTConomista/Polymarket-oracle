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

Controllo di equita': il log-loss punisce durissimo la MIS-CALIBRAZIONE, e un
GBM tende a essere sovra-confidente su un mercato ~50/50. Per non incolpare il
modello di un difetto di calibrazione, si valuta anche una versione CALIBRATA
(Platt/sigmoid in cross-validation sul training): se anche quella perde, il
problema non e' la calibrazione ma l'assenza di segnale.

REGOLA DI ADOZIONE (dichiarata PRIMA dei numeri): il GBM (nella sua versione
migliore, raw o calibrata) entra come modello ufficiale del GG/NG solo se batte
il DC con CI95 del Δ < 0 E almeno pareggia la baseline (che il DC non batteva).

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
    from sklearn.calibration import CalibratedClassifierCV

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

    print("=" * 92)
    print("GRADIENT BOOSTING sul GG/NG — GBM (raw e calibrato) vs Dixon-Coles vs "
          "baseline")
    print("log-loss, piu' basso = meglio; Δ vs DC (>0 = il GBM perde)")
    print("=" * 92)
    print(f"  {'stag.':<7}{'GBM raw':>9}{'GBM cal':>9}{'DC':>9}{'base(in)':>10}"
          f"{'base(ex)':>10}{'Δraw-DC':>10}{'Δcal-DC':>10}")
    diffs, diffs_cal = [], []
    gbm_lls, cal_lls, dc_lls, base_lls = [], [], [], []
    for s in TEST_SEASONS:
        i = FEAT_SEASONS.index(s)
        Xtr = pd.concat([X_all[t] for t in FEAT_SEASONS[:i]], ignore_index=True)
        ytr = np.concatenate([y_all[t] for t in FEAT_SEASONS[:i]])
        kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
                  l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
        clf = HistGradientBoostingClassifier(**kw).fit(Xtr, ytr)
        # Calibrazione Platt (sigmoid) in cross-validation sul solo training.
        cal = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                     method="sigmoid", cv=3).fit(Xtr, ytr)
        p_gbm = clf.predict_proba(X_all[s])[:, 1]
        p_cal = cal.predict_proba(X_all[s])[:, 1]
        y = y_all[s]
        p_dc = dfs[s]["m_btts"].to_numpy()
        ll_g = ll_binary_rows(p_gbm, y)
        ll_c = ll_binary_rows(p_cal, y)
        ll_d = ll_binary_rows(p_dc, y)
        ll_bi = ll_binary_rows(np.full(len(y), y.mean()), y)
        ll_be = ll_binary_rows(np.full(len(y), ytr.mean()), y)
        diffs.append(ll_g - ll_d); diffs_cal.append(ll_c - ll_d)
        gbm_lls.append(ll_g.mean()); cal_lls.append(ll_c.mean())
        dc_lls.append(ll_d.mean()); base_lls.append(ll_bi.mean())
        print(f"  {s:<7}{ll_g.mean():>9.4f}{ll_c.mean():>9.4f}{ll_d.mean():>9.4f}"
              f"{ll_bi.mean():>10.4f}{ll_be.mean():>10.4f}"
              f"{ll_g.mean()-ll_d.mean():>+10.4f}{ll_c.mean()-ll_d.mean():>+10.4f}")

    rng = np.random.default_rng(SEED)
    def ci(chunks):
        d = np.concatenate(chunks)
        m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
        return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()
    print("-" * 92)
    print(f"  {'MEDIA':<7}{np.mean(gbm_lls):>9.4f}{np.mean(cal_lls):>9.4f}"
          f"{np.mean(dc_lls):>9.4f}{np.mean(base_lls):>10.4f}")
    for tag, chunks in [("GBM raw - DC", diffs), ("GBM calibrato - DC", diffs_cal)]:
        mean, lo, hi, pn = ci(chunks)
        print(f"  Δ {tag:<20} {mean:+.4f}  CI95 [{lo:+.4f}, {hi:+.4f}]  "
              f"P(GBM meglio)={pn:.1%}")

    best_gbm = min(np.mean(gbm_lls), np.mean(cal_lls))
    mean_c, lo_c, hi_c, _ = ci(diffs_cal)
    mean_r, lo_r, hi_r, _ = ci(diffs)
    beats_dc = min(hi_c, hi_r) < 0
    beats_base = best_gbm < np.mean(base_lls)
    print(f"\n  REGOLA PRE-DICHIARATA: adozione GG/NG solo se (raw O calibrato) "
          f"batte DC con CI95<0 E batte baseline")
    print(f"  -> {'ADOTTARE' if (beats_dc and beats_base) else 'NON adottare'} "
          f"(batte DC: {beats_dc}; batte baseline: {beats_base})")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase21_gbm_btts", "league": "serie_a",
         "variant": "gbm_vs_dc_summary", "model": "HistGradientBoosting",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(sum(len(d) for d in diffs)),
         "gbm_raw_btts_logloss": float(np.mean(gbm_lls)),
         "gbm_cal_btts_logloss": float(np.mean(cal_lls)),
         "dc_btts_logloss": float(np.mean(dc_lls)),
         "baseline_btts_logloss": float(np.mean(base_lls)),
         "gbm_raw_minus_dc_mean": float(mean_r), "gbm_raw_minus_dc_ci_lo": float(lo_r),
         "gbm_raw_minus_dc_ci_hi": float(hi_r),
         "gbm_cal_minus_dc_mean": float(mean_c), "gbm_cal_minus_dc_ci_lo": float(lo_c),
         "gbm_cal_minus_dc_ci_hi": float(hi_c)}, fp))


if __name__ == "__main__":
    main()
