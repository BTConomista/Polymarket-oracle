"""Audit di CALIBRAZIONE del motore sulle DUE LEGHE NUOVE (Bundesliga, Ligue 1).

DOMANDA
-------
Il log-loss dice «quanto bene predici», non «le tue probabilita' sono oneste».
Il progetto ha verificato per via diretta sulle 3 leghe storiche che l'oracolo e'
calibrato (`scripts/_run_fase82_verifica_predizioni.py`). Sulle due leghe nuove
non e' mai stato fatto — ed e' il controllo che conta di piu', perche' il valore
residuo del progetto sta nel prezzare CALIBRATO i ~17 mercati che il book NON
quota: li' nessuno ci corregge, e se sbagliamo non ce ne accorgiamo mai.

CHE COSA FA
-----------
1. Path MERCATO (titolare): inverte la chiusura 1X2+O/U nei tassi (lam, mu) col
   codice di produzione (`metrics.devig_*` + `mi.implied_lambda_mu`, rho=-0.06),
   prezza TUTTO il listino Tier 1 con `mi.price_markets` e misura, mercato per
   mercato: curva di affidabilita' (10 fasce), ECE, bias medio con CI95, n per
   fascia. Finestra standard del path mercato: 7 stagioni 1920 -> 2526.
2. Confronto col MERCATO STESSO dove la quota esiste (1X2 e O/U 2.5, devigati):
   siamo calibrati quanto il book? Differenza di ECE e di |bias| con bootstrap
   APPAIATO (stessi indici di ricampionamento per i due prezzi).
3. Mercati SENZA quota (ris. esatto, multigol, total-squadra, clean sheet,
   vince-a-zero, scarto>=2, pari/dispari, doppie chance, GG/NG): unica verifica
   possibile = calibrazione contro la REALTA'. Verdetto mercato per mercato.
4. Effetto delle LEVE sulla CALIBRAZIONE (non solo sul log-loss): router
   double-Poisson theta e phi(|lam-mu|), entrambi con parametri fittati
   LEAVE-ONE-SEASON-OUT (mai in-sample). Il progetto ha gia' visto un caso (la
   Liga) in cui theta raddrizzava il GG (bias -0.036 -> -0.008, ECE 0.036 ->
   0.012) guadagnando pochissimo in log-loss: se succede anche qui e' un
   argomento per adottare la leva anche senza CI conclusivo sul log-loss.
5. Path DC senza quote (walk-forward, 6 stagioni 2021->2526, predizioni gia' in
   `cantiere/out/tracer_pred_*.csv`): quanto e' onesto il predittore standalone.
6. Tabella finale mercato x lega -> affidabile / cautela / non affidabile, col
   criterio NUMERICO dichiarato prima di misurare (sotto).

IL CRITERIO, DICHIARATO PRIMA
-----------------------------
Con n ~ 2.100-2.300 partite anche un modello PERFETTAMENTE calibrato produce un
ECE > 0 per solo rumore campionario. Quindi l'ECE grezzo non e' interpretabile da
solo: serve la sua distribuzione NULLA. Per ogni mercato simulo B_NULL esiti
y* ~ Bernoulli(p) con le MIE stesse p, ricalcolo l'ECE e ne prendo il 95-esimo
percentile (ECE_null95). Definisco r = ECE / ECE_null95.

  affidabile              |bias| < 0.010  E  r <= 1.5
  da usare con cautela    non affidabile-pieno, ma |bias| < 0.025 E r <= 3.0
  non affidabile          |bias| >= 0.025  OPPURE  r > 3.0

(0.010 = un punto percentuale, il piu' piccolo errore che conti davvero per
prezzare; il margine del book e' ~4.8% su tre esiti, cioe' ~1.6 pp per esito.
r <= 1.5 = errore di calibrazione entro una volta e mezza il rumore puro.)

ASPETTATIVE DICHIARATE PRIMA DI GUARDARE I NUMERI
-------------------------------------------------
A1 (sanita'). Sulle 3 leghe storiche, finestra 6 stagioni e theta della verifica
   gia' pubblicata (SA 1.225, PL nessuno, Liga 1.2), il mio apparato deve
   RIPRODURRE bias ed ECE gia' registrati in experiments/runs.jsonl entro 5e-4.
   Se non torna, mi fermo.
A2. Su 1X2 e O/U 2.5 il motore e' ANCORATO al mercato (sono i bersagli
   dell'inversione): calibrazione ~ identica a quella del book
   (|dbias| < 0.003, |dECE| < 0.005). E' un controllo, non «valore».
A3. GG/NG: bias NEGATIVO in entrambe le leghe nuove (la matrice Poisson
   sovra-disperde i gol -> troppi 0-0 marginali -> troppo poco GG), ma piu'
   piccolo in modulo del -0.036 della Liga, perche' theta e' 1.08/1.10 e non
   1.24. Predico bias_GG in [-0.025, 0.000].
A4. Pareggio: bias <= 0, modulo minore del -0.020 della Serie A.
A5. I mercati peggio calibrati saranno gli «estremi»: scarto>=2 (in SA +0.035,
   Liga +0.031 -> mi aspetto positivo anche qui), over 4.5, vince-a-zero.
A6. La leva theta migliora la calibrazione dei mercati sensibili alla
   dispersione (GG, clean sheet, pareggio, scarto) ma di circa un TERZO di
   quanto fa in Liga; non deve peggiorare l'1X2.
A7. Il path DC senza quote e' peggio calibrato del path mercato su (quasi) tutti
   i mercati.

CONFUTAZIONI PROGRAMMATE (prima di dichiarare qualunque risultato)
------------------------------------------------------------------
C1. l'ECE dipende dal binning? Ricalcolo con 5, 10, 20 fasce a larghezza uguale
    E con 10 fasce a QUANTILI. Se il verdetto cambia, il verdetto non vale.
C2. l'ECE osservato e' distinguibile dal rumore? -> distribuzione nulla (sopra).
C3. il bias e' stabile o e' una stagione? -> bias per stagione, sd e min/max.
C4. multiple testing: 24 mercati x 5 leghe = 120 test sul bias. Soglia di
    Bonferroni dichiarata (alpha 0.05/120 -> z = 3.29): quali sopravvivono.
C5. sanita' A1 sopra + riproduzione dei parametri (theta, phi) gia' registrati
    in cantiere/out/tranche3_market_tracer.json.

Uso:  python cantiere/scripts/nuovo_calibrazione.py [--leagues ...] [--quick]
Output: cantiere/out/nuovo_calibrazione.json  (+ stampa leggibile)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scripts import _fase52_common as C           # noqa: E402
from src.data import loader                       # noqa: E402
from src.evaluation import metrics                # noqa: E402
from src.models import market_implied as mi       # noqa: E402
# ECE e statistiche binarie: NON reimplementate, prese dalla verifica gia'
# pubblicata dal progetto (fonte unica anche per questa metrica).
from scripts._run_fase82_verifica_predizioni import (  # noqa: E402
    _ece as ece_progetto, _binary_stats)

OUT = ROOT / "cantiere" / "out"
CACHE = Path(os.environ.get(
    "SCRATCH",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")) / "calibrazione"
SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "cantiere" / "data",
        "ligue_1": ROOT / "cantiere" / "data"}
NUOVE = ["bundesliga", "ligue_1"]
LEAGUES = NUOVE + ["serie_a", "premier_league", "la_liga"]
SEASONS7 = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
SEASONS6 = SEASONS7[1:]
RHO = -0.06
MAXG = mi.MAX_GOALS
SEED = 5150                       # nessun significato oltre la riproducibilita'
B_BOOT = 10_000                   # bootstrap appaiato sul bias (standard progetto)
B_NULL = 2_000                    # distribuzione nulla dell'ECE
B_PAIR = 2_000                    # bootstrap appaiato ECE motore vs book
NBINS = 10
# theta usato dalla verifica gia' pubblicata (per il controllo di sanita' A1)
THETA_PUBBL = {"serie_a": 1.225, "premier_league": None, "la_liga": 1.2}

SOGLIA_BIAS_OK, SOGLIA_BIAS_KO = 0.010, 0.025
SOGLIA_R_OK, SOGLIA_R_KO = 1.5, 3.0

# --------------------------------------------------------------------------- #
# Il listino Tier 1: nome della probabilita' in derive_markets -> esito reale.
# Ricalca cantiere/scripts/leve_theta_griglia.BIN_MARKETS (+ dc_12).
# --------------------------------------------------------------------------- #
BIN_MARKETS: list[tuple[str, object]] = [
    ("home_win",      lambda h, a: h > a),
    ("draw",          lambda h, a: h == a),
    ("away_win",      lambda h, a: a > h),
    ("dc_1x",         lambda h, a: h >= a),
    ("dc_2x",         lambda h, a: a >= h),
    ("dc_12",         lambda h, a: h != a),
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
MK = [m for m, _ in BIN_MARKETS]
# i mercati che il book QUOTA nei nostri dati (gli altri sono ciechi)
QUOTATI = {"home_win", "draw", "away_win", "over_2.5"}


# ------------------------------------------------------------------ dati --- #
def carica(league: str, seasons: list[str]) -> pd.DataFrame:
    """Righe con chiusura 1X2 + O/U 2.5 reale. Per le 3 leghe storiche passa dal
    loader di produzione (identico a `_run_fase81_mega_sweep_mi._load`), per le
    due nuove legge lo snapshot del cantiere con la STESSA logica."""
    if league in NUOVE:
        df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                         dtype={"season": str}, parse_dates=["date"])
    else:
        df = loader.load_league(league)
        df["season"] = df["season"].astype(str)
    df = df[df["season"].isin(seasons)].copy()
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    ok = np.isfinite(df[need].to_numpy()).all(axis=1)
    return df[ok].reset_index(drop=True)


def inverti(df: pd.DataFrame, league: str) -> tuple[np.ndarray, np.ndarray]:
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"rates_{league}_{len(df)}_rho{RHO:+.2f}.csv"
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


def devig_mercato(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Probabilita' devigate del BOOK: (n x 3) per l'1X2 e (n,) per over 2.5."""
    P = np.array([metrics.devig_1x2(h, d, a) for h, d, a in
                  df[["odds_home", "odds_draw", "odds_away"]].to_numpy()])
    po = np.array([metrics.devig_binary(o, u)[0] for o, u in
                   df[["odds_over25", "odds_under25"]].to_numpy()])
    return P, po


