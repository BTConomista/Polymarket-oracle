"""Fase 86 — Dispersione per-squadra sulla CODA (lead che corregge l'audit).

Domanda: alcune squadre sono piu' "tutto-o-niente" del punto-stima del mercato,
in modo STABILE nel tempo, e questo aiuta a prevedere i loro esiti rari?

Due misure:
 (1) PERSISTENZA della volatilita'-sorpresa per-squadra. Per ogni partita si
     inverte la chiusura 1X2+O/U nei lambda,mu del mercato e si calcola il
     RESIDUO = (diff-reti realizzata) - (lambda-mu atteso). La volatilita'-
     sorpresa di una squadra-stagione = std dei suoi residui. Si misura la
     correlazione stagione t -> t+1 (grezza e controllata per la forza).
 (2) theta OTTIMALE per terzile di volatilita'-sorpresa PASSATA (solo stagioni
     precedenti, quindi la classificazione e' out-of-sample): se le squadre ad
     alta volatilita' vogliono un theta piu' BASSO (coda piu' pesante), la
     dispersione per-squadra e' reale e direzionale.

Esito (Fase 86): la volatilita'-sorpresa PERSISTE (corr ~0.25, ~0.20 controllata
per la forza; fuori dalla banda nulla) — CONTRO la conclusione dell'audit
("non persiste"). E il gruppo ad alta volatilita' vuole theta*=1.10 vs 1.225 dei
bassi: dispersione per-squadra reale. E' un LEAD (segnale direzionale, theta di
gruppo scelto in-sample) da confermare con un walk-forward theta_team pieno.

NON registra run (diagnostico). Uso: python scripts/_run_team_dispersion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

K = 11
LEAGUES = ["serie_a", "premier_league", "la_liga"]
THETAS = [1.0, 1.10, 1.225, 1.35, 1.5]


def invert_all() -> pd.DataFrame:
    frames = [pd.read_csv(f"data/{lg}_matches.csv") for lg in LEAGUES]
    df = pd.concat(frames, ignore_index=True)
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25",
            "home_goals", "away_goals", "home_team", "away_team", "league", "season"]
    df = df.dropna(subset=need).reset_index(drop=True)
    rec = []
    for _, r in df.iterrows():
        pH, pD, pA = metrics.devig_1x2(r["odds_home"], r["odds_draw"], r["odds_away"])
        pO, _ = metrics.devig_binary(r["odds_over25"], r["odds_under25"])
        lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, rho=-0.06)
        resid = (r["home_goals"] - r["away_goals"]) - (lam - mu)
        rec.append((r["league"], int(r["season"]), r["home_team"], r["away_team"],
                    lam, mu, int(r["home_goals"]), int(r["away_goals"]), resid, abs(lam - mu)))
    return pd.DataFrame(rec, columns=["league", "season", "home", "away", "lam", "mu",
                                      "hg", "ag", "resid", "strength"])


def _team_seasons(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in d.iterrows():
        rows.append((r.league, r.season, r.home, r.resid, r.strength))
        rows.append((r.league, r.season, r.away, -r.resid, r.strength))
    t = pd.DataFrame(rows, columns=["league", "season", "team", "resid", "strength"])
    g = t.groupby(["league", "season", "team"]).agg(
        vol=("resid", "std"), n=("resid", "size"), stren=("strength", "mean")).reset_index()
    return g[g["n"] >= 10]


def persistence(g: pd.DataFrame) -> None:
    g = g.sort_values(["league", "team", "season"]).copy()
    b = np.polyfit(g["stren"], g["vol"], 1)
    g["vol_res"] = g["vol"] - (b[0] * g["stren"] + b[1])
    g["snext"] = g.groupby(["league", "team"])["season"].shift(-1)
    for c in ["vol", "vol_res"]:
        g[c + "_next"] = g.groupby(["league", "team"])[c].shift(-1)
    p = g.dropna(subset=["snext"])
    p = p[(p["snext"].astype("Int64").astype(int) - p["season"].astype(int)) == 101]
    rng = np.random.default_rng(0)
    print(f"corr(vol-sorpresa, forza) = {np.corrcoef(g['vol'], g['stren'])[0,1]:.3f}  "
          "(confondimento con la forza)")
    for c in ["vol", "vol_res"]:
        pp = p.dropna(subset=[c + "_next"])
        corr = np.corrcoef(pp[c], pp[c + "_next"])[0, 1]
        null = [np.corrcoef(pp[c], rng.permutation(pp[c + "_next"].to_numpy()))[0, 1]
                for _ in range(3000)]
        lo, hi = np.percentile(null, [2.5, 97.5])
        tag = "grezza" if c == "vol" else "controllata per forza"
        verdict = "PERSISTE" if (corr < lo or corr > hi) else "nella banda nulla"
        print(f"  persistenza {tag:22s}: corr={corr:+.4f} (n={len(pp)}) nulla=[{lo:+.3f},{hi:+.3f}] -> {verdict}")


def theta_by_group(d: pd.DataFrame, g: pd.DataFrame) -> None:
    vs = g[["league", "season", "team", "vol"]]

    def past_vol(lg, team, s):
        h = vs[(vs.league == lg) & (vs.team == team) & (vs.season < s)]["vol"]
        return h.mean() if len(h) else np.nan
    d = d.copy()
    d["pv_h"] = [past_vol(r.league, r.home, r.season) for r in d.itertuples()]
    d["pv_a"] = [past_vol(r.league, r.away, r.season) for r in d.itertuples()]
    d["pv"] = d[["pv_h", "pv_a"]].mean(axis=1)
    dd = d.dropna(subset=["pv"]).copy()
    q1, q2 = dd["pv"].quantile([1 / 3, 2 / 3])
    dd["grp"] = np.where(dd["pv"] <= q1, "low", np.where(dd["pv"] >= q2, "high", "mid"))

    def exact_ll(sub, theta):
        ll = 0.0
        for r in sub.itertuples():
            M = mi.score_matrix(r.lam, r.mu, rho=-0.06, dp_theta=theta)
            ll += -np.log(max(M[min(r.hg, K - 1), min(r.ag, K - 1)], 1e-15))
        return ll / len(sub)
    print(f"\ntheta* per terzile di volatilita'-sorpresa PASSATA (classif. OOS; n={len(dd)})")
    for grp in ["low", "mid", "high"]:
        sub = dd[dd["grp"] == grp]
        lls = {th: exact_ll(sub, None if th == 1.0 else th) for th in THETAS}
        best = min(lls, key=lls.get)
        print(f"  {grp:4s} (n={len(sub)}): theta*={best}  " +
              "  ".join(f"{th}:{lls[th]:.4f}" for th in THETAS))
    print("Alta volatilita' -> theta piu' BASSO = coda piu' pesante: dispersione per-squadra reale.")


def walk_forward(d: pd.DataFrame) -> None:
    """Verdetto OOS (Fase 86-bis): il theta per-squadra batte il theta globale?
    Per ogni stagione test s: si fitta il theta ottimo per terzile di
    volatilita'-sorpresa PASSATA sui dati < s, lo si applica a s, si accumula il
    log-loss del risultato esatto e lo si confronta col theta globale=1.225."""
    rows = []
    for _, r in d.iterrows():
        rows.append((r.league, r.season, r.home, r.resid))
        rows.append((r.league, r.season, r.away, -r.resid))
    tr = pd.DataFrame(rows, columns=["league", "season", "team", "resid"])
    vs = tr.groupby(["league", "season", "team"]).agg(
        vol=("resid", "std"), n=("resid", "size")).reset_index()
    vs = vs[vs["n"] >= 8]
    # indice past-vol: per (league, team) le vol delle stagioni, per media espandente
    idx = {}
    for _, r in vs.iterrows():
        idx.setdefault((r.league, r.team), []).append((r.season, r.vol))

    def past_vol(lg, team, s):
        h = [v for (ss, v) in idx.get((lg, team), []) if ss < s]
        return np.mean(h) if h else np.nan

    def pv_of(sub):
        return np.array([np.nanmean([past_vol(r.league, r.home, r.season),
                                     past_vol(r.league, r.away, r.season)])
                         for r in sub.itertuples()])

    def ll(sub, theta):
        s = 0.0
        for r in sub.itertuples():
            M = mi.score_matrix(r.lam, r.mu, rho=-0.06, dp_theta=(None if theta == 1.0 else theta))
            s += -np.log(max(M[min(r.hg, K - 1), min(r.ag, K - 1)], 1e-15))
        return s

    seasons = sorted(d["season"].unique())
    glob = team = 0.0; n = 0; log = []
    for s in seasons:
        past = d[d["season"] < s]
        if len(past) < 600:
            continue
        cur = d[d["season"] == s].copy(); cur["pv"] = pv_of(cur)
        cur = cur.dropna(subset=["pv"])
        pc = past.copy(); pc["pv"] = pv_of(pc); pc = pc.dropna(subset=["pv"])
        if len(cur) < 50 or len(pc) < 200:
            continue
        q1, q2 = pc["pv"].quantile([1 / 3, 2 / 3])
        grp = lambda v: "low" if v <= q1 else ("high" if v >= q2 else "mid")
        pc["g"] = pc["pv"].map(grp); cur["g"] = cur["pv"].map(grp)
        tg = {}
        for gname in ["low", "mid", "high"]:
            sub = pc[pc["g"] == gname]
            tg[gname] = min(THETAS, key=lambda th: ll(sub, th)) if len(sub) > 30 else 1.225
        for gname in ["low", "mid", "high"]:
            sub = cur[cur["g"] == gname]
            if len(sub):
                glob += ll(sub, 1.225); team += ll(sub, tg[gname]); n += len(sub)
        log.append((s, tg))
    print(f"\n=== Walk-forward θ_team vs θ globale=1.225 (Fase 86-bis, n={n} OOS) ===")
    print(f"  exact-LL globale   : {glob/n:.4f}")
    print(f"  exact-LL θ_team    : {team/n:.4f}")
    verdict = "MEGLIO" if team < glob else "PEGGIO (non sfruttabile OOS)"
    print(f"  Δ (team − globale) : {(team-glob)/n:+.5f}  -> {verdict}")
    for s, tg in log:
        print(f"    {s}: {tg}")


def main() -> None:
    d = invert_all()
    g = _team_seasons(d)
    print(f"partite invertite: {len(d)}  |  squadra-stagioni (>=10 gare): {len(g)}\n")
    persistence(g)
    theta_by_group(d, g)
    walk_forward(d)


if __name__ == "__main__":
    main()
