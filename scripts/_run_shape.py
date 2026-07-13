"""Fase 27 — Spremere il market-implied: ottimizzare la FORMA dei punteggi.

Nel market-implied (Fase 26) i lambda,mu vengono dal mercato (ottimi, non li
tocchiamo), ma la FORMA della distribuzione attorno a quei tassi e' nostra — e
nella Fase 26 rho=-0.06 era fissato un po' a caso. Qui la impariamo dai risultati
reali, walk-forward, tenendo i lambda,mu del mercato:

  - rho=-0.06 fisso           (baseline Fase 26)
  - rho FITTATO               (verosimiglianza dei punteggi passati)
  - rho + inflazione diagonale phi   (Fase 12b, ma sui lambda,mu del mercato)
  - binomiale negativa (dispersione FITTATA)   (over-dispersione dei gol)

Onesta': la forma e' un parametro GLOBALE (non per-squadra), fittato su tutte le
partite delle stagioni PRECEDENTI e applicato alla stagione di test (walk-forward,
niente look-ahead). Non serve il Dixon-Coles: il motore usa solo quote + matrice,
quindi si lavora direttamente dallo snapshot (veloce). Valutazione sui mercati
derivati (risultato esatto, multigol, GG/NG, over lines), CI bootstrap.

Uso:  python scripts/_run_shape.py     (inversioni + fit; alcuni minuti)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics
from src.models import market_implied as mi

TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO0 = -0.06
B, SEED = 10_000, 27
MAXG = mi.MAX_GOALS


def invert(df):
    """lambda,mu impliciti (1X2+O/U, rho0) per ogni partita."""
    lm = []
    for r in df.itertuples():
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lm.append(mi.implied_lambda_mu(pH, pD, pA, pO, RHO0))
    return lm


def _nll(lam_mu, hg, ag, **shape):
    """-log-verosimiglianza dei punteggi osservati sotto la forma data."""
    tot = 0.0
    for (lam, mu), h, a in zip(lam_mu, hg, ag):
        M = mi.score_matrix(lam, mu, **shape)
        tot -= np.log(max(M[min(h, MAXG), min(a, MAXG)], 1e-15))
    return tot


def fit_rho(lam_mu, hg, ag):
    r = minimize_scalar(lambda rho: _nll(lam_mu, hg, ag, rho=rho),
                        bounds=(-0.2, 0.2), method="bounded")
    return {"rho": float(r.x)}


def fit_rho_phi(lam_mu, hg, ag):
    def f(x):
        return _nll(lam_mu, hg, ag, rho=x[0], diag_inflation=x[1])
    r = minimize(f, [RHO0, 0.05], method="L-BFGS-B",
                 bounds=[(-0.2, 0.2), (-0.3, 0.5)])
    return {"rho": float(r.x[0]), "diag_inflation": float(r.x[1])}


def fit_nb(lam_mu, hg, ag):
    # dispersione in log-scala per stabilita'; size grande ~ Poisson
    def f(logs):
        return _nll(lam_mu, hg, ag, rho=RHO0, nb_size=float(np.exp(logs)))
    r = minimize_scalar(f, bounds=(np.log(1.5), np.log(200.0)), method="bounded")
    return {"rho": RHO0, "nb_size": float(np.exp(r.x))}


BINARY = ["over_1.5", "over_3.5", "over_4.5", "btts"]


def eval_derived(lam_mu, hg, ag, **shape):
    """log-loss per-riga: risultato esatto, multigol, alcuni binari."""
    mats = [mi.score_matrix(lam, mu, **shape) for lam, mu in lam_mu]
    der = [mi.derive_markets(M) for M in mats]
    tot = hg + ag
    ex = np.array([-np.log(max(mats[k][min(hg[k], MAXG), min(ag[k], MAXG)], 1e-15))
                   for k in range(len(hg))])
    Pmg = np.array([[d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]] for d in der])
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    mg = -np.log(np.clip(Pmg[np.arange(len(ymg)), ymg], 1e-15, 1))
    out = {"risultato_esatto": ex, "multigol": mg}
    oc = {"over_1.5": tot >= 2, "over_3.5": tot >= 4, "over_4.5": tot >= 5,
          "btts": (hg >= 1) & (ag >= 1)}
    for mk in BINARY:
        p = np.array([d[mk] for d in der])
        y = oc[mk].astype(float)
        p = np.clip(p, 1e-15, 1 - 1e-15)
        out[mk] = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    return out


def boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5), (m < 0).mean()


def main():
    m = loader.load_league("serie_a")
    seasons = sorted(m["season"].unique())
    # inverti e prepara per stagione (solo stagioni con quote complete)
    per = {}
    for s in seasons:
        d = m[m["season"] == s]
        if not np.isfinite(d[["odds_home", "odds_draw", "odds_away",
                              "odds_over25", "odds_under25"]].to_numpy()).all():
            continue
        per[s] = dict(lm=invert(d), hg=d["home_goals"].to_numpy(),
                      ag=d["away_goals"].to_numpy())
    fp = experiment_log.data_fingerprint(m)

    SHAPES = {
        "rho=-0.06 (Fase 26)": ("fixed", dict(rho=RHO0)),
        "rho fittato": ("fit", fit_rho),
        "rho + phi (diag)": ("fit", fit_rho_phi),
        "binom. negativa": ("fit", fit_nb),
    }
    MK = ["risultato_esatto", "multigol"] + BINARY

    print("=" * 96)
    print("FORMA DEI PUNTEGGI sul market-implied — fittata walk-forward (lambda,mu dal mercato)")
    print("log-loss dei mercati derivati; piu' basso = meglio")
    print("=" * 96)

    # per ogni forma, raccogli le predizioni per-riga pooled sulle 6 stagioni di test
    results = {name: {mk: [] for mk in MK} for name in SHAPES}
    fitted_params = {name: [] for name in SHAPES}
    for s in TEST_SEASONS:
        past = [t for t in seasons if t < s and t in per]
        lm_tr = [x for t in past for x in per[t]["lm"]]
        hg_tr = np.concatenate([per[t]["hg"] for t in past])
        ag_tr = np.concatenate([per[t]["ag"] for t in past])
        d = per[s]
        for name, (kind, spec) in SHAPES.items():
            shape = spec if kind == "fixed" else spec(lm_tr, hg_tr, ag_tr)
            fitted_params[name].append(shape)
            ev = eval_derived(d["lm"], d["hg"], d["ag"], **shape)
            for mk in MK:
                results[name][mk].append(ev[mk])

    print(f"  {'forma':<22}" + "".join(f"{mk[:10]:>11}" for mk in MK))
    means = {}
    for name in SHAPES:
        row = {mk: np.concatenate(results[name][mk]).mean() for mk in MK}
        means[name] = row
        print(f"  {name:<22}" + "".join(f"{row[mk]:>11.4f}" for mk in MK))

    # Δ vs baseline Fase 26 (rho fisso), con CI sul risultato esatto e multigol
    base = "rho=-0.06 (Fase 26)"
    rng = np.random.default_rng(SEED)
    print(f"\n  Δ vs '{base}' (negativo = meglio); CI95 su risultato esatto e multigol:")
    for name in SHAPES:
        if name == base:
            continue
        parts = []
        for mk in ("risultato_esatto", "multigol"):
            d = (np.concatenate(results[name][mk])
                 - np.concatenate(results[base][mk]))
            mean, lo, hi, pneg = boot(d, rng)
            parts.append(f"{mk[:9]} {mean:+.4f} [{lo:+.4f},{hi:+.4f}]")
        print(f"    {name:<22} " + " | ".join(parts))

    # parametri fittati medi (diagnostica)
    print("\n  Parametri fittati (media sulle 6 tarature walk-forward):")
    for name in ("rho fittato", "rho + phi (diag)", "binom. negativa"):
        keys = fitted_params[name][0].keys()
        avg = {k: float(np.mean([fp_[k] for fp_ in fitted_params[name]])) for k in keys}
        print(f"    {name:<22} {avg}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase27_shape", "league": "serie_a", "variant": "shape_sweep",
         "bootstrap_B": B, "bootstrap_seed": SEED, "rho0": RHO0},
        {"n_matches": int(sum(len(per[s]["hg"]) for s in TEST_SEASONS)),
         **{f"{name.split()[0]}_{mk}": float(means[name][mk])
            for name in SHAPES for mk in MK}}, fp))

    print("\nNota: i lambda,mu restano quelli del mercato; qui si ottimizza SOLO la")
    print("forma della distribuzione attorno ad essi, imparata dai risultati passati.")


if __name__ == "__main__":
    main()
