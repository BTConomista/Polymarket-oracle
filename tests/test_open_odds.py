"""Test delle quote di APERTURA (Fase 14): estrazione, join, metriche CLV.

Tre famiglie di controlli:
  1. estrazione dal CSV grezzo: le colonne *_open NON devono MAI ripiegare
     sulle colonne di chiusura (*C*) — meglio NaN che mercato-vs-se-stesso;
  2. aggancio allo snapshot esistente (add_open_odds): join corretto,
     integrita' sui gol, righe senza aggancio dichiarate (NaN);
  3. metriche: chiavi *open* e CLV presenti solo se il df le ha
     (retrocompatibilita' coi run storici), e corrette su un caso giocattolo.
"""

import numpy as np
import pandas as pd
import pytest

from src.data import loader
from src.data.loader import _normalize
from src.data.sources import LEAGUES
from src.evaluation import experiment_log


# ------------------------------------------------- 1. estrazione dal grezzo

def _raw_sintetico(**extra) -> pd.DataFrame:
    base = {
        "Date": ["20/08/2024"],
        "HomeTeam": ["Milan"], "AwayTeam": ["Inter"],
        "FTHG": [1], "FTAG": [1], "FTR": ["D"],
        "HST": [5], "AST": [4],
    }
    return pd.DataFrame(base | extra)


def test_normalize_estrae_apertura_e_chiusura():
    raw = _raw_sintetico(AvgH=[2.10], AvgD=[3.30], AvgA=[3.60],
                         AvgCH=[2.00], AvgCD=[3.40], AvgCA=[3.80])
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    assert out["odds_home"].item() == 2.00        # chiusura preferita
    assert out["odds_home_open"].item() == 2.10   # apertura = colonna senza C
    assert out["odds_away_open"].item() == 3.60


def test_apertura_non_ripiega_mai_sulla_chiusura():
    """Solo colonne di chiusura nel grezzo -> apertura NaN, non chiusura."""
    raw = _raw_sintetico(AvgCH=[2.00], AvgCD=[3.40], AvgCA=[3.80])
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    assert out["odds_home"].item() == 2.00
    assert np.isnan(out["odds_home_open"].item())
    assert np.isnan(out["odds_draw_open"].item())


def test_apertura_fallback_interno_bet365():
    """Senza Avg pre-match si ripiega su B365 pre-match (mai su *C*)."""
    raw = _raw_sintetico(B365H=[2.15], B365D=[3.2], B365A=[3.5], AvgCH=[2.0])
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    assert out["odds_home_open"].item() == 2.15


# --------------------------------------------- 2. aggancio allo snapshot

def _snapshot_sintetico() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-08-20", "2024-08-21"]),
        "season": ["2425", "2425"],
        "league": ["serie_a", "serie_a"],
        "home_team": ["Milan", "Parma"],
        "away_team": ["Inter", "Spal"],
        "home_goals": [1, 0], "away_goals": [1, 2],
        "result": ["D", "A"],
        "odds_home": [2.0, 2.5],
    })


def _monkeypatch_grezzo(monkeypatch, tmp_path, raw: pd.DataFrame):
    path = tmp_path / "serie_a_2425.csv"
    raw.to_csv(path, index=False)
    monkeypatch.setattr(loader, "download_season",
                        lambda code, league, force=False: path)


def test_add_open_odds_join(monkeypatch, tmp_path):
    raw = pd.DataFrame({
        "Date": ["20/08/2024"], "HomeTeam": ["AC Milan"], "AwayTeam": ["Inter"],
        "FTHG": [1], "FTAG": [1], "FTR": ["D"],
        "AvgH": [2.10], "AvgD": [3.30], "AvgA": [3.60],
    })
    _monkeypatch_grezzo(monkeypatch, tmp_path, raw)
    out = loader.add_open_odds(_snapshot_sintetico())
    assert len(out) == 2                                   # nessuna riga persa
    milan = out[out.home_team == "Milan"]
    assert milan["odds_home_open"].item() == 2.10          # alias risolto
    assert milan["odds_home"].item() == 2.0                # esistenti intatte
    parma = out[out.home_team == "Parma"]
    assert parma["odds_home_open"].isna().all()            # niente aggancio: NaN


def test_add_open_odds_gol_diversi_rifiutati(monkeypatch, tmp_path):
    """Gol del grezzo != snapshot = join sbagliato/fonte cambiata -> errore."""
    raw = pd.DataFrame({
        "Date": ["20/08/2024"], "HomeTeam": ["Milan"], "AwayTeam": ["Inter"],
        "FTHG": [3], "FTAG": [0], "FTR": ["H"],           # gol sballati
        "AvgH": [2.10], "AvgD": [3.30], "AvgA": [3.60],
    })
    _monkeypatch_grezzo(monkeypatch, tmp_path, raw)
    with pytest.raises(ValueError, match="GOL"):
        loader.add_open_odds(_snapshot_sintetico())


# ------------------------------------------------------ 3. metriche e CLV

