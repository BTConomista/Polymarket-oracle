"""Test della verifica esterna degli allenatori contro Wikidata (Fase 141).

I test qui dentro sono quasi tutti **guardiani di un difetto gia' pagato**: due
li ho pagati scrivendo lo script (le date a precisione ridotta e le varianti del
nome proprio), gli altri stanno in piedi perche' la stessa forma di errore e'
gia' costata altrove nel progetto.

Quattro famiglie:
1. **robots.txt** — che la via SPARQL resti chiusa e quella permessa aperta. E'
   la regola che nessun test proteggeva e che un domani, trovando l'endpoint
   funzionante, qualcuno riaprirebbe;
2. **le date di Wikidata** — che una data ad anno non venga mai spacciata per
   una data esatta;
3. **l'identita' dei nomi** — che la regola sulle varianti unisca `Adi`/`Adolf`
   e NON unisca due persone diverse;
4. **la semantica del confronto** — che una data mancante resti un estremo
   aperto e non diventi una divergenza.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import wikidata_identity as WD          # noqa: E402


def _carica_script():
    percorso = ROOT / "scripts" / "aggancia_allenatori_wikidata.py"
    spec = importlib.util.spec_from_file_location("aggancia_wd", percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def S():
    return _carica_script()


# --------------------------------------------------------------------------
# 1 · Robots.txt — la via chiusa deve restare chiusa
# --------------------------------------------------------------------------

def test_la_via_permessa_e_solo_quella_con_estensione():
    """`Allow: /wiki/Special:EntityData/*.` vale per il match piu' lungo.

    ⚠️ `urllib.robotparser` su questa coppia risponde SBAGLIATO (applica
    first-match-wins invece del longest-match, RFC 9309 §2.2.2): se un giorno
    qualcuno lo "semplificasse" riusando la libreria standard, questo test
    diventa rosso.
    """
    assert WD.percorso_permesso(
        "https://www.wikidata.org/wiki/Special:EntityData/Q2074.json")
    assert not WD.percorso_permesso(
        "https://www.wikidata.org/wiki/Special:EntityData/Q2074")
    assert not WD.percorso_permesso(
        "https://www.wikidata.org/wiki/Special:GoToLinkedPage/Q1")


def test_lo_script_non_nomina_mai_l_endpoint_sparql():
    """`query.wikidata.org/robots.txt` dice `Disallow: /sparql`.

    L'endpoint RISPONDE, e una sola query avrebbe prodotto tutta la raccolta:
    e' la scorciatoia piu' facile del mondo da riprendere in mano. Il test
    esiste perche' la ragione per cui non si usa non sta nel codice — sta in
    una riga di un file su un altro dominio.
    """
    testo = (ROOT / "scripts" / "aggancia_allenatori_wikidata.py").read_text()
    codice = "\n".join(r for r in testo.splitlines()
                       if not r.strip().startswith("#"))
    corpo = codice.split('"""', 2)[-1]          # via il docstring del modulo
    assert "query.wikidata.org" not in corpo
    assert "sparql" not in corpo.lower()


# --------------------------------------------------------------------------
# 2 · Le date di Wikidata hanno una precisione dichiarata
# --------------------------------------------------------------------------

def _claim(inizio: str, precisione: int) -> dict:
    return {"qualifiers": {WD.P_INIZIO: [
        {"datavalue": {"value": {"time": inizio, "precision": precisione}}}]}}


def test_una_data_ad_anno_non_diventa_una_data_esatta(S):
    """`+1958-00-00T00:00:00Z` = «1958, mese e giorno non noti».

    Prima della correzione questo valore alzava `month must be in 1..12` e
    fermava l'intero scarico. Il rischio opposto — normalizzare in silenzio e
    far credere a una precisione che la fonte non dichiara — e' peggiore: per
    questo la precisione resta leggibile accanto alla data.
    """
    c = _claim("+1958-00-00T00:00:00Z", 9)
    assert S._data_qual(c, WD.P_INIZIO) == "1958-01-01"
    assert S._precisione_qual(c, WD.P_INIZIO) == 9      # 9 = anno, non giorno

    c = _claim("+2021-11-00T00:00:00Z", 10)
    assert S._data_qual(c, WD.P_INIZIO) == "2021-11-01"
    assert S._precisione_qual(c, WD.P_INIZIO) == 10     # mese

    c = _claim("+2021-11-24T00:00:00Z", 11)
    assert S._data_qual(c, WD.P_INIZIO) == "2021-11-24"
    assert S._precisione_qual(c, WD.P_INIZIO) == 11     # giorno


