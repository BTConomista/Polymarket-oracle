"""Il devig di SHIN contro il devig MOLTIPLICATIVO, sulle 5 leghe.

PERCHE'
-------
Tutto il progetto toglie il margine del bookmaker in modo MOLTIPLICATIVO
(`src/evaluation/metrics.devig_1x2`: p_i = (1/o_i)/Σ(1/o_j)). E' la "fonte
unica" da cui discende ogni numero storico. Il devig di **Shin (1992-93)**
modella invece una quota `z` di scommettitori INFORMATI: il book carica il
margine in modo NON uniforme, di piu' sugli esiti improbabili (favourite-
longshot bias). Effetto pratico: rispetto al moltiplicativo, Shin ALZA la
probabilita' del favorito e ABBASSA quella dell'outsider.

Il progetto lo ha misurato in Serie A (Fase 52-ter: 1X2 0.9617 vs 0.9625,
Δ −0.0007, P 97%) e ne ha confermato la DIREZIONE su Premier e Liga (Fase 53),
senza mai concludere. Le due leghe nuove (bundesliga, ligue_1) sono due
repliche INDIPENDENTI: se la direzione tiene 5/5, la leva diventa molto piu'
difendibile — e il test POOLED sulle 5 leghe ha n≈12.500, cioe' la potenza che
manca a ogni singola lega.

ASPETTATIVA DICHIARATA PRIMA DI GUARDARE I NUMERI
-------------------------------------------------
  (a) Shin ≥ moltiplicativo (log-loss 1X2) in TUTTE E 5 le leghe;
  (b) guadagno ~0.0005-0.0010 di log-loss 1X2;
  (c) per-lega NON conclusivo (sotto la soglia di risoluzione, ~1-2 millesimi
      con ~2.000 partite), POOLED conclusivo;
  (d) sull'O/U 2.5 effetto ~0: e' un mercato quasi 50/50, dove Shin e
      moltiplicativo quasi coincidono (la correzione cresce con l'asimmetria);
  (e) a valle (listino market-implied) il guadagno si DILUISCE: l'1X2 e l'O/U
      sono ancoraggi dell'inversione, quindi il segnale ci arriva quasi intero,
      ma i mercati DERIVATI (GG/NG, risultato esatto, multigol, total-squadra)
      dipendono da (λ, μ) in modo non lineare e il ~0.5% di spostamento delle
      probabilita' puo' perdersi nel rumore.

CHE COSA FA
-----------
 1. Implementa il devig di Shin per il mercato a 3 esiti E per quello binario
    (stessa formula, n qualunque; per n=3 riproduce `scripts/_run_fase52_shin.
    shin_devig`, verificato con un controllo di identita' numerica).
 2. **A MONTE — misura di verita' del mercato.** log-loss e Brier delle
    probabilita' devigate contro gli esiti reali, su 1X2 e su O/U 2.5, per le 5
    leghe, 7 stagioni (1920→2526, quelle con chiusura O/U reale). Terzo
    contendente: il **power-devig** (`src/models/market_denoise.power_devig`,
    p ∝ (1/o)^(1/η)) con η fittato LEAVE-ONE-SEASON-OUT — serve a CONFUTARE:
    se una forma a un parametro qualunque fa lo stesso lavoro, la forma
    specifica di Shin non e' speciale.
 3. Bootstrap appaiato B=10.000 per lega e POOLED sulle 5 leghe; verdetto
    esplicito CONCLUSIVO / nel rumore; correzione di Bonferroni dichiarata.
 4. **A VALLE — l'effetto sul listino.** Se cambia il devig cambiano i tassi
    impliciti (λ, μ) e quindi TUTTO il market-implied: si re-inverte con ogni
    devig (`mi.implied_lambda_mu`, ρ=−0.06) e si riprezzano 25 mercati Tier 1
    con `mi.price_markets`. Il devig migliore a monte produce prezzi migliori a
    valle? (nessuno l'ha mai verificato).
 5. **Il parametro z di Shin** per lega e per epoca: livello, dispersione,
    relazione col margine del book, trend temporale. Piu' un test che il
    progetto non ha mai fatto: la famiglia a un parametro
    p(t) = normalizza[ shin_p(t·z_riga) ], che vale il MOLTIPLICATIVO a t=0 e
    SHIN a t=1 — con t fittato LOSO sugli esiti si scopre se Shin corregge
    TROPPO, TROPPO POCO o giusto.

Metriche: log-loss/Brier con le formule di `src/evaluation/metrics` (fonte
unica) — le versioni per-riga qui dentro sono verificate contro di esse con un
assert di identita' numerica a ogni esecuzione. Bootstrap:
`scripts/_fase52_common.boot` (fonte del progetto) per n piccoli; per il pooled
(n≈12.500) una versione a blocchi identica nella distribuzione ma che non
alloca 2 GB.

Uso:  python scripts/leve_devig_shin.py [--leagues ...] [--jobs 2]
      [--no-downstream]
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
from src.models import market_denoise as MD        # noqa: E402
from src.models import market_implied as mi        # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
CACHE = Path(os.environ.get(
    "SCRATCH",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")) / "devig_shin"

SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "data",
        "ligue_1": ROOT / "data"}
LEAGUES = ["bundesliga", "ligue_1", "serie_a", "premier_league", "la_liga"]

# Finestra standard del path-mercato: tutte le stagioni con chiusura O/U reale.
SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
# Finestra estesa per il SOLO 1X2 (le quote 1X2 esistono dal 2017-18): serve
# come replica fuori-finestra, non come risultato principale.
SEASONS9 = ["1718", "1819"] + SEASONS

RHO = -0.06
MAXG = mi.MAX_GOALS
B, SEED = 10_000, 1993          # 1993 = anno del paper di Shin (nessun altro significato)
_OI = {"H": 0, "D": 1, "A": 2}

# Griglia della famiglia t: t=0 moltiplicativo, t=1 Shin.
T_GRID = [round(0.1 * i, 2) for i in range(0, 26)]      # 0.0 … 2.5

# --------------------------------------------------------------------------- #
# Il listino Tier 1 (identico a quello usato dagli altri script del cantiere e
# a `scripts/_run_market_implied._binary_outcomes` / `_run_fase52_router3`).
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
# Gli ANCORAGGI dell'inversione: 1X2+O/U 2.5 sono i target, quindi li
# riproducono per costruzione. Il valore vero e' nei DERIVATI.
ANCORE = {"home_win", "draw", "away_win", "dc_1x", "dc_2x", "over_2.5", "1X2"}
DERIVATI = [m for m in MARKETS if m not in ANCORE]


# =========================================================================== #
# 1. I DEVIG
# =========================================================================== #
def shin_z(pi: np.ndarray, iters: int = 80) -> np.ndarray:
    """Parametro z di Shin, riga per riga, per una matrice (N, k) di prob.
    grezze pi_i = 1/quota_i.

    Modello di Shin: dato Π = Σ pi_i (il "booksum", >1 per il margine), le
    probabilita' vere sono

        p_i(z) = [ sqrt(z² + 4(1−z)·pi_i²/Π) − z ] / (2(1−z))

    e z e' l'unico valore per cui Σ_i p_i(z) = 1. La somma vale sqrt(Π) in
    z=0 (quindi >1 se c'e' margine) e decresce monotonicamente in z: la
    bisezione su [0,1) e' esatta. Se Π ≤ 1 (nessun margine) la soluzione e'
    z=0 e Shin coincide col moltiplicativo dopo normalizzazione."""
    pi = np.asarray(pi, float)
    PI = pi.sum(axis=1, keepdims=True)
    lo = np.zeros((len(pi), 1))
    hi = np.full((len(pi), 1), 1.0 - 1e-9)
    for _ in range(iters):
        z = 0.5 * (lo + hi)
        s = _shin_p_raw(pi, PI, z).sum(axis=1, keepdims=True)
        troppo_alta = s > 1.0
        lo = np.where(troppo_alta, z, lo)
        hi = np.where(troppo_alta, hi, z)
    return (0.5 * (lo + hi)).ravel()


def _shin_p_raw(pi: np.ndarray, PI: np.ndarray, z: np.ndarray) -> np.ndarray:
    z = np.clip(z, 0.0, 1.0 - 1e-9)
    return (np.sqrt(z * z + 4.0 * (1.0 - z) * pi * pi / PI) - z) / (2.0 * (1.0 - z))


def shin_devig(odds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(probabilita' di Shin normalizzate, z) per una matrice (N, k) di quote."""
    pi = 1.0 / np.asarray(odds, float)
    PI = pi.sum(axis=1, keepdims=True)
    z = shin_z(pi)
    p = _shin_p_raw(pi, PI, z.reshape(-1, 1))
    return p / p.sum(axis=1, keepdims=True), z


