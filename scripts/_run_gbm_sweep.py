"""Fase 22 — Sweep del gradient boosting su MOLTI mercati e MOLTE varianti.

La Fase 21 ha provato il GBM solo sul GG/NG. Qui lo spremiamo: 6 mercati x 3 set
di feature x calibrazione, per vedere se su QUALCHE mercato il GBM muove il gap
col mercato rispetto al Dixon-Coles (principio 8: valutare per-mercato).

Mercati:  1X2 (multiclasse), Over/Under 2.5, GG/NG, e le doppie chance 1X/2X/12.
Feature:  "cov"  = solo covariate pre-partita (forma, riposo, valore, assenze);
          "dc"   = solo output del Dixon-Coles (lam/mu, P(H/D/A), P(over), P(GG));
          "dc+cov" = entrambi (stacking: il GBM parte dal DC e prova a correggerlo).
Ogni GBM in versione grezza E calibrata (Platt in CV): la Fase 21 ha mostrato che
il log-loss punisce durissimo la mis-calibrazione, quindi la headline e' la
CALIBRATA (scelta di principio, non selezionata sul test).

Onesta': walk-forward per stagione (allena su 1819..S-1); feature del DC a loro
volta walk-forward -> nessun look-ahead. Benchmark per mercato: il MERCATO (quote
di chiusura devigate) dove esiste (1X2, O/U, e derivato per le doppie chance) e la
baseline in-sample. Per il GG/NG solo baseline (niente quote nei dati).

Domanda centrale: il gap (modello - mercato) del GBM e' MINORE di quello del DC
su qualche mercato? Verdetto inferenziale sulla variante pre-scelta dc+cov
calibrata, con CI bootstrap appaiato; le altre varianti sono descrittive.

Uso:  python scripts/_run_gbm_sweep.py     (8 backtest DC + molti GBM; ~minuti)
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
B, SEED = 10_000, 22
_OI = {"H": 0, "D": 1, "A": 2}


def _worker(season):
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


def dc_block(df, cov):
    m = df.merge(cov, on=["date", "home_team", "away_team"], how="left")
    lam, mu = m.exp_home_goals, m.exp_away_goals
    return pd.DataFrame({
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_ph": m.m_home, "dc_pd": m.m_draw, "dc_pa": m.m_away,
        "dc_pover": m.m_over, "dc_pbtts": m.m_btts}), m


def cov_block(m):
    return pd.DataFrame({
        "home_form": m.home_form, "away_form": m.away_form,
        "home_rest": m.home_rest_days_full, "away_rest": m.away_rest_days_full,
        "home_logval": np.log(m.home_squad_value.astype(float)),
        "away_logval": np.log(m.away_squad_value.astype(float)),
        "home_absent": m.home_absent_value_est, "away_absent": m.away_absent_value_est,
        "home_midweek": m.home_midweek_europe, "away_midweek": m.away_midweek_europe})


def ll_bin(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ll_multi(P, y_idx):
    return -np.log(np.clip(P[np.arange(len(y_idx)), y_idx], 1e-15, 1))


def boot_ci(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()


# Definizione dei mercati: come estrarre target/DC/mercato per riga.
def market_defs(df, feat_m):
    res = df["result"].to_numpy()
    mkt = np.full((len(df), 3), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    over_mkt = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_over, r.odds_under]).all():
            over_mkt[i], _ = metrics.devig_binary(r.odds_over, r.odds_under)
    mH, mD, mA = mkt[:, 0], mkt[:, 1], mkt[:, 2]
    return {
        "1X2": dict(kind="multi", y=np.array([_OI[o] for o in res]),
                    dc=df[["m_home", "m_draw", "m_away"]].to_numpy(),
                    market=mkt),
        "O/U 2.5": dict(kind="bin", y=df["is_over"].to_numpy().astype(int),
                        dc=df["m_over"].to_numpy(), market=over_mkt),
        "GG/NG": dict(kind="bin", y=df["is_btts"].to_numpy().astype(int),
                      dc=df["m_btts"].to_numpy(), market=None),
        "1X": dict(kind="bin", y=np.isin(res, ["H", "D"]).astype(int),
                   dc=(df.m_home + df.m_draw).to_numpy(), market=mH + mD),
        "2X": dict(kind="bin", y=np.isin(res, ["A", "D"]).astype(int),
                   dc=(df.m_away + df.m_draw).to_numpy(), market=mA + mD),
        "12": dict(kind="bin", y=np.isin(res, ["H", "A"]).astype(int),
                   dc=(df.m_home + df.m_away).to_numpy(), market=mH + mA),
    }


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV

    with Pool(min(8, len(FEAT_SEASONS))) as pool:
        dfs = dict(pool.map(_worker, FEAT_SEASONS))
    all_m = loader.load_league("serie_a")
    cov = all_m[["date", "home_team", "away_team", "home_form", "away_form",
                 "home_rest_days_full", "away_rest_days_full", "home_squad_value",
                 "away_squad_value", "home_absent_value_est", "away_absent_value_est",
                 "home_midweek_europe", "away_midweek_europe"]]

    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase22_gbm_sweep", "league": "serie_a", "test_season": s,
             "variant": "dc_features", **{k: v for k, v in CFG.items()
             if k != "promoted_prior"}, "promoted_prior": 0.23},
            experiment_log.compute_metrics(df), fp))

    # Blocchi feature per stagione.
    blk = {}
    for s in FEAT_SEASONS:
        d, m = dc_block(dfs[s], cov)
        blk[s] = {"dc": d, "cov": cov_block(m), "dc+cov": pd.concat([d, cov_block(m)], axis=1)}

    FEATSETS = ["cov", "dc", "dc+cov"]
    MARKETS = ["1X2", "O/U 2.5", "GG/NG", "1X", "2X", "12"]
    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)

    def fit_predict(fs, mk, calibrate):
        """log-loss per-riga (pooled sulle 6 stagioni) del GBM su (featureset, mercato)."""
        rows_ll, dc_ll, mkt_ll, base_ll = [], [], [], []
        for s in TEST_SEASONS:
            i = FEAT_SEASONS.index(s)
            Xtr = pd.concat([blk[t][fs] for t in FEAT_SEASONS[:i]], ignore_index=True)
            defs_tr = [market_defs(dfs[t], None)[mk] for t in FEAT_SEASONS[:i]]
            ytr = np.concatenate([d["y"] for d in defs_tr])
            d = market_defs(dfs[s], None)[mk]
            Xte = blk[s][fs]
            base = HistGradientBoostingClassifier(**kw)
            clf = (CalibratedClassifierCV(base, method="sigmoid", cv=3)
                   if calibrate else base).fit(Xtr, ytr)
            if d["kind"] == "multi":
                P = clf.predict_proba(Xte)          # (N,3) in ordine classi 0,1,2
                rows_ll.append(ll_multi(P, d["y"]))
                dc_ll.append(ll_multi(d["dc"], d["y"]))
                if d["market"] is not None:
                    hasq = ~np.isnan(d["market"]).any(axis=1)
                    mkt_ll.append(ll_multi(d["market"][hasq], d["y"][hasq]))
                base_ll.append(ll_multi(np.tile(metrics.base_rates_1x2(
                    [list(_OI)[j] for j in d["y"]]), (len(d["y"]), 1)), d["y"]))
            else:
                p = clf.predict_proba(Xte)[:, 1]
                rows_ll.append(ll_bin(p, d["y"]))
                dc_ll.append(ll_bin(d["dc"], d["y"]))
                if d["market"] is not None:
                    hq = np.isfinite(d["market"])
                    mkt_ll.append(ll_bin(d["market"][hq], d["y"][hq]))
                base_ll.append(ll_bin(np.full(len(d["y"]), d["y"].mean()), d["y"]))
        return (np.concatenate(rows_ll), np.concatenate(dc_ll),
                np.concatenate(mkt_ll) if mkt_ll else None, np.concatenate(base_ll))

    # --- Tabella descrittiva: log-loss CALIBRATA per (mercato x featureset) ---
    print("=" * 96)
    print("SWEEP GBM — log-loss CALIBRATA per mercato x feature-set, vs DC / mercato / baseline")
    print("=" * 96)
    print(f"  {'mercato':<9}{'GBM cov':>9}{'GBM dc':>9}{'GBM d+c':>9}"
          f"{'DC':>9}{'mercato':>9}{'base':>8}")
    cache = {}
    for mk in MARKETS:
        cells = {}
        for fs in FEATSETS:
            g, dcl, mkl, bl = fit_predict(fs, mk, calibrate=True)
            cells[fs] = g.mean()
            cache[(mk, fs)] = (g, dcl, mkl, bl)
        _, dcl, mkl, bl = cache[(mk, "dc+cov")]
        mtxt = f"{mkl.mean():>9.4f}" if mkl is not None else f"{'—':>9}"
        print(f"  {mk:<9}{cells['cov']:>9.4f}{cells['dc']:>9.4f}{cells['dc+cov']:>9.4f}"
              f"{dcl.mean():>9.4f}{mtxt}{bl.mean():>8.4f}")

    # --- Inferenza: la variante pre-scelta dc+cov (cal) MUOVE il gap? ---
    print("\n" + "=" * 96)
    print("GAP vs MERCATO — DC vs GBM(dc+cov, calibrato); Δ gap <0 = il GBM si avvicina")
    print("(bootstrap appaiato per-partita, B=%d, seed=%d)" % (B, SEED))
    print("=" * 96)
    rng = np.random.default_rng(SEED)
    print(f"  {'mercato':<9}{'gap DC':>10}{'gap GBM':>10}{'Δ gap':>10}{'CI95 Δ gap':>22}")
    summary = {}
    for mk in MARKETS:
        g, dcl, mkl, bl = cache[(mk, "dc+cov")]
        # Δ gap = gap_GBM - gap_DC = (GBM_ll - DC_ll) sulle stesse righe: il
        # benchmark (mercato o baseline) si CANCELLA, quindi il confronto e'
        # sempre GBM vs DC appaiato per-riga, robusto a quote parziali.
        dgap = g - dcl
        mean, lo, hi, pneg = boot_ci(dgap, rng)
        if mkl is not None:
            gap_dc = (dcl - mkl).mean()
            gap_gb = (g - mkl).mean()
            summary[mk] = (gap_dc, gap_gb, mean, lo, hi)
            print(f"  {mk:<9}{gap_dc:>+10.4f}{gap_gb:>+10.4f}"
                  f"{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]")
        else:
            # GG/NG: nessun mercato -> gap riferito alla baseline
            summary[mk] = (dcl.mean() - bl.mean(), g.mean() - bl.mean(), mean, lo, hi)
            print(f"  {mk:<9}{dcl.mean()-bl.mean():>+10.4f}{g.mean()-bl.mean():>+10.4f}"
                  f"{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]  (vs baseline)")

    # Registro: riassunto per mercato (variante dc+cov calibrata).
    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase22_gbm_sweep", "league": "serie_a",
         "variant": "sweep_summary", "model": "HistGradientBoosting",
         "featureset": "dc+cov", "calibrated": True, "bootstrap_B": B,
         "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(cache[("1X2", "dc+cov")][0])),
         **{f"gap_dc_{mk}": float(v[0]) for mk, v in summary.items()},
         **{f"gap_gbm_{mk}": float(v[1]) for mk, v in summary.items()},
         **{f"dgap_mean_{mk}": float(v[2]) for mk, v in summary.items()},
         **{f"dgap_ci_lo_{mk}": float(v[3]) for mk, v in summary.items()},
         **{f"dgap_ci_hi_{mk}": float(v[4]) for mk, v in summary.items()}}, fp))

    print("\nNota: Δ gap = gap_GBM - gap_DC = (GBM_ll - DC_ll) sulle stesse righe")
    print("(il mercato si cancella). <0 con CI<0 = il GBM batte il DC su quel mercato.")


if __name__ == "__main__":
    main()
