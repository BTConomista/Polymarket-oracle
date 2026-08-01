"""Test dello scoring del test prospettico (Fase 129, passo P4).

Perche' esistono. Questo scoring gira **una volta sola e in ritardo**: la
prima esecuzione vera sara' a fine agosto, su dati che non si possono
rigenerare. Uno scoring che si rompe allora e' un turno perso; uno che gira ma
misura la cosa sbagliata e' peggio, perche' produce un numero e nessuno lo
mette in dubbio.

Il pezzo che questi test proteggono davvero e' la tabella `BINARI`: la
traduzione da mercato a esito. Un `cs_home` letto al contrario dà un numero
plausibile e sbagliato, e non c'e' modo di accorgersene guardando l'uscita.
Ogni regola e' verificata su un punteggio scelto perche' **distingue** la
regola giusta dalla sua inversione (2-0 e 0-2, mai 1-1).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from _run_prospettico_scoring import BINARI, ece, esito_1x2, scora  # noqa: E402


# --- la traduzione mercato -> esito, su un 2-0 (casa vince, ospite a zero) ---
@pytest.mark.parametrize("mercato,atteso", [
    ("over_0.5", True), ("over_1.5", True), ("over_2.5", False),
    ("over_3.5", False), ("over_4.5", False),
    ("btts", False),                    # l'ospite non ha segnato
    ("odd_total", False),               # 2 gol: pari
    ("dc_1x", True), ("dc_12", True), ("dc_2x", False),
    ("home_ov_0.5", True), ("home_ov_1.5", True),
    ("away_ov_0.5", False), ("away_ov_1.5", False),
    ("cs_home", True),                  # clean sheet CASA = l'ospite non segna
    ("cs_away", False),
    ("wtn_home", True),                 # casa vince a zero
    ("wtn_away", False),
    ("home_by_2plus", True), ("away_by_2plus", False),
    ("mg_0_1", False), ("mg_2_3", True), ("mg_4plus", False),
])
def test_regole_su_2_0(mercato, atteso):
    assert bool(BINARI[mercato](np.array([2]), np.array([0]))[0]) is atteso


@pytest.mark.parametrize("mercato", sorted(BINARI))
def test_ogni_regola_e_simmetrica_o_no_ma_mai_per_caso(mercato):
    """Un 2-0 e uno 0-2 devono dare esiti SCAMBIATI sui mercati asimmetrici e
    uguali su quelli simmetrici. E' il controllo che cattura una regola casa/
    ospite invertita, che un solo punteggio non distinguerebbe."""
    r = BINARI[mercato]
    due_zero = bool(r(np.array([2]), np.array([0]))[0])
    zero_due = bool(r(np.array([0]), np.array([2]))[0])
    # Simmetrici = quelli che dipendono solo dal TOTALE o dallo scarto in
    # valore assoluto. `dc_12` sta qui perche' e' «non pareggio», cioe'
    # `h != a`: e' l'unica doppia chance che non guarda chi ha vinto — ed e'
    # esattamente l'identita' `P(12) = 1 − P(X)` che la Fase 92 ha scoperto
    # essere stata letta al contrario per 80 fasi.
    simmetrici = {"over_0.5", "over_1.5", "over_2.5", "over_3.5", "over_4.5",
                  "btts", "odd_total", "mg_0_1", "mg_2_3", "mg_4plus", "dc_12"}
    if mercato in simmetrici:
        assert due_zero == zero_due
    else:
        assert due_zero != zero_due, f"{mercato}: non distingue casa da ospite"


def test_esito_1x2():
    h, a = np.array([2, 1, 0]), np.array([0, 1, 2])
    assert esito_1x2(h, a) == ["H", "D", "A"]


# --- lo scoring completo, su dati sintetici -------------------------------

def _previsioni() -> pd.DataFrame:
    """Due partite, con una previsione PERFETTA (prob 1 sull'esito vero)."""
    return pd.DataFrame([
        {"league": "serie_a", "home": "Inter", "away": "Monza",
         "home_win": 1.0, "draw": 0.0, "away_win": 0.0,
         "over_2.5": 1.0, "btts": 0.0, "cs_home": 1.0},
        {"league": "serie_a", "home": "Roma", "away": "Lazio",
         "home_win": 0.0, "draw": 0.0, "away_win": 1.0,
         "over_2.5": 1.0, "btts": 1.0, "cs_home": 0.0},
    ])


def _risultati() -> pd.DataFrame:
    return pd.DataFrame([
        {"league": "serie_a", "home": "Inter", "away": "Monza",
         "home_goals": 3, "away_goals": 0},
        {"league": "serie_a", "home": "Roma", "away": "Lazio",
         "home_goals": 1, "away_goals": 2},
    ])


def test_previsione_perfetta_da_log_loss_zero():
    out = scora(_previsioni(), _risultati(), "test")
    assert out["1x2"]["log_loss"] == pytest.approx(0.0, abs=1e-9)
    assert out["1x2"]["brier"] == pytest.approx(0.0, abs=1e-9)
    assert out["partite_scorate"] == 2


def test_la_baseline_e_peggiore_della_previsione_perfetta():
    out = scora(_previsioni(), _risultati(), "test")
    assert out["1x2"]["log_loss_baseline"] > out["1x2"]["log_loss"]


def test_gli_esiti_binari_sono_quelli_veri():
    out = scora(_previsioni(), _risultati(), "test")["per_mercato"]
    # 3-0 e 1-2: entrambe over 2.5 -> frequenza 1.0
    assert out["over_2.5"]["frequenza_osservata"] == 1.0
    # GG: solo la seconda -> 0.5
    assert out["btts"]["frequenza_osservata"] == 0.5
    # clean sheet casa: solo la prima -> 0.5
    assert out["cs_home"]["frequenza_osservata"] == 0.5


def test_una_partita_senza_risultato_non_viene_scorata():
    """La giornata puo' essere rinviata in parte: si scora cio' che c'e', e il
    conteggio deve DIRE che erano due e ne e' stata scorata una -- altrimenti
    una metrica su meta' campione sembra una metrica sul campione intero."""
    out = scora(_previsioni(), _risultati().iloc[:1], "test")
    assert out["partite_scorate"] == 1
    assert out["partite_congelate"] == 2


def test_nessuna_partita_agganciata_e_un_errore_rumoroso():
    """Se i nomi non combaciano, il merge e' vuoto: deve fermarsi, non
    restituire metriche su zero righe (che sarebbero NaN silenziosi)."""
    ris = _risultati().assign(home="Squadra Inesistente")
    with pytest.raises(SystemExit):
        scora(_previsioni(), ris, "test")


def test_ece_di_una_previsione_perfetta_e_zero():
    p = np.array([1.0, 0.0, 1.0, 0.0])
    y = np.array([1.0, 0.0, 1.0, 0.0])
    assert ece(p, y) == pytest.approx(0.0, abs=1e-9)


def test_ece_di_una_previsione_sistematicamente_alta():
    """40 casi al 90% dichiarato di cui la meta' veri: l'ECE deve valere
    ~0.40, cioe' lo scarto fra dichiarato e osservato."""
    p = np.full(40, 0.9)
    y = np.array([1.0] * 20 + [0.0] * 20)
    assert ece(p, y) == pytest.approx(0.4, abs=1e-9)


# --- le previsioni congelate vere ------------------------------------------

def test_il_congelato_ha_tutti_i_mercati_scorabili():
    """Ogni mercato che lo scoring sa tradurre in esito deve essere davvero
    nel file congelato: dopo il fischio non si aggiunge una colonna."""
    csv = ROOT / "experiments" / "prospettico_2026_27_m1.csv"
    if not csv.exists():                                  # pragma: no cover
        pytest.skip("previsioni non ancora congelate")
    cols = set(pd.read_csv(csv).columns)
    assert set(BINARI) <= cols, f"mancano dal congelato: {sorted(set(BINARI) - cols)}"


def test_il_congelato_e_coerente():
    """Controlli che costano nulla e che, se saltassero, renderebbero il test
    prospettico invalido senza che nessuno se ne accorga: probabilita' in
    [0,1], 1X2 che somma a 1, e le doppie chance coerenti con l'1X2."""
    csv = ROOT / "experiments" / "prospettico_2026_27_m1.csv"
    if not csv.exists():                                  # pragma: no cover
        pytest.skip("previsioni non ancora congelate")
    df = pd.read_csv(csv)
    for m in BINARI:
        assert df[m].between(0, 1).all(), f"{m} fuori da [0,1]"
    somma = df["home_win"] + df["draw"] + df["away_win"]
    assert np.allclose(somma, 1.0, atol=1e-4)
    # P(1X) = P(1) + P(X): la coerenza interna che il progetto rivendica (§1.8)
    assert np.allclose(df["dc_1x"], df["home_win"] + df["draw"], atol=1e-4)
    assert np.allclose(df["dc_12"], df["home_win"] + df["away_win"], atol=1e-4)
    assert np.allclose(df["dc_2x"], df["away_win"] + df["draw"], atol=1e-4)
