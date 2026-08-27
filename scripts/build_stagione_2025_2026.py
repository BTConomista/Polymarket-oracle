"""🗂️  data/stagione_2025_2026/ — TUTTI i dati 2025-26, ognuno al suo grano.

PERCHÉ UNA CARTELLA E NON UN FILE
─────────────────────────────────
`data/actual_database2526.csv.gz` teneva la stagione su **una riga per partita**.
Per starci ha dovuto fare due cose che costano: impacchettare le grane fini
dentro celle JSON, e lasciare fuori l'event data Opta — che impacchettato pesa
1,7 GB grezzi / **243 MB gzippati**, cioè da solo più del doppio del limite di
100 MB per file che GitHub impone.

Una cartella scioglie il vincolo, perché un file troppo grosso si **spezza**.
In cambio non è più ammesso lasciare fuori niente: qui c'è tutto, in forma
tabellare **piatta** — niente JSON dentro le celle, niente campi curati, niente
conteggi al posto del dato.

LA REGOLA CHE TIENE INSIEME LA CARTELLA
───────────────────────────────────────
**Ogni riga di ogni file porta `match_uid`**, ed è la stessa chiave ovunque:

    match_uid = competizione | data ISO | casa normalizzata | trasferta normalizzata

Quindi qualunque tabella si riaggancia a `partite.csv.gz` con un `merge` su
quella colonna sola, e due tabelle qualsiasi si incrociano fra loro. Dove la
fonte ha anche i suoi identificatori (`ID partita (SofaScore)`, `game_id`,
`player_id`) quelli restano: servono a incrociare **dentro** la partita.

COSA C'È DENTRO
───────────────
Un file per **grana**, non per fonte: le 22 competizioni si impilano nella
stessa tabella con una colonna `competizione`. Le grane sono cinque —
partita, squadra-partita, giocatore-partita, evento, posizione — più le
anagrafiche, che non dipendono dalla partita.

USO
───
    python scripts/build_stagione_2025_2026.py
    python scripts/build_stagione_2025_2026.py --solo posizioni eventi_opta
    python scripts/build_stagione_2025_2026.py --elenco     # cosa produrrebbe
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

from scripts.build_actual_database2526 import (  # noqa: E402
    COMPETIZIONI, LISTA_UTENTE, META_RACCOLTA, PS_COMPETIZIONE,
    TF_COMPETIZIONE, _pulisci, _testo, canon_competizione, chiave_partita,
    norm_data, norm_squadra,
)
from src.data import tre_fonti as tf  # noqa: E402

log = logging.getLogger("stagione_2025_2026")

CARTELLA = RADICE / "data" / "stagione_2025_2026"
STAGIONE = "2025-26"

# Il tetto per file. GitHub rifiuta sopra i 100 MB; 90 lascia margine a una
# raccolta che cresce senza costringere a ri-progettare la spezzatura.
TETTO_MB = 90.0


# ════════════════════════════════════════════════════════════════════════════
# la scrittura: un posto solo, così il manifesto non può divergere dai file
# ════════════════════════════════════════════════════════════════════════════
MANIFESTO: dict[str, dict] = {}

# Le chiavi valide: si riempie quando `partite.csv.gz` viene scritta, ed è ciò
# che rende il tasso di aggancio una misura invece di una tautologia.
CHIAVI_VALIDE: set[str] = set()

NOTA_AGGANCIO = ("frazione di righe il cui match_uid ESISTE in partite.csv.gz. "
                 "⚠️ Non è `notna()`: la chiave si costruisce sempre, quindi "
                 "un tasso calcolato su `notna` sarebbe 1.0 anche con tutte "
                 "le chiavi penzolanti.")


def _tasso_aggancio(tabella: pd.DataFrame) -> float | None:
    """Quante righe puntano a una partita che esiste davvero."""
    if "match_uid" not in tabella.columns:
        return None
    valori = tabella["match_uid"]
    if not CHIAVI_VALIDE:
        return float(valori.notna().mean())
    return float(valori.isin(CHIAVI_VALIDE).mean())


def _impronta(percorso: Path) -> str:
    digest = hashlib.sha256()
    with percorso.open("rb") as sorgente:
        for blocco in iter(lambda: sorgente.read(1 << 20), b""):
            digest.update(blocco)
    return digest.hexdigest()


def scrivi(nome: str, tabella: pd.DataFrame, *, grana: str, fonti: list[str],
           spezza_per: str | None = None, note: str = "") -> None:
    """Scrive una tabella, spezzandola se supera il tetto, e la registra.

    ⚠️ La spezzatura NON è una scelta di stile: è l'unica ragione per cui
    questa cartella può contenere ciò che un file solo non conteneva. L'asse è
    dichiarato (`spezza_per`) e finisce nel manifesto, perché chi rilegge deve
    poter ricomporre la tabella con un `pd.concat` e sapere che è completa.
    """
    if tabella is None or tabella.empty:
        log.warning("  %-34s VUOTA, non scritta", nome)
        return

    if "match_uid" in tabella.columns:
        altre = [c for c in tabella.columns if c != "match_uid"]
        tabella = tabella[["match_uid"] + altre]

    destinazione = CARTELLA / nome
    destinazione.parent.mkdir(parents=True, exist_ok=True)

    pezzi: list[tuple[Path, pd.DataFrame]] = []
    if spezza_per and spezza_per in tabella.columns:
        for valore, gruppo in tabella.groupby(spezza_per, sort=True):
            etichetta = (str(valore).lower().replace(" ", "_")
                         .replace("/", "-").replace(".", ""))
            pezzi.append((destinazione / f"{etichetta}.csv.gz", gruppo))
    else:
        pezzi.append((destinazione, tabella))

    scritti = []
    for percorso, pezzo in pezzi:
        percorso.parent.mkdir(parents=True, exist_ok=True)
        pezzo.to_csv(percorso, index=False,
                     compression={"method": "gzip", "mtime": 0})
        peso = percorso.stat().st_size / 1e6
        scritti.append({"file": str(percorso.relative_to(CARTELLA)),
                        "righe": int(len(pezzo)), "mb": round(peso, 2),
                        "sha256": _impronta(percorso)})
        if peso > TETTO_MB:
            log.error("  ⚠️  %s pesa %.1f MB: sopra il tetto di %.0f MB, "
                      "va spezzato ancora", percorso.name, peso, TETTO_MB)

    MANIFESTO[nome] = {
        "grana": grana,
        "righe": int(len(tabella)),
        "colonne": int(tabella.shape[1]),
        "nomi_colonne": list(tabella.columns),
        "fonti": fonti,
        "spezzato_per": spezza_per,
        "aggancio_match_uid": _tasso_aggancio(tabella),
        "nota_aggancio": NOTA_AGGANCIO,
        "note": note,
        "pezzi": scritti,
    }
    totale = sum(p["mb"] for p in scritti)
    log.info("  %-38s %9d righe · %4d col · %6.1f MB · %d file",
             nome, len(tabella), tabella.shape[1], totale, len(scritti))


class ScritturaIncrementale:
    """Scrive una tabella spezzata **un pezzo alla volta**, senza mai tenerla
    tutta in memoria.

    ⚠️ Non è un'ottimizzazione: è ciò che rende costruibile questa cartella.
    `eventi_opta` sono 3,7 milioni di righe x 36 colonne e `posizioni` 4,8
    milioni: concatenarle prima di spezzarle ha fatto finire la RAM e ha ucciso
    il processo a lavoro quasi finito. Qui ogni raccolta si legge, si scrive e
    si butta, e in memoria resta solo il conteggio.
    """

    def __init__(self, nome: str, *, grana: str, fonti: list[str],
                 spezzato_per: str, note: str = "") -> None:
        self.nome = nome
        self.voce = {"grana": grana, "righe": 0, "colonne": 0,
                     "nomi_colonne": [], "fonti": fonti,
                     "spezzato_per": spezzato_per, "aggancio_match_uid": None,
                     "note": note, "pezzi": []}
        self._agganciate = 0

    def aggiungi(self, etichetta: str, pezzo: pd.DataFrame) -> None:
        if pezzo is None or pezzo.empty:
            return
        if "match_uid" in pezzo.columns:
            altre = [c for c in pezzo.columns if c != "match_uid"]
            pezzo = pezzo[["match_uid"] + altre]
            self._agganciate += int(
                pezzo["match_uid"].isin(CHIAVI_VALIDE).sum() if CHIAVI_VALIDE
                else pezzo["match_uid"].notna().sum())
        sicura = (str(etichetta).lower().replace(" ", "_")
                  .replace("/", "-").replace(".", ""))
        percorso = CARTELLA / self.nome / f"{sicura}.csv.gz"
        percorso.parent.mkdir(parents=True, exist_ok=True)
        # `mtime=0`: gzip scriverebbe l'ora nell'intestazione, e due corse
        # identiche darebbero file diversi. Con l'ora azzerata lo sha256 prova
        # anche la RIPRODUCIBILITÀ, non solo l'integrità dopo la scrittura.
        pezzo.to_csv(percorso, index=False,
                     compression={"method": "gzip", "mtime": 0})
        peso = percorso.stat().st_size / 1e6
        self.voce["pezzi"].append({
            "file": str(percorso.relative_to(CARTELLA)), "righe": int(len(pezzo)),
            "mb": round(peso, 2), "sha256": _impronta(percorso)})
        self.voce["righe"] += int(len(pezzo))
        if len(pezzo.columns) > self.voce["colonne"]:
            self.voce["colonne"] = int(len(pezzo.columns))
            self.voce["nomi_colonne"] = list(pezzo.columns)
        if peso > TETTO_MB:
            log.error("  ⚠️  %s pesa %.1f MB: sopra il tetto", percorso.name, peso)

    def chiudi(self) -> None:
        if not self.voce["pezzi"]:
            return
        if self.voce["righe"]:
            self.voce["aggancio_match_uid"] = (self._agganciate
                                               / self.voce["righe"])
        self.voce["nota_aggancio"] = NOTA_AGGANCIO
        MANIFESTO[self.nome] = self.voce
        totale = sum(p["mb"] for p in self.voce["pezzi"])
        log.info("  %-38s %9d righe · %4d col · %6.1f MB · %d file",
                 self.nome, self.voce["righe"], self.voce["colonne"], totale,
                 len(self.voce["pezzi"]))


# ════════════════════════════════════════════════════════════════════════════
# la mappa id → match_uid, che tiene insieme tutta la cartella
# ════════════════════════════════════════════════════════════════════════════
def _anagrafica_tf(raccolta: str) -> pd.DataFrame:
    """Una riga per partita della raccolta, con tutti gli identificatori."""
    squadre = tf.squadre(raccolta, spareggio=True, periodo="Totale")
    if squadre.empty:
        return pd.DataFrame()
    competizione = TF_COMPETIZIONE.get(raccolta) or canon_competizione(
        squadre["Competizione"].dropna().iloc[0])
    casa = squadre[squadre["Campo"] == "Casa"].copy()
    casa["competizione"] = competizione
    casa["match_uid"] = [chiave_partita(competizione, d, s, a) for d, s, a
                         in zip(casa["Data"], casa["Squadra"], casa["Avversario"])]
    return casa


def mappe_id(raccolte: list[str]) -> tuple[dict, dict, pd.DataFrame]:
    """`ID SofaScore → match_uid`, `ID WhoScored → match_uid`, e l'anagrafica."""
    per_sofa, per_ws, righe = {}, {}, []
    for raccolta in raccolte:
        anagrafica = _anagrafica_tf(raccolta)
        if anagrafica.empty:
            continue
        for _, riga in anagrafica.iterrows():
            if pd.notna(riga.get("ID partita (SofaScore)")):
                per_sofa[riga["ID partita (SofaScore)"]] = riga["match_uid"]
            if pd.notna(riga.get("ID partita (WhoScored)")):
                per_ws[riga["ID partita (WhoScored)"]] = riga["match_uid"]
        righe.append(anagrafica)
    return per_sofa, per_ws, (pd.concat(righe, ignore_index=True)
                              if righe else pd.DataFrame())


