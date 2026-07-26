"""Fronte 6 — COSA contiene il movimento della linea apertura -> chiusura.

Contesto. Abbiamo due sole istantanee per partita (le colonne ``*_open``, che
football-data raccoglie ~1-3 giorni prima, e la chiusura), non il tick reale.
La Fase 14 aveva misurato *quanto* vale l'affinamento apertura->chiusura in
log-loss 1X2 (~+0.0020 in Serie A) e che il modello non batte nemmeno
l'apertura, con CLV -0.0028 e 45% di casi positivi. Nessuno pero' aveva mai
chiesto **cosa** contiene quel movimento. Domande di questa fase:

  1. quanto e' grande il movimento, e dove (lega/stagione)?
  2. e' PREVEDIBILE dal nostro DC? (se il mercato si muove verso il nostro
     dissenso rispetto all'apertura, avremmo CLV positivo = edge tradeable);
  3. quanta INFORMAZIONE porta (log-loss apertura vs chiusura) e su quali
     partite si concentra (equilibrate? favorite? seconda meta' di stagione?
     — l'affettatura della Fase 93);
  4. e' momentum o mean-reversion? Senza tick non si osserva la traiettoria,
     ma si puo' chiedere se il movimento ha potere predittivo INCREMENTALE
     oltre la chiusura stessa: p_gamma ∝ p_close * (p_close/p_open)^gamma.
     gamma>0 = la chiusura sotto-reagisce (momentum: conviene estrapolare);
     gamma<0 = sovra-reagisce (mean reversion: conviene disfare un pezzo).
  5. conclusione operativa: raccogliere il tick reale serve a NOI o solo a
     misurare meglio il CLV?

⚠ Trappola metodologica affrontata esplicitamente nel punto 2. La regressione
"ingenua" del movimento sul dissenso, cioe'

     y = logit(close) - logit(open)   su   x = logit(modello) - logit(open)

ha una correlazione MECCANICA positiva: se l'apertura contiene rumore eps, quel
rumore entra con segno meno in ENTRAMBI i membri, quindi beta>0 anche con un
modello inutile. Qui si riportano tre cose: (a) il beta vincolato (quello che
corrisponde davvero al CLV di una strategia apri-e-tieni), (b) la regressione
multipla y ~ a + b1*logit(modello) + b2*logit(apertura), dove b1 e' l'effetto
del NOSTRO segnale a apertura FISSA — la domanda informativa vera, e (c) un
placebo per permutazione (predizioni del modello mescolate) che quantifica
quanta parte del beta vincolato e' puro artefatto meccanico.

Dati: 3 leghe x 9 stagioni per le descrittive del movimento (le colonne *_open
1X2 ci sono da 2017-18; l'O/U di CHIUSURA solo da 2019-20); 3 leghe x 6
stagioni (2020-21 -> 2025-26) dove serve il modello DC walk-forward, come nelle
Fasi 92/93. Le predizioni DC sono cachate in outputs/line_movement_dc_cache.csv.

Uso:
  python scripts/_run_line_movement.py            # usa la cache se c'e'
  python scripts/_run_line_movement.py --refresh  # rifa' i 18 backtest (~7 min)
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import league_config              # noqa: E402
from src.data import loader                       # noqa: E402
from src.evaluation import metrics                # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "outputs" / "line_movement_dc_cache.csv"
OUT_CSV = ROOT / "outputs" / "line_movement.csv"
F93 = ROOT / "experiments" / "fase93_discrimination.csv"

LEAGUES = ("serie_a", "premier_league", "la_liga")
MODEL_SEASONS = ("2021", "2122", "2223", "2324", "2425", "2526")
LAB = {"serie_a": "Serie A", "premier_league": "Premier", "la_liga": "La Liga"}
EPS = 1e-9
RNG = np.random.default_rng(20260726)


# ------------------------------------------------------------------ utils
def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def boot_ci(x: np.ndarray, n: int = 4000, stat=np.mean) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(x), size=(n, len(x)))
    vals = stat(x[idx], axis=1)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """OLS con intercetta gia' inclusa in X. Ritorna (beta, se, R2)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = float(resid @ resid) / (n - k)
    cov = s2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else np.nan
    return beta, se, r2


def boot_slope_ci(y: np.ndarray, X: np.ndarray, j: int = 1,
                  n: int = 2000) -> tuple[float, float]:
    m = len(y)
    out = np.empty(n)
    for b in range(n):
        idx = RNG.integers(0, m, size=m)
        beta, *_ = np.linalg.lstsq(X[idx], y[idx], rcond=None)
        out[b] = beta[j]
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


def ll_1x2_rows(P: np.ndarray, res: np.ndarray) -> np.ndarray:
    """log-loss per PARTITA (vettore), P in ordine (H,D,A)."""
    idx = np.array([{"H": 0, "D": 1, "A": 2}[r] for r in res])
    return -np.log(np.clip(P[np.arange(len(res)), idx], 1e-15, 1.0))


# ------------------------------------------------------- backtest DC (cache)
def _worker(task):
    league, season = task
    cfg = league_config(league)
    from scripts.backtest import run_backtest
    d = run_backtest(league, season, cfg["half_life_days"],
                     shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                     blend_signal=cfg["blend_signal"],
                     promoted_prior=(cfg["promoted_prior"],) * 2, verbose=False)
    d["league"] = league
    return d[["league", "season", "date", "home_team", "away_team",
              "m_home", "m_draw", "m_away", "m_over"]]


