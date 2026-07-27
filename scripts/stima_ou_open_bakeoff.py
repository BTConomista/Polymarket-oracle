#!/usr/bin/env python3
"""BAKEOFF della stima delle 9 linee O/U di APERTURA mancanti (2017-19).

IL PROBLEMA
-----------
Nove partite del 2017-19 non hanno la linea Over/Under 2.5 di APERTURA:
  - 8 avevano una linea con overround impossibile (1.26-1.34 su una media
    multi-book: registro `data/correzioni_dichiarate.csv`), svuotata;
  - 1 (bundesliga 1819, Bayern Munich-Hoffenheim 2018-08-24) e' vuota alla fonte.
Per tutte e 9 l'1X2 di APERTURA e' integro (colonna diversa, altro provider).

Esiste gia' uno stimatore (`scripts/stima_ou_corrotte.py`, qui = M1):
inverte il solo 1X2 nei tassi (lambda, mu) con `market_implied.implied_lambda_mu`
(rho = -0.06), legge P(Over 2.5) dalla matrice DC e sottrae un bias costante
fittato leave-one-league-out. Errore dichiarato: MAE 0.0267 contro 0.0743 di
baseline, su 3.643 partite (RIPRODOTTO da questo script, vedi §0).

Questo script prova a BATTERLO, o a dimostrare che e' al suo tetto.

ASPETTATIVA DICHIARATA PRIMA DI MISURARE (§ principio "dichiara l'attesa")
--------------------------------------------------------------------------
  M1 (campione in carica)      MAE ~0.0267 (per costruzione)
  M2 (regressione logit su 1X2) 0.025-0.026 -- una mappa APPRESA dovrebbe battere
      di poco una mappa parametrica rigida corretta da un bias costante
  M3 (bias funzione di lambda+mu) ~0.026 -- il bias del DC dipende dal totale
  M4 (superficie di debias in (T, Delta) + varianti flessibili) 0.024-0.025
  M5 (chiusura 1xBet footiqo)  0.015-0.018 -- il report 9 misura MAE 0.0170 fra
      footiqo e l'apertura vera PRIMA di qualunque ricalibrazione; una mappa
      fittata dovrebbe scendere sotto
  effetto di rho: piccolo DOPO il debias (un bias costante ne assorbe gran parte)

METODO (vincolante, regole del progetto)
----------------------------------------
  * verita' = `metrics.devig_binary(odds_over25_open, odds_under25_open)[0]`
    (fonte unica del progetto, devig moltiplicativo);
  * insieme di valutazione: le 3.643 partite 2017-19 delle 5 leghe con linea O/U
    di apertura INTEGRA -- le stesse per TUTTI i metodi;
  * validazione: k-fold k=5, shuffle, seed fisso -> nessun metodo vede mai la
    riga che predice. Gli iperparametri (bias, coefficienti, rho, theta) sono
    fittati SOLO sulle fold di train;
  * ogni metodo esiste in 3 "scope": pooled (train = tutte le leghe),
    per_lega (train = solo quella lega), lolo (train = le altre 4 leghe);
  * bootstrap appaiato B=10.000 sugli |errori| riga per riga, verdetto esplicito
    CONCLUSIVO / nel rumore;
  * MULTIPLE TESTING: il numero di varianti provate e' contato e dichiarato, e
    il confronto vincitore-vs-M1 riporta anche il p di Bonferroni;
  * CONFUTAZIONI (§5): permutazione, leave-one-season-out, leave-one-league-out,
    devig alternativo (Shin) per la verita', strato "partite simili alle 9".

Uscite (gli unici file scritti):
  data/estimates/ou_open_corrotte_v2.csv   9 righe, probabilita' mai quote
  docs/audit_5_leghe/numeri/stima_ou_open_bakeoff.json       tutti i numeri, riproducibili

Uso: python scripts/stima_ou_open_bakeoff.py
     (cache delle inversioni in $OU_BAKEOFF_CACHE, default sotto tempdir)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scipy.optimize import minimize  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.model_selection import KFold  # noqa: E402

from src.data import sources  # noqa: E402
from src.evaluation import metrics  # noqa: E402
from src.models import market_implied as mi  # noqa: E402
from _fase52_common import boot  # noqa: E402

# --------------------------------------------------------------------------- #
# costanti
# --------------------------------------------------------------------------- #
SEED = 20260726
KFOLDS = 5
B = 10_000
RHO0 = -0.06                       # il valore di produzione
LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
NEW = ["bundesliga", "ligue_1"]
SEASONS = ["1718", "1819"]         # l'epoca Betbrain: 1X2 apertura + O/U apertura
SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "data",
        "ligue_1": ROOT / "data"}
RIC = ROOT / "data" / "ricerca_esterna"
OUT_JSON = ROOT / "docs" / "audit_5_leghe" / "numeri" / "stima_ou_open_bakeoff.json"
OUT_CSV = ROOT / "data" / "estimates" / "ou_open_corrotte_v2.csv"
CACHE = Path(os.environ.get("OU_BAKEOFF_CACHE",
                            Path(tempfile.gettempdir()) / "ou_open_bakeoff_cache"))
CACHE.mkdir(parents=True, exist_ok=True)

FOOTIQO_SEASONS = {"2017-2018": "1718", "2018-2019": "1819", "2019-2020": "1920"}
# alias residui footiqo -> nome canonico (da data/ricerca_esterna/_valida_footiqo.py)
EXTRA_ALIAS = {"Manchester Utd": "Man United", "Atl. Madrid": "Ath Madrid",
               "Dep. La Coruna": "La Coruna", "B. Monchengladbach": "M'gladbach",
               "Schalke": "Schalke 04", "Dusseldorf": "Fortuna Dusseldorf",
               "PSG": "Paris SG"}


def _canon(name: str) -> str:
    n = sources.canonical_team(str(name).strip())
    return sources.canonical_team(EXTRA_ALIAS.get(n, n))


def _logit(p) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1.0 - p))


def _expit(x) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


# --------------------------------------------------------------------------- #
# 1. dati
# --------------------------------------------------------------------------- #
def carica_footiqo() -> pd.DataFrame:
    """Chiusura 1xBet (footiqo): 1X2, scaletta O/U, GG/NG. 5 leghe x 3 stagioni."""
    fr = []
    for lg in LEAGUES:
        for lab, seas in FOOTIQO_SEASONS.items():
            fp = RIC / f"footiqo_{lg}_{lab}.json"
            if not fp.exists():
                continue
            d = pd.DataFrame(json.loads(fp.read_text(encoding="utf-8")))
            for c in d.columns:
                if c.startswith("xbetClose"):
                    d[c] = pd.to_numeric(d[c].replace("", np.nan), errors="coerce")
            d["league"] = lg
            d["season"] = seas
            d["home_team"] = d["homeTeam"].map(_canon)
            d["away_team"] = d["awayTeam"].map(_canon)
            d["date_fq"] = pd.to_datetime(d["matchDate"], format="%d-%m-%y %H:%M")
            fr.append(d)
    return pd.concat(fr, ignore_index=True)


def carica() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(insieme di valutazione, le 9 partite bersaglio) con tutte le feature."""
    F = carica_footiqo()
    fr = []
    for lg in LEAGUES:
        df = pd.read_csv(SNAP[lg] / f"{lg}_matches.csv", dtype={"season": str},
                         parse_dates=["date"])
        df = df[df.season.isin(SEASONS)].copy()
        df["league"] = lg
        df["home_team"] = df["home_team"].map(_canon)
        df["away_team"] = df["away_team"].map(_canon)
        fr.append(df)
    S = pd.concat(fr, ignore_index=True)
    need = ["odds_home_open", "odds_draw_open", "odds_away_open"]
    assert S[need].notna().all().all(), "1X2 di apertura mancante: impossibile"

    cols_fq = ["league", "season", "home_team", "away_team", "date_fq",
               "xbetClose1FT", "xbetCloseXFT", "xbetClose2FT",
               "xbetCloseOver15", "xbetCloseUnder15",
               "xbetCloseOver25", "xbetCloseUnder25",
               "xbetCloseOver35", "xbetCloseUnder35",
               "xbetCloseOver45", "xbetCloseUnder45",
               "xbetCloseBTTSY", "xbetCloseBTTSN"]
    S = S.merge(F[cols_fq], on=["league", "season", "home_team", "away_team"],
                how="left", validate="one_to_one")

    # --- devig: 1X2 di apertura (la sola informazione "di apertura" disponibile)
    d1 = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                     r.odds_away_open) for r in S.itertuples()])
    S["pH"], S["pD"], S["pA"] = d1[:, 0], d1[:, 1], d1[:, 2]
    # --- verita' (NaN sulle 9 bersaglio)
    ok = S.odds_over25_open.notna() & S.odds_under25_open.notna()
    S["y"] = np.nan
    S.loc[ok, "y"] = [metrics.devig_binary(a, b)[0] for a, b in
                      zip(S.loc[ok, "odds_over25_open"], S.loc[ok, "odds_under25_open"])]
    # --- chiusura 1xBet devigata (informazione AGGIUNTIVA, non l'apertura)
    for tag, (co, cu) in {"c15": ("xbetCloseOver15", "xbetCloseUnder15"),
                          "c25": ("xbetCloseOver25", "xbetCloseUnder25"),
                          "c35": ("xbetCloseOver35", "xbetCloseUnder35"),
                          "c45": ("xbetCloseOver45", "xbetCloseUnder45")}.items():
        m = S[co].notna() & S[cu].notna()
        S[f"p_{tag}"] = np.nan
        S.loc[m, f"p_{tag}"] = [metrics.devig_binary(a, b)[0]
                                for a, b in zip(S.loc[m, co], S.loc[m, cu])]
    m = S.xbetCloseBTTSY.notna() & S.xbetCloseBTTSN.notna()
    S["p_cbtts"] = np.nan
    S.loc[m, "p_cbtts"] = [metrics.devig_binary(a, b)[0] for a, b in
                           zip(S.loc[m, "xbetCloseBTTSY"], S.loc[m, "xbetCloseBTTSN"])]
    m = S[["xbetClose1FT", "xbetCloseXFT", "xbetClose2FT"]].notna().all(axis=1)
    for c in ["pH_c", "pD_c", "pA_c"]:
        S[c] = np.nan
    dc = np.array([metrics.devig_1x2(r.xbetClose1FT, r.xbetCloseXFT, r.xbetClose2FT)
                   for r in S[m].itertuples()])
    S.loc[m, ["pH_c", "pD_c", "pA_c"]] = dc
    S["overround_fq"] = 1.0 / S.xbetCloseOver25 + 1.0 / S.xbetCloseUnder25

    S = S.sort_values(["league", "season", "date", "home_team"]).reset_index(drop=True)
    ev = S[S.y.notna()].reset_index(drop=True)
    tg = S[S.y.isna()].reset_index(drop=True)
    return ev, tg