# ════════════════════════════════════════════════════════════════════════════
# 1 · LE GRANE FINI — posizioni e tocchi Opta, una cartella per raccolta
# ════════════════════════════════════════════════════════════════════════════
def tabella_posizioni(raccolte: list[str], per_sofa: dict, per_ws: dict) -> None:
    """4,77 milioni di POSIZIONI: una riga per tocco, con X/Y su scala 0-100.

    È il blocco che nel file unico stava solo come conteggio. Qui è per intero,
    spezzato per competizione: il pezzo più grosso resta ampiamente sotto il
    tetto, e chi ne vuole una sola lega non scarica le altre quindici.
    """
    uscita = ScritturaIncrementale(
        "posizioni", grana="una POSIZIONE (un tocco con X/Y)",
        fonti=["files/tre_fonti_*_2526/heatmap.csv.gz"],
        spezzato_per="raccolta",
        note="X/Y su scala 0-100 da SofaScore. La colonna `Tocchi` è vuota "
             "alla fonte in quasi tutte le raccolte: è nello schema e non "
             "contiene niente (R6).")
    for raccolta in raccolte:
        try:
            posizioni = tf.heatmap(raccolta, spareggio=True)
        except (FileNotFoundError, KeyError, ValueError):
            continue
        if posizioni.empty:
            continue
        colonna = ("ID partita (SofaScore)" if "ID partita (SofaScore)"
                   in posizioni.columns else "ID partita")
        posizioni = posizioni.copy()
        posizioni["match_uid"] = posizioni[colonna].map(
            lambda x: per_sofa.get(x) or per_ws.get(x))
        posizioni["raccolta"] = raccolta
        uscita.aggiungi(raccolta, posizioni)
        del posizioni
    uscita.chiudi()


def tabella_eventi_opta(raccolte: list[str], per_ws: dict) -> None:
    """3,71 milioni di TOCCHI Opta: ogni evento con coordinate, secondo e
    qualificatori. È il blocco per cui questa cartella esiste.

    ⚠️ Impacchettato in una cella pesava 1,7 GB grezzi / 243 MB gzippati — da
    solo più del doppio del limite di 100 MB per file di GitHub. Spezzato per
    competizione ogni pezzo sta comodamente sotto, e il dato non si perde.
    Copre 9 raccolte su 16: LaLiga2 non ha l'Opta (misurato: 468 pagine su 468
    senza `matchCentreData`), e le raccolte a una fonte sola nemmeno.
    """
    uscita = ScritturaIncrementale(
        "eventi_opta", grana="un TOCCO Opta",
        fonti=["files/tre_fonti_*_2526/eventi_opta*.csv.gz"],
        spezzato_per="raccolta",
        note="9 raccolte su 16: LaLiga2 e le raccolte a una fonte sola non "
             "hanno l'Opta. `ID partita` qui è quello di WhoScored.")
    for raccolta in raccolte:
        try:
            opta = tf.eventi_opta(raccolta, spareggio=True)
        except (FileNotFoundError, KeyError, ValueError):
            continue
        if opta.empty:
            continue
        opta = opta.copy()
        opta["match_uid"] = opta["ID partita"].map(per_ws)
        opta["raccolta"] = raccolta
        log.info("    opta %-24s %8d righe", raccolta, len(opta))
        uscita.aggiungi(raccolta, opta)
        del opta
    uscita.chiudi()


# ════════════════════════════════════════════════════════════════════════════
# 2 · GIOCATORE-PARTITA — tutti i campi, in colonne vere
# ════════════════════════════════════════════════════════════════════════════
def tabella_giocatori_tf(raccolte: list[str], per_sofa: dict) -> None:
    """Giocatore-partita dalle tre fonti: ~190 colonne, tutti i livelli.

    ⚠️ `livello` vale `Partita`, `Rosa` o `Stagione` e sono **tre grane
    diverse** nello stesso file della fonte: Partita è il giocatore in quella
    partita, Rosa è l'anagrafica di squadra-stagione, Stagione è l'aggregato —
    che per costruzione contiene il futuro di ogni singola partita, quindi è
    look-ahead se usato come feature (R8). Restano tutti e tre, distinti dalla
    colonna: cancellarne due sarebbe perdere dato, confonderli sarebbe peggio.
    """
    pezzi = []
    for raccolta in raccolte:
        for livello in ("Partita", "Rosa", "Stagione"):
            try:
                giocatori = tf.giocatori(raccolta, livello=livello,
                                         spareggio=True)
            except (FileNotFoundError, KeyError, ValueError):
                continue
            if giocatori.empty:
                continue
            giocatori = giocatori.copy()
            competizione = TF_COMPETIZIONE.get(raccolta)
            identificativi = (giocatori["ID partita (SofaScore)"]
                              if "ID partita (SofaScore)" in giocatori.columns
                              else pd.Series(np.nan, index=giocatori.index))
            da_id = identificativi.map(per_sofa)
            da_nome = pd.Series([
                chiave_partita(competizione, d,
                               s if c == "Casa" else a,
                               a if c == "Casa" else s)
                for d, s, a, c in zip(giocatori["Data"], giocatori["Squadra"],
                                      giocatori.get("Avversario", giocatori["Squadra"]),
                                      giocatori["Campo"])
            ], index=giocatori.index) if "Campo" in giocatori.columns else da_id
            # ⚠️ SOLO il livello `Partita` ha un match_uid. `Rosa` è
            # l'anagrafica di squadra-stagione e `Stagione` l'aggregato: lì
            # `Data` e `Avversario` sono vuoti, e costruire la chiave lo stesso
            # produceva un `Bundesliga|||wolfsburg` — una chiave sintatticamente
            # valida che nessuna partita ha. Un aggancio che non fallisce e non
            # trova niente è peggio di un NaN: il conteggio lo dà per riuscito.
            giocatori["match_uid"] = (da_id.where(da_id.notna(), da_nome)
                                      if livello == "Partita" else None)
            giocatori["raccolta"] = raccolta
            giocatori["livello"] = livello
            # ⚠️ Due colonne, non una, perché sono due fatti diversi e
            # confonderli costava caro: la prima dice che la riga NON HA l'id
            # di SofaScore (19.569 righe, quasi tutte perché la raccolta non
            # porta quell'id, non perché la fusione sia fallita); la seconda
            # dice che quel giocatore compare GIÀ in quella squadra-partita,
            # ed è l'unica che va davvero esclusa quando si aggrega — 184
            # righe, non 19.569. La nota precedente istruiva a buttarne
            # cento volte tanto.
            giocatori["senza_id_sofascore"] = identificativi.isna()
            if livello == "Partita" and {"Data", "Squadra", "Giocatore"} <= set(
                    giocatori.columns):
                giocatori["giocatore_ripetuto"] = giocatori.duplicated(
                    ["Data", "Squadra", "Giocatore"], keep="first")
            else:
                giocatori["giocatore_ripetuto"] = False
            pezzi.append(giocatori)
    if not pezzi:
        return
    tabella = pd.concat(pezzi, ignore_index=True)
    scrivi("giocatori_partita_tre_fonti", tabella,
           grana="un GIOCATORE in una partita (livello=Partita) / in una rosa "
                 "(Rosa) / in una stagione (Stagione)",
           fonti=["files/tre_fonti_*_2526/giocatori.csv.gz"],
           spezza_per="Competizione",
           note="`giocatore_ripetuto=True` marca il secondo record dello "
                "stesso giocatore nella stessa squadra-partita: è quello da "
                "escludere quando si aggrega. `senza_id_sofascore=True` dice "
                "solo che la riga non porta l'id di SofaScore — quasi sempre "
                "perché la raccolta non ce l'ha, NON perché la fusione sia "
                "fallita: non è un motivo per scartarla. "
                "⚠️ `match_uid` è pieno SOLO sul livello Partita: Rosa e "
                "Stagione non sono grana partita.")


