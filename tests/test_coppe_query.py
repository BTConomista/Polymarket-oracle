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
