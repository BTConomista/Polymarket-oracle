"""Il REGISTRO degli incarichi verificati: chi era davvero in panchina (Fase 141).

COS'E'. Una riga per ogni nostro mandato, con la risposta alla domanda «chi era
in carica in quel momento» e **da dove viene** quella risposta. Mette insieme le
due verifiche:

  1. il **confronto automatico** con Wikidata (`confronto.csv`) — struttura,
     date tipizzate, Q-id;
  2. la **verifica caso per caso** del residuo (esito del workflow) — ricerca
     esterna con fonti, e uno scettico incaricato di refutarla.

COSA NON E'. **Non è una correzione ai dati** (regola R3): non tocca
`games.csv` né gli snapshot, e nessun modello lo legge di nascosto. È un
registro dichiarato, affiancato al dato, che dice cosa dice un'altra fonte —
e dove le due non concordano lo scrive invece di scegliere.

⚠️ LA COLONNA CHE CONTA E' `fonte`, NON `in_carica`. Una risposta senza
provenienza qui non vale: `in_carica` compilato e `fonte` vuoto è un difetto,
non un dato, e il file lo rende visibile invece di nasconderlo.

USO:
    python scripts/registra_incarichi_verificati.py --workflow esito.json
    python scripts/registra_incarichi_verificati.py          # solo automatico
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WD = ROOT / "data" / "allenatori_wikidata"
FILE_CONFRONTO = WD / "confronto.csv"
FILE_REGISTRO = WD / "registro_incarichi.csv"

# Come si traduce il verdetto automatico in un ruolo e in una risposta.
# `confermato*` = la fonte esterna vede quella persona in carica in quelle date.
AUTOMATICI_CHIUSI = ("confermato", "confermato_variante")


def _id(r) -> str:
    return f"{r.club_id}_{str(r.manager_key).replace(' ', '_')}_{r.nostro_da}"


def costruisci(esito_workflow: dict | None) -> pd.DataFrame:
    conf = pd.read_csv(FILE_CONFRONTO)
    conf["id"] = [_id(r) for r in conf.itertuples()]

    # --- ciò che ha chiuso il confronto automatico
    conf["verificato_da"] = ""
    conf["in_carica"] = ""
    conf["ruolo"] = ""
    conf["fonte"] = ""
    conf["nota_verifica"] = ""
    conf["confidenza"] = ""

    chiuso = conf.verdetto.isin(AUTOMATICI_CHIUSI)
    conf.loc[chiuso, "verificato_da"] = "wikidata"
    conf.loc[chiuso, "in_carica"] = conf.loc[chiuso, "allenatore"]
    conf.loc[chiuso, "ruolo"] = "titolare"
    conf.loc[chiuso, "fonte"] = [
        f"wikidata:{q}" if isinstance(q, str) and q.startswith("Q") else "wikidata"
        for q in conf.loc[chiuso, "manager_qid"]]

    # --- ciò che ha chiuso la verifica caso per caso
    conf["refutazione"] = "non_controllato"
    if esito_workflow:
        casi = {c["id"]: c for c in esito_workflow.get("casi", [])}
        esiti = {e["id"]: e for e in esito_workflow.get("esiti_refutazione", [])}

        # ⚠️ LA DISTINZIONE CHE NON VA PERSA: «ha superato lo scettico» e «non
        # e' mai passato dallo scettico» sono due cose diverse, e finirebbero
        # nella stessa colonna se non le si separasse. La copertura della
        # refutazione e' parziale (limite di sessione), e il registro lo dice
        # riga per riga invece di lasciarlo intendere.
        vivi = {}
        for i, c in casi.items():
            e = esiti.get(i)
            if e is None:
                vivi[i] = {**c, "_refutazione": "non_controllato"}
            elif e.get("regge"):
                vivi[i] = {**c, "_refutazione": "regge"}
            elif e.get("verdetto_corretto") and e.get("in_carica_corretto"):
                # un verdetto caduto non e' un verdetto piu' debole: entra solo
                # con la correzione dello scettico, mai come stava prima
                vivi[i] = {**c, "verdetto": e["verdetto_corretto"],
                           "in_carica_davvero": e["in_carica_corretto"],
                           "fonti": e.get("fonti") or c.get("fonti") or [],
                           "nota": "corretto in refutazione: " + (e.get("perche") or ""),
                           "confidenza": "media", "_refutazione": "corretto"}
            # refutato senza correzione proposta -> la riga resta APERTA
        for i, riga in conf.iterrows():
            v = vivi.get(riga["id"])
            if not v or riga["verificato_da"]:
                continue
            fonti = [f for f in (v.get("fonti") or []) if isinstance(f, str)]
            conf.at[i, "verificato_da"] = "caso_per_caso"
            conf.at[i, "in_carica"] = v.get("in_carica_davvero", "")
            conf.at[i, "ruolo"] = v.get("ruolo_nostro", "ignoto")
            conf.at[i, "fonte"] = " | ".join(fonti[:3])
            conf.at[i, "refutazione"] = v.get("_refutazione", "non_controllato")
            conf.at[i, "confidenza"] = v.get("confidenza", "")
            conf.at[i, "nota_verifica"] = (
                f"{v.get('verdetto', '')}"
                + (f" ({v.get('motivo')})" if v.get("motivo") else "")
                + (f" — {v.get('nota')}" if v.get("nota") else ""))

    conf["verificato"] = conf.verificato_da != ""
    # ⚠️ il guardiano: una risposta senza provenienza non è una risposta
    conf["senza_fonte"] = conf.verificato & (conf.fonte == "")
    return conf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", type=Path,
                    help="JSON con l'esito del workflow di verifica")
    a = ap.parse_args()
    esito = json.loads(a.workflow.read_text()) if a.workflow else None

    df = costruisci(esito)
    df.to_csv(FILE_REGISTRO, index=False)

    n = len(df)
    print(f"registro di {n} mandati -> {FILE_REGISTRO.relative_to(ROOT)}\n")
    print("come è stato verificato ciascuno:")
    for k, v in df.verificato_da.replace("", "NON VERIFICATO").value_counts().items():
        print(f"  {k:18s} {v:5d}  ({100*v/n:5.1f}%)")
    caso = df[df.verificato_da == "caso_per_caso"]
    if len(caso):
        print("\n⚠️ copertura della REFUTAZIONE sui casi verificati a mano:")
        for k, v in caso.refutazione.value_counts().items():
            print(f"  {k:18s} {v:5d}  ({100*v/len(caso):5.1f}%)")
        print("  «non_controllato» NON vuol dire «verificato due volte»: vuol")
        print("  dire che nessuno scettico ha riaperto quel caso.")

    print(f"\nverificati in tutto: {int(df.verificato.sum())}/{n} "
          f"({100*df.verificato.mean():.1f}%)")
    print(f"in PARTITE:          {int(df[df.verificato].partite.sum())}/"
          f"{int(df.partite.sum())} "
          f"({100*df[df.verificato].partite.sum()/df.partite.sum():.1f}%)")

    if df.senza_fonte.any():
        print(f"\n⚠️ {int(df.senza_fonte.sum())} righe verificate SENZA fonte: "
              f"sono un difetto, non un dato")
        print(df[df.senza_fonte][["club", "allenatore", "nostro_da"]]
              .head(10).to_string(index=False))

    ruoli = df[df.ruolo != ""].ruolo.value_counts()
    if len(ruoli):
        print("\nruolo attribuito ai nostri mandati:")
        print(ruoli.to_string())

    # ⚠️ NON si confrontano le STRINGHE `in_carica` e `allenatore`: differiscono
    # in 109 righe, e quasi tutte sono lo stesso uomo col nome anagrafico
    # («Rubi» → Joan Francesc Ferrer Sicilia, «Pepe Bordalás» → José Bordalás).
    # Un confronto fra stringhe qui misura le convenzioni sui nomi, non i
    # cambi di panchina — ed e' il numero che si finirebbe per pubblicare.
    #
    # E nemmeno il traghettatore e' «un altro»: un interim E' in carica. Il
    # solo caso in cui il nostro dato attribuisce le partite a chi NON era in
    # carica e' il VICE per una gara.
    vice = df[df.ruolo == "vice"]
    if len(vice):
        print(f"\n⭐ {len(vice)} mandati in cui il nostro dato ha in panchina il "
              f"VICE, non chi era in carica ({int(vice.partite.sum())} partite):")
        print(vice[["club", "allenatore", "nostro_da", "partite", "in_carica",
                    "refutazione"]]
              .sort_values("partite", ascending=False).head(25)
              .to_string(index=False))
    tragh = df[df.ruolo == "traghettatore"]
    print(f"\n{len(tragh)} mandati sono un TRAGHETTATORE "
          f"({int(tragh.partite.sum())} partite): era in carica lui, ad interim "
          f"— non e' un errore del dato, e' un ruolo che il dato non distingue.")

    aperti = df[~df.verificato]
    print(f"\nresta APERTO: {len(aperti)} mandati ({int(aperti.partite.sum())} partite)")
    if len(aperti):
        print(aperti.verdetto.value_counts().to_string())


if __name__ == "__main__":
    main()
