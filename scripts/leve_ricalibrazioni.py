"""Le RICALIBRAZIONI del mercato di chiusura sulle 5 leghe (le 2 nuove al centro).

DOMANDA
-------
Il mercato di chiusura sbaglia in modo SISTEMATICO su qualche classe di esito?
Se sì, il segno dell'errore è una proprietà del **calcio** (allora esiste una
regola) o della **singola lega** (allora la leva è morta come modello generale)?

Tre leve della panchina, mai provate su bundesliga e ligue_1:

  A. RICALIBRAZIONE PER-CLASSE (`_run_fase50_market_recal.py`, F50-ter)
        q_i ∝ w_i · p_i ,  w_H ≡ 1 ,  (w_D, w_A) stimati sul PASSATO
     Stato noto: Serie A −0.0006 (non conclusivo, w_D≈1.09); Premier segno
     OPPOSTO (w_D=0.93); Liga tipo-Serie-A. Il progetto ha scritto «segno non
     universale». Le due leghe nuove sono il test decisivo.

  B. RICALIBRAZIONE DEI LIVELLI / tilt (`market_implied.RATE_LEVELS`, F51)
        λ' = λ·exp(c_λ) ,  μ' = μ·exp(c_μ) ,  c = fit_level = log(Σgol/Σtassi)
     È l'asse «livelli» dentro `sharpen_1x2` (in Serie A: ×0.9726, ×1.0224).
     Qui è isolato dal θ (una cosa alla volta) e misurato su TUTTO il listino
     Tier 1, non solo sull'1X2.

  C. POWER-DEVIG + DENOISING CROSS-STAGIONE (`src/models/market_denoise.py`)
        C1  p_i ∝ (1/o_i)^(1/η)          (η stimato sul passato; η=1 = devig molt.)
        C2  p_corr = σ(a·logit(p_raw)+b)  (Platt sui mercati DERIVATI)
     Bocciato in Serie A (F38/50), mai provato altrove.

METODO (vincolante, CLAUDE.md §1-2)
-----------------------------------
- metriche dalle funzioni del progetto (`metrics.devig_*`, `mi.price_markets`,
  `_fase52_common.{fit_level,boot}`, `market_denoise.*`); niente log-loss a mano
  oltre alla formula standard `ll_bin` copiata da `_run_market_implied`;
- parametri SEMPRE fuori campione: **LOSO** (leave-one-season-out: ogni stagione
  è test, parametri dalle altre 6) come test principale e **LFO** (leave-future-
  out walk-forward, ≥2 stagioni di training) come replica fedele della F50-ter;
- bootstrap appaiato B=10.000, verdetto esplicito: CI95 che NON attraversa lo
  zero = conclusivo, altrimenti «nel rumore». Con ~1.900-2.600 partite per lega
  la soglia di risoluzione è ~1-2 millesimi di log-loss: sotto quella soglia un
  guadagno NON è dimostrabile e va detto;
- multiple testing dichiarato: 25 mercati × 5 leghe. La regola di lettura
  pre-registrata è: headline solo sui mercati PRE-DICHIARATI (1X2 per A e C1,
  GG/NG per C2), e per le scoperte «a strascico» serve la REPLICA sull'altra
  lega nuova o Bonferroni.

ASPETTATIVA DICHIARATA PRIMA DI GUARDARE I NUMERI
-------------------------------------------------
  A: non conclusiva, e con segno INCOERENTE fra le leghe (la lezione del
     progetto è che non è universale).
  B: piccola ma con segno COERENTE col tracer market-side
     (bundesliga c_λ +0.019 / c_μ +0.022 ; ligue_1 −0.010 / +0.022).
  C: NEGATIVA (η≈1, Platt≈identità: il motore è già non-biased).

FINESTRE
--------
  - principale: 7 stagioni 1920→2526 (tutte quelle con chiusura O/U reale;
    serve a B e C2, e si usa anche per A perché i numeri siano confrontabili);
  - per A e C1 (che usano SOLO l'1X2) anche la finestra lunga 9 stagioni
    1718→2526: +29% di partite, cioè più risoluzione su una leva che vive
    proprio sotto la soglia.

Uso:  python scripts/leve_ricalibrazioni.py [--leagues ...] [--jobs 2]
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
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scripts import _fase52_common as C              # noqa: E402
from src.evaluation import metrics                   # noqa: E402
from src.models import market_denoise as MD          # noqa: E402
from src.models import market_implied as mi          # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
CACHE = Path(os.environ.get(
    "SCRATCH",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")) / "ricalibrazioni"

SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "data",
        "ligue_1": ROOT / "data"}
LEAGUES = ["bundesliga", "ligue_1", "serie_a", "premier_league", "la_liga"]

SEASONS_MKT = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
SEASONS_ALL = ["1718", "1819"] + SEASONS_MKT
RHO = -0.06
MAXG = mi.MAX_GOALS
B, SEED = 10_000, 505           # seed: solo riproducibilita'
B_PAR = 2_000                   # bootstrap sui PARAMETRI (rifit: piu' costoso)
MIN_TRAIN_SEASONS = 2           # regola pre-dichiarata della F50-ter
_OI = {"H": 0, "D": 1, "A": 2}

# --------------------------------------------------------------------------- #
# Il listino Tier 1. Chiavi = quelle di `mi.derive_markets`; gli esiti ricalcano
# `_run_market_implied._binary_outcomes` (stessa definizione, verificata riga per
# riga) estesa a clean-sheet e vince-a-zero, come `_run_fase52_router3`.
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
# Mercati PRE-DICHIARATI su cui si legge l'headline (il resto è a strascico).
HEADLINE_C2 = "btts"


# ------------------------------------------------------------------ dati ---- #
def carica(league: str, seasons: list[str], serve_ou: bool) -> pd.DataFrame:
    df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df = df[df.season.isin(seasons)]
    need = ["odds_home", "odds_draw", "odds_away"]
    if serve_ou:
        need += ["odds_over25", "odds_under25"]
    df = df.dropna(subset=need)
    return df.sort_values("date").reset_index(drop=True)


def inverti(df: pd.DataFrame, league: str) -> tuple[np.ndarray, np.ndarray]:
    """(λ, μ) impliciti nella chiusura 1X2+O/U col motore di PRODUZIONE.
    Cache su scratch (l'inversione costa ~3.5 ms a riga)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"rates_{league}_rho{RHO:+.2f}_n{len(df)}.csv"
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


# --------------------------------------------------------------- metriche -- #
def ll_bin(p, y):
    """Identica a `_run_market_implied.ll_bin` (fonte del progetto)."""
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ll_1x2(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    P = P / P.sum(axis=1, keepdims=True)
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, None))


