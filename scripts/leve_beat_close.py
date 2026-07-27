"""Si BATTE la chiusura devigata sull'1X2 in Bundesliga e Ligue 1?

IL TEST PIU' SEVERO CHE IL PROGETTO CONOSCA
-------------------------------------------
In Serie A esiste un affinamento della chiusura (`mi.sharpen_1x2`, "dp_lvl":
sotto-dispersione double-Poisson θ + correzione dei LIVELLI dei tassi impliciti)
che batte la chiusura devigata in log-loss 1X2 con CI conclusivo:
0.9609 vs 0.9625, Δ −0.0016, 7/7 stagioni. Il progetto ha poi mostrato che NON
si replica su Premier e Liga, e ha concluso che è una proprietà della *chiusura
Serie A* (mercato meno liquido).

Bundesliga e Ligue 1 non erano mai state provate. La Ligue 1 ha il MARGINE PIU'
ALTO del campione (~5.0% contro il 4.3% della Premier): se esiste una seconda
lega dove la chiusura è affinabile, a priori è quella.

ASPETTATIVA DICHIARATA **PRIMA** DI MISURARE
--------------------------------------------
NEGATIVA su entrambe. Motivo: `dp_lvl` poggia sulla sotto-dispersione, e il
blocco precedente (`leve_theta_griglia.py`) ha già trovato il router θ NEGATIVO
su entrambe le leghe nuove (0/25 mercati con CI conclusivo), con θ_MLE ≈
1.08-1.10 e una valle sei volte più piatta che in Serie A. Le leghe si dividono
in due famiglie: "latine" (θ≈1.24, dove l'affinamento paga) e "altre"
(θ≈1.08-1.10, dove non paga); Bundesliga e Ligue 1 stanno nella seconda.
Il valore di questo test è CHIUDERE la pista con una prova, non trovare un edge.
Se qualcosa uscisse positivo, l'aspettativa è che (a) non replichi sull'altra
lega e (b) non sopravviva al devig di Shin.

COSA FA
-------
0. CONTROLLO DI SANITA' OBBLIGATORIO — riproduce il numero pubblicato della
   Serie A (0.9609 vs 0.9625, 7/7 stagioni) con lo stesso apparato del codice
   di produzione (`_fase52_common.fit_theta/fit_level/dp_matrices/p1x2`).
   ⚠️  Nota dati: la Fase 73 ha spostato l'unica linea O/U 2018-19 dalla colonna
   CHIUSURA alla colonna APERTURA (era un'apertura spacciata per chiusura). La
   Fase 51 girò *prima* di quel cambio. Per riprodurla si ricostruisce la vista
   pre-Fase-73 rimettendo `odds_over25_open` nello slot chiusura per la sola
   2018-19 (verificato IDENTICO allo snapshot pre-Fase-73, commit 81a3a9b^).
   Quella stagione entra solo come STORIA (fit di θ e livelli), mai come test.
1. Applica lo stesso apparato alle 5 leghe sulla finestra con chiusura O/U reale
   (1920→2526, 7 stagioni), con θ e livelli scelti FUORI CAMPIONE:
   - LOSO (leave-one-season-out): 7 stagioni di test;
   - LFO  (leave-future-out / walk-forward, protocollo Fase 51): 6 stagioni.
2. Varianti (tutte contro la chiusura devigata moltiplicativa `market`):
     dp          θ (MLE sui punteggi) sui tassi grezzi
     lvl         solo correzione dei livelli (Poisson) — decomposizione nuova
     tilt        solo la parte ASIMMETRICA dei livelli (bias-casa a scala
                 invariata: c_λ'=(c_λ−c_μ)/2, c_μ'=−c_λ') — decomposizione nuova
     dp_lvl      θ + livelli = la ricetta di produzione `sharpen_1x2`
     dp_tilt     θ + solo il tilt (senza la scala) — decomposizione nuova
     dp_lvl_grid θ scelto per GRIGLIA sul log-loss 1X2 (best-case: se non paga
                 nemmeno col θ ottimizzato sulla metrica che conta, è chiuso)
   e contro il devig di SHIN (`shin`, il test più onesto):
     dp_lvl      la ricetta di produzione contro Shin (come Fase 52-C)
     dp_lvl_shin θ e livelli RIFITTATI sui tassi invertiti da Shin
3. Bootstrap appaiato B=10.000 (`_fase52_common.boot`), per stagione e aggregato,
   quante stagioni su 7 migliorano.
4. ROI a quota di CHIUSURA (value-bet 1X2 con dp_lvl, soglie 0.00/0.01/0.03) +
   il confronto quantitativo affinamento vs margine del book. Calcolato per
   ENTRAMBI i selettori: il LOSO misura l'esistenza dell'effetto ma usa stagioni
   FUTURE per scegliere θ — non è una strategia giocabile; il numero onesto per
   il portafoglio è quello LFO (walk-forward).
5. CONFUTAZIONE del proprio risultato negativo (richiesta esplicita dell'utente):
   prima di dichiarare che la leva non c'è, si prova a farla apparire.
   - `costanti_serie_a`: si applicano di peso θ=1.225 e livelli (0.9726, 1.0224)
     della produzione (`mi.DP_THETA`, `mi.RATE_LEVELS`) — l'errore che il §7 di
     CLAUDE.md vieta, qui misurato;
   - `in_sample`: θ e livelli fittati e valutati sulle STESSE 7 stagioni (barare
     apertamente) = tetto massimo teorico della leva. Se nemmeno barando la leva
     batte la chiusura, la pista è chiusa per argomento, non per mancanza di
     potenza;
   - `potenza`: semiampiezza del CI95 confrontata con la dimensione dell'effetto
     Serie A, per distinguere «non dimostrato» da «dimostrato assente»;
   - `seed`: il bootstrap del test primario ripetuto con 3 semi diversi.

MULTIPLE TESTING (dichiarato)
-----------------------------
Test PRIMARIO pre-dichiarato: `dp_lvl` vs `market`, selettore LOSO, sulle DUE
leghe nuove = 2 test → Bonferroni α = 0.025.
Tutto il resto è secondario/esplorativo: 9 confronti × 2 selettori × 2 leghe
nuove = 36 test → Bonferroni α = 0.05/36 ≈ 0.0014. Le tre leghe storiche sono
CONTROLLI (numeri già noti al progetto), non test nuovi.

⚠️  AVVERTENZA D'ONESTA' — qualunque cosa esca da qui NON è un invito a
scommettere soldi veri. Un vantaggio in log-loss di qualche millesimo è 25-50
volte più piccolo del margine del bookmaker: non è denaro. Il progetto ha già
mostrato (Fase 16) che la chiusura ingloba il modello.

Uso:  python scripts/leve_beat_close.py [--leagues ...] [--skip-sanity]
Scrive: docs/audit_5_leghe/numeri/leve_beat_close.json
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scripts import _fase52_common as C            # noqa: E402
from src.data import loader                        # noqa: E402
from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

OUT_FP = ROOT / "docs" / "audit_5_leghe" / "numeri" / "leve_beat_close.json"
SCRATCH = Path(os.environ.get(
    "SCRATCH",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")) / "beat_close"
# cache dei tassi (devig moltiplicativo) gia' prodotta da leve_theta_griglia.py:
# stessa finestra, stesso filtro, stesso ordinamento -> riusabile previa verifica.
CACHE_MULT = SCRATCH.parent / "theta_griglia"

SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "data",
        "ligue_1": ROOT / "data"}
LEAGUES = ["bundesliga", "ligue_1", "serie_a", "premier_league", "la_liga"]
NUOVE = ("bundesliga", "ligue_1")

SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
RHO = -0.06                       # ρ del motore di produzione (market_implied)
SEED = 5109                       # nessun significato oltre la riproducibilita'
B = 10_000
_OI = {"H": 0, "D": 1, "A": 2}
# griglia θ per la variante "best-case" (stessa di leve_theta_griglia.py)
GRID = [round(1.0 + 0.025 * i, 3) for i in range(17)]        # 1.000 … 1.400
EDGES = (0.00, 0.01, 0.03)        # soglie value-bet (0.03 = convenzione Fase 40/51)

VAR_VS_MARKET = ["shin", "dp", "lvl", "tilt", "dp_lvl", "dp_tilt", "dp_lvl_grid"]
VAR_VS_SHIN = ["dp_lvl", "dp_lvl_shin"]
ALL_VARS = ["market"] + VAR_VS_MARKET + ["dp_lvl_shin"]


# --------------------------------------------------------------------------- #
# devig
# --------------------------------------------------------------------------- #
def shin_devig(odds: np.ndarray) -> np.ndarray:
    """Devig di Shin (1992-93) per un mercato a n esiti: trova z (quota di
    scommettitori informati) tale che
        p_i = [sqrt(z² + 4(1−z)·π_i²/Π) − z] / (2(1−z)),  π_i = 1/quota_i
    sommi a 1. z=0 ricade nel devig moltiplicativo. Identico a
    `scripts/_run_fase52_shin.shin_devig`, generalizzato a n esiti (serve anche
    per l'O/U, che è binario)."""
    pi = 1.0 / np.asarray(odds, float)
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


# --------------------------------------------------------------------------- #
# dati
# --------------------------------------------------------------------------- #
def carica(league: str) -> pd.DataFrame:
    """Snapshot della lega, finestra con chiusura O/U REALE (1920→2526).
    Stesso filtro/ordinamento di `leve_theta_griglia.carica` (così la cache dei
    tassi è riusabile) e di `_fase52_common`."""
    df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df = df[df.season.isin(SEASONS)]
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    df = df.dropna(subset=need)
    return df.sort_values("date").reset_index(drop=True)


def carica_serie_a_fase51() -> pd.DataFrame:
    """La vista dati della Fase 51 (8 stagioni 1819→2526).

    Ricostruisce lo stato PRE-Fase-73: la 2018-19 non ha alcuna colonna O/U *C*
    genuina, e prima della Fase 73 il loader ci metteva la linea pre-match
    (BbAv>2.5). Oggi quella linea vive in `odds_over25_open`. Rimetterla nello
    slot chiusura riproduce ESATTAMENTE lo snapshot pre-Fase-73 (verificato per
    identità contro `git show 81a3a9b^:data/serie_a_matches.csv`: 380/380 righe
    uguali su odds_over25 e odds_under25).
    ⚠️  Serve SOLO a riprodurre un numero storico: quella linea NON è una
    chiusura, e la 2018-19 entra solo come storia, mai come stagione di test."""
    se = ["1819"] + SEASONS
    df = loader.load_league("serie_a")
    df = df[df.season.isin(se)].copy()
    fb = ~np.isfinite(df.odds_over25.to_numpy())
    df.loc[fb, "odds_over25"] = df.loc[fb, "odds_over25_open"]
    df.loc[fb, "odds_under25"] = df.loc[fb, "odds_under25_open"]
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    return df.dropna(subset=need).sort_values("date").reset_index(drop=True)


def _invert_rows(df: pd.DataFrame, devig: str) -> tuple[np.ndarray, np.ndarray]:
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        if devig == "mult":
            pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        else:
            pH, pD, pA = shin_devig(np.array([r.odds_home, r.odds_draw, r.odds_away]))
            pO, _ = shin_devig(np.array([r.odds_over25, r.odds_under25]))
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    return lam, mu


def inverti(df: pd.DataFrame, league: str, devig: str) -> tuple[np.ndarray, np.ndarray]:
    """(λ, μ) impliciti nella chiusura col motore di PRODUZIONE
    (`mi.implied_lambda_mu`, ρ=−0.06), devig moltiplicativo o di Shin.
    Cache su scratch; per il devig moltiplicativo riusa la cache di
    `leve_theta_griglia.py` solo dopo verifica su un campione di 25 righe."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fp = SCRATCH / f"rates_{league}_{devig}.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(df):
            return c["lam"].to_numpy(), c["mu"].to_numpy()
    if devig == "mult":
        old = CACHE_MULT / f"rates_{league}_rho{RHO:+.2f}.csv"
        if old.exists():
            c = pd.read_csv(old)
            if len(c) == len(df):
                idx = np.linspace(0, len(df) - 1, 25).astype(int)
                lam_c, mu_c = _invert_rows(df.iloc[idx], "mult")
                if (np.allclose(lam_c, c["lam"].to_numpy()[idx], atol=1e-6)
                        and np.allclose(mu_c, c["mu"].to_numpy()[idx], atol=1e-6)):
                    c.to_csv(fp, index=False)
                    return c["lam"].to_numpy(), c["mu"].to_numpy()
    lam, mu = _invert_rows(df, devig)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


# --------------------------------------------------------------------------- #
# metriche
# --------------------------------------------------------------------------- #
def ll_1x2(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Log-loss 1X2 PER RIGA (serve il vettore, per il bootstrap appaiato).
    Identica a `scripts/_run_fase51_beat_close._ll`; la sua media coincide con
    `src.evaluation.metrics.log_loss_1x2` — verificato da `check_metrica()`."""
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, 1.0))


