"""Test delle funzioni PURE dell'archivio outright (Fase 97).

Nessuna chiamata di rete. Si coprono le classificazioni e le regole di prezzo
di `scripts/fetch_smarkets_outrights.py` e `scripts/archive_outrights.py`, e in
particolare i SEI errori reali trovati costruendo l'archiviatore — ognuno ha
qui il suo test di non-regressione, perche' erano tutti silenziosi (producevano
un archivio dall'aspetto sano ma sbagliato):

  1. "qualify for UEFA Champions League" classificato come mercato CAMPIONE
     (la Ligue 1 usciva con 36 esiti invece di 18);
  2. mercati a piu' vincitori (qualificazione) rinormalizzati a 1;
  3. "w/o Paris Saint Germain - Winner" archiviato come mercato campione
     (due favoriti diversi per la stessa lega);
  4. "Serie A Women 26/27" archiviato come Serie A maschile;
  5. libri con sole offerte scartati -> spariva l'INTERO gruppo Top-N;
  6. "Top 2" e "Top 4" collassati sullo stesso tipo "place".
"""
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sm = _load("fetch_smarkets_outrights")


# ---------------------------------------------------------------- Smarkets

def test_market_type_distinguishes_placements():
    """Bug 6: "Top 2" e "Top 4" sono mercati DIVERSI, non un generico "place"."""
    assert sm.market_type("Premier League - Top 2") == "top2"
    assert sm.market_type("Premier League - Top 4") == "top4"
    assert sm.market_type("Ligue 1 - Top 3") == "top3"
    assert sm.market_type("Premier League - Winner") == "champion"
    assert sm.market_type("Premier League - Relegation") == "relegation"
    assert sm.market_type("Premier League - To Finish in Top Half") == "top_half"


def test_market_type_skips_conditional_and_novelty_markets():
    """Bug 3: i mercati "w/o <squadra>" finiscono in "winner$" e vanno esclusi.

    Il pattern gira sul nome GREZZO: normalizzando, "w/o" diventa "wo" e il
    filtro non scatta piu'.
    """
    for name in ("LaLiga - w/o FC Barcelona & Real Madrid - Winner",
                 "Ligue 1 - w/o Paris Saint Germain - Winner",
                 "Premier League - Best Promoted Team",
                 "Premier League - Top London Club",
                 "Premier League - Top Midlands Club",
                 "Premier League - Top On Christmas Day",
                 "Premier League - Number of promoted teams to be relegated",
                 "Premier League 2026/27 - Who will finish higher: A vs B"):
        assert sm.market_type(name) is None, name


def test_league_of_rejects_homonymous_competitions():
    """Bug 4: il match e' ancorato all'inizio, e questo da solo non basta."""
    assert sm.league_of("Serie A 26/27") == "serie_a"
    assert sm.league_of("Premier League 26/27") == "premier_league"
    assert sm.league_of("LaLiga 26/27") == "la_liga"
    assert sm.league_of("Bundesliga 26/27") == "bundesliga"
    assert sm.league_of("Ligue 1 26/27") == "ligue_1"
    # omonimi da NON confondere con la lega maschile di prima divisione
    for name in ("Serie A Women 26/27", "Bundesliga Women 26/27",
                 "Premier League U21 26/27", "Ligue 1 Promotion/Relegation",
                 "Eredivisie 26/27", "UEFA Champions League 26/27"):
        assert sm.league_of(name) is None, name


def test_championship_is_not_archived_while_ambiguous():
    """Smarkets pubblica due "Championship 26/27" (inglese e scozzese) con lo
    stesso slug: finche' non si disambigua, nessuno dei due va archiviato."""
    assert sm.league_of("Championship 26/27") is None
    assert "championship" not in sm.LEAGUE_EVENTS


