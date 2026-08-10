"""Il pannello interrogabile delle coppe (Fase 139-novies).

Questi test difendono UNA cosa sopra tutte: che la dimensione attaccata a una
riga di misura sia quella del **lato giusto**. E' l'errore che non da' segnale —
con l'allenatore avversario su meta' delle righe i numeri restano plausibili,
le medie restano credibili, e nessun conteggio se ne accorge.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import allenatori as A
from src.data import coppe_query as Q

pytestmark = pytest.mark.skipif(
    not (Q.COPPE / "aggancio_statistiche_squadra.csv").exists(),
    reason="le statistiche di coppa non sono presenti")


@pytest.fixture(scope="module")
def squadra():
    return Q.pannello_squadra()


@pytest.fixture(scope="module")
def giocatore():
    return Q.pannello_giocatore()


def test_il_lato_regge_contro_una_fonte_indipendente(squadra):
    """⭐ Il test che conta.

    L'allenatore attaccato a ogni riga viene da `partite.csv` scegliendo la
    colonna in base al `Lato`. Qui si verifica contro un percorso **diverso** —
    `allenatori.load_partite()`, che legge `games.csv` e produce la vista lunga
    per conto suo. Due strade, stesso risultato: 746/746.
    """
    L = (A.load_partite()[["game_id", "club_id", "allenatore"]]
         .rename(columns={"allenatore": "atteso"}))
    m = squadra[["game_id", "club_id", "allenatore"]].merge(
        L, on=["game_id", "club_id"], how="left")
    assert m.atteso.notna().all(), "righe senza riscontro nella fonte indipendente"
    uguali = (m.allenatore.map(A.normalizza_nome)
              == m.atteso.map(A.normalizza_nome))
    assert uguali.all(), m[~uguali].head().to_dict("records")


def test_i_due_allenatori_non_coincidono_mai(squadra):
    """La controprova del test precedente: se il lato fosse ignorato, `allenatore`
    e `allenatore_avv` sarebbero spesso uguali. Sono diversi su tutte le righe,
    quindi un errore di lato sarebbe stato visibile."""
    stesso = (squadra.allenatore.map(A.normalizza_nome)
              == squadra.allenatore_avv.map(A.normalizza_nome))
    assert not stesso.any()


def test_una_partita_da_esattamente_due_righe_squadra(squadra):
    """Ogni partita ha due squadre: se una riga si duplicasse nel merge, le
    medie per allenatore sarebbero pesate a caso."""
    per_partita = squadra.groupby("game_id").size()
    assert set(per_partita.unique()) == {2}, per_partita.value_counts().to_dict()


def test_il_pannello_non_ha_colonne_sdoppiate(squadra, giocatore):
    """Le tabelle di aggancio ripetono il contesto, a volte con la sola
    maiuscola diversa (`Competizione` / `competizione`). Se scivola nel merge,
    pandas rinomina in `_x`/`_y` e ogni filtro per competizione o fallisce o —
    peggio — filtra la copia sbagliata."""
    for d in (squadra, giocatore):
        assert not [c for c in d.columns if c.endswith(("_x", "_y"))]
        assert "competizione" in d.columns


def test_le_statistiche_di_un_allenatore_sono_solo_le_sue(squadra):
    d = Q.statistiche_allenatore("Diego Simeone", competizione="Copa del Rey")
    assert len(d) > 0
    assert set(d.squadra) == {"Atlético de Madrid"}
    assert set(d.competizione) == {"Copa del Rey"}


def test_un_giocatore_si_interroga_per_arbitro(giocatore):
    """La domanda dell'utente nella sua forma esatta: le righe di UN giocatore
    quando arbitrava UNA certa persona."""
    riga = giocatore.dropna(subset=["player_id"]).iloc[0]
    d = Q.statistiche_giocatore(player_id=int(riga.player_id),
                                arbitro=riga.arbitro)
    assert len(d) >= 1
    assert set(d.arbitro) == {riga.arbitro}


def test_i_minuti_arrivano_dalla_fonte_automatica(giocatore):
    """Il pannello e' un giro fra DUE fonti: le metriche da diretta.it, i minuti
    da player-scores. Se il secondo join saltasse, la colonna resterebbe tutta
    vuota e nessuna metrica se ne accorgerebbe.

    ⚠️ La soglia e' **0,4 e non 0,8**, e la differenza e' una scoperta di questo
    test: i minuti coprono il **51,7%** delle righe del pannello perche'
    `appearances.csv` e' parziale sulle coppe (5.438 righe su 18.566 di
    formazione). Non e' il join a perdere: ogni riga di statistica trova il suo
    giocatore in `formazioni.csv` — 9.312 su 9.312. E' la fonte a non avere il
    minutaggio, e il pannello lo eredita.
    """
    assert giocatore.minuti.notna().mean() > 0.4
    # il join NON perde nessuno: e' il valore a mancare, non la riga
    F = pd.read_csv(Q.COPPE / "formazioni.csv")
    chiavi = set(zip(F.game_id, F.player_id))
    g = giocatore.dropna(subset=["player_id"])
    trovati = sum((gi, pi) in chiavi for gi, pi in zip(g.game_id, g.player_id))
    assert trovati == len(g)


def test_la_copertura_dichiara_anche_la_numerosita():
    """⚠️ «Si puo' rispondere» non e' «la risposta e' una statistica».

    In una stagione di coppa la mediana e' 2 partite per allenatore e 1 per
    arbitro: una media su due partite non e' una media. `copertura()` deve
    dirlo, altrimenti il pannello invita a un errore.
    """
    c = Q.copertura()
    assert c["righe_squadra"] > 0 and c["righe_giocatore"] > 0
    assert "partite_per_allenatore_mediana" in c
    assert "arbitri_con_almeno_5_partite" in c
    assert c["partite_per_allenatore_mediana"] < 5, \
        "se un giorno sale, e' perche' sono entrate altre stagioni: aggiorna il commento"


# --------------------------------------------------------------------------- #
# gli invarianti di IDENTITÀ (Fase 139-decies)
# --------------------------------------------------------------------------- #
# Sono nati da un difetto vero, trovato confrontando il club del giocatore col
# club del suo lato: tre righe di statistica portavano un giocatore dell'altra
# squadra, e una coppia di omonimi condivideva un `player_id`. Nessuno di questi
# dava errore — davano numeri.

def test_ogni_giocatore_appartiene_al_club_del_suo_lato(giocatore):
    """⭐ Il controllo che ha trovato il bug.

    La riga di statistica dice `Lato`; `formazioni.csv` dice a che club
    appartiene quel `player_id`. Devono coincidere. Prima della correzione i
    candidati si cercavano nella PARTITA e non nella SQUADRA, e in
    Navalcarnero-Getafe c'erano due «Juanmi»: lo stesso `player_id` finiva su
    entrambe le squadre.
    """
    F = (pd.read_csv(Q.COPPE / "formazioni.csv")[["game_id", "player_id", "club_id"]]
         .rename(columns={"club_id": "club_form"}))
    j = (giocatore[["game_id", "player_id", "club_id"]].dropna(subset=["player_id"])
         .merge(F, on=["game_id", "player_id"], how="left")
         .dropna(subset=["club_form"]))
    assert len(j) > 9000
    diverse = j[j.club_id.astype("Int64") != j.club_form.astype("Int64")]
    assert diverse.empty, diverse.head().to_dict("records")


def test_gli_autogol_stanno_sul_lato_di_CHI_LI_SUBISCE():
    """diretta.it registra l'autogol sul lato che ne **beneficia**, ma il
    giocatore è dell'altra squadra — la stessa convenzione già misurata sulla
    fonte automatica alla Fase 138.

    Senza questa regola i 35 autogol delle sei coppe restano senza `player_id`,
    cercati nella rosa sbagliata; con la regola invertita tutto il resto si
    romperebbe. Qui si verifica che valga per ogni riga, nei due sensi.
    """
    ev = pd.read_csv(Q.COPPE / "aggancio_eventi.csv")
    ev = ev[ev.game_id.notna() & ev.player_id.notna()]
    F = (pd.read_csv(Q.COPPE / "formazioni.csv")[["game_id", "player_id", "club_id"]]
         .rename(columns={"club_id": "club_form"}))
    L = (Q._partite_per_lato()[["game_id", "Lato", "club_id"]]
         .rename(columns={"club_id": "club_lato"}))
    j = (ev[["game_id", "Lato", "Tipo evento", "player_id"]]
         .merge(L, on=["game_id", "Lato"], how="left")
         .merge(F, on=["game_id", "player_id"], how="left")
         .dropna(subset=["club_lato", "club_form"]))
    autogol = j["Tipo evento"].astype(str).str.contains("utogol", na=False)
    suo_lato = j.club_form.astype("Int64") == j.club_lato.astype("Int64")
    assert int(autogol.sum()) > 20, "se gli autogol spariscono, il test non prova più niente"
    assert (~suo_lato[autogol]).all(), "un autogol sul lato di chi lo segna"
    assert suo_lato[~autogol].all(), "un evento normale sul lato sbagliato"


def test_un_player_id_non_serve_due_persone_nella_stessa_partita():
    """Ogni riga si risolve per conto suo, quindi due nomi diversi dello stesso
    club possono rivendicare lo stesso candidato: «Perez Andoni» e «Perez Alex»
    del Club Portugalete finivano entrambi su 634542. Dove non c'è un vincitore
    unico non vince nessuno — e la casella resta vuota."""
    st = pd.read_csv(Q.COPPE / "aggancio_statistiche.csv")
    st = st.dropna(subset=["game_id", "player_id"])
    per_id = st.groupby(["game_id", "player_id"])["Giocatore"].nunique()
    assert (per_id == 1).all(), per_id[per_id > 1].to_dict()


def test_il_pannello_non_duplica_le_righe(giocatore):
    """Un giocatore, una riga per partita. Se il merge coi minuti duplicasse,
    ogni media per giocatore sarebbe pesata a caso."""
    d = giocatore.dropna(subset=["player_id"])
    assert not d.duplicated(subset=["game_id", "player_id"]).any()