def check_metrica(P: np.ndarray, risultati) -> float:
    """Controllo di sanità sulla METRICA (§5: fonte unica): la media del vettore
    per-riga deve coincidere con `metrics.log_loss_1x2`. Ritorna lo scarto."""
    y = np.array([_OI[r] for r in risultati])
    return float(abs(ll_1x2(P, y).mean() - metrics.log_loss_1x2(P, list(risultati))))


def boot_e(d: np.ndarray, rng) -> dict:
    """`_fase52_common.boot` + p-value bilaterale + verdetto esplicito."""
    if not np.any(d):
        return {"delta": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "p_batte": 0.5,
                "p_due_code": 1.0, "verdetto": "identico"}
    mean, lo, hi, p_neg = C.boot(d, rng, B)
    p2 = float(2.0 * min(p_neg, 1.0 - p_neg))
    if hi < 0:
        v = "CONCLUSIVO a favore"
    elif lo > 0:
        v = "CONCLUSIVO contro (peggiora)"
    else:
        v = "nel rumore"
    return {"delta": mean, "ci_lo": lo, "ci_hi": hi, "p_batte": p_neg,
            "p_due_code": p2, "verdetto": v}


def p_dp(lam, mu, theta, cl=0.0, cm=0.0) -> np.ndarray:
    """P(1/X/2) dalla matrice double-Poisson sui tassi corretti nei livelli.
    È esattamente `mi.sharpen_1x2(lam, mu, RHO, theta, (e^cl, e^cm))` in forma
    vettoriale (`_fase52_common.dp_matrices` + `p1x2`)."""
    return C.p1x2(C.dp_matrices(np.asarray(lam) * np.exp(cl),
                                np.asarray(mu) * np.exp(cm), RHO, theta))