# --------------------------------------------------------------- pricing --- #
def prezza(lam, mu, theta_row, phi0_row, kappa_row, hg, ag) -> dict:
    """Prezza tutto il listino con `mi.price_markets` (motore di produzione).
    theta_row/phi0_row sono per-riga (parametri LOSO diversi per stagione)."""
    n = len(lam)
    P = {m: np.zeros(n) for m in MK}
    pmg = np.zeros((n, 3)); p_ex = np.zeros(n)
    top_p = np.zeros(n); top_hit = np.zeros(n)
    for i in range(n):
        th = theta_row[i]
        th = None if (th is None or not np.isfinite(th) or th == 1.0) else float(th)
        d = mi.price_markets(float(lam[i]), float(mu[i]), RHO,
                             phi0=float(phi0_row[i]), kappa=float(kappa_row[i]),
                             dp_theta=th)
        for m in MK:
            P[m][i] = d[m]
        pmg[i] = (d["mg_0_1"], d["mg_2_3"], d["mg_4plus"])
        M = d["score_matrix"]
        p_ex[i] = M[min(hg[i], MAXG), min(ag[i], MAXG)]
        k = np.unravel_index(np.argmax(M), M.shape)
        top_p[i] = M[k]
        top_hit[i] = float(k[0] == hg[i] and k[1] == ag[i])
    return {"bin": P, "mg": pmg, "p_esatto": p_ex,
            "top_p": top_p, "top_hit": top_hit}


# --------------------------------------------------------- calibrazione --- #
def ece_bins(p, y, nbins: int) -> float:
    """ECE a fasce di larghezza uguale, generalizzato a nbins.
    Con nbins=NBINS coincide per costruzione con `_ece` del progetto (verificato
    a runtime dal controllo di sanita')."""
    p = np.asarray(p, float); y = np.asarray(y, float)
    edges = np.linspace(0, 1, nbins + 1)
    e = 0.0
    for i in range(nbins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < nbins - 1 else p <= 1)
        if m.sum() == 0:
            continue
        e += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(e)


def ece_quantile(p, y, nbins: int = NBINS) -> float:
    """ECE a fasce di QUANTILI (decili di probabilita' dichiarata): stesso numero
    di partite per fascia. Serve come confutazione C1 dove la p e' concentrata."""
    p = np.asarray(p, float); y = np.asarray(y, float)
    order = np.argsort(p, kind="stable")
    e = 0.0
    for chunk in np.array_split(order, nbins):
        if len(chunk) == 0:
            continue
        e += (len(chunk) / len(p)) * abs(p[chunk].mean() - y[chunk].mean())
    return float(e)


