"""Test del raccoglitore Smarkets pre-partita (Fase 116).

Il download non e' testabile (rete), ma la parte che puo' rompersi in
silenzio si': **il riconoscimento della lega**. Raccogliere la seconda
divisione credendola la prima sarebbe dato sporco, non un errore visibile.

⚠️ Onesta' su cosa questi test proteggono davvero (verificato per mutazione,
Fase 116). La prima stesura diceva di difendere dal caso
`germany-2-bundesliga` scambiato per `germany-bundesliga` con un match
"contiene": quella collisione e' **strutturalmente impossibile** (il "2-" sta
in mezzo, quindi nemmeno `in` la produce) e la mutazione corrispondente NON
faceva fallire nulla. Cio' che i test proteggono per davvero e' il
**contratto con un'API esterna**: gli slug attesi sono fissati qui, quindi
una mappa corrotta o un rinominamento a valle rompono la suite invece di
farci raccogliere in silenzio la lega sbagliata (o niente). Verificato:
sostituendo una voce della mappa, 2 test falliscono.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_smarkets_matches import (  # noqa: E402
    MERCATI_BASE, MERCATI_PRINCIPALI, SLUG_LEGA, _slug_lega,
    anomalia_del_listino, entro_finestra)


@pytest.mark.parametrize("slug,atteso", [
    ("/sport/football/italy-serie-a/2026/08/16/19-00/inter-vs-milan", "serie_a"),
    ("/sport/football/england-premier-league/2026/08/15/14-00/a-vs-b", "premier_league"),
    ("/sport/football/spain-laliga/2026/08/15/17-30/a-vs-b", "la_liga"),
    ("/sport/football/germany-bundesliga/2026/08/22/13-30/a-vs-b", "bundesliga"),
    ("/sport/football/france-ligue-1/2026/08/16/19-00/a-vs-b", "ligue_1"),
])
def test_riconosce_le_cinque_leghe(slug, atteso):
    assert _slug_lega(slug) == atteso


@pytest.mark.parametrize("slug", [
    "/sport/football/germany-2-bundesliga/2026/08/22/13-30/a-vs-b",   # seconda serie
    "/sport/football/italy-serie-b/2026/08/22/13-30/a-vs-b",
    "/sport/football/england-championship/2026/08/22/13-30/a-vs-b",
    "/sport/football/brazil-copa-do-brasil/2026/08/02/21-30/a-vs-b",
    "/sport/football/england-efl-cup/2026/08/22/13-30/a-vs-b",        # coppa
])
def test_scarta_seconde_divisioni_coppe_e_altri_paesi(slug):
    """Cio' che entra nell'archivio dev'essere solo la prima divisione delle 5
    leghe. Non e' la collisione `germany-2-bundesliga` a rendere utile questo
    test (quella e' impossibile, vedi il docstring del modulo): e' il fatto di
    fissare per iscritto che coppe, seconde divisioni e altri paesi restano
    fuori, cosi' un allargamento involontario della mappa rompe la suite."""
    assert _slug_lega(slug) is None


def test_slug_malformato_non_esplode():
    for s in (None, "", "/sport/tennis/atp/x", "non-uno-slug"):
        assert _slug_lega(s) is None


def test_le_leghe_dichiarate_sono_le_cinque_del_progetto():
    from src.config import LEAGUE_CONFIGS
    assert set(SLUG_LEGA.values()) == set(LEAGUE_CONFIGS)


def test_i_mercati_raccolti_sono_quelli_che_il_progetto_prezza():
    """Se un giorno Smarkets rinominasse un mercato, il raccoglitore lo
    salterebbe in silenzio: questo test fissa cosa ci aspettiamo di avere."""
    assert set(MERCATI_BASE.values()) == {
        "1x2", "ggng", "ou15", "ou25", "ou35", "risultato_esatto"}


def test_i_mercati_principali_sono_un_sottoinsieme_di_quelli_raccolti():
    """Il regime di lungo raggio filtra per ETICHETTA: se una delle principali
    non fosse fra quelle raccolte, filtrerebbe via tutto e il giro giornaliero
    scriverebbe file vuoti senza errori."""
    assert MERCATI_PRINCIPALI <= set(MERCATI_BASE.values())


# --- il listino: distinguere «finestra vuota» da «API muta» (R6) -----------

def test_listino_vuoto_e_anomalia():
    assert anomalia_del_listino(0, 0) is not None


def test_listino_senza_nessuna_delle_nostre_leghe_e_anomalia():
    """Il caso realistico: Smarkets rinomina uno slug di competizione, oppure
    filtra gli IP dei runner. Senza questo controllo il workflow resterebbe
    verde raccogliendo il nulla, e i dati pre-partita non tornano piu'."""
    assert anomalia_del_listino(709, 0) is not None


def test_listino_normale_non_e_anomalia():
    """I numeri veri del 28/07/2026, off-season profonda: 709 eventi calcio,
    48 partite nostre gia' esposte. Nessuna in finestra a 72h -- ed e' proprio
    lo stato che NON deve essere scambiato per un guasto."""
    assert anomalia_del_listino(709, 48) is None


# --- la finestra temporale -------------------------------------------------

def _ev(giorni: float, nome: str = "a vs b") -> dict:
    inizio = _ADESSO + dt.timedelta(days=giorni)
    return {"nome": nome, "lega": "serie_a", "event_id": 1,
            "inizio": inizio.isoformat(), "_inizio": inizio}


_ADESSO = dt.datetime(2026, 7, 28, 12, 0, tzinfo=dt.timezone.utc)


def test_finestra_tiene_solo_cio_che_inizia_entro_n_ore():
    evs = [_ev(0.5, "vicina"), _ev(18, "lontana")]
    tenute = entro_finestra(evs, 72, adesso=_ADESSO)
    assert [e["nome"] for e in tenute] == ["vicina"]


def test_finestra_non_positiva_prende_tutto():
    """`--tutte-le-esposte` passa 0: e' il regime di lungo raggio, quello che
    salva la traiettoria dell'esordio nelle settimane prima del via."""
    evs = [_ev(0.5), _ev(18), _ev(33)]
    assert len(entro_finestra(evs, 0, adesso=_ADESSO)) == 3


def test_il_bordo_della_finestra_e_incluso():
    """Esattamente 72h: dentro. Un `<` al posto di `<=` perderebbe in modo
    intermittente le partite raccolte all'ora esatta del giro precedente."""
    assert len(entro_finestra([_ev(3.0)], 72, adesso=_ADESSO)) == 1
