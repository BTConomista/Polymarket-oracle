"""Fase 82 — VERIFICA DIRETTA delle predizioni: indoviniamo davvero i risultati?

Domanda (utente): finora abbiamo confrontato log-loss contro il mercato; ma i
valori predetti sono GIUSTI in assoluto? Due sensi verificabili:
  1. CALIBRAZIONE — quando il modello dice "60%", l'evento succede davvero il
     ~60% delle volte? (bias globale = p̄−freq; ECE = errore medio di
     calibrazione su 10 fasce di probabilità);
  2. HIT-RATE — quanto spesso l'esito indicato come PIÙ PROBABILE si verifica?
     (confrontato con la baseline "scegli sempre l'esito più frequente" e col
     mercato dove esiste la quota).

Nota di metodo, dichiarata prima: per eventi intrinsecamente incerti il
hit-rate NON può superare di molto la baseline (se il calcio fosse
prevedibile al 90% le quote non esisterebbero); la misura GIUSTA di "essere
nel giusto" per un oracolo di probabilità è la calibrazione. Il hit-rate si
riporta comunque perché è la domanda naturale ("indoviniamo?") e perché
smaschera modelli sbilanciati.

Cosa si verifica, su 6 stagioni di test (2021→2526, n=2280/lega) × 3 leghe:
  - motore market-implied LISCIO (titolare, ρ=−0.06) su ~20 mercati Tier 1
    derivati dalla matrice (1X2, O/U, GG, doppie chance, total-squadra,
    clean sheet, vince-a-zero, scarto≥2, multigol, pari/dispari, ris. esatto);
  - il ROUTER per-lega (θ: SA 1.225, PL 1.0, Liga 1.2 — Fasi 52/81): la θ
    migliora o peggiora la calibrazione?
  - il MERCATO devigato (solo dove c'è la quota: 1X2, O/U 2.5);
  - il path DC senza quote (predizioni dai backtest in cache: 1X2, O/U, GG).

Uso:  python scripts/_run_fase82_verifica_predizioni.py    (~5 min, cache)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import LEAGUE_CONFIGS                # noqa: E402
from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from scripts._run_fase81_mega_sweep_mi import (      # noqa: E402
    SEASONS, _load, _invert_rho)
from scripts.backtest import run_backtest, promoted_teams  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
LEAGUES = ["serie_a", "premier_league", "la_liga"]
RHO = -0.06
THETA_LEGA = {"serie_a": 1.225, "premier_league": None, "la_liga": 1.2}
SEED = 82
NBINS = 10

# mercati binari: chiave derive_markets -> funzione esito reale (hg, ag)
BINARY = {
    "home_win": lambda h, a: h > a,
    "draw": lambda h, a: h == a,
    "away_win": lambda h, a: h < a,
    "dc_1x": lambda h, a: h >= a,
    "dc_2x": lambda h, a: h <= a,
    "dc_12": lambda h, a: h != a,
    "over_1.5": lambda h, a: h + a >= 2,
    "over_2.5": lambda h, a: h + a >= 3,
    "over_3.5": lambda h, a: h + a >= 4,
    "btts": lambda h, a: (h >= 1) and (a >= 1),
    "home_ov_1.5": lambda h, a: h >= 2,
    "away_ov_1.5": lambda h, a: a >= 2,
    "cs_home": lambda h, a: a == 0,
    "cs_away": lambda h, a: h == 0,
    "wtn_home": lambda h, a: (h > a) and (a == 0),
    "wtn_away": lambda h, a: (a > h) and (h == 0),
    "home_by_2plus": lambda h, a: h - a >= 2,
    "away_by_2plus": lambda h, a: a - h >= 2,
    "odd_total": lambda h, a: (h + a) % 2 == 1,
}


def _ece(p: np.ndarray, y: np.ndarray) -> float:
    """Expected Calibration Error su NBINS fasce uguali di probabilita'."""
    edges = np.linspace(0, 1, NBINS + 1)
    ece = 0.0
    for i in range(NBINS):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < NBINS - 1 else p <= 1)
        if m.sum() == 0:
            continue
        ece += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(ece)


def _binary_stats(p, y):
    p = np.asarray(p, float); y = np.asarray(y, float)
    pick = p > 0.5
    hit = float((pick == (y == 1)).mean())
    base_hit = float(max(y.mean(), 1 - y.mean()))
    return {"p_mean": float(p.mean()), "freq": float(y.mean()),
            "bias": float(p.mean() - y.mean()), "ece": _ece(p, y),
            "hit": hit, "hit_base": base_hit}


