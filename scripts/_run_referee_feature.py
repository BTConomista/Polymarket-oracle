"""Fase 97 (Fronte 2) — L'ARBITRO come FEATURE nel modello cartellini.

Contesto. La Fase 96 ha MISURATO l'effetto-arbitro sui cartellini in Premier
(sd fra arbitri 0.513 contro banda nulla da permutazione [0.158, 0.296];
ampiezza netta ~0.46 cartellini = 12.4% della media) ma non l'ha mai usato per
PREDIRE. E' il primo dato del progetto genuinamente ORTOGONALE ai gol
(|corr(cartellini, gol)| <= 0.06, Fase 96).

Domanda: l'arbitro migliora la predizione dei cartellini in modo CONCLUSIVO,
out-of-sample, walk-forward?

Metodo (tutto walk-forward, nessun look-ahead):
 0. COPERTURA del campo `Referee` — dichiarata sui dati reali, non assunta.
 1. BASE = il modello-cartellini della Fase 96 (`_run_outside_matrix.py`):
    forze attacco/difesa sul conteggio, pesate nel tempo (emivita 365g),
    shrinkage verso la media di lega, + fattori casa/ospite.
 2. BASE+ARBITRO = BASE x ref_factor, con ref_factor stimato SOLO sul passato e
    shrinkato verso 1 (formula in `referee_factors`, empirical-Bayes: la costante
    di shrinkage k e' il rapporto varianza-entro / varianza-fra stimato sul TRAIN
    di quel fold, quindi anch'essa senza look-ahead).
 3. Arbitri MAI visti nel train -> fattore 1 (contati e dichiarati).
 4. Confronto: MAE del totale, log-loss binario Over 2.5/3.5/4.5, calibrazione.
 5. CI bootstrap APPAIATO sulla differenza di log-loss e di MAE.
 6. Scomposizione della varianza: quanto pesa l'ARBITRO contro le SQUADRE.

NON registra run (diagnostico). Uso: python scripts/_run_referee_feature.py
"""
from __future__ import annotations

import glob
import io
import json
import sys
from math import exp, lgamma
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RAW_SA = "data/football_data_raw/serie_a_*.csv"
BUNDLES = {
    "premier_league": "files/football_data_premier_league_bundle.json",
    "la_liga": "files/football_data_la_liga_bundle.json",
}
HALF_LIFE = 365.0     # identica al DC ufficiale e alla BASE della Fase 96
SHRINK = 1.5          # idem
LINES = [2.5, 3.5, 4.5]
NBOOT = 4000
SEED = 20260726


# --------------------------------------------------------------------------- #
# 0. dati e copertura
# --------------------------------------------------------------------------- #
def _season_of(name: str) -> str:
    return name.split("_")[-1].replace(".csv", "")


