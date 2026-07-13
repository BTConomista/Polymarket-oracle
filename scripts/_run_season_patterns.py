"""Fase 30 — Anatomia dei pattern DENTRO la stagione.

La Fase 28 ha visto che il finale e' piu' difficile per tutti; la Fase 29 ha
escluso i dead rubber. Qui l'anatomia completa: per ogni periodo della stagione,
non solo il gap col mercato ma COSA cambia (pareggi, gol, vantaggio-casa,
entropia degli esiti), per capire PERCHE' certi momenti sono piu' difficili, e
se il pattern e' coerente tra le 6 stagioni.

Domanda chiave: l'aumento del log-loss nel finale e' spiegato da esiti PIU'
BILANCIATI/casuali (entropia H/D/A piu' alta -> tutti prevedono peggio,
meccanicamente)? O e' altro?

Uso:  python scripts/_run_season_patterns.py     (6 backtest; ~alcuni minuti)
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

TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
_OI = {"H": 0, "D": 1, "A": 2}


def _worker(season):
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df = df.sort_values("date").reset_index(drop=True)
    df["giornata"] = np.minimum(np.arange(len(df)) // 10 + 1, 38)
    df["season"] = season
    return season, df


def ll_1x2(P, out):
    idx = [_OI[o] for o in out]
    return -np.log(np.clip(P[np.arange(len(out)), idx], 1e-15, 1))


def entropy(outs):
    p = np.array([np.mean([o == k for o in outs]) for k in "HDA"])
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def main():
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, TEST_SEASONS))
    big = pd.concat([dfs[s] for s in TEST_SEASONS], ignore_index=True)

    all_m = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_m)
    for s in TEST_SEASONS:
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase30_season_patterns", "league": "serie_a",
             "test_season": s, **{k: v for k, v in CFG.items()
             if k != "promoted_prior"}, "promoted_prior": 0.23},
            experiment_log.compute_metrics(dfs[s]), fp))

    out = big["result"].tolist()
    model = big[["m_home", "m_draw", "m_away"]].to_numpy()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in big.itertuples()])
    llm = ll_1x2(model, out); llk = ll_1x2(mkt, out)
    gap = llm - llk
    gio = big["giornata"].to_numpy()
    res = np.array(out)
    goals = (big["home_goals"] + big["away_goals"]).to_numpy()

    BUCKETS = [("1-6", 1, 6), ("7-19", 7, 19), ("20-31", 20, 31),
               ("32-34", 32, 34), ("35-38", 35, 38)]
    print("=" * 104)
    print("ANATOMIA DENTRO LA STAGIONE — cosa cambia per periodo (medie su 6 stagioni)")
    print("=" * 104)
    print(f"  {'giorn.':<8}{'n':>5}{'mod ll':>8}{'mkt ll':>8}{'gap':>8}"
          f"{'%casa':>7}{'%pari':>7}{'%osp':>7}{'gol/g':>7}{'%over':>7}{'entrop':>8}")
    for name, lo, hi in BUCKETS:
        m = (gio >= lo) & (gio <= hi)
        ph = np.mean(res[m] == "H"); pd_ = np.mean(res[m] == "D"); pa = np.mean(res[m] == "A")
        print(f"  {name:<8}{m.sum():>5}{llm[m].mean():>8.4f}{llk[m].mean():>8.4f}"
              f"{gap[m].mean():>+8.4f}{ph:>7.1%}{pd_:>7.1%}{pa:>7.1%}"
              f"{goals[m].mean():>7.2f}{np.mean(goals[m] >= 3):>7.1%}{entropy(res[m]):>8.4f}")

    # correlazioni matchday ~ variabili
    print("\n  Correlazioni con la giornata (segno = tendenza nel corso della stagione):")
    for label, v in [("log-loss modello", llm), ("log-loss mercato", llk),
                     ("gap modello-mercato", gap),
                     ("e' pareggio", (res == "D").astype(float)),
                     ("gol totali", goals.astype(float)),
                     ("vittoria casa", (res == "H").astype(float))]:
        print(f"    {label:<24}{np.corrcoef(gio, v)[0, 1]:+.4f}")

    # coerenza tra stagioni: gap early/mid/late per stagione
    print("\n  Coerenza tra stagioni — gap modello-mercato per terzo di stagione:")
    print(f"  {'stagione':<10}{'inizio(1-12)':>14}{'meta(13-25)':>14}{'fine(26-38)':>14}")
    late_minus_early = []
    for s in TEST_SEASONS:
        ms = big["season"].to_numpy() == s
        g = gio[ms]; gp = gap[ms]
        e = gp[g <= 12].mean(); md = gp[(g >= 13) & (g <= 25)].mean(); l = gp[g >= 26].mean()
        late_minus_early.append(l - e)
        print(f"  {s:<10}{e:>+14.4f}{md:>+14.4f}{l:>+14.4f}")
    lme = np.array(late_minus_early)
    n_up = int((lme > 0).sum())
    print(f"\n  gap fine-inizio: media {lme.mean():+.4f}, positivo in {n_up}/6 stagioni "
          f"(range {lme.min():+.4f}..{lme.max():+.4f})")

    print("\n  Lettura: se l'entropia degli esiti sale a fine stagione, il maggior")
    print("  log-loss e' meccanico (esiti piu' bilanciati -> tutti prevedono peggio).")
    print("  Se il gap fine-inizio e' incoerente tra stagioni, non c'e' pattern robusto.")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase30_season_patterns", "league": "serie_a",
         "variant": "patterns_summary", "promoted_prior": 0.23},
        {"n_matches": int(len(big)),
         "corr_matchday_model_ll": float(np.corrcoef(gio, llm)[0, 1]),
         "corr_matchday_gap": float(np.corrcoef(gio, gap)[0, 1]),
         "corr_matchday_draw": float(np.corrcoef(gio, (res == "D"))[0, 1]),
         "corr_matchday_goals": float(np.corrcoef(gio, goals)[0, 1]),
         "gap_late_minus_early_mean": float(lme.mean()),
         "gap_late_minus_early_n_positive": n_up,
         "entropy_early": entropy(res[gio <= 12]),
         "entropy_late": entropy(res[gio >= 32])}, fp))


if __name__ == "__main__":
    main()