def shin_family(odds: np.ndarray, z: np.ndarray, t: float) -> np.ndarray:
    """Famiglia a un parametro che INTERPOLA i due devig: si valuta la formula
    di Shin in z' = t·z (z = quello che azzera il margine) e si normalizza.

      t = 0  ->  p_i ∝ pi_i / sqrt(Π)  ->  normalizzato = pi_i/Π = MOLTIPLICATIVO
      t = 1  ->  SHIN
      t > 1  ->  correzione longshot PIU' FORTE di Shin

    Serve a chiedere ai dati QUANTA correzione vogliono, invece di imporre che
    sia esattamente quella che azzera il margine."""
    pi = 1.0 / np.asarray(odds, float)
    PI = pi.sum(axis=1, keepdims=True)
    p = _shin_p_raw(pi, PI, (t * np.asarray(z, float)).reshape(-1, 1))
    return p / p.sum(axis=1, keepdims=True)


def mult_devig(odds: np.ndarray) -> np.ndarray:
    """Devig moltiplicativo vettoriale (identico a metrics.devig_1x2 /
    devig_binary: verificato con un assert a ogni esecuzione)."""
    pi = 1.0 / np.asarray(odds, float)
    return pi / pi.sum(axis=1, keepdims=True)


def power_devig(odds: np.ndarray, eta: float) -> np.ndarray:
    """Devig a potenza (src/models/market_denoise.power_devig), vettoriale:
    p_i ∝ (1/o_i)^(1/η). η=1 = moltiplicativo."""
    pi = (1.0 / np.asarray(odds, float)) ** (1.0 / eta)
    return pi / pi.sum(axis=1, keepdims=True)