def curva_affidabilita(p, y, nbins: int = NBINS, quantili: bool = False) -> list:
    p = np.asarray(p, float); y = np.asarray(y, float)
    righe = []
    if quantili:
        order = np.argsort(p, kind="stable")
        for k, chunk in enumerate(np.array_split(order, nbins)):
            if len(chunk) == 0:
                continue
            righe.append({"fascia": k + 1, "lo": float(p[chunk].min()),
                          "hi": float(p[chunk].max()), "n": int(len(chunk)),
                          "p_media": float(p[chunk].mean()),
                          "freq": float(y[chunk].mean())})
        return righe
    edges = np.linspace(0, 1, nbins + 1)
    for i in range(nbins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < nbins - 1 else p <= 1)
        if m.sum() == 0:
            righe.append({"fascia": f"{edges[i]:.1f}-{edges[i+1]:.1f}", "n": 0})
            continue
        righe.append({"fascia": f"{edges[i]:.1f}-{edges[i+1]:.1f}",
                      "n": int(m.sum()), "p_media": float(p[m].mean()),
                      "freq": float(y[m].mean())})
    return righe


def ece_nullo(p, rng, B: int = B_NULL, nbins: int = NBINS) -> tuple[float, float]:
    """Distribuzione dell'ECE SE il modello fosse perfettamente calibrato:
    y* ~ Bernoulli(p) con le nostre stesse p. Ritorna (media, 95-esimo perc.).
    E' il metro per dire se un ECE osservato e' un difetto o solo rumore."""
    p = np.asarray(p, float); n = len(p)
    edges = np.linspace(0, 1, nbins + 1)
    lab = np.clip(np.digitize(p, edges[1:-1], right=False), 0, nbins - 1)
    cnt = np.bincount(lab, minlength=nbins).astype(float)
    psum = np.bincount(lab, weights=p, minlength=nbins)
    w = cnt / n
    pm = np.divide(psum, cnt, out=np.zeros(nbins), where=cnt > 0)
    vals = np.empty(B)
    for b in range(B):
        ys = (rng.random(n) < p).astype(float)
        ysum = np.bincount(lab, weights=ys, minlength=nbins)
        ym = np.divide(ysum, cnt, out=np.zeros(nbins), where=cnt > 0)
        vals[b] = float(np.sum(w * np.abs(pm - ym)))
    return float(vals.mean()), float(np.percentile(vals, 95))


def stat_mercato(p, y, seasons, rng, con_nullo: bool = True) -> dict:
    p = np.asarray(p, float); y = np.asarray(y, float)
    d = p - y                                   # bias per riga
    bias, lo, hi, _ = C.boot(d, rng, B=B_BOOT)
    ece = ece_progetto(p, y)                    # fonte unica (fase 82)
    out = {
        "n": int(len(p)), "p_media": float(p.mean()), "freq": float(y.mean()),
        "bias": float(bias), "bias_ci95": [float(lo), float(hi)],
        "bias_z": float(bias / (d.std(ddof=1) / np.sqrt(len(d)))),
        "ece": float(ece),
        "ece_5": ece_bins(p, y, 5), "ece_20": ece_bins(p, y, 20),
        "ece_q10": ece_quantile(p, y, 10),
        "ll": float(C.ll_bin(p, y).mean()),
        "hit": float(((p > 0.5) == (y == 1)).mean()),
        "hit_base": float(max(y.mean(), 1 - y.mean())),
    }
    # ECE ricalcolato a fasce uguali con nbins=NBINS: deve coincidere con `_ece`
    out["ece_check"] = ece_bins(p, y, NBINS)
    if con_nullo:
        m0, q95 = ece_nullo(p, rng)
        out["ece_null_media"] = m0
        out["ece_null_q95"] = q95
        out["r"] = float(ece / q95) if q95 > 0 else float("nan")
        out["verdetto"] = verdetto(abs(bias), out["r"])
    # confutazione C3: bias per stagione
    per_st = {}
    for s in sorted(set(seasons)):
        m = seasons == s
        if m.sum() > 0:
            per_st[str(s)] = float(d[m].mean())
    out["bias_per_stagione"] = per_st
    v = np.array(list(per_st.values()))
    out["bias_stag_sd"] = float(v.std(ddof=1)) if len(v) > 1 else 0.0
    out["bias_stag_min"] = float(v.min()); out["bias_stag_max"] = float(v.max())
    out["segno_concorde"] = int(np.sum(np.sign(v) == np.sign(bias)))
    return out


def verdetto(abias: float, r: float) -> str:
    if abias >= SOGLIA_BIAS_KO or (np.isfinite(r) and r > SOGLIA_R_KO):
        return "non affidabile"
    if abias < SOGLIA_BIAS_OK and (not np.isfinite(r) or r <= SOGLIA_R_OK):
        return "affidabile"
    return "cautela"


def boot_appaiato_ece(p1, p2, y, rng, B: int = B_PAIR, nbins: int = NBINS):
    """CI95 della differenza ECE(p1) - ECE(p2) con RICAMPIONAMENTO APPAIATO
    (stessi indici per i due prezzi: e' lo stesso insieme di partite).
    <0 = p1 meglio calibrato."""
    p1 = np.asarray(p1, float); p2 = np.asarray(p2, float); y = np.asarray(y, float)
    n = len(y)
    edges = np.linspace(0, 1, nbins + 1)
    l1 = np.clip(np.digitize(p1, edges[1:-1]), 0, nbins - 1)
    l2 = np.clip(np.digitize(p2, edges[1:-1]), 0, nbins - 1)

    def ece_from(lab, p, yv, idx):
        lb = lab[idx]
        cnt = np.bincount(lb, minlength=nbins).astype(float)
        ps = np.bincount(lb, weights=p[idx], minlength=nbins)
        ys = np.bincount(lb, weights=yv[idx], minlength=nbins)
        w = cnt / len(idx)
        pm = np.divide(ps, cnt, out=np.zeros(nbins), where=cnt > 0)
        ym = np.divide(ys, cnt, out=np.zeros(nbins), where=cnt > 0)
        return float(np.sum(w * np.abs(pm - ym)))

    diffs = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, n)
        diffs[b] = ece_from(l1, p1, y, idx) - ece_from(l2, p2, y, idx)
    d0 = ece_progetto(p1, y) - ece_progetto(p2, y)
    return (float(d0), float(np.percentile(diffs, 2.5)),
            float(np.percentile(diffs, 97.5)))


