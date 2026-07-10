"""Driver Fase 7 — valida il prior di cold-start per le neopromosse.

Confronta baseline vs promoted_prior sulle stagioni di valutazione (2020-21 ->
2025-26). Il delta del prior (quanto sono deboli le neopromosse) e' stimato
LEAVE-FUTURE-OUT: per la stagione S si usano solo le neopromosse delle stagioni
< S (nessun look-ahead). Config del modello = ufficiale (365g/1.5/0.75/xG).

Riporta la log-loss 1X2 complessiva E ristretta alle partite che coinvolgono una
neopromossa (dove il diagnostico diceva che il modello perde: +0.029). Registra
ogni run col prior in experiments/runs.jsonl.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import analysis, experiment_log, metrics
from scripts.backtest import run_backtest, promoted_teams

HALF_LIFE, SHRINK, BLEND, SIGNAL = 365.0, 1.5, 0.75, "xg"
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]


def estimate_delta(all_matches: pd.DataFrame, seasons: list[str]) -> tuple[float, float]:
    """Stima (delta_att, delta_def) dalle neopromosse delle ``seasons`` date:
    log(gol_promosse/gol_lega) per attacco e difesa. Fallback 0.23 se vuoto."""
    gf_ratios, ga_ratios = [], []
    for s in seasons:
        promoted = promoted_teams(all_matches, s)
        if not promoted:
            continue
        cur = all_matches[all_matches["season"] == s]
        league_pg = (cur["home_goals"].sum() + cur["away_goals"].sum()) / (2 * len(cur))
        for t in promoted:
            h, a = cur[cur.home_team == t], cur[cur.away_team == t]
            gp = len(h) + len(a)
            if gp == 0:
                continue
            gf = (h.home_goals.sum() + a.away_goals.sum()) / gp
            ga = (h.away_goals.sum() + a.home_goals.sum()) / gp
            gf_ratios.append(np.log(max(gf, 0.1) / league_pg))
            ga_ratios.append(np.log(max(ga, 0.1) / league_pg))
    if not gf_ratios:
        return 0.23, 0.23
    return -float(np.mean(gf_ratios)), float(np.mean(ga_ratios))  # delta_att, delta_def


def ll_on(df: pd.DataFrame, mask: np.ndarray) -> float:
    probs = df.loc[mask, ["m_home", "m_draw", "m_away"]].to_numpy()
    return metrics.log_loss_1x2(probs, df.loc[mask, "result"].tolist())


def main() -> None:
    all_matches = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_matches)
    seasons = list(sources.SEASONS)

    rows = []
    for s in TEST_SEASONS:
        prior_seasons = seasons[:seasons.index(s)]
        d_att, d_def = estimate_delta(all_matches, prior_seasons)
        prior = (round(d_att, 3), round(d_def, 3))

        base = run_backtest("serie_a", s, HALF_LIFE, shrinkage=SHRINK,
                            shots_blend=BLEND, blend_signal=SIGNAL, verbose=False)
        prom = run_backtest("serie_a", s, HALF_LIFE, shrinkage=SHRINK,
                            shots_blend=BLEND, blend_signal=SIGNAL,
                            promoted_prior=prior, verbose=False)

        promoted = promoted_teams(all_matches, s)
        mask = (base.home_team.isin(promoted) | base.away_team.isin(promoted)).to_numpy()

        m_prom = experiment_log.compute_metrics(prom)
        config = {
            "league": "serie_a", "test_season": s, "half_life_days": HALF_LIFE,
            "shrinkage": SHRINK, "shots_blend": BLEND, "blend_signal": SIGNAL,
            "promoted_prior": list(prior), "source": "fase7_promosse",
        }
        experiment_log.append_run(experiment_log.make_record(config, m_prom, fp))

        rows.append({
            "season": s, "delta": prior, "n_prom": int(mask.sum()),
            "all_base": ll_on(base, np.ones(len(base), bool)),
            "all_prom": ll_on(prom, np.ones(len(prom), bool)),
            "sub_base": ll_on(base, mask),
            "sub_prom": ll_on(prom, mask),
            "market": m_prom["x2_market_logloss"],
        })
        r = rows[-1]
        print(f"[{s}] δ={prior}  TUTTE {r['all_base']:.4f}->{r['all_prom']:.4f} "
              f"({r['all_prom']-r['all_base']:+.4f})  | NEOPROM ({r['n_prom']}) "
              f"{r['sub_base']:.4f}->{r['sub_prom']:.4f} ({r['sub_prom']-r['sub_base']:+.4f})",
              flush=True)

    print("\n" + "=" * 82)
    print("PRIOR NEOPROMOSSE — 1X2 log-loss (piu' basso = meglio)")
    print("=" * 82)
    print(f"{'stag.':<7}{'TUTTE base':>12}{'TUTTE prior':>13}{'Δ':>9}"
          f"{'NEOPR base':>12}{'NEOPR prior':>13}{'Δ':>9}")
    agg = {k: 0.0 for k in ("ab", "ap", "sb", "sp")}
    for r in rows:
        print(f"{r['season']:<7}{r['all_base']:>12.4f}{r['all_prom']:>13.4f}"
              f"{r['all_prom']-r['all_base']:>+9.4f}{r['sub_base']:>12.4f}"
              f"{r['sub_prom']:>13.4f}{r['sub_prom']-r['sub_base']:>+9.4f}")
        agg["ab"] += r["all_base"]; agg["ap"] += r["all_prom"]
        agg["sb"] += r["sub_base"]; agg["sp"] += r["sub_prom"]
    n = len(rows)
    print("-" * 82)
    print(f"{'MEDIA':<7}{agg['ab']/n:>12.4f}{agg['ap']/n:>13.4f}"
          f"{(agg['ap']-agg['ab'])/n:>+9.4f}{agg['sb']/n:>12.4f}"
          f"{agg['sp']/n:>13.4f}{(agg['sp']-agg['sb'])/n:>+9.4f}")
    print("\nΔ < 0 = il prior MIGLIORA. 'NEOPR' = solo partite con una neopromossa.")


if __name__ == "__main__":
    main()
