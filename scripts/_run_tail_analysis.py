"""Analisi della CODA (Fase 85): quanto bene il motore market-implied prevede gli
esiti RARI (risultato esatto, scorelines alte, totali estremi), se la double-
Poisson sotto-dispersa (theta>1) aiuta o danneggia la coda, e se una dispersione
PRINCIPIATA a forma variabile (COM-Poisson) fa meglio.

Metodo. Per ogni partita con chiusura 1X2+O/U (3 leghe) si invertono le quote nei
lambda,mu del mercato UNA volta (Poisson, rho=-0.06) e si cachano in
outputs/implied_lammu_cache.csv; poi si valutano piu' forme dei marginali
ri-usando gli stessi lambda,mu (tutte mean-preserving: lambda,mu restano le
medie). Confronto: log-loss sul risultato esatto e calibrazione dei mercati di
coda (Over 3.5/4.5) contro la frequenza reale.

Conclusioni (vedi docs/DIARIO.md, Fase 85):
- la Poisson SOVRA-stima i totali alti; la dp theta>1 li corregge;
- l'exact-score log-loss ha il minimo ESATTAMENTE a theta=1.225 (= costante del
  router, Fase 52): la dp del centro e' anche l'ottimo di coda;
- "tensione di profondita'": Over 3.5 vuole theta~1.35, Over 4.5 theta~1.10 -> un
  solo parametro non calibra ogni profondita' della coda;
- la COM-Poisson (nu) pareggia la dp sul log-loss e calibra meglio la coda
  ESTREMA (Over 4.5) ma non batte: la dp e' gia' al tetto.

NON registra run (diagnostico). Uso: python scripts/_run_tail_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

K = 11
SUP = 41
LEAGUES = ["serie_a", "premier_league", "la_liga"]
CACHE = Path("outputs/implied_lammu_cache.csv")
THETAS = [1.0, 1.10, 1.225, 1.35, 1.5]
NUS = [1.15, 1.25, 1.35, 1.5]

_xs = np.arange(SUP)
_logfact = np.concatenate([[0.0], np.cumsum(np.log(np.arange(1, SUP)))])


def build_cache() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_csv(CACHE)
    frames = [pd.read_csv(f"data/{lg}_matches.csv").assign(league=lg) for lg in LEAGUES]
    df = pd.concat(frames, ignore_index=True)
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25",
            "odds_under25", "home_goals", "away_goals"]
    df = df.dropna(subset=need).reset_index(drop=True)
    out = []
    for _, r in df.iterrows():
        pH, pD, pA = metrics.devig_1x2(r["odds_home"], r["odds_draw"], r["odds_away"])
        pO, _ = metrics.devig_binary(r["odds_over25"], r["odds_under25"])
        lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, rho=-0.06)
        out.append((r["league"], r["season"], lam, mu, r["home_goals"], r["away_goals"]))
    c = pd.DataFrame(out, columns=["league", "season", "lam", "mu", "hg", "ag"])
    CACHE.parent.mkdir(exist_ok=True)
    c.to_csv(CACHE, index=False)
    return c


def compois_pmf(mean: float, nu: float, k: int = K) -> np.ndarray:
    """COM-Poisson mean-matched: rate 'a' t.c. E[X]=mean, p(x) ∝ a^x/(x!)^nu."""
    def m_of_a(a):
        logw = _xs * np.log(a) - nu * _logfact
        w = np.exp(logw - logw.max()); w /= w.sum()
        return (_xs * w).sum(), w
    lo, hi = 1e-4, 60.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        mm, _ = m_of_a(mid)
        lo, hi = (mid, hi) if mm < mean else (lo, mid)
    _, w = m_of_a(0.5 * (lo + hi))
    return w[:k]


def _dc_matrix_from_marginals(ph: np.ndarray, pa: np.ndarray, rho: float = -0.06) -> np.ndarray:
    M = np.outer(ph, pa)
    lam = (np.arange(len(ph)) * ph).sum(); mu = (np.arange(len(pa)) * pa).sum()
    M[0, 0] *= 1 - lam * mu * rho; M[0, 1] *= 1 + lam * rho
    M[1, 0] *= 1 + mu * rho; M[1, 1] *= 1 - rho
    M = np.clip(M, 0.0, None)
    return M / M.sum()


def main() -> None:
    c = build_cache()
    n = len(c)
    print(f"Partite con chiusura 1X2+O/U completa: {n}")
    hg = np.minimum(c["hg"].to_numpy(), K - 1).astype(int)
    ag = np.minimum(c["ag"].to_numpy(), K - 1).astype(int)
    tg = (c["hg"] + c["ag"]).to_numpy()
    i = np.arange(K).reshape(-1, 1); j = np.arange(K).reshape(1, -1)
    m_o35 = (i + j) >= 4; m_o45 = (i + j) >= 5
    o35r = float((tg >= 4).mean()); o45r = float((tg >= 5).mean())
    lam = c["lam"].to_numpy(); mu = c["mu"].to_numpy()

    def evaluate(build):
        ll = o35 = o45 = 0.0
        for k in range(n):
            M = build(lam[k], mu[k])
            ll += -np.log(max(M[hg[k], ag[k]], 1e-15))
            o35 += float(M[m_o35].sum()); o45 += float(M[m_o45].sum())
        return ll / n, o35 / n - o35r, o45 / n - o45r

    print(f"\nreali: Over3.5={o35r:.4f}  Over4.5={o45r:.4f}")
    print(f"\n{'modello':>28} {'exactLL':>9} {'O3.5 Δ':>9} {'O4.5 Δ':>9}")
    for th in THETAS:
        tag = "Poisson" if th == 1.0 else f"dp theta={th}"
        r = evaluate(lambda L, M, t=th: mi.score_matrix(L, M, rho=-0.06,
                     dp_theta=(None if t == 1.0 else t)))
        print(f"{tag:>28} " + "%9.4f %+9.4f %+9.4f" % r)
    for nu in NUS:
        r = evaluate(lambda L, M, v=nu: _dc_matrix_from_marginals(
            compois_pmf(L, v), compois_pmf(M, v)))
        print(f"{'COM-Poisson nu=%.2f' % nu:>28} " + "%9.4f %+9.4f %+9.4f" % r)

    print("\nLettura: exactLL minimo a theta=1.225; la coda estrema (Over4.5) e' "
          "calibrata meglio da theta~1.10 / COM nu~1.15, la coda media (Over3.5) "
          "da theta~1.35 -> nessun singolo parametro calibra ogni profondita'.")


if __name__ == "__main__":
    main()
