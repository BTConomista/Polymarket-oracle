"""Test della verifica d'identità contro Wikidata (`src/data/wikidata_identity.py`).

Nessuno di questi test tocca la rete: la parte di rete è una `urlopen` sola, e
ciò che vale la pena difendere è la **lettura** del JSON e la **regola** di
verdetto — cioè i punti dove un errore silenzioso produrrebbe un'identità
sbagliata invece di un'eccezione.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import wikidata_identity as WD


def _ent(claims):
    return {"claims": claims}


def _tempo(t, precisione=11):
    return {"mainsnak": {"snaktype": "value", "datavalue": {
        "value": {"time": t, "precision": precisione}}}}


# ---------------------------------------------------------------- robots.txt

def test_entitydata_json_e_permesso():
    """`Allow: /wiki/Special:EntityData/*.` vince sul Disallow (match più lungo)."""
    assert WD.percorso_permesso(
        "https://www.wikidata.org/wiki/Special:EntityData/Q42.json")


def test_entitydata_senza_estensione_e_vietato():
    """Senza il punto l'Allow non si applica: resta il Disallow."""
    assert not WD.percorso_permesso(
        "https://www.wikidata.org/wiki/Special:EntityData/Q42")


def test_altre_special_restano_vietate():
    assert not WD.percorso_permesso(
        "https://www.wikidata.org/wiki/Special:Search")


def test_fetch_rifiuta_percorso_vietato(monkeypatch):
    """Il controllo non è decorativo: deve fermare la richiesta, non loggarla."""
    import pytest
    monkeypatch.setattr(WD, "percorso_permesso", lambda url: False)
    with pytest.raises(ValueError):
        WD.fetch_entity("Q42", use_cache=False)


# ------------------------------------------------------------- data nascita

def test_data_nascita_precisa_al_giorno():
    e = _ent({"P569": [_tempo("+1994-01-28T00:00:00Z", 11)]})
    assert WD.data_nascita(e) == "1994-01-28"


def test_data_nascita_imprecisa_e_scartata():
    """Precisione 9 = solo l'anno: `+1994-00-00` non è il 1° gennaio (R6).

    Accettarla darebbe uno scarto di mesi contro una data vera, cioè una
    smentita inventata su un giocatore che potrebbe essere quello giusto.
    """
    assert WD.data_nascita(_ent({"P569": [_tempo("+1994-00-00T00:00:00Z", 9)]})) is None
    assert WD.data_nascita(_ent({"P569": [_tempo("+1994-06-00T00:00:00Z", 10)]})) is None


def test_data_nascita_assente():
    assert WD.data_nascita(_ent({})) is None


def test_snaktype_novalue_ignorato():
    """`somevalue`/`novalue` sono «esiste ma non si sa»: non hanno datavalue."""
    e = _ent({"P569": [{"mainsnak": {"snaktype": "somevalue"}}]})
    assert WD.data_nascita(e) is None


# --------------------------------------------------------------- militanze

def _milit(club, da=None, a=None, prec_da=11, prec_a=11, presenze=None):
    q = {}
    if da:
        q[WD.P_INIZIO] = [{"snaktype": "value", "datavalue": {
            "value": {"time": da, "precision": prec_da}}}]
    if a:
        q[WD.P_FINE] = [{"snaktype": "value", "datavalue": {
            "value": {"time": a, "precision": prec_a}}}]
    if presenze is not None:
        q[WD.P_PRESENZE] = [{"snaktype": "value", "datavalue": {
            "value": {"amount": f"+{presenze}"}}}]
    return {"mainsnak": {"snaktype": "value",
                         "datavalue": {"value": {"id": club}}},
            "qualifiers": q}


def test_militanza_legge_date_e_presenze():
    e = _ent({"P54": [_milit("Q1130", "+2015-07-01T00:00:00Z",
                             "+2019-06-30T00:00:00Z", presenze=120)]})
    m = WD.militanze(e)[0]
    assert (m.club_qid, m.da, m.a, m.presenze) == ("Q1130", "2015-07-01", "2019-06-30", 120)


