"""Fase 20 — Anatomia dei residui: TUTTE le covariate pre-partita insieme.

La Fase 13 ha testato solo "la forma" come predittore dell'errore del modello.
Qui l'analisi completa: il residuo del modello (punti reali casa - attesi,
convenzione Fase 13) e' predetto da QUALCUNA delle covariate pre-partita
disponibili? Incluse quelle di ESTREMITA' mai provate:
  - |scarto di valore rosa| (mismatch di talento estremo, non il valore assoluto
    gia' bocciato in Fase 4c);
  - |differenza di riposo| (congestione asimmetrica estrema);
  - carico totale di assenze (somma, non differenza);
  - livello di gol attesi (partite ad alto/basso punteggio);
  - confidenza del modello e DISSENSO col mercato (adverse selection).

Metodo (come Fase 13): regressione multivariata in-sample con benchmark di
rumore R²≈k/n + benchmark empirico a feature casuali. Un R² a livello rumore
IN-SAMPLE implica a fortiori nessun segnale out-of-sample. Piu' il test di
adverse selection separato: il gap vs mercato e' piu' grande dove il modello
dissente dal mercato?

Uso:  python scripts/_run_residuals.py     (6 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
PC = ["m_home", "m_draw", "m_away"]
SEED = 20


def _worker(season):
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


def zscore(x: np.ndarray) -> np.ndarray:
    """Standardizza ignorando i NaN; NaN -> 0 (neutro), come le covariate del
    modello. Feature costante -> tutti 0."""
    x = np.asarray(x, float)
    m, s = np.nanmean(x), np.nanstd(x)
    if not np.isfinite(s) or s < 1e-9:
        return np.zeros_like(x)
    return np.nan_to_num((x - m) / s)


def ols_r2(X: np.ndarray, y: np.ndarray) -> float:
    """R² di una OLS con intercetta."""
    A = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ beta
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def main():
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, SEASONS))

    all_m = loader.load_league("serie_a")
    feat_cols = ["home_xg", "away_xg", "home_ppda", "away_ppda", "home_deep",
                 "away_deep", "home_squad_value", "away_squad_value",
                 "home_absent_value_est", "away_absent_value_est",
                 "home_rest_days_full", "away_rest_days_full",
                 "home_midweek_europe", "away_midweek_europe",
                 "home_form", "away_form"]
    am = all_m[["date", "home_team", "away_team"] + feat_cols]

    pred = pd.concat([dfs[s] for s in SEASONS], ignore_index=True)
    pred = pred.merge(am, on=["date", "home_team", "away_team"], how="left")

    # Registro replicabile (regola Fase 15).
    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        cfg = {"source": "fase20_residuals", "league": "serie_a",
               "test_season": s, **{k: v for k, v in CFG.items()
               if k != "promoted_prior"}, "promoted_prior": 0.23}
        experiment_log.append_run(experiment_log.make_record(
            cfg, experiment_log.compute_metrics(df), fp))

    # --- Target: residuo del modello (punti reali casa - attesi) ---
    exp_home = 3 * pred.m_home + 1 * pred.m_draw
    real_home = np.where(pred.result == "H", 3.0,
                         np.where(pred.result == "D", 1.0, 0.0))
    resid = real_home - exp_home.to_numpy()

    # --- Feature pre-partita, incluse quelle di ESTREMITA' (nuove) ---
    sv_h = np.log(pred.home_squad_value.to_numpy(float))
    sv_a = np.log(pred.away_squad_value.to_numpy(float))
    rest_h = pred.home_rest_days_full.to_numpy(float)
    rest_a = pred.away_rest_days_full.to_numpy(float)
    abs_h = pred.home_absent_value_est.to_numpy(float)
    abs_a = pred.away_absent_value_est.to_numpy(float)
    model = pred[PC].to_numpy()
    # mercato devigato per riga (per confidenza/dissenso)
    mkt = np.full((len(pred), 3), np.nan)
    for i, r in enumerate(pred.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)

    features = {
        # direzionali (gia' note/parziali, per completezza)
        "forma casa-osp": pred.home_form.to_numpy(float) - pred.away_form.to_numpy(float),
        "valore log casa-osp": sv_h - sv_a,
        "riposo casa-osp": rest_h - rest_a,
        "assenze osp-casa": abs_a - abs_h,
        # ESTREMITA' (mai testate)
        "|scarto valore|": np.abs(sv_h - sv_a),
        "|scarto riposo|": np.abs(rest_h - rest_a),
        "assenze TOTALI": abs_h + abs_a,
        "gol attesi (P over)": pred.m_over.to_numpy(float),
        "midweek europa (o/o)": (pred.home_midweek_europe.to_numpy(float)
                                 + pred.away_midweek_europe.to_numpy(float)),
        # confidenza / adverse selection
        "confidenza modello": model.max(axis=1),
        "dissenso vs mercato": np.nansum(np.abs(model - mkt), axis=1),
    }

    n = len(resid)
    print("=" * 78)
    print(f"ANATOMIA DEI RESIDUI — {n} partite, 6 stagioni")
    print("Target: residuo = punti reali casa - attesi dal modello (>0 = casa meglio)")
    print("=" * 78)
    thr = 1.0 / np.sqrt(n)
    print(f"\n[1] Correlazioni univariate (soglia rumore |r|~{thr:.3f} = 1/√n)")
    print(f"  {'feature':<24}{'corr':>9}{'':>4}")
    for name, raw in features.items():
        z = zscore(raw)
        r = float(np.corrcoef(z, resid)[0, 1])
        flag = "  <-- oltre rumore" if abs(r) > 2 * thr else ""
        print(f"  {name:<24}{r:>+9.4f}{flag}")

    # [2] Multivariata: R² con tutte le feature vs benchmark rumore.
    X = np.column_stack([zscore(v) for v in features.values()])
    k = X.shape[1]
    r2 = ols_r2(X, resid)
    rng = np.random.default_rng(SEED)
    rand_r2 = np.mean([ols_r2(rng.standard_normal((n, k)), resid)
                       for _ in range(200)])
    print(f"\n[2] Regressione MULTIVARIATA ({k} feature)")
    print(f"  R² reale            = {r2:.4f}")
    print(f"  R² da rumore (k/n)  = {k / n:.4f}   (atteso analitico)")
    print(f"  R² feature casuali  = {rand_r2:.4f}   (media 200 draw, seed {SEED})")
    verdict = ("il residuo NON e' predetto dalle covariate (R² a livello rumore)"
               if r2 <= 3 * rand_r2 else
               "ATTENZIONE: R² sopra il rumore, indagare")
    print(f"  -> {verdict}")

    # [3] Adverse selection: il gap vs mercato cresce col dissenso?
    print("\n[3] ADVERSE SELECTION — il modello perde dove dissente dal mercato?")
    has = ~np.isnan(mkt).any(axis=1)
    idx = [{"H": 0, "D": 1, "A": 2}[o] for o in pred.result]
    ll_mod = -np.log(np.clip(model[np.arange(n), idx], 1e-15, 1))
    ll_mkt = -np.log(np.clip(mkt[np.arange(n), idx], 1e-15, 1))
    gap = (ll_mod - ll_mkt)[has]
    dis = np.nansum(np.abs(model - mkt), axis=1)[has]
    r_ds = float(np.corrcoef(dis, gap)[0, 1])
    q = pd.qcut(dis, 4, labels=["dissenso basso", "medio-basso",
                                "medio-alto", "dissenso alto"])
    print(f"  corr(dissenso, gap vs mercato) = {r_ds:+.4f}")
    print(f"  {'quartile di dissenso':<22}{'n':>6}{'gap medio':>12}")
    for lab in ["dissenso basso", "medio-basso", "medio-alto", "dissenso alto"]:
        mask = (q == lab).to_numpy()
        print(f"  {lab:<22}{mask.sum():>6}{gap[mask].mean():>+12.4f}")
    print("  (gap che CRESCE col dissenso = i 'value bet' del modello sono i suoi errori)")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase20_residuals", "league": "serie_a",
         "variant": "residual_regression", "n_features": k, "seed": SEED,
         **{k2: v for k2, v in CFG.items() if k2 != "promoted_prior"},
         "promoted_prior": 0.23},
        {"n_matches": n, "r2_real": r2, "r2_noise_kn": k / n,
         "r2_random_features": float(rand_r2),
         "adverse_selection_corr": r_ds}, fp))


if __name__ == "__main__":
    main()