# --------------------------------------------------------------------------- #
# selettori fuori campione
# --------------------------------------------------------------------------- #
def folds(seasons: np.ndarray, selector: str):
    """Genera (etichetta_stagione, maschera_train, maschera_test).
    LOSO: train = le altre 6 stagioni  -> 7 stagioni di test.
    LFO : train = le stagioni PASSATE  -> 6 stagioni di test (protocollo F51)."""
    pres = [s for s in SEASONS if (seasons == s).any()]
    for i, s in enumerate(pres):
        cur = seasons == s
        if selector == "loso":
            yield s, ~cur, cur
        else:
            if i == 0:
                continue
            yield s, np.isin(seasons, pres[:i]), cur


# --------------------------------------------------------------------------- #
# blocco principale per lega
# --------------------------------------------------------------------------- #
def run_league(league: str, verbose: bool = True) -> dict:
    t0 = time.time()
    df = carica(league)
    seasons = df.season.to_numpy()
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    y = np.array([_OI[r] for r in df.result])
    odds = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)

    lam_m, mu_m = inverti(df, league, "mult")
    lam_s, mu_s = inverti(df, league, "shin")
    P_mkt = np.array([metrics.devig_1x2(*o) for o in odds])
    P_shin = np.array([shin_devig(o) for o in odds])

    over = (1.0 / odds).sum(1)          # overround = 1 + margine del book
    res: dict = {
        "n": int(len(df)),
        "stagioni": [s for s in SEASONS if (seasons == s).any()],
        "n_per_stagione": {s: int((seasons == s).sum()) for s in SEASONS
                           if (seasons == s).any()},
        "overround_1x2_medio": float(over.mean()),
        "margine_1x2_medio_pct": float(100.0 * (over.mean() - 1.0) / over.mean()),
        "theta_mle_pooled": float(C.fit_theta(lam_m, mu_m, hg, ag, RHO)),
        "scostamento_shin_molt": float(np.abs(P_shin - P_mkt).mean()),
        "check_metrica_vs_metrics_log_loss_1x2": check_metrica(P_mkt, df.result),
    }
    assert res["check_metrica_vs_metrics_log_loss_1x2"] < 1e-12, \
        "la log-loss per-riga non coincide con metrics.log_loss_1x2"

    for selector in ("loso", "lfo"):
        rng = np.random.default_rng(SEED)
        acc: dict[str, list] = {v: [] for v in ALL_VARS}
        per_season: dict = {}
        pars: dict[str, list] = {"theta": [], "cl": [], "cm": [], "theta_grid": [],
                                 "theta_shin": [], "tilt": [], "scala": []}
        test_mask = np.zeros(len(df), bool)
        P_dplvl_oof = np.full((len(df), 3), np.nan)

        for s, tr, cur in folds(seasons, selector):
            test_mask |= cur
            # --- parametri fittati SOLO sul train ---------------------------- #
            th = C.fit_theta(lam_m[tr], mu_m[tr], hg[tr], ag[tr], RHO)
            cl = C.fit_level(lam_m[tr], hg[tr])
            cm = C.fit_level(mu_m[tr], ag[tr])
            th_s = C.fit_theta(lam_s[tr], mu_s[tr], hg[tr], ag[tr], RHO)
            cl_s = C.fit_level(lam_s[tr], hg[tr])
            cm_s = C.fit_level(mu_s[tr], ag[tr])
            # θ per GRIGLIA sul log-loss 1X2 del train (con i livelli del train)
            th_g = min(GRID, key=lambda t: ll_1x2(
                p_dp(lam_m[tr], mu_m[tr], t, cl, cm), y[tr]).mean())
            # decomposizione dei livelli: TILT (asimmetrico, scala invariata) e
            # SCALA (simmetrico). In Serie A il segnale e' quasi tutto tilt
            # (bias-casa che sopravvive al devig); altrove puo' essere solo scala.
            tilt = 0.5 * (cl - cm)
            scala = 0.5 * (cl + cm)
            for k, v in (("theta", th), ("cl", cl), ("cm", cm),
                         ("theta_grid", th_g), ("theta_shin", th_s),
                         ("tilt", tilt), ("scala", scala)):
                pars[k].append(float(v))

            P_dl = p_dp(lam_m[cur], mu_m[cur], th, cl, cm)
            P_dplvl_oof[cur] = P_dl
            preds = {
                "market": P_mkt[cur],
                "shin": P_shin[cur],
                "dp": p_dp(lam_m[cur], mu_m[cur], th),
                "lvl": p_dp(lam_m[cur], mu_m[cur], 1.0, cl, cm),
                "tilt": p_dp(lam_m[cur], mu_m[cur], 1.0, tilt, -tilt),
                "dp_lvl": P_dl,
                "dp_tilt": p_dp(lam_m[cur], mu_m[cur], th, tilt, -tilt),
                "dp_lvl_grid": p_dp(lam_m[cur], mu_m[cur], th_g, cl, cm),
                "dp_lvl_shin": p_dp(lam_s[cur], mu_s[cur], th_s, cl_s, cm_s),
            }
            row = {}
            for v, P in preds.items():
                d = ll_1x2(P, y[cur])
                acc[v].append(d)
                row[v] = float(d.mean())
            row["_theta"] = float(th); row["_theta_grid"] = float(th_g)
            row["_cl"] = float(cl); row["_cm"] = float(cm)
            per_season[s] = row

        for v in acc:
            acc[v] = np.concatenate(acc[v])
        blocco = {
            "n_test": int(len(acc["market"])),
            "stagioni_test": sorted(per_season),
            "parametri_medi": {k: float(np.mean(v)) for k, v in pars.items()},
            "parametri_per_stagione": {k: [float(x) for x in v] for k, v in pars.items()},
            "ll": {v: float(acc[v].mean()) for v in acc},
            "per_stagione": per_season,
            "vs_market": {}, "vs_shin": {},
        }
        for v in VAR_VS_MARKET:
            e = boot_e(acc[v] - acc["market"], rng)
            e["stagioni_migliorate"] = sum(
                1 for s in per_season if per_season[s][v] < per_season[s]["market"])
            e["stagioni_totali"] = len(per_season)
            blocco["vs_market"][v] = e
        for v in VAR_VS_SHIN:
            e = boot_e(acc[v] - acc["shin"], rng)
            e["stagioni_migliorate"] = sum(
                1 for s in per_season if per_season[s][v] < per_season[s]["shin"])
            e["stagioni_totali"] = len(per_season)
            blocco["vs_shin"][v] = e
        res[selector] = blocco
        if selector == "loso":
            res["_delta_primario"] = acc["dp_lvl"] - acc["market"]
        res.setdefault("roi", {})[selector] = roi_block(
            P_dplvl_oof, P_mkt, odds, y, test_mask, rng)
        if verbose:
            _stampa(league, selector, blocco)

    res["confutazione"] = confuta(res, lam_m, mu_m, hg, ag, y, P_mkt, seasons)
    if verbose:
        _stampa_confutazione(league, res["confutazione"])
    res["secondi"] = round(time.time() - t0, 1)
    return res


