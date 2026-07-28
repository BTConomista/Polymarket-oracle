"""Test delle regole disciplinari (Fase 123).

Perche' questi test esistono: le soglie **non sono universali e cambiano nel
tempo**. La Ligue 1 e' passata da 3 a 5 ammonizioni nel 2025-26, la UEFA usa
i numeri dispari, la Serie A stringe le soglie a ogni recidiva. Chi codificasse
"il calcio" con una regola unica sbaglierebbe due leghe su cinque piu' la UEFA,
e il difetto non si vedrebbe: produrrebbe una lista di diffidati **plausibile**
e sbagliata.

Fissare qui i numeri, con la fonte accanto nel modulo, e' cio' che rende
visibile un cambio di regolamento invece di lasciarlo passare.
"""
from __future__ import annotations

import pytest

from src.data.disciplina import (REGOLE, incentivo_cartellino,
                                 soglia_successiva, stato)


# --- la soglia base di ogni competizione ---------------------------------

@pytest.mark.parametrize("competizione,prima_soglia", [
    ("serie_a", 5), ("premier_league", 5), ("la_liga", 5),
    ("bundesliga", 5), ("ligue_1", 5),
    ("uefa", 3),                       # la UEFA e' l'eccezione
])
def test_prima_soglia_per_competizione(competizione, prima_soglia):
    assert REGOLE[competizione].soglie[0] == prima_soglia
    assert stato(prima_soglia, competizione)["squalificato"]
    assert not stato(prima_soglia - 1, competizione)["squalificato"]


def test_ligue_1_non_e_piu_a_tre():
    """La regola e' cambiata nel 2025-26. Se qualcuno "correggesse" la tabella
    riportandola a 3 -- il valore che quasi tutti ricordano -- questo test lo
    fermerebbe."""
    assert 3 not in REGOLE["ligue_1"].soglie
    assert not stato(3, "ligue_1")["squalificato"]


# --- diffidato = a UNA ammonizione dalla squalifica ----------------------

@pytest.mark.parametrize("competizione,cartellini", [
    ("serie_a", 4), ("la_liga", 4), ("ligue_1", 4), ("uefa", 2),
])
def test_diffidato_alla_vigilia_della_soglia(competizione, cartellini):
    s = stato(cartellini, competizione)
    assert s["diffidato"] and s["ammonizioni_alla_squalifica"] == 1
    assert not s["squalificato"]


def test_chi_e_lontano_non_e_diffidato():
    s = stato(2, "serie_a")
    assert not s["diffidato"] and s["ammonizioni_alla_squalifica"] == 3


# --- le progressioni, che sono la parte che si sbaglia -------------------

def test_serie_a_le_soglie_si_stringono():
    """5, 10, 14, 17, 19 e poi ogni ammonizione: la recidiva costa sempre di
    piu'. Con una soglia fissa ogni 5 si sbaglierebbe dal decimo giallo in poi."""
    assert [soglia_successiva(c, "serie_a") for c in (0, 5, 10, 14, 17, 19)] == \
           [5, 10, 14, 17, 19, 20]


def test_uefa_dopo_la_terza_va_a_dispari():
    """3, poi 5, 7, 9: non "ogni tre". Un passo sbagliato qui produce
    diffidati inesistenti proprio nelle partite che pesano di piu'."""
    assert [soglia_successiva(c, "uefa") for c in (0, 3, 5, 7)] == [3, 5, 7, 9]


def test_premier_dopo_la_quindicesima_non_ha_altre_soglie():
    """La Premier dichiara 5/10/15 e basta: oltre, `None` -- che e' diverso da
    "zero ammonizioni mancanti"."""
    assert soglia_successiva(15, "premier_league") is None
    assert stato(16, "premier_league")["ammonizioni_alla_squalifica"] is None
    assert not stato(16, "premier_league")["squalificato"]


def test_premier_i_turni_di_squalifica_crescono():
    assert [stato(c, "premier_league")["turni_squalifica"] for c in (5, 10, 15)] == [1, 2, 3]


# --- competizione sconosciuta: errore, non un default silenzioso ---------

def test_competizione_ignota_solleva():
    """Un default silenzioso (es. "usa 5") sarebbe il modo perfetto per
    produrre diffidati sbagliati in una coppa di cui non conosciamo le regole."""
    with pytest.raises(KeyError):
        stato(4, "coppa_italia")


# --- l'incentivo e' un GIUDIZIO, e deve dirlo ---------------------------

def test_incentivo_solo_per_i_diffidati():
    assert incentivo_cartellino(3, 0.9, 0.1)["applicabile"] is False


def test_conviene_smaltire_se_la_gara_che_conta_e_quella_dopo():
    r = incentivo_cartellino(1, importanza_prossima=0.2, importanza_successiva=0.9)
    assert r["incentivo"] > 0 and "ORA" in r["lettura"]


def test_conviene_evitare_se_la_gara_che_conta_e_imminente():
    r = incentivo_cartellino(1, importanza_prossima=0.9, importanza_successiva=0.2)
    assert r["incentivo"] < 0 and "EVITARE" in r["lettura"]


def test_l_incentivo_si_dichiara_giudizio():
    """Non e' un comportamento osservato: nessuno ha mai misurato se i
    giocatori vi si conformino. Se un giorno finisse in una colonna che sembra
    una misura, sarebbe il finto pieno della R6."""
    r = incentivo_cartellino(1, 0.1, 0.9)
    assert r["tipo"] == "giudizio" and "avvertenza" in r


# --- ogni regola dichiara la sua fonte ----------------------------------

def test_ogni_regola_cita_la_fonte():
    """Una soglia senza fonte e' un numero che nessuno potra' piu' verificare
    quando il regolamento cambiera' (§2-bis)."""
    for nome, r in REGOLE.items():
        assert r.fonte, f"{nome} non dichiara la fonte"
        assert len(r.soglie) == len(r.turni)
