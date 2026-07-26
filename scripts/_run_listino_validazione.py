"""FRONTE 7 — Il LISTINO come prodotto: ogni mercato con la sua ETICHETTA di
validazione.

PERCHE'. Il valore dimostrato del progetto non e' battere il mercato (alpha*=0,
Fase 16) ma PREZZARE CALIBRATO una ventina di mercati, inclusi i ~17 che il book
non quota. Finora pero' un lettore esterno non aveva modo di sapere *come* e'
stato validato ciascun mercato: leggere "GG/NG log-loss 0.68" accanto a "1X2
log-loss 0.96" suggerisce che le due righe abbiano lo stesso status, e non e'
vero. Sono cose diverse:

  A   validato contro un mercato ESTERNO E INDIPENDENTE — esiste una quota e
      quella quota NON entra nel modello (handicap asiatico). Qui si puo'
      affermare qualcosa sull'EFFICIENZA: prezziamo bene quanto il book sharp?
  A°  esiste una quota ma e' l'INPUT del motore (1X2, O/U 2.5, doppie chance):
      il confronto col mercato e' CIRCOLARE. Misura solo l'affinamento del
      router (double-Poisson + phi) sopra il devig grezzo, non un edge.
  B   nessuna quota nei dati, ma l'esito si OSSERVA (GG/NG, risultato esatto,
      multigol, total-squadra, clean sheet, vince-a-zero, scarto>=2, pari/dispari,
      corner, cartellini): si puo' affermare la CALIBRAZIONE e il vantaggio sulla
      BASELINE, mai l'efficienza rispetto a un mercato.
  C   non validato / fuori portata (motivo esplicito riga per riga).

COSA FA QUESTO SCRIPT (tutto walk-forward, nessun look-ahead):
 1. carica le 3 leghe (Serie A, Premier, Liga) con la chiusura 1X2+O/U 2.5 e i
    lambda,mu del mercato gia' invertiti (outputs/implied_lammu_cache.csv,
    verificati qui per campione contro mi.implied_lambda_mu);
 2. per ogni lega e ogni stagione di test, RI-FITTA sulle SOLE stagioni passate
    le due costanti del motore — (phi0,kappa) della phi(|lam-mu|) (Fase 35/39) e
    il theta double-Poisson (Fase 51/52) su griglia — e prezza il test con
    mi.price_markets (la funzione VERA del motore, non una copia);
 3. per ogni mercato calcola: probabilita' media, frequenza reale, BIAS, ECE
    (10 bin), log-loss, log-loss della baseline ex-ante (frequenza delle sole
    stagioni passate della stessa lega) e — dove esiste una quota — log-loss/
    Brier del mercato; delta con IC95% bootstrap APPAIATO sulle partite;
 4. aggiunge i mercati FUORI dalla matrice dei gol (corner, cartellini, Fase 96)
    riusando il codice della Fase 96 (import, nessuna copia) e i mercati OUTRIGHT
    (campione, retrocessione) i cui numeri sono IMPORTATI dal registro
    esperimenti e dichiarati come tali (non ricalcolati qui);
 5. stampa la TABELLA-LISTINO e salva i dati in experiments/listino_validazione.json.

LIMITI DICHIARATI (§1.6)
  - la finestra e' 2020-21..2025-26 (6 stagioni x 3 leghe) perche' la prima
    stagione con quote (2019-20) serve come train iniziale e il 2017-19 non ha
    l'O/U di chiusura (buco dati noto);
  - il bootstrap e' a livello di PARTITA (non a blocchi di stagione): sottostima
    la correlazione intra-stagione, quindi gli IC sono ottimistici;
  - la baseline ex-ante e' la frequenza delle stagioni passate della stessa lega:
    piu' onesta della costante in-sample usata in src/evaluation/markets.py, e
    quindi un po' piu' facile da battere;
  - "calibrato" non vuol dire "vincente": alpha*=0 resta il fatto centrale.

NON registra run (diagnostico). Uso: python scripts/_run_listino_validazione.py
"""
from __future__ import annotations

import glob
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

LEAGUES = ["serie_a", "premier_league", "la_liga"]
CACHE = ROOT / "outputs/implied_lammu_cache.csv"
OUT_JSON = ROOT / "experiments/listino_validazione.json"
RHO = -0.06                       # costante del motore (Fase 24+)
THETA_GRID = [1.00, 1.075, 1.15, 1.225, 1.30, 1.375, 1.45]
KMAX = mi.MAX_GOALS               # 10 -> matrice 11x11
NBOOT = 1000
RNG = np.random.default_rng(20260726)

# ---------------------------------------------------------------- livelli --- #
LEVEL_TEXT = {
    "A": "validato contro una quota ESTERNA e INDIPENDENTE (non usata come input)",
    "A°": "la quota esiste ma e' l'INPUT del motore: confronto CIRCOLARE",
    "B": "nessuna quota nei dati, esito osservabile: calibrazione si', efficienza no",
    "C": "non validato / fuori portata",
}
HONESTY = {
    "A": ("possiamo dire se prezziamo bene quanto il book sharp su questo mercato; "
          "NON che ci guadagniamo (alpha*=0)"),
    "A°": ("la quota di questo mercato ENTRA nel modello: il confronto misura solo "
           "l'affinamento del router sul devig grezzo, mai un edge indipendente"),
    "B": ("possiamo affermare che le probabilita' sono calibrate e che battono la "
          "baseline; NON possiamo dire se sono efficienti quanto un mercato, "
          "perche' un mercato non c'e' nei dati"),
}


# ------------------------------------------------------------------ dati ---- #
def _raw_frames() -> list[pd.DataFrame]:
    frames = []
    for f in sorted(glob.glob(str(ROOT / "data/football_data_raw/serie_a_*.csv"))):
        try:
            d = pd.read_csv(f, encoding="latin-1")
        except Exception:
            d = pd.read_csv(f)
        frames.append(d.assign(league="serie_a"))
    for lg, path in [("premier_league", "files/football_data_premier_league_bundle.json"),
                     ("la_liga", "files/football_data_la_liga_bundle.json")]:
        for _, csv_str in json.load(open(ROOT / path)).items():
            if not isinstance(csv_str, str):
                continue
            d = pd.read_csv(io.StringIO(csv_str))
            d.columns = [c.lstrip("﻿") for c in d.columns]
            frames.append(d.assign(league=lg))
    return frames


