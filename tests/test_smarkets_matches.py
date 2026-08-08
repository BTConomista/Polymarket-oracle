"""Test del raccoglitore Smarkets pre-partita (Fase 116).

Il download non e' testabile (rete), ma la parte che puo' rompersi in
silenzio si': **il riconoscimento della lega**. Raccogliere la seconda
divisione credendola la prima sarebbe dato sporco, non un errore visibile.

⚠️ Onesta' su cosa questi test proteggono davvero (verificato per mutazione,
Fase 116). La prima stesura diceva di difendere dal caso
`germany-2-bundesliga` scambiato per `germany-bundesliga` con un match
"contiene": quella collisione e' **strutturalmente impossibile** (il "2-" sta
in mezzo, quindi nemmeno `in` la produce) e la mutazione corrispondente NON
faceva fallire nulla. Cio' che i test proteggono per davvero e' il
**contratto con un'API esterna**: gli slug attesi sono fissati qui, quindi
una mappa corrotta o un rinominamento a valle rompono la suite invece di
farci raccogliere in silenzio la lega sbagliata (o niente). Verificato:
sostituendo una voce della mappa, 2 test falliscono.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_smarkets_matches import (  # noqa: E402
    LOTTO_MERCATI, MERCATI_BASE, MERCATI_PRINCIPALI, PERIMETRO, SLUG_LEGA,
    _etichetta_generica, _fascia, _libri_per_contratto, _slug_lega,
    anomalia_del_listino, entro_finestra, fuori_perimetro, leghe_assenti)


@pytest.mark.parametrize("slug,atteso", [
    ("/sport/football/italy-serie-a/2026/08/16/19-00/inter-vs-milan", "serie_a"),
    ("/sport/football/england-premier-league/2026/08/15/14-00/a-vs-b", "premier_league"),
    ("/sport/football/spain-laliga/2026/08/15/17-30/a-vs-b", "la_liga"),
    # Lo slug rinominato dal 31/07/2026: se questo caso non passasse, la Liga
    # tornerebbe a uscire dalla raccolta in silenzio.
    ("/sport/football/spain-la-liga/2026/08/15/17-30/a-vs-b", "la_liga"),
    ("/sport/football/germany-bundesliga/2026/08/22/13-30/a-vs-b", "bundesliga"),
    ("/sport/football/france-ligue-1/2026/08/16/19-00/a-vs-b", "ligue_1"),
])
def test_riconosce_le_cinque_leghe(slug, atteso):
    assert _slug_lega(slug) == atteso


@pytest.mark.parametrize("slug,lega,fascia", [
    # PERIMETRO ALLARGATO (Fase 142). Fino all'08/08/2026 questi erano tutti
    # `None` e il test si chiamava «scarta seconde divisioni e coppe»: era la
    # decisione di allora, non una verita'. Ora sono dentro, e il test dice
    # *con quale etichetta* -- perche' finire nell'archivio come `serie_a`
    # invece che `serie_b` sarebbe peggio che restare fuori.
    ("/sport/football/italy-serie-b/2026/08/22/13-30/a-vs-b", "serie_b", "seconda"),
    ("/sport/football/england-championship/2026/08/14/19-00/a-vs-b", "championship", "seconda"),
    ("/sport/football/germany-2-bundesliga/2026/08/08/18-30/a-vs-b", "bundesliga_2", "seconda"),
    ("/sport/football/spain-la-liga-2/2026/08/14/18-30/a-vs-b", "la_liga_2", "seconda"),
    ("/sport/football/france-ligue-2/2026/08/08/18-45/a-vs-b", "ligue_2", "seconda"),
    ("/sport/football/italy-coppa-italia/2026/08/08/18-00/a-vs-b", "coppa_italia", "coppa"),
    ("/sport/football/england-league-cup/2026/08/08/12-00/a-vs-b", "league_cup", "coppa"),
    ("/sport/football/uefa-champions-league-qualification/2026/08/11/15-00/a-vs-b",
     "ucl_qual", "coppa"),
    ("/sport/football/uefa-super-cup/2026/08/12/19-00/a-vs-b", "supercoppa_uefa", "coppa"),
    # attese: non ancora esposte l'08/08, dentro dal giorno che compaiono
    ("/sport/football/germany-dfb-pokal/2026/08/15/13-30/a-vs-b", "dfb_pokal", "coppa"),
    ("/sport/football/spain-copa-del-rey/2026/10/29/19-00/a-vs-b", "copa_del_rey", "coppa"),
])
def test_il_perimetro_allargato_entra_con_la_sua_etichetta(slug, lega, fascia):
    assert _slug_lega(slug) == lega
    assert _fascia(slug) == fascia


@pytest.mark.parametrize("slug", [
    "/sport/football/brazil-copa-do-brasil/2026/08/02/21-30/a-vs-b",   # altro paese
    "/sport/football/us-major-league-soccer/2026/08/08/20-30/a-vs-b",
    "/sport/football/england-league-1/2026/08/15/11-30/a-vs-b",        # terza serie
    "/sport/football/england-national-league/2026/08/08/14-00/a-vs-b",
    "/sport/football/germany-3-liga/2026/08/08/12-00/a-vs-b",
    "/sport/football/uefa-women-s-champions-league-qualification/2026/08/08/12-30/a-vs-b",
    "/sport/football/club-friendlies/2026/08/08/13-00/a-vs-b",
])
def test_resta_fuori_cio_che_non_abbiamo_scelto(slug):
    """Il perimetro si e' allargato, non aperto: il confine nuovo va fissato
    per iscritto esattamente come lo era il vecchio, o la prossima modifica
    lo sposta senza che nessuno lo noti."""
    assert _slug_lega(slug) is None
    assert _fascia(slug) is None


def test_il_radar_vede_una_coppa_col_nome_sbagliato():
    """Il caso che il radar esiste per prendere. Se la DFB-Pokal comparisse
    come `germany-dfb-cup` -- nome che NON abbiamo indovinato in SLUG_ATTESI --
    senza radar sparirebbe in silenzio, che e' esattamente com'e' andata con
    `spain-laliga` -> `spain-la-liga` il 31/07/2026."""
    listino = {"italy-serie-a": 10, "germany-dfb-cup": 32,
               "brazil-serie-a": 20,                      # altro paese: non ci riguarda
               "england-national-league-north": 12,       # nostro paese, ma escluso apposta
               "spain-women-liga-f": 8}                   # femminile: escluso apposta
    assert fuori_perimetro(listino) == {"germany-dfb-cup": 32}


def test_il_radar_tace_quando_non_c_e_niente_da_dire():
    """Un radar che segnala sempre e' un radar che non si legge piu'."""
    listino = {"italy-serie-a": 10, "italy-coppa-italia": 4,
               "italy-serie-b": 10, "brazil-serie-a": 20}
    assert fuori_perimetro(listino) == {}


def test_ogni_voce_del_perimetro_ha_fascia_valida():
    """Una fascia scritta male (un refuso) non darebbe errore: darebbe una
    riga che nessun filtro trova. Le fasce sono tre e sono queste."""
    for slug, (chiave, fascia) in PERIMETRO.items():
        assert fascia in ("coppa", "seconda"), f"{slug} ha fascia {fascia!r}"
        assert chiave and chiave == chiave.lower().strip()
    # e nessuno slug del perimetro allargato deve collidere coi 5 campionati,
    # o `leghe_assenti` si spegnerebbe da sola
    assert not set(PERIMETRO) & set(SLUG_LEGA)
    assert not {v[0] for v in PERIMETRO.values()} & set(SLUG_LEGA.values())


def test_slug_malformato_non_esplode():
    for s in (None, "", "/sport/tennis/atp/x", "non-uno-slug"):
        assert _slug_lega(s) is None


def test_le_leghe_dichiarate_sono_le_cinque_del_progetto():
    from src.config import LEAGUE_CONFIGS
    assert set(SLUG_LEGA.values()) == set(LEAGUE_CONFIGS)


def test_i_mercati_raccolti_sono_quelli_che_il_progetto_prezza():
    """Se un giorno Smarkets rinominasse un mercato, il raccoglitore lo
    salterebbe in silenzio: questo test fissa cosa ci aspettiamo di avere."""
    assert set(MERCATI_BASE.values()) == {
        "1x2", "ggng", "ou15", "ou25", "ou35", "risultato_esatto"}


def test_i_mercati_principali_sono_un_sottoinsieme_di_quelli_raccolti():
    """Il regime di lungo raggio filtra per ETICHETTA: se una delle principali
    non fosse fra quelle raccolte, filtrerebbe via tutto e il giro giornaliero
    scriverebbe file vuoti senza errori."""
    assert MERCATI_PRINCIPALI <= set(MERCATI_BASE.values())


# --- il listino: distinguere «finestra vuota» da «API muta» (R6) -----------

def test_listino_vuoto_e_anomalia():
    assert anomalia_del_listino(0, 0) is not None


def test_listino_senza_nessuna_delle_nostre_leghe_e_anomalia():
    """Il caso realistico: Smarkets rinomina uno slug di competizione, oppure
    filtra gli IP dei runner. Senza questo controllo il workflow resterebbe
    verde raccogliendo il nulla, e i dati pre-partita non tornano piu'."""
    assert anomalia_del_listino(709, 0) is not None


