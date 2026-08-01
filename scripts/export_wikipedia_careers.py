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
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import wikipedia_careers as W  # noqa: E402

ESITI = W.OUT_DIR / "esiti.jsonl"
TAPPE = W.OUT_DIR / "tappe.csv.gz"
RIEPILOGO = W.OUT_DIR / "esiti_riepilogo.csv"
VERDETTI = W.OUT_DIR / "verdetti_wikidata.csv.gz"


def _scrivi_atomico(df: pd.DataFrame, destinazione: Path, **kw) -> None:
    """Scrive su un temporaneo e poi rinomina: `os.replace` e' ATOMICO su POSIX.

    Serve davvero, non e' prudenza teorica. La raccolta chiama questo export
    ogni 500 giocatori mentre gira, quindi un lettore concorrente — un
    backtest, `load_wikipedia_careers`, la suite di test — puo' aprire il
    `.csv.gz` a meta' scrittura e trovarci un gzip troncato. E' gia' successo:
    `EOFError` in `gzip.py` durante `pytest`, con il file perfettamente integro
    un secondo dopo.

    E' il caso peggiore di tutti, perche' NON e' riproducibile: dipende da
    quando cade la lettura. Con la rinomina atomica il lettore vede o la
    versione vecchia intera o quella nuova intera, mai niente in mezzo.
    """
    tmp = destinazione.with_suffix(destinazione.suffix + ".tmp")
    df.to_csv(tmp, **kw)
    os.replace(tmp, destinazione)


def _verdetti() -> dict[int, dict]:
    """I verdetti Wikidata per player_id, se la verifica e' stata eseguita.

    E' un arricchimento OPZIONALE: senza il file, l'export si comporta come
    prima. Cosi' chi clona il repo e rifa' solo la raccolta Wikipedia ottiene
    comunque un deliverable coerente, invece di un errore.
    """
    if not VERDETTI.exists():
        return {}
    v = pd.read_csv(VERDETTI)
    return {int(r["player_id"]): r for _, r in v.iterrows()}


def main() -> int:
    if not ESITI.exists():
        print(f"{ESITI} non esiste: eseguire prima fetch_wikipedia_careers.py")
        return 1

    verdetti = _verdetti()
    recuperati = rimossi = 0
    tappe, esiti = [], []
    with ESITI.open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except json.JSONDecodeError:
                continue                      # riga tronca da un'interruzione
            pid = r.get("player_id")
            vd = verdetti.get(pid)
            esiti.append({k: r.get(k) for k in
                          ("player_id", "nome", "nostro", "censurato", "stato",
                           "url", "identita", "bday_pagina", "nascita_attesa")})
            esiti[-1]["identita_wikidata"] = vd["esito"] if vd is not None else None
            esiti[-1]["forma_discrepanza"] = vd["forma"] if vd is not None else None

            # ⚠️ Le tappe di una pagina la cui identita' NON e' confermata sono
            # la carriera di un'altra persona: restano in esiti.jsonl (servono a
            # sapere CHI era) ma non entrano nel deliverable.
            #
            # Il verdetto Wikidata SCAVALCA questa regola in entrambi i sensi,
            # perche' e' misurato meglio: la `bday` dell'HTML e' un ripiego, la
            # `P569` e' un valore tipizzato sulla stessa entita' (nessun
            # matching per nome, quindi nessuna omonimia nuova).
            dentro = r.get("stato") == "ok"
            if vd is not None:
                if vd["esito"] == "confermata":
                    # RECUPERO: la pagina era stata respinta perche' la data
                    # nell'HTML non tornava, ma Wikidata conferma. 17 giocatori.
                    if not dentro:
                        recuperati += 1
                    dentro = True
                elif bool(vd["persona_diversa"]):
                    # RIMOZIONE: forma senza struttura E oltre tre anni. E' una
                    # CONGIUNZIONE, non una soglia sui giorni: cosi' non tocca
                    # Chancel Mbemba (2.191 gg ma stesso giorno e mese: disputa
                    # d'eta' sulla stessa persona) ne' i refusi a ±1 anno.
                    if dentro:
                        rimossi += 1
                    dentro = False

            if dentro:
                for t in r.get("tappe", []):
                    # `identita` deve dire la VERITA' sulla riga che la porta.
                    # Lasciarci scritto «respinta» su una tappa che sta nel
                    # database sarebbe un finto pieno (R6): un valore che
                    # sembra una misura e non lo e' piu', e che tradirebbe
                    # chiunque filtri su quella colonna. Il giudizio originale
                    # non si perde — si sposta in `identita_wikipedia`.
                    t["identita_wikipedia"] = t.get("identita")
                    if vd is not None:
                        t["identita_wikidata"] = vd["esito"]
                        t["forma_discrepanza"] = vd["forma"]
                        if vd["esito"] == "confermata":
                            t["identita"] = "confermata_wikidata"
                    tappe.append(t)

    df = pd.DataFrame(tappe)
    if verdetti:
        print(f"verdetti Wikidata applicati: +{recuperati} giocatori recuperati, "
              f"-{rimossi} rimossi (identita' di un'altra persona)")

    # GUARDIA D'USCITA sull'invariante degli anni. Sta qui, e non solo nel
    # parser, perche' il file di lavoro accumula righe prodotte da versioni
    # diverse del parser lungo una raccolta di ore: una correzione al parser non
    # ripulisce da sola cio' che e' gia' stato scritto. Il deliverable dev'essere
    # coerente comunque.
    # I casi sono REFUSI DELLA FONTE, non del parser: su Wikipedia esistono
    # intervalli rovesciati come «2025–2006» (Miguel Mellado) e «2019–2013»
    # (Luan Scapolan). Si azzera la FINE, non si "corregge" invertendo: l'anno
    # giusto non lo sappiamo, e indovinarlo sarebbe inventare un dato.
    if len(df) and {"anno_da", "anno_a"} <= set(df.columns):
        rovesciate = df["anno_da"].notna() & df["anno_a"].notna() & (df["anno_a"] < df["anno_da"])
        if rovesciate.any():
            print(f"⚠️  {int(rovesciate.sum())} tappe con anno di fine PRIMA dell'inizio "
                  "(refusi della fonte): la fine viene azzerata, non invertita")
            df.loc[rovesciate, "anno_a"] = pd.NA
    _scrivi_atomico(df, TAPPE, index=False, compression="gzip")
    ri = pd.DataFrame(esiti)
    _scrivi_atomico(ri, RIEPILOGO, index=False)

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
