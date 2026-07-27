#!/usr/bin/env python3
"""Il GG/NG contro quote REALI (1xBet, chiusura, 2017-20, 5 leghe).

PERCHE'
-------
Il protocollo del progetto (CLAUDE.md §1.8) poggia su una premessa:

    «il GG/NG non ha quote nei dati (football-data non le include), quindi e'
     l'unico mercato dove non possiamo dimostrare l'efficienza del mercato —
     l'unico con "spazio" non ancora chiuso. Priorita' li'.»

Le quote GG/NG ORA esistono: `data/ricerca_esterna/footiqo_*.json` porta la
CHIUSURA 1xBet di 1X2, O/U 0.5/1.5/2.5/3.5/4.5 e GG/NG (xbetCloseBTTSY /
xbetCloseBTTSN) per 5 leghe x 3 stagioni (2017-18, 2018-19, 2019-20).
La premessa e' caduta: questo script la verifica.

LE DOMANDE (nell'ordine del compito)
------------------------------------
 D1. Il mercato GG/NG e' efficiente/informativo? Quanto, rispetto alla baseline
     "frequenza costante di lega"? E rispetto a quanto e' informativo l'O/U 2.5
     dello STESSO book sulle STESSE partite (due letture della stessa
     distribuzione di gol: lo scarto dice quanto il book *lavora* il GG/NG)?
 D2. Il nostro prezzo GG/NG batte il book? Predittori confrontati sulle stesse
     partite:
       (a)  market-implied dalle quote 1X2+O/U 2.5 dello STESSO book 1xBet
            -> test di COERENZA INTERNA: la nostra matrice, nutrita coi prezzi
               del book, riproduce il prezzo GG/NG del book?
       (a2) market-implied dalla SCALETTA COMPLETA del book (1X2 + 5 linee O/U)
            -> variante ESPLORATIVA: usa piu' informazione del book stesso.
       (b1) market-implied dallo snapshot: 1X2 di CHIUSURA (media multi-book,
            football-data) + O/U di APERTURA (reale). PRIMARIA per il 2017-19,
            perche' e' l'unico input O/U REALE che il progetto ha in quegli anni.
       (b2) stessa cosa ma con la STIMA di chiusura O/U del progetto
            (data/estimates/ou_close_2017_19.csv + data/estimates/...).
            SECONDARIA e dichiarata: i coefficienti della stima sono fittati su
            stagioni SUCCESSIVE (anti-causale) -> va letta come benchmark
            storico, non come predizione.
       (b0) 1X2 + O/U di CHIUSURA reali dello snapshot: esiste SOLO dal 2019-20
            (blocco di controllo).
       (c)  Dixon-Coles gol+xG walk-forward (nessuna quota). Solo 2018-19 e
            2019-20: per il 2017-18 non esiste storico precedente negli snapshot
            e `run_backtest` fallisce (verificato) -> escluso e dichiarato.
 D3. Le leve del progetto associate a quel mercato aiutano PROPRIO li'?
       L1 ricalibrazione del LIVELLO dei tassi (mu, e lambda+mu), LOSO per-lega
          e LOLO pooled (i due fronti del principio §1.9);
       L2 phi(|lambda-mu|) (Fase 35) e la sua versione COSTANTE (kappa=0).
 D4. ROI, SOLO se il nostro prezzo batte il book in log-loss.

METODO (vincolante)
-------------------
- devig: `metrics.devig_binary` / `metrics.devig_1x2` (fonte unica del progetto);
- log-loss binaria: `ll_bin` identica a `scripts/_run_market_implied.ll_bin`;
  Brier: `metrics.brier_binary`; log-loss aggregata: `metrics.log_loss_binary`;
- inversione e pricing: `src/models/market_implied.py` di PRODUZIONE
  (`implied_lambda_mu`, `price_markets`, `fit_balance_phi`), rho = -0.06;
- livelli: `_fase52_common.fit_level` (MLE Poisson, c = log(sum y / sum tasso));
- bootstrap appaiato B=10.000 con `_fase52_common.boot`, verdetto esplicito
  CONCLUSIVO / nel rumore;
- ogni parametro FUORI CAMPIONE (LOSO o LOLO): mai fit e valutazione sugli
  stessi dati.

ASPETTATIVA DICHIARATA PRIMA DI MISURARE (dal compito, ripetuta qui perche'
resti nel file insieme ai numeri):
  * il mercato GG/NG e' informativo ma MENO lavorato dell'1X2 (mercato
    secondario di un solo book);
  * il nostro market-implied dalle quote dello STESSO book sara' molto vicino
    al prezzo GG/NG del book;
  * il DC standalone perdera';
  * un edge, se appare, e' quasi certamente il margine del book letto male:
    va cercato PRIMA di crederci.

MULTIPLE TESTING: le comparazioni pre-dichiarate contro il book sono 6 sul
blocco principale (a, a2, b1, b2, c, + il migliore delle leve). Bonferroni a
6 test => soglia alpha 0.0083 (CI 99.17%). Il verdetto headline lo dichiara.

USO
---
  python scripts/ggng_contro_quote.py --step dati
  python scripts/ggng_contro_quote.py --step dc      # ~10 min, 2 proc
  python scripts/ggng_contro_quote.py --step analisi
  python scripts/ggng_contro_quote.py                # tutto
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

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.data import database, sources  # noqa: E402
from src.evaluation import metrics  # noqa: E402
from src.models import market_implied as mi  # noqa: E402
from _fase52_common import boot, fit_level  # noqa: E402

# --------------------------------------------------------------------------- #
# Costanti
# --------------------------------------------------------------------------- #
OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
RIC = ROOT / "data" / "ricerca_esterna"
SCRATCH = Path(os.environ.get(
    "GGNG_SCRATCH",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad/ggng"))
JSON_OUT = OUT / "ggng_contro_quote.json"

LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
SEASON_LABELS = {"2017/2018": "1718", "2018/2019": "1819", "2019/2020": "1920"}
BLOCCO_PRINC = ["1718", "1819"]      # finestra bersaglio (quote 1xBet, no O/U close)
BLOCCO_CTRL = ["1920"]               # controllo (O/U close reale nello snapshot)
DC_SEASONS = ["1819", "1920"]        # 1718 impossibile: nessuno storico

SNAP = {
    "serie_a": ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga": ROOT / "data" / "la_liga_matches.csv",
    "bundesliga": ROOT / "data" / "bundesliga_matches.csv",
    "ligue_1": ROOT / "data" / "ligue_1_matches.csv",
}
STIME = [ROOT / "data" / "estimates" / "ou_close_2017_19.csv",
         ROOT / "data" / "estimates" / "ou_close_2017_19_nuove_leghe.csv"]

RHO = -0.06
B = 10_000
SEED = 2026_07_26

# alias residui footiqo -> nome canonico (da `_valida_footiqo.py`, gia' verificati)
EXTRA_ALIAS = {
    "Manchester Utd": "Man United",
    "Atl. Madrid": "Ath Madrid",
    "Dep. La Coruna": "La Coruna",
    "B. Monchengladbach": "M'gladbach",
    "Schalke": "Schalke 04",
    "Dusseldorf": "Fortuna Dusseldorf",
    "PSG": "Paris SG",
}
OU_LINES = ["05", "15", "25", "35", "45"]
OU_THR = {"05": 0.5, "15": 1.5, "25": 2.5, "35": 3.5, "45": 4.5}

# Config ufficiale del DC (src/config.py, identica per le 5 leghe tranne delta;
# qui si usa quella Serie A come nel tracer delle leghe nuove).
DC_CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
              blend_signal="xg", promoted_prior=(0.23, 0.23))


# --------------------------------------------------------------------------- #
# Utilita' metriche (fonte unica del progetto)
# --------------------------------------------------------------------------- #
def ll_bin(p, y):
    """Identica a `scripts/_run_market_implied.ll_bin`."""
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def verdetto(d, lo, hi, n_test: int = 1):
    """Verdetto esplicito. d<0 = il primo termine e' MIGLIORE."""
    if lo > 0:
        base = "PEGGIO (CI95 conclusivo)"
    elif hi < 0:
        base = "MEGLIO (CI95 conclusivo)"
    else:
        base = "nel rumore"
    return base


def confronto(ll_a, ll_b, rng, etichetta: str = "") -> dict:
    """Bootstrap appaiato di (ll_a - ll_b). Negativo = A meglio di B."""
    d = np.asarray(ll_a, float) - np.asarray(ll_b, float)
    m, lo, hi, p_neg = boot(d, rng, B)
    return {"etichetta": etichetta, "n": int(len(d)),
            "ll_a": float(np.mean(ll_a)), "ll_b": float(np.mean(ll_b)),
            "delta": m, "ci95": [lo, hi], "P(A_meglio)": p_neg,
            "verdetto": verdetto(m, lo, hi)}


def calibrazione(p, y) -> dict:
    """Media prevista vs osservata + pendenza logistica (1.0 = calibrato)."""
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    z = np.log(p / (1 - p))

    def nll(par):
        q = 1.0 / (1.0 + np.exp(-(par[0] + par[1] * z)))
        q = np.clip(q, 1e-12, 1 - 1e-12)
        return -np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))

    r = minimize(nll, [0.0, 1.0], method="L-BFGS-B")
    return {"p_medio": float(p.mean()), "freq_reale": float(y.mean()),
            "bias": float(p.mean() - y.mean()),
            "intercetta": float(r.x[0]), "pendenza": float(r.x[1])}


# --------------------------------------------------------------------------- #
# PASSO 1 — dataset: join footiqo <-> snapshot, con i lucchetti
# --------------------------------------------------------------------------- #
def canon(name) -> str:
    n = sources.canonical_team(str(name).strip())
    n = EXTRA_ALIAS.get(n, n)
    return sources.canonical_team(n)


