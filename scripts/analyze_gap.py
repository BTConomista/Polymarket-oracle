"""Analisi approfondita del GAP col mercato (model log-loss - market log-loss).

Scompone il divario col mercato lungo quattro assi:
  1. EVOLUZIONE del modello: da grezzo -> attuale (5 versioni).
  2. per STAGIONE (2020-21 -> 2025-26).
  3. per MERCATO (1X2, doppie chance 1X/2X/12, Over/Under 2.5; GG/NG solo vs base).
  4. per FORZA delle squadre (tier da classifica) e per FAVORITISMO di mercato.

Gap > 0  = il mercato e' migliore (nostro deficit).  Piu' vicino a 0 = meglio.
Per GG/NG non ci sono quote nei dati -> si riporta il gap vs BASELINE.

Uso:  python scripts/analyze_gap.py   (parallelo; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import markets, metrics
from scripts.backtest import run_backtest, promoted_teams

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]

# Scala di versioni, dal piu' grezzo all'attuale (come da DIARIO).
VERSIONS = [
    ("V0 grezzo (gol, no shrink/decay)",
     dict(half_life_days=None, shrinkage=0.0, shots_blend=1.0, blend_signal="xg",
          promoted_prior=None)),
    ("V1 gol tarato (Fase 2b)",
     dict(half_life_days=730, shrinkage=1.5, shots_blend=1.0, blend_signal="xg",
          promoted_prior=None)),
    ("V2 +xG blend (Fase 4b)",
     dict(half_life_days=730, shrinkage=1.5, shots_blend=0.75, blend_signal="xg",
          promoted_prior=None)),
    ("V3 emivita 365 (Fase 4d, uff. pre-prior)",
     dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75, blend_signal="xg",
          promoted_prior=None)),
    ("V4 +prior neopromosse (Fase 7, ATTUALE)",
     dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75, blend_signal="xg",
          promoted_prior=(0.23, 0.23))),
]

MARKET_ORDER = ["1X2", "1X (casa o pari)", "2X (ospite o pari)", "12 (no pari)",
                "Over/Under 2.5", "GG/NG"]


def _worker(task):
    vi, season, cfg = task
    df = run_backtest("serie_a", season, cfg["half_life_days"],
                      shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                      blend_signal=cfg["blend_signal"],
                      promoted_prior=cfg["promoted_prior"], verbose=False)
    df["season"] = season
    return vi, season, df


def per_match_1x2_gap(df: pd.DataFrame) -> np.ndarray:
    """model_ll - market_ll per partita (1X2). NaN dove mancano le quote."""
    res = df["result"].tolist()
    model = df[["m_home", "m_draw", "m_away"]].to_numpy()
    mll = -np.log(np.clip(model[np.arange(len(res)),
                          [ {"H":0,"D":1,"A":2}[o] for o in res]], 1e-15, 1))
    mkt = np.full(len(df), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            kll = -np.log(max(p[{"H":0,"D":1,"A":2}[res[i]]], 1e-15))
            mkt[i] = kll
    return mll - mkt


def team_tiers(all_matches: pd.DataFrame, season: str) -> dict[str, str]:
    """Tier per squadra dalla classifica finale: forte (top6)/media/debole (bot6)."""
    d = all_matches[all_matches["season"] == season]
    pts: dict[str, int] = {}
    for _, r in d.iterrows():
        h, a = r.home_team, r.away_team
        pts.setdefault(h, 0); pts.setdefault(a, 0)
        if r.home_goals > r.away_goals: pts[h] += 3
        elif r.home_goals < r.away_goals: pts[a] += 3
        else: pts[h] += 1; pts[a] += 1
    order = sorted(pts, key=lambda t: pts[t], reverse=True)
    tier = {}
    for rank, t in enumerate(order):
        tier[t] = "forte" if rank < 6 else ("debole" if rank >= len(order) - 6 else "media")
    return tier


def main() -> None:
    all_matches = loader.load_league("serie_a")
    tasks = [(vi, s, cfg) for vi, (_, cfg) in enumerate(VERSIONS) for s in SEASONS]
    print(f"Eseguo {len(tasks)} backtest (5 versioni x 6 stagioni)...", flush=True)
    with Pool(6) as pool:
        results = pool.map(_worker, tasks)

    # dfs[vi][season] = df
    dfs: dict[int, dict[str, pd.DataFrame]] = {vi: {} for vi in range(len(VERSIONS))}
    for vi, s, df in results:
        dfs[vi][s] = df

    def gap_1x2(df):
        m = markets.compute_market_metrics(df)["1X2"]
        return m["model_ll"] - m["market_ll"]

    # ============ A. EVOLUZIONE del gap 1X2 per versione x stagione ============
    print("\n" + "=" * 92)
    print("A. EVOLUZIONE DEL GAP 1X2 col mercato (model_ll - market_ll; >0 = mercato meglio)")
    print("=" * 92)
    print(f"{'versione':<44}" + "".join(f"{s:>7}" for s in SEASONS) + f"{'MEDIA':>8}")
    for vi, (label, _) in enumerate(VERSIONS):
        gaps = [gap_1x2(dfs[vi][s]) for s in SEASONS]
        print(f"{label:<44}" + "".join(f"{g:>+7.4f}" for g in gaps)
              + f"{np.mean(gaps):>+8.4f}")
    # valori assoluti (attuale vs mercato) per riferimento
    print("\n  Riferimento valori ASSOLUTI (versione ATTUALE):")
    cur = len(VERSIONS) - 1
    print(f"  {'':<44}" + "".join(f"{s:>7}" for s in SEASONS) + f"{'MEDIA':>8}")
    for name, fn in [("modello", lambda d: markets.compute_market_metrics(d)["1X2"]["model_ll"]),
                     ("mercato", lambda d: markets.compute_market_metrics(d)["1X2"]["market_ll"])]:
        vals = [fn(dfs[cur][s]) for s in SEASONS]
        print(f"  {name:<44}" + "".join(f"{v:>7.4f}" for v in vals) + f"{np.mean(vals):>8.4f}")

    # ============ B. GAP per MERCATO x versione (pool 6 stagioni) ============
    print("\n" + "=" * 92)
    print("B. GAP per MERCATO x versione (pool 6 stagioni; GG/NG = gap vs BASELINE, no quote)")
    print("=" * 92)
    print(f"{'versione':<44}" + "".join(f"{m.split(' ')[0]:>9}" for m in MARKET_ORDER))
    for vi, (label, _) in enumerate(VERSIONS):
        pool_df = pd.concat([dfs[vi][s] for s in SEASONS], ignore_index=True)
        mm = markets.compute_market_metrics(pool_df)
        cells = []
        for mk in MARKET_ORDER:
            d = mm[mk]
            ref = d.get("market_ll", d["baseline_ll"])
            cells.append(d["model_ll"] - ref)
        print(f"{label:<44}" + "".join(f"{c:>+9.4f}" for c in cells))
    print("  (GG/NG: niente quote -> gap vs baseline; le doppie chance usano quote derivate 1X2)")

    # ============ C. DEEP DIVE versione ATTUALE ============
    print("\n" + "=" * 92)
    print("C. DEEP DIVE — versione ATTUALE (gol+xG+prior)")
    print("=" * 92)

    # C1. per stagione x mercato
    print("\n  C1. Gap per STAGIONE x MERCATO")
    print(f"  {'stagione':<10}" + "".join(f"{m.split(' ')[0]:>9}" for m in MARKET_ORDER))
    for s in SEASONS:
        mm = markets.compute_market_metrics(dfs[cur][s])
        cells = [mm[mk]["model_ll"] - mm[mk].get("market_ll", mm[mk]["baseline_ll"])
                 for mk in MARKET_ORDER]
        print(f"  {s:<10}" + "".join(f"{c:>+9.4f}" for c in cells))

    # C2. gap 1X2 per FORZA squadra (tier) e per neopromosse
    print("\n  C2. Gap 1X2 per FORZA delle squadre coinvolte (media sulle partite del gruppo)")
    tier_gap = {"forte": [], "media": [], "debole": [], "neopromossa": []}
    for s in SEASONS:
        df = dfs[cur][s]
        tiers = team_tiers(all_matches, s)
        promoted = promoted_teams(all_matches, s)
        gaps = per_match_1x2_gap(df)
        for i, (_, r) in enumerate(df.iterrows()):
            if np.isnan(gaps[i]):
                continue
            involved = {r.home_team, r.away_team}
            for t in involved:
                tier_gap[tiers.get(t, "media")].append(gaps[i])
            if involved & promoted:
                tier_gap["neopromossa"].append(gaps[i])
    print(f"  {'gruppo':<14}{'n(partite-squadra)':>20}{'gap medio 1X2':>16}")
    for g in ["forte", "media", "debole", "neopromossa"]:
        arr = np.array(tier_gap[g])
        print(f"  {g:<14}{len(arr):>20}{arr.mean():>+16.4f}")
    print("  (una partita conta per entrambe le squadre coinvolte)")

    # C3. gap 1X2 per FAVORITISMO di mercato (quanto e' netto il favorito)
    print("\n  C3. Gap 1X2 per FAVORITISMO di mercato (prob. max del favorito, devigata)")
    buckets = {"equilibrata (<45%)": [], "moderata (45-60%)": [], "netta (>60%)": []}
    for s in SEASONS:
        df = dfs[cur][s]
        gaps = per_match_1x2_gap(df)
        for i, (_, r) in enumerate(df.iterrows()):
            if not np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
                continue
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away).max()
            key = ("equilibrata (<45%)" if p < 0.45
                   else "moderata (45-60%)" if p < 0.60 else "netta (>60%)")
            buckets[key].append(gaps[i])
    print(f"  {'gruppo':<22}{'n':>8}{'gap medio 1X2':>16}")
    for k, arr in buckets.items():
        a = np.array(arr)
        print(f"  {k:<22}{len(a):>8}{a.mean():>+16.4f}")


if __name__ == "__main__":
    main()