def boot_e(d: np.ndarray, rng) -> dict:
    """`_fase52_common.boot` + verdetto. d < 0 = la leva MIGLIORA."""
    if not np.any(d):
        return {"delta": 0.0, "ci95": [0.0, 0.0], "p_migliora": 0.5,
                "verdetto": "identico"}
    mean, lo, hi, p_neg = C.boot(d, rng, B)
    verdetto = ("MEGLIO (CI conclusivo)" if hi < 0 else
                ("PEGGIO (CI conclusivo)" if lo > 0 else "nel rumore"))
    return {"delta": mean, "ci95": [lo, hi], "p_migliora": p_neg,
            "verdetto": verdetto}


def boot_param(n: int, rng, stima, nullo: float, B_: int = B_PAR) -> dict:
    """CI95 bootstrap NON appaiato su un PARAMETRO: si ricampionano le partite e
    si RIFITTA. Serve alla domanda che conta (il segno è reale o è rumore?): se
    il CI del parametro contiene il valore neutro, «il segno» non esiste.
    ``stima(idx) -> float``; ``nullo`` = valore neutro (1 per w/η, 0 per il tilt)."""
    v = np.array([stima(rng.integers(0, n, n)) for _ in range(B_)])
    lo, hi = np.percentile(v, [2.5, 97.5])
    lato = float((v > nullo).mean())
    return {"ci95": [float(lo), float(hi)],
            "p_sopra_nullo": lato,
            "segno_certo": bool(lo > nullo or hi < nullo)}


# ============================================================== LEVA A ====== #
def fit_w(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    """(w_D, w_A) che minimizzano la log-loss di q ∝ w·p, w_H≡1.
    Copia fedele di `_run_fase50_market_recal._fit_w` (stessi bound 0.5-2)."""
    def nll(x):
        w = np.array([1.0, x[0], x[1]])
        Q = P * w; Q = Q / Q.sum(1, keepdims=True)
        return -np.mean(np.log(np.clip(Q[np.arange(len(y)), y], 1e-15, 1)))
    r = minimize(nll, [1.0, 1.0], method="L-BFGS-B", bounds=[(0.5, 2), (0.5, 2)])
    return np.array([1.0, r.x[0], r.x[1]])


def applica_w(P: np.ndarray, w: np.ndarray) -> np.ndarray:
    Q = P * w
    return Q / Q.sum(1, keepdims=True)


def leva_A(league: str, seasons: list[str], rng) -> dict:
    df = carica(league, seasons, serve_ou=False)
    P = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in df.itertuples()])
    y = np.array([_OI[r] for r in df.result])
    ss = df.season.to_numpy()
    stag = [s for s in seasons if (ss == s).any()]

    raw = ll_1x2(P, y)
    w_pool = fit_w(P, y)                       # solo per LEGGERE IL SEGNO

    out = {"n": int(len(df)), "stagioni": stag,
           "w_in_sample": {"w_D": float(w_pool[1]), "w_A": float(w_pool[2])},
           "ll_mercato": float(raw.mean())}
    bw = boot_param(len(y), rng, lambda i: fit_w(P[i], y[i])[1], 1.0)
    ba = boot_param(len(y), rng, lambda i: fit_w(P[i], y[i])[2], 1.0)
    out["w_bootstrap"] = {"w_D": bw, "w_A": ba}

    # --- LOSO: ogni stagione è test, parametri dalle altre ------------------ #
    rec = np.zeros(len(y)); w_loso = {}
    for s in stag:
        tr = ss != s; cur = ss == s
        w = fit_w(P[tr], y[tr]); w_loso[s] = [float(w[1]), float(w[2])]
        rec[cur] = ll_1x2(applica_w(P[cur], w), y[cur])
    per_stag = {s: float((rec[ss == s] - raw[ss == s]).mean()) for s in stag}
    out["loso"] = {"w_per_stagione": w_loso, "ll_recal": float(rec.mean()),
                   **boot_e(rec - raw, rng),
                   "stagioni_migliorate": int(sum(v < 0 for v in per_stag.values())),
                   "stagioni_totali": len(stag),
                   "delta_per_stagione": per_stag}

    # --- LFO walk-forward (replica F50-ter: >= 2 stagioni di training) ------ #
    mask = np.zeros(len(y), bool); rec_f = np.zeros(len(y)); w_lfo = {}
    for i, s in enumerate(stag):
        if i < MIN_TRAIN_SEASONS:
            continue
        past = np.isin(ss, stag[:i]); cur = ss == s
        w = fit_w(P[past], y[past]); w_lfo[s] = [float(w[1]), float(w[2])]
        rec_f[cur] = ll_1x2(applica_w(P[cur], w), y[cur]); mask |= cur
    d = rec_f[mask] - raw[mask]
    per_stag_f = {s: float((rec_f[ss == s] - raw[ss == s]).mean()) for s in w_lfo}
    out["lfo"] = {"w_per_stagione": w_lfo, "n_test": int(mask.sum()),
                  "ll_mercato": float(raw[mask].mean()),
                  "ll_recal": float(rec_f[mask].mean()), **boot_e(d, rng),
                  "stagioni_migliorate": int(sum(v < 0 for v in per_stag_f.values())),
                  "stagioni_totali": len(w_lfo),
                  "delta_per_stagione": per_stag_f}
    return out


