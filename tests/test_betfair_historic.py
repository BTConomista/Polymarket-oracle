"""Test del parser dello stream storico Betfair (Fase 109).

Il DOWNLOAD non e' testabile qui (l'API e' geo-bloccata dall'ambiente del
progetto e richiede un token personale), ma il PARSING si': e' una funzione
pura da bytes a dict, ed e' la parte rischiosa. Il rischio specifico non e'
"sbagliare a leggere un JSON": e' prendere per CHIUSURA un prezzo gia'
IN-PLAY, cioe' un prezzo che sa gia' cosa sta succedendo in campo. Sarebbe
look-ahead, la stessa classe di errore che il progetto ha gia' pagato con
Udinese-Roma (docs/DATI.md) e che invalida ogni confronto beat-the-close.
"""
from __future__ import annotations

import bz2
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_betfair_historic import _closing_from_stream  # noqa: E402

_MD = {
    "eventId": "28139610", "eventName": "Juventus v Napoli",
    "marketType": "OVER_UNDER_25", "countryCode": "IT",
    "marketTime": "2017-08-19T18:00:00.000Z",
    "runners": [{"id": 47972, "name": "Over 2.5 Goals"},
                {"id": 47973, "name": "Under 2.5 Goals"}],
}


def _line(pt: int, rc=None, inplay=None) -> str:
    mc: dict = {"id": "1.12345"}
    if inplay is not None:
        mc["marketDefinition"] = dict(_MD, inPlay=inplay)
    if rc:
        mc["rc"] = rc
    return json.dumps({"op": "mcm", "pt": pt, "mc": [mc]})


def _stream_normale() -> bytes:
    return "\n".join([
        _line(1500000000000, [{"ltp": 2.00, "id": 47972}, {"ltp": 2.00, "id": 47973}], inplay=False),
        _line(1500000060000, [{"ltp": 1.90, "id": 47972}]),
        _line(1500000120000, [{"ltp": 1.85, "id": 47972}, {"ltp": 2.15, "id": 47973}]),
        _line(1500000180000, inplay=True),
        # dopo il fischio d'inizio: prezzi che riflettono il campo, MAI la chiusura
        _line(1500000240000, [{"ltp": 5.00, "id": 47972}, {"ltp": 1.10, "id": 47973}]),
    ]).encode()


def test_chiusura_e_lultimo_prezzo_prima_dellinplay():
    r = _closing_from_stream(_stream_normale())
    assert r is not None
    assert r["odds_over25_close"] == 1.85
    assert r["odds_under25_close"] == 2.15
    assert r["chiusura_da_inplay"] is True


def test_nessun_look_ahead_i_prezzi_in_play_sono_ignorati():
    """Il test che conta: 5.00/1.10 sono i prezzi DOPO il primo gol. Se
    comparissero nel risultato, ogni analisi costruita su questi dati
    sarebbe falsata a nostro favore."""
    r = _closing_from_stream(_stream_normale())
    assert r["odds_over25_close"] != 5.00
    assert r["odds_under25_close"] != 1.10


def test_mercato_mai_in_play_usa_lultimo_stato_ma_lo_dichiara():
    """Mercati sospesi/annullati non segnano mai inPlay: si tiene l'ultimo
    prezzo noto, ma la riga deve DICHIARARLO (regola R4: un'anomalia si
    dichiara anche quando non e' un errore)."""
    stream = "\n".join([
        _line(1500000000000, [{"ltp": 2.00, "id": 47972}, {"ltp": 2.00, "id": 47973}], inplay=False),
        _line(1500000060000, [{"ltp": 1.95, "id": 47972}, {"ltp": 2.05, "id": 47973}]),
    ]).encode()
    r = _closing_from_stream(stream)
    assert r["odds_over25_close"] == 1.95
    assert r["chiusura_da_inplay"] is False


def test_file_senza_prezzi_ritorna_none_non_una_riga_finta():
    """Meglio nessuna riga che una riga inventata: un file senza `ltp` non
    deve produrre un record (regola R6: il buco peggiore e' il finto pieno)."""
    assert _closing_from_stream(_line(1, inplay=False).encode()) is None


def test_un_solo_lato_del_mercato_non_basta():
    """Con solo l'Over e senza l'Under non si puo' devigare: la riga va
    scartata in blocco, mai tenuta a meta' (stessa politica del guard
    bilaterale di loader._pick_market_odds)."""
    stream = "\n".join([
        _line(1500000000000, [{"ltp": 1.85, "id": 47972}], inplay=False),
        _line(1500000060000, inplay=True),
    ]).encode()
    assert _closing_from_stream(stream) is None


def test_accetta_il_bz2_reale_e_le_righe_vuote():
    """I file arrivano compressi bz2 e possono contenere righe vuote o
    troncate: non devono far cadere il parser."""
    grezzo = _stream_normale().decode() + "\n\n{ non-json\n"
    r = _closing_from_stream(bz2.decompress(bz2.compress(grezzo.encode())))
    assert r["odds_over25_close"] == 1.85


def test_metadati_per_il_join_sono_presenti():
    """Senza data e nomi squadra il dato non e' agganciabile allo snapshot:
    e' il requisito che ha fatto scartare piu' di un candidato nelle cacce
    precedenti (docs/CACCIA_OU_2017_19.md §1)."""
    r = _closing_from_stream(_stream_normale())
    assert r["eventName"] == "Juventus v Napoli"
    assert r["marketTime"] == "2017-08-19T18:00:00.000Z"
    assert r["countryCode"] == "IT"


@pytest.mark.parametrize("nome_over,nome_under", [
    ("Over 2.5 Goals", "Under 2.5 Goals"),
    ("OVER 2.5 GOALS", "UNDER 2.5 GOALS"),
])
def test_riconosce_i_runner_a_prescindere_dal_maiuscolo(nome_over, nome_under):
    md = dict(_MD, runners=[{"id": 47972, "name": nome_over},
                            {"id": 47973, "name": nome_under}])
    stream = "\n".join([
        json.dumps({"op": "mcm", "pt": 1, "mc": [{
            "id": "1.1", "marketDefinition": dict(md, inPlay=False),
            "rc": [{"ltp": 1.8, "id": 47972}, {"ltp": 2.2, "id": 47973}]}]}),
        json.dumps({"op": "mcm", "pt": 2, "mc": [{
            "id": "1.1", "marketDefinition": dict(md, inPlay=True)}]}),
    ]).encode()
    r = _closing_from_stream(stream)
    assert r["odds_over25_close"] == 1.8 and r["odds_under25_close"] == 2.2