def test_una_lega_sparita_e_vista():
    """Il caso vero del 31/07/2026: 4 leghe su 5 nel file, la Liga assente
    perche' lo slug era stato rinominato. La guardia a soglia zero-su-cinque
    non lo vedeva -- il workflow era verde con 38 partite invece di 48."""
    nostre = [{"lega": lega, "fascia": "campionato"} for lega in
              ("serie_a", "premier_league", "bundesliga", "ligue_1")]
    assert leghe_assenti(nostre) == {"la_liga"}
    # E la guardia vecchia, da sola, continua a NON vederlo: e' proprio il
    # buco che `leghe_assenti` copre.
    assert anomalia_del_listino(850, len(nostre)) is None


def test_tutte_le_leghe_esposte_non_e_un_allarme():
    nostre = [{"lega": lega, "fascia": "campionato"} for lega in
              ("serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1")]
    assert leghe_assenti(nostre) == set()


def test_le_coppe_non_coprono_una_lega_sparita():
    """Il rischio nuovo del perimetro allargato (Fase 142): un file pieno di
    coppe e cadetterie NON deve far sembrare presente un campionato che non
    c'e'. Senza il filtro sulla fascia, bastava una collisione di chiave."""
    nostre = ([{"lega": lega, "fascia": "campionato"} for lega in
               ("serie_a", "premier_league", "bundesliga", "ligue_1")]
              + [{"lega": "coppa_italia", "fascia": "coppa"},
                 {"lega": "la_liga_2", "fascia": "seconda"}])
    assert leghe_assenti(nostre) == {"la_liga"}