def load_matches() -> pd.DataFrame:
    """Snapshot delle 3 leghe con chiusura completa + lambda,mu del mercato dalla
    cache + colonne grezze (handicap asiatico) agganciate per chiave naturale."""
    snap = pd.concat([pd.read_csv(ROOT / f"data/{lg}_matches.csv").assign(league=lg)
                      for lg in LEAGUES], ignore_index=True)
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25",
            "home_goals", "away_goals"]
    snap = snap.dropna(subset=need).reset_index(drop=True)
    cache = pd.read_csv(CACHE)
    assert len(cache) == len(snap), f"cache {len(cache)} != snapshot {len(snap)}"
    assert (cache["league"].to_numpy() == snap["league"].to_numpy()).all()
    assert (cache["hg"].to_numpy() == snap["home_goals"].to_numpy()).all()
    snap["lam"] = cache["lam"].to_numpy()
    snap["mu"] = cache["mu"].to_numpy()

    # verifica a campione che la cache sia davvero l'inversione di QUESTE quote
    idx = RNG.choice(len(snap), 25, replace=False)
    worst = 0.0
    for i in idx:
        r = snap.iloc[i]
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, rho=RHO)
        worst = max(worst, abs(lam - r.lam), abs(mu - r.mu))
    print(f"  verifica cache lambda,mu su 25 partite: scarto max {worst:.2e}")
    assert worst < 1e-5, "la cache NON corrisponde alle quote: rigenerarla"

    # aggancio dei dati grezzi (handicap asiatico) per chiave naturale
    raw = pd.concat(_raw_frames(), ignore_index=True)
    raw["date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce")
    for c in ["AHCh", "PCAHH", "PCAHA", "AvgCAHH", "AvgCAHA"]:
        if c not in raw.columns:
            raw[c] = np.nan
    raw["key"] = (raw["league"] + "|" + raw["date"].astype(str) + "|"
                  + raw["AvgCH"].astype(str) + "|" + raw["AvgCD"].astype(str) + "|"
                  + raw["FTHG"].astype(str) + "|" + raw["FTAG"].astype(str))
    raw = raw.drop_duplicates(subset="key", keep=False)
    snap["key"] = (snap["league"] + "|" + pd.to_datetime(snap["date"]).astype(str)
                   + "|" + snap["odds_home"].astype(str) + "|"
                   + snap["odds_draw"].astype(str) + "|"
                   + snap["home_goals"].astype(str) + "|"
                   + snap["away_goals"].astype(str))
    cols = ["key", "AHCh", "PCAHH", "PCAHA", "AvgCAHH", "AvgCAHA"]
    snap = snap.merge(raw[cols], on="key", how="left")
    return snap


# ------------------------------------------------------- utilita' metriche -- #
def _ll_binary(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected Calibration Error: media pesata di |P media - frequenza| su 10 bin
    equispaziati in [0,1]."""
    edges = np.linspace(0.0, 1.0, bins + 1)
    b = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    tot = 0.0
    for k in range(bins):
        m = b == k
        if m.sum() == 0:
            continue
        tot += m.sum() / len(p) * abs(p[m].mean() - y[m].mean())
    return float(tot)


def classwise_ece(P: np.ndarray, Y: np.ndarray, bins: int = 10) -> float:
    """ECE multiclasse 'classwise': tratta ogni colonna (esito) come una previsione
    binaria e mette insieme tutti i punti. Per l'1X2 e il risultato esatto, dove il
    bias medio e' nullo per costruzione (le probabilita' sommano a 1)."""
    return ece(P.ravel(), Y.ravel(), bins)


def boot_ci(diff: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    """IC95% bootstrap APPAIATO della media di `diff` (per-partita), piu' la
    frazione di ricampionamenti con media < 0."""
    means = diff[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi), float((means < 0).mean())


# ---------------------------------------- fit walk-forward delle costanti --- #
def _matrix_batch(lam, mu, ph, pa, phi):
    """Matrici (n,11,11) da marginali gia' calcolati + correzione DC + phi."""
    M = ph[:, :, None] * pa[:, None, :]
    M[:, 0, 0] *= 1.0 - lam * mu * RHO
    M[:, 0, 1] *= 1.0 + lam * RHO
    M[:, 1, 0] *= 1.0 + mu * RHO
    M[:, 1, 1] *= 1.0 - RHO
    M = np.clip(M, 0.0, None)
    if phi is not None:
        d = np.arange(M.shape[1])
        M[:, d, d] *= (1.0 + phi)[:, None]
    return M / M.sum(axis=(1, 2), keepdims=True)


def fit_theta(lam, mu, hg, ag, pmf, phi) -> tuple[float, dict]:
    """theta double-Poisson scelto sulla griglia minimizzando il log-loss del
    RISULTATO ESATTO sulle stagioni passate (stessa metrica della Fase 85)."""
    out = {}
    for th in THETA_GRID:
        M = _matrix_batch(lam, mu, pmf[th][0], pmf[th][1], phi)
        p = M[np.arange(len(hg)), hg, ag]
        out[th] = float(-np.log(np.clip(p, 1e-15, None)).mean())
    best = min(out, key=out.get)
    return best, out


