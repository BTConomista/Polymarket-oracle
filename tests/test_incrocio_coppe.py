"""L'incrocio dei dati di coppa: i blocchi si uniscono davvero? (Fase 139-octies)

Questi test non proteggono un numero: proteggono la **distinzione** fra tre
cose che un conteggio ingenuo confonde, e che ogni volta fanno sembrare
mancante qualcosa che c'e' (o presente qualcosa che non si unisce):

  fuori perimetro   mai chiesto        != buco
  senza ponte       leggibile da solo  != assente
  presente          !=                 unibile
"""

from __future__ import annotations

import pandas as pd
import pytest

from scripts.verifica_incrocio_coppe import (
    COPPE,
    _sponda_automatica,
    _sponda_manuale,
    incrocia_partita,
)

pytestmark = pytest.mark.skipif(
    not (COPPE / "partite.csv").exists(),
    reason="le coppe 2025-26 non sono presenti")


@pytest.fixture(scope="module")
def sponde():
    return _sponda_automatica(), _sponda_manuale()


def test_il_perimetro_non_va_al_denominatore(sponde):
    """Le 82 partite fuori perimetro non sono un buco: non sono mai state
    chieste. Contarle fra le mancanti e' il modo piu' facile di trasformare
    una decisione dell'utente in un difetto immaginario."""
    P, _ = sponde
    assert len(P) == 662
    assert int(P.dentro_perimetro.sum()) == 580


def test_la_coupe_de_france_non_e_vuota_solo_perche_non_ha_il_game_id(sponde):
    """Il test che tiene onesta la tabella.

    Sulla chiave automatica la Coupe de France e' 0 su tutto — e uno scrive
    «non abbiamo niente». Sulla SUA chiave ha 201 partite raccolte, 63 con le
    sostituzioni, 87 con le statistiche di squadra. Non e' assenza: e' assenza
    di **ponte**, che e' un'altra cosa e si ripara in un altro modo.
    """
    _, M = sponde
    fr = M[M.competizione == "Coupe de France"]
    assert len(fr) == 201
    assert int(fr.ha_ponte.sum()) == 0, "se un giorno diventa > 0, e' una notizia"
    assert int(fr.b_sostituzioni.sum()) > 0
    assert int(fr.b_statistiche_squadra.sum()) > 0


def test_quattro_coppe_si_incrociano_quasi_per_intero(sponde):
    """Coppa Italia, Pokal, EFL e FA Cup: arbitro + allenatori + undici +
    minuti + sostituzioni + statistiche, tutto sullo stesso `game_id`."""
    P, M = sponde
    dentro = P[P.dentro_perimetro]
    col_m = ["b_sostituzioni", "b_statistiche_individuali", "b_statistiche_squadra"]
    X = dentro.merge(M[M.ha_ponte][["game_id"] + col_m], on="game_id", how="left")
    for c in col_m:
        X[c] = X[c].fillna(False)
    # ⚠️ `b_minuti_giocati` e' fuori dalla congiunzione: i minuti non erano fra
    # i blocchi chiesti, e sono pieni su 5.438 righe di formazione su 18.566
    # per un buco di `appearances.csv` — nessuna partita li ha su tutte le
    # righe. Includerli misurerebbe la fonte, non i nostri agganci.
    tutti = ["b_arbitro", "b_allenatori", "b_undici_titolari"] + col_m
    X["ok"] = X[tutti].all(axis=1)
    quota = X[X.competizione.isin(
        ["Coppa Italia", "DFB-Pokal", "EFL Cup", "FA Cup"])].groupby(
        "competizione")["ok"].mean()
    assert (quota > 0.85).all(), quota.to_dict()


def test_il_giro_completo_arriva_al_singolo_titolare():
    """Il join che conta: dal titolare (player-scores) alla sua riga di
    statistica (diretta.it), per `player_id`.

    Le tabelle di copertura possono essere verdi e questo rosso — la partita
    c'e' da entrambe le parti, le PERSONE no. Misurato 98,3%; la soglia e'
    tenuta bassa apposta, il test difende il meccanismo, non il decimale.
    """
    F = pd.read_csv(COPPE / "formazioni.csv")
    st = pd.read_csv(COPPE / "aggancio_statistiche.csv")
    tit = F[(F.ruolo_partita == "titolare") & F.game_id.notna()][
        ["game_id", "player_id"]]
    sp = (st.dropna(subset=["game_id", "player_id"])[["game_id", "player_id"]]
          .drop_duplicates().assign(ok=True))
    giro = tit.merge(sp, on=["game_id", "player_id"], how="left")
    giro = giro[giro.game_id.isin(set(sp.game_id))]
    assert len(giro) > 6000
    assert giro.ok.fillna(False).mean() > 0.95


def test_una_partita_si_monta_per_intero():
    """Empoli-Reggiana, Coppa Italia 15/08/2025: il giro end-to-end su un caso
    vero. Contare le presenze e FARE il join sono due verifiche diverse."""
    r = incrocia_partita(4631307)
    assert r["arbitro"] == "Andrea Calzavara"
    assert r["titolari"] == 22
    assert r["titolari_con_player_id"] == 22
    assert r["titolari_con_statistica_individuale"] == 22
    assert r["sostituzioni"] > 0
    assert r["periodi_statistica_squadra"] == ["1° tempo", "2° tempo", "Totale"]
    assert r["meteo"] is None, "il meteo del 2025-26 non esiste: non fingerlo"


def test_il_meteo_e_dichiarato_assente(sponde):
    """R6 al contrario: un blocco che non c'è deve risultare vuoto, non zero
    né dimenticato. Il giorno che il meteo entrerà, questo test cadrà — ed è
    esattamente il momento in cui va riscritto."""
    P, _ = sponde
    assert not P.b_meteo.any()


def test_i_minuti_sono_un_buco_della_FONTE_e_va_detto(sponde):
    """⚠️ Il criterio «almeno una riga coi minuti» era mio, ed era troppo largo.

    Con quello 348 partite su 379 risultavano coperte. Misurato: `minuti` e'
    pieno su **5.438 righe su 18.566** e **nessuna partita** ce l'ha su tutte —
    perche' `appearances.csv` di player-scores porta 5.438 righe su queste
    partite (mediana 16 invece di ~35). Il builder non ne perde nemmeno una: e'
    la fonte a non averle. Con il criterio stretto (tutti i titolari) sono 70.
    """
    P, _ = sponde
    F = pd.read_csv(COPPE / "formazioni.csv")
    assert F.minuti.notna().sum() == 5438
    quota = (F[F.game_id.notna()].assign(ha=F.minuti.notna())
             .groupby("game_id")["ha"].mean())
    assert (quota < 1).all(), "nessuna partita ha i minuti su TUTTE le righe"
    assert int(P.b_minuti_giocati.sum()) == 70
