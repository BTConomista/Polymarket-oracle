"""Fase 93 — DOVE si concentra il deficit di discriminazione (la domanda giusta).

La Fase 92 ha stabilito che l'88% del gap col mercato sta nella DISCRIMINAZIONE
casa/ospite, non nella massa del pareggio (Premier 94.5%, Liga 85%). Questa fase
costruisce il dato per rispondere alla domanda successiva: **su quali partite**
perdiamo quel termine?

Il deficit per partita. Dalla chain rule (Fase 92), il termine di
discriminazione di una partita NON pareggiata vale:

    c_i = -log( P(esito_i) / (1 - P_i(X)) )

cioe' il log-loss del binario "casa vs ospite" CONDIZIONATO al fatto che non sia
pareggio. Il deficit e' la differenza fra modello e mercato:

    deficit_i = c_i(modello) - c_i(mercato)

Positivo = il mercato ha fatto meglio su quella partita. La media dei deficit
(divisa per TUTTE le partite, pareggi inclusi) e' esattamente il termine di
discriminazione del gap.

Questo script produce il DATASET (una riga per partita non pareggiata, con le
covariate per affettarlo) e le prime affettature. Le domande a cui serve
rispondere: il deficit e' uniforme (informazione irriducibile) o concentrato?
Sulle partite equilibrate o sui mismatch? A inizio o a fine stagione? Su squadre
specifiche? Sulle neopromosse? Quando il mercato e il modello DISSENTONO?

Uso:
  python scripts/_run_fase93_discrimination.py                 # 3 leghe, 6 stagioni
  python scripts/_run_fase93_discrimination.py --league serie_a
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import league_config              # noqa: E402
from src.data import loader                       # noqa: E402
from src.evaluation import metrics                # noqa: E402
from src.models import market_implied as mi       # noqa: E402
from scripts.backtest import run_backtest         # noqa: E402

LEAGUES = ("serie_a", "premier_league", "la_liga")
SEASONS = ("2021", "2122", "2223", "2324", "2425", "2526")


def build(league: str, seasons) -> pd.DataFrame:
    cfg = league_config(league)
    d = pd.concat([run_backtest(league, S, cfg["half_life_days"],
                                shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                                blend_signal=cfg["blend_signal"],
                                promoted_prior=(cfg["promoted_prior"],) * 2, verbose=False)
                   for S in seasons], ignore_index=True)
    d = d.dropna(subset=["odds_home", "odds_draw", "odds_away"]).reset_index(drop=True)

    K = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in d.itertuples()])
    d["k_home"], d["k_draw"], d["k_away"] = K[:, 0], K[:, 1], K[:, 2]

    # condizionali casa/ospite dato NON pareggio
    d["m_home_c"] = d["m_home"] / (1 - d["m_draw"])
    d["k_home_c"] = d["k_home"] / (1 - d["k_draw"])

    nd = d[d["result"] != "D"].copy()
    won_home = (nd["result"] == "H").astype(float)
    nd["c_model"] = -np.log(np.where(won_home == 1, nd["m_home_c"], 1 - nd["m_home_c"]))
    nd["c_market"] = -np.log(np.where(won_home == 1, nd["k_home_c"], 1 - nd["k_home_c"]))
    nd["deficit"] = nd["c_model"] - nd["c_market"]
    nd["home_won"] = won_home

    # covariate per affettare
    nd["imbalance_model"] = (nd["m_home_c"] - 0.5).abs() * 2      # 0 = incerta, 1 = certa
    nd["imbalance_market"] = (nd["k_home_c"] - 0.5).abs() * 2
    nd["disagreement"] = (nd["m_home_c"] - nd["k_home_c"])        # segno: + = piu' pro-casa di loro
    nd["abs_disagreement"] = nd["disagreement"].abs()
    nd["favourite_agree"] = ((nd["m_home_c"] > .5) == (nd["k_home_c"] > .5))
    nd["league"] = league
    nd["date"] = pd.to_datetime(nd["date"])
    nd["month"] = nd["date"].dt.month
    # giornata approssimata: ordine cronologico dentro la stagione / 10 partite
    nd["matchday"] = nd.groupby("season")["date"].rank(method="dense").astype(int)
    return nd


def slices(nd: pd.DataFrame) -> dict:
    n_all = len(nd)
    out = {}
    print(f"\n{'='*78}\n### DEFICIT DI DISCRIMINAZIONE — {n_all} partite non pareggiate")
    print(f"  deficit medio: {nd['deficit'].mean():+.5f}   "
          f"(mediana {nd['deficit'].median():+.5f})")
    pos = (nd["deficit"] > 0).mean()
    print(f"  partite in cui il mercato fa meglio: {pos*100:.1f}%")

    def show(name, groups):
        print(f"\n  {name}")
        rows = []
        for lab, sub in groups:
            if len(sub) < 30:
                continue
            share = sub["deficit"].sum() / nd["deficit"].sum() if nd["deficit"].sum() else np.nan
            print(f"    {lab:28} n={len(sub):5d} ({len(sub)/n_all*100:4.1f}%)  "
                  f"deficit medio {sub['deficit'].mean():+.5f}  "
                  f"quota del totale {share*100:5.1f}%")
            rows.append(dict(label=lab, n=int(len(sub)),
                             mean=float(sub["deficit"].mean()), share=float(share)))
        out[name] = rows

    q = nd["imbalance_market"]
    show("per SQUILIBRIO atteso (dal mercato)", [
        (f"equilibrata (<{q.quantile(.33):.2f})", nd[q <= q.quantile(.33)]),
        ("intermedia", nd[(q > q.quantile(.33)) & (q <= q.quantile(.66))]),
        (f"mismatch (>{q.quantile(.66):.2f})", nd[q > q.quantile(.66)]),
    ])
    a = nd["abs_disagreement"]
    show("per DISACCORDO modello-mercato", [
        ("accordo stretto (<33%)", nd[a <= a.quantile(.33)]),
        ("intermedio", nd[(a > a.quantile(.33)) & (a <= a.quantile(.66))]),
        ("disaccordo forte (>66%)", nd[a > a.quantile(.66)]),
    ])
    show("per CHI HA VINTO", [
        ("ha vinto la CASA", nd[nd["home_won"] == 1]),
        ("ha vinto l'OSPITE", nd[nd["home_won"] == 0]),
    ])
    show("per FASE DELLA STAGIONE", [
        ("prime 10 giornate", nd[nd["matchday"] <= 10]),
        ("giornate 11-28", nd[(nd["matchday"] > 10) & (nd["matchday"] <= 28)]),
        ("ultime 10 giornate", nd[nd["matchday"] > 28]),
    ])
    show("per LEGA", [(lg, nd[nd["league"] == lg]) for lg in nd["league"].unique()])
    show("per STAGIONE", [(s, nd[nd["season"] == s]) for s in sorted(nd["season"].unique())])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--league", nargs="*", default=list(LEAGUES))
    ap.add_argument("--seasons", nargs="*", default=list(SEASONS))
    args = ap.parse_args(argv)

    nd = pd.concat([build(lg, args.seasons) for lg in args.league], ignore_index=True)
    out = slices(nd)

    cols = ["league", "season", "date", "home_team", "away_team", "result",
            "m_home_c", "k_home_c", "c_model", "c_market", "deficit", "home_won",
            "imbalance_model", "imbalance_market", "disagreement",
            "abs_disagreement", "favourite_agree", "matchday", "month",
            "m_home", "m_draw", "m_away", "k_home", "k_draw", "k_away"]
    dest = Path("experiments/fase93_discrimination.csv")
    nd[cols].to_csv(dest, index=False)
    Path("experiments/fase93_discrimination.json").write_text(json.dumps(out, indent=2))
    print(f"\nDataset scritto in {dest} ({len(nd)} righe)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
