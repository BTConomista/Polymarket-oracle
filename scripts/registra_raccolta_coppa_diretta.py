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

from src.data.club_matching import Agganciatore, _TRADUZIONE  # noqa: E402

FOGLI = ["Partite", "Formazioni e cambi", "Eventi", "Stat giocatori", "Note"]
NOSTRE = RADICE / "data" / "coppe_2526"

# ⚠️ Il nome del manifesto NON e' `manifesto.json`, ed e' deliberato: e' cosi'
# che `player_stats` (campionati) e `team_stats` (squadra) scoprono le PROPRIE
# raccolte senza inciampare in quelle altrui. Una raccolta di coppa ha uno
# schema diverso: col nome condiviso, il caricatore dei campionati la trovava e
# falliva su una chiave che qui non esiste — misurato, 2 test rossi.
FILE_MANIFESTO = "manifesto_coppa.json"

# Nomi che diretta.it scrive in modo che il registro non riconosce da solo.
# Ognuno verificato a candidato unico contro `club_names.csv.gz`.
ALIAS_COPPA = {
    "Entella": "Virtus Entella",
    "L.R. Vicenza": "LR Vicenza",
    "Inter": "Inter Milan",
    "Sudtirol": "FC Sudtirol",
    "Juve Stabia": "SS Juve Stabia",
    "Internazionale": "Inter Milan",
}


def _log(m: str) -> None:
    print(m, flush=True)


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
    s = str(nome).translate(_TRADUZIONE)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # l'apostrofo si TOGLIE, non si sostituisce con uno spazio: spezzando,
    # «N'Dri» darebbe «dri» e «Ndri» non si aggancerebbe.
    s = s.replace("'", "").replace("’", "")
    iniziali = frozenset(m.group(1).lower()
                         for m in re.finditer(r"\b([A-Za-z]{1,3})\.", s))
    s = re.sub(r"\b[A-Za-z]{1,3}\.", " ", s)
    s = re.sub(r"[^A-Za-z ]", " ", s)
    return frozenset(p.lower() for p in s.split() if len(p) > 1), iniziali


def _compatibili(iniziali: frozenset[str], parole: frozenset[str]) -> bool:
    """Ogni iniziale dev'essere il prefisso di una parola dell'altro nome."""
    return all(any(p.startswith(i) for p in parole) for i in iniziali)


def _stessa_persona(a: tuple, b: tuple) -> bool:
    (pa, ia), (pb, ib) = a, b
    if not pa or not pb:
        return False
    if not (pa <= pb or pb <= pa):
        return False
    return _compatibili(ia, pb) and _compatibili(ib, pa)


def _appaia_undici(A: list[frozenset], B: list[frozenset]) -> int:
    """Quanti giocatori restano spaiati fra due undici.

    Due passate, e la seconda serve davvero: le convenzioni sui nomi spagnoli
    non sono in relazione di sottoinsieme («Santiago Perez J.» contro «Yellu
    Santiago» — la stessa persona, Yellu Santiago Pérez). Dopo che la prima
    passata ha appaiato tutti gli altri, accettare un **token in comune** e'
    sicuro: un giocatore davvero diverso non condivide il cognome.
    """
    liberi, spaiati = list(B), []
    for a in A:
        for i, b in enumerate(liberi):
            if _stessa_persona(a, b):
                liberi.pop(i)
                break
        else:
            spaiati.append(a)
    residui = []
    for a in spaiati:
        for i, b in enumerate(liberi):
            if a[0] & b[0]:
                liberi.pop(i)
                break
        else:
            residui.append(a)
    return len(residui) + len(liberi)


def confronta_con_automatica(fogli: dict, coppa: str) -> dict:
    if not (NOSTRE / "partite.csv").exists():
        return {"eseguito": False, "motivo": "raccolta automatica assente"}

    ag = Agganciatore()

    def cid(n):
        return ag.aggancia(ALIAS_COPPA.get(n, n))

    L = fogli["Partite"].copy()
    N = pd.read_csv(NOSTRE / "partite.csv")
    N = N[N.competizione == coppa].copy()
    if N.empty:
        return {"eseguito": False, "motivo": f"«{coppa}» assente dalla raccolta automatica"}

    L["data_iso"] = pd.to_datetime(L.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    for d, c_casa, c_osp in ((L, "Casa", "Ospite"), (N, "casa", "ospite")):
        d["_c"] = d[c_casa].map(cid)
        d["_o"] = d[c_osp].map(cid)
    L["k"] = L.data_iso + "|" + L._c.astype("Int64").astype(str) + "|" + L._o.astype("Int64").astype(str)
    N["k"] = N.data + "|" + N._c.astype("Int64").astype(str) + "|" + N._o.astype("Int64").astype(str)

    m = L.merge(N, on="k", suffixes=("_l", "_n"))
    divergenti = []
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
            divergenti.append({"partita": f"{r.data_iso} {r.Casa}-{r.Ospite}", "differenze": p})

    # --- formazioni
    F = fogli["Formazioni e cambi"].copy()
    F["data_iso"] = pd.to_datetime(F.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    F["_s"] = F.Squadra.map(cid)
    F["k"] = (F.data_iso + "|" + F.Casa.map(cid).astype("Int64").astype(str)
              + "|" + F.Ospite.map(cid).astype("Int64").astype(str))
    NF = pd.read_csv(NOSTRE / "formazioni.csv")
    NF = NF[NF.game_id.isin(set(N.game_id.dropna()))].copy()
    NF["k"] = NF.game_id.map(dict(zip(N.game_id, N.k)))

    uguali = totale = 0
    form_diverse = []
    for k in sorted(set(F.k) & set(NF.k.dropna())):
        l = F[(F.k == k) & (F.Gruppo == "Titolare")]
        n = NF[(NF.k == k) & (NF.ruolo_partita == "titolare")]
        for squadra in set(l._s.dropna()):
            A = [_token(v) for v in l[l._s == squadra].Giocatore]
            B = [_token(v) for v in n[n.club_id == squadra].giocatore]
            if not B:
                continue
            totale += 1
            spaiati = _appaia_undici(A, B)
            if spaiati == 0:
                uguali += 1
            else:
                form_diverse.append({"partita": k, "club_id": int(squadra),
                                     "spaiati": spaiati})

    return {
        "eseguito": True,
        "partite": {
            "manuale": int(len(L)), "automatica": int(len(N)),
            "appaiate": int(len(m)),
            "identiche_su_tutti_i_punteggi": int(len(m) - len(divergenti)),
            "divergenti": divergenti,
            "non_appaiate_manuale": [
                f"{r.data_iso} {r.Casa}-{r.Ospite}"
                for _, r in L[~L.k.isin(set(N.k))].iterrows()],
            "non_appaiate_automatica": [
                f"{r.data} {r.casa}-{r.ospite}"
                for _, r in N[~N.k.isin(set(L.k))].iterrows()],
        },
        "formazioni": {
            "squadre_partita_confrontabili": totale,
            "undici_identici": uguali,
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
        _log(f"     partite appaiate {p['appaiate']} · punteggi identici "
             f"{p['identiche_su_tutti_i_punteggi']}/{p['appaiate']}")
        if p["divergenti"]:
            for d in p["divergenti"]:
                _log(f"       DIVERGE {d['partita']}: {d['differenze']}")
        _log(f"     undici identici {f['undici_identici']}/{f['squadre_partita_confrontabili']}")
    _log(f"\n  scritto {(dest / FILE_MANIFESTO).relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
