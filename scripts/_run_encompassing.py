"""Fase 16 — Test di ENCOMPASSING: il modello aggiunge informazione al mercato?

La domanda che il gap non puo' dire: un modello a +0.0165 dal mercato puo'
essere (a) mercato degradato con rumore -> inutile, oppure (b) portatore di
informazione INDIPENDENTE -> utile in combinazione, anche se da solo perde.
Test standard (forecast encompassing): si mescola

    p_blend = alpha * p_modello + (1 - alpha) * p_mercato      (alpha in [0,1])

e si stima alpha minimizzando la log-loss. Se il mercato "ingloba" il modello,
alpha* ~ 0 e il blend non batte il mercato; se alpha* > 0 in modo stabile e il
blend migliora OUT-OF-SAMPLE, il modello contiene segnale proprio.

Protocollo onesto (niente senno di poi): alpha viene fittato SOLO sulle
stagioni di test precedenti (pooled per-partita) e applicato alla successiva
-> la prima stagione (2020-21) non e' valutabile, restano 5 valutazioni.
L'alpha* in-sample per stagione e' stampato come descrittivo, NON come
risultato. Verdetto sul pooled walk-forward con bootstrap appaiato.

Uso:  python scripts/_run_encompassing.py     (6 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
PC = ["m_home", "m_draw", "m_away"]
BOOT_B, BOOT_SEED = 10_000, 16   # bootstrap appaiato, seed fisso (replicabile)


def _worker(season):
    df = run_backtest("serie_a", season, CFG["half_life_days"],
                      shrinkage=CFG["shrinkage"], shots_blend=CFG["shots_blend"],
                      blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


def market_probs(df: pd.DataFrame) -> np.ndarray:
    """Probabilita' 1X2 di mercato devigate per riga (NaN dove mancano quote)."""
    out = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            out[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    return out


def fit_alpha(model: np.ndarray, market: np.ndarray, outcomes: list[str]) -> float:
    """alpha* in [0,1] che minimizza la log-loss del blend (convesso: le
    probabilita' del blend sommano a 1 per costruzione)."""
    def nll(a: float) -> float:
        return metrics.log_loss_1x2(a * model + (1 - a) * market, outcomes)
    res = minimize_scalar(nll, bounds=(0.0, 1.0), method="bounded")
    return float(res.x)


def per_match_ll(probs: np.ndarray, outcomes: list[str]) -> np.ndarray:
    idx = [{"H": 0, "D": 1, "A": 2}[o] for o in outcomes]
    return -np.log(np.clip(probs[np.arange(len(outcomes)), idx], 1e-15, 1.0))


def main():
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, SEASONS))

    fp = experiment_log.data_fingerprint(loader.load_league("serie_a"))
    for s, df in dfs.items():
        cfg = {"source": "fase16_encompassing", "league": "serie_a",
               "test_season": s, **{k: v for k, v in CFG.items()
               if k != "promoted_prior"}, "promoted_prior": 0.23}
        experiment_log.append_run(experiment_log.make_record(
            cfg, experiment_log.compute_metrics(df), fp))

    # Righe con quote valide (nello snapshot attuale: tutte), per stagione.
    data = {}
    for s in SEASONS:
        df = dfs[s]
        mkt = market_probs(df)
        ok = ~np.isnan(mkt).any(axis=1)
        data[s] = dict(model=df[PC].to_numpy()[ok], market=mkt[ok],
                       out=[o for o, k in zip(df["result"], ok) if k])
        n_drop = int((~ok).sum())
        if n_drop:
            print(f"  [{s}] {n_drop} righe senza quote escluse (fit e valutazione)")

    print("=" * 88)
    print("ENCOMPASSING — p_blend = a*modello + (1-a)*mercato  (1X2 log-loss)")
    print("=" * 88)

    # alpha* in-sample per stagione: SOLO descrittivo (quanto segnale vede il
    # fit quando puo' barare). Il verdetto e' nel walk-forward sotto.
    print("\n[descrittivo] alpha* fittato in-sample sulla singola stagione:")
    for s in SEASONS:
        d = data[s]
        a = fit_alpha(d["model"], d["market"], d["out"])
        print(f"  {s}: alpha*={a:.3f}")

    # Walk-forward: alpha dalle stagioni di test PRECEDENTI (pooled).
    print("\n[verdetto] alpha dal passato, applicato alla stagione successiva:")
    print(f"  {'stag.':<7}{'alpha(passato)':>15}{'mercato':>10}{'blend':>10}{'Δ':>10}")
    diffs = []   # ll_blend - ll_market per partita (pooled, 5 stagioni)
    rows = []
    for i, s in enumerate(SEASONS):
        if i == 0:
            print(f"  {s:<7}{'—':>15}{'—':>10}{'—':>10}{'—':>10}   (nessun passato)")
            continue
        past = [data[t] for t in SEASONS[:i]]
        a = fit_alpha(np.vstack([d["model"] for d in past]),
                      np.vstack([d["market"] for d in past]),
                      sum((d["out"] for d in past), []))
        d = data[s]
        blend = a * d["model"] + (1 - a) * d["market"]
        ll_m = metrics.log_loss_1x2(d["market"], d["out"])
        ll_b = metrics.log_loss_1x2(blend, d["out"])
        diffs.append(per_match_ll(blend, d["out"]) - per_match_ll(d["market"], d["out"]))
        rows.append((s, a, ll_m, ll_b))
        print(f"  {s:<7}{a:>15.3f}{ll_m:>10.4f}{ll_b:>10.4f}{ll_b-ll_m:>+10.4f}")

    d_all = np.concatenate(diffs)
    rng = np.random.default_rng(BOOT_SEED)
    bm = d_all[rng.integers(0, len(d_all), (BOOT_B, len(d_all)))].mean(axis=1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    p_neg = float((bm < 0).mean())
    print(f"\n  POOLED (5 stagioni, n={len(d_all)}): Δ medio {d_all.mean():+.4f}  "
          f"CI95 [{lo:+.4f}, {hi:+.4f}]  P(Δ<0)={p_neg:.1%}")
    print(f"  (bootstrap appaiato per-partita, B={BOOT_B}, seed={BOOT_SEED})")

    verdict = ("il blend MIGLIORA il mercato out-of-sample: il modello contiene "
               "informazione propria" if hi < 0 else
               "il blend NON migliora il mercato in modo distinguibile dal "
               "rumore: nessuna evidenza di informazione propria" if lo < 0 <= hi
               else "il blend PEGGIORA il mercato: il modello e' mercato+rumore")
    print(f"\n  VERDETTO: {verdict}.")

    # Riassunto nel registro (replicabile senza rifare i backtest).
    summary = {"n_matches": int(len(d_all)),
               "blend_minus_market_ll": float(d_all.mean()),
               "ci95_lo": float(lo), "ci95_hi": float(hi),
               "p_delta_negative": p_neg,
               **{f"alpha_wf_{s}": float(a) for s, a, _, _ in rows}}
    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase16_encompassing", "league": "serie_a",
         "variant": "walkforward_blend_summary", "bootstrap_B": BOOT_B,
         "bootstrap_seed": BOOT_SEED, "promoted_prior": 0.23}, summary, fp))


if __name__ == "__main__":
    main()