# ============================================================== LEVA B ====== #
def prezza(lam, mu, hg, ag, phi0: float = 0.0) -> dict[str, np.ndarray]:
    """LL per-riga di ogni mercato del listino, dal router di PRODUZIONE
    `mi.price_markets` (phi0=0 → matrice unica, dp_theta=None → Poisson)."""
    n = len(lam)
    prob = {m: np.zeros(n) for m, _ in BIN_MARKETS}
    p3 = np.zeros((n, 3)); pmg = np.zeros((n, 3)); ex = np.zeros(n)
    for i in range(n):
        d = mi.price_markets(float(lam[i]), float(mu[i]), RHO, phi0)
        for m, _ in BIN_MARKETS:
            prob[m][i] = d[m]
        p3[i] = (d["home_win"], d["draw"], d["away_win"])
        pmg[i] = (d["mg_0_1"], d["mg_2_3"], d["mg_4plus"])
        ex[i] = -np.log(max(d["score_matrix"][min(hg[i], MAXG),
                                              min(ag[i], MAXG)], 1e-15))
    out = {m: ll_bin(prob[m], f(hg, ag).astype(float)) for m, f in BIN_MARKETS}
    out["1X2"] = ll_1x2(p3, np.where(hg > ag, 0, np.where(hg == ag, 1, 2)))
    tot = hg + ag
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    out["multigol"] = -np.log(np.clip(pmg[np.arange(n), ymg], 1e-15, None))
    out["risultato_esatto"] = ex
    out["_prob"] = prob                     # serve alla leva C2
    return out


def p1x2_veloce(lam, mu, fl: float, fm: float) -> np.ndarray:
    """(P1,PX,P2) vettoriale per la griglia della leva B: stessa matrice di
    `score_matrix(lam*fl, mu*fm, RHO)` — `dp_matrices(...,θ=1)` è la Poisson."""
    return C.p1x2(C.dp_matrices(lam * fl, mu * fm, RHO, 1.0))


GRID_LVL = [round(0.88 + 0.01 * i, 3) for i in range(21)]    # 0.880 … 1.080


def leva_B(league: str, rng) -> dict:
    df = carica(league, SEASONS_MKT, serve_ou=True)
    lam, mu = inverti(df, league)
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    ss = df.season.to_numpy()
    stag = [s for s in SEASONS_MKT if (ss == s).any()]
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))

    ref = prezza(lam, mu, hg, ag)
    out = {"n": int(len(df)), "stagioni": stag,
           "tilt_in_sample": {"c_lambda": float(C.fit_level(lam, hg)),
                              "c_mu": float(C.fit_level(mu, ag))},
           "tilt_bootstrap": {
               "c_lambda": boot_param(len(lam), rng,
                                      lambda i: C.fit_level(lam[i], hg[i]), 0.0),
               "c_mu": boot_param(len(mu), rng,
                                  lambda i: C.fit_level(mu[i], ag[i]), 0.0)},
           "ll_riferimento": {m: float(ref[m].mean()) for m in MARKETS}}

    # --- primario: costanti fit_level LOSO ---------------------------------- #
    cl = {s: float(C.fit_level(lam[ss != s], hg[ss != s])) for s in stag}
    cm = {s: float(C.fit_level(mu[ss != s], ag[ss != s])) for s in stag}
    lam_t = lam.copy(); mu_t = mu.copy()
    for s in stag:
        cur = ss == s
        lam_t[cur] = lam[cur] * np.exp(cl[s]); mu_t[cur] = mu[cur] * np.exp(cm[s])
    til = prezza(lam_t, mu_t, hg, ag)
    out["mle_loso"] = {
        "c_lambda_per_stagione": cl, "c_mu_per_stagione": cm,
        "fattori_medi": [float(np.exp(np.mean(list(cl.values())))),
                         float(np.exp(np.mean(list(cm.values()))))],
        "mercati": {m: {"ll": float(til[m].mean()), **boot_e(til[m] - ref[m], rng)}
                    for m in MARKETS}}

    # --- secondario (ESPLORATIVO): fattori scelti per GRIGLIA sull'1X2, LOSO - #
    # La lezione del progetto (F53 vs F81) dice che griglia > MLE. Qui la si
    # applica ai livelli. 25x25 = 625 combinazioni: multiple testing enorme, per
    # questo è dichiarato ESPLORATIVO e il verdetto richiede la replica.
    llg = {}
    for fl in GRID_LVL:
        for fm in GRID_LVL:
            llg[(fl, fm)] = ll_1x2(p1x2_veloce(lam, mu, fl, fm), y3)
    combi = list(llg)
    picks = {}
    lam_g = lam.copy(); mu_g = mu.copy()
    for s in stag:
        tr = ss != s
        best = min(combi, key=lambda c: llg[c][tr].mean())
        picks[s] = [float(best[0]), float(best[1])]
        cur = ss == s
        lam_g[cur] = lam[cur] * best[0]; mu_g[cur] = mu[cur] * best[1]
    gri = prezza(lam_g, mu_g, hg, ag)
    out["griglia_loso"] = {
        "fattori_per_stagione": picks,
        "fattori_medi": [float(np.mean([p[0] for p in picks.values()])),
                         float(np.mean([p[1] for p in picks.values()]))],
        "mercati": {m: {"ll": float(gri[m].mean()), **boot_e(gri[m] - ref[m], rng)}
                    for m in MARKETS}}
    return out


