"""Fase 45 — Router "stakes-aware" sul path SENZA quote (context-routing).

Decisione di architettura (Fase 44): sul path DC (nessuna quota) il predittore e'
DC + prior-neopromosse + φ35, "con eventuale aggiustamento-stakes". Qui si COSTRUISCE
e si VALIDA quell'aggiustamento. Meccanismo (Fasi 31/32): quando UNA squadra e'
DECISA (niente in palio) e l'altra e' IN CORSA, il DC — che usa la forza stagionale,
cieco alla motivazione — perde piu' del mercato; il GBM cattura il segnale ~6x meglio.

ROUTER (mecanico, per contesto): 1X2 = DC ovunque, ma sulle partite MISMATCH
(home_settled+away_settled==1) usa la previsione GBM-stakes. Variante SOFT: sul
mismatch fonde DC e GBM-stakes 50/50 (meno aggressiva). Si misura il router vs DC
puro: overall e SULLE MISMATCH (dove vive il segnale), con CI bootstrap appaiato, e
il gap vs mercato (chiudiamo il +0.057 della Fase 31?).

Onesta' attesa (Fase 32): direzione giusta ma campione mismatch piccolo (~5% delle
partite) → indizio, non prova. Walk-forward su cache db_base (train GBM su stagioni
passate); il segnale e' concentrato a fine stagione.

Uso:  python scripts/_run_stakes_routing.py    (cache db_base + feature loader; no backtest)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                        # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
B, SEED = 10_000, 45
_OI = {"H": 0, "D": 1, "A": 2}
FEATS = ["home_form", "away_form", "home_rest_days_full", "away_rest_days_full",
         "home_squad_value", "away_squad_value", "home_absent_value_est",
         "away_absent_value_est", "home_settled", "away_settled"]


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


def _gbm_features(df, with_stakes):
    lam, mu = df.exp_home_goals.values, df.exp_away_goals.values
    cols = {
        "dc_lam": lam, "dc_mu": mu, "dc_lam_x_mu": lam * mu, "dc_lam_plus_mu": lam + mu,
        "dc_ph": df.m_home, "dc_pd": df.m_draw, "dc_pa": df.m_away,
        "dc_pover": df.m_over, "dc_pbtts": df.m_btts,
        "home_form": df.home_form, "away_form": df.away_form,
        "home_rest": df.home_rest_days_full, "away_rest": df.away_rest_days_full,
        "home_logval": df.home_logval, "away_logval": df.away_logval,
        "home_absent": df.home_absent_value_est, "away_absent": df.away_absent_value_est}
    if with_stakes:
        cols["home_settled"] = df.home_settled.astype(float)
        cols["away_settled"] = df.away_settled.astype(float)
        cols["settled_diff"] = (df.home_settled - df.away_settled).astype(float)
    return pd.DataFrame(cols)


def _ll(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.calibration import CalibratedClassifierCV

    df = _load()
    kw = dict(max_iter=200, max_depth=3, learning_rate=0.05,
              l2_regularization=1.0, min_samples_leaf=30, random_state=SEED)

    parts = []      # per-stagione: dizionario con predizioni e maschere allineate
    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])].reset_index(drop=True)
        cur = df[df.season == s].reset_index(drop=True)
        y1 = np.array([_OI[o] for o in cur.result])
        ytr = np.array([_OI[o] for o in past.result])

        dc = cur[["m_home", "m_draw", "m_away"]].to_numpy()
        mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                        for r in cur.itertuples()])
        gbm_base = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                          method="sigmoid", cv=3).fit(
            _gbm_features(past, False), ytr).predict_proba(_gbm_features(cur, False))
        gbm_st = CalibratedClassifierCV(HistGradientBoostingClassifier(**kw),
                                        method="sigmoid", cv=3).fit(
            _gbm_features(past, True), ytr).predict_proba(_gbm_features(cur, True))
        mism = ((cur.home_settled + cur.away_settled) == 1).to_numpy()
        parts.append(dict(y=y1, dc=dc, mkt=mkt, gbm_base=gbm_base,
                          gbm_st=gbm_st, mism=mism))

    y = np.concatenate([p["y"] for p in parts])
    dc = np.vstack([p["dc"] for p in parts])
    mkt = np.vstack([p["mkt"] for p in parts])
    gbm_base = np.vstack([p["gbm_base"] for p in parts])
    gbm_st = np.vstack([p["gbm_st"] for p in parts])
    mism = np.concatenate([p["mism"] for p in parts])

    # ROUTER: DC ovunque, GBM-stakes sul mismatch. SOFT: 50/50 sul mismatch.
    route = dc.copy(); route[mism] = gbm_st[mism]
    soft = dc.copy(); soft[mism] = 0.5 * dc[mism] + 0.5 * gbm_st[mism]

    ll_dc, ll_gb, ll_gs = _ll(dc, y), _ll(gbm_base, y), _ll(gbm_st, y)
    ll_rt, ll_sf, ll_mk = _ll(route, y), _ll(soft, y), _ll(mkt, y)
    rng = np.random.default_rng(SEED)

    print("=" * 92)
    print("FASE 45 — router stakes-aware sul path SENZA quote (1X2)")
    print(f"n partite: {len(y)}   di cui MISMATCH (una decisa/una in corsa): {int(mism.sum())}"
          f" ({mism.mean():.1%})")
    print("=" * 92)

    def line(name, ll_v, mask):
        mean, lo, hi, pneg = _boot((ll_v - ll_dc)[mask], rng)
        gap = (ll_v[mask] - ll_mk[mask]).mean()
        print(f"  {name:<22} ll {ll_v[mask].mean():.4f}   Δ vs DC {mean:+.4f} "
              f"[{lo:+.4f},{hi:+.4f}]  P(aiuta)={1-pneg:.0%}   gap-mkt {gap:+.4f}")

    for label, mask in [("--- OVERALL ---", np.ones(len(y), bool)),
                        ("--- SOLO MISMATCH ---", mism)]:
        print(f"\n{label}  (DC log-loss = {ll_dc[mask].mean():.4f}, "
              f"mercato = {ll_mk[mask].mean():.4f}, gap DC {ll_dc[mask].mean()-ll_mk[mask].mean():+.4f})")
        line("GBM-base", ll_gb, mask)
        line("GBM-stakes", ll_gs, mask)
        line("ROUTER (hard)", ll_rt, mask)
        line("ROUTER (soft 50/50)", ll_sf, mask)

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase45_stakes_routing", "league": "serie_a", "variant": "context_router",
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(y)), "n_mismatch": int(mism.sum()),
         "dc_ll": float(ll_dc.mean()), "router_ll": float(ll_rt.mean()),
         "soft_ll": float(ll_sf.mean()),
         "dc_ll_mismatch": float(ll_dc[mism].mean()),
         "router_ll_mismatch": float(ll_rt[mism].mean()),
         "soft_ll_mismatch": float(ll_sf[mism].mean()),
         "gbm_stakes_ll_mismatch": float(ll_gs[mism].mean()),
         "mkt_ll_mismatch": float(ll_mk[mism].mean())},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase45_stakes_routing).")


if __name__ == "__main__":
    main()
