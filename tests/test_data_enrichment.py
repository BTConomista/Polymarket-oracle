"""Test dell'arricchimento dati: xG Understat, valori rosa e assenze TM.

Tre famiglie di controlli:
  1. allineamento nomi squadra/giocatore tra fonti (alias, normalizzazione);
  2. correttezza del join xG su dati sintetici (nessuna partita persa,
     orfani rilevati, idempotenza);
  3. integrita' dello snapshot arricchito versionato (offline, nessuna rete).
"""

import numpy as np
import pandas as pd
import pytest

from src.data import database, sources, understat
from src.data.transfermarkt import normalize_name
from src.data.understat import XG_COLUMNS


# ---------------------------------------------------------------- 1. nomi

def test_alias_squadre_understat():
    """I nomi Understat divergenti vanno mappati sui canonici football-data."""
    assert sources.canonical_team("AC Milan") == "Milan"
    assert sources.canonical_team("Parma Calcio 1913") == "Parma"
    assert sources.canonical_team("SPAL 2013") == "Spal"
    # I canonici restano invariati.
    assert sources.canonical_team("Inter") == "Inter"
    assert sources.canonical_team("Verona") == "Verona"


def test_normalize_name_giocatori():
    assert normalize_name("Danilo D&#039;Ambrosio") == "danilo d ambrosio"
    assert normalize_name("Nicolás González") == "nicolas gonzalez"
    assert normalize_name("Danilo (2)") == "danilo"            # suffisso TM
    assert normalize_name("Simon Kjær") == "simon kjaer"       # translitterazione
    assert normalize_name("Kenan Yıldız") == "kenan yildiz"
    assert normalize_name("  Zlatan   Ibrahimović ") == "zlatan ibrahimovic"


def test_map_players_inversione_nome_cognome(monkeypatch):
    """Fase 63: Understat scrive "Djené Dakonam", Transfermarkt "Dakonam Djené"
    (stesso insieme di token, ordine diverso): il match deve riuscire via lo
    stadio token_sort — prima del fix il giocatore restava unmatched (25960
    minuti persi nel solo caso reale di Getafe)."""
    from src.data import transfermarkt as tm

    names = pd.DataFrame({"tm_id": [221150, 999],
                          "name_norm": ["dakonam djene", "altro giocatore"]})
    positions = {221150: "Defender", 999: "Attack"}
    valuations = {221150: (np.array(["2020-01-01"], dtype="datetime64[ns]"),
                           np.array([5e6]))}
    monkeypatch.setattr(tm, "_load_name_index",
                        lambda force=False: (names, positions))
    monkeypatch.setattr(tm, "_load_valuations", lambda force=False: valuations)

    squads = pd.DataFrame({
        "season": ["2223"], "team": ["Getafe"],
        "player_id": ["u1"], "player_name": ["Djené Dakonam"],
        "position": ["D"], "minutes": [3000.0],
    })
    mapping, stats = tm.map_players(squads)
    assert stats["token_sort"] == 1
    assert int(mapping.iloc[0]["tm_id"]) == 221150


def test_map_players_token_sort_ambiguo_non_aggancia(monkeypatch):
    """Due persone DIVERSE con gli stessi token (in ordini diversi) -> il
    token_sort e' ambiguo -> NIENTE match (meglio un buco dichiarato che un
    omonimo sbagliato). Serve un nome a 3 token: con 2 token uno dei due
    ordini coincide sempre col match esatto."""
    from src.data import transfermarkt as tm

    names = pd.DataFrame({"tm_id": [1, 2],
                          "name_norm": ["ana bruno carlos", "bruno ana carlos"]})
    positions = {1: "Defender", 2: "Defender"}
    dates = np.array(["2020-01-01"], dtype="datetime64[ns]")
    valuations = {1: (dates, np.array([1e6])), 2: (dates, np.array([2e6]))}
    monkeypatch.setattr(tm, "_load_name_index",
                        lambda force=False: (names, positions))
    monkeypatch.setattr(tm, "_load_valuations", lambda force=False: valuations)

    squads = pd.DataFrame({
        "season": ["2223"], "team": ["X"],
        "player_id": ["u1"], "player_name": ["Carlos Bruno Ana"],
        "position": ["D"], "minutes": [900.0],
    })
    mapping, stats = tm.map_players(squads)
    assert stats["token_sort"] == 0            # ambiguo: non deve scattare
    assert pd.isna(mapping.iloc[0]["tm_id"]) or stats["unmatched"] == 0
    # (il fallback per COGNOME puo' legittimamente agganciare o no; il punto
    #  del test e' che il token_sort ambiguo non scelga a caso)


