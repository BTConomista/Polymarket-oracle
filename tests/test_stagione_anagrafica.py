"""Test del costruttore dell'anagrafica 2026-27 (Fase 120).

Il download non è testabile (rete + 213 MB), ma le due cose che possono
rompersi **in silenzio** sì:

1. **l'aggregato su una rosa incompleta** — il difetto trovato durante la
   costruzione: il Frosinone usciva con «valore rosa 0.8 M€» sommando **1
   giocatore su 31**, perché il record del club è fermo al 2023. Un numero
   plausibile e falso è peggio di un buco (R6);
2. **il contratto con i nomi delle fonti** — gli alias sono verificati a mano
   una voce alla volta, e questo test li fissa: se una fonte rinomina una
   squadra, la suite si accorge invece di farci scrivere l'anagrafica sbagliata.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_stagione_anagrafica import (  # noqa: E402
    ALIAS, ASSENTI, LEGA_COMP, LEGA_PAESE, _norm, slug, valore_aggregato)


# --- l'aggregato su rosa incompleta (il difetto vero) ----------------------

def test_niente_aggregato_se_la_rosa_e_stantia():
    """Il caso Frosinone: 1 valore su una rosa ufficiale di 31."""
    assert valore_aggregato([800_000], "stantia") is None


def test_niente_aggregato_se_la_squadra_e_assente():
    assert valore_aggregato([], "assente") is None


def test_aggregato_solo_su_rosa_completa():
    assert valore_aggregato([10, 20, 30], "completa") == 60


def test_aggregato_ignora_i_valori_mancanti_ma_non_li_inventa():
    """`None` in mezzo ai valori non deve valere zero né far saltare la somma,
    **purché** la copertura resti sopra soglia: 9 valutati su 10 = 90%."""
    assert valore_aggregato([10] * 9 + [None], "completa") == 90
    assert valore_aggregato([None, None], "completa") is None


def test_sotto_l_ottantacinque_percento_di_valutati_niente_aggregato():
    """La soglia è quella che il progetto già applica in
    `transfermarkt.team_season_values` (`MIN_COVERAGE = 0.85`), non una nuova:
    due nozioni diverse di «rosa coperta» nello stesso repo sarebbero il modo
    più semplice per confrontare numeri non confrontabili.

    2 valutati su 3 = 67%: sotto soglia, niente somma."""
    assert valore_aggregato([10, None, 30], "completa") is None
    # 17 su 20 = 85% esatto: la soglia è inclusiva, il bordo passa
    assert valore_aggregato([10] * 17 + [None] * 3, "completa") == 170


def test_la_soglia_e_la_stessa_del_resto_del_progetto():
    from src.data.transfermarkt import MIN_COVERAGE
    from build_stagione_anagrafica import MIN_COPERTURA_VALORI
    assert MIN_COPERTURA_VALORI == MIN_COVERAGE


# --- slug: è una chiave tecnica, deve restare stabile ---------------------

@pytest.mark.parametrize("nome,atteso", [
    ("Inter Milano", "inter-milano"),
    ("RC Deportivo De La Coruna", "rc-deportivo-de-la-coruna"),
    ("Köln", "koln"),
    ("Saint-Étienne", "saint-etienne"),
    ("1.FSV Mainz 05", "1-fsv-mainz-05"),
])
def test_slug_stabile_e_ascii(nome, atteso):
    """Lo slug è il nome della cartella: se cambia, si spezza tutto lo storico
    di quel club. Fissarlo qui è ciò che impedisce a un refactoring della
    normalizzazione di rinominare 96 cartelle senza che nessuno se ne accorga."""
    assert slug(nome) == atteso


def test_slug_non_esplode_su_input_strani():
    for s in ("", "   ", "---", "123"):
        slug(s)  # non deve sollevare


# --- il contratto con le fonti -------------------------------------------

def test_le_leghe_sono_le_cinque_del_progetto():
    from src.config import LEAGUE_CONFIGS
    assert set(LEGA_COMP) == set(LEAGUE_CONFIGS) == set(LEGA_PAESE)


def test_alias_e_assenti_non_si_sovrappongono():
    """Una squadra o si aggancia al dataset o è dichiarata assente: non
    entrambe. Se comparisse in tutti e due, l'esito dipenderebbe dall'ordine
    dei controlli — cioè da un dettaglio di implementazione."""
    assert not (set(ALIAS) & ASSENTI)


def test_alias_verificati_a_mano_restano_quelli():
    """Campione degli alias che la normalizzazione NON risolve da sola.
    Verificati uno per uno contro `clubs.csv` (Fase 120)."""
    assert ALIAS["AS Roma"] == "Associazione Sportiva Roma"
    assert ALIAS["Inter Milano"] == "Inter Milan"
    assert ALIAS["Atletico Madrid"] == "Atlético de Madrid"
    assert ALIAS["Köln"] == "1.FC Köln"
    assert ALIAS["Lille OSC"] == "LOSC Lille"


def test_la_normalizzazione_avvicina_le_scritture_diverse():
    """`_norm` serve solo ad agganciare le sigle diverse della stessa squadra."""
    assert _norm("Bologna FC") == _norm("Bologna Football Club 1909")
    assert _norm("Celta Vigo") != _norm("Celta de Vigo")  # per questo esiste ALIAS


def test_la_normalizzazione_non_fonde_squadre_diverse():
    """Il rischio opposto, e più grave: due club distinti che collassano sulla
    stessa chiave verrebbero agganciati al club sbagliato."""
    diverse = ["Inter Milan", "AC Milan", "Real Madrid", "Real Betis Balompié",
               "Atlético de Madrid", "Manchester City", "Manchester United"]
    assert len({_norm(x) for x in diverse}) == len(diverse)