def test_listino_normale_non_e_anomalia():
    """I numeri veri del 28/07/2026, off-season profonda: 709 eventi calcio,
    48 partite nostre gia' esposte. Nessuna in finestra a 72h -- ed e' proprio
    lo stato che NON deve essere scambiato per un guasto."""
    assert anomalia_del_listino(709, 48) is None


# --- la finestra temporale -------------------------------------------------

def _ev(giorni: float, nome: str = "a vs b") -> dict:
    inizio = _ADESSO + dt.timedelta(days=giorni)
    return {"nome": nome, "lega": "serie_a", "event_id": 1,
            "inizio": inizio.isoformat(), "_inizio": inizio}


_ADESSO = dt.datetime(2026, 7, 28, 12, 0, tzinfo=dt.timezone.utc)


def test_finestra_tiene_solo_cio_che_inizia_entro_n_ore():
    evs = [_ev(0.5, "vicina"), _ev(18, "lontana")]
    tenute = entro_finestra(evs, 72, adesso=_ADESSO)
    assert [e["nome"] for e in tenute] == ["vicina"]


def test_finestra_non_positiva_prende_tutto():
    """`--tutte-le-esposte` passa 0: e' il regime di lungo raggio, quello che
    salva la traiettoria dell'esordio nelle settimane prima del via."""
    evs = [_ev(0.5), _ev(18), _ev(33)]
    assert len(entro_finestra(evs, 0, adesso=_ADESSO)) == 3


def test_il_bordo_della_finestra_e_incluso():
    """Esattamente 72h: dentro. Un `<` al posto di `<=` perderebbe in modo
    intermittente le partite raccolte all'ora esatta del giro precedente."""
    assert len(entro_finestra([_ev(3.0)], 72, adesso=_ADESSO)) == 1


# --------------------------------------------------------------------------
# Il listino intero (Fase 135): batching e etichette stabili
# --------------------------------------------------------------------------

def test_etichetta_generica_e_stabile_fra_partite():
    """L'etichetta di un mercato NON deve contenere i nomi delle squadre.

    Ricavarla dal nome visualizzato dava «alaves_0_5_corners_getafe_0_5_corners»:
    360 "tipi" su 6 partite invece di ~100, cioe' un archivio che nessun
    raggruppamento puo' leggere. Si usa `market_type.name` (+ `param`), che
    l'API garantisce stabile.
    """
    casa = {"market_type": {"name": "CORNERS_HANDICAP", "param": 0.5}}
    trasf = {"market_type": {"name": "CORNERS_HANDICAP", "param": 0.5}}
    a = _etichetta_generica(casa, "Alaves 0.5 corners / Getafe 0.5 corners")
    b = _etichetta_generica(trasf, "Celta 0.5 corners / Osasuna 0.5 corners")
    assert a == b == "corners_handicap_0_5"
    # niente nomi squadra
    for squadra in ("alaves", "getafe", "celta", "osasuna"):
        assert squadra not in a

    # linee diverse restano mercati diversi
    altra = _etichetta_generica(
        {"market_type": {"name": "CORNERS_HANDICAP", "param": 1.5}}, "x")
    assert altra != a

    # senza market_type si ripiega sul nome, invece di produrre un'etichetta vuota
    assert _etichetta_generica({}, "Qualcosa Strano") == "qualcosa_strano"