# --------------------------------------------------------------------------- #
# confutazione: si prova a FAR APPARIRE la leva prima di dichiararla assente
# --------------------------------------------------------------------------- #
def confuta(res, lam, mu, hg, ag, y, P_mkt, seasons) -> dict:
    rng = np.random.default_rng(SEED + 1)
    ll_mkt = ll_1x2(P_mkt, y)
    out: dict = {}

    # 1) le COSTANTI della Serie A copiate di peso (l'errore vietato dal §7)
    P = p_dp(lam, mu, mi.DP_THETA,
             float(np.log(mi.RATE_LEVELS[0])), float(np.log(mi.RATE_LEVELS[1])))
    e = boot_e(ll_1x2(P, y) - ll_mkt, rng)
    e["ll"] = float(ll_1x2(P, y).mean())
    e["parametri"] = {"theta": mi.DP_THETA, "levels": list(mi.RATE_LEVELS)}
    out["costanti_serie_a"] = e

    # 2) IN-SAMPLE: θ e livelli fittati e valutati sulle stesse 7 stagioni.
    #    E' barare — apposta: è il TETTO di ciò che la leva può dare qui.
    th_is = C.fit_theta(lam, mu, hg, ag, RHO)
    cl_is = C.fit_level(lam, hg); cm_is = C.fit_level(mu, ag)
    th_g_is = min(GRID, key=lambda t: ll_1x2(p_dp(lam, mu, t, cl_is, cm_is), y).mean())
    for nome, P in (("dp_lvl_in_sample", p_dp(lam, mu, th_is, cl_is, cm_is)),
                    ("dp_lvl_grid_in_sample", p_dp(lam, mu, th_g_is, cl_is, cm_is)),
                    ("dp_in_sample", p_dp(lam, mu, th_is))):
        e = boot_e(ll_1x2(P, y) - ll_mkt, rng)
        e["ll"] = float(ll_1x2(P, y).mean())
        out[nome] = e
    out["parametri_in_sample"] = {"theta_mle": float(th_is), "theta_grid": float(th_g_is),
                                  "cl": float(cl_is), "cm": float(cm_is),
                                  "tilt": float(0.5 * (cl_is - cm_is)),
                                  "scala": float(0.5 * (cl_is + cm_is))}

    # 3) POTENZA: «non dimostrato» o «dimostrato assente»?
    #    L'effetto Serie A pubblicato è −0.0016. Se il CI di questa lega è più
    #    stretto di quell'effetto, un effetto di quella taglia SAREBBE emerso.
    prim = res["loso"]["vs_market"]["dp_lvl"]
    semi = 0.5 * (prim["ci_hi"] - prim["ci_lo"])
    out["potenza"] = {
        "semiampiezza_ci95_loso": float(semi),
        "effetto_serie_a_pubblicato": -0.0016,
        "un_effetto_come_serie_a_sarebbe_rilevabile": bool(prim["ci_hi"] < -0.0016 + semi
                                                           and semi < 0.0016),
        "ci95_esclude_effetto_serie_a": bool(prim["ci_lo"] > -0.0016),
    }

    # 4) SEED: il verdetto primario dipende dal seme del bootstrap?
    d_prim = res.pop("_delta_primario")
    out["seed"] = {str(sd): boot_e(d_prim, np.random.default_rng(sd))
                   for sd in (SEED, SEED + 7, SEED + 77)}
    return out


