"""Fase 28 — Quando falliscono i modelli? Errore per MOMENTO della stagione.

Ipotesi: a fine campionato alcune squadre non lottano piu' per nulla (salve o
gia' retrocesse), quindi i risultati delle ultime giornate sono piu' "ballerini".
Ma la domanda decisiva e': e' un fallimento NOSTRO o falliscono TUTTI (mercato
incluso)?
  - se a fine stagione peggiorano sia modello SIA mercato e il GAP resta piatto
    -> casualita' irriducibile: non un nostro difetto, e nemmeno dati sulla
    motivazione aiuterebbero (neanche il mercato la prezza);
  - se il GAP si allarga (il modello peggiora PIU' del mercato) -> il mercato
    prezza la posta in palio e noi no: difetto nostro, dati nuovi utili.

Calcola log-loss di modello e mercato (1X2 e O/U) per giornata, il gap per
bucket, e il test late (giornate 35-38) vs resto con CI bootstrap sui tre
livelli (modello, mercato, gap). Giornata stimata ordinando le partite di ogni
stagione per data (gruppi di 10).

Uso:  python scripts/_run_matchday.py     (6 backtest; ~alcuni minuti)
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
B, SEED = 10_000, 28
_OI = {"H": 0, "D": 1, "A": 2}


def _worker(season):
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    # Giornata stimata: ordina per data, gruppi di 10 (20 squadre -> 10 gare/turno).
    df = df.sort_values("date").reset_index(drop=True)
    df["giornata"] = np.minimum(np.arange(len(df)) // 10 + 1, 38)
    return season, df


def ll_1x2_rows(P, out):
    idx = [_OI[o] for o in out]
    return -np.log(np.clip(P[np.arange(len(out)), idx], 1e-15, 1))


def ll_bin_rows(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot_diff(a, b, rng):
    """media(a)-media(b) con CI bootstrap (campioni indipendenti)."""
    ma = a[rng.integers(0, len(a), (B, len(a)))].mean(axis=1)
    mb = b[rng.integers(0, len(b), (B, len(b)))].mean(axis=1)
    d = ma - mb
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, TEST_SEASONS))
    big = pd.concat([dfs[s] for s in TEST_SEASONS], ignore_index=True)

    all_m = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase28_matchday", "league": "serie_a", "test_season": s,
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, experiment_log.compute_metrics(df), fp))

    out = big["result"].tolist()
    model = big[["m_home", "m_draw", "m_away"]].to_numpy()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in big.itertuples()])
    llm = ll_1x2_rows(model, out)
    llk = ll_1x2_rows(mkt, out)
    # O/U
    y_ou = big["is_over"].to_numpy().astype(float)
    p_mou = big["m_over"].to_numpy()
    p_kou = np.array([metrics.devig_binary(r.odds_over, r.odds_under)[0]
                      for r in big.itertuples()])
    llm_ou = ll_bin_rows(p_mou, y_ou)
    llk_ou = ll_bin_rows(p_kou, y_ou)
    gio = big["giornata"].to_numpy()

    BUCKETS = [("1-6 (inizio)", 1, 6), ("7-19", 7, 19), ("20-31", 20, 31),
               ("32-34", 32, 34), ("35-38 (fine)", 35, 38)]
    print("=" * 96)
    print("ERRORE PER MOMENTO DELLA STAGIONE — log-loss 1X2 (modello, mercato, gap)")
    print("gap = modello - mercato; se il gap NON cresce a fine stagione, e' casualita' per tutti")
    print("=" * 96)
    print(f"  {'giornate':<16}{'n':>6}{'modello':>10}{'mercato':>10}{'gap':>10}"
          f"{'O/U mod':>10}{'O/U mkt':>10}")
    for name, lo, hi in BUCKETS:
        m = (gio >= lo) & (gio <= hi)
        print(f"  {name:<16}{m.sum():>6}{llm[m].mean():>10.4f}{llk[m].mean():>10.4f}"
              f"{llm[m].mean()-llk[m].mean():>+10.4f}"
              f"{llm_ou[m].mean():>10.4f}{llk_ou[m].mean():>10.4f}")

    # correlazione log-loss ~ giornata (modello e gap)
    r_llm = float(np.corrcoef(gio, llm)[0, 1])
    r_gap = float(np.corrcoef(gio, llm - llk)[0, 1])
    print(f"\n  corr(giornata, log-loss modello) = {r_llm:+.4f}")
    print(f"  corr(giornata, gap modello-mercato) = {r_gap:+.4f}")

    # Test late (35-38) vs resto: sui TRE livelli
    rng = np.random.default_rng(SEED)
    late = gio >= 35
    rest = ~late
    print(f"\n  Late (giornate 35-38, n={late.sum()}) vs resto (n={rest.sum()}):")
    for label, a_late, a_rest in [
        ("log-loss MODELLO", llm[late], llm[rest]),
        ("log-loss MERCATO", llk[late], llk[rest]),
        ("GAP modello-mercato", (llm - llk)[late], (llm - llk)[rest]),
    ]:
        d, lo, hi = boot_diff(a_late, a_rest, rng)
        star = " *" if (lo > 0 or hi < 0) else ""
        print(f"    {label:<22} Δ(late-resto) {d:+.4f}  CI95 [{lo:+.4f}, {hi:+.4f}]{star}")

    print("\n  Lettura: se MODELLO e MERCATO peggiorano insieme a fine stagione ma il")
    print("  GAP non cambia (CI include 0) -> casualita' irriducibile, non un difetto")
    print("  nostro. Se il GAP cresce (CI>0) -> il mercato prezza la posta in palio e")
    print("  noi no: li' dati sulla motivazione potrebbero aiutare.")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase28_matchday", "league": "serie_a", "variant": "matchday_summary",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(big)),
         "model_ll_late": float(llm[late].mean()), "model_ll_rest": float(llm[rest].mean()),
         "market_ll_late": float(llk[late].mean()), "market_ll_rest": float(llk[rest].mean()),
         "gap_late": float((llm - llk)[late].mean()),
         "gap_rest": float((llm - llk)[rest].mean()),
         "corr_matchday_model_ll": r_llm, "corr_matchday_gap": r_gap}, fp))


if __name__ == "__main__":
    main()
