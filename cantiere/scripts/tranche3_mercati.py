"""Tranche 3, passi 4 e 5 del playbook: il MOTORE market-implied sulle leghe nuove
e la leva φ(|λ−μ|) della rosa.

**Passo 4 — multi-mercato.** L'inversione della chiusura 1X2+O/U nei tassi
(λ, μ) e la matrice DC danno il prezzo di OGNI mercato Tier 1. Si confronta con
il DC-da-gol (stessi (λ,μ) del modello) e con la baseline in-sample, mercato per
mercato, con bootstrap appaiato. Riuso ESATTO delle funzioni della Fase 26
(`scripts/_run_market_implied.py`), quindi i numeri sono confrontabili 1:1 con
quelli storici del progetto.
ASPETTATIVA DICHIARATA PRIMA: il market-implied batte il DC-da-gol su ~13/14
mercati (la MATRICE e' universale: 3/3 leghe finora). Se non accade, ci si ferma
e si guarda ai dati, non al modello.

**Passo 5 — la leva φ35 sulla famiglia-pareggio.** Si riprezza con
`price_markets(phi0, kappa)` usando i parametri fittati **leave-one-season-out**
(mai in-sample) e si misura se la famiglia-pareggio migliora.
ASPETTATIVA DICHIARATA PRIMA (dall'EDA, report 3 §6, e dal tracer market-side):
Ligue 1 φ0 = 0 → nessun guadagno atteso; Bundesliga φ0 ≈ 0.18 → guadagno
possibile ma piccolo.

Uso: python cantiere/scripts/tranche3_mercati.py [--leagues ...]
"""
from __future__ import annotations

import argparse
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

from scripts import _run_market_implied as MI  # noqa: E402
from scripts._run_market_implied import (  # noqa: E402
    BINARY, SEED, baseline_ll, boot, dc_lambda_mu, eval_markets, invert_all,
    ll_bin, _binary_outcomes)
from src.models import market_implied as mi  # noqa: E402

OUT = ROOT / "cantiere" / "out"
RHO = MI.RHO_MAIN
LEAGUES = ["bundesliga", "ligue_1", "serie_a", "premier_league", "la_liga"]
# La famiglia-pareggio: i mercati che la phi(|lam-mu|) puo' toccare.
FAMIGLIA_PAREGGIO = ["draw", "dc_1x", "dc_x2"]


