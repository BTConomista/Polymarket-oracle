"""🔎 Verifica avversariale di `data/actual_database2526.csv`.

Non ricontrolla che il file esista: prova a **romperlo**. Ogni controllo è una
domanda a cui una risposta sbagliata sarebbe passata inosservata guardando il
file a occhio, e la maggior parte nasce da un difetto vero già pagato dal
progetto (il riferimento è nel nome del controllo).

    python scripts/_run_verifica_actual_database2526.py
    python scripts/_run_verifica_actual_database2526.py --json esito.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

from scripts.build_actual_database2526 import (  # noqa: E402
    COMPETIZIONI, LISTA_UTENTE, USCITA_DEFAULT,
)

# Quante partite ci aspettiamo per competizione. Sono i conteggi delle FONTI,
# misurati dai loro moduli, non copiati dal file che stiamo verificando.
ATTESE = {
    "Serie A": 380, "Premier League": 380, "LaLiga": 380, "LaLiga2": 468,
    "Bundesliga": 308, "2. Bundesliga": 310, "Ligue 1": 310,
    "UEFA Champions League": 281, "UEFA Europa League": 271,
    "UEFA Conference League": 409, "Supercoppa UEFA": 1,
    "Supercoppa Italiana": 3, "Supercopa de España": 3, "Community Shield": 1,
    "DFL-Supercup": 1, "Trophée des Champions": 1,
    "Coppa Italia": 45, "Copa del Rey": 137, "DFB-Pokal": 63, "FA Cup": 123,
    "EFL Cup": 93, "Coupe de France": 201,
}


def controlli(tabella: pd.DataFrame) -> list[dict]:
    esiti: list[dict] = []

    def dichiara(nome: str, passa: bool, dettaglio: str) -> None:
        esiti.append({"controllo": nome, "esito": "ok" if passa else "ROTTO",
                      "dettaglio": dettaglio})

    # 1 · la grana è la partita: nessuna chiave ripetuta
    doppie = tabella["match_uid"].duplicated().sum()
    dichiara("grana: match_uid unico", doppie == 0, f"{doppie} duplicati")

    doppie2 = tabella.duplicated(["competizione", "data", "casa", "trasferta"]).sum()
    dichiara("grana: (competizione, data, casa, trasferta) unica",
             doppie2 == 0, f"{doppie2} duplicati")

    # 2 · conteggi per competizione contro le fonti
    conteggi = tabella["competizione"].value_counts().to_dict()
    sbagliate = {c: (conteggi.get(c, 0), n) for c, n in ATTESE.items()
                 if conteggi.get(c, 0) != n}
    dichiara("conteggi per competizione", not sbagliate,
             f"divergenti: {sbagliate}" if sbagliate else
             f"{len(ATTESE)} competizioni, tutte al conteggio atteso")

    # 3 · ogni competizione del file è una di quelle dichiarate
    ignote = set(tabella["competizione"]) - set(COMPETIZIONI)
    dichiara("competizioni note", not ignote, f"ignote: {sorted(ignote)}")

    # 4 · R6 — nessuna colonna interamente vuota
    vuote = [c for c in tabella.columns if tabella[c].isna().all()]
    dichiara("R6: nessuna colonna interamente vuota", not vuote,
             f"{len(vuote)} vuote: {vuote[:5]}")

    # 5 · i pacchetti JSON sono JSON veri (il bug del letterale NaN)
    rotti: dict[str, int] = {}
    for colonna in [c for c in tabella.columns if c.endswith("_json")]:
        quanti = 0
        for valore in tabella[colonna].dropna().head(400):
            try:
                json.loads(valore)
            except (json.JSONDecodeError, TypeError):
                quanti += 1
        if quanti:
            rotti[colonna] = quanti
    dichiara("i pacchetti JSON si rileggono", not rotti, f"rotti: {rotti}")

    # 6 · ⚠️ la lotteria dei rigori NON è dentro il punteggio
    #     (Partizan-AEK Larnaca legge 7-7 nel grezzo ed è 2-1)
    caso = tabella[(tabella["competizione"] == "UEFA Europa League")
                   & (tabella["casa"].str.contains("Partizan", na=False))
                   & (tabella["trasferta"].str.contains("Larnaca", na=False))]
    if caso.empty:
        dichiara("rigori fuori dal punteggio (Partizan-AEK)", False,
                 "partita non trovata: il controllo non ha potuto girare")
    else:
        riga = caso.iloc[0]
        giusto = (riga["gol_casa_finale"] == 2 and riga["gol_trasferta_finale"] == 1)
        dichiara("rigori fuori dal punteggio (Partizan-AEK)", giusto,
                 f"{riga['gol_casa_finale']}-{riga['gol_trasferta_finale']} "
                 f"(rigori {riga.get('rigori_casa')}-{riga.get('rigori_trasferta')})")

    # 7 · i 90 minuti non superano mai il punteggio finale
    novanta = pd.to_numeric(tabella["gol_casa"], errors="coerce")
    finale = pd.to_numeric(tabella["gol_casa_finale"], errors="coerce")
    incoerenti = int(((novanta > finale) & novanta.notna() & finale.notna()).sum())
    dichiara("90' ≤ finale (casa)", incoerenti == 0,
             f"{incoerenti} righe con i 90' sopra il finale")

    # 8 · i due tempi sommano al punteggio dei 90 minuti
    for lato in ("casa", "trasferta"):
        primo = pd.to_numeric(tabella.get(f"gol_{lato}_1t"), errors="coerce")
        secondo = pd.to_numeric(tabella.get(f"gol_{lato}_2t"), errors="coerce")
        totale = pd.to_numeric(tabella[f"gol_{lato}"], errors="coerce")
        confrontabili = primo.notna() & secondo.notna() & totale.notna()
        rotte = int((confrontabili & (primo + secondo != totale)).sum())
        dichiara(f"identità 1T+2T = 90' ({lato})", rotte == 0,
                 f"{rotte} righe su {int(confrontabili.sum())} confrontabili")

    # 9 · l'esito è coerente col punteggio
    def atteso(riga) -> object:
        c, t = riga["gol_casa"], riga["gol_trasferta"]
        if pd.isna(c) or pd.isna(t):
            return None
        return "1" if c > t else ("2" if c < t else "X")
    calcolato = tabella.apply(atteso, axis=1)
    diverso = int((calcolato.notna() & (calcolato != tabella["esito_1x2"])).sum())
    dichiara("esito_1x2 coerente col punteggio", diverso == 0,
             f"{diverso} righe incoerenti")

    # 10 · la provenienza cita prefissi di blocco che esistono davvero
    citate: set[str] = set()
    campi_citati: set[str] = set()
    for valore in tabella["provenienza_json"].dropna().head(1500):
        contenuto = json.loads(valore)
        citate.update(contenuto.values())
        campi_citati.update(contenuto.keys())
    prefissi = {p.rstrip("_") for p in ("tf_", "dir_", "snap_", "cop_",
                                        "sof_", "ps_")}
    fantasma = sorted(citate - prefissi)
    dichiara("provenienza_json cita blocchi esistenti", not fantasma,
             f"fantasma: {fantasma[:5]}")
    senza_colonna = sorted(campi_citati - set(tabella.columns))
    dichiara("provenienza_json cita campi esistenti", not senza_colonna,
             f"campi assenti: {senza_colonna[:5]}")

    # 11 · le 25 della lista: quante coperte, e quali no
    presenti = [c for c in LISTA_UTENTE if c in set(tabella["competizione"])]
    mancanti = [c for c in LISTA_UTENTE if c not in presenti]
    dichiara("lista utente: copertura dichiarata", True,
             f"{len(presenti)}/25 presenti; mancanti: {mancanti}")

    # 12 · confronto incrociato dei gol: snapshot contro tre fonti
    if "snap_home_goals" in tabella.columns and "tf_Gol casa 90" in tabella.columns:
        a = pd.to_numeric(tabella["snap_home_goals"], errors="coerce")
        b = pd.to_numeric(tabella["tf_Gol casa 90"], errors="coerce")
        confrontabili = a.notna() & b.notna()
        divergenti = int((confrontabili & (a != b)).sum())
        dichiara("gol: snapshot == tre fonti", divergenti == 0,
                 f"{divergenti} divergenze su {int(confrontabili.sum())} confronti")

    # 13 · la data è sempre dentro la stagione 2025-26
    date = pd.to_datetime(tabella["data"], errors="coerce")
    fuori = int(((date < "2025-06-01") | (date > "2026-08-01")).sum())
    dichiara("date dentro la stagione 2025-26", fuori == 0,
             f"{fuori} fuori finestra; da {date.min().date()} a {date.max().date()}")

    return esiti


def main() -> None:
    argomenti = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argomenti.add_argument("--file", type=Path, default=USCITA_DEFAULT)
    argomenti.add_argument("--json", type=Path, default=None)
    opzioni = argomenti.parse_args()

    tabella = pd.read_csv(opzioni.file, low_memory=False)
    print(f"{opzioni.file}: {len(tabella)} partite × {tabella.shape[1]} colonne "
          f"· {opzioni.file.stat().st_size / 1e6:.1f} MB\n")

    esiti = controlli(tabella)
    for esito in esiti:
        segno = "✔" if esito["esito"] == "ok" else "✘"
        print(f" {segno} {esito['controllo']:44s} {esito['dettaglio']}")

    rotti = [e for e in esiti if e["esito"] != "ok"]
    print(f"\n{len(esiti) - len(rotti)}/{len(esiti)} controlli passati")

    if opzioni.json:
        opzioni.json.write_text(json.dumps(esiti, ensure_ascii=False, indent=2))
    raise SystemExit(1 if rotti else 0)


if __name__ == "__main__":
    main()
