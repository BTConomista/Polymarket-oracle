"""Fase 75 — Spremere il 2017-19: apertura REALE (1X2+O/U) + chiusura STIMATA.

Dopo la Fase 73 il 2017-19 ha: apertura 1X2 (Pinnacle PS*) e apertura O/U
(Betbrain BbAv) REALI; chiusura 1X2 reale (PSC*); chiusura O/U STIMATA
(E3 pooled, data/estimates/). Richiesta utente: trattare questo blocco come
terreno di caccia e spremerlo in ogni direzione. Quattro esperimenti:

A. MOTORE market-implied dall'APERTURA — tutto reale, ZERO stime.
   Il market-implied non richiede training (inverte le quote): le 6
   lega-stagioni nuove (1718/1819 x SA/PL/Liga, ~4560 partite) sono un
   test-set VERGINE per il motore. Confronto su 20 mercati Tier 1:
   baseline in-sample vs MI-Poisson vs MI-dp(θ=1.225 — fittato sul 2019+,
   quindi qui PURO out-of-sample).

B. La SOTTO-DISPERSIONE (θ>1, Fasi 51/52/53) esisteva già nel 2017-19?
   fit di θ per (lega, stagione) sui tassi dell'apertura. Se θ>1 anche qui
   (dati mai visti da nessun fit), la dp è una proprietà strutturale, non un
   artefatto della finestra 2019+.

C. Il DC contro la chiusura STIMATA (benchmark DICHIARATO, 1819 Serie A).
   Caveat esplicito: la stima è costruita da informazione di mercato
   (apertura + movimento 1X2) → confronto parzialmente circolare, il gap
   esce gonfiato rispetto a un closing indipendente. Mai ROI.

D. ENCOMPASSING esteso al 1819:
   D1 (REALE)   1X2: blend a*DC+(1-a)*closing Pinnacle vero → a*?
                (estende la Fase 16, che usava il 2021+, a una stagione nuova)
   D2 (STIMA)   O/U: blend a*DC+(1-a)*chiusura stimata → a*?
                (se a*≈0 perfino contro una RICOSTRUZIONE, il tetto
                informativo è ancora più stringente)

Uso:  python scripts/_run_fase75_squeeze_2017_19.py
      (richiede outputs/db_base_1819.csv per C/D — scripts/_gen_cache.py)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database                        # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from scripts._fase52_common import fit_theta, ll_bin  # noqa: E402
from scripts._run_fase52_router3 import _MKTS         # noqa: E402

B, SEED = 10_000, 75
RHO = -0.06                  # costante del motore (Fase 24/26)
DP_THETA = 1.225             # θ del router adottato (Fase 52, fit 2019+)
LEAGUES = ["serie_a", "premier_league", "la_liga"]
NEW_SEASONS = ["1718", "1819"]
CACHE = Path(__file__).resolve().parents[1] / "outputs"
EST_FP = Path(__file__).resolve().parents[1] / "data" / "estimates" / "ou_close_2017_19.csv"

_OPEN = ["odds_home_open", "odds_draw_open", "odds_away_open",
         "odds_over25_open", "odds_under25_open"]


def _boot(diff: np.ndarray, rng) -> tuple[float, float, float, float]:
    n = len(diff)
    boots = diff[rng.integers(0, n, size=(B, n))].mean(axis=1)
    return (float(diff.mean()), float(np.percentile(boots, 2.5)),
            float(np.percentile(boots, 97.5)), float((boots < 0).mean()))


def _load_open() -> pd.DataFrame:
    frames = []
    for lg in LEAGUES:
        df = database.read_snapshot(database.snapshot_path(lg))
        df["season"] = df["season"].astype(str)
        df = df[df["season"].isin(NEW_SEASONS)].dropna(subset=_OPEN).copy()
        df["league"] = lg
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    p1 = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                     r.odds_away_open) for r in out.itertuples()])
    out[["pH_o", "pD_o", "pA_o"]] = p1
    out["pO_o"] = [metrics.devig_binary(r.odds_over25_open, r.odds_under25_open)[0]
                   for r in out.itertuples()]
    return out


def part_A_B(df: pd.DataFrame, rng) -> dict:
    t0 = time.time()
    # inversione apertura -> lam,mu (reale) per ogni riga
    lam = np.empty(len(df)); mu = np.empty(len(df))
    for i, r in enumerate(df.itertuples()):
        lam[i], mu[i] = mi.implied_lambda_mu(r.pH_o, r.pD_o, r.pA_o, r.pO_o, RHO)
    df = df.assign(lam=lam, mu=mu)
    print(f"  inversioni: {len(df)} righe ({time.time()-t0:.0f}s)")

    hg = df["home_goals"].to_numpy(int); ag = df["away_goals"].to_numpy(int)

    # ---- A: pricing Poisson vs dp(1.225) vs baseline in-sample -------------
    prices_poi = [mi.price_markets(l, m, RHO) for l, m in zip(lam, mu)]
    prices_dp = [mi.price_markets(l, m, RHO, dp_theta=DP_THETA)
                 for l, m in zip(lam, mu)]
    res_A = {}
    print(f"\n  {'mercato':14s} {'base':>7s} {'MI-poi':>7s} {'MI-dp':>7s} "
          f"{'d dp-poi':>22s} {'d poi-base':>22s}")
    means = {"base": [], "poi": [], "dp": []}
    for mk, (label_fn, _fam) in _MKTS.items():
        y = label_fn(hg, ag).astype(float)
        p_poi = np.array([p[mk] for p in prices_poi])
        p_dp = np.array([p[mk] for p in prices_dp])
        # baseline in-sample per (lega, stagione) — dichiarata (come backtest core)
        p_base = np.empty(len(df))
        for (lg, s), g in df.groupby(["league", "season"]):
            idx = g.index.to_numpy()
            p_base[idx] = y[idx].mean()
        ll_b, ll_p, ll_d = ll_bin(p_base, y), ll_bin(p_poi, y), ll_bin(p_dp, y)
        d_dp = _boot(ll_d - ll_p, rng)
        d_pb = _boot(ll_p - ll_b, rng)
        res_A[mk] = {"ll_base": float(ll_b.mean()), "ll_poi": float(ll_p.mean()),
                     "ll_dp": float(ll_d.mean()), "d_dp_poi": d_dp,
                     "d_poi_base": d_pb}
        for k, v in (("base", ll_b), ("poi", ll_p), ("dp", ll_d)):
            means[k].append(float(v.mean()))
        flag = "✓" if d_pb[2] < 0 else " "
        flag2 = "✓" if d_dp[2] < 0 else (" " if d_dp[1] < 0 else "!")
        print(f"  {mk:14s} {ll_b.mean():7.4f} {ll_p.mean():7.4f} {ll_d.mean():7.4f} "
              f"{d_dp[0]:+.4f} [{d_dp[1]:+.4f},{d_dp[2]:+.4f}]{flag2} "
              f"{d_pb[0]:+.4f} [{d_pb[1]:+.4f},{d_pb[2]:+.4f}]{flag}")
    print(f"  {'MEDIA 20 mkt':14s} {np.mean(means['base']):7.4f} "
          f"{np.mean(means['poi']):7.4f} {np.mean(means['dp']):7.4f}")
    res_A["_means"] = {k: float(np.mean(v)) for k, v in means.items()}

    # ---- B: θ per (lega, stagione) sui tassi di apertura -------------------
    print("\n  θ double-Poisson sui tassi dell'APERTURA (fit per lega-stagione):")
    res_B = {}
    for (lg, s), g in df.groupby(["league", "season"]):
        th = fit_theta(g["lam"].to_numpy(), g["mu"].to_numpy(),
                       g["home_goals"].to_numpy(int), g["away_goals"].to_numpy(int))
        res_B[f"{lg}_{s}"] = round(th, 3)
        print(f"    {lg:16s} {s}: θ = {th:.3f}")
    for lg in LEAGUES:
        g = df[df["league"] == lg]
        th = fit_theta(g["lam"].to_numpy(), g["mu"].to_numpy(),
                       g["home_goals"].to_numpy(int), g["away_goals"].to_numpy(int))
        res_B[f"{lg}_pooled"] = round(th, 3)
        print(f"    {lg:16s} 1718+1819 pooled: θ = {th:.3f}")
    return {"A": res_A, "B": res_B}


def part_C_D(rng) -> dict:
    cache_fp = CACHE / "db_base_1819.csv"
    if not cache_fp.exists():
        print("  cache db_base_1819 assente: salto C/D (lanciare _gen_cache.py)")
        return {}
    c = pd.read_csv(cache_fp)
    est = pd.read_csv(EST_FP)
    est = est[(est["league"] == "serie_a") & (est["season"].astype(str) == "1819")]
    m = c.merge(est[["home_team", "away_team", "p_over25_close_est"]],
                on=["home_team", "away_team"], how="inner")
    y_ou = m["is_over"].to_numpy(float)
    out = {}

    # ---- C: DC vs chiusura STIMATA (benchmark dichiarato) ------------------
    ll_dc = ll_bin(m["m_over"].to_numpy(), y_ou)
    ll_est = ll_bin(m["p_over25_close_est"].to_numpy(), y_ou)
    d = _boot(ll_dc - ll_est, rng)
    out["C_gap_dc_vs_stima"] = d
    print(f"\n  C. O/U 1819 SA (n={len(m)}): DC {ll_dc.mean():.4f} vs "
          f"stima-chiusura {ll_est.mean():.4f} → gap {d[0]:+.4f} "
          f"[{d[1]:+.4f},{d[2]:+.4f}]  (⚠️ benchmark STIMATO, parz. circolare)")

    # ---- D2: encompassing O/U con la STIMA ---------------------------------
    alphas = np.linspace(0, 1, 21)
    lls = [ll_bin(a * m["m_over"].to_numpy()
                  + (1 - a) * m["p_over25_close_est"].to_numpy(), y_ou).mean()
           for a in alphas]
    a_star_ou = float(alphas[int(np.argmin(lls))])
    out["D2_alpha_ou_stima"] = a_star_ou
    print(f"  D2. blend a*DC+(1-a)*STIMA (O/U): a* = {a_star_ou:.2f} "
          f"(LL {min(lls):.4f})")

    # ---- D1: encompassing 1X2 col closing Pinnacle REALE -------------------
    ok = m[["odds_home", "odds_draw", "odds_away"]].notna().all(axis=1)
    mm = m[ok]
    pmkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                     for r in mm.itertuples()])
    pdc = mm[["m_home", "m_draw", "m_away"]].to_numpy()
    y3 = pd.get_dummies(mm["result"])[["H", "D", "A"]].to_numpy(float)
    lls3 = []
    for a in alphas:
        p = a * pdc + (1 - a) * pmkt
        p = p / p.sum(axis=1, keepdims=True)
        lls3.append(float(-(y3 * np.log(np.clip(p, 1e-15, None))).sum(axis=1).mean()))
    a_star_1x2 = float(alphas[int(np.argmin(lls3))])
    out["D1_alpha_1x2_reale"] = a_star_1x2
    ll_dc3 = lls3[-1]; ll_mkt3 = lls3[0]
    print(f"  D1. blend a*DC+(1-a)*closing Pinnacle VERO (1X2, n={len(mm)}): "
          f"a* = {a_star_1x2:.2f}  (DC {ll_dc3:.4f}, mercato {ll_mkt3:.4f}, "
          f"blend {min(lls3):.4f})")
    return out


def main() -> None:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    df = _load_open()
    print(f"Partite 2017-19 con apertura 1X2+O/U REALE completa: {len(df)} "
          f"({df.groupby('league').size().to_dict()})")

    res = part_A_B(df, rng)
    res_cd = part_C_D(rng)
    res.update(res_cd)

    fingerprint = experiment_log.data_fingerprint(df)
    experiment_log.append_run(experiment_log.make_record(
        config={"source": "fase75_squeeze_2017_19", "rho": RHO,
                "dp_theta": DP_THETA, "seasons": NEW_SEASONS,
                "leagues": LEAGUES, "bootstrap_B": B, "seed": SEED,
                "note": ("A/B: apertura REALE (zero stime); C/D2: chiusura "
                         "STIMATA dichiarata (mai ROI); D1: closing 1X2 reale")},
        metrics_dict={k: v for k, v in res.items()},
        fingerprint=fingerprint,
    ))
    print(f"\nRegistrato in runs.jsonl (source=fase75_squeeze_2017_19). "
          f"Totale {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
