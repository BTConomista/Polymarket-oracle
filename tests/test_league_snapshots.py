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
    # Chiusura 1X2: dalla Fase 101-bis e' presente su OGNI riga di ogni lega.
    #
    # Storia (serve a capire perche' il test e' cambiato): le due partite qui
    # sotto erano le uniche due senza chiusura — La Liga Alaves-Sociedad
    # 14/10/2017 e Bundesliga Bayern Munich-Hannover 04/05/2019 — perche' le
    # PSC* erano vuote nel grezzo e dalla Fase 73 la chiusura non ripiega piu'
    # sul fallback pre-match. Alla Fase 101-bis il dato REALE e' stato trovato
    # su una fonte secondaria dichiarata (iredchuk, confermata da una seconda
    # fonte indipendente) e inserito via il registro delle correzioni.
    #
    # Il test ora verifica il nuovo invariante — zero buchi — E che quelle due
    # partite portino davvero i valori del registro: se qualcuno ritira la
    # correzione senza aggiornare la documentazione, o se i valori cambiano
    # sotto i piedi, questo test lo dice.
    n_senza_chiusura = int(df["odds_home"].isna().sum())
    assert n_senza_chiusura == 0, (
        f"{league}: {n_senza_chiusura} righe senza chiusura 1X2, attese 0")
    DA_FONTE_SECONDARIA = {
        "la_liga": [("1718", "Alaves", "Sociedad", 3.40, 3.34, 2.15)],
        "bundesliga": [("1819", "Bayern Munich", "Hannover", 1.03, 18.43, 43.88)],
    }
    for season, casa, ospite, qh, qd, qa in DA_FONTE_SECONDARIA.get(league, []):
        m = df[(df.season.astype(str) == season) & (df.home_team == casa)
               & (df.away_team == ospite)]
        assert len(m) == 1, f"{league}: {casa}-{ospite} {season} non trovata"
        r = m.iloc[0]
        assert (round(float(r.odds_home), 2), round(float(r.odds_draw), 2),
                round(float(r.odds_away), 2)) == (qh, qd, qa), (
            f"{league} {casa}-{ospite}: quote di chiusura diverse da quelle "
            f"dichiarate in data/correzioni_dichiarate.csv")
        assert pd.notna(r.odds_home_open)            # apertura reale presente
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


# --------------------------------------------------------------------- #
# I gol all'intervallo devono sopravvivere a un --refresh (Fase 137)
# --------------------------------------------------------------------- #
def _grezzo_finto() -> pd.DataFrame:
    """Un CSV football-data in miniatura, con i campi che `_normalize` esige."""
    return pd.DataFrame({
        "Date": ["12/08/2023", "13/08/2023", "14/08/2023"],
        "HomeTeam": ["Inter", "Milan", "Roma"],
        "AwayTeam": ["Milan", "Roma", "Inter"],
        "FTHG": [3, 1, 0], "FTAG": [1, 1, 2], "FTR": ["H", "D", "A"],
        # asimmetrici di proposito: un'inversione casa/ospite si vede
        "HTHG": [2, 0, 0], "HTAG": [0, 1, 1],
    })


def test_normalize_produce_i_gol_all_intervallo():
    """Un `--refresh` NON deve perdere i gol all'intervallo.

    Perche' questo test esiste. La Fase 133 aveva aggiunto `home_goals_ht` /
    `away_goals_ht` con uno script che scriveva sugli snapshot GIA' fatti. Il
    ramo `--refresh` di `build_database.py`, pero', ricostruisce lo snapshot da
    zero passando da `loader._normalize`: finche' le due colonne non nascevano
    li', un solo refresh riportava la lega a 38 colonne — e nessun modulo sotto
    `src/` le nominava, quindi nessun test poteva accorgersene.

    L'asimmetria dei valori e' voluta: se HTHG e HTAG fossero scambiate, la
    prima riga darebbe 0-2 invece di 2-0 e questo test fallirebbe.
    """
    from src.data import sources

    out = loader._normalize(_grezzo_finto(), "2324", sources.LEAGUES["serie_a"])
    assert {"home_goals_ht", "away_goals_ht"} <= set(out.columns)
    assert list(out["home_goals_ht"]) == [2, 0, 0]
    assert list(out["away_goals_ht"]) == [0, 1, 1]
    # e restano coerenti col finale, riga per riga
    assert (out["home_goals_ht"] <= out["home_goals"]).all()
    assert (out["away_goals_ht"] <= out["away_goals"]).all()