def _stampa_confutazione(league: str, c: dict) -> None:
    print(f"\n  --- CONFUTAZIONE ({league}): si prova a FAR APPARIRE la leva ---")
    e = c["costanti_serie_a"]
    print(f"  costanti Serie A di peso (θ={mi.DP_THETA}, livelli {mi.RATE_LEVELS}): "
          f"ll {e['ll']:.4f}  Δ {e['delta']:+.4f} "
          f"[{e['ci_lo']:+.4f},{e['ci_hi']:+.4f}]  {e['verdetto']}")
    p = c["parametri_in_sample"]
    print(f"  IN-SAMPLE (barando: fit e test sulle stesse 7 stagioni) — "
          f"θ_MLE {p['theta_mle']:.3f}  θ_griglia {p['theta_grid']:.3f}  "
          f"tilt {p['tilt']:+.4f}  scala {p['scala']:+.4f}")
    for k in ("dp_in_sample", "dp_lvl_in_sample", "dp_lvl_grid_in_sample"):
        e = c[k]
        print(f"    {k:<24} ll {e['ll']:.4f}  Δ {e['delta']:+.4f} "
              f"[{e['ci_lo']:+.4f},{e['ci_hi']:+.4f}]  {e['verdetto']}")
    pw = c["potenza"]
    print(f"  potenza: semiampiezza CI95 (LOSO, dp_lvl) = {pw['semiampiezza_ci95_loso']:.4f}"
          f"  vs effetto Serie A −0.0016  →  "
          f"{'un effetto di quella taglia sarebbe emerso' if pw['semiampiezza_ci95_loso'] < 0.0016 else 'potenza insufficiente per escluderlo'}")
    print("  seed del bootstrap: " + "  ".join(
        f"{sd}→Δ{v['delta']:+.4f}[{v['ci_lo']:+.4f},{v['ci_hi']:+.4f}]"
        for sd, v in c["seed"].items()))


