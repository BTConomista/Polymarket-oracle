"""Test del database allenatori (strato 1, da `games.csv`).

Quattro famiglie, con scopi diversi:
1. **guardiani dei dati** — copertura e conteggi misurati alla Fase 140. Se il
   file cambia sotto i piedi devono rompersi qui, non dentro un'analisi;
2. **guardiani della logica dei mandati** — su casi costruiti a mano, perche' i
   tre modi di sbagliare (il ritorno letto come mandato unico, la sola lega,
   il vice in panchina per una partita) danno tutti un numero plausibile;
3. **guardiani dell'identita'** — che `manager_key` unisca le due grafie dello
   stesso uomo e che l'omonimo resti dichiarato, mai silenzioso;
4. **guardiani della regola R8** — che `esperienza_prima` non veda mai la
   partita in corso ne' quelle dopo.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import allenatori as A


@pytest.fixture(scope="module")
def tutte() -> pd.DataFrame:
    return A.load_partite()


@pytest.fixture(scope="module")
def perimetro() -> pd.DataFrame:
    return A.load_partite(solo_top5=True, stagioni=A.STAGIONI)


@pytest.fixture(scope="module")
def mandati(tutte) -> pd.DataFrame:
    return A.panchine(tutte)


def _finte_partite(righe: list[tuple]) -> pd.DataFrame:
    """(data, club_id, allenatore, competizione) -> vista di `load_partite`."""
    df = pd.DataFrame(righe, columns=["date", "club_id", "allenatore",
                                      "competition_id"])
    df["date"] = pd.to_datetime(df["date"])
    df["game_id"] = range(1, len(df) + 1)
    df["club_name"] = "Club " + df["club_id"].astype(str)
    df["manager_key"] = df["allenatore"].map(A.normalizza_nome)
    df["gol_fatti"] = 1
    df["gol_subiti"] = 0
    df["esito"] = "V"
    df["is_top5"] = df["competition_id"].isin(A.TOP5)
    return df


# --------------------------------------------------------------------------
# 1 · Guardiani dei dati
# --------------------------------------------------------------------------

def test_il_perimetro_e_quello_degli_snapshot(perimetro):
    """16.111 partite: le stesse righe dei cinque snapshot congelati.

    Meno una: Nantes-Tolosa del 2026-05-17 non ha allenatori (ne' arbitro) e
    `load_partite` la scarta di default.
    """
    assert perimetro["game_id"].nunique() == 16_110
    assert len(perimetro) == 32_220
    assert set(perimetro["competition_id"]) == set(A.TOP5)


def test_copertura_allenatore_nel_perimetro():
    r = A.rapporto_copertura()
    assert r["partite_perimetro"] == 16_111
    assert r["senza_allenatore_perimetro"] == 2
    assert r["copertura_perimetro"] > 0.9999


def test_ogni_partita_ha_due_righe_speculari(perimetro):
    conteggio = perimetro.groupby("game_id").size()
    assert set(conteggio.unique()) == {2}
    casa = perimetro[perimetro["casa"]].set_index("game_id")
    fuori = perimetro[~perimetro["casa"]].set_index("game_id")
    assert (casa["gol_fatti"] == fuori["gol_subiti"]).all()
    assert (casa["allenatore"] == fuori["allenatore_avv"]).all()


def test_marcatura_temporale_dichiarata(perimetro):
    """R8: ogni colonna sta in `pre` o in `post`, nessuna resta senza."""
    dichiarate = set(A.COLONNE_PRE) | set(A.COLONNE_POST)
    restanti = set(perimetro.columns) - dichiarate - {"is_top5", "fonte"}
    assert not restanti, f"colonne senza marcatura temporale: {restanti}"


def test_arbitro_e_allenatore_vengono_dalla_stessa_riga(perimetro):
    """La Fase 125 leggeva `referee` da qui con uno script una tantum: e' la
    stessa tabella, e ora e' strutturale. Se la copertura arbitro crolla, il
    problema e' della fonte, non di questo modulo."""
    assert perimetro["arbitro"].notna().mean() > 0.999


# --------------------------------------------------------------------------
# 2 · Guardiani della logica dei mandati
# --------------------------------------------------------------------------

def test_il_ritorno_e_due_mandati_non_uno():
    """A -> B -> A nello stesso club sono tre mandati, non due.

    E' il caso Allegri: l'intervallo grezzo (prima e ultima partita di quel
    nome in quel club) direbbe «in carica dal 2012 al 2026».
    """
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-02-01", 1, "Bruno", "IT1"),
        ("2020-03-01", 1, "Bruno", "IT1"),
        ("2020-04-01", 1, "Aldo", "IT1"),
    ])
    m = A.panchine(p)
    assert list(m["mandato"]) == [1, 2, 3]
    assert list(m["manager_key"]) == ["aldo", "bruno", "aldo"]
    assert list(m["partite"]) == [1, 2, 1]
    assert list(m["precedente"])[1:] == ["aldo", "bruno"]


