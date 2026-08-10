#!/usr/bin/env python3
"""Aggancia le raccolte manuali di coppa al resto del database (Fase 139-bis).

TRE PONTI, non uno. La raccolta diretta.it parla per NOMI; il database parla per
identificatori. Finche' non si toccano, «la carriera di questo giocatore» e
«come ha giocato in Coppa Italia» restano due frasi che non si possono dire
insieme.

  squadre    nome diretta.it   -> `club_id`      (registro player-scores)
  partite    `ID partita`      -> `game_id`      (la stessa partita nelle due fonti)
  giocatori  nome diretta.it   -> `player_id`    (l'anagrafica, e quindi le carriere)

⭐ **L'ordine dei tre ponti non e' arbitrario: il terzo si regge sul secondo.**
Agganciata la partita, i candidati per un giocatore non sono piu' «tutti quelli
in campo quel giorno» ma le **18-23 persone di quel club in quella partita**. Su
un insieme cosi' piccolo il confronto per nome diventa quasi sempre univoco.

Misurato, ed e' la ragione per cui questo script non usa
`player_identity.collega_per_eliminazione`: quella funzione aggancia per
`(data, token del nome)` e va benissimo sui CAMPIONATI, dove diretta.it scrive
il nome intero («Garces Facundo»). Nelle **coppe** lo abbrevia («Motta E.»), il
token set e' `{motta}` contro `{emanuele, motta}` e la chiave non combacia mai:
**25,6%** sulla Coppa Italia, **12,0%** sulla Pokal. Passando dal vincolo della
partita: **97,5%** e **98,0%**.

⚠️ Un aggancio ambiguo NON si sceglie a caso: resta vuoto. Attribuire a un
giocatore la carriera di un altro e' peggio di non sapere (nota in testa a
`player_identity`). L'eliminazione scatta **solo** quando resta una sola
possibilita' da entrambe le parti — 46 righe su 4.651.

USO:
    python scripts/aggancia_coppe.py                 # tutte le raccolte trovate
    python scripts/aggancia_coppe.py --coppa "DFB-Pokal"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from src.data.coppe_aggancio import appaia_partite, sinonimi_squadra  # noqa: E402
from scripts.registra_raccolta_coppa_diretta import (  # noqa: E402
    FILE_MANIFESTO,
    _stessa_persona as _uguali,
    _token as _tok,
)

USCITA = RADICE / "data" / "coppe_2526"


def _log(m: str) -> None:
    print(m, flush=True)


def _aggancia_giocatori(F: pd.DataFrame, partite: pd.DataFrame, cid) -> pd.DataFrame:
    """`player_id` per ogni riga di formazione, dentro la singola partita.

    Due passate, nell'ordine che conta:
      1. **per nome**, con la stessa regola della porta d'ingresso (sottoinsieme
         dei token + iniziale come prefisso) — cosi' «Motta E.» trova «Emanuele
         Motta» ma «Esposito Sa.» non finisce su «Francesco Esposito»;
      2. **per eliminazione**: se in un (partita, club) resta UN nostro nome
         spaiato e UN candidato libero, sono la stessa persona per esclusione.
         Se ne restano due o piu', **nessuno** viene agganciato: un aggancio
         indovinato attribuisce a un giocatore la carriera di un altro.
    """
    nostre = pd.read_csv(USCITA / "formazioni.csv")
    mappa = dict(zip(partite.id_diretta, partite.game_id))

    F = F.copy()
    F["game_id"] = F["ID partita"].map(mappa)
    F["club_id"] = F.Squadra.map(cid).astype("Int64")
    F["player_id"] = pd.array([pd.NA] * len(F), dtype="Int64")
    F["metodo"] = None

    per_gruppo = {k: v for k, v in nostre.groupby(["game_id", "club_id"])}
    for (gid, club), righe in F.dropna(subset=["game_id"]).groupby(["game_id", "club_id"]):
        cand = per_gruppo.get((gid, club))
        if cand is None:
            continue
        liberi = list(zip(cand.player_id, [_tok(x) for x in cand.giocatore]))
        spaiati = []
        for idx, nome in zip(righe.index, righe.Giocatore):
            t = _tok(nome)
            for i, (pid, tb) in enumerate(liberi):
                if _uguali(t, tb):
                    F.at[idx, "player_id"] = pid
                    F.at[idx, "metodo"] = "nome"
                    liberi.pop(i)
                    break
            else:
                spaiati.append(idx)
        # eliminazione: solo se resta UNA possibilita' da entrambe le parti
        if len(spaiati) == 1 and len(liberi) == 1:
            F.at[spaiati[0], "player_id"] = liberi[0][0]
            F.at[spaiati[0], "metodo"] = "eliminazione"

    # --- terza passata: le partite SENZA controparte ---------------------- #
    # Le finali non esistono nella fonte automatica (Fase 138), quindi per
    # quelle righe non c'e' nessun (game_id, club_id) da cui pescare. Il
    # ripiego e' la ROSA STAGIONALE del club: chi ha almeno una presenza per
    # quel club nel 2025-26.
    #
    # ⚠️ E' un vincolo piu' DEBOLE — ~30-40 persone invece di 18-23, e non c'e'
    # la garanzia che il giocatore fosse in campo quel giorno. Per questo:
    # (a) si applica SOLO dove la prima strada non esiste, mai come scorciatoia;
    # (b) accetta solo il match UNIVOCO, mai l'eliminazione;
    # (c) si marca `rosa_stagionale`, cosi' a valle si puo' distinguere.
    # Misurato sulle 92 righe delle finali: 90 univoci, 0 ambigui, 2 assenti.
    orfane = F[F.player_id.isna() & F.game_id.isna()]
    if len(orfane):
        rosa = _rosa_stagionale()
        for idx, riga in orfane.iterrows():
            cand = rosa.get(riga.club_id, [])
            t = _tok(riga.Giocatore)
            hit = [p for p, tb in cand if _uguali(t, tb)]
            if len(hit) == 1:
                F.at[idx, "player_id"] = hit[0]
                F.at[idx, "metodo"] = "rosa_stagionale"
    return F


def _rosa_stagionale(dal: str = "2025-07-01") -> dict:
    """`club_id -> [(player_id, token del nome)]` per la stagione 2025-26."""
    from src.data import careers as C

    app = C._load_appearances()
    a = (app[app.date >= pd.Timestamp(dal)][["player_id", "player_club_id"]]
         .drop_duplicates())
    nomi = pd.read_csv(RADICE / "files" / "player_scores" / "players.csv.gz",
                       usecols=["player_id", "name"])
    a = a.merge(nomi, on="player_id", how="left")
    return {c: list(zip(d.player_id, [_tok(n) for n in d.name]))
            for c, d in a.groupby("player_club_id")}


def raccolte() -> list[Path]:
    return sorted(d for d in (RADICE / "files").iterdir()
                  if (d / FILE_MANIFESTO).exists())


def aggancia(cartella: Path, appearances=None) -> tuple[dict, dict]:
    manifesto = json.loads((cartella / FILE_MANIFESTO).read_text(encoding="utf-8"))
    coppa = manifesto["coppa"]
    _log(f"\n=== {coppa}  ({cartella.name})")

    P = pd.read_csv(cartella / "partite.csv")
    F = pd.read_csv(cartella / "formazioni_e_cambi.csv")
    N = pd.read_csv(USCITA / "partite.csv")
    N = N[N.competizione == coppa].copy()

    # ⭐ UNA sola implementazione, condivisa con la porta d'ingresso: risoluzione
    # dei club (alias, registro, **deduzione dalle partite**) e appaiamento
    # (chiave con ripiego sul nome, **appaiamento per nome dentro la giornata**).
    # Qui c'era una seconda versione che si fermava a `Agganciatore.aggancia`:
    # 77/117 partite sulla Copa del Rey e 0/201 sulla Coupe de France, mentre lo
    # script gemello sugli stessi file ne appaiava 117 e 161. Due implementazioni
    # divergenti dello stesso appaiamento ERANO il bug.
    P = P.copy()
    app = appaia_partite(P, N)
    cid = app.cid

    # --- 1. squadre -------------------------------------------------------- #
    nomi = sorted(set(P.Casa) | set(P.Ospite))
    squadre = pd.DataFrame({"competizione": coppa, "nome_diretta": nomi})
    squadre["club_id"] = squadre.nome_diretta.map(cid).astype("Int64")
    _log(f"  squadre:   {squadre.club_id.notna().sum()}/{len(squadre)} agganciate"
         f"  (di cui {len(app.dedotti)} dedotte dalle partite)")

    # --- 2. partite -------------------------------------------------------- #
    P["data_iso"] = app.data_iso
    P["club_casa"] = pd.array(list(P.Casa.map(cid)), dtype="Int64")
    P["club_ospite"] = pd.array(list(P.Ospite.map(cid)), dtype="Int64")
    P["k"] = app.k_manuale
    N["k"] = app.k_automatica
    N_unica = N.drop_duplicates(subset="k")
    partite = P.merge(N_unica[["k", "game_id", "turno"]], on="k", how="left",
                      suffixes=("", "_nostro"))
    partite["Competizione"] = coppa
    partite = partite[["Competizione", "Turno", "data_iso", "Casa", "Ospite",
                       "club_casa", "club_ospite", "ID partita", "game_id",
                       "turno"]].rename(columns={
                           "Competizione": "competizione", "Turno": "turno_diretta",
                           "data_iso": "data", "Casa": "casa", "Ospite": "ospite",
                           "ID partita": "id_diretta", "turno": "turno_nostro"})
    # ⚠️ «appaiate» e «agganciate a un `game_id`» sono due cose diverse, e la
    # Coupe de France e' il caso che le separa: 161 righe su 201 trovano la loro
    # gemella nella fonte automatica (ed e' cosi' che se ne verificano i
    # punteggi), ma quella fonte e' Wikipedia e non ha `game_id` — quindi 0/201
    # qui. Il ponte manca dalla sponda opposta, non da questa.
    appaiate = int(P.k.isin(set(N.k)).sum())
    _log(f"  partite:   {partite.game_id.notna().sum()}/{len(partite)} agganciate "
         f"a un `game_id`  ·  {appaiate}/{len(P)} appaiate con la fonte automatica"
         + (f" ({app.rimappate} per nome dentro la giornata"
            + (f", {app.contese} contese e lasciate vuote)" if app.contese else ")")
            if app.rimappate else ""))

    # --- 3. giocatori ------------------------------------------------------ #
    # ⚠️ NON si usa `player_identity.collega_per_eliminazione`, ed e' una
    # scelta misurata. Quella funzione aggancia per `(data, token del nome)`, e
    # funziona sui CAMPIONATI perche' li' diretta.it scrive il nome intero
    # («Garces Facundo»). Nelle coppe lo **abbrevia** («Motta E.»): il token set
    # e' `{motta}` contro `{emanuele, motta}` e la chiave non combacia mai.
    # Misurato: 25,6% sulla Coppa Italia, 12,0% sulla Pokal.
    #
    # Qui c'e' un vincolo molto piu' forte, e ce l'abbiamo gia': la **partita
    # e' agganciata**. Dentro un singolo (game_id, club_id) i candidati sono le
    # 18-23 persone che hanno giocato QUELLA partita per QUEL club — non tutte
    # quelle in campo quel giorno. Su un insieme cosi' piccolo il confronto per
    # sottoinsieme + iniziale (lo stesso della porta d'ingresso) e' quasi
    # sempre univoco, e cio' che resta si chiude per eliminazione.
    g = _aggancia_giocatori(F, partite, cid)
    # ⚠️ la colonna `Competizione` e' l'etichetta della FONTE («Carabao Cup»),
    # non il nome canonico del progetto («EFL Cup»). Le due convivevano nelle
    # tabelle di aggancio, e un filtro per competizione ne avrebbe visto meta'.
    g["Competizione"] = coppa
    g["data_iso"] = pd.to_datetime(g.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    giocatori = g[["Competizione", "Turno", "data_iso", "Squadra", "club_id",
                   "Giocatore", "player_id", "metodo", "Gruppo", "Numero",
                   "Ruolo", "ID partita", "game_id"]].rename(columns={
                       "Competizione": "competizione", "Turno": "turno",
                       "data_iso": "data", "Squadra": "squadra",
                       "Giocatore": "nome_diretta", "Gruppo": "gruppo",
                       "Numero": "numero", "Ruolo": "ruolo",
                       "ID partita": "id_diretta"})
    # --- 4. eventi e statistiche ------------------------------------------ #
    # Erano rimasti fuori: 8.475 righe di evento e 8.115 di statistica per
    # giocatore raccolte e mai collegate a niente. Si agganciano con la stessa
    # anagrafica gia' risolta al punto 3 — dentro la stessa partita il nome di
    # un evento e' lo stesso nome della formazione, quindi non serve rifare il
    # confronto: basta una mappa (id_diretta, nome) -> player_id.
    # ⚠️ `stat_giocatori` NON ha la colonna `ID partita` (ce l'hanno partite,
    # formazioni ed eventi): la chiave comune a tutti e quattro i fogli e'
    # (Data, Casa, Ospite). Si usa quella, cosi' la stessa funzione serve i due
    # fogli senza casi speciali.
    def chiave(d):
        return list(zip(d.Data, d.Casa, d.Ospite))

    # ⭐ LA CHIAVE E' (partita, CLUB), non la partita. Cercare i candidati nella
    # partita intera li prende da ENTRAMBE le rose, e in una partita ci sono
    # omonimi: Navalcarnero-Getafe del 03/12/2025 ha «Juanmi» (Getafe, 126737) e
    # «Juanmi Heredero» (Navalcarnero, 285973). Con la chiave per partita il
    # dizionario per nome collideva e **lo stesso `player_id` finiva sulle due
    # righe di squadre diverse**; altre due righe prendevano un giocatore
    # dell'altra squadra. Tre righe sbagliate su 9.312 — poche, ma sono
    # «certezze sbagliate» (R6), non buchi: a valle nessuno le vede.
    # Trovate confrontando il club del giocatore con il club del suo lato.
    def chiave_club(d, club_col):
        return list(zip(d.Data, d.Casa, d.Ospite, club_col))

    kg = chiave_club(g, g.club_id)
    anagrafica = {(k, n): p for k, n, p in
                  zip(kg, g.Giocatore, g.player_id) if pd.notna(p)}
    # ⚠️ `stat_giocatori` scrive i nomi per INTERO («Dumfries Denzel») mentre
    # `formazioni` li abbrevia («Dumfries D.»): la ricerca per stringa esatta
    # trovava 30 righe su 1.307. Per quel foglio serve la regola di confronto,
    # non l'uguaglianza — e i nomi interi sono anzi il caso FACILE.
    per_partita = {}
    for k, n, pid in zip(kg, g.Giocatore, g.player_id):
        if pd.notna(pid):
            per_partita.setdefault(k, []).append((_tok(n), pid))
    # `partite` nasce da un merge LEFT su `P`, quindi le righe sono allineate:
    # la chiave grezza si prende da P, il game_id dal risultato.
    mappa_gid = {k: v for k, v in zip(chiave(P), partite.game_id) if pd.notna(v)}
    mappa_gid_id = {k: v for k, v in zip(P["ID partita"], partite.game_id)
                    if pd.notna(v)}

    def collega_foglio(nome_file: str, colonna_nome: str,
                       una_riga_per_persona: bool = False) -> pd.DataFrame:
        d = pd.read_csv(cartella / nome_file)
        d["competizione"] = coppa
        # ⚠️ Il foglio delle statistiche arriva da un SECONDO consegnato, e la
        # stessa fonte puo' scrivere un club in due modi fra i due file: sulla
        # Copa del Rey «Cieza» contro «Ciudad Cieza» di `partite.csv`. La
        # chiave e' (Data, Casa, Ospite): senza riportare i nomi alla stessa
        # grafia, le 27 righe di quelle due partite perdono `game_id` e
        # `player_id` — e il calo (94,2% -> 92,3%) sembra un limite del dato.
        # Stessa funzione della porta d'ingresso, per la lezione della F139-quater.
        sin = sinonimi_squadra(P, d)
        if sin:
            for col in ("Casa", "Ospite", "Squadra"):
                if col in d.columns:
                    d[col] = [sin.get(str(x), x) for x in d[col]]
        d["game_id"] = pd.Series([mappa_gid.get(k) for k in chiave(d)],
                                 index=d.index).astype("Int64")

        # ⚠️ Il club della riga, e qui c'e' la trappola: `stat_giocatori` ha la
        # colonna `Squadra`, **`eventi` no** — ha solo `Lato`. Prendendolo dal
        # solo `Squadra` gli eventi restavano senza club e ripiegavano sulla
        # ricerca larga: 3.639 righe agganciate diventavano 561. Il lato basta,
        # perche' la partita dice chi gioca in casa e chi fuori.
        if "Squadra" in d.columns:
            club_riga = [cid(x) for x in d["Squadra"]]
        else:
            # ⭐ E l'AUTOGOL va al contrario. diretta.it registra l'autogol sul
            # lato che ne **beneficia** — e' la stessa convenzione che la Fase
            # 138 aveva gia' misurato sulla fonte automatica (invertirla faceva
            # crollare la resa dal 98,5% all'89,7%) — ma il giocatore e'
            # dell'altra squadra. Senza questa riga i 35 autogol delle sei
            # coppe restano senza `player_id`: cercati nella rosa sbagliata.
            autogol = (d["Tipo evento"].astype(str)
                       .str.contains("utogol", na=False))
            club_riga = [cid((o if a else c) if l == "Casa" else (c if a else o))
                         for l, c, o, a in
                         zip(d["Lato"], d["Casa"], d["Ospite"], autogol)]

        def risolvi(k_club, k_part, n):
            if k_club[3] is not None:
                diretto = anagrafica.get((k_club, n))
                if diretto is not None:
                    return diretto
                t = _tok(n)
                hit = [pid for tb, pid in per_partita.get(k_club, [])
                       if _uguali(t, tb)]
                if len(hit) == 1:
                    return hit[0]
                return None
            # ripiego senza club (Coupe de France: i club non sono nel
            # registro): si cerca in tutta la partita, per nome esatto e poi
            # per regola, e **solo** se il risultato e' unico.
            for kk, righe in per_partita.items():
                if kk[:3] == k_part and (kk, n) in anagrafica:
                    return anagrafica[(kk, n)]
            t = _tok(n)
            hit = [pid for kk, righe in per_partita.items() if kk[:3] == k_part
                   for tb, pid in righe if _uguali(t, tb)]
            return hit[0] if len(hit) == 1 else None

        d["player_id"] = pd.Series(
            [risolvi((dd, cc, oo, cl), (dd, cc, oo), n)
             for (dd, cc, oo), cl, n in
             zip(chiave(d), club_riga, d[colonna_nome])],
            index=d.index).astype("Int64")

        # ⭐ Un `player_id` non puo' servire DUE persone nella stessa partita.
        # Ogni riga si risolve per conto suo, quindi due nomi diversi dello
        # stesso club possono rivendicare lo stesso candidato: nella Copa del
        # Rey «Perez Andoni» e «Perez Alex» del Club Portugalete finivano
        # entrambi su 634542. E' la regola di sempre applicata qui — dove non
        # c'e' un vincitore unico non vince nessuno — e vale solo per i fogli
        # con UNA riga per persona (le statistiche); negli EVENTI lo stesso
        # giocatore ha per forza piu' righe.
        if una_riga_per_persona:
            gruppo = d.groupby(["game_id", "player_id"], dropna=True)
            contesi = {k for k, v in gruppo[colonna_nome].nunique().items()
                       if v > 1}
            if contesi:
                d["player_id"] = [
                    pd.NA if (g, p) in contesi else p
                    for g, p in zip(d.game_id, d.player_id)]
                _log(f"    ⚠️ {len(contesi)} `player_id` rivendicati da due "
                     f"persone nello stesso match: lasciati VUOTI")
        return d

    # --- statistiche di SQUADRA (nuove, Fase 139-quater) ------------------- #
    # Non hanno un giocatore: si agganciano a (game_id, club_id). E' il primo
    # dato di coppa diviso per PERIODO — Totale / 1o tempo / 2o tempo /
    # Supplementari — cioe' la forma che serve al modello a due stadi.
    squadra = None
    f_sq = cartella / "stat_squadra.csv"
    if f_sq.exists():
        squadra = pd.read_csv(f_sq)
        squadra["competizione"] = coppa
        sin_sq = sinonimi_squadra(P, squadra)
        if sin_sq:
            for col in ("Casa", "Ospite", "Squadra"):
                if col in squadra.columns:
                    squadra[col] = [sin_sq.get(str(x), x) for x in squadra[col]]
        squadra["game_id"] = squadra["ID partita"].map(mappa_gid_id).astype("Int64")
        squadra["club_id"] = squadra.Squadra.map(cid).astype("Int64")
        _log(f"  stat squadra: {int(squadra.game_id.notna().sum())}/{len(squadra)} "
             f"con game_id · {int(squadra.club_id.notna().sum())}/{len(squadra)} "
             f"con club_id")

    eventi = collega_foglio("eventi.csv", "Giocatore")
    stat = collega_foglio("stat_giocatori.csv", "Giocatore",
                          una_riga_per_persona=True)
    # negli eventi ci sono righe senza persona (es. il punteggio dopo un gol
    # avversario): il denominatore giusto e' quelle CON un nome.
    ev_con_nome = eventi[eventi.Giocatore.notna()]
    _log(f"  eventi:    {int(ev_con_nome.player_id.notna().sum())}/"
         f"{len(ev_con_nome)} righe con giocatore agganciate "
         f"(su {len(eventi)} totali)")
    _log(f"  statistiche: {int(stat.player_id.notna().sum())}/{len(stat)} agganciate")

    tot, agg = len(giocatori), int(giocatori.player_id.notna().sum())
    tit = giocatori[giocatori.gruppo == "Titolare"]
    _log(f"  giocatori: {agg}/{tot} agganciati a un `player_id` ({agg/tot:.1%})"
         f"  ·  titolari {int(tit.player_id.notna().sum())}/{len(tit)} "
         f"({tit.player_id.notna().mean():.1%})")

    quadro = {
        "coppa": coppa,
        "squadre": {"totali": len(squadre),
                    "agganciate": int(squadre.club_id.notna().sum()),
                    "non_agganciate": sorted(
                        squadre.loc[squadre.club_id.isna(), "nome_diretta"])},
        "partite": {"totali": len(partite),
                    "agganciate": int(partite.game_id.notna().sum()),
                    # dichiarato a parte: una partita puo' essere APPAIATA con la
                    # fonte automatica (e quindi verificata nei punteggi) senza
                    # avere un `game_id`, se quella fonte non ne ha — Coupe de
                    # France, 161 appaiate e 0 con identificatore.
                    "appaiate_con_la_fonte_automatica": appaiate,
                    "appaiate_per_nome_dentro_la_giornata": app.rimappate,
                    "contese_lasciate_vuote": app.contese,
                    "club_dedotti_dalle_partite": {k: int(v) for k, v
                                                   in sorted(app.dedotti.items())},
                    "non_agganciate": [
                        f"{r.data} {r.casa}-{r.ospite}"
                        for _, r in partite[partite.game_id.isna()].iterrows()]},
        "giocatori": {
            "righe": tot, "agganciate": agg,
            "quota": round(agg / tot, 4),
            "titolari": int(len(tit)),
            "titolari_agganciati": int(tit.player_id.notna().sum()),
            "persone_distinte": int(giocatori.player_id.nunique()),
        },
    }
    quadro["eventi"] = {
        "righe": int(len(eventi)),
        "con_giocatore": int(len(ev_con_nome)),
        "agganciate": int(ev_con_nome.player_id.notna().sum()),
        "con_game_id": int(eventi.game_id.notna().sum()),
    }
    quadro["statistiche"] = {
        "righe": int(len(stat)),
        "agganciate": int(stat.player_id.notna().sum()),
        "con_game_id": int(stat.game_id.notna().sum()),
    }
    tabelle = {"squadre": squadre, "partite": partite, "giocatori": giocatori,
               "eventi": eventi, "statistiche": stat}
    if squadra is not None:
        tabelle["statistiche_squadra"] = squadra
        quadro["statistiche_squadra"] = {
            "righe": int(len(squadra)),
            "con_game_id": int(squadra.game_id.notna().sum()),
            "con_club_id": int(squadra.club_id.notna().sum()),
        }
    return tabelle, quadro


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coppa", help="ne aggancia una sola")
    args = ap.parse_args()

    from src.data import careers as C
    _log("carico le presenze player-scores una volta sola…")
    appearances = C._load_appearances()

    tabelle = {"squadre": [], "partite": [], "giocatori": [],
               "eventi": [], "statistiche": [], "statistiche_squadra": []}
    quadri = []
    for d in raccolte():
        m = json.loads((d / FILE_MANIFESTO).read_text(encoding="utf-8"))
        if args.coppa and m["coppa"] != args.coppa:
            continue
        t, q = aggancia(d, appearances)
        for k, v in t.items():
            tabelle[k].append(v)
        quadri.append(q)

    if not quadri:
        _log("nessuna raccolta trovata")
        return 1

    USCITA.mkdir(parents=True, exist_ok=True)
    for k, pezzi in tabelle.items():
        if not pezzi:
            continue
        f = USCITA / f"aggancio_{k}.csv"
        pd.concat(pezzi, ignore_index=True).to_csv(f, index=False)
        _log(f"\n  scritto {f.relative_to(RADICE)}")
    f = USCITA / "aggancio_manifesto.json"
    f.write_text(json.dumps(quadri, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"  scritto {f.relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