# ============================================================== LEVA C ====== #
def leva_C1(league: str, seasons: list[str], rng) -> dict:
    """Power-devig: p ∝ (1/o)^(1/η), η stimato sul passato (`MD.fit_power_eta`)."""
    df = carica(league, seasons, serve_ou=False)
    O = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    res = list(df.result)
    y = np.array([_OI[r] for r in res])
    ss = df.season.to_numpy()
    stag = [s for s in seasons if (ss == s).any()]
    raw = ll_1x2(np.array([metrics.devig_1x2(*o) for o in O]), y)

    out = {"n": int(len(df)), "ll_mercato": float(raw.mean()),
           "eta_in_sample": float(MD.fit_power_eta(O, res)),
           "eta_bootstrap": boot_param(
               len(y), rng,
               lambda i: MD.fit_power_eta(O[i], [res[k] for k in i]), 1.0, 500)}
    for tag in ("loso", "lfo"):
        pw = np.zeros(len(y)); mask = np.zeros(len(y), bool); etas = {}
        for i, s in enumerate(stag):
            cur = ss == s
            if tag == "loso":
                tr = ss != s
            else:
                if i < MIN_TRAIN_SEASONS:
                    continue
                tr = np.isin(ss, stag[:i])
            eta = MD.fit_power_eta(O[tr], [res[k] for k in np.where(tr)[0]])
            etas[s] = float(eta)
            pw[cur] = ll_1x2(np.array([MD.power_devig(*o, eta=eta) for o in O[cur]]),
                             y[cur])
            mask |= cur
        out[tag] = {"eta_per_stagione": etas, "n_test": int(mask.sum()),
                    "ll_mercato": float(raw[mask].mean()),
                    "ll_power": float(pw[mask].mean()),
                    **boot_e(pw[mask] - raw[mask], rng)}
    return out


def leva_C2(league: str, rng, ref: dict | None = None,
            dati: tuple | None = None) -> dict:
    """Platt cross-stagione sui mercati DERIVATI del market-implied."""
    if dati is None:
        df = carica(league, SEASONS_MKT, serve_ou=True)
        lam, mu = inverti(df, league)
        hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
        ss = df.season.to_numpy()
        ref = prezza(lam, mu, hg, ag)
    else:
        hg, ag, ss = dati
    stag = [s for s in SEASONS_MKT if (ss == s).any()]
    prob = ref["_prob"]
    out = {"n": int(len(ss)), "mercati": {}}
    for m, f in BIN_MARKETS:
        p = prob[m]; yb = f(hg, ag).astype(float)
        pc = np.zeros(len(yb)); ab = {}
        for s in stag:
            tr = ss != s; cur = ss == s
            a, b = MD.fit_derived_recal(p[tr], yb[tr])
            ab[s] = [float(a), float(b)]
            pc[cur] = MD.apply_derived_recal(p[cur], a, b)
        d = ll_bin(pc, yb) - ref[m]
        out["mercati"][m] = {"ll_raw": float(ref[m].mean()),
                             "ll_platt": float(ll_bin(pc, yb).mean()),
                             "a_medio": float(np.mean([v[0] for v in ab.values()])),
                             "b_medio": float(np.mean([v[1] for v in ab.values()])),
                             "ab_per_stagione": ab, **boot_e(d, rng)}
    return out


# ========================================================= CONFUTAZIONI ===== #
# Prima di dichiarare qualunque risultato, si prova a demolirlo (richiesta
# esplicita dell'utente). Tre attacchi mirati ai soli numeri che «sembrano
# qualcosa»:
#   1. il w_D>1 della leva A è un fatto di mercato o un artefatto del DEVIG
#      MOLTIPLICATIVO? Si rifà tutto col devig di SHIN (favourite-longshot bias
#      modellato) — stessa domanda che la Fase 52-C pose al tilt.
#   2. il tilt della leva B è un bias del MERCATO o un artefatto
#      dell'INVERSIONE Poisson? Se i gol sono sotto-dispersi (θ>1), invertire
#      con marginali Poisson sposta i tassi in modo sistematico e produce un
#      tilt che non è del mercato. Si ri-inverte con marginali double-Poisson.
#   3. il fallimento fuori campione della leva A è «non c'è bias» o «il bias
#      DERIVA nel tempo»? Placebo: stesse 7 pieghe, ma CASUALI invece che
#      stagionali. Se col taglio casuale la leva funziona e con quello
#      temporale no, il bias esiste ma non è trasportabile nel futuro.
# --------------------------------------------------------------------------- #
def shin_devig(odds_home: float, odds_draw: float, odds_away: float) -> np.ndarray:
    """Copia VERBATIM di `scripts/_run_fase52_shin.shin_devig` (verificata riga
    per riga): p_i = [sqrt(z²+4(1−z)·π_i²/Π) − z] / (2(1−z)), z per bisezione."""
    pi = np.array([1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away])
    PI = pi.sum()

    def p_of(z):
        return (np.sqrt(z * z + 4.0 * (1.0 - z) * pi * pi / PI) - z) / (2.0 * (1.0 - z))

    lo, hi = 0.0, 0.3
    for _ in range(60):
        z = 0.5 * (lo + hi)
        if p_of(z).sum() > 1.0:
            lo = z
        else:
            hi = z
    p = p_of(0.5 * (lo + hi))
    return p / p.sum()