def _load_footiqo(lega: str, label: str) -> pd.DataFrame:
    fp = RIC / f"footiqo_{lega}_{label.replace('/', '-')}.json"
    d = pd.DataFrame(json.loads(fp.read_text(encoding="utf-8")))
    for c in d.columns:
        if c.startswith("xbetClose"):
            d[c] = pd.to_numeric(d[c].replace("", np.nan), errors="coerce")
    d["date_fq"] = pd.to_datetime(d["matchDate"], format="%d-%m-%y %H:%M").dt.normalize()
    d["home_team"] = d["homeTeam"].map(canon)
    d["away_team"] = d["awayTeam"].map(canon)
    return d


def _load_footiqo_gol(lega: str, label: str) -> pd.DataFrame | None:
    fp = RIC / f"footiqo_gol_{lega}_{label.replace('/', '-')}.json"
    if not fp.exists():
        return None
    g = pd.DataFrame(json.loads(fp.read_text(encoding="utf-8")))
    g["home_team"] = g["homeTeam"].map(canon)
    g["away_team"] = g["awayTeam"].map(canon)
    g["fq_hg"] = pd.to_numeric(g["ftHomeTeamGoals"], errors="coerce")
    g["fq_ag"] = pd.to_numeric(g["ftAwayTeamGoals"], errors="coerce")
    return g[["home_team", "away_team", "fq_hg", "fq_ag"]]


def _load_stime() -> pd.DataFrame:
    fr = []
    for fp in STIME:
        if not fp.exists():
            continue
        d = pd.read_csv(fp, dtype={"season": str})
        fr.append(d[["league", "season", "date", "home_team", "away_team",
                     "p_over25_close_est"]])
    s = pd.concat(fr, ignore_index=True)
    s["date"] = pd.to_datetime(s["date"]).dt.normalize()
    s["home_team"] = s["home_team"].map(canon)
    s["away_team"] = s["away_team"].map(canon)
    return s


def costruisci_dati() -> tuple[pd.DataFrame, dict]:
    stime = _load_stime()
    lock = {"gol_confrontati": 0, "gol_identici": 0, "discordanze_gol": [],
            "join": {}, "scartate": {}}
    frames = []
    for lega in LEAGUES:
        snap = pd.read_csv(SNAP[lega], dtype={"season": str}, parse_dates=["date"])
        snap["date"] = snap["date"].dt.normalize()
        snap["home_team"] = snap["home_team"].map(canon)
        snap["away_team"] = snap["away_team"].map(canon)
        for label, st in SEASON_LABELS.items():
            fq = _load_footiqo(lega, label)
            s = snap[snap["season"] == st].copy()
            m = s.merge(fq, on=["home_team", "away_team"], how="left",
                        suffixes=("", "_fq"))
            m["lega"] = lega
            m["delta_giorni"] = (m["date_fq"] - m["date"]).dt.days
            # --- lucchetto 1: i gol della fonte coincidono coi nostri? -------
            gol = _load_footiqo_gol(lega, label)
            if gol is not None:
                m = m.merge(gol, on=["home_team", "away_team"], how="left")
                v = m.dropna(subset=["fq_hg", "fq_ag"])
                ug = int(((v["fq_hg"] == v["home_goals"]) &
                          (v["fq_ag"] == v["away_goals"])).sum())
                lock["gol_confrontati"] += int(len(v))
                lock["gol_identici"] += ug
                bad = v[(v["fq_hg"] != v["home_goals"]) |
                        (v["fq_ag"] != v["away_goals"])]
                for r in bad.itertuples():
                    lock["discordanze_gol"].append(
                        f"{lega} {st} {r.home_team}-{r.away_team}: "
                        f"snapshot {int(r.home_goals)}-{int(r.away_goals)} "
                        f"footiqo {int(r.fq_hg)}-{int(r.fq_ag)}")
            else:
                m["fq_hg"] = np.nan
                m["fq_ag"] = np.nan
            lock["join"][f"{lega}_{st}"] = {
                "righe_snapshot": int(len(s)),
                "appaiate": int(m["date_fq"].notna().sum()),
                "delta_giorni_oltre_1": int(
                    m["delta_giorni"].dropna().abs().gt(1).sum()),
            }
            frames.append(m)
    A = pd.concat(frames, ignore_index=True)
    A = A.merge(stime, left_on=["lega", "season", "date", "home_team", "away_team"],
                right_on=["league", "season", "date", "home_team", "away_team"],
                how="left", suffixes=("", "_st"))

    # --- lucchetto 2: si scarta chi non ha il dato che serve ------------------
    prima = len(A)
    A = A[A["xbetCloseBTTSY"].notna() & A["xbetCloseBTTSN"].notna()].copy()
    lock["scartate"]["senza_quota_GGNG"] = int(prima - len(A))
    prima = len(A)
    A = A[A["xbetClose1FT"].notna() & A["xbetCloseXFT"].notna() &
          A["xbetClose2FT"].notna() & A["xbetCloseOver25"].notna() &
          A["xbetCloseUnder25"].notna()].copy()
    lock["scartate"]["senza_1X2_o_OU25_del_book"] = int(prima - len(A))
    prima = len(A)
    A = A[A["odds_home"].notna() & A["odds_draw"].notna() &
          A["odds_away"].notna()].copy()
    lock["scartate"]["senza_1X2_snapshot"] = int(prima - len(A))
    prima = len(A)
    A = A[A["delta_giorni"].abs() <= 1].copy()
    lock["scartate"]["data_incoerente_oltre_1_giorno"] = int(prima - len(A))

    A["y_btts"] = ((A["home_goals"] >= 1) & (A["away_goals"] >= 1)).astype(float)
    A["y_over25"] = ((A["home_goals"] + A["away_goals"]) >= 3).astype(float)
    A = A.sort_values(["lega", "season", "date"]).reset_index(drop=True)
    lock["n_finale"] = int(len(A))
    lock["n_per_stagione"] = A.groupby("season").size().to_dict()
    lock["n_per_lega"] = A.groupby("lega").size().to_dict()
    return A, lock


# --------------------------------------------------------------------------- #
# PASSO 2 — Dixon-Coles walk-forward (path c)
# --------------------------------------------------------------------------- #
_orig_snapshot_path = database.snapshot_path


def _snapshot_path(league_key: str = "serie_a") -> Path:
    if league_key in nuove_leghe.NEW_LEAGUES:
        return ROOT / "data" / f"{league_key}_matches.csv"
    return _orig_snapshot_path(league_key)


database.snapshot_path = _snapshot_path


def _dc_worker(arg):
    lega, st = arg
    from backtest import run_backtest
    t0 = time.time()
    df = run_backtest(lega, st, DC_CFG["half_life_days"],
                      shrinkage=DC_CFG["shrinkage"],
                      shots_blend=DC_CFG["shots_blend"],
                      blend_signal=DC_CFG["blend_signal"],
                      promoted_prior=DC_CFG["promoted_prior"], verbose=False)
    df["lega"] = lega
    df["season"] = st
    fp = SCRATCH / f"dc_{lega}_{st}.csv"
    df.to_csv(fp, index=False)
    return f"{lega} {st}: {len(df)} gare in {time.time()-t0:.0f}s -> {fp.name}"


def esegui_dc(jobs: int = 2) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    todo = [(lg, st) for lg in LEAGUES for st in DC_SEASONS
            if not (SCRATCH / f"dc_{lg}_{st}.csv").exists()]
    if not todo:
        print("  [dc] tutti i file gia' presenti")
        return
    with Pool(jobs) as pool:
        for msg in pool.imap_unordered(_dc_worker, todo):
            print("  [dc]", msg, flush=True)


def carica_dc() -> pd.DataFrame:
    fr = []
    for lg in LEAGUES:
        for st in DC_SEASONS:
            fp = SCRATCH / f"dc_{lg}_{st}.csv"
            if fp.exists():
                d = pd.read_csv(fp, dtype={"season": str}, parse_dates=["date"])
                d["date"] = d["date"].dt.normalize()
                d["lega"] = lg
                d["season"] = st
                d["home_team"] = d["home_team"].map(canon)
                d["away_team"] = d["away_team"].map(canon)
                fr.append(d[["lega", "season", "date", "home_team", "away_team",
                             "exp_home_goals", "exp_away_goals"]])
    return pd.concat(fr, ignore_index=True) if fr else pd.DataFrame()


# --------------------------------------------------------------------------- #
# PASSO 3 — inversioni (lambda, mu) e pricing
# --------------------------------------------------------------------------- #
def _invert_rows(pH, pD, pA, pO) -> tuple[np.ndarray, np.ndarray]:
    lam = np.full(len(pH), np.nan)
    mu = np.full(len(pH), np.nan)
    for i in range(len(pH)):
        if not np.isfinite([pH[i], pD[i], pA[i]]).all():
            continue
        po = pO[i] if (pO is not None and np.isfinite(pO[i])) else None
        lam[i], mu[i] = mi.implied_lambda_mu(float(pH[i]), float(pD[i]),
                                             float(pA[i]), po, RHO)
    return lam, mu


def inverti_cached(tag: str, pH, pD, pA, pO) -> tuple[np.ndarray, np.ndarray]:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fp = SCRATCH / f"rates_{tag}.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(pH):
            return c["lam"].to_numpy(), c["mu"].to_numpy()
    lam, mu = _invert_rows(pH, pD, pA, pO)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


def _fit_ladder(pH, pD, pA, p_over: dict[str, float]) -> tuple[float, float]:
    """(lambda, mu) che riproduce al meglio 1X2 + TUTTE le linee O/U del book.
    Stessa struttura di `mi.implied_lambda_mu`, con piu' bersagli."""
    K = np.arange(mi.MAX_GOALS + 1)
    tot = K.reshape(-1, 1) + K.reshape(1, -1)

    def loss(x):
        M = mi.score_matrix(x[0], x[1], RHO)
        qH = float(np.tril(M, -1).sum())
        qD = float(np.trace(M))
        qA = float(np.triu(M, 1).sum())
        e = (qH - pH) ** 2 + (qD - pD) ** 2 + (qA - pA) ** 2
        for k, thr in OU_THR.items():
            if k in p_over:
                e += (float(M[tot >= thr + 0.5].sum()) - p_over[k]) ** 2
        return e

    tot0 = 2.5 + (p_over.get("25", 0.5) - 0.5) * 2.0
    tilt = float(np.clip(0.5 + (pH - pA) * 0.6, 0.15, 0.85))
    r = minimize(loss, [max(0.2, tot0 * tilt), max(0.2, tot0 * (1 - tilt))],
                 method="L-BFGS-B", bounds=[(0.1, 4.5), (0.1, 4.5)])
    return float(r.x[0]), float(r.x[1])


