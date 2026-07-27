"""Il router double-Poisson (θ) sulle DUE LEGHE NUOVE, scelto per GRIGLIA.

PERCHE'
-------
Il progetto ha gia' scoperto (confronto F53 vs F81 sulla Liga) che il θ stimato
per MASSIMA VEROSIMIGLIANZA sui punteggi e quello scelto per GRIGLIA sulla
metrica che conta sono DUE COSE DIVERSE: sulla Liga il primo (1.097) non
produceva guadagno, il secondo (≈1.2) ha ribaltato la bocciatura.

Sulle leghe nuove (bundesliga, ligue_1) finora e' stato misurato SOLO il θ
debole (fit_theta = MLE sui punteggi: 1.080 e 1.103). Qui si rifa' per griglia.

CHE COSA FA
-----------
1. Carica gli snapshot delle 5 leghe (7 stagioni con chiusura O/U reale,
   1920→2526) e inverte la chiusura 1X2+O/U nei tassi (λ, μ) del mercato con il
   codice di PRODUZIONE (`metrics.devig_*` + `mi.implied_lambda_mu`, ρ=−0.06).
2. Griglia θ ∈ {1.000, 1.025, …, 1.400} (+1.50 per la replica F81) applicata via
   `mi.price_markets(lam, mu, rho, dp_theta=θ)` a TUTTO il listino Tier 1
   (25 mercati), NON solo all'1X2. Riferimento: il router Poisson (dp_theta=None).
3. Scelta di θ FUORI CAMPIONE:
   - LOSO  (leave-one-season-out): θ scelto sulle altre 6 stagioni, valutato
     sulla settima → tutte e 7 le stagioni sono test;
   - LFO   (leave-future-out, come F81): θ scelto sulle stagioni PASSATE →
     6 stagioni di test.
   La curva in-sample e' riportata solo per far vedere la differenza.
4. Bootstrap appaiato B=10.000 (`_fase52_common.boot`) su ogni mercato.
5. CONTROLLO DI SANITA' OBBLIGATORIO: replica esatta dell'asse θ della Fase 81
   (griglia 1.00…1.50 passo 0.05, selettore lfo, test 2021→2526) su serie_a e
   la_liga, e confronto con i numeri pubblicati in docs/PANCHINA.md.

Metriche: log-loss per riga, calcolata con le stesse formule di
`scripts/_run_market_implied.ll_bin` / `_run_fase81_mega_sweep_mi._row_ll`.
Bootstrap: `scripts/_fase52_common.boot` (fonte del progetto).

Uso:  python scripts/leve_theta_griglia.py [--leagues ...] [--jobs 2]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scripts import _fase52_common as C            # noqa: E402
from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
CACHE = Path(os.environ.get(
    "SCRATCH",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")) / "theta_griglia"

SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "data",
        "ligue_1": ROOT / "data"}
LEAGUES = ["bundesliga", "ligue_1", "serie_a", "premier_league", "la_liga"]

SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06
MAXG = mi.MAX_GOALS
SEED = 1225                      # nessun significato oltre la riproducibilita'

# Griglia fine (il compito) + 1.50 che serve solo alla replica della Fase 81.
GRID = [round(1.0 + 0.025 * i, 3) for i in range(17)]        # 1.000 … 1.400
GRID81 = [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50]
THETAS = sorted(set(GRID) | set(GRID81))

# --------------------------------------------------------------------------- #
# Il listino Tier 1: 22 mercati binari + 1X2 + multigol + risultato esatto.
# I nomi delle probabilita' sono le chiavi di `mi.derive_markets`; gli esiti
# ricalcano `_run_market_implied._binary_outcomes` e `_run_fase52_router3._MKTS`.
# --------------------------------------------------------------------------- #
BIN_MARKETS: list[tuple[str, object]] = [
    ("home_win",      lambda h, a: h > a),
    ("draw",          lambda h, a: h == a),
    ("away_win",      lambda h, a: a > h),
    ("dc_1x",         lambda h, a: h >= a),
    ("dc_2x",         lambda h, a: a >= h),
    ("over_0.5",      lambda h, a: h + a >= 1),
    ("over_1.5",      lambda h, a: h + a >= 2),
    ("over_2.5",      lambda h, a: h + a >= 3),
    ("over_3.5",      lambda h, a: h + a >= 4),
    ("over_4.5",      lambda h, a: h + a >= 5),
    ("btts",          lambda h, a: (h >= 1) & (a >= 1)),
    ("home_ov_0.5",   lambda h, a: h >= 1),
    ("home_ov_1.5",   lambda h, a: h >= 2),
    ("away_ov_0.5",   lambda h, a: a >= 1),
    ("away_ov_1.5",   lambda h, a: a >= 2),
    ("odd_total",     lambda h, a: (h + a) % 2 == 1),
    ("home_by_2plus", lambda h, a: h - a >= 2),
    ("away_by_2plus", lambda h, a: a - h >= 2),
    ("cs_home",       lambda h, a: a == 0),
    ("cs_away",       lambda h, a: h == 0),
    ("wtn_home",      lambda h, a: (h > 0) & (a == 0)),
    ("wtn_away",      lambda h, a: (a > 0) & (h == 0)),
]
MARKETS = [m for m, _ in BIN_MARKETS] + ["1X2", "multigol", "risultato_esatto"]
# I 6 mercati dell'asse θ della Fase 81 (LAB: cs = RISULTATO ESATTO, non
# clean-sheet: attenzione, e' una fonte di equivoci).
MK81 = {"x2": "1X2", "gg": "btts", "draw": "draw", "cs": "risultato_esatto",
        "mg": "multigol", "ou": "over_2.5"}


# ----------------------------------------------------------------- dati ---- #
def carica(league: str) -> pd.DataFrame:
    df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df = df[df.season.isin(SEASONS)]
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    df = df.dropna(subset=need)
    return df.sort_values("date").reset_index(drop=True)


def inverti(df: pd.DataFrame, league: str) -> tuple[np.ndarray, np.ndarray]:
    """(λ, μ) impliciti nella chiusura, motore di produzione. Cache su scratch."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"rates_{league}_rho{RHO:+.2f}.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(df):
            return c["lam"].to_numpy(), c["mu"].to_numpy()
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