def test_normalize_intervallo_vuoto_resta_vuoto_e_non_zero():
    """Regola R6: un buco dichiarato e' innocuo, un finto pieno no.

    Il caso reale e' Union Berlin-Bochum del 14/12/2024 (sospesa, 1-1 sul campo
    e 0-2 a tavolino): football-data ne registra il verdetto ma lascia
    l'intervallo in bianco. Uno 0-0 al suo posto racconterebbe una partita che
    non c'e' stata. Il tipo dev'essere Int64 nullable proprio per questo: un
    `int` non puo' essere vuoto e un `float` scriverebbe `2.0` in ogni cella.
    """
    grezzo = _grezzo_finto()
    grezzo.loc[1, ["HTHG", "HTAG"]] = [None, None]

    from src.data import sources

    out = loader._normalize(grezzo, "2324", sources.LEAGUES["serie_a"])
    assert str(out["home_goals_ht"].dtype) == "Int64"
    assert pd.isna(out.loc[1, "home_goals_ht"])
    assert pd.isna(out.loc[1, "away_goals_ht"])
    assert out.loc[0, "home_goals_ht"] == 2      # le altre righe non ne risentono


def test_normalize_senza_le_colonne_di_intervallo_alla_fonte():
    """Una fonte che non porta HTHG/HTAG non deve far esplodere il caricamento:
    le colonne ci sono lo stesso, vuote. E' il caso di una stagione vecchia o di
    un provider diverso — e vale la stessa regola dei tiri in porta, che gia'
    mancano in alcune righe."""
    grezzo = _grezzo_finto().drop(columns=["HTHG", "HTAG"])

    from src.data import sources

    out = loader._normalize(grezzo, "2324", sources.LEAGUES["serie_a"])
    assert {"home_goals_ht", "away_goals_ht"} <= set(out.columns)
    assert out["home_goals_ht"].isna().all()
    assert str(out["home_goals_ht"].dtype) == "Int64"


def test_le_colonne_di_intervallo_sono_nello_schema_interno():
    """Guardia contro il ritorno del difetto: qualunque cosa succeda, le due
    colonne devono nascere dentro `src/`, non da uno script a valle.

    Prima della Fase 137 `grep -rl goals_ht src/ scripts/` rispondeva con UN
    file solo — lo script della Fase 133 — e questo bastava a spiegare il
    difetto: nessuna riga della pipeline di produzione le conosceva.
    """
    import inspect

    sorgente = inspect.getsource(loader._normalize)
    assert "HTHG" in sorgente and "HTAG" in sorgente
    assert "home_goals_ht" in sorgente and "away_goals_ht" in sorgente


