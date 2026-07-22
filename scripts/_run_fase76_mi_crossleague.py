"""Fase 76 — Market-implied multi-mercato su Premier League e La Liga (chiusura).

Chiude la pista #4 (PISTE.md): il motore market-implied — il piu' forte del
progetto — era backtestato multi-mercato SOLO in Serie A (Fase 26: batte il
DC-da-gol su 13/14 mercati e la baseline su 13/14). La Fase 75 l'ha validato
sul 2017-19 dall'APERTURA (2.280 partite vergini, 17/20 mercati vs baseline).
Qui il tassello mancante: le stesse 6 stagioni di CHIUSURA (2020-21 → 2025-26)
di Premier e Liga, stesso identico protocollo della Fase 26 (walk-forward per
stagione, bootstrap appaiato, RHO=-0.06), riusando le sue funzioni.

Per ogni lega: market-implied (inversione chiusura 1X2+O/U -> lambda,mu ->
matrice DC -> ogni mercato) vs DC-da-gol vs baseline in-sample. La domanda:
il motore trasferisce cross-lega ANCHE sulla chiusura (non solo apertura),
come previsto (struttura universale, ρ unico) o le costanti Serie A non bastano?

Uso:  python scripts/_run_fase76_mi_crossleague.py    (2 leghe x 6 stagioni; minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                                   # noqa: E402
from src.evaluation import experiment_log                     # noqa: E402
# Riuso ESATTO delle funzioni della Fase 26 (stesso protocollo, numeri 1:1)
from scripts import _run_market_implied as MI                 # noqa: E402
from scripts._run_market_implied import (                     # noqa: E402
    BINARY, B, MAXG, RHO_MAIN, SEED, baseline_ll, boot,
    dc_lambda_mu, eval_markets, invert_all,
)
from src.config import LEAGUE_CONFIGS                         # noqa: E402

# TUTTE le stagioni con chiusura O/U reale (2019-20 in poi): il market-implied
# non richiede training, quindi la finestra e' limitata solo dalla disponibilita'
# della chiusura. Fase 26 usava 2021-2526 per la Serie A -> qui esteso a 1920
# (2019-20, la prima con chiusura reale) su TUTTE e 3 le leghe. Il 2017-19 non ha
# chiusura reale (Fase 73) ed e' gia' coperto DALL'APERTURA nella Fase 75.
TEST_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
LEAGUES = ["serie_a", "premier_league", "la_liga"]
ANCHORS = {"over_2.5"}

# Le funzioni importate iterano sul TEST_SEASONS del LORO modulo: lo allineo a
# questa finestra estesa (altrimenti il 1920 verrebbe ignorato).
MI.TEST_SEASONS = TEST_SEASONS


def _worker(args):
    league, season = args
    from scripts.backtest import run_backtest
    cfg = LEAGUE_CONFIGS[league]
    delta = cfg["promoted_prior"]
    df = run_backtest(league, season, cfg["half_life_days"],
                      shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                      blend_signal=cfg["blend_signal"],
                      promoted_prior=(delta, delta), verbose=False)
    df["season"] = season
    return season, df


def run_league(league: str, rng) -> dict:
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, [(league, s) for s in TEST_SEASONS]))
    fp = experiment_log.data_fingerprint(loader.load_league(league))

    lm_mkt = invert_all(dfs, targets_over=True, rho=RHO_MAIN)
    lm_dc = dc_lambda_mu(dfs)
    ev_mkt = eval_markets(lm_mkt, dfs, RHO_MAIN)
    ev_dc = eval_markets(lm_dc, dfs, RHO_MAIN)
    ev_base = baseline_ll(dfs)

    markets = BINARY + ["multigol", "risultato_esatto"]
    print("=" * 100)
    print(f"MARKET-IMPLIED — {league} (chiusura 1X2+O/U, rho={RHO_MAIN}, "
          f"stagioni {TEST_SEASONS[0]}..{TEST_SEASONS[-1]})")
    print("log-loss; Δ = market-implied - DC-da-gol (<0 = il mercato aiuta); * = NON prezzato")
    print("=" * 100)
    print(f"  {'mercato':<18}{'mkt-impl':>10}{'DC-gol':>10}{'baseline':>10}"
          f"{'Δ vs DC':>10}{'CI95 Δ':>20}{'P<0':>7}")
    summary = {}
    for mk in markets:
        g, dc, bl = ev_mkt[mk], ev_dc[mk], ev_base[mk]
        mean, lo, hi, pneg = boot(g - dc, rng)
        star = "" if mk in ANCHORS else " *"
        print(f"  {mk+star:<18}{g.mean():>10.4f}{dc.mean():>10.4f}{bl.mean():>10.4f}"
              f"{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]{pneg:>7.1%}")
        summary[mk] = (float(g.mean()), float(dc.mean()), float(bl.mean()),
                       float(mean), float(lo), float(hi), float(pneg))

    nonanchor = [mk for mk in markets if mk not in ANCHORS]
    beat_dc = sum(1 for mk in nonanchor if summary[mk][3] < 0)
    beat_dc_sig = sum(1 for mk in nonanchor if summary[mk][5] < 0)
    beat_base = sum(1 for mk in nonanchor if summary[mk][0] < summary[mk][2])
    print(f"\n  Su {len(nonanchor)} mercati non-ancora ({league}): market-implied batte "
          f"il DC-da-gol in {beat_dc} (CI<0 in {beat_dc_sig}); batte la baseline in {beat_base}.")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase76_mi_crossleague", "league": league,
         "variant": "sweep_summary", "rho": RHO_MAIN, "test_seasons": TEST_SEASONS,
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"beat_dc_count": beat_dc, "beat_dc_sig_count": beat_dc_sig,
         "beat_baseline_count": beat_base, "n_nonanchor": len(nonanchor),
         **{f"mktimpl_{mk}": summary[mk][0] for mk in nonanchor},
         **{f"dcgol_{mk}": summary[mk][1] for mk in nonanchor},
         **{f"delta_{mk}": summary[mk][3] for mk in nonanchor}}, fp))
    return {"league": league, "beat_dc": beat_dc, "beat_dc_sig": beat_dc_sig,
            "beat_base": beat_base, "n": len(nonanchor)}


def main():
    rng = np.random.default_rng(SEED)
    out = [run_league(lg, rng) for lg in LEAGUES]
    print("\n" + "=" * 100)
    print("SINTESI cross-lega (market-implied dalla CHIUSURA, mercati non-ancora)")
    print("  riferimento Serie A (Fase 26): batte DC 13/14, baseline 13/14")
    for r in out:
        print(f"  {r['league']:16s}: batte DC {r['beat_dc']}/{r['n']} "
              f"(CI<0 {r['beat_dc_sig']}); baseline {r['beat_base']}/{r['n']}")


if __name__ == "__main__":
    main()