# =========================================================================== #
# 2. METRICHE (per-riga; identita' con la fonte unica verificata via assert)
# =========================================================================== #
def ll_rows(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    P = np.clip(np.asarray(P, float), 1e-15, 1.0)
    return -np.log(P[np.arange(len(y)), y])


def brier_rows(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    Y = np.zeros_like(P)
    Y[np.arange(len(y)), y] = 1.0
    return ((P - Y) ** 2).sum(axis=1)


def _verifica_fonte_unica(odds3: np.ndarray, odds2: np.ndarray,
                          res: list[str], is_over: np.ndarray) -> dict:
    """Controllo di sanita' OBBLIGATORIO: le formule vettoriali qui dentro
    devono coincidere con `src.evaluation.metrics` riga per riga."""
    P3 = np.array([metrics.devig_1x2(*o) for o in odds3])
    P2 = np.array([metrics.devig_binary(*o) for o in odds2])
    d3 = float(np.abs(P3 - mult_devig(odds3)).max())
    d2 = float(np.abs(P2 - mult_devig(odds2)).max())
    y = np.array([_OI[r] for r in res])
    ll_mine = float(ll_rows(mult_devig(odds3), y).mean())
    ll_src = metrics.log_loss_1x2(P3, res)
    br_mine = float(brier_rows(mult_devig(odds3), y).mean())
    br_src = metrics.brier_1x2(P3, res)
    llb_mine = float(ll_rows(mult_devig(odds2), 1 - is_over.astype(int)).mean())
    llb_src = metrics.log_loss_binary(P2[:, 0], is_over)
    return {"max_diff_devig_1x2": d3, "max_diff_devig_binary": d2,
            "diff_logloss_1x2": abs(ll_mine - ll_src),
            "diff_brier_1x2": abs(br_mine - br_src),
            "diff_logloss_ou": abs(llb_mine - llb_src)}


def boot_mem(d: np.ndarray, rng, B_: int = B, chunk: int = 500) -> tuple:
    """Bootstrap appaiato identico a `_fase52_common.boot` (stessa statistica,
    stessa distribuzione), ma a blocchi: con n≈12.500 la versione originale
    allocherebbe ~2 GB. Per n piccoli si usa C.boot verbatim."""
    n = len(d)
    if n <= 4000:
        return C.boot(d, rng, B_)
    means = np.empty(B_)
    for i in range(0, B_, chunk):
        k = min(chunk, B_ - i)
        means[i:i + k] = d[rng.integers(0, n, (k, n))].mean(axis=1)
    return (float(d.mean()), float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)), float((means < 0).mean()))


def verdetto(lo: float, hi: float) -> str:
    if hi < 0:
        return "CONCLUSIVO (meglio)"
    if lo > 0:
        return "CONCLUSIVO (peggio)"
    return "nel rumore"


def p_due_code(p_neg: float) -> float:
    return float(2.0 * min(p_neg, 1.0 - p_neg))


# =========================================================================== #
# 3. DATI
# =========================================================================== #
def carica(league: str, seasons: list[str], serve_ou: bool = True) -> pd.DataFrame:
    df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df = df[df.season.isin(seasons)]
    need = ["odds_home", "odds_draw", "odds_away"]
    if serve_ou:
        need += ["odds_over25", "odds_under25"]
    df = df.dropna(subset=need)
    return df.sort_values("date").reset_index(drop=True)