def load_raw() -> pd.DataFrame:
    """Stesso caricamento della Fase 96 (per confrontare mele con mele)."""
    frames = []
    for f in sorted(glob.glob(RAW_SA)):
        try:
            d = pd.read_csv(f, encoding="latin-1")
        except Exception:
            d = pd.read_csv(f)
        d["league"] = "serie_a"; d["season"] = _season_of(f)
        frames.append(d)
    for lg, path in BUNDLES.items():
        for k, v in json.load(open(path)).items():
            if not isinstance(v, str):
                continue
            d = pd.read_csv(io.StringIO(v))
            d.columns = [c.lstrip("﻿") for c in d.columns]
            d["league"] = lg; d["season"] = _season_of(k)
            frames.append(d)
    keep = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HC", "AC",
            "HY", "AY", "HR", "AR", "league", "season"]
    out = []
    for d in frames:
        cols = [c for c in keep if c in d.columns]
        e = d[cols].copy()
        e["Referee"] = d["Referee"] if "Referee" in d.columns else np.nan
        out.append(e)
    df = pd.concat(out, ignore_index=True)
    df["date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "HY", "AY"]).sort_values("date")
    df["yellows"] = df["HY"] + df["AY"]
    df["cards_pts"] = (df["HY"] + df["AY"]
                       + 2 * df["HR"].fillna(0) + 2 * df["AR"].fillna(0))
    df["goals"] = df["FTHG"] + df["FTAG"]
    return df.reset_index(drop=True)


def coverage(df: pd.DataFrame) -> None:
    print("\n=== 0. COPERTURA REALE del campo `Referee` (verificata, non assunta) ===")
    print(f"{'lega':<16}{'partite':>9}{'con arbitro':>13}{'copertura':>11}"
          f"{'arbitri':>9}{'stagioni':>10}")
    for lg, g in df.groupby("league"):
        nn = int(g["Referee"].notna().sum())
        print(f"{lg:<16}{len(g):>9}{nn:>13}{100*nn/len(g):>10.1f}%"
              f"{g['Referee'].nunique():>9}{g['season'].nunique():>10}")
    d = df[df["Referee"].notna()]
    if not d.empty:
        cnt = d.groupby("Referee").size()
        print(f"  arbitri distinti: {len(cnt)} | con >=30 partite: {int((cnt>=30).sum())} "
              f"(coprono il {100*d['Referee'].isin(cnt[cnt>=30].index).mean():.1f}% delle partite)")
    print("  -> il campo esiste SOLO nel bundle Premier: La Liga e Serie A NON lo hanno.")
    print("     Tutto cio' che segue e' quindi Premier-only (limite dichiarato).")


# --------------------------------------------------------------------------- #
# 1. BASE — il modello-cartellini della Fase 96, invariato
# --------------------------------------------------------------------------- #
def fit_counts(train: pd.DataFrame, col_h: str, col_a: str, as_of: pd.Timestamp):
    """Copia fedele di `_run_outside_matrix.fit_counts` (Fase 96)."""
    w = 0.5 ** ((as_of - train["date"]).dt.days / HALF_LIFE)
    tot = (train[col_h] * w).sum() + (train[col_a] * w).sum()
    n = 2 * w.sum()
    base = tot / n if n else 1.0
    hadv = ((train[col_h] * w).sum() / w.sum()) / max(base, 1e-9)
    aadv = ((train[col_a] * w).sum() / w.sum()) / max(base, 1e-9)
    att, dfn = {}, {}
    teams = set(train["HomeTeam"]) | set(train["AwayTeam"])
    for t in teams:
        mh, ma = train["HomeTeam"] == t, train["AwayTeam"] == t
        wt = w[mh].sum() + w[ma].sum()
        prod = (train.loc[mh, col_h] * w[mh]).sum() + (train.loc[ma, col_a] * w[ma]).sum()
        conc = (train.loc[mh, col_a] * w[mh]).sum() + (train.loc[ma, col_h] * w[ma]).sum()
        k = SHRINK * 10.0
        att[t] = (prod + k * base) / (wt + k) / max(base, 1e-9)
        dfn[t] = (conc + k * base) / (wt + k) / max(base, 1e-9)
    return att, dfn, base, hadv, aadv


# --------------------------------------------------------------------------- #
# 2. il fattore-arbitro (empirical Bayes, stimato SOLO sul train del fold)
# --------------------------------------------------------------------------- #
def referee_factors(x: np.ndarray, ref: np.ndarray, mode: str = "raw"):
    """Moltiplicatore per-arbitro con shrinkage verso 1.

    x   : quantita' per partita su cui si stima l'arbitro
          mode='raw'   -> x = cartellini totali della partita  (spec del task)
          mode='resid' -> x = cartellini / atteso_BASE         (netto delle squadre)
    ref : etichetta arbitro della stessa partita.

    FORMULA (shrinkage empirical-Bayes, one-way random effects, MoM):
        m_bar   = media generale di x sul TRAIN
        m_r     = media di x per l'arbitro r,  n_r = sue partite nel TRAIN
        s2_e    = varianza ENTRO arbitro (pooled):
                  sum_i (x_i - m_{r(i)})^2 / (N - R)
        tau2    = varianza FRA arbitri, corretta per il rumore di campionamento:
                  [ sum_r n_r (m_r - m_bar)^2 - (R-1) * s2_e ]
                  / ( N - sum_r n_r^2 / N )
        k       = s2_e / tau2          <- costante di shrinkage, IN PARTITE
        m_hat_r = (n_r * m_r + k * m_bar) / (n_r + k)
        factor_r= m_hat_r / m_bar   =  1 + (m_r/m_bar - 1) * n_r/(n_r + k)

    Il peso n_r/(n_r+k) e' 0 con zero partite (fattore 1) e -> 1 con molte
    partite: e' esattamente lo "shrinkage proporzionale al numero di partite
    arbitrate" richiesto, con k scelto dai dati invece che a mano.
    Se tau2 <= 0 (nessun segnale fra arbitri nel train) -> k = +inf -> tutti i
    fattori valgono 1: il modello si auto-protegge.
    """
    s = pd.DataFrame({"x": x, "r": ref})
    m_bar = float(s["x"].mean())
    g = s.groupby("r")["x"].agg(["count", "mean"])
    N, R = len(s), len(g)
    within = float(((s["x"] - s["r"].map(g["mean"])) ** 2).sum())
    s2_e = within / max(N - R, 1)
    between = float((g["count"] * (g["mean"] - m_bar) ** 2).sum())
    denom = N - float((g["count"] ** 2).sum()) / N
    tau2 = (between - (R - 1) * s2_e) / denom if denom > 0 else 0.0
    if tau2 <= 0 or m_bar <= 0:
        return {r: 1.0 for r in g.index}, float("inf"), 0.0, s2_e
    k = s2_e / tau2
    fac = {}
    for r, row in g.iterrows():
        n_r = float(row["count"])
        m_hat = (n_r * row["mean"] + k * m_bar) / (n_r + k)
        fac[r] = m_hat / m_bar
    return fac, k, tau2, s2_e


# --------------------------------------------------------------------------- #
# 3. walk-forward: BASE vs BASE+ARBITRO
# --------------------------------------------------------------------------- #
def walk_forward(df: pd.DataFrame, col_h: str, col_a: str, league: str,
                 time_weighted_ref: bool = False) -> tuple[pd.DataFrame, list]:
    g = df[df["league"] == league].copy()
    rows, folds = [], []
    seasons = sorted(g["season"].unique())
    for s in seasons[2:]:                        # >=2 stagioni di storia (come F96)
        train = g[g["season"] < s]
        test = g[g["season"] == s]
        if len(train) < 400 or test.empty:
            continue
        as_of = test["date"].min()
        att, dfn, base, hadv, aadv = fit_counts(train, col_h, col_a, as_of)

        tr = train[train["Referee"].notna()].copy()
        tr["tot"] = tr[col_h] + tr[col_a]
        # atteso BASE sul train (per la variante 'resid'): stesse forze del fold
        exp_tr = np.array([
            base * hadv * att.get(h, 1.0) * dfn.get(a, 1.0)
            + base * aadv * att.get(a, 1.0) * dfn.get(h, 1.0)
            for h, a in zip(tr["HomeTeam"], tr["AwayTeam"])])
        fac_raw, k_raw, tau2, s2e = referee_factors(
            tr["tot"].to_numpy(), tr["Referee"].to_numpy(), "raw")
        fac_res, k_res, tau2r, _ = referee_factors(
            (tr["tot"].to_numpy() / np.maximum(exp_tr, 1e-9)),
            tr["Referee"].to_numpy(), "resid")

        # --- costante di LIVELLO, stimata SOLO sul train -------------------
        # Il BASE sotto-stima (i cartellini in Premier CRESCONO nel tempo) e il
        # fattore-arbitro medio applicato risulta > 1: parte del guadagno
        # potrebbe essere una semplice CORREZIONE DI LIVELLO, non informazione
        # sull'arbitro. c_fold = media dei fattori pesata per le partite che
        # ogni arbitro ha diretto nell'ULTIMA stagione di train (proxy senza
        # look-ahead di chi arbitrera'). Serve a costruire due controlli:
        #   exp_lvl = BASE * c_fold        (solo livello, arbitro indistinto)
        #   exp_cen = BASE * f_r / c_fold  (solo discriminazione, livello tolto)
        last = tr[tr["season"] == tr["season"].max()]
        cnt_last = last.groupby("Referee").size()
        num = sum(cnt_last.get(r, 0) * fac_raw[r] for r in fac_raw)
        den = sum(cnt_last.get(r, 0) for r in fac_raw)
        c_fold = float(num / den) if den > 0 else 1.0

        # --- SMORZAMENTO b stimato con walk-forward ANNIDATO dentro il train --
        # Il fattore grezzo risulta sovra-esteso (b<1) perche' il tasso-cartellini
        # di un arbitro DERIVA nel tempo. b si puo' stimare senza look-ahead:
        # si rifitta tutto sulle stagioni < ultima-di-train e si misura l'ampiezza
        # che regge sull'ultima stagione di train (che qui fa da test interno).
        b_in = 0.0
        inner_seasons = sorted(tr["season"].unique())
        if len(inner_seasons) >= 3:
            i_te = tr[tr["season"] == inner_seasons[-1]]
            i_tr = tr[tr["season"] < inner_seasons[-1]]
            i_att, i_dfn, i_base, i_h, i_a = fit_counts(
                i_tr, col_h, col_a, i_te["date"].min())
            i_fac, *_ = referee_factors(
                (i_tr[col_h] + i_tr[col_a]).to_numpy(), i_tr["Referee"].to_numpy())
            xs, ys = [], []
            for _, q in i_te.iterrows():
                h, a = q["HomeTeam"], q["AwayTeam"]
                if h not in i_att or a not in i_att:
                    continue
                ee = (i_base * i_h * i_att[h] * i_dfn[a]
                      + i_base * i_a * i_att[a] * i_dfn[h])
                xs.append(i_fac.get(q["Referee"], 1.0) - 1.0)
                ys.append((q[col_h] + q[col_a]) / max(ee, 1e-9))
            if len(xs) > 50:
                Ai = np.column_stack([np.ones(len(xs)), np.array(xs)])
                ci, *_ = np.linalg.lstsq(Ai, np.array(ys), rcond=None)
                b_in = float(np.clip(ci[1], 0.0, 1.0))

        n_unseen = 0
        for _, r in test.iterrows():
            h, a = r["HomeTeam"], r["AwayTeam"]
            if h not in att or a not in att:
                continue
            e = (base * hadv * att[h] * dfn[a]) + (base * aadv * att[a] * dfn[h])
            ref = r["Referee"]
            seen = isinstance(ref, str) and ref in fac_raw
            if not seen:
                n_unseen += 1
            f_raw = fac_raw.get(ref, 1.0) if isinstance(ref, str) else 1.0
            f_res = fac_res.get(ref, 1.0) if isinstance(ref, str) else 1.0
            rows.append({"season": s, "date": r["date"], "ref": ref,
                         "seen": bool(seen),
                         "exp_base": e, "exp_ref": e * f_raw,
                         "exp_res": e * f_res,
                         "exp_lvl": e * c_fold, "exp_cen": e * f_raw / c_fold,
                         "exp_damp": e * (1.0 + b_in * (f_raw - 1.0)),
                         "f_raw": f_raw, "f_res": f_res, "c_fold": c_fold,
                         "b_in": b_in,
                         "real": r[col_h] + r[col_a], "lgmean": 2 * base})
        folds.append({"season": s, "n_train": len(tr), "n_ref_train": tr["Referee"].nunique(),
                      "k_raw": k_raw, "tau2": tau2, "s2e": s2e, "k_res": k_res,
                      "unseen": n_unseen, "c_fold": c_fold, "b_in": b_in,
                      "fmin": min(fac_raw.values()), "fmax": max(fac_raw.values())})
    return pd.DataFrame(rows), folds


# --------------------------------------------------------------------------- #
# 4. metriche
# --------------------------------------------------------------------------- #
def _pois_over(mean: float, line: float) -> float:
    kmax = int(np.floor(line))
    lm = np.log(max(mean, 1e-9))
    p_le = sum(exp(-mean + k * lm - lgamma(k + 1)) for k in range(kmax + 1))
    return float(min(max(1.0 - p_le, 1e-9), 1 - 1e-9))


def over_probs(means: np.ndarray, line: float) -> np.ndarray:
    return np.array([_pois_over(m, line) for m in means])


def logloss_vec(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def paired_boot(d: np.ndarray, nboot: int = NBOOT, seed: int = SEED):
    """CI bootstrap APPAIATO sulla media di d (differenza per-partita)."""
    rng = np.random.default_rng(seed)
    n = len(d)
    idx = rng.integers(0, n, size=(nboot, n))
    means = d[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float((means < 0).mean())


# --------------------------------------------------------------------------- #
# 5. report
# --------------------------------------------------------------------------- #
def report(wf: pd.DataFrame, folds: list, label: str) -> None:
    print(f"\n=== BASE vs BASE+ARBITRO — {label} ===")
    if wf.empty:
        print("  nessun dato"); return
    print(f"  fold walk-forward: {len(folds)} stagioni di test, n={len(wf)} partite OOS")
    print(f"\n  {'stagione':>9}{'n_train':>9}{'arb.train':>11}{'k (EB)':>9}"
          f"{'tau2':>9}{'fattori min-max':>18}{'arb. MAI visti':>16}")
    for f in folds:
        k = f["k_raw"]
        ktxt = f"{k:.1f}" if np.isfinite(k) else "inf"
        rng_txt = "%.3f-%.3f" % (f["fmin"], f["fmax"])
        print(f"  {f['season']:>9}{f['n_train']:>9}{f['n_ref_train']:>11}"
              f"{ktxt:>9}{f['tau2']:>9.4f}{rng_txt:>18}{f['unseen']:>16}")
    tot_unseen = sum(f["unseen"] for f in folds)
    print(f"  partite di test con arbitro MAI visto prima (fattore=1): "
          f"{tot_unseen} / {len(wf)} ({100*tot_unseen/len(wf):.1f}%)")

    y_r, e_b, e_r, e_s = (wf["real"].to_numpy().astype(float),
                          wf["exp_base"].to_numpy(), wf["exp_ref"].to_numpy(),
                          wf["exp_res"].to_numpy())
    lg = wf["lgmean"].to_numpy()
    # sanity anti-bias (regola 4 del brief): medie a confronto
    print(f"\n  SANITY bias: media reale {y_r.mean():.3f} | BASE {e_b.mean():.3f} "
          f"({e_b.mean()-y_r.mean():+.3f}) | +ARB {e_r.mean():.3f} "
          f"({e_r.mean()-y_r.mean():+.3f}) | +ARB-resid {e_s.mean():.3f} "
          f"({e_s.mean()-y_r.mean():+.3f}) | fattore medio applicato {wf['f_raw'].mean():.4f}")

    print(f"\n  {'modello':<22}{'MAE':>9}{'RMSE':>9}{'R2 vs media-lega':>19}")
    for nm, e in [("media di lega", lg), ("BASE (Fase 96)", e_b),
                  ("BASE + arbitro", e_r), ("BASE + arbitro-resid", e_s)]:
        mae = float(np.abs(e - y_r).mean())
        rmse = float(np.sqrt(((e - y_r) ** 2).mean()))
        r2 = 1 - ((e - y_r) ** 2).mean() / ((lg - y_r) ** 2).mean()
        print(f"  {nm:<22}{mae:>9.4f}{rmse:>9.4f}{r2:>+19.4f}")

    d_mae = np.abs(e_r - y_r) - np.abs(e_b - y_r)
    m, lo, hi, pneg = paired_boot(d_mae)
    print(f"  Delta MAE (+arbitro - BASE) = {m:+.4f}  IC95% [{lo:+.4f}, {hi:+.4f}]"
          f"  P(miglioramento)={pneg:.3f}   (negativo = arbitro MEGLIO)")

    print(f"\n  --- log-loss binario Over/Under (Poisson attorno all'atteso) ---")
    print(f"  {'linea':>7}{'freq reale':>12}{'P BASE':>9}{'P +ARB':>9}"
          f"{'LL BASE':>10}{'LL +ARB':>10}{'Delta':>10}{'IC95% appaiato':>26}{'P(migl.)':>10}")
    for L in LINES:
        y = (y_r > L).astype(float)
        pb, pr = over_probs(e_b, L), over_probs(e_r, L)
        lb, lr = logloss_vec(pb, y), logloss_vec(pr, y)
        d = lr - lb
        m, lo, hi, pneg = paired_boot(d)
        print(f"  {('O'+str(L)):>7}{y.mean():>12.4f}{pb.mean():>9.4f}{pr.mean():>9.4f}"
              f"{lb.mean():>10.4f}{lr.mean():>10.4f}{m:>+10.5f}"
              f"{f'[{lo:+.5f}, {hi:+.5f}]':>26}{pneg:>10.3f}")
    print("  (Delta negativo = il modello con l'arbitro ha log-loss MINORE = meglio.")
    print("   CONCLUSIVO se l'IC95% appaiato sta interamente sotto lo zero.)")

    print(f"\n  --- variante 'resid' (fattore stimato sul rapporto reale/atteso-BASE) ---")
    for L in LINES:
        y = (y_r > L).astype(float)
        pb, ps = over_probs(e_b, L), over_probs(e_s, L)
        d = logloss_vec(ps, y) - logloss_vec(pb, y)
        m, lo, hi, pneg = paired_boot(d)
        print(f"  {('O'+str(L)):>7} Delta LL {m:>+10.5f}  IC95% [{lo:+.5f}, {hi:+.5f}]"
              f"  P(migl.)={pneg:.3f}")

    # calibrazione per terzili di fattore-arbitro (dove l'arbitro dice qualcosa)
    # ---- LIVELLO vs DISCRIMINAZIONE (controllo anti-artefatto) -------------
    e_l, e_c = wf["exp_lvl"].to_numpy(), wf["exp_cen"].to_numpy()
    print(f"\n  --- CONTROLLO: il guadagno e' INFORMAZIONE sull'arbitro o solo "
          f"CORREZIONE DI LIVELLO? ---")
    print(f"  c_fold (costante di livello train-only) per stagione: "
          + ", ".join(f"{f['season']}={f['c_fold']:.4f}" for f in folds))
    print(f"  {'modello':<34}{'MAE':>9}{'media attesa':>14}{'LL O3.5':>10}{'Delta LL vs BASE':>19}")
    y35 = (y_r > 3.5).astype(float)
    ll_base35 = logloss_vec(over_probs(e_b, 3.5), y35)
    for nm, e in [("BASE", e_b), ("BASE x c_fold (SOLO livello)", e_l),
                  ("BASE x f_arb (livello+arbitro)", e_r),
                  ("BASE x f_arb/c_fold (SOLO arbitro)", e_c)]:
        ll = logloss_vec(over_probs(e, 3.5), y35)
        print(f"  {nm:<34}{float(np.abs(e-y_r).mean()):>9.4f}{e.mean():>14.3f}"
              f"{ll.mean():>10.4f}{ll.mean()-ll_base35.mean():>+19.5f}")
    d_cen = logloss_vec(over_probs(e_c, 3.5), y35) - ll_base35
    m, lo, hi, pneg = paired_boot(d_cen)
    print(f"  SOLO arbitro (livello tolto) vs BASE su O3.5: Delta LL {m:+.5f} "
          f"IC95% [{lo:+.5f}, {hi:+.5f}] P(migl.)={pneg:.3f}")
    d_ref_vs_lvl = (logloss_vec(over_probs(e_r, 3.5), y35)
                    - logloss_vec(over_probs(e_l, 3.5), y35))
    m, lo, hi, pneg = paired_boot(d_ref_vs_lvl)
    print(f"  +ARBITRO vs SOLO-livello su O3.5:              Delta LL {m:+.5f} "
          f"IC95% [{lo:+.5f}, {hi:+.5f}] P(migl.)={pneg:.3f}")

    print(f"\n  --- CALIBRAZIONE per terzile del fattore-arbitro (totale atteso vs reale) ---")
    q = pd.qcut(wf["f_raw"], 3, labels=["arb. permissivo", "arb. medio", "arb. severo"],
                duplicates="drop")
    print(f"  {'gruppo':<18}{'n':>7}{'fattore μ':>11}{'atteso BASE':>13}"
          f"{'atteso +ARB':>13}{'reale':>9}{'bias BASE':>11}{'bias +ARB':>11}")
    for name, sub in wf.groupby(q, observed=True):
        print(f"  {str(name):<18}{len(sub):>7}{sub['f_raw'].mean():>11.4f}"
              f"{sub['exp_base'].mean():>13.3f}{sub['exp_ref'].mean():>13.3f}"
              f"{sub['real'].mean():>9.3f}"
              f"{sub['exp_base'].mean()-sub['real'].mean():>+11.3f}"
              f"{sub['exp_ref'].mean()-sub['real'].mean():>+11.3f}")

    # quanto del fattore-arbitro "regge" fuori campione?
    # regressione OOS senza intercetta forzata:  real/BASE = a + b*(f_r - 1)
    # b=1 -> il fattore e' esattamente della giusta ampiezza; b<1 -> e' TROPPO
    # esteso (lo shrinkage EB non basta); b~0 -> non predice nulla.
    ratio = y_r / np.maximum(e_b, 1e-9)
    xx = wf["f_raw"].to_numpy() - 1.0
    A = np.column_stack([np.ones_like(xx), xx])
    coef, *_ = np.linalg.lstsq(A, ratio, rcond=None)
    resid = ratio - A @ coef
    dof = max(len(xx) - 2, 1)
    cov = float(resid @ resid) / dof * np.linalg.inv(A.T @ A)
    se_b = float(np.sqrt(cov[1, 1]))
    print(f"\n  --- ampiezza OOS del fattore: real/BASE = a + b*(f_arb - 1) ---")
    print(f"  a = {coef[0]:.4f} (il livello che manca al BASE) | "
          f"b = {coef[1]:.3f} ± {se_b:.3f} (IC95% [{coef[1]-1.96*se_b:+.3f}, "
          f"{coef[1]+1.96*se_b:+.3f}])")
    print(f"  b=1 -> fattore della giusta ampiezza; b<1 -> SOVRA-esteso; "
          f"b~0 -> nessun potere predittivo.")

    # variante SMORZATA: b stimato train-only (walk-forward annidato)
    e_d = wf["exp_damp"].to_numpy()
    print(f"\n  --- variante SMORZATA (b stimato train-only, annidato) ---")
    print(f"  b_in per stagione: " + ", ".join(f"{f['season']}={f['b_in']:.3f}" for f in folds))
    print(f"  {'linea':>7}{'LL BASE':>10}{'LL smorz.':>11}{'Delta':>10}"
          f"{'IC95% appaiato':>26}{'P(migl.)':>10}")
    for L in LINES:
        y = (y_r > L).astype(float)
        d = logloss_vec(over_probs(e_d, L), y) - logloss_vec(over_probs(e_b, L), y)
        m, lo, hi, pneg = paired_boot(d)
        print(f"  {('O'+str(L)):>7}{logloss_vec(over_probs(e_b,L),y).mean():>10.4f}"
              f"{logloss_vec(over_probs(e_d,L),y).mean():>11.4f}{m:>+10.5f}"
              f"{f'[{lo:+.5f}, {hi:+.5f}]':>26}{pneg:>10.3f}")
    print(f"  MAE smorzato {float(np.abs(e_d-y_r).mean()):.4f} vs BASE "
          f"{float(np.abs(e_b-y_r).mean()):.4f}")

    # per stagione
    print(f"\n  --- per stagione (MAE) ---")
    print(f"  {'stagione':>9}{'n':>6}{'MAE BASE':>11}{'MAE +ARB':>11}{'Delta':>10}")
    nwin = 0
    for s, sub in wf.groupby("season"):
        mb = float(np.abs(sub["exp_base"] - sub["real"]).mean())
        mr = float(np.abs(sub["exp_ref"] - sub["real"]).mean())
        nwin += int(mr < mb)
        print(f"  {s:>9}{len(sub):>6}{mb:>11.4f}{mr:>11.4f}{mr-mb:>+10.4f}")
    print(f"  stagioni in cui l'arbitro migliora il MAE: {nwin}/{wf['season'].nunique()}")


# --------------------------------------------------------------------------- #
# 6. arbitro vs squadre: chi spiega piu' varianza?
# --------------------------------------------------------------------------- #
def variance_decomposition(df: pd.DataFrame, wf: pd.DataFrame, col_h: str,
                           col_a: str, label: str) -> None:
    print(f"\n=== 6. VARIANZA: l'ARBITRO o le SQUADRE? — {label} ===")
    d = df[(df["league"] == "premier_league") & df["Referee"].notna()].copy()
    d["tot"] = d[col_h] + d[col_a]
    tot_var = float(d["tot"].var())
    print(f"  varianza totale dei cartellini per partita: {tot_var:.4f} "
          f"(media {d['tot'].mean():.3f})")

    def comp(labels: pd.Series, x: pd.Series) -> float:
        """Componente di varianza FRA gruppi, MoM one-way (corretta per il
        rumore di campionamento):  tau2 = [SSB - (R-1)*s2_e] / (N - sum n_r^2/N)."""
        s = pd.DataFrame({"g": labels.to_numpy(), "x": x.to_numpy()})
        m_bar = s["x"].mean()
        g = s.groupby("g")["x"].agg(["count", "mean"])
        N, R = len(s), len(g)
        s2_e = float(((s["x"] - s["g"].map(g["mean"])) ** 2).sum()) / max(N - R, 1)
        ssb = float((g["count"] * (g["mean"] - m_bar) ** 2).sum())
        den = N - float((g["count"] ** 2).sum()) / N
        return max((ssb - (R - 1) * s2_e) / den, 0.0) if den > 0 else 0.0

    v_ref = comp(d["Referee"], d["tot"])
    v_home = comp(d["HomeTeam"], d["tot"])
    v_away = comp(d["AwayTeam"], d["tot"])
    pair = d["HomeTeam"].astype(str) + "|" + d["AwayTeam"].astype(str)
    v_pair = comp(pair, d["tot"])
    print(f"\n  componenti di varianza (MoM, al netto del rumore di campionamento):")
    print(f"    {'raggruppamento':<26}{'varianza':>11}{'% del totale':>14}{'sd (cartellini)':>18}")
    for nm, v in [("ARBITRO", v_ref), ("squadra di CASA", v_home),
                  ("squadra OSPITE", v_away), ("accoppiamento casa|ospite", v_pair)]:
        print(f"    {nm:<26}{v:>11.4f}{100*v/tot_var:>13.1f}%{np.sqrt(v):>18.3f}")

    # confronto in-sample onesto: quanto del segnale OOS viene da chi
    v_teams_model = float(np.var(wf["exp_base"]))
    v_ref_model = float(np.var(wf["exp_ref"] - wf["exp_base"] + wf["exp_ref"].mean()))
    print(f"\n  lato MODELLO (out-of-sample, sulle {len(wf)} partite di test):")
    print(f"    varianza dell'atteso BASE (segnale SQUADRE):        {v_teams_model:.4f}")
    print(f"    varianza aggiunta dal fattore-arbitro (shrinkato):  "
          f"{float(np.var(wf['exp_ref'] - wf['exp_base'])):.4f}")
    print(f"    sd del fattore-arbitro applicato OOS: {wf['f_raw'].std():.4f} "
          f"(range {wf['f_raw'].min():.3f}-{wf['f_raw'].max():.3f})")
    # R2 OOS marginali
    y = wf["real"].to_numpy().astype(float)
    lgm = wf["lgmean"].to_numpy()
    sse0 = ((lgm - y) ** 2).mean()
    only_ref = lgm * wf["f_raw"].to_numpy()
    print(f"\n  R2 OOS marginali (contro la media di lega):")
    print(f"    solo SQUADRE (BASE):        {1 - ((wf['exp_base']-y)**2).mean()/sse0:+.4f}")
    print(f"    solo ARBITRO:               {1 - ((only_ref-y)**2).mean()/sse0:+.4f}")
    print(f"    SQUADRE + ARBITRO:          {1 - ((wf['exp_ref']-y)**2).mean()/sse0:+.4f}")


def main() -> None:
    df = load_raw()
    print(f"Partite caricate: {len(df)} ({df['league'].nunique()} leghe, "
          f"{df['season'].nunique()} stagioni)")
    coverage(df)

    # bersaglio primario: HY+AY = lo STESSO target del modello-cartellini F96
    wf, folds = walk_forward(df, "HY", "AY", "premier_league")
    report(wf, folds, "GIALLI (HY+AY) — target del modello Fase 96")
    variance_decomposition(df, wf, "HY", "AY", "GIALLI (HY+AY)")

    # robustezza: punti-cartellino (gialli + 2x rossi) = target della MISURA F96
    df2 = df.copy()
    df2["HYp"] = df2["HY"] + 2 * df2["HR"].fillna(0)
    df2["AYp"] = df2["AY"] + 2 * df2["AR"].fillna(0)
    wf2, folds2 = walk_forward(df2, "HYp", "AYp", "premier_league")
    report(wf2, folds2, "PUNTI-CARTELLINO (gialli + 2x rossi) — target della misura F96")
    variance_decomposition(df2, wf2, "HYp", "AYp", "PUNTI-CARTELLINO")


if __name__ == "__main__":
    main()
