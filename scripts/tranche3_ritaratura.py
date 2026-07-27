"""Tranche 3, passo 3 del playbook: RI-TARATURA per-lega degli iperparametri.

Una leva alla volta (§1.2 del CLAUDE.md), le altre ferme al default Serie A.
Il riferimento (config Serie A pura) e' gia' calcolato dal tracer: qui si
misurano solo le varianti.

Leve provate (griglia minima del playbook):
  - **δ neopromosse** — l'unico iperparametro finora davvero per-lega. Valore
    per-lega calcolato dai dati: Bundesliga 0.277, Ligue 1 0.188 (report 3 §6);
  - **emivita** 730g (contro i 365 del default);
  - **shrinkage** 3.0 (contro 1.5).

ASPETTATIVA DICHIARATA PRIMA (playbook): curve **piatte** su emivita e
shrinkage (successo su 3/3 leghe finora: il tetto e' informativo, non di
taratura); δ per-lega adottabile per motivazione strutturale anche con CI non
conclusivo (precedente: Fasi 7/17/57).

Uso: python scripts/tranche3_ritaratura.py [--leagues ...]
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
CANTIERE_DATA = ROOT / "data"
_orig = database.snapshot_path
database.snapshot_path = lambda k="serie_a": (
    CANTIERE_DATA / f"{k}_matches.csv" if k in nuove_leghe.NEW_LEAGUES else _orig(k))

from backtest import run_backtest  # noqa: E402
from tranche3_tracer import TEST_SEASONS, bootstrap_ci, perpartita_logloss  # noqa: E402

# δ calcolato dai dati di ciascuna lega (report 3 §6): ln(gol_lega/gol_promosse)
DELTA_PER_LEGA = {"bundesliga": 0.277, "ligue_1": 0.188}


def varianti(league: str) -> dict[str, dict]:
    base = dict(half_life_days=SERIE_A["half_life_days"],
                shrinkage=SERIE_A["shrinkage"],
                shots_blend=SERIE_A["shots_blend"],
                blend_signal=SERIE_A["blend_signal"],
                delta=SERIE_A["promoted_prior"])
    d = DELTA_PER_LEGA[league]
    return {
        "delta_per_lega": {**base, "delta": d},
        "emivita_730": {**base, "delta": d, "half_life_days": 730.0},
        "shrinkage_3": {**base, "delta": d, "shrinkage": 3.0},
    }


def esegui(league: str, cfg: dict, seasons: list[str]) -> pd.DataFrame:
    frames = []
    for s in seasons:
        df = run_backtest(league, s, cfg["half_life_days"],
                          shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                          blend_signal=cfg["blend_signal"],
                          promoted_prior=(cfg["delta"], cfg["delta"]), verbose=False)
        df["test_season"] = s
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=["bundesliga", "ligue_1"])
    ap.add_argument("--seasons", nargs="*", default=TEST_SEASONS)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    risultati = {}
    for league in args.leagues:
        rif_path = OUT / f"tracer_pred_{league}.csv"
        if not rif_path.exists():
            raise SystemExit(f"manca {rif_path}: esegui prima tranche3_tracer.py")
        rif = pd.read_csv(rif_path, dtype={"test_season": str}, parse_dates=["date"])
        rif = rif[rif.test_season.isin(args.seasons)]
        m_rif = experiment_log.compute_metrics(rif)
        ll_rif = perpartita_logloss(rif[["m_home", "m_draw", "m_away"]].to_numpy(),
                                    rif.result.tolist())
        print(f"\n=== {league} ===")
        print(f"  RIFERIMENTO (config Serie A pura, delta 0.23): "
              f"1X2 {m_rif['x2_model_logloss']:.4f}  O/U {m_rif['ou_model_logloss']:.4f}")

        risultati[league] = {"riferimento": {
            "x2": m_rif["x2_model_logloss"], "ou": m_rif["ou_model_logloss"]}}
        for nome, cfg in varianti(league).items():
            t0 = time.time()
            df = esegui(league, cfg, args.seasons)
            m = experiment_log.compute_metrics(df)
            ll = perpartita_logloss(df[["m_home", "m_draw", "m_away"]].to_numpy(),
                                    df.result.tolist())
            d, lo, hi = bootstrap_ci(ll_rif, ll)   # >0 = la variante MIGLIORA
            print(f"  {nome:16s} 1X2 {m['x2_model_logloss']:.4f} "
                  f"({m['x2_model_logloss']-m_rif['x2_model_logloss']:+.4f})  "
                  f"O/U {m['ou_model_logloss']:.4f}  | guadagno {d:+.4f} "
                  f"CI95 [{lo:+.4f}, {hi:+.4f}] -> "
                  f"{'MEGLIO' if lo > 0 else ('PEGGIO' if hi < 0 else 'nel rumore')}"
                  f"   [{time.time()-t0:.0f}s]")
            risultati[league][nome] = {
                "config": cfg, "x2": m["x2_model_logloss"], "ou": m["ou_model_logloss"],
                "delta_vs_rif": m["x2_model_logloss"] - m_rif["x2_model_logloss"],
                "guadagno": d, "ci95": [lo, hi],
                "verdetto": "meglio" if lo > 0 else ("peggio" if hi < 0 else "nel rumore")}

    path = OUT / "tranche3_ritaratura.json"
    prev = json.loads(path.read_text()) if path.exists() else {}
    prev.update(risultati)
    path.write_text(json.dumps(prev, indent=2, default=str))
    print(f"\n-> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