# ------------------------------------------------------------- i mercati --- #
def outcomes(hg: np.ndarray, ag: np.ndarray) -> dict:
    tot = hg + ag
    return {
        "home_win": (hg > ag), "draw": (hg == ag), "away_win": (ag > hg),
        "over_0.5": tot >= 1, "over_1.5": tot >= 2, "over_2.5": tot >= 3,
        "over_3.5": tot >= 4, "over_4.5": tot >= 5,
        "btts": (hg >= 1) & (ag >= 1),
        "home_ov_0.5": hg >= 1, "home_ov_1.5": hg >= 2,
        "away_ov_0.5": ag >= 1, "away_ov_1.5": ag >= 2,
        "odd_total": (tot % 2) == 1,
        "home_by_2plus": (hg - ag) >= 2, "away_by_2plus": (ag - hg) >= 2,
        "mg_0_1": tot <= 1, "mg_2_3": (tot >= 2) & (tot <= 3), "mg_4plus": tot >= 4,
        "dc_1x": hg >= ag, "dc_2x": ag >= hg, "dc_12": hg != ag,
        "cs_home": ag == 0, "cs_away": hg == 0,
        "wtn_home": (hg >= 1) & (ag == 0), "wtn_away": (ag >= 1) & (hg == 0),
    }


LABEL = {
    "home_win": "1 (casa vince)", "draw": "X (pareggio)", "away_win": "2 (ospite vince)",
    "over_0.5": "Over 0.5", "over_1.5": "Over 1.5", "over_2.5": "Over 2.5",
    "over_3.5": "Over 3.5", "over_4.5": "Over 4.5",
    "btts": "GG (entrambe segnano)",
    "home_ov_0.5": "casa segna (Over 0.5 casa)", "home_ov_1.5": "casa Over 1.5",
    "away_ov_0.5": "ospite segna (Over 0.5 osp.)", "away_ov_1.5": "ospite Over 1.5",
    "odd_total": "totale DISPARI",
    "home_by_2plus": "casa vince con >=2 gol", "away_by_2plus": "ospite vince con >=2 gol",
    "mg_0_1": "multigol 0-1", "mg_2_3": "multigol 2-3", "mg_4plus": "multigol 4+",
    "dc_1x": "doppia chance 1X", "dc_2x": "doppia chance 2X", "dc_12": "doppia chance 12",
    "cs_home": "clean sheet casa", "cs_away": "clean sheet ospite",
    "wtn_home": "casa vince a zero", "wtn_away": "ospite vince a zero",
}
# mercati la cui quota ENTRA nel modello (livello A°)
CIRCULAR = {"home_win", "draw", "away_win", "over_2.5", "dc_1x", "dc_2x", "dc_12"}


# ------------------------------------------------------------------ main ---- #
def build_predictions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, list]:
    """Prezza walk-forward ogni stagione di test con le costanti fittate sul solo
    passato. Ritorna (righe di test con tutte le prob dei mercati, prob esatto, log)."""
    lam_all = df["lam"].to_numpy(); mu_all = df["mu"].to_numpy()
    hg_all = np.clip(df["home_goals"].to_numpy().astype(int), 0, KMAX)
    ag_all = np.clip(df["away_goals"].to_numpy().astype(int), 0, KMAX)

    print(f"  precalcolo marginali double-Poisson su {len(THETA_GRID)} theta "
          f"x {len(df)} partite ...", flush=True)
    pmf = {}
    for th in THETA_GRID:
        PH = np.array([mi._dp_pmf(l, th) for l in lam_all])
        PA = np.array([mi._dp_pmf(m, th) for m in mu_all])
        pmf[th] = (PH, PA)

    rows, exact_p, exact_base, folds = [], [], [], []
    for lg in LEAGUES:
        sl = np.where(df["league"].to_numpy() == lg)[0]
        seasons = sorted(df.iloc[sl]["season"].unique())
        for si, s in enumerate(seasons):
            if si == 0:
                continue                                   # prima stagione = solo train
            tr = sl[df.iloc[sl]["season"].to_numpy() < s]
            te = sl[df.iloc[sl]["season"].to_numpy() == s]
            # 1) phi(|lam-mu|) sulle sole stagioni passate
            phi0, kappa = mi.fit_balance_phi(lam_all[tr], mu_all[tr],
                                             (hg_all[tr] == ag_all[tr]).astype(float),
                                             rho=RHO)
            phi_tr = phi0 * np.exp(-kappa * np.abs(lam_all[tr] - mu_all[tr]))
            # 2) theta double-Poisson sulle sole stagioni passate
            th, grid = fit_theta(lam_all[tr], mu_all[tr], hg_all[tr], ag_all[tr],
                                 {t: (pmf[t][0][tr], pmf[t][1][tr]) for t in THETA_GRID},
                                 phi_tr)
            # 3) baseline ex-ante: frequenze delle stagioni passate
            out_tr = outcomes(hg_all[tr], ag_all[tr])
            base_rates = {k: float(v.mean()) for k, v in out_tr.items()}
            cnt = np.zeros((KMAX + 1, KMAX + 1))
            np.add.at(cnt, (hg_all[tr], ag_all[tr]), 1.0)
            base_score = (cnt + 0.5) / (cnt + 0.5).sum()
            folds.append({"league": lg, "test_season": int(s), "n_train": int(len(tr)),
                          "n_test": int(len(te)), "phi0": phi0, "kappa": kappa,
                          "theta": th, "theta_grid_ll": grid})
            # 4) prezzi del motore VERO
            for i in te:
                pr = mi.price_markets(lam_all[i], mu_all[i], rho=RHO,
                                      phi0=phi0, kappa=kappa, dp_theta=th)
                M = pr.pop("score_matrix"); pr.pop("lam"); pr.pop("mu")
                pr.update({"league": lg, "season": int(s), "idx": int(i)})
                rows.append(pr)
                exact_p.append(float(M[hg_all[i], ag_all[i]]))
                exact_base.append(float(base_score[hg_all[i], ag_all[i]]))
            for k, v in base_rates.items():
                for r in rows[-len(te):]:
                    r["base_" + k] = v
        print(f"  {lg}: {len(seasons) - 1} stagioni di test prezzate", flush=True)
    out = pd.DataFrame(rows)
    out["exact_p"] = exact_p
    out["exact_base"] = exact_base
    return out, pmf, folds