# ════════════════════════════════════════════════════════════════════════════
# 3 · SQUADRA-PARTITA-PERIODO e la CLASSIFICA
# ════════════════════════════════════════════════════════════════════════════
def tabella_squadre_tf(raccolte: list[str], per_sofa: dict) -> None:
    """Squadra-partita-PERIODO: Totale, 1° tempo, 2° tempo, supplementari.

    Le 215 colonne restano tutte, col nome della fonte dentro: due fonti che
    misurano la stessa grandezza non sono la stessa colonna.
    """
    pezzi = []
    for raccolta in raccolte:
        squadre = tf.squadre(raccolta, spareggio=True)
        if squadre.empty:
            continue
        squadre = squadre.copy()
        identificativi = squadre.get("ID partita (SofaScore)")
        squadre["match_uid"] = (identificativi.map(per_sofa)
                                if identificativi is not None else None)
        squadre["raccolta"] = raccolta
        # il punteggio riparato, come nel file unico
        if "Gol casa (SofaScore)" in squadre.columns:
            casa_reg, via_reg = tf.punteggio_vero(squadre)
            squadre["Gol casa regolamentari"] = casa_reg
            squadre["Gol trasferta regolamentari"] = via_reg
            squadre["Rigori nel punteggio grezzo"] = tf.RIGORI_NEL_PUNTEGGIO.get(
                raccolta, False)
        pezzi.append(squadre)
    if not pezzi:
        return
    tabella = pd.concat(pezzi, ignore_index=True)
    scrivi("squadre_partita_tre_fonti", tabella,
           spezza_per="Competizione",
           grana="una SQUADRA in una partita, per PERIODO "
                 "(Totale / 1° tempo / 2° tempo / supplementari)",
           fonti=["files/tre_fonti_*_2526/squadre.csv.gz"],
           note="`Gol casa/trasferta regolamentari` è il punteggio con la "
                "lotteria dei rigori scorporata dove l'export la somma "
                "(Europa League e Conference).")


def tabella_classifiche(raccolte: list[str]) -> None:
    """La classifica finale, in tre versioni per squadra (generale/casa/fuori).

    ⚠️ È la classifica di FINE stagione: su una partita di ottobre è
    look-ahead puro. Sta qui perché è dato che il repo ha, non perché sia
    usabile come feature — e sta in un file suo proprio per non confondersi
    con le righe di partita.
    """
    pezzi = []
    for raccolta in raccolte:
        try:
            classifica = tf.classifica(raccolta)
        except (FileNotFoundError, KeyError, ValueError):
            continue
        if classifica.empty:
            continue
        classifica = classifica.copy()
        classifica["raccolta"] = raccolta
        classifica["competizione"] = TF_COMPETIZIONE.get(raccolta)
        pezzi.append(classifica)
    if not pezzi:
        return
    scrivi("classifiche.csv.gz", pd.concat(pezzi, ignore_index=True),
           grana="una SQUADRA in una classifica (generale / casa / trasferta)",
           fonti=["files/tre_fonti_*_2526/squadre.csv.gz (livello Stagione)"],
           note="Classifica FINALE: R8, è look-ahead per ogni partita "
                "della stagione.")


# ════════════════════════════════════════════════════════════════════════════
# 4 · EVENTI — le sette categorie, ognuna con la sua grana
# ════════════════════════════════════════════════════════════════════════════
def tabella_eventi_tf(raccolte: list[str], per_sofa: dict) -> None:
    """Il contenitore a sette categorie, un file per categoria.

    ⚠️ Le sette categorie hanno **grane diverse** (`tf.GRANA`): cinque
    descrivono la partita, due la squadra. Leggerle insieme dà un frame con 47
    colonne piene a macchia di leopardo — per questo qui sono file separati.

    ⚠️ L'aggancio si fa per `ID partita (SofaScore)`: su 9 partite le righe
    `Tiro` di Understat portano una data diversa da quelle di SofaScore, e con
    la chiave per nome e data metà dei tiri sparirebbe in silenzio.
    """
    per_categoria: dict[str, list] = defaultdict(list)
    for raccolta in raccolte:
        eventi = tf.eventi(raccolta, spareggio=True)
        if eventi.empty:
            continue
        eventi = eventi.copy()
        identificativi = eventi.get("ID partita (SofaScore)")
        da_id = (identificativi.map(per_sofa) if identificativi is not None
                 else pd.Series(None, index=eventi.index, dtype="object"))
        # ⚠️ Nelle raccolte UEFA e nelle supercoppe `ID partita (SofaScore)` è
        # VUOTA nel file degli eventi: agganciare solo per id lasciava 17.941
        # righe su 73.983 senza `match_uid` — e sono le coppe, cioè proprio le
        # competizioni per cui questa cartella esiste. Lì ci sono `Casa` e
        # `Trasferta` per esteso, quindi il ripiego per nome e data è sicuro.
        competizione = TF_COMPETIZIONE.get(raccolta)
        da_nome = pd.Series(
            [chiave_partita(competizione, d, c, t) for d, c, t
             in zip(eventi["Data"], eventi["Casa"], eventi["Trasferta"])],
            index=eventi.index)
        eventi["match_uid"] = da_id.where(da_id.notna(), da_nome)
        eventi["raccolta"] = raccolta
        for categoria, gruppo in eventi.groupby("Categoria", sort=False):
            per_categoria[str(categoria)].append(
                gruppo.dropna(axis=1, how="all"))

    etichette = {"Cronaca": "cronaca", "Momentum": "momentum", "Quota": "quote",
                 "Tiro": "tiri", "Evento": "eventi", "Serie": "serie",
                 "Migliore in campo": "migliore_in_campo"}
    for categoria, pezzi in per_categoria.items():
        nome = etichette.get(categoria,
                             categoria.lower().replace(" ", "_"))
        tabella = pd.concat(pezzi, ignore_index=True)
        scrivi(f"{nome}.csv.gz", tabella,
               grana=f"un evento di categoria «{categoria}» "
                     f"({tf.GRANA.get(categoria, '?')})",
               fonti=["files/tre_fonti_*_2526/eventi.csv.gz"],
               note=f"categoria {categoria}; la grana la dichiara tf.GRANA")


# ════════════════════════════════════════════════════════════════════════════
# 5 · DIRETTA.IT — 5 campionati e 6 coppe, tre famiglie di schemi
# ════════════════════════════════════════════════════════════════════════════
DIRETTA_LEGHE = {"serie_a": "Serie A", "premier_league": "Premier League",
                 "la_liga": "LaLiga", "bundesliga": "Bundesliga",
                 "ligue_1": "Ligue 1"}
FILES = RADICE / "files"


def _uid_diretta(competizione: str, riga: pd.Series) -> str:
    """Da (Data, Squadra, Campo, Avversario) al `match_uid`."""
    casa = riga["Squadra"] if riga["Campo"] == "Casa" else riga["Avversario"]
    via = riga["Avversario"] if riga["Campo"] == "Casa" else riga["Squadra"]
    return chiave_partita(competizione, riga["Data"], casa, via)


def tabelle_diretta_campionati() -> None:
    """Le raccolte diretta.it dei 5 campionati: 97 statistiche per giocatore,
    45 per squadra e periodo, più i quattro fogli che solo Bundesliga e
    Ligue 1 hanno (partite, formazioni, cambi, eventi).

    ⚠️ Non sono un doppione di SofaScore anche dove le grandezze si chiamano
    uguale: sono un'altra misura della stessa partita, e hanno voci che
    l'altra fonte non ha (`Gol concessi` individuale, gli ingressi in area, i
    passaggi progressivi).
    """
    from src.data import player_stats as ps, team_stats as ts

    famiglie: dict[str, list] = defaultdict(list)
    for lega, competizione in DIRETTA_LEGHE.items():
        squadre = ts.load_team_matches(lega=lega)
        if not squadre.empty:
            squadre = squadre.copy()
            squadre["competizione"] = competizione
            squadre["match_uid"] = [_uid_diretta(competizione, r)
                                    for _, r in squadre.iterrows()]
            famiglie["squadre_partita_diretta"].append(squadre)

        giocatori = ps.load_player_matches(lega=lega)
        if not giocatori.empty:
            giocatori = giocatori.copy()
            giocatori["competizione"] = competizione
            giocatori["match_uid"] = [_uid_diretta(competizione, r)
                                      for _, r in giocatori.iterrows()]
            famiglie["giocatori_partita_diretta"].append(giocatori)

        stagionale = ps.load_season_totals(lega=lega)
        if not stagionale.empty:
            stagionale = stagionale.copy()
            stagionale["competizione"] = competizione
            famiglie["giocatori_stagione_diretta"].append(stagionale)

        # i quattro fogli in più di Bundesliga e Ligue 1
        for cosa, funzione in (("formazioni_diretta", "load_lineups"),
                               ("cambi_diretta", "load_substitutions"),
                               ("eventi_diretta", "load_events"),
                               ("elenco_partite_diretta", "load_match_list")):
            try:
                frame = getattr(ps, funzione)(lega=lega)
            except (FileNotFoundError, KeyError, ValueError, AttributeError):
                continue
            if frame.empty:
                continue
            frame = frame.copy()
            frame["competizione"] = competizione
            if {"Squadra", "Campo"} <= set(frame.columns):
                avversari = {}
                if not squadre.empty:
                    for _, r in squadre.iterrows():
                        avversari[(r["Data"], r["Squadra"])] = r["Avversario"]
                frame["Avversario"] = [
                    avversari.get((d, s)) for d, s in zip(frame["Data"],
                                                          frame["Squadra"])]
                frame["match_uid"] = [
                    _uid_diretta(competizione, r) if pd.notna(r["Avversario"])
                    else None for _, r in frame.iterrows()]
            famiglie[cosa].append(frame)

    for nome, pezzi in famiglie.items():
        if not pezzi:
            continue
        scrivi(f"{nome}.csv.gz", pd.concat(pezzi, ignore_index=True),
               grana=nome.replace("_", " "),
               fonti=[f"files/diretta_{l}_2526/" for l in DIRETTA_LEGHE],
               note="formazioni/cambi/eventi/elenco esistono SOLO per "
                    "Bundesliga e Ligue 1: le altre tre raccolte non li hanno.")


