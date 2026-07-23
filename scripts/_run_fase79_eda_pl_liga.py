"""Fase 79 (EDA) — Studio dedicato di Premier League e La Liga: le dimensioni
che decidono i PROSSIMI test per-lega.

La Fase 55 ha fotografato le tre leghe sulle dimensioni portanti della Serie A
(gamma, delta, dispersione, margine). Qui si scende di un livello, sulle TRE
dimensioni che motivano le prime leve per-lega mai testate (PANCHINA ✱2 e #9/#12):

  1. STRUTTURA DEL PAREGGIO vs EQUILIBRIO — il pareggio nelle partite
     equilibrate (|pH−pA| devig piccolo) e' il territorio della φ35 (Fase 35).
     In Serie A: pareggi reali > mercato nelle equilibrate (draw-bias). La
     Fase 53 dice che il mercato Premier SOVRA-prezza i pareggi (w_D=0.93):
     qui misuriamo la frequenza REALE per fascia di equilibrio, per capire se
     una φ35 per-lega avrebbe qualcosa da correggere (e con che segno).
  2. CONGESTIONE — distribuzione del riposo vero (rest_days_full, Fase 59) e
     della dummy midweek_europe per lega, con i tassi-gol e gli esiti nelle
     partite a riposo corto. La Premier (niente pausa invernale, Boxing Day)
     dovrebbe essere la lega piu' congestionata: se l'effetto descrittivo
     esiste, il test della covariata (mai fatto fuori Serie A) ha senso.
  3. VANTAGGIO-CASA NEL TEMPO — gamma_t per stagione: quanto e' stabile il
     vantaggio-casa per lega (crollo COVID e recupero)? Il DC lo fitta da
     solo, ma la sua VARIABILITA' dice quanto il fit "insegue" (Fase 47/48
     hanno chiuso il dinamico in Serie A; qui solo descrittivo).

Solo pandas sugli snapshot congelati: nessun backtest, nessuna rete.
Registra un run per lega (source=fase79_eda_pl_liga).

Uso:  python scripts/_run_fase79_eda_pl_liga.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402

LEAGUES = ["serie_a", "premier_league", "la_liga"]   # Serie A = riferimento


def draw_structure(df: pd.DataFrame) -> dict:
    """P(pari) reale vs mercato per fascia di equilibrio |pH−pA| (devig)."""
    P = np.array([metrics.devig_1x2(h, d, a) for h, d, a in
                  df[["odds_home", "odds_draw", "odds_away"]].to_numpy()])
    bal = np.abs(P[:, 0] - P[:, 2])                  # equilibrio di MERCATO
    is_draw = (df["result"] == "D").to_numpy(float)
    out = {}
    q = pd.qcut(pd.Series(bal), 4, labels=["equil", "medio-b", "medio-a", "sbil"])
    for lab in ["equil", "medio-b", "medio-a", "sbil"]:
        m = (q == lab).to_numpy()
        out[lab] = {"n": int(m.sum()),
                    "reale": float(is_draw[m].mean()),
                    "mercato": float(P[m, 1].mean()),
                    "gap": float(is_draw[m].mean() - P[m, 1].mean())}
    return out


def congestion(df: pd.DataFrame) -> dict:
    """Riposo corto e midweek europeo: quota e effetto descrittivo sui gol."""
    out = {}
    rows = []
    for side in ["home", "away"]:
        rest = df[f"{side}_rest_days_full"]
        rows.append({
            "lato": side,
            "riposo_mediano": float(rest.median()),
            "quota_riposo<=3g": float((rest <= 3).mean()),
            "quota_riposo<=4g": float((rest <= 4).mean()),
            "quota_midweek_eu": float(df[f"{side}_midweek_europe"].mean()),
            "gol_riposo<=3g": float(df.loc[rest <= 3, f"{side}_goals"].mean()),
            "gol_riposo>3g": float(df.loc[rest > 3, f"{side}_goals"].mean()),
            "gol_dopo_midweek": float(
                df.loc[df[f"{side}_midweek_europe"] == 1, f"{side}_goals"].mean()),
            "gol_no_midweek": float(
                df.loc[df[f"{side}_midweek_europe"] == 0, f"{side}_goals"].mean()),
        })
        out[side] = rows[-1]
    # dicembre (Boxing Day inglese): quota di partite a riposo corto nel mese
    dec = df[df["date"].dt.month == 12]
    out["dicembre_riposo<=3g"] = float((dec["home_rest_days_full"] <= 3).mean())
    return out


def gamma_by_season(df: pd.DataFrame) -> dict:
    """gamma_t = ln(gol casa / gol ospite) per stagione (crollo COVID e dopo)."""
    out = {}
    for s, g in df.groupby(df["season"].astype(str)):
        out[s] = float(np.log(g["home_goals"].mean() / g["away_goals"].mean()))
    return out


def main() -> None:
    print("=" * 92)
    print("FASE 79 (EDA) — struttura pareggio / congestione / gamma_t, per lega")
    print("=" * 92)
    for lg in LEAGUES:
        df = loader.load_league(lg)
        df = df[np.isfinite(df[["odds_home", "odds_draw", "odds_away"]]).all(axis=1)]
        print(f"\n### {lg}  (n={len(df)})")

        ds = draw_structure(df)
        print("  P(pari) per fascia di equilibrio |pH-pA| del mercato "
              "(gap = reale - mercato):")
        print(f"    {'fascia':<9}{'n':>6}{'reale':>8}{'mercato':>9}{'gap':>8}")
        for lab, v in ds.items():
            print(f"    {lab:<9}{v['n']:>6}{v['reale']:>8.3f}"
                  f"{v['mercato']:>9.3f}{v['gap']:>+8.3f}")

        cg = congestion(df)
        print("  Congestione (calendario completo di club, Fase 59):")
        for side in ["home", "away"]:
            c = cg[side]
            print(f"    {side:<5} riposo mediano {c['riposo_mediano']:.0f}g | "
                  f"<=3g {c['quota_riposo<=3g']:.1%} | midweek-EU "
                  f"{c['quota_midweek_eu']:.1%} | gol <=3g "
                  f"{c['gol_riposo<=3g']:.2f} vs >3g {c['gol_riposo>3g']:.2f} | "
                  f"gol dopo-midweek {c['gol_dopo_midweek']:.2f} vs "
                  f"{c['gol_no_midweek']:.2f}")
        print(f"    dicembre: partite con riposo <=3g = "
              f"{cg['dicembre_riposo<=3g']:.1%}")

        gt = gamma_by_season(df)
        print("  gamma_t per stagione: " + "  ".join(
            f"{s}:{v:+.2f}" for s, v in gt.items()))

        rec = experiment_log.make_record(
            {"source": "fase79_eda_pl_liga", "league": lg},
            {"n_matches": int(len(df)),
             "draw_structure": ds,
             "congestion": {k: v for k, v in cg.items()},
             "gamma_by_season": gt},
            experiment_log.data_fingerprint(df))
        experiment_log.append_run(rec)
    print("\nRun registrati in experiments/runs.jsonl (source=fase79_eda_pl_liga).")


if __name__ == "__main__":
    main()