def sanity_check(df: pd.DataFrame, folds: list) -> None:
    """Il percorso veloce (_matrix_batch) deve dare la STESSA matrice del motore."""
    f = folds[0]
    i = 0
    lam, mu = df["lam"].to_numpy()[i], df["mu"].to_numpy()[i]
    phi = f["phi0"] * np.exp(-f["kappa"] * abs(lam - mu))
    M_ref = mi.score_matrix(lam, mu, RHO, diag_inflation=phi, dp_theta=f["theta"])
    M_fast = _matrix_batch(np.array([lam]), np.array([mu]),
                           np.array([mi._dp_pmf(lam, f["theta"])]),
                           np.array([mi._dp_pmf(mu, f["theta"])]),
                           np.array([phi]))[0]
    d = float(np.abs(M_ref - M_fast).max())
    print(f"  controllo percorso veloce vs mi.score_matrix: scarto max {d:.2e}")
    assert d < 1e-12


def market_probs(df: pd.DataFrame) -> dict:
    """Probabilita' del MERCATO (devig) per i soli mercati quotati."""
    o = df[["odds_home", "odds_draw", "odds_away"]].to_numpy()
    inv = 1.0 / o
    p = inv / inv.sum(axis=1, keepdims=True)
    io_, iu = 1.0 / df["odds_over25"].to_numpy(), 1.0 / df["odds_under25"].to_numpy()
    pov = io_ / (io_ + iu)
    return {"home_win": p[:, 0], "draw": p[:, 1], "away_win": p[:, 2],
            "over_2.5": pov, "dc_1x": p[:, 0] + p[:, 1], "dc_2x": p[:, 2] + p[:, 1],
            "dc_12": p[:, 0] + p[:, 2]}


def cover_grid(h: float) -> np.ndarray:
    """Frazione di stake vinta dalla casa, cella per cella della matrice (Fase 88)."""
    i = np.arange(KMAX + 1).reshape(-1, 1); j = np.arange(KMAX + 1).reshape(1, -1)
    adj = (i - j) + h
    g = np.zeros_like(adj, dtype=float)
    g[adj >= 0.5] = 1.0
    g[np.isclose(adj, 0.25)] = 0.75
    g[np.isclose(adj, 0.0)] = 0.5
    g[np.isclose(adj, -0.25)] = 0.25
    return g


def asian_handicap_block(df: pd.DataFrame, pred: pd.DataFrame, folds: list) -> dict:
    """Handicap asiatico: l'UNICA quota esterna che NON entra nel motore."""
    fold = {(f["league"], f["test_season"]): f for f in folds}
    recs = []
    for _, r in pred.iterrows():
        s = df.iloc[int(r["idx"])]
        line = s.get("AHCh", np.nan)
        oh = s.get("PCAHH", np.nan); oa = s.get("PCAHA", np.nan)
        if not np.isfinite(oh) or not np.isfinite(oa):
            oh, oa = s.get("AvgCAHH", np.nan), s.get("AvgCAHA", np.nan)
        if not np.isfinite(line) or not np.isfinite(oh) or not np.isfinite(oa):
            continue
        f = fold[(r["league"], int(r["season"]))]
        phi = f["phi0"] * np.exp(-f["kappa"] * abs(s["lam"] - s["mu"]))
        M = mi.score_matrix(s["lam"], s["mu"], RHO, diag_inflation=phi,
                            dp_theta=f["theta"])
        g = cover_grid(float(line))
        mp = float((M * g).sum())
        mk = float((1.0 / oh) / (1.0 / oh + 1.0 / oa))
        margin = int(s["home_goals"] - s["away_goals"])
        adj = margin + float(line)
        real = (1.0 if adj >= 0.5 else 0.75 if np.isclose(adj, 0.25)
                else 0.5 if np.isclose(adj, 0.0) else 0.25 if np.isclose(adj, -0.25)
                else 0.0)
        recs.append((r["league"], float(line), mp, mk, real))
    a = pd.DataFrame(recs, columns=["league", "line", "model_p", "market_p", "real"])
    mp = a["model_p"].to_numpy(); mk = a["market_p"].to_numpy(); y = a["real"].to_numpy()
    idx = RNG.integers(0, len(a), size=(NBOOT, len(a)))
    d = (mp - y) ** 2 - (mk - y) ** 2
    lo, hi, pneg = boot_ci(d, idx)
    half = np.isin(y, [0.0, 1.0])
    res = {
        "n": int(len(a)), "brier_model": float(((mp - y) ** 2).mean()),
        "brier_market": float(((mk - y) ** 2).mean()),
        "delta_brier": float(d.mean()), "ci_delta_brier": [lo, hi],
        "p_model_better": pneg,
        "corr_model_market": float(np.corrcoef(mp, mk)[0, 1]),
        "p_media_modello": float(mp.mean()), "p_media_mercato": float(mk.mean()),
        "copertura_reale": float(y.mean()),
        "n_linee_binarie": int(half.sum()),
        "ll_model_half": float(_ll_binary(mp[half], y[half]).mean()),
        "ll_market_half": float(_ll_binary(mk[half], y[half]).mean()),
        "ece_model_half": ece(mp[half], y[half]),
        "ece_market_half": ece(mk[half], y[half]),
    }
    # il bias di copertura e' condiviso da modello e mercato: e' informativo sapere
    # se e' distinguibile da zero (se lo e', e' una proprieta' della LINEA, non nostra)
    for nm, arr in (("modello", mp - y), ("mercato", mk - y)):
        lo_b, hi_b, _ = boot_ci(arr, idx)
        res[f"ci_bias_{nm}"] = [lo_b, hi_b]
    dh = _ll_binary(mp[half], y[half]) - _ll_binary(mk[half], y[half])
    ih = RNG.integers(0, int(half.sum()), size=(NBOOT, int(half.sum())))
    lo2, hi2, pneg2 = boot_ci(dh, ih)
    res.update({"delta_ll_half": float(dh.mean()), "ci_delta_ll_half": [lo2, hi2],
                "p_model_better_ll_half": pneg2})
    return res


