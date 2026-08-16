"""Test dello scheletro giornaliero e delle rose da Wikipedia (Fasi 121/122).

Le due cose che qui possono rompersi in silenzio, e che i test presidiano:

1. **«zero raccolte» deve restare distinguibile da «non ha girato»** — la
   lezione della Fase 118, che qui costa di più: il dato pre-partita non si
   recupera. Perciò il meteo che *non esiste ancora* (partita oltre l'orizzonte
   di previsione) non è un errore, e il registro deve annotare anche i fetch
   falliti;
2. **il conteggio della rosa** — al Napoli la voce elenca 26 tesserati con
   numero e 21 giovani aggregati senza: contarli insieme era il difetto che
   rendeva `rosa_n` illeggibile (Fase 120).
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_rose_wikipedia import (  # noqa: E402
    _pulisci_data, _titolo_plausibile, leggi_rosa)
from raccolta_giornaliera import (  # noqa: E402
    METEO_ORIZZONTE_GIORNI, Registro, meteo_partita)


# --- il meteo che non esiste ancora NON è un guasto -----------------------

def _fra(giorni: int) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=giorni, hours=2)


def test_partita_oltre_l_orizzonte_non_e_un_errore():
    """Misurato il 28/07/2026: open-meteo copre 16 giorni e oltre risponde
    400. Una partita a 18 giorni non ha previsione perché la previsione **non
    esiste**, non perché il fetch è fallito: va scritto come tale, o fra mesi
    nessuno saprà distinguere i due casi."""
    reg = Registro()
    esito = meteo_partita(reg, 45.47, 9.12, _fra(METEO_ORIZZONTE_GIORNI + 2))
    assert esito["stato"] == "fuori_orizzonte"
    assert esito["giorni_mancanti"] > METEO_ORIZZONTE_GIORNI
    assert reg.voci == [], "non deve nemmeno chiamare l'API: sa già che non c'è"


def test_dentro_l_orizzonte_il_fetch_si_tenta():
    """L'altra metà: dentro l'orizzonte la richiesta si fa davvero. Senza
    questo, un bug che mettesse tutto «fuori orizzonte» non lo vedrebbe
    nessuno — il raccoglitore resterebbe verde e vuoto per sempre."""
    reg = Registro()
    chiamate = []
    reg.get = lambda url, **kw: chiamate.append(url) or None   # type: ignore
    meteo_partita(reg, 45.47, 9.12, _fra(1))
    assert len(chiamate) == 1 and "open-meteo" in chiamate[0]


# --- il registro delle fonti ---------------------------------------------

def test_il_registro_annota_anche_i_fallimenti():
    """`fonti.json` esiste per distinguere «non è successo niente» da «non ha
    girato»: se annotasse solo i successi, un giorno di API morta sarebbe
    indistinguibile da un giorno tranquillo."""
    reg = Registro()
    assert reg.get("https://esempio.invalido/x", timeout=2) is None
    assert len(reg.voci) == 1 and reg.falliti == 1
    voce = reg.voci[0]
    assert voce["esito"] != "ok" and "quando_utc" in voce and "durata_s" in voce


# --- la rosa: numerati vs giovani aggregati -------------------------------

WIKITEXT = """
== Rosa ==
''Rosa e numerazione aggiornate al 26 luglio 2026.''
{{Calciatore in rosa/inizio}}
{{Calciatore in rosa|n=1|nazione=ITA|nome=[[Alex Meret]]|ruolo=P}}
{{Calciatore in rosa|n=3|nazione=ESP|nome=[[Miguel Gutiérrez (calciatore 2001)|Miguel Gutiérrez]]|ruolo=D}}
{{Calciatore in rosa|n=|nazione=ITA|nome=Raffaele Colella|ruolo=D}}
{{Calciatore in rosa/fine}}
"""


def test_legge_numero_ruolo_e_nazione():
    rosa = leggi_rosa(WIKITEXT)
    assert len(rosa) == 3
    assert rosa[0] == {"nome": "Alex Meret", "numero": 1, "ruolo": "P", "nazione": "ITA"}


def test_il_wikilink_con_disambigua_da_il_nome_leggibile():
    """`[[Miguel Gutiérrez (calciatore 2001)|Miguel Gutiérrez]]` deve dare il
    nome visualizzato, non il titolo della voce con la disambigua: è la stringa
    su cui si farà il join con le altre fonti."""
    assert leggi_rosa(WIKITEXT)[1]["nome"] == "Miguel Gutiérrez"


def test_il_giovane_aggregato_ha_numero_None():
    """Il discrimine prima squadra / primavera è il numero di maglia, ed è un
    dato della fonte, non una soglia inventata da noi."""
    rosa = leggi_rosa(WIKITEXT)
    assert rosa[2]["numero"] is None
    assert sum(1 for g in rosa if g["numero"] is not None) == 2


# --- la voce giusta, non la competizione ---------------------------------

def test_scarta_la_pagina_della_competizione():
    """Cercando «Paris Saint-Germain 2026-2027» il primo risultato era *UEFA
    Champions League 2026-2027*: contiene la stagione e nessuna rosa."""
    assert not _titolo_plausibile("UEFA Champions League 2026-2027",
                                  ["Paris Saint-Germain"])
    assert not _titolo_plausibile("Serie A 2026-2027", ["Inter Milan"])


def test_accetta_la_voce_del_club():
    assert _titolo_plausibile("Football Club Internazionale Milano 2026-2027",
                              ["Inter Milan", "Inter Milano"])
    assert _titolo_plausibile("Real Madrid Club de Fútbol 2026-2027",
                              ["Real Madrid"])


def test_serve_la_stagione_giusta():
    """Una voce di un'altra stagione dello stesso club non va bene: sarebbe la
    rosa dell'anno scorso, cioè un dato sbagliato che sembra giusto."""
    assert not _titolo_plausibile("Football Club Internazionale Milano 2025-2026",
                                  ["Inter Milano"])