def test_le_coppe_entrano_nella_stessa_timeline():
    """Un traghettatore di una sola partita di coppa e' un mandato: chi taglia
    i mandati sul solo campionato non lo vede proprio."""
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-01-08", 1, "Vice", "CIT"),
        ("2020-01-15", 1, "Bruno", "IT1"),
    ])
    completa = A.panchine(p)
    solo_lega = A.panchine(p[p["competition_id"] == "IT1"])
    assert len(completa) == 3 and len(solo_lega) == 2
    assert "vice" not in set(solo_lega["manager_key"])


def test_il_vice_per_una_partita_e_marcato_come_interruzione():
    """A -> X -> A: e' il caso Simeone/Vivas. Marcato sempre, riassorbito solo
    su richiesta — e senza perdere la partita del vice."""
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-01-08", 1, "Vice", "IT1"),
        ("2020-01-15", 1, "Aldo", "IT1"),
    ])
    grezzo = A.panchine(p)
    assert list(grezzo["interruzione"]) == [False, True, False]
    assert len(grezzo) == 3

    ricucito = A.panchine(p, ricuci=True)
    assert len(ricucito) == 1
    riga = ricucito.iloc[0]
    assert riga["manager_key"] == "aldo"
    assert riga["partite"] == 2 and riga["partite_altrui"] == 1
    assert riga["interruzioni"] == 1
    assert riga["data_da"] == pd.Timestamp("2020-01-01")
    assert riga["data_a"] == pd.Timestamp("2020-01-15")


def test_la_ricucitura_non_perde_nessuna_partita(tutte, mandati):
    ricucito = A.panchine(tutte, ricuci=True)
    assert mandati["partite"].sum() == len(tutte)
    assert ricucito["partite"].sum() + ricucito["partite_altrui"].sum() == len(tutte)


def test_due_interruzioni_di_fila_restano_attribuite():
    """A X A Y A: entrambe le interruzioni vanno al mandato di A, e nessuna
    partita finisce in un mandato che non esiste piu'."""
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-01-08", 1, "Vice", "IT1"),
        ("2020-01-15", 1, "Aldo", "IT1"),
        ("2020-01-22", 1, "Altro", "IT1"),
        ("2020-01-29", 1, "Aldo", "IT1"),
    ])
    r = A.panchine(p, ricuci=True)
    assert len(r) == 1
    assert r.iloc[0]["partite"] == 3
    assert r.iloc[0]["partite_altrui"] == 2
    assert r.iloc[0]["interruzioni"] == 2


def test_interruzione_piu_lunga_della_soglia_non_si_ricuce():
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-01-08", 1, "Vice", "IT1"),
        ("2020-01-11", 1, "Vice", "IT1"),
        ("2020-01-15", 1, "Aldo", "IT1"),
    ])
    r = A.panchine(p, ricuci=True)
    assert len(r) == 3
    assert bool(r.iloc[1]["interruzione"]) is True


def test_i_mandati_non_scavallano_i_club():
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-01-08", 2, "Aldo", "IT1"),
    ])
    m = A.panchine(p)
    assert len(m) == 2
    assert list(m["mandato"]) == [1, 1]
    assert m["precedente"].isna().all()


