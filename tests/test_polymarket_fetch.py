"""Test delle funzioni PURE di scripts/fetch_polymarket_open.py.

Nessuna chiamata di rete: si testano il parsing dei prezzi (stringhe JSON),
lo stripping degli slug di sotto-evento e la ricostruzione delle partite di
calcio (1X2 + O/U + BTTS) su un fixture giocattolo che riproduce la struttura
reale della Gamma API (verificata sul campo il 2026-07-24):
  - un evento base "A vs. B" con 3 mercati Yes/No = 1X2;
  - un evento "A vs. B - More Markets" con O/U e Both Teams to Score;
  - outcomes/outcomePrices come STRINGHE JSON.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "fetch_polymarket_open",
    Path(__file__).resolve().parents[1] / "scripts" / "fetch_polymarket_open.py",
)
pm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pm)


def _mkt(question, outcomes, prices, git=""):
    return {"question": question,
            "outcomes": str(outcomes).replace("'", '"'),
            "outcomePrices": str(prices).replace("'", '"'),
            "groupItemTitle": git}


BASE = {
    "title": "Roma vs. Lazio",
    "slug": "ita-rom-laz-2026-08-24",
    "endDate": "2026-08-24T18:00:00Z",
    "tags": [{"label": "Sports"}, {"label": "Soccer"}, {"label": "Serie A"}],
    "markets": [
        _mkt("Will Roma win on 2026-08-24?", ["Yes", "No"], [0.5, 0.5]),
        _mkt("Will Roma vs. Lazio end in a draw?", ["Yes", "No"], [0.3, 0.7]),
        _mkt("Will Lazio win on 2026-08-24?", ["Yes", "No"], [0.2, 0.8]),
    ],
}
MORE = {
    "title": "Roma vs. Lazio - More Markets",
    "slug": "ita-rom-laz-2026-08-24-more-markets",
    "endDate": "2026-08-24T18:00:00Z",
    "tags": [{"label": "Soccer"}],
    "markets": [
        _mkt("Roma vs. Lazio: O/U 2.5", ["Over", "Under"], [0.55, 0.45], "O/U 2.5"),
        _mkt("Roma vs. Lazio: Both Teams to Score", ["Yes", "No"], [0.6, 0.4],
             "Both Teams to Score"),
    ],
}


def test_market_outcomes_parses_json_strings():
    o = pm.market_outcomes(BASE["markets"][0])
    assert o == {"Yes": 0.5, "No": 0.5}


def test_base_slug_strips_subevent_suffixes():
    assert pm._base_slug("ita-rom-laz-2026-08-24-more-markets") == "ita-rom-laz-2026-08-24"
    assert pm._base_slug("x-halftime-result") == "x"
    assert pm._base_slug("no-suffix-here") == "no-suffix-here"


def test_event_tags_extracts_labels():
    assert pm.event_tags(BASE) == ["Sports", "Soccer", "Serie A"]


def test_build_soccer_matches_1x2_devig_and_markets():
    matches = pm.build_soccer_matches([BASE, MORE])
    assert len(matches) == 1
    m = matches[0]
    # 1X2: prezzi grezzi + devig normalizzato a 1
    assert m["home"] == "Roma" and m["away"] == "Lazio"
    assert m["one_x_two"]["raw"] == {"home": 0.5, "draw": 0.3, "away": 0.2}
    dv = m["one_x_two"]["devig"]
    assert abs(sum(dv.values()) - 1.0) < 1e-9
    assert dv["home"] == 0.5 and dv["draw"] == 0.3 and dv["away"] == 0.2  # overround 1.0 qui
    # O/U 2.5 e BTTS agganciati dall'evento "More Markets"
    assert m["over_under"]["2.5"] == {"over": 0.55, "under": 0.45}
    assert m["btts"] == {"yes": 0.6, "no": 0.4}
    # i due eventi della stessa partita sono stati fusi
    assert set(m["event_slugs"]) == {BASE["slug"], MORE["slug"]}


def test_build_soccer_matches_ignores_outrights():
    outright = {"title": "Serie A: 2027 Champion", "slug": "serie-a-2027-champion",
                "tags": [{"label": "Soccer"}], "markets": []}
    assert pm.build_soccer_matches([outright]) == []


# ---- regressioni dall'audit Fase 90 (bug reali, verificati su dati live) ----
DERBY_BASE = {
    "title": "Manchester City vs. Manchester United",
    "slug": "epl-mci-mun-2026-09-12",
    "endDate": "2026-09-12T14:00:00Z",
    "tags": [{"label": "Soccer"}, {"label": "EPL"}],
    "markets": [
        _mkt("Will Manchester City win on 2026-09-12?", ["Yes", "No"], [0.55, 0.45]),
        _mkt("Will Manchester City vs. Manchester United end in a draw?",
             ["Yes", "No"], [0.25, 0.75]),
        _mkt("Will Manchester United win on 2026-09-12?", ["Yes", "No"], [0.20, 0.80]),
    ],
}


def test_derby_with_shared_first_word_keeps_1x2():
    """Bug Fase 90(a): col match sulla PRIMA PAROLA la domanda sull'ospite
    finiva nel ramo della casa e l'intera partita usciva senza 1X2."""
    m = pm.build_soccer_matches([DERBY_BASE])[0]
    assert m["one_x_two"] is not None, "1X2 perso sul derby"
    assert m["one_x_two"]["raw"] == {"home": 0.55, "draw": 0.25, "away": 0.20}


