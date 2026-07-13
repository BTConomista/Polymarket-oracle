"""Fase 33 — Le ultime covariate mai provate: PPDA/deep (stile) e finishing-luck.

Nello snapshot ci sono due segnali mai messi nel modello:
  - PPDA (pressing) e deep completions (dominio territoriale) -- indicatori
    TATTICI (Understat), usati come feature ROLLING pre-partita;
  - finishing-luck = gol - xG rolling (mean-reversion: chi ha segnato sopra
    l'xG regredisce).
Test walk-forward su DC (covariate) e GBM (feature), con la disciplina solita
(overall 1X2 log-loss + gap vs mercato, CI bootstrap vs baseline). Aspettativa
onesta: probabilmente ridondanti (l'xG cattura gia' la qualita' delle occasioni,
il tetto e' informativo), ma sono gli ultimi segnali interni inesplorati.

Uso:  python scripts/_run_style_luck.py     (backtest DC + GBM; ~minuti)
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

FEAT_SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
PC = ["m_home", "m_draw", "m_away"]
B, SEED = 10_000, 33
_OI = {"H": 0, "D": 1, "A": 2}
# covariate DC da testare: singole e combinate
DC_VARIANTS = {"base": (), "+ppda+deep": ("ppda", "deep"), "+luck": ("luck",),
               "+tutte": ("ppda", "deep", "luck")}


def _worker(task):
    season, covs = task
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], covariates=covs, verbose=False)
    df["season"] = season
    return (season, covs), df


def ll_1x2(P, out):
    idx = [_OI[o] for o in out]
    return -np.log(np.clip(P[np.arange(len(out)), idx], 1e-15, 1))


def boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV

    # DC: per ogni variante di covariate, 6 stagioni di test.
    tasks = [(s, covs) for covs in DC_VARIANTS.values() for s in TEST_SEASONS]
    # per il GBM servono anche le feature DC di 1819/1920 (train): backtest base.
    tasks += [(s, ()) for s in ("1819", "1920")]
    with Pool(6) as pool:
        res = dict(pool.map(_worker, tasks))

    allm = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(allm)
    for (s, covs), df in res.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase33_style_luck", "league": "serie_a", "test_season": s,
             "covariates": list(covs), **{k: v for k, v in CFG.items()
             if k != "promoted_prior"}, "promoted_prior": 0.23},
            experiment_log.compute_metrics(df), fp))

    def big(covs):
        return pd.concat([res[(s, covs)] for s in TEST_SEASONS], ignore_index=True)

    base = big(())
    out = base["result"].tolist()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in base.itertuples()])
    llk = ll_1x2(mkt, out)
    ll_base = ll_1x2(base[PC].to_numpy(), out)
    rng = np.random.default_rng(SEED)

    print("=" * 92)
    print("DIXON-COLES ± covariate PPDA/deep/luck — 1X2 log-loss e gap vs mercato")
    print("Δ = variante - base (negativo = aiuta)")
    print("=" * 92)
    print(f"  {'variante':<14}{'log-loss':>10}{'gap':>10}{'Δ vs base':>12}{'CI95':>22}")
    print(f"  {'base':<14}{ll_base.mean():>10.4f}{(ll_base.mean()-llk.mean()):>+10.4f}"
          f"{'—':>12}")
    for name, covs in DC_VARIANTS.items():
        if not covs:
            continue
        llv = ll_1x2(big(covs)[PC].to_numpy(), out)
        d = llv - ll_base
        mean, lo, hi, pneg = boot(d, rng)
        print(f"  {name:<14}{llv.mean():>10.4f}{(llv.mean()-llk.mean()):>+10.4f}"
              f"{mean:>+12.4f}   [{lo:+.4f}, {hi:+.4f}]")

    # --- GBM: base (dc+cov) vs + style/luck feature ---
    print("\n" + "=" * 92)
    print("GBM ± feature PPDA/deep/luck — 1X2 log-loss")
    print("=" * 92)
    cov = allm[["date", "home_team", "away_team", "home_form", "away_form",
                "home_rest_days_full", "away_rest_days_full", "home_squad_value",
                "away_squad_value", "home_absent_value_est", "away_absent_value_est",
                "home_ppda_roll", "away_ppda_roll", "home_deep_roll", "away_deep_roll",
                "home_luck", "away_luck"]]

    def blocks(s):
        m = res[(s, ())].merge(cov, on=["date", "home_team", "away_team"], how="left")
        lam, mu = m.exp_home_goals, m.exp_away_goals
        dccov = pd.DataFrame({
            "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
            "dc_ph": m.m_home, "dc_pd": m.m_draw, "dc_pa": m.m_away,
            "dc_pover": m.m_over, "dc_pbtts": m.m_btts,
            "home_form": m.home_form, "away_form": m.away_form,
            "home_rest": m.home_rest_days_full, "away_rest": m.away_rest_days_full,
            "home_logval": np.log(m.home_squad_value.astype(float)),
            "away_logval": np.log(m.away_squad_value.astype(float)),
            "home_absent": m.home_absent_value_est, "away_absent": m.away_absent_value_est})
        extra = pd.DataFrame({"h_ppda": m.home_ppda_roll, "a_ppda": m.away_ppda_roll,
                              "h_deep": m.home_deep_roll, "a_deep": m.away_deep_roll,
                              "h_luck": m.home_luck, "a_luck": m.away_luck})
        return dccov, extra

    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
    blk = {s: blocks(s) for s in FEAT_SEASONS}
    p_no, p_yes = [], []
    for s in TEST_SEASONS:
        i = FEAT_SEASONS.index(s); past = FEAT_SEASONS[:i]
        ytr = np.concatenate([np.array([_OI[o] for o in res[(t, ())]["result"]]) for t in past])
        for withx, store in [(False, p_no), (True, p_yes)]:
            Xtr = pd.concat([pd.concat([blk[t][0]] + ([blk[t][1]] if withx else []), axis=1)
                             for t in past], ignore_index=True)
            Xte = pd.concat([blk[s][0]] + ([blk[s][1]] if withx else []), axis=1)
            clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                         method="sigmoid", cv=3).fit(Xtr, ytr)
            store.append(clf.predict_proba(Xte))
    ll_g_no = ll_1x2(np.vstack(p_no), out); ll_g_yes = ll_1x2(np.vstack(p_yes), out)
    d = ll_g_yes - ll_g_no
    mean, lo, hi, pneg = boot(d, rng)
    print(f"  GBM base (dc+cov):      {ll_g_no.mean():.4f}")
    print(f"  GBM + ppda/deep/luck:   {ll_g_yes.mean():.4f}")
    print(f"  Δ {mean:+.4f}  CI95 [{lo:+.4f}, {hi:+.4f}]  P(aiuta)={pneg:.1%}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase33_style_luck", "league": "serie_a", "variant": "summary",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(out)), "dc_base_ll": float(ll_base.mean()),
         **{f"dc{name}_ll": float(ll_1x2(big(covs)[PC].to_numpy(), out).mean())
            for name, covs in DC_VARIANTS.items() if covs},
         "gbm_base_ll": float(ll_g_no.mean()), "gbm_style_ll": float(ll_g_yes.mean())}, fp))

    print("\nNota: covariate GENERALI (non concentrate su un subset come lo stakes),")
    print("quindi il test e' l'effetto OVERALL. Se Δ ~0 con CI che include lo zero,")
    print("PPDA/deep/luck sono ridondanti (gia' impliciti in gol+xG): tetto informativo.")


if __name__ == "__main__":
    main()
