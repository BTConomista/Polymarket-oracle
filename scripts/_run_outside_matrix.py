"""Fase 96 — I mercati FUORI dalla matrice dei gol: corner e cartellini.

Perche'. Tutto cio' che il progetto ha dimostrato (alpha*=0, tetto informativo,
coda al tetto) vale per i mercati DERIVABILI dalla matrice P(gol_casa, gol_ospite):
1X2, O/U, GG/NG, esatto, multigol, clean sheet, scarto/handicap. I mercati con un
processo generatore PROPRIO — corner (pressione territoriale), cartellini
(arbitro, tensione, falli) — non sono mai stati modellati: il tetto non dice
niente su di loro.

Cosa misura questo script (tutto walk-forward, nessun look-ahead):
 1. STRUTTURA: media/varianza dei conteggi, indice di dispersione var/media, e
    quanto i corner/cartellini sono correlati coi gol (se fossero ridondanti
    col motore-gol non sarebbero un mercato nuovo);
 2. MODELLO: un Dixon-Coles-like sui CONTEGGI (forza-corner attacco/difesa per
    squadra + vantaggio casa, stima pesata nel tempo), confrontato con la
    baseline "media di lega" e con la Poisson a tasso costante;
 3. CALIBRAZIONE: sui mercati derivati (Over/Under corner sulle linee 8.5-11.5,
    Over cartellini 3.5-4.5) — la calibrazione si misura CON GLI ESITI, non
    servono le quote (nota di metodo della Fase 96: senza quote manca il
    benchmark di EFFICIENZA, non la calibrazione);
 4. EFFETTO ARBITRO (solo Premier, l'unica lega col campo `Referee`): quanto
    della varianza dei cartellini e' spiegato da CHI arbitra, e se e' un effetto
    reale o rumore da campione piccolo (confronto con permutazione).

NON registra run (diagnostico). Uso: python scripts/_run_outside_matrix.py
"""
from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RAW_SA = "data/football_data_raw/serie_a_*.csv"
BUNDLES = {
    "premier_league": "files/football_data_premier_league_bundle.json",
    "la_liga": "files/football_data_la_liga_bundle.json",
}
HALF_LIFE = 365.0     # stessa memoria del DC ufficiale
SHRINK = 1.5


def _season_of(name: str) -> str:
    return name.split("_")[-1].replace(".csv", "")


