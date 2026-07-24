"""Fase 87 — La coda a DUE parametri (PISTE §4-ter), walk-forward: chiude le due
vie tastate nell'audit Fase 86.

Contesto (Fase 85): un solo θ (double-Poisson) non calibra ogni profondità della
coda (Over 3.5 vuole θ≈1.35, Over 4.5 θ≈1.10). Due vie per un secondo parametro:
 (A) ISOTONICA PER-SOGLIA — ricalibra ogni mercato-totale (Over 1.5/2.5/3.5/4.5)
     con una mappa monotona (PAVA) fittata sul passato, applicata al futuro.
     Metro: log-loss binario OOS e ECE, vs il router grezzo (dp θ=1.225).
 (B) MISTURA DI DUE POISSON — la matrice diventa una mistura su un fattore-tempo s
     condiviso: M(s)=½·q(λ(1+s))⊗q(μ(1+s)) + ½·q(λ(1−s))⊗q(μ(1−s)), marginali dp
     θ=1.225, poi ρ=−0.06. Mean-preserving (½λ(1+s)+½λ(1−s)=λ), allarga la coda.
     Metro: log-loss del risultato esatto OOS, vs il router (s=0).

Entrambe walk-forward espandente (fit su stagioni < s, applicato a s). Usa la
cache `outputs/implied_lammu_cache.csv` (λ,μ del mercato per 7980 partite).

NON registra run (diagnostico). Uso: python scripts/_run_tail_two_param.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import market_implied as mi        # noqa: E402
from src.models.market_implied import _dp_pmf       # noqa: E402

K = 11
THETA = 1.225
RHO = -0.06
CACHE = Path("outputs/implied_lammu_cache.csv")
OVER_LINES = [1.5, 2.5, 3.5, 4.5]
S_GRID = [0.0, 0.05, 0.10, 0.15, 0.20]


# ---------- PAVA (isotonic regression) fatto a mano ----------
def isotonic_fit(x: np.ndarray, y: np.ndarray):
    """Fit monotono non-decrescente y~x (pool-adjacent-violators pesato).
    Ritorna (xs, ys) da usare con np.interp per predire."""
    order = np.argsort(x, kind="mergesort")
    xs = x[order].astype(float); ys = y[order].astype(float)
    w = np.ones_like(ys)
    # PAVA
    vals = list(ys); wts = list(w)
    i = 0
    blocks = [[v, wv] for v, wv in zip(vals, wts)]
    merged = []
    for v, wv in blocks:
        merged.append([v, wv])
        while len(merged) > 1 and merged[-2][0] >= merged[-1][0]:
            v2, w2 = merged.pop()
            v1, w1 = merged.pop()
            nw = w1 + w2
            merged.append([(v1 * w1 + v2 * w2) / nw, nw])
    # espandi i blocchi ai punti x
    fitted = []
    for v, wv in merged:
        fitted.extend([v] * int(round(wv)))
    fitted = np.array(fitted[:len(xs)])
    return xs, fitted


def iso_predict(xs, ys, xnew):
    return np.interp(xnew, xs, ys, left=ys[0], right=ys[-1])


def load():
    c = pd.read_csv(CACHE)
    lam = c["lam"].to_numpy(); mu = c["mu"].to_numpy()
    hg = np.minimum(c["hg"].to_numpy(), K - 1).astype(int)
    ag = np.minimum(c["ag"].to_numpy(), K - 1).astype(int)
    tot = (c["hg"] + c["ag"]).to_numpy()
    seasons = c["season"].to_numpy()
    return c, lam, mu, hg, ag, tot, seasons


def router_over(lam, mu):
    """P(Over 1.5/2.5/3.5/4.5) dal router dp θ=1.225."""
    M = mi.score_matrix(lam, mu, rho=RHO, dp_theta=THETA)
    i = np.arange(K).reshape(-1, 1); j = np.arange(K).reshape(1, -1)
    tt = i + j
    return {L: float(M[tt >= int(L + 0.5)].sum()) for L in OVER_LINES}


def _ll(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def _ece(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p < edges[b + 1] if b < bins - 1 else p <= 1.0)
        if m.sum():
            e += m.mean() * abs(p[m].mean() - y[m].mean())
    return e


def via_A(c, lam, mu, tot, seasons):
    print("\n=== (A) Isotonica per-soglia dei totali — walk-forward ===")
    # pred router per ogni soglia
    P = {L: np.array([router_over(lam[k], mu[k])[L] for k in range(len(lam))])
         for L in OVER_LINES}
    Y = {L: (tot >= int(L + 0.5)).astype(float) for L in OVER_LINES}
    uniq = sorted(np.unique(seasons))
    print(f"{'soglia':>8} {'LL router':>10} {'LL isoton':>10} {'Δ LL':>9} "
          f"{'ECE rout':>9} {'ECE iso':>9}")
    for L in OVER_LINES:
        raw_ll = []; iso_ll = []; raw_y = []; raw_p = []; iso_p = []
        for s in uniq:
            past = seasons < s; cur = seasons == s
            if past.sum() < 600 or cur.sum() < 30:
                continue
            xs, ys = isotonic_fit(P[L][past], Y[L][past])
            pr = P[L][cur]; pi = iso_predict(xs, ys, pr)
            raw_p.append(pr); iso_p.append(pi); raw_y.append(Y[L][cur])
        rp = np.concatenate(raw_p); ip = np.concatenate(iso_p); yy = np.concatenate(raw_y)
        print(f"{('O%.1f'%L):>8} {_ll(rp,yy):>10.4f} {_ll(ip,yy):>10.4f} "
              f"{_ll(ip,yy)-_ll(rp,yy):>+9.4f} {_ece(rp,yy):>9.4f} {_ece(ip,yy):>9.4f}")
    print("Δ LL > 0 = l'isotonica PEGGIORA OOS (il router è già calibrato).")


def _mix_matrix(lam, mu, s):
    if s == 0.0:
        return mi.score_matrix(lam, mu, rho=RHO, dp_theta=THETA)
    ph1, pa1 = _dp_pmf(lam * (1 + s), THETA), _dp_pmf(mu * (1 + s), THETA)
    ph2, pa2 = _dp_pmf(lam * (1 - s), THETA), _dp_pmf(mu * (1 - s), THETA)
    M = 0.5 * np.outer(ph1, pa1) + 0.5 * np.outer(ph2, pa2)
    M[0, 0] *= 1 - lam * mu * RHO; M[0, 1] *= 1 + lam * RHO
    M[1, 0] *= 1 + mu * RHO; M[1, 1] *= 1 - RHO
    M = np.clip(M, 0.0, None)
    return M / M.sum()


def _exact_ll(idx, lam, mu, hg, ag, s):
    ll = 0.0
    for k in idx:
        M = _mix_matrix(lam[k], mu[k], s)
        ll += -np.log(max(M[hg[k], ag[k]], 1e-15))
    return ll / len(idx)


def via_B(c, lam, mu, hg, ag, seasons):
    print("\n=== (B) Mistura di due Poisson (fattore-tempo s) ===")
    allidx = np.arange(len(lam))
    print("in-sample (tutte le partite):")
    base = _exact_ll(allidx, lam, mu, hg, ag, 0.0)
    for s in S_GRID:
        d = _exact_ll(allidx, lam, mu, hg, ag, s) - base
        print(f"  s={s:.2f}: exact-LL Δ vs router {d:+.5f}")
    print("\nwalk-forward (fit s* su passato, applicato al futuro):")
    uniq = sorted(np.unique(seasons))
    diffs = []  # per-match (ll_mix - ll_router) OOS
    log = []; per_season = []
    for st in uniq:
        past = np.where(seasons < st)[0]; cur = np.where(seasons == st)[0]
        if len(past) < 600 or len(cur) < 30:
            continue
        s_star = min(S_GRID, key=lambda s: _exact_ll(past, lam, mu, hg, ag, s))
        dseason = []
        for k in cur:
            llr = -np.log(max(_mix_matrix(lam[k], mu[k], 0.0)[hg[k], ag[k]], 1e-15))
            llm = -np.log(max(_mix_matrix(lam[k], mu[k], s_star)[hg[k], ag[k]], 1e-15))
            dseason.append(llm - llr)
        diffs.extend(dseason); log.append((st, s_star))
        per_season.append((int(st), s_star, float(np.mean(dseason))))
    diffs = np.array(diffs); n = len(diffs)
    # bootstrap CI appaiato sulla differenza media per-partita
    rng = np.random.default_rng(0)
    boot = [diffs[rng.integers(0, n, n)].mean() for _ in range(5000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"  Δ medio (mistura − router) : {diffs.mean():+.5f}  n={n}")
    print(f"  CI95 appaiato: [{lo:+.5f}, {hi:+.5f}]  P(mistura meglio)={100*np.mean(np.array(boot)<0):.1f}%")
    print(f"  -> {'CONCLUSIVO (CI<0)' if hi < 0 else 'nel rumore (CI include 0)'}")
    print("  per stagione (s*, Δ medio):")
    for st, ss, dd in per_season:
        print(f"    {st}: s*={ss:.2f}  Δ={dd:+.5f}  {'✓' if dd < 0 else '✗'}")


def main():
    c, lam, mu, hg, ag, tot, seasons = load()
    print(f"Partite (cache): {len(c)}")
    via_A(c, lam, mu, tot, seasons)
    via_B(c, lam, mu, hg, ag, seasons)


if __name__ == "__main__":
    main()