def implied_lambda_mu_dp(pH, pD, pA, pO, rho, theta):
    """Variante LOCALE di `mi.implied_lambda_mu`: identica riga per riga (stessa
    loss, stessa inizializzazione, stessi bound) tranne il passaggio di
    ``dp_theta`` a `score_matrix` — marginali double-Poisson invece di Poisson."""
    def loss(x):
        lam, mu = x
        qH, qD, qA, qO = mi._1x2_over(mi.score_matrix(lam, mu, rho, dp_theta=theta))
        e = (qH - pH) ** 2 + (qD - pD) ** 2 + (qA - pA) ** 2
        if pO is not None:
            e += (qO - pO) ** 2
        return e
    tot0 = 2.5 + ((pO - 0.5) * 2.0 if pO is not None else 0.0)
    tilt = float(np.clip(0.5 + (pH - pA) * 0.6, 0.15, 0.85))
    x0 = [max(0.2, tot0 * tilt), max(0.2, tot0 * (1.0 - tilt))]
    r = minimize(loss, x0, method="L-BFGS-B", bounds=[(0.1, 4.5), (0.1, 4.5)])
    return float(r.x[0]), float(r.x[1])


def confuta_league(league: str) -> dict:
    rng = np.random.default_rng(SEED + 1)
    out: dict = {}

    # --- 1. leva A col devig di SHIN (finestra lunga: piu' risoluzione) ------ #
    df = carica(league, SEASONS_ALL, serve_ou=False)
    y = np.array([_OI[r] for r in df.result]); ss = df.season.to_numpy()
    stag = [s for s in SEASONS_ALL if (ss == s).any()]
    Pm = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                   for r in df.itertuples()])
    Psh = np.array([shin_devig(r.odds_home, r.odds_draw, r.odds_away)
                    for r in df.itertuples()])
    blocco = {}
    for tag, P in (("moltiplicativo", Pm), ("shin", Psh)):
        w = fit_w(P, y)
        raw = ll_1x2(P, y); rec = np.zeros(len(y))
        for s in stag:
            tr = ss != s; cur = ss == s
            rec[cur] = ll_1x2(applica_w(P[cur], fit_w(P[tr], y[tr])), y[cur])
        blocco[tag] = {
            "w_D": float(w[1]), "w_A": float(w[2]),
            "w_D_ci": boot_param(len(y), rng, lambda i: fit_w(P[i], y[i])[1], 1.0)["ci95"],
            "ll_base": float(raw.mean()), "ll_recal": float(rec.mean()),
            **boot_e(rec - raw, rng)}
    out["A_devig_shin"] = blocco

    # --- 2. leva A con pieghe CASUALI invece che stagionali (placebo/deriva) - #
    K = len(stag)
    fold = rng.integers(0, K, len(y))
    raw = ll_1x2(Pm, y); rec = np.zeros(len(y))
    for k in range(K):
        tr = fold != k; cur = fold == k
        rec[cur] = ll_1x2(applica_w(Pm[cur], fit_w(Pm[tr], y[tr])), y[cur])
    out["A_pieghe_casuali"] = {"K": K, "ll_base": float(raw.mean()),
                              "ll_recal": float(rec.mean()), **boot_e(rec - raw, rng)}

    # --- 3. leva B: il tilt sopravvive a un'inversione SOTTO-dispersa? ------- #
    dfm = carica(league, SEASONS_MKT, serve_ou=True)
    lam, mu = inverti(dfm, league)
    hg = dfm.home_goals.to_numpy(int); ag = dfm.away_goals.to_numpy(int)
    theta = float(C.fit_theta(lam, mu, hg, ag, RHO))
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"rates_dp_{league}_t{theta:.3f}_n{len(dfm)}.csv"
    if fp.exists():
        c = pd.read_csv(fp); lam_dp, mu_dp = c["lam"].to_numpy(), c["mu"].to_numpy()
    else:
        lam_dp = np.zeros(len(dfm)); mu_dp = np.zeros(len(dfm))
        for i, r in enumerate(dfm.itertuples()):
            pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
            lam_dp[i], mu_dp[i] = implied_lambda_mu_dp(pH, pD, pA, pO, RHO, theta)
        pd.DataFrame({"lam": lam_dp, "mu": mu_dp}).to_csv(fp, index=False)
    out["B_tilt_sotto_inversione_dp"] = {
        "theta_mle": theta,
        "poisson": {"c_lambda": float(C.fit_level(lam, hg)),
                    "c_mu": float(C.fit_level(mu, ag))},
        "double_poisson": {"c_lambda": float(C.fit_level(lam_dp, hg)),
                           "c_mu": float(C.fit_level(mu_dp, ag))}}

    # --- 4. leva B: il tilt e' STABILE o e' l'effetto-COVID (stadi vuoti)? --- #
    # Se il tilt vive nel 1920/2021 (porte chiuse, vantaggio-casa crollato) e
    # sparisce dopo, non e' un bias del mercato: e' un evento storico.
    sm = dfm.season.to_numpy()
    per_st = {s: {"n": int((sm == s).sum()),
                  "c_lambda": float(C.fit_level(lam[sm == s], hg[sm == s])),
                  "c_mu": float(C.fit_level(mu[sm == s], ag[sm == s]))}
              for s in SEASONS_MKT if (sm == s).any()}
    post = [s for s in per_st if s not in ("1920", "2021")]
    mpost = np.isin(sm, post)
    out["B_tilt_per_stagione"] = {
        "per_stagione": per_st,
        "senza_covid_1920_2021": {"n": int(mpost.sum()),
                                  "c_lambda": float(C.fit_level(lam[mpost], hg[mpost])),
                                  "c_mu": float(C.fit_level(mu[mpost], ag[mpost]))}}
    return out


def _worker_conf(league):
    return league, confuta_league(league)


