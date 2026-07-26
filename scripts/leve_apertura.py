"""Il motore market-implied a partire dall'APERTURA (invece che dalla chiusura),
su Bundesliga e Ligue 1.

PERCHE'
-------
Sulle 3 leghe storiche il progetto ha gia' verificato che il motore funziona anche
partendo dall'apertura. Sulle due leghe nuove non e' mai stato provato, ed e'
interessante per due motivi:
  (a) l'apertura esiste anche nel 2017-19 (la chiusura O/U no) -> la finestra e'
      di 9 stagioni invece di 7: +40% di partite, ed e' il rimedio principale al
      limite di risoluzione (1-2 millesimi di log-loss) che ha reso inconcludenti
      quasi tutte le leve del blocco precedente;
  (b) l'apertura e' il prezzo che si vede PRIMA: e' l'unico rilevante per un uso
      prospettico.

AVVERTENZA SUI DATI (dichiarata prima di misurare, verificata nel blocco A).
La precedenza delle colonne football-data in `src/data/loader.py` e':
    odds_*_open       : Avg*  -> PS*   -> BbAv* -> B365*
    odds_over25_open  : Avg>2.5 -> BbAv>2.5 -> B365>2.5
    odds_* (chiusura) : AvgC* -> B365C* -> PSC*
    odds_over25       : AvgC>2.5 -> B365C>2.5      (assente nel 2017-19)
Quindi nel 2017-19 l'APERTURA 1X2 e' Pinnacle pre-match (UN book) e l'apertura
O/U e' la media Betbrain (multi-book): **due provider diversi nella stessa riga**.
Dal 2019-20 sono entrambe la media multi-book Avg*. La CHIUSURA 1X2 nel 2017-19 e'
Pinnacle (PSC*), dal 2019-20 e' AvgC*. Il blocco A misura l'overround per verificare
il cambio, e ogni risultato e' riportato anche SPEZZATO nei due regimi
(1718-1819 = "PS/BbAv" vs 1920-2526 = "Avg") per far vedere se c'e' uno scalino.

ASPETTATIVE DICHIARATE PRIMA DI MISURARE
----------------------------------------
1. (blocco B) Il market-implied dall'apertura batte la baseline su quasi tutti i
   mercati e batte il DC-da-gol su >=13/25, ma **meno nettamente** della chiusura:
   l'apertura e' un prezzo peggiore.
2. (blocco C) theta_open ~ theta_close ~ 1.08-1.11 in entrambe le leghe (famiglia
   "non latina", report 10 §2.1). Marginalmente mi aspetto theta_open <= theta_close:
   tassi piu' rumorosi -> dispersione APPARENTE piu' alta -> sotto-dispersione
   misurata piu' bassa. Il router a griglia dovrebbe restare non conclusivo.
   phi0_open: Bundesliga > 0 piccolo, Ligue 1 ~ 0 (come sulla chiusura).
3. (blocco D, LA DOMANDA CHIAVE) l'apertura affinata **non** arriva a valere la
   chiusura grezza in queste due leghe: le leve dell'affinamento (theta, phi) sono
   gia' risultate morte qui, quindi non c'e' niente con cui recuperare il divario
   apertura->chiusura, che mi aspetto tra +0.004 e +0.012 di log-loss 1X2.
   (In Serie A l'apertura affinata valeva la chiusura grezza perche' li' theta paga.)
4. (blocco E) movimento apertura->chiusura: |Delta p| medio ~0.02-0.03 per esito;
   la chiusura batte l'apertura con CI conclusivo; il coefficiente beta di
   "quanto del movimento e' informazione" ~ 1 (movimento tutto informativo).

ESITO (compilato DOPO aver misurato, per confronto con le aspettative)
---------------------------------------------------------------------
1. SUPERATA: l'apertura batte il DC-da-gol su 25/25 mercati in entrambe le leghe
   (mi aspettavo >=13/25) e la baseline su 24/25 (l'unico "perso" e' pari/dispari,
   che non e' predicibile da nessuno). Perde contro la chiusura su 23/25 e 22/25.
2. CONFERMATA: theta_apertura < theta_chiusura in entrambe (1.067/1.071 vs 1.080;
   1.105/1.086 vs 1.103) e il router a griglia resta 0/25 conclusivi anche con il
   40% di partite in piu'. La phi resta bocciata (peggiora la doppia 1X in
   Bundesliga con CI conclusivo, esattamente come sulla chiusura).
   Il blocco H aggiunge il pezzo che mancava: theta_DC < theta_apertura <
   theta_chiusura, 11 stagioni-lega su 12.
3. SMENTITA A META'. Sull'1X2 l'apertura grezza vale GIA' la chiusura grezza
   (+0.0016 pooled, CI95 [-0.0001, +0.0034], nel rumore): non c'e' niente da
   recuperare, e infatti l'affinamento non recupera. Sull'O/U invece la chiusura
   vince in modo conclusivo (+0.0044, CI [+0.0027, +0.0060]) e l'affinamento
   recupera solo il 18% del divario, restando conclusivamente indietro.
   Il divario apertura->chiusura non e' un fatto della "partita": e' un fatto
   dei TOTALI.
4. PARZIALMENTE SMENTITA: |Delta p| 0.016-0.022, la chiusura vince
   conclusivamente solo sull'O/U, e beta NON e' 1: 0.75-0.90 sull'1X2 (il
   movimento sovra-corregge) e 1.75-1.90 sull'O/U (sotto-corregge). Il beta>1
   e' stato CONFUTATO nel blocco F: nel rumore con selettore fuori campione,
   ridotto dal devig di Shin, in gran parte spiegato dal fatto che la chiusura
   O/U e' sotto-estrema (alfa 1.15-1.33), e ROI -3.95% / +0.91%.
5. Il cambio di provider NON crea uno scalino: sull'esperimento controllato
   (stesse partite, blocco G) l'apertura Pinnacle e l'apertura media multi-book
   danno lo STESSO log-loss (Delta +/-0.0002) nonostante 2 punti di overround
   di differenza, e lo STESSO theta a tre decimali.

METODO
------
- inversione con il codice di PRODUZIONE: `metrics.devig_1x2` / `devig_binary` +
  `mi.implied_lambda_mu` (rho = -0.06);
- prezzi dal router di produzione `mi.price_markets` (replicato in forma
  vettoriale e verificato cella per cella contro di esso: `_sanity_router`);
- log-loss per riga con le stesse formule di `scripts/_run_market_implied.ll_bin`;
- ogni parametro (theta, phi0, kappa, livelli) scelto FUORI CAMPIONE
  (leave-one-season-out; LFO walk-forward dove indicato);
- bootstrap appaiato B=10.000 (`scripts/_fase52_common.boot`) e verdetto esplicito
  CONCLUSIVO / nel rumore, con soglia di Bonferroni dichiarata;
- CONTROLLO DI SANITA': la finestra-chiusura riproduce i numeri gia' pubblicati
  (theta MLE 1.080 bundesliga / 1.103 ligue_1, report 10 §2.1).

Uso:
    python cantiere/scripts/leve_apertura.py --blocchi A B C D E
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from scripts import _fase52_common as C            # noqa: E402
from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

OUT = ROOT / "cantiere" / "out" / "leve_apertura.json"
SCRATCH = Path("/tmp/claude-0/-home-user-Polymarket-oracle/"
               "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad") / "apertura"
SNAP = {"bundesliga": ROOT / "cantiere/data/bundesliga_matches.csv",
        "ligue_1": ROOT / "cantiere/data/ligue_1_matches.csv"}
TRACER = {lg: ROOT / f"cantiere/out/tracer_pred_{lg}.csv" for lg in SNAP}
LEAGUES = ["bundesliga", "ligue_1"]

SEASONS9 = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
SEASONS7 = SEASONS9[2:]          # finestra con la chiusura O/U reale
SEASONS6 = SEASONS9[3:]          # finestra del tracer DC (walk-forward)
REGIME = {s: ("PS/BbAv" if s in ("1718", "1819") else "Avg") for s in SEASONS9}

RHO = -0.06
SEED = 1718                      # nessun significato oltre la riproducibilita'
MAXG = mi.MAX_GOALS
K = np.arange(MAXG + 1)

# --------------------------------------------------------------------------- #
# Il listino Tier 1 (le stesse 25 voci di cantiere/scripts/leve_theta_griglia.py)
# --------------------------------------------------------------------------- #
_I, _J = np.meshgrid(K, K, indexing="ij")
_TOT = _I + _J
MASKS: dict[str, np.ndarray] = {
    "home_win": _I > _J, "draw": _I == _J, "away_win": _J > _I,
    "dc_1x": _I >= _J, "dc_2x": _J >= _I,
    "over_0.5": _TOT >= 1, "over_1.5": _TOT >= 2, "over_2.5": _TOT >= 3,
    "over_3.5": _TOT >= 4, "over_4.5": _TOT >= 5,
    "btts": (_I >= 1) & (_J >= 1),
    "home_ov_0.5": _I >= 1, "home_ov_1.5": _I >= 2,
    "away_ov_0.5": _J >= 1, "away_ov_1.5": _J >= 2,
    "odd_total": (_TOT % 2) == 1,
    "home_by_2plus": (_I - _J) >= 2, "away_by_2plus": (_J - _I) >= 2,
    "cs_home": _J == 0, "cs_away": _I == 0,
    "wtn_home": (_I >= 1) & (_J == 0), "wtn_away": (_J >= 1) & (_I == 0),
}
BIN_MK = list(MASKS)
CAT_MK = ["1X2", "multigol", "risultato_esatto"]
MARKETS = BIN_MK + CAT_MK
# mercati che `mi.price_markets` prende dalla matrice TAU (senza phi)
TAU_MK = {"over_0.5", "over_1.5", "over_2.5", "over_3.5", "over_4.5",
          "home_ov_0.5", "home_ov_1.5", "away_ov_0.5", "away_ov_1.5",
          "odd_total", "cs_home", "cs_away", "multigol"}
_MGB = [(_TOT <= 1), (_TOT >= 2) & (_TOT <= 3), (_TOT >= 4)]

GRID_THETA = [round(1.0 + 0.025 * i, 3) for i in range(17)]      # 1.000 … 1.400
PHI0S = np.round(np.arange(0.0, 0.6001, 0.05), 3)
KAPPAS = np.round(np.arange(0.0, 4.0001, 0.5), 3)
GRID_PHI = [(0.0, 0.0)] + [(float(p), float(k)) for p in PHI0S if p > 0
                           for k in KAPPAS]


# ------------------------------------------------------------------ dati --- #
def carica(league: str) -> pd.DataFrame:
    """Snapshot 9 stagioni, righe con l'APERTURA 1X2+O/U completa (il requisito
    del motore). `has_close` marca dove esiste anche la chiusura 1X2+O/U."""
    df = pd.read_csv(SNAP[league], dtype={"season": str}, parse_dates=["date"])
    co = ["odds_home_open", "odds_draw_open", "odds_away_open",
          "odds_over25_open", "odds_under25_open"]
    cc = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    df["has_open"] = np.isfinite(df[co].to_numpy(float)).all(axis=1)
    df["has_close"] = np.isfinite(df[cc].to_numpy(float)).all(axis=1)
    # La CHIUSURA 1X2 esiste anche nel 2017-19 (PSC*, Pinnacle): solo la chiusura
    # O/U manca. Tenerle separate allarga il confronto sull'1X2 a 9 stagioni.
    df["has_close_1x2"] = np.isfinite(df[cc[:3]].to_numpy(float)).all(axis=1)
    df["has_close_ou"] = np.isfinite(df[cc[3:]].to_numpy(float)).all(axis=1)
    df["regime"] = df["season"].map(REGIME)
    return df.sort_values("date").reset_index(drop=True)


def inverti(df: pd.DataFrame, league: str, quale: str) -> pd.DataFrame:
    """(lam, mu) impliciti, motore di produzione. quale in {'open','close'}.
    Righe senza le quote -> NaN. Cache su scratch."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fp = SCRATCH / f"rates_{league}_{quale}.csv"
    suf = "_open" if quale == "open" else ""
    flag = "has_open" if quale == "open" else "has_close"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(df):
            df[f"lam_{quale}"] = c["lam"].to_numpy()
            df[f"mu_{quale}"] = c["mu"].to_numpy()
            return df
    lam = np.full(len(df), np.nan); mu = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if not getattr(r, flag):
            continue
        pH, pD, pA = metrics.devig_1x2(getattr(r, f"odds_home{suf}"),
                                       getattr(r, f"odds_draw{suf}"),
                                       getattr(r, f"odds_away{suf}"))
        pO, _ = metrics.devig_binary(getattr(r, f"odds_over25{suf}"),
                                     getattr(r, f"odds_under25{suf}"))
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    df[f"lam_{quale}"] = lam; df[f"mu_{quale}"] = mu
    return df


