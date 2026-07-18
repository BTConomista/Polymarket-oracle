"""Test del calendario di club completo e della congestione vera (fixtures.py).

Famiglie di controlli:
  1. aggancio nomi squadra tra fonti (alias europei/coppa -> canonici);
  2. parser di date openfootball (anno ereditato, reset di girone, rollover
     Gen->year1, finali di Agosto post-COVID);
  3. parser partite Europa (filtro ITA, home_away/opponent, due italiane);
  4. parser Coppa Italia nei DUE formati (con " v " e col punteggio in mezzo);
  5. Serie A dallo snapshot: nessuna partita persa (2 righe per partita);
  6. rest_days_full: partita nascosta catturata, NIENTE look-ahead, cap, NaN,
     flag midweek_europe;
  7. integrita' offline dello snapshot arricchito e di data/club_fixtures.csv.
"""

import numpy as np
import pandas as pd
import pytest

from src.data import database, fixtures, loader, sources
from src.data.fixtures import (
    FIXTURE_COLUMNS,
    REST_FULL_COLUMNS,
    _DateTracker,
    _serie_a_rows,
    add_rest_days_full,
    parse_cup,
    parse_europe,
)


# --------------------------------------------------------------- 1. nomi

def test_alias_squadre_europa_coppa():
    """Le varianti estese di coppe/Europa vanno mappate sui nomi canonici."""
    assert sources.canonical_team("ACF Fiorentina") == "Fiorentina"
    assert sources.canonical_team("FC Internazionale Milano") == "Inter"
    assert sources.canonical_team("SS Lazio") == "Lazio"
    assert sources.canonical_team("Juventus FC") == "Juventus"
    assert sources.canonical_team("SPAL 2013 Ferrara") == "Spal"
    assert sources.canonical_team("US Salernitana 1919") == "Salernitana"
    # I canonici restano invariati.
    assert sources.canonical_team("Napoli") == "Napoli"


# ------------------------------------------------------- 2. parser di date

def test_date_tracker_eredita_anno_e_semestre():
    t = _DateTracker("1920")  # stagione 2019-20
    assert t.parse("  Wed Sep 18 2019") == pd.Timestamp("2019-09-18")  # esplicito
    assert t.parse("  Tue Oct 1") == pd.Timestamp("2019-10-01")        # ereditato
    # nuovo girone che riparte da Settembre: NON deve incrementare l'anno
    assert t.parse("  Wed Sep 18") == pd.Timestamp("2019-09-18")


def test_date_tracker_rollover_anno_e_covid_agosto():
    t = _DateTracker("1920")
    assert t.parse("  Wed Sep 18 2019") == pd.Timestamp("2019-09-18")
    # Gennaio-Giugno -> anno di fine (year1)
    assert t.parse("  Tue Feb 18") == pd.Timestamp("2020-02-18")
    # Agosto DOPO aver visto year1 -> finali post-COVID nel 2020
    assert t.parse("  Fri Aug 7") == pd.Timestamp("2020-08-07")


def test_date_tracker_agosto_preliminari_resta_year0():
    t = _DateTracker("2425")  # 2024-25
    # Agosto PRIMA di qualsiasi data di year1 -> preliminari, anno di inizio
    assert t.parse("  Wed Aug 7") == pd.Timestamp("2024-08-07")


# ----------------------------------------------------- 3. parser Europa

_EU_TXT = """= UEFA Champions League 2019/20

▪ Group A
  Wed Sep 18 2019
    21:00  Juventus (ITA)          v Atlético Madrid (ESP)    1-0 (1-0)
    18:55  Real Madrid (ESP)       v Club Brugge KV (BEL)     2-2
  Tue Oct 1
           Napoli (ITA)            v Liverpool (ENG)          2-0 (1-0)
▪ Round of 16
  Tue Feb 25
    21:00  Atalanta (ITA)          v Valencia (ESP)           4-1 (1-0)
"""


