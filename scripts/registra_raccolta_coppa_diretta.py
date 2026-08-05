#!/usr/bin/env python3
"""Registra una raccolta manuale diretta.it di una COPPA (Fase 139).

E' la gemella di `registra_raccolta_diretta.py`, che serve i CAMPIONATI. Non e'
la stessa porta perche' la forma del dato e' diversa, e la differenza non e'
cosmetica:

  campionato                      coppa
  ----------------------------    ------------------------------------------
  `Giornata` (1..38)              `Turno` (1/64 FINALE .. FINALE)
  un risultato                    tre (90', dopo supplementari, rigori)
  `Titolare/Subentrato`           `Gruppo` (Titolare/Panchina) + entrata/uscita
  un foglio                       quattro (partite, formazioni, eventi, stat)

COSA VERIFICA prima di accettare (e si ferma se non torna):
  1. i quattro fogli ci sono, con le colonne fondamentali;
  2. ogni squadra-partita ha **esattamente 11 titolari**;
  3. il punteggio dichiarato **non somma mai i rigori** — il difetto che la
     Fase 138 ha trovato nella fonte automatica, qui cercato nella manuale;
  4. la sequenza dei rigori negli eventi **ricompone** il punteggio ai rigori;
  5. ⭐ **il confronto con la nostra raccolta automatica**, partita per partita:
     e' il controllo piu' forte, perche' le due fonti sono indipendenti. Non e'
     un adempimento — e' l'unico modo di accorgersi che una delle due sbaglia
     (regola R5, passo 2), ed e' il motivo per cui `data/coppe_2526/` esiste.

Gli originali vengono archiviati **come consegnati** (§5-ter): senza, un bug
della nostra conversione diventa indistinguibile dal dato.

USO:
    python scripts/registra_raccolta_coppa_diretta.py \\
        --xlsx ~/scaricati/CoppaItalia_202526_coppa.xlsx \\
        --coppa "Coppa Italia" --stagione 2526
    python scripts/registra_raccolta_coppa_diretta.py --cartella files/diretta_coppa_italia_2526
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from src.data.club_matching import _TRADUZIONE  # noqa: E402
from src.data.coppe_aggancio import appaia_partite  # noqa: E402

FOGLI = ["Partite", "Formazioni e cambi", "Eventi", "Stat giocatori", "Note"]

# Il file delle STATISTICHE e' un secondo consegnato, COMPLEMENTARE al primo:
# non ha formazioni ne' eventi, e in piu' ha il foglio di SQUADRA per PERIODO
# (Totale / 1o tempo / 2o tempo / Supplementari) che il primo non aveva.
FOGLI_STATISTICHE = ["Partite", "Statistiche squadra", "Statistiche giocatori", "Note"]
NOSTRE = RADICE / "data" / "coppe_2526"

# ⚠️ Il nome del manifesto NON e' `manifesto.json`, ed e' deliberato: e' cosi'
# che `player_stats` (campionati) e `team_stats` (squadra) scoprono le PROPRIE
# raccolte senza inciampare in quelle altrui. Una raccolta di coppa ha uno
# schema diverso: col nome condiviso, il caricatore dei campionati la trovava e
# falliva su una chiave che qui non esiste — misurato, 2 test rossi.
FILE_MANIFESTO = "manifesto_coppa.json"

# Espansione tedesca delle umlaut: NON e' un'alternativa a `_TRADUZIONE` di
# club_matching (che copre ß, ø, ł…), e' una SECONDA lettura dello stesso nome.
_UMLAUT = str.maketrans({"ö": "oe", "Ö": "oe", "ü": "ue", "Ü": "ue",
                         "ä": "ae", "Ä": "ae"})

# --------------------------------------------------------------------------- #
# SINONIMI di GIOCATORE, verificati uno per uno su fonte esterna
# --------------------------------------------------------------------------- #
# Casi in cui le due fonti scrivono un cognome DIVERSO, non una grafia diversa:
# nessuna regola di normalizzazione puo' agganciarli, e indovinare sarebbe
# esattamente l'errore che tutto il resto del modulo evita. Ognuno e' stato
# accertato su fonte esterna (indagine del 03/08/2026, con verifica avversaria
# indipendente su ciascuno).
#
# chiave = token come lo scrive diretta.it  ->  token del registro Transfermarkt
SINONIMI_GIOCATORE = {
    # Portiere e capitano dell'SV Hemelingen. Il registro UFFICIALE della
    # DFB (datencenter.dfb.de, rosa DFB-Pokal 2025-26) scrive «Marcel Pfaar,
    # 18.10.1998»; fussball.de, kicker e il Weser-Kurier idem. diretta.it ha
    # invertito le due lettere. La forma giusta e' quella del registro.
    "pfarr": "pfaar",
    # ⭐ NON un refuso: un CAMBIO DI COGNOME. Il sito ufficiale dello ZFC
    # Meuselwitz elenca «Ben Nitschke (ehem. Keßler)» — «ex Keßler» — in una
    # sola voce fra i 29 nomi della rosa; nessun Keßler separato. Alla data
    # della partita (17/08/2025) i referti ufficiali portavano ancora
    # «Kessler»: diretta.it usa il nome in vigore allora, Transfermarkt
    # l'attuale. **Nessuna delle due fonti sbaglia.**
    "kessler": "nitschke",
    # Difensore ucraino dello Stoke. Due traslitterazioni di Таловєров: la
    # forma con -ie- e' quella del club, di UEFA e della BBC; Transfermarkt usa
    # la resa piu' russificata. Stesso `player_id` 668557 gia' presente nel
    # nostro database carriere, con data di nascita verificata.
    "talovierov": "taloverov",
    # Hannibal Mejbri: il registro lo porta col solo nome proprio, «Hannibal»,
    # diretta.it col cognome. Mononimo contro cognome, stessa persona.
    "mejbri": "hannibal",
}

def _log(m: str) -> None:
    print(m, flush=True)


def integra_statistiche(cartella: Path, xlsx: Path) -> dict:
    """Integra il file di STATISTICHE in una raccolta gia' registrata.

    E' un secondo consegnato, non un sostituto: porta il foglio di SQUADRA per
    PERIODO — che la raccolta base non aveva — e una versione del foglio
    giocatori con due cose in piu': la colonna `ID partita` (che mancava, e che
    obbligava ad agganciare per data+squadre) e i decimali per intero, dove
    prima erano arrotondati a tre.

    ⚠️ Non si sovrascrive niente senza VERIFICARE prima che sia lo stesso dato:
    le partite devono essere le stesse, e sul foglio giocatori si pretende che i
    valori coincidano a meno dell'arrotondamento. Un file «definitivo» che in
    realta' e' di un'altra raccolta non deve poter entrare in silenzio.
    """
    x = pd.ExcelFile(xlsx)
    mancanti = [f for f in FOGLI_STATISTICHE if f not in x.sheet_names]
    if mancanti:
        raise ValueError(f"fogli mancanti nel file di statistiche: {mancanti}")
    fogli = {}
    for f in FOGLI_STATISTICHE:
        d = x.parse(f)
        d.columns = [str(c).replace("\ufeff", "").strip() for c in d.columns]
        fogli[f] = d

    quadro: dict = {"file": xlsx.name,
                    "sha256": hashlib.sha256(xlsx.read_bytes()).hexdigest()}

    # 1. le partite devono essere le stesse della raccolta gia' registrata
    base = pd.read_csv(cartella / "partite.csv")
    nuove = fogli["Partite"]
    chiave = lambda d: set(zip(d.Data, d.Casa, d.Ospite))  # noqa: E731
    solo_base, solo_nuove = chiave(base) - chiave(nuove), chiave(nuove) - chiave(base)
    quadro["partite"] = {"raccolta": len(base), "statistiche": len(nuove),
                         "solo_nella_raccolta": sorted(map(str, solo_base)),
                         "solo_nelle_statistiche": sorted(map(str, solo_nuove))}
    if solo_base or solo_nuove:
        raise ValueError(
            f"le partite non coincidono: {len(solo_base)} solo nella raccolta, "
            f"{len(solo_nuove)} solo nelle statistiche. Il file di statistiche "
            f"non appartiene a questa raccolta, o una delle due e' incompleta.")

    # 2. il foglio giocatori dev'essere lo STESSO dato, piu' preciso
    vecchio = pd.read_csv(cartella / "stat_giocatori.csv")
    nuovo = fogli["Statistiche giocatori"]
    comuni = [c for c in vecchio.columns if c in set(nuovo.columns)]
    # ⚠️ La chiave di ordinamento dev'essere STABILE FRA LE DUE FONTI, altrimenti
    # il confronto misura il disallineamento invece dei valori. Prima ordinavo
    # sulle prime otto colonne comuni, `Turno` compreso: sulla Carabao Cup i due
    # consegnati lo scrivono in modo diverso («1° turno» contro «1/64 FINALE»),
    # le due tabelle finivano in ordine diverso e divergevano **122.401 celle**
    # su un dato che e' identico riga per riga. Era un controllo cieco: bocciava
    # il dato buono per una differenza di etichetta.
    CHIAVE = ["Data", "Squadra", "Giocatore"]
    if any(c not in comuni for c in CHIAVE):
        raise ValueError(f"chiave di confronto assente: {CHIAVE}")
    doppioni = int(nuovo.duplicated(subset=CHIAVE).sum())
    if doppioni:
        raise ValueError(
            f"{doppioni} righe con la stessa (data, squadra, giocatore): la "
            f"chiave non e' univoca e il confronto non sarebbe affidabile.")
    a = nuovo[comuni].sort_values(CHIAVE).reset_index(drop=True)
    b = vecchio[comuni].sort_values(CHIAVE).reset_index(drop=True)
    oltre_arrotondamento = 0
    etichette_diverse = {}
    if a.shape == b.shape:
        import numpy as np
        for c in comuni:
            if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
                x1, y1 = a[c].fillna(-9e9), b[c].fillna(-9e9)
                oltre_arrotondamento += int(
                    (~np.isclose(x1, y1, rtol=0, atol=0.0006)).sum())
            else:
                # le colonne testuali NON bloccano: una nomenclatura diversa
                # del turno e' un fatto da dichiarare, non un dato sbagliato.
                d = (a[c].fillna("~").astype(str).str.lower()
                     != b[c].fillna("~").astype(str).str.lower())
                if d.any():
                    etichette_diverse[c] = int(d.sum())
    quadro["fedelta_giocatori"] = {
        "righe_prima": len(vecchio), "righe_dopo": len(nuovo),
        "colonne_prima": vecchio.shape[1], "colonne_dopo": nuovo.shape[1],
        "colonne_nuove": [c for c in nuovo.columns if c not in set(vecchio.columns)],
        "celle_divergenti_oltre_arrotondamento": oltre_arrotondamento,
        "colonne_testuali_con_etichette_diverse": etichette_diverse,
    }
    if oltre_arrotondamento:
        raise ValueError(
            f"{oltre_arrotondamento} celle divergono OLTRE l'arrotondamento: "
            f"non e' la stessa misura piu' precisa, e' un dato diverso.")

    # 3. si scrive solo dopo che tutto e' tornato
    nuovo.to_csv(cartella / "stat_giocatori.csv", index=False)
    sq = fogli["Statistiche squadra"]
    sq.to_csv(cartella / "stat_squadra.csv", index=False)
    # ⚠️ Ri-integrare PARTENDO dall'originale gia' archiviato e' il modo normale
    # di rifare il lavoro quando cambia qualcosa a monte (un alias di club, una
    # regola di aggancio): l'originale conservato per la §5-ter serve proprio a
    # questo. Senza la guardia, `copy2` alza SameFileError DOPO aver riscritto i
    # due CSV e PRIMA di aggiornare il manifesto — cioe' lascia la raccolta in
    # uno stato a meta'.
    archivio = cartella / "originale_statistiche.xlsx"
    if xlsx.resolve() != archivio.resolve():
        shutil.copy2(xlsx, archivio)
    quadro["statistiche_squadra"] = {
        "righe": len(sq),
        "partite": int(sq["ID partita"].nunique()),
        "metriche": int(len(sq.columns) - 9),
        "per_periodo": {k: int(v) for k, v in sq.Periodo.value_counts().items()},
    }
    return quadro


def leggi_xlsx(percorso: Path) -> dict[str, pd.DataFrame]:
    x = pd.ExcelFile(percorso)
    mancanti = [f for f in FOGLI if f not in x.sheet_names]
    if mancanti:
        raise ValueError(f"fogli mancanti nel file: {mancanti}")
    fogli = {}
    for f in FOGLI:
        d = x.parse(f)
        d.columns = [str(c).replace("﻿", "").strip() for c in d.columns]
        fogli[f] = d
    return fogli


# --------------------------------------------------------------------------- #
# verifiche interne
# --------------------------------------------------------------------------- #
def verifica_undici(formazioni: pd.DataFrame) -> dict:
    t = formazioni[formazioni.Gruppo == "Titolare"]
    conte = t.groupby(["ID partita", "Squadra"]).size()
    fuori = conte[conte != 11]
    return {
        "squadre_partita": int(len(conte)),
        "con_undici_esatti": int((conte == 11).sum()),
        "anomale": [{"partita": a, "squadra": b, "titolari": int(v)}
                    for (a, b), v in fuori.items()],
    }


def verifica_punteggio(partite: pd.DataFrame) -> dict:
    """Il punteggio non deve MAI sommare i rigori (il difetto della Fase 138)."""
    sospette = []
    for _, r in partite.iterrows():
        c90, o90 = r["Gol casa 90"], r["Gol ospite 90"]
        rc, ro = r["Rigori casa"], r["Rigori ospite"]
        if pd.isna(rc):
            continue
        # se ai rigori si e' arrivati, i 90' (o i supplementari) erano PARI
        fin_c = r["Gol casa dts"] if pd.notna(r["Gol casa dts"]) else c90
        fin_o = r["Gol ospite dts"] if pd.notna(r["Gol ospite dts"]) else o90
        if fin_c != fin_o:
            sospette.append(
                f"{r.Data} {r.Casa}-{r.Ospite}: ai rigori ma il punteggio "
                f"finale e' {fin_c:.0f}-{fin_o:.0f}, non di parita'")
        if rc == ro:
            sospette.append(f"{r.Data} {r.Casa}-{r.Ospite}: rigori {rc:.0f}-{ro:.0f} in parita'")
    return {"partite_ai_rigori": int(partite["Rigori casa"].notna().sum()),
            "incoerenti": sospette}


def verifica_rigori_eventi(partite: pd.DataFrame, eventi: pd.DataFrame) -> dict:
    """La sequenza dei rigori negli eventi deve ricomporre il punteggio.

    E' il controllo che la fonte automatica NON supera: li' la sequenza e'
    troncata (Grimsby-United, 23 tiri su 25+), quindi i rigori vanno ricavati
    per sottrazione. Qui invece si puo' pretendere che tornino.
    """
    rig = eventi[eventi.Periodo == "Rigori"]
    segnati = (rig[rig["Tipo evento"] == "Rigore"]
               .groupby(["ID partita", "Lato"]).size().unstack(fill_value=0))
    ok, divergenti = 0, []
    con_rigori = partite[partite["Rigori casa"].notna()]
    for _, r in con_rigori.iterrows():
        pid = r["ID partita"]
        if pid not in segnati.index:
            divergenti.append(f"{r.Data} {r.Casa}-{r.Ospite}: nessun evento di rigore")
            continue
        c = int(segnati.loc[pid].get("Casa", 0))
        o = int(segnati.loc[pid].get("Ospite", 0))
        if (c, o) == (int(r["Rigori casa"]), int(r["Rigori ospite"])):
            ok += 1
        else:
            divergenti.append(
                f"{r.Data} {r.Casa}-{r.Ospite}: colonna "
                f"{r['Rigori casa']:.0f}-{r['Rigori ospite']:.0f}, eventi {c}-{o}")
    return {"partite_ai_rigori": int(len(con_rigori)),
            "sequenza_ricompone": ok, "divergenti": divergenti}


# --------------------------------------------------------------------------- #
# ⭐ il confronto con la fonte automatica
# --------------------------------------------------------------------------- #
def _token(nome: str) -> tuple[frozenset[str], frozenset[str]]:
    """Nome di persona -> (parole intere, iniziali puntate).

    ⚠️ Le due fonti scrivono i nomi in modo diverso, e in quattro modi diversi:
    l'ordine («Motta E.» contro «Emanuele Motta»), le iniziali puntate, gli
    apostrofi («Ndri K.» contro «Konan N'Dri») e i **caratteri che NFKD non
    decompone** — «Grønbaek», «Kılıçsoy», «Højlund». Senza la tabella
    `_TRADUZIONE` del progetto quindici undici risultavano diversi: erano
    quindici volte la stessa persona scritta in due modi.

    ⭐ **L'iniziale si conserva, non si butta.** Buttandola «Esposito Sa.»
    diventa `{esposito}`, che e' sottoinsieme di `{francesco, esposito}`: il
    confronto non distinguerebbe **due omonimi in rosa** — Salvatore e
    Francesco Esposito giocano davvero nella stessa Coppa Italia. Tenuta come
    prefisso da verificare, li separa.
    """
    grezzo = str(nome)
    # l'apostrofo si TOGLIE, non si sostituisce con uno spazio: spezzando,
    # «N'Dri» darebbe «dri» e «Ndri» non si aggancerebbe.
    grezzo = grezzo.replace("'", "").replace("’", "")
    iniziali = frozenset(m.group(1).lower()
                         for m in re.finditer(r"\b([A-Za-z]{1,3})\.", grezzo))

    def parole(testo: str) -> frozenset[str]:
        s = unicodedata.normalize("NFKD", testo)
        s = "".join(c for c in s if not unicodedata.combining(c))
        s = re.sub(r"\b[A-Za-z]{1,3}\.", " ", s)
        s = re.sub(r"[^A-Za-z ]", " ", s)
        return frozenset(p.lower() for p in s.split() if len(p) > 1)

    # ⚠️ DUE varianti, non una scelta fra le due. Le umlaut tedesche si scrivono
    # in due modi entrambi legittimi: Transfermarkt tiene la lettera
    # («Splettstößer») e NFKD la riduce a `splettstosser`; diretta.it la ESPANDE
    # («Splettstoesser»). Normalizzare in un verso solo rompe l'altro — se
    # espandessimo sempre, «Muller» non aggancerebbe piu' «Müller». Si generano
    # entrambe le forme e basta che UNA coppia combaci.
    diretta = parole(grezzo.translate(_TRADUZIONE))
    espansa = parole(grezzo.translate(_UMLAUT).translate(_TRADUZIONE))
    varianti = [diretta] + ([espansa] if espansa != diretta else [])

    # terza variante: i sinonimi accertati su fonte esterna. Si applicano come
    # una lettura IN PIU', mai sostituendo l'originale — cosi' un sinonimo
    # sbagliato non puo' far perdere un aggancio che gia' funzionava.
    for v in list(varianti):
        tradotta = frozenset(SINONIMI_GIOCATORE.get(t, t) for t in v)
        if tradotta != v and tradotta not in varianti:
            varianti.append(tradotta)
    return tuple(varianti), iniziali


def _compatibili(iniziali: frozenset[str], parole: frozenset[str]) -> bool:
    """**Almeno una** iniziale dev'essere il prefisso di una parola dell'altro.

    ⚠️ La prima versione pretendeva che le rispettasse **tutte**, ed era troppo
    severa per una ragione precisa: le due fonti non portano lo stesso numero di
    nomi di battesimo. diretta.it scrive «Manu K. S.» (King Samuel), Transfermarkt
    tiene solo «King Manu» — l'iniziale `s` non ha prefisso da nessuna parte e la
    coppia cadeva. Stessa cosa per «Obiogumu D. U.» (Destiny Uche) contro «Uche
    Obiogumu», «Zimmer M. N.» (Melvin Noah), «Gross F. C.» (Falk Christopher).
    Verificato leggendo `stat_giocatori.csv` della stessa raccolta, che i nomi li
    scrive **per intero**: in tutti e cinque i casi e' la stessa persona.

    La protezione contro gli omonimi **non si indebolisce**, ed e' misurabile:
    con UNA sola iniziale «almeno una» e «tutte» coincidono, quindi «Esposito
    Sa.» continua a non agganciare «Francesco Esposito». Il rilassamento agisce
    solo da due iniziali in su. Misurato sull'intera raccolta: **+23 righe
    agganciate, 0 nuove ambiguita'**.
    """
    return not iniziali or any(
        any(p.startswith(i) for p in parole) for i in iniziali)


def _stessa_persona(a: tuple, b: tuple) -> bool:
    """Le due scritture sono la stessa persona?

    Basta che UNA coppia di varianti soddisfi il sottoinsieme; le iniziali si
    verificano contro la variante che ha combaciato.
    """
    (va, ia), (vb, ib) = a, b
    for pa in va:
        for pb in vb:
            if not pa or not pb:
                continue
            if (pa <= pb or pb <= pa) and _compatibili(ia, pb) and _compatibili(ib, pa):
                return True
    return False


def numero_maglia(x) -> int | None:
    """Il numero di maglia come intero, o `None` se la fonte non lo scrive.

    Le due fonti lo tengono in due tipi diversi (float nella manuale, stringa
    nell'automatica): senza normalizzarlo `15.0 == "15"` e' falso e il confronto
    non troverebbe mai niente.
    """
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def _appaia_undici(A: list[tuple], B: list[tuple]) -> tuple[list[str], list[str], int]:
    """Chi resta spaiato fra due undici, e quanti ha riconosciuto il NUMERO DI MAGLIA.

    `A` e `B` sono liste di `(token, numero, nome)`; torna i **nomi** rimasti
    scoperti dai due lati — non un conteggio: un buco si dichiara con dentro
    scritto chi e', altrimenti la sessione dopo deve rifare l'indagine da capo.

    Due passate sul NOME, in ordine di forza decrescente, poi una terza che il
    nome non lo guarda affatto.

    1. `_stessa_persona` — sottoinsieme dei token + iniziali.
    2. **token in comune**, solo sui residui: le convenzioni sui nomi spagnoli
       non sono in relazione di sottoinsieme («Santiago Perez J.» contro «Yellu
       Santiago» — la stessa persona, Yellu Santiago Pérez). Dopo che la prima
       passata ha appaiato tutti gli altri, un giocatore davvero diverso non
       condivide il cognome.
    3. ⭐ **il NUMERO DI MAGLIA** (Copa del Rey). Le due fonti scrivono lo stesso
       giocatore con due nomi **diversi**, non con due grafie diverse, e nessuna
       normalizzazione puo' arrivarci: «Pibe» contro «Agustín Pastoriza», «Ruiz
       A. M.» contro «Azael Martín». Ma il numero di maglia e' **unico dentro
       una squadra in una partita**: due righe con lo stesso numero SONO la
       stessa persona. Non e' un'euristica sul nome, e' un identificatore
       indipendente — la stessa natura del `club_id` per le squadre.

    ⚠️ Perche' non bastano ne' una regola sul nome ne' `SINONIMI_GIOCATORE`.
    Sulla Copa del Rey le coppie distinte da agganciare erano **53**, e solo
    **15** hanno una relazione grafica su cui una regola potrebbe reggersi
    (troncamento o due modifiche: «Willman M.»/Willmann, «Petxa A.»/Petxarroman,
    «Babanzilla M.»/Babanzila). Le altre **38 non hanno nessuna relazione**: sono
    soprannomi («Jogo» = Jonathan Gómez, «Yusi» = Youssef Enríquez, «Pacha» =
    Alfonso Espino) e **cognomi doppi scelti in modo diverso dalle due fonti** —
    diretta.it mostra il secondo cognome e abbrevia il resto, il registro mostra
    nome + primo cognome («Martinez M. G.» = Miguel García, «Sanchez A.» = Álex
    Salto). Metterle nei sinonimi sarebbe peggio del problema: quella tabella e'
    **globale**, quindi una voce `sanchez -> salto` verrebbe applicata alle **79
    righe** che portano «Sánchez» nelle sei raccolte (138 per «García»), e
    trasformerebbe un buco dichiarato in agganci sbagliati.

    Quanto vale il numero, misurato: sulle **8.071** coppie che il nome aggancia
    gia' da solo nelle cinque coppe confrontabili, il numero coincide **8.059**
    volte (**99,85%**). Sui residui della Copa del Rey ne risolve **69 su 70**.

    ⚠️ Si accetta **solo la coppia univoca da entrambe le parti**: se due residui
    portano lo stesso numero, o se un numero pesca due candidati liberi, non si
    aggancia nessuno dei due. E' la regola di sempre — un aggancio incerto resta
    vuoto — e qui costa poco perche' il numero e' gia' unico per costruzione.

    ⚠️ **L'ordine non e' negoziabile: il numero va per ULTIMO, dopo i nomi.** Non
    e' prudenza astratta, e' un caso reale sfiorato. Portugalete-Valladolid
    29/10/2025: diretta.it scrive «Crespo G.» col **18**, la fonte automatica da'
    il 18 a Gorka Tapiador e l'11 a Gorka Crespo. Se il numero avesse avuto la
    precedenza, Crespo sarebbe finito su Tapiador — un aggancio sbagliato al
    posto di un buco. Col nome davanti, Crespo trova Crespo e resta scoperto solo
    Tapiador, che e' la verita': quell'undici manuale ha **10** titolari, e
    `verifica_undici` lo dichiarava gia' (233/234).
    """
    liberi, spaiati = list(B), []
    for a in A:
        for i, b in enumerate(liberi):
            if _stessa_persona(a[0], b[0]):
                liberi.pop(i)
                break
        else:
            spaiati.append(a)

    def condivide_una_parola(a, b) -> bool:
        return any(pa & pb for pa in a[0][0] for pb in b[0][0])

    residui = []
    for a in spaiati:
        for i, b in enumerate(liberi):
            if condivide_una_parola(a, b):
                liberi.pop(i)
                break
        else:
            residui.append(a)

    da_numero = 0
    quanti_a, quanti_b = {}, {}
    for a in residui:
        quanti_a[a[1]] = quanti_a.get(a[1], 0) + 1
    for b in liberi:
        quanti_b[b[1]] = quanti_b.get(b[1], 0) + 1
    ancora = []
    for a in residui:
        n = a[1]
        if n is not None and quanti_a.get(n) == 1 and quanti_b.get(n) == 1:
            liberi.pop(next(i for i, b in enumerate(liberi) if b[1] == n))
            da_numero += 1
        else:
            ancora.append(a)
    return [a[2] for a in ancora], [b[2] for b in liberi], da_numero


def confronta_con_automatica(fogli: dict, coppa: str) -> dict:
    if not (NOSTRE / "partite.csv").exists():
        return {"eseguito": False, "motivo": "raccolta automatica assente"}

    L = fogli["Partite"].copy()
    N = pd.read_csv(NOSTRE / "partite.csv")
    N = N[N.competizione == coppa].copy()
    if N.empty:
        return {"eseguito": False, "motivo": f"«{coppa}» assente dalla raccolta automatica"}

    # ⭐ La risoluzione dei club e l'appaiamento delle partite NON vivono qui:
    # stanno in `src.data.coppe_aggancio`, e `scripts/aggancia_coppe.py` chiama
    # la stessa funzione. Averle scritte due volte era il bug — la seconda
    # implementazione non aveva ne' la deduzione ne' l'appaiamento per nome, e
    # si fermava a 77/117 partite sulla Copa del Rey e 0/201 sulla Coupe.
    app = appaia_partite(L, N)
    cid2, dedotti = app.cid, app.dedotti
    L["data_iso"] = app.data_iso
    L["k"] = app.k_manuale
    N["k"] = app.k_automatica
    if app.rimappate:
        _log(f"     appaiate per nome dentro la giornata: {app.rimappate}")
    if app.contese:
        _log(f"     lasciate vuote perche' contese fra due righe: {app.contese}")

    m = L.merge(N, on="k", suffixes=("_l", "_n"))
    divergenti, colmate = [], []
    _log(f"     club dedotti dalle partite: {len(dedotti)}")
    for _, r in m.iterrows():
        lfin = ((r["Gol casa dts"], r["Gol ospite dts"])
                if pd.notna(r["Gol casa dts"])
                else (r["Gol casa 90"], r["Gol ospite 90"]))
        lr = None if pd.isna(r["Rigori casa"]) else (int(r["Rigori casa"]), int(r["Rigori ospite"]))
        nr = None if pd.isna(r.rigori_casa) else (int(r.rigori_casa), int(r.rigori_ospite))
        p = []
        if pd.notna(r.gol_casa_90) and (int(r["Gol casa 90"]), int(r["Gol ospite 90"])) != \
                (int(r.gol_casa_90), int(r.gol_ospite_90)):
            p.append(f"90': manuale {r['Gol casa 90']:.0f}-{r['Gol ospite 90']:.0f} "
                     f"· automatica {r.gol_casa_90:.0f}-{r.gol_ospite_90:.0f}")
        if (int(lfin[0]), int(lfin[1])) != (int(r.gol_casa_finale), int(r.gol_ospite_finale)):
            p.append(f"finale: manuale {lfin[0]:.0f}-{lfin[1]:.0f} "
                     f"· automatica {r.gol_casa_finale:.0f}-{r.gol_ospite_finale:.0f}")
        if lr != nr:
            p.append(f"rigori: manuale {lr} · automatica {nr}")
        if p:
            voce = {"partita": f"{r.data_iso} {r.Casa}-{r.Ospite}", "differenze": p}
            # ⚠️ Se la NOSTRA riga era gia' marcata `eventi_incompleti`, la
            # differenza non e' un disaccordo fra le fonti: e' un buco che la
            # fonte automatica aveva DICHIARATO e che la manuale colma. Contarlo
            # fra le divergenze farebbe sembrare un problema quello che invece
            # e' il motivo per cui la seconda fonte serve.
            (colmate if bool(r.eventi_incompleti) else divergenti).append(voce)

    quadro_partite = {
        "manuale": int(len(L)), "automatica": int(len(N)),
        "appaiate": int(len(m)),
        "identiche_su_tutti_i_punteggi": int(len(m) - len(divergenti) - len(colmate)),
        "divergenti": divergenti,
        "buchi_colmati_dalla_manuale": colmate,
        "club_dedotti_dalle_partite": {k: int(v) for k, v in sorted(dedotti.items())},
        "appaiate_per_nome_dentro_la_giornata": app.rimappate,
        "contese_lasciate_vuote": app.contese,
        "non_appaiate_manuale": [
            f"{r.data_iso} {r.Casa}-{r.Ospite}"
            for _, r in L[~L.k.isin(set(N.k))].iterrows()],
        "non_appaiate_automatica": [
            f"{r.data} {r.casa}-{r.ospite}"
            for _, r in N[~N.k.isin(set(L.k))].iterrows()],
    }

    # --- formazioni
    F = fogli["Formazioni e cambi"].copy()
    F["data_iso"] = pd.to_datetime(F.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    F["_s"] = F.Squadra.map(cid2)
    # ⚠️ La chiave delle formazioni si PRENDE da quella delle partite, non si
    # ricostruisce: le partite appaiate per nome dentro la giornata hanno una
    # chiave RI-MAPPATA (quella della fonte automatica), e ricostruirla dai nomi
    # di questo foglio la riporterebbe alla forma vecchia — undici confrontabili
    # che spariscono senza che niente dia errore.
    da_partita = {(d, c, o): k for d, c, o, k
                  in zip(L.data_iso, L.Casa, L.Ospite, L.k)}
    F["k"] = [da_partita.get((d, c, o)) for d, c, o
              in zip(F.data_iso, F.Casa, F.Ospite)]
    NF = pd.read_csv(NOSTRE / "formazioni.csv")
    NF = NF[NF.game_id.isin(set(N.game_id.dropna()))].copy()
    # ⚠️ Per la Coupe de France la fonte automatica viene da Wikipedia e NON ha
    # formazioni: non c'e' niente da confrontare, e dirlo e' diverso dal dire
    # «zero undici identici». Il confronto sugli undici si salta, dichiarandolo.
    if NF.empty:
        return {
            "eseguito": True,
            "partite": quadro_partite,
            "formazioni": {
                "squadre_partita_confrontabili": 0,
                "undici_identici": 0,
                "giocatori_appaiati_dal_numero_di_maglia": 0,
                "con_differenze": [],
                "non_confrontabile": "la fonte automatica non ha formazioni per "
                                     "questa coppa (Coupe de France, da Wikipedia)",
            },
        }
    mappa_k = {g: k for g, k in zip(N.game_id, N.k) if pd.notna(g)}
    NF["k"] = NF.game_id.map(mappa_k)

    uguali = totale = da_numero = 0
    form_diverse = []
    for k in sorted(set(F.k) & set(NF.k.dropna())):
        l = F[(F.k == k) & (F.Gruppo == "Titolare")]
        n = NF[(NF.k == k) & (NF.ruolo_partita == "titolare")]
        for squadra in set(l._s.dropna()):
            lq, nq = l[l._s == squadra], n[n.club_id == squadra]
            A = [(_token(v), numero_maglia(x), str(v))
                 for v, x in zip(lq.Giocatore, lq.Numero)]
            B = [(_token(v), numero_maglia(x), str(v))
                 for v, x in zip(nq.giocatore, nq.numero)]
            if not B:
                continue
            totale += 1
            solo_diretta, solo_registro, n_num = _appaia_undici(A, B)
            da_numero += n_num
            if not solo_diretta and not solo_registro:
                uguali += 1
            else:
                form_diverse.append({
                    "partita": k, "club_id": int(squadra),
                    "spaiati": len(solo_diretta) + len(solo_registro),
                    # i NOMI, non solo quanti: e' cio' che permette di riprendere
                    # l'indagine senza rifarla (§5-bis R4 — un'anomalia si
                    # dichiara, anche quando non e' un errore nostro).
                    "solo_nella_manuale": solo_diretta,
                    "solo_nell_automatica": solo_registro,
                })

    return {
        "eseguito": True,
        "partite": quadro_partite,
        "formazioni": {
            "squadre_partita_confrontabili": totale,
            "undici_identici": uguali,
            # dichiarato a parte, MAI confuso con gli identici per nome: sono
            # undici in cui le due fonti concordano sulla persona ma non sulla
            # scrittura del nome, e chi legge ha diritto di saperlo.
            "giocatori_appaiati_dal_numero_di_maglia": da_numero,
            "con_differenze": form_diverse,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xlsx", type=Path, help="il file consegnato")
    ap.add_argument("--coppa", default=None,
                    help="nome della coppa; con --cartella si riprende dal "
                         "manifesto se non indicato")
    ap.add_argument("--stagione", default="2526")
    ap.add_argument("--cartella", type=Path, help="ri-registra una raccolta esistente")
    ap.add_argument("--statistiche", type=Path,
                    help="il file di STATISTICHE (squadra per periodo + giocatori), "
                         "da integrare in una raccolta gia' registrata: serve --cartella")
    ap.add_argument("--extra", type=Path, nargs="*", default=[],
                    help="altri file consegnati da archiviare com'e' (csv, ecc.)")
    args = ap.parse_args()

    if args.cartella:
        dest = args.cartella if args.cartella.is_absolute() else (RADICE / args.cartella)
        xlsx = next(dest.glob("originale*.xlsx"))
        # ⚠️ il nome della coppa si RIPRENDE dal manifesto, non dal default:
        # ri-registrando la Pokal senza `--coppa` la si confrontava con la
        # Coppa Italia, e il confronto dava 0 partite appaiate — un risultato
        # che sembra un dato («le due fonti non si parlano») ed e' un bug.
        vecchio = dest / FILE_MANIFESTO
        if args.coppa is None and vecchio.exists():
            args.coppa = json.loads(vecchio.read_text(encoding="utf-8"))["coppa"]
            _log(f"  coppa ripresa dal manifesto: {args.coppa}")
    else:
        if not args.xlsx:
            ap.error("serve --xlsx oppure --cartella")
        if not args.coppa:
            ap.error("con --xlsx serve anche --coppa")
        slug = re.sub(r"[^a-z0-9]+", "_", args.coppa.lower()).strip("_")
        dest = RADICE / "files" / f"diretta_{slug}_{args.stagione}"
        dest.mkdir(parents=True, exist_ok=True)
        xlsx = dest / "originale_coppa.xlsx"
        shutil.copy2(args.xlsx, xlsx)
        for f in args.extra:
            shutil.copy2(f, dest / f"originale_{f.name.split('_')[-1]}")
        _log(f"  archiviati gli originali in {dest.relative_to(RADICE)}")

    if args.statistiche:
        q = integra_statistiche(dest, args.statistiche)
        _log(f"  statistiche integrate in {dest.relative_to(RADICE)}")
        _log(f"     giocatori: {q['fedelta_giocatori']['righe_dopo']} righe, "
             f"{q['fedelta_giocatori']['colonne_dopo']} colonne "
             f"(+{q['fedelta_giocatori']['colonne_nuove']}), "
             f"{q['fedelta_giocatori']['celle_divergenti_oltre_arrotondamento']} "
             f"celle divergenti oltre l'arrotondamento")
        s = q["statistiche_squadra"]
        _log(f"     SQUADRA (nuovo): {s['righe']} righe · {s['partite']} partite · "
             f"{s['metriche']} metriche · periodi {s['per_periodo']}")
        vecchio_m = json.loads((dest / FILE_MANIFESTO).read_text(encoding="utf-8"))
        vecchio_m["statistiche"] = q
        (dest / FILE_MANIFESTO).write_text(
            json.dumps(vecchio_m, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8")
        _log(f"  manifesto aggiornato")
        return 0

    fogli = leggi_xlsx(xlsx)
    _log(f"  fogli letti: " + ", ".join(f"{k} ({len(v)})" for k, v in fogli.items()))

    quadro = {
        "coppa": args.coppa,
        "stagione": args.stagione,
        "fonte": "diretta.it (Flashscore), raccolta manuale",
        "file_originale": xlsx.name,
        "sha256": hashlib.sha256(xlsx.read_bytes()).hexdigest(),
        "conteggi": {
            "partite": int(len(fogli["Partite"])),
            "righe_formazione": int(len(fogli["Formazioni e cambi"])),
            "titolari": int((fogli["Formazioni e cambi"].Gruppo == "Titolare").sum()),
            "panchina": int((fogli["Formazioni e cambi"].Gruppo == "Panchina").sum()),
            "eventi": int(len(fogli["Eventi"])),
            "righe_statistiche": int(len(fogli["Stat giocatori"])),
            "metriche_per_giocatore": int(len(fogli["Stat giocatori"].columns) - 11),
        },
        "verifiche": {
            "undici_titolari": verifica_undici(fogli["Formazioni e cambi"]),
            "punteggio_non_somma_i_rigori": verifica_punteggio(fogli["Partite"]),
            "sequenza_rigori": verifica_rigori_eventi(fogli["Partite"], fogli["Eventi"]),
            "confronto_con_fonte_automatica": confronta_con_automatica(fogli, args.coppa),
        },
    }

    for nome, d in fogli.items():
        f = dest / (re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_") + ".csv")
        d.to_csv(f, index=False)
    _log(f"  scritti i 5 fogli come CSV in {dest.relative_to(RADICE)}")

    (dest / FILE_MANIFESTO).write_text(
        json.dumps(quadro, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    v = quadro["verifiche"]
    _log("\n== verifiche")
    _log(f"  undici esatti: {v['undici_titolari']['con_undici_esatti']}"
         f"/{v['undici_titolari']['squadre_partita']}"
         + (f"  ANOMALIE: {v['undici_titolari']['anomale']}"
            if v['undici_titolari']['anomale'] else ""))
    _log(f"  punteggio non contaminato: "
         f"{'OK' if not v['punteggio_non_somma_i_rigori']['incoerenti'] else v['punteggio_non_somma_i_rigori']['incoerenti']}")
    sr = v["sequenza_rigori"]
    _log(f"  sequenza rigori ricompone: {sr['sequenza_ricompone']}/{sr['partite_ai_rigori']}")
    c = v["confronto_con_fonte_automatica"]
    if c.get("eseguito"):
        p, f = c["partite"], c["formazioni"]
        _log(f"  ⭐ contro la fonte automatica:")
        colmate = p.get("buchi_colmati_dalla_manuale", [])
        _log(f"     partite appaiate {p['appaiate']} · punteggi identici "
             f"{p['identiche_su_tutti_i_punteggi']}/{p['appaiate']}"
             + (f" · {len(colmate)} buco/i DICHIARATO/I colmato/i dalla manuale"
                if colmate else ""))
        for c in colmate:
            _log(f"       colmato {c['partita']}: {c['differenze']}")
        if p["divergenti"]:
            for d in p["divergenti"]:
                _log(f"       DIVERGE {d['partita']}: {d['differenze']}")
        _log(f"     undici identici {f['undici_identici']}/{f['squadre_partita_confrontabili']}"
             + (f" · {f['giocatori_appaiati_dal_numero_di_maglia']} giocatori "
                f"riconosciuti dal NUMERO di maglia, non dal nome"
                if f.get("giocatori_appaiati_dal_numero_di_maglia") else ""))
        for d in f["con_differenze"]:
            _log(f"       DIVERGE {d['partita']} club {d['club_id']}: "
                 f"manuale {d['solo_nella_manuale']} · "
                 f"automatica {d['solo_nell_automatica']}")
    _log(f"\n  scritto {(dest / FILE_MANIFESTO).relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