def tabelle_diretta_coppe(mappa_coppe: dict) -> None:
    """Le sei cartelle di coppa di diretta.it, che nessun modulo di `src/data/`
    legge: il loro manifesto si chiama `manifesto_coppa.json` e i due
    caricatori dei campionati non lo vedono.

    ⚠️ Le loro statistiche di squadra hanno colonne di TESTO COMPOSITO
    (`86% (387/448)`): restano come sono — scomporle sarebbe modificare il
    dato — e il README della cartella lo dichiara.
    """
    famiglie: dict[str, list] = defaultdict(list)
    for cartella in sorted(FILES.glob("diretta_*_2526")):
        if not (cartella / "manifesto_coppa.json").exists():
            continue
        for nome_file in ("partite", "formazioni_e_cambi", "eventi",
                          "stat_giocatori", "stat_squadra", "note"):
            percorso = cartella / f"{nome_file}.csv"
            if not percorso.exists():
                continue
            frame = pd.read_csv(percorso, low_memory=False)
            frame["cartella"] = cartella.name
            if {"Competizione", "Data", "Casa"} <= set(frame.columns):
                colonna_ospite = "Ospite" if "Ospite" in frame.columns else "Trasferta"
                frame["match_uid"] = [
                    mappa_coppe.get((canon_competizione(c), norm_data(d),
                                     norm_squadra(x), norm_squadra(y)))
                    for c, d, x, y in zip(frame["Competizione"], frame["Data"],
                                          frame["Casa"], frame[colonna_ospite])]
            famiglie[f"coppe_diretta_{nome_file}"].append(frame)

    for nome, pezzi in famiglie.items():
        if not pezzi:
            continue
        scrivi(f"{nome}.csv.gz", pd.concat(pezzi, ignore_index=True),
               grana=nome.replace("coppe_diretta_", "").replace("_", " "),
               fonti=["files/diretta_{coppa}_2526/"],
               note="raccolta manuale diretta.it delle 6 coppe nazionali; "
                    "nessun modulo di src/data/ la legge.")


# ════════════════════════════════════════════════════════════════════════════
# 6 · COPPE NAZIONALI — data/coppe_2526
# ════════════════════════════════════════════════════════════════════════════
COPPE_DIR = RADICE / "data" / "coppe_2526"


def tabelle_coppe() -> dict:
    """Le 11 tabelle di `data/coppe_2526/`, e la mappa che le lega.

    Torna la mappa `(competizione, data, casa, ospite) → match_uid` con cui le
    raccolte diretta.it delle coppe si riagganciano.
    """
    partite = pd.read_csv(COPPE_DIR / "partite.csv", low_memory=False)
    partite["competizione"] = partite["competizione"].map(canon_competizione)
    partite["match_uid"] = [chiave_partita(c, d, x, y) for c, d, x, y
                            in zip(partite["competizione"], partite["data"],
                                   partite["casa"], partite["ospite"])]
    per_game = {r["game_id"]: r["match_uid"] for _, r in partite.iterrows()
                if pd.notna(r.get("game_id"))}

    # il ponte: i nomi di diretta.it verso il match_uid
    ponte = pd.read_csv(COPPE_DIR / "aggancio_partite.csv", low_memory=False)
    mappa_nomi: dict[tuple, str] = {}
    for _, riga in ponte.iterrows():
        uid = per_game.get(riga.get("game_id"))
        if uid:
            mappa_nomi[(canon_competizione(riga["competizione"]),
                        norm_data(riga["data"]), norm_squadra(riga["casa"]),
                        norm_squadra(riga["ospite"]))] = uid
    for _, riga in partite.iterrows():
        mappa_nomi.setdefault((riga["competizione"], norm_data(riga["data"]),
                               norm_squadra(riga["casa"]),
                               norm_squadra(riga["ospite"])), riga["match_uid"])

    scrivi("coppe_partite.csv.gz", partite, grana="una partita di coppa",
           fonti=["data/coppe_2526/partite.csv"],
           note="`gol_*_dichiarato` è il grezzo di games.csv e SOMMA la "
                "lotteria dei rigori su 68 partite: usare `gol_*_90` e "
                "`gol_*_finale`, che sono ricostruiti dagli eventi.")

    for nome_file, chiave_id in (("formazioni", "game_id"),
                                 ("eventi", "game_id"),
                                 ("aggancio_giocatori", "game_id"),
                                 ("aggancio_squadre", None),
                                 ("aggancio_partite", "game_id"),
                                 ("incrocio_per_partita", "game_id"),
                                 ("da_raccogliere", None),
                                 ("aggancio_statistiche", "game_id"),
                                 ("aggancio_statistiche_squadra", "game_id"),
                                 ("aggancio_eventi", "game_id")):
        percorso = COPPE_DIR / f"{nome_file}.csv"
        if not percorso.exists():
            continue
        frame = pd.read_csv(percorso, low_memory=False)
        if chiave_id and chiave_id in frame.columns:
            frame["match_uid"] = frame[chiave_id].map(per_game)
        colonne = set(frame.columns)
        if "match_uid" not in colonne or frame["match_uid"].isna().any():
            # ripiego sui nomi di diretta.it, dove la tabella li ha
            casa = "Casa" if "Casa" in colonne else "casa"
            ospite = ("Ospite" if "Ospite" in colonne
                      else ("ospite" if "ospite" in colonne else None))
            data = "Data" if "Data" in colonne else "data"
            comp = ("competizione" if "competizione" in colonne
                    else ("Competizione" if "Competizione" in colonne else None))
            if ospite and comp and data in colonne and casa in colonne:
                ripiego = [mappa_nomi.get((canon_competizione(c), norm_data(d),
                                           norm_squadra(x), norm_squadra(y)))
                           for c, d, x, y in zip(frame[comp], frame[data],
                                                 frame[casa], frame[ospite])]
                if "match_uid" in colonne:
                    frame["match_uid"] = frame["match_uid"].where(
                        frame["match_uid"].notna(), pd.Series(ripiego,
                                                              index=frame.index))
                else:
                    frame["match_uid"] = ripiego
        scrivi(f"coppe_{nome_file}.csv.gz", frame,
               grana=nome_file.replace("_", " "),
               fonti=[f"data/coppe_2526/{nome_file}.csv"])
    return mappa_nomi


# ════════════════════════════════════════════════════════════════════════════
# 7 · COPPE EUROPEE (SofaScore), SNAPSHOT, QUOTE GREZZE, PLAYER-SCORES
# ════════════════════════════════════════════════════════════════════════════
SOF_DIR = FILES / "sofascore_coppe_europee_2526"


def tabelle_coppe_europee(per_sofa: dict) -> None:
    """Champions, Europa e Conference: i sei CSV e i SETTE fogli dell'`.xlsx`.

    ⚠️ Tre fogli non hanno un CSV gemello e vivono solo nell'`.xlsx`:
    `Partite` (il più ricco della consegna: arbitro con lo storico di carriera,
    stadio con capienza e coordinate, superficie), `Posizioni medie` e
    `Colori maglie`. Leggerli da lì non è un vezzo, è l'unico modo di averli.
    """
    if not SOF_DIR.exists():
        return
    fogli = pd.ExcelFile(SOF_DIR / "originale_sofascore.xlsx")
    partite = fogli.parse("Partite")
    partite["competizione"] = partite["Competizione"].map(canon_competizione)
    partite["match_uid"] = [chiave_partita(c, d, x, y) for c, d, x, y
                            in zip(partite["competizione"], partite["Data"],
                                   partite["Casa"], partite["Trasferta"])]
    per_id = dict(zip(partite["ID partita"], partite["match_uid"]))
    scrivi("uefa_partite_sofascore.csv.gz", partite,
           grana="una partita di coppa UEFA",
           fonti=["files/sofascore_coppe_europee_2526/originale_sofascore.xlsx"],
           note="il foglio `Partite` non ha un CSV gemello nella consegna.")

    for nome_file in ("giocatori", "statistiche_squadra", "eventi", "tiri",
                      "momentum", "cambi"):
        percorso = SOF_DIR / f"{nome_file}.csv.gz"
        if not percorso.exists():
            continue
        frame = pd.read_csv(percorso, low_memory=False)
        if "ID partita" in frame.columns:
            frame["match_uid"] = frame["ID partita"].map(per_id)
        scrivi(f"uefa_{nome_file}.csv.gz", frame,
               grana=nome_file.replace("_", " "),
               fonti=[f"files/sofascore_coppe_europee_2526/{nome_file}.csv.gz"])

    for foglio, nome in (("Posizioni medie", "uefa_posizioni_medie"),
                         ("Colori maglie", "uefa_colori_maglie"),
                         ("Note e copertura", "uefa_note_copertura")):
        if foglio not in fogli.sheet_names:
            continue
        frame = fogli.parse(foglio)
        colonna = next((c for c in frame.columns if "ID partita" in c), None)
        if colonna:
            frame["match_uid"] = frame[colonna].map(per_id)
        scrivi(f"{nome}.csv.gz", frame, grana=foglio.lower(),
               fonti=["files/sofascore_coppe_europee_2526/originale_sofascore.xlsx"],
               note="foglio senza CSV gemello nella consegna.")


SNAPSHOT_COMPETIZIONE = {"serie_a": "Serie A", "premier_league": "Premier League",
                         "la_liga": "LaLiga", "bundesliga": "Bundesliga",
                         "ligue_1": "Ligue 1"}


