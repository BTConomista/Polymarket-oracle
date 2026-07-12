"""Fase 17 — Intervalli di confidenza (bootstrap appaiato) sui numeri chiave.

Finora ogni confronto era una media senza incertezza: "nel rumore" era un
giudizio a occhio. Qui si mette un CI95 bootstrap sui quattro numeri che
reggono le conclusioni del progetto:

  1. gap 1X2 modello - mercato   (il numero principale: +0.0165)
  2. gap 12 (no pari)            (il "quasi-zero": +0.0020 e' distinguibile da 0?)
  3. gap Over/Under 2.5          (+0.0069, il mercato volatile)
  4. Δ prior neopromosse V4-V3   (-0.0010, l'unica feature ADOTTATA: e' reale?)

Metodo: bootstrap APPAIATO per-partita (si ricampionano le differenze di
log-loss della stessa partita, mai serie sfasate), B=10000, seed fisso.
Nota di disciplina (multiple testing): dopo ~30 test sulle stesse 6 stagioni,
un CI che sfiora lo zero va letto come "non concluso", non come scoperta.

Uso:  python scripts/_run_gap_uncertainty.py    (12 backtest; ~alcuni minuti)
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
BASE = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75, blend_signal="xg")
PC = ["m_home", "m_draw", "m_away"]
B, SEED = 10_000, 17


def _worker(task):
    version, season = task            # version: "V4" (col prior) | "V3" (senza)
    prior = (0.23, 0.23) if version == "V4" else None
    df = run_backtest("serie_a", season, BASE["half_life_days"],
                      shrinkage=BASE["shrinkage"], shots_blend=BASE["shots_blend"],
                      blend_signal=BASE["blend_signal"], promoted_prior=prior,
                      verbose=False)
    df["season"] = season
    return version, season, df


def ll_1x2_rows(probs, outcomes):
    idx = [{"H": 0, "D": 1, "A": 2}[o] for o in outcomes]
    return -np.log(np.clip(probs[np.arange(len(outcomes)), idx], 1e-15, 1.0))


def ll_bin_rows(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d: np.ndarray, rng) -> tuple[float, float, float, float]:
    """(media, ci_lo, ci_hi, quota di bootstrap < 0) delle differenze appaiate."""
    means = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float((means < 0).mean())


def main():
    tasks = [(v, s) for v in ("V4", "V3") for s in SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    dfs = {(v, s): df for v, s, df in res}

    fp = experiment_log.data_fingerprint(loader.load_league("serie_a"))
    for (v, s), df in dfs.items():
        cfg = {"source": "fase17_bootstrap", "league": "serie_a",
               "test_season": s, **BASE,
               "promoted_prior": 0.23 if v == "V4" else None}
        experiment_log.append_run(experiment_log.make_record(
            cfg, experiment_log.compute_metrics(df), fp))

    # Differenze appaiate per partita, pooled sulle 6 stagioni (config V4).
    d_1x2, d_12, d_ou, d_prior = [], [], [], []
    for s in SEASONS:
        df = dfs[("V4", s)]
        out = df["result"].tolist()
        model = df[PC].to_numpy()
        mkt = np.full((len(df), 3), np.nan)
        for i, (_, r) in enumerate(df.iterrows()):
            if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
                mkt[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        ok = ~np.isnan(mkt).any(axis=1)
        o_ok = [o for o, k in zip(out, ok) if k]

        d_1x2.append(ll_1x2_rows(model[ok], o_ok) - ll_1x2_rows(mkt[ok], o_ok))

        y12 = np.array([o in "HA" for o in o_ok], float)
        d_12.append(ll_bin_rows((model[ok, 0] + model[ok, 2]), y12)
                    - ll_bin_rows((mkt[ok, 0] + mkt[ok, 2]), y12))

        m_over = np.full(len(df), np.nan)
        for i, (_, r) in enumerate(df.iterrows()):
            if np.isfinite([r.odds_over, r.odds_under]).all():
                m_over[i], _ = metrics.devig_binary(r.odds_over, r.odds_under)
        ok_ou = np.isfinite(m_over)
        y_ou = df["is_over"].to_numpy()[ok_ou].astype(float)
        d_ou.append(ll_bin_rows(df["m_over"].to_numpy()[ok_ou], y_ou)
                    - ll_bin_rows(m_over[ok_ou], y_ou))

        # Δ prior: V4 - V3 sulla stessa partita (ordine deterministico; check).
        df3 = dfs[("V3", s)]
        assert (df["home_team"].to_numpy() == df3["home_team"].to_numpy()).all()
        d_prior.append(ll_1x2_rows(model, out) - ll_1x2_rows(df3[PC].to_numpy(), out))

    rng = np.random.default_rng(SEED)
    print("=" * 88)
    print(f"INTERVALLI DI CONFIDENZA (bootstrap appaiato per-partita, B={B}, "
          f"seed={SEED}; pooled 6 stagioni)")
    print("=" * 88)
    print(f"{'quantita':<38}{'media':>10}{'CI95':>22}{'P(<0)':>9}{'n':>7}")
    results = {}
    for name, key, chunks in [
        ("gap 1X2 (modello - mercato)", "gap_1x2", d_1x2),
        ("gap 12 no pari (modello - mercato)", "gap_12", d_12),
        ("gap O/U 2.5 (modello - mercato)", "gap_ou", d_ou),
        ("Δ prior neopromosse (V4 - V3)", "delta_prior", d_prior),
    ]:
        d = np.concatenate(chunks)
        mean, lo, hi, p_neg = boot(d, rng)
        results |= {f"{key}_mean": mean, f"{key}_ci_lo": lo,
                    f"{key}_ci_hi": hi, f"{key}_p_neg": p_neg}
        sig = " " if lo < 0 < hi else "*"
        print(f"{name:<38}{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]{sig}"
              f"{p_neg:>9.1%}{len(d):>7}")
    print("\n*  = CI95 che non attraversa lo zero.")
    print("Lettura: P(<0) ~ 'probabilita'' che il modello sia meglio (per i gap)")
    print("o che il prior aiuti (per il Δ). Caveat multiple-testing nel diario.")

    # Per-stagione del gap 1X2 (le barre d'errore della tabella del README).
    print(f"\n{'gap 1X2 per stagione':<20}{'media':>10}{'CI95':>24}")
    for s, d in zip(SEASONS, d_1x2):
        mean, lo, hi, _ = boot(d, rng)
        print(f"  {s:<18}{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]")

    results["n_matches"] = int(sum(len(d) for d in d_1x2))
    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase17_bootstrap", "league": "serie_a",
         "variant": "ci_summary", "bootstrap_B": B, "bootstrap_seed": SEED,
         **BASE, "promoted_prior": 0.23}, results, fp))


if __name__ == "__main__":
    main()
