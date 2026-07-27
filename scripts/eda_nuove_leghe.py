"""Passo 1 del playbook: conoscere le leghe nuove PRIMA di modellare.

Batteria EDA standard del progetto (pattern Fasi 55/79), calcolata sulle 5 leghe
insieme cosi' che Bundesliga e Ligue 1 si leggano SEMPRE per confronto con le
tre gia' studiate. Serve anche come ulteriore validazione dei dati: se una lega
nuova avesse numeri strutturalmente impossibili, si vedrebbe qui.

Indicatori (uno per colonna della tabella finale):
  gol/gara, % esiti H/D/A, Over 2.5, gamma = ln(gol casa / gol ospite),
  Var/Media dei gol (dispersione), delta = ln(gol lega / gol neopromosse),
  correlazione xG-gol, margine del book (chiusura 1X2), e il "deficit-pareggio"
  per quartile di equilibrio (reale - mercato), che dice se la lega e' "latina"
  (mercato che sotto-prezza il pareggio nelle gare equilibrate) o "inglese".

Uso: python scripts/eda_nuove_leghe.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()
from src.evaluation.metrics import devig_1x2  # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "data",
        "ligue_1": ROOT / "data"}


def promoted_delta(df: pd.DataFrame) -> float:
    """delta = ln(gol medi della lega / gol medi delle NEOPROMOSSE).

    Neopromossa = squadra presente in una stagione e assente nella precedente
    (la prima stagione dei dati non ha un "prima": si salta). I gol contati sono
    quelli SEGNATI dalla squadra, in casa e fuori."""
    seasons = sorted(df.season.unique())
    teams = {s: set(df[df.season == s].home_team) | set(df[df.season == s].away_team)
             for s in seasons}
    goals_pro, n_pro = 0.0, 0
    for prev, cur in zip(seasons, seasons[1:]):
        promoted = teams[cur] - teams[prev]
        sdf = df[df.season == cur]
        for t in promoted:
            g = sdf.loc[sdf.home_team == t, "home_goals"].sum() + \
                sdf.loc[sdf.away_team == t, "away_goals"].sum()
            n = (sdf.home_team == t).sum() + (sdf.away_team == t).sum()
            goals_pro += float(g); n_pro += int(n)
    lega = float((df.home_goals + df.away_goals).mean() / 2)   # gol per squadra/gara
    return float(np.log(lega / (goals_pro / n_pro))) if n_pro else float("nan")


def draw_deficit(df: pd.DataFrame) -> dict:
    """Pareggi reali - pareggi prezzati dal mercato, per quartile di equilibrio
    |pH - pA| (devig chiusura). Quartile 1 = gare piu' equilibrate."""
    sub = df.dropna(subset=["odds_home", "odds_draw", "odds_away"]).copy()
    p = np.array([devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in sub.itertuples()])
    sub["p_draw"] = p[:, 1]
    sub["bal"] = np.abs(p[:, 0] - p[:, 2])
    sub["is_draw"] = (sub.result == "D").astype(float)
    q = pd.qcut(sub.bal, 4, labels=["Q1 equilibrate", "Q2", "Q3", "Q4 sbilanciate"])
    out = {}
    for name, g in sub.groupby(q, observed=True):
        out[str(name)] = round(float(g.is_draw.mean() - g.p_draw.mean()), 4)
    return out


def main() -> int:
    rows, extra = [], {}
    for lg, d in SNAP.items():
        df = pd.read_csv(d / f"{lg}_matches.csv", dtype={"season": str},
                         parse_dates=["date"])
        tot = df.home_goals + df.away_goals
        sub = df.dropna(subset=["odds_home", "odds_draw", "odds_away"])
        marg = float((1 / sub.odds_home + 1 / sub.odds_draw + 1 / sub.odds_away).mean() - 1)
        xg_all = pd.concat([df.home_xg, df.away_xg])
        g_all = pd.concat([df.home_goals, df.away_goals]).astype(float)
        ok = xg_all.notna()
        rows.append({
            "lega": lg, "gare": len(df), "stagioni": df.season.nunique(),
            "gol/gara": round(float(tot.mean()), 3),
            "casa%": round(float((df.result == "H").mean()), 3),
            "pari%": round(float((df.result == "D").mean()), 3),
            "ospite%": round(float((df.result == "A").mean()), 3),
            "over2.5%": round(float((tot > 2.5).mean()), 3),
            "gamma": round(float(np.log(df.home_goals.mean() / df.away_goals.mean())), 3),
            "Var/Media": round(float(tot.var() / tot.mean()), 3),
            "delta_promosse": round(promoted_delta(df), 3),
            "corr(xG,gol)": round(float(np.corrcoef(xg_all[ok], g_all[ok])[0, 1]), 3),
            "margine1X2": round(marg, 4),
        })
        extra[lg] = draw_deficit(df)

    tab = pd.DataFrame(rows)
    print("=== EDA: le 5 leghe a confronto (9 stagioni ciascuna, 2017-18 -> 2025-26) ===")
    print(tab.to_string(index=False))
    print("\n=== Deficit-pareggio (reale - prezzato dal mercato) per quartile di equilibrio ===")
    dd = pd.DataFrame(extra).T
    print(dd.to_string())
    print("\nLettura: valore POSITIVO in Q1 = il mercato SOTTO-prezza il pareggio nelle")
    print("gare equilibrate (il 'deficit latino' che la phi(|lam-mu|) della Fase 35 corregge).")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "eda_5_leghe.json").write_text(json.dumps(
        {"tabella": rows, "deficit_pareggio": extra}, indent=2))
    print(f"\n-> {(OUT / 'eda_5_leghe.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