def tabella_snapshot() -> None:
    """Gli snapshot congelati, stagione 2526: le 40 colonne su cui gira il
    modello del progetto (quote medie multi-book, xG/PPDA Understat, riposo
    vero da calendario, stime dichiarate sugli assenti)."""
    pezzi = []
    for lega, competizione in SNAPSHOT_COMPETIZIONE.items():
        percorso = RADICE / "data" / f"{lega}_matches.csv"
        if not percorso.exists():
            continue
        frame = pd.read_csv(percorso)
        frame = frame[frame["season"] == 2526].copy()
        frame["competizione"] = competizione
        frame["match_uid"] = [chiave_partita(competizione, d, c, t) for d, c, t
                              in zip(frame["date"], frame["home_team"],
                                     frame["away_team"])]
        pezzi.append(frame)
    if pezzi:
        scrivi("snapshot_partite.csv.gz", pd.concat(pezzi, ignore_index=True),
               grana="una partita dei 5 campionati (snapshot congelato)",
               fonti=["data/{lega}_matches.csv"],
               note="⚠️ `home/away_absent_*_est` è un finto pieno sul 2025-26: "
                    "il dump infortuni è congelato a settembre 2025, da ottobre "
                    "lo 0.0 significa «non lo so» (R6).")


FD_GREZZO = {
    "serie_a": ("Serie A", RADICE / "data" / "football_data_raw" / "serie_a_2526.csv"),
    "premier_league": ("Premier League",
                       FILES / "football_data_premier_league_bundle.json"),
    "la_liga": ("LaLiga", FILES / "football_data_la_liga_bundle.json"),
}


def tabella_football_data() -> None:
    """I CSV di football-data come arrivano: 131 colonne, non le 10 dello
    snapshot. Dentro c'è **l'handicap asiatico al completo** — l'unico mercato
    che il progetto abbia validato contro una quota esterna (Fase 88) — più i
    singoli bookmaker uno per uno, i falli, i corner e i cartellini.

    ⚠️ Copre tre leghe su cinque: per Bundesliga e Ligue 1 il grezzo non è
    archiviato (la Fase 100 le ha scaricate tenendo solo lo snapshot).
    """
    import io
    pezzi = []
    for lega, (competizione, percorso) in FD_GREZZO.items():
        if not percorso.exists():
            continue
        if percorso.suffix == ".json":
            testo = json.loads(percorso.read_text()).get(f"{lega}_2526.csv")
            if not testo:
                continue
            frame = pd.read_csv(io.StringIO(testo))
        else:
            frame = pd.read_csv(percorso, encoding="latin-1")
        frame.columns = [c.lstrip("﻿") for c in frame.columns]
        frame["competizione"] = competizione
        frame["match_uid"] = [chiave_partita(competizione, norm_data(d), c, t)
                              for d, c, t in zip(frame["Date"],
                                                 frame["HomeTeam"],
                                                 frame["AwayTeam"])]
        pezzi.append(frame)
    if pezzi:
        scrivi("quote_football_data.csv.gz", pd.concat(pezzi, ignore_index=True),
               grana="una partita, con le ~108 colonne di quota della fonte",
               fonti=["data/football_data_raw/", "files/football_data_*_bundle.json"],
               note="Serie A, Premier e Liga. Bundesliga e Ligue 1 non hanno il "
                    "grezzo archiviato: buco dichiarato.")


def tabelle_player_scores() -> None:
    """Gli otto file di `files/player_scores/` (Transfermarkt via Kaggle).

    `games` porta arbitro e allenatori per **tutte** le competizioni;
    `appearances` è l'unica fonte per giocatore che copre le coppe minori con
    la stessa struttura, e porta il `player_id` — la chiave con cui un
    giocatore si segue fra competizioni e stagioni.

    ⚠️ `red_cards` di `appearances` è un finto pieno sul 2025-26: vale 0 su
    tutte e 76.887 le righe del perimetro, mentre le stesse competizioni nel
    2024-25 ne contano 265.
    ⚠️ `clubs.coach_name` è l'allenatore CORRENTE, senza data: usarla per una
    partita di ottobre è look-ahead.
    """
    from src.data import allenatori as al

    partite = al.load_partite()
    partite = partite[partite["casa"] & (partite["season"] == 2025)].copy()
    partite["competizione"] = partite["competition_id"].map(PS_COMPETIZIONE)
    nostre = partite[partite["competizione"].notna()].copy()
    nostre["match_uid"] = [chiave_partita(c, d, x, y) for c, d, x, y
                           in zip(nostre["competizione"], nostre["date"],
                                  nostre["club_name"], nostre["avversario_name"])]

    # ⚠️ Sulle coppe UEFA i nomi di Transfermarkt e quelli di SofaScore non
    # coincidono («Paris Saint-Germain» contro «PSG»), e 471 partite restavano
    # con una chiave che nessuna riga di `partite.csv.gz` ha: il dato c'era da
    # entrambe le parti, era la chiave a non incontrarsi. Stessa regola delle
    # coppe nazionali — inclusione fra insiemi di parole, accettata solo se in
    # quel giorno resta UNA candidata sola.
    spina = pd.read_csv(CARTELLA / "partite.csv.gz", low_memory=False,
                        usecols=["match_uid"]) if (CARTELLA / "partite.csv.gz").exists() else None
    note = set(spina["match_uid"]) if spina is not None else set()
    if note:
        per_giorno: dict[tuple, list] = defaultdict(list)
        for chiave in note:
            pezzi = chiave.split("|")
            if len(pezzi) == 4:
                per_giorno[(pezzi[0], pezzi[1])].append((pezzi[2], pezzi[3], chiave))

        def _compatibili(uno: str, altro: str) -> bool:
            if not uno or not altro:
                return False
            if uno == altro:
                return True
            a, b = set(uno.split()), set(altro.split())
            return a <= b or b <= a

        riparate, nuove = 0, []
        for chiave, competizione, data, casa, via in zip(
                nostre["match_uid"], nostre["competizione"], nostre["date"],
                nostre["club_name"], nostre["avversario_name"]):
            if chiave in note:
                nuove.append(chiave)
                continue
            candidate = [k for c, t, k
                         in per_giorno.get((competizione, norm_data(data)), [])
                         if _compatibili(norm_squadra(casa), c)
                         and _compatibili(norm_squadra(via), t)]
            if len(candidate) == 1:
                nuove.append(candidate[0])
                riparate += 1
            else:
                nuove.append(None)
        nostre["match_uid"] = nuove
        log.info("  Transfermarkt: %d partite agganciate per abbreviazione, "
                 "%d senza chiave", riparate, sum(1 for k in nuove if k is None))
    per_game = dict(zip(nostre["game_id"], nostre["match_uid"]))
    # ⚠️ `partite` tiene TUTTE le 9.554 partite 2025-26 che Transfermarkt
    # censisce, non solo le nostre: 44 competizioni fuori perimetro comprese.
    # `match_uid` è pieno solo dove la partita è nel perimetro — ed è giusto
    # così: una partita di Eredivisie non ha una riga in `partite.csv.gz`.
    # ⚠️ `partite` tiene tutte le 9.554 partite 2025-26 che Transfermarkt
    # censisce, 44 competizioni fuori perimetro comprese. La cartella è della
    # NOSTRA stagione: restano le nostre 22 competizioni, e il resto no.
    # ⚠️ 33 righe portano `season=2025` ma una data fuori stagione (32 sono
    # amichevoli di nazionale del giugno 2024): la stagione la decide la DATA,
    # non l'etichetta.
    partite = nostre.copy()
    quando = pd.to_datetime(partite["date"], errors="coerce")
    prima = len(partite)
    partite = partite[(quando >= "2025-07-01") & (quando <= "2026-07-01")].copy()
    if len(partite) != prima:
        log.info("    partite Transfermarkt fuori stagione scartate: %d",
                 prima - len(partite))
    scrivi("transfermarkt_partite.csv.gz", partite,
           grana="una partita 2025-26 delle nostre 22 competizioni, "
                 "vista da Transfermarkt",
           fonti=["files/player_scores/games.csv.gz"],
           note="`manager_name` è CHI SEDEVA IN PANCHINA quella partita, non "
                "chi era in carica: 836 mandati su 13.810 sono un vice per "
                "una gara sola.")

    cartella = FILES / "player_scores"
    # il perimetro: chi è sceso in campo e quali club hanno giocato. Serve a
    # tenere fuori dalla cartella della stagione i 50.149 giocatori e i 796
    # club di ogni epoca che i file di Transfermarkt portano per costruzione.
    percorso_presenze = cartella / "appearances.csv.gz"
    giocatori_2526: set = set()
    if percorso_presenze.exists():
        indice = pd.read_csv(percorso_presenze, low_memory=False,
                             usecols=["game_id", "player_id"])
        giocatori_2526 = set(indice[indice["game_id"].isin(per_game)]["player_id"])
    club_2526 = set(nostre["club_id"]) | set(nostre["avversario_id"])
    competizioni_2526 = set(nostre["competition_id"])

    for nome_file in ("appearances", "club_games", "players", "clubs",
                      "player_valuations", "club_names", "competitions"):
        percorso = cartella / f"{nome_file}.csv.gz"
        if not percorso.exists():
            continue
        frame = pd.read_csv(percorso, low_memory=False)
        prima = len(frame)
        if "game_id" in frame.columns:
            frame["match_uid"] = frame["game_id"].map(per_game)
            # solo il perimetro: `appearances` ha 1,89 M di righe su tutto il
            # mondo e tutte le stagioni, qui interessano le nostre partite
            frame = frame[frame["match_uid"].notna()].copy()
        elif nome_file == "player_valuations":
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
            frame = frame[(frame["date"] >= "2025-06-01")
                          & (frame["date"] <= "2026-08-01")
                          & frame["player_id"].isin(giocatori_2526)].copy()
        elif nome_file == "players" and giocatori_2526:
            frame = frame[frame["player_id"].isin(giocatori_2526)].copy()
        elif nome_file in ("clubs", "club_names") and club_2526:
            frame = frame[frame["club_id"].isin(club_2526)].copy()
        elif nome_file == "competitions" and competizioni_2526:
            frame = frame[frame["competition_id"].isin(competizioni_2526)].copy()
        if len(frame) != prima:
            log.info("    %s ristretto al perimetro: %d righe su %d",
                     nome_file, len(frame), prima)
        scrivi(f"transfermarkt_{nome_file}.csv.gz", frame,
               grana=nome_file.replace("_", " "),
               fonti=[f"files/player_scores/{nome_file}.csv.gz"],
               note=("⚠️ `red_cards` vale 0 su tutte le righe del 2025-26: "
                     "finto pieno (R6)." if nome_file == "appearances" else
                     "⚠️ `coach_name` è l'allenatore CORRENTE: look-ahead."
                     if nome_file == "clubs" else ""))


