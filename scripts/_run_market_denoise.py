"""Punto 4 — Denoising CROSS-STAGIONE del market-implied.

Il motore market-implied (Fase 24/26) inverte OGNI partita in isolamento. Qui
proviamo due correzioni stimate sul PASSATO e applicate al futuro (leave-future-out),
sul mercato-vetrina non prezzato: il GG/NG.

  1. POWER-DEVIG: p_i ∝ (1/o_i)^(1/eta) invece del devig moltiplicativo (eta=1);
     eta tarato sulla log-loss 1X2 passata (corregge il bias del margine bookmaker).
  2. RICAL. DERIVATA: Platt (a,b) sul GG/NG market-implied, imparato sulle stagioni
     passate (corregge un bias sistematico del motore su un mercato non prezzato).

Trade-off bias/varianza/lag: calibrazione su TUTTO il passato (half-life=inf, minima
varianza) vs pesata sul RECENTE (half-life=2 stagioni, segue la deriva ma piu'
rumorosa). Confronto esplicito.

Riferimenti: raw market-implied (Fase 26), DC-da-gol, baseline in-sample.
Uso:  python scripts/_run_market_denoise.py   (usa i backtest in cache; inversioni)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402
from src.models import market_implied as mi        # noqa: E402
from src.models import market_denoise as md        # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 4


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv", parse_dates=["date"]); d["season"] = s
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def _implied_gg(row, eta):
    """P(GG) market-implied per una riga, con power-devig (eta) sul 1X2."""
    if eta == 1.0:
        pH, pD, pA = metrics.devig_1x2(row.odds_home, row.odds_draw, row.odds_away)
    else:
        pH, pD, pA = md.power_devig(row.odds_home, row.odds_draw, row.odds_away, eta)
    pOver, _ = metrics.devig_binary(row.odds_over, row.odds_under)
    lam, mu = mi.implied_lambda_mu(pH, pD, pA, pOver, RHO)
    return mi.derive_markets(mi.score_matrix(lam, mu, RHO))["btts"]


def _ll(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    odds_ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away", "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    df = df[odds_ok].copy()
    df["is_btts"] = ((df.home_goals >= 1) & (df.away_goals >= 1)).astype(float)

    # P(GG) raw (eta=1) per tutte le righe (una volta).
    df["gg_raw"] = [_implied_gg(r, 1.0) for r in df.itertuples()]
    rng = np.random.default_rng(SEED)

    # --- Leave-future-out: per stagione i, calibra su < i, applica a i ---
    def eval_variant(power, recal, half_life):
        base_ll, den_ll, etas, abs_ = [], [], [], []
        for i, s in enumerate(SEASONS):
            if i == 0:
                continue
            past = df[df.season.isin(SEASONS[:i])]
            cur = df[df.season == s]
            w = md.recency_weights(past.season.tolist(), SEASONS, half_life) if recal or power else None
            # 1) power-devig: calibra eta sul 1X2 passato, ricalcola gg su cur
            if power:
                odds_past = past[["odds_home", "odds_draw", "odds_away"]].to_numpy()
                eta = md.fit_power_eta(odds_past, past.result.tolist(), w)
                gg_cur = np.array([_implied_gg(r, eta) for r in cur.itertuples()])
                gg_past = np.array([_implied_gg(r, eta) for r in past.itertuples()])
            else:
                eta = 1.0
                gg_cur = cur.gg_raw.to_numpy(); gg_past = past.gg_raw.to_numpy()
            etas.append(eta)
            # 2) ricalibrazione derivata: Platt su gg_past -> applica a gg_cur
            if recal:
                a, b = md.fit_derived_recal(gg_past, past.is_btts.to_numpy(), w)
                gg_out = md.apply_derived_recal(gg_cur, a, b)
                abs_.append((a, b))
            else:
                gg_out = gg_cur
            base_ll.append(_ll(cur.gg_raw.to_numpy(), cur.is_btts.to_numpy()))
            den_ll.append(_ll(gg_out, cur.is_btts.to_numpy()))
        base = np.concatenate(base_ll); den = np.concatenate(den_ll)
        return base, den, np.mean(etas), (np.mean(abs_, axis=0) if abs_ else None)

    # Riferimenti (sulle stagioni 1..5, coerenti col LFO)
    ref = df[df.season.isin(SEASONS[1:])]
    dc_ll = _ll(ref.m_btts.to_numpy(), ref.is_btts.to_numpy()).mean()
    base_rate = ref.is_btts.mean()
    base_ll = _ll(np.full(len(ref), base_rate), ref.is_btts.to_numpy()).mean()
    raw_ll = _ll(ref.gg_raw.to_numpy(), ref.is_btts.to_numpy()).mean()

    print("=" * 84)
    print("PUNTO 4 — denoising cross-stagione del market-implied sul GG/NG (LFO, 5 stagioni)")
    print("=" * 84)
    print(f"  riferimenti:  raw market-implied={raw_ll:.4f}   DC-da-gol={dc_ll:.4f}   "
          f"baseline={base_ll:.4f}")
    print(f"\n  {'denoiser':<34}{'GG log-loss':>12}{'Δ vs raw':>11}{'CI95 Δ':>22}{'P(mig)':>8}")
    summary = {"raw_ll": raw_ll, "dc_ll": dc_ll, "baseline_ll": base_ll}
    variants = [
        ("power-devig (eta, all-history)", True, False, np.inf),
        ("recal derivata (all-history)", False, True, np.inf),
        ("recal derivata (recency hl=2)", False, True, 2.0),
        ("power + recal (all-history)", True, True, np.inf),
    ]
    for name, power, recal, hl in variants:
        base, den, eta, ab = eval_variant(power, recal, hl)
        mean, lo, hi, pmig = _boot(den - base, rng)
        extra = f"eta={eta:.3f}" if power else ""
        if ab is not None:
            extra += f" a={ab[0]:.2f} b={ab[1]:+.2f}"
        verd = "VIVA" if hi < 0 else ("promett." if mean < 0 else "")
        print(f"  {name:<34}{den.mean():>12.4f}{mean:>+11.4f}   [{lo:+.4f}, {hi:+.4f}]{pmig:>8.0%} {verd}")
        print(f"        {extra}")
        summary[f"{name}_ll"] = float(den.mean()); summary[f"{name}_delta"] = mean
        summary[f"{name}_ci_lo"] = lo; summary[f"{name}_ci_hi"] = hi

    experiment_log.append_run(experiment_log.make_record(
        {"source": "punto4_market_denoise", "league": "serie_a", "variant": "gg_denoise",
         "rho": RHO, "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(ref)), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=punto4_market_denoise).")


if __name__ == "__main__":
    main()