def test_parse_europa_filtra_ita_e_orienta():
    df = parse_europe(_EU_TXT, "1920", "Champions League")
    # solo le 3 partite con un club ITA (Real vs Brugge esclusa)
    assert len(df) == 3
    r = df[df.home_raw == "Juventus"].iloc[0]
    assert r.home_cc == "ITA" and r.away_raw == "Atlético Madrid"
    assert r.date == pd.Timestamp("2019-09-18")
    # rows per-squadra: Juventus in casa -> H, avversario canonico
    teams = fixtures._uefa_team_rows(df, {"Juventus", "Napoli", "Atalanta"})
    juve = [x for x in teams if x["team"] == "Juventus"][0]
    # "Atletico Madrid" e' ora un alias noto (Fase 59, aggiunto per La Liga) ->
    # l'avversario e' canonicalizzato allo stesso nome usato altrove nel progetto.
    assert juve["home_away"] == "H" and juve["opponent"] == "Ath Madrid"


def test_parse_europa_due_italiane_due_righe():
    txt = ("▪ Final\n  Wed May 31 2023\n"
           "    21:00  Inter (ITA)             v AS Roma (ITA)            1-0\n")
    df = parse_europe(txt, "2223", "Europa League")
    rows = fixtures._uefa_team_rows(df, {"Inter", "Roma"})
    # una riga per ciascuna delle due italiane
    assert {r["team"] for r in rows} == {"Inter", "Roma"}
    inter = [r for r in rows if r["team"] == "Inter"][0]
    roma = [r for r in rows if r["team"] == "Roma"][0]
    assert inter["home_away"] == "H" and inter["opponent"] == "Roma"
    assert roma["home_away"] == "A" and roma["opponent"] == "Inter"


def test_parse_europa_logga_non_agganciato(caplog):
    """Un club ITA non presente nello snapshot va LOGGATo, non ignorato in silenzio."""
    txt = "▪ X\n  Wed Sep 18 2019\n    21:00  Sconosciuta (ITA) v Ajax (NED) 0-0\n"
    df = parse_europe(txt, "1920", "Champions League")
    import logging
    with caplog.at_level(logging.WARNING):
        rows = fixtures._uefa_team_rows(df, {"Inter", "Milan"})
    assert rows == []                       # nessuna riga emessa
    assert any("NON agganciato" in m for m in caplog.messages)


# ----------------------------------------------------- 4. parser Coppa Italia

def test_parse_coppa_formato_punteggio_in_mezzo():
    txt = ("▪ Round 1\nFri Aug 5 2022\n"
           "  21:00  US Lecce                2-3 a.e.t. (1-1, 0-0)  AS Cittadella\n"
           "  21:15  Torino FC               3-0 (0-0)  Palermo FC\n")
    df = parse_cup(txt, "2223", "Coppa Italia")
    assert len(df) == 2
    assert set(df.home_raw) == {"US Lecce", "Torino FC"}
    assert df[df.home_raw == "US Lecce"].iloc[0].away_raw == "AS Cittadella"


def test_parse_coppa_formato_con_v():
    txt = ("▪ Round of 16\n  Tue Dec 3 2024\n"
           "    21:00  AC Milan                v Sassuolo Calcio          6-1 (4-0)\n")
    df = parse_cup(txt, "2425", "Coppa Italia")
    assert len(df) == 1
    assert df.iloc[0].home_raw == "AC Milan" and df.iloc[0].away_raw == "Sassuolo Calcio"
    rows = fixtures._cup_team_rows(df, {"Milan"})   # solo il lato di Serie A
    assert len(rows) == 1 and rows[0]["team"] == "Milan"
    assert rows[0]["opponent"] == "Sassuolo"        # avversario canonicalizzato


# ------------------------------------------- 5. Serie A: nessuna partita persa

def test_serie_a_rows_due_per_partita():
    m = pd.DataFrame({
        "date": pd.to_datetime(["2024-08-20", "2024-08-21"]),
        "season": ["2425", "2425"], "home_team": ["Milan", "Parma"],
        "away_team": ["Inter", "Spal"],
    })
    rows = _serie_a_rows(m)
    assert len(rows) == 2 * len(m)                 # esattamente 2 righe per partita
    assert all(r["competition"] == "Serie A" for r in rows)
    milan = [r for r in rows if r["team"] == "Milan"][0]
    assert milan["home_away"] == "H" and milan["opponent"] == "Inter"


# ----------------------------------------- 6. rest_days_full: la parte cruciale

def _matches_sint():
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-09-01", "2024-09-15"]),
        "season": ["2425", "2425"], "league": ["serie_a", "serie_a"],
        "home_team": ["Inter", "Inter"], "away_team": ["Milan", "Roma"],
        "home_goals": [1, 2], "away_goals": [0, 1],
    })