def inverti(odds3: np.ndarray, odds2: np.ndarray, P3: np.ndarray,
            P2: np.ndarray, tag: str, league: str) -> tuple[np.ndarray, np.ndarray]:
    """(λ, μ) impliciti col motore di PRODUZIONE, partendo da probabilita' gia'
    devigate. Cache su scratch (la chiave include il tag del devig)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"rates_{league}_{tag}_rho{RHO:+.2f}.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(P3):
            return c["lam"].to_numpy(), c["mu"].to_numpy()
    lam = np.zeros(len(P3)); mu = np.zeros(len(P3))
    for i in range(len(P3)):
        lam[i], mu[i] = mi.implied_lambda_mu(P3[i, 0], P3[i, 1], P3[i, 2],
                                             P2[i, 0], RHO)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


def prezza(lam: np.ndarray, mu: np.ndarray, hg: np.ndarray,
           ag: np.ndarray) -> dict[str, np.ndarray]:
    """LL per-riga di ogni mercato del listino col router di produzione
    `mi.price_markets` (φ=0, θ=None: il motore nudo, cosi' l'unico fattore che
    cambia e' il DEVIG)."""
    n = len(lam)
    prob = {m: np.zeros(n) for m, _ in BIN_MARKETS}
    p3 = np.zeros((n, 3)); pmg = np.zeros((n, 3)); ex = np.zeros(n)
    for i in range(n):
        d = mi.price_markets(float(lam[i]), float(mu[i]), RHO)
        for m, _ in BIN_MARKETS:
            prob[m][i] = d[m]
        p3[i] = (d["home_win"], d["draw"], d["away_win"])
        pmg[i] = (d["mg_0_1"], d["mg_2_3"], d["mg_4plus"])
        M = d["score_matrix"]
        ex[i] = -np.log(max(M[min(hg[i], MAXG), min(ag[i], MAXG)], 1e-15))
    out = {}
    for m, f in BIN_MARKETS:
        y = f(hg, ag).astype(float)
        p = np.clip(prob[m], 1e-15, 1 - 1e-15)
        out[m] = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
    P3 = p3 / p3.sum(axis=1, keepdims=True)
    out["1X2"] = ll_rows(P3, y3)
    tot = hg + ag
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    out["multigol"] = ll_rows(pmg / pmg.sum(axis=1, keepdims=True), ymg)
    out["risultato_esatto"] = ex
    return out


# =========================================================================== #
# 4. UNA LEGA
# =========================================================================== #
def run_league(league: str, downstream: bool = True) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    df = carica(league, SEASONS)
    odds3 = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    odds2 = df[["odds_over25", "odds_under25"]].to_numpy(float)
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    res = list(df.result)
    y3 = np.array([_OI[r] for r in res])
    is_over = (hg + ag) >= 3
    y2 = 1 - is_over.astype(int)          # colonna 0 = Over -> indice 0 se Over
    seasons = df.season.to_numpy()
    n = len(df)

    out: dict = {"n": int(n), "stagioni": sorted(set(seasons))}
    out["sanity_fonte_unica"] = _verifica_fonte_unica(odds3, odds2, res, is_over)

    # --- margini del book ------------------------------------------------- #
    booksum3 = (1.0 / odds3).sum(axis=1)
    booksum2 = (1.0 / odds2).sum(axis=1)
    out["margine_1x2"] = float(booksum3.mean() - 1.0)
    out["margine_ou"] = float(booksum2.mean() - 1.0)

    # --- i tre devig ------------------------------------------------------- #
    P3_mult = mult_devig(odds3)
    P3_shin, z3 = shin_devig(odds3)
    P2_mult = mult_devig(odds2)
    P2_shin, z2 = shin_devig(odds2)

    # power-devig: η fittato LEAVE-ONE-SEASON-OUT (mai in-sample)
    eta3 = {}; eta2 = {}
    P3_pow = np.zeros_like(P3_mult); P2_pow = np.zeros_like(P2_mult)
    for s in sorted(set(seasons)):
        tr = seasons != s; cur = seasons == s
        eta3[s] = MD.fit_power_eta(odds3[tr], [res[i] for i in np.where(tr)[0]])
        P3_pow[cur] = power_devig(odds3[cur], eta3[s])
        eta2[s] = _fit_power_eta_bin(odds2[tr], y2[tr])
        P2_pow[cur] = power_devig(odds2[cur], eta2[s])
    out["power_eta_loso_1x2"] = {k: float(v) for k, v in eta3.items()}
    out["power_eta_loso_ou"] = {k: float(v) for k, v in eta2.items()}

    # --- differenza tipica fra i due devig --------------------------------- #
    out["scostamento"] = {
        "abs_medio_1x2": float(np.abs(P3_shin - P3_mult).mean()),
        "abs_max_1x2": float(np.abs(P3_shin - P3_mult).max()),
        "abs_medio_ou": float(np.abs(P2_shin - P2_mult).mean()),
        # direzione: quanto Shin sposta il FAVORITO e l'OUTSIDER dell'1X2
        "delta_favorito": float((np.take_along_axis(
            P3_shin, P3_mult.argmax(1)[:, None], 1)
            - P3_mult.max(1, keepdims=True)).mean()),
        "delta_outsider": float((np.take_along_axis(
            P3_shin, P3_mult.argmin(1)[:, None], 1)
            - P3_mult.min(1, keepdims=True)).mean()),
    }

    # --- A MONTE: log-loss e Brier ---------------------------------------- #
    up = {}
    for tag, (P3, P2) in {"mult": (P3_mult, P2_mult),
                          "shin": (P3_shin, P2_shin),
                          "power": (P3_pow, P2_pow)}.items():
        up[tag] = {
            "1X2": {"ll": ll_rows(P3, y3), "brier": brier_rows(P3, y3)},
            "OU25": {"ll": ll_rows(P2, y2), "brier": brier_rows(P2, y2)},
        }
    blocco = {}
    for mk in ("1X2", "OU25"):
        b = {t: {"ll": float(up[t][mk]["ll"].mean()),
                 "brier": float(up[t][mk]["brier"].mean())} for t in up}
        for sfida, rif in (("shin", "mult"), ("power", "mult"), ("shin", "power")):
            key = f"{sfida}_vs_{rif}"
            d_ll = up[sfida][mk]["ll"] - up[rif][mk]["ll"]
            d_br = up[sfida][mk]["brier"] - up[rif][mk]["brier"]
            m, lo, hi, pn = boot_mem(d_ll, rng)
            mb, lob, hib, pnb = boot_mem(d_br, rng)
            per_s = {s: float((d_ll[seasons == s]).mean())
                     for s in sorted(set(seasons))}
            b[key] = {"delta_ll": m, "ci95_ll": [lo, hi],
                      "p_due_code_ll": p_due_code(pn), "p_meglio": pn,
                      "verdetto_ll": verdetto(lo, hi),
                      "delta_brier": mb, "ci95_brier": [lob, hib],
                      "p_due_code_brier": p_due_code(pnb),
                      "verdetto_brier": verdetto(lob, hib),
                      "stagioni_migliorate": int(sum(v < 0 for v in per_s.values())),
                      "stagioni": len(per_s), "delta_per_stagione": per_s}
        blocco[mk] = b
    out["a_monte"] = blocco
    # righe grezze per il pooled (le rimuove il chiamante dopo l'aggregazione)
    out["_righe"] = {t: {mk: {"ll": up[t][mk]["ll"], "brier": up[t][mk]["brier"]}
                         for mk in ("1X2", "OU25")} for t in up}
    out["_seasons"] = seasons

    # --- il parametro z ---------------------------------------------------- #
    out["z"] = {
        "1x2": {"media": float(z3.mean()), "mediana": float(np.median(z3)),
                "sd": float(z3.std()), "p10": float(np.percentile(z3, 10)),
                "p90": float(np.percentile(z3, 90)),
                "per_stagione": {s: float(z3[seasons == s].mean())
                                 for s in sorted(set(seasons))},
                "margine_per_stagione": {
                    s: float(booksum3[seasons == s].mean() - 1.0)
                    for s in sorted(set(seasons))},
                "z_su_margine": float((z3 / (booksum3 - 1.0)).mean()),
                "corr_z_margine_righe": float(np.corrcoef(z3, booksum3 - 1.0)[0, 1])},
        "ou": {"media": float(z2.mean()), "mediana": float(np.median(z2)),
               "sd": float(z2.std()),
               "per_stagione": {s: float(z2[seasons == s].mean())
                                for s in sorted(set(seasons))},
               "z_su_margine": float((z2 / (booksum2 - 1.0)).mean())},
    }

    # --- la famiglia t: quanto correggere? (LOSO) -------------------------- #
    ll_t = {}
    for t in T_GRID:
        ll_t[t] = ll_rows(shin_family(odds3, z3, t), y3)
    sel = np.zeros(n); picks = {}
    for s in sorted(set(seasons)):
        tr = seasons != s; cur = seasons == s
        best = min(T_GRID, key=lambda t: ll_t[t][tr].mean())
        picks[s] = best
        sel[cur] = ll_t[best][cur]
    m, lo, hi, pn = boot_mem(sel - ll_t[0.0], rng)
    out["famiglia_t"] = {
        "curva_in_sample": {str(t): float(ll_t[t].mean()) for t in T_GRID},
        "t_migliore_in_sample": float(min(T_GRID, key=lambda t: ll_t[t].mean())),
        "t_loso_per_stagione": {k: float(v) for k, v in picks.items()},
        "loso_vs_mult": {"delta": m, "ci95": [lo, hi],
                         "p_due_code": p_due_code(pn), "verdetto": verdetto(lo, hi)},
        "ll_t0_mult": float(ll_t[0.0].mean()), "ll_t1_shin": float(ll_t[1.0].mean()),
    }

    # --- A VALLE: il listino market-implied -------------------------------- #
    if downstream:
        giu = {}
        rates = {}
        for tag, (P3, P2) in {"mult": (P3_mult, P2_mult),
                              "shin": (P3_shin, P2_shin),
                              "power": (P3_pow, P2_pow)}.items():
            lam, mu = inverti(odds3, odds2, P3, P2, tag, league)
            rates[tag] = (lam, mu)
            giu[tag] = prezza(lam, mu, hg, ag)
        d_lam = rates["shin"][0] - rates["mult"][0]
        d_mu = rates["shin"][1] - rates["mult"][1]
        blocco = {"tassi": {
            "lam_medio_mult": float(rates["mult"][0].mean()),
            "lam_medio_shin": float(rates["shin"][0].mean()),
            "mu_medio_mult": float(rates["mult"][1].mean()),
            "mu_medio_shin": float(rates["shin"][1].mean()),
            "delta_lam_medio": float(d_lam.mean()),
            "delta_mu_medio": float(d_mu.mean()),
            "delta_lam_abs_medio": float(np.abs(d_lam).mean()),
            "delta_mu_abs_medio": float(np.abs(d_mu).mean())}, "mercati": {}}
        for m_ in MARKETS:
            riga = {"mult": float(giu["mult"][m_].mean()),
                    "shin": float(giu["shin"][m_].mean()),
                    "power": float(giu["power"][m_].mean()), "ancora": m_ in ANCORE}
            for sfida in ("shin", "power"):
                dd = giu[sfida][m_] - giu["mult"][m_]
                mm, lo_, hi_, pn_ = boot_mem(dd, rng)
                riga[f"{sfida}_vs_mult"] = {
                    "delta": mm, "ci95": [lo_, hi_],
                    "p_due_code": p_due_code(pn_), "verdetto": verdetto(lo_, hi_)}
            blocco["mercati"][m_] = riga
        out["a_valle"] = blocco
        out["_valle_righe"] = giu

    out["secondi"] = round(time.time() - t0, 1)
    return out


def _fit_power_eta_bin(odds2: np.ndarray, y: np.ndarray,
                       bounds: tuple[float, float] = (0.5, 2.0)) -> float:
    """Analogo binario di `market_denoise.fit_power_eta` (stessa formula,
    2 esiti invece di 3). y = indice dell'esito (0 = Over)."""
    from scipy.optimize import minimize_scalar
    if len(y) < 30:
        return 1.0

    def loss(eta: float) -> float:
        P = power_devig(odds2, eta)
        return float(-np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1.0))))
    return float(minimize_scalar(loss, bounds=bounds, method="bounded").x)


