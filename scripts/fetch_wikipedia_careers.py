#!/usr/bin/env python3
"""Raccoglie le carriere dall'infobox di Wikipedia — strato 2 del database.

USO:
    python scripts/fetch_wikipedia_careers.py --limit 50        # prova
    python scripts/fetch_wikipedia_careers.py                   # tutti
    python scripts/fetch_wikipedia_careers.py --solo-popolazione # i nostri 7.709

E' **RESUMABILE**: ogni giocatore viene scritto su `esiti.jsonl` appena
finito, e un nuovo avvio salta chi c'e' gia'. Un'interruzione non perde nulla e
non fa riscaricare nulla (c'e' anche la cache HTML su disco). Serve, perche' a
un secondo per pagina i 29.531 giocatori sono ~8 ore.

ORDINE DI PRIORITA' (chi da' piu' informazione per primo, cosi' un'esecuzione
parziale e' comunque utile):
  1. i giocatori delle NOSTRE 5 leghe **censurati** al bordo del dataset —
     quelli per cui lo strato 1 e' un limite inferiore, non una misura;
  2. il resto della nostra popolazione;
  3. tutti gli altri.

Registra anche gli ESITI NEGATIVI (principio §1.4 del CLAUDE.md): senza, la
sessione dopo ritenta gli stessi fallimenti.

⚖️ L'output e' CC BY-SA 4.0 (contenuto Wikipedia). Vedi
`src/data/wikipedia_careers.py` e `data/carriere_wikipedia/README.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import careers as C  # noqa: E402
from src.data import wikipedia_careers as W  # noqa: E402

OUT_DIR = W.OUT_DIR
ESITI = OUT_DIR / "esiti.jsonl"

# Suffissi da provare quando il nome nudo non da' una pagina utile. L'ordine
# conta: si prova il piu' specifico per ultimo, per non agganciare un omonimo.
SUFFISSI = ("", " (footballer)", " (soccer)")


def elenco_giocatori(solo_popolazione: bool) -> pd.DataFrame:
    app = C._load_appearances()
    pop = set(C.population(app))
    prima = app.groupby("player_id")["date"].min()
    presenze = app.groupby("player_id").size()

    players = pd.read_csv(
        W.ROOT / "files" / "player_scores" / "players.csv.gz",
        usecols=["player_id", "name", "date_of_birth", "country_of_citizenship"],
    )
    players = players[players["player_id"].isin(presenze.index)].copy()
    players["prima_presenza"] = players["player_id"].map(prima)
    players["presenze"] = players["player_id"].map(presenze)
    players["nostro"] = players["player_id"].isin(pop)
    players["censurato"] = players["prima_presenza"] <= C.CENSORING_CUTOFF

    if solo_popolazione:
        players = players[players["nostro"]]

    # priorita': censurati nostri -> nostri -> altri; e dentro ogni gruppo
    # prima chi ha giocato di piu' (piu' informazione per pagina scaricata)
    players["priorita"] = (
        (~(players["nostro"] & players["censurato"])).astype(int) * 2
        + (~players["nostro"]).astype(int)
    )
    return players.sort_values(
        ["priorita", "presenze"], ascending=[True, False]
    ).reset_index(drop=True)


def gia_fatti() -> set[int]:
    if not ESITI.exists():
        return set()
    fatti = set()
    with ESITI.open() as f:
        for riga in f:
            try:
                fatti.add(json.loads(riga)["player_id"])
            except Exception:
                continue
    return fatti


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="quanti giocatori")
    ap.add_argument("--solo-popolazione", action="store_true",
                    help="solo i 7.709 delle nostre 5 leghe")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    elenco = elenco_giocatori(args.solo_popolazione)
    fatti = gia_fatti()
    da_fare = elenco[~elenco["player_id"].isin(fatti)]
    if args.limit:
        da_fare = da_fare.head(args.limit)

    print(f"giocatori in elenco: {len(elenco):,} | gia' fatti: {len(fatti):,} "
          f"| da fare ora: {len(da_fare):,}", flush=True)

    conta = {"ok": 0, "nessuna_pagina": 0, "nessun_infobox": 0,
             "nessun_blocco": 0, "errore": 0}
    t0 = time.monotonic()

    with ESITI.open("a") as out:
        for i, r in enumerate(da_fare.itertuples(), 1):
            esito = None
            for suff in SUFFISSI:
                e = W.fetch_player(r.player_id, f"{r.name}{suff}",
                                   use_cache=not args.no_cache)
                if e.stato == "ok":
                    esito = e
                    break
                if esito is None or e.stato != "nessuna_pagina":
                    esito = e
            conta[esito.stato] = conta.get(esito.stato, 0) + 1
            out.write(json.dumps({
                "player_id": int(r.player_id), "nome": r.name,
                "nostro": bool(r.nostro), "censurato": bool(r.censurato),
                "stato": esito.stato, "url": esito.url,
                "dettaglio": esito.dettaglio,
                "tappe": [asdict(t) for t in esito.tappe],
            }, ensure_ascii=False) + "\n")
            out.flush()

            if i % 25 == 0:
                dt = time.monotonic() - t0
                print(f"  {i:,}/{len(da_fare):,} | {dt/i:.2f}s/giocatore | "
                      f"ok {conta['ok']:,} | senza pagina {conta['nessuna_pagina']:,} | "
                      f"senza blocco {conta['nessun_blocco']:,}", flush=True)

    print("\n=== ESITO ===")
    for k, v in sorted(conta.items(), key=lambda x: -x[1]):
        if v:
            print(f"  {k:18s} {v:,}")
    print(f"  registrati in {ESITI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
