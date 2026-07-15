"""Fase 50 (Track C) — GBM BESPOKE per singolo mercato: l'ultima variante mai testata.

Il bakeoff (Fase 41) ha incoronato il market-implied su 19/20 mercati Tier 1, ma con
una riserva esplicita (CLAUDE.md §1.8): "un ML bespoke per singolo mercato resta
l'unica variante non ancora testata". Qui la si testa e la si chiude, sui due path:

  - path CON quote:  GBM addestrato DIRETTAMENTE sul mercato bersaglio, con feature
    DC-block + λ,μ market-implied + la predizione dell'engine stesso (encompassing
    non-lineare sul mercato NON prezzato — la Fase 23 lo fece solo sull'1X2 coi
    prezzi 1X2). Se il GBM battesse l'engine, ci sarebbe segnale residuo.
  - path SENZA quote: GBM (solo feature interne + DC-block) vs il DC — il "bespoke"
    puro sul fallback.

Mercati bersaglio (binari, non prezzati tranne O/U): GG/NG, clean sheet casa,
total-squadra casa Over 1.5, O/U 2.5 (sanity: prezzato, il GBM non deve battere il
mercato letto). Feature extra rispetto alle Fasi 22/36: matchday (il GBM puo'
scoprire da solo il pattern di fine stagione della Fase 48), |λ−μ| (equilibrio,
Fase 35), λ,μ del mercato.

Walk-forward 8 stagioni (test = ultime 7), GBM calibrato (Platt, cv=3 — lezione
Fase 21). Bootstrap appaiato GBM − engine di riferimento per ogni mercato.

Uso:  python scripts/_run_fase50_gbm_bespoke.py    (cache db_base; sklearn extra)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO_MI = -0.06
RHO_DC = -0.05
B, SEED = 10_000, 50
FEATS = ["home_form", "away_form", "home_rest_days_full", "away_rest_days_full",
         "home_squad_value", "away_squad_value", "home_absent_value_est",
         "away_absent_value_est", "home_settled", "away_settled"]

# mercato -> (etichetta, y(hg,ag), famiglia di forma per il routing Fase 44)
MARKETS = {
    "gg":         ("GG/NG",              lambda hg, ag: (hg >= 1) & (ag >= 1), "phi"),
    "cs_home":    ("clean sheet casa",   lambda hg, ag: ag == 0,               "tau"),
    "home_ov_15": ("casa Over 1.5",      lambda hg, ag: hg >= 2,               "tau"),
    "ou25":       ("O/U 2.5 (sanity)",   lambda hg, ag: (hg + ag) >= 3,        "tau"),
}
MKEY = {"gg": "btts", "cs_home": "cs_home", "home_ov_15": "home_ov_1.5",
        "ou25": "over_2.5"}


def _add_matchday(df):
    df = df.sort_values("date").reset_index(drop=True)
    m = np.zeros(len(df), int)
    for _, g in df.groupby("season"):
        cnt: dict = {}
        for i in g.index:
            h, a = df.at[i, "home_team"], df.at[i, "away_team"]
            hi, ai = cnt.get(h, 0), cnt.get(a, 0)
            m[i] = int(round((hi + ai) / 2)) + 1
            cnt[h], cnt[a] = hi + 1, ai + 1
    df["matchday"] = m
    return df


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
    df = _add_matchday(df)
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO_MI)
    df["mlam"], df["mmu"] = lam, mu
    return df


def _engine_probs(df, phi_by_season):
    """Prob per-riga dell'engine market-implied (routing Fase 44) e del DC
    (matrice dai λ,μ del backtest ufficiale) per ogni mercato bersaglio."""
    out_mi = {k: np.zeros(len(df)) for k in MARKETS}
    out_dc = {k: np.zeros(len(df)) for k in MARKETS}
    for i, r in enumerate(df.itertuples()):
        phi0, kappa = phi_by_season[r.season]
        M_tau = mi.score_matrix(r.mlam, r.mmu, RHO_MI)
        phi = mi.balance_phi(r.mlam, r.mmu, phi0, kappa)
        M_phi = mi.score_matrix(r.mlam, r.mmu, RHO_MI, diag_inflation=phi)
        d_tau, d_phi = mi.derive_markets(M_tau), mi.derive_markets(M_phi)
        Mdc = mi.score_matrix(r.exp_home_goals, r.exp_away_goals, RHO_DC)
        ddc = mi.derive_markets(Mdc)
        for k, (_, _, fam) in MARKETS.items():
            src = d_phi if fam == "phi" else d_tau
            out_mi[k][i] = src[MKEY[k]]
            out_dc[k][i] = ddc[MKEY[k]]
    return out_mi, out_dc


def _features(df, mi_probs, dc_probs, mk, with_market: bool):
    lam, mu = df.exp_home_goals.values, df.exp_away_goals.values
    cols = {
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu,
        "dc_lam_plus_mu": lam + mu, "dc_balance": np.abs(lam - mu),
        "dc_ph": df.m_home, "dc_pd": df.m_draw, "dc_pa": df.m_away,
        "dc_pover": df.m_over, "dc_pbtts": df.m_btts,
        "dc_p_target": dc_probs[mk],
        "home_form": df.home_form, "away_form": df.away_form,
        "home_rest": df.home_rest_days_full, "away_rest": df.away_rest_days_full,
        "home_logval": np.log(df.home_squad_value.astype(float)),
        "away_logval": np.log(df.away_squad_value.astype(float)),
        "home_absent": df.home_absent_value_est, "away_absent": df.away_absent_value_est,
        "home_settled": df.home_settled.astype(float),
        "away_settled": df.away_settled.astype(float),
        "matchday": df.matchday.astype(float),
    }
    if with_market:
        mlam, mmu = df.mlam.values, df.mmu.values
        cols.update({"mlam": mlam, "mmu": mmu, "m_balance": np.abs(mlam - mmu),
                     "m_tot": mlam + mmu, "mi_p_target": mi_probs[mk]})
    return pd.DataFrame(cols)


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

    # φ(|λ−μ|) walk-forward per l'engine (come Fase 39); prima stagione: φ=0.
    phi_by_season: dict = {seasons[0]: (0.0, 0.0)}
    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past = df[df.season.isin(seasons[:i])]
        is_dr = (past.home_goals == past.away_goals).astype(float).values
        phi_by_season[s] = mi.fit_balance_phi(past.mlam.values, past.mmu.values,
                                              is_dr, RHO_MI)
    mi_probs, dc_probs = _engine_probs(df, phi_by_season)
    print(f"engine pronti in {time.time()-t0:.0f}s", flush=True)

    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)
    res: dict = {mk: {"y": [], "mi": [], "dc": [], "gbm_dc": [], "gbm_mkt": [],
                      "base": []} for mk in MARKETS}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past_idx = df.season.isin(seasons[:i]).to_numpy()
        cur_idx = (df.season == s).to_numpy()
        past, cur = df[past_idx], df[cur_idx]
        for mk, (_, yfun, _) in MARKETS.items():
            ytr = yfun(past.home_goals.values, past.away_goals.values).astype(int)
            ycu = yfun(cur.home_goals.values, cur.away_goals.values).astype(int)
            res[mk]["y"].append(ycu)
            res[mk]["mi"].append(mi_probs[mk][cur_idx])
            res[mk]["dc"].append(dc_probs[mk][cur_idx])
            res[mk]["base"].append(np.full(len(cur), ycu.mean()))  # in-sample, onesta Fase 15
            for tag, wm in (("gbm_dc", False), ("gbm_mkt", True)):
                Xtr = _features(past, {k: v[past_idx] for k, v in mi_probs.items()},
                                {k: v[past_idx] for k, v in dc_probs.items()}, mk, wm)
                Xcu = _features(cur, {k: v[cur_idx] for k, v in mi_probs.items()},
                                {k: v[cur_idx] for k, v in dc_probs.items()}, mk, wm)
                clf = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                             method="sigmoid", cv=3)
                p = clf.fit(Xtr, ytr).predict_proba(Xcu)[:, 1]
                res[mk][tag].append(p)
        print(f"  stagione {s} fatta ({time.time()-t0:.0f}s)", flush=True)

    rng = np.random.default_rng(SEED)
    print("\n" + "=" * 96)
    print(f"FASE 50 (Track C) — GBM bespoke per mercato vs engine "
          f"(walk-forward {len(seasons)-1} stagioni)")
    print("=" * 96)
    print(f"  {'mercato':<20}{'baseline':>10}{'DC':>9}{'mkt-impl':>10}{'gbm_dc':>9}"
          f"{'gbm_mkt':>9}   Δ(gbm_mkt−mi) CI95, P(migliora)")
    summary: dict = {}
    for mk, (lab, _, _) in MARKETS.items():
        y = np.concatenate(res[mk]["y"]).astype(float)
        ll = {t: _ll_bin(np.concatenate(res[mk][t]), y)
              for t in ("mi", "dc", "gbm_dc", "gbm_mkt", "base")}
        d_mkt, lo, hi, p = _boot(ll["gbm_mkt"] - ll["mi"], rng)
        d_dc = float((ll["gbm_dc"] - ll["dc"]).mean())
        print(f"  {lab:<20}{ll['base'].mean():>10.4f}{ll['dc'].mean():>9.4f}"
              f"{ll['mi'].mean():>10.4f}{ll['gbm_dc'].mean():>9.4f}"
              f"{ll['gbm_mkt'].mean():>9.4f}   {d_mkt:+.4f} [{lo:+.4f},{hi:+.4f}] "
              f"P={p:.0%}")
        summary[f"{mk}__baseline"] = float(ll["base"].mean())
        summary[f"{mk}__dc"] = float(ll["dc"].mean())
        summary[f"{mk}__mi"] = float(ll["mi"].mean())
        summary[f"{mk}__gbm_dc"] = float(ll["gbm_dc"].mean())
        summary[f"{mk}__gbm_mkt"] = float(ll["gbm_mkt"].mean())
        summary[f"{mk}__gbm_vs_mi_delta"] = d_mkt
        summary[f"{mk}__gbm_vs_mi_ci_lo"] = lo
        summary[f"{mk}__gbm_vs_mi_ci_hi"] = hi
        summary[f"{mk}__gbm_vs_mi_p"] = p
        summary[f"{mk}__gbmdc_vs_dc_delta"] = d_dc

    n = int(len(np.concatenate(res["gg"]["y"])))
    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase50_gbm_bespoke", "league": "serie_a",
         "variant": "gbm_bespoke_per_mercato", "rho_mi": RHO_MI,
         "seasons": seasons, "bootstrap_B": B, "bootstrap_seed": SEED,
         "markets": list(MARKETS)},
        {"n_matches": n, **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase50_gbm_bespoke). "
          f"Tempo totale {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
