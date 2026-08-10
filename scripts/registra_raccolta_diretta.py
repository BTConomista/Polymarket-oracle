#!/usr/bin/env python3
"""Registra una nuova raccolta di statistiche per giocatore (diretta.it).

E' la porta d'ingresso per le prossime leghe e per le competizioni europee e
internazionali: **verifica** i dati e scrive il `manifesto.json` che il modulo
`src/data/player_stats.py` legge. Nessuna modifica a `src/` e' mai necessaria
per aggiungere una raccolta.

USO:
    # da un .xlsx o .csv appena raccolto
    python scripts/registra_raccolta_diretta.py \\
        --partite ~/scaricati/Premier_202526_partita_per_partita.xlsx \\
        --lega premier_league --stagione 2526 \\
        [--riepilogo ...xlsx] [--legenda ...csv] [--fonte "diretta.it (Flashscore)"]

    # oppure ri-registra una cartella gia' esistente (ricalcola i conteggi)
    python scripts/registra_raccolta_diretta.py --cartella files/diretta_serie_a_2526

COSA VERIFICA prima di accettare (e si ferma se non torna):
  1. le colonne fondamentali ci sono;
  2. le date si leggono e la finestra e' plausibile;
  3. ogni squadra-partita ha **esattamente 11 titolari**;
  4. nessuna riga duplicata (stessa giornata, squadra, giocatore);
  5. minuti e percentuali dentro i range fisici;
  6. **se esiste uno snapshot della lega**: join e coerenza dei gol contro di
     esso — che e' il controllo piu' forte, perche' e' una fonte indipendente.
     Le competizioni senza snapshot (coppe, nazionali) saltano questo passo, e
     il manifesto lo dichiara.

Il manifesto NON e' un adempimento: e' cio' che rende le guardie di
`load_player_matches(strict=True)` specifiche per raccolta invece che incise
nel codice.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import player_stats as PS  # noqa: E402

COLONNE_MINIME = ["Giornata", "Data", "Squadra", "Campo", "Avversario",
                  "Giocatore", "Titolare/Subentrato", "Minuti giocati"]


def _leggi(percorso: Path, foglio: str | None = None) -> pd.DataFrame:
    if percorso.suffix.lower() in (".xlsx", ".xlsm"):
        df = pd.read_excel(percorso, sheet_name=foglio or 0)
    else:
        df = pd.read_csv(percorso)
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    return df


def verifica(df: pd.DataFrame, lega: str) -> dict:
    """Controlla e restituisce i numeri per il manifesto. Alza se non torna."""
    mancanti = [c for c in COLONNE_MINIME if c not in df.columns]
    if mancanti:
        raise SystemExit(f"❌ colonne mancanti: {mancanti}")

    d = df.copy()
    d["data"] = pd.to_datetime(d["Data"], format="%d.%m.%Y", errors="coerce")
    # stessa normalizzazione del caricatore: il controllo deve vedere cio' che
    # vedra' il codice, non i nomi grezzi
    from src.data.sources import TEAM_ALIASES

    for col in ("Squadra", "Avversario"):
        if col in d.columns:
            d[col] = d[col].map(lambda x: TEAM_ALIASES.get(x, x))
    if d["data"].isna().any():
        raise SystemExit(f"❌ {int(d['data'].isna().sum())} date non interpretabili")

    # La colonna `Fase` (Bundesliga in poi) separa il campionato dallo spareggio
    # promozione/retrocessione. I controlli e i conteggi del manifesto valgono
    # per il CAMPIONATO: lo spareggio non sta negli snapshot, quindi un join
    # calcolato su tutto risulterebbe incompleto per un motivo che non e' un
    # difetto. Le righe fuori campionato restano nel file e si contano a parte.
    fuori = pd.DataFrame(columns=d.columns)
    if "Fase" in d.columns:
        ignote = set(d["Fase"].dropna()) - set(PS.FASI_CAMPIONATO) - set(PS.FASI_FUORI_CAMPIONATO)
        if ignote:
            raise SystemExit(
                f"❌ fasi sconosciute: {sorted(ignote)}. Aggiungerle a "
                "src/data/player_stats.py (FASI_CAMPIONATO / FASI_FUORI_CAMPIONATO)."
            )
        fuori = d[~d["Fase"].isin(PS.FASI_CAMPIONATO)]
        d = d[d["Fase"].isin(PS.FASI_CAMPIONATO)]

    titolari = (
        d[d["Titolare/Subentrato"].astype(str).str.strip().str.lower() == "titolare"]
        .groupby(["data", "Squadra"]).size()
    )
    if set(titolari.unique()) != {11}:
        strane = titolari[titolari != 11]
        raise SystemExit(
            f"❌ {len(strane)} squadra-partita non hanno 11 titolari: "
            f"{strane.head().to_dict()}"
        )

    dup = d.duplicated(subset=["Giornata", "Squadra", "Giocatore"]).sum()
    if dup:
        raise SystemExit(f"❌ {dup} righe duplicate (giornata+squadra+giocatore)")

    # ⚠️ Lo ZERO e' ammesso, e viene CONTATO. Il limite era 1-120 e la Ligue 1
    # l'ha fatto scattare su una riga: Ali Youssef, titolare in Lorient-Nantes
    # (g. 20) con rating 6,5 e un giallo all'88' — ha giocato, ma diretta.it non
    # gli attribuisce minuti. E' una lacuna della fonte, cioe' uno zero che
    # significa «non lo so»: il finto pieno della regola R6. Non si corregge
    # (R3) e non si nasconde: si lascia com'e' e si dichiara nel manifesto,
    # cosi' chi filtra su `Minuti giocati > 0` sa che sta perdendo quella riga.
    if not d["Minuti giocati"].between(0, 120).all():
        raise SystemExit("❌ minuti fuori dal range 0-120")
    zero_minuti = d[d["Minuti giocati"] == 0]
    for col in [c for c in d.columns if "(%)" in c]:
        v = d[col].dropna()
        if len(v) and not v.between(0, 100).all():
            raise SystemExit(f"❌ {col} fuori da 0-100")

    info = {
        # righe_attese conta il FILE INTERO (spareggio compreso): e' la guardia
        # che verifica di aver letto tutto il disco. I conteggi che seguono sono
        # invece di CAMPIONATO, cioe' cio' che load_player_matches restituisce
        # col suo default.
        "righe_attese": int(len(d) + len(fuori)),
        "righe_campionato": int(len(d)),
        "righe_fuori_campionato": int(len(fuori)),
        "righe_con_zero_minuti": [
            {"data": str(r.data.date()), "squadra": r.Squadra,
             "giocatore": r.Giocatore}
            for r in zero_minuti.itertuples()
        ],
        "team_partita_attesi": int(d.groupby(["data", "Squadra", "Avversario"]).ngroups),
        "squadre": int(d["Squadra"].nunique()),
        "giocatori": int(d["Giocatore"].nunique()),
        "statistiche": int(len(PS.statistic_columns(d))),
        "data_prima": str(d["data"].min().date()),
        "data_ultima": str(d["data"].max().date()),
    }
    info["partite_attese"] = info["team_partita_attesi"] // 2

    # Controllo forte, dove possibile: contro una fonte INDIPENDENTE.
    from src.data import database

    percorso = database.snapshot_path(lega) if lega else None
    if percorso is not None and percorso.exists():
        snap = database.read_snapshot(percorso)
        snap["data"] = pd.to_datetime(snap["date"])
        snap = snap[snap["data"].between(d["data"].min(), d["data"].max())]
        chiavi = set(zip(snap["data"], snap["home_team"], snap["away_team"]))
        nostre = set(zip(d["data"], d["Squadra"], d["Avversario"]))
        agganciate = sum(
            1 for (dt, a, b) in nostre if (dt, a, b) in chiavi or (dt, b, a) in chiavi
        )
        info["join_snapshot"] = f"{agganciate}/{len(nostre)}"
        info["snapshot_verificato"] = agganciate == len(nostre)
        if not info["snapshot_verificato"]:
            print(f"⚠️  join incompleto: {agganciate}/{len(nostre)} team-partita. "
                  "Probabile disallineamento dei nomi squadra o delle date.")
        mancano = [k for k in chiavi if (k[0], k[1], k[2]) not in
                   {(x[0], x[1], x[2]) for x in nostre}
                   and (k[0], k[2], k[1]) not in {(x[0], x[1], x[2]) for x in nostre}]
        info["partite_mancanti"] = [
            {"data": str(k[0].date()), "casa": k[1], "trasferta": k[2]} for k in sorted(mancano)
        ]
    else:
        info["snapshot_verificato"] = False
        info["nota_snapshot"] = (
            "nessuno snapshot per questa competizione: il controllo contro una "
            "fonte indipendente non e' stato possibile, e join_to_snapshot() "
            "non e' utilizzabile"
        )
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--partite", type=Path, help="file partita-per-partita (.xlsx o .csv)")
    ap.add_argument("--riepilogo", type=Path)
    ap.add_argument("--legenda", type=Path)
    ap.add_argument("--cartella", type=Path, help="ri-registra una raccolta esistente")
    ap.add_argument("--lega", default=None)
    ap.add_argument("--stagione", default=None)
    ap.add_argument("--fonte", default="diretta.it (Flashscore)")
    ap.add_argument("--foglio", default=None, help="nome del foglio Excel")
    ap.add_argument("--originale", type=Path, default=None,
                    help="il file COME CONSEGNATO, da archiviare accanto ai CSV "
                         "(regola §5-ter: senza l'originale un bug della nostra "
                         "conversione e' indistinguibile dal dato)")
    ap.add_argument("--fogli-extra", action="store_true",
                    help="salva anche i fogli di contorno presenti nell'.xlsx "
                         "(Partite, Formazioni, Cambi, Eventi, Note e copertura)")
    args = ap.parse_args()

    if args.cartella:
        cartella = args.cartella
        manifesto = cartella / PS.FILE_MANIFESTO
        vecchio = json.loads(manifesto.read_text()) if manifesto.is_file() else {}
        lega = args.lega or vecchio.get("lega")
        stagione = args.stagione or vecchio.get("stagione")
        df = PS._read(cartella / PS.FILE_PARTITE)
    else:
        if not (args.partite and args.lega and args.stagione):
            raise SystemExit("servono --partite, --lega e --stagione (oppure --cartella)")
        lega, stagione = args.lega, args.stagione
        cartella = PS.FILES / f"{PS.PREFISSO}{lega}_{stagione}"
        cartella.mkdir(parents=True, exist_ok=True)
        df = _leggi(args.partite, args.foglio)
        df.to_csv(cartella / PS.FILE_PARTITE, index=False, compression="gzip")
        if args.riepilogo:
            _leggi(args.riepilogo).to_csv(cartella / PS.FILE_STAGIONE,
                                          index=False, compression="gzip")
        if args.legenda:
            shutil.copy(args.legenda, cartella / PS.FILE_LEGENDA)
        if args.originale:
            shutil.copy(args.originale, cartella / f"originale{args.originale.suffix}")
        if args.fogli_extra:
            # I fogli che la fonte espone SOLO per alcune consegne. Si prendono
            # tutti (§5-ter): raccogliere e usare sono due decisioni separate.
            extra = {"Partite": PS.FILE_ELENCO, "Formazioni": PS.FILE_FORMAZIONI,
                     "Cambi": PS.FILE_CAMBI, "Eventi": PS.FILE_EVENTI}
            disponibili = pd.ExcelFile(args.partite).sheet_names
            for foglio, dest in extra.items():
                if foglio in disponibili:
                    _leggi(args.partite, foglio).to_csv(
                        cartella / dest, index=False, compression="gzip")
                    print(f"   + foglio «{foglio}» -> {dest}")
            if "Note e copertura" in disponibili:
                _leggi(args.partite, "Note e copertura").to_csv(
                    cartella / "note_fonte_giocatori.csv", index=False)
                print("   + foglio «Note e copertura» -> note_fonte_giocatori.csv")
            if "Legenda" in disponibili and not args.legenda:
                _leggi(args.partite, "Legenda").to_csv(
                    cartella / PS.FILE_LEGENDA, index=False)
                print(f"   + foglio «Legenda» -> {PS.FILE_LEGENDA}")

    print(f"verifico {lega}/{stagione} ({len(df):,} righe)…")
    info = verifica(df, lega)
    info.update({"lega": lega, "stagione": stagione, "fonte": args.fonte})

    (cartella / PS.FILE_MANIFESTO).write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"\n✅ registrata in {cartella}")
    for k, v in info.items():
        if k != "partite_mancanti":
            print(f"   {k:22s} {v}")
    if info.get("partite_mancanti"):
        print(f"   {'partite_mancanti':22s} {len(info['partite_mancanti'])}")
        for p in info["partite_mancanti"][:5]:
            print(f"      ⚠️  {p['data']} {p['casa']} - {p['trasferta']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
