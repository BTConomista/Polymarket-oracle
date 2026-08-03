"""Test della porta d'ingresso per le raccolte manuali di coppa (Fase 139).

Il valore di questa porta non e' l'archiviazione: e' il **confronto con la
fonte automatica**. Due fonti indipendenti sulla stessa partita sono l'unico
modo di accorgersi che una delle due sbaglia — e la Fase 138 aveva appena
dimostrato che una delle due sbagliava davvero (68 punteggi su 458 sommavano
i rigori). Questi test proteggono i controlli, non i dati.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.registra_raccolta_coppa_diretta import (
    _appaia_undici,
    _token,
    verifica_punteggio,
    verifica_rigori_eventi,
    verifica_undici,
)

RADICE = Path(__file__).resolve().parents[1]
RACCOLTA = RADICE / "files" / "diretta_coppa_italia_2526"


# --------------------------------------------------------------------------- #
# l'aggancio dei nomi fra le due fonti
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("diretta, registro", [
    ("Motta E.", "Emanuele Motta"),            # ordine invertito + iniziale
    ("Caracciolo Ant.", "Antonio Caracciolo"),  # iniziale di tre lettere
    ("Esposito Sa.", "Salvatore Esposito"),     # due Esposito, iniziale lunga
    ("Gronbaek A.", "Albert Grønbaek"),         # ø: NFKD non lo decompone
    ("Kilicsoy S.", "Semih Kılıçsoy"),          # ı senza punto
    ("Hojlund R.", "Rasmus Højlund"),
    ("Yildiz K.", "Kenan Yıldız"),
    ("Ndri K.", "Konan N'Dri"),                 # apostrofo
])
def test_stesso_giocatore_scritto_dalle_due_fonti(diretta, registro):
    """Ognuno di questi e' UNA persona scritta in due modi.

    Non sono casi di scuola: sono i 15 che, senza la tabella dei caratteri
    del progetto, facevano risultare «formazioni diverse» quindici undici
    che erano identici.
    """
    from scripts.registra_raccolta_coppa_diretta import _stessa_persona
    assert _stessa_persona(_token(diretta), _token(registro)), \
        f"«{diretta}» e «{registro}» non si agganciano"


def test_due_omonimi_in_rosa_non_si_confondono():
    """Salvatore e Francesco Esposito giocano davvero nella stessa Coppa
    Italia: l'iniziale è l'unica cosa che li distingue, e per questo si
    conserva invece di buttarla."""
    from scripts.registra_raccolta_coppa_diretta import _stessa_persona
    assert _stessa_persona(_token("Esposito Sa."), _token("Salvatore Esposito"))
    assert not _stessa_persona(_token("Esposito Sa."), _token("Francesco Esposito"))


def test_giocatori_diversi_non_si_agganciano():
    assert _appaia_undici([_token("Rossi M.")], [_token("Bianchi L.")]) == 2


def test_convenzione_spagnola_appaiata_solo_in_seconda_passata():
    """«Santiago Perez J.» e «Yellu Santiago» sono la stessa persona ma NON
    in relazione di sottoinsieme: li appaia solo la seconda passata."""
    from scripts.registra_raccolta_coppa_diretta import _stessa_persona
    a, b = _token("Santiago Perez J."), _token("Yellu Santiago")
    assert not _stessa_persona(a, b)
    assert _appaia_undici([a], [b]) == 0


# --------------------------------------------------------------------------- #
# le verifiche sul dato consegnato
# --------------------------------------------------------------------------- #
def test_undici_titolari_anomali_vengono_segnalati():
    f = pd.DataFrame({
        "ID partita": ["A"] * 11 + ["A"] * 10,
        "Squadra": ["Casa"] * 11 + ["Ospite"] * 10,
        "Gruppo": ["Titolare"] * 21,
    })
    r = verifica_undici(f)
    assert r["con_undici_esatti"] == 1
    assert len(r["anomale"]) == 1
    assert r["anomale"][0]["titolari"] == 10


def test_punteggio_ai_rigori_deve_partire_da_una_parita():
    """Se una partita e' andata ai rigori ma il punteggio non e' di parita',
    o il punteggio somma i rigori o e' sbagliato: in entrambi i casi si dice."""
    buona = pd.DataFrame([{
        "Data": "16.08.2025", "Casa": "A", "Ospite": "B",
        "Gol casa 90": 1, "Gol ospite 90": 1,
        "Gol casa dts": None, "Gol ospite dts": None,
        "Rigori casa": 5, "Rigori ospite": 4}])
    assert verifica_punteggio(buona)["incoerenti"] == []

    contaminata = buona.copy()
    contaminata.loc[0, ["Gol casa 90", "Gol ospite 90"]] = [6, 5]  # 1-1 + rigori
    assert len(verifica_punteggio(contaminata)["incoerenti"]) == 1


