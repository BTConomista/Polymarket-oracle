"""Fase 23 — GBM che combina MODELLO + MERCATO: si puo' ridurre il gap?

Fin qui il GBM ha ricevuto solo informazione NOSTRA (output DC + covariate) e non
batte il DC (Fase 22). Ma c'e' un'informazione che abbiamo e non abbiamo mai dato
al modello: le QUOTE DI MERCATO stesse. Due domande, entrambe su "ridurre il gap":

  1. BATTERE il mercato: un GBM con [DC + covariate + quote] che prova a
     CORREGGERE le inefficienze residue della linea di chiusura. La Fase 16
     (encompassing) ha mostrato alpha*=0 ma solo LINEARE; un GBM cattura bias
     non-lineari (favourite-longshot, mispricing del pareggio per fascia). Se il
     mercato ha struttura sfruttabile -> gap NEGATIVO.
  2. RIDURRE il gap a ~0: anche senza edge, un modello che INCORPORA la linea da'
     la miglior stima per-caso (≈ livello mercato, meglio del DC da solo a
     +0.0165) — utile da portare su un mercato DIVERSO/meno efficiente.

Onesta': le quote di CHIUSURA sono pre-esito (nessun look-ahead sull'outcome), ma
sono informazione del mercato: usarle come feature e' lecito e mirato. Walk-forward
per stagione; GBM calibrato (Fase 21). Confronto per mercato (1X2 e O/U):
  - GBM senza mercato (dc+cov)  -> riferimento (≈ Fase 22)
  - GBM con mercato (dc+cov+mkt) -> puo' battere/pareggiare la linea?
Benchmark = il MERCATO. Bootstrap appaiato per-riga.

REGOLA DI ADOZIONE (dichiarata PRIMA dei numeri): "edge sul mercato" solo se il
GBM-con-mercato batte il MERCATO con CI95 del gap < 0. Ridurre il gap a ~0
(pareggiare il mercato) NON e' un edge ma e' un miglioramento come stimatore.

Uso:  python scripts/_run_gbm_market.py     (8 backtest DC + GBM; ~minuti)
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

FEAT_SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
B, SEED = 10_000, 23
_OI = {"H": 0, "D": 1, "A": 2}


def _worker(season):
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


def blocks(df, cov):
    m = df.merge(cov, on=["date", "home_team", "away_team"], how="left")
    lam, mu = m.exp_home_goals, m.exp_away_goals
    dc = pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_ph": m.m_home, "dc_pd": m.m_draw, "dc_pa": m.m_away,
        "dc_pover": m.m_over, "dc_pbtts": m.m_btts})
    cv = pd.DataFrame({
        "home_form": m.home_form, "away_form": m.away_form,
        "home_rest": m.home_rest_days_full, "away_rest": m.away_rest_days_full,
        "home_logval": np.log(m.home_squad_value.astype(float)),
        "away_logval": np.log(m.away_squad_value.astype(float)),
        "home_absent": m.home_absent_value_est, "away_absent": m.away_absent_value_est})
    # Blocco MERCATO: probabilita' devigate di chiusura (1X2 e O/U).
    mk_h, mk_d, mk_a, mk_o = [], [], [], []
    for r in df.itertuples():
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        else:
            p = [np.nan] * 3
        mk_h.append(p[0]); mk_d.append(p[1]); mk_a.append(p[2])
        if np.isfinite([r.odds_over, r.odds_under]).all():
            o, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        else:
            o = np.nan
        mk_o.append(o)
    mkt = pd.DataFrame({"mkt_ph": mk_h, "mkt_pd": mk_d, "mkt_pa": mk_a, "mkt_pover": mk_o})
    return dc, cv, mkt


def ll_bin(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ll_multi(P, yi):
    return -np.log(np.clip(P[np.arange(len(yi)), yi], 1e-15, 1))


def boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV

    with Pool(min(8, len(FEAT_SEASONS))) as pool:
        dfs = dict(pool.map(_worker, FEAT_SEASONS))
    all_m = loader.load_league("serie_a")
    cov = all_m[["date", "home_team", "away_team", "home_form", "away_form",
                 "home_rest_days_full", "away_rest_days_full", "home_squad_value",
                 "away_squad_value", "home_absent_value_est", "away_absent_value_est"]]
    B_ = {s: blocks(dfs[s], cov) for s in FEAT_SEASONS}

    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase23_gbm_market", "league": "serie_a", "test_season": s,
             "variant": "dc_features", **{k: v for k, v in CFG.items()
             if k != "promoted_prior"}, "promoted_prior": 0.23},
            experiment_log.compute_metrics(df), fp))

    def feats(s, withmkt):
        dc, cv, mkt = B_[s]
        return pd.concat([dc, cv, mkt] if withmkt else [dc, cv], axis=1)

    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)

    def run_market(mk, withmkt):
        """log-loss per-riga (pooled) del GBM + di DC e mercato, per 1X2 o O/U."""
        g_ll, dc_ll, mk_ll = [], [], []
        for s in TEST_SEASONS:
            i = FEAT_SEASONS.index(s)
            Xtr = pd.concat([feats(t, withmkt) for t in FEAT_SEASONS[:i]], ignore_index=True)
            Xte = feats(s, withmkt)
            df = dfs[s]
            if mk == "1X2":
                ytr = np.concatenate([np.array([_OI[o] for o in dfs[t]["result"]])
                                      for t in FEAT_SEASONS[:i]])
                y = np.array([_OI[o] for o in df["result"]])
                clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                             method="sigmoid", cv=3).fit(Xtr, ytr)
                P = clf.predict_proba(Xte)
                g_ll.append(ll_multi(P, y))
                dc_ll.append(ll_multi(df[["m_home", "m_draw", "m_away"]].to_numpy(), y))
                mkt = np.column_stack([B_[s][2].mkt_ph, B_[s][2].mkt_pd, B_[s][2].mkt_pa])
                mk_ll.append(ll_multi(mkt, y))
            else:  # O/U
                ytr = np.concatenate([dfs[t]["is_over"].to_numpy().astype(int)
                                      for t in FEAT_SEASONS[:i]])
                y = df["is_over"].to_numpy().astype(int)
                clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                             method="sigmoid", cv=3).fit(Xtr, ytr)
                p = clf.predict_proba(Xte)[:, 1]
                g_ll.append(ll_bin(p, y))
                dc_ll.append(ll_bin(df["m_over"].to_numpy(), y))
                mk_ll.append(ll_bin(B_[s][2].mkt_pover.to_numpy(), y))
        return (np.concatenate(g_ll), np.concatenate(dc_ll), np.concatenate(mk_ll))

    rng = np.random.default_rng(SEED)
    print("=" * 90)
    print("GBM MODELLO + MERCATO — puo' ridurre/annullare il gap col mercato?")
    print("log-loss, e gap = modello - mercato (>0 = sotto il mercato)")
    print("=" * 90)
    summ = {}
    for mk in ["1X2", "O/U 2.5"]:
        g_no, dc_ll, mk_ll = run_market(mk, withmkt=False)
        g_wi, _, _ = run_market(mk, withmkt=True)
        print(f"\n[{mk}]  (n={len(g_wi)})")
        print(f"  {'modello':<26}{'log-loss':>10}{'gap vs mercato':>16}")
        print(f"  {'DC (Dixon-Coles)':<26}{dc_ll.mean():>10.4f}{dc_ll.mean()-mk_ll.mean():>+16.4f}")
        print(f"  {'GBM senza mercato':<26}{g_no.mean():>10.4f}{g_no.mean()-mk_ll.mean():>+16.4f}")
        print(f"  {'GBM CON mercato':<26}{g_wi.mean():>10.4f}{g_wi.mean()-mk_ll.mean():>+16.4f}")
        print(f"  {'MERCATO (chiusura)':<26}{mk_ll.mean():>10.4f}{0.0:>+16.4f}")
        # Inferenza: il GBM-con-mercato batte il MERCATO? (gap<0 con CI<0)
        d_vs_mkt = g_wi - mk_ll
        mean, lo, hi, pneg = boot(d_vs_mkt, rng)
        # ...e batte il DC? (miglioramento come stimatore)
        d_vs_dc = g_wi - dc_ll
        mean2, lo2, hi2, _ = boot(d_vs_dc, rng)
        print(f"  -> GBM+mkt vs MERCATO: Δ {mean:+.4f} CI95 [{lo:+.4f}, {hi:+.4f}] "
              f"P(batte mkt)={pneg:.1%}")
        print(f"  -> GBM+mkt vs DC:      Δ {mean2:+.4f} CI95 [{lo2:+.4f}, {hi2:+.4f}]")
        beats_mkt = hi < 0
        print(f"  REGOLA: edge sul mercato solo se CI95<0 -> "
              f"{'EDGE!' if beats_mkt else 'nessun edge'}; "
              f"gap ridotto da {dc_ll.mean()-mk_ll.mean():+.4f} (DC) a "
              f"{g_wi.mean()-mk_ll.mean():+.4f} (GBM+mkt)")
        summ[mk] = dict(dc=dc_ll.mean(), gbm_no=g_no.mean(), gbm_mkt=g_wi.mean(),
                        market=mk_ll.mean(), d_vs_mkt=mean, ci_lo=lo, ci_hi=hi,
                        d_vs_dc=mean2)

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase23_gbm_market", "league": "serie_a",
         "variant": "market_stacking_summary", "model": "HistGradientBoosting",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": len(TEST_SEASONS) * 380,
         **{f"{mk.replace('/', '').replace(' ', '')}_{k}": float(v)
            for mk, d in summ.items() for k, v in d.items()}}, fp))

    print("\nNota: 'GBM CON mercato' usa le quote di chiusura come feature -> non e'")
    print("un edge giocabile CONTRO quel book (circolare), ma misura se la linea ha")
    print("struttura non-lineare sfruttabile, e da' il miglior stimatore per-caso da")
    print("portare su un mercato DIVERSO (meno efficiente).")


if __name__ == "__main__":
    main()