def aggancia_dc(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Aggancia i (lam, mu) del Dixon-Coles dal tracer walk-forward (6 stagioni)."""
    t = pd.read_csv(TRACER[league], dtype={"season": str, "test_season": str},
                    parse_dates=["date"])
    t = t[["date", "home_team", "away_team", "exp_home_goals", "exp_away_goals"]]
    t = t.rename(columns={"exp_home_goals": "lam_dc", "exp_away_goals": "mu_dc"})
    return df.merge(t, on=["date", "home_team", "away_team"], how="left")


# ----------------------------------------------------------- log-loss ------ #
def ll_bin(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def esiti(hg, ag) -> dict[str, np.ndarray]:
    out = {mk: np.array([bool(MASKS[mk][min(h, MAXG), min(a, MAXG)])
                         for h, a in zip(hg, ag)], float) for mk in BIN_MK}
    return out


def matrici(lam, mu, theta: float | None) -> np.ndarray:
    """Matrici (n,11,11) identiche a `mi.score_matrix(lam, mu, RHO, dp_theta)`."""
    return C.dp_matrices(np.asarray(lam, float), np.asarray(mu, float), RHO,
                         1.0 if theta is None else float(theta))


def _infla(M: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """M * (1 + phi*I), rinormalizzata (= score_matrix(diag_inflation=phi))."""
    Mp = M.copy()
    idx = np.arange(MAXG + 1)
    Mp[:, idx, idx] *= (1.0 + phi)[:, None]
    return Mp / Mp.sum(axis=(1, 2), keepdims=True)


def valuta(lam, mu, hg, ag, theta=None, phi0=0.0, kappa=0.0
           ) -> dict[str, np.ndarray]:
    """Log-loss per riga di tutti i mercati del listino, col ROUTING di
    `mi.price_markets` (tau per i totali/marginali, phi per esiti/joint)."""
    lam = np.asarray(lam, float); mu = np.asarray(mu, float)
    hg = np.asarray(hg, int); ag = np.asarray(ag, int)
    n = len(lam)
    M_tau = matrici(lam, mu, theta)
    if phi0:
        phi = phi0 * np.exp(-kappa * np.abs(lam - mu))
        M_phi = _infla(M_tau, phi)
    else:
        M_phi = M_tau
    y = esiti(hg, ag)
    out = {}
    for mk in BIN_MK:
        M = M_tau if mk in TAU_MK else M_phi
        out[mk] = ll_bin((M * MASKS[mk][None]).sum(axis=(1, 2)), y[mk])
    # 1X2 a 3 esiti
    p3 = np.stack([(M_phi * MASKS[m][None]).sum(axis=(1, 2))
                   for m in ("home_win", "draw", "away_win")], 1)
    p3 = p3 / p3.sum(1, keepdims=True)
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
    out["1X2"] = -np.log(np.clip(p3[np.arange(n), y3], 1e-15, None))
    # multigol (dalla tau, come il router)
    pmg = np.stack([(M_tau * b[None]).sum(axis=(1, 2)) for b in _MGB], 1)
    pmg = pmg / pmg.sum(1, keepdims=True)
    tot = hg + ag
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    out["multigol"] = -np.log(np.clip(pmg[np.arange(n), ymg], 1e-15, None))
    # risultato esatto (dalla matrice phi: la diagonale conta)
    hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
    out["risultato_esatto"] = -np.log(np.clip(M_phi[np.arange(n), hc, ac],
                                              1e-15, None))
    return out


def baseline_ll(df: pd.DataFrame, mask: np.ndarray) -> dict[str, np.ndarray]:
    """Baseline in-sample per stagione (frequenza dell'esito), come
    `scripts/_run_market_implied.baseline_ll`."""
    sub = df[mask]
    out = {mk: np.zeros(len(sub)) for mk in MARKETS}
    pos = 0
    for s, g in sub.groupby("season", sort=False):
        hg = g.home_goals.to_numpy(int); ag = g.away_goals.to_numpy(int)
        sl = slice(pos, pos + len(g)); pos += len(g)
        y = esiti(hg, ag)
        for mk in BIN_MK:
            out[mk][sl] = ll_bin(np.full(len(g), y[mk].mean()), y[mk])
        y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
        fr3 = np.array([(y3 == c).mean() for c in (0, 1, 2)])
        out["1X2"][sl] = -np.log(np.clip(fr3[y3], 1e-15, None))
        tot = hg + ag
        ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
        frm = np.array([(ymg == c).mean() for c in (0, 1, 2)])
        out["multigol"][sl] = -np.log(np.clip(frm[ymg], 1e-15, None))
        hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
        f = np.zeros((MAXG + 1, MAXG + 1))
        for a_, b_ in zip(hc, ac):
            f[a_, b_] += 1
        f /= f.sum()
        out["risultato_esatto"][sl] = -np.log(np.clip(f[hc, ac], 1e-15, None))
    return out


def boot_e(d: np.ndarray, rng):
    """boot del progetto + p-value a due code. d identicamente nullo -> p=1."""
    if not np.any(d):
        return 0.0, 0.0, 0.0, 1.0
    m, lo, hi, pneg = C.boot(d, rng)
    return m, lo, hi, float(2.0 * min(pneg, 1.0 - pneg))


def verdetto(lo: float, hi: float) -> str:
    return "MEGLIO" if hi < 0 else ("PEGGIO" if lo > 0 else "nel rumore")


# --------------------------------------------------------------- sanity ---- #
def _sanity_router(lam, mu) -> dict:
    """La forma vettoriale deve coincidere con `mi.price_markets` cella per cella
    (con e senza theta, con e senza phi). Se non torna, ci si ferma."""
    worst = {}
    for theta, phi0, kappa in [(None, 0.0, 0.0), (1.2, 0.0, 0.0),
                               (None, 0.25, 1.5), (1.2, 0.25, 1.5)]:
        M_tau = matrici(lam, mu, theta)
        if phi0:
            phi = phi0 * np.exp(-kappa * np.abs(np.asarray(lam) - np.asarray(mu)))
            M_phi = _infla(M_tau, phi)
        else:
            M_phi = M_tau
        err = 0.0
        for i in range(len(lam)):
            d = mi.price_markets(float(lam[i]), float(mu[i]), RHO, phi0, kappa,
                                 dp_theta=theta)
            for mk in BIN_MK:
                M = M_tau if mk in TAU_MK else M_phi
                mine = float((M[i] * MASKS[mk]).sum())
                err = max(err, abs(mine - d[mk]))
            err = max(err, float(np.abs(M_phi[i] - d["score_matrix"]).max()))
        worst[f"theta={theta},phi0={phi0},kappa={kappa}"] = err
    return worst


# ============================================================ BLOCCO A ===== #
def blocco_A(dati: dict) -> dict:
    print("\n" + "=" * 96)
    print("BLOCCO A — copertura, provider, tassi impliciti")
    print("=" * 96)
    res = {}
    for lg, df in dati.items():
        righe = []
        for s, g in df.groupby("season"):
            o1 = np.isfinite(g[["odds_home_open", "odds_draw_open",
                                "odds_away_open"]].to_numpy(float)).all(1)
            oo = np.isfinite(g[["odds_over25_open",
                                "odds_under25_open"]].to_numpy(float)).all(1)
            ov1 = (1 / g.loc[o1, ["odds_home_open", "odds_draw_open",
                                  "odds_away_open"]].to_numpy(float)).sum(1)
            ovo = (1 / g.loc[oo, ["odds_over25_open",
                                  "odds_under25_open"]].to_numpy(float)).sum(1)
            c1 = np.isfinite(g[["odds_home", "odds_draw",
                                "odds_away"]].to_numpy(float)).all(1)
            cv1 = ((1 / g.loc[c1, ["odds_home", "odds_draw",
                                   "odds_away"]].to_numpy(float)).sum(1)
                   if c1.any() else np.array([np.nan]))
            righe.append({
                "season": s, "regime": REGIME[s], "n": int(len(g)),
                "open_ok": int(g.has_open.sum()), "close_ok": int(g.has_close.sum()),
                "overround_open_1x2": float(ov1.mean()),
                "overround_open_ou": float(ovo.mean()),
                "overround_close_1x2": float(np.nanmean(cv1)),
                "lam_open": float(g.lam_open.mean(skipna=True)),
                "mu_open": float(g.mu_open.mean(skipna=True)),
                "lam_close": float(g.lam_close.mean(skipna=True)),
                "mu_close": float(g.mu_close.mean(skipna=True)),
                "gol_casa": float(g.home_goals.mean()),
                "gol_osp": float(g.away_goals.mean()),
            })
        t = pd.DataFrame(righe)
        print(f"\n{lg}  (apertura completa: {int(df.has_open.sum())}/{len(df)}, "
              f"chiusura completa: {int(df.has_close.sum())}/{len(df)})")
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
        res[lg] = righe
    return res


# ============================================================ BLOCCO B ===== #
def blocco_B(dati: dict, rng) -> dict:
    print("\n" + "=" * 96)
    print("BLOCCO B — il listino Tier 1 dall'APERTURA vs DC-da-gol vs baseline")
    print("=" * 96)
    res = {}
    for lg, df in dati.items():
        res[lg] = {}
        # --- B1: finestra 9 stagioni, apertura vs baseline -----------------
        m9 = df.has_open.to_numpy()
        sub = df[m9]
        ll_open = valuta(sub.lam_open, sub.mu_open, sub.home_goals, sub.away_goals)
        ll_base = baseline_ll(df, m9)
        print(f"\n[{lg}] B1 — 9 stagioni, {int(m9.sum())} partite "
              f"(apertura vs baseline in-sample)")
        print(f"  {'mercato':<18}{'apertura':>10}{'baseline':>10}{'Delta':>11}"
              f"{'CI95':>24}  verdetto")
        b1 = {}
        vinti = 0
        for mk in MARKETS:
            d = ll_open[mk] - ll_base[mk]
            m, lo, hi, p2 = boot_e(d, rng)
            vinti += int(m < 0)
            print(f"  {mk:<18}{ll_open[mk].mean():>10.4f}{ll_base[mk].mean():>10.4f}"
                  f"{m:>+11.4f}  [{lo:+.4f},{hi:+.4f}]  {verdetto(lo, hi)}")
            b1[mk] = {"apertura": float(ll_open[mk].mean()),
                      "baseline": float(ll_base[mk].mean()),
                      "delta": m, "ci95": [lo, hi], "p2": p2}
        print(f"  -> l'apertura batte la baseline su {vinti}/{len(MARKETS)} mercati")
        res[lg]["b1_9stagioni"] = {"n": int(m9.sum()), "vinti_su_baseline": vinti,
                                   "mercati": b1}

        # --- B2: finestra del tracer (6 stagioni), apertura vs DC vs chiusura
        m6 = (df.has_open & df.has_close & df.lam_dc.notna()).to_numpy()
        sub = df[m6]
        llo = valuta(sub.lam_open, sub.mu_open, sub.home_goals, sub.away_goals)
        lld = valuta(sub.lam_dc, sub.mu_dc, sub.home_goals, sub.away_goals)
        llc = valuta(sub.lam_close, sub.mu_close, sub.home_goals, sub.away_goals)
        llb = baseline_ll(df, m6)
        print(f"\n[{lg}] B2 — 6 stagioni del tracer, {int(m6.sum())} partite "
              f"(Delta = apertura - DC; <0 = l'apertura vince)")
        print(f"  {'mercato':<18}{'apert.':>9}{'chius.':>9}{'DC-gol':>9}"
              f"{'base':>9}{'ap-DC':>10}{'CI95':>24}{'ap-ch':>10}")
        b2 = {}
        v_dc = v_base = v_ch = 0
        for mk in MARKETS:
            a, c_, d_, b_ = (llo[mk].mean(), llc[mk].mean(),
                             lld[mk].mean(), llb[mk].mean())
            m, lo, hi, p2 = boot_e(llo[mk] - lld[mk], rng)
            m2, lo2, hi2, _ = boot_e(llo[mk] - llc[mk], rng)
            v_dc += int(m < 0); v_base += int(a < b_); v_ch += int(m2 < 0)
            print(f"  {mk:<18}{a:>9.4f}{c_:>9.4f}{d_:>9.4f}{b_:>9.4f}"
                  f"{m:>+10.4f}  [{lo:+.4f},{hi:+.4f}]{m2:>+10.4f}")
            b2[mk] = {"apertura": float(a), "chiusura": float(c_),
                      "dc": float(d_), "baseline": float(b_),
                      "ap_meno_dc": m, "ci95_ap_dc": [lo, hi], "p2_ap_dc": p2,
                      "ap_meno_chiusura": m2, "ci95_ap_ch": [lo2, hi2]}
        print(f"  -> apertura batte il DC-da-gol su {v_dc}/{len(MARKETS)}, "
              f"la baseline su {v_base}/{len(MARKETS)}, "
              f"la CHIUSURA su {v_ch}/{len(MARKETS)}")
        res[lg]["b2_6stagioni"] = {"n": int(m6.sum()), "vinti_su_dc": v_dc,
                                   "vinti_su_baseline": v_base,
                                   "vinti_su_chiusura": v_ch, "mercati": b2}

        # --- B3: scalino di provider (apertura, 1X2 e O/U, per regime) ------
        b3 = {}
        for reg in ("PS/BbAv", "Avg"):
            mm = (df.has_open & (df.regime == reg)).to_numpy()
            if not mm.any():
                continue
            s2 = df[mm]
            lo_ = valuta(s2.lam_open, s2.mu_open, s2.home_goals, s2.away_goals)
            lb_ = baseline_ll(df, mm)
            b3[reg] = {"n": int(mm.sum()),
                       **{mk: {"apertura": float(lo_[mk].mean()),
                               "baseline": float(lb_[mk].mean()),
                               "guadagno": float(lb_[mk].mean() - lo_[mk].mean())}
                          for mk in ("1X2", "over_2.5", "btts",
                                     "risultato_esatto")}}
        print(f"\n[{lg}] B3 — scalino di provider (guadagno sulla baseline)")
        for reg, v in b3.items():
            print(f"  {reg:<9} n={v['n']:<5} " + "  ".join(
                f"{mk} {v[mk]['guadagno']:+.4f}"
                for mk in ("1X2", "over_2.5", "btts", "risultato_esatto")))
        res[lg]["b3_provider"] = b3
    return res


# ============================================================ BLOCCO C ===== #
def _theta_mle(df, mask, quale) -> float:
    s = df[mask]
    return float(C.fit_theta(s[f"lam_{quale}"].to_numpy(),
                             s[f"mu_{quale}"].to_numpy(),
                             s.home_goals.to_numpy(int),
                             s.away_goals.to_numpy(int), RHO))


def blocco_C(dati: dict, rng) -> dict:
    print("\n" + "=" * 96)
    print("BLOCCO C — theta e phi0 sull'APERTURA, confronto con la CHIUSURA")
    print("=" * 96)
    res = {}
    for lg, df in dati.items():
        blk = {}
        # --- C1: theta MLE sui punteggi ------------------------------------
        m9 = df.has_open.to_numpy()
        m7 = (df.has_open & df.has_close).to_numpy()
        blk["theta_mle"] = {
            "open_9stagioni": _theta_mle(df, m9, "open"),
            "open_7stagioni": _theta_mle(df, m7, "open"),
            "close_7stagioni": _theta_mle(df, m7, "close"),
            "open_per_regime": {
                reg: _theta_mle(df, (df.has_open & (df.regime == reg)).to_numpy(),
                                "open")
                for reg in ("PS/BbAv", "Avg")},
            "open_loso": {s: _theta_mle(df, (m9 & (df.season != s)).to_numpy(),
                                        "open") for s in SEASONS9},
        }
        t = blk["theta_mle"]
        print(f"\n[{lg}] C1 — theta MLE sui punteggi")
        print(f"  apertura 9 stagioni {t['open_9stagioni']:.3f} | "
              f"apertura 7 stagioni {t['open_7stagioni']:.3f} | "
              f"CHIUSURA 7 stagioni {t['close_7stagioni']:.3f}  "
              f"(controllo di sanita': atteso 1.080 bundesliga / 1.103 ligue_1)")
        print(f"  per regime: " + ", ".join(
            f"{k} {v:.3f}" for k, v in t["open_per_regime"].items()))
        print(f"  LOSO apertura: [{min(t['open_loso'].values()):.3f}, "
              f"{max(t['open_loso'].values()):.3f}]")

        # --- C2: griglia theta LOSO su tutto il listino (apertura) ---------
        sub = df[m9]
        lam = sub.lam_open.to_numpy(); mu = sub.mu_open.to_numpy()
        hg = sub.home_goals.to_numpy(int); ag = sub.away_goals.to_numpy(int)
        seas = sub.season.to_numpy()
        lls = {th: valuta(lam, mu, hg, ag, theta=(None if th == 1.0 else th))
               for th in GRID_THETA}
        ref = lls[1.0]
        c2 = {}
        conc = []
        peg = []
        print(f"\n[{lg}] C2 — griglia theta LOSO sull'apertura "
              f"({len(sub)} partite, 9 stagioni)")
        print(f"  {'mercato':<18}{'LL Poisson':>11}{'theta LOSO':>14}"
              f"{'Delta':>10}{'CI95':>24}{'st.+':>7}")
        for mk in MARKETS:
            sel = np.zeros(len(sub)); picks = {}
            for s in SEASONS9:
                tr = seas != s; cur = seas == s
                if not cur.any():
                    continue
                best = min(GRID_THETA, key=lambda th: lls[th][mk][tr].mean())
                picks[s] = best; sel[cur] = lls[best][mk][cur]
            d = sel - ref[mk]
            m, lo, hi, p2 = boot_e(d, rng)
            nst = sum((sel[seas == s] - ref[mk][seas == s]).mean() < 0
                      for s in SEASONS9 if (seas == s).any())
            if hi < 0:
                conc.append(mk)
            if lo > 0:
                peg.append(mk)
            ts = sorted(set(picks.values()))
            print(f"  {mk:<18}{ref[mk].mean():>11.4f}"
                  f"{f'{ts[0]:.3f}-{ts[-1]:.3f}':>14}{m:>+10.4f}  "
                  f"[{lo:+.4f},{hi:+.4f}]{nst:>5}/9")
            c2[mk] = {"ll_poisson": float(ref[mk].mean()),
                      "theta_per_stagione": {k: float(v) for k, v in picks.items()},
                      "delta": m, "ci95": [lo, hi], "p2": p2,
                      "stagioni_migliorate": int(nst)}
        print(f"  -> CI95 sotto zero (guadagno conclusivo): {len(conc)}/{len(MARKETS)} "
              f"{conc}; peggiorati con CI conclusivo: {len(peg)} {peg}")
        blk["theta_griglia_loso_apertura"] = {
            "n": len(sub), "conclusivi": conc, "peggiorati": peg, "mercati": c2}
        blk["theta_best_in_sample_apertura"] = {
            mk: float(min(GRID_THETA, key=lambda th: lls[th][mk].mean()))
            for mk in MARKETS}
        # profondita' della valle sul risultato esatto (il confronto del report 10)
        v = [lls[th]["risultato_esatto"].mean() for th in GRID_THETA]
        blk["valle_risultato_esatto_apertura"] = float(min(v) - v[0])

        # --- C3: phi0 sull'apertura ---------------------------------------
        isd = (sub.home_goals.to_numpy() == sub.away_goals.to_numpy()).astype(float)
        phi_mle = {"pooled_open": list(map(float, mi.fit_balance_phi(
            lam, mu, isd, RHO)))}
        sc = df[m7]
        phi_mle["pooled_close"] = list(map(float, mi.fit_balance_phi(
            sc.lam_close.to_numpy(), sc.mu_close.to_numpy(),
            (sc.home_goals.to_numpy() == sc.away_goals.to_numpy()).astype(float),
            RHO)))
        phi_mle["open_per_regime"] = {}
        for reg in ("PS/BbAv", "Avg"):
            g = sub[sub.regime == reg]
            phi_mle["open_per_regime"][reg] = list(map(float, mi.fit_balance_phi(
                g.lam_open.to_numpy(), g.mu_open.to_numpy(),
                (g.home_goals.to_numpy() == g.away_goals.to_numpy()).astype(float),
                RHO)))
        print(f"\n[{lg}] C3 — phi(|lam-mu|)")
        print(f"  MLE apertura (phi0, kappa) = "
              f"({phi_mle['pooled_open'][0]:.3f}, {phi_mle['pooled_open'][1]:.3f}) | "
              f"chiusura = ({phi_mle['pooled_close'][0]:.3f}, "
              f"{phi_mle['pooled_close'][1]:.3f})")
        # griglia LOSO sui mercati della famiglia-pareggio + 1X2
        fam = ["1X2", "draw", "dc_1x", "dc_2x", "btts"]
        cache = {}
        for p0, kp in GRID_PHI:
            cache[(p0, kp)] = valuta(lam, mu, hg, ag, theta=None,
                                     phi0=p0, kappa=kp)
        refp = cache[(0.0, 0.0)]
        c3 = {}
        print(f"  {'mercato':<12}{'senza phi':>11}{'con phi':>10}{'Delta':>11}"
              f"{'CI95':>24}  (phi0,kappa) scelti")
        for mk in fam:
            sel = np.zeros(len(sub)); picks = {}
            for s in SEASONS9:
                tr = seas != s; cur = seas == s
                if not cur.any():
                    continue
                best = min(GRID_PHI, key=lambda pk: cache[pk][mk][tr].mean())
                picks[s] = best; sel[cur] = cache[best][mk][cur]
            m, lo, hi, p2 = boot_e(sel - refp[mk], rng)
            uniq = sorted(set(picks.values()))
            print(f"  {mk:<12}{refp[mk].mean():>11.4f}{sel.mean():>10.4f}"
                  f"{-m:>+11.5f}  [{-hi:+.5f},{-lo:+.5f}]  {uniq}")
            c3[mk] = {"senza_phi": float(refp[mk].mean()),
                      "con_phi": float(sel.mean()),
                      "guadagno": float(-m), "ci95_guadagno": [-hi, -lo],
                      "p2": p2, "verdetto": verdetto(lo, hi),
                      "parametri_per_stagione": {k: list(v) for k, v in picks.items()}}
        blk["phi"] = {"mle": phi_mle, "griglia_loso_apertura": c3}
        res[lg] = blk
    return res

# ============================================================ BLOCCO D ===== #
RICETTE = ("R0", "R1", "R2", "R3", "R4")
DESCR = {"R0": "apertura GREZZA (devig)",
         "R1": "apertura ri-proiettata (Poisson)",
         "R2": "R1 + theta LOSO (router dp)",
         "R3": "R2 + phi(|lam-mu|) LOSO",
         "R4": "R2 + livelli dei tassi LOSO (sharpen rifittato)"}


def _ricette(sub: pd.DataFrame, seasons: list[str], rng) -> dict:
    """Le 5 ricette di affinamento dell'apertura + la chiusura grezza, sulle
    righe di `sub`. Tutti i parametri scelti leave-one-season-out."""
    seas = sub.season.to_numpy()
    lam = sub.lam_open.to_numpy(); mu = sub.mu_open.to_numpy()
    hg = sub.home_goals.to_numpy(int); ag = sub.away_goals.to_numpy(int)
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
    yov = (hg + ag >= 3).astype(float)
    n = len(sub)
    ll: dict[str, np.ndarray] = {}

    P_op = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                       r.odds_away_open) for r in sub.itertuples()])
    ll["R0_1X2"] = -np.log(np.clip(P_op[np.arange(n), y3], 1e-15, None))
    if sub.has_close_1x2.all():
        P_cl = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                         for r in sub.itertuples()])
        ll["C0_1X2"] = -np.log(np.clip(P_cl[np.arange(n), y3], 1e-15, None))
    if sub.has_close_ou.all():
        O_op = np.array([metrics.devig_binary(r.odds_over25_open,
                                              r.odds_under25_open)[0]
                         for r in sub.itertuples()])
        O_cl = np.array([metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
                         for r in sub.itertuples()])
        ll["R0_OU"] = ll_bin(O_op, yov)
        ll["C0_OU"] = ll_bin(O_cl, yov)

    v1 = valuta(lam, mu, hg, ag)
    ll["R1_1X2"], ll["R1_OU"] = v1["1X2"], v1["over_2.5"]

    lls = {th: valuta(lam, mu, hg, ag, theta=(None if th == 1.0 else th))
           for th in GRID_THETA}
    picks = {}
    for tag, mk in (("1X2", "1X2"), ("OU", "over_2.5")):
        sel = np.zeros(n); pk = {}
        for s in seasons:
            tr = seas != s; cur = seas == s
            if not cur.any():
                continue
            best = min(GRID_THETA, key=lambda th: lls[th][mk][tr].mean())
            pk[s] = best; sel[cur] = lls[best][mk][cur]
        ll[f"R2_{tag}"] = sel; picks[tag] = pk

    cache = {pk: valuta(lam, mu, hg, ag, theta=None, phi0=pk[0], kappa=pk[1])
             for pk in GRID_PHI}
    sel = np.zeros(n); pk3 = {}
    for s in seasons:
        tr = seas != s; cur = seas == s
        if not cur.any():
            continue
        best = min(GRID_PHI, key=lambda p: cache[p]["1X2"][tr].mean())
        pk3[s] = best; sel[cur] = cache[best]["1X2"][cur]
    ll["R3_1X2"] = sel
    ll["R3_OU"] = ll["R2_OU"]          # la phi e' routata FUORI dai totali

    sel1 = np.zeros(n); sel2 = np.zeros(n); pk4 = {}
    for s in seasons:
        tr = seas != s; cur = seas == s
        if not cur.any():
            continue
        cl = float(np.sum(hg[tr]) / np.sum(lam[tr]))
        cm = float(np.sum(ag[tr]) / np.sum(mu[tr]))
        th = picks["1X2"].get(s, 1.0)
        v = valuta(lam[cur] * cl, mu[cur] * cm, hg[cur], ag[cur],
                   theta=(None if th == 1.0 else th))
        sel1[cur] = v["1X2"]; sel2[cur] = v["over_2.5"]
        pk4[s] = [cl, cm, th]
    ll["R4_1X2"], ll["R4_OU"] = sel1, sel2
    return {"ll": ll, "theta_loso": picks, "phi_loso": pk3, "livelli_loso": pk4}


def _tabella_D(ll: dict, tag: str, etichetta: str, sub, rng, nric: int,
               accumula: dict | None = None) -> dict:
    base = ll[f"C0_{tag}"]
    out = {}
    if accumula is not None:
        for r in RICETTE:
            accumula.setdefault(r, []).append(ll[f"{r}_{tag}"] - base)
    print(f"  --- {etichetta} --- chiusura grezza LL {base.mean():.4f} "
          f"({len(base)} partite)")
    for r in RICETTE:
        d = ll[f"{r}_{tag}"] - base
        mm, lo, hi, p2 = boot_e(d, rng)
        bonf = "si" if p2 < 0.05 / nric else "no"
        print(f"  {r+' '+etichetta:<26}{ll[f'{r}_{tag}'].mean():>9.4f}"
              f"{mm:>+13.4f}  [{lo:+.4f},{hi:+.4f}]  {verdetto(lo, hi):<11} "
              f"p2={p2:.4f} bonf={bonf}   {DESCR[r]}")
        out[r] = {"ll": float(ll[f"{r}_{tag}"].mean()),
                  "ll_chiusura_grezza": float(base.mean()),
                  "delta": mm, "ci95": [lo, hi], "p2": p2,
                  "verdetto": verdetto(lo, hi), "bonferroni": bonf}
    gap = ll[f"R0_{tag}"].mean() - base.mean()
    best_r = min(("R1", "R2", "R3", "R4"), key=lambda r: ll[f"{r}_{tag}"].mean())
    resid = ll[f"{best_r}_{tag}"].mean() - base.mean()
    out["recupero"] = {"divario_grezzo": float(gap),
                       "ricetta_migliore": best_r, "residuo": float(resid),
                       "quota_recuperata": float((gap - resid) / gap) if gap else None}
    print(f"    divario grezzo {gap:+.4f} -> residuo migliore ({best_r}) "
          f"{resid:+.4f}" + (f"  = recuperato {(gap-resid)/gap:.1%}" if gap else ""))
    # per regime
    out["per_regime"] = {}
    for reg in ("PS/BbAv", "Avg"):
        mk = (sub.regime == reg).to_numpy()
        if not mk.any():
            continue
        out["per_regime"][reg] = {
            "n": int(mk.sum()),
            **{r: float(ll[f"{r}_{tag}"][mk].mean()) for r in RICETTE},
            "C0": float(base[mk].mean()),
            "gap_R0_C0": float((ll[f"R0_{tag}"] - base)[mk].mean())}
    for reg, v in out["per_regime"].items():
        print(f"    regime {reg:<9} n={v['n']:<5} R0 {v['R0']:.4f}  "
              f"C0 {v['C0']:.4f}  gap {v['gap_R0_C0']:+.4f}  "
              f"migliore {min(v[r] for r in RICETTE):.4f}")
    return out


def blocco_D(dati: dict, rng, _=None) -> dict:
    """LA DOMANDA CHIAVE: l'apertura affinata vale la chiusura grezza?

    Ricette (parametri scelti LOSO, mai in-sample):
      R0 apertura GREZZA        = devig delle quote di apertura
      R1 apertura ri-proiettata = market-implied Poisson (theta=1, phi=0)
      R2 R1 + theta LOSO (router dp)
      R3 R2 + phi LOSO (famiglia-pareggio)   [sull'1X2; i totali sono routati tau]
      R4 R2 + ricalibrazione dei LIVELLI dei tassi LOSO (= sharpen_1x2 rifittato)
    Riferimento: C0 chiusura GREZZA = devig delle quote di chiusura.

    DUE finestre, perche' i dati non sono simmetrici:
      1X2      -> 9 stagioni (la chiusura 1X2 esiste anche nel 2017-19: PSC*)
      O/U 2.5  -> 7 stagioni (la chiusura O/U non esiste prima del 2019-20)
    """
    print("\n" + "=" * 96)
    print("BLOCCO D — l'apertura affinata arriva a valere la chiusura grezza?")
    print("=" * 96)
    NRIC = 5 * 2 * 2       # ricette x mercati x leghe -> soglia di Bonferroni
    res = {}
    acc = {"1X2": {}, "OU": {}}
    for lg, df in dati.items():
        blk = {}
        # ---- finestra 1X2: 9 stagioni --------------------------------------
        m = (df.has_open & df.has_close_1x2).to_numpy()
        sub = df[m].reset_index(drop=True)
        r = _ricette(sub, SEASONS9, rng)
        print(f"\n[{lg}] 1X2 su {len(sub)} partite, 9 stagioni "
              f"(Bonferroni alpha=0.05/{NRIC} = {0.05/NRIC:.4f})")
        print(f"  {'ricetta':<26}{'LL':>9}{'vs chiusura':>13}"
              f"{'CI95':>20}  verdetto")
        blk["1X2_9stagioni"] = _tabella_D(r["ll"], "1X2", "1X2", sub, rng, NRIC,
                                          acc["1X2"])
        blk["1X2_9stagioni"]["n"] = len(sub)
        blk["parametri_1X2"] = {
            "theta_loso": {k: {a: float(b) for a, b in v.items()}
                           for k, v in r["theta_loso"].items()},
            "phi_loso": {k: list(v) for k, v in r["phi_loso"].items()},
            "livelli_loso": r["livelli_loso"]}
        # ---- finestra O/U: 7 stagioni --------------------------------------
        m = (df.has_open & df.has_close).to_numpy()
        sub = df[m].reset_index(drop=True)
        r = _ricette(sub, SEASONS7, rng)
        print(f"\n[{lg}] O/U 2.5 su {len(sub)} partite, 7 stagioni")
        print(f"  {'ricetta':<26}{'LL':>9}{'vs chiusura':>13}"
              f"{'CI95':>20}  verdetto")
        blk["OU_7stagioni"] = _tabella_D(r["ll"], "OU", "O/U 2.5", sub, rng, NRIC,
                                         acc["OU"])
        blk["OU_7stagioni"]["n"] = len(sub)
        # controllo: l'1X2 sulla stessa finestra di 7 stagioni (confrontabile)
        blk["1X2_7stagioni"] = _tabella_D(r["ll"], "1X2", "1X2 (7 st.)", sub,
                                          rng, NRIC)
        blk["1X2_7stagioni"]["n"] = len(sub)
        blk["parametri_OU"] = {
            "theta_loso": {k: {a: float(b) for a, b in v.items()}
                           for k, v in r["theta_loso"].items()},
            "phi_loso": {k: list(v) for k, v in r["phi_loso"].items()},
            "livelli_loso": r["livelli_loso"]}
        res[lg] = blk
    # ---- POOLED sulle due leghe (il rimedio vero al limite di risoluzione) --
    print(f"\n[POOLED 2 leghe] apertura affinata vs chiusura grezza")
    res["pooled"] = {}
    for tag, etich in (("1X2", "1X2 (9 stagioni)"), ("OU", "O/U 2.5 (7 stagioni)")):
        blocco = {}
        print(f"  --- {etich} ---")
        for r in RICETTE:
            d = np.concatenate(acc[tag][r])
            mm, lo, hi, p2 = boot_e(d, rng)
            bonf = "si" if p2 < 0.05 / NRIC else "no"
            print(f"  {r:<6} n={len(d):<6} Delta {mm:+.4f} [{lo:+.4f},{hi:+.4f}]  "
                  f"{verdetto(lo, hi):<11} p2={p2:.4f} bonf={bonf}   {DESCR[r]}")
            blocco[r] = {"n": int(len(d)), "delta": mm, "ci95": [lo, hi],
                         "p2": p2, "verdetto": verdetto(lo, hi), "bonferroni": bonf}
        res["pooled"][tag] = blocco
    return res


# ============================================================ BLOCCO E ===== #
BETAS = np.round(np.arange(-0.5, 2.001, 0.05), 3)


def blocco_E(dati: dict, rng) -> dict:
    """Quanto e' grande il movimento apertura->chiusura, e' informativo, in che
    direzione. beta = quanto del movimento e' informazione: si valuta
    p(beta) = normalizza(p_open + beta*(p_close - p_open)); beta=0 -> il
    movimento e' rumore, beta=1 -> la chiusura e' il prezzo giusto, beta>1 -> il
    movimento sotto-corregge. beta scelto LOSO (mai in-sample).

    Come nel blocco D: 1X2 su 9 stagioni, O/U su 7.
    """
    print("\n" + "=" * 96)
    print("BLOCCO E — il movimento apertura -> chiusura")
    print("=" * 96)
    res = {}
    for lg, df in dati.items():
        blk = {}
        for tag, maschera, seasons in (
                ("1X2", (df.has_open & df.has_close_1x2).to_numpy(), SEASONS9),
                ("over_2.5", (df.has_open & df.has_close).to_numpy(), SEASONS7)):
            sub = df[maschera].reset_index(drop=True)
            seas = sub.season.to_numpy(); n = len(sub)
            hg = sub.home_goals.to_numpy(int); ag = sub.away_goals.to_numpy(int)
            if tag == "1X2":
                y = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
                A = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                                r.odds_away_open)
                              for r in sub.itertuples()])
                Z = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw,
                                                r.odds_away)
                              for r in sub.itertuples()])
                lla = -np.log(np.clip(A[np.arange(n), y], 1e-15, None))
                llz = -np.log(np.clip(Z[np.arange(n), y], 1e-15, None))

                def f_beta(b, idx):
                    P = np.clip(A[idx] + b * (Z - A)[idx], 1e-6, None)
                    P = P / P.sum(1, keepdims=True)
                    return -np.log(P[np.arange(int(idx.sum())), y[idx]])
            else:
                y = (hg + ag >= 3).astype(float)
                A = np.array([metrics.devig_binary(r.odds_over25_open,
                                                   r.odds_under25_open)[0]
                              for r in sub.itertuples()])
                Z = np.array([metrics.devig_binary(r.odds_over25,
                                                   r.odds_under25)[0]
                              for r in sub.itertuples()])
                lla, llz = ll_bin(A, y), ll_bin(Z, y)

                def f_beta(b, idx):
                    return ll_bin(np.clip(A[idx] + b * (Z - A)[idx], 1e-6, 1 - 1e-6),
                                  y[idx])
            D = Z - A
            mad = float(np.abs(D).mean())
            drift = (D.mean(0).tolist() if D.ndim == 2 else float(D.mean()))
            corr = (float(np.corrcoef(A[:, 0], Z[:, 0])[0, 1]) if D.ndim == 2
                    else float(np.corrcoef(A, Z)[0, 1]))
            m1, lo1, hi1, p1 = boot_e(lla - llz, rng)
            allidx = np.ones(n, bool)
            curva = {str(b): float(f_beta(b, allidx).mean()) for b in BETAS}
            b_in = float(min(BETAS, key=lambda b: f_beta(b, allidx).mean()))
            sel = np.zeros(n); pk = {}
            for s in seasons:
                tr = (seas != s); cur = (seas == s)
                if not cur.any():
                    continue
                best = float(min(BETAS, key=lambda b: f_beta(b, tr).mean()))
                pk[s] = best; sel[cur] = f_beta(best, cur)
            ref1 = f_beta(1.0, allidx)
            mb, lob, hib, pb = boot_e(sel - ref1, rng)
            b = {"n": n, "stagioni": seasons,
                 "mad": mad,
                 "mad_per_esito": (np.abs(D).mean(0).tolist() if D.ndim == 2
                                   else None),
                 "drift_medio": drift, "corr_apertura_chiusura": corr,
                 "quota_mosse_gt_0.02": float(
                     ((np.abs(D).max(1) if D.ndim == 2 else np.abs(D)) > 0.02).mean()),
                 "ll_apertura": float(lla.mean()), "ll_chiusura": float(llz.mean()),
                 "guadagno_chiusura": m1, "ci95_guadagno": [lo1, hi1], "p2": p1,
                 "verdetto": ("la chiusura vince, CONCLUSIVO" if lo1 > 0
                              else ("l'apertura vince, CONCLUSIVO" if hi1 < 0
                                    else "nel rumore")),
                 "beta_in_sample": b_in,
                 "beta_loso": {k: float(v) for k, v in pk.items()},
                 "curva_beta_in_sample": curva,
                 "ll_beta_loso": float(sel.mean()),
                 "ll_beta1": float(ref1.mean()),
                 "delta_beta_vs_chiusura": mb, "ci95_beta": [lob, hib], "p2_beta": pb,
                 "per_regime": {}, "per_stagione": {}}
            for reg in ("PS/BbAv", "Avg"):
                mk = (sub.regime == reg).to_numpy()
                if not mk.any():
                    continue
                b["per_regime"][reg] = {
                    "n": int(mk.sum()), "mad": float(np.abs(D[mk]).mean()),
                    "ll_apertura": float(lla[mk].mean()),
                    "ll_chiusura": float(llz[mk].mean()),
                    "guadagno_chiusura": float((lla - llz)[mk].mean()),
                    "beta_in_sample": float(min(
                        BETAS, key=lambda x: f_beta(x, mk).mean()))}
            for s in seasons:
                mk = (seas == s)
                if not mk.any():
                    continue
                b["per_stagione"][s] = {
                    "n": int(mk.sum()), "mad": float(np.abs(D[mk]).mean()),
                    "guadagno_chiusura": float((lla - llz)[mk].mean()),
                    "beta_in_sample": float(min(
                        BETAS, key=lambda x: f_beta(x, mk).mean()))}
            print(f"\n[{lg}] {tag} — {n} partite, {len(b['per_stagione'])} stagioni")
            print(f"  |Delta p| medio {mad:.4f}"
                  + (f" (H {b['mad_per_esito'][0]:.4f} X {b['mad_per_esito'][1]:.4f} "
                     f"A {b['mad_per_esito'][2]:.4f})" if b["mad_per_esito"] else "")
                  + f"   corr apertura-chiusura {corr:.4f}   "
                    f"mosse >2 punti {b['quota_mosse_gt_0.02']:.1%}")
            print(f"  drift medio (chiusura - apertura): {drift}")
            print(f"  LL apertura {lla.mean():.4f} -> chiusura {llz.mean():.4f}  "
                  f"guadagno {m1:+.4f} CI95 [{lo1:+.4f},{hi1:+.4f}] -> {b['verdetto']}")
            print(f"  beta: in-sample {b_in:.2f} | LOSO {sorted(set(pk.values()))} "
                  f"| LL(beta LOSO) {sel.mean():.4f} vs LL(beta=1) {ref1.mean():.4f}"
                  f"  Delta {mb:+.4f} [{lob:+.4f},{hib:+.4f}]")
            for reg, v in b["per_regime"].items():
                print(f"    regime {reg:<9} n={v['n']:<5} |Dp| {v['mad']:.4f}  "
                      f"guadagno {v['guadagno_chiusura']:+.4f}  "
                      f"beta {v['beta_in_sample']:.2f}")
            blk[tag] = b
        res[lg] = blk
    return res


# ============================================================ BLOCCO F ===== #
# Confutazione dei due risultati del blocco E che "suonano troppo bene":
#   (i)  sull'1X2 l'apertura vale gia' la chiusura (nel rumore in entrambe);
#   (ii) sull'O/U il coefficiente beta e' ~1.8: estrapolando il movimento si
#        BATTEREBBE la chiusura. Il progetto ha stabilito che la chiusura
#        ingloba tutto: un beta>1 va trattato come sospetto finche' non
#        sopravvive a tutte le prove qui sotto.
def _sigmoide_pot(P: np.ndarray, a: float) -> np.ndarray:
    """Estremizzazione (temperature scaling): P^a rinormalizzata. Per un mercato
    binario equivale a sigma(a*logit(p)). a>1 = piu' estremo, a<1 = piu' piatto."""
    Q = np.clip(P, 1e-12, None) ** a
    return Q / Q.sum(axis=1, keepdims=True)


ALFA = np.round(np.arange(0.7, 1.601, 0.025), 3)


def blocco_F(dati: dict, rng) -> dict:
    print("\n" + "=" * 96)
    print("BLOCCO F — confutazioni e test pooled sulle due leghe")
    print("=" * 96)
    try:
        from leve_devig_shin import shin_devig
    except Exception as e:                       # pragma: no cover
        print(f"  (Shin non disponibile: {e})")
        shin_devig = None

    def prepara(df, tag):
        """Matrici (n,k) di quote apertura/chiusura + esito, per un mercato."""
        if tag == "1X2":
            m = (df.has_open & df.has_close_1x2).to_numpy()
            s = df[m].reset_index(drop=True)
            Oo = s[["odds_home_open", "odds_draw_open", "odds_away_open"]].to_numpy(float)
            Oc = s[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
            hg = s.home_goals.to_numpy(int); ag = s.away_goals.to_numpy(int)
            y = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
            seasons = SEASONS9
        else:
            m = (df.has_open & df.has_close).to_numpy()
            s = df[m].reset_index(drop=True)
            Oo = s[["odds_over25_open", "odds_under25_open"]].to_numpy(float)
            Oc = s[["odds_over25", "odds_under25"]].to_numpy(float)
            tot = (s.home_goals + s.away_goals).to_numpy(int)
            y = np.where(tot >= 3, 0, 1)          # colonna 0 = Over
            seasons = SEASONS7
        return s, Oo, Oc, y, seasons

    def ll_of(P, y):
        return -np.log(np.clip(P[np.arange(len(y)), y], 1e-15, None))

    def devig(O, come):
        if come == "mult":
            pi = 1.0 / O
            return pi / pi.sum(1, keepdims=True)
        return shin_devig(O)[0]

    res = {}
    pool = {}
    for tag in ("1X2", "over_2.5"):
        pool[tag] = {"d_raw": [], "d_beta": [], "lega": []}
    for lg, df in dati.items():
        blk = {}
        for tag in ("1X2", "over_2.5"):
            s, Oo, Oc, y, seasons = prepara(df, tag)
            seas = s.season.to_numpy(); n = len(s)
            sub = {}
            for come in ("mult", "shin"):
                if come == "shin" and shin_devig is None:
                    continue
                A, Z = devig(Oo, come), devig(Oc, come)

                def f(b, idx, A=A, Z=Z):
                    P = np.clip(A[idx] + b * (Z - A)[idx], 1e-6, None)
                    return ll_of(P / P.sum(1, keepdims=True), y[idx])
                allidx = np.ones(n, bool)
                b_in = float(min(BETAS, key=lambda b: f(b, allidx).mean()))
                # selettore LOSO e selettore LFO (walk-forward: solo il passato)
                sel_l = np.zeros(n); pk_l = {}
                sel_f = np.zeros(n); pk_f = {}; testf = np.zeros(n, bool)
                for i, sn in enumerate(seasons):
                    cur = seas == sn
                    if not cur.any():
                        continue
                    tr = seas != sn
                    pk_l[sn] = float(min(BETAS, key=lambda b: f(b, tr).mean()))
                    sel_l[cur] = f(pk_l[sn], cur)
                    past = np.isin(seas, seasons[:i])
                    if past.any():
                        pk_f[sn] = float(min(BETAS, key=lambda b: f(b, past).mean()))
                        sel_f[cur] = f(pk_f[sn], cur); testf |= cur
                ref = f(1.0, allidx)
                m1, lo1, hi1, p1 = boot_e(sel_l - ref, rng)
                m2, lo2, hi2, p2 = boot_e((sel_f - ref)[testf], rng)
                stag = {sn: float((sel_l - ref)[seas == sn].mean())
                        for sn in seasons if (seas == sn).any()}
                sub[come] = {"beta_in_sample": b_in,
                             "beta_loso": pk_l, "beta_lfo": pk_f,
                             "ll_chiusura": float(ref.mean()),
                             "ll_beta_loso": float(sel_l.mean()),
                             "delta_loso": m1, "ci95_loso": [lo1, hi1], "p2_loso": p1,
                             "n_lfo": int(testf.sum()),
                             "ll_beta_lfo": float(sel_f[testf].mean()),
                             "delta_lfo": m2, "ci95_lfo": [lo2, hi2], "p2_lfo": p2,
                             "stagioni_migliorate":
                                 int(sum(v < 0 for v in stag.values())),
                             "n_stagioni": len(stag),
                             "delta_per_stagione": stag}
                if come == "mult":
                    A_m, Z_m, ref_m, sel_m = A, Z, ref, sel_l
            # --- F2: estremizzazione della SOLA chiusura (LOSO) -------------
            sel_a = np.zeros(n); pk_a = {}
            for sn in seasons:
                cur = seas == sn
                if not cur.any():
                    continue
                tr = seas != sn
                best = float(min(ALFA, key=lambda a: ll_of(
                    _sigmoide_pot(Z_m[tr], a), y[tr]).mean()))
                pk_a[sn] = best
                sel_a[cur] = ll_of(_sigmoide_pot(Z_m[cur], best), y[cur])
            ma, loa, hia, pa = boot_e(sel_a - ref_m, rng)
            # --- F3: beta RESIDUO dopo aver estremizzato apertura e chiusura -
            a_pool = float(min(ALFA, key=lambda a: ll_of(
                _sigmoide_pot(Z_m, a), y).mean()))
            Ae, Ze = _sigmoide_pot(A_m, a_pool), _sigmoide_pot(Z_m, a_pool)

            def f_e(b, idx):
                P = np.clip(Ae[idx] + b * (Ze - Ae)[idx], 1e-6, None)
                return ll_of(P / P.sum(1, keepdims=True), y[idx])
            b_res = float(min(BETAS, key=lambda b: f_e(b, np.ones(n, bool)).mean()))
            blk[tag] = {"n": n, "devig": sub,
                        "estremizza_chiusura": {
                            "alfa_loso": pk_a, "alfa_in_sample": a_pool,
                            "ll": float(sel_a.mean()),
                            "ll_chiusura": float(ref_m.mean()),
                            "delta": ma, "ci95": [loa, hia], "p2": pa,
                            "verdetto": verdetto(loa, hia)},
                        "beta_residuo_dopo_estremizzazione": b_res}
            pool[tag]["d_raw"].append(ll_of(A_m, y) - ref_m)
            pool[tag]["d_beta"].append(sel_m - ref_m)
            pool[tag]["lega"].append(lg)
            v = sub["mult"]
            print(f"\n[{lg}] {tag} — n={n}")
            print(f"  beta (devig moltiplicativo): in-sample {v['beta_in_sample']:.2f} | "
                  f"LOSO Delta {v['delta_loso']:+.4f} [{v['ci95_loso'][0]:+.4f},"
                  f"{v['ci95_loso'][1]:+.4f}] {verdetto(*v['ci95_loso'])} | "
                  f"stagioni migliorate {v['stagioni_migliorate']}/{v['n_stagioni']}")
            print(f"  beta LFO (walk-forward, il solo usabile): n={v['n_lfo']} "
                  f"Delta {v['delta_lfo']:+.4f} [{v['ci95_lfo'][0]:+.4f},"
                  f"{v['ci95_lfo'][1]:+.4f}] {verdetto(*v['ci95_lfo'])}")
            if "shin" in sub:
                w = sub["shin"]
                print(f"  CONFUTAZIONE devig di Shin: beta in-sample "
                      f"{w['beta_in_sample']:.2f} (moltiplicativo "
                      f"{v['beta_in_sample']:.2f}) | LOSO Delta {w['delta_loso']:+.4f} "
                      f"[{w['ci95_loso'][0]:+.4f},{w['ci95_loso'][1]:+.4f}]")
            e = blk[tag]["estremizza_chiusura"]
            print(f"  CONFUTAZIONE estremizzazione della sola chiusura: alfa "
                  f"{sorted(set(e['alfa_loso'].values()))} -> Delta {e['delta']:+.4f} "
                  f"[{e['ci95'][0]:+.4f},{e['ci95'][1]:+.4f}] {e['verdetto']}")
            print(f"  beta RESIDUO dopo estremizzazione (alfa={a_pool:.3f}): {b_res:.2f}")
        # --- F4: il test dei SOLDI, solo sull'O/U (dove beta>1) -------------
        s, Oo, Oc, y, seasons = prepara(df, "over_2.5")
        seas = s.season.to_numpy(); n = len(s)
        A = devig(Oo, "mult"); Z = devig(Oc, "mult")
        roi = {}
        for etichetta, P in (("beta=1 (chiusura)", Z),
                             ("beta LOSO", None)):
            if P is None:
                P = np.zeros_like(Z)
                for sn in seasons:
                    cur = seas == sn
                    if not cur.any():
                        continue
                    tr = seas != sn

                    def f(b, idx):
                        Q = np.clip(A[idx] + b * (Z - A)[idx], 1e-6, None)
                        return ll_of(Q / Q.sum(1, keepdims=True), y[idx])
                    best = float(min(BETAS, key=lambda b: f(b, tr).mean()))
                    Q = np.clip(A[cur] + best * (Z - A)[cur], 1e-6, None)
                    P[cur] = Q / Q.sum(1, keepdims=True)
            ev = P * Oc - 1.0                     # EV per 1 unita' su ogni lato
            bet = ev > 0
            prof = np.where(bet, np.where((np.arange(2)[None] == y[:, None]),
                                          Oc - 1.0, -1.0), 0.0)
            nb = int(bet.sum())
            tot = float(prof[bet].sum()) if nb else 0.0
            if nb:
                d = prof[bet]
                mm, lo, hi, _ = boot_e(d - 0.0, rng)
            else:
                mm = lo = hi = 0.0
            roi[etichetta] = {"n_scommesse": nb, "profitto": tot,
                              "roi": (tot / nb) if nb else None,
                              "ci95_roi": [lo, hi]}
            print(f"  [ROI O/U, quote di CHIUSURA reali] {etichetta:<20} "
                  f"n={nb:<5} ROI {(tot/nb if nb else 0):+.2%} "
                  f"CI95 [{lo:+.2%},{hi:+.2%}]")
        blk["roi_over"] = roi
        res[lg] = blk

    # --- F0: POOLED sulle due leghe -------------------------------------- #
    print(f"\n[POOLED 2 leghe]")
    res["pooled"] = {}
    for tag in ("1X2", "over_2.5"):
        d_raw = np.concatenate(pool[tag]["d_raw"])
        d_bet = np.concatenate(pool[tag]["d_beta"])
        m1, lo1, hi1, p1 = boot_e(d_raw, rng)
        m2, lo2, hi2, p2 = boot_e(d_bet, rng)
        res["pooled"][tag] = {
            "n": int(len(d_raw)),
            "apertura_meno_chiusura": {"delta": m1, "ci95": [lo1, hi1], "p2": p1,
                                       "verdetto": verdetto(lo1, hi1)},
            "beta_loso_meno_chiusura": {"delta": m2, "ci95": [lo2, hi2], "p2": p2,
                                        "verdetto": verdetto(lo2, hi2)}}
        print(f"  {tag:<9} n={len(d_raw):<5} apertura grezza - chiusura "
              f"{m1:+.4f} [{lo1:+.4f},{hi1:+.4f}] {verdetto(lo1, hi1)}   |   "
              f"beta LOSO - chiusura {m2:+.4f} [{lo2:+.4f},{hi2:+.4f}] "
              f"{verdetto(lo2, hi2)}")
    return res


# ============================================================ BLOCCO G ===== #
# L'ESPERIMENTO CONTROLLATO sul cambio di provider.
# I blocchi A-F confrontano regimi che sono anche EPOCHE diverse (2017-19 contro
# 2019-26): qualunque differenza e' confusa con la stagione. Ma le colonne
# Pinnacle (PSH/PSD/PSA pre-match, P>2.5/P<2.5 pre-match, PSCH/PSCD/PSCA
# chiusura) esistono in TUTTE e 9 le stagioni del file grezzo football-data.
# Quindi si puo' costruire l'apertura con i DUE provider sulle STESSE partite:
# ogni differenza e' allora provider puro, non stagione.
FD = ROOT / "cantiere" / "data" / "fonti" / "football_data"
COLS_G = {
    "ps_open":  ["PSH", "PSD", "PSA"], "ps_open_ou": ["P>2.5", "P<2.5"],
    "ps_close": ["PSCH", "PSCD", "PSCA"],
    "avg_open": ["AvgH", "AvgD", "AvgA"], "avg_open_ou": ["Avg>2.5", "Avg<2.5"],
    "avg_close": ["AvgCH", "AvgCD", "AvgCA"], "avg_close_ou": ["AvgC>2.5", "AvgC<2.5"],
}


def _grezzo(league: str) -> pd.DataFrame:
    from src.data import loader, sources
    fr = []
    for s in SEASONS9:
        d = pd.read_csv(FD / f"{league}_{s}.csv")
        d = d.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
        out = pd.DataFrame({
            "date": loader._parse_dates(d["Date"]),
            "home_team": d["HomeTeam"].astype(str).str.strip().map(sources.canonical_team),
            "away_team": d["AwayTeam"].astype(str).str.strip().map(sources.canonical_team),
            "season": s})
        for gruppo, cc in COLS_G.items():
            for i, c in enumerate(cc):
                out[f"{gruppo}_{i}"] = (pd.to_numeric(d[c], errors="coerce")
                                        if c in d.columns else np.nan)
        fr.append(out)
    return pd.concat(fr, ignore_index=True)


def blocco_G(dati: dict, rng) -> dict:
    print("\n" + "=" * 96)
    print("BLOCCO G — esperimento CONTROLLATO sul provider (stesse partite, 2 fonti)")
    print("=" * 96)
    res = {}
    for lg, df in dati.items():
        g = _grezzo(lg)
        m = df.merge(g, on=["date", "home_team", "away_team", "season"], how="left")
        assert len(m) == len(df)
        hg = m.home_goals.to_numpy(int); ag = m.away_goals.to_numpy(int)
        y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
        yov = np.where(hg + ag >= 3, 0, 1)
        seas = m.season.to_numpy()

        def dv3(pref):
            O = m[[f"{pref}_{i}" for i in range(3)]].to_numpy(float)
            pi = 1.0 / O
            return pi / pi.sum(1, keepdims=True), (1.0 / O).sum(1)

        def dv2(pref):
            O = m[[f"{pref}_{i}" for i in range(2)]].to_numpy(float)
            pi = 1.0 / O
            return pi / pi.sum(1, keepdims=True), (1.0 / O).sum(1)

        def ll3(P, k):
            return -np.log(np.clip(P[k, y3[k]], 1e-15, None))

        def ll2(P, k):
            return -np.log(np.clip(P[k, yov[k]], 1e-15, None))

        P_ps_o, ov_ps_o = dv3("ps_open")
        P_av_o, ov_av_o = dv3("avg_open")
        P_ps_c, ov_ps_c = dv3("ps_close")
        P_av_c, ov_av_c = dv3("avg_close")
        Q_ps_o, ovq_ps = dv2("ps_open_ou")
        Q_av_o, ovq_av = dv2("avg_open_ou")
        Q_av_c, ovq_avc = dv2("avg_close_ou")
        blk = {}

        # --- G1: apertura Pinnacle vs apertura Avg, STESSE partite -----------
        k = (np.isfinite(P_ps_o).all(1) & np.isfinite(P_av_o).all(1)
             & np.isfinite(P_av_c).all(1))
        a, b, c = ll3(P_ps_o, k), ll3(P_av_o, k), ll3(P_av_c, k)
        m1, lo1, hi1, p1 = boot_e(a - b, rng)       # <0 = Pinnacle meglio
        m2, lo2, hi2, p2 = boot_e(a - c, rng)       # apertura PS vs chiusura Avg
        m3, lo3, hi3, p3 = boot_e(b - c, rng)       # apertura Avg vs chiusura Avg
        blk["G1_1x2"] = {
            "n": int(k.sum()), "stagioni": sorted(set(seas[k])),
            "overround_ps_open": float(ov_ps_o[k].mean()),
            "overround_avg_open": float(ov_av_o[k].mean()),
            "overround_avg_close": float(ov_av_c[k].mean()),
            "ll_ps_open": float(a.mean()), "ll_avg_open": float(b.mean()),
            "ll_avg_close": float(c.mean()),
            "ps_meno_avg_apertura": {"delta": m1, "ci95": [lo1, hi1], "p2": p1,
                                     "verdetto": verdetto(lo1, hi1)},
            "ps_apertura_meno_chiusura": {"delta": m2, "ci95": [lo2, hi2], "p2": p2,
                                          "verdetto": verdetto(lo2, hi2)},
            "avg_apertura_meno_chiusura": {"delta": m3, "ci95": [lo3, hi3], "p2": p3,
                                           "verdetto": verdetto(lo3, hi3)}}
        print(f"\n[{lg}] G1 — 1X2, {int(k.sum())} partite con TUTTI i provider "
              f"({min(seas[k])}..{max(seas[k])})")
        print(f"  overround: Pinnacle apertura {ov_ps_o[k].mean():.4f} | "
              f"Avg apertura {ov_av_o[k].mean():.4f} | Avg chiusura "
              f"{ov_av_c[k].mean():.4f}")
        print(f"  LL: Pinnacle apertura {a.mean():.4f} | Avg apertura {b.mean():.4f} "
              f"| Avg chiusura {c.mean():.4f}")
        print(f"  Pinnacle apert. - Avg apert.:  {m1:+.4f} [{lo1:+.4f},{hi1:+.4f}] "
              f"-> {verdetto(lo1, hi1)}")
        print(f"  Pinnacle apert. - Avg chius.:  {m2:+.4f} [{lo2:+.4f},{hi2:+.4f}] "
              f"-> {verdetto(lo2, hi2)}")
        print(f"  Avg apert.      - Avg chius.:  {m3:+.4f} [{lo3:+.4f},{hi3:+.4f}] "
              f"-> {verdetto(lo3, hi3)}")

        # --- G1b: O/U, apertura Pinnacle vs apertura Avg ---------------------
        k2 = (np.isfinite(Q_ps_o).all(1) & np.isfinite(Q_av_o).all(1)
              & np.isfinite(Q_av_c).all(1))
        a2, b2, c2 = ll2(Q_ps_o, k2), ll2(Q_av_o, k2), ll2(Q_av_c, k2)
        n1, l1, h1, q1 = boot_e(a2 - b2, rng)
        n2, l2, h2, q2 = boot_e(a2 - c2, rng)
        blk["G1_ou"] = {"n": int(k2.sum()),
                        "overround_ps_open": float(ovq_ps[k2].mean()),
                        "overround_avg_open": float(ovq_av[k2].mean()),
                        "overround_avg_close": float(ovq_avc[k2].mean()),
                        "ll_ps_open": float(a2.mean()),
                        "ll_avg_open": float(b2.mean()),
                        "ll_avg_close": float(c2.mean()),
                        "ps_meno_avg_apertura": {"delta": n1, "ci95": [l1, h1],
                                                 "p2": q1, "verdetto": verdetto(l1, h1)},
                        "ps_apertura_meno_chiusura": {"delta": n2, "ci95": [l2, h2],
                                                      "p2": q2,
                                                      "verdetto": verdetto(l2, h2)}}
        print(f"  [O/U 2.5, {int(k2.sum())} partite] overround PS {ovq_ps[k2].mean():.4f} "
              f"Avg {ovq_av[k2].mean():.4f} | LL PS {a2.mean():.4f} "
              f"Avg apert. {b2.mean():.4f} Avg chius. {c2.mean():.4f}")
        print(f"    PS apert. - Avg apert. {n1:+.4f} [{l1:+.4f},{h1:+.4f}] "
              f"{verdetto(l1, h1)} | PS apert. - Avg chius. {n2:+.4f} "
              f"[{l2:+.4f},{h2:+.4f}] {verdetto(l2, h2)}")

        # --- G2: il percorso TUTTO-Pinnacle su 9 stagioni (nessun cambio) ----
        k3 = np.isfinite(P_ps_o).all(1) & np.isfinite(P_ps_c).all(1)
        ao, ac = ll3(P_ps_o, k3), ll3(P_ps_c, k3)
        d1, e1, f1, g1 = boot_e(ao - ac, rng)
        D = (P_ps_c - P_ps_o)[k3]

        def fb(bb, idx):
            P = np.clip(P_ps_o[k3][idx] + bb * D[idx], 1e-6, None)
            P = P / P.sum(1, keepdims=True)
            return -np.log(np.clip(P[np.arange(int(idx.sum())), y3[k3][idx]],
                                   1e-15, None))
        sk = seas[k3]
        allidx = np.ones(int(k3.sum()), bool)
        b_in = float(min(BETAS, key=lambda bb: fb(bb, allidx).mean()))
        sel = np.zeros(int(k3.sum())); pk = {}
        for s in SEASONS9:
            cur = sk == s
            if not cur.any():
                continue
            tr = sk != s
            pk[s] = float(min(BETAS, key=lambda bb: fb(bb, tr).mean()))
            sel[cur] = fb(pk[s], cur)
        ref = fb(1.0, allidx)
        d2, e2, f2, g2 = boot_e(sel - ref, rng)
        blk["G2_pinnacle_9stagioni"] = {
            "n": int(k3.sum()), "stagioni": sorted(set(sk)),
            "overround_open": float(ov_ps_o[k3].mean()),
            "overround_close": float(ov_ps_c[k3].mean()),
            "mad": float(np.abs(D).mean()),
            "ll_apertura": float(ao.mean()), "ll_chiusura": float(ac.mean()),
            "guadagno_chiusura": d1, "ci95": [e1, f1], "p2": g1,
            "verdetto": verdetto(-f1, -e1),
            "beta_in_sample": b_in, "beta_loso": pk,
            "delta_beta_vs_chiusura": d2, "ci95_beta": [e2, f2], "p2_beta": g2,
            "per_stagione": {s: {"n": int((sk == s).sum()),
                                 "mad": float(np.abs(D[sk == s]).mean()),
                                 "guadagno": float((ao - ac)[sk == s].mean())}
                             for s in SEASONS9 if (sk == s).any()},
            "per_regime": {reg: {"n": int(((sk == "1718") | (sk == "1819")).sum()
                                          if reg == "PS/BbAv" else
                                          (~((sk == "1718") | (sk == "1819"))).sum()),
                                 "guadagno": float((ao - ac)[
                                     ((sk == "1718") | (sk == "1819"))
                                     if reg == "PS/BbAv" else
                                     ~((sk == "1718") | (sk == "1819"))].mean())}
                           for reg in ("PS/BbAv", "Avg")}}
        print(f"\n[{lg}] G2 — percorso TUTTO-Pinnacle (PS -> PSC), {int(k3.sum())} "
              f"partite su 9 stagioni: NESSUN cambio di provider")
        print(f"  overround apertura {ov_ps_o[k3].mean():.4f} -> chiusura "
              f"{ov_ps_c[k3].mean():.4f} | |Delta p| {np.abs(D).mean():.4f}")
        print(f"  LL apertura {ao.mean():.4f} -> chiusura {ac.mean():.4f}  "
              f"guadagno {d1:+.4f} CI95 [{e1:+.4f},{f1:+.4f}] -> "
              f"{'la chiusura vince, CONCLUSIVO' if e1 > 0 else 'nel rumore'}")
        print(f"  beta in-sample {b_in:.2f} | LOSO {sorted(set(pk.values()))} | "
              f"Delta vs chiusura {d2:+.4f} [{e2:+.4f},{f2:+.4f}]")
        pr = blk["G2_pinnacle_9stagioni"]["per_regime"]
        print(f"  per epoca: " + " | ".join(
            f"{r} n={v['n']} guadagno {v['guadagno']:+.4f}" for r, v in pr.items()))

        # --- G3: theta dai tassi Pinnacle vs Avg, stesse partite -------------
        kk = np.where(k & k2)[0]
        th = {}
        for etich, P3, P2 in (("pinnacle_open", P_ps_o, Q_ps_o),
                              ("avg_open", P_av_o, Q_av_o),
                              ("avg_close", P_av_c, Q_av_c)):
            lam = np.zeros(len(kk)); mu = np.zeros(len(kk))
            for j, i in enumerate(kk):
                lam[j], mu[j] = mi.implied_lambda_mu(P3[i, 0], P3[i, 1], P3[i, 2],
                                                     P2[i, 0], RHO)
            th[etich] = float(C.fit_theta(lam, mu, hg[kk], ag[kk], RHO))
        blk["G3_theta"] = {"n": int(len(kk)), **th}
        print(f"\n[{lg}] G3 — theta MLE sulle STESSE {len(kk)} partite: "
              + " | ".join(f"{k_} {v:.3f}" for k_, v in th.items()))
        res[lg] = blk
    return res


# ============================================================ BLOCCO H ===== #
# La SCALA di theta. Il progetto spiega il theta piu' basso sui tassi del DC
# (1.138) rispetto a quelli del mercato (1.225) cosi': "i tassi nostri sono piu'
# rumorosi del mercato, e il rumore di stima aggiunge dispersione apparente"
# (src/models/market_implied.py, commento a DP_THETA_DC). Se e' vero, allora
# l'APERTURA — un prezzo intermedio fra il nostro modello e la chiusura — deve
# dare un theta INTERMEDIO. E' una previsione secca, verificabile sulle STESSE
# partite (le 6 stagioni del tracer, dove esistono tutti e tre i tassi).
# ASPETTATIVA DICHIARATA PRIMA: theta_DC < theta_apertura < theta_chiusura,
# in entrambe le leghe.
def blocco_H(dati: dict, rng) -> dict:
    print("\n" + "=" * 96)
    print("BLOCCO H — la scala di theta: DC < apertura < chiusura?")
    print("=" * 96)
    res = {}
    for lg in dati:
        m = pd.read_csv(TRACER[lg], dtype={"season": str, "test_season": str})
        cols = ["odds_home_open", "odds_draw_open", "odds_away_open",
                "odds_over_open", "odds_under_open", "odds_home", "odds_draw",
                "odds_away", "odds_over", "odds_under"]
        m = m[np.isfinite(m[cols].to_numpy(float)).all(1)].reset_index(drop=True)
        hg = m.home_goals.to_numpy(int); ag = m.away_goals.to_numpy(int)
        seas = m.test_season.to_numpy()
        tassi = {"DC": (m.exp_home_goals.to_numpy(), m.exp_away_goals.to_numpy())}
        for tag, suf in (("apertura", "_open"), ("chiusura", "")):
            lam = np.zeros(len(m)); mu = np.zeros(len(m))
            for i, r in enumerate(m.itertuples()):
                pH, pD, pA = metrics.devig_1x2(getattr(r, f"odds_home{suf}"),
                                               getattr(r, f"odds_draw{suf}"),
                                               getattr(r, f"odds_away{suf}"))
                pO, _ = metrics.devig_binary(getattr(r, f"odds_over{suf}"),
                                             getattr(r, f"odds_under{suf}"))
                lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
            tassi[tag] = (lam, mu)
        pooled = {k: float(C.fit_theta(v[0], v[1], hg, ag, RHO))
                  for k, v in tassi.items()}
        perst = {}
        for s in SEASONS6:
            c = seas == s
            if not c.any():
                continue
            perst[s] = {k: float(C.fit_theta(v[0][c], v[1][c], hg[c], ag[c], RHO))
                        for k, v in tassi.items()}
        ok = sum(1 for v in perst.values()
                 if v["DC"] < v["apertura"] < v["chiusura"])
        res[lg] = {"n": int(len(m)), "pooled": pooled, "per_stagione": perst,
                   "stagioni_con_scala_rispettata": ok,
                   "n_stagioni": len(perst)}
        print(f"\n[{lg}] n={len(m)}  pooled:  DC {pooled['DC']:.3f}  <  apertura "
              f"{pooled['apertura']:.3f}  <  chiusura {pooled['chiusura']:.3f}  "
              f"-> {'SCALA RISPETTATA' if pooled['DC'] < pooled['apertura'] < pooled['chiusura'] else 'SCALA VIOLATA'}")
        print(f"  per stagione: " + " | ".join(
            f"{s} {v['DC']:.2f}/{v['apertura']:.2f}/{v['chiusura']:.2f}"
            for s, v in perst.items()))
        print(f"  scala rispettata in {ok}/{len(perst)} stagioni "
              f"(atteso per caso: 1/6 = {1/6:.1%})")
    return res


# --------------------------------------------------------------- main ------ #
def salva(chiave: str, valore) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    prev[chiave] = valore
    OUT.write_text(json.dumps(prev, indent=2, default=str))
    print(f"  [salvato: {chiave} -> {OUT.relative_to(ROOT)}]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--blocchi", nargs="*", default=["A", "B", "C", "D", "E", "F", "G", "H"])
    args = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)

    dati = {}
    for lg in args.leagues:
        df = carica(lg)
        df = inverti(df, lg, "open")
        df = inverti(df, lg, "close")
        df = aggancia_dc(df, lg)
        dati[lg] = df
        print(f"{lg}: {len(df)} partite, apertura {int(df.has_open.sum())}, "
              f"chiusura {int(df.has_close.sum())}, DC {int(df.lam_dc.notna().sum())}")

    if "A" in args.blocchi:
        # controllo di sanita' del router vettoriale (prima di qualunque numero)
        lg0 = args.leagues[0]
        s = dati[lg0][dati[lg0].has_open].head(40)
        w = _sanity_router(s.lam_open.to_numpy(), s.mu_open.to_numpy())
        print("\nCONTROLLO DI SANITA' router vettoriale vs mi.price_markets "
              "(errore massimo):")
        for k, v in w.items():
            print(f"  {k:<34} {v:.2e}")
        if max(w.values()) > 1e-10:
            raise SystemExit("router vettoriale NON coincide con price_markets")
        salva("sanity_router", {k: float(v) for k, v in w.items()})
        # 2o controllo di sanita': il devig di questo script deve riprodurre il
        # log-loss di mercato della FONTE UNICA (experiment_log.compute_metrics),
        # gia' pubblicato nel tracer (cantiere/out/tranche3_tracer.json).
        import json as _json
        tr = _json.loads((ROOT / "cantiere/out/tranche3_tracer.json").read_text())
        san2 = {}
        for lg in args.leagues:
            s = dati[lg]
            s = s[s.season.isin(SEASONS6) & s.has_close]
            hg = s.home_goals.to_numpy(int); ag = s.away_goals.to_numpy(int)
            yy = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
            P = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                          for r in s.itertuples()])
            O = np.array([metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
                          for r in s.itertuples()])
            mio_x = float((-np.log(P[np.arange(len(yy)), yy])).mean())
            mio_o = float(ll_bin(O, (hg + ag >= 3).astype(float)).mean())
            pub_x = float(tr[lg]["pooled"]["x2_market_logloss"])
            pub_o = float(tr[lg]["pooled"]["ou_market_logloss"])
            san2[lg] = {"n": int(len(s)), "mio_1x2": mio_x, "pubblicato_1x2": pub_x,
                        "mio_ou": mio_o, "pubblicato_ou": pub_o,
                        "scarto_1x2": mio_x - pub_x, "scarto_ou": mio_o - pub_o}
            print(f"  compute_metrics {lg}: 1X2 mio {mio_x:.4f} vs pubblicato "
                  f"{pub_x:.4f} | O/U mio {mio_o:.4f} vs {pub_o:.4f}")
            if max(abs(mio_x - pub_x), abs(mio_o - pub_o)) > 5e-5:
                raise SystemExit(f"il devig NON riproduce compute_metrics su {lg}")
        salva("sanity_compute_metrics", san2)
        salva("blocco_A_dati", blocco_A(dati))
    if "B" in args.blocchi:
        salva("blocco_B_listino", blocco_B(dati, rng))
    if "C" in args.blocchi:
        salva("blocco_C_theta_phi", blocco_C(dati, rng))
    if "D" in args.blocchi:
        salva("blocco_D_apertura_vs_chiusura", blocco_D(dati, rng, {}))
    if "E" in args.blocchi:
        salva("blocco_E_movimento", blocco_E(dati, rng))
    if "F" in args.blocchi:
        salva("blocco_F_confutazioni", blocco_F(dati, rng))
    if "G" in args.blocchi:
        salva("blocco_G_provider", blocco_G(dati, rng))
    if "H" in args.blocchi:
        salva("blocco_H_scala_theta", blocco_H(dati, rng))
    salva("_meta", {"seed": SEED, "rho": RHO, "B_bootstrap": 10000,
                    "griglia_theta": GRID_THETA,
                    "griglia_phi_n": len(GRID_PHI),
                    "stagioni9": SEASONS9, "stagioni7": SEASONS7,
                    "secondi": round(time.time() - t0, 1)})
    print(f"\nfatto in {time.time()-t0:.0f}s -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