# ------------------------------------------------------------- parametri --- #
def parametri_loso(lam, mu, hg, ag, draw, seasons, seasons_list):
    """theta (MLE double-Poisson) e (phi0, kappa) fittati LEAVE-ONE-SEASON-OUT:
    per la stagione s si usano i parametri stimati sulle ALTRE. Mai in-sample."""
    th, ph = {}, {}
    for s in seasons_list:
        tr = seasons != s
        if tr.sum() == 0 or (seasons == s).sum() == 0:
            continue
        th[s] = C.fit_theta(lam[tr], mu[tr], hg[tr], ag[tr], RHO)
        ph[s] = mi.fit_balance_phi(lam[tr], mu[tr], draw[tr], RHO)
    return th, ph


# ------------------------------------------------------------------ run ---- #
def analizza_lega(league: str, quick: bool = False) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    df = carica(league, SEASONS7)
    lam, mu = inverti(df, league)
    hg = df.home_goals.astype(int).to_numpy()
    ag = df.away_goals.astype(int).to_numpy()
    seasons = df.season.to_numpy()
    n = len(df)
    esiti = {m: f(hg, ag).astype(float) for m, f in BIN_MARKETS}
    print(f"\n{'='*104}\n{league.upper()} — path MERCATO, {n} partite, "
          f"stagioni {SEASONS7[0]}..{SEASONS7[-1]}, rho={RHO}\n{'='*104}", flush=True)

    # parametri fuori campione
    th_loso, ph_loso = parametri_loso(lam, mu, hg, ag, esiti["draw"],
                                      seasons, SEASONS7)
    print("  theta LOSO:", {s: round(v, 4) for s, v in th_loso.items()})
    print("  phi0 LOSO :", {s: round(v[0], 4) for s, v in ph_loso.items()},
          " kappa:", {s: round(v[1], 3) for s, v in ph_loso.items()}, flush=True)

    # tilt del LIVELLO dei tassi, LOSO (`_fase52_common.fit_level`): serve a
    # SEPARARE il difetto EREDITATO dal mercato (i suoi tassi sono alti/bassi)
    # da quello della MATRICE (la forma con cui li trasformiamo in prezzi).
    tilt = {}
    for s in SEASONS7:
        tr = seasons != s
        if tr.sum() == 0 or (seasons == s).sum() == 0:
            continue
        tilt[s] = (C.fit_level(lam[tr], hg[tr]), C.fit_level(mu[tr], ag[tr]))
    print("  tilt LOSO (c_lam, c_mu):",
          {s: (round(a, 4), round(b, 4)) for s, (a, b) in tilt.items()}, flush=True)
    lam_t = lam * np.exp([tilt.get(s, (0.0, 0.0))[0] for s in seasons])
    mu_t = mu * np.exp([tilt.get(s, (0.0, 0.0))[1] for s in seasons])
    res_livello = {
        "lam_medio": float(lam.mean()), "hg_medio": float(hg.mean()),
        "mu_medio": float(mu.mean()), "ag_medio": float(ag.mean()),
        "tot_predetto": float((lam + mu).mean()), "tot_reale": float((hg + ag).mean()),
        "tilt_loso": {s: [float(a), float(b)] for s, (a, b) in tilt.items()},
    }

    uno = np.ones(n)
    th_row = np.array([th_loso.get(s, 1.0) for s in seasons])
    ph0_row = np.array([ph_loso.get(s, (0.0, 0.0))[0] for s in seasons])
    kap_row = np.array([ph_loso.get(s, (0.0, 0.0))[1] for s in seasons])
    zeros = np.zeros(n)
    nan = uno * np.nan

    varianti = {
        "motore": (lam, mu, nan, zeros, zeros),          # liscio (titolare)
        "theta": (lam, mu, th_row, zeros, zeros),
        "phi": (lam, mu, nan, ph0_row, kap_row),
        "theta_phi": (lam, mu, th_row, ph0_row, kap_row),
        "tilt": (lam_t, mu_t, nan, zeros, zeros),
        "tilt_theta": (lam_t, mu_t, th_row, zeros, zeros),
    }
    if quick:
        varianti = {k: varianti[k] for k in ("motore", "theta")}

    prezzi = {}
    for nome, (L, M, tr, p0, kp) in varianti.items():
        prezzi[nome] = prezza(L, M, tr, p0, kp, hg, ag)
        print(f"  prezzato «{nome}» ({time.time()-t0:.0f}s)", flush=True)

    res = {"league": league, "n": n, "stagioni": SEASONS7,
           "theta_loso": {s: float(v) for s, v in th_loso.items()},
           "phi_loso": {s: [float(a), float(b)] for s, (a, b) in ph_loso.items()},
           "livello": res_livello, "varianti": {}}

    # --- calibrazione mercato per mercato, variante per variante ------------ #
    for nome in prezzi:
        rr = {}
        for m in MK:
            rr[m] = stat_mercato(prezzi[nome]["bin"][m], esiti[m], seasons, rng)
        # multigol: calibrazione della classe scelta (argmax) + delle 3 classi
        tot = hg + ag
        ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
        Pmg = prezzi[nome]["mg"]
        conf = Pmg.max(1); pick = Pmg.argmax(1)
        rr["multigol_argmax"] = stat_mercato(conf, (pick == ymg).astype(float),
                                             seasons, rng)
        rr["multigol_argmax"]["ll_3classi"] = float(
            -np.log(np.clip(Pmg[np.arange(n), ymg], 1e-15, None)).mean())
        for k, nm in enumerate(["mg_0_1", "mg_2_3", "mg_4plus"]):
            rr[nm] = stat_mercato(Pmg[:, k], (ymg == k).astype(float),
                                  seasons, rng)
        # risultato esatto: calibrazione della scelta di punta
        rr["esatto_top"] = stat_mercato(prezzi[nome]["top_p"],
                                        prezzi[nome]["top_hit"], seasons, rng)
        rr["esatto_top"]["ll_matrice"] = float(
            -np.log(np.clip(prezzi[nome]["p_esatto"], 1e-15, None)).mean())
        res["varianti"][nome] = rr
        salva_parziale(res)

    # --- confronto col BOOK dove la quota esiste ---------------------------- #
    Pm, po = devig_mercato(df)
    book = {"home_win": Pm[:, 0], "draw": Pm[:, 1], "away_win": Pm[:, 2],
            "over_2.5": po}
    conf_book = {}
    for m, pb in book.items():
        sb = stat_mercato(pb, esiti[m], seasons, rng)
        pe = prezzi["motore"]["bin"][m]
        d0, lo, hi = boot_appaiato_ece(pe, pb, esiti[m], rng)
        conf_book[m] = {"book": sb,
                        "motore_meno_book_ece": d0, "ci95": [lo, hi],
                        "d_bias": float(res["varianti"]["motore"][m]["bias"] - sb["bias"]),
                        "d_ece": float(res["varianti"]["motore"][m]["ece"] - sb["ece"])}
    res["confronto_book"] = conf_book

    # --- curve di affidabilita' (motore liscio) ----------------------------- #
    res["curve"] = {m: {"larghezza_uguale":
                        curva_affidabilita(prezzi["motore"]["bin"][m], esiti[m]),
                        "decili":
                        curva_affidabilita(prezzi["motore"]["bin"][m], esiti[m],
                                           quantili=True)}
                    for m in MK}
    res["secondi"] = round(time.time() - t0, 1)
    salva_parziale(res)
    return res


