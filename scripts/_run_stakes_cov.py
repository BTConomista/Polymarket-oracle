"""Fase 32 — Validazione walk-forward della covariata 'stakes mismatch' (DC e GBM).

La Fase 31 ha trovato un indizio: quando UNA squadra e' decisa (niente in gioco)
e l'altra e' in corsa, il modello perde piu' del mercato (gap +0.057 vs +0.017).
Qui si valida se una covariata 'stakes' (posta in palio, 1=decisa/0=in corsa,
dalla classifica) MIGLIORA la previsione out-of-sample — su ENTRAMBI i modelli:
  - Dixon-Coles: covariata nel fit (--covariates stakes);
  - GBM: feature aggiuntive (home_settled, away_settled, differenza).

Il segnale e' su ~5% di partite (i mismatch di fine stagione), quindi l'effetto
OVERALL sara' minuscolo per costruzione: il test vero e' SULLE PARTITE MISMATCH
(una decisa, una in corsa). CI bootstrap appaiato. Se non regge li', era rumore
da piccolo campione (Fase 31).

Uso:  python scripts/_run_stakes_cov.py     (14 backtest + GBM; ~minuti)
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
B, SEED = 10_000, 32
_OI = {"H": 0, "D": 1, "A": 2}


def _worker(task):
    season, use_stakes = task
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"],
                      covariates=("stakes",) if use_stakes else (), verbose=False)
    df["season"] = season
    return (season, use_stakes), df


def ll_1x2(P, out):
    idx = [_OI[o] for o in out]
    return -np.log(np.clip(P[np.arange(len(out)), idx], 1e-15, 1))


def boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()


def dc_block(df, cov):
    m = df.merge(cov, on=["date", "home_team", "away_team"], how="left")
    lam, mu = m.exp_home_goals, m.exp_away_goals
    dc = pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_ph": m.m_home, "dc_pd": m.m_draw, "dc_pa": m.m_away,
        "dc_pover": m.m_over, "dc_pbtts": m.m_btts,
        "home_form": m.home_form, "away_form": m.away_form,
        "home_rest": m.home_rest_days_full, "away_rest": m.away_rest_days_full,
        "home_logval": np.log(m.home_squad_value.astype(float)),
        "away_logval": np.log(m.away_squad_value.astype(float)),
        "home_absent": m.home_absent_value_est, "away_absent": m.away_absent_value_est})
    stakes = pd.DataFrame({"home_settled": m.home_settled, "away_settled": m.away_settled,
                           "settled_diff": m.home_settled - m.away_settled})
    return dc, stakes, m


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV

    tasks = [(s, False) for s in FEAT_SEASONS] + [(s, True) for s in TEST_SEASONS]
    with Pool(min(8, len(tasks))) as pool:
        res = dict(pool.map(_worker, tasks))
    base = {s: res[(s, False)] for s in FEAT_SEASONS}
    dcst = {s: res[(s, True)] for s in TEST_SEASONS}

    allm = loader.load_league("serie_a")
    cov = allm[["date", "home_team", "away_team", "home_form", "away_form",
                "home_rest_days_full", "away_rest_days_full", "home_squad_value",
                "away_squad_value", "home_absent_value_est", "away_absent_value_est",
                "home_settled", "away_settled"]]
    fp = experiment_log.data_fingerprint(allm)
    for (s, us), df in res.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase32_stakes_cov", "league": "serie_a", "test_season": s,
             "covariates": ["stakes"] if us else [],
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, experiment_log.compute_metrics(df), fp))

    rng = np.random.default_rng(SEED)

    def report(name, ll_ref, ll_var, mkt, mism):
        """Confronto per-riga: variante - riferimento, overall e su mismatch."""
        for sub, mask in [("overall", np.ones(len(ll_ref), bool)), ("MISMATCH", mism)]:
            d = ll_var[mask] - ll_ref[mask]
            mean, lo, hi, pneg = boot(d, rng)
            g_ref = (ll_ref[mask] - mkt[mask]).mean()
            g_var = (ll_var[mask] - mkt[mask]).mean()
            print(f"  {name} [{sub:<8} n={mask.sum():>4}]  ll {ll_ref[mask].mean():.4f}"
                  f"->{ll_var[mask].mean():.4f}  Δ {mean:+.4f} [{lo:+.4f},{hi:+.4f}]"
                  f"  gap {g_ref:+.4f}->{g_var:+.4f}")

    # --- allineamento per-partita su TEST_SEASONS ---
    big_base = pd.concat([base[s] for s in TEST_SEASONS], ignore_index=True)
    big_st = pd.concat([dcst[s] for s in TEST_SEASONS], ignore_index=True)
    assert (big_base["home_team"].to_numpy() == big_st["home_team"].to_numpy()).all()
    out = big_base["result"].tolist()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in big_base.itertuples()])
    llk = ll_1x2(mkt, out)
    sett = big_base.merge(cov[["date", "home_team", "away_team",
                               "home_settled", "away_settled"]],
                          on=["date", "home_team", "away_team"], how="left")
    mism = ((sett.home_settled + sett.away_settled) == 1).to_numpy()

    print("=" * 100)
    print("DIXON-COLES ± covariata stakes — 1X2 log-loss e gap vs mercato")
    print("Δ = con-stakes - base (negativo = la covariata aiuta); mismatch = una decisa/una in corsa")
    print("=" * 100)
    ll_dc_base = ll_1x2(big_base[PC].to_numpy(), out)
    ll_dc_st = ll_1x2(big_st[PC].to_numpy(), out)
    report("DC", ll_dc_base, ll_dc_st, llk, mism)

    # --- GBM ± stakes (1X2 calibrato, walk-forward per stagione) ---
    print("\n" + "=" * 100)
    print("GBM ± feature stakes — 1X2 log-loss e gap vs mercato")
    print("=" * 100)
    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
    blocks = {s: dc_block(base[s], cov) for s in FEAT_SEASONS}
    p_no, p_yes = [], []
    for s in TEST_SEASONS:
        i = FEAT_SEASONS.index(s)
        past = FEAT_SEASONS[:i]
        y_tr = np.concatenate([np.array([_OI[o] for o in base[t]["result"]]) for t in past])
        for tag, withst, store in [("no", False, p_no), ("yes", True, p_yes)]:
            Xtr = pd.concat([pd.concat([blocks[t][0]] + ([blocks[t][1]] if withst else []), axis=1)
                             for t in past], ignore_index=True)
            Xte = pd.concat([blocks[s][0]] + ([blocks[s][1]] if withst else []), axis=1)
            clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                         method="sigmoid", cv=3).fit(Xtr, y_tr)
            store.append(clf.predict_proba(Xte))
    P_no = np.vstack(p_no); P_yes = np.vstack(p_yes)
    ll_g_no = ll_1x2(P_no, out); ll_g_yes = ll_1x2(P_yes, out)
    report("GBM", ll_g_no, ll_g_yes, llk, mism)

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase32_stakes_cov", "league": "serie_a", "variant": "cov_summary",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(out)), "n_mismatch": int(mism.sum()),
         "dc_base_ll": float(ll_dc_base.mean()), "dc_stakes_ll": float(ll_dc_st.mean()),
         "dc_base_ll_mismatch": float(ll_dc_base[mism].mean()),
         "dc_stakes_ll_mismatch": float(ll_dc_st[mism].mean()),
         "gbm_base_ll": float(ll_g_no.mean()), "gbm_stakes_ll": float(ll_g_yes.mean()),
         "gbm_base_ll_mismatch": float(ll_g_no[mism].mean()),
         "gbm_stakes_ll_mismatch": float(ll_g_yes[mism].mean())}, fp))

    print("\nNota: il segnale e' su ~5% di partite (mismatch), quindi l'effetto overall")
    print("e' minuscolo per costruzione. Il test vero e' sulla riga MISMATCH: se li'")
    print("la covariata non aiuta (CI include 0), il lead della Fase 31 era rumore.")


if __name__ == "__main__":
    main()
