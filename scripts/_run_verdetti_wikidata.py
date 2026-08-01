#!/usr/bin/env python3
"""Legge i verdetti Wikidata e risponde alle tre domande che contano.

USO:  python scripts/_run_verdetti_wikidata.py

1. **Quanti giocatori si recuperano e quanti si perdono**, cioè il bilancio
   concreto sul database: i `respinta` che Wikidata conferma tornano dentro, i
   `quarantena` che Wikidata smentisce escono.

2. **Wikidata è una fonte INDIPENDENTE?** La data attesa viene da Transfermarkt;
   la `bday` della pagina e la `P569` di Wikidata vengono entrambe
   dall'ecosistema Wikimedia. Se le due concordano sempre, una `smentita` non
   dice «è un'altra persona»: dice «Wikimedia e Transfermarkt discordano». La
   domanda va **misurata**, non assunta (R7).

3. **Lo scarto è bimodale?** Uno scarto di dieci anni è un'altra persona; uno
   scarto di due mesi dentro lo stesso anno è quasi certamente la stessa persona
   con una discrepanza di fonte. Trattarli allo stesso modo butterebbe via
   giocatori buoni.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "carriere_wikipedia"


def main() -> int:
    v = pd.read_csv(OUT / "verdetti_wikidata.csv.gz")
    print(f"verdetti: {len(v):,}\n")

    print("=== 1. BILANCIO SUL DATABASE ===")
    tab = pd.crosstab(v["identita_prima"], v["esito"])
    print(tab.to_string(), "\n")

    # le tappe in gioco: quante righe entrano/escono davvero
    tappe_per_gioc: dict[int, int] = {}
    stato_per_gioc: dict[int, str] = {}
    with (OUT / "esiti.jsonl").open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except Exception:
                continue
            tappe_per_gioc[r["player_id"]] = len(r.get("tappe") or [])
            stato_per_gioc[r["player_id"]] = r.get("stato")
    v["n_tappe"] = v["player_id"].map(tappe_per_gioc).fillna(0).astype(int)

    rec = v[(v["identita_prima"] == "respinta") & (v["esito"] == "confermata")]
    pers = v[(v["identita_prima"] == "quarantena") & (v["esito"] == "smentita")]
    conf = v[(v["identita_prima"] == "quarantena") & (v["esito"] == "confermata")]
    print(f"  RECUPERATI (respinta -> confermata):  {len(rec):4,} giocatori, "
          f"{int(rec['n_tappe'].sum()):5,} tappe")
    print(f"  PROMOSSI   (quarantena -> confermata):{len(conf):4,} giocatori, "
          f"{int(conf['n_tappe'].sum()):5,} tappe")
    print(f"  DA TOGLIERE(quarantena -> smentita):  {len(pers):4,} giocatori, "
          f"{int(pers['n_tappe'].sum()):5,} tappe  <-- oggi SONO nel database\n")

    print("=== 2. WIKIDATA E' INDIPENDENTE DALLA PAGINA? ===")
    bday: dict[int, str | None] = {}
    with (OUT / "esiti.jsonl").open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except Exception:
                continue
            bday[r["player_id"]] = r.get("bday_pagina")
    v["bday_pagina"] = v["player_id"].map(bday)
    con_entrambe = v[v["bday_pagina"].notna() & v["nascita_wikidata"].notna()].copy()
    uguali = (con_entrambe["bday_pagina"].str[:10]
              == con_entrambe["nascita_wikidata"].str[:10])
    n, k = len(con_entrambe), int(uguali.sum())
    if n:
        p = k / n
        # intervallo di Wilson: a p vicino a 1 il normale darebbe estremi > 1 (R7)
        import math
        z = 1.96
        den = 1 + z * z / n
        centro = (p + z * z / (2 * n)) / den
        semi = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        print(f"  pagina e Wikidata danno la STESSA data in {k:,}/{n:,} casi "
              f"= {p:.1%}  IC95% [{max(0, centro-semi):.1%}, {min(1, centro+semi):.1%}]")
        if p > 0.95:
            print("  -> NON sono fonti indipendenti: una `smentita` significa")
            print("     «Wikimedia discorda da Transfermarkt», non «e' un'altra persona».")
            print("     Il valore di Wikidata NON e' l'indipendenza: e' che la data")
            print("     e' STRUTTURATA, quindi leggibile dove l'HTML non la dava.")
        else:
            print("  -> le due fonti divergono abbastanza da portare informazione propria.")
    print()

    print("=== 3. LO SCARTO E' BIMODALE? ===")
    s = v.loc[v["esito"] == "smentita", "scarto_giorni"].dropna()
    if len(s):
        fasce = Counter()
        for g in s:
            if g <= 31:
                fasce["<= 1 mese"] += 1
            elif g <= 366:
                fasce["1-12 mesi"] += 1
            elif g <= 3 * 366:
                fasce["1-3 anni"] += 1
            else:
                fasce["> 3 anni"] += 1
        ordine = ["<= 1 mese", "1-12 mesi", "1-3 anni", "> 3 anni"]
        for f in ordine:
            print(f"  {f:12s} {fasce[f]:4,}")
        vicini = fasce["<= 1 mese"] + fasce["1-12 mesi"]
        print(f"\n  mediana {s.median():,.0f} gg | entro l'anno: {vicini:,}/{len(s):,} "
              f"({vicini/len(s):.1%})")
        print("  Le due fasce NON vanno trattate allo stesso modo: sotto l'anno lo")
        print("  scarto e' compatibile con una discrepanza di fonte sulla STESSA")
        print("  persona; sopra i 3 anni e' un'altra persona (il padre, l'omonimo).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
