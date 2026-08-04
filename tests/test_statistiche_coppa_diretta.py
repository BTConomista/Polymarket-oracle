"""Test della porta d'ingresso delle STATISTICHE di coppa (Fase 140).

Cosa proteggono davvero questi test.

La consegna precedente delle stesse coppe esisteva gia': stesse righe, stessi
giocatori. Quella nuova porta tre cose che non c'erano — le statistiche di
SQUADRA per periodo, la colonna `ID partita` sulle statistiche per giocatore, e
sei decimali invece di tre. Il rischio, in una consegna cosi', non e' il dato
mancante: e' il dato che **cambia** senza che nessuno se ne accorga, nascosto
dentro un arrotondamento che sembra innocuo. Per questo il confronto con la
consegna precedente ha una soglia esplicita (0.005) e non una tolleranza a
occhio, e per questo l'additivita' fra periodi si ricalcola qui invece di
fidarsi del numero scritto nel manifesto.

Il difetto piu' insidioso trovato scrivendo questa porta non era nei dati: era
nel CONTROLLO. Da pandas 3.0 `astype(str)` lascia il NaN com'e' invece di
produrre la stringa 'nan', e `NaN != NaN` e' vero — quindi due colonne identiche
risultavano divergenti su ogni cella vuota, e la verifica di fedelta' accusava
la conversione di un difetto inesistente (134 falsi positivi sulla colonna
`Rating`). `test_testo_e_null_safe` e' la sua regressione: un controllo che
grida al lupo e' un controllo che verra' spento.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.registra_raccolta_statistiche_coppa_diretta import (
    COMPOSITE,
    FILE_GIOCATORI,
    FILE_MANIFESTO,
    FILE_ORIGINALE,
    FILE_SQUADRA,
    _celle_divergenti,
    _espandi,
    _percento,
    _testo,
)
from src.data import team_stats as TS

RADICE = Path(__file__).resolve().parents[1]
CARTELLE = {
    "EFL Cup": RADICE / "files" / "diretta_efl_cup_2526",
    "FA Cup": RADICE / "files" / "diretta_fa_cup_2526",
}
REGISTRATE = [n for n, d in CARTELLE.items() if (d / FILE_MANIFESTO).exists()]


# --------------------------------------------------------------------------- #
# le funzioni pure
# --------------------------------------------------------------------------- #
def test_espandi_composita():
    assert _espandi("77% (364/473)") == (364.0, 473.0, 77.0)
    assert _espandi("0% (0/3)") == (0.0, 3.0, 0.0)


def test_espandi_vuoto_resta_vuoto():
    """Il vuoto NON e' uno zero: qui non si sa quanti passaggi siano stati
    tentati, e riempirlo con 0 sarebbe un finto pieno (regola R6)."""
    assert all(np.isnan(v) for v in _espandi(np.nan))


def test_espandi_rifiuta_una_forma_che_non_conosce():
    with pytest.raises(SystemExit):
        _espandi("364/473")          # senza percentuale
    with pytest.raises(SystemExit):
        _espandi("77%")              # senza il dettaglio


def test_percento():
    assert _percento("61%") == 61.0
    assert np.isnan(_percento(np.nan))
    with pytest.raises(SystemExit):
        _percento("61")


def test_testo_e_null_safe():
    """REGRESSIONE: due colonne identiche non devono divergere sui vuoti.

    Da pandas 3.0 `astype(str)` non produce piu' la stringa 'nan' sul NaN, e
    `NaN != NaN`. Senza `fillna` prima del confronto, ogni cella vuota diventa
    una falsa divergenza.
    """
    s = pd.Series([1.0, np.nan, 3.0])
    assert (_testo(s) == _testo(s.copy())).all()


def test_celle_divergenti_ignora_i_vuoti_e_vede_le_differenze_vere():
    a = pd.DataFrame({"x": [1.0, np.nan, 3.0], "t": ["a", None, "c"]})
    assert _celle_divergenti(a, a.copy()) == 0

    b = a.copy()
    b.loc[2, "x"] = 3.5
    assert _celle_divergenti(a, b) == 1


def test_celle_divergenti_non_confonde_3_con_3_punto_0():
    """Il CSV consegnato e l'.xlsx scrivono lo stesso intero in due modi: se il
    confronto fosse testuale, la fedelta' fallirebbe su un dato identico."""
    a = pd.DataFrame({"x": ["3", "4"]})
    b = pd.DataFrame({"x": [3.0, 4.0]})
    assert _celle_divergenti(a, b) == 0