def test_rigori_in_parita_sono_impossibili():
    d = pd.DataFrame([{
        "Data": "16.08.2025", "Casa": "A", "Ospite": "B",
        "Gol casa 90": 1, "Gol ospite 90": 1,
        "Gol casa dts": None, "Gol ospite dts": None,
        "Rigori casa": 4, "Rigori ospite": 4}])
    assert len(verifica_punteggio(d)["incoerenti"]) == 1


def test_sequenza_rigori_confrontata_col_totale():
    partite = pd.DataFrame([{
        "ID partita": "X", "Data": "16.08.2025", "Casa": "A", "Ospite": "B",
        "Rigori casa": 5, "Rigori ospite": 4}])
    eventi = pd.DataFrame(
        [{"ID partita": "X", "Periodo": "Rigori", "Tipo evento": "Rigore",
          "Lato": "Casa"}] * 5
        + [{"ID partita": "X", "Periodo": "Rigori", "Tipo evento": "Rigore",
            "Lato": "Ospite"}] * 4)
    assert verifica_rigori_eventi(partite, eventi)["sequenza_ricompone"] == 1

    monca = eventi.iloc[:-1]           # un rigore non registrato
    r = verifica_rigori_eventi(partite, monca)
    assert r["sequenza_ricompone"] == 0
    assert len(r["divergenti"]) == 1


# --------------------------------------------------------------------------- #
# la raccolta effettivamente registrata
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not (RACCOLTA / "manifesto_coppa.json").exists(),
                    reason="la raccolta Coppa Italia non e' presente")
class TestCoppaItaliaRegistrata:

    @pytest.fixture(scope="class")
    def manifesto(self):
        return json.loads((RACCOLTA / "manifesto_coppa.json").read_text(encoding="utf-8"))

    def test_conteggi(self, manifesto):
        c = manifesto["conteggi"]
        assert c["partite"] == 45
        assert c["titolari"] == 45 * 22      # 11 per squadra, 2 squadre
        assert c["metriche_per_giocatore"] > 100

    def test_tutte_le_verifiche_interne_passano(self, manifesto):
        v = manifesto["verifiche"]
        assert v["undici_titolari"]["anomale"] == []
        assert v["punteggio_non_somma_i_rigori"]["incoerenti"] == []
        sr = v["sequenza_rigori"]
        assert sr["sequenza_ricompone"] == sr["partite_ai_rigori"] > 0

    def test_le_due_fonti_indipendenti_concordano(self, manifesto):
        """Il risultato che dà senso a tutto il resto.

        Se un giorno diverge, questo test lo dice — ed è il momento in cui si
        va a capire QUALE delle due sbaglia, non quello in cui si sceglie la
        più comoda.
        """
        c = manifesto["verifiche"]["confronto_con_fonte_automatica"]
        assert c["eseguito"]
        p, f = c["partite"], c["formazioni"]
        assert p["appaiate"] == p["manuale"] == p["automatica"]
        assert p["divergenti"] == []
        assert p["identiche_su_tutti_i_punteggi"] == p["appaiate"]
        assert f["con_differenze"] == []
        assert f["undici_identici"] == f["squadre_partita_confrontabili"]

    def test_originali_conservati(self):
        """§5-ter: senza l'originale, un bug della nostra conversione diventa
        indistinguibile dal dato."""
        assert (RACCOLTA / "originale_coppa.xlsx").exists()
