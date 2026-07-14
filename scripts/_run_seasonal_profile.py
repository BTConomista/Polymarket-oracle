"""Fase 48 — Modello dinamico a PROFILO STAGIONALE liscio, su 8 stagioni.

La Fase 47 ha trovato (redirect): il vantaggio-casa di fine stagione non crolla perche'
la casa segni meno, ma perche' l'OSPITE segna ~+14.8% nel finale (le partite si aprono).
E' un effetto di FASE STAGIONALE deterministico (uguale ogni anno), non deriva casuale
delle forze (stabili — Fasi 2b/13/25). Il modello dinamico giusto NON e' un Kalman
(random-walk delle forze) ma un PROFILO stagionale liscio dei tassi λ,μ in funzione
della giornata.

Qui si fa DUE cose insieme:
  (1) ROBUSTEZZA: si estende a 8 stagioni (1819-2526, come Fasi 19/31) — il finale
      passa da 202 a ~280 partite.
  (2) MODELLO PIENO: profilo liscio via regressione di Poisson. Per la casa e per
      l'ospite si stima un moltiplicatore del tasso  r(md) = exp(c0 + c1·s + c2·tail),
      con  s = (md−19.5)/18.5 ∈ [−1,1] (trend globale) e  tail = max(0,md−31)/7
      (salita di coda, 0 fino alla 31 → 1 alla 38). c fittati WALK-FORWARD (MLE Poisson
      con offset ln(tasso)) sulle stagioni passate. Confronto: base (γ costante) vs
      V2-bucket (Fase 47, 3 gradini) vs PROFILO liscio; overall e finale, CI bootstrap.

Uso:  python scripts/_run_seasonal_profile.py    (cache db_base 8 stagioni; no backtest)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                        # noqa: E402
from src.evaluation import experiment_log          # noqa: E402
from src.models import market_implied as mi        # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.05
B, SEED = 10_000, 48
_OI = {"H": 0, "D": 1, "A": 2}


def _add_matchday(df):
    df = df.sort_values("date").reset_index(drop=True)
    md = np.zeros(len(df), int)
    for _, g in df.groupby("season"):
        cnt = {}
        for i in g.index:
            h, a = df.at[i, "home_team"], df.at[i, "away_team"]
            hi, ai = cnt.get(h, 0), cnt.get(a, 0)
            md[i] = int(round((hi + ai) / 2)) + 1
            cnt[h], cnt[a] = hi + 1, ai + 1
    df["matchday"] = md
    return df


def _basis(md):
    md = np.asarray(md, float)
    s = (md - 19.5) / 18.5
    tail = np.maximum(0.0, md - 31.0) / 7.0
    return np.column_stack([np.ones_like(md), s, tail])


def _bucket(md):
    return np.where(md <= 31, "early", np.where(md <= 34, "tense", "late"))


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = _add_matchday(df)
    df["bucket"] = _bucket(df["matchday"].values)
    return df


def _fit_profile(base_rate, goals, md):
    """MLE Poisson del profilo: y~Poisson(base·exp(X·c)). Ritorna c (3,)."""
    X = _basis(md)
    base = np.asarray(base_rate, float); y = np.asarray(goals, float)

    def nll(c):
        g = X @ c
        rate = base * np.exp(g)
        return float(np.sum(rate - y * g))            # + const (y·ln base) irrilevante

    def grad(c):
        g = X @ c
        rate = base * np.exp(g)
        return X.T @ (rate - y)

    res = minimize(nll, np.zeros(3), jac=grad, method="L-BFGS-B")
    return res.x


def _fit_buckets(past):
    out = {}
    for b in ("early", "tense", "late"):
        g = past[past.bucket == b]
        d = float(np.log(g.home_goals.sum() / g.exp_home_goals.sum())) if len(g) else 0.0
        e = float(np.log(g.away_goals.sum() / g.exp_away_goals.sum())) if len(g) else 0.0
        out[b] = (d, e)
    return out


def _ll_multi(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1))


def _ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    rng = np.random.default_rng(SEED)
    acc = {v: {m: [] for m in ("x1x2", "over", "btts")} for v in ("base", "bucket", "smooth")}
    buckets = []
    boost38 = []          # moltiplicatore ospite alla giornata 38 (profilo liscio)

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        y1 = np.array([_OI[o] for o in cur.result])
        yo = cur.is_over.astype(int).values
        yb = cur.is_btts.astype(int).values
        lam, mu, md = cur.exp_home_goals.values, cur.exp_away_goals.values, cur.matchday.values
        buckets.append(cur.bucket.values)

        deltas = _fit_buckets(past)
        c_lam = _fit_profile(past.exp_home_goals.values, past.home_goals.values, past.matchday.values)
        c_mu = _fit_profile(past.exp_away_goals.values, past.away_goals.values, past.matchday.values)
        boost38.append(float(np.exp(_basis([38]) @ c_mu)[0]))

        r_lam = np.exp(_basis(md) @ c_lam)
        r_mu = np.exp(_basis(md) @ c_mu)

        for k in range(len(cur)):
            d, e = deltas[cur.bucket.iloc[k]]
            variants = {
                "base": (lam[k], mu[k]),
                "bucket": (lam[k] * np.exp(d), mu[k] * np.exp(e)),
                "smooth": (lam[k] * r_lam[k], mu[k] * r_mu[k]),
            }
            for v, (l2, m2) in variants.items():
                dm = mi.derive_markets(mi.score_matrix(l2, m2, RHO))
                p1x2 = np.array([dm["home_win"], dm["draw"], dm["away_win"]])
                acc[v]["x1x2"].append(_ll_multi(p1x2[None, :], y1[k:k + 1])[0])
                acc[v]["over"].append(_ll_bin(np.array([dm["over_2.5"]]), yo[k:k + 1])[0])
                acc[v]["btts"].append(_ll_bin(np.array([dm["btts"]]), yb[k:k + 1])[0])

    for v in acc:
        for m in acc[v]:
            acc[v][m] = np.array(acc[v][m])
    buckets = np.concatenate(buckets)
    late = buckets == "late"

    print("=" * 96)
    print("FASE 48 — modello dinamico a profilo stagionale liscio (8 stagioni)")
    print(f"n partite: {len(buckets)}   finale (35-38): {int(late.sum())}   "
          f"stagioni di test: {len(SEASONS)-1}")
    print(f"moltiplicatore OSPITE alla 38a (profilo liscio, media walk-forward): "
          f"×{np.mean(boost38):.3f}  (Fase 47 bucket-late: ×1.148)")
    print("=" * 96)
    labels = {"x1x2": "1X2", "over": "Over 2.5", "btts": "GG/NG"}
    summ = {}
    for scope, mask in [("OVERALL", np.ones(len(buckets), bool)), ("FINALE 35-38", late)]:
        print(f"\n--- {scope} (n={int(mask.sum())}) ---   P(aiuta)=P(Δ<0) bootstrap")
        for mk in ("x1x2", "over", "btts"):
            base = acc["base"][mk][mask]
            print(f"  {labels[mk]:<9} base {base.mean():.4f}", end="")
            for v in ("bucket", "smooth"):
                mean, lo, hi, pneg = _boot(acc[v][mk][mask] - base, rng)
                tag = "meglio" if hi < 0 else ("rumore" if lo < 0 < hi else "peggio")
                print(f"   | {v:<6} {acc[v][mk][mask].mean():.4f} Δ{mean:+.4f}"
                      f"[{lo:+.4f},{hi:+.4f}]P{pneg:.0%} {tag}", end="")
                summ[f"{scope}_{mk}_{v}"] = mean
            print()

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase48_seasonal_profile", "league": "serie_a",
         "variant": "smooth_seasonal_profile", "rho": RHO, "n_seasons": len(SEASONS) - 1,
         "away_boost_md38": float(np.mean(boost38)), "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(buckets)), "n_late": int(late.sum()),
         **{k: v for k, v in summ.items()}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase48_seasonal_profile).")


if __name__ == "__main__":
    main()
