"""Tranche 3, passo 2 del playbook: TRACER BULLET del Dixon-Coles sulle leghe nuove.

Domanda: il modello **cosi' com'e'** (config Serie A, nessuna ri-taratura)
funziona su Bundesliga e Ligue 1? Prima di toccare un solo iperparametro
(§1.1 e §1.3 del CLAUDE.md: fetta verticale reale, poi si raffina).

Metodo: identico a quello di tutto il progetto — walk-forward settimanale
(`scripts/backtest.run_backtest`), metriche dalla fonte unica
(`experiment_log.compute_metrics`), finestra di test standard di 6 stagioni
(2020-21 → 2025-26) per essere confrontabile con i numeri storici.

ASPETTATIVE DICHIARATE PRIMA (playbook, passo 2):
  - il DC deve battere la baseline (frequenze di stagione);
  - NON deve battere il mercato: gap atteso +0.015…+0.021 di log-loss 1X2,
    piu' largo dove il book e' piu' liquido.

Le due leghe nuove leggevano lo snapshot dal cantiere (R4: non si toccava
`data/`); dall'integrazione leggono `data/<lega>_matches.csv` come le altre.

Uso:
    python scripts/tranche3_tracer.py                      # 2 leghe nuove
    python scripts/tranche3_tracer.py --leagues serie_a    # controllo
    python scripts/tranche3_tracer.py --seasons 2526
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.config import SERIE_A  # noqa: E402
from src.data import database  # noqa: E402
from src.evaluation import experiment_log  # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"

# STORICO (Fase 101-bis): qui viveva un dirottamento di `database.snapshot_path`
# verso il cantiere, perche' Bundesliga e Ligue 1 non erano ancora in `data/`.
# Dall'integrazione e' un NO-OP dimostrato — `snapshot_path` restituisce gia'
# `data/<lega>_matches.csv` per tutte e 5 le leghe — quindi e' stato rimosso.

from backtest import run_backtest  # noqa: E402

# Finestra di test standard del progetto: 6 stagioni.
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]


def bootstrap_ci(a: np.ndarray, b: np.ndarray, B: int = 10000, seed: int = 7):
    """CI95 appaiato sulla differenza media (a - b), B ricampionamenti."""
    rng = np.random.default_rng(seed)
    d = a - b
    idx = rng.integers(0, len(d), (B, len(d)))
    boot = d[idx].mean(axis=1)
    return float(d.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def perpartita_logloss(p: np.ndarray, outcomes: list[str]) -> np.ndarray:
    """Log-loss riga per riga (serve al bootstrap appaiato)."""
    idx = {"H": 0, "D": 1, "A": 2}
    p = np.clip(p, 1e-12, 1.0)
    return np.array([-np.log(p[i, idx[o]]) for i, o in enumerate(outcomes)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=["bundesliga", "ligue_1"])
    ap.add_argument("--seasons", nargs="*", default=TEST_SEASONS)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    cfg = SERIE_A
    prior = (cfg["promoted_prior"], cfg["promoted_prior"])
    print(f"Config usata (Serie A, NON ri-tarata): emivita {cfg['half_life_days']:.0f}g, "
          f"shrinkage {cfg['shrinkage']}, blend {cfg['shots_blend']} "
          f"({cfg['blend_signal']}), delta neopromosse {cfg['promoted_prior']}")

    riassunto = {}
    for league in args.leagues:
        print(f"\n=== {league} ===")
        frames = []
        for season in args.seasons:
            t0 = time.time()
            df = run_backtest(
                league, season, cfg["half_life_days"],
                shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                blend_signal=cfg["blend_signal"], promoted_prior=prior,
                verbose=False)
            df["test_season"] = season
            frames.append(df)
            m = experiment_log.compute_metrics(df)
            print(f"  {season}: {len(df):3d} gare in {time.time()-t0:5.1f}s  "
                  f"1X2 modello {m['x2_model_logloss']:.4f} | "
                  f"baseline {m['x2_baseline_logloss']:.4f} | "
                  f"mercato {m['x2_market_logloss']:.4f}  "
                  f"(gap {m['x2_model_logloss']-m['x2_market_logloss']:+.4f})")
        allp = pd.concat(frames, ignore_index=True)
        allp.to_csv(OUT / f"tracer_pred_{league}.csv", index=False)

        m = experiment_log.compute_metrics(allp)
        # bootstrap appaiato modello vs baseline e modello vs mercato
        outcomes = allp["result"].tolist()
        ll_model = perpartita_logloss(allp[["m_home", "m_draw", "m_away"]].to_numpy(), outcomes)
        base = np.tile([np.mean([o == k for o in outcomes]) for k in "HDA"], (len(allp), 1))
        ll_base = perpartita_logloss(base, outcomes)
        from src.evaluation.metrics import devig_1x2
        has = allp[["odds_home", "odds_draw", "odds_away"]].notna().all(axis=1).to_numpy()
        mkt = np.array([devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                        if h else (np.nan,) * 3
                        for r, h in zip(allp.itertuples(), has)])
        ll_mkt = np.full(len(allp), np.nan)
        ll_mkt[has] = perpartita_logloss(mkt[has], [o for o, h in zip(outcomes, has) if h])

        d_base, lo_b, hi_b = bootstrap_ci(ll_base, ll_model)
        d_mkt, lo_m, hi_m = bootstrap_ci(ll_model[has], ll_mkt[has])
        print(f"\n  POOLED ({len(allp)} partite, {len(args.seasons)} stagioni)")
        print(f"    1X2  modello {m['x2_model_logloss']:.4f}  "
              f"baseline {m['x2_baseline_logloss']:.4f}  mercato {m['x2_market_logloss']:.4f}")
        print(f"    O/U  modello {m['ou_model_logloss']:.4f}  "
              f"baseline {m['ou_baseline_logloss']:.4f}  mercato {m['ou_market_logloss']:.4f}")
        print(f"    modello vs BASELINE: guadagno {d_base:+.4f} "
              f"CI95 [{lo_b:+.4f}, {hi_b:+.4f}] -> "
              f"{'CONCLUSIVO' if lo_b > 0 else 'non conclusivo'}")
        print(f"    modello vs MERCATO : gap     {d_mkt:+.4f} "
              f"CI95 [{lo_m:+.4f}, {hi_m:+.4f}] -> "
              f"{'il mercato vince, conclusivo' if lo_m > 0 else 'non conclusivo'}")

        riassunto[league] = {
            "n_partite": int(len(allp)), "stagioni": args.seasons,
            "config": {k: cfg[k] for k in cfg},
            "pooled": {k: v for k, v in m.items() if isinstance(v, (int, float))},
            "vs_baseline": {"guadagno": d_base, "ci95": [lo_b, hi_b]},
            "vs_mercato": {"gap": d_mkt, "ci95": [lo_m, hi_m]},
            "per_stagione": {
                s: {kk: vv for kk, vv in experiment_log.compute_metrics(
                    allp[allp.test_season == s]).items()
                    if isinstance(vv, (int, float))}
                for s in args.seasons},
        }

    path = OUT / "tranche3_tracer.json"
    prev = json.loads(path.read_text()) if path.exists() else {}
    prev.update(riassunto)
    path.write_text(json.dumps(prev, indent=2, default=str))
    print(f"\n-> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