# ------------------------------------------------------------ 2. join xG

def _partite_sintetiche() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-08-20", "2024-08-21"]),
        "season": ["2425", "2425"],
        "league": ["serie_a", "serie_a"],
        "home_team": ["Milan", "Parma"],
        "away_team": ["Inter", "Spal"],
        "home_goals": [1, 0],
        "away_goals": [1, 2],
    })


def _xg_sintetico() -> pd.DataFrame:
    riga = {c: 1.0 for c in XG_COLUMNS}
    return pd.DataFrame([
        # nomi come li fornirebbe Understat: alias da risolvere
        {"season": "2425", "home_team": "Milan", "away_team": "Inter",
         "understat_date": pd.Timestamp("2024-08-20"), **riga},
    ])


def test_add_xg_join_senza_perdite(monkeypatch):
    """Il join non deve perdere partite; dove manca l'xG restano NaN."""
    monkeypatch.setattr(understat, "season_xg",
                        lambda code, league="serie_a", force=False: _xg_sintetico())
    out = understat.add_xg(_partite_sintetiche())
    assert len(out) == 2                                  # nessuna riga persa
    assert out.loc[out.home_team == "Milan", "home_xg"].item() == 1.0
    assert out.loc[out.home_team == "Parma", "home_xg"].isna().all()


def test_add_xg_idempotente(monkeypatch):
    monkeypatch.setattr(understat, "season_xg",
                        lambda code, league="serie_a", force=False: _xg_sintetico())
    una = understat.add_xg(_partite_sintetiche())
    due = understat.add_xg(una)                           # seconda passata
    pd.testing.assert_frame_equal(una, due)


def test_add_xg_duplicati_rifiutati(monkeypatch):
    doppio = pd.concat([_xg_sintetico()] * 2, ignore_index=True)
    monkeypatch.setattr(understat, "season_xg",
                        lambda code, league="serie_a", force=False: doppio)
    with pytest.raises(ValueError):
        understat.add_xg(_partite_sintetiche())


# ------------------------------------------- 3. snapshot arricchito (offline)

COLONNE_BASE = [
    "date", "season", "league", "home_team", "away_team",
    "home_goals", "away_goals", "result", "home_sot", "away_sot",
    "odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25",
]
COLONNE_NUOVE = XG_COLUMNS + [
    "home_squad_value", "away_squad_value",
    "home_absent_count_est", "away_absent_count_est",
    "home_absent_value_est", "away_absent_value_est",
]


@pytest.fixture(scope="module")
def snapshot() -> pd.DataFrame:
    if not database.SNAPSHOT_PATH.exists():
        pytest.skip("snapshot non presente")
    return database.read_snapshot()


def test_snapshot_schema(snapshot):
    """Colonne originali intatte (e per prime), nuove colonne presenti."""
    assert list(snapshot.columns[: len(COLONNE_BASE)]) == COLONNE_BASE
    assert set(COLONNE_NUOVE) <= set(snapshot.columns)


def test_snapshot_chiave_unica(snapshot):
    assert not snapshot.duplicated(["season", "home_team", "away_team"]).any()


def test_snapshot_xg_completo(snapshot):
    """xG presente per OGNI partita di OGNI stagione (380/380)."""
    per_stagione = snapshot.groupby("season")["home_xg"].apply(
        lambda s: s.notna().all()
    )
    assert per_stagione.all(), per_stagione[~per_stagione]
    assert snapshot[["away_xg", "home_npxg", "away_npxg"]].notna().all().all()


