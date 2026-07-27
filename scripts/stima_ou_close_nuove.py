"""STIMA della chiusura O/U 2.5 mancante nel 2017-19 di Bundesliga e Ligue 1
   + RIESAME dello stimatore ora che le leghe sono 5 invece di 3.

SUPERATO dall'integrazione (Fase 100): la stima pubblicata e' quella del fit
pooled a 5 leghe, `data/estimates/ou_close_2017_19.csv` (3.638 righe, prodotta
da `scripts/build_estimates.py`), che copre anche Bundesliga e Ligue 1. Il file
`ou_close_2017_19_nuove_leghe.csv` di questo script e' stato RIMOSSO da
`data/estimates/` in 6c9b377 proprio perche' duplicato e superato. Lo script
resta come verbale del metodo e come termine di paragone, e la sua uscita NON
va piu' in `data/estimates/`: scrive in `docs/audit_5_leghe/numeri/` con il
suffisso `_storico` — stessa scelta gia' fatta per `scripts/stima_ou_corrotte.py`
(audit Fase 101).

CHE COSA MANCA. Nel 2017-18 e 2018-19 football-data pubblica UNA sola linea
O/U (`BbAv`, Betbrain media, pre-match: negli snapshot vive correttamente in
`odds_over25_open`). La CHIUSURA O/U di quelle stagioni non esiste alla fonte:
sono 1.372 partite x 2 celle (over+under) = 2.744 celle, il buco singolo piu'
grosso rimasto. L'1X2 invece ha entrambe le istantanee (Pinnacle PS -> PSC).

LO STIMATORE ESISTENTE (E3 pooled, Fasi 62/62-bis, in `scripts/build_estimates.py`)
regredisce in spazio logit la chiusura O/U su [1, logit(p_over_apertura),
Dlogit(H), Dlogit(D), Dlogit(A)] dove le D sono il movimento 1X2 apertura ->
chiusura. Qui NON si cambia la formula: si cambia solo su CHE COSA la si fitta,
e lo si misura.

LE DOMANDE (richiesta esplicita: rimettere in discussione lo stimatore).
  Q1  il pooled a 5 leghe batte il pooled a 3 leghe, applicato alle 2 nuove?
  Q2  serve un'intercetta per-lega (effetto fisso) sopra il pooled?
  Q3  il per-lega puro adesso vince (prima perdeva)?
  Q4  quanto conta la finestra: solo le stagioni vicine (2019-21) o tutte?
  + baseline oneste obbligatorie: identita' (chiusura = apertura) e media di
    lega-stagione.

PROTOCOLLO DI VALIDAZIONE. Tutti i candidati sono valutati sulle stagioni
2019-20+ (dove la chiusura O/U VERA esiste) con **leave-one-(lega,stagione)-out**:
la coppia valutata non entra mai nel fit. E' il proxy piu' fedele
dell'applicazione reale, in cui abbiamo tutte le altre (lega, stagione) e ci
manca proprio quella che vogliamo stimare. In piu' un protocollo
**leave-one-LEAGUE-out** (fitta su 4 leghe, valuta sulla quinta): misura la
trasferibilita' pura, ed e' la situazione in cui si trovavano Bundesliga e
Ligue 1 prima di esistere nel progetto.

METRICHE (entrambe, come chiesto):
  - MAE in probabilita' vs la chiusura vera devigata  -> FEDELTA' (e' il compito
    della stima: ricostruire un prezzo, non prevedere il risultato);
  - log-loss contro l'esito reale Over/Under          -> UTILITA' a valle;
  - corr/beta del movimento stimato vs quello vero    -> quanto ne cattura.
  Incertezza: bootstrap appaiato B=10.000 (`scripts/_fase52_common.boot`), con
  dichiarazione esplicita se il CI95 e' CONCLUSIVO o no.

ASPETTATIVE DICHIARATE PRIMA DI GUARDARE I NUMERI (§ metodo del progetto):
  A1 E3 batte nettamente identita' e media-di-lega (in Fase 62-bis MAE ~0.012
     contro un movimento medio |close-open| ~0.020).
  A2 Q1: differenza pooled-5 vs pooled-3 PICCOLA e probabilmente nel rumore --
     la mappa "movimento 1X2 -> movimento O/U" e' fisica della matrice dei
     punteggi, quindi universale; 4 leghe di train invece di 3 aggiungono dati
     ma non informazione nuova. Se qualcosa, un filo a favore del pooled-5.
  A3 Q2: intercetta per-lega ~ inutile: il livello della lega e' gia' dentro
     logit(p_over_apertura), che e' una feature per-partita.
  A4 Q3: il per-lega puro NON vince (2.000 righe di train contro 10.000+), ma
     il divario dovrebbe essere piccolo e non conclusivo.
  A5 Q4: la finestra corta (2019-21) PEGGIORA -- meno dati, e il segnale non
     sembra avere una deriva temporale forte.
  A6 l'errore sulle 2 leghe nuove sara' dello stesso ordine delle 3 storiche
     (0.010-0.015): nessun motivo strutturale perche' Bundesliga/Ligue 1 siano
     piu' difficili.
  A7 la stima applicata al 2017-19 dovrebbe MIGLIORARE il log-loss rispetto
     all'apertura reale, di un ordine simile a quanto la chiusura vera migliora
     l'apertura nelle stagioni dove entrambe esistono.

TRAPPOLE DICHIARATE (il progetto ci e' gia' inciampato):
  - nel 2017-19 la linea O/U di input e' `BbAv` (Betbrain media) mentre il fit
    usa le medie `Avg` (2019-20+): semantiche diverse dello stesso concetto
    "media di mercato pre-partita";
  - il movimento 1X2 nel 2017-19 e' Pinnacle (PS -> PSC), dal 2019-20 e'
    Avg -> AvgC: due provider diversi per la stessa feature. Il diagnostico
    "scala del movimento" (sd di Dlogit(H) per stagione) e' stampato apposta;
  - i coefficienti sono fittati su stagioni SUCCESSIVE a quelle stimate: e'
    l'unico dato possibile, ma va detto. Lo stress test all'indietro (fitta sul
    tardi, predici sul presto) misura quanto costa;
  - 9 righe delle leghe nuove hanno l'apertura O/U a NaN (linea corrotta,
    svuotata dall'audit) e 1 riga non ha la chiusura 1X2: NON sono stimabili
    con questo metodo e sono trattate a parte.

USCITE
  docs/audit_5_leghe/numeri/ou_close_2017_19_nuove_leghe_storico.csv
      (probabilita', mai quote; metodo STORICO, superato dal pooled a 5)
  docs/audit_5_leghe/numeri/stima_ou_close_nuove.json                 (tutti i numeri)

Uso:  python scripts/stima_ou_close_nuove.py
      python scripts/stima_ou_close_nuove.py --no-chained   (salta la
          misura dell'errore composto per le 8 righe con apertura stimata)
"""
from __future__ import annotations

