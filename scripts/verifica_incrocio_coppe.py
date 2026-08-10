#!/usr/bin/env python3
"""Le coppe 2025-26 si incrociano? Blocco per blocco, partita per partita.

LA DOMANDA (utente, 05/08/2026): «verifica che siamo in grado di incrociare
tutti i dati relativi a queste partite: allenatore, arbitro, statistiche di
squadra, meteo, 11 titolari + sostituzioni + statistiche individuali».

PERCHE' NON BASTA GUARDARE GLI SCHEMI. Ogni blocco vive in una tabella diversa,
con una chiave diversa, prodotta da una fonte diversa. «Le colonne ci sono» non
e' «per QUESTA partita ho tutto, e si unisce». La differenza si vede solo
contando riga per riga — ed e' lo stesso difetto della Fase 139-ter (8.475
righe di evento raccolte e collegate a niente, invisibili perche' le
percentuali erano al 99%).

⚠️ DUE COSE CHE UN CONTEGGIO INGENUO SBAGLIA, ed e' il motivo per cui questo
script produce TRE tabelle invece di una:

1. **Il perimetro.** Delle 662 partite di coppa, la raccolta manuale ne copre
   **580** per decisione dell'utente («da dove iniziano a giocare i club di
   seconda divisione»). Le altre 82 non sono un buco: non sono mai state
   chieste. Metterle al denominatore fa sembrare mancante cio' che e' fuori
   perimetro.
2. **Le due isole.** Le coppe hanno DUE chiavi, non una:

       fonte AUTOMATICA (player-scores)  `game_id`      arbitro, allenatori,
                                                        titolari, minuti
       raccolta MANUALE (diretta.it)     `ID partita`   sostituzioni al minuto,
                                                        statistiche individuali,
                                                        statistiche di squadra

   Contare i blocchi manuali sulla chiave automatica azzera la **Coupe de
   France**, che di `game_id` non ne ha nemmeno uno — e la fa sembrare vuota
   quando ha 2.495 righe di formazione e 476 di statistica di squadra. Sono
   leggibili: solo, non incrociabili con l'altra sponda.

USO:
    python scripts/verifica_incrocio_coppe.py            # le tre tabelle
    python scripts/verifica_incrocio_coppe.py --csv      # + matrice per partita
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

COPPE = RADICE / "data" / "coppe_2526"

# I blocchi chiesti dall'utente, con la sponda su cui vivono.
BLOCCHI = {
    "arbitro": "automatica",
    "allenatori": "automatica",
    "undici_titolari": "automatica",
    "minuti_giocati": "automatica",
    "sostituzioni": "manuale",
    "statistiche_individuali": "manuale",
    "statistiche_squadra": "manuale",
    "meteo": "assente",
}


def _log(m: str) -> None:
    print(m, flush=True)


def _sponda_automatica() -> pd.DataFrame:
    """Una riga per partita di coppa, coi blocchi di player-scores."""
    P = pd.read_csv(COPPE / "partite.csv")
    F = pd.read_csv(COPPE / "formazioni.csv")

    P["b_arbitro"] = P.arbitro.notna()
    P["b_allenatori"] = P.allenatore_casa.notna() & P.allenatore_ospite.notna()

    # ⚠️ «ha le formazioni» non basta: servono DUE squadre con 11 titolari.
    # Una sola non e' meta' del dato, e' un dato inutilizzabile per un
    # confronto fra le due squadre.
    tit = (F[F.ruolo_partita == "titolare"]
           .groupby(["game_id", "club_id"]).size().rename("n").reset_index())
    undici = (tit[tit.n == 11].groupby("game_id").size().rename("squadre_con_11"))
    P = P.merge(undici, on="game_id", how="left")
    P["squadre_con_11"] = P["squadre_con_11"].fillna(0).astype(int)
    P["b_undici_titolari"] = P.squadre_con_11 == 2

    # ⚠️ I MINUTI: qui avevo sbagliato, ed e' lo stesso errore che due righe piu'
    # su avevo evitato apposta. La prima versione contava «almeno una riga con i
    # minuti» — e con quella soglia 348 partite su 379 risultavano coperte.
    # Misurato davvero: `minuti` e' pieno su **5.438 righe di formazione su
    # 18.566 (29,3%)**, e **nessuna partita** ce l'ha su tutte le righe. Non e'
    # un difetto nostro: `appearances.csv` di player-scores porta 5.438 righe su
    # queste partite (mediana **16** per partita invece di ~35) e il merge del
    # builder non ne perde nemmeno una. E' un buco della FONTE.
    # Il criterio onesto e' il piu' stretto che abbia senso — tutti i titolari —
    # e da' **70 partite su 458**.
    tot_tit = tit.groupby("game_id")["n"].sum().rename("titolari_totali")
    con_min = (F[(F.ruolo_partita == "titolare") & F.minuti.notna()]
               .groupby("game_id").size().rename("titolari_con_minuti"))
    P = P.merge(tot_tit, on="game_id", how="left").merge(
        con_min, on="game_id", how="left")
    P["titolari_totali"] = P["titolari_totali"].fillna(0).astype(int)
    P["titolari_con_minuti"] = P["titolari_con_minuti"].fillna(0).astype(int)
    P["b_minuti_giocati"] = ((P.titolari_totali > 0)
                             & (P.titolari_con_minuti == P.titolari_totali))

    # Dichiarato, non omesso: per il 2025-26 il meteo non esiste in nessuna
    # tabella del progetto. L'infrastruttura c'e' (coordinate degli stadi,
    # raccolta giornaliera) ma e' PROSPETTICA, per il 2026-27.
    P["b_meteo"] = False
    return P


def _sponda_manuale() -> pd.DataFrame:
    """Una riga per partita RACCOLTA A MANO, coi blocchi di diretta.it.

    La chiave e' `ID partita`, quella della fonte manuale: e' l'unico modo di
    misurare la Coupe de France, che sull'altra chiave non esiste.
    """
    ev = pd.read_csv(COPPE / "aggancio_eventi.csv")
    st = pd.read_csv(COPPE / "aggancio_statistiche.csv")
    sq_f = COPPE / "aggancio_statistiche_squadra.csv"
    sq = pd.read_csv(sq_f) if sq_f.exists() else pd.DataFrame()

    def conta(d, nome, filtro=None):
        if d.empty:
            return pd.DataFrame(columns=["ID partita", "competizione", nome])
        x = d if filtro is None else d[filtro(d)]
        return (x.groupby(["ID partita", "competizione"]).size()
                .rename(nome).reset_index())

    pezzi = [
        conta(ev, "n_sostituzioni",
              lambda d: d["Tipo evento"].astype(str)
              .str.contains("ostituzione", case=False, na=False)),
        conta(st, "n_statistiche_individuali"),
        conta(sq, "n_statistiche_squadra"),
    ]
    M = None
    for pz in pezzi:
        M = pz if M is None else M.merge(pz, on=["ID partita", "competizione"],
                                         how="outer")
    for c in ("n_sostituzioni", "n_statistiche_individuali",
              "n_statistiche_squadra"):
        M[c] = M[c].fillna(0).astype(int)

    # tutte le partite raccolte, comprese quelle senza nessuna delle tre cose
    tutte = pd.read_csv(COPPE / "aggancio_partite.csv")[
        ["id_diretta", "competizione", "game_id"]].rename(
        columns={"id_diretta": "ID partita"})
    M = tutte.merge(M, on=["ID partita", "competizione"], how="left")
    for c in ("n_sostituzioni", "n_statistiche_individuali",
              "n_statistiche_squadra"):
        M[c] = M[c].fillna(0).astype(int)

    M["b_sostituzioni"] = M.n_sostituzioni > 0
    M["b_statistiche_individuali"] = M.n_statistiche_individuali > 0
    M["b_statistiche_squadra"] = M.n_statistiche_squadra > 0
    M["ha_ponte"] = M.game_id.notna()
    return M


def incrocia_partita(game_id: int) -> dict:
    """Tutti i blocchi di UNA partita, uniti davvero.

    ⚠️ Non e' una demo: contare le presenze e **fare** il join sono due
    verifiche diverse, e la seconda e' quella che l'utente ha chiesto. Una
    colonna puo' esserci in tutte e due le tabelle e non unirsi lo stesso —
    tipo sbagliato della chiave, `Int64` contro `float`, un id che e' una
    stringa da una parte e un numero dall'altra. Qui si vede subito.
    """
    P = pd.read_csv(COPPE / "partite.csv")
    riga = P[P.game_id == game_id]
    if riga.empty:
        raise ValueError(f"game_id {game_id} non e' una partita di coppa")
    r = riga.iloc[0]

    F = pd.read_csv(COPPE / "formazioni.csv")
    f = F[F.game_id == game_id]
    ev = pd.read_csv(COPPE / "aggancio_eventi.csv")
    ev = ev[ev.game_id == game_id]
    st = pd.read_csv(COPPE / "aggancio_statistiche.csv")
    st = st[st.game_id == game_id]
    sq_f = COPPE / "aggancio_statistiche_squadra.csv"
    sq = pd.read_csv(sq_f)
    sq = sq[sq.game_id == game_id]

    # il giro completo: dal giocatore della formazione (fonte automatica) alla
    # sua riga di statistica (fonte manuale), passando per `player_id`. E' il
    # ponte che la Fase 139-bis ha costruito, e qui si verifica che regga.
    tit = f[f.ruolo_partita == "titolare"]
    con_stat = tit.merge(st[["player_id", "Rating"]].dropna(subset=["player_id"]),
                         on="player_id", how="left")
    return {
        "partita": f"{r.casa}-{r.ospite} ({r.competizione}, {r.data})",
        "punteggio": f"{r.gol_casa_finale:.0f}-{r.gol_ospite_finale:.0f}",
        "arbitro": r.arbitro,
        "allenatori": f"{r.allenatore_casa} / {r.allenatore_ospite}",
        "stadio": r.stadio,
        "spettatori": r.spettatori,
        "moduli": f"{r.modulo_casa} / {r.modulo_ospite}",
        "titolari": len(tit),
        "titolari_con_player_id": int(tit.player_id.notna().sum()),
        "titolari_con_statistica_individuale": int(con_stat.Rating.notna().sum()),
        "sostituzioni": int(ev["Tipo evento"].astype(str)
                            .str.contains("ostituzione", case=False, na=False).sum()),
        "righe_statistica_individuale": len(st),
        "righe_statistica_squadra": len(sq),
        "periodi_statistica_squadra": sorted(set(sq.Periodo)) if len(sq) else [],
        "meteo": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", action="store_true",
                    help="scrive anche la matrice per partita")
    ap.add_argument("--partita", type=int, default=None,
                    help="game_id: fa il join COMPLETO su quella partita e lo stampa")
    args = ap.parse_args()

    if args.partita is not None:
        for k, v in incrocia_partita(args.partita).items():
            _log(f"  {k:38s} {v}")
        return 0

    P = _sponda_automatica()
    M = _sponda_manuale()
    dentro = P[P.dentro_perimetro].copy()

    # --- 1. la sponda automatica ------------------------------------------ #
    col_a = ["b_arbitro", "b_allenatori", "b_undici_titolari", "b_minuti_giocati"]
    # ⚠️ `b_minuti_giocati` NON entra nella congiunzione dell'incrocio: i minuti
    # non erano fra i blocchi chiesti, e includerli farebbe crollare il numero
    # per un buco della fonte invece che per un difetto degli agganci. Restano
    # riportati a parte, con la loro copertura vera.
    col_incrocio = ["b_arbitro", "b_allenatori", "b_undici_titolari"]
    ta = dentro.groupby("competizione")[col_a].sum()
    ta.insert(0, "nel_perimetro", dentro.groupby("competizione").size())
    _log("\n=== 1. FONTE AUTOMATICA (player-scores) — chiave `game_id` ===")
    _log("    denominatore: le partite NEL PERIMETRO\n")
    _log(ta.to_string())

    # --- 2. la sponda manuale --------------------------------------------- #
    col_m = ["b_sostituzioni", "b_statistiche_individuali", "b_statistiche_squadra"]
    tm = M.groupby("competizione")[col_m].sum()
    tm.insert(0, "raccolte", M.groupby("competizione").size())
    tm["con_ponte_al_game_id"] = M.groupby("competizione")["ha_ponte"].sum()
    _log("\n=== 2. RACCOLTA MANUALE (diretta.it) — chiave `ID partita` ===")
    _log("    denominatore: le partite EFFETTIVAMENTE RACCOLTE a mano\n")
    _log(tm.to_string())

    # --- 3. l'incrocio vero ------------------------------------------------ #
    # Una partita e' «incrociabile» se ha il ponte E tutti i blocchi delle due
    # sponde. E' questa la risposta alla domanda, non le due tabelle sopra.
    X = dentro.merge(
        M[M.ha_ponte][["game_id"] + col_m], on="game_id", how="left")
    for c in col_m:
        X[c] = X[c].fillna(False)
    tutti = col_incrocio + col_m
    X["incrociabile"] = X[tutti].all(axis=1)
    tx = X.groupby("competizione")[["incrociabile"]].sum()
    tx.insert(0, "nel_perimetro", X.groupby("competizione").size())
    tx["quota"] = (100 * tx.incrociabile / tx.nel_perimetro).round(1)
    _log("\n=== 3. L'INCROCIO: partite con TUTTI i blocchi, uniti dal `game_id` ===")
    _log("    (meteo escluso: non esiste per il 2025-26)\n")
    _log(tx.to_string())
    _log(f"\n  TOTALE: {int(tx.incrociabile.sum())}/{len(X)} partite del "
         f"perimetro ({100*tx.incrociabile.sum()/len(X):.1f}%)")

    # perche' le altre non lo sono: il motivo, non solo il conteggio
    _log("\n  Perche' le altre NON si incrociano (un blocco per riga):")
    manca = X[~X.incrociabile]
    for c in tutti:
        n = int((~manca[c].astype(bool)).sum())
        if n:
            _log(f"    manca {c:28s} {n:4d} partite")

    # --- 4. il join PIU' PROFONDO ----------------------------------------- #
    # Non «la partita ha i due blocchi» ma «QUESTO titolare arriva alla SUA
    # riga di statistica». E' il giro completo fra due fonti indipendenti
    # (player-scores -> `player_id` -> diretta.it) e l'unico che serve davvero
    # a un modello per giocatore. Le tabelle 1-3 possono essere verdi e questa
    # rossa: la partita c'e' da entrambe le parti, le PERSONE no.
    F = pd.read_csv(COPPE / "formazioni.csv")
    stat = pd.read_csv(COPPE / "aggancio_statistiche.csv")
    tit = F[(F.ruolo_partita == "titolare") & F.game_id.notna()][
        ["game_id", "player_id"]].copy()
    sp = (stat.dropna(subset=["game_id", "player_id"])[["game_id", "player_id"]]
          .drop_duplicates().assign(ok=True))
    giro = (tit.merge(sp, on=["game_id", "player_id"], how="left")
            .merge(P[["game_id", "competizione"]], on="game_id", how="left"))
    giro = giro[giro.game_id.isin(set(sp.game_id))]
    giro["ok"] = giro["ok"].fillna(False)
    tg = giro.groupby("competizione")["ok"].agg(["size", "sum"])
    tg["quota"] = (100 * tg["sum"] / tg["size"]).round(1)
    _log("\n=== 4. IL GIRO COMPLETO: titolare -> la SUA statistica individuale ===")
    _log("    (join per `player_id` fra due fonti indipendenti, sulle partite "
         "che hanno entrambi i blocchi)\n")
    _log(tg.to_string())
    _log(f"\n  TOTALE: {int(tg['sum'].sum())}/{int(tg['size'].sum())} titolari "
         f"({100*tg['sum'].sum()/tg['size'].sum():.1f}%)")

    quadro = {
        "partite_totali": len(P),
        "giro_completo_titolari": json.loads(tg.to_json(orient="index")),
        "nel_perimetro": len(dentro),
        "sponda_automatica": json.loads(ta.to_json(orient="index")),
        "sponda_manuale": json.loads(tm.to_json(orient="index")),
        "incrocio": json.loads(tx.to_json(orient="index")),
        "incrociabili": int(tx.incrociabile.sum()),
        "meteo": "assente per il 2025-26 (l'infrastruttura e' prospettica)",
    }
    (COPPE / "incrocio_manifesto.json").write_text(
        json.dumps(quadro, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"\n  scritto {COPPE / 'incrocio_manifesto.json'}")

    if args.csv:
        cols = (["competizione", "turno", "data", "casa", "ospite", "game_id"]
                + tutti + ["incrociabile"])
        X[cols].to_csv(COPPE / "incrocio_per_partita.csv", index=False)
        _log(f"  scritto {COPPE / 'incrocio_per_partita.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