def test_pulisce_la_data_dichiarata():
    assert _pulisci_data("26 luglio 2026''") == "26 luglio 2026"
    assert _pulisci_data("13 luglio 2026))") == "13 luglio 2026"
    assert _pulisci_data("{{data|18|07|2026}}") == "18/07/2026"
    assert _pulisci_data(None) is None


# --------------------------------------------------------------------------
# Il guasto del 31/07/2026: la borsa rinomina, il join si rompe in silenzio
# --------------------------------------------------------------------------

def test_il_join_col_listino_non_dipende_dalla_convenzione_di_smarkets():
    """Fra il 30 e il 31/07/2026 Smarkets e' passata dai nomi formali a quelli
    brevi, e il join anagrafiche-listino e' crollato da 96/96 a 32/96 **senza
    che niente fallisse**: il giro restava verde e il meteo usciva
    `coordinate_mancanti` perche' l'anagrafica non si agganciava piu'.

    La correzione e' canonicalizzare ENTRAMBI i lati con la mappa che il
    progetto gia' ha. Il test lo verifica dove conta: sul listino vero.
    """
    import importlib.util
    from pathlib import Path

    radice = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "rg", radice / "scripts" / "raccolta_giornaliera.py")
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)

    partite = rg.prossime_partite(30)
    if not partite:
        pytest.skip("nessuna partita in finestra: niente da agganciare")
    schede = rg._schede_club()
    squadre = ({(p["lega"], p["casa"]) for p in partite}
               | {(p["lega"], p["ospite"]) for p in partite})

    # ⚠️ La proprieta' si verifica DOVE l'anagrafica esiste (rettifica Fase 145).
    # Da quando il listino comprende coppe, preliminari UEFA e cadetterie
    # (Fase 142), la maggioranza delle squadre viene da competizioni che
    # un'anagrafica di club non ce l'hanno proprio: pretenderla li' faceva
    # fallire questo test per un motivo che con la rinomina di Smarkets non
    # c'entra nulla — ed era rosso su `main`. Il difetto che il test deve
    # ancora vedere e' l'altro: una squadra senza scheda in una lega che le
    # schede ce l'ha.
    leghe_con_anagrafica = {lega for lega, _ in schede}
    coperte = [(l, n) for l, n in squadre if l in leghe_con_anagrafica]
    assert coperte, "nessuna squadra delle leghe modellate nel listino"
    orfane = [f"{l}/{n}" for l, n in coperte if (l, rg._canonico(n)) not in schede]
    assert not orfane, f"{len(orfane)}/{len(coperte)} squadre senza anagrafica: {orfane[:10]}"


def test_la_guardia_scatta_se_gli_alias_spariscono(monkeypatch):
    """Controprova con denti: senza la mappa alias il join DEVE rompersi.

    Un test che passa sia col rimedio sia senza non dimostrerebbe niente —
    e' la stessa trappola che il repo ha gia' incontrato piu' volte.
    """
    import importlib.util
    from pathlib import Path

    from src.data import sources

    radice = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "rg2", radice / "scripts" / "raccolta_giornaliera.py")
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)

    partite = rg.prossime_partite(30)
    if not partite:
        pytest.skip("nessuna partita in finestra")
    monkeypatch.setattr(sources, "TEAM_ALIASES", {})
    schede = rg._schede_club()
    squadre = ({(p["lega"], p["casa"]) for p in partite}
               | {(p["lega"], p["ospite"]) for p in partite})
    orfane = [1 for l, n in squadre if (l, rg._canonico(n)) not in schede]
    assert orfane, "senza alias il join dovrebbe rompersi, e non si rompe"


def test_il_giorno_si_committa_anche_se_la_guardia_ha_fatto_fallire_il_giro():
    """Fase 156-ter, pagata con due giorni di archivio.

    Il raccoglitore scrive il giorno e POI esce 1 se trova squadre senza
    anagrafica. Senza `if: !cancelled()` sul passo di commit, quel file muore
    col container: il 9 e il 10 agosto 2026 il log dice «scritto
    data/.../2026-08-10/» e non c'e' nessun commit -- sono gli unici due giorni
    mancanti dell'archivio. La guardia deve far suonare l'allarme, non
    cancellare il dato gia' raccolto (lezione della Fase 141).
    """
    import yaml
    from pathlib import Path

    wf = yaml.safe_load((Path(__file__).resolve().parents[1] / ".github"
                         / "workflows" / "raccolta-giornaliera.yml").read_text())
    passi = wf["jobs"]["raccogli"]["steps"]
    salva = [s for s in passi if "Salva" in (s.get("name") or "")]
    assert salva, "manca il passo che committa il giorno"
    cond = str(salva[0].get("if", ""))
    assert "cancelled" in cond, (
        "il passo di commit non gira dopo un passo fallito: il giorno gia' "
        f"scritto verrebbe buttato via (if attuale: {cond!r})")
