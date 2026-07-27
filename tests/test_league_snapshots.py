"""Test degli snapshot delle leghe oltre la Serie A (Fase 54; Bundesliga e
Ligue 1 aggiunte dopo).

Verifica che la pipeline dai bundle produca dati integri e che la riconciliazione
dei nomi squadra (football-data <-> Understat) sia completa: nessun buco di xG =
nessun alias mancante. Se un domani un bundle cambia i nomi, questo test lo cattura.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, loader                # noqa: E402


ALTRE_LEGHE = ["premier_league", "la_liga", "bundesliga", "ligue_1"]
TUTTE = ["serie_a"] + ALTRE_LEGHE


@pytest.mark.parametrize("league", ALTRE_LEGHE)
def test_snapshot_integro_e_xg_completo(league):
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito (scripts/build_league_snapshot.py)")
    df = loader.load_league(league)
    assert df["season"].nunique() == 9
    # Numero di partite per stagione: dipende dalla struttura della lega, non e'
    # 380 ovunque. Bundesliga = 18 squadre (306); Ligue 1 = 20 fino al 2022-23
    # (380), 18 dal 2023-24 (306), e 279 nel 2019-20 perche' il campionato fu
    # CANCELLATO per COVID (unico dei cinque a non essere ripreso).
    per_stagione = df.groupby("season").size()
    if league == "bundesliga":
        assert (per_stagione == 306).all()
    elif league == "ligue_1":
        assert set(per_stagione.unique()) <= {380, 306, 279}
        assert per_stagione["1920"] == 279       # troncamento COVID, dato reale
    else:
        assert (per_stagione == 380).all()
    # copertura xG piena = alias tutti riconciliati (nessuna partita orfana),
    # tranne i buchi DICHIARATI: Understat non ha acquisito quelle partite.
    XG_MANCANTI_DICHIARATI = {
        "ligue_1": 1,      # Nantes-Toulouse 17/05/2026 (isResult=false)
        "bundesliga": 1,   # Holstein Kiel-Bochum 09/02/2025 (lista tiri VUOTA:
                           # i valori pubblicati erano un segnaposto, non misure)
    }
    atteso = XG_MANCANTI_DICHIARATI.get(league, 0)
    assert int(df["home_xg"].isna().sum()) == atteso
    assert int(df["away_xg"].isna().sum()) == atteso
    # Chiusura 1X2 presente ovunque, tranne l'unica eccezione documentata
    # (Fase 73): La Liga Alaves-Sociedad 14/10/2017 non ha la chiusura Pinnacle
    # (PSC* vuote nel grezzo) e dalla Fase 73 la chiusura non ripiega piu' sul
    # fallback pre-match -> resta NaN (l'apertura reale PS* c'e', vedi sotto).
    # Le eccezioni sono DICHIARATE una per una: se ne compare una nuova, il test
    # deve rompersi (e' il suo scopo). In entrambi i casi l'apertura reale c'e'.
    CHIUSURA_1X2_MANCANTE = {
        "la_liga": [("1718", "Alaves", "Sociedad")],
        "bundesliga": [("1819", "Bayern Munich", "Hannover")],
    }
    attese = CHIUSURA_1X2_MANCANTE.get(league, [])
    missing_close = df[df["odds_home"].isna()]
    assert len(missing_close) == len(attese), (
        f"{league}: {len(missing_close)} righe senza chiusura 1X2, "
        f"{len(attese)} dichiarate")
    for row, (season, casa, ospite) in zip(
            missing_close.itertuples(), attese):
        assert (str(row.season), row.home_team, row.away_team) == (season, casa, ospite)
        assert pd.notna(row.odds_home_open)          # apertura reale presente
    # risultato coerente coi gol
    import numpy as np
    exp = np.where(df.home_goals > df.away_goals, "H",
                   np.where(df.home_goals < df.away_goals, "A", "D"))
    assert (df["result"].values == exp).all()


@pytest.mark.parametrize("league", ALTRE_LEGHE)
def test_nomi_squadra_stabili_tra_stagioni(league):
    """Ogni squadra deve avere >= 1 stagione piena; nessun nome 'quasi-duplicato'
    (spia di alias mancante: es. 'Man City' e 'Manchester City' entrambi presenti)."""
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito")
    df = loader.load_league(league)
    teams = set(df["home_team"]) | set(df["away_team"])
    # nessuna coppia di nomi dove uno e' contenuto nell'altro (case-insensitive)
    low = sorted(teams, key=len)
    for i, a in enumerate(low):
        for b in low[i + 1:]:
            assert not (a.lower() in b.lower() and a != b), \
                f"{league}: '{a}' e '{b}' — alias non riconciliato?"


@pytest.mark.parametrize("league", TUTTE)
def test_quote_1x2_senza_overround_impossibile(league):
    """Fase 58 (audit dati): un book vero non ha mai overround < 1 (arbitraggio
    garantito). Trovato e corretto un caso reale (La Liga, Mallorca-Barcelona
    2025-08-16: Avg chiusura con overround 0.929, ripiegato su B365 in
    src/data/loader.py). Questo test blocca la regressione su tutte le leghe,
    chiusura e apertura."""
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito")
    df = loader.load_league(league)
    close = df[["odds_home", "odds_draw", "odds_away"]].dropna()
    overround = 1 / close["odds_home"] + 1 / close["odds_draw"] + 1 / close["odds_away"]
    assert (overround >= 1.0).all(), \
        f"{league}: {(overround < 1.0).sum()} righe con overround chiusura < 1"

    if "odds_home_open" in df.columns:
        openo = df[["odds_home_open", "odds_draw_open", "odds_away_open"]].dropna()
        if len(openo):
            ov_open = (1 / openo["odds_home_open"] + 1 / openo["odds_draw_open"]
                      + 1 / openo["odds_away_open"])
            assert (ov_open >= 1.0).all(), \
                f"{league}: {(ov_open < 1.0).sum()} righe con overround apertura < 1"


def test_schema_identico_tra_leghe():
    """Lo schema deve essere identico su TUTTE le leghe — non solo lo stesso
    INSIEME di colonne, ma lo stesso ORDINE.

    Perche' l'ordine conta: `docs/DATI.md` dichiara «lo schema e' identico», e
    per un periodo non lo era — Premier e Liga avevano le 5 colonne `*_open` in
    posizione 15-19 e la Serie A in posizione 29-33. Nessun calcolo ne
    risentiva (si legge per nome), ma la divergenza si perpetuava a ogni
    refresh e nessun test la vedeva. Questo test la vede.
    """
    base = None
    for league in TUTTE:
        if not database.snapshot_path(league).exists():
            pytest.skip(f"snapshot {league} non costruito")
        cols = list(pd.read_csv(database.snapshot_path(league), nrows=1).columns)
        if base is None:
            base, riferimento = cols, league
            continue
        assert cols == base, (
            f"{league}: schema diverso da {riferimento}. "
            f"Solo in {league}: {set(cols) - set(base)}; "
            f"solo in {riferimento}: {set(base) - set(cols)}; "
            f"stesso insieme ma ordine diverso: {set(cols) == set(base)}")


def test_overround_impossibilmente_alto_scartato():
    """Il guard protegge ENTRAMBI i lati: anche un margine troppo ALTO e' un
    dato corrotto, non un prezzo.

    Il caso reale da cui nasce: La Liga 2018-19 Alaves-Real Madrid, linea O/U
    pre-match 1.53/1.59 = overround 1.283, cioe' il 28% di margine su un
    mercato a due esiti. Il guard originale vedeva solo l'overround < 1 e
    lasciava passare questi. I valori qui sotto sono quelli veri di quella riga.
    """
    from src.data import loader

    corrotta = pd.Series({"Avg>2.5": 1.53, "Avg<2.5": 1.59})
    picks = loader._pick_market_odds(
        corrotta, ["odds_over25_open", "odds_under25_open"],
        loader._ODDS_PREFERENCE_OPEN)
    assert all(pd.isna(v) for v in picks.values()), \
        "una linea con overround 1.283 non deve entrare nello snapshot"

    # e una linea sana deve passare indisturbata (il guard non e' un colino)
    sana = pd.Series({"Avg>2.5": 1.90, "Avg<2.5": 1.95})
    picks = loader._pick_market_odds(
        sana, ["odds_over25_open", "odds_under25_open"],
        loader._ODDS_PREFERENCE_OPEN)
    assert picks["odds_over25_open"] == 1.90 and picks["odds_under25_open"] == 1.95


@pytest.mark.parametrize("league", TUTTE)
def test_nessun_margine_impossibile_negli_snapshot(league):
    """Nessuna riga, in nessuna delle 5 leghe, ha un margine fuori dai limiti
    credibili — ne' sotto 1 (arbitraggio) ne' sopra ORR_MAX (dato corrotto)."""
    from src.data.loader import ORR_MAX

    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito")
    df = loader.load_league(league)
    mercati = [("odds_home", "odds_draw", "odds_away"),
               ("odds_home_open", "odds_draw_open", "odds_away_open"),
               ("odds_over25", "odds_under25"),
               ("odds_over25_open", "odds_under25_open")]
    for cols in mercati:
        sub = df[list(cols)].dropna()
        if not len(sub):
            continue
        orr = sum(1.0 / sub[c] for c in cols)
        assert (orr >= 1.0).all() and (orr <= ORR_MAX).all(), (
            f"{league}/{cols[0]}: {int(((orr < 1) | (orr > ORR_MAX)).sum())} "
            f"righe con margine impossibile (min {orr.min():.4f}, max {orr.max():.4f})")


def test_xg_segnaposto_scartato():
    """Un record SEGNAPOSTO della fonte xG non deve entrare come se fosse una
    misura — ed e' il caso piu' insidioso, perche' il dato coincide con la
    fonte e nessun confronto snapshot-vs-fonte lo vede.

    Caso reale: Holstein Kiel-Bochum 09/02/2025. Understat non ha acquisito la
    partita (lista tiro-per-tiro VUOTA, mentre football-data conta 3+6 tiri in
    porta) e ha pubblicato xG = gol esatti, ppda azzerata, deep 0.
    """
    from src.data import understat

    segnaposto = {
        "teams": {"1": {"title": "Holstein Kiel", "history": [
                      {"date": "2025-02-09 13:30:00", "npxG": "1.25",
                       "ppda": {"att": 0, "def": 0}, "deep": 0}]},
                  "2": {"title": "Bochum", "history": [
                      {"date": "2025-02-09 13:30:00", "npxG": "2",
                       "ppda": {"att": 0, "def": 0}, "deep": 0}]}},
        "dates": [{"isResult": True,
                   "h": {"title": "Holstein Kiel"}, "a": {"title": "Bochum"},
                   "goals": {"h": "2", "a": "2"}, "xG": {"h": "2", "a": "2"},
                   "datetime": "2025-02-09 13:30:00"}],
    }
    df = understat.parse_season_xg(segnaposto, "2425")
    assert len(df) == 1
    for c in ("home_xg", "away_xg", "home_npxg", "away_npxg",
              "home_deep", "away_deep"):
        assert pd.isna(df.iloc[0][c]), f"{c} doveva essere NaN"

    # Una partita davvero sterile (deep 0 su entrambi) ma con xG MISURATO non
    # deve essere toccata: il guard e' conservativo, non un colino.
    vera = {
        "teams": {"1": {"title": "Reims", "history": [
                      {"date": "2020-08-30 15:00:00", "npxG": "0.206627",
                       "ppda": {"att": 108, "def": 10}, "deep": 0}]},
                  "2": {"title": "Lille", "history": [
                      {"date": "2020-08-30 15:00:00", "npxG": "0.906784",
                       "ppda": {"att": 164, "def": 10}, "deep": 0}]}},
        "dates": [{"isResult": True,
                   "h": {"title": "Reims"}, "a": {"title": "Lille"},
                   "goals": {"h": "0", "a": "1"},
                   "xG": {"h": "0.206627", "a": "0.906784"},
                   "datetime": "2020-08-30 15:00:00"}],
    }
    df2 = understat.parse_season_xg(vera, "2021")
    assert df2.iloc[0]["home_xg"] == pytest.approx(0.206627)
    assert df2.iloc[0]["away_xg"] == pytest.approx(0.906784)


def test_gruppo_di_mercato_incompleto_scartato_in_blocco():
    """Un solo lato di un mercato non e' una linea: si scarta IN BLOCCO.

    Politica dichiarata nella docstring di `_pick_market_odds` ("mai un solo
    lato") ma non implementata: con un lato mancante il guard veniva saltato
    del tutto e usciva un dict misto (un numero + un NaN). Sui dati odierni non
    cambia nulla — 0 righe con NaN parziale sui 4 gruppi in tutte e 5 le leghe
    (audit Fase 101) — ma un refresh futuro potrebbe incontrarne uno.
    """
    from src.data import loader

    meta_linea = pd.Series({"Avg>2.5": 1.90})          # manca il lato Under
    picks = loader._pick_market_odds(
        meta_linea, ["odds_over25_open", "odds_under25_open"],
        loader._ODDS_PREFERENCE_OPEN)
    assert all(pd.isna(v) for v in picks.values()), \
        "con un solo lato valorizzato l'intero gruppo deve andare a NaN"

    meta_1x2 = pd.Series({"AvgH": 2.10, "AvgD": 3.40})  # manca la trasferta
    picks = loader._pick_market_odds(
        meta_1x2, ["odds_home_open", "odds_draw_open", "odds_away_open"],
        loader._ODDS_PREFERENCE_OPEN)
    assert all(pd.isna(v) for v in picks.values())


@pytest.mark.parametrize("league", TUTTE)
def test_nessun_gruppo_di_mercato_parziale_negli_snapshot(league):
    """Controparte sui dati: nessuna riga ha un gruppo di quote a meta'."""
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito")
    df = pd.read_csv(database.snapshot_path(league))
    for cols in (["odds_home", "odds_draw", "odds_away"],
                 ["odds_over25", "odds_under25"],
                 ["odds_home_open", "odds_draw_open", "odds_away_open"],
                 ["odds_over25_open", "odds_under25_open"]):
        cols = [c for c in cols if c in df.columns]
        if not cols:
            continue
        na = df[cols].isna()
        parziali = int((na.any(axis=1) & ~na.all(axis=1)).sum())
        assert parziali == 0, f"{league}: {parziali} righe con {cols} a meta'"


def test_enrich_richiede_la_lega_giusta():
    """`enrich` deve sapere QUALE lega sta arricchendo.

    Fino all'audit della Fase 101 non riceveva `league_key` e le tre funzioni
    chiamate (add_xg, add_squad_values, add_absences) ripiegavano sul default
    "serie_a": con UNDERSTAT_LEAGUES a 5 voci la guardia non bloccava piu'
    nulla e `--enrich --league premier_league` avrebbe riscritto l'xG della
    Premier con quello della Serie A (add_xg fa il drop delle colonne prima di
    riscriverle). Qui si verifica che la firma prenda la lega e che una lega
    incoerente col contenuto si fermi RUMOROSAMENTE, senza rete.
    """
    import inspect

    from src.data import loader

    assert "league_key" in inspect.signature(loader.enrich).parameters

    finto = pd.DataFrame({"league": ["premier_league"] * 2,
                          "season": ["2425"] * 2,
                          "home_team": ["Arsenal", "Chelsea"],
                          "away_team": ["Chelsea", "Arsenal"]})
    with pytest.raises(ValueError, match="premier_league"):
        loader.enrich(finto, "serie_a")