def test_data_troncata_alla_precisione_dichiarata():
    """Precisione 9 → si tiene l'anno. Scrivere `2015-01-01` sarebbe inventare."""
    e = _ent({"P54": [_milit("Q1", "+2015-00-00T00:00:00Z", prec_da=9)]})
    assert WD.militanze(e)[0].da == "2015"


def test_ultimo_anno_carriera():
    e = _ent({"P54": [_milit("Q1", a="+2004-06-30T00:00:00Z"),
                      _milit("Q2", a="+2009-06-30T00:00:00Z")]})
    assert WD.ultimo_anno(WD.militanze(e)) == 2009


def test_militanza_aperta_non_ha_ultimo_anno():
    """`P580` senza `P582` = ancora in corso.

    Se `ultimo_anno` restituisse l'anno d'inizio, il ramo 2 della verifica
    dichiarerebbe «carriera chiusa nel 2015» un giocatore ancora in attività —
    una smentita fabbricata dal nostro codice, non dai dati.
    """
    e = _ent({"P54": [_milit("Q1", a="+2004-06-30T00:00:00Z"),
                      _milit("Q2", da="+2015-07-01T00:00:00Z")]})
    assert WD.ultimo_anno(WD.militanze(e)) is None


# ---------------------------------------------------------------- verdetto

def _fissa(monkeypatch, ent):
    monkeypatch.setattr(WD, "fetch_entity", lambda qid, **kw: ent)


def test_verdetto_conferma_su_data_identica(monkeypatch):
    _fissa(monkeypatch, _ent({"P569": [_tempo("+1994-01-28T00:00:00Z")]}))
    v = WD.verifica(1, "Q1", "1994-01-28", "quarantena")
    assert v.esito == "confermata" and v.scarto_giorni == 0


def test_verdetto_tollera_pochi_giorni(monkeypatch):
    _fissa(monkeypatch, _ent({"P569": [_tempo("+1994-01-30T00:00:00Z")]}))
    assert WD.verifica(1, "Q1", "1994-01-28", "quarantena").esito == "confermata"


def test_verdetto_smentisce_oltre_la_tolleranza(monkeypatch):
    _fissa(monkeypatch, _ent({"P569": [_tempo("+1969-11-28T00:00:00Z")]}))
    v = WD.verifica(1, "Q1", "2007-03-15", "quarantena")
    assert v.esito == "smentita" and v.scarto_giorni > 13_000


def test_ramo_temporale_solo_senza_data(monkeypatch):
    """Carriera chiusa prima della nostra prima presenza → è un altro (il padre)."""
    _fissa(monkeypatch, _ent({"P54": [_milit("Q1", a="+2004-06-30T00:00:00Z")]}))
    v = WD.verifica(1, "Q1", None, "respinta", prima_presenza="2015-08-22")
    assert v.esito == "smentita" and "2004" in v.motivo


def test_ramo_temporale_non_scatta_se_compatibile(monkeypatch):
    _fissa(monkeypatch, _ent({"P54": [_milit("Q1", a="+2020-06-30T00:00:00Z")]}))
    v = WD.verifica(1, "Q1", None, "respinta", prima_presenza="2015-08-22")
    assert v.esito == "indeterminato"


def test_assenza_di_prova_non_e_prova(monkeypatch):
    """Nessuna data, nessuna militanza → `indeterminato`, MAI `confermata`.

    È la regola che tiene in piedi tutta la verifica: marcare come confermato
    ciò che non lo è ricrea esattamente il problema che questo modulo esiste
    per chiudere.
    """
    _fissa(monkeypatch, _ent({}))
    assert WD.verifica(1, "Q1", "1994-01-28", "quarantena").esito == "indeterminato"


def test_entita_assente(monkeypatch):
    monkeypatch.setattr(WD, "fetch_entity", lambda qid, **kw: None)
    v = WD.verifica(1, "Q1", "1994-01-28", "quarantena")
    assert v.esito == "indeterminato" and "assente" in v.motivo


def test_qid_malformato_non_va_in_rete(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("non deve andare in rete")
    monkeypatch.setattr(WD.urllib.request, "urlopen", _boom)
    assert WD.fetch_entity("", use_cache=False) is None
    assert WD.fetch_entity("12345", use_cache=False) is None
