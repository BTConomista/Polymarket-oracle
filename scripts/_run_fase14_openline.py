"""Fase 14 — Il modello batte la linea di APERTURA? (test Closing Line Value)

Finora ogni confronto era contro le quote di CHIUSURA: lo stimatore piu'
efficiente che esista, l'avversario piu' duro. Ma nessuno e' costretto a
scommettere alla chiusura: si puo' prendere il prezzo PRIMA, quando la linea
ha ancora dentro meno informazione. Domanda della fase: il nostro modello e'
piu' accurato della linea PRE-chiusura ("apertura")? Se si', esiste un edge
*tradeable* anche senza battere la chiusura — e il test CLV (la chiusura si
muove verso di noi?) e' il criterio che i professionisti usano per distinguere
edge da fortuna.

Disegno: le predizioni del modello NON dipendono dalla quota, quindi si
riusano le 5 versioni x 6 stagioni di analyze_gap e si cambia solo il
benchmark. Confronto SEMPRE sulle stesse righe (quote di apertura E chiusura
entrambe presenti), altrimenti i log-loss non sono comparabili.

Onesta' sui dati: la "apertura" football-data (colonne senza suffisso C) e'
raccolta ~1-3 giorni prima della partita, non e' l'apertura vera del mercato;
e il ROI value-bet resta illustrativo (media di ~17 book, niente limiti/liquidita').

Uso:  python scripts/_run_fase14_openline.py     (30 backtest; alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log
from scripts.analyze_gap import SEASONS, VERSIONS, _worker

# Righe comparabili: TUTTE le quote 1X2 (apertura e chiusura) presenti.
_JOINT_1X2 = ["odds_home", "odds_draw", "odds_away",
              "odds_home_open", "odds_draw_open", "odds_away_open"]
_JOINT_OU = ["odds_over", "odds_under", "odds_over_open", "odds_under_open"]


def _joint(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    ok = np.isfinite(df[cols].to_numpy(dtype=float)).all(axis=1)
    return df[ok].reset_index(drop=True)


def main() -> None:
    snap_cols = loader.load_league("serie_a").columns
    if "odds_home_open" not in snap_cols:
        raise SystemExit(
            "Lo snapshot non ha le colonne *_open: eseguire prima "
            "`python scripts/build_database.py --open-odds`.")

    tasks = [(vi, s, cfg) for vi, (_, cfg) in enumerate(VERSIONS) for s in SEASONS]
    print(f"Eseguo {len(tasks)} backtest (5 versioni x 6 stagioni)...", flush=True)
    with Pool(6) as pool:
        results = pool.map(_worker, tasks)

    dfs: dict[int, dict[str, pd.DataFrame]] = {vi: {} for vi in range(len(VERSIONS))}
    for vi, s, df in results:
        dfs[vi][s] = df

    # Registro: un run per cella, replicabile (metriche sul df completo,
    # con le nuove chiavi *open* calcolate da compute_metrics).
    all_matches = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_matches)
    for vi, (label, cfg) in enumerate(VERSIONS):
        for s in SEASONS:
            config = {"source": "fase14_openline", "version": label,
                      "test_season": s, **cfg,
                      "promoted_prior": (cfg["promoted_prior"][0]
                                         if cfg["promoted_prior"] else None)}
            rec = experiment_log.make_record(
                config, experiment_log.compute_metrics(dfs[vi][s]), fp)
            experiment_log.append_run(rec)
    print(f"Registrati {len(tasks)} run in experiments/runs.jsonl "
          f"(source=fase14_openline, dati {fp})")

    cur = len(VERSIONS) - 1

    # Copertura del confronto (righe con entrambe le linee).
    n_tot = sum(len(dfs[cur][s]) for s in SEASONS)
    n_joint = sum(len(_joint(dfs[cur][s], _JOINT_1X2)) for s in SEASONS)
    print(f"\nRighe comparabili 1X2 (apertura E chiusura presenti): "
          f"{n_joint}/{n_tot}")

    # ============ A. Gap 1X2 per versione: APERTURA vs CHIUSURA ============
    print("\n" + "=" * 92)
    print("A. GAP 1X2 (model_ll - market_ll) per versione — vs APERTURA e vs CHIUSURA")
    print("   (>0 = mercato meglio; <0 = MODELLO MEGLIO. Stesse righe per entrambe le linee.)")
    print("=" * 92)
    print(f"{'versione':<44}{'gap vs APERTURA':>17}{'gap vs CHIUSURA':>17}{'diff.':>9}")
    for vi, (label, _) in enumerate(VERSIONS):
        go, gc = [], []
        for s in SEASONS:
            sub = _joint(dfs[vi][s], _JOINT_1X2)
            m = experiment_log.compute_metrics(sub)
            go.append(m["x2_model_logloss"] - m["x2_market_open_logloss"])
            gc.append(m["x2_model_logloss"] - m["x2_market_logloss"])
        print(f"{label:<44}{np.mean(go):>+17.4f}{np.mean(gc):>+17.4f}"
              f"{np.mean(go) - np.mean(gc):>+9.4f}")

    # ============ B. Versione ATTUALE, per stagione ============
    print("\n" + "=" * 92)
    print("B. Versione ATTUALE per STAGIONE (1X2 log-loss, righe comparabili)")
    print("=" * 92)
    print(f"{'stagione':<10}{'modello':>9}{'apertura':>9}{'chiusura':>9}"
          f"{'gap vs open':>12}{'gap vs close':>13}{'open-close':>11}")
    rows = []
    for s in SEASONS:
        sub = _joint(dfs[cur][s], _JOINT_1X2)
        m = experiment_log.compute_metrics(sub)
        rows.append((m["x2_model_logloss"], m["x2_market_open_logloss"],
                     m["x2_market_logloss"]))
        mo, op, cl = rows[-1]
        print(f"{s:<10}{mo:>9.4f}{op:>9.4f}{cl:>9.4f}"
              f"{mo - op:>+12.4f}{mo - cl:>+13.4f}{op - cl:>+11.4f}")
    a = np.array(rows)
    print(f"{'MEDIA':<10}{a[:,0].mean():>9.4f}{a[:,1].mean():>9.4f}{a[:,2].mean():>9.4f}"
          f"{(a[:,0]-a[:,1]).mean():>+12.4f}{(a[:,0]-a[:,2]).mean():>+13.4f}"
          f"{(a[:,1]-a[:,2]).mean():>+11.4f}")
    print("  (open-close = quanto la linea si affila tra apertura e chiusura:")
    print("   e' l'informazione che arriva al mercato nelle ultime ore.)")

    # ============ C. Over/Under 2.5 ============
    print("\n" + "=" * 92)
    print("C. Versione ATTUALE — Over/Under 2.5 (log-loss, righe comparabili)")
    print("=" * 92)
    print(f"{'stagione':<10}{'modello':>9}{'apertura':>9}{'chiusura':>9}"
          f"{'gap vs open':>12}{'gap vs close':>13}")
    rows = []
    for s in SEASONS:
        sub = _joint(dfs[cur][s], _JOINT_OU)
        m = experiment_log.compute_metrics(sub)
        rows.append((m["ou_model_logloss"], m["ou_market_open_logloss"],
                     m["ou_market_logloss"]))
        mo, op, cl = rows[-1]
        print(f"{s:<10}{mo:>9.4f}{op:>9.4f}{cl:>9.4f}{mo-op:>+12.4f}{mo-cl:>+13.4f}")
    a = np.array(rows)
    print(f"{'MEDIA':<10}{a[:,0].mean():>9.4f}{a[:,1].mean():>9.4f}{a[:,2].mean():>9.4f}"
          f"{(a[:,0]-a[:,1]).mean():>+12.4f}{(a[:,0]-a[:,2]).mean():>+13.4f}")

    # ============ D. Value bet all'APERTURA + CLV (versione ATTUALE) ============
    print("\n" + "=" * 92)
    print("D. VALUE BET alla linea di APERTURA + CLV (versione ATTUALE; illustrativo)")
    print("   CLV = prob_chiusura - prob_apertura sulla selezione: >0 = la chiusura")
    print("   si e' mossa VERSO il modello (il criterio dei professionisti).")
    print("=" * 92)
    print(f"{'stagione':<10}{'bet@open':>9}{'ROI@open':>10}{'bet@close':>10}"
          f"{'ROI@close':>10}{'CLV medio':>11}{'CLV>0':>8}")
    pool_df = []
    for s in SEASONS:
        sub = _joint(dfs[cur][s], _JOINT_1X2)
        pool_df.append(sub)
        n_o, roi_o = experiment_log.value_bet_roi(
            sub, odds_cols=experiment_log._ODDS_1X2_OPEN)
        n_c, roi_c = experiment_log.value_bet_roi(sub)
        _, clv_m, clv_p = experiment_log.clv_stats(sub)
        print(f"{s:<10}{n_o:>9}{roi_o:>+9.1f}%{n_c:>10}{roi_c:>+9.1f}%"
              f"{clv_m:>+11.4f}{clv_p:>7.0%}")
    allj = pd.concat(pool_df, ignore_index=True)
    n_o, roi_o = experiment_log.value_bet_roi(
        allj, odds_cols=experiment_log._ODDS_1X2_OPEN)
    n_c, roi_c = experiment_log.value_bet_roi(allj)
    clv_n, clv_m, clv_p = experiment_log.clv_stats(allj)
    print(f"{'POOL':<10}{n_o:>9}{roi_o:>+9.1f}%{n_c:>10}{roi_c:>+9.1f}%"
          f"{clv_m:>+11.4f}{clv_p:>7.0%}")
    print(f"\n  Selezioni CLV valutate: {clv_n}. ROI illustrativo (media ~17 book,"
          f" niente limiti/liquidita');")
    print("  il CLV e' il segnale robusto: ROI positivo con CLV<=0 e' fortuna, non edge.")


if __name__ == "__main__":
    main()
