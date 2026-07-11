"""Fase 13-ter — Ricerca DATA-DRIVEN di pattern nel rendimento recente.

Invece di scegliere soglie/finestre arbitrarie, si testa un ampio ventaglio di
segnali di rendimento recente (risultati, GOL fatti/subiti, xG, "fortuna"=gol-xG,
serie aperte) su piu' finestre, e si misura se PREDICONO l'errore del modello.

Verdetto in un numero: R^2 = frazione della varianza del residuo del modello
spiegata dal rendimento recente. ~0 (vicino al rumore n_feature/N) = nessun
pattern nascosto. Solo Serie A (i risultati che abbiamo), no look-ahead.
"""
from __future__ import annotations

import sys
from collections import deque
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
WINDOWS = [3, 5, 10]


def recent_features(matches: pd.DataFrame) -> pd.DataFrame:
    """Feature di rendimento recente per squadra, entrando in ogni gara."""
    df = matches.sort_values("date").reset_index(drop=True)
    hist: dict[str, dict] = {}   # team -> deque per gf,ga,xgf,xga,pts

    def st(team):
        return hist.setdefault(team, {
            "gf": deque(maxlen=10), "ga": deque(maxlen=10),
            "xgf": deque(maxlen=10), "xga": deque(maxlen=10),
            "pts": deque(maxlen=10), "unb": 0, "los": 0})

    feats = {f"{side}_{k}{w}": [] for side in ("h", "a")
             for k in ("gf", "ga", "gd", "xgf", "xga", "luck", "pts") for w in WINDOWS}
    feats.update({f"{side}_{k}": [] for side in ("h", "a") for k in ("unb", "los")})

    def snap(team, side):
        s = st(team)
        for w in WINDOWS:
            def mean(dq): return np.mean(list(dq)[-w:]) if len(dq) else np.nan
            feats[f"{side}_gf{w}"].append(mean(s["gf"]))
            feats[f"{side}_ga{w}"].append(mean(s["ga"]))
            feats[f"{side}_gd{w}"].append((mean(s["gf"]) - mean(s["ga"])))
            feats[f"{side}_xgf{w}"].append(mean(s["xgf"]))
            feats[f"{side}_xga{w}"].append(mean(s["xga"]))
            g_ = list(s["gf"])[-w:]; xg_ = list(s["xgf"])[-w:]
            feats[f"{side}_luck{w}"].append(np.mean(np.array(g_) - np.array(xg_)) if g_ else np.nan)
            feats[f"{side}_pts{w}"].append(mean(s["pts"]))
        feats[f"{side}_unb"].append(s["unb"]); feats[f"{side}_los"].append(s["los"])

    for _, r in df.iterrows():
        snap(r["home_team"], "h"); snap(r["away_team"], "a")
        hg, ag = r["home_goals"], r["away_goals"]
        hx, ax = r.get("home_xg", np.nan), r.get("away_xg", np.nan)
        for team, gf, ga, xf, xa, res in ((r["home_team"], hg, ag, hx, ax, np.sign(hg - ag)),
                                          (r["away_team"], ag, hg, ax, hx, np.sign(ag - hg))):
            s = st(team)
            s["gf"].append(gf); s["ga"].append(ga); s["xgf"].append(xf); s["xga"].append(xa)
            s["pts"].append(3 if res > 0 else (1 if res == 0 else 0))
            s["unb"] = s["unb"] + 1 if res >= 0 else 0
            s["los"] = s["los"] + 1 if res < 0 else 0
    out = pd.DataFrame(feats)
    out[["date", "home_team", "away_team"]] = df[["date", "home_team", "away_team"]].values
    return out


def _worker(s):
    return run_backtest("serie_a", s, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                        shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                        promoted_prior=CFG["promoted_prior"], verbose=False)


def main():
    with Pool(6) as pool:
        pred = pd.concat(pool.map(_worker, SEASONS), ignore_index=True)
    am = loader.load_league("serie_a")
    feats = recent_features(am)
    d = pred.merge(feats, on=["date", "home_team", "away_team"], how="left")

    exp_home = 3 * d.m_home + 1 * d.m_draw
    resid = (np.where(d.result == "H", 3, np.where(d.result == "D", 1, 0)) - exp_home).to_numpy()

    # Differenziali casa-ospite per ogni feature.
    keys = [f"{k}{w}" for k in ("gf", "ga", "gd", "xgf", "xga", "luck", "pts") for w in WINDOWS] \
        + ["unb", "los"]
    X = np.column_stack([(d[f"h_{k}"] - d[f"a_{k}"]).to_numpy() for k in keys])
    ok = np.isfinite(X).all(axis=1) & np.isfinite(resid)
    X, y = X[ok], resid[ok]

    print("=" * 72)
    print(f"PATTERN NEL RENDIMENTO RECENTE — predicono l'errore del modello? (n={ok.sum()})")
    print("=" * 72)
    corrs = sorted(((np.corrcoef(X[:, i], y)[0, 1], keys[i]) for i in range(len(keys))),
                   key=lambda t: -abs(t[0]))
    se = 1.0 / np.sqrt(len(y))
    print(f"  (rumore: |corr| < ~{2*se:.3f} = non significativo; SE~{se:.3f})\n")
    print(f"  {'feature (diff casa-ospite)':<26}{'corr con residuo':>18}")
    for c, k in corrs:
        flag = "" if abs(c) < 2 * se else "  *"
        print(f"  {k:<26}{c:>+18.4f}{flag}")

    # Multivariata: R^2 del residuo spiegato da TUTTE le feature recenti.
    Xs = (X - X.mean(0)) / X.std(0)
    Xd = np.column_stack([np.ones(len(y)), Xs])
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    yhat = Xd @ beta
    r2 = 1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2)
    noise_r2 = len(keys) / len(y)
    print("\n" + "-" * 72)
    print(f"  R^2 (residuo spiegato dal rendimento recente) = {r2:.4f}")
    print(f"  R^2 atteso da puro rumore ({len(keys)} feature / {len(y)} partite) = {noise_r2:.4f}")
    print("  => se R^2 ~ rumore, NESSUN pattern nascosto sfruttabile.")


if __name__ == "__main__":
    main()
