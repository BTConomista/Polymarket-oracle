"""🔎 Verifica avversariale di `data/stagione_2025_2026/`.

Non ricontrolla che i file esistano: prova a **romperli**. Le due promesse
della cartella sono che ci sia TUTTO il 2025-26 e SOLO il 2025-26, e ogni
controllo qui sotto è un modo in cui una delle due potrebbe essere falsa senza
che si veda.

    python scripts/_run_verifica_stagione_2025_2026.py
    python scripts/_run_verifica_stagione_2025_2026.py --json esito.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

from scripts.build_actual_database2526 import norm_data  # noqa: E402
from scripts.build_stagione_2025_2026 import CARTELLA, TETTO_MB  # noqa: E402

# La finestra della stagione: dal 1° turno preliminare di Champions
# (08/07/2025) alla finale playoff di LaLiga2 (20/06/2026).
FINESTRA = ("2025-07-01", "2026-07-01")

# Le tabelle che possono legittimamente precedere il primo fischio, e perché.
# ⚠️ Non è una deroga di comodo: il valore di mercato «alla data» di una
# partita di agosto è per forza una quotazione di giugno — una valutazione
# successiva alla partita sarebbe look-ahead (R8). Tagliare qui vorrebbe dire
# rendere inutilizzabile proprio il dato che serve.
FINESTRE_PROPRIE = {"transfermarkt_player_valuations.csv.gz": ("2025-06-01",
                                                               "2026-07-01")}

# Le fonti che la cartella deve rappresentare, con le righe attese. I numeri
# vengono dai moduli che leggono la fonte, non dalla cartella che verifichiamo.
ATTESE_RIGHE = {
    "posizioni": 4_767_120,
    "eventi_opta": 3_708_677,
    "giocatori_partita_tre_fonti": 169_939,
}


def _leggi_colonne(percorso: Path, colonne: list[str]) -> pd.DataFrame:
    """Legge poche colonne: i file grossi non stanno in memoria interi.

    ⚠️ Salta ciò che CSV non è: nella cartella c'è anche un `.json` (i
    manifesti delle consegne), e darlo in pasto a `read_csv` non dà una
    tabella vuota — dà un UnicodeDecodeError a metà verifica.
    """
    if not percorso.name.endswith(".csv.gz"):
        return pd.DataFrame()
    intestazione = pd.read_csv(percorso, nrows=0)
    presenti = [c for c in colonne if c in intestazione.columns]
    if not presenti:
        return pd.DataFrame()
    return pd.read_csv(percorso, usecols=presenti, low_memory=False)


def controlli(cartella: Path) -> list[dict]:
    esiti: list[dict] = []

    def dichiara(nome: str, passa: bool, dettaglio: str) -> None:
        esiti.append({"controllo": nome, "esito": "ok" if passa else "ROTTO",
                      "dettaglio": dettaglio})

    manifesto = json.loads((cartella / "MANIFESTO.json").read_text())
    dettaglio = manifesto["tabelle_dettaglio"]

    # 1 · il manifesto descrive il disco, e il disco il manifesto
    attesi = {cartella / p["file"] for v in dettaglio.values() for p in v["pezzi"]}
    sul_disco = {p for p in cartella.rglob("*") if p.is_file()
                 and p.name not in {"MANIFESTO.json", "README.md"}}
    dichiara("manifesto ⇄ disco: nessun file di troppo",
             not (sul_disco - attesi),
             f"{len(sul_disco - attesi)} file sul disco che il manifesto non "
             f"nomina: {[p.name for p in list(sul_disco - attesi)[:4]]}")
    dichiara("manifesto ⇄ disco: nessun file mancante",
             not (attesi - sul_disco),
             f"{len(attesi - sul_disco)} file dichiarati e assenti")

    # 2 · le impronte: un file modificato a mano si vede
    alterati = []
    for voce in dettaglio.values():
        for pezzo in voce["pezzi"][:3]:      # un campione per tabella
            percorso = cartella / pezzo["file"]
            if not percorso.exists():
                continue
            digest = hashlib.sha256()
            with percorso.open("rb") as sorgente:
                for blocco in iter(lambda: sorgente.read(1 << 20), b""):
                    digest.update(blocco)
            if digest.hexdigest() != pezzo["sha256"]:
                alterati.append(pezzo["file"])
    dichiara("sha256: nessun file alterato dopo la scrittura",
             not alterati, f"alterati: {alterati[:4]}")

    # 3 · il tetto per file, che è la ragione per cui la cartella esiste
    pesi = [p["mb"] for v in dettaglio.values() for p in v["pezzi"]]
    sopra = [p for p in pesi if p > TETTO_MB]
    dichiara(f"nessun file sopra i {TETTO_MB:.0f} MB", not sopra,
             f"il più grosso: {max(pesi, default=0):.1f} MB su "
             f"{len(pesi)} file")

    # 4 · le righe attese dalle fonti, sulle tabelle grosse
    sbagliate = {n: (dettaglio.get(n, {}).get("righe"), attesa)
                 for n, attesa in ATTESE_RIGHE.items()
                 if dettaglio.get(n, {}).get("righe") != attesa}
    dichiara("righe = quelle della fonte (posizioni, opta, giocatori)",
             not sbagliate, f"divergenti: {sbagliate}" if sbagliate
             else "3 tabelle su 3 al conteggio della fonte")

    # 5 · `match_uid`: le chiavi esistono davvero in partite.csv.gz?
    #    un tasso di aggancio al 100% NON vede una chiave orfana.
    partite = pd.read_csv(cartella / "partite.csv.gz", usecols=["match_uid"],
                          low_memory=False)
    note = set(partite["match_uid"])
    orfane: dict[str, int] = {}
    for nome, voce in dettaglio.items():
        if voce.get("aggancio_match_uid") is None:
            continue
        for pezzo in voce["pezzi"][:2]:
            percorso = cartella / pezzo["file"]
            colonna = _leggi_colonne(percorso, ["match_uid"])
            if colonna.empty:
                continue
            fuori = colonna["match_uid"].dropna()
            quante = int((~fuori.isin(note)).sum())
            if quante:
                orfane[pezzo["file"]] = quante
    dichiara("match_uid: nessuna chiave orfana", not orfane,
             f"{len(orfane)} file con chiavi che partite.csv.gz non ha: "
             f"{dict(list(orfane.items())[:3])}")

    # 6 · SOLO la stagione 2025-26: nessuna data fuori finestra
    fuori_finestra: dict[str, int] = {}
    for nome, voce in dettaglio.items():
        colonne_data = [c for c in voce["nomi_colonne"]
                        if c.lower() in {"data", "date", "data e ora iso (utc)"}]
        if not colonne_data:
            continue
        for pezzo in voce["pezzi"][:2]:
            frame = _leggi_colonne(cartella / pezzo["file"], colonne_data[:1])
            if frame.empty:
                continue
            # ⚠️ Nella cartella convivono date ISO (`2026-05-09`) e date
            # `15.11.2025`, e NESSUN singolo flag di pandas le legge entrambe:
            # `dayfirst=True` legge l'ISO al contrario (2026-05-09 diventa
            # il 5 settembre) e `dayfirst=False` legge la seconda al contrario.
            # `norm_data` del progetto le distingue guardando la FORMA, ed è
            # la stessa funzione che costruisce le chiavi: qui e là la data
            # deve essere letta allo stesso modo.
            date = pd.to_datetime(frame.iloc[:, 0].map(norm_data),
                                  errors="coerce")
            da, a = FINESTRE_PROPRIE.get(pezzo["file"], FINESTRA)
            quante = int(((date < da) | (date > a)).sum())
            if quante:
                fuori_finestra[pezzo["file"]] = quante
    dichiara("SOLO 2025-26: nessuna data fuori finestra", not fuori_finestra,
             f"{len(fuori_finestra)} file con date fuori: "
             f"{dict(list(fuori_finestra.items())[:3])}")

    # 7 · i temi che l'utente ha nominato: ci sono, e in quante partite?
    temi = {
        "arbitro": ["arbitro", "Arbitro", "Arbitro (SofaScore)", "referee",
                    "Referee"],
        "quote": ["Quota iniziale", "AHCh", "odds_home", "tf_quota_1x2_1_chiude"],
        "meteo": ["Meteo (WhoScored)", "meteo_codice_whoscored"],
    }
    for tema, candidate in temi.items():
        tabelle = [n for n, v in dettaglio.items()
                   if any(c in v["nomi_colonne"] for c in candidate)]
        dichiara(f"il tema «{tema}» è nella cartella", bool(tabelle),
                 f"{len(tabelle)} tabelle: {tabelle[:4]}")

    # 8 · il meteo è il finto pieno dichiarato, non un dato
    squadre = list((cartella / "squadre_partita_tre_fonti").glob("*.csv.gz"))
    if squadre:
        valori = set()
        for percorso in squadre[:6]:
            frame = _leggi_colonne(percorso, ["Meteo (WhoScored)"])
            if not frame.empty:
                valori |= set(frame.iloc[:, 0].dropna().unique())
        dichiara("meteo: costante, come dichiarato (R6)", len(valori) <= 1,
                 f"valori distinti: {sorted(valori)[:5] or 'nessuno'}")

    # 9 · la porta d'ingresso ha una riga per partita, senza duplicati
    uid = pd.read_csv(cartella / "partite.csv.gz", usecols=["match_uid"],
                      low_memory=False)["match_uid"]
    dichiara("partite.csv.gz: match_uid unico", not uid.duplicated().any(),
             f"{len(uid)} partite, {int(uid.duplicated().sum())} duplicati")

    # 10 · ogni tabella con match_uid ne aggancia almeno il grosso
    deboli = {n: round(v["aggancio_match_uid"], 3)
              for n, v in dettaglio.items()
              if v.get("aggancio_match_uid") is not None
              and v["aggancio_match_uid"] < 0.70}
    dichiara("aggancio a match_uid ≥ 70% ovunque", not deboli,
             f"sotto soglia: {deboli}" if deboli else
             f"{sum(1 for v in dettaglio.values() if v.get('aggancio_match_uid') is not None)} "
             f"tabelle agganciate")

    # 11 · il ranking UEFA non guarda avanti (R8)
    #
    # ⚠️ Il controllo NON è «esiste una colonna col nome giusto»: sarebbe
    # soddisfatto da una colonna piena di copie del numero pubblicato. Si
    # verifica l'IDENTITÀ che le separa — `pubblicato − fino_2526 = punti_2627`
    # dove il pavimento non morde — e si pretende che su qualche riga le due
    # finestre DIVERGANO davvero. Un controllo che passa anche quando la
    # riparazione non è stata applicata non è un controllo.
    colonne_uefa = ["casa_uefa_coeff_fino_2526", "casa_uefa_coeff_pubblicato",
                    "casa_uefa_punti_2627", "casa_uefa_somma_pubblicata",
                    "casa_uefa_somma_fino_2526"]
    try:
        ranking = pd.read_csv(cartella / "partite.csv.gz", usecols=colonne_uefa,
                              low_memory=False)
    except (ValueError, FileNotFoundError):
        dichiara("ranking UEFA: la finestra dell'archivio è nel file", False,
                 f"mancano le colonne {colonne_uefa}")
    else:
        sopra = pd.to_numeric(ranking["casa_uefa_coeff_pubblicato"],
                              errors="coerce")
        sotto = pd.to_numeric(ranking["casa_uefa_coeff_fino_2526"],
                              errors="coerce")
        futuro = pd.to_numeric(ranking["casa_uefa_punti_2627"], errors="coerce")
        s_sopra = pd.to_numeric(ranking["casa_uefa_somma_pubblicata"],
                                errors="coerce")
        s_sotto = pd.to_numeric(ranking["casa_uefa_somma_fino_2526"],
                                errors="coerce")
        # ⚠️ L'identità si verifica sulle SOMME, non sui coefficienti. Il
        # coefficiente è `MAX(somma; 20% federazione)`, e il pavimento è una
        # proprietà della FINESTRA: su 6 club morde nella troncata e non nella
        # pubblicata, quindi `pubblicato − troncato ≠ punti 26/27` per un
        # motivo giusto. Una prima stesura di questo controllo lo chiamava
        # difetto — era il controllo a essere sbagliato, non il dato.
        # ⚠️ le parentesi non sono estetiche: in Python `&` lega PIÙ STRETTO
        # di `>`, quindi `a > 1e-6 & libere` prova a fare `1e-6 & Series`.
        note = s_sopra.notna() & s_sotto.notna() & futuro.notna()
        rotte = int((((s_sopra - s_sotto - futuro).abs() > 1e-6) & note).sum())
        # e il coefficiente troncato non può MAI superare il pubblicato:
        # togliere punti non ne aggiunge.
        cresciute = int((sotto > sopra + 1e-9).sum())
        diverse = int(((sopra - sotto).abs() > 1e-9).sum())
        dichiara("ranking UEFA: la 26/27 è fuori dalla finestra dell'archivio",
                 rotte == 0 and cresciute == 0 and diverse > 0,
                 f"{diverse} righe in cui le due finestre divergono, "
                 f"{rotte} in cui somma_pubblicata−somma_troncata≠26/27, "
                 f"{cresciute} in cui il troncato SUPERA il pubblicato")

    # 12 · i tempi che non ricompongono sono MARCATI, non zittiti (R5)
    try:
        tempi = pd.read_csv(cartella / "partite.csv.gz",
                            usecols=["tempi_non_ricompongono",
                                     "tempi_tutti_a_zero_con_gol"],
                            low_memory=False)
    except (ValueError, FileNotFoundError):
        dichiara("i tempi che non ricompongono hanno la loro colonna", False,
                 "manca `tempi_non_ricompongono` in partite.csv.gz")
    else:
        quante = int(tempi["tempi_non_ricompongono"].astype("string")
                     .str.lower().eq("true").sum())
        zero = int(tempi["tempi_tutti_a_zero_con_gol"].astype("string")
                   .str.lower().eq("true").sum())
        dichiara("i tempi che non ricompongono hanno la loro colonna", True,
                 f"{quante} partite marcate, di cui {zero} con tutti i tempi "
                 f"a zero e gol nella partita (reperto NON diagnosticato)")

    return esiti


def main() -> None:
    argomenti = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argomenti.add_argument("--cartella", type=Path, default=CARTELLA)
    argomenti.add_argument("--json", type=Path, default=None)
    opzioni = argomenti.parse_args()

    manifesto = json.loads((opzioni.cartella / "MANIFESTO.json").read_text())
    print(f"{opzioni.cartella}: {manifesto['tabelle']} tabelle · "
          f"{manifesto['file']} file · {manifesto['righe_totali']:,} righe · "
          f"{manifesto['mb_totali']} MB\n".replace(",", "."))

    esiti = controlli(opzioni.cartella)
    for esito in esiti:
        segno = "✔" if esito["esito"] == "ok" else "✘"
        print(f" {segno} {esito['controllo']:46s} {esito['dettaglio']}")

    rotti = [e for e in esiti if e["esito"] != "ok"]
    print(f"\n{len(esiti) - len(rotti)}/{len(esiti)} controlli passati")
    if opzioni.json:
        opzioni.json.write_text(json.dumps(esiti, ensure_ascii=False, indent=2))
    raise SystemExit(1 if rotti else 0)


if __name__ == "__main__":
    main()