def _backtest_df(con_open: bool) -> pd.DataFrame:
    df = pd.DataFrame({
        "result": ["H", "D", "A", "H"],
        "m_home": [0.60, 0.30, 0.25, 0.55],
        "m_draw": [0.25, 0.32, 0.30, 0.25],
        "m_away": [0.15, 0.38, 0.45, 0.20],
        "is_over": [1, 0, 1, 0],
        "m_over": [0.6, 0.4, 0.55, 0.45],
        "odds_home": [2.0, 3.0, 3.8, 2.1],
        "odds_draw": [3.4, 3.2, 3.4, 3.3],
        "odds_away": [3.8, 2.4, 2.0, 3.6],
        "odds_over": [1.9, 2.1, 1.85, 2.05],
        "odds_under": [1.9, 1.7, 1.95, 1.75],
    })
    if con_open:
        # Apertura piu' larga sulla casa: il modello ha edge vs open SOLO
        # sulle righe 0 e 3, e li' la chiusura si muove verso il modello
        # (CLV > 0); la riga 1 non genera selezioni (nessun edge > 5%).
        df["odds_home_open"] = [2.4, 3.1, 3.9, 2.5]
        df["odds_draw_open"] = [3.3, 3.1, 3.3, 3.2]
        df["odds_away_open"] = [3.1, 2.35, 2.0, 3.0]
        df["odds_over_open"] = [2.0, 2.15, 1.9, 2.1]
        df["odds_under_open"] = [1.8, 1.65, 1.9, 1.7]
    return df


def test_compute_metrics_retrocompatibile():
    """Senza colonne *_open il dizionario resta identico a prima."""
    m = experiment_log.compute_metrics(_backtest_df(con_open=False))
    assert "x2_market_logloss" in m
    assert not any(k.endswith("open_logloss") for k in m)
    assert "clv_n" not in m


def test_compute_metrics_con_apertura():
    m = experiment_log.compute_metrics(_backtest_df(con_open=True))
    for chiave in ["x2_market_open_logloss", "x2_market_open_brier",
                   "ou_market_open_logloss", "value_bet_open_n",
                   "clv_n", "clv_mean_prob", "clv_positive_share"]:
        assert chiave in m, chiave
    # Le metriche di chiusura devono restare identiche al caso senza open.
    base = experiment_log.compute_metrics(_backtest_df(con_open=False))
    assert m["x2_market_logloss"] == base["x2_market_logloss"]
    assert m["value_bet_n"] == base["value_bet_n"]


def test_clv_positivo_quando_chiusura_si_muove_verso_il_modello():
    n, media, quota_pos = experiment_log.clv_stats(_backtest_df(con_open=True))
    assert n >= 1
    assert media > 0          # la chiusura accorcia la casa: linea verso di noi
    assert quota_pos == 1.0


def test_clv_senza_selezioni():
    df = _backtest_df(con_open=True)
    # Modello identico all'apertura -> nessun edge -> nessuna selezione.
    open_p = np.array([experiment_log.metrics.devig_1x2(r.odds_home_open,
                                                        r.odds_draw_open,
                                                        r.odds_away_open)
                       for _, r in df.iterrows()])
    df[["m_home", "m_draw", "m_away"]] = open_p
    n, media, quota_pos = experiment_log.clv_stats(df)
    assert n == 0 and np.isnan(media)


# ---------------------------------------- 4. snapshot esteso (se presente)

@pytest.fixture(scope="module")
def snapshot():
    from src.data import database
    if not database.SNAPSHOT_PATH.exists():
        pytest.skip("snapshot non presente")
    snap = database.read_snapshot()
    if "odds_home_open" not in snap.columns:
        pytest.skip("snapshot senza quote di apertura (build_database --open-odds)")
    return snap


def test_snapshot_apertura_copertura(snapshot):
    """Copertura piena nelle stagioni di test (2020-21+)."""
    recenti = snapshot[snapshot["season"].isin(
        ["2021", "2122", "2223", "2324", "2425", "2526"])]
    assert recenti["odds_home_open"].notna().mean() >= 0.95


def test_snapshot_apertura_distinta_dalla_chiusura(snapshot):
    """Nelle stagioni con chiusura vera le due linee devono differire spesso:
    se coincidono (quasi) sempre, l'estrazione ha ripiegato sulla chiusura."""
    recenti = snapshot[snapshot["season"].isin(
        ["2021", "2122", "2223", "2324", "2425", "2526"])].dropna(
        subset=["odds_home", "odds_home_open"])
    diverse = (recenti["odds_home"] != recenti["odds_home_open"]).mean()
    assert diverse > 0.5, f"solo {diverse:.0%} di quote distinte open vs close"


def test_snapshot_apertura_plausibile(snapshot):
    quote = pd.concat([snapshot["odds_home_open"], snapshot["odds_draw_open"],
                       snapshot["odds_away_open"]]).dropna()
    assert (quote > 1.0).all() and (quote < 100).all()