def _fixtures_sint():
    rows = [
        ("Inter", "2024-08-10", "Serie A"),      # prima partita nota (>14g -> cap)
        ("Inter", "2024-09-01", "Serie A"),
        ("Inter", "2024-09-11", "Champions League"),  # gara NASCOSTA infrasettimana
        ("Inter", "2024-09-15", "Serie A"),
        ("Inter", "2024-09-20", "Champions League"),  # FUTURA -> non deve contare
    ]
    return pd.DataFrame([
        {"season": "2425", "team": t, "date": pd.Timestamp(d),
         "competition": c, "home_away": "H", "opponent": "X"}
        for t, d, c in rows
    ])


def test_rest_full_cattura_gara_nascosta_e_cap():
    out = add_rest_days_full(_matches_sint(), _fixtures_sint(), cap=14)
    r1 = out.iloc[0]   # 2024-09-01: prior 2024-08-10 (22g) -> cap 14
    r2 = out.iloc[1]   # 2024-09-15: prior 2024-09-11 (Champions) -> 4g
    assert r1.home_rest_days_full == 14
    assert r2.home_rest_days_full == 4          # la gara nascosta accorcia il riposo
    assert r2.home_midweek_europe == 1          # Champions nei 4 giorni prima
    assert r1.home_midweek_europe == 0


def test_rest_full_no_look_ahead():
    """La gara FUTURA (2024-09-20) non deve influenzare la partita del 15/09."""
    out = add_rest_days_full(_matches_sint(), _fixtures_sint())
    # se guardasse avanti, il riposo del 15/09 sarebbe negativo o sbagliato
    assert out.iloc[1].home_rest_days_full == 4
    assert (out[["home_rest_days_full", "away_rest_days_full"]].dropna() >= 0).all().all()


def test_rest_full_nan_alla_prima():
    out = add_rest_days_full(_matches_sint(), _fixtures_sint())
    # Roma (ospite del 15/09) non ha partite precedenti nel calendario -> NaN
    assert np.isnan(out.iloc[1].away_rest_days_full)


def test_rest_full_idempotente():
    una = add_rest_days_full(_matches_sint(), _fixtures_sint())
    due = add_rest_days_full(una, _fixtures_sint())
    pd.testing.assert_frame_equal(una, due)


# ------------------------------------- 7. integrita' offline (snapshot + csv)

@pytest.fixture(scope="module")
def snapshot():
    if not database.SNAPSHOT_PATH.exists():
        pytest.skip("snapshot non presente")
    return database.read_snapshot()


@pytest.fixture(scope="module")
def club_fx():
    if not fixtures.CLUB_FIXTURES_PATH.exists():
        pytest.skip("club_fixtures.csv non presente")
    return fixtures.read_club_fixtures()


def test_snapshot_ha_colonne_rest_full(snapshot):
    assert set(REST_FULL_COLUMNS) <= set(snapshot.columns)


def test_snapshot_rest_full_plausibile(snapshot):
    v = pd.concat([snapshot.home_rest_days_full,
                   snapshot.away_rest_days_full]).dropna()
    assert v.between(0, 14).all()               # cap rispettato, mai negativo
    for c in ("home_midweek_europe", "away_midweek_europe"):
        assert set(snapshot[c].dropna().unique()) <= {0, 1}


def test_snapshot_rest_full_non_supera_solo_serie_a(snapshot):
    """Invariante forte: il calendario completo e' un SOVRAINSieme di quello di
    Serie A, quindi la partita precedente e' >= -> rest_full <= rest solo-lega
    (dove entrambi definiti). Cattura sia bug di join sia look-ahead."""
    base = loader.add_rest_days(snapshot)
    for side in ("home", "away"):
        a = base[f"{side}_rest_days"]
        b = base[f"{side}_rest_days_full"]
        both = a.notna() & b.notna()
        assert (b[both] <= a[both] + 1e-9).all()


def test_club_fixtures_schema_e_competizioni(club_fx):
    assert list(club_fx.columns) == FIXTURE_COLUMNS
    note = (set(sources.EUROPE_COMPETITIONS.values())
            | set(sources.ITALY_CUP_COMPETITIONS.values())
            | {sources.SERIE_A_COMPETITION,
               sources.prelude_competition("serie_a"),      # Fase 68
               sources.SECOND_TIER_NAMES["serie_a"]})
    assert set(club_fx.competition.unique()) <= note


