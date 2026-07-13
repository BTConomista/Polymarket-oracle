"""Fase 35 — Inflazione-pareggio condizionata all'EQUILIBRIO |lam-mu|.

Il punto centrale emerso dall'audit (Fase 34): le tre vie sul pareggio provate
finora hanno modellato solo il VOLUME dei gol attesi (tau di Dixon-Coles; phi
COSTANTE Fase 12b; rho DINAMICO sul totale lam+mu, Fase 18). Ma il pareggio e' un
fenomeno di EQUILIBRIO: due squadre pari-livello (|lam-mu| piccolo) pareggiano piu'
di quanto una Poisson preveda, a parita' di gol totali attesi. Il diagnostico D2
(Fase 34) ha mostrato il deficit di pareggio CONCENTRATO nelle partite equilibrate.

Questo script valida la Fase 35: phi(lam,mu)=phi0*exp(-kappa*|lam-mu|), fittato
nella verosimiglianza. Confronta ESPLICITAMENTE, sugli STESSI split walk-forward e
sulle STESSE partite (bootstrap appaiato per-riga):

    base (solo tau)  |  phi COSTANTE (Fase 12b)  |  rho DINAMICO (Fase 18)  |  phi(|lam-mu|) (Fase 35)

Metriche: 1X2 log-loss (headline), calibrazione del pareggio per quartile di
|lam-mu| (dove la Fase 35 dovrebbe agire), O/U come sanity check. Regola dichiarata
prima: la Fase 35 e' adottabile solo se batte la base con Δ<0 e CI95<0.

Uso:  python scripts/_run_draw_balance.py     (24 backtest walk-forward; ~minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402
from src.models.dixon_coles import DixonColesModel  # noqa: E402
from scripts.backtest import run_backtest, promoted_teams  # noqa: E402

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
VARIANTS = {
    "base":            {},
    "phi_costante":    {"draw_inflation": True},
    "rho_dinamico":    {"dynamic_rho": True},
    "phi_equilibrio":  {"draw_balance": True},
}
B, SEED = 10_000, 35
_IDX = {"H": 0, "D": 1, "A": 2}
CACHE = Path(__file__).resolve().parents[1] / "outputs"


def _worker(args):
    name, season = args
    fp = CACHE / f"db_{name}_{season}.csv"
    if fp.exists():
        return name, season, pd.read_csv(fp, parse_dates=["date"])
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False, **VARIANTS[name])
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return name, season, df


def _ll_1x2(df):
    P = np.clip(df[["m_home", "m_draw", "m_away"]].to_numpy(), 1e-15, 1)
    y = np.array([_IDX[o] for o in df.result])
    return -np.log(P[np.arange(len(y)), y])


def _market_1x2_ll(df):
    ll = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            ll[i] = -np.log(max(p[_IDX[r.result]], 1e-15))
    return ll


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    jobs = [(name, s) for name in VARIANTS for s in SEASONS]
    with Pool(4) as pool:            # 4 core reali: niente oversubscription
        res = pool.map(_worker, jobs)

    # Riordina: per variante, concat 6 stagioni (stesso ordine di partite -> appaiabile).
    by_var = {name: pd.concat([df for n, s, df in res if n == name], ignore_index=True)
              for name in VARIANTS}
    key = ["season", "home_team", "away_team"]
    base_df = by_var["base"].sort_values(key).reset_index(drop=True)
    n = len(base_df)
    ll = {name: _ll_1x2(by_var[name].sort_values(key).reset_index(drop=True)) for name in VARIANTS}
    mkt_ll = _market_1x2_ll(base_df)
    has_mkt = np.isfinite(mkt_ll)
    rng = np.random.default_rng(SEED)

    print("=" * 88)
    print(f"FASE 35 — pareggio condizionato a |lam-mu| ({n} partite, 6 stagioni walk-forward)")
    print("=" * 88)
    print(f"  mercato 1X2 log-loss (rif.) = {mkt_ll[has_mkt].mean():.4f}\n")
    print(f"  {'variante':<16}{'1X2 log-loss':>14}{'Δ vs base':>12}{'CI95 Δ':>22}{'P(mig)':>8}")
    summary = {}
    for name in VARIANTS:
        d = ll[name] - ll["base"]
        if name == "base":
            print(f"  {name:<16}{ll[name].mean():>14.4f}{'—':>12}{'—':>22}{'—':>8}")
            summary[name] = (float(ll[name].mean()), 0.0, 0.0, 0.0, 0.0)
            continue
        mean, lo, hi, pmig = _boot(d, rng)
        verd = " VIVA" if hi < 0 else (" promettente" if mean < 0 else "")
        print(f"  {name:<16}{ll[name].mean():>14.4f}{mean:>+12.4f}"
              f"   [{lo:+.4f}, {hi:+.4f}]{pmig:>8.0%}{verd}")
        summary[name] = (float(ll[name].mean()), mean, lo, hi, pmig)

    # --- Calibrazione del pareggio per quartile di |lam-mu| (dove agisce la Fase 35) ---
    print("\n" + "=" * 88)
    print("CALIBRAZIONE PAREGGIO per quartile |lam-mu| — P(pari): reale vs varianti vs mercato")
    print("=" * 88)
    b = by_var["base"].sort_values(key).reset_index(drop=True)
    bal = (b.exp_home_goals - b.exp_away_goals).abs()
    is_draw = (b.result == "D").astype(float).to_numpy()
    mkt_draw = np.full(n, np.nan)
    for i, r in enumerate(b.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            mkt_draw[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)[1]
    draws = {name: by_var[name].sort_values(key).reset_index(drop=True).m_draw.to_numpy()
             for name in VARIANTS}
    q = pd.qcut(bal, 4, labels=["equil", "medio-b", "medio-a", "sbil"])
    print(f"  {'quartile':<9}{'n':>5}{'reale':>8}{'base':>8}{'phiCost':>9}{'rhoDin':>8}"
          f"{'phiEq':>8}{'mercato':>9}")
    for lab in ["equil", "medio-b", "medio-a", "sbil"]:
        m = (q == lab).to_numpy()
        row = f"  {lab:<9}{m.sum():>5}{is_draw[m].mean():>8.3f}{draws['base'][m].mean():>8.3f}"
        row += f"{draws['phi_costante'][m].mean():>9.3f}{draws['rho_dinamico'][m].mean():>8.3f}"
        row += f"{draws['phi_equilibrio'][m].mean():>8.3f}"
        mm = m & np.isfinite(mkt_draw)
        row += f"{np.nanmean(mkt_draw[mm]):>9.3f}"
        print(row)

    # --- Parametri fittati (phi0, kappa) per stagione ---
    print("\n" + "=" * 88)
    print("PARAMETRI FITTATI phi(lam,mu)=phi0*exp(-kappa*|lam-mu|) — un fit a inizio stagione")
    print("=" * 88)
    all_m = loader.load_league("serie_a")
    phi0s, kappas = [], []
    for s in SEASONS:
        cur = all_m[all_m.season.astype(str) == s]
        as_of = cur.date.min()
        prom = promoted_teams(all_m, s)
        mdl = DixonColesModel(half_life_days=CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                              shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                              promoted_prior=CFG["promoted_prior"], draw_balance=True)
        mdl.fit(all_m, as_of_date=as_of, promoted_teams=prom)
        phi0s.append(mdl.draw_phi0); kappas.append(mdl.draw_kappa)
        print(f"  {s}:  phi0={mdl.draw_phi0:.3f}  kappa={mdl.draw_kappa:.3f}")
    print(f"  media: phi0={np.mean(phi0s):.3f}  kappa={np.mean(kappas):.3f}  "
          f"(a squadre pari-livello il boost pareggio e' ~{np.mean(phi0s)*100:.0f}%)")

    # --- Registro ---
    fp = experiment_log.data_fingerprint(all_m)
    for name in VARIANTS:
        rec_cfg = {"source": "fase35_draw_balance", "league": "serie_a", "variant": name,
                   **{k: v for k, v in CFG.items() if k != "promoted_prior"},
                   "promoted_prior": 0.23}
        experiment_log.append_run(experiment_log.make_record(
            rec_cfg, {"n_matches": n, "x2_model_logloss": summary[name][0],
                      "delta_vs_base": summary[name][1], "ci_lo": summary[name][2],
                      "ci_hi": summary[name][3], "p_improve": summary[name][4],
                      "phi0_mean": float(np.mean(phi0s)) if name == "phi_equilibrio" else None,
                      "kappa_mean": float(np.mean(kappas)) if name == "phi_equilibrio" else None},
            fp))
    print("\nRun registrati in experiments/runs.jsonl (source=fase35_draw_balance).")


if __name__ == "__main__":
    main()