# =========================================================================== #
# 5. REPLICA FUORI-FINESTRA: solo 1X2, 9 stagioni
# =========================================================================== #
def run_league_9(league: str) -> dict:
    rng = np.random.default_rng(SEED + 1)
    df = carica(league, SEASONS9, serve_ou=False)
    odds3 = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    y3 = np.array([_OI[r] for r in df.result])
    seasons = df.season.to_numpy()
    P_m = mult_devig(odds3); P_s, z = shin_devig(odds3)
    d = ll_rows(P_s, y3) - ll_rows(P_m, y3)
    m, lo, hi, pn = boot_mem(d, rng)
    extra = np.isin(seasons, ["1718", "1819"])
    me, loe, hie, pne = boot_mem(d[extra], rng)
    return {"n": int(len(df)), "delta_9stagioni": m, "ci95": [lo, hi],
            "p_due_code": p_due_code(pn), "verdetto": verdetto(lo, hi),
            "n_extra": int(extra.sum()), "delta_solo_1718_1819": me,
            "ci95_extra": [loe, hie], "verdetto_extra": verdetto(loe, hie),
            "z_medio_1718_1819": float(z[extra].mean()),
            "z_medio_1920_2526": float(z[~extra].mean()),
            "delta_per_stagione": {s: float(d[seasons == s].mean())
                                   for s in sorted(set(seasons))}}


