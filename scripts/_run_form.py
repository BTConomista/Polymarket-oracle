"""Fase 13 — Stato di forma: pattern nascosto oltre la forza time-weighted?

Due parti:
 (1) DIAGNOSTICO del pattern nascosto: la forma (punti/gara ultime 5) predice
     l'ERRORE del modello attuale? Se le squadre in forma battono sistematicamente
     l'aspettativa del modello, c'e' segnale non catturato dalla forza pesata.
 (2) COVARIATA walk-forward: modello attuale vs +form, 6 stagioni.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import metrics
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))


def _worker(task):
    cov, s = task
    df = run_backtest("serie_a", s, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], covariates=cov, verbose=False)
    df["season"] = s
    return ("form" if cov else "base"), s, df


def main():
    tasks = [(cov, s) for cov in ((), ("form",)) for s in SEASONS]
    with Pool(6) as pool:
        res = pool.map(_worker, tasks)
    P = {(name, s): df for name, s, df in res}

    am = loader.load_league("serie_a")[["date", "home_team", "away_team",
                                        "home_form", "away_form"]]

    # ---------- (1) DIAGNOSTICO: la forma predice l'errore del modello? ----------
    base = pd.concat([P[("base", s)] for s in SEASONS], ignore_index=True)
    base = base.merge(am, on=["date", "home_team", "away_team"], how="left")
    base = base.dropna(subset=["home_form", "away_form"])
    # punti attesi casa dal modello vs punti reali
    exp_home_pts = 3 * base.m_home + 1 * base.m_draw
    real_home_pts = np.where(base.result == "H", 3, np.where(base.result == "D", 1, 0))
    residual = real_home_pts - exp_home_pts          # >0 = casa meglio dell'atteso
    fdiff = base.home_form - base.away_form           # forma casa - ospite
    r_all = np.corrcoef(fdiff, residual)[0, 1]

    print("=" * 78)
    print("(1) DIAGNOSTICO — la FORMA predice l'errore del modello?")
    print("=" * 78)
    print(f"corr(forma_casa - forma_ospite, residuo punti casa) = {r_all:+.4f}")
    print("  (residuo = punti reali casa - attesi dal modello; ~0 = forma gia' catturata)")
    # per terzili di differenza-forma: il modello sotto/sovra-stima la casa in forma?
    q = pd.qcut(fdiff, 3, labels=["ospite in forma", "pari", "casa in forma"])
    print(f"\n  {'gruppo (per diff. forma)':<24}{'n':>7}{'residuo medio':>16}")
    for g in ["ospite in forma", "pari", "casa in forma"]:
        mask = (q == g).to_numpy()
        print(f"  {g:<24}{mask.sum():>7}{residual[mask].mean():>+16.4f}")
    print("  (residuo medio ~0 in ogni gruppo = nessun bias legato alla forma)")

    # ---------- (2) COVARIATA walk-forward ----------
    print("\n" + "=" * 78)
    print("(2) COVARIATA form — 1X2 log-loss walk-forward")
    print("=" * 78)
    print(f"{'stag.':<7}{'base':>10}{'+form':>10}{'Δ':>10}")
    ab = ai = 0.0
    for s in SEASONS:
        b = metrics.log_loss_1x2(P[("base", s)][["m_home", "m_draw", "m_away"]].to_numpy(),
                                 P[("base", s)]["result"].tolist())
        i = metrics.log_loss_1x2(P[("form", s)][["m_home", "m_draw", "m_away"]].to_numpy(),
                                 P[("form", s)]["result"].tolist())
        ab += b; ai += i
        print(f"{s:<7}{b:>10.4f}{i:>10.4f}{i-b:>+10.4f}")
    n = len(SEASONS)
    print("-" * 37)
    print(f"{'MEDIA':<7}{ab/n:>10.4f}{ai/n:>10.4f}{(ai-ab)/n:>+10.4f}")
    print("\nΔ < 0 = la forma come covariata migliora.")


if __name__ == "__main__":
    main()
