"""Fase 52 (G) — Modello SCORE-DRIVEN (il "Kalman economico"): il dinamico chiuso per TEST.

Le Fasi 47-48 hanno chiuso "l'architettura dinamica" testando il profilo
stagionale deterministico; il random-walk delle FORZE (state-space/Kalman) era
rimasto chiuso *per argomento* (il decadimento esponenziale e' il Kalman a
regime). Qui la versione economica del vero dinamico (metodo §1.3): un modello
**score-driven** (GAS-lite) in cui attacco/difesa di ogni squadra si aggiornano
DOPO OGNI PARTITA con il residuo di Poisson — nessun refit batch, memoria infinita
adattiva:

    λ = exp(c + a_H − d_A + γ)          μ = exp(c + a_A − d_H)
    dopo la partita:  a_H += η·(y_H − λ)/√λ     d_A −= η·(y_H − λ)/√λ
                      a_A += η·(y_A − μ)/√μ     d_H −= η·(y_A − μ)/√μ
    (residuo di Pearson: auto-scala l'update; squadre nuove partono a 0 = media)

η (learning rate) scelto LEAVE-FUTURE-OUT su una griglia (log-loss 1X2 delle
stagioni passate); c e γ stimati sulle medie del passato. Confronto col DC batch
ufficiale (cache) sulle stesse righe: se il GAS ~ DC, lo state-space non aggiunge
nulla (chiusura PER TEST); se perde, idem a fortiori.

Uso:  python scripts/_run_fase52_gas.py    (cache db_base)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log            # noqa: E402
from scripts import _fase52_common as C              # noqa: E402

B, SEED = 10_000, 52
RHO_DC = -0.05
_OI = {"H": 0, "D": 1, "A": 2}
ETAS = [0.01, 0.02, 0.035, 0.05, 0.08, 0.12]


def _run_gas(df, eta: float, c: float, gamma: float):
    """Esegue il modello score-driven su TUTTO il dataframe (ordinato per data);
    ritorna (lam, mu) PRE-partita per ogni riga (predizione, poi update)."""
    att: dict = {}; dfn: dict = {}
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for k, r in enumerate(df.itertuples()):
        h, a = r.home_team, r.away_team
        ah, dh = att.get(h, 0.0), dfn.get(h, 0.0)
        aa, da = att.get(a, 0.0), dfn.get(a, 0.0)
        l = np.exp(c + ah - da + gamma)
        m = np.exp(c + aa - dh)
        lam[k], mu[k] = l, m
        rh = (r.home_goals - l) / np.sqrt(l)
        ra = (r.away_goals - m) / np.sqrt(m)
        att[h] = ah + eta * rh; dfn[a] = da - eta * rh
        att[a] = aa + eta * ra; dfn[h] = dh - eta * ra
    return lam, mu


def _ll_x2(lam, mu, res):
    P = np.clip(C.p1x2(C.dp_matrices(lam, mu, RHO_DC, 1.0)), 1e-15, 1)
    yi = np.array([_OI[o] for o in res])
    return -np.log(P[np.arange(len(yi)), yi])


def main():
    t0 = time.time()
    df = C.load_with_rates().sort_values("date").reset_index(drop=True)
    print(f"dati pronti in {time.time()-t0:.0f}s (n={len(df)})", flush=True)
    seasons = [s for s in C.SEASONS if s in set(df.season)]

    ll_gas, ll_dc, etas_used = [], [], []
    per_season: dict = {}

    for i, s in enumerate(seasons):
        if i == 0:
            continue
        past_m = df.season.isin(seasons[:i]).to_numpy()
        cur_m = (df.season == s).to_numpy()
        past = df[past_m]
        # c, gamma dalle medie del passato
        gh, ga = past.home_goals.mean(), past.away_goals.mean()
        c = float(np.log(np.sqrt(gh * ga)))
        gamma = float(np.log(gh / ga))
        # scelta di eta LEAVE-FUTURE-OUT: log-loss 1X2 sul passato (salta il
        # primo anno di burn-in per non punire l'inizializzazione a zero)
        burn = df.season.isin(seasons[:1]).to_numpy()
        sel = past_m & ~burn
        if not sel.any():            # prima iterazione: il passato E' il burn-in
            sel = past_m
        best_eta, best_ll = None, np.inf
        for eta in ETAS:
            lam, mu = _run_gas(df, eta, c, gamma)
            ll = float(_ll_x2(lam[sel], mu[sel], df.result.values[sel]).mean())
            if ll < best_ll:
                best_ll, best_eta = ll, eta
        etas_used.append(best_eta)
        lam, mu = _run_gas(df, best_eta, c, gamma)
        g = _ll_x2(lam[cur_m], mu[cur_m], df.result.values[cur_m])
        # DC batch ufficiale (cache): stesse righe, stessa forma (tau, rho -0.05)
        d = _ll_x2(df.exp_home_goals.values[cur_m], df.exp_away_goals.values[cur_m],
                   df.result.values[cur_m])
        ll_gas.append(g); ll_dc.append(d)
        per_season[s] = (float(g.mean()), float(d.mean()))
        print(f"  {s}: GAS {g.mean():.4f} (η={best_eta})   DC {d.mean():.4f}", flush=True)

    ll_gas = np.concatenate(ll_gas); ll_dc = np.concatenate(ll_dc)
    rng = np.random.default_rng(SEED)
    mean, lo, hi, p = C.boot(ll_gas - ll_dc, rng)

    print("\n" + "=" * 84)
    print(f"FASE 52 (G) — score-driven (GAS) vs DC batch (1X2, n={len(ll_gas)})")
    print("=" * 84)
    print(f"  GAS {ll_gas.mean():.4f}   DC batch {ll_dc.mean():.4f}   "
          f"Δ={mean:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  P(GAS meglio)={p:.0%}")
    print(f"  η scelti walk-forward: {etas_used}")
    wins = sum(1 for s in per_season if per_season[s][0] < per_season[s][1])
    print(f"  stagioni in cui il GAS batte il DC: {wins}/{len(per_season)}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase52_gas", "league": "serie_a",
         "variant": "score_driven_vs_dc_batch", "rho": RHO_DC,
         "etas_grid": ETAS, "seasons": seasons,
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": int(len(ll_gas)), "gas_ll": float(ll_gas.mean()),
         "dc_ll": float(ll_dc.mean()), "delta": mean,
         "ci_lo": lo, "ci_hi": hi, "p_gas_better": p,
         "eta_mean": float(np.mean(etas_used)), "seasons_gas_wins": int(wins)},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print(f"\nRun registrato (source=fase52_gas). Tempo {time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