# =========================================================================== #
# 6. MAIN
# =========================================================================== #
def _worker(args):
    league, downstream = args
    return league, run_league(league, downstream), run_league_9(league)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--no-downstream", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    downstream = not args.no_downstream

    print("=" * 100)
    print("DEVIG DI SHIN vs DEVIG MOLTIPLICATIVO — 5 leghe, 7 stagioni (1920→2526)")
    print("ASPETTATIVA DICHIARATA PRIMA: Shin ≥ moltiplicativo in 5/5 leghe; guadagno")
    print("1X2 ~0.0005-0.0010; per-lega NON conclusivo, POOLED conclusivo; O/U ~0;")
    print("a valle il guadagno si diluisce sui mercati DERIVATI.")
    print("=" * 100, flush=True)

    if args.jobs > 1 and len(args.leagues) > 1:
        with Pool(min(args.jobs, len(args.leagues))) as pool:
            got = pool.map(_worker, [(lg, downstream) for lg in args.leagues])
    else:
        got = [_worker((lg, downstream)) for lg in args.leagues]
    per_lega = {lg: r for lg, r, _ in got}
    nove = {lg: r9 for lg, _, r9 in got}

    rng = np.random.default_rng(SEED + 2)

    # ---------------------------------------------------------------- pooled #
    pooled: dict = {}
    for mk in ("1X2", "OU25"):
        blocco = {}
        righe = {t: {m_: np.concatenate([per_lega[lg]["_righe"][t][mk][m_]
                                         for lg in args.leagues])
                     for m_ in ("ll", "brier")} for t in ("mult", "shin", "power")}
        for t in ("mult", "shin", "power"):
            blocco[t] = {"ll": float(righe[t]["ll"].mean()),
                         "brier": float(righe[t]["brier"].mean())}
        for sfida, rif in (("shin", "mult"), ("power", "mult"), ("shin", "power")):
            d_ll = righe[sfida]["ll"] - righe[rif]["ll"]
            d_br = righe[sfida]["brier"] - righe[rif]["brier"]
            m, lo, hi, pn = boot_mem(d_ll, rng)
            mb, lob, hib, pnb = boot_mem(d_br, rng)
            vinte = sum(1 for lg in args.leagues
                        if per_lega[lg]["a_monte"][mk][f"{sfida}_vs_{rif}"]["delta_ll"] < 0)
            blocco[f"{sfida}_vs_{rif}"] = {
                "n": int(len(d_ll)), "delta_ll": m, "ci95_ll": [lo, hi],
                "p_due_code_ll": p_due_code(pn), "verdetto_ll": verdetto(lo, hi),
                "delta_brier": mb, "ci95_brier": [lob, hib],
                "p_due_code_brier": p_due_code(pnb),
                "verdetto_brier": verdetto(lob, hib),
                "leghe_migliorate": f"{vinte}/{len(args.leagues)}",
                "p_test_dei_segni_una_coda": float(0.5 ** len(args.leagues))
                if vinte == len(args.leagues) else None}
        pooled[mk] = blocco

    # pooled a valle
    if downstream:
        pv = {}
        for m_ in MARKETS:
            righe = {t: np.concatenate([per_lega[lg]["_valle_righe"][t][m_]
                                        for lg in args.leagues])
                     for t in ("mult", "shin", "power")}
            riga = {t: float(righe[t].mean()) for t in righe}
            riga["ancora"] = m_ in ANCORE
            for sfida in ("shin", "power"):
                d = righe[sfida] - righe["mult"]
                m, lo, hi, pn = boot_mem(d, rng)
                vinte = sum(1 for lg in args.leagues
                            if per_lega[lg]["a_valle"]["mercati"][m_][f"{sfida}_vs_mult"]["delta"] < 0)
                riga[f"{sfida}_vs_mult"] = {
                    "delta": m, "ci95": [lo, hi], "p_due_code": p_due_code(pn),
                    "verdetto": verdetto(lo, hi),
                    "leghe_migliorate": f"{vinte}/{len(args.leagues)}"}
            pv[m_] = riga
        pooled["a_valle"] = pv

    for lg in args.leagues:
        per_lega[lg].pop("_righe", None)
        per_lega[lg].pop("_seasons", None)
        per_lega[lg].pop("_valle_righe", None)

    # --------------------------------------------------------------- stampa #
    print("\n" + "=" * 100)
    print("A MONTE — il devig come MISURA DI VERITA' del mercato (log-loss; − = Shin meglio)")
    print("=" * 100)
    for mk in ("1X2", "OU25"):
        print(f"\n### {mk}")
        print(f"  {'lega':<16}{'n':>6}{'margine':>9}{'molt.':>9}{'shin':>9}"
              f"{'power':>9}{'Δ shin−molt':>13}{'CI95':>22}{'stag.':>7}  verdetto")
        for lg in args.leagues:
            b = per_lega[lg]["a_monte"][mk]
            s = b["shin_vs_mult"]
            mar = per_lega[lg]["margine_1x2" if mk == "1X2" else "margine_ou"]
            print(f"  {lg:<16}{per_lega[lg]['n']:>6}{mar:>8.2%}{b['mult']['ll']:>9.4f}"
                  f"{b['shin']['ll']:>9.4f}{b['power']['ll']:>9.4f}"
                  f"{s['delta_ll']:>+13.5f}   [{s['ci95_ll'][0]:+.5f},{s['ci95_ll'][1]:+.5f}]"
                  f"{s['stagioni_migliorate']:>4}/{s['stagioni']}  {s['verdetto_ll']}")
        p = pooled[mk]["shin_vs_mult"]
        print(f"  {'POOLED':<16}{p['n']:>6}{'':>9}{pooled[mk]['mult']['ll']:>9.4f}"
              f"{pooled[mk]['shin']['ll']:>9.4f}{pooled[mk]['power']['ll']:>9.4f}"
              f"{p['delta_ll']:>+13.5f}   [{p['ci95_ll'][0]:+.5f},{p['ci95_ll'][1]:+.5f}]"
              f"{'':>7}  {p['verdetto_ll']}  ({p['leghe_migliorate']} leghe)")
        pb = pooled[mk]["shin_vs_mult"]
        print(f"    Brier pooled: molt {pooled[mk]['mult']['brier']:.5f} → shin "
              f"{pooled[mk]['shin']['brier']:.5f}  Δ {pb['delta_brier']:+.6f} "
              f"[{pb['ci95_brier'][0]:+.6f},{pb['ci95_brier'][1]:+.6f}] {pb['verdetto_brier']}")
        pp = pooled[mk]["shin_vs_power"]
        print(f"    Shin vs power-devig (η LOSO): Δ {pp['delta_ll']:+.5f} "
              f"[{pp['ci95_ll'][0]:+.5f},{pp['ci95_ll'][1]:+.5f}] {pp['verdetto_ll']}")

    print("\n" + "=" * 100)
    print("IL PARAMETRO z DI SHIN — livello, epoca, relazione col margine")
    print("=" * 100)
    print(f"  {'lega':<16}{'margine 1X2':>12}{'z medio':>10}{'z/margine':>11}"
          f"{'z sd':>8}{'z 17-19':>9}{'z 25-26':>9}")
    zrows = []
    for lg in args.leagues:
        z = per_lega[lg]["z"]["1x2"]
        ps = z["per_stagione"]
        print(f"  {lg:<16}{per_lega[lg]['margine_1x2']:>11.2%}{z['media']:>10.4f}"
              f"{z['z_su_margine']:>11.3f}{z['sd']:>8.4f}"
              f"{nove[lg]['z_medio_1718_1819']:>9.4f}{ps.get('2526', float('nan')):>9.4f}")
        zrows.append((per_lega[lg]["margine_1x2"], z["media"]))
    if len(zrows) > 2:
        a = np.array(zrows)
        print(f"  corr(z medio, margine) fra le leghe = {np.corrcoef(a[:,0],a[:,1])[0,1]:+.3f}"
              f"  (n={len(zrows)}; ATTENZIONE: z e' determinato dalle quote, la"
              f" correlazione e' in gran parte MECCANICA)")

    print("\n  Quanta correzione vogliono i dati? (famiglia t: 0 = moltiplicativo, 1 = Shin)")
    print(f"  {'lega':<16}{'t* in-sample':>14}{'t LOSO':>28}{'Δ vs molt.':>12}  verdetto")
    for lg in args.leagues:
        f = per_lega[lg]["famiglia_t"]
        picks = sorted(set(f["t_loso_per_stagione"].values()))
        print(f"  {lg:<16}{f['t_migliore_in_sample']:>14.2f}"
              f"{str(picks):>28}{f['loso_vs_mult']['delta']:>+12.5f}  "
              f"{f['loso_vs_mult']['verdetto']}")

    if downstream:
        print("\n" + "=" * 100)
        print("A VALLE — il listino market-implied re-invertito con l'altro devig")
        print("(Δ = shin − molt sul log-loss del mercato; * = ancora dell'inversione)")
        print("=" * 100)
        print(f"  {'mercato':<18}{'molt.':>9}{'shin':>9}{'Δ pooled':>11}"
              f"{'CI95':>24}{'leghe':>8}  verdetto")
        for m_ in MARKETS:
            r = pooled["a_valle"][m_]
            s = r["shin_vs_mult"]
            tag = m_ + (" *" if r["ancora"] else "")
            print(f"  {tag:<18}{r['mult']:>9.4f}{r['shin']:>9.4f}{s['delta']:>+11.5f}"
                  f"   [{s['ci95'][0]:+.5f},{s['ci95'][1]:+.5f}]{s['leghe_migliorate']:>8}"
                  f"  {s['verdetto']}")
        der_meglio = sum(1 for m_ in DERIVATI
                         if pooled["a_valle"][m_]["shin_vs_mult"]["delta"] < 0)
        der_ci = sum(1 for m_ in DERIVATI
                     if pooled["a_valle"][m_]["shin_vs_mult"]["ci95"][1] < 0)
        print(f"\n  Sui {len(DERIVATI)} mercati DERIVATI (non ancore): Shin meglio in "
              f"{der_meglio}, con CI conclusivo in {der_ci}.")

    print("\n" + "=" * 100)
    print("REPLICA FUORI-FINESTRA — solo 1X2, 9 stagioni (aggiunge 2017-18 e 2018-19)")
    print("=" * 100)
    print(f"  {'lega':<16}{'n':>6}{'Δ 9 stag.':>12}{'CI95':>22}"
          f"{'n extra':>9}{'Δ solo extra':>14}")
    for lg in args.leagues:
        r = nove[lg]
        print(f"  {lg:<16}{r['n']:>6}{r['delta_9stagioni']:>+12.5f}"
              f"   [{r['ci95'][0]:+.5f},{r['ci95'][1]:+.5f}]{r['n_extra']:>9}"
              f"{r['delta_solo_1718_1819']:>+14.5f}")

    print("\n  Controllo di sanita' (identita' con la fonte unica src/evaluation/metrics):")
    peggio = max(max(per_lega[lg]["sanity_fonte_unica"].values()) for lg in args.leagues)
    print(f"    scarto massimo su tutte le leghe e tutte le metriche: {peggio:.2e}")

    ris = {"meta": {"finestra": SEASONS, "leghe": args.leagues, "rho": RHO,
                    "bootstrap_B": B, "seed": SEED,
                    "aspettativa_dichiarata": {
                        "shin_meglio_in": "5/5 leghe",
                        "guadagno_1x2_atteso": [0.0005, 0.0010],
                        "per_lega": "non conclusivo",
                        "pooled": "conclusivo",
                        "ou": "effetto ~0",
                        "a_valle": "diluito sui derivati"},
                    "secondi": round(time.time() - t0, 1)},
           "per_lega": per_lega, "pooled": pooled, "nove_stagioni": nove}
    path = OUT / "leve_devig_shin.json"
    path.write_text(json.dumps(ris, indent=2, default=float))
    print(f"\n-> {path}")
    print(f"Tempo totale {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
