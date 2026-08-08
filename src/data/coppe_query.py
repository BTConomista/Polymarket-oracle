"""Le coppe come PANNELLO interrogabile: allenatore × arbitro × squadra × giocatore.

PERCHE' ESISTE. La Fase 139-octies aveva risposto alla domanda «i blocchi si
uniscono?» — sì, 296 partite su 580, e il giro fino al singolo titolare regge al
98,3%. Ma l'utente ne intendeva una piu' esigente:

    «se io chiedo le statistiche che hanno avuto le squadre di un determinato
     allenatore in quella competizione siamo in grado di rispondere, o le
     statistiche di un giocatore quando ad arbitrare la partita era un certo
     arbitro»

Sono domande che **attraversano** i blocchi: partono da una dimensione
(allenatore, arbitro) che vive nella fonte automatica e chiedono una misura che
vive nella raccolta manuale. Perche' si possa rispondere non basta che le
tabelle si uniscano: la dimensione dev'essere **attaccata a ogni riga di
misura**, dal lato giusto.

⚠️ IL LATO E' LA PARTE DIFFICILE, ed e' silenziosa se sbagliata. `partite.csv`
ha `allenatore_casa` e `allenatore_ospite`; una riga di statistica ha `Lato`
(Casa/Ospite). Attaccare l'allenatore senza guardare il lato produce numeri
plausibili e sbagliati — meta' delle righe avrebbero l'allenatore avversario, e
nessun controllo se ne accorgerebbe. Qui il lato e' la chiave, non un dettaglio.

⚠️ IL NOME NON E' UN'IDENTITA' (Fase 140). Vale per gli allenatori — e
`conflitti_identita()` ne ha dimostrati 11 col test «nessuno allena due club lo
stesso giorno» — e a maggior ragione per gli arbitri, di cui non abbiamo
nemmeno un id. Le chiavi normalizzate qui servono a UNIRE le grafie della stessa
persona, non a garantire che due persone diverse restino separate.

USO:
    from src.data import coppe_query as Q
    Q.statistiche_allenatore("Antonio Conte")             # squadre di Conte
    Q.statistiche_allenatore("Conte", competizione="Coppa Italia")
    Q.statistiche_giocatore(arbitro="Daniele Doveri")     # chi ha arbitrato lui
    Q.pannello_squadra()                                  # la tabella grezza
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .allenatori import normalizza_nome

RADICE = Path(__file__).resolve().parents[2]
COPPE = RADICE / "data" / "coppe_2526"

# Le colonne di `partite.csv` che descrivono la PARTITA e non una delle due
# squadre: si portano identiche su entrambe le righe.
_CONTESTO = ["competizione", "paese", "turno", "data", "arbitro", "stadio",
             "spettatori", "supplementari", "dentro_perimetro"]


def _partite_per_lato() -> pd.DataFrame:
    """Una riga per (partita, lato), con l'allenatore GIUSTO su ogni riga.

    E' il pezzo che rende rispondibile la domanda dell'utente: da qui in poi
    ogni misura si attacca per (`game_id`, `Lato`) e l'allenatore che si porta
    dietro e' quello della sua squadra, non dell'altra.
    """
    P = pd.read_csv(COPPE / "partite.csv")
    P = P[P.game_id.notna()].copy()

    def lato(nome: str, mio: str, suo: str, gf: str, gs: str,
             div: str, mod: str) -> pd.DataFrame:
        d = P[_CONTESTO + ["game_id"]].copy()
        d["Lato"] = nome
        d["squadra"] = P[mio].to_numpy()
        d["avversario"] = P[suo].to_numpy()
        d["allenatore"] = P[f"allenatore_{'casa' if nome == 'Casa' else 'ospite'}"].to_numpy()
        d["allenatore_avv"] = P[f"allenatore_{'ospite' if nome == 'Casa' else 'casa'}"].to_numpy()
        d["club_id"] = P[f"{'home' if nome == 'Casa' else 'away'}_club_id"].to_numpy()
        d["gol_fatti"] = P[gf].to_numpy()
        d["gol_subiti"] = P[gs].to_numpy()
        d["divisione"] = P[div].to_numpy()
        d["modulo"] = P[mod].to_numpy()
        return d

    L = pd.concat([
        lato("Casa", "casa", "ospite", "gol_casa_finale", "gol_ospite_finale",
             "divisione_casa", "modulo_casa"),
        lato("Ospite", "ospite", "casa", "gol_ospite_finale", "gol_casa_finale",
             "divisione_ospite", "modulo_ospite"),
    ], ignore_index=True)

    L["allenatore_chiave"] = L.allenatore.map(normalizza_nome)
    L["arbitro_chiave"] = L.arbitro.map(normalizza_nome)
    L["esito"] = pd.Series(
        ["V" if a > b else ("P" if a < b else "N")
         for a, b in zip(L.gol_fatti, L.gol_subiti)], index=L.index)
    return L


def _senza_doppioni(misure: pd.DataFrame, dimensioni: pd.DataFrame) -> pd.DataFrame:
    """Toglie dalle misure le colonne che le dimensioni gia' portano.

    ⚠️ Non e' cosmesi. Le tabelle di aggancio ripetono il contesto (data,
    squadre, competizione) con nomi che a volte differiscono solo per la
    maiuscola — `Competizione` dal foglio consegnato, `competizione` aggiunta
    da `aggancia_coppe`. Lasciandole, il merge le rinomina in `_x`/`_y` e ogni
    query per competizione fallisce con un `KeyError`, o peggio filtra sulla
    copia sbagliata. Le dimensioni sono la fonte, le misure no.
    """
    tieni = ["game_id", "Lato"]
    doppie = {c for c in misure.columns if c not in tieni
              and (c in dimensioni.columns or c.lower() in
                   {x.lower() for x in dimensioni.columns})}
    # il contesto ripetuto dal foglio consegnato: non serve, e confonde
    doppie |= {c for c in ("Casa", "Ospite", "Squadra", "ID partita")
               if c in misure.columns}
    return misure.drop(columns=sorted(doppie))


def pannello_squadra(periodo: str | None = "Totale") -> pd.DataFrame:
    """Una riga per (partita, squadra, periodo): dimensioni + 35 metriche.

    `periodo=None` tiene tutti i periodi (Totale / 1° tempo / 2° tempo /
    Supplementari); il default e' `Totale`, perche' e' quello che si intende
    quando si chiede «le statistiche di quella partita».

    ⚠️ `Totale` e' la partita INTERA, supplementari compresi (misurato alla
    Fase 139-septies: `1T + 2T + Suppl = Totale` su 2.228/2.228 celle). Chi
    vuole i 90 minuti deve sommare 1° e 2° tempo, non usare `Totale`.
    """
    sq = pd.read_csv(COPPE / "aggancio_statistiche_squadra.csv")
    sq = sq[sq.game_id.notna()].copy()
    if periodo is not None:
        sq = sq[sq.Periodo == periodo]
    L = _partite_per_lato()
    return L.merge(_senza_doppioni(sq, L), on=["game_id", "Lato"], how="inner")


def pannello_giocatore() -> pd.DataFrame:
    """Una riga per (partita, giocatore): dimensioni + le metriche individuali.

    I minuti giocati vengono dalla fonte AUTOMATICA (`formazioni.csv`), le
    metriche dalla manuale: e' il giro completo, ed e' il motivo per cui questa
    tabella esiste invece di leggere un file solo.
    """
    st = pd.read_csv(COPPE / "aggancio_statistiche.csv")
    st = st[st.game_id.notna()].copy()
    L = _partite_per_lato()
    G = L.merge(_senza_doppioni(st, L), on=["game_id", "Lato"], how="inner")

    F = pd.read_csv(COPPE / "formazioni.csv")
    F = F[F.game_id.notna() & F.player_id.notna()][
        ["game_id", "player_id", "minuti", "ruolo_partita", "numero"]]
    return G.merge(F, on=["game_id", "player_id"], how="left")


# --------------------------------------------------------------------------- #
# le due domande dell'utente
# --------------------------------------------------------------------------- #
def _filtra_nome(d: pd.DataFrame, colonna: str, nome: str) -> pd.DataFrame:
    """Cerca per chiave normalizzata; se non basta, per sottostringa.

    Il secondo passo serve perche' le fonti scrivono «Antonio Conte» e a volte
    solo «Conte»: chi interroga non deve conoscere la grafia esatta. Non e' un
    aggancio di identita' — e' una ricerca.
    """
    k = normalizza_nome(nome)
    esatto = d[d[f"{colonna}_chiave"] == k]
    if len(esatto):
        return esatto
    return d[d[f"{colonna}_chiave"].str.contains(k, regex=False, na=False)]


def statistiche_allenatore(nome: str, competizione: str | None = None,
                           periodo: str = "Totale",
                           metriche: list[str] | None = None) -> pd.DataFrame:
    """«Le statistiche che hanno avuto le squadre di questo allenatore.»

    Una riga per partita, con la squadra allenata da lui — mai quella di
    fronte. Se `competizione` e' dato, si restringe a quella coppa.
    """
    d = pannello_squadra(periodo=periodo)
    if competizione:
        d = d[d.competizione == competizione]
    d = _filtra_nome(d, "allenatore", nome)
    base = ["competizione", "turno", "data", "squadra", "avversario", "Lato",
            "arbitro", "gol_fatti", "gol_subiti", "esito"]
    if metriche is None:
        metriche = ["Goal previsti (xG)", "Tiri totali", "Tiri in porta",
                    "Possesso palla", "Calci d'angolo", "Falli",
                    "Cartellini gialli"]
    metriche = [m for m in metriche if m in d.columns]
    return d[base + metriche].sort_values("data").reset_index(drop=True)


def statistiche_giocatore(giocatore: str | None = None,
                          player_id: int | None = None,
                          arbitro: str | None = None,
                          competizione: str | None = None,
                          metriche: list[str] | None = None) -> pd.DataFrame:
    """«Le statistiche di un giocatore quando arbitrava un certo arbitro.»

    Ogni filtro e' opzionale e si compone con gli altri: solo il giocatore, solo
    l'arbitro (tutti i giocatori delle sue partite), o i due insieme.
    """
    d = pannello_giocatore()
    if competizione:
        d = d[d.competizione == competizione]
    if player_id is not None:
        d = d[d.player_id == player_id]
    elif giocatore:
        k = normalizza_nome(giocatore)
        d = d[d.Giocatore.map(normalizza_nome).str.contains(k, regex=False,
                                                            na=False)]
    if arbitro:
        d = _filtra_nome(d, "arbitro", arbitro)
    base = ["competizione", "turno", "data", "Giocatore", "squadra",
            "avversario", "allenatore", "arbitro", "Stato", "minuti", "Rating"]
    if metriche is None:
        metriche = ["EXPECTED_GOALS", "SHOTS_TOTAL", "PASSES_TOTAL",
                    "DUELS_WON", "FOULS_COMMITTED", "CARDS_YELLOW"]
    base = [c for c in base if c in d.columns]
    metriche = [m for m in metriche if m in d.columns]
    return d[base + metriche].sort_values("data").reset_index(drop=True)


def copertura() -> dict:
    """Quante partite/righe reggono davvero le due domande, e con che potenza.

    ⚠️ La risposta «sì, si può» non basta: in una coppa un allenatore ha 1-3
    partite, e una media su 2 partite non e' una statistica. Questo e' il
    numero che va guardato PRIMA di credere a una media.
    """
    S, G = pannello_squadra(), pannello_giocatore()
    per_all = S.groupby("allenatore_chiave").size()
    per_arb = S.groupby("arbitro_chiave").size() / 2      # 2 righe per partita
    per_gio = G.groupby("player_id").size()
    return {
        "righe_squadra": len(S),
        "righe_giocatore": len(G),
        "allenatori_distinti": int(per_all.size),
        "partite_per_allenatore_mediana": float(per_all.median()),
        "allenatori_con_almeno_3_partite": int((per_all >= 3).sum()),
        "arbitri_distinti": int(per_arb.size),
        "partite_per_arbitro_mediana": float(per_arb.median()),
        "arbitri_con_almeno_5_partite": int((per_arb >= 5).sum()),
        "giocatori_distinti": int(per_gio.size),
        "giocatori_con_almeno_3_partite": int((per_gio >= 3).sum()),
    }