def analizza_dc(league: str) -> dict:
    """Path DC senza quote: predizioni walk-forward gia' prodotte dal tracer
    (6 stagioni 2021->2526). Calibrazione delle colonne native (1X2, O/U 2.5,
    GG/NG) e dell'intero listino derivato dai (lambda, mu) del modello."""
    rng = np.random.default_rng(SEED)
    fp = OUT / f"tracer_pred_{league}.csv"
    if not fp.exists():
        return {}
    d = pd.read_csv(fp, dtype={"test_season": str})
    hg = d.home_goals.astype(int).to_numpy(); ag = d.away_goals.astype(int).to_numpy()
    seasons = d.test_season.to_numpy()
    n = len(d)
    esiti = {m: f(hg, ag).astype(float) for m, f in BIN_MARKETS}
    out = {"n": n, "stagioni": sorted(set(seasons)), "nativo": {}, "derivato": {}}
    # colonne native del modello
    y3 = np.array([{"H": 0, "D": 1, "A": 2}[r] for r in d.result])
    P3 = d[["m_home", "m_draw", "m_away"]].to_numpy()
    for k, m in enumerate(["home_win", "draw", "away_win"]):
        out["nativo"][m] = stat_mercato(P3[:, k], esiti[m], seasons, rng)
    out["nativo"]["over_2.5"] = stat_mercato(d.m_over.to_numpy(),
                                             esiti["over_2.5"], seasons, rng)
    out["nativo"]["btts"] = stat_mercato(d.m_btts.to_numpy(), esiti["btts"],
                                         seasons, rng)
    out["nativo"]["x2_hit"] = float((P3.argmax(1) == y3).mean())
    # listino completo derivato dai tassi del DC
    lam = d.exp_home_goals.to_numpy(); mu = d.exp_away_goals.to_numpy()
    pr = prezza(lam, mu, np.full(n, np.nan), np.zeros(n), np.zeros(n), hg, ag)
    for m in MK:
        out["derivato"][m] = stat_mercato(pr["bin"][m], esiti[m], seasons, rng)
    out["derivato"]["esatto_top"] = stat_mercato(pr["top_p"], pr["top_hit"],
                                                 seasons, rng)
    return out


def sanita_fase82(league: str) -> dict:
    """CONTROLLO A1: rifaccio la verifica gia' pubblicata (6 stagioni, theta
    pubblicato) e confronto con experiments/runs.jsonl. Deve tornare."""
    rng = np.random.default_rng(SEED)
    df = carica(league, SEASONS6)
    lam, mu = inverti(df, league)
    hg = df.home_goals.astype(int).to_numpy(); ag = df.away_goals.astype(int).to_numpy()
    n = len(df)
    th = THETA_PUBBL[league]
    th_row = np.full(n, th if th else np.nan)
    esiti = {m: f(hg, ag).astype(float) for m, f in BIN_MARKETS}
    pe = prezza(lam, mu, np.full(n, np.nan), np.zeros(n), np.zeros(n), hg, ag)
    pr = prezza(lam, mu, th_row, np.zeros(n), np.zeros(n), hg, ag)
    mio = {"n": n, "engine": {}, "router": {}}
    for m in MK:
        mio["engine"][m] = _binary_stats(pe["bin"][m], esiti[m])
        mio["router"][m] = _binary_stats(pr["bin"][m], esiti[m])
    # atteso: dal registro del progetto
    atteso = None
    for line in open(ROOT / "experiments" / "runs.jsonl"):
        r = json.loads(line)
        if (r.get("config", {}).get("source") == "fase82_verifica_predizioni"
                and r["config"]["league"] == league):
            atteso = r["metrics"]
    diffs = []
    if atteso:
        for lato, chiave in [("engine", "binary_engine"), ("router", "binary_router")]:
            for m, v in atteso[chiave].items():
                if m in mio[lato]:
                    diffs.append(abs(mio[lato][m]["bias"] - v["bias"]))
                    diffs.append(abs(mio[lato][m]["ece"] - v["ece"]))
    return {"n": n, "n_confronti": len(diffs),
            "max_scarto": float(max(diffs)) if diffs else None,
            "atteso_trovato": atteso is not None}


def salva_parziale(res: dict) -> None:
    """Salva subito: se il processo viene interrotto, il lavoro non si perde."""
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(CACHE / f"parziale_{res['league']}.json", "w") as f:
        json.dump(res, f, default=float)


# ------------------------------------------------------------- stampa ------ #
TUTTI_MK = MK + ["mg_0_1", "mg_2_3", "mg_4plus", "multigol_argmax", "esatto_top"]
# Righe che sono il COMPLEMENTO ESATTO di un'altra riga (stesso evento, prob 1−p):
# non sono test indipendenti e vanno contate una volta sola.
COMPLEMENTI = {"dc_2x": "home_win", "dc_12": "draw", "dc_1x": "away_win",
               "away_ov_0.5": "cs_home", "home_ov_0.5": "cs_away",
               "mg_4plus": "over_3.5", "mg_0_1": "over_1.5"}