# =============================================================== lega ======= #
def run_league(league: str) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    r: dict = {}
    r["A_7stagioni"] = leva_A(league, SEASONS_MKT, rng)
    r["A_9stagioni"] = leva_A(league, SEASONS_ALL, rng)
    r["B"] = leva_B(league, rng)
    r["C1_7stagioni"] = leva_C1(league, SEASONS_MKT, rng)
    r["C1_9stagioni"] = leva_C1(league, SEASONS_ALL, rng)
    # C2 riusa l'inversione e il riferimento della leva B
    df = carica(league, SEASONS_MKT, serve_ou=True)
    lam, mu = inverti(df, league)
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    r["C2"] = leva_C2(league, rng, prezza(lam, mu, hg, ag),
                      (hg, ag, df.season.to_numpy()))
    r["secondi"] = round(time.time() - t0, 1)
    return r


def _worker(league):
    return league, run_league(league)


# ============================================================== report ====== #
def _fl(v, w=9, p=4):
    return f"{v:>+{w}.{p}f}"


def stampa(lg: str, r: dict) -> None:
    print("\n" + "=" * 104)
    print(f"{lg.upper()}   ({r['A_7stagioni']['n']} partite 1920-2526, "
          f"{r['A_9stagioni']['n']} partite 1718-2526)      [{r['secondi']}s]")
    print("=" * 104)

    print("\n  --- LEVA A · ricalibrazione per-classe del mercato (w_D, w_A) ---")
    for tag in ("A_7stagioni", "A_9stagioni"):
        a = r[tag]
        bw, ba = a["w_bootstrap"]["w_D"], a["w_bootstrap"]["w_A"]
        print(f"   [{tag.split('_')[1]}]  w in-sample: "
              f"w_D={a['w_in_sample']['w_D']:.3f} CI95 "
              f"[{bw['ci95'][0]:.3f},{bw['ci95'][1]:.3f}]"
              f"{' SEGNO CERTO' if bw['segno_certo'] else ' (contiene 1)'}"
              f"   w_A={a['w_in_sample']['w_A']:.3f} CI95 "
              f"[{ba['ci95'][0]:.3f},{ba['ci95'][1]:.3f}]"
              f"{' SEGNO CERTO' if ba['segno_certo'] else ' (contiene 1)'}"
              f"   ({'pari SOTTO-prezzato' if a['w_in_sample']['w_D'] > 1 else 'pari SOVRA-prezzato'})")
        for sel in ("loso", "lfo"):
            b = a[sel]
            print(f"      {sel.upper():5s} mercato {a['ll_mercato']:.4f} -> "
                  f"recal {b['ll_recal']:.4f}   Δ {_fl(b['delta'])} "
                  f"CI95 [{b['ci95'][0]:+.4f},{b['ci95'][1]:+.4f}] "
                  f"P(migl) {b['p_migliora']:.0%}  "
                  f"{b['stagioni_migliorate']}/{b['stagioni_totali']} stag  "
                  f"-> {b['verdetto']}")

    print("\n  --- LEVA B · ricalibrazione dei livelli (tilt λ, μ) ---")
    b = r["B"]
    t = b["tilt_in_sample"]; tb = b["tilt_bootstrap"]
    print(f"   tilt in-sample: c_λ {t['c_lambda']:+.4f} (×{np.exp(t['c_lambda']):.4f}) "
          f"CI95 [{tb['c_lambda']['ci95'][0]:+.4f},{tb['c_lambda']['ci95'][1]:+.4f}]"
          f"{' SEGNO CERTO' if tb['c_lambda']['segno_certo'] else ' (contiene 0)'}")
    print(f"                   c_μ {t['c_mu']:+.4f} (×{np.exp(t['c_mu']):.4f}) "
          f"CI95 [{tb['c_mu']['ci95'][0]:+.4f},{tb['c_mu']['ci95'][1]:+.4f}]"
          f"{' SEGNO CERTO' if tb['c_mu']['segno_certo'] else ' (contiene 0)'}")
    for tag, nome in (("mle_loso", "fit_level LOSO (primario)"),
                      ("griglia_loso", "griglia LOSO su 1X2 (esplorativo)")):
        blk = b[tag]
        conc_m = [m for m in MARKETS if blk["mercati"][m]["ci95"][1] < 0]
        conc_p = [m for m in MARKETS if blk["mercati"][m]["ci95"][0] > 0]
        print(f"   {nome}: fattori medi ×{blk['fattori_medi'][0]:.4f}, "
              f"×{blk['fattori_medi'][1]:.4f}")
        print(f"      {'mercato':<17}{'rif.':>9}{'tilt':>9}{'Δ':>10}{'CI95':>21}{'P':>6}")
        for m in MARKETS:
            v = blk["mercati"][m]
            fl = "*" if v["ci95"][1] < 0 else ("!" if v["ci95"][0] > 0 else " ")
            print(f"      {m:<17}{b['ll_riferimento'][m]:>9.4f}{v['ll']:>9.4f}"
                  f"{v['delta']:>+10.4f}  [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]"
                  f"{v['p_migliora']:>6.0%} {fl}")
        print(f"      -> MEGLIO con CI conclusivo su {len(conc_m)}/{len(MARKETS)}: "
              f"{conc_m if conc_m else '-'}")
        print(f"      -> PEGGIO con CI conclusivo su {len(conc_p)}/{len(MARKETS)}: "
              f"{conc_p if conc_p else '-'}")

    print("\n  --- LEVA C1 · power-devig (η) ---")
    for tag in ("C1_7stagioni", "C1_9stagioni"):
        c = r[tag]
        eb = c["eta_bootstrap"]
        print(f"   [{tag.split('_')[1]}] η in-sample {c['eta_in_sample']:.4f} "
              f"CI95 [{eb['ci95'][0]:.4f},{eb['ci95'][1]:.4f}]"
              f"{' SEGNO CERTO' if eb['segno_certo'] else ' (contiene 1)'}")
        for sel in ("loso", "lfo"):
            v = c[sel]
            print(f"      {sel.upper():5s} η LOSO/LFO "
                  f"[{min(v['eta_per_stagione'].values()):.3f},"
                  f"{max(v['eta_per_stagione'].values()):.3f}]  "
                  f"molt {v['ll_mercato']:.4f} -> power {v['ll_power']:.4f}   "
                  f"Δ {_fl(v['delta'])} CI95 [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]"
                  f"  -> {v['verdetto']}")

    print("\n  --- LEVA C2 · Platt cross-stagione sui mercati derivati (LOSO) ---")
    c2 = r["C2"]["mercati"]
    conc_m = [m for m in c2 if c2[m]["ci95"][1] < 0]
    conc_p = [m for m in c2 if c2[m]["ci95"][0] > 0]
    h = c2[HEADLINE_C2]
    print(f"   HEADLINE pre-dichiarato «{HEADLINE_C2}»: {h['ll_raw']:.4f} -> "
          f"{h['ll_platt']:.4f}  Δ {_fl(h['delta'])} "
          f"CI95 [{h['ci95'][0]:+.4f},{h['ci95'][1]:+.4f}] "
          f"a={h['a_medio']:.3f} b={h['b_medio']:+.3f} -> {h['verdetto']}")
    print(f"   a strascico: MEGLIO conclusivo {len(conc_m)}/{len(c2)} {conc_m if conc_m else '-'}"
          f" | PEGGIO conclusivo {len(conc_p)}/{len(c2)}")
    for m in sorted(c2, key=lambda k: c2[k]["delta"])[:4]:
        v = c2[m]
        print(f"      {m:<15}{v['ll_raw']:>9.4f}{v['ll_platt']:>9.4f}"
              f"{v['delta']:>+10.4f}  [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]"
              f"  a={v['a_medio']:.3f} b={v['b_medio']:+.3f}")


