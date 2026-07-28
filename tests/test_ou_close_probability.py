"""Test di `loader.ou_close_probability` (Fase 114).

La funzione unisce due cose che il progetto tiene deliberatamente separate:
il PREZZO reale (quote di mercato) e la STIMA (ricostruzione di modello). Il
rischio non e' un errore di calcolo: e' che la separazione si perda per
strada e una stima finisca per essere trattata come un prezzo -- il "finto
pieno" della regola R6, e la violazione di data/estimates/README.md. Questi
test sorvegliano il confine, non l'aritmetica.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import database, loader


@pytest.fixture(scope="module")
def snap():
    p = database.snapshot_path("serie_a")
    if not p.exists():
        pytest.skip("snapshot non presente")
    return database.read_snapshot(p)


def test_le_colonne_quota_non_vengono_mai_toccate(snap):
    """La regola non negoziabile: una stima non entra MAI in una colonna
    quota (data/estimates/README.md). Le quote in uscita devono essere
    identiche, NaN compresi."""
    out = loader.ou_close_probability(snap)
    for c in ("odds_over25", "odds_under25"):
        pd.testing.assert_series_equal(out[c], snap[c])


def test_ogni_riga_dichiara_la_propria_provenienza(snap):
    out = loader.ou_close_probability(snap)
    assert set(out["p_over25_close_fonte"].unique()) <= {"reale", "stima", "assente"}
    # dove c'e' la probabilita' la fonte non puo' essere "assente", e viceversa
    assert not ((out["p_over25_close"].notna()) & (out["p_over25_close_fonte"] == "assente")).any()
    assert not ((out["p_over25_close"].isna()) & (out["p_over25_close_fonte"] != "assente")).any()


def test_dove_il_prezzo_esiste_la_fonte_e_reale_e_il_valore_e_il_devig(snap):
    """Il dato reale ha la precedenza sulla stima, sempre: se il mercato c'e',
    si usa quello."""
    out = loader.ou_close_probability(snap)
    reale = out["odds_over25"].notna() & out["odds_under25"].notna()
    assert (out.loc[reale, "p_over25_close_fonte"] == "reale").all()
    atteso = (1 / out.loc[reale, "odds_over25"]) / (
        1 / out.loc[reale, "odds_over25"] + 1 / out.loc[reale, "odds_under25"])
    assert np.allclose(out.loc[reale, "p_over25_close"], atteso)


def test_usa_stime_false_lascia_il_buco_scoperto(snap):
    """Chi non vuole stime deve poterle rifiutare e vedere il buco vero:
    e' la differenza fra 'non lo so' e 'te lo ricostruisco'."""
    out = loader.ou_close_probability(snap, usa_stime=False)
    assert "stima" not in set(out["p_over25_close_fonte"].unique())
    reale = snap["odds_over25"].notna() & snap["odds_under25"].notna()
    assert out.loc[~reale, "p_over25_close"].isna().all()


def test_le_stime_coprono_solo_il_buco_dichiarato_2017_19(snap):
    """Le stime esistono per il buco sistemico 2017-19 e per nient'altro: se
    comparissero altrove, il join starebbe sbagliando chiave."""
    out = loader.ou_close_probability(snap)
    stimate = out[out["p_over25_close_fonte"] == "stima"]
    assert set(stimate["season"].astype(str).unique()) <= {"1718", "1819"}


def test_le_probabilita_sono_probabilita(snap):
    out = loader.ou_close_probability(snap)
    v = out["p_over25_close"].dropna()
    assert v.between(0, 1).all()
    assert len(v) > 0
