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

from src.data.club_matching import Agganciatore, normalizza  # noqa: E402
from scripts.registra_raccolta_coppa_diretta import (  # noqa: E402
    ALIAS_COPPA,
    FILE_MANIFESTO,
    _stessa_persona as _uguali,
    _token as _tok,
)

USCITA = RADICE / "data" / "coppe_2526"


def _log(m: str) -> None:
    print(m, flush=True)


def _chiave_partita(data, id_casa, id_osp, nome_casa, nome_osp) -> str:
    """Chiave di partita che regge anche senza `club_id` (vedi la nota gemella
    in `registra_raccolta_coppa_diretta.confronta_con_automatica`)."""
    def lato(idc, nome):
        return str(int(idc)) if pd.notna(idc) else "~" + "".join(
            sorted(normalizza(str(nome))))

    return f"{str(data)[:10]}|{lato(id_casa, nome_casa)}|{lato(id_osp, nome_osp)}"


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

    ag = Agganciatore()

    def cid(n):
        return ag.aggancia(ALIAS_COPPA.get(n, n))

    # --- 1. squadre -------------------------------------------------------- #
    nomi = sorted(set(P.Casa) | set(P.Ospite))
    squadre = pd.DataFrame({"competizione": coppa, "nome_diretta": nomi})
    squadre["club_id"] = squadre.nome_diretta.map(cid).astype("Int64")
    _log(f"  squadre:   {squadre.club_id.notna().sum()}/{len(squadre)} agganciate")

    # --- 2. partite -------------------------------------------------------- #
    P = P.copy()
    P["data_iso"] = pd.to_datetime(P.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    P["club_casa"] = P.Casa.map(cid).astype("Int64")
    P["club_ospite"] = P.Ospite.map(cid).astype("Int64")
    # ⚠️ Sul lato AUTOMATICO gli identificatori ci sono gia': non si ri-derivano
    # dal nome. Ri-derivarli e' un giro inutile che introduce un punto di
    # rottura — «FC Südtirol-Alto Adige» non si agganciava (il registro lo
    # chiama «FC Südtirol») e la partita Como-Südtirol spariva, pur avendo
    # `home_club_id` scritto nella riga accanto.
    N["club_casa"] = N.home_club_id.astype("Int64")
    N["club_ospite"] = N.away_club_id.astype("Int64")
    # ⚠️ NON si fa il merge su (data, id, id): dove gli id mancano — la Coupe de
    # France e' fatta di club dilettantistici che il registro non ha — tutte le
    # righe hanno la stessa chiave `(data, NaN, NaN)` e il merge esplode in un
    # prodotto cartesiano: 201 partite diventavano 4.804. Si riusa la stessa
    # chiave della porta d'ingresso, che ripiega sul nome quando l'id non c'e'.
    P["k"] = [_chiave_partita(d, a, b, na, nb) for d, a, b, na, nb
              in zip(P.data_iso, P.club_casa, P.club_ospite, P.Casa, P.Ospite)]
    N["k"] = [_chiave_partita(d, a, b, na, nb) for d, a, b, na, nb
              in zip(N.data, N.club_casa, N.club_ospite, N.casa, N.ospite)]
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
    _log(f"  partite:   {partite.game_id.notna().sum()}/{len(partite)} agganciate "
         f"a un `game_id`")

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

    anagrafica = {(k, n): p for k, n, p in
                  zip(chiave(g), g.Giocatore, g.player_id) if pd.notna(p)}
    # ⚠️ `stat_giocatori` scrive i nomi per INTERO («Dumfries Denzel») mentre
    # `formazioni` li abbrevia («Dumfries D.»): la ricerca per stringa esatta
    # trovava 30 righe su 1.307. Per quel foglio serve la regola di confronto,
    # non l'uguaglianza — e i nomi interi sono anzi il caso FACILE.
    per_partita = {}
    for k, n, pid in zip(chiave(g), g.Giocatore, g.player_id):
        if pd.notna(pid):
            per_partita.setdefault(k, []).append((_tok(n), pid))
    # `partite` nasce da un merge LEFT su `P`, quindi le righe sono allineate:
    # la chiave grezza si prende da P, il game_id dal risultato.
    mappa_gid = {k: v for k, v in zip(chiave(P), partite.game_id) if pd.notna(v)}

    def collega_foglio(nome_file: str, colonna_nome: str) -> pd.DataFrame:
        d = pd.read_csv(cartella / nome_file)
        d["competizione"] = coppa
        d["game_id"] = pd.Series([mappa_gid.get(k) for k in chiave(d)],
                                 index=d.index).astype("Int64")
        def risolvi(k, n):
            diretto = anagrafica.get((k, n))
            if diretto is not None:
                return diretto
            t = _tok(n)
            hit = [pid for tb, pid in per_partita.get(k, []) if _uguali(t, tb)]
            return hit[0] if len(hit) == 1 else None

        d["player_id"] = pd.Series(
            [risolvi(k, n) for k, n in zip(chiave(d), d[colonna_nome])],
            index=d.index).astype("Int64")
        return d

    eventi = collega_foglio("eventi.csv", "Giocatore")
    stat = collega_foglio("stat_giocatori.csv", "Giocatore")
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
    return {"squadre": squadre, "partite": partite, "giocatori": giocatori,
            "eventi": eventi, "statistiche": stat}, quadro


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coppa", help="ne aggancia una sola")
    args = ap.parse_args()

    from src.data import careers as C
    _log("carico le presenze player-scores una volta sola…")
    appearances = C._load_appearances()

    tabelle = {"squadre": [], "partite": [], "giocatori": [],
               "eventi": [], "statistiche": []}
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
        f = USCITA / f"aggancio_{k}.csv"
        pd.concat(pezzi, ignore_index=True).to_csv(f, index=False)
        _log(f"\n  scritto {f.relative_to(RADICE)}")
    f = USCITA / "aggancio_manifesto.json"
    f.write_text(json.dumps(quadri, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"  scritto {f.relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
