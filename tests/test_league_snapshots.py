"""Test degli snapshot Premier League / La Liga (Fase 54).

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


@pytest.mark.parametrize("league", ["premier_league", "la_liga"])
def test_snapshot_integro_e_xg_completo(league):
    if not database.snapshot_path(league).exists():
        pytest.skip(f"snapshot {league} non costruito (scripts/build_league_snapshot.py)")
    df = loader.load_league(league)
    # 9 stagioni da 380 partite (20 squadre, girone doppio)
    assert df["season"].nunique() == 9
    assert (df.groupby("season").size() == 380).all()
    # copertura piena = alias tutti riconciliati (nessuna partita orfana di xG)
    assert df["home_xg"].notna().all()
    assert df["away_xg"].notna().all()
    # Chiusura 1X2 presente ovunque, tranne l'unica eccezione documentata
    # (Fase 73): La Liga Alaves-Sociedad 14/10/2017 non ha la chiusura Pinnacle
    # (PSC* vuote nel grezzo) e dalla Fase 73 la chiusura non ripiega piu' sul
    # fallback pre-match -> resta NaN (l'apertura reale PS* c'e', vedi sotto).
    missing_close = df[df["odds_home"].isna()]
    if len(missing_close):
        assert league == "la_liga" and len(missing_close) == 1
        row = missing_close.iloc[0]
        assert str(row["season"]) == "1718" and row["home_team"] == "Alaves"
        assert pd.notna(row["odds_home_open"])       # apertura reale presente
    # risultato coerente coi gol
    import numpy as np
    exp = np.where(df.home_goals > df.away_goals, "H",
                   np.where(df.home_goals < df.away_goals, "A", "D"))
    assert (df["result"].values == exp).all()


@pytest.mark.parametrize("league", ["premier_league", "la_liga"])
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


@pytest.mark.parametrize("league", ["serie_a", "premier_league", "la_liga"])
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