def _dc_cached(league: str) -> pd.DataFrame | None:
    """Predizioni del DC senza quote dai backtest in cache (F79); per la
    Serie A le stagioni mancanti vengono calcolate (config ufficiale)."""
    frames = []
    for s in SEASONS[1:]:
        fp = (CACHE / f"db79_{league}_base_{s}.csv" if league != "serie_a"
              else CACHE / f"db82_serie_a_base_{s}.csv")
        if fp.exists():
            frames.append(pd.read_csv(fp))
            continue
        if league != "serie_a":
            return None
        cfg = LEAGUE_CONFIGS[league]
        df = run_backtest(league, s, cfg["half_life_days"],
                          shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                          blend_signal=cfg["blend_signal"],
                          promoted_prior=(cfg["promoted_prior"],) * 2,
                          verbose=False)
        df["season"] = s
        df.to_csv(fp, index=False)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _sa_worker(s):
    return _dc_cached_single_sa(s)


def _dc_cached_single_sa(s):
    fp = CACHE / f"db82_serie_a_base_{s}.csv"
    if not fp.exists():
        cfg = LEAGUE_CONFIGS["serie_a"]
        df = run_backtest("serie_a", s, cfg["half_life_days"],
                          shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                          blend_signal=cfg["blend_signal"],
                          promoted_prior=(cfg["promoted_prior"],) * 2,
                          verbose=False)
        df["season"] = s
        df.to_csv(fp, index=False)
    return s