def counts_block() -> list:
    """Corner e cartellini (Fase 96), stessa finestra di test del resto del listino.
    Riusa il codice della Fase 96 via import (nessuna copia)."""
    spec = importlib.util.spec_from_file_location(
        "_om", ROOT / "scripts/_run_outside_matrix.py")
    om = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    cwd = Path.cwd()
    import os
    os.chdir(ROOT)
    try:
        spec.loader.exec_module(om)
        raw = om.load_raw()
        out, levels = [], {}
        for kind, lines, fam in (("corners", [8.5, 9.5, 10.5, 11.5], "corner"),
                                 ("cards", [2.5, 3.5, 4.5], "cartellini")):
            wf = om.walk_forward(raw, kind)
            wf = wf[wf["season"].astype(int) >= 2021]     # stessa finestra del listino
            exp = wf["exp"].to_numpy(); base = wf["base"].to_numpy()
            real = wf["real"].to_numpy()
            # DIAGNOSI DI LIVELLO: un bias dello stesso segno su TUTTE le soglie e'
            # o un errore di normalizzazione o una DERIVA del livello atteso. Qui si
            # distingue: se media(atteso) > media(reale), e' il livello (deriva), non
            # la forma della distribuzione.
            levels[fam] = {"media_attesa_modello": float(exp.mean()),
                           "media_attesa_baseline": float(base.mean()),
                           "media_reale": float(real.mean()),
                           "scarto_livello_modello": float(exp.mean() - real.mean()),
                           "scarto_livello_baseline": float(base.mean() - real.mean()),
                           "n": int(len(real))}
            print(f"  {fam}: media attesa modello {exp.mean():.3f}, baseline "
                  f"{base.mean():.3f}, REALE {real.mean():.3f} -> scarto di LIVELLO "
                  f"{exp.mean()-real.mean():+.3f} (spiega il segno del bias sulle soglie)")
            for L in lines:
                p = np.array([om._pois_over(m, L) for m in exp])
                pb = np.array([om._pois_over(m, L) for m in base])
                y = (real > L).astype(float)
                idx = RNG.integers(0, len(y), size=(NBOOT, len(y)))
                d = _ll_binary(p, y) - _ll_binary(pb, y)
                lo, hi, pneg = boot_ci(d, idx)
                out.append({
                    "key": f"{kind}_ov_{L}", "label": f"Over {L} {fam}",
                    "family": fam, "level": "B", "n": int(len(y)),
                    "p_mean": float(p.mean()), "freq": float(y.mean()),
                    "bias": float(p.mean() - y.mean()), "ece": ece(p, y),
                    "ll_model": float(_ll_binary(p, y).mean()),
                    "ll_base": float(_ll_binary(pb, y).mean()),
                    "delta_base": float(d.mean()), "ci_delta_base": [lo, hi],
                    "p_model_better_base": pneg,
                    "ll_market": None, "delta_market": None, "ci_delta_market": None,
                })
        return out, levels
    finally:
        os.chdir(cwd)


def outright_block() -> list:
    """Mercati OUTRIGHT: numeri IMPORTATI dal registro esperimenti (Fase 89/94),
    non ricalcolati qui. Dichiarato riga per riga."""
    out = []
    p89 = ROOT / "experiments/fase89_season_champion.json"
    if p89.exists():
        rep = json.load(open(p89))["report"]
        out.append({
            "key": "champion", "label": "campione di stagione (outright)",
            "family": "stagione", "level": "B-limitato", "n": int(rep["n"]),
            "p_mean": float(rep["favourite_claimed"]),
            "freq": float(rep["favourite_hit_rate"]),
            "bias": float(rep["favourite_claimed"] - rep["favourite_hit_rate"]),
            "ece": None,
            "ll_model": float(rep["logloss_model"]),
            "ll_base": float(rep["logloss_persistence2_loo"]),
            "delta_base": float(rep["logloss_model"] - rep["logloss_persistence2_loo"]),
            "ci_delta_base": [-rep["gain_ci_persistence2"][1],
                              -rep["gain_ci_persistence2"][0]],
            "p_model_better_base": None,
            "ll_market": None, "delta_market": None, "ci_delta_market": None,
            "source": "experiments/fase89_season_champion.json (importato)",
        })
    p94 = ROOT / "experiments/fase94_drift.json"
    if p94.exists():
        d94 = json.load(open(p94))["0.0"]["markets"]
        out.append({
            "key": "relegation", "label": "retrocessione (outright)",
            "family": "stagione", "level": "B-limitato", "n": 24,
            "p_mean": float(d94["promoted_rel_declared"]),
            "freq": float(d94["promoted_rel_realised"]),
            "bias": float(d94["promoted_rel_declared"] - d94["promoted_rel_realised"]),
            "ece": None, "ll_model": float(d94["rel_logloss"]),
            "ll_base": None, "delta_base": None, "ci_delta_base": None,
            "p_model_better_base": None,
            "ll_market": None, "delta_market": None, "ci_delta_market": None,
            "source": "experiments/fase94_drift.json, deriva 0.0 (importato); "
                      "bias e log-loss sono per-squadra, non per-stagione",
        })
    return out


C_MARKETS = [
    ("handicap asiatico su linee NON quotate", "il motore le prezza dalla matrice, "
     "ma senza una quota esterna per quella linea non c'e' verifica di efficienza; "
     "resta la calibrazione implicita della famiglia-margine (riga A dell'AH)"),
    ("Primo/Secondo tempo, HT/FT, gol nei 15'", "i gol di primo tempo esistono nei "
     "dati grezzi (HTHG/HTAG) ma il motore NON ha una matrice per tempo: Tier 3 "
     "mai costruito"),
    ("corner/cartellini PER SQUADRA o per tempo", "il modello di conteggio della "
     "Fase 96 prezza solo il TOTALE di partita: le marginali per squadra non sono "
     "state validate"),
    ("cartellini con l'arbitro designato", "l'effetto arbitro e' REALE e misurato "
     "(Fase 96, sd 0.513 fra arbitri in Premier) ma NON e' dentro il prezzo: la "
     "designazione arbitrale non e' nei dati storici in modo utilizzabile ex-ante"),
    ("marcatori, primo gol, minuto del gol", "nessun dato a livello giocatore/evento "
     "nel progetto"),
    ("campione/retrocessione contro un MERCATO", "non esistono quote outright "
     "storiche: l'efficienza non e' testabile all'indietro (Fasi 89/95/97); il "
     "confronto con Polymarket/Smarkets misura l'ACCORDO oggi, non chi ha ragione"),
    ("qualunque mercato LIVE / in-play", "nessun dato intra-partita"),
]


