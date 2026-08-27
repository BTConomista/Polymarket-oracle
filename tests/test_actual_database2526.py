"""Le guardie di `data/actual_database2526.csv` e del suo costruttore.

PERCHE' ESISTE QUESTO FILE. Il database unificato 2025-26 fonde sette famiglie
di fonti che chiamano le stesse cose in modi diversi: club con grafie diverse,
date in due formati, punteggi con e senza la lotteria dei rigori, ruoli in
italiano e in inglese. Ognuno di questi e' un modo di rompersi **senza dare
errore** — il join non fallisce, restituisce meno righe; il filtro non alza
un'eccezione, restituisce una colonna vuota.

I due difetti veri gia' pagati da questo file, e inchiodati qui sotto:
  * `norm_data` — `aggancio_statistiche_squadra.csv` scrive `15.11.2025`,
    `aggancio_partite.csv` scrive `2025-11-15`. Tagliare i primi dieci
    caratteri perdeva 476 righe di Coupe de France in silenzio;
  * il filtro sui titolari delle coppe cercava `start` dentro una colonna che
    vale `titolare`/`panchina`: zero titolari su 458 partite, e una copertura
    all'84% invece che al 95% come unico sintomo.

I test che leggono il CSV prodotto si saltano se il file non c'e' (si rigenera
con `python scripts/build_actual_database2526.py`, ~12 minuti).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_actual_database2526 import (
    COMPETIZIONI, CAMPI_GIOCATORE_COPPA, LISTA_UTENTE, PS_COMPETIZIONE,
    USCITA_COMPLETA, USCITA_DEFAULT, _compatibili, _esito, _testo,
    canon_competizione, chiave_partita, json_tabellare, norm_data, norm_squadra,
)


# ════════════════════════════════════════════════════════════════════════════
# le funzioni pure — girano sempre, non serve il CSV
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("grezzo, atteso", [
    ("2025-11-15", "2025-11-15"),        # ISO, la forma di aggancio_partite
    ("15.11.2025", "2025-11-15"),        # dd.mm.yyyy, la forma delle statistiche
    ("15/11/2025", "2025-11-15"),
    ("2025-11-15T20:45:00Z", "2025-11-15"),
])
def test_norm_data_riconosce_le_due_grafie(grezzo, atteso):
    assert norm_data(grezzo) == atteso


def test_norm_data_su_un_vuoto_non_esplode():
    assert norm_data(None) == ""
    assert norm_data(float("nan")) == ""


def test_testo_non_trasforma_un_nan_nella_stringa_nan():
    """`str(x or "")` su un NaN da' «nan»: truthy, non vuota, e ha marcato
    vincenti tutti e tre gli esiti 1X2 di ogni partita."""
    assert _testo(float("nan")) == ""
    assert _testo(None) == ""
    assert _testo(" sì ") == "sì"


def test_norm_squadra_usa_gli_alias_del_progetto():
    assert norm_squadra("Internazionale") == norm_squadra("Inter")
    assert norm_squadra("Hellas Verona") == norm_squadra("Verona")


def test_norm_squadra_non_collassa_la_seconda_squadra():
    """`Real Sociedad B` NON e' il `Real Sociedad`: un aggancio univoco e
    sbagliato e' il difetto che nessun conteggio vede (R6)."""
    assert norm_squadra("Real Sociedad B") != norm_squadra("Real Sociedad")


def test_compatibili_accetta_l_abbreviazione_e_rifiuta_i_diversi():
    assert _compatibili(norm_squadra("AC Seyssinet"), norm_squadra("Seyssinet"))
    assert not _compatibili(norm_squadra("Espoir Sainte Luce"),
                            norm_squadra("Eveil des Trois Ilets"))


def test_chiave_partita_e_stabile_fra_grafie_e_formati_di_data():
    assert (chiave_partita("Serie A", "15.11.2025", "Internazionale", "AC Milan")
            == chiave_partita("Serie A", "2025-11-15", "Inter", "Milan"))


@pytest.mark.parametrize("nome, atteso", [
    ("Carabao Cup", "EFL Cup"),
    ("Coppa di Francia", "Coupe de France"),
    ("Champions League", "UEFA Champions League"),
    ("LaLiga", "LaLiga"),
])
def test_canon_competizione(nome, atteso):
    assert canon_competizione(nome) == atteso


def test_esito():
    assert _esito(2, 1) == "1"
    assert _esito(1, 2) == "2"
    assert _esito(1, 1) == "X"
    assert _esito(None, 1) is None


def test_json_tabellare_si_rilegge_come_tabella():
    testo = json_tabellare([{"nome": "A", "gol": 1}, {"nome": "B"}],
                           ["nome", "gol"])
    letto = json.loads(testo)
    assert letto["campi"] == ["nome", "gol"]
    tabella = pd.DataFrame(letto["righe"], columns=letto["campi"])
    assert list(tabella["nome"]) == ["A", "B"]
    # l'assente e' un null esplicito, non una chiave mancante
    assert letto["righe"][1][1] is None


def test_json_tabellare_scarta_i_campi_mai_presenti():
    testo = json_tabellare([{"nome": "A"}], ["nome", "gol", "xg"])
    assert json.loads(testo)["campi"] == ["nome"]


def test_la_lista_dell_utente_e_dentro_le_competizioni_dichiarate():
    assert set(LISTA_UTENTE) <= set(COMPETIZIONI)


# ════════════════════════════════════════════════════════════════════════════
# il file prodotto — si salta se non e' stato ancora costruito
# ════════════════════════════════════════════════════════════════════════════
COLONNE_DI_TESTA = ["match_uid", "competizione", "data", "casa", "trasferta",
                    "gol_casa", "gol_trasferta", "esito_1x2", "arbitro",
                    "allenatore_casa", "provenienza_json",
                    "tf_heatmap_json", "tf_n_posizioni_heatmap",
                    "tf_n_tiri_tracciati", "fd_AHh"]


