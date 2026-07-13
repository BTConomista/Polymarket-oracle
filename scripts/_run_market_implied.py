"""Fase 26 — Market-implied esteso a TUTTI i mercati sui gol (molte strade).

Estende la Fase 24 (GG/NG dai lambda,mu del mercato) a ogni mercato basato sui
gol, e prova piu' strade. Per ogni mercato DERIVATO (che il book non prezza)
confronta:  market-implied  vs  DC-da-gol  vs  baseline.

Strade testate:
  1. MERCATI: O/U 0.5/1.5/2.5/3.5/4.5, GG/NG, 1X2, multigol (0-1/2-3/4+),
     total-squadra (casa/ospite Over 0.5/1.5), pari/dispari, scarto >=2,
     e il RISULTATO ESATTO (log-loss sull'intera matrice);
  2. RHO della correzione DC: 0 / -0.03 / -0.06 / -0.10;
  3. TARGET d'inversione: 1X2+O/U vs solo-1X2 (quanto aggiunge l'O/U?);
  4. BLEND: lambda,mu del mercato vs media col lambda,mu del nostro DC.

Onesta': 1X2 e O/U 2.5 sono gli ANCORAGGI dell'inversione -> riproducono il
mercato (controllo di sanita', non 'valore'). Il valore e' nei mercati derivati
NON prezzati; non e' verificabile contro un'ipotetica linea di chiusura di quei
mercati (assente nei dati). Walk-forward per stagione, bootstrap appaiato.

Uso:  python scripts/_run_market_implied.py     (6 backtest + inversioni; minuti)
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
from src.models import market_implied as mi

TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
RHO_MAIN = -0.06
B, SEED = 10_000, 26
MAXG = mi.MAX_GOALS


def _worker(season):
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df


# --- mercati BINARI: nome -> esito(hg,ag)->0/1 (la prob e' derive_markets[nome]) ---
def _binary_outcomes(hg, ag):
    tot = hg + ag
    return {
        "over_0.5": tot >= 1, "over_1.5": tot >= 2, "over_2.5": tot >= 3,
        "over_3.5": tot >= 4, "over_4.5": tot >= 5,
        "btts": (hg >= 1) & (ag >= 1),
        "home_ov_0.5": hg >= 1, "home_ov_1.5": hg >= 2,
        "away_ov_0.5": ag >= 1, "away_ov_1.5": ag >= 2,
        "odd_total": (tot % 2) == 1,
        "home_by_2plus": (hg - ag) >= 2, "away_by_2plus": (ag - hg) >= 2,
    }


BINARY = list(_binary_outcomes(0, 0).keys())


def ll_bin(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()


def invert_all(dfs, targets_over, rho):
    """Per ogni partita di ogni stagione, inverte il mercato -> lambda,mu e deriva
    tutti i mercati. Ritorna dict stagione -> lista di dict derive_markets, piu'
    i lambda,mu impliciti."""
    out = {}
    for s in TEST_SEASONS:
        rows = []
        for r in dfs[s].itertuples():
            pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            pOver = None
            if targets_over:
                pOver, _ = metrics.devig_binary(r.odds_over, r.odds_under)
            lam, mu = mi.implied_lambda_mu(pH, pD, pA, pOver, rho)
            rows.append((lam, mu))
        out[s] = rows
    return out


def dc_lambda_mu(dfs):
    return {s: list(zip(dfs[s]["exp_home_goals"], dfs[s]["exp_away_goals"]))
            for s in TEST_SEASONS}


def eval_markets(lm_by_season, dfs, rho):
    """Da (lambda,mu) per partita -> log-loss per-riga pooled di ogni mercato
    (binari + multigol + risultato esatto)."""
    binll = {mk: [] for mk in BINARY}
    mgll, exll = [], []          # multigol (3-classi), risultato esatto
    for s in TEST_SEASONS:
        hg = dfs[s]["home_goals"].to_numpy(); ag = dfs[s]["away_goals"].to_numpy()
        outc = _binary_outcomes(hg, ag)
        mats = [mi.score_matrix(lam, mu, rho) for lam, mu in lm_by_season[s]]
        der = [mi.derive_markets(M) for M in mats]
        for mk in BINARY:
            p = np.array([d[mk] for d in der])
            binll[mk].append(ll_bin(p, outc[mk].astype(float)))
        # multigol 3-classi
        Pmg = np.array([[d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]] for d in der])
        tot = hg + ag
        ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
        mgll.append(-np.log(np.clip(Pmg[np.arange(len(ymg)), ymg], 1e-15, 1)))
        # risultato esatto: -log M[min(hg,MAX), min(ag,MAX)]
        hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
        exll.append(np.array([-np.log(max(mats[k][hc[k], ac[k]], 1e-15))
                              for k in range(len(hg))]))
    res = {mk: np.concatenate(v) for mk, v in binll.items()}
    res["multigol"] = np.concatenate(mgll)
    res["risultato_esatto"] = np.concatenate(exll)
    return res


def baseline_ll(dfs):
    """Baseline in-sample per ogni mercato (frequenza dell'esito nella stagione)."""
    binll = {mk: [] for mk in BINARY}
    mgll, exll = [], []
    for s in TEST_SEASONS:
        hg = dfs[s]["home_goals"].to_numpy(); ag = dfs[s]["away_goals"].to_numpy()
        outc = _binary_outcomes(hg, ag)
        for mk in BINARY:
            y = outc[mk].astype(float)
            binll[mk].append(ll_bin(np.full(len(y), y.mean()), y))
        tot = hg + ag
        ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
        fr = np.array([(ymg == c).mean() for c in (0, 1, 2)])
        mgll.append(-np.log(np.clip(fr[ymg], 1e-15, 1)))
        # risultato esatto: distribuzione empirica dei punteggi (in-sample)
        hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
        freq = np.zeros((MAXG + 1, MAXG + 1))
        for a, b in zip(hc, ac):
            freq[a, b] += 1
        freq /= freq.sum()
        exll.append(np.array([-np.log(max(freq[hc[k], ac[k]], 1e-15))
                              for k in range(len(hg))]))
    res = {mk: np.concatenate(v) for mk, v in binll.items()}
    res["multigol"] = np.concatenate(mgll)
    res["risultato_esatto"] = np.concatenate(exll)
    return res


def main():
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, TEST_SEASONS))
    all_m = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_m)
    for s, df in dfs.items():
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase26_market_implied", "league": "serie_a",
             "test_season": s, "variant": "dc_features",
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, experiment_log.compute_metrics(df), fp))

    ALL_MK = ["1X2_note"] + BINARY + ["multigol", "risultato_esatto"]
    rng = np.random.default_rng(SEED)

    # Inversioni: main (1X2+OU, rho principale), DC-da-gol.
    lm_mkt = invert_all(dfs, targets_over=True, rho=RHO_MAIN)
    lm_dc = dc_lambda_mu(dfs)
    ev_mkt = eval_markets(lm_mkt, dfs, RHO_MAIN)
    ev_dc = eval_markets(lm_dc, dfs, RHO_MAIN)
    ev_base = baseline_ll(dfs)

    ANCHORS = {"over_2.5"}   # ancoraggi dell'inversione (riproducono il mercato)
    print("=" * 100)
    print(f"MARKET-IMPLIED — tutti i mercati sui gol (inversione 1X2+O/U, rho={RHO_MAIN})")
    print("log-loss; Δ = market-implied - DC-da-gol (<0 = il mercato aiuta); * = mercato NON prezzato")
    print("=" * 100)
    print(f"  {'mercato':<18}{'mkt-impl':>10}{'DC-gol':>10}{'baseline':>10}"
          f"{'Δ vs DC':>10}{'CI95 Δ':>20}{'P<0':>7}")
    summary = {}
    for mk in BINARY + ["multigol", "risultato_esatto"]:
        g, dc, bl = ev_mkt[mk], ev_dc[mk], ev_base[mk]
        d = g - dc
        mean, lo, hi, pneg = boot(d, rng)
        star = "" if mk in ANCHORS else " *"
        print(f"  {mk+star:<18}{g.mean():>10.4f}{dc.mean():>10.4f}{bl.mean():>10.4f}"
              f"{mean:>+10.4f}   [{lo:+.4f}, {hi:+.4f}]{pneg:>7.1%}")
        summary[mk] = (g.mean(), dc.mean(), bl.mean(), mean, lo, hi, pneg)

    # riepilogo: su quanti mercati NON-ancora il market-implied batte DC e baseline
    nonanchor = [mk for mk in BINARY + ["multigol", "risultato_esatto"] if mk not in ANCHORS]
    beat_dc = sum(1 for mk in nonanchor if summary[mk][3] < 0)
    beat_dc_sig = sum(1 for mk in nonanchor if summary[mk][5] < 0)
    beat_base = sum(1 for mk in nonanchor if summary[mk][0] < summary[mk][2])
    print(f"\n  Su {len(nonanchor)} mercati non-ancora: market-implied batte il DC-da-gol "
          f"in {beat_dc} (CI<0 in {beat_dc_sig}); batte la baseline in {beat_base}.")

    # --- STRADA 2: rho ---
    print("\n" + "=" * 100)
    print("STRADA rho — log-loss di alcuni mercati al variare di rho (inversione 1X2+O/U)")
    print("=" * 100)
    reps = ["risultato_esatto", "over_1.5", "btts", "multigol"]
    RHOS = (0.0, -0.03, -0.06, -0.10)
    print(f"  {'mercato':<18}" + "".join(f"rho={r:>+.2f}".rjust(12) for r in RHOS))
    rho_cache = {}
    for rho in RHOS:
        ev = eval_markets(invert_all(dfs, targets_over=True, rho=rho), dfs, rho)
        rho_cache[rho] = {mk: ev[mk].mean() for mk in reps}
    for mk in reps:
        print(f"  {mk:<18}" + "".join(f"{rho_cache[r][mk]:>12.4f}" for r in RHOS))

    # --- STRADA 3: target d'inversione (1X2+O/U vs solo 1X2) ---
    print("\n" + "=" * 100)
    print(f"STRADA target — 1X2+O/U vs solo-1X2 (rho={RHO_MAIN}); Δ = solo1X2 - conOU")
    print("=" * 100)
    lm_1x2 = invert_all(dfs, targets_over=False, rho=RHO_MAIN)
    ev_1x2 = eval_markets(lm_1x2, dfs, RHO_MAIN)
    print(f"  {'mercato':<18}{'con O/U':>12}{'solo 1X2':>12}{'Δ':>10}")
    for mk in reps:
        print(f"  {mk:<18}{ev_mkt[mk].mean():>12.4f}{ev_1x2[mk].mean():>12.4f}"
              f"{ev_1x2[mk].mean()-ev_mkt[mk].mean():>+10.4f}")

    # --- STRADA 4: blend lambda,mu mercato + DC ---
    print("\n" + "=" * 100)
    print(f"STRADA blend — lambda,mu del mercato vs media(mercato, DC) (rho={RHO_MAIN})")
    print("=" * 100)
    lm_blend = {s: [((lm_mkt[s][k][0] + lm_dc[s][k][0]) / 2,
                     (lm_mkt[s][k][1] + lm_dc[s][k][1]) / 2)
                    for k in range(len(lm_mkt[s]))] for s in TEST_SEASONS}
    ev_blend = eval_markets(lm_blend, dfs, RHO_MAIN)
    print(f"  {'mercato':<18}{'mercato':>12}{'blend':>12}{'Δ':>10}")
    for mk in reps:
        print(f"  {mk:<18}{ev_mkt[mk].mean():>12.4f}{ev_blend[mk].mean():>12.4f}"
              f"{ev_blend[mk].mean()-ev_mkt[mk].mean():>+10.4f}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase26_market_implied", "league": "serie_a",
         "variant": "sweep_summary", "rho": RHO_MAIN, "bootstrap_B": B,
         "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(sum(len(ev_mkt[BINARY[0]]) for _ in [0])),
         "beat_dc_count": beat_dc, "beat_dc_sig_count": beat_dc_sig,
         "beat_baseline_count": beat_base, "n_nonanchor": len(nonanchor),
         **{f"mktimpl_{mk}": float(summary[mk][0]) for mk in nonanchor},
         **{f"dcgol_{mk}": float(summary[mk][1]) for mk in nonanchor},
         **{f"delta_{mk}": float(summary[mk][3]) for mk in nonanchor}}, fp))

    print("\nNota: over_2.5 e 1X2 sono ancoraggi (riproducono il mercato). Il valore")
    print("e' nei mercati NON prezzati (con *); non verificabile vs una linea di")
    print("chiusura di quei mercati (assente nei dati).")


if __name__ == "__main__":
    main()