import argparse
import json
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

from src.evaluation import metrics  # noqa: E402
from _fase52_common import boot, ll_bin  # noqa: E402

OUT_JSON = ROOT / "docs" / "audit_5_leghe" / "numeri" / "stima_ou_close_nuove.json"
OUT_CSV = (ROOT / "docs" / "audit_5_leghe" / "numeri"
           / "ou_close_2017_19_nuove_leghe_storico.csv")
# L'apertura STIMATA delle righe con la linea O/U corrotta. Il vecchio percorso
# `data/stime_ou_corrotte.csv` e' stato cancellato da 6c9b377: il suo produttore
# (`scripts/stima_ou_corrotte.py`, stesso metodo di inversione del solo 1X2 su
# cui e' misurato `mae_ch` qui sotto) scrive ora sotto docs/. Si punta li', non
# alla stima del bakeoff, per non cambiare in silenzio l'input di una misura
# d'errore che al bakeoff non si riferisce.
CORROTTE = (ROOT / "docs" / "audit_5_leghe" / "numeri"
            / "stima_ou_corrotte_metodo_storico.csv")

HIST = ["serie_a", "premier_league", "la_liga"]
NEW = ["bundesliga", "ligue_1"]
LEAGUES = HIST + NEW
SNAP_DIR = {lg: (ROOT / "data") for lg in HIST}
SNAP_DIR.update({lg: (ROOT / "data") for lg in NEW})

FIT_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TARGET_SEASONS = ["1718", "1819"]
WINDOW_SEASONS = ["1920", "2021"]      # "finestra vicina" al 2017-19 (Q4)
LATE_SEASONS = ["2223", "2324", "2425", "2526"]   # stress test all'indietro

B, SEED = 10_000, 6219
# colonne necessarie per APPLICARE lo stimatore (la chiusura O/U e' cio' che si stima)
NEED_APPLY = ["odds_home", "odds_draw", "odds_away",
              "odds_home_open", "odds_draw_open", "odds_away_open",
              "odds_over25_open", "odds_under25_open"]
NEED_FIT = NEED_APPLY + ["odds_over25", "odds_under25"]


# --------------------------------------------------------------------------- #
# dati e feature (identiche a scripts/build_estimates.py: _devig + _X)
# --------------------------------------------------------------------------- #
def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def _devig(df: pd.DataFrame, with_close_ou: bool) -> pd.DataFrame:
    """Probabilita' devigate (fonte unica: metrics.devig_*) + esito reale."""
    out = df.copy()
    p_c = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in df.itertuples()])
    p_o = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                      r.odds_away_open) for r in df.itertuples()])
    out[["pH_c", "pD_c", "pA_c"]] = p_c
    out[["pH_o", "pD_o", "pA_o"]] = p_o
    out["p_over_line"] = [metrics.devig_binary(r.odds_over25_open,
                                               r.odds_under25_open)[0]
                          for r in df.itertuples()]
    if with_close_ou:
        out["p_over_close"] = [metrics.devig_binary(r.odds_over25,
                                                    r.odds_under25)[0]
                               for r in df.itertuples()]
    out["is_over"] = ((df["home_goals"] + df["away_goals"]) >= 3).astype(int)
    return out.reset_index(drop=True)


def _X(df: pd.DataFrame) -> np.ndarray:
    """Design matrix E3 (Fase 62-bis), copiata riga per riga da build_estimates._X."""
    return np.column_stack([
        np.ones(len(df)),
        _logit(df["p_over_line"]),
        _logit(df["pH_c"]) - _logit(df["pH_o"]),
        _logit(df["pD_c"]) - _logit(df["pD_o"]),
        _logit(df["pA_c"]) - _logit(df["pA_o"]),
    ])