def run_league(league: str) -> None:
    df = _load(league)
    test = np.isin(df.season.values, SEASONS[1:])
    dft = df[test].reset_index(drop=True)
    lam, mu = _invert_rho(df, league, RHO)
    lam, mu = lam[test], mu[test]
    hg = dft.home_goals.astype(int).values
    ag = dft.away_goals.astype(int).values
    n = len(dft)

    # matrici: motore liscio + router per-lega
    theta = THETA_LEGA[league]
    probs = {"engine": {k: np.zeros(n) for k in BINARY},
             "router": {k: np.zeros(n) for k in BINARY}}
    mg_pred_e = np.zeros((n, 3)); topscore = np.zeros((n, 3))
    for k in range(n):
        Me = mi.score_matrix(lam[k], mu[k], RHO)
        Mr = (mi.score_matrix(lam[k], mu[k], RHO, dp_theta=theta)
              if theta else Me)
        de, dr = mi.derive_markets(Me), mi.derive_markets(Mr)
        for mk in BINARY:
            probs["engine"][mk][k] = de[mk]
            probs["router"][mk][k] = dr[mk]
        mg_pred_e[k] = [de["mg_0_1"], de["mg_2_3"], de["mg_4plus"]]
        idx = np.unravel_index(np.argmax(Mr), Mr.shape)
        topscore[k] = [idx[0], idx[1], Mr[idx]]

    # mercato devigato (1X2 + O/U)
    P_mkt = np.array([metrics.devig_1x2(h, d, a) for h, d, a in
                      dft[["odds_home", "odds_draw", "odds_away"]].to_numpy()])
    p_ov_mkt = np.array([metrics.devig_binary(o, u)[0] for o, u in
                         dft[["odds_over25", "odds_under25"]].to_numpy()])

    print("\n" + "=" * 100)
    print(f"FASE 82 — {league.upper()}  (n={n}, 6 stagioni di test)")
    print("=" * 100)
    print(f"  {'mercato':<14}{'p̄ pred':>9}{'freq oss':>10}{'bias':>8}{'ECE':>7}"
          f"{'hit%':>7}{'base%':>7}{'router: bias':>13}{'ECE':>7}")
    summary = {"engine": {}, "router": {}}
    for mk, fn in BINARY.items():
        y = np.array([fn(h, a) for h, a in zip(hg, ag)], float)
        se = _binary_stats(probs["engine"][mk], y)
        sr = _binary_stats(probs["router"][mk], y)
        summary["engine"][mk] = se; summary["router"][mk] = sr
        print(f"  {mk:<14}{se['p_mean']:>9.3f}{se['freq']:>10.3f}"
              f"{se['bias']:>+8.3f}{se['ece']:>7.3f}"
              f"{se['hit']:>7.1%}{se['hit_base']:>7.1%}"
              f"{sr['bias']:>+13.3f}{sr['ece']:>7.3f}")

    # --- 1X2 multiclasse: hit dell'argmax, modello vs mercato vs baseline --- #
    P_eng = np.column_stack([probs["engine"]["home_win"],
                             probs["engine"]["draw"],
                             probs["engine"]["away_win"]])
    P_rout = np.column_stack([probs["router"]["home_win"],
                              probs["router"]["draw"],
                              probs["router"]["away_win"]])
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
    base_cls = np.bincount(y3, minlength=3).argmax()
    x2 = {}
    for name, P in [("engine", P_eng), ("router", P_rout), ("mercato", P_mkt)]:
        pick = P.argmax(1)
        conf = P.max(1)
        x2[name] = {"hit": float((pick == y3).mean()),
                    "conf_media": float(conf.mean()),
                    "ece_argmax": _ece(conf, (pick == y3).astype(float))}
    x2["baseline"] = {"hit": float((y3 == base_cls).mean())}
    print(f"\n  [1X2 argmax]  modello {x2['engine']['hit']:.1%} (conf media "
          f"{x2['engine']['conf_media']:.1%}, ECE argmax {x2['engine']['ece_argmax']:.3f})"
          f"  router {x2['router']['hit']:.1%}  mercato {x2['mercato']['hit']:.1%}"
          f"  baseline(sempre {'1X2'[base_cls]}) {x2['baseline']['hit']:.1%}")

    # O/U 2.5: modello vs mercato
    y_ov = (hg + ag >= 3).astype(float)
    ou_m = _binary_stats(p_ov_mkt, y_ov)
    print(f"  [O/U 2.5 mercato]  bias {ou_m['bias']:+.3f}  ECE {ou_m['ece']:.3f}"
          f"  hit {ou_m['hit']:.1%}  (modello sopra: riga over_2.5)")

    # multigol argmax + risultato esatto (top-pick)
    y_mg = np.where(hg + ag <= 1, 0, np.where(hg + ag <= 3, 1, 2))
    mg_hit = float((mg_pred_e.argmax(1) == y_mg).mean())
    mg_base = float(np.bincount(y_mg, minlength=3).max() / n)
    ts_hit = float(((topscore[:, 0] == hg) & (topscore[:, 1] == ag)).mean())
    ts_conf = float(topscore[:, 2].mean())
    from collections import Counter
    mode_score = Counter(zip(hg, ag)).most_common(1)[0]
    ts_base = mode_score[1] / n
    print(f"  [multigol argmax]  modello {mg_hit:.1%}  baseline {mg_base:.1%}")
    print(f"  [ris. esatto top-pick]  indovinato {ts_hit:.1%} (prob media "
          f"dichiarata {ts_conf:.1%})  baseline(sempre {mode_score[0]}) {ts_base:.1%}")

    # --- path DC senza quote ------------------------------------------------ #
    dc = _dc_cached(league)
    dc_stats = {}
    if dc is not None:
        y3d = np.array([{"H": 0, "D": 1, "A": 2}[r] for r in dc.result])
        Pd = dc[["m_home", "m_draw", "m_away"]].to_numpy()
        dc_stats["x2_hit"] = float((Pd.argmax(1) == y3d).mean())
        for mk, col, yv in [("over_2.5", "m_over", dc.is_over.to_numpy(float)),
                            ("btts", "m_btts", dc.is_btts.to_numpy(float))]:
            dc_stats[mk] = _binary_stats(dc[col].to_numpy(), yv)
        print(f"  [path DC senza quote]  1X2 argmax {dc_stats['x2_hit']:.1%}"
              f"  | O2.5 bias {dc_stats['over_2.5']['bias']:+.3f} ECE "
              f"{dc_stats['over_2.5']['ece']:.3f} hit {dc_stats['over_2.5']['hit']:.1%}"
              f"  | GG bias {dc_stats['btts']['bias']:+.3f} ECE "
              f"{dc_stats['btts']['ece']:.3f} hit {dc_stats['btts']['hit']:.1%}")

    all_m = loader.load_league(league)
    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase82_verifica_predizioni", "league": league,
         "seasons": SEASONS, "rho": RHO, "theta_router": theta},
        {"n": n, "binary_engine": summary["engine"],
         "binary_router": summary["router"], "x2": x2,
         "ou_market": ou_m, "mg_hit": mg_hit, "mg_base": mg_base,
         "topscore_hit": ts_hit, "topscore_conf": ts_conf,
         "topscore_base": ts_base, "dc": dc_stats},
        experiment_log.data_fingerprint(all_m)))


def main() -> None:
    # pre-calcola i 6 backtest DC Serie A mancanti (cache, Pool)
    missing = [s for s in SEASONS[1:]
               if not (CACHE / f"db82_serie_a_base_{s}.csv").exists()]
    if missing:
        print(f"pre-calcolo {len(missing)} backtest DC Serie A (cache)...",
              flush=True)
        with Pool(4) as pool:
            pool.map(_sa_worker, missing)
    for league in LEAGUES:
        run_league(league)
    print("\nRun registrati in experiments/runs.jsonl "
          "(source=fase82_verifica_predizioni).")


if __name__ == "__main__":
    main()