def dc_predictions(refresh: bool) -> pd.DataFrame:
    if CACHE.exists() and not refresh:
        d = pd.read_csv(CACHE, parse_dates=["date"])
        print(f"[cache] predizioni DC walk-forward: {len(d)} righe da {CACHE}")
        return d
    tasks = [(lg, s) for lg in LEAGUES for s in MODEL_SEASONS]
    print(f"Eseguo {len(tasks)} backtest walk-forward (3 leghe x 6 stagioni)...",
          flush=True)
    with Pool(6) as pool:
        parts = pool.map(_worker, tasks)
    d = pd.concat(parts, ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    CACHE.parent.mkdir(exist_ok=True)
    d.to_csv(CACHE, index=False)
    print(f"[cache] scritte {len(d)} righe in {CACHE}")
    return d


# --------------------------------------------------------------- dati base
def build_movement() -> pd.DataFrame:
    frames = []
    for lg in LEAGUES:
        d = loader.load_league(lg)
        d = d.copy()
        d["league"] = lg
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)

    o = d[["odds_home_open", "odds_draw_open", "odds_away_open"]].to_numpy(float)
    c = d[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    ok = np.isfinite(o).all(1) & np.isfinite(c).all(1)
    d = d[ok].reset_index(drop=True)
    o, c = o[ok], c[ok]

    d["overround_open"] = (1 / o).sum(1)
    d["overround_close"] = (1 / c).sum(1)
    Po = (1 / o) / (1 / o).sum(1, keepdims=True)      # devig moltiplicativo
    Pc = (1 / c) / (1 / c).sum(1, keepdims=True)
    for k, nm in enumerate(("home", "draw", "away")):
        d[f"open_{nm}"] = Po[:, k]
        d[f"close_{nm}"] = Pc[:, k]
        d[f"dlogit_{nm}"] = logit(Pc[:, k]) - logit(Po[:, k])
        d[f"dp_{nm}"] = Pc[:, k] - Po[:, k]

    # assi interpretabili: discriminazione (casa vs ospite | non pareggio) e
    # massa del pareggio — gli stessi due assi della scomposizione Fase 92.
    d["disc_open"] = np.log(Po[:, 0] / Po[:, 2])
    d["disc_close"] = np.log(Pc[:, 0] / Pc[:, 2])
    d["d_disc"] = d["disc_close"] - d["disc_open"]
    d["draw_open_l"] = logit(Po[:, 1])
    d["draw_close_l"] = logit(Pc[:, 1])
    d["d_draw"] = d["draw_close_l"] - d["draw_open_l"]
    d["abs_dp"] = np.abs(np.c_[d.dp_home, d.dp_draw, d.dp_away]).mean(1)

    # Over/Under 2.5 (chiusura presente solo dal 2019-20)
    oo = d[["odds_over25_open", "odds_under25_open"]].to_numpy(float)
    cc = d[["odds_over25", "odds_under25"]].to_numpy(float)
    ok2 = np.isfinite(oo).all(1) & np.isfinite(cc).all(1)
    po = np.where(ok2, (1 / oo[:, 0]) / (1 / oo).sum(1), np.nan)
    pc = np.where(ok2, (1 / cc[:, 0]) / (1 / cc).sum(1), np.nan)
    d["open_over"], d["close_over"] = po, pc
    d["d_over"] = logit(pc) - logit(po)
    d.loc[~ok2, "d_over"] = np.nan

    d["is_over"] = (d["home_goals"] + d["away_goals"] > 2.5).astype(float)
    # meta' stagione: rango cronologico dentro (lega, stagione)
    d["rank_in_season"] = d.groupby(["league", "season"])["date"].rank(method="first")
    n_per = d.groupby(["league", "season"])["date"].transform("size")
    d["frac_season"] = d["rank_in_season"] / n_per
    d["second_half"] = d["frac_season"] > 0.5
    return d


# ---------------------------------------------------------------- sezione A
def section_a(d: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("A. QUANTO SI MUOVE LA LINEA (devig moltiplicativo; 3 leghe x 9 stagioni)")
    print("=" * 100)
    rows = []
    for lg, g in d.groupby("league"):
        rows.append(dict(
            lega=LAB[lg], n=len(g),
            overr_open=g.overround_open.mean(), overr_close=g.overround_close.mean(),
            dp_medio=g.abs_dp.mean(),
            dp_max_med=np.abs(np.c_[g.dp_home, g.dp_draw, g.dp_away]).max(1).mean(),
            sd_dlgt_H=g.dlogit_home.std(), sd_dlgt_X=g.dlogit_draw.std(),
            sd_dlgt_A=g.dlogit_away.std(),
            sd_d_disc=g.d_disc.std(), sd_d_draw=g.d_draw.std(),
            mean_d_disc=g.d_disc.mean(), mean_d_draw=g.d_draw.mean(),
            quota_mossa_1pt=(g.abs_dp > 0.01).mean(),
            quota_mossa_3pt=(g.abs_dp > 0.03).mean(),
        ))
    t = pd.DataFrame(rows)
    print(t.to_string(index=False, float_format=lambda v: f"{v:8.4f}"))
    print("  dp_medio = |p_close-p_open| medio sui 3 esiti (punti di probabilita');")
    print("  sd_d_disc = sd del movimento sull'asse discriminazione log(pH/pA);")
    print("  mean_* = drift SISTEMATICO (media del Delta-logit): e' ~30-50 volte piu'")
    print("  piccolo della sd, ma mean_d_draw e' positivo in tutte e 3 le leghe (la")
    print("  quota del pareggio si accorcia da apertura a chiusura). Cautela: con il")
    print("  devig moltiplicativo un cambio nella STRUTTURA del margine (favourite-")
    print("  longshot bias) puo' generare da solo un drift di questo ordine.")

    print("\n  Movimento per STAGIONE (sd del Delta-logit discriminazione | dp medio):")
    piv = d.pivot_table(index="season", columns="league",
                        values=["d_disc", "abs_dp"],
                        aggfunc={"d_disc": "std", "abs_dp": "mean"})
    print(piv.to_string(float_format=lambda v: f"{v:7.4f}"))

    ou = d.dropna(subset=["d_over"])
    print(f"\n  Over/Under 2.5 (righe con O/U apertura E chiusura: {len(ou)}):")
    for lg, g in ou.groupby("league"):
        print(f"    {LAB[lg]:<9} sd Delta-logit(over) = {g.d_over.std():.4f}   "
              f"|dp_over| medio = {np.abs(g.close_over - g.open_over).mean():.4f}   "
              f"media = {g.d_over.mean():+.4f}")


# ---------------------------------------------------------------- sezione B
def section_b(dm: pd.DataFrame) -> dict:
    print("\n" + "=" * 100)
    print("B. IL MOVIMENTO E' PREVEDIBILE DAL NOSTRO DC? (6 stagioni con backtest)")
    print("=" * 100)
    dm = dm.copy()
    m_disc = np.log(dm.m_home / dm.m_away)
    dm["x_disc"] = m_disc - dm.disc_open              # dissenso vs APERTURA
    dm["m_disc"] = m_disc
    dm["x_draw"] = logit(dm.m_draw) - dm.draw_open_l
    dm["m_draw_l"] = logit(dm.m_draw)

    print("\n B1. Regressione VINCOLATA (quella che corrisponde al CLV):")
    kpi: dict = {}
    print("     Delta = a + beta * (modello - apertura).  beta>0 = la chiusura si")
    print("     muove VERSO di noi.  ATTENZIONE: beta>0 anche con modello inutile,")
    print("     perche' il rumore dell'apertura entra in entrambi i membri (placebo B3).")
    print(f"\n{'asse':<14}{'lega':<10}{'n':>6}{'beta':>9}{'se':>8}{'IC95 boot':>20}{'R2':>9}"
          f"{'corr':>8}")
    for axis, xcol, ycol in (("discrimin.", "x_disc", "d_disc"),
                             ("pareggio", "x_draw", "d_draw")):
        for lg in list(LEAGUES) + ["POOL"]:
            g = dm if lg == "POOL" else dm[dm.league == lg]
            x, y = g[xcol].to_numpy(), g[ycol].to_numpy()
            X = np.c_[np.ones(len(x)), x]
            beta, se, r2 = ols(y, X)
            lo, hi = boot_slope_ci(y, X, 1, n=1500)
            cr = np.corrcoef(x, y)[0, 1]
            nm = "POOL" if lg == "POOL" else LAB[lg]
            print(f"{axis:<14}{nm:<10}{len(x):>6}{beta[1]:>+9.4f}{se[1]:>8.4f}"
                  f"  [{lo:+.4f},{hi:+.4f}]{r2:>9.4f}{cr:>+8.3f}")
            if lg == "POOL" and axis == "discrimin.":
                kpi.update(beta_pool=float(beta[1]), beta_lo=lo, beta_hi=hi,
                           r2_pool=float(r2))

    print("\n B2. Regressione MULTIPLA (la domanda informativa vera):")
    print("     Delta = a + b1*logit(modello) + b2*logit(apertura).")
    print("     b1 = effetto del NOSTRO segnale ad APERTURA FISSA: se b1>0 e")
    print("     significativo, sappiamo dove andra' la linea oltre al ritorno")
    print("     meccanico del rumore dell'apertura.")
    print(f"\n{'asse':<14}{'lega':<10}{'n':>6}{'b1':>9}{'se':>8}{'IC95 boot':>20}"
          f"{'b2':>9}{'R2':>9}")
    for axis, mcol, ocol, ycol in (("discrimin.", "m_disc", "disc_open", "d_disc"),
                                   ("pareggio", "m_draw_l", "draw_open_l", "d_draw")):
        for lg in list(LEAGUES) + ["POOL"]:
            g = dm if lg == "POOL" else dm[dm.league == lg]
            y = g[ycol].to_numpy()
            X = np.c_[np.ones(len(g)), g[mcol].to_numpy(), g[ocol].to_numpy()]
            beta, se, r2 = ols(y, X)
            lo, hi = boot_slope_ci(y, X, 1, n=1500)
            nm = "POOL" if lg == "POOL" else LAB[lg]
            print(f"{axis:<14}{nm:<10}{len(g):>6}{beta[1]:>+9.4f}{se[1]:>8.4f}"
                  f"  [{lo:+.4f},{hi:+.4f}]{beta[2]:>+9.4f}{r2:>9.4f}")

    print("\n B3. PLACEBO per permutazione (asse discriminazione, POOL):")
    print("     si mescolano le predizioni del modello DENTRO (lega, stagione):")
    print("     il termine meccanico -Cov(apertura, Delta) resta identico, il")
    print("     segnale sparisce. Se il beta vero cade nella banda del placebo,")
    print("     il 'movimento verso di noi' e' artefatto.")
    y = dm.d_disc.to_numpy()
    X = np.c_[np.ones(len(dm)), dm.x_disc.to_numpy()]
    beta_true, _, r2_true = ols(y, X)
    cov_true = np.cov(dm.x_disc, dm.d_disc)[0, 1]
    betas, covs = [], []
    for _ in range(300):
        perm = dm.groupby(["league", "season"])["m_disc"].transform(
            lambda s: s.sample(frac=1.0, random_state=int(RNG.integers(1 << 30))).to_numpy())
        xp = perm.to_numpy() - dm.disc_open.to_numpy()
        Xp = np.c_[np.ones(len(dm)), xp]
        b, _, _ = ols(y, Xp)
        betas.append(b[1])
        covs.append(np.cov(xp, y)[0, 1])
    betas, covs = np.array(betas), np.array(covs)
    print(f"     beta vero      = {beta_true[1]:+.4f}   (R2 {r2_true:.4f})")
    print(f"     beta placebo   = {betas.mean():+.4f}   banda 95% "
          f"[{np.percentile(betas,2.5):+.4f},{np.percentile(betas,97.5):+.4f}]")
    print("     Scomposizione ESATTA della covarianza (identita', non prosa):")
    print("       Cov(x,y) = Cov(logit modello, Delta) - Cov(logit apertura, Delta)")
    cov_open = np.cov(dm.disc_open, dm.d_disc)[0, 1]
    cov_mod = np.cov(dm.m_disc, dm.d_disc)[0, 1]
    print(f"       Cov(x,y)                 = {cov_true:+.5f}")
    print(f"       Cov(modello, Delta)      = {cov_mod:+.5f}   <- il NOSTRO segnale")
    print(f"       -Cov(apertura, Delta)    = {-cov_open:+.5f}   <- termine meccanico")
    print(f"       somma (verifica)         = {cov_mod - cov_open:+.5f}")
    print(f"       placebo (permutazione)   = {covs.mean():+.5f}   banda 95% "
          f"[{np.percentile(covs,2.5):+.5f},{np.percentile(covs,97.5):+.5f}]")
    print("     Nota: qui il termine meccanico e' NEGATIVO (Cov(apertura,Delta)>0:")
    print("     la linea si allarga, non torna indietro), quindi il beta ingenuo e'")
    print("     semmai distorto verso il BASSO: la conclusione 'nessuna")
    print("     prevedibilita'' non e' un artefatto del rumore dell'apertura.")

    print("\n B4. CLV diretto delle value bet all'APERTURA (soglia di edge sulle")
    print("     probabilita' devigate; CLV = p_close - p_open sulla selezione):")
    print(f"{'soglia':<8}{'lega':<10}{'n bet':>8}{'CLV medio':>12}{'IC95':>22}"
          f"{'CLV>0':>8}{'ROI@open':>10}")
    P_m = dm[["m_home", "m_draw", "m_away"]].to_numpy()
    P_o = dm[["open_home", "open_draw", "open_away"]].to_numpy()
    P_c = dm[["close_home", "close_draw", "close_away"]].to_numpy()
    odds_o = dm[["odds_home_open", "odds_draw_open", "odds_away_open"]].to_numpy(float)
    res = dm["result"].to_numpy()
    for thr in (0.02, 0.05):
        for lg in list(LEAGUES) + ["POOL"]:
            sel = np.ones(len(dm), bool) if lg == "POOL" else (dm.league == lg).to_numpy()
            clvs, profs = [], []
            for i in np.where(sel)[0]:
                for k, key in enumerate("HDA"):
                    if P_m[i, k] - P_o[i, k] > thr:
                        clvs.append(P_c[i, k] - P_o[i, k])
                        profs.append(odds_o[i, k] - 1.0 if res[i] == key else -1.0)
            clvs, profs = np.array(clvs), np.array(profs)
            lo, hi = boot_ci(clvs, n=3000)
            nm = "POOL" if lg == "POOL" else LAB[lg]
            print(f"{thr:<8.2f}{nm:<10}{len(clvs):>8}{clvs.mean():>+12.4f}"
                  f"  [{lo:+.4f},{hi:+.4f}]{(clvs>0).mean():>8.1%}"
                  f"{100*profs.mean():>+9.1f}%")
            if lg == "POOL" and thr == 0.05:
                kpi.update(clv_pool=float(clvs.mean()), clv_lo=lo, clv_hi=hi,
                           clv_pos=float((clvs > 0).mean()), clv_n=len(clvs))
    print("  (Fase 14, Serie A, 6 stagioni, soglia 0.05: CLV -0.0028, 45% positivi:")
    print("   la riga Serie A/0.05 qui sopra deve essere dello stesso ordine.)")
    return kpi


# ---------------------------------------------------------------- sezione C
def section_c(d: pd.DataFrame, dm: pd.DataFrame) -> dict:
    print("\n" + "=" * 100)
    print("C. QUANTA INFORMAZIONE PORTA IL MOVIMENTO (log-loss apertura vs chiusura)")
    print("=" * 100)
    Po = d[["open_home", "open_draw", "open_away"]].to_numpy()
    Pc = d[["close_home", "close_draw", "close_away"]].to_numpy()
    res = d["result"].to_numpy()
    d = d.copy()
    d["ll_open"] = ll_1x2_rows(Po, res)
    d["ll_close"] = ll_1x2_rows(Pc, res)
    d["gain"] = d.ll_open - d.ll_close          # >0 = la chiusura e' migliore

    kpi: dict = {}
    print(f"\n{'lega':<10}{'n':>6}{'LL apertura':>13}{'LL chiusura':>13}"
          f"{'guadagno':>11}{'IC95 appaiato':>24}")
    for lg in list(LEAGUES) + ["POOL"]:
        g = d if lg == "POOL" else d[d.league == lg]
        lo, hi = boot_ci(g.gain.to_numpy(), n=4000)
        nm = "POOL" if lg == "POOL" else LAB[lg]
        print(f"{nm:<10}{len(g):>6}{g.ll_open.mean():>13.4f}{g.ll_close.mean():>13.4f}"
              f"{g.gain.mean():>+11.4f}  [{lo:+.4f},{hi:+.4f}]")
        if lg == "POOL":
            kpi.update(gain_pool=float(g.gain.mean()), gain_lo=lo, gain_hi=hi)

    print("\n  Per stagione (guadagno apertura->chiusura, 1X2):")
    piv = d.pivot_table(index="season", columns="league", values="gain", aggfunc="mean")
    piv.columns = [LAB[c] for c in piv.columns]
    print(piv.to_string(float_format=lambda v: f"{v:+7.4f}"))

    ou = d.dropna(subset=["d_over"]).copy()
    po, pc = ou.open_over.to_numpy(), ou.close_over.to_numpy()
    y = ou.is_over.to_numpy()
    ou["ll_o"] = -(y * np.log(np.clip(po, 1e-15, 1)) + (1 - y) * np.log(np.clip(1 - po, 1e-15, 1)))
    ou["ll_c"] = -(y * np.log(np.clip(pc, 1e-15, 1)) + (1 - y) * np.log(np.clip(1 - pc, 1e-15, 1)))
    print("\n  Over/Under 2.5 (dal 2019-20):")
    for lg in list(LEAGUES) + ["POOL"]:
        g = ou if lg == "POOL" else ou[ou.league == lg]
        gain = (g.ll_o - g.ll_c).to_numpy()
        lo, hi = boot_ci(gain, n=3000)
        nm = "POOL" if lg == "POOL" else LAB[lg]
        print(f"    {nm:<10}n={len(g):>5}  LL open {g.ll_o.mean():.4f} -> close "
              f"{g.ll_c.mean():.4f}   guadagno {gain.mean():+.4f} "
              f"[{lo:+.4f},{hi:+.4f}]")

    print("\n  DOVE il movimento e' piu' grande / piu' informativo (POOL 3 leghe):")
    d["bal_bin"] = pd.qcut(d.disc_open.abs(), 4,
                           labels=["Q1 equilibrate", "Q2", "Q3", "Q4 sbilanciate"])
    print(f"\n{'fascia (|log pH/pA| apertura)':<32}{'n':>6}{'sd mov.disc':>13}"
          f"{'|dp| medio':>12}{'guadagno LL':>13}{'IC95':>22}")
    for b, g in d.groupby("bal_bin", observed=True):
        lo, hi = boot_ci(g.gain.to_numpy(), n=3000)
        print(f"{str(b):<32}{len(g):>6}{g.d_disc.std():>13.4f}{g.abs_dp.mean():>12.4f}"
              f"{g.gain.mean():>+13.4f}  [{lo:+.4f},{hi:+.4f}]")

    print(f"\n{'meta di stagione':<32}{'n':>6}{'sd mov.disc':>13}{'|dp| medio':>12}"
          f"{'guadagno LL':>13}{'IC95':>22}")
    for b, g in d.groupby("second_half"):
        lo, hi = boot_ci(g.gain.to_numpy(), n=3000)
        nm = "2a meta'" if b else "1a meta'"
        print(f"{nm:<32}{len(g):>6}{g.d_disc.std():>13.4f}{g.abs_dp.mean():>12.4f}"
              f"{g.gain.mean():>+13.4f}  [{lo:+.4f},{hi:+.4f}]")

    # ---- dimensionamento: quanto vale il movimento CONTRO il nostro gap? ----
    print("\n  C-bis. DIMENSIONE del movimento rispetto al NOSTRO gap (6 stagioni,")
    print("  righe con predizione DC): quanto recupereremmo anticipando TUTTO il")
    print("  movimento? (limite superiore assoluto: nessuno anticipa tutto)")
    Pm = dm[["m_home", "m_draw", "m_away"]].to_numpy()
    Po2 = dm[["open_home", "open_draw", "open_away"]].to_numpy()
    Pc2 = dm[["close_home", "close_draw", "close_away"]].to_numpy()
    rr = dm["result"].to_numpy()
    llm, llo, llc = ll_1x2_rows(Pm, rr), ll_1x2_rows(Po2, rr), ll_1x2_rows(Pc2, rr)
    print(f"\n{'lega':<10}{'n':>6}{'LL DC':>9}{'LL open':>9}{'LL close':>9}"
          f"{'gap vs close':>14}{'gap vs open':>13}{'movimento':>11}{'mov/gap':>9}")
    for lg in list(LEAGUES) + ["POOL"]:
        m = np.ones(len(dm), bool) if lg == "POOL" else (dm.league == lg).to_numpy()
        gc, go = (llm[m] - llc[m]).mean(), (llm[m] - llo[m]).mean()
        mv = (llo[m] - llc[m]).mean()
        nm = "POOL" if lg == "POOL" else LAB[lg]
        print(f"{nm:<10}{m.sum():>6}{llm[m].mean():>9.4f}{llo[m].mean():>9.4f}"
              f"{llc[m].mean():>9.4f}{gc:>+14.4f}{go:>+13.4f}{mv:>+11.4f}"
              f"{mv/gc:>9.1%}")
        if lg == "POOL":
            kpi.update(gap_close=float(gc), gap_open=float(go), mov_gap=float(mv / gc))

    # ---- l'informazione del movimento e' LA STESSA che ci manca? ----
    print("\n  C-ter. L'informazione che arriva fra apertura e chiusura e' la")
    print("  STESSA che manca a noi? Deficit di DISCRIMINAZIONE per partita")
    print("  (Fase 93): c = -log P(esito | non pareggio), deficit = c(.) - c(close).")
    nd = dm[dm.result != "D"].copy()
    won = (nd.result == "H").to_numpy().astype(float)
    for nm, ph in (("model", nd.m_home / (nd.m_home + nd.m_away)),
                   ("open", nd.open_home / (nd.open_home + nd.open_away)),
                   ("close", nd.close_home / (nd.close_home + nd.close_away))):
        ph = np.clip(ph.to_numpy(), 1e-9, 1 - 1e-9)
        nd[f"c_{nm}"] = -np.log(np.where(won == 1, ph, 1 - ph))
    nd["def_model"] = nd.c_model - nd.c_close
    nd["def_open"] = nd.c_open - nd.c_close
    r = np.corrcoef(nd.def_model, nd.def_open)[0, 1]
    X = np.c_[np.ones(len(nd)), nd.def_open.to_numpy()]
    beta, se, r2 = ols(nd.def_model.to_numpy(), X)
    lo, hi = boot_slope_ci(nd.def_model.to_numpy(), X, 1, n=1500)
    print(f"    n non pareggiate = {len(nd)}   deficit medio NOSTRO "
          f"{nd.def_model.mean():+.4f}   deficit dell'APERTURA {nd.def_open.mean():+.4f}")
    print(f"    corr(deficit nostro, deficit dell'apertura) = {r:+.4f}   "
          f"pendenza {beta[1]:+.4f} [{lo:+.4f},{hi:+.4f}]  R2 {r2:.4f}")
    print("    (pendenza ~1 e corr alta = il nostro errore E' l'errore che il")
    print("     movimento corregge; corr bassa = sono errori DIVERSI e il tick")
    print("     non ci darebbe l'informazione che ci manca.)")
    print("    ⚠ ATTENZIONE: i due deficit condividono il termine -c_close, quindi")
    print("    una correlazione positiva nasce anche con un modello INUTILE. Placebo")
    print("    per permutazione (predizioni DC mescolate dentro lega x stagione):")
    ph_true = np.clip((nd.m_home / (nd.m_home + nd.m_away)).to_numpy(), 1e-9, 1 - 1e-9)
    nd["_ph"] = ph_true
    cors, bins_null = [], []
    nd["mov_bin_"] = pd.qcut(nd.d_disc.abs(), 4, labels=[1, 2, 3, 4])
    for _ in range(300):
        perm = nd.groupby(["league", "season"])["_ph"].transform(
            lambda s: s.sample(frac=1.0,
                               random_state=int(RNG.integers(1 << 30))).to_numpy()).to_numpy()
        c_perm = -np.log(np.where(won == 1, perm, 1 - perm))
        d_perm = c_perm - nd.c_close.to_numpy()
        cors.append(np.corrcoef(d_perm, nd.def_open)[0, 1])
        bins_null.append([d_perm[(nd.mov_bin_ == b).to_numpy()].mean() for b in (1, 2, 3, 4)])
    cors = np.array(cors)
    bins_null = np.array(bins_null)
    print(f"      corr vera = {r:+.4f}   corr placebo = {cors.mean():+.4f}  banda 95% "
          f"[{np.percentile(cors,2.5):+.4f},{np.percentile(cors,97.5):+.4f}]")
    print("      deficit medio per quartile di |movimento| — vero vs placebo:")
    veri = []
    for i, b in enumerate((1, 2, 3, 4)):
        vero = nd.def_model[(nd.mov_bin_ == b).to_numpy()].mean()
        veri.append(vero)
        print(f"        Q{b}: vero {vero:+.4f}   placebo {bins_null[:,i].mean():+.4f} "
              f"[{np.percentile(bins_null[:,i],2.5):+.4f},"
              f"{np.percentile(bins_null[:,i],97.5):+.4f}]")
    d41 = bins_null[:, 3] - bins_null[:, 0]
    print(f"      PENDENZA Q4-Q1: vera {veri[3]-veri[0]:+.4f}   placebo "
          f"{d41.mean():+.4f} [{np.percentile(d41,2.5):+.4f},{np.percentile(d41,97.5):+.4f}]")
    print("      (i livelli non sono confrontabili — il modello mescolato e' pessimo —")
    print("       ma la PENDENZA si': se la pendenza vera non supera quella placebo,")
    print("       la 'concentrazione del deficit sulle partite mosse' e' un artefatto")
    print("       del denominatore c_close, non un fatto sul nostro modello.)")

    # link Fase 93: il deficit di discriminazione e' dove la linea si muove?
    if F93.exists():
        f93 = pd.read_csv(F93, parse_dates=["date"])
        key = ["league", "season", "home_team", "away_team"]
        f93["season"] = f93["season"].astype(str)
        mm = dm.merge(f93[key + ["deficit", "abs_disagreement"]], on=key, how="inner")
        print(f"\n  Link Fase 93 (deficit di discriminazione per partita, "
              f"{len(mm)} partite non pareggiate):")
        mm["abs_mov"] = mm.d_disc.abs()
        c1 = np.corrcoef(mm.abs_mov, mm.deficit)[0, 1]
        print(f"    corr(|movimento discriminazione|, deficit F93) = {c1:+.4f}")
        mm["mov_bin"] = pd.qcut(mm.abs_mov, 4, labels=["Q1 ferma", "Q2", "Q3", "Q4 mossa"])
        for b, g in mm.groupby("mov_bin", observed=True):
            lo, hi = boot_ci(g.deficit.to_numpy(), n=3000)
            print(f"    {str(b):<12} n={len(g):>5}  deficit medio {g.deficit.mean():+.4f} "
                  f"[{lo:+.4f},{hi:+.4f}]   |mov| medio {g.abs_mov.mean():.4f}")
    else:
        print("\n  (fase93_discrimination.csv assente: link F93 saltato)")
    kpi.update(corr_def=float(r), corr_def_placebo=float(cors.mean()),
               slope_q41=float(veri[3] - veri[0]), slope_q41_placebo=float(d41.mean()))
    return kpi


# ---------------------------------------------------------------- sezione D
def section_d(d: pd.DataFrame) -> dict:
    print("\n" + "=" * 100)
    print("D. MOMENTUM O MEAN-REVERSION? (il movimento ha valore OLTRE la chiusura?)")
    print("=" * 100)
    print("   p_gamma ∝ p_close * (p_close/p_open)^gamma, poi rinormalizzata.")
    print("   gamma>0 = estrapolare il movimento MIGLIORA (la chiusura sotto-reagisce,")
    print("   momentum);  gamma<0 = conviene disfarne un pezzo (sovra-reazione).")

    Po = d[["open_home", "open_draw", "open_away"]].to_numpy()
    Pc = d[["close_home", "close_draw", "close_away"]].to_numpy()
    res = d["result"].to_numpy()
    L = np.log(np.clip(Pc, 1e-12, 1)) - np.log(np.clip(Po, 1e-12, 1))   # Delta log
    base = np.log(np.clip(Pc, 1e-12, 1))
    idx = np.array([{"H": 0, "D": 1, "A": 2}[r] for r in res])

    def ll_gamma(gam: float, mask: np.ndarray) -> float:
        z = base[mask] + gam * L[mask]
        z = z - z.max(1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(1, keepdims=True)
        return float(-np.log(np.clip(p[np.arange(mask.sum()), idx[mask]], 1e-15, 1)).mean())

    def fit_gamma(mask: np.ndarray) -> float:
        grid = np.linspace(-1.0, 1.0, 201)
        vals = [ll_gamma(g, mask) for g in grid]
        g0 = grid[int(np.argmin(vals))]
        fine = np.linspace(g0 - 0.02, g0 + 0.02, 41)
        return float(fine[int(np.argmin([ll_gamma(g, mask) for g in fine]))])

    print(f"\n{'lega':<10}{'n':>6}{'gamma*':>9}{'LL chiusura':>13}{'LL a gamma*':>13}"
          f"{'guadagno':>11}{'IC95 gamma (boot)':>26}")
    for lg in list(LEAGUES) + ["POOL"]:
        mask = np.ones(len(d), bool) if lg == "POOL" else (d.league == lg).to_numpy()
        g_star = fit_gamma(mask)
        ll0, ll1 = ll_gamma(0.0, mask), ll_gamma(g_star, mask)
        # bootstrap su gamma*: ricalcolo su ricampionamenti
        gs = []
        pos = np.where(mask)[0]
        for _ in range(200):
            sel = pos[RNG.integers(0, len(pos), size=len(pos))]
            zb = base[sel]
            Lb = L[sel]
            ib = idx[sel]

            def llb(gam):
                z = zb + gam * Lb
                z = z - z.max(1, keepdims=True)
                p = np.exp(z)
                p /= p.sum(1, keepdims=True)
                return -np.log(np.clip(p[np.arange(len(sel)), ib], 1e-15, 1)).mean()

            grid = np.linspace(-1.0, 1.0, 81)
            gs.append(grid[int(np.argmin([llb(g) for g in grid]))])
        gs = np.array(gs)
        nm = "POOL" if lg == "POOL" else LAB[lg]
        print(f"{nm:<10}{mask.sum():>6}{g_star:>+9.3f}{ll0:>13.4f}{ll1:>13.4f}"
              f"{ll0-ll1:>+11.4f}  [{np.percentile(gs,2.5):+.3f},{np.percentile(gs,97.5):+.3f}]")

    print("\n  Versione ONESTA walk-forward: gamma stimato sulle stagioni PRECEDENTI")
    print("  della stessa lega e applicato alla successiva (nessun look-ahead).")
    seasons = sorted(d.season.unique())
    tot_c, tot_g, n_tot = 0.0, 0.0, 0
    rows = []
    for lg in LEAGUES:
        for i, s in enumerate(seasons):
            if i == 0:
                continue
            tr = ((d.league == lg) & (d.season.isin(seasons[:i]))).to_numpy()
            te = ((d.league == lg) & (d.season == s)).to_numpy()
            if tr.sum() < 200 or te.sum() == 0:
                continue
            g_star = fit_gamma(tr)
            ll0, ll1 = ll_gamma(0.0, te), ll_gamma(g_star, te)
            rows.append((LAB[lg], s, tr.sum(), te.sum(), g_star, ll0, ll1, ll0 - ll1))
            tot_c += ll0 * te.sum(); tot_g += ll1 * te.sum(); n_tot += te.sum()
    r = pd.DataFrame(rows, columns=["lega", "stagione", "n_train", "n_test",
                                    "gamma_train", "LL_close", "LL_gamma", "guadagno"])
    print(r.to_string(index=False, float_format=lambda v: f"{v:9.4f}"))
    print(f"  TOTALE walk-forward: n={n_tot}  LL chiusura {tot_c/n_tot:.4f} -> "
          f"LL con gamma {tot_g/n_tot:.4f}   guadagno {(tot_c-tot_g)/n_tot:+.4f}")
    print(f"  stagioni con guadagno>0: {(r.guadagno>0).sum()}/{len(r)}")
    kpi = dict(wf_gain=float((tot_c - tot_g) / n_tot),
               wf_pos=int((r.guadagno > 0).sum()), wf_n=int(len(r)))

    # correlazione movimento-residuo (segnale incrementale grezzo)
    print("\n  Segnale incrementale grezzo: corr(movimento, residuo della chiusura)")
    for lg in list(LEAGUES) + ["POOL"]:
        g = d if lg == "POOL" else d[d.league == lg]
        y_h = (g.result == "H").astype(float) - g.close_home
        y_a = (g.result == "A").astype(float) - g.close_away
        c_h = np.corrcoef(g.dp_home, y_h)[0, 1]
        c_a = np.corrcoef(g.dp_away, y_a)[0, 1]
        nm = "POOL" if lg == "POOL" else LAB[lg]
        print(f"    {nm:<10} corr(dp_casa, esito-casa - p_close) = {c_h:+.4f} ;  "
              f"corr(dp_ospite, ...) = {c_a:+.4f}")
    return kpi


# --------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="rifa' i 18 backtest walk-forward invece di usare la cache")
    args = ap.parse_args()

    d = build_movement()
    print(f"Partite con quote 1X2 di APERTURA e CHIUSURA: {len(d)} "
          f"(3 leghe x 9 stagioni)")

    section_a(d)

    dc = dc_predictions(args.refresh)
    dc["season"] = dc["season"].astype(str)
    d["season"] = d["season"].astype(str)
    dm = d.merge(dc, on=["league", "season", "date", "home_team", "away_team"],
                 how="inner")
    print(f"\nPartite con predizione DC walk-forward E entrambe le linee: {len(dm)} "
          f"(3 leghe x 6 stagioni)")

    kb = section_b(dm)
    kc = section_c(d, dm)
    kd = section_d(d)

    print("\n" + "=" * 100)
    print("E. SINTESI OPERATIVA (tutti i numeri sono quelli stampati sopra)")
    print("=" * 100)
    print(f"  1. Il movimento esiste ma e' piccolo: |p_close-p_open| medio "
          f"{d.abs_dp.mean():.4f} punti di probabilita' per esito;")
    print(f"     vale {kc['gain_pool']:+.4f} di log-loss 1X2 "
          f"[{kc['gain_lo']:+.4f},{kc['gain_hi']:+.4f}] (POOL 3 leghe x 9 stagioni).")
    print(f"  2. NON e' prevedibile da noi: beta vincolato {kb['beta_pool']:+.4f} "
          f"[{kb['beta_lo']:+.4f},{kb['beta_hi']:+.4f}], R2 {kb['r2_pool']:.4f}.")
    print(f"     CLV delle value bet all'apertura: {kb['clv_pool']:+.4f} "
          f"[{kb['clv_lo']:+.4f},{kb['clv_hi']:+.4f}], positivi {kb['clv_pos']:.1%} "
          f"su {kb['clv_n']} selezioni -> NEGATIVO.")
    print(f"  3. Dimensione relativa: il movimento e' il {kc['mov_gap']:.1%} del nostro "
          f"gap col mercato ({kc['gap_close']:+.4f}).")
    print(f"     Anticipandolo TUTTO (impossibile) resteremmo a {kc['gap_open']:+.4f}.")
    print(f"  4. Nessun valore incrementale oltre la chiusura: gamma walk-forward "
          f"{kd['wf_gain']:+.4f} ({kd['wf_pos']}/{kd['wf_n']} stagioni positive).")
    print(f"  5. Il nostro errore correla col deficit dell'apertura "
          f"({kc['corr_def']:+.4f} vs placebo {kc['corr_def_placebo']:+.4f}): il")
    print("     movimento corregge un errore che facciamo anche noi, ma la")
    print(f"     concentrazione sulle partite piu' mosse (pendenza Q4-Q1 "
          f"{kc['slope_q41']:+.4f}) NON supera")
    print(f"     l'artefatto meccanico ({kc['slope_q41_placebo']:+.4f}): non e' un fatto "
          f"sul modello.")
    print("  => Raccogliere il TICK reale: utile per MISURARE il CLV in un test")
    print("     prospettico e per prendere il prezzo migliore, NON come feature")
    print("     predittiva (non sappiamo anticipare il movimento, e il movimento")
    print("     non aggiunge nulla oltre la chiusura).")

    OUT_CSV.parent.mkdir(exist_ok=True)
    keep = ["league", "season", "date", "home_team", "away_team", "result",
            "open_home", "open_draw", "open_away", "close_home", "close_draw",
            "close_away", "d_disc", "d_draw", "d_over", "abs_dp",
            "overround_open", "overround_close", "frac_season"]
    d[keep].to_csv(OUT_CSV, index=False)
    print(f"\nDataset del movimento salvato in {OUT_CSV} ({len(d)} righe).")


if __name__ == "__main__":
    main()
