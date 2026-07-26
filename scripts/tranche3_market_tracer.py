"""Tranche 3, passo 2b del playbook: TRACER MARKET-SIDE sulle leghe nuove.

Non serve il modello: bastano quote di chiusura e risultati. Misura, per ogni
lega, le quattro grandezze che il progetto ha trovato in Serie A e che le Fasi
53/79/80 hanno mostrato essere **per-contesto**:

  1. **θ (sotto-dispersione)** — i gol, dati i tassi del mercato, sono meno
     dispersi di una Poisson? (θ>1 = sotto-dispersi). Fittato leave-one-season-out.
  2. **tilt dei livelli** — il mercato sbaglia sistematicamente il livello di
     λ (casa) e μ (ospite)? Correzione log fittata LOSO (`fit_level` =
     log(Σgol/Σtassi)): **0 = mercato centrato**; il fattore moltiplicativo è
     exp(c), quindi +0.02 significa «il mercato sotto-stima i gol del 2%».
  3. **draw-bias / famiglia-pareggio φ(|λ−μ|)** — il mercato sotto-prezza il
     pareggio nelle gare equilibrate? (φ0>0 = sì, «deficit latino»).
  4. **ROI pari-equilibrio** — scommettere il pareggio dove |λ−μ| è piccolo
     rende? (soglia fissa 0.5, come Fase 40).

ASPETTATIVE DICHIARATE PRIMA (playbook, «cosa aspettarsi»):
  - θ > 1 ma **decrescente con la liquidità** del mercato;
  - i bias sfruttabili **non** si replicano fuori dalla Serie A (finora mai);
  - dall'EDA (report 3 §6): Ligue 1 φ0 ≈ 0 (lega «inglese»), Bundesliga φ0
    piccolo e positivo.

Uso: python cantiere/scripts/tranche3_market_tracer.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scripts import _fase52_common as C  # noqa: E402
from src.evaluation import metrics  # noqa: E402
from src.models import market_implied as mi  # noqa: E402

OUT = ROOT / "cantiere" / "out"
SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "cantiere" / "data",
        "ligue_1": ROOT / "cantiere" / "data"}
# Tutte le stagioni con chiusura O/U reale (serve per invertire 1X2+O/U).
SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
B, SEED = 10_000, 3


def carica(league: str) -> pd.DataFrame:
    df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df = df[df.season.isin(SEASONS)]
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    return df.dropna(subset=need).reset_index(drop=True)


def inverti(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(λ, μ) impliciti nella chiusura 1X2 + O/U, con il motore di produzione."""
    lam, mu = [], []
    for r in df.itertuples():
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        l, m = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
        lam.append(l); mu.append(m)
    return np.array(lam), np.array(mu)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    out = {}
    for league in SNAP:
        df = carica(league)
        lam, mu = inverti(df)
        hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
        is_draw = (df.result == "D").to_numpy().astype(float)
        seasons = df.season.to_numpy()
        margine = float((1 / df.odds_home + 1 / df.odds_draw + 1 / df.odds_away).mean() - 1)

        # --- 1. theta, leave-one-season-out -------------------------------
        thetas = {}
        for s in sorted(set(seasons)):
            tr = seasons != s
            thetas[s] = C.fit_theta(lam[tr], mu[tr], hg[tr], ag[tr], RHO)
        theta_all = C.fit_theta(lam, mu, hg, ag, RHO)

        # --- 2. tilt dei livelli (LOSO) -----------------------------------
        c_lam = {s: C.fit_level(lam[seasons != s], hg[seasons != s]) for s in thetas}
        c_mu = {s: C.fit_level(mu[seasons != s], ag[seasons != s]) for s in thetas}

        # --- 3. famiglia-pareggio phi(|lam-mu|) (LOSO) --------------------
        phis = {}
        for s in thetas:
            tr = seasons != s
            phi0, kappa = mi.fit_balance_phi(lam[tr], mu[tr], is_draw[tr], RHO)
            phis[s] = (float(phi0), float(kappa))
        phi0_all, kappa_all = mi.fit_balance_phi(lam, mu, is_draw, RHO)

        # --- 4. ROI pari-equilibrio (soglia fissa 0.5) --------------------
        bal = np.abs(lam - mu) < 0.5
        stake = int(bal.sum())
        vinte = float(is_draw[bal].sum())
        ritorno = float((df.odds_draw.to_numpy()[bal] * is_draw[bal]).sum())
        roi = (ritorno - stake) / stake if stake else float("nan")
        #    bootstrap sul ROI (le scommesse sono indipendenti)
        pnl = df.odds_draw.to_numpy()[bal] * is_draw[bal] - 1.0
        idx = rng.integers(0, stake, (B, stake)) if stake else None
        roi_lo, roi_hi = ((np.percentile(pnl[idx].mean(axis=1), [2.5, 97.5]))
                          if stake else (np.nan, np.nan))

        print(f"\n=== {league} ({len(df)} partite, {len(set(seasons))} stagioni, "
              f"margine book {margine:.2%}) ===")
        print(f"  theta        pooled {theta_all:.3f} | LOSO "
              f"[{min(thetas.values()):.3f}, {max(thetas.values()):.3f}]  "
              f"({'SOTTO-dispersi' if theta_all > 1 else 'sovra-dispersi'})")
        cl, cm = float(np.mean(list(c_lam.values()))), float(np.mean(list(c_mu.values())))
        print(f"  tilt livelli lambda {cl:+.4f} (x{np.exp(cl):.4f}) | "
              f"mu {cm:+.4f} (x{np.exp(cm):.4f})   [0 = mercato centrato]")
        print(f"  phi(|lam-mu|) phi0 {phi0_all:.4f}  kappa {kappa_all:.3f} | "
              f"phi0 LOSO [{min(p[0] for p in phis.values()):.4f}, "
              f"{max(p[0] for p in phis.values()):.4f}]")
        print(f"  ROI pari-equilibrio {roi:+.2%} su {stake} scommesse "
              f"(CI95 [{roi_lo:+.2%}, {roi_hi:+.2%}]) -> "
              f"{'POSITIVO conclusivo' if roi_lo > 0 else 'non sfruttabile'}")

        out[league] = {
            "n": int(len(df)), "margine_book": margine,
            "theta_pooled": float(theta_all),
            "theta_loso": {k: float(v) for k, v in thetas.items()},
            "tilt_lambda": float(np.mean(list(c_lam.values()))),
            "tilt_mu": float(np.mean(list(c_mu.values()))),
            "phi0": float(phi0_all), "kappa": float(kappa_all),
            "phi0_loso": {k: v[0] for k, v in phis.items()},
            "roi_pari": {"roi": roi, "n_bet": stake, "vinte": vinte,
                         "ci95": [float(roi_lo), float(roi_hi)]},
        }

    (OUT / "tranche3_market_tracer.json").write_text(json.dumps(out, indent=2))
    print("\n=== QUADRO CROSS-LEGA ===")
    print(f"{'lega':16s} {'margine':>8s} {'theta':>7s} {'tilt_l':>7s} {'tilt_m':>7s} "
          f"{'phi0':>7s} {'ROI pari':>9s}")
    for lg, v in out.items():
        print(f"{lg:16s} {v['margine_book']:7.2%} {v['theta_pooled']:7.3f} "
              f"{v['tilt_lambda']:7.4f} {v['tilt_mu']:7.4f} {v['phi0']:7.4f} "
              f"{v['roi_pari']['roi']:+8.2%}")
    print(f"\n-> {(OUT / 'tranche3_market_tracer.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