def test_cambi_panchina_esclude_i_cambi_estivi():
    p = _finte_partite([
        ("2020-03-01", 1, "Aldo", "IT1"),
        ("2020-08-01", 1, "Bruno", "IT1"),      # cambio d'estate
        ("2020-11-01", 1, "Carlo", "IT1"),      # esonero in corsa
    ])
    m = A.panchine(p)
    dentro = A.cambi_panchina(m)
    assert list(dentro["entra"]) == ["carlo"]
    tutti = A.cambi_panchina(m, solo_in_stagione=False)
    assert list(tutti["entra"]) == ["bruno", "carlo"]
    assert list(tutti["esce"]) == ["aldo", "bruno"]


def test_i_mandati_ricuciti_riducono_i_cambi_contati(tutte, mandati):
    """Contare i cambi sui mandati grezzi sovrastima: ogni vice in panchina per
    una partita vale due eventi finti (esce/rientra)."""
    grezzi = len(A.cambi_panchina(mandati))
    veri = len(A.cambi_panchina(A.panchine(tutte, ricuci=True)))
    assert veri < grezzi


# --------------------------------------------------------------------------
# 3 · Guardiani dell'identita'
# --------------------------------------------------------------------------

def test_normalizza_unisce_le_due_grafie_dello_stesso_uomo():
    assert A.normalizza_nome("Ivan Jurić") == A.normalizza_nome("Ivan Juric")
    assert A.normalizza_nome("Bruno Génésio") == A.normalizza_nome("Bruno Genesio")
    assert A.normalizza_nome("Sanchez-Flores") == A.normalizza_nome("Sanchez Flores")
    assert A.normalizza_nome("  Pep   Guardiola ") == "pep guardiola"
    assert A.normalizza_nome(None) == ""
    assert A.normalizza_nome(float("nan")) == ""


def test_la_normalizzazione_unisce_solo_dove_serve(perimetro, tutte):
    """Nel perimetro: 496 nomi grezzi -> 494 chiavi (2 gruppi, 485 partite)."""
    assert perimetro["allenatore"].nunique() == 496
    assert perimetro["manager_key"].nunique() == 494
    assert tutte["allenatore"].nunique() == 7031
    assert tutte["manager_key"].nunique() == 6995


def test_gli_omonimi_sono_dichiarati_non_nascosti(tutte):
    """Il test di impossibilita' fisica: stesso nome, stesso giorno, due club.

    `Michel` sono due allenatori spagnoli diversi, e il 2022-10-02 la stessa
    stringa siede su due panchine. Finche' non c'e' una fonte di identita'
    esterna, il minimo e' che il conflitto sia elencabile.
    """
    conf = A.conflitti_identita(tutte)
    assert conf["manager_key"].nunique() == 11
    assert "michel" in set(conf["manager_key"])
    riga = conf[conf["manager_key"] == "michel"].iloc[0]
    assert riga["giorni"] == 0
    assert riga["club_a"] != riga["club_b"]


def test_conflitti_identita_su_caso_costruito():
    p = _finte_partite([
        ("2020-01-01", 1, "Mario Rossi", "IT1"),
        ("2020-01-01", 2, "Mario Rossi", "GR1"),
        ("2020-01-01", 3, "Anna Bianchi", "IT1"),
    ])
    conf = A.conflitti_identita(p)
    assert list(conf["manager_key"]) == ["mario rossi"]
    assert A.conflitti_identita(p[p["club_id"] == 1]).empty


def test_una_finestra_piu_larga_trova_almeno_altrettanto(tutte):
    stretta = set(A.conflitti_identita(tutte)["manager_key"])
    larga = set(A.conflitti_identita(tutte, giorni=7)["manager_key"])
    assert stretta <= larga


# --------------------------------------------------------------------------
# 4 · Guardiani della regola R8
# --------------------------------------------------------------------------

def test_esperienza_prima_non_guarda_la_partita_in_corso():
    p = _finte_partite([
        ("2020-01-01", 1, "Aldo", "IT1"),
        ("2020-02-01", 1, "Aldo", "IT1"),
        ("2020-03-01", 1, "Aldo", "IT1"),
    ])
    e = A.esperienza_prima("2020-02-01", p)
    assert e.loc["aldo", "partite_prima"] == 1       # non 2, non 3
    assert e.loc["aldo", "primo_incarico"] == pd.Timestamp("2020-01-01")


