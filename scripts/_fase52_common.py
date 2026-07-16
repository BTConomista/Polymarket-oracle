"""Helper condivisi della Fase 52 (evita di ripetere l'inversione delle quote).

- ``load_with_rates()``: cache db_base 8 stagioni + λ,μ impliciti (chiusura),
  con cache su disco (`outputs/implied_rates.csv`) per non ripetere le ~3000
  inversioni a ogni script.
- ``dp_pmf`` / ``dp_matrices``: double-Poisson mean-preserving vettoriale (Fase 51).
- ``fit_theta``: MLE walk-forward di θ sulla verosimiglianza congiunta dei punteggi.
- ``add_matchday``: giornata derivata dal conteggio gare (come Fasi 48-51).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import metrics                   # noqa: E402
from src.models import market_implied as mi          # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
MAXG = mi.MAX_GOALS
K = np.arange(MAXG + 1)
_LOGFACT = gammaln(K + 1.0)
_RATES_FP = CACHE / "implied_rates.csv"


def add_matchday(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    m = np.zeros(len(df), int)
    for _, g in df.groupby("season"):
        cnt: dict = {}
        for i in g.index:
            h, a = df.at[i, "home_team"], df.at[i, "away_team"]
            hi, ai = cnt.get(h, 0), cnt.get(a, 0)
            m[i] = int(round((hi + ai) / 2)) + 1
            cnt[h], cnt[a] = hi + 1, ai + 1
    df["matchday"] = m
    return df


def load_with_rates(require_open: bool = False) -> pd.DataFrame:
    """Cache db_base (8 stagioni) + λ,μ impliciti di CHIUSURA (colonne mlam/mmu)
    e, se ``require_open``, anche di APERTURA (mlam_open/mmu_open) sulle sole
    righe che hanno le quote open complete."""
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    df = df[ok].reset_index(drop=True)
    df = add_matchday(df)

    key = ["date", "home_team", "away_team"]
    cache_cols = ["mlam", "mmu", "mlam_open", "mmu_open"]
    if _RATES_FP.exists():
        rates = pd.read_csv(_RATES_FP, parse_dates=["date"])
        df = df.merge(rates, on=key, how="left")
    for c in cache_cols:
        if c not in df.columns:
            df[c] = np.nan

    todo = ~np.isfinite(df["mlam"].to_numpy())
    if todo.any():
        for i in np.where(todo)[0]:
            r = df.iloc[i]
            pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
            lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
            df.iloc[i, df.columns.get_loc("mlam")] = lam
            df.iloc[i, df.columns.get_loc("mmu")] = mu
    if require_open:
        has_open = np.isfinite(df[["odds_home_open", "odds_draw_open",
                                   "odds_away_open", "odds_over_open",
                                   "odds_under_open"]].to_numpy()).all(axis=1)
        todo_o = has_open & ~np.isfinite(df["mlam_open"].to_numpy())
        for i in np.where(todo_o)[0]:
            r = df.iloc[i]
            pH, pD, pA = metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                           r.odds_away_open)
            pO, _ = metrics.devig_binary(r.odds_over_open, r.odds_under_open)
            lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
            df.iloc[i, df.columns.get_loc("mlam_open")] = lam
            df.iloc[i, df.columns.get_loc("mmu_open")] = mu
    df[key + cache_cols].to_csv(_RATES_FP, index=False)
    return df


def dp_pmf(rates, theta: float) -> np.ndarray:
    """PMF (N, 11) double-Poisson mean-preserving (Fase 51), vettoriale."""
    r = np.asarray(rates, float).reshape(-1, 1)
    if theta == 1.0:
        q = np.exp(K * np.log(r) - r - _LOGFACT)
        return q / q.sum(1, keepdims=True)
    lo = np.full(len(r), 0.2); hi = np.full(len(r), 5.0)
    for _ in range(45):
        c = 0.5 * (lo + hi)
        lamc = c.reshape(-1, 1) * r
        q = np.exp(theta * (K * np.log(lamc) - lamc - _LOGFACT))
        q = q / q.sum(1, keepdims=True)
        mean = (q * K).sum(1)
        too_low = mean < r.ravel()
        lo = np.where(too_low, c, lo); hi = np.where(too_low, hi, c)
    return q


def dp_matrices(lam, mu, rho: float, theta: float | np.ndarray) -> np.ndarray:
    """Matrici (N, 11, 11) double-Poisson + correzione ρ. ``theta`` scalare o
    per-riga (array): θ per-riga costruisce le PMF riga per riga."""
    lam = np.asarray(lam, float); mu = np.asarray(mu, float)
    if np.isscalar(theta) or getattr(theta, "ndim", 0) == 0:
        qh, qa = dp_pmf(lam, float(theta)), dp_pmf(mu, float(theta))
    else:
        theta = np.asarray(theta, float)
        qh = np.empty((len(lam), MAXG + 1)); qa = np.empty_like(qh)
        for t in np.unique(np.round(theta, 4)):
            m = np.round(theta, 4) == t
            qh[m] = dp_pmf(lam[m], float(t)); qa[m] = dp_pmf(mu[m], float(t))
    M = qh[:, :, None] * qa[:, None, :]
    M[:, 0, 0] *= 1.0 - lam * mu * rho
    M[:, 0, 1] *= 1.0 + lam * rho
    M[:, 1, 0] *= 1.0 + mu * rho
    M[:, 1, 1] *= 1.0 - rho
    M = np.clip(M, 0.0, None)
    return M / M.sum(axis=(1, 2), keepdims=True)


def fit_theta(lam, mu, hg, ag, rho: float = RHO,
              bounds: tuple[float, float] = (0.6, 1.8)) -> float:
    n = np.arange(len(hg))

    def nll(theta):
        M = dp_matrices(lam, mu, rho, theta)
        return -float(np.mean(np.log(np.clip(M[n, hg, ag], 1e-15, None))))
    return float(minimize_scalar(nll, bounds=bounds, method="bounded",
                                 options={"xatol": 1e-3}).x)


def fit_level(rate, y) -> float:
    """MLE Poisson del fattore comune di livello: exp(c) = Σy / Σrate."""
    return float(np.log(np.sum(y) / np.sum(rate)))


def p1x2(M: np.ndarray) -> np.ndarray:
    tri = np.tril(np.ones((MAXG + 1, MAXG + 1)), -1)
    return np.column_stack([(M * tri[None]).sum(axis=(1, 2)),
                            np.trace(M, axis1=1, axis2=2),
                            (M * tri.T[None]).sum(axis=(1, 2))])


def ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d, rng, B: int = 10_000):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))