# ════════════════════════════════════════════════════════════════════════════
# 8 · ANAGRAFICHE E CONTORNO — ciò che non dipende dalla singola partita
# ════════════════════════════════════════════════════════════════════════════
def _perimetro_2526() -> tuple[set, set]:
    """I `player_id` e i `club_id` che il 2025-26 tocca davvero.

    ⚠️ Serve a una regola dell'utente: la cartella deve contenere **solo** la
    stagione 2025-26. Le anagrafiche di Transfermarkt e le carriere di
    Wikipedia coprono per costruzione ogni epoca — 50.149 giocatori e 209.809
    tappe di carriera dal secolo scorso. Tenerle intere vorrebbe dire mettere
    nella cartella della stagione dati di trent'anni fa; buttarle vorrebbe dire
    non poter leggere il nome di chi ha giocato. Il taglio giusto è il
    **perimetro**: chi è sceso in campo, e i club che hanno giocato.
    """
    from src.data import allenatori as al

    percorso = FILES / "player_scores" / "appearances.csv.gz"
    partite = al.load_partite()
    partite = partite[partite["season"] == 2025]
    partite = partite[partite["competition_id"].map(PS_COMPETIZIONE).notna()]
    club = set(partite["club_id"]) | set(partite["avversario_id"])
    giocatori: set = set()
    if percorso.exists():
        presenze = pd.read_csv(percorso, low_memory=False,
                               usecols=["game_id", "player_id"])
        presenze = presenze[presenze["game_id"].isin(set(partite["game_id"]))]
        giocatori = set(presenze["player_id"])
    log.info("  perimetro 2025-26: %d giocatori · %d club",
             len(giocatori), len(club))
    return giocatori, club


def tabelle_anagrafiche() -> None:
    """Coefficienti UEFA, valori rosa, calendario di club, identità degli
    allenatori, carriere dei giocatori, registro delle correzioni.

    Sono `statico` o di grana squadra-stagione: non hanno un `match_uid` e non
    devono averlo. Si agganciano per nome di club o per `player_id`.
    """
    from src.data import ranking_uefa as ru

    try:
        club = ru.club()
        club["_norm"] = club["Club"].map(norm_squadra)
        scrivi("anagrafiche/ranking_uefa_club.csv.gz", club,
               grana="un club nel ranking UEFA",
               fonti=["data/ranking_uefa/"],
               note="⚠️ il coefficiente è MAX(somma 5 stagioni; 20% della "
                    "federazione) e il pavimento morde su 146 club su 410: "
                    "per quelli il numero misura il PAESE, non la squadra.")
    except (FileNotFoundError, ValueError, KeyError):
        log.warning("ranking UEFA club non leggibile")

    # ⚠️ Solo la finestra 2025-26: quella 2026-27 esiste nel file e decide
    # l'access list dell'anno DOPO — è dato di un'altra stagione (R8).
    for finestra in ("2025-26",):
        try:
            federazioni = ru.federazioni(finestra)
        except (FileNotFoundError, ValueError, KeyError):
            continue
        scrivi(f"anagrafiche/ranking_uefa_federazioni_{finestra}.csv.gz",
               federazioni, grana="una federazione nel ranking UEFA",
               fonti=["data/ranking_uefa/"],
               note="⚠️ due finestre, e decidono due access list diverse: "
                    "usare quella di oggi per una partita di ieri è "
                    "look-ahead (R8).")

    semplici = [
        ("data/squad_value_2526_transfermarkt.csv", "anagrafiche/valore_rose_transfermarkt.csv.gz",
         "una squadra-stagione", "fonte secondaria dichiarata (R2): copre le "
         "16 squadre che player-scores non ha."),
        ("data/presenze_integrate.csv", "anagrafiche/presenze_integrate.csv.gz", "", ""),
        ("data/aggancio_manuale.csv", "anagrafiche/aggancio_manuale.csv.gz", "", ""),
        ("data/correzioni_dichiarate.csv", "anagrafiche/correzioni_dichiarate.csv.gz",
         "una correzione", "il registro R3: ogni correzione con valore-prima, "
         "motivo, fonte, chi ha deciso e quando."),
    ]
    for origine, destinazione, grana, nota in semplici:
        percorso = RADICE / origine
        if not percorso.exists():
            continue
        frame = pd.read_csv(percorso, low_memory=False)
        if "season" in frame.columns:
            # le correzioni dichiarate coprono nove stagioni: qui la nostra
            frame = frame[frame["season"].astype(str).str.contains("2526")].copy()
        scrivi(destinazione, frame,
               grana=grana or destinazione.split("/")[-1].replace(".csv.gz", ""),
               fonti=[origine], note=nota)

    giocatori_2526, club_2526 = _perimetro_2526()

    carriere = RADICE / "data" / "carriere_wikipedia" / "tappe.csv.gz"
    if carriere.exists() and giocatori_2526:
        tappe = pd.read_csv(carriere, low_memory=False)
        dentro = tappe[tappe["player_id"].isin(giocatori_2526)].copy()
        scrivi("anagrafiche/carriere_wikipedia.csv.gz", dentro,
               grana="una tappa di carriera di un giocatore sceso in campo "
                     "nel 2025-26",
               fonti=["data/carriere_wikipedia/tappe.csv.gz"],
               note=f"ristretta al perimetro: {len(dentro)} tappe su "
                    f"{len(tappe)}. Le tappe sono di ogni epoca — è la "
                    "carriera — ma i giocatori sono quelli del 2025-26.")

    cartella_wikidata = RADICE / "data" / "allenatori_wikidata"
    for percorso in sorted(cartella_wikidata.glob("*.csv")):
        frame = pd.read_csv(percorso, low_memory=False)
        if "club_id" in frame.columns and club_2526:
            frame = frame[frame["club_id"].isin(club_2526)].copy()
        scrivi(f"anagrafiche/allenatori_wikidata_{percorso.stem}.csv.gz",
               frame,
               grana=percorso.stem.replace("_", " "),
               fonti=[str(percorso.relative_to(RADICE))],
               note="⚠️ il NOME non è un'identità: 11 omonimi dimostrati. "
                    "Il QID sì.")

    calendari = []
    for percorso in sorted((RADICE / "data").glob("club_fixtures*.csv")):
        frame = pd.read_csv(percorso)
        frame["file"] = percorso.name
        calendari.append(frame)
    if calendari:
        tutto = pd.concat(calendari, ignore_index=True)
        scrivi("anagrafiche/calendario_club.csv.gz",
               tutto[tutto["season"] == 2526].copy(),
               grana="una partita nel calendario COMPLETO di un club "
                     "(coppe ed Europa comprese)",
               fonti=["data/club_fixtures*.csv"],
               note="è la fonte del riposo vero e della congestione: copre le "
                    "partite che i 5 campionati non vedono.")

    # ⚠️ Le stime dichiarate coprono 2017-2122: qui entra solo ciò che tocca
    # la nostra stagione, e quasi nulla la tocca. Una stima del 2017-19 in una
    # cartella intitolata 2025-26 sarebbe un dato di un'altra stagione.
    stime = RADICE / "data" / "estimates"
    if stime.exists():
        for percorso in sorted(stime.glob("*.csv")):
            try:
                frame = pd.read_csv(percorso, low_memory=False)
            except (OSError, ValueError):
                continue
            # ⚠️ La colonna della stagione si chiama `season` in un file e
            # `stagione` in un altro: guardarne una sola lasciava passare 32
            # righe del 2018-19 e del 2020-21 dentro la cartella del 2025-26.
            for colonna in ("season", "stagione"):
                if colonna in frame.columns:
                    frame = frame[frame[colonna].astype(str)
                                  .str.contains("2526")].copy()
            if frame.empty:
                log.info("  stime %-30s nessuna riga 2025-26, non scritta",
                         percorso.stem)
                continue
            scrivi(f"anagrafiche/stime_{percorso.stem}.csv.gz", frame,
                   grana="una stima dichiarata",
                   fonti=[str(percorso.relative_to(RADICE))],
                   note="⚠️ STIMA, non misura: vedi data/estimates/README.md. "
                        "Mai usarla per simulare ROI.")


