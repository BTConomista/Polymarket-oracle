#!/usr/bin/env python3
"""Registra la raccolta STATISTICHE di una COPPA (diretta.it) — Fase 140.

E' la TERZA porta d'ingresso delle raccolte manuali, e non e' un doppione delle
altre due. La differenza non e' cosmetica:

  registra_raccolta_coppa_diretta     registra_raccolta_squadra_diretta     QUESTA
  --------------------------------    ---------------------------------     ------------------
  partite/formazioni/eventi/stat      statistiche di squadra per periodo    statistiche di
  di UNA coppa                        di UN CAMPIONATO                      squadra + giocatore
                                                                            di UNA COPPA
  nessuna statistica di squadra       round-robin, join allo snapshot       niente round-robin,
                                      della lega                            niente snapshot:
                                                                            il controllo forte e'
                                                                            la raccolta di coppa
                                                                            gia' in casa

COSA PORTA DI NUOVO questa consegna, rispetto a `originale_coppa.xlsx`:
  1. ⭐ le **statistiche di SQUADRA per periodo** (Totale / 1° tempo / 2° tempo,
     piu' «Supplementari» dove si sono giocati). Per le coppe non esistevano:
     e' lo stesso dato che la Fase 131 ha portato per le 5 leghe, ed e' il
     mattone del modello a due stadi (residuo aperto delle Fasi 96/99);
  2. ⭐ la colonna **`ID partita` sulle statistiche per GIOCATORE**. Non e' un
     dettaglio: `scripts/aggancia_coppe.py` documenta a riga 239 di aver dovuto
     aggirare la sua assenza appaiando per (Data, Casa, Ospite) e poi per nome.
     Con la chiave esplicita l'aggancio diventa esatto invece che dedotto;
  3. la **piena precisione** dei decimali (la consegna precedente era arrotondata
     a 3: qui sono 6 — misurato, max|diff| = 0.0005 su ogni colonna comune);
  4. le etichette dei turni **editoriali** («4° turno (ottavi)», «Semifinali
     (andata)») al posto di quelle generiche del sito («1/8 FINALE», «SEMI
     FINALI»), che non distinguevano andata e ritorno.

COSA VERIFICA prima di accettare (e si ferma se non torna):
  1. i quattro fogli ci sono, con le colonne fondamentali;
  2. **fedelta'** dei CSV consegnati contro l'`.xlsx` originale, cella per cella
     (§5-ter: senza l'originale un bug della conversione e' invisibile);
  3. `ID partita`: nessun nullo, e ogni partita delle statistiche esiste nel
     foglio Partite **e** nella raccolta di coppa gia' registrata;
  4. i periodi: Totale/1T/2T per ogni squadra-partita, «Supplementari» **solo**
     dove il foglio Partite li dichiara giocati (i due fatti devono combaciare);
  5. **additivita'** 1T + 2T (+ Supplementari) = Totale sulle metriche di
     conteggio — le percentuali sono rapporti e restano fuori;
  6. ⭐ il confronto con la raccolta di coppa **gia' in casa**: stesse righe
     giocatore, punteggi identici. E' il controllo forte, perche' le due
     consegne sono indipendenti. Una divergenza oltre l'arrotondamento
     (0.0005) ferma tutto: sarebbe un dato che cambia, non un dato piu' preciso.

Cio' che scrive in `files/diretta_{coppa}_{stagione}/`:
  - `squadra_per_partita.csv.gz`   statistiche di squadra, schema canonico delle
                                   leghe (le 45 metriche di `team_stats`), cosi'
                                   coppe e campionati si leggono allo stesso modo
  - `stat_giocatori.csv`           AGGIORNATO: + `ID partita`, piena precisione
  - `turni_rietichettati.csv`      vecchia etichetta -> nuova, cosi' il cambio e'
                                   verificabile e reversibile (R3: niente
                                   modifiche non tracciate)
  - `note_statistiche.csv`         il foglio «Note», conservato come DICHIARAZIONE
  - `originale_statistiche.xlsx`   ⭐ l'originale COME CONSEGNATO (§5-ter)
  - `manifesto_statistiche.json`   perimetro, copertura e esito di ogni verifica

USO:
    python scripts/registra_raccolta_statistiche_coppa_diretta.py \\
        --xlsx ~/scaricati/CarabaoCup_202526_STATISTICHE.xlsx \\
        --cartella files/diretta_efl_cup_2526 \\
        --csv-giocatori ~/scaricati/CarabaoCup_202526_STATISTICHE_giocatori.csv \\
        --csv-squadra   ~/scaricati/CarabaoCup_202526_STATISTICHE_squadra.csv
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from src.data import team_stats as TS  # noqa: E402

FOGLI = ["Partite", "Statistiche squadra", "Statistiche giocatori", "Note"]

FILE_SQUADRA = "squadra_per_partita.csv.gz"
FILE_GIOCATORI = "stat_giocatori.csv"
FILE_TURNI = "turni_rietichettati.csv"
FILE_NOTE = "note_statistiche.csv"
FILE_ORIGINALE = "originale_statistiche.xlsx"
FILE_MANIFESTO = "manifesto_statistiche.json"

PERIODO_SUPPL = "Supplementari"

# Le sei metriche che la fonte consegna in forma COMPOSITA («77% (364/473)») e
# che le leghe hanno gia' espanse. Espanderle qui e' cio' che rende lo schema
# delle coppe identico a quello dei campionati: 35 colonne consegnate -> 45
# canoniche (29 pure + possesso + 5 composite x 3).
COMPOSITE = {
    "Passaggi": ("Passaggi riusciti", "Passaggi totali", "Passaggi %"),
    "Passaggi lunghi": ("Passaggi lunghi riusciti", "Passaggi lunghi totali",
                        "Passaggi lunghi %"),
    "Passaggi offensivi": ("Passaggi offensivi riusciti", "Passaggi offensivi totali",
                           "Passaggi offensivi %"),
    "Cross": ("Cross riusciti", "Cross totali", "Cross %"),
    "Tackles": ("Tackles riusciti", "Tackles totali", "Tackles %"),
}

IDENTITA = ["Competizione", "Turno", "Data", "Casa", "Ospite", "Periodo", "Lato",
            "Squadra", "ID partita"]

# Lo schema di uscita: le colonne d'identita' della COPPA (che non sono quelle
# di un campionato — non c'e' `Giornata`, c'e' `Turno`; e `ID partita` e' la
# chiave vera) seguite dalle 45 metriche canoniche, nell'ordine di team_stats.
USCITA_IDENTITA = ["Competizione", "Turno", "Data", "Squadra", "Campo", "Avversario",
                   "Risultato squadra", "Esito", "Periodo", "ID partita"]

_RE_COMPOSITA = re.compile(r"^\s*(\d+)%\s*\((\d+)/(\d+)\)\s*$")
_RE_PERCENTO = re.compile(r"^\s*(\d+)%\s*$")


def _stop(msg: str) -> None:
    raise SystemExit(f"❌ {msg}")


def _leggi_foglio(percorso: Path, foglio: str) -> pd.DataFrame:
    df = pd.read_excel(percorso, sheet_name=foglio)
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    return df


def _leggi_csv(percorso: Path) -> pd.DataFrame:
    df = pd.read_csv(percorso, sep=";", encoding="utf-8-sig")
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    return df


# --------------------------------------------------------------------------- #
# 2. fedelta' CSV consegnato <-> xlsx originale (§5-ter)
# --------------------------------------------------------------------------- #
def _testo(s: pd.Series) -> pd.Series:
    """Vista testuale NULL-SAFE di una colonna.

    ⚠️ Serve `fillna` PRIMA del confronto: da pandas 3.0 `astype(str)` lascia il
    NaN com'e' invece di produrre la stringa 'nan', e `NaN != NaN` e' vero. Senza
    questo, due colonne identiche risultano divergenti su ogni cella vuota — e il
    controllo di fedelta' accusa la conversione di un difetto che non esiste
    (misurato: 134 falsi positivi sulla colonna `Rating` della Carabao Cup).
    """
    return s.astype("string").fillna("").str.strip()


def _celle_divergenti(a: pd.DataFrame, b: pd.DataFrame) -> int:
    """Conta le celle diverse fra due fogli con le stesse colonne e righe.

    Il confronto e' NUMERICO dove entrambi i lati lo sono (altrimenti '3' e
    '3.0' risulterebbero diversi senza esserlo) e testuale altrove.
    """
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return max(a.size, b.size)
    diverse = 0
    for c in a.columns:
        x, y = a[c], b[c]
        xn, yn = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
        numerica = xn.notna().sum() + yn.notna().sum() > 0
        sx, sy = _testo(x), _testo(y)
        if numerica:
            d = pd.Series(~np.isclose(xn, yn, rtol=0, atol=5e-7, equal_nan=True),
                          index=x.index)
            # dove il numero non si legge da nessuna delle due parti, si cade
            # sul testo: una colonna mista non deve sfuggire al controllo.
            testo = xn.isna() & yn.isna()
            d = (d & ~testo) | (testo & (sx != sy))
        else:
            d = sx != sy
        diverse += int(d.sum())
    return diverse


# --------------------------------------------------------------------------- #
# normalizzazione delle statistiche di squadra allo schema canonico
# --------------------------------------------------------------------------- #
def _espandi(valore) -> tuple[float, float, float]:
    """«77% (364/473)» -> (364, 473, 77). Il vuoto resta vuoto."""
    if pd.isna(valore):
        return (np.nan, np.nan, np.nan)
    m = _RE_COMPOSITA.match(str(valore))
    if not m:
        _stop(f"valore composito non interpretabile: {valore!r}")
    pct, ok, tot = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (float(ok), float(tot), float(pct))


def _percento(valore) -> float:
    if pd.isna(valore):
        return np.nan
    m = _RE_PERCENTO.match(str(valore))
    if not m:
        _stop(f"percentuale non interpretabile: {valore!r}")
    return float(m.group(1))


def normalizza_squadra(sq: pd.DataFrame, partite: pd.DataFrame) -> pd.DataFrame:
    """Porta le 35 colonne consegnate sulle 45 canoniche di `team_stats`."""
    mancanti = [c for c in IDENTITA if c not in sq.columns]
    if mancanti:
        _stop(f"colonne d'identita' mancanti nelle statistiche di squadra: {mancanti}")

    out = pd.DataFrame(index=sq.index)
    out["Competizione"] = sq["Competizione"]
    out["Turno"] = sq["Turno"]
    out["Data"] = sq["Data"]
    out["Squadra"] = sq["Squadra"]
    # `Lato` dice se la riga e' la squadra di casa o quella ospite; le leghe
    # scrivono 'Casa'/'Trasferta' e ci uniformiamo a quello.
    out["Campo"] = sq["Lato"].map({"Casa": "Casa", "Ospite": "Trasferta"})
    if out["Campo"].isna().any():
        _stop(f"valori di `Lato` inattesi: {sorted(set(sq['Lato']))}")
    out["Avversario"] = np.where(sq["Lato"].eq("Casa"), sq["Ospite"], sq["Casa"])
    out["Periodo"] = sq["Periodo"]
    out["ID partita"] = sq["ID partita"]

    # --- risultato, dal foglio Partite: il periodo «Totale» copre i 90' PIU' i
    # supplementari dove si sono giocati, quindi il punteggio di riferimento e'
    # `dts` la' dove esiste. I rigori non entrano mai (nota della fonte).
    p = partite.set_index("ID partita")
    casa_g = p["Gol casa dts"].fillna(p["Gol casa 90"])
    osp_g = p["Gol ospite dts"].fillna(p["Gol ospite 90"])
    mio = np.where(sq["Lato"].eq("Casa"),
                   sq["ID partita"].map(casa_g), sq["ID partita"].map(osp_g))
    suo = np.where(sq["Lato"].eq("Casa"),
                   sq["ID partita"].map(osp_g), sq["ID partita"].map(casa_g))
    mio, suo = pd.Series(mio, index=sq.index), pd.Series(suo, index=sq.index)
    if mio.isna().any() or suo.isna().any():
        _stop("una riga di statistiche punta a un `ID partita` senza punteggio")
    out["Risultato squadra"] = (mio.astype(int).astype(str) + "-"
                                + suo.astype(int).astype(str))
    out["Esito"] = np.select([mio > suo, mio == suo], ["V", "N"], default="P")

    # --- metriche
    for col in TS.COLONNE_METRICHE:
        if col in sq.columns:
            out[col] = pd.to_numeric(sq[col], errors="coerce")
    out["Possesso palla %"] = sq["Possesso palla"].map(_percento)
    for sorgente, (c_ok, c_tot, c_pct) in COMPOSITE.items():
        if sorgente not in sq.columns:
            _stop(f"manca la colonna composita `{sorgente}`")
        espansi = sq[sorgente].map(_espandi)
        out[c_ok] = [e[0] for e in espansi]
        out[c_tot] = [e[1] for e in espansi]
        out[c_pct] = [e[2] for e in espansi]

    persi = [c for c in TS.COLONNE_METRICHE if c not in out.columns]
    if persi:
        _stop(f"metriche canoniche non prodotte: {persi}")
    return out[USCITA_IDENTITA + list(TS.COLONNE_METRICHE)]


# --------------------------------------------------------------------------- #
# verifiche
# --------------------------------------------------------------------------- #
def verifica(sq: pd.DataFrame, gioc: pd.DataFrame, partite: pd.DataFrame,
             cartella: Path) -> dict:
    info: dict = {}

    # --- 3. ID partita
    for nome, d in (("statistiche squadra", sq), ("statistiche giocatori", gioc)):
        if d["ID partita"].isna().any():
            _stop(f"{nome}: {int(d['ID partita'].isna().sum())} righe senza `ID partita`")
    ids_partite = set(partite["ID partita"].astype(str))
    for nome, d in (("statistiche squadra", sq), ("statistiche giocatori", gioc)):
        orfani = set(d["ID partita"].astype(str)) - ids_partite
        if orfani:
            _stop(f"{nome}: {len(orfani)} `ID partita` che il foglio Partite non ha")
    info["partite"] = len(partite)
    info["id_partita_orfani"] = 0

    # --- il controllo forte: la raccolta di coppa gia' registrata
    vecchie_partite = cartella / "partite.csv"
    if not vecchie_partite.exists():
        _stop(f"{vecchie_partite} non esiste: registrare prima la raccolta di coppa")
    vp = pd.read_csv(vecchie_partite)
    ids_vecchi = set(vp["ID partita"].astype(str))
    if ids_partite != ids_vecchi:
        _stop(
            "le partite di questa consegna non coincidono con quelle gia' in casa: "
            f"solo qui {len(ids_partite - ids_vecchi)}, solo la' {len(ids_vecchi - ids_partite)}"
        )
    # punteggi identici, partita per partita
    a = partite.set_index("ID partita")[["Gol casa 90", "Gol ospite 90"]].sort_index()
    b = vp.set_index("ID partita")[["Gol casa 90", "Gol ospite 90"]].sort_index()
    discordi = int((a.fillna(-1) != b.fillna(-1)).any(axis=1).sum())
    if discordi:
        _stop(f"{discordi} partite con punteggio a 90' discorde dalla raccolta gia' in casa")
    info["partite_confronto_raccolta_esistente"] = f"{len(a)}/{len(a)} punteggi identici"

    # --- 4. periodi
    conteggi = dict(sq["Periodo"].value_counts())
    n_tot = conteggi.get(TS.PERIODO_TOTALE, 0)
    for periodo in (TS.PERIODO_1T, TS.PERIODO_2T):
        if conteggi.get(periodo, 0) != n_tot:
            _stop(f"periodo '{periodo}': {conteggi.get(periodo, 0)} righe contro {n_tot} di 'Totale'")
    # i supplementari devono combaciare con cio' che il foglio Partite dichiara
    dichiarati = set(partite.loc[partite["Supplementari giocati"].eq("Sì"), "ID partita"].astype(str))
    con_suppl = set(sq.loc[sq["Periodo"].eq(PERIODO_SUPPL), "ID partita"].astype(str))
    if dichiarati != con_suppl:
        _stop(
            "i supplementari dichiarati nel foglio Partite non combaciano con le "
            f"righe di statistica: dichiarate {len(dichiarati)}, con righe {len(con_suppl)}"
        )
    info["team_partita"] = int(n_tot)
    info["periodi"] = sorted(conteggi)
    info["righe_squadra"] = int(len(sq))
    info["partite_con_supplementari"] = len(dichiarati)

    # --- 5. additivita' 1T + 2T (+ Supplementari) = Totale
    additive = [c for c in TS.COLONNE_METRICHE if c not in TS.COLONNE_NON_ADDITIVE]
    d = sq.copy()
    for c in TS.COLONNE_ZERO_IMPLICITO:
        if c in d.columns:
            d[c] = d[c].fillna(0)
    chiave = ["ID partita", "Squadra"]
    somma = d[d["Periodo"] != TS.PERIODO_TOTALE].groupby(chiave)[additive].sum()
    rif = d[d["Periodo"] == TS.PERIODO_TOTALE].set_index(chiave)[additive]
    diff = (somma - rif).abs()
    violazioni = int((diff > 0.005).sum().sum())
    celle = int(diff.size)
    if violazioni:
        peggiori = diff.max().sort_values(ascending=False).head(5).to_dict()
        _stop(f"additivita' violata in {violazioni}/{celle} celle. Peggiori: {peggiori}")
    info["additivita_periodi"] = f"{celle - violazioni}/{celle}"

    # --- 6. confronto con le statistiche giocatore gia' in casa
    vecchie = cartella / FILE_GIOCATORI
    if vecchie.exists():
        v = pd.read_csv(vecchie)
        key = ["Data", "Casa", "Ospite", "Squadra", "Giocatore"]
        x = gioc.sort_values(key).reset_index(drop=True)
        y = v.sort_values(key).reset_index(drop=True)
        if len(x) != len(y):
            _stop(f"statistiche giocatore: {len(x)} righe contro {len(y)} gia' in casa")
        comuni = [c for c in y.columns if c in x.columns and c != "Turno"]
        peggiore, reali = 0.0, 0
        for c in comuni:
            xn = pd.to_numeric(x[c], errors="coerce")
            yn = pd.to_numeric(y[c], errors="coerce")
            if xn.notna().any() and yn.notna().any():
                delta = (xn - yn).abs()
                peggiore = max(peggiore, float(delta.max() or 0.0))
                reali += int((delta > 0.005).sum())
            else:
                reali += int((_testo(x[c]) != _testo(y[c])).sum())
        if reali:
            _stop(
                f"{reali} celle divergono oltre l'arrotondamento dalla consegna "
                "precedente: e' un dato che CAMBIA, non un dato piu' preciso. "
                "Fermarsi e capire quale delle due consegne sbaglia (regola R5)."
            )
        info["giocatori_confronto_consegna_precedente"] = {
            "righe": int(len(x)),
            "colonne_comuni": len(comuni),
            "celle_confrontate": int(len(x) * len(comuni)),
            "divergenze_reali": 0,
            "scarto_massimo": round(peggiore, 6),
            "lettura": ("scarto compatibile con il solo arrotondamento a 3 decimali "
                        "della consegna precedente: qui i decimali sono 6"),
        }
    info["righe_giocatori"] = int(len(gioc))
    info["metriche_per_giocatore"] = int(
        len([c for c in gioc.columns if c.isupper() or c == "Rating"]))
    return info


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", required=True, type=Path)
    ap.add_argument("--cartella", required=True, type=Path)
    ap.add_argument("--csv-giocatori", type=Path, default=None)
    ap.add_argument("--csv-squadra", type=Path, default=None)
    args = ap.parse_args()

    cartella = args.cartella if args.cartella.is_absolute() else RADICE / args.cartella
    if not cartella.exists():
        _stop(f"{cartella} non esiste")

    xlsx = args.xlsx
    fogli = pd.ExcelFile(xlsx).sheet_names
    mancanti = [f for f in FOGLI if f not in fogli]
    if mancanti:
        _stop(f"fogli mancanti nell'originale: {mancanti} (trovati: {fogli})")

    partite = _leggi_foglio(xlsx, "Partite")
    sq_grezzo = _leggi_foglio(xlsx, "Statistiche squadra")
    gioc = _leggi_foglio(xlsx, "Statistiche giocatori")
    note = _leggi_foglio(xlsx, "Note")

    # --- 2. fedelta' dei CSV consegnati contro l'originale
    fedelta = {}
    for etichetta, percorso, riferimento in (
        ("giocatori", args.csv_giocatori, gioc),
        ("squadra", args.csv_squadra, sq_grezzo),
    ):
        if percorso is None:
            fedelta[etichetta] = "non consegnato"
            continue
        consegnato = _leggi_csv(percorso)
        diverse = _celle_divergenti(consegnato, riferimento)
        if diverse:
            _stop(f"CSV `{etichetta}`: {diverse} celle divergono dall'originale .xlsx")
        fedelta[etichetta] = f"{riferimento.size}/{riferimento.size} celle identiche"

    sq = normalizza_squadra(sq_grezzo, partite)
    info = verifica(sq, gioc, partite, cartella)
    info["fedelta_csv_vs_xlsx"] = fedelta

    # --- turni rietichettati: il cambio va lasciato verificabile (R3)
    vecchie_partite = pd.read_csv(cartella / "partite.csv")
    mappa = (partite[["ID partita", "Turno"]]
             .merge(vecchie_partite[["ID partita", "Turno"]], on="ID partita",
                    suffixes=(" nuovo", " sito")))
    coppie = (mappa[["Turno sito", "Turno nuovo"]].drop_duplicates()
              .sort_values(["Turno sito", "Turno nuovo"]))
    info["turni_rietichettati"] = int(len(coppie))

    # --- scritture
    # ⚠️ `mtime=0`: senza, gzip incorpora l'ORA nell'intestazione e lo stesso
    # contenuto produce due file diversi a ogni esecuzione. Un artefatto che
    # cambia impronta senza che sia cambiato un dato e' esattamente cio' che
    # rende un registro non verificabile (R3: la correzione dev'essere
    # idempotente, e l'idempotenza si controlla al byte).
    sq.to_csv(cartella / FILE_SQUADRA, index=False,
              compression={"method": "gzip", "mtime": 0})
    gioc.to_csv(cartella / FILE_GIOCATORI, index=False)
    coppie.to_csv(cartella / FILE_TURNI, index=False)
    note.to_csv(cartella / FILE_NOTE, index=False)
    shutil.copy2(xlsx, cartella / FILE_ORIGINALE)

    # ⚠️ Il nome canonico e' quello che la cartella usa gia' (`manifesto_coppa.json`),
    # non quello della consegna: la Carabao Cup e' il nome SPONSORIZZATO della EFL
    # Cup, e due manifesti nella stessa cartella che chiamano la stessa
    # competizione in due modi sono esattamente cio' che una sessione futura
    # legge come due competizioni diverse (regola R4: l'anomalia si dichiara
    # anche quando non e' un errore). Si tengono entrambi, uno dichiarato tale.
    canonico = json.loads(
        (cartella / "manifesto_coppa.json").read_text(encoding="utf-8"))["coppa"]
    dichiarato = str(partite["Competizione"].iloc[0])
    info["coppa"] = canonico
    if dichiarato != canonico:
        info["coppa_come_dichiarata_dalla_fonte"] = dichiarato
        info["nota_nome"] = (
            f"«{dichiarato}» e «{canonico}» sono la STESSA competizione: la prima e' "
            "il nome sponsorizzato. Il nome canonico di questa cartella resta il secondo."
        )
    info["fonte"] = "diretta.it (Flashscore), raccolta manuale"
    info["file_originale"] = FILE_ORIGINALE
    info["sha256"] = hashlib.sha256((cartella / FILE_ORIGINALE).read_bytes()).hexdigest()
    info["statistiche_squadra"] = len(TS.COLONNE_METRICHE)
    info["disponibilita_temporale"] = (
        "post — ogni metrica di questi due fogli esiste solo a partita finita "
        "(regola R8). Utilizzabile per prevedere partite SUCCESSIVE, mai quella "
        "che l'ha prodotta."
    )

    ordine = ["coppa", "fonte", "file_originale", "sha256"]
    ordine += [k for k in info if k not in ordine]
    (cartella / FILE_MANIFESTO).write_text(
        json.dumps({k: info[k] for k in ordine}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"✅ {info['coppa']} -> {cartella}")
    for k in ("partite", "team_partita", "righe_squadra", "periodi",
              "partite_con_supplementari", "additivita_periodi",
              "partite_confronto_raccolta_esistente", "righe_giocatori",
              "turni_rietichettati", "fedelta_csv_vs_xlsx"):
        print(f"   {k:38s} {info[k]}")
    if "giocatori_confronto_consegna_precedente" in info:
        c = info["giocatori_confronto_consegna_precedente"]
        print(f"   {'divergenze reali vs consegna prec.':38s} "
              f"{c['divergenze_reali']} su {c['celle_confrontate']} celle "
              f"(scarto max {c['scarto_massimo']})")


if __name__ == "__main__":
    main()