def carica(league: str, seasons: list[str]) -> dict[str, pd.DataFrame]:
    path = OUT / f"tracer_pred_{league}.csv"
    if not path.exists():
        raise SystemExit(f"manca {path}: esegui prima tranche3_tracer.py")
    df = pd.read_csv(path, dtype={"test_season": str}, parse_dates=["date"])
    df = df.dropna(subset=["odds_home", "odds_draw", "odds_away",
                           "odds_over", "odds_under"])
    return {s: df[df.test_season == s].reset_index(drop=True)
            for s in seasons if (df.test_season == s).any()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    esito = {}

    for league in args.leagues:
        dfs = carica(league, MI.TEST_SEASONS)
        MI.TEST_SEASONS = [s for s in MI.TEST_SEASONS if s in dfs]
        n = sum(len(d) for d in dfs.values())
        print(f"\n{'='*92}\nMARKET-IMPLIED — {league} "
              f"({n} partite, stagioni {MI.TEST_SEASONS[0]}..{MI.TEST_SEASONS[-1]}, rho={RHO})\n{'='*92}")

        lm_mkt = invert_all(dfs, targets_over=True, rho=RHO)
        lm_dc = dc_lambda_mu(dfs)
        ev_mkt, ev_dc, ev_base = (eval_markets(lm_mkt, dfs, RHO),
                                  eval_markets(lm_dc, dfs, RHO),
                                  baseline_ll(dfs))

        mercati = BINARY + ["multigol", "risultato_esatto"]
        print(f"{'mercato':22s} {'mercato-impl':>12s} {'DC-da-gol':>11s} "
              f"{'baseline':>10s}   {'MI vs DC':>20s}")
        vinti_dc = vinti_base = 0
        righe = {}
        for mk in mercati:
            a, b, c = ev_mkt[mk].mean(), ev_dc[mk].mean(), ev_base[mk].mean()
            d, lo, hi = boot(ev_dc[mk] - ev_mkt[mk], rng)   # >0 = MI meglio
            vinti_dc += int(a < b); vinti_base += int(a < c)
            print(f"{mk:22s} {a:12.4f} {b:11.4f} {c:10.4f}   "
                  f"{d:+.4f} [{lo:+.4f},{hi:+.4f}] "
                  f"{'*' if lo > 0 else ('!' if hi < 0 else ' ')}")
            righe[mk] = {"market_implied": float(a), "dc": float(b), "baseline": float(c),
                         "mi_meno_dc": float(d), "ci95": [float(lo), float(hi)]}
        print(f"\n  market-implied batte il DC-da-gol su {vinti_dc}/{len(mercati)} mercati, "
              f"la baseline su {vinti_base}/{len(mercati)}")

        # ---- passo 5: la leva phi(|lam-mu|), fittata leave-one-season-out ----
        print(f"\n  [leva phi35 sulla famiglia-pareggio, fit leave-one-season-out]")
        lam_all = {s: np.array([l for l, _ in lm_mkt[s]]) for s in dfs}
        mu_all = {s: np.array([m for _, m in lm_mkt[s]]) for s in dfs}
        draw_all = {s: (dfs[s].result == "D").to_numpy().astype(float) for s in dfs}
        phi_par = {}
        for s in dfs:
            tr = [x for x in dfs if x != s]
            L = np.concatenate([lam_all[x] for x in tr])
            M = np.concatenate([mu_all[x] for x in tr])
            D = np.concatenate([draw_all[x] for x in tr])
            phi_par[s] = mi.fit_balance_phi(L, M, D, RHO)
        print("    phi0 per stagione (fit sulle ALTRE): "
              + ", ".join(f"{s}:{phi_par[s][0]:.3f}" for s in dfs))

        ll_phi = {mk: [] for mk in FAMIGLIA_PAREGGIO}
        ll_no = {mk: [] for mk in FAMIGLIA_PAREGGIO}
        for s in dfs:
            phi0, kappa = phi_par[s]
            hg = dfs[s].home_goals.to_numpy(); ag = dfs[s].away_goals.to_numpy()
            outc = _binary_outcomes(hg, ag)
            pr_phi = [mi.price_markets(l, m, RHO, phi0, kappa) for l, m in lm_mkt[s]]
            pr_no = [mi.price_markets(l, m, RHO) for l, m in lm_mkt[s]]
            for mk in FAMIGLIA_PAREGGIO:
                y = outc[mk].astype(float)
                ll_phi[mk].append(ll_bin(np.array([p[mk] for p in pr_phi]), y))
                ll_no[mk].append(ll_bin(np.array([p[mk] for p in pr_no]), y))
        fam = {}
        for mk in FAMIGLIA_PAREGGIO:
            a = np.concatenate(ll_no[mk]); b = np.concatenate(ll_phi[mk])
            d, lo, hi = boot(a - b, rng)          # >0 = phi35 MIGLIORA
            verdetto = "MEGLIO" if lo > 0 else ("PEGGIO" if hi < 0 else "nel rumore")
            print(f"    {mk:8s} senza phi {a.mean():.4f} -> con phi {b.mean():.4f}   "
                  f"guadagno {d:+.5f} CI95 [{lo:+.5f},{hi:+.5f}] -> {verdetto}")
            fam[mk] = {"senza_phi": float(a.mean()), "con_phi": float(b.mean()),
                       "guadagno": float(d), "ci95": [float(lo), float(hi)],
                       "verdetto": verdetto}

        esito[league] = {"n": n, "stagioni": list(dfs),
                         "mercati": righe,
                         "mi_batte_dc": f"{vinti_dc}/{len(mercati)}",
                         "mi_batte_baseline": f"{vinti_base}/{len(mercati)}",
                         "phi35": {"parametri_loso": {s: list(map(float, phi_par[s])) for s in dfs},
                                   "famiglia_pareggio": fam}}
        MI.TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]

    path = OUT / "tranche3_mercati.json"
    prev = json.loads(path.read_text()) if path.exists() else {}
    prev.update(esito)
    path.write_text(json.dumps(prev, indent=2, default=str))
    print(f"\n-> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
