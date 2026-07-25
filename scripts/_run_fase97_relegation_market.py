"""Fase 97 — La nostra RETROCESSIONE contro un prezzo di mercato vero (Smarkets).

PERCHE'. La Fase 95 ha confrontato per la prima volta una nostra stima outright
con un mercato reale, ma solo sul CAMPIONE, perche' Polymarket non quota altro.
La retrocessione era rimasta senza verifica esterna — ed e' il mercato che ci
interessa di piu', per due motivi:
  - e' quello dove il simulatore e' meglio tarato: la Fase 94 ha ADOTTATO li'
    (e solo li') la deriva di forza in-stagione, eterosch. 0.30 promosse /
    0.16 altre, guadagno +0.0095 con IC [+0.0020, +0.0180];
  - e' quello che il modello sbagliava in modo piu' vistoso prima della
    correzione (neopromosse condannate al 54.7% contro un 48.6% reale).

Smarkets lo quota (Polymarket no, in nessuna lega): questo confronto e' quindi
il PRIMO controllo esterno della Fase 94.

LIMITI DICHIARATI (§1.6)
  - i nostri dati finiscono a fine 2025-26: non vediamo il mercato estivo 2026,
    il prezzo Smarkets si'. Uno scarto puo' essere nostro errore o informazione
    che non abbiamo;
  - il libro Smarkets della retrocessione e' PARZIALE (17 esiti su 20 hanno un
    mid a due lati): le altre 3 righe non sono prezzi e restano fuori;
  - e AVERE un mid non basta: su un libro largo il mid non e' un prezzo ma il
    punto medio fra due numeri scollegati. Il Nottingham Forest quota bid 0.1%
    / ask 10.0% -> "mid 5.05%" che non significa niente. Si filtra a
    spread <= 5pp, e si stampano entrambi i conti per non nascondere il taglio;
  - NON e' un test di edge. Senza esito (la stagione non e' giocata) si misura
    l'ACCORDO, non chi ha ragione. Il verdetto e' a maggio 2027.

Uso:
  python scripts/archive_outrights.py            # (prima: serve l'archivio)
  python scripts/_run_fase97_relegation_market.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import LEAGUE_CONFIGS, drift_sd_map          # noqa: E402
from src.data import loader                                  # noqa: E402
from src.models.dixon_coles import DixonColesModel           # noqa: E402
from src.models.season_sim import round_robin, simulate_season  # noqa: E402

HIST = Path("data/outright_snapshots/history.csv")

# Smarkets -> nomi canonici del nostro snapshot Premier. Costruito a mano
# confrontando i 20 nomi Smarkets con i 32 dello storico (non ne resta fuori
# nessuno): senza questa tabella il join fallisce su 18 nomi su 20 e le squadre
# "mancanti" verrebbero silenziosamente escluse dalla simulazione — che per la
# retrocessione vuol dire togliere proprio le favorite.
SMARKETS_TO_OURS = {
    "AFC Bournemouth": "Bournemouth", "Arsenal FC": "Arsenal",
    "Aston Villa": "Aston Villa", "Brentford FC": "Brentford",
    "Brighton & Hove Albion": "Brighton", "Chelsea FC": "Chelsea",
    "Coventry City": "Coventry", "Crystal Palace": "Crystal Palace",
    "Everton FC": "Everton", "Fulham FC": "Fulham", "Hull City": "Hull",
    "Ipswich Town": "Ipswich", "Leeds United": "Leeds",
    "Liverpool FC": "Liverpool", "Manchester City": "Man City",
    "Manchester United": "Man United", "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest", "Sunderland AFC": "Sunderland",
    "Tottenham Hotspur": "Tottenham",
}


def market_rows(league="premier_league", market="relegation") -> pd.DataFrame:
    rows = [r for r in csv.DictReader(open(HIST))
            if r["source"] == "smarkets" and r["league"] == league
            and r["market"] == market and r["prob"]]
    if not rows:
        raise SystemExit("Archivio vuoto: esegui prima scripts/archive_outrights.py")
    last = max(r["snapshot_date"] for r in rows)
    rows = [r for r in rows if r["snapshot_date"] == last]
    df = pd.DataFrame(dict(
        team_market=[r["team"] for r in rows],
        p_market=[float(r["prob"]) for r in rows],
        spread=[float(r["spread"]) if r["spread"] else np.nan for r in rows],
        date=last))
    df["team"] = df["team_market"].map(SMARKETS_TO_OURS)
    unknown = df[df["team"].isna()]["team_market"].tolist()
    if unknown:
        raise SystemExit(f"Nomi Smarkets non mappati: {unknown} — aggiorna "
                         "SMARKETS_TO_OURS invece di lasciarli cadere.")
    return df


def our_probs(teams, league="premier_league", n_sims=20000, seed=96, drift=True):
    cfg = LEAGUE_CONFIGS[league]
    allm = loader.load_league(league)
    allm["date"] = pd.to_datetime(allm["date"])
    as_of = allm["date"].max() + pd.Timedelta(days=1)
    last = str(allm["season"].iloc[-1])
    last_teams = set(allm[allm["season"].astype(str) == last]["home_team"])
    promoted = {t for t in teams if t not in last_teams}
    d = cfg["promoted_prior"]
    model = DixonColesModel(
        half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
        shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
        promoted_prior=(d, d),
    ).fit(allm, as_of_date=as_of, promoted_teams=promoted)
    # deriva ETEROSCHEDASTICA (Fase 94): 0.30 alle promosse, 0.16 alle altre
    sd = drift_sd_map(teams, promoted) if drift else 0.0
    out = simulate_season(model, round_robin(teams), teams, league_key=league,
                          n_sims=n_sims, seed=seed, drift_sd=sd)
    rank, nt = out["rank"], len(teams)
    p = np.array([(rank[:, k] >= nt - 2).mean() for k in range(nt)])
    return pd.Series(p, index=teams), promoted


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-sims", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=96)
    ap.add_argument("--max-spread", type=float, default=0.05,
                    help="scarta i mid con spread piu' largo di cosi' (default 5pp)")
    args = ap.parse_args(argv)

    mk = market_rows()
    teams = sorted(SMARKETS_TO_OURS.values())     # tutte e 20: la classifica
    print(f"### RETROCESSIONE PREMIER 2026-27 — nostra stima vs Smarkets "
          f"({mk['date'].iloc[0]})")
    print(f"    {len(mk)} esiti col mid su 20 quotati; simulazione su tutte e 20\n")

    p_drift, promoted = our_probs(teams, n_sims=args.n_sims, seed=args.seed, drift=True)
    p_flat, _ = our_probs(teams, n_sims=args.n_sims, seed=args.seed, drift=False)
    print(f"  neopromosse (prior δ={LEAGUE_CONFIGS['premier_league']['promoted_prior']}): "
          f"{sorted(promoted)}\n")

    df = mk.merge(p_drift.rename("p_drift"), left_on="team", right_index=True) \
           .merge(p_flat.rename("p_flat"), left_on="team", right_index=True) \
           .sort_values("p_market", ascending=False)

    df["usable"] = df["spread"] <= args.max_spread
    print(f"  {'squadra':<18}{'mercato':>9}{'noi(der.)':>11}{'noi(senza)':>12}"
          f"{'scarto':>9}{'spread':>9}")
    for r in df.itertuples():
        flag = " *" if r.team in promoted else "  "
        flag += "" if r.usable else "  libro largo: mid non significativo"
        print(f"  {r.team:<18}{r.p_market*100:8.1f}%{r.p_drift*100:10.1f}%"
              f"{r.p_flat*100:11.1f}%{(r.p_drift-r.p_market)*100:+8.1f}pp"
              f"{r.spread*100:8.2f}pp{flag}")
    print(f"\n  (* = neopromossa;  {(~df['usable']).sum()} righe scartate per "
          f"spread > {args.max_spread*100:.0f}pp)")

    for tag, sub in (("TUTTI i mid", df), (f"spread <= {args.max_spread*100:.0f}pp",
                                           df[df["usable"]])):
        print(f"\n  --- {tag}  (n={len(sub)}) ---")
        for lbl, col in (("CON deriva (Fase 94)", "p_drift"), ("senza deriva", "p_flat")):
            e = sub[col] - sub["p_market"]
            print(f"  {lbl:22} MAE {e.abs().mean()*100:5.2f}pp   "
                  f"corr {sub[col].corr(sub['p_market']):.3f}   "
                  f"somma nostra {sub[col].sum():.2f} vs mercato {sub['p_market'].sum():.2f}")
            pr = sub[sub["team"].isin(promoted)]
            if len(pr):
                print(f"  {'':22} neopromosse: noi {pr[col].mean()*100:.1f}% "
                      f"contro mercato {pr['p_market'].mean()*100:.1f}% "
                      f"({(pr[col].mean()-pr['p_market'].mean())*100:+.1f}pp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