def test_libri_per_contratto_regge_entrambe_le_forme():
    """/quotes/ risponde in DUE modi: annidato per mercato con un ID solo,
    piatto per contratto quando gli ID sono a lotti. Verificato dal vivo."""
    piatto = {"111": {"bids": [], "offers": []}, "222": {"bids": [], "offers": []}}
    assert _libri_per_contratto(piatto) == piatto

    annidato = {"999": {"111": {"bids": [], "offers": []}}}
    assert _libri_per_contratto(annidato) == {"111": {"bids": [], "offers": []}}

    assert _libri_per_contratto({}) == {}


def test_il_lotto_e_dichiarato_e_ragionevole():
    """Senza batching il listino intero non sta in nessun budget di tempo:
    221 richieste per partita contro 13. Il numero non e' magico ma dev'esserci
    ed essere > 1, altrimenti il batching non esiste."""
    assert LOTTO_MERCATI > 1
    assert LOTTO_MERCATI <= 50      # oltre, l'URL diventa troppo lungo


def test_nessuno_legge_l_archivio_a_mano():
    """Chi glob-a `smarkets_matches/*.json` si perde i `.json.gz`, in silenzio.

    Dalla Fase 136 l'archivio ha due estensioni: `.json` per cio' che c'era gia'
    e `.json.gz` per il nuovo. Un lettore che continua a globare solo `*.json`
    non fallisce -- legge di MENO, che e' il difetto peggiore (R6). E uno che
    legge col `read_text()` esplode su un file compresso. L'unico modo di non
    ricascarci e' che nessuno lo faccia a mano: si passa da
    `src/data/smarkets_archive.py`.

    Questo test e' la guardia: se qualcuno riapre la scorciatoia, la suite si
    rompe subito invece che il giorno in cui l'archivio conta davvero.
    """
    import re

    radice = Path(__file__).resolve().parents[1]
    sospetti = []
    for cartella in ("scripts", "src", "tests"):
        for f in (radice / cartella).rglob("*.py"):
            if f.name == "smarkets_archive.py":
                continue          # e' lui il posto giusto
            testo = f.read_text(encoding="utf-8")
            for riga in testo.splitlines():
                if "smarkets_matches" in riga and re.search(r'glob\(|"\*\.json"', riga):
                    sospetti.append(f"{f.relative_to(radice)}: {riga.strip()[:90]}")
    assert not sospetti, (
        "questi leggono l'archivio Smarkets a mano e si perderanno i .json.gz:\n"
        + "\n".join(sospetti))


# ---------------------------------------------------------------------------
# RESILIENZA DELLA RACCOLTA (08/08/2026)
#
# Il giro di lungo raggio delle 06:24 e' morto su un `HTTP Error 503: Service
# Unavailable` alla 22a partita su 58, portandosi via le 21 gia' raccolte: mai
# scritte, mai committate. Tre difetti in fila, e questi test tengono chiusi
# tutti e tre:
#   1. `_get` riprovava sul 429 ma non sui 5xx, che sono transitori uguale;
#   2. l'eccezione di UNA partita usciva dal ciclo e uccideva l'intero giro;
#   3. anche uscendo rossi dopo aver scritto, il passo di commit del workflow
#      veniva saltato e il file moriva sul runner (`if: always()`, testato in
#      test_workflow_smarkets_commit_anche_se_la_raccolta_fallisce).
# ---------------------------------------------------------------------------

import urllib.error   # noqa: E402
import urllib.request  # noqa: E402

import fetch_smarkets_matches as fsm   # noqa: E402
import fetch_smarkets_outrights as fso  # noqa: E402


class _Risposta:
    """Il minimo che serve a `_get`: un context manager con `.read()`."""

    def __init__(self, corpo: bytes):
        self._corpo = corpo

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self._corpo


