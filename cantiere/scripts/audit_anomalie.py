"""AUDIT avversariale: cercare ATTIVAMENTE dati sbagliati che i controlli
standard non vedono.

L'audit principale (audit_snapshots.py) verifica che lo snapshot corrisponda
alla fonte. Questo script fa la domanda opposta e piu' scomoda: **e se la fonte
stessa fosse sbagliata?** Un numero puo' essere fedelmente copiato dal
provider ed essere comunque impossibile.

Controlli (ognuno con la sua soglia motivata):

  1. MARGINE IMPOSSIBILE — il guard di produzione (`loader._pick_market_odds`,
     Fase 58) scarta solo l'overround < 1 (arbitraggio). Ma anche un overround
     TROPPO ALTO e' impossibile per una media multi-book: un mercato binario
     con 28% di margine non esiste. Scansione di tutte le righe.
  2. COERENZA TRA MERCATI — l'1X2 e l'O/U della stessa partita descrivono la
     stessa distribuzione di gol. Se la coppia (lambda, mu) che spiega l'1X2 e'
     incompatibile con la linea O/U, uno dei due prezzi e' corrotto.
  3. FISICA — gol > tiri in porta e' possibile solo con autogol; conteggi
     anomali segnalano righe sballate.
  4. IMPRONTE DUPLICATE — la stessa quintupla di quote su partite diverse
     nella stessa giornata e' il sintomo classico di un copia-incolla a monte.
  5. RIPOSO COERENTE — `rest_days_full` non puo' essere MAGGIORE del riposo
     calcolato sulle sole partite di campionato (aggiungere coppe puo' solo
     accorciare la pausa).
  6. xG IMPOSSIBILE — xG negativo, o gol molto sopra/sotto l'xG oltre i limiti
     fisici plausibili.

Uso: python cantiere/scripts/audit_anomalie.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data import sources  # noqa: E402

sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
import nuove_leghe  # noqa: E402

nuove_leghe.registra()
from src.evaluation.metrics import devig_1x2, devig_binary  # noqa: E402
from src.models.market_implied import (  # noqa: E402
    _1x2_over, implied_lambda_mu, score_matrix)

FONTI = ROOT / "cantiere" / "data" / "fonti" / "football_data"
OUT = ROOT / "cantiere" / "out"
LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
SNAP_DIR = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
            "la_liga": ROOT / "data", "bundesliga": ROOT / "cantiere" / "data",
            "ligue_1": ROOT / "cantiere" / "data"}

# Soglie. Il margine di una media multi-book sta storicamente in [1.01, 1.09]
# (misurato: mediana 1.045 sull'1X2, 1.051 sull'O/U). 1.12 e' ~6 deviazioni
# oltre la mediana: oltre quella soglia non e' un book caro, e' un dato rotto.
ORR_MAX_1X2 = 1.12
ORR_MAX_OU = 1.12


def check_margini(df: pd.DataFrame, league: str) -> list[dict]:
    rows = []
    markets = {
        "1X2_chiusura": (["odds_home", "odds_draw", "odds_away"], ORR_MAX_1X2),
        "1X2_apertura": (["odds_home_open", "odds_draw_open", "odds_away_open"], ORR_MAX_1X2),
        "OU_chiusura": (["odds_over25", "odds_under25"], ORR_MAX_OU),
        "OU_apertura": (["odds_over25_open", "odds_under25_open"], ORR_MAX_OU),
    }
    for name, (cols, thr) in markets.items():
        sub = df.dropna(subset=cols)
        orr = (1.0 / sub[cols]).sum(axis=1)
        for i, r in sub[orr > thr].iterrows():
            rows.append({
                "league": league, "mercato": name, "season": r.season,
                "date": str(r.date.date()), "match": f"{r.home_team}-{r.away_team}",
                "overround": round(float(orr[i]), 4),
                "quote": [float(r[c]) for c in cols],
            })
    return rows


def check_coerenza_mercati(df: pd.DataFrame, league: str) -> list[dict]:
    """1X2 e O/U devono descrivere la stessa distribuzione di gol.

    Metodo: si inverte la coppia (1X2, O/U) nei tassi (lambda, mu) col motore
    di produzione (`market_implied.implied_lambda_mu`, rho=-0.06) e si
    ricalcola dalla matrice la P(Over 2.5). L'inversione e' ai minimi quadrati:
    non "fallisce" mai, ma se i due prezzi sono incompatibili NON riesce a
    riprodurli entrambi -> il residuo sull'Over diventa grande. Soglia: 0.03 in
    probabilita' (il residuo tipico di una coppia sana e' <0.005).
    """
    rows = []
    for kind, (c1, c2, c3, co, cu) in {
        "chiusura": ("odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"),
        "apertura": ("odds_home_open", "odds_draw_open", "odds_away_open",
                     "odds_over25_open", "odds_under25_open"),
    }.items():
        sub = df.dropna(subset=[c1, c2, c3, co, cu])
        for r in sub.itertuples():
            p1, px, p2 = devig_1x2(getattr(r, c1), getattr(r, c2), getattr(r, c3))
            p_over, _ = devig_binary(getattr(r, co), getattr(r, cu))
            lam, mu = implied_lambda_mu(p1, px, p2, p_over, rho=-0.06)
            qH, qD, qA, qO = _1x2_over(score_matrix(lam, mu, -0.06))
            resid = abs(qO - p_over)
            tot = lam + mu
            if resid > 0.03 or not (1.0 < tot < 6.0):
                rows.append({"league": league, "tipo": kind, "season": r.season,
                             "date": str(r.date.date()),
                             "match": f"{r.home_team}-{r.away_team}",
                             "residuo_over": round(float(resid), 4),
                             "totale_implicito": round(float(tot), 3),
                             "p_over_mercato": round(p_over, 4),
                             "p_over_matrice": round(float(qO), 4)})
    return rows


def check_fisica(league: str) -> dict:
    """Gol > tiri in porta (possibile SOLO con autogol) e tiri in porta > tiri."""
    anomalies = []
    n_rows = 0
    for season in sources.SEASONS:
        raw = pd.read_csv(FONTI / f"{league}_{season}.csv", encoding="latin-1")
        raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
        n_rows += len(raw)
        for side, g, st, sh in (("home", "FTHG", "HST", "HS"), ("away", "FTAG", "AST", "AS")):
            if st not in raw or sh not in raw:
                continue
            gt = pd.to_numeric(raw[g], errors="coerce")
            stv = pd.to_numeric(raw[st], errors="coerce")
            shv = pd.to_numeric(raw[sh], errors="coerce")
            bad_gs = raw[(gt > stv) & stv.notna()]
            bad_ss = raw[(stv > shv) & shv.notna()]
            for _, r in bad_gs.iterrows():
                anomalies.append({"league": league, "season": season, "tipo": f"gol>{st}",
                                  "date": r["Date"], "match": f"{r.HomeTeam}-{r.AwayTeam}",
                                  "gol": int(r[g]), "sot": int(r[st])})
            for _, r in bad_ss.iterrows():
                anomalies.append({"league": league, "season": season, "tipo": f"{st}>{sh}",
                                  "date": r["Date"], "match": f"{r.HomeTeam}-{r.AwayTeam}",
                                  "sot": int(r[st]), "shots": int(r[sh])})
    return {"n_rows": n_rows, "anomalies": anomalies}


def check_impronte_duplicate(df: pd.DataFrame, league: str) -> list[dict]:
    """Stessa quintupla di quote su piu' partite nello stesso giorno."""
    cols = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    sub = df.dropna(subset=cols).copy()
    sub["fp"] = sub[cols].round(3).astype(str).agg("|".join, axis=1)
    g = sub.groupby(["date", "fp"]).size()
    out = []
    for (date, fp), n in g[g > 1].items():
        rows = sub[(sub.date == date) & (sub.fp == fp)]
        out.append({"league": league, "date": str(date.date()), "n": int(n),
                    "quote": fp,
                    "match": [f"{r.home_team}-{r.away_team}" for r in rows.itertuples()]})
    return out