# --------------------------------------------------------------------------- #
# le raccolte effettivamente registrate
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not REGISTRATE, reason="nessuna raccolta statistiche di coppa presente")
@pytest.mark.parametrize("coppa", REGISTRATE)
class TestStatisticheRegistrate:

    @pytest.fixture
    def cartella(self, coppa):
        return CARTELLE[coppa]

    @pytest.fixture
    def manifesto(self, cartella):
        return json.loads((cartella / FILE_MANIFESTO).read_text(encoding="utf-8"))

    @pytest.fixture
    def squadra(self, cartella):
        return pd.read_csv(cartella / FILE_SQUADRA)

    def test_originale_conservato(self, cartella, manifesto):
        """§5-ter: senza l'originale, un bug della nostra conversione diventa
        indistinguibile dal dato."""
        assert (cartella / FILE_ORIGINALE).exists()
        assert len(manifesto["sha256"]) == 64

    def test_fedelta_dei_csv_consegnati(self, manifesto):
        for etichetta, esito in manifesto["fedelta_csv_vs_xlsx"].items():
            if esito == "non consegnato":
                continue
            fatte, totali = (int(x) for x in esito.split()[0].split("/"))
            assert fatte == totali > 0, f"{etichetta}: {esito}"

    def test_nessuna_divergenza_reale_dalla_consegna_precedente(self, manifesto):
        """Il controllo che conta: piu' precisione e' benvenuta, un dato che
        CAMBIA no. La soglia e' esplicita, non a occhio."""
        c = manifesto["giocatori_confronto_consegna_precedente"]
        assert c["divergenze_reali"] == 0
        assert c["scarto_massimo"] <= 0.005
        assert c["celle_confrontate"] > 100_000

    def test_additivita_ricalcolata_non_dichiarata(self, squadra):
        """Si ricalcola qui: un manifesto che si auto-certifica non e' una prova."""
        additive = [c for c in TS.COLONNE_METRICHE if c not in TS.COLONNE_NON_ADDITIVE]
        d = squadra.copy()
        for c in TS.COLONNE_ZERO_IMPLICITO:
            d[c] = d[c].fillna(0)
        chiave = ["ID partita", "Squadra"]
        somma = d[d["Periodo"] != TS.PERIODO_TOTALE].groupby(chiave)[additive].sum()
        rif = d[d["Periodo"] == TS.PERIODO_TOTALE].set_index(chiave)[additive]
        assert int(((somma - rif).abs() > 0.005).sum().sum()) == 0

    def test_possesso_somma_a_cento(self, squadra):
        """Controllo SEMANTICO indipendente: nessuna verifica della porta lo
        impone, quindi se torna e' perche' il dato e' quello giusto."""
        tot = squadra[squadra["Periodo"] == TS.PERIODO_TOTALE]
        somme = tot.groupby("ID partita")["Possesso palla %"].sum()
        assert (somme == 100).all()

    def test_id_partita_aggancia_le_partite(self, cartella, squadra):
        """E' la ragione d'essere di questa consegna: `aggancia_coppe.py` doveva
        aggirarne l'assenza appaiando per (Data, Casa, Ospite) e poi per nome."""
        partite = pd.read_csv(cartella / "partite.csv")
        ids = set(partite["ID partita"].astype(str))
        gioc = pd.read_csv(cartella / FILE_GIOCATORI)
        assert "ID partita" in gioc.columns
        assert not gioc["ID partita"].isna().any()
        assert set(gioc["ID partita"].astype(str)) <= ids
        assert set(squadra["ID partita"].astype(str)) <= ids

    def test_supplementari_solo_dove_sono_stati_giocati(self, cartella, squadra):
        """Un periodo «Supplementari» su una partita finita nei 90' sarebbe un
        finto pieno (R6); mancarne uno dove si sono giocati e' un buco muto."""
        partite = pd.read_csv(cartella / "partite.csv", dtype={"ID partita": str})
        con_righe = set(squadra.loc[squadra["Periodo"] == "Supplementari",
                                    "ID partita"].astype(str))
        originale = pd.read_excel(cartella / FILE_ORIGINALE, sheet_name="Partite")
        dichiarati = set(originale.loc[originale["Supplementari giocati"] == "Sì",
                                       "ID partita"].astype(str))
        assert con_righe == dichiarati


# --------------------------------------------------------------------------- #
# il guardiano strutturale: coppe e campionati devono leggersi allo stesso modo
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(len(REGISTRATE) < 2, reason="servono due raccolte per confrontarle")
def test_schema_identico_fra_le_coppe():
    a, b = (pd.read_csv(CARTELLE[c] / FILE_SQUADRA, nrows=1) for c in REGISTRATE[:2])
    assert list(a.columns) == list(b.columns)


@pytest.mark.skipif(not REGISTRATE, reason="nessuna raccolta statistiche di coppa presente")
def test_artefatto_deterministico():
    """L'artefatto compresso non deve cambiare impronta senza che cambi un dato.

    `gzip` incorpora l'ORA nell'intestazione: senza `mtime=0` la stessa
    esecuzione produce due file diversi, e un registro la cui impronta balla da
    sola non e' piu' verificabile da nessuno (R3, idempotenza al byte).
    """
    import gzip

    percorso = CARTELLE[REGISTRATE[0]] / FILE_SQUADRA
    grezzo = percorso.read_bytes()
    # byte 4..7 dell'header gzip = mtime, little-endian
    assert grezzo[4:8] == b"\x00\x00\x00\x00", "l'ora e' finita nell'artefatto"
    assert gzip.decompress(grezzo).count(b"\n") > 100


@pytest.mark.skipif(not REGISTRATE, reason="nessuna raccolta statistiche di coppa presente")
def test_le_metriche_di_coppa_sono_quelle_dei_campionati():
    """Il punto della normalizzazione: la fonte consegna le coppe con sei
    metriche COMPOSITE («77% (364/473)») che i campionati hanno gia' espanse in
    tre colonne. Espanderle qui e' cio' che permette di confrontare una partita
    di coppa con una di campionato senza codice speciale.
    """
    d = pd.read_csv(CARTELLE[REGISTRATE[0]] / FILE_SQUADRA, nrows=1)
    metriche = [c for c in d.columns if c in TS.COLONNE_METRICHE]
    assert metriche == list(TS.COLONNE_METRICHE)
    # e nessuna colonna composita e' sopravvissuta alla normalizzazione
    assert not set(COMPOSITE) & set(d.columns)