def load_raw() -> pd.DataFrame:
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
            "HY", "AY", "HR", "AR", "HS", "AS", "HF", "AF", "league", "season"]
    out = []
    for d in frames:
        cols = [c for c in keep if c in d.columns]
        e = d[cols].copy()
        e["Referee"] = d["Referee"] if "Referee" in d.columns else np.nan
        out.append(e)
    df = pd.concat(out, ignore_index=True)
    df["date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "HC", "AC", "HY", "AY"]).sort_values("date")
    df["corners"] = df["HC"] + df["AC"]
    df["cards"] = df["HY"] + df["AY"] + 2 * df["HR"].fillna(0) + 2 * df["AR"].fillna(0)
    df["goals"] = df["FTHG"] + df["FTAG"]
    return df.reset_index(drop=True)


def structure(df: pd.DataFrame) -> None:
    print("\n=== 1. STRUTTURA dei conteggi (per lega) ===")
    print(f"{'lega':<16}{'n':>6}{'corner μ':>10}{'σ²/μ':>8}{'cart. μ':>10}{'σ²/μ':>8}"
          f"{'corr(corner,gol)':>18}{'corr(cart,gol)':>16}")
    for lg, g in df.groupby("league"):
        c, k, go = g["corners"], g["cards"], g["goals"]
        print(f"{lg:<16}{len(g):>6}{c.mean():>10.2f}{c.var()/c.mean():>8.2f}"
              f"{k.mean():>10.2f}{k.var()/k.mean():>8.2f}"
              f"{np.corrcoef(c, go)[0,1]:>18.3f}{np.corrcoef(k, go)[0,1]:>16.3f}")
    print("  σ²/μ > 1 = SOVRA-dispersi (al contrario dei gol dati i tassi del "
          "mercato, sotto-dispersi θ>1: sono processi diversi).")
    print("  corr bassa coi gol = informazione NON ridondante col motore-gol.")


def fit_counts(train: pd.DataFrame, col_h: str, col_a: str, as_of: pd.Timestamp
               ) -> tuple[dict, dict, float, float]:
    """Forze attacco/difesa sul conteggio, stile DC ma in forma chiusa pesata:
    att_t = log(media pesata prodotta da t / media lega), def_t = log(concessa)."""
    w = 0.5 ** ((as_of - train["date"]).dt.days / HALF_LIFE)
    tot = (train[col_h] * w).sum() + (train[col_a] * w).sum()
    n = 2 * w.sum()
    base = tot / n if n else 1.0
    # vantaggio casa E fattore ospite: devono sommare a 2 (altrimenti il totale
    # atteso e' sistematicamente gonfiato — bug trovato dal bias +0.61 sui corner)
    hadv = ((train[col_h] * w).sum() / w.sum()) / max(base, 1e-9)
    aadv = ((train[col_a] * w).sum() / w.sum()) / max(base, 1e-9)
    att, dfn = {}, {}
    teams = set(train["HomeTeam"]) | set(train["AwayTeam"])
    for t in teams:
        mh, ma = train["HomeTeam"] == t, train["AwayTeam"] == t
        wt = w[mh].sum() + w[ma].sum()
        prod = (train.loc[mh, col_h] * w[mh]).sum() + (train.loc[ma, col_a] * w[ma]).sum()
        conc = (train.loc[mh, col_a] * w[mh]).sum() + (train.loc[ma, col_h] * w[ma]).sum()
        # shrinkage verso 1 (nessun effetto) con peso equivalente SHRINK*10 partite
        k = SHRINK * 10.0
        att[t] = (prod + k * base) / (wt + k) / max(base, 1e-9)
        dfn[t] = (conc + k * base) / (wt + k) / max(base, 1e-9)
    return att, dfn, base, hadv, aadv


def walk_forward(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Predice il totale di partita (corner o cartellini) per ogni stagione di
    test usando solo il passato. Ritorna righe con atteso e realizzato."""
    ch, ca = ("HC", "AC") if kind == "corners" else ("HY", "AY")
    rows = []
    for lg, g in df.groupby("league"):
        seasons = sorted(g["season"].unique())
        for s in seasons[2:]:                       # servono >=2 stagioni di storia
            train = g[g["season"] < s]
            test = g[g["season"] == s]
            if len(train) < 400 or test.empty:
                continue
            as_of = test["date"].min()
            att, dfn, base, hadv, aadv = fit_counts(train, ch, ca, as_of)
            for _, r in test.iterrows():
                h, a = r["HomeTeam"], r["AwayTeam"]
                if h not in att or a not in att:
                    continue
                exp_h = base * hadv * att[h] * dfn[a]
                exp_a = base * aadv * att[a] * dfn[h]
                rows.append({"league": lg, "season": s, "exp": exp_h + exp_a,
                             "real": r[ch] + r[ca], "base": 2 * base})
    return pd.DataFrame(rows)


def _pois_over(mean: float, line: float) -> float:
    """P(totale > line) con Poisson di media `mean` (line semi-intera)."""
    from math import exp, lgamma
    kmax = int(np.floor(line))
    p_le = sum(exp(-mean + k * np.log(max(mean, 1e-9)) - lgamma(k + 1))
               for k in range(kmax + 1))
    return float(1.0 - p_le)


def model_and_calibration(df: pd.DataFrame, kind: str, lines: list[float]) -> None:
    name = "CORNER" if kind == "corners" else "CARTELLINI (gialli, rossi×2)"
    print(f"\n=== 2-3. MODELLO e CALIBRAZIONE — {name} ===")
    wf = walk_forward(df, kind)
    if wf.empty:
        print("  nessun dato"); return
    err_m = float(np.abs(wf["exp"] - wf["real"]).mean())
    err_b = float(np.abs(wf["base"] - wf["real"]).mean())
    ss_m = float(((wf["exp"] - wf["real"]) ** 2).mean())
    ss_b = float(((wf["base"] - wf["real"]) ** 2).mean())
    print(f"  n={len(wf)} partite OOS | MAE modello {err_m:.3f} vs baseline "
          f"{err_b:.3f} ({100*(err_b-err_m)/err_b:+.1f}%) | "
          f"R² vs baseline {1-ss_m/ss_b:+.4f}")
    # calibrazione sui mercati Over/Under derivati (Poisson attorno all'atteso)
    print(f"\n  {'linea':>8}{'P media':>10}{'freq reale':>12}{'scarto':>9}"
          f"{'log-loss':>10}{'LL baseline':>13}")
    for L in lines:
        p = np.array([_pois_over(m, L) for m in wf["exp"]])
        pb = np.array([_pois_over(m, L) for m in wf["base"]])
        y = (wf["real"] > L).to_numpy().astype(float)
        ll = float(-(y * np.log(np.clip(p, 1e-9, 1)) +
                     (1 - y) * np.log(np.clip(1 - p, 1e-9, 1))).mean())
        llb = float(-(y * np.log(np.clip(pb, 1e-9, 1)) +
                      (1 - y) * np.log(np.clip(1 - pb, 1e-9, 1))).mean())
        print(f"{('O'+str(L)):>8}{p.mean():>10.3f}{y.mean():>12.3f}"
              f"{p.mean()-y.mean():>+9.3f}{ll:>10.4f}{llb:>13.4f}")
    print("  (la CALIBRAZIONE si misura con gli esiti: non servono le quote. "
          "Senza quote manca solo il confronto di EFFICIENZA col mercato.)")


def referee_effect(df: pd.DataFrame) -> None:
    print("\n=== 4. EFFETTO ARBITRO sui cartellini (solo Premier: unica lega col campo) ===")
    d = df[(df["league"] == "premier_league") & df["Referee"].notna()].copy()
    if d.empty:
        print("  nessun dato arbitro"); return
    g = d.groupby("Referee")["cards"].agg(["count", "mean"])
    g = g[g["count"] >= 30]
    print(f"  arbitri con ≥30 partite: {len(g)} | media generale {d['cards'].mean():.2f} "
          f"cartellini/partita")
    print(f"  range medie per arbitro: {g['mean'].min():.2f} – {g['mean'].max():.2f} "
          f"(sd fra arbitri {g['mean'].std():.3f})")
    # l'effetto e' reale o rumore? confronto con permutazione dell'etichetta-arbitro
    rng = np.random.default_rng(0)
    obs = float(g["mean"].std())
    null = []
    lab = d["Referee"].to_numpy(); val = d["cards"].to_numpy()
    for _ in range(2000):
        perm = rng.permutation(lab)
        s = pd.DataFrame({"r": perm, "c": val}).groupby("r")["c"].agg(["count", "mean"])
        s = s[s["count"] >= 30]
        null.append(float(s["mean"].std()))
    null = np.array(null)
    lo, hi = np.percentile(null, [2.5, 97.5])
    print(f"  sd osservata {obs:.3f} vs banda nulla [{lo:.3f}, {hi:.3f}] "
          f"-> {'EFFETTO REALE' if obs > hi else 'dentro il rumore'}")
    if obs > hi:
        extra = np.sqrt(max(obs ** 2 - null.mean() ** 2, 0))
        print(f"  ampiezza dell'effetto al netto del rumore: ~{extra:.2f} cartellini "
              f"di sd fra arbitri ({100*extra/d['cards'].mean():.1f}% della media)")
    print("  NB: e' un dato ORTOGONALE ai gol — nessun modello-gol lo contiene.")


def main() -> None:
    df = load_raw()
    print(f"Partite caricate: {len(df)} ({df['league'].nunique()} leghe, "
          f"{df['season'].nunique()} stagioni)")
    structure(df)
    model_and_calibration(df, "corners", [8.5, 9.5, 10.5, 11.5])
    model_and_calibration(df, "cards", [2.5, 3.5, 4.5])
    referee_effect(df)


if __name__ == "__main__":
    main()
