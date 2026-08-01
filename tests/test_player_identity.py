"""Test del ponte fra le statistiche diretta.it e il `player_id` delle carriere."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import player_identity as PI


def test_ordine_dei_token_irrilevante():
    """È il punto del modulo: le due fonti scrivono il nome al contrario.

    diretta.it usa «Cognome Nome», player-scores «Nome Cognome». Con una lista
    sarebbero due chiavi diverse e il ponte non esisterebbe.
    """
    assert PI.normalizza_nome("Garces Facundo") == PI.normalizza_nome("Facundo Garces")


def test_diacritici_ignorati():
    assert PI.normalizza_nome("Facundo Garcés") == PI.normalizza_nome("Garces Facundo")


def test_lettere_che_nfkd_non_decompone():
    """`ı`, `ø`, `ł` non sono lettere accentate: sono lettere a sé, e NFKD non
    le tocca. Senza la tabella esplicita, `Kenan Yıldız` non aggancia
    `Yildiz Kenan` — misurato: 4 giocatori, 101 righe."""
    assert PI.normalizza_nome("Kenan Yıldız") == PI.normalizza_nome("Yildiz Kenan")
    assert PI.normalizza_nome("Jørgen Larsen") == PI.normalizza_nome("Larsen Jorgen")
    assert PI.normalizza_nome("Łukasz Fabiański") == PI.normalizza_nome("Fabianski Lukasz")


def test_iniziali_scartate():
    assert PI.normalizza_nome("J. Smith") == frozenset({"smith"})


def test_nome_vuoto_non_genera_chiave():
    """Una chiave costruita sul vuoto aggancerebbe TUTTI i nomi vuoti fra loro."""
    assert PI.normalizza_nome(None) == frozenset()
    assert PI.normalizza_nome("  ") == frozenset()
    assert PI._chiave("2025-08-16", None) == ""
    assert PI._chiave("2025-08-16", "...") == ""


def test_chiave_include_la_data():
    """Senza la data, un omonimo di un'altra partita aggancerebbe lo stesso."""
    a = PI._chiave("2025-08-16", "Mario Rossi")
    b = PI._chiave("2025-08-17", "Mario Rossi")
    assert a and b and a != b


def test_chiavi_ambigue_non_si_agganciano():
    """Due `player_id` diversi sotto la stessa chiave: NESSUNO dei due vince.

    Sceglierne uno attribuirebbe a un giocatore la carriera di un altro — lo
    stesso errore che la verifica d'identità è servita a chiudere, rifatto qui
    a valle. Un buco dichiarato è meglio di un aggancio inventato.
    """
    app = pd.DataFrame({
        "player_id": [1, 2, 3],
        "date": pd.to_datetime(["2025-08-16", "2025-08-16", "2025-08-16"]),
    })
    nomi = pd.DataFrame({"player_id": [1, 2, 3],
                         "name": ["Mario Rossi", "Rossi Mario", "Ugo Bianchi"]})
    import src.data.careers as C
    orig = pd.read_csv
    try:
        pd.read_csv = lambda *a, **k: nomi          # noqa: ARG005
        t = PI.tabella_aggancio(app)
    finally:
        pd.read_csv = orig
    agganciati = set(t["player_id"])
    assert 3 in agganciati          # univoco: aggancia
    assert 1 not in agganciati and 2 not in agganciati   # ambiguo: nessuno dei due


@pytest.mark.parametrize("lega", ["serie_a", "premier_league", "la_liga"])
def test_aggancio_reale_sopra_il_90_percento(lega):
    """Il ponte deve reggere sui dati veri, non solo sugli esempi costruiti."""
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(lega=lega, stagione="2526")
    except Exception:
        pytest.skip(f"raccolta {lega} non disponibile")
    if d.empty:
        pytest.skip("raccolta vuota")
    out = PI.collega(d)
    assert out["player_id"].notna().mean() > 0.90


def test_collega_non_muta_lingresso():
    """`collega` ritorna una copia: chi passa un DataFrame non se lo ritrova
    modificato sotto i piedi."""
    from src.data import player_stats as PS
    try:
        d = PS.load_player_matches(lega="serie_a", stagione="2526")
    except Exception:
        pytest.skip("raccolta non disponibile")
    colonne_prima = list(d.columns)
    PI.collega(d)
    assert list(d.columns) == colonne_prima