def stampa_lega(res: dict) -> None:
    v = res["varianti"]
    lv = res.get("livello", {})
    if lv:
        print(f"\n  [livello dei tassi] gol totali predetti dal mercato "
              f"{lv['tot_predetto']:.4f} vs reali {lv['tot_reale']:.4f} "
              f"({100*(lv['tot_predetto']/lv['tot_reale']-1):+.2f}%)  |  "
              f"casa {lv['lam_medio']:.4f} vs {lv['hg_medio']:.4f}, "
              f"ospite {lv['mu_medio']:.4f} vs {lv['ag_medio']:.4f}")
    print(f"\n  {'mercato':<16}{'p̄':>8}{'freq':>8}{'bias':>9}{'CI95 bias':>21}"
          f"{'ECE':>8}{'null95':>8}{'r':>6}  {'verdetto':<15}"
          f"{'θ:bias':>9}{'θ:ECE':>8}{'φ:bias':>9}{'tilt:bias':>10}{'tilt:ECE':>9}")
    for m in TUTTI_MK:
        a = v["motore"][m]
        t = v.get("theta", {}).get(m, {})
        f_ = v.get("phi", {}).get(m, {})
        ti = v.get("tilt", {}).get(m, {})
        nan = float("nan")
        print(f"  {m:<16}{a['p_media']:>8.3f}{a['freq']:>8.3f}{a['bias']:>+9.4f}"
              f" [{a['bias_ci95'][0]:+.4f},{a['bias_ci95'][1]:+.4f}]"
              f"{a['ece']:>8.4f}{a['ece_null_q95']:>8.4f}{a['r']:>6.2f}  "
              f"{a['verdetto']:<15}"
              f"{t.get('bias', nan):>+9.4f}{t.get('ece', nan):>8.4f}"
              f"{f_.get('bias', nan):>+9.4f}"
              f"{ti.get('bias', nan):>+10.4f}{ti.get('ece', nan):>9.4f}")
    print("\n  [confronto col BOOK, solo dove la quota esiste]")
    for m, c in res["confronto_book"].items():
        a = v["motore"][m]
        print(f"    {m:<12} motore bias {a['bias']:+.4f} ECE {a['ece']:.4f} | "
              f"book bias {c['book']['bias']:+.4f} ECE {c['book']['ece']:.4f} | "
              f"ΔECE {c['motore_meno_book_ece']:+.4f} "
              f"[{c['ci95'][0]:+.4f},{c['ci95'][1]:+.4f}]")


def tabella_finale(tutto: dict) -> dict:
    """Griglia mercato x lega col verdetto del criterio dichiarato, piu' la
    correzione per MULTIPLE TESTING (C4) sul bias."""
    leghe = [l for l in LEAGUES if l in tutto["leghe"]]
    n_test = len(TUTTI_MK) * len(leghe)
    z_bonf = 3.29 if n_test <= 200 else 3.5     # alpha 0.05 / ~120 test
    simbolo = {"affidabile": "OK ", "cautela": "~  ", "non affidabile": "NO "}
    print(f"\n\n{'='*104}\nTABELLA FINALE — mercato x lega  "
          f"(OK affidabile / ~ cautela / NO non affidabile)\n"
          f"criterio: |bias|<{SOGLIA_BIAS_OK} e r<={SOGLIA_R_OK} -> OK;  "
          f"|bias|>={SOGLIA_BIAS_KO} o r>{SOGLIA_R_KO} -> NO;  altrimenti ~\n"
          f"* = bias con |z| > {z_bonf} (sopravvive a Bonferroni su "
          f"{n_test} test)\n{'='*104}")
    print(f"  {'mercato':<16}" + "".join(f"{l[:12]:>14}" for l in leghe))
    grid = {}
    for m in TUTTI_MK:
        riga = ""
        grid[m] = {}
        for l in leghe:
            a = tutto["leghe"][l]["varianti"]["motore"][m]
            star = "*" if abs(a["bias_z"]) > z_bonf else " "
            riga += f"{simbolo[a['verdetto']]}{a['bias']:+.3f}{star}".rjust(14)
            grid[m][l] = {"verdetto": a["verdetto"], "bias": a["bias"],
                          "r": a["r"], "bonferroni": abs(a["bias_z"]) > z_bonf}
        print(f"  {m:<16}{riga}")
    tutto["tabella_finale"] = {"grid": grid, "n_test": n_test, "z_bonf": z_bonf}
    # --- POOLED: il bias si replica o e' di una lega sola? ------------------ #
    # ATTENZIONE (onesta' sul conteggio dei test): 7 delle 28 righe sono
    # COMPLEMENTI ESATTI di altre (dc_2x = 1 − home_win, cs_home = 1 −
    # away_ov_0.5, mg_4plus = over_3.5, ...): stesso evento, bias opposto.
    # I mercati INDIPENDENTI sono 21, ed e' su 21 che si corregge Bonferroni.
    uniq = [m for m in TUTTI_MK if m not in COMPLEMENTI]
    z_b21 = 3.04                                   # alpha 0.05/21, due code
    tutto["mercati_indipendenti"] = uniq
    pooled_all = {}
    for scope, sub in [("nuove", [l for l in NUOVE if l in leghe]),
                       ("tutte", leghe)]:
        if not sub:
            continue
        print(f"\n  [pooled {scope}: {', '.join(sub)}]  bias pesato per n, "
              f"z pooled, leghe con lo stesso segno  "
              f"(* = |z|>{z_b21}, Bonferroni su {len(uniq)} mercati indipendenti)")
        pooled = {}
        for m in TUTTI_MK:
            b = np.array([tutto["leghe"][l]["varianti"]["motore"][m]["bias"]
                          for l in sub])
            z = np.array([tutto["leghe"][l]["varianti"]["motore"][m]["bias_z"]
                          for l in sub])
            nn = np.array([tutto["leghe"][l]["n"] for l in sub], float)
            se = np.abs(np.divide(b, z, out=np.full_like(b, np.nan), where=z != 0))
            w = nn / nn.sum()
            bp = float((w * b).sum())
            sep = float(np.sqrt((w ** 2 * se ** 2).sum()))
            zp = bp / sep if sep > 0 else float("nan")
            conc = int(np.sum(np.sign(b) == np.sign(bp)))
            pooled[m] = {"bias": bp, "z": zp, "leghe_stesso_segno": conc,
                         "bias_per_lega": {l: float(x) for l, x in zip(sub, b)}}
            if m in uniq:
                flag = "*" if abs(zp) > z_b21 else (" " if abs(zp) < 1.96 else "+")
                print(f"    {m:<16}{bp:>+9.4f}  z={zp:>+6.2f}{flag}  "
                      f"segno concorde {conc}/{len(sub)}")
        pooled_all[scope] = pooled
    tutto["pooled"] = pooled_all.get("tutte", {})
    tutto["pooled_scope"] = pooled_all
    # riepilogo: quante celle per verdetto
    for l in leghe:
        c = {"affidabile": 0, "cautela": 0, "non affidabile": 0}
        for m in TUTTI_MK:
            c[grid[m][l]["verdetto"]] += 1
        print(f"  {l:<16} affidabili {c['affidabile']}/{len(TUTTI_MK)}, "
              f"cautela {c['cautela']}, non affidabili {c['non affidabile']}")
        tutto["tabella_finale"].setdefault("conteggi", {})[l] = c
    return tutto