def test_club_fixtures_serie_a_completo(snapshot, club_fx):
    """Le partite di Serie A nel calendario = 2 righe per partita snapshot."""
    n_serie_a = (club_fx.competition == "Serie A").sum()
    assert n_serie_a == 2 * len(snapshot)


def test_club_fixtures_nessun_club_serie_a_orfano(snapshot, club_fx):
    """Ogni squadra del calendario di Serie A e' un club canonico dello snapshot
    (aggancio nomi riuscito, nessun 'Verona'-bug silenzioso)."""
    universo = set(snapshot.home_team) | set(snapshot.away_team)
    teams_serie_a = set(club_fx[club_fx.competition == "Serie A"].team)
    assert teams_serie_a <= universo


def test_club_fixtures_no_look_ahead_date(club_fx):
    """Ogni partita cade nella finestra temporale della sua stagione."""
    for season, grp in club_fx.groupby("season"):
        y = 2000 + int(season[:2])
        assert grp.date.between(pd.Timestamp(y, 7, 1), pd.Timestamp(y + 1, 8, 31)).all()


# --------------------------- 8. congestione vera generalizzata (Fase 59) -----
# Stessi controlli della sezione 7, ma parametrizzati su Premier League/La Liga
# (build_club_fixtures/add_rest_days_full generalizzati oltre la sola Serie A).

@pytest.fixture(params=["premier_league", "la_liga"])
def altra_lega(request):
    return request.param


@pytest.fixture
def altro_snapshot(altra_lega):
    path = database.snapshot_path(altra_lega)
    if not path.exists():
        pytest.skip(f"snapshot {altra_lega} non costruito")
    snap = database.read_snapshot(path)
    if not set(REST_FULL_COLUMNS) <= set(snap.columns):
        pytest.skip(f"{altra_lega}: congestione vera non ancora costruita "
                    f"(build_league_snapshot.py --fixtures)")
    return snap


@pytest.fixture
def altro_club_fx(altra_lega):
    path = fixtures.club_fixtures_path(altra_lega)
    if not path.exists():
        pytest.skip(f"club_fixtures {altra_lega} non presente")
    return fixtures.read_club_fixtures(path)


def test_altra_lega_snapshot_rest_full_plausibile(altro_snapshot):
    v = pd.concat([altro_snapshot.home_rest_days_full,
                   altro_snapshot.away_rest_days_full]).dropna()
    assert v.between(0, 14).all()
    for c in ("home_midweek_europe", "away_midweek_europe"):
        assert set(altro_snapshot[c].dropna().unique()) <= {0, 1}


def test_altra_lega_rest_full_non_supera_solo_lega(altro_snapshot):
    """Stessa invariante della Serie A (test_snapshot_rest_full_non_supera_solo_serie_a):
    il calendario completo e' un sovrainsieme del solo-lega -> rest_full <= rest."""
    base = loader.add_rest_days(altro_snapshot)
    for side in ("home", "away"):
        a = base[f"{side}_rest_days"]
        b = base[f"{side}_rest_days_full"]
        both = a.notna() & b.notna()
        assert (b[both] <= a[both] + 1e-9).all()


def test_altra_lega_club_fixtures_completo_e_senza_orfani(altra_lega, altro_snapshot, altro_club_fx):
    own = sources.own_league_competition(altra_lega)
    n_own = (altro_club_fx.competition == own).sum()
    assert n_own == 2 * len(altro_snapshot)
    universo = set(altro_snapshot.home_team) | set(altro_snapshot.away_team)
    teams_own = set(altro_club_fx[altro_club_fx.competition == own].team)
    assert teams_own <= universo


def test_altra_lega_club_fixtures_competizioni_note(altra_lega, altro_club_fx):
    own = sources.own_league_competition(altra_lega)
    note = (set(sources.EUROPE_COMPETITIONS.values())
            | set(sources.DOMESTIC_CUP_COMPETITIONS[altra_lega].values())
            | {own, sources.prelude_competition(altra_lega),   # Fase 68
               sources.SECOND_TIER_NAMES[altra_lega]})
    assert set(altro_club_fx.competition.unique()) <= note
