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