def confuta_rho(leghe: list[str]) -> dict:
    """CONFUTAZIONE del risultato principale (GG/NG sotto-prezzato).

    Spiegazione alternativa: non e' la dispersione dei marginali, e' la
    correzione di Dixon-Coles rho = −0.06 (fissa, mai ri-tarata fuori dalla
    Serie A) che sposta proprio le celle 0-0/0-1/1-0/1-1, cioe' esattamente
    quelle che decidono il GG/NG. Se bastasse un rho diverso a raddrizzare il
    GG, la lettura «sotto-dispersione» cadrebbe.

    Rifaccio inversione E matrice con rho coerente in {0, −0.03, −0.06, −0.10}
    e guardo il bias del GG/NG. Riporto anche il rho che azzererebbe il bias."""
    fuori = {}
    rng = np.random.default_rng(SEED)
    for league in leghe:
        df = carica(league, SEASONS7)
        hg = df.home_goals.astype(int).to_numpy()
        ag = df.away_goals.astype(int).to_numpy()
        y = ((hg >= 1) & (ag >= 1)).astype(float)
        n = len(df)
        riga = {}
        for rho in [0.0, -0.03, -0.06, -0.10, -0.15]:
            fp = CACHE / f"rates_{league}_{n}_rho{rho:+.2f}.csv"
            if fp.exists() and len(pd.read_csv(fp)) == n:
                c = pd.read_csv(fp)
                lam, mu = c["lam"].to_numpy(), c["mu"].to_numpy()
            else:
                lam = np.zeros(n); mu = np.zeros(n)
                for i, r in enumerate(df.itertuples()):
                    pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw,
                                                   r.odds_away)
                    pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
                    lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, rho)
                CACHE.mkdir(parents=True, exist_ok=True)
                pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
            p = np.array([mi.price_markets(float(lam[i]), float(mu[i]), rho)["btts"]
                          for i in range(n)])
            riga[f"{rho:+.2f}"] = {"bias": float(p.mean() - y.mean()),
                                   "ece": float(ece_progetto(p, y)),
                                   "ll": float(C.ll_bin(p, y).mean())}
            print(f"  {league:<12} rho {rho:+.2f}: GG bias "
                  f"{riga[f'{rho:+.2f}']['bias']:+.4f}  ECE "
                  f"{riga[f'{rho:+.2f}']['ece']:.4f}  LL "
                  f"{riga[f'{rho:+.2f}']['ll']:.4f}", flush=True)
        fuori[league] = riga
    return fuori


def replica_pubblicata(tutto: dict) -> dict:
    """Le leghe non ricalcolate qui (per tempo macchina) hanno gia' i numeri di
    calibrazione nel registro del progetto, su finestra 6 stagioni: li rileggo
    tali e quali. NON li mescolo con i miei (finestra diversa): servono solo a
    dire se il segno del bias si replica anche li'."""
    fuori = {}
    for line in open(ROOT / "experiments" / "runs.jsonl"):
        r = json.loads(line)
        c = r.get("config", {})
        if c.get("source") != "fase82_verifica_predizioni":
            continue
        lg = c["league"]
        if lg in tutto["leghe"]:
            continue                      # ricalcolata da me: uso la mia
        fuori[lg] = {"finestra": "6 stagioni 2021..2526 (registro del progetto)",
                     "n": r["metrics"]["n"],
                     "motore": {m: {"bias": v["bias"], "ece": v["ece"]}
                                for m, v in r["metrics"]["binary_engine"].items()},
                     "theta": {m: {"bias": v["bias"], "ece": v["ece"]}
                               for m, v in r["metrics"]["binary_router"].items()}}
    if fuori:
        print(f"\n{'='*104}\nREPLICA sulle leghe NON ricalcolate qui "
              f"(numeri gia' pubblicati, finestra 6 stagioni)\n{'='*104}")
        print(f"  {'mercato':<16}" + "".join(f"{l[:14]:>26}" for l in fuori))
        for m in MK:
            riga = ""
            for l, d in fuori.items():
                a = d["motore"].get(m); b = d["theta"].get(m)
                if a is None:
                    riga += "—".rjust(26); continue
                riga += (f"bias{a['bias']:+.4f} θ{b['bias']:+.4f} "
                         f"ECE{a['ece']:.3f}").rjust(26)
            print(f"  {m:<16}{riga}")
    tutto["replica_pubblicata"] = fuori
    return tutto


def stampa_dc(tutto: dict) -> None:
    """Path DC senza quote: quanto e' onesto il predittore standalone, e quanto
    perde rispetto al path mercato sulla stessa lega (A7)."""
    if not tutto.get("dc"):
        return
    print(f"\n{'='*104}\nPATH DC SENZA QUOTE (walk-forward 6 stagioni) — bias ed "
          f"ECE, confronto col path MERCATO della stessa lega\n{'='*104}")
    print(f"  {'lega':<16}{'mercato':<14}{'bias DC':>10}{'ECE DC':>9}"
          f"{'bias mkt':>10}{'ECE mkt':>9}   nota")
    for l, d in tutto["dc"].items():
        if not d:
            continue
        for m in ["home_win", "draw", "away_win", "over_2.5", "btts", "cs_home",
                  "home_by_2plus", "esatto_top"]:
            a = d.get("derivato", {}).get(m)
            if a is None:
                continue
            b = tutto["leghe"].get(l, {}).get("varianti", {}).get("motore", {}).get(m, {})
            peggio = ("DC peggio" if abs(a["bias"]) > abs(b.get("bias", 0))
                      else "DC meglio")
            print(f"  {l:<16}{m:<14}{a['bias']:>+10.4f}{a['ece']:>9.4f}"
                  f"{b.get('bias', float('nan')):>+10.4f}"
                  f"{b.get('ece', float('nan')):>9.4f}   {peggio}")