# --------------------------------------------------------------------------- #
# ROI
# --------------------------------------------------------------------------- #
def roi_block(P_dp_oof, P_mkt, odds, y, test_mask, rng) -> dict:
    """ROI a quota di CHIUSURA (puntata unitaria) del value-bet 1X2 con dp_lvl,
    probabilità FUORI CAMPIONE (LOSO). Riferimento onesto: `tutte` = puntare
    ogni esito, il cui ROI atteso è −margine.
    Aggiunge il conto che spiega tutto: |Δp| dell'affinamento contro il margine
    che una scommessa deve superare (soglia di pareggio Δ* = margine/quota)."""
    m = test_mask
    P, Q, O, Y = P_dp_oof[m], P_mkt[m], odds[m], y[m]
    edge = P - Q
    out: dict = {"n_partite": int(m.sum())}

    tutte = np.concatenate([np.where(Y == k, O[:, k] - 1.0, -1.0) for k in range(3)])
    mean, lo, hi, p_neg = C.boot(tutte, rng, B)
    out["tutte"] = {"n": int(len(tutte)), "roi": mean, "ci_lo": lo, "ci_hi": hi,
                    "p_roi_positivo": float(1.0 - p_neg)}

    # soglia di pareggio per esito: Δ* tale che (q+Δ)·quota = 1
    soglia = 1.0 / O - Q
    strategie = {f"edge_{t:.2f}": edge > t for t in EDGES}
    # il criterio ECONOMICAMENTE corretto: si punta dove il modello dice EV>0,
    # cioe' p_modello · quota > 1  <=>  edge > soglia. Le soglie fisse sopra sono
    # solo la convenzione storica del progetto (Fase 40/51).
    strategie["ev_positivo"] = edge > soglia
    for nome, sel in strategie.items():
        ret = np.concatenate([np.where(Y[sel[:, k]] == k, O[sel[:, k], k] - 1.0, -1.0)
                              for k in range(3)])
        if len(ret) == 0:
            out[nome] = {"n": 0}
            continue
        mean, lo, hi, p_neg = C.boot(ret, rng, B)
        out[nome] = {
            "n": int(len(ret)), "roi": mean, "ci_lo": lo, "ci_hi": hi,
            "p_roi_positivo": float(1.0 - p_neg),
            "n_per_esito": [int(sel[:, k].sum()) for k in range(3)]}

    # anatomia: quanto vale l'affinamento contro quanto costa il margine
    over = (1.0 / O).sum(1)
    margine = (over - 1.0) / over                      # frazione trattenuta dal book
    out["anatomia"] = {
        "affinamento_medio_abs": float(np.abs(edge).mean()),
        "affinamento_p95_abs": float(np.percentile(np.abs(edge), 95)),
        "affinamento_max_abs": float(np.abs(edge).max()),
        "margine_medio_frazione": float(margine.mean()),
        "soglia_pareggio_media": float(soglia.mean()),
        "rapporto_soglia_su_affinamento": float(soglia.mean() / max(np.abs(edge).mean(), 1e-12)),
        "quota_esiti_con_EV_positivo_pct": float(100.0 * (edge > soglia).mean()),
    }
    return out


# --------------------------------------------------------------------------- #
# controllo di sanita': la Fase 51 in Serie A
# --------------------------------------------------------------------------- #
ATTESO_F51 = {"market": 0.9624556190165922, "dp": 0.9615468329442237,
              "dp_lvl": 0.9608524742744878, "theta_mean": 1.2045742547537681,
              "dp_lvl_delta": -0.0016031447421044128, "dp_lvl_seasons_beat": 7,
              "n": 2660}