def test_un_qualificatore_assente_resta_assente(S):
    assert S._data_qual({}, WD.P_INIZIO) is None
    assert S._precisione_qual({}, WD.P_INIZIO) is None


def test_ogni_data_normalizzata_e_una_data_valida(S):
    import pandas as pd
    for t, p in [("+1958-00-00T00:00:00Z", 9), ("+2021-00-00T00:00:00Z", 9),
                 ("+2021-11-00T00:00:00Z", 10), ("+2021-02-28T00:00:00Z", 11)]:
        assert pd.notna(pd.Timestamp(S._data_qual(_claim(t, p), WD.P_INIZIO)))


# --------------------------------------------------------------------------
# 3 · L'identita' dei nomi
# --------------------------------------------------------------------------

def test_le_varianti_del_nome_proprio_si_uniscono(S):
    """I due casi veri: un diminutivo e una forma locale — e Wikidata usa
    entrambe le grafie DENTRO la stessa storia di club."""
    assert S._stessa_persona("adi hutter", "adolf hutter")
    assert S._stessa_persona("freddie ljungberg", "fredrik ljungberg")
    assert S._stessa_persona("mikel arteta", "mikel arteta")


def test_due_persone_diverse_NON_si_uniscono(S):
    """Il guardrail che rende la regola accettabile: cognome diverso, mai."""
    assert not S._stessa_persona("diego simeone", "nelson vivas")
    assert not S._stessa_persona("adi hutter", "adi favre")
    assert not S._stessa_persona("marco rossi", "marco bianchi")
    assert not S._stessa_persona("", "adolf hutter")


def test_stesso_cognome_ma_nome_incompatibile_non_si_unisce(S):
    """Padre e figlio, o due fratelli, hanno lo stesso cognome. La regola
    chiede anche il nome compatibile, non solo l'ultimo token."""
    assert not S._stessa_persona("vladimir weiss", "milan weiss")
    assert not S._stessa_persona("robert kramer", "frank kramer")


# --------------------------------------------------------------------------
# 4 · La semantica del confronto
# --------------------------------------------------------------------------

def test_la_tolleranza_e_dichiarata_e_motivata(S):
    """Le nostre date sono prima/ultima PARTITA, quelle di Wikidata nomina ed
    esonero: senza tolleranza ogni mandato sarebbe una divergenza."""
    assert S.TOLLERANZA_GIORNI == 45


def test_i_club_alias_sono_dichiarati_uno_per_uno(S):
    """Cinque nomi scritti a mano, non indovinati. Se qualcuno ne aggiunge uno
    senza verificarlo, almeno il conteggio cambia sotto gli occhi."""
    assert len(S.ALIAS_CLUB) == 5
    assert "FC Barcelona" in S.ALIAS_CLUB


def test_il_barcellona_e_un_club_anche_se_il_p31_dice_altro(S):
    """La polisportiva non e' «societa' calcistica» per P31 ma ha 64 mandati
    P286: fermarsi alla tassonomia avrebbe scartato il club piu' titolato."""
    polisportiva = {"claims": {"P31": [{"mainsnak": {"datavalue": {
        "value": {"id": "Q10651067"}}}}], "P286": [{"mainsnak": {}}]}}
    assert S._e_club(polisportiva)

    persona = {"claims": {"P31": [{"mainsnak": {"datavalue": {
        "value": {"id": "Q5"}}}}], "P286": [{"mainsnak": {}}]}}
    assert not S._e_club(persona)      # un umano non e' un club, mai

    niente = {"claims": {"P31": [{"mainsnak": {"datavalue": {
        "value": {"id": "Q3336843"}}}}]}}
    assert not S._e_club(niente)