def effetto_leve(tutto: dict) -> dict:
    """La leva RADDRIZZA la calibrazione? Test pulito e senza ricampionare i
    prezzi (che sono deterministici).

    Sia p̄_m la probabilita' media del motore liscio, p̄_L quella con la leva,
    ȳ la frequenza osservata. Lo spostamento D = p̄_L − p̄_m NON ha incertezza
    (dipende solo dai prezzi). L'unica quantita' aleatoria e' ȳ. Allora:

        |p̄_L − ȳ| < |p̄_m − ȳ|   <=>   ȳ sta oltre il PUNTO MEDIO (p̄_L+p̄_m)/2
                                        nella direzione dello spostamento

    quindi il test «la leva riduce il bias» e' un test su ȳ contro la soglia
    nota mid = (p̄_L+p̄_m)/2:   z = (ȳ − mid)/se · segno(D),  se = √(ȳ(1−ȳ)/n).
    Riporto anche la QUOTA di correzione servita: D / (ȳ − p̄_m).
    """
    leghe = [l for l in LEAGUES if l in tutto["leghe"]]
    fuori = {}
    for leva in ["theta", "phi", "tilt", "theta_phi", "tilt_theta"]:
        if leva not in tutto["leghe"][leghe[0]]["varianti"]:
            continue
        righe = {}
        print(f"\n{'='*104}\nEFFETTO DELLA LEVA «{leva}» SULLA CALIBRAZIONE "
              f"(D = spostamento, quota = D/(freq−p̄ motore), z = «riduce il "
              f"bias»)\n{'='*104}")
        print(f"  {'mercato':<16}" + "".join(f"{l[:11]:>26}" for l in leghe))
        for m in TUTTI_MK:
            riga = ""
            righe[m] = {}
            zs, ns = [], []
            for l in leghe:
                a = tutto["leghe"][l]["varianti"]["motore"][m]
                b = tutto["leghe"][l]["varianti"][leva][m]
                n = a["n"]; y = a["freq"]
                D = b["p_media"] - a["p_media"]
                gap = y - a["p_media"]
                mid = (b["p_media"] + a["p_media"]) / 2
                se = np.sqrt(max(y * (1 - y), 1e-9) / n)
                z = float(np.sign(D) * (y - mid) / se) if D != 0 else 0.0
                quota = float(D / gap) if abs(gap) > 1e-9 else float("nan")
                dbias = abs(b["bias"]) - abs(a["bias"])
                righe[m][l] = {"D": float(D), "quota": quota, "z": z,
                               "d_abs_bias": float(dbias),
                               "d_ece": float(b["ece"] - a["ece"])}
                zs.append(z); ns.append(n)
                riga += f"D{D:+.4f} z{z:+5.2f} ΔECE{b['ece']-a['ece']:+.4f}".rjust(26)
            # Stouffer: combina le leghe (stesso segno = replica)
            zc = float(np.sum(zs) / np.sqrt(len(zs))) if zs else float("nan")
            righe[m]["_pooled_z"] = zc
            print(f"  {m:<16}{riga}   [z pooled {zc:+.2f}]")
        fuori[leva] = righe
    tutto["effetto_leve"] = fuori
    return tutto


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-dc", action="store_true")
    ap.add_argument("--post", action="store_true",
                    help="rifa' solo tabella finale/pooled/leve dal JSON gia' scritto")
    ap.add_argument("--confuta-rho", action="store_true",
                    help="confutazione: il difetto sul GG/NG e' colpa di rho?")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.confuta_rho:
        with open(OUT / "nuovo_calibrazione.json") as f:
            tutto = json.load(f)
        print("CONFUTAZIONE — il GG/NG sotto-prezzato e' colpa del rho fisso?")
        tutto["confutazione_rho"] = confuta_rho(
            [l for l in args.leagues if l in tutto["leghe"]])
        with open(OUT / "nuovo_calibrazione.json", "w") as f:
            json.dump(tutto, f, indent=1, default=float)
        return 0
    if args.post:
        with open(OUT / "nuovo_calibrazione.json") as f:
            tutto = json.load(f)
        tutto = tabella_finale(tutto)
        tutto = effetto_leve(tutto)
        tutto = replica_pubblicata(tutto)
        stampa_dc(tutto)
        with open(OUT / "nuovo_calibrazione.json", "w") as f:
            json.dump(tutto, f, indent=1, default=float)
        print(f"\nScritto {OUT/'nuovo_calibrazione.json'}")
        return 0
    tutto = {"criterio": {
        "bias_ok": SOGLIA_BIAS_OK, "bias_ko": SOGLIA_BIAS_KO,
        "r_ok": SOGLIA_R_OK, "r_ko": SOGLIA_R_KO,
        "nota": "r = ECE / 95-esimo percentile dell'ECE sotto calibrazione "
                "perfetta (parametric bootstrap y*~Bernoulli(p), B=%d)" % B_NULL},
        "rho": RHO, "seed": SEED, "B_boot": B_BOOT, "B_null": B_NULL,
        "leghe": {}, "dc": {}, "sanita": {}}

    # --- controllo di sanita' A1 (prima di tutto) --------------------------- #
    print("CONTROLLO DI SANITA' A1 — riproduco la verifica gia' pubblicata")
    for lg in ["serie_a", "premier_league", "la_liga"]:
        s = sanita_fase82(lg)
        tutto["sanita"][lg] = s
        print(f"  {lg:<16} n={s['n']}  confronti={s['n_confronti']}  "
              f"scarto massimo = {s['max_scarto']:.2e}")
    with open(OUT / "nuovo_calibrazione.json", "w") as f:
        json.dump(tutto, f, indent=1, default=float)

    for lg in args.leagues:
        res = analizza_lega(lg, quick=args.quick)
        stampa_lega(res)
        tutto["leghe"][lg] = res
        if not args.no_dc:
            tutto["dc"][lg] = analizza_dc(lg)
        with open(OUT / "nuovo_calibrazione.json", "w") as f:
            json.dump(tutto, f, indent=1, default=float)
    tutto = tabella_finale(tutto)
    tutto = effetto_leve(tutto)
    tutto = replica_pubblicata(tutto)
    stampa_dc(tutto)
    with open(OUT / "nuovo_calibrazione.json", "w") as f:
        json.dump(tutto, f, indent=1, default=float)
    print(f"\nScritto {OUT/'nuovo_calibrazione.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