# --------------------------------------------------------------------- #
# La posta in palio non puo' presumere 20 squadre (Fase 137)
# --------------------------------------------------------------------- #
def _stagione_finta(n: int, season: str = "2324",
                    inizio: str = "2023-08-01") -> pd.DataFrame:
    """Un campionato finto ma REALISTICO: doppio girone col metodo del cerchio.

    Serve che sia realistico e non un elenco qualunque di partite: `add_stakes`
    ragiona sulla classifica giornata per giornata, quindi un calendario con una
    partita al giorno (tutte le gare interne di una squadra di fila) produce
    classifiche che non esistono, e non distingue una lega a 18 da una a 20.
    Qui invece ogni giornata manda in campo TUTTE le squadre, come nella realta'.

    I risultati sono deterministici e gerarchici — vince sempre la squadra col
    numero piu' basso — cosi' a fine stagione titolo, Europa e salvezza sono
    decisi per davvero e c'e' qualcosa da misurare.
    """
    squadre = [f"T{i:02d}" for i in range(n)]
    righe, giorno = [], pd.Timestamp(inizio)
    for ritorno in (False, True):
        rot = list(squadre)
        for _ in range(n - 1):
            for i in range(n // 2):
                a, b = rot[i], rot[n - 1 - i]
                casa, ospite = (b, a) if ritorno else (a, b)
                righe.append({
                    "date": giorno, "season": season,
                    "home_team": casa, "away_team": ospite,
                    "result": "H" if casa < ospite else "A",
                })
            giorno += pd.Timedelta(days=7)
            rot = [rot[0], rot[-1], *rot[1:-1]]     # rotazione del cerchio
    return pd.DataFrame(righe)


def test_add_stakes_legge_il_numero_di_squadre_dai_dati():
    """`total` deve venire dalla lega vera, non da un 20 cablato.

    Il difetto: `load_league` chiamava `add_stakes(df)` con i default per tutte
    e cinque le leghe. La Bundesliga ha 18 squadre in tutte e 9 le stagioni e la
    Ligue 1 e' passata a 18 nel 2023-24: 34 giornate, non 38. Con n_teams=20 la
    raggiungibilita' `3*(total-played)` sopravvalutava di 12 punti la rimonta
    ancora possibile, quindi a fine stagione «nessuno era deciso».

    Misurato sugli snapshot veri: in Bundesliga le partite con la squadra di
    casa a posta decisa passano da 7 a 114, in Ligue 1 da 76 a 112. In Serie A
    (che 20 squadre le ha davvero) non cambia **una sola cella**: la correzione
    tocca solo dove il numero era sbagliato.
    """
    a18 = _stagione_finta(18)
    assert len(a18) == 306 and a18["date"].nunique() == 34
    dedotto = loader.add_stakes(a18)
    cablato = loader.add_stakes(a18, n_teams=20)
    assert dedotto["home_settled"].sum() > cablato["home_settled"].sum(), (
        "con 18 squadre il calendario e' piu' corto: dedurlo dai dati deve "
        "dichiarare DECISE piu' partite del conto a 20, che vede 4 giornate "
        "fantasma e quindi 12 punti di rimonta che non esistono")

    # dove le squadre sono davvero 20, dedurre e presumere devono coincidere:
    # la correzione non deve muovere una sola cella di Serie A/Premier/Liga.
    a20 = _stagione_finta(20)
    assert len(a20) == 380 and a20["date"].nunique() == 38
    for col in ("home_settled", "away_settled"):
        assert (loader.add_stakes(a20)[col].values
                == loader.add_stakes(a20, n_teams=20)[col].values).all(), col


def test_add_stakes_non_guarda_avanti():
    """Regola R8: la classifica usata e' quella PRIMA della partita.

    La prima giornata di ogni stagione parte da una classifica vuota, quindi
    nessuno puo' risultare «deciso»: se lo fosse, vorrebbe dire che la funzione
    ha gia' letto risultati che non erano ancora accaduti.
    """
    df = loader.add_stakes(_stagione_finta(18))
    prima = df[df["date"] == df["date"].min()]
    assert (prima["home_settled"] == 0.0).all()
    assert (prima["away_settled"] == 0.0).all()


def test_add_stakes_e_per_stagione_non_per_lega():
    """Una lega che cambia formato a meta' storia dev'essere gestita stagione
    per stagione: e' il caso vero della Ligue 1 (20 squadre fino al 2022-23,
    18 dal 2023-24), che un unico `n_teams` per lega non puo' descrivere."""
    a = _stagione_finta(20, season="2324", inizio="2023-08-01")
    b = _stagione_finta(18, season="2425", inizio="2024-08-01")
    unite = loader.add_stakes(pd.concat([a, b], ignore_index=True))

    chiave = ["date", "home_team", "away_team"]
    for pezzo, stagione in ((a, "2324"), (b, "2425")):
        sola = loader.add_stakes(pezzo)
        # confronto per CHIAVE e non per posizione: `sort_values("date")` non e'
        # stabile, quindi due esecuzioni possono ordinare diversamente le
        # partite dello stesso giorno. I valori restano attaccati alla loro
        # riga — ed e' quello che conta — ma un confronto posizionale
        # fallirebbe per un motivo che non c'entra nulla con la posta in palio.
        m = unite[unite["season"] == stagione].merge(sola, on=chiave,
                                                     suffixes=("_ins", "_sola"))
        assert len(m) == len(sola)
        for col in ("home_settled", "away_settled"):
            assert (m[f"{col}_ins"] == m[f"{col}_sola"]).all(), (stagione, col)
