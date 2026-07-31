"""Test del database CARRIERE, strato 1 (da `appearances.csv`).

Come per `test_player_stats.py`, due famiglie: guardiani dei numeri e
guardiani della regola R8. Qui i secondi contano ancora di più, perché
«presenze in carriera» è la feature che **per sua natura contiene il futuro**:
un test che si limitasse a controllare i totali passerebbe anche su un
calcolo palesemente look-ahead.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import careers as C


@pytest.fixture(scope="module")
def app() -> pd.DataFrame:
    return C._load_appearances()


@pytest.fixture(scope="module")
def careers(app) -> pd.DataFrame:
    return C.load_careers(app)


# --------------------------------------------------------------------------
# 1 · Guardiani dei numeri
# --------------------------------------------------------------------------

def test_popolazione(app):
    """7.709 giocatori con >=1 presenza nelle 5 leghe dal 2017-07."""
    pop = C.population(app)
    assert len(pop) == 7709
    assert pop.is_unique


def test_copertura(app):
    r = C.coverage_report(app)
    assert r["giocatori"] == 7709
    assert r["competizioni"] == 48           # non 5: e' la scoperta che regge lo strato 1
    assert r["con_presenze_fuori_top5"] == 6580
    assert r["censurati_a_sinistra"] == 1045
    assert r["senza_storia_precedente"] == 2875


def test_struttura_carriere(careers):
    assert careers["player_id"].nunique() == 7709
    assert (careers["appearances"] > 0).all()
    assert (careers["date_to"] >= careers["date_from"]).all()
    assert (careers["fonte"] == C.FONTE_STRATO1).all()
    # una riga e' univoca per giocatore x club x competizione x stagione
    assert not careers.duplicated(
        subset=["player_id", "club_id", "competition_id", "season"]
    ).any()


def test_ogni_riga_dichiara_la_fonte(careers):
    """Regola R2 a livello di RIGA: quando arrivera' lo strato 2 (Wikipedia)
    si dovra' poter distinguere una tappa misurata da una ricostruita."""
    assert "fonte" in careers.columns
    assert careers["fonte"].notna().all()


def test_i_totali_coincidono_con_le_presenze_grezze(app, careers):
    """La tabella e' un'aggregazione: non deve perdere ne' inventare partite."""
    pop = C.population(app)
    grezzo = app[app["player_id"].isin(pop)]
    assert careers["appearances"].sum() == len(grezzo)
    assert careers["goals"].sum() == grezzo["goals"].sum()
    assert careers["minutes"].sum() == grezzo["minutes_played"].sum()


def test_season_taglia_a_luglio():
    """Il taglio a luglio non e' un dettaglio: la coda COVID della 2019-20
    arriva al 2 agosto 2020 e con un taglio a gennaio finirebbe nella
    stagione sbagliata."""
    d = pd.Series(pd.to_datetime(
        ["2019-08-01", "2020-01-15", "2020-06-30", "2020-08-02", "2020-09-01"]
    ))
    s = C.season_of(d)
    assert list(s) == ["2019-20", "2019-20", "2019-20", "2020-21", "2020-21"]


# --------------------------------------------------------------------------
# 2 · Guardiani della regola R8 (anti look-ahead) — i test che contano
# --------------------------------------------------------------------------

def test_career_before_esclude_tutto_cio_che_viene_dopo(app):
    """IL test. `career_before(D)` non deve contenere una sola partita >= D."""
    for data in ("2018-01-01", "2020-06-01", "2023-09-15"):
        cb = C.career_before(data, app)
        atteso = app[app["date"] < pd.Timestamp(data)]
        assert cb["appearances_before"].sum() == len(atteso), (
            f"{data}: il totale non coincide con le sole partite precedenti"
        )
        # e nessun giocatore che ha esordito DOPO puo' comparire
        esordi = app.groupby("player_id")["date"].min()
        dopo = set(esordi[esordi >= pd.Timestamp(data)].index)
        assert not (set(cb.index) & dopo), f"{data}: presenti giocatori non ancora esorditi"


def test_career_before_e_monotona(app):
    """Una carriera non si accorcia. Se il taglio fosse sbagliato (per esempio
    su un confronto `<=` contro `<` mal gestito) la monotonia si romperebbe."""
    a = C.career_before("2019-01-01", app)
    b = C.career_before("2021-01-01", app)
    comuni = a.index.intersection(b.index)
    assert (b.loc[comuni, "appearances_before"] >= a.loc[comuni, "appearances_before"]).all()
    assert (b.loc[comuni, "goals_before"] >= a.loc[comuni, "goals_before"]).all()


def test_career_before_e_stretta_non_inclusiva(app):
    """Il confine e' `< as_of`, non `<=`: la partita del giorno stesso e' la
    partita da prevedere, e non puo' entrare nella sua stessa feature."""
    giorno = pd.Timestamp("2019-03-02")
    quel_giorno = int((app["date"] == giorno).sum())
    assert quel_giorno > 0, "scegliere un giorno con partite per rendere il test vero"
    prima = C.career_before(giorno, app)["appearances_before"].sum()
    dopo = C.career_before(giorno + pd.Timedelta(days=1), app)["appearances_before"].sum()
    assert dopo - prima == quel_giorno


def test_censored_left_marca_chi_e_tagliato_dal_bordo(app):
    """Chi ha la prima presenza al bordo del dataset non e' un esordiente:
    i suoi totali sono un LIMITE INFERIORE. Non marcarlo e' l'errore che e'
    gia' costato 155 allenatori su 496 (audit §D.2)."""
    cb = C.career_before("2026-01-01", app)
    assert cb["censored_left"].sum() > 0
    assert (cb.loc[cb["censored_left"], "first_appearance"] <= C.CENSORING_CUTOFF).all()
    assert (cb.loc[~cb["censored_left"], "first_appearance"] > C.CENSORING_CUTOFF).all()


def test_top5_e_altre_sommano_al_totale(app):
    cb = C.career_before("2024-01-01", app)
    assert (
        cb["top5_appearances_before"] + cb["other_appearances_before"]
        == cb["appearances_before"]
    ).all()


def test_career_before_filtra_per_giocatore(app):
    ids = list(C.population(app)[:50])
    cb = C.career_before("2023-01-01", app, player_ids=ids)
    assert set(cb.index) <= set(ids)