def quadro(out: dict) -> None:
    print("\n\n" + "=" * 104)
    print("QUADRO CROSS-LEGA — IL SEGNO È UNA PROPRIETÀ DEL CALCIO O DELLA LEGA?")
    print("=" * 104)
    print(f"{'lega':16s}{'A w_D':>8}{'A w_A':>8}{'A Δ7':>10}{'A Δ9':>10}"
          f"{'B c_λ':>9}{'B c_μ':>9}{'B Δ1X2':>10}{'C1 η':>8}{'C1 Δ':>10}{'C2 GG Δ':>10}")
    for lg, r in out.items():
        a7, a9 = r["A_7stagioni"], r["A_9stagioni"]
        b, c1, c2 = r["B"], r["C1_7stagioni"], r["C2"]["mercati"][HEADLINE_C2]
        print(f"{lg:16s}{a7['w_in_sample']['w_D']:>8.3f}{a7['w_in_sample']['w_A']:>8.3f}"
              f"{a7['loso']['delta']:>+10.4f}{a9['loso']['delta']:>+10.4f}"
              f"{b['tilt_in_sample']['c_lambda']:>+9.4f}"
              f"{b['tilt_in_sample']['c_mu']:>+9.4f}"
              f"{b['mle_loso']['mercati']['1X2']['delta']:>+10.4f}"
              f"{c1['eta_in_sample']:>8.3f}{c1['loso']['delta']:>+10.4f}"
              f"{c2['delta']:>+10.4f}")
    # Il segno «vale» solo se il CI95 del parametro esclude il valore neutro:
    # altrimenti non c'è nessun segno da replicare, solo rumore.
    assi = [
        ("A w_D-1", lambda r: (r["A_9stagioni"]["w_in_sample"]["w_D"] - 1,
                               r["A_9stagioni"]["w_bootstrap"]["w_D"]["segno_certo"])),
        ("A w_A-1", lambda r: (r["A_9stagioni"]["w_in_sample"]["w_A"] - 1,
                               r["A_9stagioni"]["w_bootstrap"]["w_A"]["segno_certo"])),
        ("B c_λ", lambda r: (r["B"]["tilt_in_sample"]["c_lambda"],
                             r["B"]["tilt_bootstrap"]["c_lambda"]["segno_certo"])),
        ("B c_μ", lambda r: (r["B"]["tilt_in_sample"]["c_mu"],
                             r["B"]["tilt_bootstrap"]["c_mu"]["segno_certo"])),
        ("C1 η-1", lambda r: (r["C1_9stagioni"]["eta_in_sample"] - 1,
                              r["C1_9stagioni"]["eta_bootstrap"]["segno_certo"])),
    ]
    print("\n  [leva B secondaria] fattori scelti per GRIGLIA sull'1X2 (LOSO) — "
          f"griglia {GRID_LVL[0]}…{GRID_LVL[-1]}:")
    for lg, r in out.items():
        g = r["B"]["griglia_loso"]["fattori_medi"]
        bordo = ("AL BORDO" if min(g) <= GRID_LVL[0] + 1e-9
                 or max(g) >= GRID_LVL[-1] - 1e-9 else "interno")
        print(f"    {lg:16s} ×{g[0]:.4f}, ×{g[1]:.4f}   [{bordo}]   "
              f"Δ1X2 {r['B']['griglia_loso']['mercati']['1X2']['delta']:+.4f}  "
              f"peggiora conclusivamente "
              f"{sum(1 for m in MARKETS if r['B']['griglia_loso']['mercati'][m]['ci95'][0] > 0)}"
              f"/{len(MARKETS)} mercati")

    print("\n  (segno letto sulla finestra piu' lunga disponibile; «certo» = CI95 "
          "bootstrap del parametro che esclude il valore neutro)")
    for nome, f in assi:
        pos = [lg for lg, r in out.items() if f(r)[0] > 0]
        neg = [lg for lg, r in out.items() if f(r)[0] < 0]
        certi = [lg for lg, r in out.items() if f(r)[1]]
        univ = "UNIVERSALE" if not pos or not neg else "NON universale"
        print(f"  segno {nome:<9}: +{len(pos)} / -{len(neg)}  -> {univ}"
              f"   (+: {[l[:4] for l in pos]}, -: {[l[:4] for l in neg]}) "
              f" certi {len(certi)}/{len(out)}: {[l[:4] for l in certi]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--modo", choices=["leve", "confuta"], default="leve")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leve_ricalibrazioni.json"
    t0 = time.time()

    if args.modo == "confuta":
        if args.jobs > 1 and len(args.leagues) > 1:
            with Pool(min(args.jobs, len(args.leagues))) as pool:
                cf = dict(pool.map(_worker_conf, args.leagues))
        else:
            cf = dict(_worker_conf(lg) for lg in args.leagues)
        print("\n" + "=" * 104)
        print("CONFUTAZIONI — si prova a demolire i (pochi) numeri che sembrano qualcosa")
        print("=" * 104)
        print("\n  [1] leva A: il w_D>1 sopravvive al devig di SHIN? "
              "(finestra lunga 1718-2526)")
        print(f"  {'lega':16s}{'w_D molt':>10}{'CI95 molt':>18}{'w_D shin':>10}"
              f"{'CI95 shin':>18}{'Δ LOSO molt':>13}{'Δ LOSO shin':>13}")
        for lg in args.leagues:
            m = cf[lg]["A_devig_shin"]["moltiplicativo"]; s = cf[lg]["A_devig_shin"]["shin"]
            print(f"  {lg:16s}{m['w_D']:>10.3f}"
                  f"  [{m['w_D_ci'][0]:.3f},{m['w_D_ci'][1]:.3f}]{s['w_D']:>10.3f}"
                  f"  [{s['w_D_ci'][0]:.3f},{s['w_D_ci'][1]:.3f}]"
                  f"{m['delta']:>+13.4f}{s['delta']:>+13.4f}")
        print("\n  [2] leva A: pieghe CASUALI invece che stagionali "
              "(il bias c'e' ma DERIVA nel tempo?)")
        print(f"  {'lega':16s}{'Δ pieghe casuali':>19}{'CI95':>22}{'verdetto':>26}")
        for lg in args.leagues:
            v = cf[lg]["A_pieghe_casuali"]
            print(f"  {lg:16s}{v['delta']:>+19.4f}  [{v['ci95'][0]:+.4f},"
                  f"{v['ci95'][1]:+.4f}]{v['verdetto']:>26}")
        print("\n  [3] leva B: il tilt sopravvive a un'inversione SOTTO-dispersa?")
        print(f"  {'lega':16s}{'θ MLE':>8}{'c_λ Pois':>10}{'c_λ dp':>10}"
              f"{'c_μ Pois':>10}{'c_μ dp':>10}")
        for lg in args.leagues:
            v = cf[lg]["B_tilt_sotto_inversione_dp"]
            print(f"  {lg:16s}{v['theta_mle']:>8.3f}{v['poisson']['c_lambda']:>+10.4f}"
                  f"{v['double_poisson']['c_lambda']:>+10.4f}"
                  f"{v['poisson']['c_mu']:>+10.4f}{v['double_poisson']['c_mu']:>+10.4f}")
        print("\n  [4] leva B: il tilt e' l'effetto-COVID (stadi vuoti 1920/2021)?")
        print(f"  {'lega':16s}{'c_λ tutte':>11}{'c_λ post':>10}{'c_μ tutte':>11}"
              f"{'c_μ post':>10}   tilt per stagione (c_λ | c_μ)")
        for lg in args.leagues:
            v = cf[lg]["B_tilt_per_stagione"]; t = cf[lg]["B_tilt_sotto_inversione_dp"]
            det = " ".join(f"{s}:{d['c_lambda']:+.3f}|{d['c_mu']:+.3f}"
                           for s, d in v["per_stagione"].items())
            print(f"  {lg:16s}{t['poisson']['c_lambda']:>+11.4f}"
                  f"{v['senza_covid_1920_2021']['c_lambda']:>+10.4f}"
                  f"{t['poisson']['c_mu']:>+11.4f}"
                  f"{v['senza_covid_1920_2021']['c_mu']:>+10.4f}\n      {det}")
        prev = json.loads(path.read_text()) if path.exists() else {}
        prev.setdefault("_confutazione", {}).update(cf)
        path.write_text(json.dumps(prev, indent=2, default=str))
        print(f"\n-> {path.relative_to(ROOT)}   ({time.time()-t0:.0f}s)")
        return 0

    if args.jobs > 1 and len(args.leagues) > 1:
        with Pool(min(args.jobs, len(args.leagues))) as pool:
            out = dict(pool.map(_worker, args.leagues))
    else:
        out = dict(_worker(lg) for lg in args.leagues)
    out = {lg: out[lg] for lg in args.leagues}

    for lg in args.leagues:
        stampa(lg, out[lg])
    quadro(out)

    prev = json.loads(path.read_text()) if path.exists() else {}
    prev.update(out)
    prev["_meta"] = {
        "stagioni_mercato": SEASONS_MKT, "stagioni_lunghe": SEASONS_ALL,
        "rho": RHO, "bootstrap_B": B, "seed": SEED,
        "min_train_seasons_lfo": MIN_TRAIN_SEASONS,
        "griglia_livelli": [GRID_LVL[0], GRID_LVL[-1], len(GRID_LVL)],
        "mercati": MARKETS, "headline_C2": HEADLINE_C2,
        "aspettativa_dichiarata": {
            "A": "non conclusiva, segno INCOERENTE fra leghe",
            "B": "piccola, segno coerente col tracer market-side",
            "C": "negativa (eta~1, Platt~identita')"}}
    path.write_text(json.dumps(prev, indent=2, default=str))
    print(f"\n-> {path.relative_to(ROOT)}   ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
