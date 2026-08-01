#!/usr/bin/env python3
"""Versa `esiti.jsonl` (file di lavoro) nel deliverable versionato.

`esiti.jsonl` serve alla **resumabilita'** della raccolta e cresce fino a ~80 MB
su 29.530 giocatori: troppo per un repo che ne pesa 68 in tutto, ed e' comunque
un formato di lavoro. Questo script ne estrae le tappe in un CSV compresso
(`tappe.csv.gz`) piu' un riepilogo degli esiti, entrambi versionati.

    python scripts/export_wikipedia_careers.py

⚖️ L'output e' CC BY-SA 4.0: vedi data/carriere_wikipedia/README.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import wikipedia_careers as W  # noqa: E402

ESITI = W.OUT_DIR / "esiti.jsonl"
TAPPE = W.OUT_DIR / "tappe.csv.gz"
RIEPILOGO = W.OUT_DIR / "esiti_riepilogo.csv"


def main() -> int:
    if not ESITI.exists():
        print(f"{ESITI} non esiste: eseguire prima fetch_wikipedia_careers.py")
        return 1

    tappe, esiti = [], []
    with ESITI.open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except json.JSONDecodeError:
                continue                      # riga tronca da un'interruzione
            esiti.append({k: r.get(k) for k in
                          ("player_id", "nome", "nostro", "censurato", "stato",
                           "url", "identita", "bday_pagina", "nascita_attesa")})
            # ⚠️ Le tappe di una pagina la cui identita' NON e' confermata sono
            # la carriera di un'altra persona: restano in esiti.jsonl (servono a
            # sapere CHI era) ma non entrano nel deliverable.
            if r.get("stato") == "ok":
                tappe.extend(r.get("tappe", []))

    df = pd.DataFrame(tappe)
    df.to_csv(TAPPE, index=False, compression="gzip")
    ri = pd.DataFrame(esiti)
    ri.to_csv(RIEPILOGO, index=False)

    print(f"tappe:     {len(df):,} righe -> {TAPPE} ({TAPPE.stat().st_size/1e6:.1f} MB)")
    print(f"esiti:     {len(ri):,} giocatori tentati -> {RIEPILOGO}")
    resp = int((ri["stato"] == "identita_non_confermata").sum())
    if resp:
        print(f"⚠️  {resp} pagine ESCLUSE: erano di un'altra persona (verifica d'identita')")
    print("\nper stato:")
    for stato, n in ri["stato"].value_counts().items():
        print(f"  {stato:18s} {n:,}")
    if len(df):
        sen = df[~df["giovanili"]]
        print(f"\ntappe senior: {len(sen):,} | giovanili: {len(df)-len(sen):,} "
              f"| prestiti: {int(df['prestito'].sum()):,}")
        pre2012 = sen[sen["anno_a"].notna() & (sen["anno_a"] <= 2012)]
        print(f"tappe invisibili allo strato 1 (finite entro il 2012): {len(pre2012):,}"
              f" per {int(pre2012['presenze'].fillna(0).sum()):,} presenze")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
