"""Stato del database per la stagione 2025-26 — ogni numero ri-calcolabile.

Nasce da una domanda semplice ("come va il 2025-26?") che ha prodotto un
risultato non ovvio: la colonna delle **assenze stimate** e' piena al 100% ma
**vuota di informazione** da ottobre 2025 in poi. E' il caso R6 (§5-bis del
CLAUDE.md) — il finto pieno — e nessun conteggio di celle non-NaN lo vede,
perche' il valore che la fonte scrive quando non sa nulla e' `0.0`, non `NaN`.

Lo script stampa quattro blocchi, in ordine di quanto contano:

  1. COPERTURA   — partite e riempimento colonna per colonna, 2025-26 contro
                   lo storico 2017-25 (e' qui che il finto pieno NON si vede);
  2. ASSENZE     — la firma della fonte congelata: quante volte il conteggio
                   per squadra SALE. Se la fonte e' viva, salgono ~29% dei
                   passi (nuovi infortuni); se e' ferma, puo' solo scendere;
  3. INCROCIO    — snapshot 2025-26 contro le due raccolte per squadra e per
                   giocatore, e la controprova dei gol a due fonti
                   indipendenti (football-data contro diretta.it);
  4. QUOTE       — overround 1X2 stagione per stagione: dice se le quote sono
                   vere (un book ha margine) e se la loro semantica ha tenuto.

Uso:
    python scripts/_run_stato_2526.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import team_stats  # noqa: E402

LEGHE = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
STAGIONE = "2526"
DATA = Path(__file__).resolve().parents[1] / "data"


def _snapshot_completo() -> pd.DataFrame:
    """I cinque snapshot in un frame solo, con la colonna `_lega`."""
    frames = []
    for lega in LEGHE:
        df = pd.read_csv(DATA / f"{lega}_matches.csv")
        df["_lega"] = lega
        frames.append(df)
    tutto = pd.concat(frames, ignore_index=True)
    tutto["season"] = tutto["season"].astype(str)
    tutto["date"] = pd.to_datetime(tutto["date"])
    return tutto


def _per_squadra(df: pd.DataFrame, colonna: str) -> pd.DataFrame:
    """Da una riga-partita a due righe-squadra, per la colonna indicata."""
    casa = df[["date", "_lega", "home_team", f"home_{colonna}"]].rename(
        columns={"home_team": "team", f"home_{colonna}": "n"})
    fuori = df[["date", "_lega", "away_team", f"away_{colonna}"]].rename(
        columns={"away_team": "team", f"away_{colonna}": "n"})
    return pd.concat([casa, fuori], ignore_index=True).sort_values("date")


# --------------------------------------------------------------------------
# 1. Copertura
# --------------------------------------------------------------------------
def blocco_copertura(tutto: pd.DataFrame) -> None:
    print("=" * 78)
    print("1. COPERTURA — 2025-26 contro lo storico 2017-25")
    print("=" * 78)
    cur = tutto[tutto.season == STAGIONE]
    old = tutto[tutto.season != STAGIONE]

    print(f"\n{'lega':16s} {'partite':>8s}  {'dal':>10s}  {'al':>10s}")
    for lega in LEGHE:
        d = cur[cur._lega == lega]
        print(f"{lega:16s} {len(d):8d}  {d.date.min():%Y-%m-%d}  {d.date.max():%Y-%m-%d}")
    print(f"{'TOTALE':16s} {len(cur):8d}")

    print(f"\nColonne con un buco dichiarato (NaN) nel 2025-26:")
    vuoto = True
    for c in tutto.columns:
        if c == "_lega":
            continue
        a, b = cur[c].notna().mean() * 100, old[c].notna().mean() * 100
        if a < 100.0:
            print(f"  {c:26s} {a:6.2f}% pieno   (storico {b:6.2f}%)")
            vuoto = False
    if vuoto:
        print("  nessuna")

    print("\n⚠️  Questo blocco NON vede il finto pieno: vedi il blocco 2.")


# --------------------------------------------------------------------------
# 2. Assenze — la firma della fonte congelata
# --------------------------------------------------------------------------
def blocco_assenze(tutto: pd.DataFrame) -> None:
    print("\n" + "=" * 78)
    print("2. ASSENZE STIMATE — la fonte e' viva o e' ferma?")
    print("=" * 78)
    print("\nUna fonte infortuni VIVA fa SALIRE spesso il conteggio per squadra")
    print("(arrivano infortuni nuovi). Una fonte FERMA puo' solo farlo scendere:")
    print("i vecchi infortuni guariscono e nessuno li rimpiazza.\n")

    print(f"{'stagione':10s} {'passi':>7s} {'sale':>7s} {'scende':>7s} "
          f"{'fermo':>7s} {'% sale':>8s} {'% righe a 0':>12s}")
    for s in sorted(tutto.season.unique()):
        d = _per_squadra(tutto[tutto.season == s], "absent_count_est")
        su = giu = fermo = 0
        for _, g in d.groupby(["_lega", "team"]):
            dif = g.n.diff().dropna()
            su += int((dif > 0).sum())
            giu += int((dif < 0).sum())
            fermo += int((dif == 0).sum())
        tot = su + giu + fermo
        zero = (d.n == 0).mean() * 100
        print(f"{s:10s} {tot:7d} {su:7d} {giu:7d} {fermo:7d} "
              f"{su / tot * 100:7.1f}% {zero:11.1f}%")

    print(f"\nDentro il {STAGIONE}, mese per mese:")
    d = _per_squadra(tutto[tutto.season == STAGIONE], "absent_count_est")
    d["mese"] = d.date.dt.to_period("M")
    pezzi = []
    for _, g in d.groupby(["_lega", "team"]):
        g = g.copy()
        g["dif"] = g.n.diff()
        pezzi.append(g.dropna(subset=["dif"]))
    dd = pd.concat(pezzi, ignore_index=True)
    print(f"\n{'mese':10s} {'passi':>7s} {'sale':>7s} {'% sale':>8s} "
          f"{'media assenti':>14s}")
    for mese, g in dd.groupby("mese"):
        media = d[d.mese == mese].n.mean()
        print(f"{str(mese):10s} {len(g):7d} {int((g.dif > 0).sum()):7d} "
              f"{(g.dif > 0).mean() * 100:7.1f}% {media:14.2f}")

    print("\n⚠️  Zero salite da ottobre 2025 = la fonte Transfermarkt e' congelata.")
    print("   La colonna resta PIENA (0.0, non NaN) ma non porta piu' informazione.")
    print("   Non usarla come covariata sul 2025-26: misurerebbe il nulla.")


# --------------------------------------------------------------------------
# 3. Incrocio con le raccolte 2025-26
# --------------------------------------------------------------------------
def blocco_incrocio() -> None:
    print("\n" + "=" * 78)
    print("3. INCROCIO — lo snapshot 2025-26 contro le raccolte dirette")
    print("=" * 78)
    print("\nControprova dei gol a DUE FONTI INDIPENDENTI:")
    print("  football-data (snapshot)  contro  diretta.it (team_stats).")
    print("`gol_dedotti` da' i gol SUBITI, quindi il confronto e' contro i gol")
    print("segnati dall'AVVERSARIO — sbagliare lato qui non da' segnale, da'")
    print("il 74% di righe 'divergenti' che sono solo scambiate.\n")

    print(f"{'lega':16s} {'righe':>7s} {'esatti':>8s} {'scarto -1':>10s} "
          f"{'scarto -2':>10s} {'sovrastime':>11s}")
    tot = esa = m1 = m2 = sov = 0
    for lega in LEGHE:
        t = team_stats.load_team_matches(lega, STAGIONE)
        t = t[t["Periodo"] == "Totale"].copy()
        # join_to_snapshot alza se anche una sola riga resta orfana.
        j = team_stats.join_to_snapshot(t)
        dedotti = team_stats.gol_dedotti(j)
        veri = np.where(j["in_casa"], j["away_goals"], j["home_goals"])
        d = (dedotti - veri).dropna()
        n = len(d)
        e = int((d == 0).sum())
        a1 = int((d == -1).sum())
        a2 = int((d == -2).sum())
        s = int((d > 0).sum())
        print(f"{lega:16s} {n:7d} {e:8d} {a1:10d} {a2:10d} {s:11d}")
        tot += n; esa += e; m1 += a1; m2 += a2; sov += s
    print(f"{'TOTALE':16s} {tot:7d} {esa:8d} {m1:10d} {m2:10d} {sov:11d}")
    print(f"\n  esatti {esa / tot * 100:.1f}%  |  sotto di 1 o 2 "
          f"{(m1 + m2) / tot * 100:.1f}% (autogol: previsti dalla docstring)")
    print(f"  SOVRASTIME: {sov} — la deduzione puo' solo sottostimare, quindi")
    print("  una sola sovrastima sarebbe un difetto vero. Zero = identita' regge.")


# --------------------------------------------------------------------------
# 4. Quote
# --------------------------------------------------------------------------
def blocco_quote(tutto: pd.DataFrame) -> None:
    print("\n" + "=" * 78)
    print("4. QUOTE — sono vere, e la loro semantica ha tenuto?")
    print("=" * 78)
    print("\nUn book ha un margine: overround > 1. Un overround di 1.0000 esatto")
    print("sarebbe una probabilita' travestita da quota, non un prezzo.\n")

    tutto = tutto.copy()
    tutto["ovr"] = (1 / tutto.odds_home + 1 / tutto.odds_draw + 1 / tutto.odds_away)
    print(f"{'stagione':10s} {'overround 1X2':>15s} {'righe a 1.0000':>16s}")
    for s in sorted(tutto.season.unique()):
        d = tutto[tutto.season == s]
        print(f"{s:10s} {d.ovr.mean():15.4f} {int((d.ovr.round(4) == 1.0).sum()):16d}")

    print("\nIl margine mese per mese sul confine fra le due ultime stagioni:")
    d = tutto[tutto.season.isin(["2425", STAGIONE])].copy()
    d["mese"] = d.date.dt.to_period("M")
    g = d.groupby("mese").ovr.agg(["size", "mean"])
    for mese, r in g.iterrows():
        print(f"  {str(mese):10s} {int(r['size']):5d} partite   {r['mean']:.4f}")
    print("\n⚠️  Il salto e' sul CONFINE di stagione, non dentro: i mercati non")
    print("   ri-prezzano il margine nella stessa notte in cinque paesi. Punta a")
    print("   un cambio nel paniere di book dietro `AvgC*`, da verificare alla fonte.")


def main() -> None:
    tutto = _snapshot_completo()
    blocco_copertura(tutto)
    blocco_assenze(tutto)
    blocco_incrocio()
    blocco_quote(tutto)


if __name__ == "__main__":
    main()