def tabelle_metadati(raccolte: list[str]) -> None:
    """Le legende e i manifesti delle raccolte: dicono cosa significa ogni
    colonna, quale fonte l'ha prodotta e con che copertura.

    Non sono dati di partita, ma senza di loro metà delle colonne di questa
    cartella sono nomi senza definizione — e i manifesti portano gli sha256
    delle consegne, cioè la prova che i file non sono stati toccati.
    """
    legende = []
    for raccolta in raccolte:
        try:
            legenda = tf.legenda(raccolta)
        except (FileNotFoundError, KeyError, ValueError):
            continue
        if legenda.empty:
            continue
        legenda = legenda.copy()
        legenda["raccolta"] = raccolta
        legende.append(legenda)
    if legende:
        scrivi("metadati/legenda_tre_fonti.csv.gz",
               pd.concat(legende, ignore_index=True),
               grana="una colonna documentata",
               fonti=["files/tre_fonti_*_2526/legenda.csv.gz"])

    legende_diretta = []
    for percorso in sorted(FILES.glob("diretta_*_2526/legenda*.csv")):
        try:
            frame = pd.read_csv(percorso)
        except (OSError, ValueError):
            continue
        frame["raccolta"] = percorso.parent.name
        frame["file"] = percorso.name
        legende_diretta.append(frame)
    if legende_diretta:
        scrivi("metadati/legenda_diretta.csv.gz",
               pd.concat(legende_diretta, ignore_index=True),
               grana="una colonna documentata delle raccolte diretta.it",
               fonti=["files/diretta_*_2526/legenda*.csv"])

    manifesti = {}
    for percorso in sorted(FILES.glob("*/manifesto*.json")):
        try:
            manifesti[str(percorso.relative_to(RADICE))] = json.loads(
                percorso.read_text())
        except (OSError, ValueError):
            continue
    for percorso in sorted((RADICE / "data").glob("*/manifesto*.json")):
        try:
            manifesti[str(percorso.relative_to(RADICE))] = json.loads(
                percorso.read_text())
        except (OSError, ValueError):
            continue
    if manifesti:
        (CARTELLA / "metadati").mkdir(parents=True, exist_ok=True)
        destinazione = CARTELLA / "metadati" / "manifesti_delle_raccolte.json"
        destinazione.write_text(json.dumps(manifesti, ensure_ascii=False,
                                           indent=1))
        MANIFESTO["metadati/manifesti_delle_raccolte.json"] = {
            "grana": "un manifesto di consegna",
            "righe": len(manifesti), "colonne": 0, "nomi_colonne": [],
            "fonti": ["files/*/manifesto*.json", "data/*/manifesto*.json"],
            "spezzato_per": None, "aggancio_match_uid": None,
            "note": "gli sha256 delle consegne: la prova che i file non sono "
                    "stati toccati (R3).",
            "pezzi": [{"file": "metadati/manifesti_delle_raccolte.json",
                       "righe": len(manifesti),
                       "mb": round(destinazione.stat().st_size / 1e6, 2),
                       "sha256": _impronta(destinazione)}],
        }
        log.info("  %-38s %9d manifesti", "metadati/manifesti", len(manifesti))


# ════════════════════════════════════════════════════════════════════════════
# 9 · LA TABELLA D'INGRESSO — una riga per partita
# ════════════════════════════════════════════════════════════════════════════
def tabella_partite() -> None:
    """`partite.csv.gz`: la porta d'ingresso della cartella.

    Una riga per partita con l'anagrafica, il risultato, lo stadio, l'arbitro,
    gli allenatori, i moduli, i coefficienti e le statistiche di squadra
    affiancate. È la stessa tabella che il file unico produceva, **meno** i
    pacchetti JSON: quelli qui sono file a sé, al loro grano naturale.

    ⚠️ È una **vista denormalizzata**, comoda ma non la fonte: le statistiche
    di squadra affiancate in `casa_*`/`trasferta_*` sono una proiezione di
    `squadre_partita_tre_fonti.csv.gz`, che è la forma normale. Se le due
    divergono, ha ragione quella.
    """
    from scripts.build_actual_database2526 import Profilo, costruisci

    tabella = costruisci(profilo=Profilo.LEGGERO)
    tabella = tabella.rename(columns={"match_uid": "match_uid"})
    pacchetti = [c for c in tabella.columns
                 if c.endswith("_json") and c != "provenienza_json"]
    tabella = tabella.drop(columns=pacchetti)
    CHIAVI_VALIDE.update(tabella["match_uid"].dropna())
    scrivi("partite.csv.gz", tabella, grana="una PARTITA",
           fonti=["tutte le famiglie, coalescite"],
           note="vista denormalizzata: la forma normale delle statistiche di "
                "squadra è squadre_partita_tre_fonti.csv.gz. "
                "`provenienza_json` dice quale fonte ha vinto per ogni campo "
                "normalizzato.")


# ════════════════════════════════════════════════════════════════════════════
# 10 · MONTAGGIO
# ════════════════════════════════════════════════════════════════════════════
BLOCCHI = {
    "partite": "una riga per partita: la porta d'ingresso",
    "squadre": "squadra-partita-periodo, tre fonti",
    "giocatori": "giocatore-partita, tre fonti (tutti i campi)",
    "eventi": "le 7 categorie di eventi, una per file",
    "posizioni": "4,77 M di posizioni heatmap",
    "eventi_opta": "3,71 M di tocchi Opta",
    "classifiche": "la classifica finale",
    "diretta": "le 11 raccolte diretta.it",
    "coppe": "le coppe nazionali",
    "uefa": "le coppe europee da SofaScore",
    "snapshot": "gli snapshot congelati",
    "quote": "le quote grezze di football-data",
    "transfermarkt": "gli 8 file di player-scores",
    "anagrafiche": "ranking, valori, calendario, identità",
    "metadati": "legende e manifesti delle consegne",
}


def costruisci_cartella(solo: list[str] | None = None) -> None:
    raccolte = tf.leghe_disponibili()
    attivo = (lambda nome: solo is None or nome in solo)

    log.info("── mappe degli identificatori ────────────────────────────────")
    per_sofa, per_ws, _ = mappe_id(raccolte)
    log.info("  %d id SofaScore · %d id WhoScored", len(per_sofa), len(per_ws))

    # ⚠️ `partite.csv.gz` si costruisce PER PRIMA: è l'insieme delle chiavi
    # valide, e i blocchi che agganciano per somiglianza (Transfermarkt sulle
    # coppe UEFA) hanno bisogno di sapere quali chiavi esistono davvero.
    if attivo("partite"):
        tabella_partite()

    log.info("── tre fonti ─────────────────────────────────────────────────")
    if attivo("squadre"):
        tabella_squadre_tf(raccolte, per_sofa)
    if attivo("giocatori"):
        tabella_giocatori_tf(raccolte, per_sofa)
    if attivo("eventi"):
        tabella_eventi_tf(raccolte, per_sofa)
    if attivo("classifiche"):
        tabella_classifiche(raccolte)
    if attivo("posizioni"):
        tabella_posizioni(raccolte, per_sofa, per_ws)
    if attivo("eventi_opta"):
        tabella_eventi_opta(raccolte, per_ws)

    log.info("── coppe nazionali e diretta.it ──────────────────────────────")
    mappa_coppe: dict = {}
    if attivo("coppe"):
        mappa_coppe = tabelle_coppe()
    if attivo("diretta"):
        tabelle_diretta_campionati()
        tabelle_diretta_coppe(mappa_coppe)

    log.info("── coppe europee, snapshot, quote, Transfermarkt ─────────────")
    if attivo("uefa"):
        tabelle_coppe_europee(per_sofa)
    if attivo("snapshot"):
        tabella_snapshot()
    if attivo("quote"):
        tabella_football_data()
    if attivo("transfermarkt"):
        tabelle_player_scores()

    log.info("── anagrafiche e metadati ────────────────────────────────────")
    if attivo("anagrafiche"):
        tabelle_anagrafiche()
    if attivo("metadati"):
        tabelle_metadati(raccolte)




def scrivi_manifesto() -> dict:
    """`MANIFESTO.json`: cosa c'è, quanto pesa, con che impronta.

    È l'unico posto da cui si può dire «non manca niente» senza riaprire i
    file: righe, colonne, nomi delle colonne, fonti, asse di spezzatura, tasso
    di aggancio a `match_uid` e sha256 di ogni pezzo.
    """
    # ⚠️ Le impronte si ricalcolano QUI, non al momento della scrittura: il
    # manifesto deve descrivere il disco **come sta alla fine**, non come stava
    # a metà corsa. Con l'impronta presa al volo, un file riscritto più tardi
    # nella stessa corsa lasciava nel manifesto un sha che non corrispondeva
    # più a niente — e un manifesto che sbaglia l'impronta è peggio che non
    # averla, perché fa gridare all'alterazione dove non c'è.
    for voce in MANIFESTO.values():
        for pezzo in voce["pezzi"]:
            percorso = CARTELLA / pezzo["file"]
            if percorso.exists():
                pezzo["sha256"] = _impronta(percorso)
                pezzo["mb"] = round(percorso.stat().st_size / 1e6, 2)

    pezzi = [p for voce in MANIFESTO.values() for p in voce["pezzi"]]
    riepilogo = {
        "stagione": STAGIONE,
        "tabelle": len(MANIFESTO),
        "file": len(pezzi),
        "righe_totali": sum(v["righe"] for v in MANIFESTO.values()),
        "mb_totali": round(sum(p["mb"] for p in pezzi), 1),
        "file_piu_grosso_mb": round(max((p["mb"] for p in pezzi), default=0), 1),
        "tetto_mb": TETTO_MB,
        "competizioni": LISTA_UTENTE,
        "competizioni_assenti_dal_repo": [
            c for c in LISTA_UTENTE
            if c in ("Serie B", "Championship", "Ligue 2", "EFL Trophy")],
        "chiave": "match_uid = competizione | data ISO | casa norm. | trasferta norm.",
        "tabelle_dettaglio": MANIFESTO,
    }
    CARTELLA.mkdir(parents=True, exist_ok=True)
    (CARTELLA / "MANIFESTO.json").write_text(
        json.dumps(riepilogo, ensure_ascii=False, indent=1))
    return riepilogo