def inverti_ladder_cached(A: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fp = SCRATCH / "rates_ladder.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(A):
            return c["lam"].to_numpy(), c["mu"].to_numpy()
    lam = np.full(len(A), np.nan)
    mu = np.full(len(A), np.nan)
    for i, r in enumerate(A.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.xbetClose1FT, r.xbetCloseXFT, r.xbetClose2FT)
        po = {}
        for k in OU_LINES:
            o = getattr(r, f"xbetCloseOver{k}")
            u = getattr(r, f"xbetCloseUnder{k}")
            if np.isfinite(o) and np.isfinite(u) and o > 1 and u > 1:
                po[k] = metrics.devig_binary(o, u)[0]
        lam[i], mu[i] = _fit_ladder(pH, pD, pA, po)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


def prezza_btts(lam, mu, phi0: float = 0.0, kappa: float = 0.0) -> np.ndarray:
    """P(GG) dal router di produzione `mi.price_markets` (rho = -0.06)."""
    out = np.full(len(lam), np.nan)
    for i in range(len(lam)):
        if not np.isfinite(lam[i]) or not np.isfinite(mu[i]):
            continue
        out[i] = mi.price_markets(float(lam[i]), float(mu[i]), RHO,
                                  phi0, kappa)["btts"]
    return out


def prezza_over25(lam, mu) -> np.ndarray:
    out = np.full(len(lam), np.nan)
    for i in range(len(lam)):
        if not np.isfinite(lam[i]) or not np.isfinite(mu[i]):
            continue
        out[i] = mi.price_markets(float(lam[i]), float(mu[i]), RHO)["over_2.5"]
    return out


def fit_phi_kappa0(lams, mus, is_draw) -> float:
    """phi0 con kappa FISSO a 0 (inflazione-pareggio COSTANTE): stessa
    verosimiglianza di `mi.fit_balance_phi`, un solo parametro."""
    lams = np.asarray(lams, float)
    mus = np.asarray(mus, float)
    is_draw = np.asarray(is_draw, float)
    d_match = np.array([float(np.trace(mi.score_matrix(l, m, RHO)))
                        for l, m in zip(lams, mus)])
    d_match = np.clip(d_match, 1e-12, 1 - 1e-12)

    def neg_ll(p):
        phi = p[0]
        return -np.sum(np.log1p(phi * is_draw) - np.log1p(phi * d_match))

    r = minimize(neg_ll, np.array([0.1]), method="L-BFGS-B", bounds=[(0.0, 2.0)])
    return float(r.x[0])


# --------------------------------------------------------------------------- #
# PASSO 4 — analisi
# --------------------------------------------------------------------------- #
def analisi(A: pd.DataFrame, lock: dict) -> dict:
    rng = np.random.default_rng(SEED)
    res: dict = {
        "titolo": "GG/NG contro quote reali (1xBet chiusura, 2017-20, 5 leghe)",
        "aspettativa_dichiarata_prima": {
            "D1": "mercato GG/NG informativo ma MENO lavorato dell'1X2",
            "D2a": "il market-implied dalle quote dello STESSO book sara' molto "
                   "vicino al prezzo GG/NG del book",
            "D2c": "il DC standalone perdera'",
            "cautela": "un edge, se appare, e' quasi certamente il margine del "
                       "book letto male: cercarlo prima di crederci",
        },
        "lucchetti": lock,
    }

    # ------------------------------------------------------------------ prezzi
    n = len(A)
    lega = A["lega"].to_numpy()
    stag = A["season"].to_numpy()
    y = A["y_btts"].to_numpy()
    y_ou = A["y_over25"].to_numpy()

    # book: GG/NG e O/U 2.5 devigati
    p_book = np.array([metrics.devig_binary(o, u)[0]
                       for o, u in zip(A["xbetCloseBTTSY"], A["xbetCloseBTTSN"])])
    p_book_ou = np.array([metrics.devig_binary(o, u)[0]
                          for o, u in zip(A["xbetCloseOver25"], A["xbetCloseUnder25"])])
    orr_btts = (1 / A["xbetCloseBTTSY"] + 1 / A["xbetCloseBTTSN"]).to_numpy()
    orr_ou = (1 / A["xbetCloseOver25"] + 1 / A["xbetCloseUnder25"]).to_numpy()
    orr_1x2 = (1 / A["xbetClose1FT"] + 1 / A["xbetCloseXFT"]
               + 1 / A["xbetClose2FT"]).to_numpy()

    # ---------------------------------------------------------------- D1
    ll_book = ll_bin(p_book, y)
    ll_book_ou = ll_bin(p_book_ou, y_ou)

    def base_insample(vals, key_l, key_s):
        """Frequenza costante di lega-stagione (in-sample: FAVOREVOLE alla
        baseline, convenzione di `_run_market_implied.baseline_ll`)."""
        out = np.zeros(len(vals))
        df = pd.DataFrame({"v": vals, "l": key_l, "s": key_s})
        for (_, _), g in df.groupby(["l", "s"]):
            out[g.index] = g["v"].mean()
        return out

    def base_loso(vals, key_l, key_s):
        """Frequenza di lega calcolata sulle ALTRE stagioni (fuori campione)."""
        out = np.zeros(len(vals))
        df = pd.DataFrame({"v": vals, "l": key_l, "s": key_s})
        for l_, gl in df.groupby("l"):
            for s_, g in gl.groupby("s"):
                altre = gl[gl["s"] != s_]["v"]
                out[g.index] = altre.mean() if len(altre) else gl["v"].mean()
        return out

    d1 = {}
    for nome, pv, yv, llv in (("GG/NG", p_book, y, ll_book),
                              ("O/U 2.5", p_book_ou, y_ou, ll_book_ou)):
        b_in = base_insample(yv, lega, stag)
        b_lo = base_loso(yv, lega, stag)
        ll_in = ll_bin(b_in, yv)
        ll_lo = ll_bin(b_lo, yv)
        d1[nome] = {
            "n": int(n),
            "log_loss_mercato": float(metrics.log_loss_binary(pv, yv)),
            "brier_mercato": float(metrics.brier_binary(pv, yv)),
            "log_loss_baseline_insample": float(ll_in.mean()),
            "log_loss_baseline_LOSO": float(ll_lo.mean()),
            "brier_baseline_insample": float(metrics.brier_binary(b_in, yv)),
            "guadagno_vs_baseline_insample": confronto(llv, ll_in, rng,
                                                       f"{nome}: book vs baseline in-sample"),
            "guadagno_vs_baseline_LOSO": confronto(llv, ll_lo, rng,
                                                   f"{nome}: book vs baseline LOSO"),
            "skill_%_vs_baseline_insample":
                float(100 * (1 - llv.mean() / ll_in.mean())),
            "calibrazione": calibrazione(pv, yv),
        }
    d1["overround_del_book"] = {
        "GG/NG": float(np.nanmean(orr_btts)),
        "O/U 2.5": float(np.nanmean(orr_ou)),
        "1X2": float(np.nanmean(orr_1x2)),
    }
    d1["lettura"] = (
        "confronto fra due letture della STESSA distribuzione di gol: lo scarto "
        "di skill fra GG/NG e O/U 2.5 dice quanto il book lavora il GG/NG")
    # --- efficienza in senso SCOMMESSA: strategie cieche sulle quote del book -
    oy_ = A["xbetCloseBTTSY"].to_numpy(); on_ = A["xbetCloseBTTSN"].to_numpy()
    cieche = {
        "sempre_GG": np.where(y == 1, oy_ - 1, -1.0),
        "sempre_NG": np.where(y == 0, on_ - 1, -1.0),
        "sempre_il_favorito": np.where(
            p_book >= 0.5, np.where(y == 1, oy_ - 1, -1.0),
            np.where(y == 0, on_ - 1, -1.0)),
    }
    d1["ROI_strategie_cieche"] = {}
    for k, v in cieche.items():
        m_, lo_, hi_, _ = boot(v, rng, B)
        d1["ROI_strategie_cieche"][k] = {
            "ROI_%": round(100 * m_, 3), "ci95_%": [round(100 * lo_, 3),
                                                    round(100 * hi_, 3)]}
    d1["ROI_strategie_cieche"]["atteso_se_efficiente"] = (
        f"circa -{100*(np.nanmean(orr_btts)-1)/np.nanmean(orr_btts):.2f}% "
        "(= il margine del book)")
    # --- calibrazione per decile di prezzo ---------------------------------
    q = pd.qcut(p_book, 10, labels=False, duplicates="drop")
    d1["calibrazione_per_decile"] = [
        {"decile": int(k), "n": int((q == k).sum()),
         "p_medio": float(p_book[q == k].mean()),
         "freq_reale": float(y[q == k].mean())}
        for k in sorted(pd.unique(q))]
    res["D1_efficienza_mercato_GGNG"] = d1

    # per lega
    res["D1_per_lega"] = {}
    for lg in LEAGUES:
        m = lega == lg
        if m.sum() == 0:
            continue
        b_in = base_insample(y[m], lega[m], stag[m])
        res["D1_per_lega"][lg] = {
            "n": int(m.sum()),
            "ll_book": float(ll_book[m].mean()),
            "ll_baseline_insample": float(ll_bin(b_in, y[m]).mean()),
            "freq_GG": float(y[m].mean()),
            "p_medio_book": float(p_book[m].mean()),
        }

    # --------------------------------------------------- controllo di sanita'
    m1719 = np.isin(stag, BLOCCO_PRINC)
    res["controllo_di_sanita"] = {
        "riferimento": "docs/audit_5_leghe/09_chiusura_buchi.md §2.4 (primo sguardo, "
                       "finestra 2017-19, 5 leghe)",
        "atteso": {"p_medio_GG": 0.526, "freq_GG": 0.516,
                   "ll_mercato": 0.687, "ll_baseline": 0.693,
                   "overround": 1.043, "n": 3652},
        "ottenuto": {
            "p_medio_GG": float(p_book[m1719].mean()),
            "freq_GG": float(y[m1719].mean()),
            "ll_mercato": float(ll_book[m1719].mean()),
            "ll_baseline_costante_globale": float(
                ll_bin(np.full(int(m1719.sum()), y[m1719].mean()), y[m1719]).mean()),
            "overround": float(np.nanmean(orr_btts[m1719])),
            "n": int(m1719.sum()),
        },
    }

    # ---------------------------------------------------------------- D2
    # (a) market-implied dalle quote 1X2 + O/U 2.5 DELLO STESSO BOOK
    pH_b = np.zeros(n); pD_b = np.zeros(n); pA_b = np.zeros(n)
    for i, r in enumerate(A.itertuples()):
        pH_b[i], pD_b[i], pA_b[i] = metrics.devig_1x2(
            r.xbetClose1FT, r.xbetCloseXFT, r.xbetClose2FT)
    lam_a, mu_a = inverti_cached("book_1x2_ou25", pH_b, pD_b, pA_b, p_book_ou)
    p_a = prezza_btts(lam_a, mu_a)

    # (a2) dalla scaletta completa del book
    lam_a2, mu_a2 = inverti_ladder_cached(A)
    p_a2 = prezza_btts(lam_a2, mu_a2)

    # (b) dallo snapshot: 1X2 di chiusura multi-book + varie sorgenti di O/U
    pH_s = np.zeros(n); pD_s = np.zeros(n); pA_s = np.zeros(n)
    for i, r in enumerate(A.itertuples()):
        pH_s[i], pD_s[i], pA_s[i] = metrics.devig_1x2(
            r.odds_home, r.odds_draw, r.odds_away)
    po_open = np.full(n, np.nan)
    ok = A["odds_over25_open"].notna().to_numpy() & A["odds_under25_open"].notna().to_numpy()
    po_open[ok] = [metrics.devig_binary(o, u)[0] for o, u in
                   zip(A["odds_over25_open"][ok], A["odds_under25_open"][ok])]
    lam_b1, mu_b1 = inverti_cached("snap_1x2close_ouopen", pH_s, pD_s, pA_s, po_open)
    p_b1 = prezza_btts(lam_b1, mu_b1)
    p_b1[~ok] = np.nan          # senza l'input O/U il path non esiste: si scarta

    po_est = A["p_over25_close_est"].to_numpy(float)
    oke = np.isfinite(po_est)
    lam_b2, mu_b2 = inverti_cached("snap_1x2close_ouest", pH_s, pD_s, pA_s, po_est)
    p_b2 = prezza_btts(lam_b2, mu_b2)
    p_b2[~oke] = np.nan

    po_close = np.full(n, np.nan)
    okc = A["odds_over25"].notna().to_numpy() & A["odds_under25"].notna().to_numpy()
    po_close[okc] = [metrics.devig_binary(o, u)[0] for o, u in
                     zip(A["odds_over25"][okc], A["odds_under25"][okc])]
    lam_b0, mu_b0 = inverti_cached("snap_1x2close_ouclose", pH_s, pD_s, pA_s, po_close)
    p_b0 = prezza_btts(lam_b0, mu_b0)
    p_b0[~okc] = np.nan

    # (c) Dixon-Coles walk-forward
    dc = carica_dc()
    p_c = np.full(n, np.nan)
    lam_c = np.full(n, np.nan); mu_c = np.full(n, np.nan)
    if len(dc):
        key = A[["lega", "season", "date", "home_team", "away_team"]].copy()
        key["_i"] = np.arange(n)
        j = key.merge(dc, on=["lega", "season", "date", "home_team", "away_team"],
                      how="left")
        lam_c[j["_i"].to_numpy()] = j["exp_home_goals"].to_numpy()
        mu_c[j["_i"].to_numpy()] = j["exp_away_goals"].to_numpy()
        p_c = prezza_btts(lam_c, mu_c)

    predittori = {
        "a_MI_book_1X2+OU2.5": p_a,
        "a2_MI_book_scaletta_completa": p_a2,
        "b1_MI_snap_1X2close+OUopen": p_b1,
        "b2_MI_snap_1X2close+OUstima": p_b2,
        "b0_MI_snap_1X2close+OUclose": p_b0,
        "c_DC_gol+xG_walkforward": p_c,
    }
    res["D2_nostro_prezzo_vs_book"] = {"note": {
        "b1": "PRIMARIA per il 2017-19: O/U di APERTURA REALE (nessuna stima)",
        "b2": "SECONDARIA: stima di chiusura O/U del progetto, coefficienti "
              "fittati su stagioni SUCCESSIVE (anti-causale) -> benchmark "
              "storico, non predizione",
        "b0": "solo 2019-20: O/U di CHIUSURA reale (dal 2019-20 esiste)",
        "c": "solo 2018-19 e 2019-20: per il 2017-18 non c'e' storico -> "
             "run_backtest fallisce (verificato)",
    }}
    for blocco, stagioni in (("2017-19 (principale)", BLOCCO_PRINC),
                             ("2019-20 (controllo)", BLOCCO_CTRL),
                             ("tutte e 3 le stagioni", BLOCCO_PRINC + BLOCCO_CTRL)):
        mb = np.isin(stag, stagioni)
        blk = {"n_blocco": int(mb.sum()),
               "ll_book": float(ll_book[mb].mean())}
        for nome, pv in predittori.items():
            m = mb & np.isfinite(pv)
            if m.sum() < 50:
                blk[nome] = {"n": int(m.sum()), "verdetto": "non applicabile"}
                continue
            c = confronto(ll_bin(pv[m], y[m]), ll_book[m], rng,
                          f"{nome} vs book [{blocco}]")
            c["brier_nostro"] = float(metrics.brier_binary(pv[m], y[m]))
            c["brier_book"] = float(metrics.brier_binary(p_book[m], y[m]))
            c["calibrazione_nostra"] = calibrazione(pv[m], y[m])
            c["corr_col_book"] = float(np.corrcoef(pv[m], p_book[m])[0, 1])
            c["MAE_dal_book"] = float(np.mean(np.abs(pv[m] - p_book[m])))
            blk[nome] = c
        res["D2_nostro_prezzo_vs_book"][blocco] = blk

    # ------------------------------------------------- D2-bis: test di ENCOMPASSING
    # La domanda della Fase 16 applicata al GG/NG: il prezzo del book INGLOBA
    # il nostro? z = (1-alpha)*logit(p_book) + alpha*logit(p_nostro), alpha
    # scelto su griglia FUORI CAMPIONE (LOSO per-lega). alpha*=0 => il book
    # ingloba tutto e non c'e' niente da aggiungere.
    def logit(p):
        p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
        return np.log(p / (1 - p))

    GRID_A = np.round(np.arange(0.0, 1.001, 0.05), 3)

    def encompassing(pv: np.ndarray, nome: str) -> dict:
        ok_ = np.isfinite(pv)
        zb, zo = logit(p_book), logit(np.where(ok_, pv, 0.5))
        p_mix = np.full(n, np.nan)
        alphas = {}
        for lg in LEAGUES:
            ml = (lega == lg) & ok_
            for s in np.unique(stag[ml]):
                cur = ml & (stag == s)
                tr = ml & (stag != s)
                if tr.sum() < 100 or cur.sum() == 0:
                    continue
                best, bll = 0.0, np.inf
                for a in GRID_A:
                    z = (1 - a) * zb[tr] + a * zo[tr]
                    v = ll_bin(1 / (1 + np.exp(-z)), y[tr]).mean()
                    if v < bll:
                        bll, best = v, float(a)
                alphas[f"{lg}_{s}"] = best
                z = (1 - best) * zb[cur] + best * zo[cur]
                p_mix[cur] = 1 / (1 + np.exp(-z))
        m_ = np.isfinite(p_mix)
        return {"alpha_per_lega_stagione": alphas,
                "alpha_medio": float(np.mean(list(alphas.values()))) if alphas else None,
                "quota_alpha_zero": float(np.mean([a == 0 for a in alphas.values()]))
                if alphas else None,
                "blend_vs_book": confronto(ll_bin(p_mix[m_], y[m_]), ll_book[m_],
                                           rng, f"blend(book,{nome}) vs book")}

    res["D2bis_encompassing"] = {
        "domanda": "il prezzo GG/NG del book INGLOBA il nostro? (Fase 16 sul GG/NG)",
        "forma": "logit(p) = (1-alpha)*logit(p_book) + alpha*logit(p_nostro), "
                 "alpha su griglia 0..1 passo 0.05, scelto LOSO per-lega",
        "con_a_MI_book": encompassing(p_a, "a"),
        "con_c_DC": encompassing(p_c, "DC"),
        "con_b1_MI_snap": encompassing(p_b1, "b1"),
    }

    # ------------------------------------- D2-ter: da cosa e' fatto lo scarto
    # book - nostro (path a): e' un OFFSET costante (gusto/margine) o e'
    # informazione partita per partita?
    dz = logit(p_book) - logit(p_a)
    res["D2ter_scarto_book_meno_nostro"] = {
        "in_logit": {"media": float(dz.mean()), "sd": float(dz.std()),
                     "quota_varianza_spiegata_dalla_media":
                         float(dz.mean() ** 2 / (dz.mean() ** 2 + dz.var()))},
        "in_probabilita": {"MAE": float(np.mean(np.abs(p_book - p_a))),
                           "bias_medio": float(np.mean(p_book - p_a))},
        "per_lega": {lg: {"bias_logit": float(dz[lega == lg].mean()),
                          "sd_logit": float(dz[lega == lg].std())}
                     for lg in LEAGUES},
        "lettura": ("se quasi tutta la varianza dello scarto e' nella MEDIA, il "
                    "prezzo GG/NG del book e' la nostra stessa matrice piu' un "
                    "offset (gusto/margine); se e' nella dispersione, il book "
                    "prezza partita per partita qualcosa che noi non abbiamo"),
    }

    # ------------------------------- D2-quater: CHI HA RAGIONE SUL LIVELLO?
    # Il book prezza il GG sopra la proiezione dei suoi stessi marginali. Ma la
    # realta' da' ragione a chi? Si misura il bias di livello di ciascuno con
    # bootstrap, e il bias APPAIATO fra i due (che ha varianza molto minore).
    def bias_boot(pv):
        m_ = np.isfinite(pv)
        d = pv[m_] - y[m_]
        mm, lo, hi, _ = boot(d, rng, B)
        return {"bias": mm, "ci95": [lo, hi],
                "conclusivo": bool(lo * hi > 0), "n": int(m_.sum())}

    res["D2quater_livello"] = {
        "domanda": "il book sovra-prezza il GG, o e' la nostra proiezione a "
                   "sotto-prezzarlo? con 5.337 partite si puo' dire?",
        "frequenza_reale_GG": float(y.mean()),
        "bias_del_book": bias_boot(p_book),
        "bias_del_nostro_a": bias_boot(p_a),
        "bias_del_nostro_a2": bias_boot(p_a2),
        "differenza_appaiata_book_meno_a": {
            **dict(zip(["bias", "ci95_lo", "ci95_hi", "P(<0)"],
                       boot(p_book - p_a, rng, B)))},
        "lettura": ("la differenza APPAIATA fra i due prezzi ha varianza ~10x "
                    "minore del bias di ciascuno contro l'esito: si dimostra "
                    "CHE differiscono, non CHI dei due ha ragione"),
    }
    # offset puro (Platt con pendenza FISSA a 1), fittato LOLO: la versione
    # minima della domanda 'il livello del book va corretto?'
    zb0 = logit(p_book)
    p_off = np.full(n, np.nan)
    off = {}
    for lg in LEAGUES:
        cur = lega == lg
        tr = ~cur

        def nll_a(par, tr=tr):
            q = np.clip(1 / (1 + np.exp(-(par[0] + zb0[tr]))), 1e-12, 1 - 1e-12)
            return -np.mean(y[tr] * np.log(q) + (1 - y[tr]) * np.log(1 - q))
        r = minimize(nll_a, [0.0], method="L-BFGS-B")
        off[lg] = round(float(r.x[0]), 4)
        p_off[cur] = 1 / (1 + np.exp(-(r.x[0] + zb0[cur])))
    res["D2quater_livello"]["offset_puro_LOLO"] = {
        "offset_logit_per_lega": off,
        "vs_book": confronto(ll_bin(p_off, y), ll_book, rng, "offset LOLO vs book"),
    }

    # ---------------------------------------------------------------- D3 leve
    # Si lavora sul path (a) — il migliore lato mercato — sul blocco principale
    # + controllo (3 stagioni), con parametri FUORI CAMPIONE.
    leve: dict = {"path": "a_MI_book_1X2+OU2.5", "rho": RHO,
                  "note": "parametri sempre fuori campione (LOSO per-lega, "
                          "LOLO pooled cross-lega)"}
    hg = A["home_goals"].to_numpy(float)
    ag = A["away_goals"].to_numpy(float)
    is_draw = (A["home_goals"] == A["away_goals"]).to_numpy(float)
    ll_a = ll_bin(p_a, y)

    # --- L1: livelli dei tassi ---------------------------------------------
    def applica_livelli(fronte: str, solo_mu: bool) -> tuple[np.ndarray, dict]:
        lam_t = lam_a.copy(); mu_t = mu_a.copy()
        par = {}
        if fronte == "LOSO":
            for lg in LEAGUES:
                ml = lega == lg
                for s in np.unique(stag[ml]):
                    cur = ml & (stag == s)
                    tr = ml & (stag != s)
                    if tr.sum() < 100:
                        continue
                    cm = fit_level(mu_a[tr], ag[tr])
                    cl = 0.0 if solo_mu else fit_level(lam_a[tr], hg[tr])
                    lam_t[cur] = lam_a[cur] * np.exp(cl)
                    mu_t[cur] = mu_a[cur] * np.exp(cm)
                    par[f"{lg}_{s}"] = [round(cl, 5), round(cm, 5)]
        else:                                       # LOLO pooled
            for lg in LEAGUES:
                cur = lega == lg
                tr = ~cur
                cm = fit_level(mu_a[tr], ag[tr])
                cl = 0.0 if solo_mu else fit_level(lam_a[tr], hg[tr])
                lam_t[cur] = lam_a[cur] * np.exp(cl)
                mu_t[cur] = mu_a[cur] * np.exp(cm)
                par[lg] = [round(cl, 5), round(cm, 5)]
        return prezza_btts(lam_t, mu_t), par

    prezzi_leve: dict[str, np.ndarray] = {}
    for tag, fronte, solo_mu in (
            ("L1a_livelli_lambda_mu_LOSO_per_lega", "LOSO", False),
            ("L1b_livello_solo_mu_LOSO_per_lega", "LOSO", True),
            ("L1c_livelli_lambda_mu_LOLO_pooled", "LOLO", False),
            ("L1d_livello_solo_mu_LOLO_pooled", "LOLO", True)):
        pv, par = applica_livelli(fronte, solo_mu)
        prezzi_leve[tag] = pv
        m = np.isfinite(pv)
        leve[tag] = {
            "parametri": par,
            "vs_noi_senza_leva": confronto(ll_bin(pv[m], y[m]), ll_a[m], rng,
                                           f"{tag} vs path a"),
            "vs_book": confronto(ll_bin(pv[m], y[m]), ll_book[m], rng,
                                 f"{tag} vs book"),
        }

    # --- L2: phi(|lambda-mu|) e phi costante --------------------------------
    def applica_phi(kappa_zero: bool) -> tuple[np.ndarray, dict]:
        pv = np.full(n, np.nan)
        par = {}
        for lg in LEAGUES:
            ml = lega == lg
            for s in np.unique(stag[ml]):
                cur = ml & (stag == s)
                tr = ml & (stag != s)
                if tr.sum() < 100:
                    continue
                if kappa_zero:
                    phi0 = fit_phi_kappa0(lam_a[tr], mu_a[tr], is_draw[tr])
                    kap = 0.0
                else:
                    phi0, kap = mi.fit_balance_phi(lam_a[tr], mu_a[tr],
                                                   is_draw[tr], RHO)
                par[f"{lg}_{s}"] = [round(float(phi0), 4), round(float(kap), 4)]
                idx = np.where(cur)[0]
                pv[idx] = prezza_btts(lam_a[idx], mu_a[idx], phi0, kap)
        return pv, par

    for tag, kz in (("L2a_phi35_|lambda-mu|_LOSO", False),
                    ("L2b_phi_COSTANTE_kappa0_LOSO", True)):
        pv, par = applica_phi(kz)
        prezzi_leve[tag] = pv
        m = np.isfinite(pv)
        leve[tag] = {
            "parametri": par,
            "vs_noi_senza_leva": confronto(ll_bin(pv[m], y[m]), ll_a[m], rng,
                                           f"{tag} vs path a"),
            "vs_book": confronto(ll_bin(pv[m], y[m]), ll_book[m], rng,
                                 f"{tag} vs book"),
        }
    # --- L3: ricalibrazione (Platt) del PREZZO DEL BOOK stesso -------------
    # La calibrazione di D1 mostra un bias: il book sovra-prezza il GG. La
    # domanda: quel bias e' informazione sfruttabile o resta dentro il margine?
    # Platt logit(q) = a + b*logit(p_book), (a,b) fittati FUORI CAMPIONE.
    def platt(zi, yi, zo):
        def nll(par):
            q = np.clip(1 / (1 + np.exp(-(par[0] + par[1] * zi))), 1e-12, 1 - 1e-12)
            return -np.mean(yi * np.log(q) + (1 - yi) * np.log(1 - q))
        r = minimize(nll, [0.0, 1.0], method="L-BFGS-B")
        return 1 / (1 + np.exp(-(r.x[0] + r.x[1] * zo))), r.x

    zb = np.log(np.clip(p_book, 1e-6, 1 - 1e-6) / (1 - np.clip(p_book, 1e-6, 1 - 1e-6)))
    for tag, fronte in (("L3a_ricalibrazione_del_BOOK_LOSO_per_lega", "LOSO"),
                        ("L3b_ricalibrazione_del_BOOK_LOLO_pooled", "LOLO")):
        pv = np.full(n, np.nan)
        par = {}
        if fronte == "LOSO":
            for lg in LEAGUES:
                ml = lega == lg
                for s in np.unique(stag[ml]):
                    cur = ml & (stag == s); tr = ml & (stag != s)
                    if tr.sum() < 100:
                        continue
                    pv[cur], co = platt(zb[tr], y[tr], zb[cur])
                    par[f"{lg}_{s}"] = [round(float(co[0]), 4), round(float(co[1]), 4)]
        else:
            for lg in LEAGUES:
                cur = lega == lg; tr = ~cur
                pv[cur], co = platt(zb[tr], y[tr], zb[cur])
                par[lg] = [round(float(co[0]), 4), round(float(co[1]), 4)]
        prezzi_leve[tag] = pv
        m = np.isfinite(pv)
        leve[tag] = {"parametri_[a,b]": par,
                     "vs_book": confronto(ll_bin(pv[m], y[m]), ll_book[m], rng,
                                          f"{tag} vs book")}
    res["D3_leve_sul_GGNG"] = leve

    # ------------------------------------------------- D3-bis: per-lega L1b
    # (il segnale del blocco precedente era su bundesliga: si riguarda li')
    pv_l1b, _ = applica_livelli("LOSO", True)
    per_lega = {}
    for lg in LEAGUES:
        m = (lega == lg) & np.isfinite(pv_l1b)
        if m.sum() < 100:
            continue
        per_lega[lg] = {
            "vs_noi": confronto(ll_bin(pv_l1b[m], y[m]), ll_a[m], rng, lg),
            "vs_book": confronto(ll_bin(pv_l1b[m], y[m]), ll_book[m], rng, lg),
        }
    res["D3bis_L1b_per_lega"] = per_lega

    # ---------------------------------------------------------------- D4 ROI
    # SOLO se un nostro prezzo batte il book in log-loss con CI conclusivo.
    candidati = []
    for blocco in ("2017-19 (principale)", "tutte e 3 le stagioni"):
        for k, v in res["D2_nostro_prezzo_vs_book"][blocco].items():
            if isinstance(v, dict) and v.get("verdetto", "").startswith("MEGLIO"):
                candidati.append((blocco, k))
    for k, v in res["D3_leve_sul_GGNG"].items():
        if isinstance(v, dict) and isinstance(v.get("vs_book"), dict) \
                and v["vs_book"]["verdetto"].startswith("MEGLIO"):
            candidati.append(("leve", k))
    res["D4_ROI"] = {
        "regola_pre_dichiarata": "il ROI si misura SOLO se un nostro prezzo "
                                 "batte il book in log-loss con CI95 conclusivo",
        "candidati_che_battono_il_book": candidati,
    }
    if not candidati:
        res["D4_ROI"]["esito"] = (
            "NON misurato: nessun nostro prezzo batte il book in log-loss con "
            "CI95 conclusivo. Come da regola del progetto: si dichiara e si "
            "chiude, senza promettere edge.")
    else:
        roi = {}
        for blocco, k in candidati:
            pv = predittori.get(k, prezzi_leve.get(k))
            if pv is None:
                continue
            mb = np.isin(stag, BLOCCO_PRINC if "2017-19" in blocco
                         else BLOCCO_PRINC + BLOCCO_CTRL)
            m = mb & np.isfinite(pv)
            oy = A["xbetCloseBTTSY"].to_numpy()
            on = A["xbetCloseBTTSN"].to_numpy()
            sub = {}
            for soglia in (0.0, 0.02, 0.05):
                bet_y = m & ((pv * oy - 1) > soglia)
                bet_n = m & (((1 - pv) * on - 1) > soglia)
                pnl = np.concatenate([
                    np.where(y[bet_y] == 1, oy[bet_y] - 1, -1.0),
                    np.where(y[bet_n] == 0, on[bet_n] - 1, -1.0)])
                sub[f"soglia_{soglia}"] = {
                    "n_scommesse": int(len(pnl)),
                    "ROI": float(pnl.mean()) if len(pnl) else None,
                    "ROI_ci95": (list(boot(pnl, rng, B)[1:3]) if len(pnl) > 30
                                 else None),
                }
            roi[f"{blocco} | {k}"] = sub
        res["D4_ROI"]["misure"] = roi
        res["D4_ROI"]["avvertenza"] = (
            "UN SOLO BOOK, overround 1.043 sul GG/NG, quote di chiusura non "
            "necessariamente disponibili al momento della scommessa. "
            "NON usare per scommettere soldi veri.")

    # -------------------------------------------------- confutazioni proprie
    res["confutazioni"] = confuta(A, p_book, p_a, p_a2, y, lega, stag,
                                  orr_btts, rng, ll_book, ll_a)

    # C6 — LA confutazione decisiva del risultato D2-ter/quater: lo scarto di
    # 1.6pp e' una proprieta' del BOOK o un ARTEFATTO dell'inversione? Se la
    # matrice DC(rho=-0.06) non riproducesse i bersagli (1X2 + O/U 2.5) del
    # book, il "nostro" prezzo non sarebbe la proiezione dei suoi marginali.
    K_ = np.arange(mi.MAX_GOALS + 1)
    tot_ = K_.reshape(-1, 1) + K_.reshape(1, -1)
    r1x2 = np.zeros((n, 3)); rou = np.zeros(n)
    for i in range(n):
        M = mi.score_matrix(float(lam_a[i]), float(mu_a[i]), RHO)
        r1x2[i] = (float(np.tril(M, -1).sum()) - pH_b[i],
                   float(np.trace(M)) - pD_b[i],
                   float(np.triu(M, 1).sum()) - pA_b[i])
        rou[i] = float(M[tot_ >= 3].sum()) - p_book_ou[i]
    res["confutazioni"]["C6_roundtrip_inversione"] = {
        "domanda": "la matrice DC riproduce i bersagli del book? se no, il "
                   "'nostro' prezzo non e' la proiezione dei suoi marginali e "
                   "lo scarto di 1.6pp sarebbe un artefatto",
        "residuo_medio_assoluto_1X2": [float(np.mean(np.abs(r1x2[:, k])))
                                       for k in range(3)],
        "residuo_p99_assoluto_1X2": [float(np.percentile(np.abs(r1x2[:, k]), 99))
                                     for k in range(3)],
        "residuo_medio_assoluto_over25": float(np.mean(np.abs(rou))),
        "residuo_p99_assoluto_over25": float(np.percentile(np.abs(rou), 99)),
        "scarto_da_spiegare_sul_GGNG": float(np.mean(p_book - p_a)),
        "residuo_MEDIO_CON_SEGNO_1X2": [float(np.mean(r1x2[:, k])) for k in range(3)],
        "residuo_MEDIO_CON_SEGNO_over25": float(np.mean(rou)),
        "corr_residuo_pareggio_vs_scarto_GGNG":
            float(np.corrcoef(r1x2[:, 1], p_book - p_a)[0, 1]),
        "verdetto": ("ARTEFATTO se i residui sono dello stesso ordine dello "
                     "scarto (0.016); PROPRIETA' DEL BOOK se sono un ordine "
                     "di grandezza sotto"),
    }

    # C7 — la prova decisiva: si LIBERA rho (3 parametri, 4 bersagli) cosi'
    # l'inversione riproduce i marginali del book quasi esattamente. Se lo
    # scarto di 1.6pp sul GG/NG sopravvive, e' del BOOK; se collassa, era il
    # vincolo rho = -0.06 (cioe' nostro).
    def _inv_rho_libero(pH, pD, pA, pO):
        def loss(x):
            M = mi.score_matrix(x[0], x[1], x[2])
            e = (float(np.tril(M, -1).sum()) - pH) ** 2
            e += (float(np.trace(M)) - pD) ** 2
            e += (float(np.triu(M, 1).sum()) - pA) ** 2
            e += (float(M[tot_ >= 3].sum()) - pO) ** 2
            return e
        r = minimize(loss, [1.4, 1.2, RHO], method="L-BFGS-B",
                     bounds=[(0.1, 4.5), (0.1, 4.5), (-0.35, 0.35)])
        return float(r.x[0]), float(r.x[1]), float(r.x[2])

    fp7 = SCRATCH / "rates_rho_libero.csv"
    if fp7.exists() and len(pd.read_csv(fp7)) == n:
        c7 = pd.read_csv(fp7)
        lam7, mu7, rho7 = (c7["lam"].to_numpy(), c7["mu"].to_numpy(),
                           c7["rho"].to_numpy())
    else:
        lam7 = np.zeros(n); mu7 = np.zeros(n); rho7 = np.zeros(n)
        for i in range(n):
            lam7[i], mu7[i], rho7[i] = _inv_rho_libero(
                pH_b[i], pD_b[i], pA_b[i], p_book_ou[i])
        pd.DataFrame({"lam": lam7, "mu": mu7, "rho": rho7}).to_csv(fp7, index=False)
    p7 = np.zeros(n); res7 = np.zeros((n, 4))
    for i in range(n):
        M = mi.score_matrix(float(lam7[i]), float(mu7[i]), float(rho7[i]))
        p7[i] = float(M[1:, 1:].sum())
        res7[i] = (float(np.tril(M, -1).sum()) - pH_b[i],
                   float(np.trace(M)) - pD_b[i],
                   float(np.triu(M, 1).sum()) - pA_b[i],
                   float(M[tot_ >= 3].sum()) - p_book_ou[i])
    res["confutazioni"]["C7_inversione_a_rho_libero"] = {
        "domanda": "liberando rho l'inversione centra i marginali del book: lo "
                   "scarto di 1.6pp sul GG/NG sopravvive?",
        "residuo_medio_assoluto_[H,D,A,O2.5]":
            [float(np.mean(np.abs(res7[:, k]))) for k in range(4)],
        "rho_fittato": {"media": float(rho7.mean()), "sd": float(rho7.std()),
                        "p05": float(np.percentile(rho7, 5)),
                        "p95": float(np.percentile(rho7, 95))},
        "scarto_book_meno_nostro_con_rho_libero": float(np.mean(p_book - p7)),
        "scarto_book_meno_nostro_con_rho_fisso": float(np.mean(p_book - p_a)),
        "bias_del_nostro_rho_libero": bias_boot(p7),
        "vs_book_logloss": confronto(ll_bin(p7, y), ll_book, rng,
                                     "rho libero vs book"),
        "vs_a_logloss": confronto(ll_bin(p7, y), ll_a, rng, "rho libero vs a"),
    }

    # C8 — se la matrice a rho libero (che centra 1X2+O2.5) riproduce anche le
    # ALTRE linee O/U del book, allora i MARGINALI sono giusti e il residuo
    # sul GG/NG e' una faccenda di CORRELAZIONE (cioe' una vera differenza col
    # book). Se invece sbaglia le altre linee, la famiglia Poisson e' la
    # colpevole e il residuo non e' attribuibile.
    altre = {}
    Mset = [mi.score_matrix(float(lam7[i]), float(mu7[i]), float(rho7[i]))
            for i in range(n)]
    for k in ("05", "15", "35", "45"):
        o = A[f"xbetCloseOver{k}"].to_numpy()
        u = A[f"xbetCloseUnder{k}"].to_numpy()
        okk = np.isfinite(o) & np.isfinite(u) & (o > 1) & (u > 1)
        if okk.sum() < 100:
            continue
        pbk = np.array([metrics.devig_binary(a_, b_)[0]
                        for a_, b_ in zip(o[okk], u[okk])])
        thr = OU_THR[k]
        pmod = np.array([float(Mset[i][tot_ >= thr + 0.5].sum())
                         for i in np.where(okk)[0]])
        altre[f"over_{thr}"] = {
            "n": int(okk.sum()),
            "residuo_medio_con_segno": float(np.mean(pmod - pbk)),
            "residuo_medio_assoluto": float(np.mean(np.abs(pmod - pbk))),
        }
    res["confutazioni"]["C8_le_altre_linee_OU_del_book"] = {
        "domanda": "la matrice a rho libero riproduce le linee O/U che NON ha "
                   "usato come bersaglio (0.5, 1.5, 3.5, 4.5)?",
        "linee": altre,
        "residuo_GGNG_da_attribuire": float(np.mean(p_book - p7)),
        "lettura": ("residui sulle altre linee << 0.011 => i marginali del "
                    "book sono ben riprodotti e il residuo GG/NG e' una "
                    "differenza di CORRELAZIONE fra noi e il book; residui "
                    "dello stesso ordine => la famiglia Poisson e' la "
                    "colpevole e il residuo non e' attribuibile al book"),
    }
    # --------------------------------------------- soglia di risoluzione vera
    sd_a = float(np.std(ll_a - ll_book))
    res["soglia_di_risoluzione"] = {
        "n": int(n),
        "sd_differenza_per_riga_(a - book)": sd_a,
        "semi_ampiezza_CI95_attesa": float(1.96 * sd_a / np.sqrt(n)),
        "lettura": ("con questo n il bootstrap risolve differenze di log-loss "
                    "dell'ordine del millesimo: sotto quella soglia «non "
                    "dimostrato» NON e' «dimostrato nullo»"),
    }
    res["multiple_testing"] = {
        "predittori_confrontati_col_book": 6,
        "blocchi_temporali": 3,
        "leve_provate": 6,
        "confronti_totali_vs_book": 6 * 3 + 6,
        "famiglia_pre_registrata_headline": [
            "a_MI_book_1X2+OU2.5 sul blocco 2017-19",
            "b1_MI_snap_1X2close+OUopen sul blocco 2017-19",
            "c_DC_gol+xG_walkforward sul blocco 2017-19",
            "L1b (livello mu, la leva che il blocco precedente indicava)",
        ],
        "bonferroni_alpha_famiglia_headline": round(0.05 / 4, 4),
        "bonferroni_alpha_tutti_i_confronti": round(0.05 / (6 * 3 + 6), 5),
        "regola": "un confronto conclusivo al 95% dentro una famiglia di 24 "
                  "test non basta: serve Bonferroni o la replica su un blocco "
                  "indipendente (2019-20) o su un'altra lega",
    }
    return res


def confuta(A, p_book, p_a, p_a2, y, lega, stag, orr_btts, rng, ll_book, ll_a) -> dict:
    """Prove per DIMOSTRARE CHE IL RISULTATO E' SBAGLIATO (richiesta esplicita)."""
    c = {}

    # C1 — il margine e' letto male? Il devig moltiplicativo assume margine
    # proporzionale. Se il book carica il margine in modo asimmetrico, la
    # "nostra" probabilita' migliore potrebbe essere solo un devig diverso.
    oy = A["xbetCloseBTTSY"].to_numpy(); on = A["xbetCloseBTTSN"].to_numpy()
    varianti = {}
    # additivo: p = 1/o - (overround-1)/2
    inv_y, inv_n = 1 / oy, 1 / on
    exc = inv_y + inv_n - 1
    p_add = np.clip(inv_y - exc / 2, 1e-6, 1 - 1e-6)
    varianti["devig_additivo"] = p_add
    # power: p ∝ (1/o)^(1/eta), eta risolto riga per riga
    p_pow = np.zeros(len(oy))
    for i in range(len(oy)):
        lo_, hi_ = 0.5, 3.0
        for _ in range(40):
            e = 0.5 * (lo_ + hi_)
            s = inv_y[i] ** (1 / e) + inv_n[i] ** (1 / e)
            if s > 1:
                lo_ = e
            else:
                hi_ = e
        e = 0.5 * (lo_ + hi_)
        p_pow[i] = inv_y[i] ** (1 / e) / (inv_y[i] ** (1 / e) + inv_n[i] ** (1 / e))
    varianti["devig_power"] = p_pow
    for nome, pv in varianti.items():
        c[f"C1_{nome}"] = confronto(ll_bin(pv, y), ll_book, rng,
                                    f"{nome} vs devig moltiplicativo")
    c["C1_lettura"] = ("se il vantaggio di un nostro prezzo sparisse cambiando "
                       "solo il metodo di devig, non sarebbe informazione ma "
                       "margine letto male")

    # C2 — il prezzo GG/NG del book e' ridondante rispetto ai suoi stessi
    # marginali? Regressione: y ~ logit(p_a) + [logit(p_book) - logit(p_a)]
    def lg_(p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return np.log(p / (1 - p))

    X = np.column_stack([np.ones(len(y)), lg_(p_a), lg_(p_book) - lg_(p_a)])

    def nll(b):
        z = X @ b
        q = 1 / (1 + np.exp(-z))
        q = np.clip(q, 1e-12, 1 - 1e-12)
        return -np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))

    r = minimize(nll, [0.0, 1.0, 1.0], method="L-BFGS-B")
    # bootstrap sul coefficiente dello "scarto" (informazione EXTRA del book)
    coefs = []
    for _ in range(400):
        idx = rng.integers(0, len(y), len(y))

        def nll_b(b, idx=idx):
            z = X[idx] @ b
            q = np.clip(1 / (1 + np.exp(-z)), 1e-12, 1 - 1e-12)
            return -np.mean(y[idx] * np.log(q) + (1 - y[idx]) * np.log(1 - q))
        coefs.append(minimize(nll_b, r.x, method="L-BFGS-B").x[2])
    coefs = np.array(coefs)
    c["C2_informazione_extra_del_book"] = {
        "modello": "y ~ 1 + logit(p_nostro_a) + [logit(p_book) - logit(p_nostro_a)]",
        "coef_scarto": float(r.x[2]),
        "ci95_bootstrap400": [float(np.percentile(coefs, 2.5)),
                              float(np.percentile(coefs, 97.5))],
        "lettura": ("coef ~ 0 => il prezzo GG/NG del book NON aggiunge nulla ai "
                    "suoi stessi marginali (e' una proiezione meccanica); "
                    "coef > 0 => il book sa qualcosa in piu' sulla CORRELAZIONE"),
    }

    # C3 — la scaletta completa (a2) contro il 1X2+O2.5 (a): l'informazione in
    # piu' del book sta nelle altre linee O/U?
    m = np.isfinite(p_a2)
    c["C3_scaletta_vs_2linee"] = confronto(ll_bin(p_a2[m], y[m]), ll_a[m], rng,
                                           "a2 (scaletta) vs a (1X2+O2.5)")

    # C4 — stabilita' per stagione e per lega del confronto (a) vs book
    per = {}
    for s in np.unique(stag):
        ms = stag == s
        per[f"stagione_{s}"] = confronto(ll_a[ms], ll_book[ms], rng, s)["delta"]
    for lg in np.unique(lega):
        ml = lega == lg
        per[f"lega_{lg}"] = confronto(ll_a[ml], ll_book[ml], rng, lg)["delta"]
    c["C4_stabilita_a_vs_book"] = per

    # C5 — un book con overround 1.043 su un mercato binario: quanto vale il
    # margine in log-loss? (ordine di grandezza dell'"edge" apparente)
    c["C5_ordine_di_grandezza_del_margine"] = {
        "overround_medio_GGNG": float(np.nanmean(orr_btts)),
        "margine_per_lato_%": float(100 * (np.nanmean(orr_btts) - 1) / 2),
        "nota": ("il devig moltiplicativo toglie il margine in proporzione: se "
                 "il book lo carica asimmetricamente, il residuo e' dell'ordine "
                 "di 0.001-0.005 in probabilita', cioe' ~1e-4..1e-3 di log-loss: "
                 "sotto la soglia di risoluzione del bootstrap con questo n"),
    }
    return c