def main() -> None:
    print("=" * 100)
    print("FRONTE 7 — LISTINO DEI MERCATI CON ETICHETTA DI VALIDAZIONE")
    print("=" * 100)
    print("\n[1] Dati")
    df = load_matches()
    print(f"  partite con chiusura 1X2 + O/U 2.5: {len(df)} "
          f"({df['league'].nunique()} leghe, {df['season'].nunique()} stagioni)")
    print(f"  handicap asiatico agganciato: {df['AHCh'].notna().mean()*100:.1f}% delle righe")

    print("\n[2] Prezzi walk-forward (costanti ri-fittate sul solo passato)")
    pred, _pmf, folds = build_predictions(df)
    sanity_check(df, folds)
    te_idx = pred["idx"].to_numpy()
    sub = df.iloc[te_idx].reset_index(drop=True)
    hg = np.clip(sub["home_goals"].to_numpy().astype(int), 0, KMAX)
    ag = np.clip(sub["away_goals"].to_numpy().astype(int), 0, KMAX)
    seasons_te = sorted(pred["season"].unique())
    print(f"  test: {len(pred)} partite, stagioni {seasons_te[0]}..{seasons_te[-1]}")
    print(f"\n  {'lega':<16}{'stag.':>7}{'n train':>9}{'n test':>8}{'phi0':>8}"
          f"{'kappa':>8}{'theta':>8}")
    for f in folds:
        print(f"  {f['league']:<16}{f['test_season']:>7}{f['n_train']:>9}"
              f"{f['n_test']:>8}{f['phi0']:>8.3f}{f['kappa']:>8.3f}{f['theta']:>8.3f}")

    y = outcomes(hg, ag)
    mkt = market_probs(sub)
    idx = RNG.integers(0, len(pred), size=(NBOOT, len(pred)))

    listino = []
    for k, lab in LABEL.items():
        p = pred[k].to_numpy(); yy = y[k].astype(float)
        pb = pred["base_" + k].to_numpy()
        llm, llb = _ll_binary(p, yy), _ll_binary(pb, yy)
        lo, hi, pneg = boot_ci(llm - llb, idx)
        row = {
            "key": k, "label": lab, "family": "matrice dei gol",
            "level": "A°" if k in CIRCULAR else "B", "n": int(len(p)),
            "p_mean": float(p.mean()), "freq": float(yy.mean()),
            "bias": float(p.mean() - yy.mean()), "ece": ece(p, yy),
            "ll_model": float(llm.mean()), "ll_base": float(llb.mean()),
            "delta_base": float((llm - llb).mean()), "ci_delta_base": [lo, hi],
            "p_model_better_base": pneg,
            "ll_market": None, "delta_market": None, "ci_delta_market": None,
            "ece_market": None, "bias_market": None,
        }
        if k in mkt:
            llk = _ll_binary(mkt[k], yy)
            lo2, hi2, pneg2 = boot_ci(llm - llk, idx)
            row.update({"ll_market": float(llk.mean()),
                        "delta_market": float((llm - llk).mean()),
                        "ci_delta_market": [lo2, hi2],
                        "p_model_better_market": pneg2,
                        "ece_market": ece(mkt[k], yy),
                        "bias_market": float(mkt[k].mean() - yy.mean())})
        listino.append(row)

    # --- 1X2 multiclasse e risultato esatto (righe multiclasse) --- #
    P1 = pred[["home_win", "draw", "away_win"]].to_numpy()
    B1 = pred[["base_home_win", "base_draw", "base_away_win"]].to_numpy()
    M1 = np.column_stack([mkt["home_win"], mkt["draw"], mkt["away_win"]])
    Y1 = np.column_stack([y["home_win"], y["draw"], y["away_win"]]).astype(float)
    pick = lambda P: -np.log(np.clip((P * Y1).sum(axis=1), 1e-15, None))  # noqa: E731
    lo, hi, pneg = boot_ci(pick(P1) - pick(B1), idx)
    lo2, hi2, pneg2 = boot_ci(pick(P1) - pick(M1), idx)
    listino.append({
        "key": "1x2_multi", "label": "1X2 (multiclasse, 3 esiti)",
        "family": "matrice dei gol", "level": "A°", "n": int(len(P1)),
        "p_mean": None, "freq": None, "bias": 0.0,
        "ece": classwise_ece(P1, Y1),
        "ll_model": float(pick(P1).mean()), "ll_base": float(pick(B1).mean()),
        "delta_base": float((pick(P1) - pick(B1)).mean()), "ci_delta_base": [lo, hi],
        "p_model_better_base": pneg,
        "ll_market": float(pick(M1).mean()),
        "delta_market": float((pick(P1) - pick(M1)).mean()),
        "ci_delta_market": [lo2, hi2], "p_model_better_market": pneg2,
        "ece_market": classwise_ece(M1, Y1), "bias_market": 0.0,
    })
    ep = pred["exact_p"].to_numpy(); eb = pred["exact_base"].to_numpy()
    lle, lleb = -np.log(np.clip(ep, 1e-15, None)), -np.log(np.clip(eb, 1e-15, None))
    lo, hi, pneg = boot_ci(lle - lleb, idx)
    listino.append({
        "key": "exact_score", "label": "risultato esatto (121 esiti)",
        "family": "matrice dei gol", "level": "B", "n": int(len(ep)),
        "p_mean": None, "freq": None, "bias": 0.0, "ece": None,
        "ll_model": float(lle.mean()), "ll_base": float(lleb.mean()),
        "delta_base": float((lle - lleb).mean()), "ci_delta_base": [lo, hi],
        "p_model_better_base": pneg,
        "ll_market": None, "delta_market": None, "ci_delta_market": None,
        "ece_market": None, "bias_market": None,
    })

    print("\n[3] Handicap asiatico (l'unica quota esterna NON usata come input)")
    ah = asian_handicap_block(df, pred, folds)
    listino.append({
        "key": "asian_handicap", "label": "handicap asiatico (linea di chiusura)",
        "family": "matrice dei gol", "level": "A", "n": ah["n"],
        "p_mean": ah["p_media_modello"], "freq": ah["copertura_reale"],
        "bias": ah["p_media_modello"] - ah["copertura_reale"],
        "ece": ah["ece_model_half"],
        "ll_model": ah["ll_model_half"], "ll_base": None,
        "delta_base": None, "ci_delta_base": None, "p_model_better_base": None,
        "ll_market": ah["ll_market_half"],
        "delta_market": ah["ll_model_half"] - ah["ll_market_half"],
        "ci_delta_market": None, "ece_market": ah["ece_market_half"],
        "bias_market": ah["p_media_mercato"] - ah["copertura_reale"],
        "brier_model": ah["brier_model"], "brier_market": ah["brier_market"],
        "delta_brier_vs_market": ah["delta_brier"],
        "ci_delta_brier_vs_market": ah["ci_delta_brier"],
        "corr_model_market": ah["corr_model_market"],
    })
    print(f"  n={ah['n']} (linee binarie {ah['n_linee_binarie']}) | "
          f"corr modello-mercato {ah['corr_model_market']:.4f}")
    print(f"  Brier modello {ah['brier_model']:.4f} vs mercato {ah['brier_market']:.4f} "
          f"| delta {ah['delta_brier']:+.4f} IC95 "
          f"[{ah['ci_delta_brier'][0]:+.4f}, {ah['ci_delta_brier'][1]:+.4f}]")
    print(f"  copertura: modello {ah['p_media_modello']:.4f}, mercato "
          f"{ah['p_media_mercato']:.4f}, reale {ah['copertura_reale']:.4f}")
    print(f"  bias di copertura: modello {ah['p_media_modello']-ah['copertura_reale']:+.4f} "
          f"IC[{ah['ci_bias_modello'][0]:+.4f},{ah['ci_bias_modello'][1]:+.4f}] | "
          f"mercato {ah['p_media_mercato']-ah['copertura_reale']:+.4f} "
          f"IC[{ah['ci_bias_mercato'][0]:+.4f},{ah['ci_bias_mercato'][1]:+.4f}]")
    print("  (il bias e' CONDIVISO col book: se e' distinguibile da zero e' una "
          "proprieta' della linea di chiusura, non un nostro errore)")

    print("\n[4] Mercati fuori dalla matrice dei gol (corner, cartellini — Fase 96)")
    counts_rows, counts_levels = counts_block()
    listino += counts_rows
    print("\n[5] Mercati outright (numeri importati dal registro)")
    listino += outright_block()

    # --- calibrazione PER LEGA sui mercati della matrice (nessuna quota serve) --- #
    per_lega = {}
    lg_arr = pred["league"].to_numpy()
    for lg in LEAGUES:
        m = lg_arr == lg
        d = {}
        for k in LABEL:
            p = pred[k].to_numpy()[m]; yy = y[k].astype(float)[m]
            d[k] = {"bias": float(p.mean() - yy.mean()), "ece": ece(p, yy),
                    "ll_model": float(_ll_binary(p, yy).mean())}
        per_lega[lg] = {"n": int(m.sum()), "mercati": d,
                        "bias_assoluto_medio": float(np.mean([abs(v["bias"])
                                                              for v in d.values()])),
                        "ece_medio": float(np.mean([v["ece"] for v in d.values()]))}

    # ------------------------------------------------------------ tabelle -- #
    order = {"A": 0, "A°": 1, "B": 2, "B-limitato": 3, "C": 4}
    listino.sort(key=lambda r: (order[r["level"]], r["ll_model"] if r["ll_model"] else 0))

    def fmt(v, w=8, d=4, sign=False):
        if v is None:
            return " " * (w - 1) + "—"
        return f"{v:>{w}.{d}f}" if not sign else f"{v:>+{w}.{d}f}"

    print("\n" + "=" * 118)
    print("TABELLA-LISTINO — calibrazione (walk-forward, 3 leghe, 6 stagioni di test)")
    print("=" * 118)
    print(f"{'mercato':<34}{'liv':>5}{'n':>7}{'P media':>10}{'reale':>9}"
          f"{'bias':>9}{'ECE':>8}{'LL mod':>9}{'LL base':>9}{'Δ base':>10}"
          f"{'LL mkt':>9}{'Δ mkt':>9}")
    print("-" * 118)
    last = None
    for r in listino:
        if r["level"] != last:
            print(f"--- livello {r['level']}: {LEVEL_TEXT.get(r['level'], 'esito osservabile, n piccolo')} ---")
            last = r["level"]
        print(f"{r['label']:<34}{r['level']:>5}{r['n']:>7}"
              f"{fmt(r['p_mean'], 10)}{fmt(r['freq'], 9)}{fmt(r['bias'], 9, 4, True)}"
              f"{fmt(r['ece'], 8)}{fmt(r['ll_model'], 9)}{fmt(r['ll_base'], 9)}"
              f"{fmt(r['delta_base'], 10, 4, True)}{fmt(r['ll_market'], 9)}"
              f"{fmt(r['delta_market'], 9, 4, True)}")
    print("-" * 118)
    print("Δ negativo = il modello e' MEGLIO (log-loss piu' basso). 'base' = frequenza")
    print("delle sole stagioni passate della stessa lega (ex-ante, giocabile).")
    print("ATTENZIONE alle IDENTITA': 1X = 1 − P(2), 2X = 1 − P(1), 12 = 1 − P(X). Le tre")
    print("righe di doppia chance NON sono validazioni indipendenti: sono le stesse")
    print("previsioni scritte al contrario (stessa log-loss binaria). Stessa trappola")
    print("che la Fase 92 ha scoperto sul mercato '12'.")

    print(f"\n{'CALIBRAZIONE PER LEGA (26 mercati binari della matrice)':<60}")
    print(f"  {'lega':<18}{'n':>7}{'|bias| medio':>14}{'ECE medio':>12}")
    for lg, v in per_lega.items():
        print(f"  {lg:<18}{v['n']:>7}{v['bias_assoluto_medio']:>14.4f}"
              f"{v['ece_medio']:>12.4f}")

    print("\n" + "=" * 118)
    print("RIGHE DI ONESTA — cosa possiamo e cosa NON possiamo affermare")
    print("=" * 118)
    for lev in ["A", "A°", "B"]:
        ks = [r["label"] for r in listino if r["level"] == lev]
        if not ks:
            continue
        print(f"\n[{lev}] {LEVEL_TEXT[lev]}")
        print(f"     -> {HONESTY[lev]}")
        print(f"     mercati ({len(ks)}): " + ", ".join(ks))
    lim = [r for r in listino if r["level"] == "B-limitato"]
    if lim:
        print("\n[B-limitato] esito osservabile ma n minuscolo e numeri IMPORTATI dal registro")
        print("     -> si puo' dire che battono le baseline di persistenza, ma su 24 "
              "stagioni-lega e con sovra-confidenza nota; nessuna quota storica")
        for r in lim:
            print(f"     {r['label']}: {r.get('source')}")
    print("\n[C] non validato / fuori portata")
    for name, why in C_MARKETS:
        print(f"     - {name}: {why}")

    # confronti significativi
    print("\n" + "=" * 118)
    print("VERDETTI (IC95% bootstrap appaiato sulle partite, 1000 ricampionamenti)")
    print("=" * 118)
    nb = [r for r in listino if r["ci_delta_base"]]
    win = [r for r in nb if r["ci_delta_base"][1] < 0]
    lose = [r for r in nb if r["ci_delta_base"][0] > 0]
    print(f"  batte la baseline ex-ante con IC conclusivo: {len(win)}/{len(nb)} mercati")
    if lose:
        print("  PERDE contro la baseline con IC conclusivo: "
              + ", ".join(r["label"] for r in lose))
    else:
        print("  nessun mercato perde contro la baseline con IC conclusivo")
    tie = [r for r in nb if r not in win and r not in lose]
    if tie:
        print("  NON conclusivi (IC include lo zero): "
              + ", ".join(f"{r['label']} ({r['delta_base']:+.4f})" for r in tie))
    print(f"\n  handicap asiatico (livello A) — log-loss sulle linee binarie: "
          f"Δ vs mercato {ah['delta_ll_half']:+.4f} "
          f"IC[{ah['ci_delta_ll_half'][0]:+.4f},{ah['ci_delta_ll_half'][1]:+.4f}]")
    mm = [r for r in listino if r.get("ci_delta_market")]
    for r in mm:
        v = ("MEGLIO del mercato" if r["ci_delta_market"][1] < 0
             else "PEGGIO del mercato" if r["ci_delta_market"][0] > 0 else "pari (IC include 0)")
        print(f"  {r['label']:<34} Δ vs mercato {r['delta_market']:+.4f} "
              f"IC[{r['ci_delta_market'][0]:+.4f},{r['ci_delta_market'][1]:+.4f}] -> {v}")

    # ---------------------------------------------------------------- json - #
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                         cwd=ROOT, text=True).strip()
    except Exception:
        commit = None
    payload = {
        "meta": {
            "titolo": "Listino dei mercati con etichetta di validazione (Fronte 7)",
            "commit": commit,
            "leghe": LEAGUES,
            "stagioni_test": [int(s) for s in seasons_te],
            "n_partite_test": int(len(pred)),
            "rho": RHO, "theta_grid": THETA_GRID, "n_bootstrap": NBOOT,
            "motore": "market-implied + router v3 (mi.price_markets), costanti "
                      "(phi0,kappa,theta) ri-fittate walk-forward sulle sole "
                      "stagioni passate della stessa lega",
            "baseline": "frequenza dell'esito nelle sole stagioni passate della "
                        "stessa lega (ex-ante)",
            "limiti": [
                "bootstrap a livello di partita: IC ottimistici (ignora la "
                "correlazione intra-stagione)",
                "livello A° = la quota e' l'INPUT del modello: confronto circolare",
                "finestra 2020-21..2025-26; il 2017-19 non ha O/U di chiusura",
                "calibrato non vuol dire vincente: alpha*=0 resta il fatto centrale",
                "le righe outright NON sono ricalcolate qui: importate dal registro",
            ],
        },
        "livelli": LEVEL_TEXT,
        "onesta": HONESTY,
        "folds": folds,
        "listino": listino,
        "handicap_asiatico_dettaglio": ah,
        "diagnosi_livello_conteggi": counts_levels,
        "calibrazione_per_lega": per_lega,
        "identita": ("1X = 1 − P(2), 2X = 1 − P(1), 12 = 1 − P(X): le doppie chance "
                     "non sono validazioni indipendenti dell'1X2 (lezione Fase 92)"),
        "livello_C": [{"mercato": n, "perche": w} for n, w in C_MARKETS],
    }
    OUT_JSON.parent.mkdir(exist_ok=True)
    json.dump(payload, open(OUT_JSON, "w"), indent=1, ensure_ascii=False)
    print(f"\nDati salvati in {OUT_JSON.relative_to(ROOT)} "
          f"({len(listino)} righe di listino)")


if __name__ == "__main__":
    main()