# --------------------------------------------------------------------------- #
# 2. inversione 1X2 -> (lambda, mu) -> P(Over 2.5), con cache
# --------------------------------------------------------------------------- #
def _invert_row(pH: float, pD: float, pA: float, rho: float,
                theta: float | None) -> tuple[float, float]:
    """Inversione ai minimi quadrati sul SOLO 1X2. Con theta=None e' identica,
    riga per riga, a market_implied.implied_lambda_mu (verificato in §0)."""
    def loss(x):
        lam, mu = x
        M = mi.score_matrix(lam, mu, rho, dp_theta=theta)
        qH, qD, qA, _ = mi._1x2_over(M)
        return (qH - pH) ** 2 + (qD - pD) ** 2 + (qA - pA) ** 2
    tot0 = 2.5
    tilt = float(np.clip(0.5 + (pH - pA) * 0.6, 0.15, 0.85))
    x0 = [max(0.2, tot0 * tilt), max(0.2, tot0 * (1.0 - tilt))]
    r = minimize(loss, x0, method="L-BFGS-B", bounds=[(0.1, 4.5), (0.1, 4.5)])
    return float(r.x[0]), float(r.x[1])


def inversione(df: pd.DataFrame, rho: float, theta: float | None,
               tag: str) -> pd.DataFrame:
    """Colonne lam, mu, T=lam+mu, D=|lam-mu|, p_raw = P(Over 2.5). Cache su disco."""
    key = f"{tag}_rho{rho:+.3f}_th{'NA' if theta is None else f'{theta:.3f}'}.npz"
    fp = CACHE / key
    if fp.exists():
        z = np.load(fp)
        if len(z["lam"]) == len(df):
            out = df.copy()
            out["lam"], out["mu"], out["p_raw"] = z["lam"], z["mu"], z["p_raw"]
            out["T"] = out.lam + out.mu
            out["D"] = (out.lam - out.mu).abs()
            return out
    lam = np.empty(len(df))
    mu = np.empty(len(df))
    praw = np.empty(len(df))
    for i, r in enumerate(df.itertuples()):
        if theta is None and abs(rho - RHO0) < 1e-12:
            l, m = mi.implied_lambda_mu(r.pH, r.pD, r.pA, None, rho)  # produzione
        else:
            l, m = _invert_row(r.pH, r.pD, r.pA, rho, theta)
        lam[i], mu[i] = l, m
        praw[i] = mi._1x2_over(mi.score_matrix(l, m, rho, dp_theta=theta))[3]
    np.savez(fp, lam=lam, mu=mu, p_raw=praw)
    out = df.copy()
    out["lam"], out["mu"], out["p_raw"] = lam, mu, praw
    out["T"] = out.lam + out.mu
    out["D"] = (out.lam - out.mu).abs()
    return out


# --------------------------------------------------------------------------- #
# 3. stimatori
# --------------------------------------------------------------------------- #
def _feat(df: pd.DataFrame, names: list[str]) -> np.ndarray:
    """Matrice di design: costante + le colonne richieste (gia' trasformate)."""
    cols = [np.ones(len(df))]
    for n in names:
        cols.append(_col(df, n))
    return np.column_stack(cols)


def _col(df: pd.DataFrame, n: str) -> np.ndarray:
    if n == "lH":
        return _logit(df.pH)
    if n == "lD":
        return _logit(df.pD)
    if n == "lA":
        return _logit(df.pA)
    if n == "absHA":
        return np.abs(_logit(df.pH) - _logit(df.pA))
    if n == "dHA":
        return _logit(df.pH) - _logit(df.pA)
    if n == "lraw":
        return _logit(df.p_raw)
    if n == "T":
        return df["T"].to_numpy(float)
    if n == "D":
        return df["D"].to_numpy(float)
    if n == "T2":
        return df["T"].to_numpy(float) ** 2
    if n == "D2":
        return df["D"].to_numpy(float) ** 2
    if n == "TD":
        return df["T"].to_numpy(float) * df["D"].to_numpy(float)
    if n == "lc25":
        return _logit(df.p_c25)
    if n == "lc15":
        return _logit(df.p_c15)
    if n == "lc35":
        return _logit(df.p_c35)
    if n == "lc45":
        return _logit(df.p_c45)
    if n == "lcbtts":
        return _logit(df.p_cbtts)
    if n == "lHc":
        return _logit(df.pH_c)
    if n == "lDc":
        return _logit(df.pD_c)
    if n == "lAc":
        return _logit(df.pA_c)
    raise KeyError(n)