def test_esperienza_prima_cresce_col_tempo(tutte):
    a = A.esperienza_prima("2019-01-01", tutte, manager_keys=["pep guardiola"])
    b = A.esperienza_prima("2023-01-01", tutte, manager_keys=["pep guardiola"])
    assert b.loc["pep guardiola", "partite_prima"] > a.loc["pep guardiola", "partite_prima"]
    assert (b.loc["pep guardiola", "top5_prima"]
            + b.loc["pep guardiola", "altro_prima"]
            == b.loc["pep guardiola", "partite_prima"])


def test_prima_dell_inizio_del_dataset_non_c_e_esperienza(tutte):
    assert A.esperienza_prima("2006-01-01", tutte).empty


def test_la_censura_a_sinistra_e_marcata():
    """Chi compare al bordo della propria competizione e' censurato: i suoi
    totali sono un limite inferiore, non una misura."""
    p = _finte_partite([
        ("2012-08-11", 1, "Aldo", "IT1"),       # il bordo
        ("2015-08-11", 2, "Bruno", "IT1"),      # tre anni dopo
    ])
    e = A.esperienza_prima("2020-01-01", p)
    assert bool(e.loc["aldo", "censurata"]) is True
    assert bool(e.loc["bruno", "censurata"]) is False


def test_i_falsi_esordi_del_perimetro_sono_censurati(tutte):
    """Ancelotti «esordisce» nel 2012 e Mourinho nel 2012 solo perche' li'
    comincia il dataset. Se un giorno questo test passasse a False, vorrebbe
    dire che qualcuno ha allargato la finestra a monte — non che hanno
    davvero esordito allora."""
    e = A.esperienza_prima("2026-01-01", tutte,
                           manager_keys=["carlo ancelotti", "jose mourinho"])
    assert e["censurata"].all()


# --------------------------------------------------------------------------
# 5 · Il registro della verifica esterna (Fase 141)
# --------------------------------------------------------------------------

def test_il_registro_e_opzionale(monkeypatch, tmp_path):
    """Chi clona il repo senza aver eseguito la verifica deve poter usare il
    modulo lo stesso: lo strato esterno e' opzionale per costruzione."""
    monkeypatch.setattr(A, "REGISTRO_INCARICHI", tmp_path / "non_esiste.csv")
    vuoto = A.incarichi_verificati()
    assert vuoto.empty
    assert "in_carica" in vuoto.columns          # lo schema c'e' comunque


def test_con_verifica_non_perde_ne_aggiunge_mandati(mandati):
    """⚠️ Il modo piu' rapido di far sembrare completa una verifica che non lo
    e' sarebbe far sparire i mandati non verificati. Restano, con le colonne
    vuote."""
    campione = mandati.head(200)
    unito = A.con_verifica(campione)
    assert len(unito) == len(campione)
    assert set(unito["manager_key"]) == set(campione["manager_key"])
    for c in ("verificato_da", "in_carica", "ruolo", "fonte"):
        assert c in unito.columns


def test_il_registro_non_corregge_la_fonte_primaria(tutte):
    """R3: `panchine()` deve dare lo stesso identico risultato con o senza
    registro. Se un giorno qualcuno lo facesse "applicare", questo test cade."""
    prima = A.panchine(tutte.head(5000))
    dopo = A.con_verifica(A.panchine(tutte.head(5000)))
    comuni = list(prima.columns)
    pd.testing.assert_frame_equal(prima[comuni], dopo[comuni])


def test_una_risposta_senza_fonte_e_marcata_come_difetto():
    """`in_carica` compilato e `fonte` vuota non e' un dato: il registro deve
    saperlo dire di se stesso."""
    reg = A.incarichi_verificati()
    if reg.empty:
        pytest.skip("verifica esterna non eseguita in questo ambiente")
    assert "senza_fonte" in reg.columns
    verificate = reg[reg["verificato"]]
    assert (verificate["fonte"].fillna("") != "").all(), (
        "ci sono righe verificate senza fonte: sono un difetto, non un dato")
