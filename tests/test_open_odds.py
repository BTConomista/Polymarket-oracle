"""Test delle quote di APERTURA (Fase 14): estrazione, join, metriche CLV.

Tre famiglie di controlli:
  1. estrazione dal CSV grezzo: le colonne *_open NON devono MAI ripiegare
     sulle colonne di chiusura (*C*) — meglio NaN che mercato-vs-se-stesso —
     e sono valorizzate SOLO dove la chiusura proviene da una colonna *C*
     (audit Fase 15: se la chiusura e' il fallback pre-match, open==close
     per costruzione e la riga va esclusa, non contaminata);
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


def test_quota_media_inquinata_ripiega_sul_livello_successivo():
    """Fase 58 (audit dati): un caso reale (La Liga 2025-08-16, Mallorca-Barcelona)
    ha AvgCH/AvgCD/AvgCA singolarmente validi (>1.0) ma con overround implicito
    0.929 -- impossibile per un book vero, sintomo di un bookmaker anomalo
    incluso nella media della fonte. La scelta per riga deve scartare IN BLOCCO
    il livello preferito e ripiegare su B365CH/B365CD/B365CA (livello successivo),
    mai un solo lato aggiustato a mano."""
    raw = _raw_sintetico(AvgCH=[8.70], AvgCD=[5.79], AvgCA=[1.56],
                         B365CH=[9.50], B365CD=[5.50], B365CA=[1.30])
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    assert out["odds_home"].item() == 9.50
    assert out["odds_draw"].item() == 5.50
    assert out["odds_away"].item() == 1.30
    overround = 1 / 9.50 + 1 / 5.50 + 1 / 1.30
    assert overround >= 1.0


def test_quota_valida_non_scartata_da_overround_ok():
    """Controllo di non-regressione: un overround normale (>1) non deve
    innescare il ripiego -- solo il caso impossibile lo fa."""
    raw = _raw_sintetico(AvgCH=[2.00], AvgCD=[3.40], AvgCA=[3.80],
                         B365CH=[1.90], B365CD=[3.10], B365CA=[3.50])
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    assert out["odds_home"].item() == 2.00
    assert out["odds_draw"].item() == 3.40
    assert out["odds_away"].item() == 3.80


def test_apertura_fallback_interno_bet365():
    """Senza Avg pre-match si ripiega su B365 pre-match (mai su *C*)."""
    raw = _raw_sintetico(B365H=[2.15], B365D=[3.2], B365A=[3.5], AvgCH=[2.0])
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    assert out["odds_home_open"].item() == 2.15


def test_chiusura_pinnacle_e_apertura_pinnacle_prime_stagioni():
    """Fase 61: le prime 2 stagioni (2017-18, 2018-19) NON hanno la chiusura
    aggregata (AvgC*/B365C*) ma hanno Pinnacle apertura (PS*) e chiusura (PSC*).
    Il loader deve usare PSC* come CHIUSURA (una chiusura VERA, non la pre-match
    spacciata) e PS* come APERTURA -- un CLV pulito Pinnacle->Pinnacle."""
    raw = _raw_sintetico(
        PSH=[2.20], PSD=[3.30], PSA=[3.50],       # Pinnacle apertura
        PSCH=[2.05], PSCD=[3.45], PSCA=[3.70],    # Pinnacle chiusura
        # nessuna colonna Avg*/AvgC*/B365C*: e' lo scenario 2017-19
    )
    out = _normalize(raw, "1718", LEAGUES["serie_a"])
    assert out["odds_home"].item() == 2.05        # chiusura = Pinnacle closing
    assert out["odds_away"].item() == 3.70
    assert out["odds_home_open"].item() == 2.20   # apertura = Pinnacle pre-match
    assert out["odds_away_open"].item() == 3.50
    # apertura e chiusura DEVONO differire (altrimenti niente CLV)
    assert out["odds_home"].item() != out["odds_home_open"].item()


def test_pinnacle_non_tocca_le_stagioni_con_media():
    """Non-regressione: dove la media di chiusura (AvgC*) c'e' (2019-20+), resta
    lei la scelta -- Pinnacle e' solo il ripiego per le stagioni che ne sono
    prive, e non deve mai scavalcare la media."""
    raw = _raw_sintetico(
        AvgCH=[2.00], AvgCD=[3.40], AvgCA=[3.80],  # chiusura aggregata
        AvgH=[2.10], AvgD=[3.30], AvgA=[3.60],     # apertura aggregata
        PSCH=[1.95], PSCD=[3.50], PSCA=[3.90],     # Pinnacle presente ma NON scelto
        PSH=[2.15], PSD=[3.25], PSA=[3.55],
    )
    out = _normalize(raw, "2223", LEAGUES["serie_a"])
    assert out["odds_home"].item() == 2.00         # media, non Pinnacle
    assert out["odds_home_open"].item() == 2.10    # media, non Pinnacle


def test_apertura_oscurata_dove_la_chiusura_e_fallback():
    """Riga SENZA colonne *C*: la chiusura ripiega sulla pre-match, quindi
    open==close per costruzione -> l'apertura va oscurata (NaN), riga per riga
    (audit Fase 15: un CLV=0 spurio verrebbe contato come negativo)."""
    raw = pd.DataFrame({
        "Date": ["20/08/2024", "21/08/2024"],
        "HomeTeam": ["Milan", "Parma"], "AwayTeam": ["Inter", "Lecce"],
        "FTHG": [1, 0], "FTAG": [1, 2], "FTR": ["D", "A"],
        "HST": [5, 3], "AST": [4, 6],
        "AvgH": [2.10, 2.60], "AvgD": [3.30, 3.10], "AvgA": [3.60, 2.90],
        # Chiusura vera solo sulla prima riga.
        "AvgCH": [2.00, np.nan], "AvgCD": [3.40, np.nan], "AvgCA": [3.80, np.nan],
    })
    out = _normalize(raw, "2425", LEAGUES["serie_a"])
    milan = out[out.home_team == "Milan"].iloc[0]
    parma = out[out.home_team == "Parma"].iloc[0]
    assert milan["odds_home_open"] == 2.10          # chiusura da colonna C: ok
    assert milan["odds_home"] == 2.00
    assert parma["odds_home"] == 2.60               # chiusura = fallback...
    assert np.isnan(parma["odds_home_open"])        # ...quindi apertura oscurata


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
        # Chiusura vera presente: senza colonne *C* l'apertura resterebbe
        # oscurata (vedi test_apertura_oscurata_dove_la_chiusura_e_fallback).
        "AvgCH": [2.00], "AvgCD": [3.40], "AvgCA": [3.80],
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
                   "x2_model_open_logloss", "ou_market_open_logloss",
                   "ou_model_open_logloss", "value_bet_open_n",
                   "clv_n", "clv_mean_prob", "clv_positive_share"]:
        assert chiave in m, chiave
    # Le metriche di chiusura devono restare identiche al caso senza open.
    base = experiment_log.compute_metrics(_backtest_df(con_open=False))
    assert m["x2_market_logloss"] == base["x2_market_logloss"]
    assert m["value_bet_n"] == base["value_bet_n"]


def test_metriche_modello_vs_apertura_sulle_stesse_righe():
    """Audit Fase 15: il gap modello-vs-apertura dal registro deve confrontare
    le STESSE righe. Con una riga senza quote di apertura, x2_model_open_logloss
    va calcolato sul sottoinsieme con apertura, non su tutte le partite."""
    df = _backtest_df(con_open=True)
    df.loc[2, ["odds_home_open", "odds_draw_open", "odds_away_open"]] = np.nan
    df.loc[2, ["odds_over_open", "odds_under_open"]] = np.nan
    m = experiment_log.compute_metrics(df)
    sub = experiment_log.compute_metrics(df.drop(index=2).reset_index(drop=True))
    assert m["x2_model_open_logloss"] == pytest.approx(sub["x2_model_open_logloss"])
    assert m["x2_model_open_logloss"] != pytest.approx(m["x2_model_logloss"])
    assert m["ou_model_open_logloss"] == pytest.approx(sub["ou_model_open_logloss"])


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


def test_snapshot_apertura_recuperata_prime_stagioni(snapshot):
    """Fase 61: anche 2017-18 e 2018-19 hanno ora l'apertura 1X2 (Pinnacle),
    non piu' NaN come prima (la chiusura aggregata mancava, ma PSC*/PS* c'erano
    e non venivano usate)."""
    vecchie = snapshot[snapshot["season"].isin(["1718", "1819"])]
    if vecchie.empty:
        pytest.skip("stagioni 2017-19 non presenti nello snapshot")
    assert vecchie["odds_home_open"].notna().mean() >= 0.95
    # e le due linee (apertura Pinnacle vs chiusura Pinnacle) differiscono
    sub = vecchie.dropna(subset=["odds_home", "odds_home_open"])
    assert (sub["odds_home"] != sub["odds_home_open"]).mean() > 0.5


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