def test_book_price_keeps_one_sided_books():
    """Bug 5: un libro con sole offerte non da' un mid, ma non e' vuoto.

    Se lo si scarta, spariscono interi mercati (i Top-N della Premier su
    Smarkets hanno SOLO offerte).
    """
    two = sm.book_price({"bids": [{"price": 3448}], "offers": [{"price": 3472}]})
    assert two["price_side"] == "mid"
    assert abs(two["price"] - 0.3460) < 1e-9
    assert abs(two["spread"] - 0.0024) < 1e-9

    ask_only = sm.book_price({"bids": [], "offers": [{"price": 435}]})
    assert ask_only["price_side"] == "ask_only"
    assert ask_only["price"] is None and ask_only["spread"] is None
    assert abs(ask_only["best_ask"] - 0.0435) < 1e-9   # l'informazione resta

    assert sm.book_price({"bids": [{"price": 100}], "offers": []})["price_side"] == "bid_only"
    assert sm.book_price({})["price_side"] == "empty"


def test_book_price_takes_best_of_each_side():
    """Il libro puo' avere piu' livelli: bid MIGLIORE = il piu' alto,
    ask MIGLIORE = la piu' bassa."""
    b = sm.book_price({"bids": [{"price": 1000}, {"price": 1200}, {"price": 900}],
                       "offers": [{"price": 1500}, {"price": 1300}, {"price": 1900}]})
    assert abs(b["best_bid"] - 0.12) < 1e-9
    assert abs(b["best_ask"] - 0.13) < 1e-9
    assert abs(b["price"] - 0.125) < 1e-9


def test_exclusive_only_for_single_winner_markets():
    """Bug 2: la retrocessione somma ~3 (tre retrocesse) — non e' un overround."""
    assert "champion" in sm.EXCLUSIVE
    assert "relegation" not in sm.EXCLUSIVE
    assert "top4" not in sm.EXCLUSIVE


# ------------------------------------------------------- Polymarket / archivio

ar = _load("archive_outrights")


def test_qualification_recognised_before_champion():
    """Bug 1: "qualify for UEFA Champions League" contiene "champions"."""
    assert ar._type_of("Ligue 1: Team to qualify for UEFA Champions League") == "qual_ucl"
    assert ar._type_of("EPL: Team to qualify for UEFA Europa League") == "qual_uel"
    assert ar._type_of("Serie A: Team to qualify for UEFA Conference League") == "qual_uecl"
    assert ar._type_of("Serie A Champion 2027") == "champion"
    assert ar._type_of("Premier League: Team to be relegated") == "relegation"


def test_placeholder_rows_are_dropped():
    """I segnaposto "Team A/B/C" senza mercato vero falsavano la somma."""
    assert ar._is_placeholder("Team A", 0.0, 1.0, 0)
    assert ar._is_placeholder("Other", None, None, None)
    assert not ar._is_placeholder("Inter Milan", 0.44, 0.48, 12000)
    # nome generico ma con un mercato VERO dietro: si tiene
    assert not ar._is_placeholder("Team A", 0.30, 0.32, 5000)


def _event(title, tags, prices, slug="x"):
    mk = [{"groupItemTitle": t,
           "outcomes": '["Yes", "No"]',
           "outcomePrices": f'["{p}", "{1 - p}"]',
           "bestBid": p - 0.01, "bestAsk": p + 0.01, "volumeNum": 1000}
          for t, p in prices]
    return {"title": title, "slug": slug,
            "tags": [{"label": t} for t in tags], "markets": mk}


def test_extract_normalises_only_exclusive_markets():
    ev = [_event("Serie A Champion 2027", ["Serie A"],
                 [("Inter", 0.50), ("Napoli", 0.30), ("Milan", 0.28)]),
          _event("Serie A: Team to qualify for UEFA Champions League", ["Serie A"],
                 [("Inter", 0.90), ("Napoli", 0.80), ("Milan", 0.70)])]
    rows = ar.extract(ev)
    champ = [r for r in rows if r["market"] == "champion"]
    qual = [r for r in rows if r["market"] == "qual_ucl"]
    # esclusivo -> devigato: la somma delle prob torna a 1
    assert abs(sum(r["prob"] for r in champ) - 1.0) < 1e-9
    assert all(r["exclusive"] for r in champ)
    assert abs(champ[0]["overround"] - 1.08) < 1e-9
    # NON esclusivo -> prob = prezzo grezzo, somma 2.4 e va bene cosi'
    assert not any(r["exclusive"] for r in qual)
    assert abs(sum(r["prob"] for r in qual) - 2.4) < 1e-9
    assert all(r["overround"] is None for r in qual)
    assert {r["source"] for r in rows} == {"polymarket"}