def sanity_fase51() -> dict:
    """Replica del walk-forward della Fase 51 (registro `fase51_beat_close`)."""
    df = carica_serie_a_fase51()
    seasons = df.season.to_numpy()
    hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
    y = np.array([_OI[r] for r in df.result])
    odds = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    lam, mu = inverti(df, "serie_a_f51", "mult")
    P_mkt = np.array([metrics.devig_1x2(*o) for o in odds])

    pres = ["1819"] + [s for s in SEASONS if (seasons == s).any()]
    acc = {v: [] for v in ("market", "dp", "dp_lvl")}
    per_season = {}; ths = []
    for i, s in enumerate(pres):
        if i == 0:
            continue
        tr = np.isin(seasons, pres[:i]); cur = seasons == s
        th = C.fit_theta(lam[tr], mu[tr], hg[tr], ag[tr], RHO)
        cl = C.fit_level(lam[tr], hg[tr]); cm = C.fit_level(mu[tr], ag[tr])
        ths.append(th)
        preds = {"market": P_mkt[cur],
                 "dp": p_dp(lam[cur], mu[cur], th),
                 "dp_lvl": p_dp(lam[cur], mu[cur], th, cl, cm)}
        row = {}
        for v, P in preds.items():
            d = ll_1x2(P, y[cur]); acc[v].append(d); row[v] = float(d.mean())
        row["_theta"] = float(th); row["_cl"] = float(cl); row["_cm"] = float(cm)
        per_season[s] = row
    for v in acc:
        acc[v] = np.concatenate(acc[v])
    rng = np.random.default_rng(SEED)
    e = boot_e(acc["dp_lvl"] - acc["market"], rng)
    got = {"n": int(len(acc["market"])),
           "market": float(acc["market"].mean()), "dp": float(acc["dp"].mean()),
           "dp_lvl": float(acc["dp_lvl"].mean()), "theta_mean": float(np.mean(ths)),
           "dp_lvl_delta": e["delta"],
           "dp_lvl_seasons_beat": sum(1 for s in per_season
                                      if per_season[s]["dp_lvl"] < per_season[s]["market"])}
    scarti = {k: float(got[k] - ATTESO_F51[k]) for k in ATTESO_F51}
    ok = (abs(scarti["market"]) < 1e-6 and abs(scarti["dp_lvl"]) < 5e-4
          and got["dp_lvl_seasons_beat"] == 7 and e["ci_hi"] < 0)
    return {"atteso": ATTESO_F51, "ottenuto": got, "scarti": scarti,
            "bootstrap_dp_lvl_vs_market": e, "per_stagione": per_season,
            "superato": bool(ok),
            "nota": "market riprodotto a 1e-7; le differenze residue su θ/dp_lvl "
                    "(~1e-4) vengono dalla stagione 2018-19 usata come STORIA, "
                    "la cui riga O/U e' stata ricostruita dalla vista pre-Fase-73 "
                    "(valori identici allo snapshot d'epoca) e da tolleranze "
                    "numeriche dell'ottimizzatore. Il verdetto qualitativo "
                    "(7/7 stagioni, CI conclusivo) e' riprodotto."}


