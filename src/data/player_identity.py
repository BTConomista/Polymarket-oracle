"""Collega i dati diretta.it (per NOME) al `player_id` del database carriere.

IL PROBLEMA. Le due metà del database giocatori non si parlano:

* le statistiche per giocatore-partita 2025-26 (`src/data/player_stats.py`,
  raccolta diretta.it) hanno **solo il nome**, scritto «Cognome Nome» e **senza
  segni diacritici** — `Garces Facundo`, `Yildiz Kenan`;
* le carriere (`src/data/careers.py`) e tutto ciò che ne deriva sono su
  **`player_id`**, con i nomi scritti «Nome Cognome» **con** i diacritici —
  `Facundo Garcés`, `Kenan Yıldız`.

Finché il ponte non esiste, sapere la carriera di un giocatore e sapere come ha
giocato domenica sono due cose che non si possono mettere nella stessa frase.

LA CHIAVE: `(data, insieme dei token del nome)`. Non il nome, non la squadra.

* la **data** allinea perfettamente — 175 giornate su 175 in comune fra le due
  fonti, misurato;
* l'**insieme** dei token rende l'ordine irrilevante, che è esattamente la
  differenza fra le due convenzioni (`{garces, facundo}` da entrambe le parti);
* la **squadra non serve** e sarebbe dannosa: richiederebbe di allineare anche i
  nomi dei club (un secondo problema di normalizzazione) per guadagnare nulla —
  la coppia (data, nome) è già praticamente univoca: **15 chiavi ambigue su
  35.356**, lo 0,04%.

⚠️ Le chiavi ambigue NON si agganciano. Due giocatori diversi con lo stesso
insieme di token nello stesso giorno esistono, e sceglierne uno a caso
significherebbe attribuire a un giocatore la carriera di un altro — lo stesso
errore che la verifica d'identità Wikidata è servita a chiudere, rifatto qui a
valle. Meglio un buco dichiarato che un aggancio inventato.

⏱️ R8: l'aggancio è **`statico`** — lega un'identità a un'identità, non aggiunge
nessuna misura. Non cambia la disponibilità temporale di ciò che collega: le
statistiche restano `post`, la carriera resta da leggere con `career_before`.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

# Lettere che NFKD **non** decompone, perché non sono lettere accentate ma
# lettere a sé: la `ı` turca senza punto, la `ø` danese, la `ł` polacca. Senza
# questa tabella `Kenan Yıldız` non aggancia `Yildiz Kenan` — misurato: vale
# 4 giocatori e 101 righe, cioè lo 0,3%.
_TRADUZIONE = str.maketrans({
    "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
    "ß": "ss", "æ": "ae", "Æ": "ae", "ð": "d", "þ": "th",
    "ı": "i", "İ": "i", "ħ": "h", "ŋ": "n", "œ": "oe", "ĸ": "k",
})


def normalizza_nome(nome: str | None) -> frozenset[str]:
    """Il nome ridotto a un **insieme** di token minuscoli e senza diacritici.

    Insieme e non lista: è ciò che rende «Cognome Nome» e «Nome Cognome» la
    stessa chiave. I token di una lettera sola si scartano (iniziali puntate).
    """
    if not isinstance(nome, str) or not nome.strip():
        return frozenset()
    t = nome.translate(_TRADUZIONE)
    t = "".join(c for c in unicodedata.normalize("NFKD", t)
                if not unicodedata.combining(c))
    t = re.sub(r"[^a-z ]", " ", t.lower())
    return frozenset(x for x in t.split() if len(x) > 1)


def _chiave(data, nome) -> str:
    tok = normalizza_nome(nome)
    if not tok:
        return ""
    return f"{pd.Timestamp(data).strftime('%Y%m%d')}|{'_'.join(sorted(tok))}"


def tabella_aggancio(appearances=None, *, dal="2025-07-01") -> pd.DataFrame:
    """La tabella `chiave -> player_id`, costruita dalle `appearances`.

    Le chiavi che mappano a **più di un** `player_id` vengono ESCLUSE, non
    risolte a caso: vedi la nota in testa al modulo.
    """
    from . import careers as C

    app = appearances if appearances is not None else C._load_appearances()
    a = app[app["date"] >= pd.Timestamp(dal)].copy()
    nomi = pd.read_csv(
        C.ROOT_DATA.parent / "files" / "player_scores" / "players.csv.gz",
        usecols=["player_id", "name"],
    )
    a = a.merge(nomi, on="player_id", how="left")
    a["chiave"] = [_chiave(d, n) for d, n in zip(a["date"], a["name"])]
    a = a[a["chiave"] != ""]

    per_chiave = a.groupby("chiave")["player_id"].agg(["nunique", "first"])
    univoche = per_chiave[per_chiave["nunique"] == 1]
    return pd.DataFrame({
        "chiave": univoche.index,
        "player_id": univoche["first"].to_numpy(),
    })


def collega(df: pd.DataFrame, appearances=None, *, colonna_nome="Giocatore",
            colonna_data="Data") -> pd.DataFrame:
    """Aggiunge `player_id` a un DataFrame di statistiche diretta.it.

    Ritorna una COPIA con la colonna in più; le righe non agganciate hanno
    `player_id` nullo — dichiarato, non silenzioso.
    """
    out = df.copy()
    date = pd.to_datetime(out[colonna_data], dayfirst=True)
    out["chiave"] = [_chiave(d, n) for d, n in zip(date, out[colonna_nome])]
    mappa = tabella_aggancio(appearances).set_index("chiave")["player_id"]
    out["player_id"] = out["chiave"].map(mappa)
    return out.drop(columns="chiave")


# --------------------------------------------------------------------------
# Secondo passaggio: l'ELIMINAZIONE
# --------------------------------------------------------------------------
# Il primo passaggio aggancia il 95,4% e lascia fuori 94 nomi. Non sono nomi
# «sporchi»: sono nomi SCRITTI DIVERSAMENTE dalle due fonti — nome legale contro
# nome d'uso (`Pope Nicholas David` / `Nick Pope`, `Livramento Valentino` /
# `Tino Livramento`), cognomi composti spagnoli, mononimi (`Djene`, `Fermín`).
# Nessuna normalizzazione del nome può chiuderli, perché il nome non è lo stesso.
#
# Ma c'è un argomento più forte del nome, ed è STRUTTURALE. Misurato sui dati:
# per ogni (partita, squadra) le due fonti elencano gli STESSI giocatori —
# 1.145 coppie con righe residue si distribuiscono in (1,1) 774, (2,2) 268,
# (3,3) 83, (4,4) 11, (5,5) 1, e solo **9 su 1.145** hanno conteggi diversi.
#
# Quindi dove resta UNA riga diretta libera e UN giocatore libero in quella
# partita, sono la stessa persona **per eliminazione**: non serve che i nomi si
# somiglino, serve che non ci sia nessun altro che possano essere.
#
# ⚠️ Perché questo è più sicuro del nome, e non meno: l'aggancio per somiglianza
# sbagliava proprio dove il nome ingannava. `Cunat Pablo` veniva agganciato a
# `Pablo Campos` perché condividevano `pablo` — un nome di battesimo che nel
# dataset compare 124 volte, mentre `cunat` non compare mai. L'eliminazione non
# ha questo modo di fallire: non guarda il nome.

SOGLIA_TOKEN_COMUNE = 50   # oltre questa frequenza un token non prova nulla


def _liberi(cand, usati, chiave):
    return [(p, n) for p, n in cand.get(chiave, []) if p not in usati[chiave]]


def collega_per_eliminazione(df, appearances=None, *, colonna_nome="Giocatore",
                             colonna_data="Data", colonna_squadra="Squadra"):
    """`collega` + secondo passaggio per eliminazione dentro la singola partita.

    La mappa squadra→`club_id` **non** si costruisce allineando i nomi dei club:
    si DEDUCE dalle righe già agganciate al primo passaggio. Purezza misurata
    0,9999 su 60 squadre — un problema di normalizzazione in meno, e risolto
    dai dati invece che da una tabella scritta a mano.
    """
    import collections

    from . import careers as C

    out = collega(df, appearances, colonna_nome=colonna_nome,
                  colonna_data=colonna_data)
    date = pd.to_datetime(out[colonna_data], dayfirst=True)

    app = appearances if appearances is not None else C._load_appearances()
    a = app[app["date"] >= pd.Timestamp("2025-07-01")][
        ["player_id", "date", "player_club_id"]].copy()
    nomi = pd.read_csv(
        C.ROOT_DATA.parent / "files" / "player_scores" / "players.csv.gz",
        usecols=["player_id", "name"])
    a = a.merge(nomi, on="player_id", how="left")

    freq = collections.Counter()
    for n in nomi["name"]:
        for t in normalizza_nome(n):
            freq[t] += 1

    agg = out["player_id"].notna()
    # Il club della riga già agganciata si prende con un MERGE, non con una
    # chiave-stringa: `astype(str)` su una colonna di date rende `2025-07-01`
    # mentre un f-string sullo stesso Timestamp rende `2025-07-01 00:00:00`.
    # Le due chiavi non combaciano mai e la mappa esce vuota — in silenzio,
    # perché un dizionario che non trova nulla non è un errore. Costato un
    # passaggio intero che sembrava funzionare e non agganciava niente.
    ponte = a[["player_id", "date", "player_club_id"]].rename(
        columns={"date": "_d"})
    tmp = pd.DataFrame({"player_id": out["player_id"], "_d": date})
    out["_cid"] = tmp.merge(ponte, on=["player_id", "_d"],
                            how="left")["player_club_id"].to_numpy()
    club = (out[agg].groupby(colonna_squadra)["_cid"]
            .agg(lambda s: s.value_counts().idxmax() if s.notna().any() else None))

    usati = collections.defaultdict(set)
    for p, d, c in zip(out.loc[agg, "player_id"], date[agg], out.loc[agg, "_cid"]):
        usati[(d, c)].add(p)
    cand = collections.defaultdict(list)
    for r in a.itertuples():
        cand[(r.date, r.player_club_id)].append((r.player_id, r.name))

    da_fare = collections.defaultdict(list)
    for i in out.index[~agg]:
        cid = club.get(out.at[i, colonna_squadra])
        if cid is not None:
            da_fare[(date[i], cid)].append(i)

    # I passaggi si ripetono FINO A PUNTO FISSO. Ogni assegnazione toglie un
    # candidato dal mucchio e può rendere univoco un caso che prima non lo era:
    # girare una volta sola lascia sul tavolo proprio i casi che si sbloccano a
    # vicenda. Misurato: il portiere del Levante restava fuori solo per questo.
    for _ in range(10):
        fatto = 0
        for chiave, righe in da_fare.items():
            aperte = [i for i in righe if pd.isna(out.at[i, "player_id"])]
            if not aperte:
                continue
            liberi = _liberi(cand, usati, chiave)
            if len(aperte) == 1 and len(liberi) == 1:
                # ELIMINAZIONE: nessun altro che possano essere.
                out.at[aperte[0], "player_id"] = liberi[0][0]
                usati[chiave].add(liberi[0][0])
                fatto += 1
                continue
            # Più di uno per parte: qui il nome torna a servire, ma su un insieme
            # di due o tre. Si prende il candidato con la sovrapposizione di token
            # STRETTAMENTE maggiore di ogni altro — non «almeno un token raro».
            #
            # La soglia sulla rarità era una difesa contro un falso positivo che
            # falso non era: `Cunat Pablo` -> `Pablo Campos` sembrava sbagliato
            # perché i cognomi non si toccano, ed è invece la STESSA persona —
            # Pablo Cuñat Campos, portiere del Levante nato il 28/04/2002
            # (verificato sul sito del club e sulla stampa spagnola, e la data
            # coincide con la nostra). In spagnolo i cognomi sono DUE, paterno e
            # materno, e due fonti possono sceglierne uno ciascuna: la
            # sovrapposizione parziale è la norma, non un indizio di errore.
            for i in aperte:
                tk = normalizza_nome(out.at[i, colonna_nome])
                punteggi = sorted(
                    ((len(normalizza_nome(n) & tk), p) for p, n in
                     _liberi(cand, usati, chiave)), reverse=True)
                if (punteggi and punteggi[0][0] > 0
                        and (len(punteggi) == 1 or punteggi[0][0] > punteggi[1][0])):
                    out.at[i, "player_id"] = punteggi[0][1]
                    usati[chiave].add(punteggi[0][1])
                    fatto += 1
        if not fatto:
            break

    # ---------------------------------------------------------------- terzo
    # L'INTERSEZIONE SULLA STAGIONE. Un nome può restare ambiguo in una singola
    # partita — due liberi, nessun token che li separi — e non esserlo affatto
    # sull'anno: se in tutte e 32 le giornate il candidato libero è sempre lo
    # stesso, l'intersezione lo identifica. È la stessa logica dell'eliminazione
    # applicata all'asse del tempo invece che a quello della rosa, e chiude 15
    # dei 20 casi residui (`Garcia de Haro Raul` → Raúl García, `Oliveira Tiago`
    # → Tiago Gabriel, `de la Fuente Adrian` → Adrián Dela).
    #
    # L'intersezione si fa per (nome, SQUADRA), non per nome: un giocatore che
    # cambia club a gennaio è due insiemi di candidati diversi, e intersecarli
    # darebbe il vuoto proprio sui trasferiti (`Lopez Fernando`, Celta e poi
    # Wolves — due volte lo stesso Fer López, ma da due rose diverse).
    resta = out["player_id"].isna()
    if resta.any():
        gruppi = collections.defaultdict(list)
        for i in out.index[resta]:
            gruppi[(out.at[i, colonna_nome], out.at[i, colonna_squadra])].append(i)
        for (_, squadra), righe in gruppi.items():
            cid = club.get(squadra)
            if cid is None:
                continue
            comune = None
            for i in righe:
                liberi = {p for p, _ in _liberi(cand, usati, (date[i], cid))}
                comune = liberi if comune is None else (comune & liberi)
            if comune and len(comune) == 1:
                pid = next(iter(comune))
                for i in righe:
                    out.at[i, "player_id"] = pid
                    usati[(date[i], cid)].add(pid)

    # ------------------------------------------------------ eccezioni (R3)
    # Ultimo: il registro degli agganci dichiarati a mano. Serve per i casi che
    # l'automatismo NON PUO' raggiungere, non per quelli su cui non è d'accordo:
    # l'aggancio passa dalle presenze, e dove la fonte delle presenze non ha la
    # riga non c'è nessun candidato fra cui scegliere. È il caso di Alessandro
    # Romano, che esiste nell'anagrafica (nato il 17/06/2006, coincide con la
    # fonte esterna) ma di cui player-scores non registra l'esordio in Serie A.
    #
    # Ogni riga del registro porta motivo, fonte e data della verifica, e si
    # applica SOLO dove il player_id è ancora vuoto: una regola che sovrascriva
    # l'automatismo sarebbe una modifica a mano dei dati mascherata da eccezione.
    reg = C.ROOT_DATA / "aggancio_manuale.csv"
    if reg.exists():
        manuale = pd.read_csv(reg)
        attese = {"giocatore_diretta", "squadra", "player_id", "motivo", "fonte"}
        mancanti = attese - set(manuale.columns)
        if mancanti:
            # Meglio dirlo qui che lasciare un AttributeError dentro un loop:
            # chi ha appena modificato il registro deve capire cosa manca.
            raise ValueError(
                f"{reg}: colonne mancanti {sorted(mancanti)}. Ogni eccezione "
                "dichiara cosa aggancia, perché e su quale fonte (R3).")
        chiavi = {(r.giocatore_diretta, r.squadra): r.player_id
                  for r in manuale.itertuples()}
        for i in out.index[out["player_id"].isna()]:
            pid = chiavi.get((out.at[i, colonna_nome], out.at[i, colonna_squadra]))
            if pid is not None:
                out.at[i, "player_id"] = pid

    return out.drop(columns="_cid")