def _ols(A: np.ndarray, y: np.ndarray) -> np.ndarray:
    assert np.isfinite(A).all() and np.isfinite(y).all(), \
        "valori non finiti nella matrice di design: nessun fit su NaN silenziosi"
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


class Est:
    """Interfaccia: fit(train) -> stato; predict(test) -> p_over stimata."""
    def __init__(self, kind: str, feats: list[str] | None = None, **kw):
        self.kind = kind
        self.feats = feats or []
        self.kw = kw

    def fit(self, tr: pd.DataFrame):
        k = self.kind
        if k == "media_lega":
            self.m = float(tr.y.mean())
        elif k == "bias_const":                          # M1
            self.b = float((tr.p_raw - tr.y).mean())
        elif k == "bias_lin":                            # M3 (spazio prob)
            self.c = _ols(_feat(tr, self.feats), (tr.p_raw - tr.y).to_numpy(float))
        elif k == "bias_logit":                          # M3b / M4 (spazio logit)
            self.c = _ols(_feat(tr, self.feats),
                          (_logit(tr.y) - _logit(tr.p_raw)))
        elif k == "ols_logit":                           # M2 / M5b / M5c
            self.c = _ols(_feat(tr, self.feats), _logit(tr.y))
        elif k == "ols_prob":
            self.c = _ols(_feat(tr, self.feats), tr.y.to_numpy(float))
        elif k == "isotonic":                            # M4-iso
            self.iso = IsotonicRegression(out_of_bounds="clip")
            self.iso.fit(tr.p_raw.to_numpy(float), tr.y.to_numpy(float))
        elif k == "gbm":                                 # M4-gbm / M5d
            X = np.column_stack([_col(tr, n) for n in self.feats])
            self.g = HistGradientBoostingRegressor(
                max_iter=self.kw.get("max_iter", 250),
                learning_rate=self.kw.get("lr", 0.05),
                max_leaf_nodes=self.kw.get("leaves", 15),
                min_samples_leaf=self.kw.get("msl", 40),
                l2_regularization=1.0, early_stopping=False,
                random_state=SEED)
            self.g.fit(X, _logit(tr.y))
        elif k == "identita_close":                      # M5a (nessun fit)
            pass
        else:
            raise KeyError(k)
        return self

    def predict(self, te: pd.DataFrame) -> np.ndarray:
        k = self.kind
        if k == "media_lega":
            return np.full(len(te), self.m)
        if k == "bias_const":
            return np.clip(te.p_raw.to_numpy(float) - self.b, 1e-4, 1 - 1e-4)
        if k == "bias_lin":
            return np.clip(te.p_raw.to_numpy(float) - _feat(te, self.feats) @ self.c,
                           1e-4, 1 - 1e-4)
        if k == "bias_logit":
            return _expit(_logit(te.p_raw) + _feat(te, self.feats) @ self.c)
        if k == "ols_logit":
            return _expit(_feat(te, self.feats) @ self.c)
        if k == "ols_prob":
            return np.clip(_feat(te, self.feats) @ self.c, 1e-4, 1 - 1e-4)
        if k == "isotonic":
            return np.clip(self.iso.predict(te.p_raw.to_numpy(float)), 1e-4, 1 - 1e-4)
        if k == "gbm":
            X = np.column_stack([_col(te, n) for n in self.feats])
            return _expit(self.g.predict(X))
        if k == "identita_close":
            return np.clip(te.p_c25.to_numpy(float), 1e-4, 1 - 1e-4)
        raise KeyError(k)


F1X2 = ["lH", "lD", "lA"]
F1X2B = ["lH", "lD", "lA", "absHA"]
FCLOSE = ["lc25"]
# scaletta 1xBet completa. NOTA: l'Over 4.5 (lc45) e' ESCLUSO -- 5 righe su 3.643
# non hanno quella quota, e imputarle sarebbe un modello dentro il modello; le
# altre linee della scaletta hanno copertura 100% sia in valutazione sia sulle 9.
FCLOSEP = ["lc25", "lc15", "lc35", "lcbtts", "lHc", "lDc", "lAc"]

# catalogo: nome -> (famiglia, costruttore, scope). LO DICHIARO TUTTO: e' il
# denominatore del multiple testing.
CATALOGO: dict[str, tuple[str, dict, str]] = {
    # --- riferimenti
    "M0 baseline media di lega":        ("M0", dict(kind="media_lega"), "per_lega"),
    # --- M1: il campione in carica
    "M1 bias costante (LOLO)":          ("M1", dict(kind="bias_const"), "lolo"),
    "M1b bias costante (per-lega)":     ("M1", dict(kind="bias_const"), "per_lega"),
    "M1c bias costante (pooled)":       ("M1", dict(kind="bias_const"), "pooled"),
    # --- M2: regressione nello spazio logit sui logit 1X2 devigati
    "M2 logit~1X2 (pooled)":            ("M2", dict(kind="ols_logit", feats=F1X2), "pooled"),
    "M2b logit~1X2 (per-lega)":         ("M2", dict(kind="ols_logit", feats=F1X2), "per_lega"),
    "M2c logit~1X2+|H-A| (pooled)":     ("M2", dict(kind="ols_logit", feats=F1X2B), "pooled"),
    "M2d logit~1X2+|H-A| (per-lega)":   ("M2", dict(kind="ols_logit", feats=F1X2B), "per_lega"),
    "M2e prob~1X2 (per-lega)":          ("M2", dict(kind="ols_prob", feats=F1X2B), "per_lega"),
    # --- M3: bias funzione del totale atteso lambda+mu
    "M3 bias=a+b*T (per-lega)":         ("M3", dict(kind="bias_lin", feats=["T"]), "per_lega"),
    "M3b bias=a+b*T (pooled)":          ("M3", dict(kind="bias_lin", feats=["T"]), "pooled"),
    "M3c logit-bias=a+b*T (per-lega)":  ("M3", dict(kind="bias_logit", feats=["T"]), "per_lega"),
    "M3d logit-bias=a+b*T (pooled)":    ("M3", dict(kind="bias_logit", feats=["T"]), "pooled"),
    # --- M4: mio. Superficie di debias nelle coordinate naturali (T, Delta)
    "M4 logit-bias su (T,D) quad (per-lega)":
        ("M4", dict(kind="bias_logit", feats=["T", "D", "T2", "D2", "TD"]), "per_lega"),
    "M4b logit-bias su (T,D) quad (pooled)":
        ("M4", dict(kind="bias_logit", feats=["T", "D", "T2", "D2", "TD"]), "pooled"),
    "M4c logit-bias su (T,D) lin (per-lega)":
        ("M4", dict(kind="bias_logit", feats=["T", "D"]), "per_lega"),
    "M4d isotonica su p_raw (per-lega)": ("M4", dict(kind="isotonic"), "per_lega"),
    "M4e GBM su 1X2+inversione (pooled)":
        ("M4", dict(kind="gbm", feats=["lD", "dHA", "lraw", "T", "D"]), "pooled"),
    # --- M5: usa la CHIUSURA 1xBet (informazione aggiuntiva, NON l'apertura)
    "M5 chiusura 1xBet grezza":         ("M5", dict(kind="identita_close"), "pooled"),
    "M5b logit~chiusura (per-lega)":    ("M5", dict(kind="ols_logit", feats=FCLOSE), "per_lega"),
    "M5c logit~chiusura (pooled)":      ("M5", dict(kind="ols_logit", feats=FCLOSE), "pooled"),
    "M5d logit~chiusura+1X2ap (per-lega)":
        ("M5", dict(kind="ols_logit", feats=FCLOSE + F1X2B), "per_lega"),
    "M5e logit~chiusura+1X2ap (pooled)":
        ("M5", dict(kind="ols_logit", feats=FCLOSE + F1X2B), "pooled"),
    "M5f logit~scaletta1xBet+1X2ap (pooled)":
        ("M5", dict(kind="ols_logit", feats=FCLOSEP + F1X2B), "pooled"),
    "M5g logit~scaletta1xBet+1X2ap (per-lega)":
        ("M5", dict(kind="ols_logit", feats=FCLOSEP + F1X2B), "per_lega"),
    "M5h GBM su scaletta1xBet+1X2ap (pooled)":
        ("M5", dict(kind="gbm", feats=FCLOSEP + ["lD", "dHA", "lraw", "T"]), "pooled"),
}


