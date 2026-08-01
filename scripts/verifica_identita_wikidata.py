#!/usr/bin/env python3
"""Dirime le identità incerte dei giocatori Wikipedia usando **Wikidata**.

USO:
    python scripts/verifica_identita_wikidata.py --limit 20     # prova
    python scripts/verifica_identita_wikidata.py                # tutti i dubbi
    python scripts/verifica_identita_wikidata.py --anche-confermate  # controllo

COSA FA. Prende i giocatori la cui identità **non** è confermata dalla data di
nascita letta nella pagina — `quarantena`, `respinta`, `confermata_club` — e per
ciascuno interroga l'entità Wikidata **della pagina stessa** (il Q-id è inciso
nell'HTML: nessun matching per nome, quindi nessuna nuova omonimia). Confronta
`P569` con la data di nascita attesa e scrive un verdetto.

⚠️ Questo script **non modifica nessun dato**: scrive solo il proprio verdetto in
`data/carriere_wikipedia/verdetti_wikidata.csv.gz`. Applicare i verdetti al
database è un passo separato, che passa dal registro delle correzioni (R3).

È **resumabile**: il file di lavoro `verdetti_wikidata.jsonl` viene riletto a
ogni avvio e i giocatori già decisi si saltano. Gli errori di rete NON si
considerano decisi (stessa regola di `fetch_wikipedia_careers.py`).

⚖️ Wikidata è CC0. Il robots.txt permette `Special:EntityData/*.` — verifica
riga per riga in `src/data/wikidata_identity.py`.
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

from src.data import wikidata_identity as WD  # noqa: E402

OUT_DIR = WD.OUT_DIR
LAVORO = OUT_DIR / "verdetti_wikidata.jsonl"
DELIVERABLE = OUT_DIR / "verdetti_wikidata.csv.gz"
QID = OUT_DIR / "wikidata_qid.csv.gz"

# Le identita' che hanno bisogno di una terza fonte. `confermata_data` no: e'
# gia' decisa dal ramo forte. `non_verificata` nemmeno: sono le pagine senza
# blocco carriera, da cui non abbiamo estratto nulla da verificare.
DA_DIRIMERE = ("quarantena", "respinta", "confermata_club")


def _decisi() -> set[int]:
    """Chi non va ritentato. Un errore di rete non e' una decisione."""
    if not LAVORO.exists():
        return set()
    fatti = set()
    with LAVORO.open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except Exception:
                continue
            if r.get("esito") in ("confermata", "smentita", "indeterminato"):
                fatti.add(r["player_id"])
    return fatti


def _versa() -> None:
    """Rigenera il deliverable versionato dal file di lavoro."""
    if not LAVORO.exists():
        return
    righe = []
    with LAVORO.open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except Exception:
                continue
            r.pop("militanze", None)   # il dettaglio resta nel .jsonl di lavoro
            righe.append(r)
    if not righe:
        return
    df = pd.DataFrame(righe)
    # l'ultimo verdetto per giocatore vince: se lo script e' stato rilanciato
    # dopo una correzione del parser, la riga buona e' la piu' recente
    df = df.drop_duplicates(subset="player_id", keep="last")
    df.sort_values("player_id").to_csv(DELIVERABLE, index=False, compression="gzip")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--anche-confermate", action="store_true",
                    help="verifica ANCHE le identita' gia' confermate dalla data "
                         "(controllo incrociato, ~21.000 richieste)")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    if not QID.exists():
        print(f"manca {QID}: esegui prima l'estrazione dei Q-id", file=sys.stderr)
        return 1
    q = pd.read_csv(QID)

    stati = DA_DIRIMERE + (("confermata_data",) if args.anche_confermate else ())
    da_fare = q[q["identita"].isin(stati) & q["qid"].notna()].copy()

    # la data di nascita ATTESA e la prima presenza vengono dallo strato 1, che
    # e' su player_id: non puo' essere contaminato dall'omonimia
    root = Path(__file__).resolve().parents[1]
    players = pd.read_csv(root / "files" / "player_scores" / "players.csv.gz",
                          usecols=["player_id", "date_of_birth"])
    nascite = players.set_index("player_id")["date_of_birth"]
    da_fare["nascita_attesa"] = da_fare["player_id"].map(nascite)

    from src.data import careers as C
    app = C._load_appearances()
    prima = app.groupby("player_id")["date"].min()
    da_fare["prima_presenza"] = da_fare["player_id"].map(prima)

    decisi = _decisi()
    da_fare = da_fare[~da_fare["player_id"].isin(decisi)]
    if args.limit:
        da_fare = da_fare.head(args.limit)

    print(f"da dirimere: {len(da_fare):,} | gia' decisi: {len(decisi):,}", flush=True)
    if da_fare.empty:
        _versa()
        return 0

    conta: dict[str, int] = {}
    t0 = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with LAVORO.open("a") as out:
        for i, r in enumerate(da_fare.itertuples(), 1):
            try:
                v = WD.verifica(
                    r.player_id, r.qid, r.nascita_attesa, r.identita,
                    prima_presenza=r.prima_presenza, use_cache=not args.no_cache,
                )
                rec = asdict(v)
            except Exception as e:                      # rete: NON e' una decisione
                rec = {"player_id": int(r.player_id), "qid": r.qid,
                       "identita_prima": r.identita, "esito": "errore",
                       "motivo": f"{type(e).__name__}: {e}"}
            conta[rec["esito"]] = conta.get(rec["esito"], 0) + 1
            out.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            out.flush()
            if i % 25 == 0:
                dt = time.monotonic() - t0
                print(f"  {i:,}/{len(da_fare):,} | {dt/i:.2f}s | "
                      + " | ".join(f"{k} {v}" for k, v in sorted(conta.items())),
                      flush=True)

    _versa()
    print("\n=== VERDETTI ===")
    for k, v in sorted(conta.items(), key=lambda x: -x[1]):
        print(f"  {k:16s} {v:,}")
    print(f"  deliverable: {DELIVERABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
