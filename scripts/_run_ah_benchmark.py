"""Fase 88 — Handicap asiatico come benchmark Tier 2: il router prezza la famiglia
margine/scarto come il mercato sharp?

L'AH e' ridondante come INPUT dell'inversione (corr 0.995 con lambda-mu, Fase 86),
ma e' l'unico mercato QUOTATO e sharp (Pinnacle, vig ~2.7%) sulla coda del
MARGINE. Qui non lo si usa per stimare: lo si usa per VALIDARE la calibrazione del
router sulla famiglia-margine (handicap, scarto>=2) contro un prezzo esterno.

Metodo (per ogni partita con chiusura 1X2+O/U+AH, 3 leghe):
 1. inverti 1X2+O/U -> lambda,mu (rho=-0.06) e costruisci la matrice del router
    (double-Poisson theta=1.225);
 2. dalla matrice: P(la casa COPRE la linea AH) come frazione-di-copertura attesa
    (gestisce linee intere/mezze/quarti: push=0.5, quarto=0.25/0.75);
 3. dal mercato: devig delle due quote AH (Pinnacle di chiusura se presente, else
    media di chiusura) -> P(casa copre) del mercato;
 4. confronto: correlazione modello-mercato, Brier di ciascuno vs la copertura
    REALIZZata, e calibrazione (media P vs media realizzata).

Se Brier(modello) ~ Brier(mercato) e corr alta, il router prezza la coda del
margine bene quanto il mercato sharp (sotto il tetto alpha*=0).

NON registra run (diagnostico). Uso: python scripts/_run_ah_benchmark.py
"""
from __future__ import annotations

import io
import json
import sys
import glob
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import metrics                 # noqa: E402
from src.models import market_implied as mi        # noqa: E402

K = 20   # supporto ampio per il margine
RHO = -0.06
THETA = 1.225


def _col(d, *names):
    for n in names:
        if n in d.columns:
            return n
    return None


def load_raw() -> pd.DataFrame:
    """Righe football-data grezze per le 3 leghe (Serie A da CSV, PL/Liga dai
    bundle JSON che contengono i CSV come stringhe)."""
    frames = []
    for f in sorted(glob.glob("data/football_data_raw/serie_a_*.csv")):
        try:
            frames.append(pd.read_csv(f, encoding="latin-1").assign(league="serie_a"))
        except Exception:
            frames.append(pd.read_csv(f).assign(league="serie_a"))
    for lg, path in [("premier_league", "files/football_data_premier_league_bundle.json"),
                     ("la_liga", "files/football_data_la_liga_bundle.json")]:
        bundle = json.load(open(path))
        for _, csv_str in bundle.items():
            if not isinstance(csv_str, str):
                continue
            d = pd.read_csv(io.StringIO(csv_str))
            d.columns = [c.lstrip("﻿") for c in d.columns]
            frames.append(d.assign(league=lg))
    return frames


def cover_fraction(margin: int, h: float) -> float:
    """Frazione di stake vinta dalla casa con linea handicap h (prospettiva casa)."""
    adj = margin + h
    if adj >= 0.5:
        return 1.0
    if abs(adj - 0.25) < 1e-9:
        return 0.75
    if abs(adj) < 1e-9:
        return 0.5
    if abs(adj + 0.25) < 1e-9:
        return 0.25
    return 0.0


def model_cover(lam: float, mu: float, h: float) -> float:
    """P(casa copre) = E[frazione di copertura] sotto la matrice del router."""
    M = mi.score_matrix(lam, mu, rho=RHO, dp_theta=THETA)
    kk = M.shape[0]
    p = 0.0
    for i in range(kk):
        for j in range(kk):
            p += M[i, j] * cover_fraction(i - j, h)
    return p


def main():
    frames = load_raw()
    recs = []
    for d in frames:
        cH = _col(d, "AvgCH", "PSCH"); cD = _col(d, "AvgCD", "PSCD"); cA = _col(d, "AvgCA", "PSCA")
        cO = _col(d, "AvgC>2.5", "PC>2.5"); cU = _col(d, "AvgC<2.5", "PC<2.5")
        cLine = _col(d, "AHCh", "BbAHh")
        # prezzi AH di chiusura: Pinnacle se c'e', else media
        cAHH = _col(d, "PCAHH", "AvgCAHH"); cAHA = _col(d, "PCAHA", "AvgCAHA")
        cFH = _col(d, "FTHG"); cFA = _col(d, "FTAG")
        need = [cH, cD, cA, cO, cU, cLine, cAHH, cAHA, cFH, cFA]
        if not all(need):
            continue
        sub = d[need + ["league"]].dropna()
        for _, r in sub.iterrows():
            try:
                pH, pD, pA = metrics.devig_1x2(r[cH], r[cD], r[cA])
                pO, _ = metrics.devig_binary(r[cO], r[cU])
                lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, rho=RHO)
                h = float(r[cLine])
                mp = model_cover(lam, mu, h)
                # mercato: devig delle due quote AH
                mkH, _ = metrics.devig_binary(r[cAHH], r[cAHA])
                margin = int(r[cFH] - r[cFA])
                realized = cover_fraction(margin, h)
                recs.append((r["league"], h, mp, mkH, realized))
            except Exception:
                continue
    a = pd.DataFrame(recs, columns=["league", "h", "model_p", "market_p", "realized"])
    print(f"Partite con 1X2+O/U+AH di chiusura: {len(a)}")
    print(f"\n{'lega':>14} {'n':>6} {'corr(mod,mkt)':>14} "
          f"{'Brier mod':>10} {'Brier mkt':>10} {'cal mod':>9} {'cal mkt':>9} {'reale':>7}")

    def block(sub, name):
        mp = sub["model_p"].to_numpy(); mk = sub["market_p"].to_numpy(); y = sub["realized"].to_numpy()
        corr = np.corrcoef(mp, mk)[0, 1]
        bm = float(((mp - y) ** 2).mean()); bk = float(((mk - y) ** 2).mean())
        print(f"{name:>14} {len(sub):>6} {corr:>14.4f} {bm:>10.4f} {bk:>10.4f} "
              f"{mp.mean():>9.4f} {mk.mean():>9.4f} {y.mean():>7.4f}")

    for lg in ["serie_a", "premier_league", "la_liga"]:
        block(a[a["league"] == lg], lg)
    block(a, "TUTTE")
    print("\nLettura: corr alta + Brier(mod)~Brier(mkt) = il router prezza la coda "
          "del margine bene quanto il mercato sharp (Tier 2 validato, sotto alpha*=0).")


if __name__ == "__main__":
    main()