def _train_mask(tr: pd.DataFrame, scope: str, lg: str) -> np.ndarray:
    if scope == "pooled":
        return np.ones(len(tr), bool)
    if scope == "per_lega":
        return (tr.league == lg).to_numpy()
    if scope == "lolo":
        return (tr.league != lg).to_numpy()
    raise KeyError(scope)


def cv_predict(ev: pd.DataFrame, spec: dict, scope: str,
               folds: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    """Predizione out-of-fold su TUTTE le righe di `ev`. Il fit vede SOLO le
    fold di train (e, secondo lo scope, solo alcune leghe)."""
    pred = np.full(len(ev), np.nan)
    for tr_idx, te_idx in folds:
        tr_all = ev.iloc[tr_idx]
        te = ev.iloc[te_idx]
        pooled_est = None
        for lg, g in te.groupby("league", observed=True):
            if scope == "pooled":                     # un solo fit per fold
                if pooled_est is None:
                    pooled_est = Est(**spec).fit(tr_all)
                est = pooled_est
            else:
                est = Est(**spec).fit(tr_all[_train_mask(tr_all, scope, lg)])
            pred[g.index.to_numpy()] = est.predict(g)
    assert np.isfinite(pred).all()
    return pred


# --------------------------------------------------------------------------- #
# 4. valutazione
# --------------------------------------------------------------------------- #
def scoring(ev: pd.DataFrame, pred: np.ndarray) -> dict:
    e = np.abs(pred - ev.y.to_numpy(float))
    d = {"mae": float(e.mean()), "rmse": float(np.sqrt((e ** 2).mean())),
         "p90": float(np.quantile(e, 0.90)), "p99": float(np.quantile(e, 0.99)),
         "max": float(e.max()), "n": int(len(e))}
    d["mae_per_lega"] = {lg: float(e[(ev.league == lg).to_numpy()].mean())
                         for lg in LEAGUES}
    d["mae_leghe_nuove"] = float(e[ev.league.isin(NEW).to_numpy()].mean())
    return d


def main() -> int:
    t0 = time.time()
    res: dict = {"seed": SEED, "k_fold": KFOLDS, "B_bootstrap": B,
                 "generato": time.strftime("%Y-%m-%dT%H:%M:%S")}
    rng = np.random.default_rng(SEED)

    print("== 0. dati e controllo di sanita' ==")
    ev0, tg0 = carica()
    print(f"   valutazione: {len(ev0)} partite (2017-19, 5 leghe, linea O/U integra)")
    print(f"   bersaglio  : {len(tg0)} partite senza linea O/U di apertura")
    assert len(tg0) == 9, f"attese 9 bersaglio, trovate {len(tg0)}"
    res["n_valutazione"] = int(len(ev0))
    res["n_bersaglio"] = int(len(tg0))
    res["copertura_footiqo_valutazione"] = float(ev0.p_c25.notna().mean())
    res["copertura_footiqo_bersaglio"] = float(tg0.p_c25.notna().mean())

    ev = inversione(ev0, RHO0, None, "ev")
    tg = inversione(tg0, RHO0, None, "tg")

    # --- controllo di sanita': riprodurre il numero noto del progetto (0.0267)
    sc = (ev.p_raw - ev.y).to_numpy(float)
    bias_lolo = {lg: float(sc[(ev.league != lg).to_numpy()].mean()) for lg in LEAGUES}
    err_orig = np.abs(np.array([ev.p_raw.iloc[i] - bias_lolo[ev.league.iloc[i]]
                                - ev.y.iloc[i] for i in range(len(ev))]))
    base = ev.groupby("league", observed=True).y.transform("mean").to_numpy(float)
    res["sanita"] = {
        "mae_M1_originale_LOLO_insample": round(float(err_orig.mean()), 4),
        "atteso_dal_progetto": 0.0267,
        "mae_baseline_media_lega": round(float(np.abs(base - ev.y).mean()), 4),
        "atteso_baseline": 0.0743,
        "mae_grezzo_senza_debias": round(float(np.abs(sc).mean()), 4),
        "bias_grezzo": round(float(sc.mean()), 4),
        "p90_M1_originale": round(float(np.quantile(err_orig, 0.9)), 4)}
    ok_s = (abs(err_orig.mean() - 0.0267) < 5e-5
            and abs(np.abs(base - ev.y).mean() - 0.0743) < 5e-5)
    res["sanita"]["riprodotto"] = bool(ok_s)
    print(f"   sanita': MAE M1 originale {err_orig.mean():.4f} (atteso 0.0267), "
          f"baseline {np.abs(base - ev.y).mean():.4f} (atteso 0.0743) -> "
          f"{'OK' if ok_s else 'NON RIPRODOTTO'}")
    if not ok_s:
        raise SystemExit("controllo di sanita' fallito: mi fermo (regola del progetto)")

    # --- l'inversione custom coincide con quella di produzione?
    chk = [_invert_row(r.pH, r.pD, r.pA, RHO0, None) for r in ev.head(50).itertuples()]
    dmax = max(max(abs(c[0] - l), abs(c[1] - m))
               for c, l, m in zip(chk, ev.lam.head(50), ev.mu.head(50)))
    res["sanita"]["inversione_custom_vs_produzione_maxdiff"] = float(dmax)
    print(f"   inversione custom vs produzione: max |diff| = {dmax:.2e}")

    # ---------------------------------------------------------------- bakeoff
    print(f"\n== 1. BAKEOFF: {len(CATALOGO)} varianti, k-fold k={KFOLDS} seed={SEED} ==")
    kf = KFold(n_splits=KFOLDS, shuffle=True, random_state=SEED)
    folds = list(kf.split(np.arange(len(ev))))
    preds: dict[str, np.ndarray] = {}
    tabella = {}
    for nome, (fam, spec, scope) in CATALOGO.items():
        p = cv_predict(ev, spec, scope, folds)
        preds[nome] = p
        tabella[nome] = scoring(ev, p) | {"famiglia": fam, "scope": scope}
        print(f"   {nome:42s} MAE {tabella[nome]['mae']:.4f}  "
              f"p90 {tabella[nome]['p90']:.4f}  "
              f"(nuove {tabella[nome]['mae_leghe_nuove']:.4f})")
    res["bakeoff"] = tabella
    res["n_varianti_provate"] = len(CATALOGO)
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False))  # salvataggio incrementale

    M1 = "M1 bias costante (LOLO)"
    ordinati = sorted((n for n in tabella if n != "M0 baseline media di lega"),
                      key=lambda n: tabella[n]["mae"])
    vincitore = ordinati[0]
    # miglior metodo che NON usa la chiusura (informazione di sola apertura)
    solo_ap = [n for n in ordinati if CATALOGO[n][0] != "M5"]
    vincitore_ap = solo_ap[0]
    print(f"\n   vincitore assoluto      : {vincitore} (MAE {tabella[vincitore]['mae']:.4f})")
    print(f"   vincitore SENZA chiusura: {vincitore_ap} (MAE {tabella[vincitore_ap]['mae']:.4f})")
    res["vincitore"] = vincitore
    res["vincitore_solo_apertura"] = vincitore_ap

    # ------------------------------------------------- bootstrap appaiati
    print("\n== 2. confronti appaiati (bootstrap B=10.000 sugli |errori|) ==")
    conf = {}
    visti: set[str] = set()
    y = ev.y.to_numpy(float)
    for nome in [vincitore, vincitore_ap] + ordinati[:6]:
        if nome in visti or nome == M1:
            continue
        visti.add(nome)
        d = np.abs(preds[nome] - y) - np.abs(preds[M1] - y)
        m, lo, hi, p_neg = boot(d, np.random.default_rng(SEED), B)
        conc = (lo < 0 and hi < 0) or (lo > 0 and hi > 0)
        p_one = min(p_neg, 1 - p_neg)
        conf[f"{nome} vs {M1}"] = {
            "delta_mae": round(m, 5), "ci95": [round(lo, 5), round(hi, 5)],
            "p_una_coda": round(float(p_one), 5),
            "p_bonferroni": round(float(min(1.0, p_one * len(CATALOGO))), 5),
            "verdetto": "CONCLUSIVO" if conc else "nel rumore",
            "conclusivo_dopo_bonferroni": bool(conc and p_one * len(CATALOGO) < 0.05)}
        print(f"   {nome:42s} d={m:+.5f} CI95[{lo:+.5f},{hi:+.5f}] "
              f"{conf[f'{nome} vs {M1}']['verdetto']}")
    # vincitore assoluto vs vincitore-di-sola-apertura
    if vincitore != vincitore_ap:
        d = np.abs(preds[vincitore] - y) - np.abs(preds[vincitore_ap] - y)
        m, lo, hi, _ = boot(d, np.random.default_rng(SEED), B)
        conf[f"{vincitore} vs {vincitore_ap}"] = {
            "delta_mae": round(m, 5), "ci95": [round(lo, 5), round(hi, 5)],
            "verdetto": "CONCLUSIVO" if (lo < 0 < hi) is False else "nel rumore"}
    # per-lega vs generale (principio 9 del progetto: due fronti per ogni leva)
    print("\n== 2-bis. per-lega vs generale (pooled), a parita' di forma ==")
    fronti = {}
    for pl, po in [("M5g logit~scaletta1xBet+1X2ap (per-lega)",
                    "M5f logit~scaletta1xBet+1X2ap (pooled)"),
                   ("M4 logit-bias su (T,D) quad (per-lega)",
                    "M4b logit-bias su (T,D) quad (pooled)"),
                   ("M2b logit~1X2 (per-lega)", "M2 logit~1X2 (pooled)"),
                   ("M1b bias costante (per-lega)", "M1c bias costante (pooled)"),
                   ("M3 bias=a+b*T (per-lega)", "M3b bias=a+b*T (pooled)")]:
        d = np.abs(preds[pl] - y) - np.abs(preds[po] - y)
        m, lo, hi, _ = boot(d, np.random.default_rng(SEED), B)
        conc = (lo < 0 and hi < 0) or (lo > 0 and hi > 0)
        fronti[f"{pl} vs {po}"] = {
            "mae_per_lega": round(tabella[pl]["mae"], 5),
            "mae_pooled": round(tabella[po]["mae"], 5),
            "delta": round(m, 5), "ci95": [round(lo, 5), round(hi, 5)],
            "verdetto": ("per-lega MEGLIO (conclusivo)" if conc and m < 0 else
                         "pooled MEGLIO (conclusivo)" if conc else "nel rumore")}
        print(f"   {pl.split()[0]:5s} per-lega {tabella[pl]['mae']:.4f} vs pooled "
              f"{tabella[po]['mae']:.4f}: d={m:+.5f} CI95[{lo:+.5f},{hi:+.5f}] "
              f"{fronti[f'{pl} vs {po}']['verdetto']}")
    res["per_lega_vs_generale"] = fronti
    res["confronti"] = conf
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False))

    # ------------------------------------------------- effetto di rho e theta
    print("\n== 3. effetto di rho (e della dispersione theta) sull'inversione ==")
    griglia_rho = [-0.20, -0.16, -0.12, -0.10, -0.08, -0.06, -0.04, -0.02,
                   0.0, 0.04, 0.08, 0.12]
    curva = {}
    for rho in griglia_rho:
        e2 = inversione(ev0, rho, None, "ev")
        p_const = cv_predict(e2, dict(kind="bias_const"), "per_lega", folds)
        p_m4 = cv_predict(e2, dict(kind="bias_logit",
                                   feats=["T", "D", "T2", "D2", "TD"]), "per_lega", folds)
        curva[f"{rho:+.2f}"] = {
            "mae_grezzo": round(float(np.abs(e2.p_raw - e2.y).mean()), 5),
            "bias_grezzo": round(float((e2.p_raw - e2.y).mean()), 5),
            "mae_debias_costante": round(float(np.abs(p_const - y).mean()), 5),
            "mae_debias_superficie_M4": round(float(np.abs(p_m4 - y).mean()), 5)}
        print(f"   rho={rho:+.2f}  grezzo {curva[f'{rho:+.2f}']['mae_grezzo']:.4f} "
              f"(bias {curva[f'{rho:+.2f}']['bias_grezzo']:+.4f})  "
              f"+bias-cost {curva[f'{rho:+.2f}']['mae_debias_costante']:.4f}  "
              f"+M4 {curva[f'{rho:+.2f}']['mae_debias_superficie_M4']:.4f}")
    res["curva_rho"] = curva

    curva_th = {}
    for th in [0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.22, 1.30]:
        e2 = inversione(ev0, RHO0, th, "ev")
        p_const = cv_predict(e2, dict(kind="bias_const"), "per_lega", folds)
        curva_th[f"{th:.2f}"] = {
            "mae_grezzo": round(float(np.abs(e2.p_raw - e2.y).mean()), 5),
            "bias_grezzo": round(float((e2.p_raw - e2.y).mean()), 5),
            "mae_debias_costante": round(float(np.abs(p_const - y).mean()), 5)}
        print(f"   theta={th:.2f}  grezzo {curva_th[f'{th:.2f}']['mae_grezzo']:.4f}  "
              f"+bias-cost {curva_th[f'{th:.2f}']['mae_debias_costante']:.4f}")
    res["curva_theta"] = curva_th
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False))

    # ------------------------------------------------- confutazioni
    print("\n== 4. confutazioni del vincitore ==")
    conf_out = {}

    # C1 - permutazione della feature portante: il vantaggio deve sparire
    ev_perm = ev.copy()
    idx = np.random.default_rng(SEED).permutation(len(ev_perm))
    if CATALOGO[vincitore][0] == "M5":
        for c in ["p_c25", "p_c15", "p_c35", "p_c45", "p_cbtts",
                  "pH_c", "pD_c", "pA_c"]:
            ev_perm[c] = ev_perm[c].to_numpy()[idx]
        etichetta = "chiusura 1xBet permutata"
    else:
        for c in ["p_raw", "T", "D"]:
            ev_perm[c] = ev_perm[c].to_numpy()[idx]
        etichetta = "inversione permutata"
    p_perm = cv_predict(ev_perm, CATALOGO[vincitore][1], CATALOGO[vincitore][2], folds)
    conf_out["C1_permutazione"] = {
        "cosa": etichetta,
        "mae_vincitore": round(tabella[vincitore]["mae"], 5),
        "mae_con_feature_permutata": round(float(np.abs(p_perm - y).mean()), 5),
        "atteso": "il MAE deve degradare fino alla baseline: se non degrada, "
                  "il vantaggio non veniva da quella feature"}
    print(f"   C1 {etichetta}: MAE {np.abs(p_perm - y).mean():.4f} "
          f"contro {tabella[vincitore]['mae']:.4f}")

    # C2 - leave-one-season-out (trasferimento temporale, non nella selezione)
    folds_s = [((ev.season != s).to_numpy().nonzero()[0],
                (ev.season == s).to_numpy().nonzero()[0]) for s in SEASONS]
    # C3 - leave-one-league-out (la lega bersaglio mai vista in fit)
    folds_l = [((ev.league != lg).to_numpy().nonzero()[0],
                (ev.league == lg).to_numpy().nonzero()[0]) for lg in LEAGUES]
    for tag, fl in [("C2_leave_one_season_out", folds_s),
                    ("C3_leave_one_league_out", folds_l)]:
        blocco = {}
        for nome in {M1, vincitore, vincitore_ap}:
            fam, spec, scope = CATALOGO[nome]
            sc_use = "pooled" if (tag.startswith("C3") and scope != "pooled") else scope
            p = cv_predict(ev, spec, sc_use, fl)
            blocco[nome] = {"mae": round(float(np.abs(p - y).mean()), 5),
                            "scope_usato": sc_use}
            if nome != M1:
                d = np.abs(p - y) - np.abs(
                    cv_predict(ev, CATALOGO[M1][1], "pooled" if tag.startswith("C3")
                               else CATALOGO[M1][2], fl) - y)
                m, lo, hi, _ = boot(d, np.random.default_rng(SEED), B)
                blocco[nome] |= {"delta_vs_M1": round(m, 5),
                                 "ci95": [round(lo, 5), round(hi, 5)],
                                 "verdetto": "CONCLUSIVO" if (lo < 0 and hi < 0) or
                                             (lo > 0 and hi > 0) else "nel rumore"}
        conf_out[tag] = blocco
        print(f"   {tag}: " + "; ".join(f"{k.split()[0]} {v['mae']:.4f}"
                                        for k, v in blocco.items()))

    # C4 - verita' devigata con Shin invece che moltiplicativo
    def shin_binary(o1: float, o2: float) -> float:
        pi1, pi2 = 1.0 / o1, 1.0 / o2
        s = pi1 + pi2
        lo_, hi_ = 0.0, 0.5
        for _ in range(80):
            z = 0.5 * (lo_ + hi_)
            q = [(np.sqrt(z * z + 4 * (1 - z) * pi * pi / s) - z) / (2 * (1 - z))
                 for pi in (pi1, pi2)]
            if sum(q) > 1.0:
                lo_ = z
            else:
                hi_ = z
        z = 0.5 * (lo_ + hi_)
        return float((np.sqrt(z * z + 4 * (1 - z) * pi1 * pi1 / s) - z) / (2 * (1 - z)))

    y_shin = np.array([shin_binary(a, b) for a, b in
                       zip(ev.odds_over25_open, ev.odds_under25_open)])
    ev_shin = ev.copy()
    ev_shin["y"] = y_shin
    blocco = {}
    for nome in {M1, vincitore, vincitore_ap}:
        p = cv_predict(ev_shin, CATALOGO[nome][1], CATALOGO[nome][2], folds)
        blocco[nome] = round(float(np.abs(p - y_shin).mean()), 5)
    conf_out["C4_verita_devig_Shin"] = blocco | {
        "nota": "cambia la definizione della verita': serve a vedere se la "
                "graduatoria dipende dal devig moltiplicativo"}
    print(f"   C4 verita' Shin: " + "; ".join(f"{k.split()[0]} {v:.4f}"
                                              for k, v in blocco.items()))

    # C5 - strato "partite simili alle 9 bersaglio" (le 9 NON sono un campione
    #      casuale: 4 su 9 sono favoriti estremi)
    z_ev = np.column_stack([_logit(ev.pD), _logit(ev.pH) - _logit(ev.pA)])
    z_tg = np.column_stack([_logit(tg.pD), _logit(tg.pH) - _logit(tg.pA)])
    sd = z_ev.std(axis=0)
    vicini = set()
    for r in z_tg:
        dd = np.sqrt((((z_ev - r) / sd) ** 2).sum(axis=1))
        vicini.update(np.argsort(dd)[:100].tolist())
    vic = np.array(sorted(vicini))
    blocco = {"n_strato": int(len(vic))}
    for nome in {M1, vincitore, vincitore_ap}:
        blocco[nome] = round(float(np.abs(preds[nome][vic] - y[vic]).mean()), 5)
    d = np.abs(preds[vincitore][vic] - y[vic]) - np.abs(preds[M1][vic] - y[vic])
    m, lo, hi, _ = boot(d, np.random.default_rng(SEED), B)
    blocco |= {"delta_vincitore_vs_M1": round(m, 5),
               "ci95": [round(lo, 5), round(hi, 5)],
               "verdetto": "CONCLUSIVO" if (lo < 0 and hi < 0) or (lo > 0 and hi > 0)
                           else "nel rumore"}
    conf_out["C5_strato_simili_alle_9"] = blocco
    print(f"   C5 strato simile (n={len(vic)}): " +
          "; ".join(f"{k.split()[0]} {v}" for k, v in blocco.items()
                    if k in (M1, vincitore, vincitore_ap)))

    # C6 - sanita' della chiusura 1xBet sulle 9 bersaglio (se il vincitore la usa)
    ladder_ok = int(((tg.p_c15 >= tg.p_c25) & (tg.p_c25 >= tg.p_c35)
                     & (tg.p_c35 >= tg.p_c45)).sum())
    conf_out["C6_sanita_chiusura_sulle_9"] = {
        "overround_medio_bersaglio": round(float(tg.overround_fq.mean()), 4),
        "overround_medio_valutazione": round(float(ev.overround_fq.mean()), 4),
        "scaletta_monotona": f"{ladder_ok}/{len(tg)}",
        "coperte": int(tg.p_c25.notna().sum())}
    print(f"   C6 chiusura sulle 9: overround {tg.overround_fq.mean():.4f}, "
          f"scaletta monotona {ladder_ok}/{len(tg)}")

    # C8 - le 9 bersaglio NON sono un campione casuale: dove cadono?
    #      (e il vincitore sta EXTRAPOLANDO o interpolando?)
    perc = {}
    for r in tg.itertuples():
        perc[f"{r.home_team}-{r.away_team}"] = {
            "T": round(float(r.T), 3), "perc_T": round(float((ev["T"] < r.T).mean()), 3),
            "D": round(float(r.D), 3), "perc_D": round(float((ev["D"] < r.D).mean()), 3),
            "p_c25": round(float(r.p_c25), 3),
            "perc_p_c25": round(float((ev.p_c25 < r.p_c25).mean()), 3)}
    conf_out["C8_dove_cadono_le_9"] = {
        "per_partita": perc,
        "range_T_valutazione": [round(float(ev["T"].min()), 3), round(float(ev["T"].max()), 3)],
        "range_T_bersaglio": [round(float(tg["T"].min()), 3), round(float(tg["T"].max()), 3)],
        "extrapolazione": bool(tg["T"].min() < ev["T"].min() or tg["T"].max() > ev["T"].max()
                               or tg.p_c25.min() < ev.p_c25.min()
                               or tg.p_c25.max() > ev.p_c25.max()),
        "nota": "le 9 sono partite da TOTALE ALTO (percentili 64-98): il MAE medio "
                "del bakeoff NON e' l'errore atteso su di loro -- vale lo strato C5"}
    print(f"   C8 le 9 cadono ai percentili T "
          f"{min(v['perc_T'] for v in perc.values()):.2f}-{max(v['perc_T'] for v in perc.values()):.2f}; "
          f"extrapolazione: {conf_out['C8_dove_cadono_le_9']['extrapolazione']}")

    # C7 - il vantaggio del vincitore e' un artefatto del k-fold casuale?
    #      ripeto con 10 semi diversi
    semi = []
    for s in range(SEED, SEED + 10):
        fl = list(KFold(n_splits=KFOLDS, shuffle=True, random_state=s)
                  .split(np.arange(len(ev))))
        pv = cv_predict(ev, CATALOGO[vincitore][1], CATALOGO[vincitore][2], fl)
        p1 = cv_predict(ev, CATALOGO[M1][1], CATALOGO[M1][2], fl)
        semi.append(float(np.abs(pv - y).mean() - np.abs(p1 - y).mean()))
    conf_out["C7_stabilita_su_10_semi"] = {
        "delta_medio": round(float(np.mean(semi)), 5),
        "delta_min": round(float(np.min(semi)), 5),
        "delta_max": round(float(np.max(semi)), 5),
        "segno_costante": bool(np.all(np.sign(semi) == np.sign(semi[0])))}
    print(f"   C7 10 semi: delta in [{np.min(semi):+.5f},{np.max(semi):+.5f}], "
          f"segno costante {np.all(np.sign(semi) == np.sign(semi[0]))}")
    res["confutazioni"] = conf_out
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False))

    # ------------------------------------------------- stima finale sulle 9
    print("\n== 5. stima finale delle 9 partite bersaglio ==")
    righe = []
    for nome, colonna in [(vincitore, "p_over25_open_est"),
                          (vincitore_ap, "p_over25_open_est_solo1x2"),
                          (M1, "p_over25_open_est_M1")]:
        fam, spec, scope = CATALOGO[nome]
        vals = np.full(len(tg), np.nan)
        for lg, g in tg.groupby("league", observed=True):
            tr = ev[_train_mask(ev, scope, lg)]
            vals[g.index.to_numpy()] = Est(**spec).fit(tr).predict(g)
        tg[colonna] = vals
    err_lega = {lg: tabella[vincitore]["mae_per_lega"][lg] for lg in LEAGUES}
    err_strato = conf_out["C5_strato_simili_alle_9"][vincitore]
    usa_chiusura = CATALOGO[vincitore][0] == "M5"

    # --------------------------------------------------------------------- #
    # 6. FUORI CONCORSO: e' salvabile UN SOLO LATO della linea corrotta?
    #    Non e' un metodo del bakeoff -- usa il dato che il progetto ha
    #    dichiarato corrotto, e la regola R6 (approvata dall'utente) dice che
    #    il mercato si scarta IN BLOCCO. Lo misuro comunque, perche' se il lato
    #    Over fosse integro non staremmo stimando: staremmo LEGGENDO il dato.
    # --------------------------------------------------------------------- #
    print("\n== 6. FUORI CONCORSO: il lato Over della linea corrotta e' integro? ==")
    ev["ovr_open"] = 1.0 / ev.odds_over25_open + 1.0 / ev.odds_under25_open
    ev["ls"] = ev.league + "|" + ev.season
    gg = ev.groupby("ls", observed=True).ovr_open
    ovr_loo = ((gg.transform("sum") - ev.ovr_open)
               / (gg.transform("count") - 1)).to_numpy(float)   # leave-one-out
    lato_over_ev = (1.0 / ev.odds_over25_open.to_numpy(float)) / ovr_loo
    lato_under_ev = 1.0 - (1.0 / ev.odds_under25_open.to_numpy(float)) / ovr_loo
    sei = {"overround_medio": round(float(ev.ovr_open.mean()), 4),
           "overround_sd": round(float(ev.ovr_open.std()), 4),
           "overround_sd_entro_lega_stagione":
               round(float(ev.groupby("ls", observed=True).ovr_open.std().mean()), 4),
           "mae_lettura_solo_lato_over": round(float(np.abs(lato_over_ev - y).mean()), 5),
           "p90_lettura_solo_lato_over": round(float(np.quantile(np.abs(lato_over_ev - y), .9)), 5),
           "mae_lettura_solo_lato_under": round(float(np.abs(lato_under_ev - y).mean()), 5),
           "nota": "l'overround della linea O/U Betbrain 2017-19 e' quasi costante: "
                   "leggere UN SOLO lato e imputare l'overround della cella "
                   "lega-stagione ricostruisce la probabilita' vera con un errore "
                   "di ~0.0016, un ordine di grandezza sotto qualunque stima."}
    print(f"   lettura di un solo lato su righe INTEGRE: MAE {sei['mae_lettura_solo_lato_over']:.5f} "
          f"(overround sd entro cella {sei['overround_sd_entro_lega_stagione']:.4f})")

    # le 8 righe corrotte: cosa dicono i due lati, letti uno alla volta?
    reg = pd.read_csv(ROOT / "data" / "correzioni_dichiarate.csv",
                      dtype={"season": str})
    reg = reg[(reg.stato == "applicata")
              & reg.colonna.isin(["odds_over25_open", "odds_under25_open"])].copy()
    reg["valore_prima"] = pd.to_numeric(reg.valore_prima, errors="coerce")
    piv = reg.pivot_table(index=["league", "season", "home_team", "away_team"],
                          columns="colonna", values="valore_prima",
                          aggfunc="first").reset_index()
    ovr_cella = ev.groupby("ls", observed=True).ovr_open.mean()
    # calibrazione: quanto si discosta la lettura-di-un-lato dalla predizione del
    # VINCITORE, su righe integre? (e' la distribuzione di riferimento del test)
    scarto_rif = np.abs(lato_over_ev - preds[vincitore])
    scarto_rif_str = np.abs(lato_over_ev[vic] - preds[vincitore][vic])
    dettaglio = []
    for r in piv.itertuples():
        k = f"{r.league}|{r.season}"
        po_o = float((1.0 / r.odds_over25_open) / ovr_cella[k])
        po_u = float(1.0 - (1.0 / r.odds_under25_open) / ovr_cella[k])
        m_ = tg[(tg.league == r.league) & (tg.season == r.season)
                & (tg.home_team == r.home_team) & (tg.away_team == r.away_team)]
        assert len(m_) == 1
        pv = float(m_.p_over25_open_est.iloc[0])
        dettaglio.append({
            "partita": f"{r.home_team}-{r.away_team}", "league": r.league,
            "season": r.season,
            "quota_over_corrotta": float(r.odds_over25_open),
            "quota_under_corrotta": float(r.odds_under25_open),
            "overround_corrotto": round(float(1 / r.odds_over25_open
                                              + 1 / r.odds_under25_open), 4),
            "p_over_da_lato_over": round(po_o, 4),
            "p_over_da_lato_under": round(po_u, 4),
            "p_over_vincitore": round(pv, 4),
            "p_over_chiusura_1xbet": round(float(m_.p_c25.iloc[0]), 4),
            "scarto_lato_over_vs_vincitore": round(po_o - pv, 4),
            "perc_nella_distribuzione_di_riferimento":
                round(float((scarto_rif < abs(po_o - pv)).mean()), 3),
            "perc_nello_strato_simile":
                round(float((scarto_rif_str < abs(po_o - pv)).mean()), 3),
            "scarto_lato_under_vs_vincitore": round(po_u - pv, 4),
            "perc_lato_under": round(float((scarto_rif < abs(po_u - pv)).mean()), 3)})
        print(f"   {r.home_team[:13]:13s}-{r.away_team[:13]:13s} "
              f"lato-over {po_o:.3f} (p{dettaglio[-1]['perc_nella_distribuzione_di_riferimento']*100:5.1f}) "
              f"| lato-under {po_u:.3f} (p{dettaglio[-1]['perc_lato_under']*100:5.1f}) "
              f"| vincitore {pv:.3f}")
    sei["righe_corrotte"] = dettaglio
    p_over_max = max(d["perc_nella_distribuzione_di_riferimento"] for d in dettaglio)
    p_under_min = min(d["perc_lato_under"] for d in dettaglio)
    sei["verdetto"] = (
        "il lato OVER e' COMPATIBILE con una quota integra (tutti gli 8 scarti "
        f"dal vincitore cadono entro il percentile {p_over_max:.2f} della "
        "distribuzione misurata su righe integre), mentre il lato UNDER NON lo e' "
        f"(tutti oltre il percentile {p_under_min:.2f}). Diagnosi: la corruzione "
        "sta nel lato UNDER, non nella riga intera."
        if p_over_max < 0.95 and p_under_min > 0.99 else
        "nessuna diagnosi netta: gli scarti dei due lati non si separano.")
    sei["conseguenza"] = (
        "SE si accettasse di leggere il solo lato Over (cosa che la regola R6, "
        "approvata dall'utente, oggi VIETA: 'il mercato si scarta IN BLOCCO'), "
        "l'errore atteso su 8 delle 9 righe scenderebbe da "
        f"{tabella[vincitore]['mae']:.4f} a {sei['mae_lettura_solo_lato_over']:.4f}, "
        "cioe' non sarebbe piu' una stima ma quasi il dato. La 9a riga "
        "(bundesliga 1819 Bayern Munich-Hoffenheim) non ha nessun lato: per "
        "quella resta la stima. DECISIONE DELL'UTENTE, non mia: qui c'e' solo "
        "la misura.")
    print(f"   -> {sei['verdetto']}")

    # 6-bis. il MECCANISMO: se il lato Under e' quello rotto, che cos'e' quel
    #        numero? Confronto con TUTTA la scaletta della chiusura 1xBet.
    scal = {"U1.5": "p_c15", "U2.5": "p_c25", "U3.5": "p_c35", "U4.5": "p_c45"}
    diffs = {k: [] for k in scal}
    for r in piv.itertuples():
        k_ = f"{r.league}|{r.season}"
        p_imp = float((1.0 / r.odds_under25_open) / ovr_cella[k_])
        m_ = tg[(tg.league == r.league) & (tg.season == r.season)
                & (tg.home_team == r.home_team) & (tg.away_team == r.away_team)].iloc[0]
        for lab, col in scal.items():
            diffs[lab].append(abs(p_imp - (1.0 - float(m_[col]))))
    mecc = {lab: round(float(np.mean(v)), 4) for lab, v in diffs.items()}
    vinc_linea = min(mecc, key=mecc.get)
    sei["meccanismo_quota_under"] = {
        "mae_contro_ogni_linea_della_chiusura_1xbet": mecc,
        "linea_piu_vicina": vinc_linea,
        "verdetto": (
            f"la quota finita nella colonna Under 2.5 e' quella dell'{vinc_linea} "
            f"(MAE {mecc[vinc_linea]:.4f} contro {mecc['U2.5']:.4f} dell'Under 2.5): "
            "non e' un numero casuale, e' uno SLITTAMENTO DI LINEA. Cio' spiega "
            "l'overround 1.26-1.34 senza chiamare in causa il lato Over."
            if vinc_linea != "U2.5" else
            "nessuno slittamento di linea identificabile.")}
    print(f"   6-bis meccanismo: la quota nella colonna Under 2.5 e' l'{vinc_linea} "
          f"(MAE {mecc[vinc_linea]:.4f} vs {mecc['U2.5']:.4f} dell'Under 2.5)")
    res["fuori_concorso_lato_over"] = sei
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    lato_by_key = {(d["league"], d["season"], d["partita"]): d for d in dettaglio}
    assert len(lato_by_key) == len(dettaglio) == 8

    print("\n== 5-bis. tabella finale delle 9 partite bersaglio ==")
    for r in tg.itertuples():
        chiave = (r.league, r.season, f"{r.home_team}-{r.away_team}")
        dd = lato_by_key.get(chiave)
        righe.append({
            "league": r.league, "season": r.season,
            "date": pd.Timestamp(r.date).date().isoformat(),
            "home_team": r.home_team, "away_team": r.away_team,
            "p_over25_open_est": round(float(r.p_over25_open_est), 4),
            "p_under25_open_est": round(1 - float(r.p_over25_open_est), 4),
            "metodo": vincitore,
            "p_over25_open_est_solo1x2": round(float(r.p_over25_open_est_solo1x2), 4),
            "metodo_solo1x2": vincitore_ap,
            "p_over25_open_est_M1_precedente": round(float(r.p_over25_open_est_M1), 4),
            "mae_atteso": round(tabella[vincitore]["mae"], 4),
            "mae_atteso_lega": round(err_lega[r.league], 4),
            "mae_atteso_strato_simili": round(float(err_strato), 4),
            "p90_err_atteso": round(tabella[vincitore]["p90"], 4),
            # FUORI CONCORSO (vedi §6 del json): lettura del solo lato Over della
            # linea corrotta. NON e' una stima -- e' quasi il dato -- ma viola la
            # regola R6 "il mercato si scarta in blocco": decisione dell'utente.
            "p_over25_lettura_lato_over_FUORI_CONCORSO":
                (round(dd["p_over_da_lato_over"], 4) if dd else ""),
            "mae_atteso_lettura_lato_over":
                (round(sei["mae_lettura_solo_lato_over"], 4) if dd else ""),
            "fonte_informazione": ("1X2 di apertura (Betbrain) + chiusura 1xBet "
                                   "(footiqo)" if usa_chiusura
                                   else "1X2 di apertura (Betbrain)"),
            "avvertenza": ("STIMA dell'apertura, non l'apertura: usa anche la "
                           "CHIUSURA di un altro book (1xBet), quindi assorbe il "
                           "movimento apertura->chiusura. NON usare questa riga per "
                           "misurare il movimento apertura->chiusura."
                           if usa_chiusura else
                           "STIMA dell'apertura ricavata dal solo 1X2 di apertura."),
            "motivo": ("linea O/U di apertura corrotta (overround impossibile) o "
                       "assente alla fonte; dato vero non recuperabile"),
        })
    out = pd.DataFrame(righe)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(out[["league", "season", "home_team", "away_team", "p_over25_open_est",
               "p_over25_open_est_solo1x2", "p_over25_open_est_M1_precedente",
               "p_over25_lettura_lato_over_FUORI_CONCORSO"]].to_string(index=False))
    res["stime"] = righe
    res["secondi"] = round(time.time() - t0, 1)
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"\n-> {OUT_CSV}")
    print(f"-> {OUT_JSON}")
    print("   probabilita' STIMATE, mai quote: restano FUORI dagli snapshot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