def scrivi_readme(riepilogo: dict) -> None:
    righe = [
        "# `data/stagione_2025_2026/` — tutti i dati della stagione, al loro grano",
        "",
        "Generato da `scripts/build_stagione_2025_2026.py`. Non modificare a mano:",
        "ogni correzione vive nel codice che legge la fonte (R3).",
        "",
        f"**{riepilogo['tabelle']} tabelle · {riepilogo['file']} file · "
        f"{riepilogo['righe_totali']:,} righe · {riepilogo['mb_totali']} MB** "
        f"(il più grosso: {riepilogo['file_piu_grosso_mb']} MB, tetto "
        f"{riepilogo['tetto_mb']:.0f} MB).".replace(",", "."),
        "",
        "## La chiave che tiene insieme tutto",
        "",
        "Ogni riga **di grana partita** porta **`match_uid`**, ed è la stessa",
        "ovunque:",
        "",
        "```",
        "match_uid = competizione | data ISO | casa normalizzata | trasferta normalizzata",
        "```",
        "",
        "Quindi qualunque tabella si riaggancia a `partite.csv.gz` con un merge",
        "su quella colonna sola, e due tabelle qualsiasi si incrociano fra loro:",
        "",
        "```python",
        "import pandas as pd",
        "p = pd.read_csv('data/stagione_2025_2026/partite.csv.gz', low_memory=False)",
        "t = pd.read_csv('data/stagione_2025_2026/tiri.csv.gz', low_memory=False)",
        "t.merge(p[['match_uid', 'competizione', 'casa', 'trasferta']], on='match_uid')",
        "```",
        "",
        "Dove la fonte ha anche i suoi identificatori (`ID partita (SofaScore)`,",
        "`game_id`, `player_id`) quelli restano: servono a incrociare **dentro**",
        "la partita.",
        "",
        "⚠️ **Non tutte le tabelle hanno un `match_uid`, e non è una lacuna.**",
        "Le anagrafiche (ranking UEFA, valori rosa, carriere, identità degli",
        "allenatori), la classifica e i livelli `Rosa`/`Stagione` dei giocatori",
        "non sono a grana partita: non c'è una partita a cui agganciarli. Il",
        "manifesto lo dichiara con `aggancio_match_uid: null`.",
        "",
        "⚠️ **`aggancio_match_uid` è misurato per APPARTENENZA**, cioè la",
        "frazione di righe la cui chiave esiste davvero in `partite.csv.gz` —",
        "non `notna()`. La differenza non è accademica: la chiave si costruisce",
        "sempre, quindi un tasso calcolato su `notna` direbbe 1.0 anche con",
        "tutte le chiavi penzolanti.",
        "",
        "## Perché una cartella e non un file",
        "",
        "Perché l'event data Opta, impacchettato in una cella, pesa **1,7 GB",
        "grezzi / 243 MB gzippati** — da solo più del doppio del limite di 100 MB",
        "per file che GitHub impone. Spezzato per competizione ogni pezzo ci sta,",
        "e non si perde niente. Vale lo stesso per le 4,77 milioni di posizioni.",
        "",
        "## I file",
        "",
        "| tabella | grana | righe | col. | MB | file |",
        "|---|---|--:|--:|--:|--:|",
    ]
    for nome, voce in sorted(MANIFESTO.items()):
        peso = sum(p["mb"] for p in voce["pezzi"])
        righe.append(f"| `{nome}` | {voce['grana']} | {voce['righe']:,} | "
                     f"{voce['colonne']} | {peso:.1f} | {len(voce['pezzi'])} |"
                     .replace(",", "."))
    righe += [
        "",
        "Il dettaglio — nomi di tutte le colonne, fonti, asse di spezzatura,",
        "tasso di aggancio a `match_uid`, sha256 di ogni pezzo — sta in",
        "`MANIFESTO.json`.",
        "",
        "## ⚠️ Le trappole che valgono per tutta la cartella",
        "",
        "1. **Il «meteo» non è il meteo.** `Meteo (WhoScored)` vale 5.0 e solo",
        "   5.0 ovunque sia pieno: varianza zero, finto pieno da manuale (R6).",
        "   Il progetto non ha dati meteo.",
        "2. **Due punteggi, non uno.** I 90 minuti e il finale con i",
        "   supplementari sono numeri diversi, e la lotteria dei rigori non sta",
        "   mai dentro nessuno dei due. In Europa League e Conference l'export",
        "   la somma dentro `Gol casa`: `Gol casa regolamentari` è la colonna",
        "   riparata.",
        "3. **L'allenatore è chi sedeva in panchina**, non chi era in carica —",
        "   SofaScore registra il vice quando il tecnico era squalificato.",
        "   WhoScored e Transfermarkt danno il tecnico. Divergono su 36 partite",
        "   su 1.752, e non è grafia.",
        "4. **`red_cards` di `transfermarkt_appearances` è muta**: vale 0 su",
        "   tutte le righe del 2025-26.",
        "5. **La classifica è quella FINALE**: su una partita di ottobre è",
        "   look-ahead puro (R8).",
        "6. **Il meteo, quando c'è, è una lega sola.** `Meteo (WhoScored)` è",
        "   piena su 2.262 righe squadra-partita su 19.852 (11,4%), e sono",
        "   quasi tutte Premier League: Serie A, Ligue 1, LaLiga2 e ogni coppa",
        "   hanno ZERO. E dove è piena vale sempre lo stesso numero.",
        "7. **14 `match_uid` hanno un lato vuoto** — turni preliminari di Copa",
        "   del Rey dove l'avversario manca alla fonte: la chiave esiste ma non",
        "   si può ricostruire da (competizione, data, casa, trasferta).",
        "8. **Lo spareggio Bundesliga/2.Bundesliga compare due volte**, una per",
        "   competizione (4 righe per 2 partite): è così che le due raccolte lo",
        "   consegnano, e i dati fini stanno sotto una delle due.",
        "9. **Otto partite di Europa League** hanno i tempi che non sommano al",
        "   risultato, cinque con entrambi i tempi a zero e gol nella partita:",
        "   è un difetto della FONTE, ereditato e non corretto (R5 — va",
        "   istruito a mano, non zittito).",
        "10. **Una sola colonna JSON sopravvive**: `provenienza_json` in",
        "    `partite.csv.gz`, che dice quale fonte ha vinto per ogni campo",
        "    normalizzato. Non è un dato impacchettato: è la provenienza.",
        "11. **R8 in generale**: questa cartella mescola per costruzione dati",
        "    `pre` (quote, arbitro, moduli, valore rosa) e `post` (gol, xG,",
        "    rating, posizioni). È un **archivio**, non un dataset di",
        "    addestramento.",
        "",
        "## Cosa NON c'è",
        "",
        "### Il perimetro, e come è tagliato",
        "",
        "Le anagrafiche di Transfermarkt e le carriere di Wikipedia coprono per",
        "costruzione ogni epoca. Qui sono **ristrette al perimetro**: i",
        "giocatori che sono scesi in campo nel 2025-26 e i club che hanno",
        "giocato. Le stime dichiarate di altre stagioni, e la finestra 2026-27",
        "del ranking UEFA, restano fuori: sono dato di un'altra stagione.",
        "",
        "### Le competizioni che mancano",
        "",
        "Quattro delle 25 chieste: **Serie B, Championship,",
        "Ligue 2, EFL Trophy**. Non è una lacuna della cartella: il repo non ha",
        "una riga della loro stagione 2025-26. Esistono altrove nel tempo — in",
        "Smarkets sono 2026-27, in `club_fixtures` sono 1617-2425.",
        "",
    ]
    (CARTELLA / "README.md").write_text("\n".join(righe))


def main() -> None:
    argomenti = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argomenti.add_argument("--solo", nargs="*", default=None,
                           choices=sorted(BLOCCHI), help="costruisce solo questi blocchi")
    argomenti.add_argument("--elenco", action="store_true",
                           help="stampa i blocchi disponibili e termina")
    argomenti.add_argument("--out", type=Path, default=None)
    opzioni = argomenti.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if opzioni.elenco:
        for nome, che_cosa in BLOCCHI.items():
            print(f"  {nome:14s} {che_cosa}")
        return

    global CARTELLA
    if opzioni.out:
        CARTELLA = opzioni.out
    CARTELLA.mkdir(parents=True, exist_ok=True)

    # ⚠️ Con `--solo` si ricostruisce un blocco alla volta, e il manifesto deve
    # restare quello di TUTTA la cartella: ripartire da zero lo farebbe
    # dichiarare vuoto ciò che sul disco c'è ancora — un manifesto che mente
    # è peggio di nessun manifesto.
    precedente = CARTELLA / "MANIFESTO.json"
    if opzioni.solo and precedente.exists():
        try:
            MANIFESTO.update(json.loads(precedente.read_text())
                             .get("tabelle_dettaglio", {}))
            log.info("manifesto precedente: %d tabelle già note", len(MANIFESTO))
        except (OSError, ValueError):
            pass

    costruisci_cartella(opzioni.solo)

    # ⚠️ Su una ricostruzione INTERA i file che il manifesto non nomina più
    # vanno via. Senza questo passo, una tabella tolta dal codice (una stima
    # di un'altra stagione, la finestra 2026-27 del ranking) resterebbe sul
    # disco per sempre: la cartella direbbe una cosa e il manifesto un'altra,
    # e la seconda avrebbe torto senza che nessuno se ne accorga.
    if not opzioni.solo:
        attesi = {CARTELLA / p["file"] for voce in MANIFESTO.values()
                  for p in voce["pezzi"]}
        attesi |= {CARTELLA / "MANIFESTO.json", CARTELLA / "README.md"}
        rimossi = 0
        for percorso in sorted(CARTELLA.rglob("*")):
            if percorso.is_file() and percorso not in attesi:
                percorso.unlink()
                rimossi += 1
        for cartella in sorted(CARTELLA.rglob("*"), reverse=True):
            if cartella.is_dir() and not any(cartella.iterdir()):
                cartella.rmdir()
        if rimossi:
            log.info("puliti %d file che il manifesto non nomina più", rimossi)

    riepilogo = scrivi_manifesto()
    scrivi_readme(riepilogo)

    log.info("──────────────────────────────────────────────────────────────")
    log.info("scritta %s", CARTELLA)
    log.info("%d tabelle · %d file · %d righe · %.1f MB (il più grosso %.1f MB)",
             riepilogo["tabelle"], riepilogo["file"], riepilogo["righe_totali"],
             riepilogo["mb_totali"], riepilogo["file_piu_grosso_mb"])
    if riepilogo["file_piu_grosso_mb"] > TETTO_MB:
        log.error("⚠️  un file supera il tetto: va spezzato ancora")


if __name__ == "__main__":
    main()
