"""Fase 44 — Routing di forma PER-MERCATO: φ35 sulla diagonale, τ sui totali.

Fase 43: φ35 vince su pareggio/GG, τ vince sui totali (φ sovra-disperde). Quindi la
forma migliore NON è la stessa per tutti i mercati. Qui si valida il ROUTING
(market_implied.price_markets): ogni mercato Tier 1 dalla sua matrice migliore, e si
confronta con "φ35 ovunque" e "τ ovunque". Il routing è ≥ del meglio per-mercato per
costruzione; qui si quantifica il guadagno aggregato.

Uso:  python scripts/_run_routing.py    (usa i backtest in cache)
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

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
MAXG = mi.MAX_GOALS

# mercati Tier 1 binari: nome derive_markets -> esito(hg,ag)
BIN = {
    "over_1.5": lambda h, a: h + a >= 2, "over_2.5": lambda h, a: h + a >= 3,
    "over_3.5": lambda h, a: h + a >= 4, "btts": lambda h, a: (h >= 1) & (a >= 1),
    "dc_1x": lambda h, a: h >= a, "dc_2x": lambda h, a: a >= h, "dc_12": lambda h, a: h != a,
    "home_ov_0.5": lambda h, a: h >= 1, "home_ov_1.5": lambda h, a: h >= 2,
    "away_ov_0.5": lambda h, a: a >= 1, "away_ov_1.5": lambda h, a: a >= 2,
    "cs_home": lambda h, a: a == 0, "cs_away": lambda h, a: h == 0,
    "wtn_home": lambda h, a: (h > a) & (a == 0), "home_by_2plus": lambda h, a: (h - a) >= 2,
    "away_by_2plus": lambda h, a: (a - h) >= 2, "odd_total": lambda h, a: ((h + a) % 2) == 1,
}


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    df = df[ok].reset_index(drop=True)
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    df["mlam"], df["mmu"] = lam, mu
    return df


def _llbin(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def main():
    df = _load()
    # accumulatori: per mercato, log-loss sotto τ / φ / router
    tot = {"tau": {}, "phi": {}, "route": {}}
    for d in tot.values():
        for k in list(BIN) + ["mg", "cs"]:
            d[k] = []

    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.isin(SEASONS[:i])]; cur = df[df.season == s]
        phi0, kappa = mi.fit_balance_phi(past.mlam.values, past.mmu.values,
                                         (past.home_goals == past.away_goals).values, RHO)
        hg, ag = cur.home_goals.values, cur.away_goals.values
        ml, mm = cur.mlam.values, cur.mmu.values
        for k in range(len(cur)):
            M_tau = mi.score_matrix(ml[k], mm[k], RHO)
            phi = mi.balance_phi(ml[k], mm[k], phi0, kappa)
            M_phi = mi.score_matrix(ml[k], mm[k], RHO, diag_inflation=phi)
            d_tau, d_phi = mi.derive_markets(M_tau), mi.derive_markets(M_phi)
            route = mi.price_markets(ml[k], mm[k], RHO, phi0, kappa)
            for name, fn in BIN.items():
                y = float(fn(hg[k], ag[k]))
                tot["tau"][name].append(_llbin(d_tau[name], y))
                tot["phi"][name].append(_llbin(d_phi[name], y))
                tot["route"][name].append(_llbin(route[name], y))
            # multigol (3-classi) e risultato esatto
            t = hg[k] + ag[k]; ymg = 0 if t <= 1 else (1 if t <= 3 else 2)
            for src, dd in (("tau", d_tau), ("phi", d_phi), ("route", route)):
                pmg = np.clip([dd["mg_0_1"], dd["mg_2_3"], dd["mg_4plus"]][ymg], 1e-15, 1)
                tot[src]["mg"].append(-np.log(pmg))
            hc, ac = min(hg[k], MAXG), min(ag[k], MAXG)
            tot["tau"]["cs"].append(-np.log(max(M_tau[hc, ac], 1e-15)))
            tot["phi"]["cs"].append(-np.log(max(M_phi[hc, ac], 1e-15)))
            tot["route"]["cs"].append(-np.log(max(route["score_matrix"][hc, ac], 1e-15)))

    mk_all = list(BIN) + ["mg", "cs"]
    means = {src: {k: float(np.mean(tot[src][k])) for k in mk_all} for src in tot}
    # aggregato: media delle log-loss per-mercato (uguale peso ai mercati)
    agg = {src: float(np.mean([means[src][k] for k in mk_all])) for src in tot}
    print("=" * 72)
    print("FASE 44 — routing di forma per-mercato (φ35 diagonale / τ totali)")
    print("=" * 72)
    print(f"  aggregato (media dei {len(mk_all)} mercati):  "
          f"τ-ovunque {agg['tau']:.4f}   φ35-ovunque {agg['phi']:.4f}   ROUTER {agg['route']:.4f}")
    print(f"  guadagno router vs φ35-ovunque: {agg['route']-agg['phi']:+.5f}   "
          f"vs τ-ovunque: {agg['route']-agg['tau']:+.5f}")
    print("\n  dove il router sceglie τ (totali) e dove φ (esiti/pareggio):")
    tau_wins = [k for k in mk_all if means["tau"][k] < means["phi"][k] - 1e-6]
    phi_wins = [k for k in mk_all if means["phi"][k] < means["tau"][k] - 1e-6]
    print(f"    τ migliore: {', '.join(tau_wins)}")
    print(f"    φ migliore: {', '.join(phi_wins)}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase44_routing", "league": "serie_a", "variant": "per_market_shape_routing",
         "rho_mi": RHO},
        {"n_matches": int(len(tot["tau"]["btts"])), "agg_tau": agg["tau"],
         "agg_phi": agg["phi"], "agg_route": agg["route"],
         "gain_vs_phi": agg["route"] - agg["phi"], "gain_vs_tau": agg["route"] - agg["tau"]},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase44_routing).")


if __name__ == "__main__":
    main()