def test_which_team_prefers_longest_full_name():
    assert pm._which_team("Will Manchester United win?", "Manchester City",
                          "Manchester United") == "away"
    assert pm._which_team("Will Manchester City win?", "Manchester City",
                          "Manchester United") == "home"
    assert pm._which_team("Will Real Betis win?", "Real Madrid", "Real Betis") == "away"
    # nessuna delle due riconoscibile -> nessuna assegnazione (meglio del falso)
    assert pm._which_team("Will Someone Else win?", "Roma", "Lazio") is None


def test_half_and_team_markets_do_not_overwrite_full_match():
    """Bug Fase 90(b): '1st Half O/U 2.5' e '<squadra> O/U 2.5' contengono la
    stessa sottostringa e con re.search sovrascrivevano la linea vera."""
    ev = {
        "title": "Roma vs. Lazio - More Markets",
        "slug": "ita-rom-laz-2026-08-24-more-markets",
        "tags": [{"label": "Soccer"}],
        "markets": [
            _mkt("Roma vs. Lazio: O/U 2.5", ["Over", "Under"], [0.295, 0.705], "O/U 2.5"),
            _mkt("Roma vs. Lazio: 1st Half O/U 2.5", ["Over", "Under"],
                 [0.500, 0.500], "1st Half O/U 2.5"),
            _mkt("Roma vs. Lazio: Roma O/U 2.5", ["Over", "Under"],
                 [0.111, 0.889], "Roma O/U 2.5"),
            _mkt("Roma vs. Lazio: Both Teams to Score", ["Yes", "No"],
                 [0.60, 0.40], "Both Teams to Score"),
            _mkt("Roma vs. Lazio: 1st Half Both Teams to Score", ["Yes", "No"],
                 [0.30, 0.70], "1st Half Both Teams to Score"),
        ],
    }
    ev_base = dict(BASE, markets=BASE["markets"])
    m = pm.build_soccer_matches([ev_base, ev])[0]
    assert m["over_under"]["2.5"] == {"over": 0.295, "under": 0.705}, "linea O/U sovrascritta"
    assert m["btts"] == {"yes": 0.60, "no": 0.40}, "BTTS sovrascritto dal primo tempo"


def test_full_match_label_filters():
    assert pm._full_match_label({"groupItemTitle": "O/U 2.5"}) == "O/U 2.5"
    assert pm._full_match_label({"groupItemTitle": "1st Half O/U 2.5"}) == "1st Half O/U 2.5"
    assert pm._OU_LABEL.match("O/U 2.5") is not None
    assert pm._OU_LABEL.match("1st Half O/U 2.5") is None
    assert pm._OU_LABEL.match("Roma O/U 2.5") is None