def test_extract_flags_settled_season_tails():
    """Un mercato con quasi tutti gli esiti a 0/1 e' la coda di una stagione
    conclusa, non una previsione: deve risultare marcato."""
    ev = [_event("Serie A: Team to qualify for UEFA Conference League", ["Serie A"],
                 [("Atalanta", 0.97)] + [(f"T{i}", 0.0) for i in range(19)])]
    rows = ar.extract(ev)
    assert rows[0]["settled_share"] >= 0.9
    live = [_event("Serie A Champion 2027", ["Serie A"],
                   [("Inter", 0.47), ("Napoli", 0.30), ("Milan", 0.23)])]
    assert ar.extract(live)[0]["settled_share"] < 0.9


def test_extract_ignores_single_matches():
    assert ar.extract([_event("Roma vs. Lazio", ["Serie A"], [("Roma", 0.5)])]) == []


# ---------------------------------------------------------------------------
# LA STAGIONE CHE COMINCIA (Fase 156-bis)
# Il difetto piu' caro trovato finora su questo file, e il piu' silenzioso:
# quando una lega comincia, Smarkets porta i suoi mercati outright da `open` a
# `live`. Il filtro originale (`!= "open"`) li scartava tutti, quindi
# l'archivio di quella lega si spegneva **il giorno del calcio d'inizio** --
# cioe' quando la serie di prezzi inizia a valere. Misurato il 16/08/2026: La
# Liga (cominciata il 15) era gia' sparita; Premier, Serie A, Ligue 1 e
# Bundesliga, non ancora cominciate, c'erano tutte, e sarebbero cadute il 21,
# 22 e 28 agosto una dopo l'altra.
# ---------------------------------------------------------------------------

def _finto_get(mercati, contratti, quotes):
    """Sostituisce le tre chiamate di rete di `fetch_outrights`."""
    def get(path):
        if path.endswith("/markets/"):
            return {"markets": mercati}
        if path.endswith("/contracts/"):
            return {"contracts": contratti}
        if path.endswith("/quotes/"):
            return quotes
        raise AssertionError(f"chiamata inattesa: {path}")
    return get


def test_un_mercato_LIVE_viene_archiviato(monkeypatch):
    """Stagione iniziata: mercato e contratti in `live`, prezzo c'e' -> si prende."""
    monkeypatch.setattr(sm, "outright_events",
                        lambda quiet=True: [{"id": 1, "name": "LaLiga 26/27",
                                             "slug": "laliga-26-27", "_league": "la_liga"}])
    monkeypatch.setattr(sm, "_get", _finto_get(
        [{"id": 9, "name": "LaLiga - Winner", "state": "live"}],
        [{"id": 11, "name": "FC Barcelona", "state_or_outcome": "live"},
         {"id": 12, "name": "Real Madrid", "state_or_outcome": "live"}],
        {11: {"bids": [{"price": 5200}], "offers": [{"price": 5300}]},
         12: {"bids": [{"price": 3900}], "offers": [{"price": 4000}]}}))

    righe = sm.fetch_outrights()
    assert {r["team"] for r in righe} == {"FC Barcelona", "Real Madrid"}
    assert all(r["market"] == "champion" and r["league"] == "la_liga" for r in righe)


def test_un_mercato_SETTLED_resta_fuori(monkeypatch):
    """Il rovescio: `settled`/`closed` non ha piu' un prezzo da congelare.
    Senza questo test, «accettare live» diventerebbe «accettare tutto»."""
    monkeypatch.setattr(sm, "outright_events",
                        lambda quiet=True: [{"id": 1, "name": "LaLiga 26/27",
                                             "slug": "laliga-26-27", "_league": "la_liga"}])
    monkeypatch.setattr(sm, "_get", _finto_get(
        [{"id": 9, "name": "LaLiga - Winner", "state": "settled"}],
        [{"id": 11, "name": "FC Barcelona", "state_or_outcome": "settled"}],
        {11: {"bids": [{"price": 9990}], "offers": []}}))

    assert sm.fetch_outrights() == []
