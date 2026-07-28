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

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_smarkets_matches import MERCATI_BASE, SLUG_LEGA, _slug_lega  # noqa: E402


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
    """Il caso che conta: `germany-2-bundesliga` NON deve passare per
    `germany-bundesliga`. Con un match "contiene" invece che esatto,
    passerebbe -- e la seconda divisione tedesca finirebbe negli stessi file
    della prima."""
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