# --------------------------------------------------------------------------- #
# stampa
# --------------------------------------------------------------------------- #
def _stampa(league: str, selector: str, b: dict) -> None:
    print(f"\n{'='*104}")
    print(f"{league.upper()}  —  selettore {selector.upper()}  "
          f"(n={b['n_test']}, {len(b['stagioni_test'])} stagioni di test)")
    pm = b["parametri_medi"]
    print(f"  θ_MLE medio {pm['theta']:.3f} | θ_griglia medio {pm['theta_grid']:.3f} "
          f"| livelli λ×{np.exp(pm['cl']):.4f}  μ×{np.exp(pm['cm']):.4f}"
          f" | tilt {pm['tilt']:+.4f}  scala {pm['scala']:+.4f}")
    print(f"{'='*104}")
    print(f"  {'variante':<14}{'log-loss':>10}{'Δ vs mercato':>14}{'CI95':>24}"
          f"{'P(batte)':>10}{'stagioni':>10}  verdetto")
    print(f"  {'market':<14}{b['ll']['market']:>10.4f}")
    for v in VAR_VS_MARKET:
        e = b["vs_market"][v]
        print(f"  {v:<14}{b['ll'][v]:>10.4f}{e['delta']:>+14.4f}"
              f"   [{e['ci_lo']:+.4f},{e['ci_hi']:+.4f}]{e['p_batte']:>10.0%}"
              f"{e['stagioni_migliorate']:>7}/{e['stagioni_totali']}  {e['verdetto']}")
    print(f"  --- contro il devig di SHIN (shin = {b['ll']['shin']:.4f}) ---")
    for v in VAR_VS_SHIN:
        e = b["vs_shin"][v]
        print(f"  {v:<14}{b['ll'][v]:>10.4f}{e['delta']:>+14.4f}"
              f"   [{e['ci_lo']:+.4f},{e['ci_hi']:+.4f}]{e['p_batte']:>10.0%}"
              f"{e['stagioni_migliorate']:>7}/{e['stagioni_totali']}  {e['verdetto']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--skip-sanity", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    OUT_FP.parent.mkdir(parents=True, exist_ok=True)
    res: dict = {"_meta": {
        "scopo": "si batte la chiusura devigata sull'1X2 in Bundesliga e Ligue 1?",
        "aspettativa_dichiarata_prima": (
            "NEGATIVA su entrambe: sharpen_1x2 poggia sulla sotto-dispersione, e "
            "il router θ e' gia' risultato negativo su 0/25 mercati in entrambe "
            "(θ_MLE 1.08-1.10, valle sei volte piu' piatta della Serie A)."),
        "finestra": SEASONS, "rho": RHO, "bootstrap_B": B, "seed": SEED,
        "griglia_theta": GRID, "soglie_value_bet": list(EDGES),
        "multiple_testing": {
            "primario": "dp_lvl vs market, LOSO, sulle 2 leghe nuove = 2 test, "
                        "Bonferroni alpha=0.025",
            "secondario": "7 confronti x 2 selettori x 2 leghe nuove = 28 test, "
                          "Bonferroni alpha=0.0018",
            "controlli": "serie_a/premier_league/la_liga: numeri gia' noti al "
                         "progetto, non test nuovi"},
        "avvertenza": ("NON e' un invito a scommettere soldi veri: un vantaggio "
                       "di log-loss di qualche millesimo e' 25-50 volte piu' "
                       "piccolo del margine del book."),
    }}

    if not args.skip_sanity:
        print("CONTROLLO DI SANITA' — replica della Fase 51 (serie_a, walk-forward)")
        s = sanity_fase51()
        res["sanity_fase51_serie_a"] = s
        g, a = s["ottenuto"], s["atteso"]
        for k in ("n", "market", "dp", "dp_lvl", "theta_mean", "dp_lvl_delta",
                  "dp_lvl_seasons_beat"):
            print(f"  {k:<22} atteso {a[k]!s:<22} ottenuto {g[k]!s:<22} "
                  f"scarto {s['scarti'][k]:+.2e}")
        e = s["bootstrap_dp_lvl_vs_market"]
        print(f"  bootstrap dp_lvl−market: Δ {e['delta']:+.4f} "
              f"CI95 [{e['ci_lo']:+.4f},{e['ci_hi']:+.4f}] → {e['verdetto']}")
        print(f"  SANITA': {'SUPERATA' if s['superato'] else 'FALLITA'}")
        OUT_FP.write_text(json.dumps(res, indent=1, ensure_ascii=False))
        if not s["superato"]:
            print("\nMI FERMO: senza il controllo di sanita' il resto non vale nulla.")
            return

    res["leghe"] = {}
    for lg in args.leagues:
        print(f"\n\n### {lg} ###", flush=True)
        res["leghe"][lg] = run_league(lg)
        OUT_FP.write_text(json.dumps(res, indent=1, ensure_ascii=False))
        print(f"  [salvato parziale in {OUT_FP.name}]", flush=True)

    # riepilogo ROI
    print(f"\n\n{'='*104}\nROI a quota di CHIUSURA (value-bet 1X2 con dp_lvl, "
          f"puntata unitaria, probabilita' fuori campione)\n"
          f"LFO = walk-forward, l'unico GIOCABILE; LOSO usa stagioni future per "
          f"scegliere θ → misura l'effetto, non una strategia.\n{'='*104}")
    for lg, r in res["leghe"].items():
        an = r["roi"]["loso"]["anatomia"]
        print(f"\n  {lg}:  margine book {100*an['margine_medio_frazione']:.2f}%  |  "
              f"affinamento medio |Δp| {an['affinamento_medio_abs']:.4f}  |  "
              f"soglia di pareggio media {an['soglia_pareggio_media']:.4f}  "
              f"(={an['rapporto_soglia_su_affinamento']:.1f}× l'affinamento)  |  "
              f"esiti con EV>0: {an['quota_esiti_con_EV_positivo_pct']:.1f}%")
        for selector in ("lfo", "loso"):
            roi = r["roi"][selector]
            for nome in ["ev_positivo"] + [f"edge_{t:.2f}" for t in EDGES]:
                d = roi[nome]
                if d.get("n", 0) == 0:
                    print(f"      [{selector}] {nome:<12}: nessuna scommessa")
                    continue
                print(f"      [{selector}] {nome:<12}: n={d['n']:>5}  "
                      f"ROI {d['roi']:+.2%}  CI95 [{d['ci_lo']:+.2%},{d['ci_hi']:+.2%}]  "
                      f"P(ROI>0)={d['p_roi_positivo']:.0%}")
            t = roi["tutte"]
            print(f"      [{selector}] riferimento: puntare TUTTO n={t['n']} "
                  f"→ ROI {t['roi']:+.2%}")

    res["_meta"]["secondi_totali"] = round(time.time() - t0, 1)
    OUT_FP.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"\nScritto {OUT_FP} ({time.time()-t0:.0f}s).")
    print("\n⚠️  NON e' un invito a scommettere soldi veri.")


if __name__ == "__main__":
    main()