@pytest.fixture(scope="module")
def database():
    percorso = (USCITA_COMPLETA if USCITA_COMPLETA.exists() else USCITA_DEFAULT)
    if not percorso.exists():
        pytest.skip("actual_database2526 non costruito")
    return pd.read_csv(percorso, low_memory=False,
                       usecols=lambda c: (c in COLONNE_DI_TESTA
                                          or c.endswith("_giocatori_json")
                                          or c.endswith("_formazione_json")))


def test_la_grana_e_la_partita(database):
    assert not database["match_uid"].duplicated().any()


def test_ogni_competizione_e_dichiarata(database):
    assert set(database["competizione"]) <= set(COMPETIZIONI)


def test_i_pacchetti_dei_giocatori_si_rileggono(database):
    """Il bug del letterale `NaN`: JSON scritto a mano che nessun parser rilegge."""
    colonne = [c for c in database.columns if c.endswith("_json")]
    assert colonne, "nessun pacchetto: il costruttore ha smesso di produrne"
    for colonna in colonne:
        for valore in database[colonna].dropna().head(50):
            letto = json.loads(valore)
            if isinstance(letto, dict) and "campi" in letto:
                assert all(len(r) == len(letto["campi"]) for r in letto["righe"])


def test_le_coppe_nazionali_hanno_le_formazioni(database):
    """La guardia del filtro `titolare` vs `start`: se qualcuno ri-scrive il
    filtro in inglese questa colonna torna vuota senza alzare errori."""
    coppe = database[database["competizione"].isin(
        ["Coppa Italia", "FA Cup", "EFL Cup", "Copa del Rey", "DFB-Pokal"])]
    if coppe.empty:
        pytest.skip("nessuna coppa nazionale nel file")
    con_distinta = coppe["cop_casa_formazione_json"].notna().sum()
    assert con_distinta > 0.7 * len(coppe), (
        f"solo {con_distinta} coppe su {len(coppe)} hanno la distinta")


def test_esito_coerente_col_punteggio(database):
    casa = pd.to_numeric(database["gol_casa"], errors="coerce")
    via = pd.to_numeric(database["gol_trasferta"], errors="coerce")
    atteso = [_esito(c, t) for c, t in zip(casa, via)]
    confrontabili = pd.Series(atteso).notna()
    assert (pd.Series(atteso)[confrontabili]
            == database["esito_1x2"][confrontabili]).all()


# ════════════════════════════════════════════════════════════════════════════
# le guardie dei difetti trovati dal censimento (workflow del 27/08/2026)
# ════════════════════════════════════════════════════════════════════════════
def test_i_campi_dei_giocatori_di_coppa_esistono_davvero():
    """Sei nomi su 26 erano SBAGLIATI e il codice li saltava in silenzio: il
    pacchetto dichiarava 26 campi e ne consegnava 20, senza i minuti giocati.
    Un `if colonna in riga.index` che non trova niente non è un errore — è un
    dato che sparisce."""
    percorso = (Path(__file__).resolve().parents[1] / "data" / "coppe_2526"
                / "aggancio_statistiche.csv")
    if not percorso.exists():
        pytest.skip("raccolta coppe assente")
    colonne = set(pd.read_csv(percorso, nrows=1).columns)
    mancanti = [c for c in CAMPI_GIOCATORE_COPPA if c not in colonne]
    assert not mancanti, f"nomi inesistenti nella fonte: {mancanti}"


def test_efl_cup_e_nella_mappa_di_player_scores():
    """Il codice `CGB` mancava, e 93 partite di EFL Cup uscivano senza
    arbitro né allenatori pur avendoli nella fonte al 100%."""
    assert "CGB" in PS_COMPETIZIONE
    assert PS_COMPETIZIONE["CGB"] == "EFL Cup"


def test_la_heatmap_e_nel_file(database):
    """La domanda dell'utente in forma di test: ci sono le posizioni?"""
    if "tf_heatmap_json" not in database.columns:
        pytest.skip("file leggero")
    piene = database["tf_heatmap_json"].notna()
    assert piene.sum() > 3000, f"solo {piene.sum()} partite con la heatmap"
    for valore in database.loc[piene, "tf_heatmap_json"].head(20):
        per_giocatore = json.loads(valore)
        assert per_giocatore
        prima = next(iter(per_giocatore.values()))
        assert set(prima) == {"l", "p"}
        assert prima["p"] and len(prima["p"][0]) == 2


def test_il_pacchetto_heatmap_coincide_col_conteggio(database):
    """Il conteggio è la colonna che dice quanto denso è il dato: se diverge
    dal pacchetto, una delle due è un finto pieno."""
    if "tf_heatmap_json" not in database.columns:
        pytest.skip("file leggero")
    fetta = database[database["tf_heatmap_json"].notna()
                     & database["tf_n_posizioni_heatmap"].notna()].head(60)
    for _, riga in fetta.iterrows():
        dentro = sum(len(v["p"]) for v in
                     json.loads(riga["tf_heatmap_json"]).values())
        assert abs(dentro - riga["tf_n_posizioni_heatmap"]) <= 2


def test_handicap_asiatico_grezzo_presente(database):
    """Le 98 colonne di quota di football-data che lo snapshot pota, e con
    esse l'unico mercato validato contro una quota esterna (Fase 88)."""
    if "fd_AHh" not in database.columns:
        pytest.skip("file leggero")
    assert database["fd_AHh"].notna().sum() > 1000