# ------------------------------------------------------------ log-loss ----- #
def ll_bin(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def eval_theta(lam, mu, hg, ag, theta: float | None) -> dict[str, np.ndarray]:
    """LL per-riga di ogni mercato del listino, prezzato dal router di
    produzione `price_markets` (phi0=0 → matrice unica) con `dp_theta=theta`.
    theta=None (o 1.0) = router Poisson di riferimento."""
    n = len(lam)
    th = None if (theta is None or theta == 1.0) else float(theta)
    prob = {m: np.zeros(n) for m, _ in BIN_MARKETS}
    p3 = np.zeros((n, 3)); pmg = np.zeros((n, 3)); ex = np.zeros(n)
    for i in range(n):
        d = mi.price_markets(float(lam[i]), float(mu[i]), RHO, dp_theta=th)
        for m, _ in BIN_MARKETS:
            prob[m][i] = d[m]
        p3[i] = (d["home_win"], d["draw"], d["away_win"])
        pmg[i] = (d["mg_0_1"], d["mg_2_3"], d["mg_4plus"])
        M = d["score_matrix"]
        ex[i] = -np.log(max(M[min(hg[i], MAXG), min(ag[i], MAXG)], 1e-15))
    out = {m: ll_bin(prob[m], f(hg, ag).astype(float)) for m, f in BIN_MARKETS}
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
    P3 = p3 / p3.sum(axis=1, keepdims=True)
    out["1X2"] = -np.log(np.clip(P3[np.arange(n), y3], 1e-15, None))
    tot = hg + ag
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    out["multigol"] = -np.log(np.clip(pmg[np.arange(n), ymg], 1e-15, None))
    out["risultato_esatto"] = ex
    return out


# ---------------------------------------------------------- selettori ------ #
def pick_loso(lls: dict, thetas: list, seasons: np.ndarray, mk: str):
    """Per ogni stagione s: θ col LL medio migliore sulle ALTRE 6. Ritorna
    (ll_scelto_per_riga, {stagione: θ})."""
    sel = np.zeros(len(seasons)); picks = {}
    for s in SEASONS:
        tr = seasons != s; cur = seasons == s
        if not cur.any():
            continue
        best = min(thetas, key=lambda t: lls[t][mk][tr].mean())
        picks[s] = best
        sel[cur] = lls[best][mk][cur]
    return sel, picks


def pick_lfo(lls: dict, thetas: list, seasons: np.ndarray, mk: str, ref):
    """Selettore walk-forward della Fase 81: per la stagione i>0 si sceglie θ
    sulle stagioni PASSATE. La prima stagione non e' di test."""
    sel = np.zeros(len(seasons)); picks = {}
    test = np.zeros(len(seasons), bool)
    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = np.isin(seasons, SEASONS[:i]); cur = seasons == s
        if not cur.any():
            continue
        best = ref if not past.any() else min(
            thetas, key=lambda t: lls[t][mk][past].mean())
        picks[s] = best
        sel[cur] = lls[best][mk][cur]
        test |= cur
    return sel, picks, test


def boot_e(d: np.ndarray, rng) -> tuple[float, float, float, float]:
    """`_fase52_common.boot` + p-value a due code. Caso degenere: se il
    selettore ha scelto ovunque θ=1.0 la differenza e' identicamente nulla —
    non e' un risultato «p=0», e' «nessuna differenza» (p=1)."""
    if not np.any(d):
        return 0.0, 0.0, 0.0, 1.0
    mean, lo, hi, p_neg = C.boot(d, rng)
    return mean, lo, hi, float(2.0 * min(p_neg, 1.0 - p_neg))


# ------------------------------------------------------------- lega -------- #
def run_league(league: str) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    df = carica(league)
    lam, mu = inverti(df, league)
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    seasons = df.season.to_numpy()
    n = len(df)

    lls = {t: eval_theta(lam, mu, hg, ag, t) for t in THETAS}
    ref = lls[1.0]                       # router Poisson (dp_theta=None)
    ref_check = eval_theta(lam, mu, hg, ag, None)
    coerente = all(np.allclose(ref[m], ref_check[m]) for m in MARKETS)

    res = {"n": n, "stagioni": sorted(set(seasons)),
           "theta_1_uguale_poisson": bool(coerente), "mercati": {}}

    # --- θ MLE sui punteggi (il metodo "debole"), LOSO + pooled -------------- #
    mle = {s: float(C.fit_theta(lam[seasons != s], mu[seasons != s],
                                hg[seasons != s], ag[seasons != s], RHO))
           for s in sorted(set(seasons))}
    res["theta_mle_pooled"] = float(C.fit_theta(lam, mu, hg, ag, RHO))
    res["theta_mle_loso"] = mle

    # --- curve in-sample (pooled 7 stagioni) -------------------------------- #
    res["curve_in_sample"] = {
        m: {str(t): float(lls[t][m].mean()) for t in GRID} for m in MARKETS}
    res["theta_best_in_sample"] = {
        m: float(min(GRID, key=lambda t: lls[t][m].mean())) for m in MARKETS}

    # --- LOSO / LFO per mercato --------------------------------------------- #
    for m in MARKETS:
        sel, picks = pick_loso(lls, GRID, seasons, m)
        d = sel - ref[m]
        mean, lo, hi, p2 = boot_e(d, rng)
        stag = {s: float((sel[seasons == s] - ref[m][seasons == s]).mean())
                for s in sorted(set(seasons))}
        sel_f, picks_f, test_f = pick_lfo(lls, GRID, seasons, m, 1.0)
        df_ = sel_f[test_f] - ref[m][test_f]
        mf, lof, hif, p2f = boot_e(df_, rng)
        res["mercati"][m] = {
            "ll_poisson": float(ref[m].mean()),
            "loso": {"theta_per_stagione": {k: float(v) for k, v in picks.items()},
                     "ll": float(sel.mean()), "delta": mean,
                     "ci95": [lo, hi], "p_due_code": p2,
                     "stagioni_migliorate": int(sum(v < 0 for v in stag.values())),
                     "delta_per_stagione": stag},
            "lfo": {"theta_per_stagione": {k: float(v) for k, v in picks_f.items()},
                    "delta": mf, "ci95": [lof, hif], "p_due_code": p2f},
        }

    # --- UN SOLO θ per lega (come il router v3 in produzione) --------------- #
    # criterio di scelta LOSO sull'1X2 (metrica principale del progetto) e,
    # in alternativa, sul risultato esatto (≈ la MLE: stessa verosimiglianza).
    for crit in ("1X2", "risultato_esatto"):
        _, picks = pick_loso(lls, GRID, seasons, crit)
        blocco = {"theta_per_stagione": {k: float(v) for k, v in picks.items()},
                  "mercati": {}}
        for m in MARKETS:
            sel = np.zeros(n)
            for s, t in picks.items():
                cur = seasons == s
                sel[cur] = lls[t][m][cur]
            d = sel - ref[m]
            mean, lo, hi, p2 = boot_e(d, rng)
            blocco["mercati"][m] = {"delta": mean, "ci95": [lo, hi],
                                    "p_due_code": p2}
        res[f"theta_unico_loso_su_{crit}"] = blocco

    # --- replica ESATTA dell'asse θ della Fase 81 (controllo di sanita') ----- #
    rep = {}
    for tag, m in MK81.items():
        sel, picks, test = pick_lfo(lls, GRID81, seasons, m, 1.00)
        d = sel[test] - ref[m][test]
        mean, lo, hi, p2 = boot_e(d, rng)
        best = min(GRID81, key=lambda t: lls[t][m][test].mean())
        rep[tag] = {"mercato": m, "lfo_delta": mean, "ci95": [lo, hi],
                    "p_due_code": p2,
                    "picks": {k: float(v) for k, v in picks.items()},
                    "best_in_sample_test": float(best),
                    "ll_ref_test": float(ref[m][test].mean())}
    res["replica_fase81"] = rep
    res["secondi"] = round(time.time() - t0, 1)
    return res


def _worker(league):
    return league, run_league(league)


# ------------------------------------------- modalita' «θ FISSO importato» -- #
# Test PIU' SEVERO del LOSO: nessuna selezione, nemmeno fuori campione. Si
# prende una costante decisa ALTROVE (θ=1.225 e' quella di produzione, tarata
# sulla Serie A) e la si applica tale e quale. Se il router vale davvero come
# proprieta' del calcio, deve pagare anche cosi'; se paga solo col selettore,
# il guadagno e' (in parte) il selettore che pesca il rumore.
THETA_FISSI = [1.10, 1.15, 1.20, 1.225, 1.25, 1.30]


def run_league_fisso(league: str) -> dict:
    rng = np.random.default_rng(SEED)
    df = carica(league)
    lam, mu = inverti(df, league)
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    ref = eval_theta(lam, mu, hg, ag, None)
    out = {}
    for t in THETA_FISSI:
        ll = eval_theta(lam, mu, hg, ag, t)
        blocco = {}
        for m in MARKETS:
            mean, lo, hi, p2 = boot_e(ll[m] - ref[m], rng)
            blocco[m] = {"delta": mean, "ci95": [lo, hi], "p_due_code": p2}
        out[str(t)] = blocco
    return out


def _worker_fisso(league):
    return league, run_league_fisso(league)


# -------------------------------------------------------------- report ----- #
def stampa(league: str, r: dict) -> None:
    print("\n" + "=" * 100)
    print(f"{league.upper()}  —  {r['n']} partite, {len(r['stagioni'])} stagioni "
          f"({r['stagioni'][0]}→{r['stagioni'][-1]}), ρ={RHO}")
    print("=" * 100)
    print(f"  θ=1.000 riproduce il router Poisson: {r['theta_1_uguale_poisson']}")
    print(f"  θ MLE sui punteggi (metodo debole): pooled {r['theta_mle_pooled']:.3f}"
          f"   LOSO [{min(r['theta_mle_loso'].values()):.3f}, "
          f"{max(r['theta_mle_loso'].values()):.3f}]")
    bis = r["theta_best_in_sample"]
    print(f"  θ ottimo IN-SAMPLE per griglia: 1X2 {bis['1X2']:.3f} | "
          f"ris.esatto {bis['risultato_esatto']:.3f} | GG {bis['btts']:.3f} | "
          f"O/U2.5 {bis['over_2.5']:.3f} | cs_home {bis['cs_home']:.3f}")
    print(f"\n  {'mercato':<17}{'LL Poisson':>11}{'θ LOSO':>16}"
          f"{'Δ LOSO':>10}{'CI95':>22}{'p2':>8}{'st.+':>6}{'Δ LFO':>10}")
    for m in MARKETS:
        b = r["mercati"][m]
        ts = sorted(set(b["loso"]["theta_per_stagione"].values()))
        rng_t = f"{ts[0]:.3f}-{ts[-1]:.3f}" if len(ts) > 1 else f"{ts[0]:.3f}"
        lo, hi = b["loso"]["ci95"]
        flag = "*" if hi < 0 else ("!" if lo > 0 else " ")
        print(f"  {m:<17}{b['ll_poisson']:>11.4f}{rng_t:>16}"
              f"{b['loso']['delta']:>+10.4f}  [{lo:+.4f},{hi:+.4f}]"
              f"{b['loso']['p_due_code']:>8.3f}{b['loso']['stagioni_migliorate']:>4}/7"
              f"{b['lfo']['delta']:>+10.4f} {flag}")
    for crit in ("1X2", "risultato_esatto"):
        blk = r[f"theta_unico_loso_su_{crit}"]
        ts = sorted(set(blk["theta_per_stagione"].values()))
        conc = [m for m in MARKETS if blk["mercati"][m]["ci95"][1] < 0]
        peg = [m for m in MARKETS if blk["mercati"][m]["ci95"][0] > 0]
        print(f"\n  θ UNICO scelto LOSO su «{crit}» "
              f"(θ ∈ [{ts[0]:.3f}, {ts[-1]:.3f}]): "
              f"mercati con CI95 sotto zero {len(conc)}/{len(MARKETS)} "
              f"{conc if conc else ''}")
        if peg:
            print(f"      peggiora con CI95 sopra zero: {peg}")
    print("\n  [replica Fase 81 — griglia 1.00…1.50, selettore lfo, test 2021→2526]")
    for tag, v in r["replica_fase81"].items():
        lo, hi = v["ci95"]
        print(f"    {tag:<6}({v['mercato']:<17}) Δ {v['lfo_delta']:+.4f} "
              f"[{lo:+.4f},{hi:+.4f}] p2={v['p_due_code']:.3f} "
              f"picks={list(v['picks'].values())}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--modo", choices=["griglia", "fisso"], default="griglia")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leve_theta_griglia.json"

    t0 = time.time()
    if args.modo == "fisso":
        with Pool(min(args.jobs, len(args.leagues))) as pool:
            fissi = dict(pool.map(_worker_fisso, args.leagues))
        prev = json.loads(path.read_text()) if path.exists() else {}
        for lg, blk in fissi.items():
            print(f"\n=== θ FISSO (nessuna selezione) — {lg} ===")
            print(f"  {'mercato':<17}" + "".join(f"{t:>11}" for t in THETA_FISSI))
            for m in MARKETS:
                riga = f"  {m:<17}"
                for t in THETA_FISSI:
                    v = blk[str(t)][m]
                    fl = "*" if v["ci95"][1] < 0 else ("!" if v["ci95"][0] > 0 else " ")
                    riga += f"{v['delta']:>+10.4f}{fl}"
                print(riga)
            prev.setdefault(lg, {})["theta_fissi"] = blk
        prev.setdefault("_meta", {})["theta_fissi"] = THETA_FISSI
        path.write_text(json.dumps(prev, indent=2, default=str))
        print(f"\n-> {path.relative_to(ROOT)}   ({time.time()-t0:.0f}s)")
        return 0

    if args.jobs > 1 and len(args.leagues) > 1:
        with Pool(min(args.jobs, len(args.leagues))) as pool:
            out = dict(pool.map(_worker, args.leagues))
    else:
        out = dict(_worker(lg) for lg in args.leagues)
    for lg in args.leagues:
        stampa(lg, out[lg])

    prev = json.loads(path.read_text()) if path.exists() else {}
    for lg, blk in out.items():
        blk["theta_fissi"] = prev.get(lg, {}).get("theta_fissi")
        prev[lg] = blk
    prev["_meta"] = {"seasons": SEASONS, "rho": RHO, "grid": GRID,
                     "grid_fase81": GRID81, "bootstrap_B": 10_000,
                     "seed": SEED, "n_mercati": len(MARKETS),
                     "mercati": MARKETS,
                     "theta_fissi": prev.get("_meta", {}).get("theta_fissi")}
    path.write_text(json.dumps(prev, indent=2, default=str))
    print(f"\n-> {path.relative_to(ROOT)}   ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
