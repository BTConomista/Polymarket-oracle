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
        season = Path(f).stem.split("_")[-1]
        try:
            d = pd.read_csv(f, encoding="latin-1")
        except Exception:
            d = pd.read_csv(f)
        frames.append(d.assign(league="serie_a", season=season))
    for lg, path in [("premier_league", "files/football_data_premier_league_bundle.json"),
                     ("la_liga", "files/football_data_la_liga_bundle.json")]:
        bundle = json.load(open(path))
        for name, csv_str in bundle.items():
            if not isinstance(csv_str, str):
                continue
            d = pd.read_csv(io.StringIO(csv_str))
            d.columns = [c.lstrip("﻿") for c in d.columns]
            # la chiave e' del tipo "<lega>_<stagione>.csv"
            frames.append(d.assign(league=lg, season=Path(name).stem.split("_")[-1]))
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
        sub = d[need + ["league", "season"]].dropna()
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
                recs.append((r["league"], r["season"], h, mp, mkH, realized))
            except Exception:
                continue
    a = pd.DataFrame(recs, columns=["league", "season", "h", "model_p",
                                    "market_p", "realized"])
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
          "del margine bene quanto il mercato sharp (Tier 2 validato).")

    encompassing(a)


# --------------------------------------------------------------------------- #
# ENCOMPASSING (aggiunto alla Fase 101-bis)
#
# Perche' esiste: la Fase 88 concludeva «e' alpha*=0 su un mercato nuovo (il
# margine)» SENZA aver mai calcolato l'encompassing — l'audit della Fase 101 lo
# ha rilevato e la rettifica (alpha*=1.08) e' stata scritta nel DIARIO e nel
# README, ma restava non ri-derivabile da nessuno script: viola CLAUDE.md
# §2-bis punto 4. Qui il numero diventa riproducibile.
#
# Il modello e' il blend p = k + alpha*(m - k) con k = mercato, m = router:
#   alpha* = mean((y-k)(m-k)) / mean((m-k)^2)      [minimi quadrati, forma chiusa]
# alpha*=0 -> il mercato INGLOBA il modello (Fase 16). Attenzione all'inter-
# pretazione: qui m e' una TRADUZIONE delle stesse quote 1X2+O/U da cui si
# ricava il prezzo, non un previsore indipendente, quindi alpha*>0 non dice
# «battiamo il mercato» — dice solo che le due letture non sono la stessa cosa.
# --------------------------------------------------------------------------- #
def _alpha_star(y, k, m):
    """Coefficiente di encompassing in forma chiusa (nan se il denominatore e' 0)."""
    num = float(np.mean((y - k) * (m - k)))
    den = float(np.mean((m - k) ** 2))
    return num / den if den > 0 else float("nan")


def encompassing(a: pd.DataFrame, B: int = 10000, seed: int = 88) -> None:
    y = a["realized"].to_numpy()
    k = a["market_p"].to_numpy()
    m = a["model_p"].to_numpy()

    alpha = _alpha_star(y, k, m)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(y), (B, len(y)))
    boots = np.array([_alpha_star(y[i], k[i], m[i]) for i in idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    print(f"\nENCOMPASSING in-sample (n={len(y)}): alpha* = {alpha:+.3f} "
          f"IC95 [{lo:+.3f}, {hi:+.3f}] -> "
          f"{'lo zero e ESCLUSO' if lo > 0 else 'lo zero e incluso'}")

    # Walk-forward col protocollo della Fase 16: alpha e' stimato SOLO sulle
    # stagioni precedenti. Due varianti, e la differenza NON e' cosmetica:
    #   pooled=True  -> alpha da tutte le leghe insieme (protocollo PUBBLICATO
    #                   dalla Fase 88/101: e' il numero che sta nel README);
    #   pooled=False -> alpha dalla sola lega valutata.
    # Le due danno Delta di segno opposto (-0.000064 contro +0.000011), en-
    # trambi ampiamente dentro il rumore: e' il promemoria che con un effetto
    # di questa taglia il protocollo di stima pesa quanto il risultato.
    def _wf(pooled: bool):
        rows, esclusi = [], 0
        for s in sorted(a["season"].unique()):
            cur_s = a[a["season"] == s]
            for lg, g in cur_s.groupby("league"):
                past = (a[a["season"] < s] if pooled
                        else a[(a["season"] < s) & (a["league"] == lg)])
                if past.empty:
                    esclusi += len(g)
                    continue
                al = _alpha_star(past["realized"].to_numpy(),
                                 past["market_p"].to_numpy(),
                                 past["model_p"].to_numpy())
                al = 0.0 if not np.isfinite(al) else al
                kk = g["market_p"].to_numpy(); mm = g["model_p"].to_numpy()
                yy = g["realized"].to_numpy()
                blend = kk + al * (mm - kk)
                rows.append((blend - yy) ** 2 - (kk - yy) ** 2)
        return np.concatenate(rows), esclusi

    for pooled in (True, False):
        d, esclusi = _wf(pooled)
        bi = rng.integers(0, len(d), (B, len(d)))
        bd = d[bi].mean(axis=1)
        blo, bhi = np.percentile(bd, [2.5, 97.5])
        eti = "alpha pooled (protocollo pubblicato)" if pooled else "alpha per-lega"
        print(f"ENCOMPASSING walk-forward — {eti}: n={len(d)} fuori campione "
              f"({esclusi} casi della prima stagione esclusi)")
        print(f"  Delta Brier (blend - mercato) = {float(d.mean()):+.6f} "
              f"IC95 [{blo:+.6f}, {bhi:+.6f}]  "
              f"P(Delta<0) = {float((bd < 0).mean()):.2f}")
    print("  Delta<0 = il blend batte il mercato fuori campione; l'IC che "
          "include lo zero = non concluso.")


if __name__ == "__main__":
    main()