# --------------------------------------------------------------------------- #
def stampa(res: dict) -> None:
    L = res["lucchetti"]
    print("\n" + "=" * 92)
    print("GG/NG CONTRO QUOTE REALI — 1xBet chiusura, 5 leghe, 2017-18/2018-19/2019-20")
    print("=" * 92)
    print(f"\nLUCCHETTI: gol confrontati {L['gol_confrontati']}, identici "
          f"{L['gol_identici']} ({100*L['gol_identici']/max(L['gol_confrontati'],1):.2f}%), "
          f"discordanze {len(L['discordanze_gol'])}")
    print(f"  scartate: {L['scartate']}")
    print(f"  n finale {L['n_finale']} — per stagione {L['n_per_stagione']}")

    s = res["controllo_di_sanita"]
    print("\nCONTROLLO DI SANITA' (report 09 §2.4, finestra 2017-19)")
    for k, v in s["atteso"].items():
        got = s["ottenuto"].get(k if k != "ll_baseline" else
                                "ll_baseline_costante_globale")
        print(f"  {k:12s} atteso {v}  ottenuto {got:.4f}" if isinstance(got, float)
              else f"  {k:12s} atteso {v}  ottenuto {got}")

    d1 = res["D1_efficienza_mercato_GGNG"]
    print("\nD1 — quanto e' informativo il mercato del book (stesse partite)")
    for nome in ("GG/NG", "O/U 2.5"):
        v = d1[nome]
        g = v["guadagno_vs_baseline_insample"]
        print(f"  {nome:8s} LL {v['log_loss_mercato']:.4f} vs baseline "
              f"{v['log_loss_baseline_insample']:.4f}  guadagno {-g['delta']:+.4f} "
              f"CI95 [{-g['ci95'][1]:+.4f},{-g['ci95'][0]:+.4f}] "
              f"skill {v['skill_%_vs_baseline_insample']:.2f}%  "
              f"[calibr. pend. {v['calibrazione']['pendenza']:.3f}, "
              f"bias {v['calibrazione']['bias']:+.4f}]")
    print(f"  overround del book: {d1['overround_del_book']}")

    print("\nD2 — il nostro prezzo GG/NG contro il book (delta<0 = NOI meglio)")
    for blocco, v in res["D2_nostro_prezzo_vs_book"].items():
        if blocco == "note":
            continue
        print(f"  [{blocco}]  n={v['n_blocco']}  LL book {v['ll_book']:.4f}")
        for k, c in v.items():
            if not isinstance(c, dict) or "delta" not in c:
                continue
            print(f"    {k:34s} LL {c['ll_a']:.4f}  delta {c['delta']:+.5f} "
                  f"CI95 [{c['ci95'][0]:+.5f},{c['ci95'][1]:+.5f}]  "
                  f"corr {c['corr_col_book']:.4f} MAE {c['MAE_dal_book']:.4f}  "
                  f"-> {c['verdetto']}")

    print("\nD3 — le leve sul GG/NG (path a), parametri fuori campione")
    for k, v in res["D3_leve_sul_GGNG"].items():
        if not isinstance(v, dict) or "vs_book" not in v:
            continue
        a = v.get("vs_noi_senza_leva"); b = v["vs_book"]
        pa = (f"vs noi {a['delta']:+.5f} [{a['ci95'][0]:+.5f},{a['ci95'][1]:+.5f}] "
              f"{a['verdetto']:24s}" if a else " " * 56)
        print(f"  {k:38s} {pa} | vs book {b['delta']:+.5f} "
              f"[{b['ci95'][0]:+.5f},{b['ci95'][1]:+.5f}] {b['verdetto']}")

    print("\nD2-bis — ENCOMPASSING (alpha* = peso del NOSTRO nel blend col book)")
    for k, v in res["D2bis_encompassing"].items():
        if not isinstance(v, dict) or "blend_vs_book" not in v:
            continue
        b = v["blend_vs_book"]
        print(f"  {k:16s} alpha medio {v['alpha_medio']:.3f}  "
              f"alpha=0 nel {100*v['quota_alpha_zero']:.0f}% dei fit  "
              f"blend vs book {b['delta']:+.5f} "
              f"[{b['ci95'][0]:+.5f},{b['ci95'][1]:+.5f}] -> {b['verdetto']}")

    q = res["D2quater_livello"]
    print(f"\nD2-quater — livello: freq reale GG {q['frequenza_reale_GG']:.4f}")
    for k in ("bias_del_book", "bias_del_nostro_a", "bias_del_nostro_a2"):
        v = q[k]
        print(f"  {k:22s} {v['bias']:+.4f} CI95 "
              f"[{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}] "
              f"{'CONCLUSIVO' if v['conclusivo'] else 'contiene 0'}")
    dd = q["differenza_appaiata_book_meno_a"]
    print(f"  differenza appaiata   {dd['bias']:+.4f} CI95 "
          f"[{dd['ci95_lo']:+.4f},{dd['ci95_hi']:+.4f}]")
    o = q["offset_puro_LOLO"]
    print(f"  offset puro LOLO {o['offset_logit_per_lega']} -> vs book "
          f"{o['vs_book']['delta']:+.5f} "
          f"[{o['vs_book']['ci95'][0]:+.5f},{o['vs_book']['ci95'][1]:+.5f}] "
          f"{o['vs_book']['verdetto']}")

    t = res["D2ter_scarto_book_meno_nostro"]
    print(f"\nD2-ter — scarto book-noi: MAE {t['in_probabilita']['MAE']:.4f}, "
          f"bias {t['in_probabilita']['bias_medio']:+.4f}; in logit media "
          f"{t['in_logit']['media']:+.4f} sd {t['in_logit']['sd']:.4f} -> la media "
          f"spiega il {100*t['in_logit']['quota_varianza_spiegata_dalla_media']:.1f}% "
          f"dello scarto quadratico")

    print("\nD3-bis — L1b (livello mu) per lega")
    for lg, v in res["D3bis_L1b_per_lega"].items():
        a = v["vs_noi"]; b = v["vs_book"]
        print(f"  {lg:16s} vs noi {a['delta']:+.5f} "
              f"[{a['ci95'][0]:+.5f},{a['ci95'][1]:+.5f}] {a['verdetto']:24s} | "
              f"vs book {b['delta']:+.5f} {b['verdetto']}")

    print("\nD4 — ROI")
    print(f"  {res['D4_ROI'].get('esito', res['D4_ROI'].get('misure'))}")

    print("\nCONFUTAZIONI")
    cf = res["confutazioni"]
    for k in ("C1_devig_additivo", "C1_devig_power", "C3_scaletta_vs_2linee"):
        v = cf[k]
        print(f"  {k:28s} delta {v['delta']:+.5f} "
              f"[{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}] -> {v['verdetto']}")
    v = cf["C2_informazione_extra_del_book"]
    print(f"  C2 coef 'scarto' del book {v['coef_scarto']:+.4f} "
          f"CI95 {[round(x,4) for x in v['ci95_bootstrap400']]}")
    stab = {k: round(x, 5) for k, x in cf["C4_stabilita_a_vs_book"].items()}
    print("  C4 stabilita' (a - book, per blocco):", stab)
    v = cf["C6_roundtrip_inversione"]
    print(f"  C6 residui inversione: 1X2 medi "
          f"{[round(x,5) for x in v['residuo_medio_assoluto_1X2']]} "
          f"p99 {[round(x,5) for x in v['residuo_p99_assoluto_1X2']]}; "
          f"O2.5 medio {v['residuo_medio_assoluto_over25']:.5f} "
          f"p99 {v['residuo_p99_assoluto_over25']:.5f} "
          f"— scarto GG/NG da spiegare {v['scarto_da_spiegare_sul_GGNG']:+.4f}")
    v = cf["C7_inversione_a_rho_libero"]
    print(f"  C7 rho LIBERO: residui {[round(x,5) for x in v['residuo_medio_assoluto_[H,D,A,O2.5]']]}, "
          f"rho medio {v['rho_fittato']['media']:+.4f} (sd {v['rho_fittato']['sd']:.4f})")
    print(f"     scarto book-noi: {v['scarto_book_meno_nostro_con_rho_fisso']:+.4f} "
          f"(rho fisso) -> {v['scarto_book_meno_nostro_con_rho_libero']:+.4f} (rho libero); "
          f"bias vs realta' {v['bias_del_nostro_rho_libero']['bias']:+.4f} "
          f"CI95 [{v['bias_del_nostro_rho_libero']['ci95'][0]:+.4f},"
          f"{v['bias_del_nostro_rho_libero']['ci95'][1]:+.4f}]")
    print(f"     log-loss vs book {v['vs_book_logloss']['delta']:+.5f} "
          f"[{v['vs_book_logloss']['ci95'][0]:+.5f},{v['vs_book_logloss']['ci95'][1]:+.5f}] "
          f"-> {v['vs_book_logloss']['verdetto']}")
    v = cf["C8_le_altre_linee_OU_del_book"]
    print("  C8 altre linee O/U (residuo medio con segno / assoluto):")
    for k, x in v["linee"].items():
        print(f"     {k:10s} {x['residuo_medio_con_segno']:+.5f} / "
              f"{x['residuo_medio_assoluto']:.5f}  (n={x['n']})")
    print(f"     residuo GG/NG da attribuire {v['residuo_GGNG_da_attribuire']:+.5f}")
    sr = res["soglia_di_risoluzione"]
    print(f"\nSOGLIA DI RISOLUZIONE: n={sr['n']}, sd per riga "
          f"{sr['sd_differenza_per_riga_(a - book)']:.4f} -> semi-ampiezza CI95 "
          f"attesa {sr['semi_ampiezza_CI95_attesa']:.5f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["dati", "dc", "analisi", "tutto"],
                    default="tutto")
    ap.add_argument("--jobs", type=int, default=2)
    args = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    ds_fp = SCRATCH / "ggng_dataset.csv"
    lock_fp = SCRATCH / "ggng_lucchetti.json"

    if args.step in ("dati", "tutto") or not ds_fp.exists():
        t0 = time.time()
        A, lock = costruisci_dati()
        A.to_csv(ds_fp, index=False)
        lock_fp.write_text(json.dumps(lock, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        print(f"[dati] {len(A)} righe in {time.time()-t0:.0f}s -> {ds_fp}")
        print(f"[dati] gol identici {lock['gol_identici']}/{lock['gol_confrontati']}, "
              f"discordanze {len(lock['discordanze_gol'])}")
    if args.step == "dati":
        return 0

    if args.step in ("dc", "tutto"):
        esegui_dc(args.jobs)
    if args.step == "dc":
        return 0

    A = pd.read_csv(ds_fp, dtype={"season": str}, parse_dates=["date"])
    A["date"] = A["date"].dt.normalize()
    lock = json.loads(lock_fp.read_text(encoding="utf-8"))
    t0 = time.time()
    res = analisi(A, lock)
    res["_meta"] = {"seed": SEED, "B_bootstrap": B, "rho": RHO,
                    "secondi": round(time.time() - t0, 1),
                    "script": "scripts/ggng_contro_quote.py"}
    JSON_OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1,
                                   default=float), encoding="utf-8")
    stampa(res)
    print(f"\n-> {JSON_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