def test_snapshot_xg_plausibile(snapshot):
    assert snapshot["home_xg"].between(0, 8).all()
    assert snapshot["away_xg"].between(0, 8).all()
    # npxG non puo' superare l'xG totale della stessa squadra.
    assert (snapshot["home_npxg"] <= snapshot["home_xg"] + 1e-9).all()
    # In media il fattore campo deve vedersi anche nell'xG.
    assert snapshot["home_xg"].mean() > snapshot["away_xg"].mean()


def test_snapshot_valori_rosa(snapshot):
    """Copertura e ordini di grandezza sensati (niente look-ahead garantito a
    monte: valutazioni <= 1 settembre della stagione). Dalla Fase 67 la fonte
    e' player-scores: 100% sulle stagioni concluse, buchi onesti solo nella
    stagione in corso."""
    entrambe = (snapshot["home_squad_value"].notna()
                & snapshot["away_squad_value"].notna())
    per_stagione = entrambe.groupby(snapshot["season"].astype(str)).mean()
    concluse = per_stagione.drop(index="2526", errors="ignore")
    assert (concluse >= 0.95).all(), per_stagione
    valori = pd.concat([snapshot["home_squad_value"],
                        snapshot["away_squad_value"]]).dropna()
    assert valori.between(10e6, 1500e6).all()


def test_snapshot_assenze_stimate(snapshot):
    conteggi = pd.concat([snapshot["home_absent_count_est"],
                          snapshot["away_absent_count_est"]]).dropna()
    assert conteggi.between(0, 25).all()
    valori = pd.concat([snapshot["home_absent_value_est"],
                        snapshot["away_absent_value_est"]]).dropna()
    assert (valori >= 0).all()


def test_snapshot_base_invariata(snapshot):
    """La parte congelata non deve cambiare con l'arricchimento."""
    assert len(snapshot) == 3420
    assert snapshot.groupby("season").size().eq(380).all()
    assert snapshot["home_goals"].between(0, 15).all()


# --------------------- 4. valore rosa/assenze generalizzati (Fase 59) --------
# Le rose per Premier/Liga vengono dai bundle Understat locali (mirror Understat
# per-stagione sparito, Fase 14) mentre Transfermarkt e' raggiunto via rete
# (mirror diverso, ancora vivo): vedi transfermarkt.add_squad_values(squads=...)
# e scripts/build_league_snapshot.py --enrich.

# Copertura minima onesta per lega (stagioni CONCLUSE; la 2526 in corso e'
# testata a parte in test_player_scores). Dalla Fase 67 la fonte e'
# player-scores: praticamente piena ovunque.
_MIN_COVERAGE_PER_LEGA = {"premier_league": 0.95, "la_liga": 0.95}


@pytest.fixture(params=["premier_league", "la_liga"])
def altra_lega(request):
    return request.param


@pytest.fixture
def altro_snapshot(altra_lega):
    path = database.snapshot_path(altra_lega)
    if not path.exists():
        pytest.skip(f"snapshot {altra_lega} non costruito")
    snap = database.read_snapshot(path)
    if "home_squad_value" not in snap.columns:
        pytest.skip(f"{altra_lega}: valore rosa non ancora costruito "
                    f"(build_league_snapshot.py --enrich)")
    return snap


def test_altra_lega_valori_rosa_plausibili(altra_lega, altro_snapshot):
    entrambe = (altro_snapshot["home_squad_value"].notna()
                & altro_snapshot["away_squad_value"].notna())
    per_stagione = entrambe.groupby(
        altro_snapshot["season"].astype(str)).mean()
    concluse = per_stagione.drop(index="2526", errors="ignore")
    soglia = _MIN_COVERAGE_PER_LEGA[altra_lega]
    assert (concluse >= soglia).all(), per_stagione
    valori = pd.concat([altro_snapshot["home_squad_value"],
                        altro_snapshot["away_squad_value"]]).dropna()
    assert valori.between(10e6, 1500e6).all()


def test_altra_lega_assenze_stimate_plausibili(altro_snapshot):
    conteggi = pd.concat([altro_snapshot["home_absent_count_est"],
                          altro_snapshot["away_absent_count_est"]]).dropna()
    assert conteggi.between(0, 25).all()
    valori = pd.concat([altro_snapshot["home_absent_value_est"],
                        altro_snapshot["away_absent_value_est"]]).dropna()
    assert (valori >= 0).all()