def _snapshot(league: str) -> pd.DataFrame:
    df = pd.read_csv(SNAP_DIR[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df["league"] = league
    return df


def load_fit() -> pd.DataFrame:
    """Righe 2019-20+ con TUTTE e 4 le linee (dove la chiusura O/U vera esiste)."""
    fr = []
    for lg in LEAGUES:
        df = _snapshot(lg)
        df = df[df.season.isin(FIT_SEASONS)].dropna(subset=NEED_FIT)
        fr.append(_devig(df, with_close_ou=True))
    out = pd.concat(fr, ignore_index=True)
    out["ls"] = out["league"] + "|" + out["season"]
    return out


def load_target() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(righe 2017-19 stimabili delle 2 leghe nuove, righe NON stimabili)."""
    ok, bad = [], []
    for lg in NEW:
        df = _snapshot(lg)
        df = df[df.season.isin(TARGET_SEASONS)]
        m = df[NEED_APPLY].notna().all(axis=1)
        ok.append(_devig(df[m], with_close_ou=False))
        b = df[~m].copy()
        b["motivo"] = [", ".join(c for c in NEED_APPLY if pd.isna(getattr(r, c)))
                       for r in b.itertuples()]
        bad.append(b)
    return pd.concat(ok, ignore_index=True), pd.concat(bad, ignore_index=True)


# --------------------------------------------------------------------------- #
# stimatori: ognuno restituisce le predizioni su `te` dato l'insieme di fit
# --------------------------------------------------------------------------- #
def _ols(A: np.ndarray, y: np.ndarray) -> np.ndarray:
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def _fe_design(X: np.ndarray, leagues: pd.Series, order: list[str]) -> np.ndarray:
    """E3 + dummy di lega (la prima lega di `order` resta nell'intercetta)."""
    D = np.column_stack([(leagues.to_numpy() == lg).astype(float)
                         for lg in order[1:]])
    return np.column_stack([X, D])


def predict(variant: str, fit: pd.DataFrame, X: np.ndarray, y: np.ndarray,
            te: np.ndarray, lg: str, season: str) -> np.ndarray:
    """Predizione del candidato `variant` sulle righe `te`, con il train scelto
    in modo che la coppia (lega, stagione) valutata non ci entri MAI."""
    L = fit["league"].to_numpy()
    S = fit["season"].to_numpy()
    not_cell = ~((L == lg) & (S == season))           # leave-one-(lega,stagione)-out
    not_league = L != lg                              # leave-one-league-out

    if variant == "identita":
        return fit["p_over_line"].to_numpy()[te]
    if variant == "media_train":                      # media di lega (train)
        tr = not_cell & (L == lg)
        return np.full(len(te), fit["p_over_close"].to_numpy()[tr].mean())
    if variant == "media_stagione_ORACOLO":           # non usabile: guarda il test
        return np.full(len(te), fit["p_over_close"].to_numpy()[te].mean())

    if variant == "E3_per_lega":
        tr = not_cell & (L == lg)
    elif variant == "E3_pooled5":
        tr = not_cell
    elif variant == "E3_pooled4_LOLO":
        tr = not_league
    elif variant == "E3_pooled3_storiche":
        tr = not_league & np.isin(L, HIST)
    elif variant == "E3_finestra_1921":
        tr = not_cell & np.isin(S, WINDOW_SEASONS)
    elif variant == "E3_pooled5_FE":
        tr = not_cell
        A = _fe_design(X[tr], fit["league"][tr], LEAGUES)
        coef = _ols(A, y[tr])
        return _sigmoid(_fe_design(X[te], fit["league"].iloc[te], LEAGUES) @ coef)
    else:
        raise ValueError(variant)
    return _sigmoid(X[te] @ _ols(X[tr], y[tr]))


VARIANTS = ["identita", "media_train", "media_stagione_ORACOLO",
            "E3_per_lega", "E3_pooled3_storiche", "E3_pooled4_LOLO",
            "E3_pooled5", "E3_pooled5_FE", "E3_finestra_1921"]


def run_bakeoff(fit: pd.DataFrame) -> tuple[dict, dict]:
    """Predizioni out-of-sample di ogni candidato su tutte le (lega, stagione)."""
    X = _X(fit)
    y = _logit(fit["p_over_close"])
    preds = {v: np.full(len(fit), np.nan) for v in VARIANTS}
    for lg in LEAGUES:
        for s in FIT_SEASONS:
            te = np.where((fit["league"] == lg) & (fit["season"] == s))[0]
            if len(te) == 0:
                continue
            for v in VARIANTS:
                preds[v][te] = predict(v, fit, X, y, te, lg, s)
    stats = {}
    p_close = fit["p_over_close"].to_numpy()
    p_open = fit["p_over_line"].to_numpy()
    yy = fit["is_over"].to_numpy()
    for v in VARIANTS:
        stats[v] = {}
        for scope, mask in _scopes(fit):
            ph, pc, po, y0 = preds[v][mask], p_close[mask], p_open[mask], yy[mask]
            mv_p, mv_t = ph - po, pc - po
            corr = (float(np.corrcoef(mv_p, mv_t)[0, 1])
                    if mv_p.std() > 1e-12 else float("nan"))
            beta = (float(np.cov(mv_t, mv_p)[0, 1] / mv_p.var())
                    if mv_p.std() > 1e-12 else float("nan"))
            stats[v][scope] = {"n": int(mask.sum()),
                               "mae": float(np.abs(ph - pc).mean()),
                               "logloss": float(ll_bin(ph, y0).mean()),
                               "corr_mov": corr, "beta_mov": beta}
    return preds, stats


def _scopes(fit: pd.DataFrame):
    L = fit["league"].to_numpy()
    yield "TUTTE", np.ones(len(fit), bool)
    yield "NUOVE", np.isin(L, NEW)
    for lg in LEAGUES:
        yield lg, L == lg


def _ci(delta: tuple[float, float, float, float]) -> str:
    d, lo, hi, _ = delta
    verdict = "CONCLUSIVO" if (lo > 0 or hi < 0) else "nel rumore"
    return f"{d:+.5f} [{lo:+.5f},{hi:+.5f}] {verdict}"


def confronto(preds, fit, a: str, b: str, mask: np.ndarray, rng) -> dict:
    """Bootstrap appaiato su (a - b): MAE e log-loss. Negativo = `a` migliore."""
    pc = fit["p_over_close"].to_numpy()[mask]
    yy = fit["is_over"].to_numpy()[mask]
    pa, pb = preds[a][mask], preds[b][mask]
    d_mae = boot(np.abs(pa - pc) - np.abs(pb - pc), rng, B)
    d_ll = boot(ll_bin(pa, yy) - ll_bin(pb, yy), rng, B)
    return {"n": int(mask.sum()), "mae": list(d_mae), "logloss": list(d_ll),
            "mae_txt": _ci(d_mae), "logloss_txt": _ci(d_ll)}


# --------------------------------------------------------------------------- #
def fit_finale(variant: str, fit: pd.DataFrame, target_league: str):
    """Coefficienti definitivi del candidato scelto, per applicarli al 2017-19.
    Nessuna riga del 2017-19 entra nel fit (non esiste la sua chiusura O/U)."""
    X, y = _X(fit), _logit(fit["p_over_close"])
    L, S = fit["league"].to_numpy(), fit["season"].to_numpy()
    tr = {"E3_pooled5": np.ones(len(fit), bool),
          "E3_pooled4_LOLO": L != target_league,
          "E3_pooled3_storiche": np.isin(L, HIST),
          "E3_per_lega": L == target_league,
          "E3_finestra_1921": np.isin(S, WINDOW_SEASONS)}[variant]
    return _ols(X[tr], y[tr]), int(tr.sum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-chained", action="store_true",
                    help="salta la misura dell'errore composto (apertura stimata)")
    args = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    res: dict = {"generato": time.strftime("%Y-%m-%d %H:%M"), "seed": SEED,
                 "bootstrap_B": B}

    fit = load_fit()
    target, bad = load_target()
    print(f"fit: {len(fit)} partite 2019-20+ con tutte e 4 le linee "
          f"({fit.groupby('league').size().to_dict()})")
    print(f"target 2017-19 leghe nuove: {len(target)} stimabili, "
          f"{len(bad)} NON stimabili")
    res["n_fit"] = int(len(fit))
    res["n_fit_per_lega"] = {k: int(v) for k, v in
                             fit.groupby("league").size().items()}
    res["n_target"] = int(len(target))
    res["non_stimabili"] = [
        {"league": r.league, "season": r.season,
         "date": r.date.strftime("%Y-%m-%d"), "home_team": r.home_team,
         "away_team": r.away_team, "colonne_mancanti": r.motivo}
        for r in bad.itertuples()]

    # ---- 0. diagnostico "cambio provider" ---------------------------------
    print("\n=== 0. DIAGNOSTICO SEMANTICA: scala del movimento 1X2 per stagione ===")
    print("   (2017-19 = Pinnacle PS->PSC; 2019-20+ = Avg->AvgC; se la scala "
          "cambia, i coefficienti trasferiscono male)")
    diag = {}
    for lg in LEAGUES:
        df = _snapshot(lg).dropna(subset=NEED_APPLY)
        d = _devig(df, with_close_ou=False)
        d["dH"] = _logit(d["pH_c"]) - _logit(d["pH_o"])
        g = d.groupby("season")["dH"].agg(["size", "mean", "std"]).round(4)
        diag[lg] = {s: {"n": int(r["size"]), "mean": float(r["mean"]),
                        "sd": float(r["std"])} for s, r in g.iterrows()}
        print(f"  {lg:15s} " + "  ".join(
            f"{s}:sd={r['std']:.3f}" for s, r in g.iterrows()))
    res["diagnostico_movimento_1x2"] = diag

    # ---- 1. bakeoff --------------------------------------------------------
    print(f"\n=== 1. BAKEOFF ({len(VARIANTS)} candidati, "
          f"leave-one-(lega,stagione)-out su {len(FIT_SEASONS)} stagioni x "
          f"{len(LEAGUES)} leghe) ===")
    preds, stats = run_bakeoff(fit)
    hdr = f"{'candidato':24s} {'MAE tutte':>9s} {'MAE nuove':>9s} " + \
          " ".join(f"{lg[:9]:>9s}" for lg in LEAGUES) + f" {'LL nuove':>9s}"
    print(hdr)
    for v in sorted(VARIANTS, key=lambda k: stats[k]["NUOVE"]["mae"]):
        print(f"{v:24s} {stats[v]['TUTTE']['mae']:9.5f} "
              f"{stats[v]['NUOVE']['mae']:9.5f} " +
              " ".join(f"{stats[v][lg]['mae']:9.5f}" for lg in LEAGUES) +
              f" {stats[v]['NUOVE']['logloss']:9.5f}")
    print("\n  movimento catturato (corr / beta), sulle 2 leghe nuove:")
    for v in VARIANTS:
        s = stats[v]["NUOVE"]
        print(f"    {v:24s} corr {s['corr_mov']:6.3f}  beta {s['beta_mov']:6.2f}")
    res["bakeoff"] = stats
    # quanto c'e' da catturare
    mv = fit["p_over_close"].to_numpy() - fit["p_over_line"].to_numpy()
    isnew = np.isin(fit["league"].to_numpy(), NEW)
    res["movimento_reale"] = {
        "tutte": {"mean": float(mv.mean()), "abs_mean": float(np.abs(mv).mean()),
                  "sd": float(mv.std())},
        "nuove": {"mean": float(mv[isnew].mean()),
                  "abs_mean": float(np.abs(mv[isnew]).mean()),
                  "sd": float(mv[isnew].std())}}
    print(f"\n  movimento REALE apertura->chiusura O/U (quanto c'e' da catturare): "
          f"|.| medio {np.abs(mv[isnew]).mean():.5f} sulle nuove, "
          f"{np.abs(mv).mean():.5f} su tutte")

    # ---- 2. i confronti con CI --------------------------------------------
    print("\n=== 2. CONFRONTI (bootstrap appaiato B=10.000; negativo = il primo "
          "e' migliore) ===")
    L = fit["league"].to_numpy()
    m_new = np.isin(L, NEW)
    coppie = [
        ("Q1  pooled5 vs pooled3storiche", "E3_pooled5", "E3_pooled3_storiche", "NUOVE"),
        ("Q1b pooled4LOLO vs pooled3stor", "E3_pooled4_LOLO", "E3_pooled3_storiche", "NUOVE"),
        ("Q2  pooled5+FE vs pooled5", "E3_pooled5_FE", "E3_pooled5", "NUOVE"),
        ("Q3  per_lega vs pooled5", "E3_per_lega", "E3_pooled5", "NUOVE"),
        ("Q4  finestra1921 vs pooled5", "E3_finestra_1921", "E3_pooled5", "NUOVE"),
        ("B1  pooled5 vs identita", "E3_pooled5", "identita", "NUOVE"),
        ("B2  pooled5 vs media_train", "E3_pooled5", "media_train", "NUOVE"),
        ("B3  pooled5 vs media_stag ORACOLO", "E3_pooled5", "media_stagione_ORACOLO", "NUOVE"),
        ("X1  pooled5 vs pooled4LOLO", "E3_pooled5", "E3_pooled4_LOLO", "NUOVE"),
    ]
    res["confronti"] = {}
    for label, a, b, scope in coppie:
        mask = m_new if scope == "NUOVE" else np.ones(len(fit), bool)
        c = confronto(preds, fit, a, b, mask, rng)
        res["confronti"][label] = c
        print(f"  {label:34s} MAE {c['mae_txt']:42s} | LL {c['logloss_txt']}")

    print("\n  gli stessi confronti chiave, lega per lega (MAE):")
    res["confronti_per_lega"] = {}
    for label, a, b in [("Q1 pooled5-pooled3stor", "E3_pooled5", "E3_pooled3_storiche"),
                        ("Q3 per_lega-pooled5", "E3_per_lega", "E3_pooled5"),
                        ("B1 pooled5-identita", "E3_pooled5", "identita")]:
        row = {}
        for lg in LEAGUES:
            c = confronto(preds, fit, a, b, L == lg, rng)
            row[lg] = c
        res["confronti_per_lega"][label] = row
        print(f"    {label:24s} " + "  ".join(
            f"{lg[:4]}:{row[lg]['mae'][0]:+.5f}"
            f"{'*' if (row[lg]['mae'][1] > 0 or row[lg]['mae'][2] < 0) else ' '}"
            for lg in LEAGUES) + "     (* = CI conclusivo)")

    # ---- 3. il REGIME D'USO: estrapolazione ALL'INDIETRO ---------------------
    #
    # Questo blocco e' stato riscritto dopo la verifica avversariale (report 10
    # §15). Prima confrontava i candidati solo in INTERPOLAZIONE (il fit vede
    # stagioni prima e dopo la riga stimata) e su quel confronto sceglieva: cosi'
    # il per-lega vinceva. Ma la chiusura O/U del 2017-19 NON esiste, quindi i
    # coefficienti possono venire SOLO da stagioni successive: il regime d'uso e'
    # l'estrapolazione all'indietro, e li' il verdetto si capovolge.
    # Ora ogni candidato e' valutato in QUEL regime, e la scelta si fa li'.
    print("\n=== 3. REGIME D'USO: fit sulle stagioni TARDE, predizione sulle "
          "PRIME (e' cosi' che la stima viene davvero usata) ===")
    X, yv = _X(fit), _logit(fit["p_over_close"])
    S = fit["season"].to_numpy()
    pc_all = fit["p_over_close"].to_numpy()
    tr_late = np.isin(S, LATE_SEASONS)

    def _tr_indietro(variant: str, lg: str, s_test: str) -> np.ndarray:
        """Righe di training del candidato NEL REGIME D'USO.

        Vincolo che vale per TUTTI i candidati: la stagione su cui si valuta non
        entra mai nel fit. Sembra ovvio, e infatti la prima stesura di questo
        blocco lo violava per il solo candidato "finestra vicina" (che si
        allenava sulle stesse stagioni 1920/2021 su cui veniva valutato) e lo
        faceva vincere. E' lo stesso difetto di protocollo che la verifica
        avversariale aveva trovato altrove: qui viene chiuso alla radice.

        Nota onesta sul candidato "finestra vicina": escludendo la stagione di
        test gli resta una sola stagione di training invece di due, quindi il
        confronto lo PENALIZZA rispetto al suo uso reale. E' il prezzo da pagare
        per non barare; se vincesse comunque, sarebbe un risultato solido.
        """
        base = {"E3_pooled5": np.ones(len(fit), bool),
                "E3_pooled4_LOLO": L != lg,
                "E3_pooled3_storiche": np.isin(L, HIST),
                "E3_per_lega": L == lg,
                "E3_finestra_1921": np.isin(S, WINDOW_SEASONS)}[variant]
        finestra = variant == "E3_finestra_1921"
        return (base & (S != s_test)) if finestra else (base & tr_late)

    # l'effetto fisso per-lega non e' applicabile al 2017-19 (l'intercetta della
    # lega bersaglio non e' stimabile fuori campione): resta fuori dalla scelta,
    # coerentemente con fit_finale, ed era gia' risultato nel rumore (Q2).
    CAND = [v for v in VARIANTS if v.startswith("E3") and v != "E3_pooled5_FE"]
    err_ind = {v: {lg: [] for lg in NEW} for v in CAND}
    stress = {}
    for s_test in WINDOW_SEASONS:
        for lg in NEW:
            te = np.where((L == lg) & (S == s_test))[0]
            if len(te) == 0:
                continue
            riga = {"n": int(len(te))}
            for v in CAND:
                tr = _tr_indietro(v, lg, s_test)
                ph = _sigmoid(X[te] @ _ols(X[tr], yv[tr]))
                e = ph - pc_all[te]
                err_ind[v][lg].append(e)
                riga[v] = float(np.abs(e).mean())
            riga["mae_loso_pooled5"] = float(
                np.abs(preds["E3_pooled5"][te] - pc_all[te]).mean())
            stress[f"{lg}|{s_test}"] = riga
            print(f"  {lg:12s} {s_test} (n={len(te):3d})  " + "  ".join(
                f"{v.replace('E3_', ''):16s}{riga[v]:.5f}" for v in CAND))
    res["regime_uso_indietro"] = stress

    # confronto appaiato fra candidati NEL REGIME D'USO
    err_pool = {v: np.concatenate([np.concatenate(err_ind[v][lg]) for lg in NEW])
                for v in CAND}
    mae_ind = {v: float(np.abs(err_pool[v]).mean()) for v in CAND}
    print("\n  MAE nel REGIME D'USO, 2 leghe nuove insieme:")
    for v in sorted(CAND, key=lambda k: mae_ind[k]):
        print(f"    {v:24s} {mae_ind[v]:.5f}")
    res["mae_regime_uso"] = {v: round(mae_ind[v], 5) for v in CAND}

    # Il confronto e' fra 4 candidati e il pooled: sono 4 test, non uno. Senza
    # correzione, un CI appena conclusivo su 4 tentativi e' quello che il caso
    # produce da solo. E' la lezione procedurale della verifica avversariale
    # ("ogni statistica di testa deve avere il suo intervallo"), applicata qui.
    K_TEST = len(CAND) - 1
    ALPHA_B = 0.05 / K_TEST

    def _boot_pair(a, b):
        n = len(a)
        idx = rng.integers(0, n, size=(B, n))
        d = np.abs(a)[idx].mean(1) - np.abs(b)[idx].mean(1)
        return (float(np.abs(a).mean() - np.abs(b).mean()),
                float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)),
                float(np.percentile(d, 100 * ALPHA_B / 2)),
                float(np.percentile(d, 100 * (1 - ALPHA_B / 2))))

    res["confronti_regime_uso"] = {"_nota": f"{K_TEST} confronti, "
                                   f"Bonferroni alpha={ALPHA_B:.4f}"}
    for v in CAND:
        if v == "E3_pooled5":
            continue
        d, lo, hi, blo, bhi = _boot_pair(err_pool[v], err_pool["E3_pooled5"])
        concl = lo > 0 or hi < 0
        concl_b = blo > 0 or bhi < 0
        res["confronti_regime_uso"][f"{v} vs E3_pooled5"] = {
            "delta_mae": round(d, 6), "ci95": [round(lo, 6), round(hi, 6)],
            "ci_bonferroni": [round(blo, 6), round(bhi, 6)],
            "conclusivo": bool(concl), "conclusivo_bonferroni": bool(concl_b)}
        print(f"    {v:24s} vs pooled5: {d:+.5f} [{lo:+.5f},{hi:+.5f}] "
              f"{'CONCLUSIVO' if concl else 'nel rumore'}"
              f"  | Bonf [{blo:+.5f},{bhi:+.5f}] "
              f"{'CONCLUSIVO' if concl_b else 'no'}")

    # ---- 4. scelta e applicazione -----------------------------------------
    # La scelta si fa nel REGIME D'USO (§3), non in interpolazione: e' la
    # correzione imposta dalla verifica avversariale. Resta la disciplina del
    # multiple testing: se il migliore non batte il pooled con CI conclusivo,
    # si tiene il pooled (piu' semplice, ed e' la formula gia' in produzione).
    ordine = sorted(CAND, key=lambda k: mae_ind[k])
    best = ordine[0]
    if best != "E3_pooled5":
        cc = res["confronti_regime_uso"][f"{best} vs E3_pooled5"]
        # Seconda condizione, oltre al CI corretto: il SEGNO deve reggere su
        # ENTRAMBE le leghe separatamente. E' la regola di replica che il
        # progetto usa gia' per ogni leva ("si replica sull'altra lega?"), e
        # qui serve perche' un CI di Bonferroni che sfiora lo zero non
        # distingue un effetto vero da un caso fortunato.
        per_lega = {lg: (float(np.abs(np.concatenate(err_ind[best][lg])).mean())
                         - float(np.abs(np.concatenate(
                             err_ind["E3_pooled5"][lg])).mean()))
                    for lg in NEW}
        replica = all(v < 0 for v in per_lega.values())
        cc["delta_per_lega"] = {lg: round(v, 6) for lg, v in per_lega.items()}
        cc["replica_su_entrambe"] = bool(replica)
        print(f"\n  migliore nominale nel regime d'uso: {best} "
              f"({cc['delta_mae']:+.5f} {cc['ci95']}, "
              f"Bonferroni {cc['ci_bonferroni']})")
        print("     per lega: " + "  ".join(
            f"{lg} {per_lega[lg]:+.5f}" for lg in NEW)
            + f"   -> segno {'replicato' if replica else 'NON replicato'}")
        if not cc["conclusivo_bonferroni"] or not replica:
            motivo = ("non conclusiva dopo la correzione per i "
                      f"{K_TEST} confronti" if not cc["conclusivo_bonferroni"]
                      else "il segno non si replica su entrambe le leghe")
            print(f"  -> {motivo}: si sceglie il piu' semplice "
                  "(E3_pooled5, stessa formula gia' in produzione).")
            best = "E3_pooled5"
    print(f"\n=== 4. STIMATORE SCELTO (nel regime d'uso): {best} ===")
    res["scelto"] = best
    res["scelto_criterio"] = ("MAE nell'estrapolazione all'indietro (fit su "
                              "stagioni tarde -> stima sul 2017-19), che e' il "
                              "regime in cui la stima viene davvero usata; "
                              "in interpolazione vincerebbe E3_per_lega, ma "
                              "quel confronto non e' il regime d'uso "
                              "(verifica avversariale, report 10 §15)")
    # errore atteso DICHIARATO = quello del regime d'uso, per lega
    mae_uso_lega = {lg: float(np.abs(np.concatenate(err_ind[best][lg])).mean())
                    for lg in NEW}
    res["mae_atteso_regime_uso"] = {lg: round(v, 4) for lg, v in mae_uso_lega.items()}
    print("  errore atteso DICHIARATO (regime d'uso): " + "  ".join(
        f"{lg} {mae_uso_lega[lg]:.4f}" for lg in NEW))

    rows = []
    coefs = {}
    for lg in NEW:
        coef, n_tr = fit_finale(best, fit, lg)
        coefs[lg] = {"coef": [float(c) for c in coef], "n_train": n_tr}
        sub = target[target["league"] == lg]
        p_est = _sigmoid(_X(sub) @ coef)
        # errore DICHIARATO = quello del regime d'uso (estrapolazione
        # all'indietro), non quello in interpolazione: il secondo e' 15-25% piu'
        # ottimistico e descrive una situazione che qui non si verifica mai.
        mae_lg = mae_uso_lega[lg]
        mae_interp = stats[best][lg]["mae"]
        print(f"  {lg:12s} coef {np.array2string(coef, precision=4)} "
              f"(n_train {n_tr}) -> {len(sub)} stime, MAE atteso {mae_lg:.4f} "
              f"(in interpolazione sarebbe {mae_interp:.4f})")
        for r, p in zip(sub.itertuples(), p_est):
            rows.append({
                "league": lg, "season": r.season,
                "date": r.date.strftime("%Y-%m-%d"),
                "home_team": r.home_team, "away_team": r.away_team,
                "p_over25_close_est": round(float(p), 4),
                "metodo": f"E3 ({best}): logit(close) ~ 1 + logit(open O/U) + "
                          f"Dlogit(H,D,A) 1X2, fit su {n_tr} partite 2019-20+",
                "mae_atteso": round(mae_lg, 4),
                "mae_interpolazione": round(mae_interp, 4),
                "note": "coefficienti fittati su stagioni SUCCESSIVE (l'unico "
                        "dato possibile: la chiusura O/U 2017-19 non esiste). "
                        "mae_atteso e' misurato in quello STESSO regime "
                        "(fit sul tardi -> stima sul 2017-19); "
                        "mae_interpolazione e' il valore piu' ottimistico che "
                        "si otterrebbe se il fit vedesse anche stagioni "
                        "precedenti, e NON si applica qui. Input O/U 2017-19 = "
                        "BbAv (Betbrain), movimento 1X2 = Pinnacle.",
            })
    res["coefficienti_finali"] = coefs

    # sensibilita': quanto cambierebbe la stima con un altro candidato?
    print("\n  sensibilita' della stima alla scelta del candidato "
          "(|differenza| media sulle righe target):")
    sens = {}
    for alt in ["E3_pooled3_storiche", "E3_per_lega", "E3_pooled4_LOLO",
                "E3_finestra_1921"]:
        diffs = []
        for lg in NEW:
            c_b, _ = fit_finale(best, fit, lg)
            c_a, _ = fit_finale(alt, fit, lg)
            sub = target[target["league"] == lg]
            Xs = _X(sub)
            diffs.append(np.abs(_sigmoid(Xs @ c_b) - _sigmoid(Xs @ c_a)))
        d = np.concatenate(diffs)
        sens[alt] = {"mean_abs_diff": float(d.mean()), "p95": float(np.percentile(d, 95))}
        print(f"    vs {alt:22s} {d.mean():.5f} (p95 {np.percentile(d,95):.5f})")
    res["sensibilita_scelta"] = sens

    # ---- 5. CONFUTAZIONE: la stima migliora davvero il 2017-19? ------------
    print("\n=== 5. CONFUTAZIONE — la stima vale qualcosa SULLE RIGHE VERE del "
          "2017-19? (log-loss contro l'esito Over/Under reale) ===")
    est = pd.DataFrame(rows)
    conf = {}
    for lg in NEW:
        sub = target[target["league"] == lg].reset_index(drop=True)
        p_hat = est[est.league == lg]["p_over25_close_est"].to_numpy()
        p_open = sub["p_over_line"].to_numpy()
        y0 = sub["is_over"].to_numpy()
        d = boot(ll_bin(p_hat, y0) - ll_bin(p_open, y0), rng, B)
        # riferimento: quanto vale la chiusura VERA sulle stagioni 2019-20+
        m = L == lg
        d_ref = boot(ll_bin(fit["p_over_close"].to_numpy()[m], fit["is_over"].to_numpy()[m])
                     - ll_bin(fit["p_over_line"].to_numpy()[m], fit["is_over"].to_numpy()[m]),
                     rng, B)
        conf[lg] = {"stima_vs_apertura_1719": list(d), "stima_vs_apertura_txt": _ci(d),
                    "chiusura_vera_vs_apertura_1926": list(d_ref),
                    "chiusura_vera_vs_apertura_txt": _ci(d_ref)}
        print(f"  {lg:12s} stima 2017-19 vs apertura reale:  LL {_ci(d)}")
        print(f"  {'':12s} (riferimento 2019-26: chiusura VERA vs apertura "
              f"{_ci(d_ref)})")
    res["confutazione_1719"] = conf

    # ---- 6. le righe NON stimabili -----------------------------------------
    print(f"\n=== 6. RIGHE NON STIMABILI ({len(bad)}) ===")
    for r in bad.itertuples():
        print(f"  {r.league:12s} {r.season} {r.date:%Y-%m-%d} "
              f"{r.home_team}-{r.away_team}: manca {r.motivo}")
    if not args.no_chained and not CORROTTE.exists():
        print(f"\n  [stima concatenata SALTATA: manca {CORROTTE}. "
              f"Rigenerarla con `python scripts/stima_ou_corrotte.py`.]")
    if not args.no_chained and CORROTTE.exists():
        chained, mae_ch = stima_concatenata(fit, best, rng)
        if chained:
            rows.extend(chained)
            res["errore_composto_mae"] = mae_ch
            print(f"  -> {len(chained)} di queste hanno un'APERTURA STIMATA "
                  f"({CORROTTE.name}): stima concatenata prodotta con "
                  f"MAE atteso {mae_ch:.4f} (misurato, vedi sopra)")

    # ---- 7. uscita ---------------------------------------------------------
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows).sort_values(["league", "season", "date",
                                          "home_team"])
    out.to_csv(OUT_CSV, index=False)
    res["n_stime_scritte"] = int(len(out))
    res["mae_atteso_per_lega"] = {lg: round(stats[best][lg]["mae"], 4)
                                  for lg in NEW}
    res["mae_atteso_leghe_storiche"] = {lg: round(stats[best][lg]["mae"], 4)
                                        for lg in HIST}
    OUT_JSON.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"\n-> {OUT_CSV.relative_to(ROOT)}: {len(out)} stime")
    print(f"-> {OUT_JSON.relative_to(ROOT)}")
    print("   ⚠️  PROBABILITA' stimate, mai quote: restano FUORI dagli snapshot.")
    print(f"({time.time()-t0:.0f}s)")
    return 0


