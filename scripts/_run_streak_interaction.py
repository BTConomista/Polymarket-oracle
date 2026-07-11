"""Fase 13-quater — Interazione STREAK x favorevolezza del match.

Ipotesi dell'utente: una squadra su una buona striscia CONTRO un avversario debole
sposta l'esito (verso 1/X) oltre quanto gia' fa il modello. Si testa se il
termine d'INTERAZIONE (streak x favoritismo) predice il residuo del modello oltre
gli effetti principali. La "debolezza avversario / favorevolezza" = favoritismo
del modello (P(casa)-P(ospite)), out-of-sample. Solo Serie A.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from scripts._run_streaks import compute_streaks

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))


def _worker(s):
    from scripts.backtest import run_backtest
    return run_backtest("serie_a", s, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                        shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                        promoted_prior=CFG["promoted_prior"], verbose=False)


def r2(y, X):
    Xd = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    yhat = Xd @ beta
    return 1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2), beta


def main():
    with Pool(6) as pool:
        pred = pd.concat(pool.map(_worker, SEASONS), ignore_index=True)
    streaks = compute_streaks(loader.load_league("serie_a"))
    d = pred.merge(streaks, on=["date", "home_team", "away_team"], how="left")

    exp_home = 3 * d.m_home + 1 * d.m_draw
    resid = (np.where(d.result == "H", 3, np.where(d.result == "D", 1, 0)) - exp_home).to_numpy()

    streak = ((d.h_unb - d.h_los) - (d.a_unb - d.a_los)).to_numpy(float)  # momentum casa-osp
    fav = (d.m_home - d.m_away).to_numpy()                                # favoritismo casa
    inter = (streak - streak.mean()) * (fav - fav.mean())                # interazione centrata

    print("=" * 74)
    print("STREAK x FAVOREVOLEZZA — l'interazione predice l'errore del modello?")
    print("=" * 74)
    print(f"  corr(streak, residuo)         = {np.corrcoef(streak, resid)[0,1]:+.4f}")
    print(f"  corr(favoritismo, residuo)    = {np.corrcoef(fav, resid)[0,1]:+.4f}")
    print(f"  corr(INTERAZIONE, residuo)    = {np.corrcoef(inter, resid)[0,1]:+.4f}")
    se = 1.0 / np.sqrt(len(resid))
    print(f"  (soglia rumore 2*SE ~ {2*se:.3f})\n")

    r2_main, _ = r2(resid, np.column_stack([streak, fav]))
    r2_full, beta = r2(resid, np.column_stack([streak, fav, inter]))
    print(f"  R^2 solo effetti principali (streak + fav) = {r2_main:.4f}")
    print(f"  R^2 con INTERAZIONE aggiunta               = {r2_full:.4f}")
    print(f"  guadagno di R^2 dall'interazione           = {r2_full-r2_main:+.5f}")
    print(f"  (1 feature in piu' da sola darebbe ~{1/len(resid):.5f} per puro rumore)")

    # Griglia 2x2 leggibile: casa in serie utile? x casa favorita?
    print("\n  Griglia — residuo medio (punti reali casa - attesi):")
    on_streak = (d.h_unb >= 5).to_numpy()      # su buona serie utile (>=5)
    favored = fav > 0.2                        # match favorevole per la casa
    print(f"  {'':<22}{'avversario NON debole':>22}{'avversario debole':>20}")
    for sname, sm in [("casa in serie (>=5)", on_streak), ("casa senza serie", ~on_streak)]:
        cells = []
        for fm in (~favored, favored):
            m = sm & fm
            cells.append(f"{resid[m].mean():+.4f} (n={m.sum()})" if m.sum() else "-")
        print(f"  {sname:<22}{cells[0]:>22}{cells[1]:>20}")
    print("\n  Se l'interazione fosse reale, la cella 'in serie & avversario debole'")
    print("  avrebbe residuo POSITIVO e distinto dalle altre. ~0 ovunque = niente.")


if __name__ == "__main__":
    main()
