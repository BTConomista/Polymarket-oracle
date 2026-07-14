"""Fase 49 — Quale FINESTRA/FORMA per il nudge stagionale GG/NG? (perche' 35-38?)

Domanda: il profilo del nudge (Fase 48) ha un ginocchio a g.31 scelto a mano. E se il
boost si applicasse ad altre giornate, o "a scalare"? E' per forza quella finestra?
Qui si fa decidere ai dati: si confrontano OOS (8 stagioni, walk-forward) piu' forme del
moltiplicatore μ per la sola GG/NG, dalla piu' stretta alla piu' larga alla piu' libera:

  base       nessun nudge (r=1)
  knee34     coda che parte a g.34 (~solo 35-38, piu' stretta)
  knee31     coda a g.31 (ATTUALE, Fase 48)
  knee25     coda a g.25 (piu' larga: seconda meta')
  cubic      profilo LIBERO liscio [1, s, s², s³] (nessun ginocchio: la forma la
             sceglie il fit — se il segnale fosse graduale/altrove, lo troverebbe)

Log-loss GG/NG per fetta (early 1-19, mid 20-34, finale 35-38) + CI bootstrap vs base.
Attesa onesta (dalla forma empirica): il segnale affidabile e' solo nel finale stretto;
allargare o "graduare" aggiunge rumore, non guadagno.

Uso:  python scripts/_run_season_window.py    (cache db_base 8 stagioni; no backtest)
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
B, SEED = 10_000, 49


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


def _s(md):
    return (np.asarray(md, float) - 19.5) / 18.5


def _basis(name, md):
    md = np.asarray(md, float); s = _s(md); one = np.ones_like(md)
    if name == "cubic":
        return np.column_stack([one, s, s ** 2, s ** 3])
    knee = {"knee34": 34.0, "knee31": 31.0, "knee25": 25.0}[name]
    tail = np.maximum(0.0, md - knee) / (38.0 - knee)
    return np.column_stack([one, s, tail])


def _fit(name, mu, y, md):
    X = _basis(name, md); base = np.asarray(mu, float); y = np.asarray(y, float)

    def nll(c):
        return float(np.sum(base * np.exp(X @ c) - y * (X @ c)))

    def grad(c):
        return X.T @ (base * np.exp(X @ c) - y)

    return minimize(nll, np.zeros(X.shape[1]), jac=grad, method="L-BFGS-B").x


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    return _add_matchday(df)


def _ll_bin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    if len(d) == 0:
        return 0.0, 0.0, 0.0, 0.5
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    variants = ["base", "knee34", "knee31", "knee25", "cubic"]
    acc = {v: [] for v in variants}
    md_all, boost = [], {v: [] for v in variants if v != "base"}

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        yb = cur.is_btts.astype(int).values
        lam, mu, md = cur.exp_home_goals.values, cur.exp_away_goals.values, cur.matchday.values
        md_all.append(md)

        coefs = {v: _fit(v, past.exp_away_goals.values, past.away_goals.values,
                         past.matchday.values) for v in variants if v != "base"}
        for v in variants:
            boost_v = None if v == "base" else np.exp(_basis(v, md) @ coefs[v])
            if v != "base":
                boost[v].append(float(np.exp(_basis(v, [38]) @ coefs[v])[0]))
            gg = np.empty(len(cur))
            for k in range(len(cur)):
                m2 = mu[k] if v == "base" else mu[k] * boost_v[k]
                gg[k] = mi.derive_markets(mi.score_matrix(lam[k], m2, RHO))["btts"]
            acc[v].append(_ll_bin(gg, yb))

    for v in acc:
        acc[v] = np.concatenate(acc[v])
    md_all = np.concatenate(md_all)
    rng = np.random.default_rng(SEED)

    print("=" * 90)
    print("FASE 49 — quale finestra/forma per il nudge GG/NG? (perche' 35-38)")
    print(f"n partite: {len(md_all)}   moltiplicatore ospite alla 38a (media walk-forward):")
    print("   " + "   ".join(f"{v} ×{np.mean(boost[v]):.3f}" for v in boost))
    print("=" * 90)
    slices = [("OVERALL", md_all >= 1), ("early 1-19", md_all <= 19),
              ("mid 20-34", (md_all >= 20) & (md_all <= 34)), ("finale 35-38", md_all >= 35)]
    summ = {}
    for lab, mask in slices:
        base = acc["base"][mask]
        print(f"\n--- {lab} (n={int(mask.sum())}) ---   base GG/NG {base.mean():.4f}")
        for v in variants:
            if v == "base":
                continue
            mean, lo, hi, pneg = _boot(acc[v][mask] - base, rng)
            tag = "meglio" if hi < 0 else ("rumore" if lo < 0 < hi else "peggio")
            print(f"    {v:<7} {acc[v][mask].mean():.4f}   Δ {mean:+.4f} "
                  f"[{lo:+.4f},{hi:+.4f}]  P(aiuta) {pneg:.0%}  {tag}")
            summ[f"{lab}_{v}"] = mean

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase49_season_window", "league": "serie_a", "variant": "gg_nudge_window",
         "rho": RHO, "bootstrap_B": B, "bootstrap_seed": SEED,
         **{f"boost38_{v}": float(np.mean(boost[v])) for v in boost}},
        {"n_matches": int(len(md_all)), **{k: v for k, v in summ.items()}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase49_season_window).")


if __name__ == "__main__":
    main()
