"""Fase 25 — Sensibilita' alla FINESTRA dei dati: memoria lunga o calcio vecchio?

Il modello gia' scorda il passato in modo MORBIDO (emivita 365g: una partita di
2 stagioni fa pesa <0.25, di 3 fa <0.06). Domanda: tagliare via del tutto le
stagioni vecchie — o la sola stagione COVID a porte chiuse (2020-21, anomala) —
aiuta, o l'emivita basta gia'?

Varianti di TRAINING (config ufficiale invariata: hl365, shr1.5, blend xG 0.75,
prior 0.23):
  - "tutto"          : tutta la storia disponibile (attuale)
  - "finestra 3 stag": solo le partite entro ~1095 giorni prima (taglio netto)
  - "finestra 2 stag": solo entro ~730 giorni
  - "senza COVID"    : esclude la stagione 2020-21 dal training (non dal test)

Per ognuna: log-loss 1X2 e gap vs mercato, pooled sulle 6 stagioni di test e
spezzato in RECENTI-3 (2023-26, "calcio di oggi") vs VECCHIE-3 (2020-23). Cosi'
si vede se restringere ai dati recenti cambia qualcosa, soprattutto sulle
stagioni recenti.

Uso:  python scripts/_run_window.py     (24 backtest; ~alcuni minuti)
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

TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RECENT3 = ["2324", "2425", "2526"]
OLD3 = ["2021", "2122", "2223"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))

# (etichetta, train_window_days, drop_train_seasons)
VARIANTS = [
    ("tutto (attuale)", None, ()),
    ("finestra 3 stag (1095g)", 1095.0, ()),
    ("finestra 2 stag (730g)", 730.0, ()),
    ("senza COVID 2020-21", None, ("2021",)),
]


def _worker(task):
    vi, s = task
    from scripts.backtest import run_backtest
    _, win, drop = VARIANTS[vi]
    df = run_backtest("serie_a", s, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], train_window_days=win,
                      drop_train_seasons=drop, verbose=False)
    m = experiment_log.compute_metrics(df)
    return vi, s, m


def main():
    tasks = [(vi, s) for vi in range(len(VARIANTS)) for s in TEST_SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    M = {(vi, s): m for vi, s, m in res}

    fp = experiment_log.data_fingerprint(loader.load_league("serie_a"))
    for vi, s, m in res:
        label, win, drop = VARIANTS[vi]
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase25_window", "league": "serie_a", "test_season": s,
             "variant": label, "train_window_days": win,
             "drop_train_seasons": list(drop),
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, m, fp))

    def agg(vi, seasons, key):
        return float(np.mean([M[(vi, s)][key] for s in seasons]))

    print("=" * 92)
    print("FINESTRA DEI DATI — log-loss 1X2 e gap vs mercato (config ufficiale)")
    print("gap = modello - mercato; piu' basso = meglio")
    print("=" * 92)
    hdr = (f"  {'variante':<26}{'1X2 tutte':>11}{'gap tutte':>11}"
           f"{'1X2 rec-3':>11}{'gap rec-3':>11}{'1X2 vec-3':>11}{'gap vec-3':>11}")
    print(hdr)
    for vi, (label, _, _) in enumerate(VARIANTS):
        mod_a = agg(vi, TEST_SEASONS, "x2_model_logloss")
        mkt_a = agg(vi, TEST_SEASONS, "x2_market_logloss")
        mod_r = agg(vi, RECENT3, "x2_model_logloss")
        mkt_r = agg(vi, RECENT3, "x2_market_logloss")
        mod_o = agg(vi, OLD3, "x2_model_logloss")
        mkt_o = agg(vi, OLD3, "x2_market_logloss")
        print(f"  {label:<26}{mod_a:>11.4f}{mod_a-mkt_a:>+11.4f}"
              f"{mod_r:>11.4f}{mod_r-mkt_r:>+11.4f}"
              f"{mod_o:>11.4f}{mod_o-mkt_o:>+11.4f}")

    base = VARIANTS[0][0]
    print(f"\n  Riferimento: '{base}'. Δ log-loss vs riferimento (negativo = meglio):")
    for vi, (label, _, _) in enumerate(VARIANTS[1:], start=1):
        d_a = agg(vi, TEST_SEASONS, "x2_model_logloss") - agg(0, TEST_SEASONS, "x2_model_logloss")
        d_r = agg(vi, RECENT3, "x2_model_logloss") - agg(0, RECENT3, "x2_model_logloss")
        print(f"    {label:<26} tutte {d_a:+.4f}   recenti-3 {d_r:+.4f}")

    print("\nLettura: se le finestre corte e il 'senza COVID' danno Δ ~0, l'emivita")
    print("gia' gestisce la recency e tagliare i dati vecchi non serve (ne' danneggia).")


if __name__ == "__main__":
    main()