def _errore(codice: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", codice, "boom", {}, None)


@pytest.fixture
def _senza_attese(monkeypatch):
    """Toglie di mezzo throttle e backoff: qui si misura la LOGICA dei
    tentativi, non il tempo che aspettano."""
    monkeypatch.setattr(fso.time, "sleep", lambda _s: None)


@pytest.mark.parametrize("codice", sorted(fso.HTTP_TRANSITORI))
def test_get_riprova_sui_codici_transitori(codice, monkeypatch, _senza_attese):
    """503 compreso: e' letteralmente il codice che ha ucciso il giro."""
    tentativi = []

    def finto(url, timeout=None):
        tentativi.append(url)
        if len(tentativi) < 3:
            raise _errore(codice)
        return _Risposta(b'{"ok": true}')

    monkeypatch.setattr(urllib.request, "urlopen", finto)
    assert fso._get("/events/") == {"ok": True}
    assert len(tentativi) == 3


@pytest.mark.parametrize("codice", [400, 401, 403, 404, 422])
def test_get_non_riprova_sugli_errori_di_richiesta(codice, monkeypatch, _senza_attese):
    """Un 404 non diventa un 200 riprovando: insistere nasconderebbe un bug
    nostro dietro cinque tentativi e venti secondi."""
    tentativi = []

    def finto(url, timeout=None):
        tentativi.append(url)
        raise _errore(codice)

    monkeypatch.setattr(urllib.request, "urlopen", finto)
    with pytest.raises(urllib.error.HTTPError):
        fso._get("/events/")
    assert len(tentativi) == 1


def test_get_si_arrende_dopo_i_tentativi(monkeypatch, _senza_attese):
    """Un guasto che dura non deve diventare un ciclo infinito, ne' un `{}`
    silenzioso: deve propagare, cosi' chi chiama lo dichiara."""
    tentativi = []

    def finto(url, timeout=None):
        tentativi.append(url)
        raise _errore(503)

    monkeypatch.setattr(urllib.request, "urlopen", finto)
    with pytest.raises(urllib.error.HTTPError):
        fso._get("/events/", retries=4)
    assert len(tentativi) == 4


_EVENTO = {"event_id": 1, "nome": "Inter vs Milan", "lega": "serie_a",
           "inizio": "2026-08-22T16:30:00Z",
           "_inizio": dt.datetime(2026, 8, 22, 16, 30, tzinfo=dt.timezone.utc)}


def _finto_get(guasti=()):
    """Un `_get` finto: due mercati, un contratto ciascuno. `guasti` elenca i
    frammenti di URL che devono fallire con un 503."""
    def get(path):
        if any(g in path for g in guasti):
            raise _errore(503)
        if path.endswith("/markets/"):
            return {"markets": [{"id": 10, "name": "Full-time result"},
                                {"id": 11, "name": "Both teams to score"}]}
        if "/contracts/" in path:
            ids = path.split("/markets/")[1].split("/")[0].split(",")
            return {"contracts": [{"id": 100 + int(i), "market_id": int(i),
                                   "name": "c"} for i in ids]}
        return {str(100 + int(i)): {"bids": [], "offers": []}
                for i in path.split("/markets/")[1].split("/")[0].split(",")}
    return get


def test_quote_partita_dichiara_i_mercati_persi(monkeypatch):
    """Un lotto che non arriva costa i suoi mercati, non la partita -- e il
    conto torna indietro a chi chiama, perche' un raccolto parziale che si
    spaccia per completo e' il «finto pieno» di R6."""
    monkeypatch.setattr(fsm, "LOTTO_MERCATI", 1)      # un mercato per lotto
    monkeypatch.setattr(fsm, "_get", _finto_get(guasti=("/markets/11/",)))
    righe, persi = fsm.quote_partita(_EVENTO, tutti=False)
    assert persi == 1
    assert [r["mercato"] for r in righe] == ["1x2"]   # l'altro e' salvo


def test_quote_partita_senza_guasti_non_perde_nulla(monkeypatch):
    monkeypatch.setattr(fsm, "_get", _finto_get())
    righe, persi = fsm.quote_partita(_EVENTO, tutti=False)
    assert persi == 0
    assert {r["mercato"] for r in righe} == {"1x2", "ggng"}


def _tre_partite():
    base = dt.datetime(2026, 8, 22, 16, 30, tzinfo=dt.timezone.utc)
    return [{"event_id": i, "nome": f"A{i} vs B{i}", "lega": "serie_a",
             "fascia": "campionato", "inizio": base.isoformat(),
             # inizi CRESCENTI: dalla Fase 142 il ciclo raccoglie in ordine di
             # calcio d'inizio, e il test del budget si appoggia a quell'ordine
             "_inizio": base + dt.timedelta(hours=i)} for i in (1, 2, 3)]


def _prepara_main(monkeypatch, tmp_path, quote):
    """Aggancia `main` a tre partite finte e a una cartella temporanea."""
    monkeypatch.setattr(fsm, "scandaglia_upcoming",
                        lambda: (_tre_partite(), 700, {"italy-serie-a": 3}))
    monkeypatch.setattr(fsm, "leghe_assenti", lambda _n: set())
    monkeypatch.setattr(fsm, "quote_partita", quote)
    monkeypatch.setattr(fsm, "DEST", tmp_path)


def _letto(tmp_path):
    from src.data import smarkets_archive
    files = sorted(tmp_path.iterdir())
    assert len(files) == 1, f"atteso un file solo, trovati {files}"
    return smarkets_archive.leggi(files[0])


def test_una_partita_persa_non_porta_via_le_altre(monkeypatch, tmp_path):
    """IL BUG DELL'08/08/2026, in una riga: la seconda partita esplode e le
    altre due devono comunque finire su disco."""
    def quote(ev, tutti, solo_principali=False):
        if ev["event_id"] == 2:
            raise _errore(503)
        return [{"partita": ev["nome"], "mercato": "1x2"}], 0

    _prepara_main(monkeypatch, tmp_path, quote)
    with pytest.raises(SystemExit):      # incompleta: si esce rossi, ma DOPO
        fsm.main(["--entro-ore", "0"])

    dati = _letto(tmp_path)
    assert {r["partita"] for r in dati["righe"]} == {"A1 vs B1", "A3 vs B3"}
    # e il buco e' DICHIARATO nel file, non solo nei log
    assert [x["partita"] for x in dati["partite_incomplete"]] == ["A2 vs B2"]
    assert dati["partite_incomplete"][0]["mercati_persi"] == "tutti"


def test_raccolta_completa_esce_verde_e_senza_buchi(monkeypatch, tmp_path):
    _prepara_main(monkeypatch, tmp_path,
                  lambda ev, tutti, solo_principali=False:
                  ([{"partita": ev["nome"], "mercato": "1x2"}], 0))
    fsm.main(["--entro-ore", "0"])       # nessun SystemExit
    dati = _letto(tmp_path)
    assert len(dati["righe"]) == 3
    assert dati["partite_incomplete"] == []


def test_qualche_mercato_perso_e_dichiarato_ma_non_fa_fallire(monkeypatch, tmp_path):
    """Rosso solo per una partita persa INTERA. Qualche mercato mancante
    lascia la traiettoria leggibile ed e' gia' scritto nel file: farne una
    mail rossa insegna solo a non leggere le mail rosse."""
    _prepara_main(monkeypatch, tmp_path,
                  lambda ev, tutti, solo_principali=False:
                  ([{"partita": ev["nome"], "mercato": "1x2"}], 4))
    fsm.main(["--entro-ore", "0"])
    dati = _letto(tmp_path)
    assert len(dati["righe"]) == 3
    assert [x["mercati_persi"] for x in dati["partite_incomplete"]] == [4, 4, 4]


def test_zero_righe_su_partite_in_finestra_e_un_fallimento(monkeypatch, tmp_path):
    """Se NESSUNA quota arriva non si scrive un file vuoto: sarebbe
    indistinguibile da un'off-season, e l'archivio non deve mai contenere un
    silenzio che sembra un dato (R6)."""
    def quote(ev, tutti, solo_principali=False):
        raise _errore(503)

    _prepara_main(monkeypatch, tmp_path, quote)
    with pytest.raises(SystemExit, match="raccolta FALLITA"):
        fsm.main(["--entro-ore", "0"])
    assert list(tmp_path.iterdir()) == []


def test_budget_esaurito_salva_il_raccolto_e_dichiara_il_resto(monkeypatch, tmp_path):
    """Il contrappeso ai tentativi: se l'API e' giu' a lungo, ogni chiamata
    costa fino a 45s e il giro non finirebbe piu'. Allo scadere si scrive cio'
    che si ha, e le partite non raccolte sono dichiarate una per una."""
    _prepara_main(monkeypatch, tmp_path,
                  lambda ev, tutti, solo_principali=False:
                  ([{"partita": ev["nome"], "mercato": "1x2"}], 0))

    # l'orologio avanza di un'ora a ogni lettura: la prima partita passa,
    # dalla seconda il budget e' gia' scaduto
    orologio = iter([dt.datetime(2026, 8, 8, 6, h, tzinfo=dt.timezone.utc)
                     for h in (0, 1, 59, 59, 59, 59)])

    class _Dt(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return next(orologio)

    monkeypatch.setattr(fsm.dt, "datetime", _Dt)
    with pytest.raises(SystemExit, match="budget|INCOMPLETA"):
        fsm.main(["--entro-ore", "0", "--budget-minuti", "45"])

    dati = _letto(tmp_path)
    assert [r["partita"] for r in dati["righe"]] == ["A1 vs B1"]
    assert [x["partita"] for x in dati["partite_incomplete"]] == \
        ["A2 vs B2", "A3 vs B3"]
    assert all("budget" in x["errore"] for x in dati["partite_incomplete"])


def test_workflow_smarkets_commit_anche_se_la_raccolta_fallisce():
    """Il terzo difetto dell'08/08/2026, e il piu' beffardo: lo script scrive
    il file PRIMA di uscire rosso apposta («i dati sono comunque salvati»), ma
    in GitHub Actions un passo fallito SALTA quelli dopo -- quindi il commit
    non avveniva e l'allarme costava esattamente i dati che proteggeva.

    Il test legge il workflow: il passo che salva deve avere un `if:` che
    sopravvive al fallimento del passo prima.
    """
    testo = (Path(__file__).resolve().parents[1]
             / ".github" / "workflows" / "smarkets-prematch.yml").read_text()
    salva = testo.split("- name: Salva lo snapshot")[1].split("run: |")[0]
    assert "!cancelled()" in salva or "always()" in salva, (
        "il passo di commit verrebbe saltato quando la raccolta esce rossa, "
        "e il file scritto morirebbe sul runner")


# ---------------------------------------------------------------------------
# PERIMETRO ALLARGATO — il rischio non e' raccogliere di piu': e' che qualcosa
# a valle scambi una coppa per un campionato senza dare errore (Fase 142).
# ---------------------------------------------------------------------------

def _perimetro_misto():
    base = dt.datetime(2026, 8, 22, 16, 30, tzinfo=dt.timezone.utc)
    return [
        {"event_id": 1, "nome": "Inter vs Milan", "lega": "serie_a",
         "fascia": "campionato", "inizio": base.isoformat(), "_inizio": base},
        {"event_id": 2, "nome": "Vicenza vs Catania", "lega": "coppa_italia",
         "fascia": "coppa", "inizio": base.isoformat(),
         "_inizio": base + dt.timedelta(hours=1)},
        {"event_id": 3, "nome": "Vicenza vs Catanzaro", "lega": "serie_b",
         "fascia": "seconda", "inizio": base.isoformat(),
         "_inizio": base + dt.timedelta(hours=2)},
    ]


def test_ogni_riga_porta_la_sua_fascia(monkeypatch, tmp_path):
    """Senza `fascia` sulla riga, un lettore che raggruppa per `lega` mette
    Vicenza-Catania fra le partite di Serie A e non se ne accorge."""
    monkeypatch.setattr(fsm, "scandaglia_upcoming",
                        lambda: (_perimetro_misto(), 865,
                                 {"italy-serie-a": 10, "italy-coppa-italia": 4}))
    monkeypatch.setattr(fsm, "leghe_assenti", lambda _n: set())
    monkeypatch.setattr(fsm, "quote_partita",
                        lambda ev, tutti, solo_principali=False:
                        ([{"partita": ev["nome"], "lega": ev["lega"],
                           "fascia": ev["fascia"], "mercato": "1x2"}], 0))
    monkeypatch.setattr(fsm, "DEST", tmp_path)
    fsm.main(["--entro-ore", "0"])

    dati = _letto(tmp_path)
    assert {r["fascia"] for r in dati["righe"]} == {"campionato", "coppa", "seconda"}
    assert dati["partite_per_fascia"] == {"campionato": 1, "coppa": 1, "seconda": 1}
    assert ["coppa", "coppa_italia"] in [list(x) for x in dati["perimetro"]]


def test_il_radar_finisce_nel_file_non_solo_nel_log(monkeypatch, tmp_path):
    """Un avviso che vive solo nei log di GitHub Actions scade con i log. Se
    domani compare una coppa col nome che non avevamo previsto, deve restare
    scritto nel file che quel giorno c'era e non l'abbiamo presa."""
    monkeypatch.setattr(fsm, "scandaglia_upcoming",
                        lambda: (_perimetro_misto(), 865,
                                 {"italy-serie-a": 10, "germany-dfb-cup": 32}))
    monkeypatch.setattr(fsm, "leghe_assenti", lambda _n: set())
    monkeypatch.setattr(fsm, "quote_partita",
                        lambda ev, tutti, solo_principali=False:
                        ([{"partita": ev["nome"], "mercato": "1x2"}], 0))
    monkeypatch.setattr(fsm, "DEST", tmp_path)
    fsm.main(["--entro-ore", "0"])
    assert _letto(tmp_path)["fuori_perimetro"] == {"germany-dfb-cup": 32}


def test_le_coppe_non_fanno_passare_un_listino_senza_campionati(monkeypatch, tmp_path):
    """La guardia R6 dev'essere immune al perimetro allargato: se sparissero
    tutti e 5 i campionati e restassero le coppe, il giro deve FALLIRE. Prima
    del filtro sulla fascia sarebbe uscito verde con un file pieno di coppe."""
    solo_coppe = [e for e in _perimetro_misto() if e["fascia"] != "campionato"]
    monkeypatch.setattr(fsm, "scandaglia_upcoming",
                        lambda: (solo_coppe, 865, {"italy-coppa-italia": 4}))
    monkeypatch.setattr(fsm, "DEST", tmp_path)
    with pytest.raises(SystemExit, match="ANOMALIA"):
        fsm.main(["--entro-ore", "0"])
    assert list(tmp_path.iterdir()) == []


def test_si_raccoglie_in_ordine_di_calcio_d_inizio(monkeypatch, tmp_path):
    """Se il budget scade si perde la CODA: la coda dev'essere cio' che manca
    di piu'. Una partita fra tre settimane la ri-prendiamo domani, una che
    comincia fra un'ora no. L'API restituisce in ordine arbitrario."""
    base = dt.datetime(2026, 8, 22, 16, 30, tzinfo=dt.timezone.utc)
    disordinate = [
        {"event_id": 9, "nome": "tardi vs x", "lega": "serie_a", "fascia": "campionato",
         "inizio": "z", "_inizio": base + dt.timedelta(days=20)},
        {"event_id": 1, "nome": "subito vs y", "lega": "serie_a", "fascia": "campionato",
         "inizio": "a", "_inizio": base},
    ]
    ordine = []
    monkeypatch.setattr(fsm, "scandaglia_upcoming",
                        lambda: (disordinate, 865, {"italy-serie-a": 2}))
    monkeypatch.setattr(fsm, "leghe_assenti", lambda _n: set())
    monkeypatch.setattr(fsm, "quote_partita",
                        lambda ev, tutti, solo_principali=False:
                        (ordine.append(ev["nome"]) or
                         [{"partita": ev["nome"], "mercato": "1x2"}], 0))
    monkeypatch.setattr(fsm, "DEST", tmp_path)
    fsm.main(["--entro-ore", "0"])
    assert ordine == ["subito vs y", "tardi vs x"]


def test_archivio_non_scambia_le_coppe_per_leghe(tmp_path):
    """`ultimo_listino_completo` cerca il file che copre tutte e 5 le leghe.
    Contando anche coppe e cadetterie, un file con DUE campionati e quattro
    coppe supererebbe la soglia di cinque travestito da listino completo."""
    from src.data import smarkets_archive as arch

    def scrivi(nome, righe):
        arch.scrivi(tmp_path / nome, {"righe": righe})

    finto_pieno = ([{"lega": l, "fascia": "campionato"} for l in ("serie_a", "la_liga")]
                   + [{"lega": c, "fascia": "coppa"} for c in
                      ("coppa_italia", "league_cup", "ucl_qual", "supercoppa_uefa")])
    vero_pieno = [{"lega": l, "fascia": "campionato"} for l in
                  ("serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1")]
    scrivi("2026-08-08T10-00-00.json", vero_pieno)
    scrivi("2026-08-08T11-00-00.json", finto_pieno)      # piu' recente, ma parziale

    assert arch.ultimo_listino_completo(tmp_path).name == "2026-08-08T10-00-00.json.gz"


def test_archivio_legge_ancora_i_file_pre_fase_142(tmp_path):
    """Retrocompatibilita': i file gia' in archivio non hanno `fascia` e sono
    tutti e soli campionati. L'assenza del campo deve valere `campionato`,
    altrimenti l'archivio storico diventa illeggibile da un giorno all'altro."""
    from src.data import smarkets_archive as arch
    arch.scrivi(tmp_path / "2026-08-01T10-00-00.json",
                {"righe": [{"lega": l} for l in
                           ("serie_a", "premier_league", "la_liga",
                            "bundesliga", "ligue_1")]})
    assert arch.ultimo_listino_completo(tmp_path).name == "2026-08-01T10-00-00.json.gz"


def test_ogni_input_del_workflow_e_davvero_usato():
    """Un input dichiarato e mai letto e' peggio di un input assente: nella
    UI di GitHub c'e' la casella, la si spunta, e non succede niente.

    Pagato l'08/08/2026: aggiunto `tutti_i_mercati` per poter forzare a mano
    il regime di chiusura (il cron orario parte con 30-40 min di ritardo), e
    committato SENZA collegarlo al comando. La casella c'era e non faceva
    nulla -- un guasto che nessun test del codice Python puo' vedere, perche'
    il difetto sta fra il YAML e se stesso.
    """
    import re

    testo = (Path(__file__).resolve().parents[1]
             / ".github" / "workflows" / "smarkets-prematch.yml").read_text()
    blocco = testo.split("workflow_dispatch:")[1].split("permissions:")[0]
    # gli input sono le chiavi a 6 spazi d'indentazione dentro `inputs:`
    dichiarati = re.findall(r"^      (\w+):$", blocco.split("inputs:")[1], re.M)
    assert dichiarati, "nessun input trovato: il parsing del workflow e' rotto"

    corpo = testo.split("jobs:")[1]
    non_usati = [i for i in dichiarati if f"inputs.{i}" not in corpo]
    assert not non_usati, (
        f"input dichiarati e mai letti dal job: {non_usati}. Nella UI di "
        f"GitHub compare la casella e spuntarla non produce alcun effetto.")
