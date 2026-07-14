"""Fase 47 — Tracer-bullet: vantaggio-casa TEMPO-VARIANTE (γ per fascia di giornata).

Idea (Fase 30): il vantaggio-casa NON e' costante dentro la stagione — crolla nelle
ultime giornate (casa 40%→36%, trasferta 31%→38% nelle 35-38). Il nostro DC usa un γ
COSTANTE: quel crollo lo ignora. Qui il tracer-bullet piu' economico del modello
dinamico: rendere γ dipendente dalla FASCIA di giornata e vedere se migliora la
previsione OUT-OF-SAMPLE. Se da' segnale → si costruisce lo state-space pieno; se no →
si chiude anche l'ultima architettura, documentato (metodo: versione economica prima).

Meccanismo. γ entra solo in λ (casa): λ = exp(att_h + dif_a + γ). Un γ per fascia =
scalare λ per exp(δ_fascia). δ_fascia stimato sulle stagioni PASSATE (leave-future-out)
come deviazione del tasso-gol casa dalla predizione del modello:

    e^{δ_fascia} = Σ gol_casa / Σ λ   sulle partite passate della fascia   (MLE Poisson)

Due varianti:
  V1 (γ dinamico puro):  λ' = λ·e^δ,  μ invariato        — il vero "vantaggio-casa t"
  V2 (rical. completa):  λ' = λ·e^δ,  μ' = μ·e^ε          — cattura anche l'ascesa
     ospite (Fase 30), con ε = ln(Σ gol_ospite / Σ μ) per fascia

Fasce (Fase 30): early 1-31, tese 32-34, finale 35-38. Confronto walk-forward vs γ
COSTANTE (base), overall e SULLA FINALE (dove vive l'effetto), con CI bootstrap.

Uso:  python scripts/_run_dynamic_gamma.py    (cache db_base; no backtest)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                        # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402
from src.models import market_implied as mi        # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.05
B, SEED = 10_000, 47
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


def _fit_deltas(past):
    """δ,ε per fascia sulle stagioni passate (MLE Poisson closed-form)."""
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
    # accumulatori per-riga
    acc = {v: {m: [] for m in ("x1x2", "over", "btts")} for v in ("base", "v1", "v2")}
    buckets, deltas_hist = [], []

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]
        cur = df[df.season == s].reset_index(drop=True)
        deltas = _fit_deltas(past)
        deltas_hist.append({b: deltas[b] for b in deltas})

        y1 = np.array([_OI[o] for o in cur.result])
        yo = cur.is_over.astype(int).values
        yb = cur.is_btts.astype(int).values
        lam, mu = cur.exp_home_goals.values, cur.exp_away_goals.values
        buckets.append(cur.bucket.values)

        for k in range(len(cur)):
            d, e = deltas[cur.bucket.iloc[k]]
            for v, (l2, m2) in (("base", (lam[k], mu[k])),
                                ("v1", (lam[k] * np.exp(d), mu[k])),
                                ("v2", (lam[k] * np.exp(d), mu[k] * np.exp(e)))):
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

    # δ,ε medi walk-forward (direzione del pattern Fase 30)
    dmean = {b: (float(np.mean([h[b][0] for h in deltas_hist])),
                 float(np.mean([h[b][1] for h in deltas_hist]))) for b in ("early", "tense", "late")}

    print("=" * 94)
    print("FASE 47 — vantaggio-casa tempo-variante (γ per fascia di giornata)")
    print(f"n partite: {len(buckets)}   finale (35-38): {int(late.sum())}   "
          f"tese (32-34): {int((buckets=='tense').sum())}")
    print("=" * 94)
    print("δ,ε medi per fascia (scarto log del tasso-gol dalla predizione; <0 = meno gol del previsto):")
    for b in ("early", "tense", "late"):
        d, e = dmean[b]
        print(f"    {b:<6}  δ_casa {d:+.4f}  (×{np.exp(d):.3f})    ε_ospite {e:+.4f}  (×{np.exp(e):.3f})")
    if dmean["late"][0] < dmean["early"][0]:
        print("  → il vantaggio-casa CALA nella finale (δ_late < δ_early): pattern Fase 30 confermato in-sample.")

    labels = {"x1x2": "1X2", "over": "Over 2.5", "btts": "GG/NG"}
    summ = {}
    for scope, mask in [("OVERALL", np.ones(len(buckets), bool)), ("FINALE 35-38", late)]:
        print(f"\n--- {scope} (n={int(mask.sum())}) ---")
        for mk in ("x1x2", "over", "btts"):
            base = acc["base"][mk][mask]
            print(f"  {labels[mk]:<9} base {base.mean():.4f}", end="")
            for v in ("v1", "v2"):
                mean, lo, hi, pneg = _boot(acc[v][mk][mask] - base, rng)
                tag = "meglio" if hi < 0 else ("rumore" if lo < 0 < hi else "peggio")
                print(f"   | {v} {acc[v][mk][mask].mean():.4f} Δ{mean:+.4f}[{lo:+.4f},{hi:+.4f}]"
                      f"P(aiuta){pneg:.0%} {tag}", end="")
                summ[f"{scope}_{mk}_{v}"] = mean
            print()

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase47_dynamic_gamma", "league": "serie_a", "variant": "time_varying_home_adv",
         "rho": RHO, "bootstrap_B": B, "bootstrap_seed": SEED,
         "delta_late_home": dmean["late"][0], "delta_early_home": dmean["early"][0],
         "eps_late_away": dmean["late"][1]},
        {"n_matches": int(len(buckets)), "n_late": int(late.sum()),
         **{k: v for k, v in summ.items()}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase47_dynamic_gamma).")


if __name__ == "__main__":
    main()
