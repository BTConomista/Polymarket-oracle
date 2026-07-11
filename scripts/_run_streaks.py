"""Fase 13-bis — STREAK (serie aperte) invece della media-ultime-5.

Idea dell'utente: non una finestra fissa arbitraria, ma la lunghezza delle serie
in corso (es. 12 risultati utili di fila, 5 sconfitte di fila). Cattura effetti
di soglia/psicologici (regressione alla media dopo lunghe serie, crisi/fiducia)
che una media mobile appiattisce.

Diagnostico (gate, solo Serie A: i risultati che abbiamo): le streak predicono
l'ERRORE del modello? In particolare le squadre su lunghe serie REGREDISCONO
(residuo<0) o quelle su serie negative RIMBALZANO (residuo>0)?
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))


def compute_streaks(matches: pd.DataFrame) -> pd.DataFrame:
    """Per ogni partita, le streak di ciascuna squadra ENTRANDO nella gara
    (no look-ahead): serie utile (non-sconfitte), serie di sconfitte, di vittorie."""
    df = matches.sort_values("date").reset_index(drop=True)
    unb = {}; los = {}; win = {}  # stato corrente per squadra
    cols = {k: [] for k in ("h_unb", "a_unb", "h_los", "a_los", "h_win", "a_win")}
    for _, r in df.iterrows():
        h, a = r["home_team"], r["away_team"]
        cols["h_unb"].append(unb.get(h, 0)); cols["a_unb"].append(unb.get(a, 0))
        cols["h_los"].append(los.get(h, 0)); cols["a_los"].append(los.get(a, 0))
        cols["h_win"].append(win.get(h, 0)); cols["a_win"].append(win.get(a, 0))
        hg, ag = r["home_goals"], r["away_goals"]
        if hg > ag:  # casa vince
            unb[h] = unb.get(h, 0) + 1; win[h] = win.get(h, 0) + 1; los[h] = 0
            unb[a] = 0; win[a] = 0; los[a] = los.get(a, 0) + 1
        elif hg < ag:  # ospite vince
            unb[a] = unb.get(a, 0) + 1; win[a] = win.get(a, 0) + 1; los[a] = 0
            unb[h] = 0; win[h] = 0; los[h] = los.get(h, 0) + 1
        else:  # pari: serie utile continua, vittorie azzerate, sconfitte azzerate
            unb[h] = unb.get(h, 0) + 1; unb[a] = unb.get(a, 0) + 1
            win[h] = win[a] = 0; los[h] = los[a] = 0
    for k, v in cols.items():
        df[k] = v
    return df[["date", "home_team", "away_team"] + list(cols)]


def _worker(s):
    df = run_backtest("serie_a", s, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    return df


def main():
    with Pool(6) as pool:
        dfs = pool.map(_worker, SEASONS)
    pred = pd.concat(dfs, ignore_index=True)

    am = loader.load_league("serie_a")
    streaks = compute_streaks(am)
    d = pred.merge(streaks, on=["date", "home_team", "away_team"], how="left")

    exp_home = 3 * d.m_home + 1 * d.m_draw
    real_home = np.where(d.result == "H", 3, np.where(d.result == "D", 1, 0))
    resid = real_home - exp_home                       # >0 = casa meglio dell'atteso

    print("=" * 76)
    print("STREAK (Serie A) — predicono l'ERRORE del modello? (residuo punti casa)")
    print("=" * 76)
    for name, x in [("serie utile (casa-osp)", d.h_unb - d.a_unb),
                    ("serie sconfitte (casa-osp)", d.h_los - d.a_los),
                    ("serie vittorie (casa-osp)", d.h_win - d.a_win)]:
        print(f"  corr({name:<26}, residuo) = {np.corrcoef(x, resid)[0,1]:+.4f}")

    print("\n--- REGRESSIONE ALLA MEDIA: residuo per lunghezza serie UTILE (casa) ---")
    for lo, hi, lab in [(0, 3, "0-2"), (3, 6, "3-5"), (6, 10, "6-9"),
                        (10, 15, "10-14"), (15, 99, "15+")]:
        m = ((d.h_unb >= lo) & (d.h_unb < hi)).to_numpy()
        if m.sum():
            print(f"  serie utile {lab:<6} (n={m.sum():>4}):  residuo medio {resid[m].mean():+.4f}")
    print("  (residuo<0 su serie lunghe = il modello SOVRASTIMA -> pattern sfruttabile)")

    print("\n--- RIMBALZO: residuo per lunghezza serie di SCONFITTE (casa) ---")
    for lo, hi, lab in [(0, 1, "0"), (1, 2, "1"), (2, 3, "2"), (3, 5, "3-4"), (5, 99, "5+")]:
        m = ((d.h_los >= lo) & (d.h_los < hi)).to_numpy()
        if m.sum():
            print(f"  sconfitte {lab:<5} (n={m.sum():>4}):  residuo medio {resid[m].mean():+.4f}")
    print("  (residuo>0 su serie negative = il modello SOTTOSTIMA -> rimbalzo sfruttabile)")
    print(f"\n  serie utile max osservata: {int(d.h_unb.max())}; sconfitte max: {int(d.h_los.max())}")


if __name__ == "__main__":
    main()