def stima_concatenata(fit: pd.DataFrame, best: str, rng, n_sample: int = 900):
    """Le 8 righe con apertura O/U corrotta hanno gia' una STIMA dell'apertura
    (docs/audit_5_leghe/numeri/stima_ou_corrotte_metodo_storico.csv,
    inversione del solo 1X2, prodotta da scripts/stima_ou_corrotte.py).
    Applicarci
    sopra E3 e' una stima-su-stima: l'errore va MISURATO, non assunto.

    Misura: su un campione delle righe 2019-20+ si sostituisce l'apertura vera
    con la stessa stima-da-1X2 (debiasata leave-one-league-out) e si guarda il
    MAE di E3 vs la chiusura vera."""
    from src.models import market_implied as mi
    RHO = -0.06
    idx = rng.choice(len(fit), size=min(n_sample, len(fit)), replace=False)
    sub = fit.iloc[idx].reset_index(drop=True)
    p_from_1x2 = np.empty(len(sub))
    for i, r in enumerate(sub.itertuples()):
        lam, mu = mi.implied_lambda_mu(r.pH_o, r.pD_o, r.pA_o, None, RHO)
        p_from_1x2[i] = mi._1x2_over(mi.score_matrix(lam, mu, RHO))[3]
    err = p_from_1x2 - sub["p_over_line"].to_numpy()
    bias = {lg: float(err[(sub["league"] != lg).to_numpy()].mean())
            for lg in LEAGUES}
    sub = sub.copy()
    sub["p_over_line"] = np.clip(
        p_from_1x2 - sub["league"].map(bias).to_numpy(), 1e-4, 1 - 1e-4)
    maes = []
    for lg in LEAGUES:
        m = (sub["league"] == lg).to_numpy()
        if not m.any():
            continue
        coef, _ = fit_finale(best, fit, lg)
        ph = _sigmoid(_X(sub[m]) @ coef)
        maes.append(np.abs(ph - sub["p_over_close"].to_numpy()[m]))
    mae_ch = float(np.concatenate(maes).mean())

    corr = pd.read_csv(CORROTTE, dtype={"season": str})
    rows = []
    for r in corr.itertuples():
        if r.league not in NEW or r.season not in TARGET_SEASONS:
            continue
        df = _snapshot(r.league)
        m = df[(df.season == r.season) & (df.home_team == r.home_team)
               & (df.away_team == r.away_team)]
        if m.empty or m[["odds_home", "odds_draw", "odds_away", "odds_home_open",
                         "odds_draw_open", "odds_away_open"]].isna().any(axis=1).all():
            continue
        row = m.iloc[[0]].copy()
        row["odds_over25_open"] = 1.0 / r.p_over25_open_est      # solo per _devig
        row["odds_under25_open"] = 1.0 / r.p_under25_open_est
        d = _devig(row, with_close_ou=False)
        coef, _ = fit_finale(best, fit, r.league)
        p = float(_sigmoid(_X(d) @ coef)[0])
        rows.append({
            "league": r.league, "season": r.season, "date": r.date,
            "home_team": r.home_team, "away_team": r.away_team,
            "p_over25_close_est": round(p, 4),
            "metodo": f"E3 ({best}) applicato a un'APERTURA a sua volta STIMATA "
                      f"({CORROTTE.name}): stima su stima",
            "mae_atteso": round(mae_ch, 4),
            "note": "apertura O/U originale corrotta e svuotata: errore composto, "
                    "misurato sostituendo l'apertura vera con la stessa stima "
                    "sulle stagioni 2019-20+",
        })
    return rows, mae_ch


if __name__ == "__main__":
    sys.exit(main())