def check_riposo(df: pd.DataFrame, league: str) -> list[dict]:
    """rest_days_full <= riposo calcolato sulle sole partite di campionato."""
    long = pd.concat([
        df[["date", "home_team"]].rename(columns={"home_team": "team"}),
        df[["date", "away_team"]].rename(columns={"away_team": "team"}),
    ]).sort_values("date")
    prev = {}
    league_rest = {}
    for r in long.itertuples():
        p = prev.get(r.team)
        league_rest[(r.date, r.team)] = min((r.date - p).days, 14) if p is not None else np.nan
        prev[r.team] = r.date
    bad = []
    for r in df.itertuples():
        for side in ("home", "away"):
            team = getattr(r, f"{side}_team")
            full = getattr(r, f"{side}_rest_days_full")
            lg = league_rest.get((r.date, team), np.nan)
            if pd.notna(lg) and pd.notna(full) and full > lg + 1e-9:
                bad.append({"league": league, "date": str(r.date.date()),
                            "team": team, "rest_full": float(full),
                            "rest_solo_campionato": float(lg)})
    return bad


def check_xg(df: pd.DataFrame, league: str) -> list[dict]:
    """xG IMPOSSIBILE, non solo 'strano'.

    Un xG di ESATTAMENTE 0 e' legittimo solo se la squadra non ha tirato e non
    ha segnato. Se ha segnato (o ha tirato), un xG nullo e' un buco della fonte
    scritto come zero: il modello lo leggerebbe come 'occasioni zero'.
    Il controllo incrocia l'xG (Understat) coi TIRI (football-data), cioe' due
    fonti indipendenti."""
    shots = {}
    for season in sources.SEASONS:
        raw = pd.read_csv(FONTI / f"{league}_{season}.csv", encoding="latin-1")
        raw = raw.dropna(subset=["HomeTeam", "AwayTeam"])
        for r in raw.itertuples():
            k = (season, sources.canonical_team(str(r.HomeTeam).strip()),
                 sources.canonical_team(str(r.AwayTeam).strip()))
            shots[k] = (getattr(r, "HS", float("nan")), getattr(r, "AS", float("nan")))

    bad = []
    for side, idx in (("home", 0), ("away", 1)):
        sub = df[(df[f"{side}_xg"] <= 0)
                 | ((df[f"{side}_goals"] >= 5) & (df[f"{side}_xg"] < 0.5))]
        for r in sub.itertuples():
            sh = shots.get((r.season, r.home_team, r.away_team), (None, None))[idx]
            gol = int(getattr(r, f"{side}_goals"))
            xg = float(getattr(r, f"{side}_xg"))
            impossibile = (xg <= 0) and (gol > 0 or (pd.notna(sh) and sh > 0))
            bad.append({"league": league, "season": r.season,
                        "date": str(r.date.date()),
                        "match": f"{r.home_team}-{r.away_team}", "side": side,
                        "gol": gol, "xg": xg, "tiri": None if sh is None else float(sh),
                        "IMPOSSIBILE": bool(impossibile)})
    return bad


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, list | dict] = {k: [] for k in
                                      ("margini", "coerenza", "fisica", "impronte",
                                       "riposo", "xg")}
    for league in LEAGUES:
        print(f"\n=== {league} ===")
        df = pd.read_csv(SNAP_DIR[league] / f"{league}_matches.csv",
                         dtype={"season": str}, parse_dates=["date"])
        m = check_margini(df, league)
        print(f"  1. margini impossibili (>{ORR_MAX_1X2}): {len(m)}")
        report["margini"] += m
        c = check_coerenza_mercati(df, league)
        print(f"  2. coppie 1X2/OU incoerenti: {len(c)}")
        report["coerenza"] += c
        f = check_fisica(league)
        print(f"  3. anomalie fisiche (gol>tiri in porta, tiri in porta>tiri): "
              f"{len(f['anomalies'])} su {f['n_rows']} righe grezze")
        report["fisica"] += f["anomalies"]
        d = check_impronte_duplicate(df, league)
        print(f"  4. impronte-quota duplicate nello stesso giorno: {len(d)}")
        report["impronte"] += d
        rr = check_riposo(df, league)
        print(f"  5. riposo incoerente col calendario di campionato: {len(rr)}")
        report["riposo"] += rr
        x = check_xg(df, league)
        n_imp = sum(1 for i in x if i["IMPOSSIBILE"])
        print(f"  6. xG a zero/estremi: {len(x)} (di cui IMPOSSIBILI, "
              f"cioe' con gol o tiri: {n_imp})")
        report["xg"] += x

    (OUT / "audit_anomalie.json").write_text(json.dumps(report, indent=2, default=str))
    print("\n=== DETTAGLIO ANOMALIE ===")
    for k, v in report.items():
        if v:
            print(f"\n[{k}] {len(v)} casi:")
            for item in v[:12]:
                print("   ", json.dumps(item, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
