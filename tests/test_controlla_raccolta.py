"""Test del cane da guardia (Fase 144).

Un guardiano che non suona quando deve e' peggio di nessun guardiano: da' la
sensazione di essere coperti. Quindi qui si verifica soprattutto il caso
POSITIVO — che il rilevatore scatti — su ognuno dei quattro buchi che sa
vedere, e il caso negativo su un archivio sano (un allarme che suona sempre
si smette di leggere, ed e' l'altro modo di non funzionare).
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import controlla_raccolta as cr   # noqa: E402
from src.data import smarkets_archive as arch   # noqa: E402


UTC = dt.timezone.utc
ADESSO = dt.datetime(2026, 8, 8, 20, 0, tzinfo=UTC)


def _scrivi(cartella: Path, quando: dt.datetime, dati: dict) -> None:
    cartella.mkdir(parents=True, exist_ok=True)
    arch.scrivi(cartella / f"{quando.strftime('%Y-%m-%dT%H-%M-%S')}.json", dati)


def _riga(partita: str, kickoff: dt.datetime) -> dict:
    return {"partita": partita, "lega": "serie_a", "fascia": "campionato",
            "inizio": kickoff.isoformat(), "mercato": "1x2"}


@pytest.fixture
def archivio(tmp_path, monkeypatch):
    """Un archivio finto: pre-partita in una cartella, in-play nell'altra."""
    pre, live = tmp_path / "matches", tmp_path / "live"
    pre.mkdir(); live.mkdir()
    monkeypatch.setattr(arch, "ARCHIVIO", pre)
    monkeypatch.setattr(cr, "LIVE", live)
    return pre, live


def _archivio_sano(pre: Path, live: Path) -> dt.datetime:
    """Una giornata come dovrebbe andare: lungo raggio fresco, chiusura presa,
    in-play presente. Ritorna il kickoff usato."""
    kick = ADESSO - dt.timedelta(hours=4)
    _scrivi(pre, ADESSO - dt.timedelta(hours=10),
            {"entro_ore": 0, "righe": [_riga("A vs B", kick)]})
    _scrivi(pre, kick - dt.timedelta(hours=1),
            {"entro_ore": 2, "righe": [_riga("A vs B", kick)]})
    _scrivi(live, kick + dt.timedelta(minutes=20),
            {"partite": ["A vs B"], "righe": [{"partita": "A vs B"}]})
    return kick


def test_un_archivio_sano_non_suona(archivio):
    """Il caso che rende utile l'allarme: se suonasse sempre, nessuno lo
    guarderebbe piu' — ed e' l'altro modo di non funzionare."""
    pre, live = archivio
    _archivio_sano(pre, live)
    r = cr.controlla(adesso=ADESSO)
    assert r["problemi"] == [], r["problemi"]
    assert r["copertura_inplay"] == 1.0


def test_A_il_lungo_raggio_fermo_da_troppo_suona(archivio):
    """E' il guasto piu' insidioso: le partite continuano a essere raccolte
    dai giri densi quando si avvicinano, quindi l'archivio sembra vivo — manca
    solo la coda di traiettoria, che e' il motivo per cui il giro esiste."""
    pre, live = archivio
    kick = _archivio_sano(pre, live)
    # si sposta il lungo raggio a 30 ore fa (soglia: 26)
    for f in arch.snapshots(pre):
        if arch.leggi(f).get("entro_ore") == 0:
            f.unlink()
    _scrivi(pre, ADESSO - dt.timedelta(hours=30),
            {"entro_ore": 0, "righe": [_riga("A vs B", kick)]})
    r = cr.controlla(adesso=ADESSO)
    assert any(p.startswith("A)") for p in r["problemi"]), r["problemi"]


def test_A_nessun_lungo_raggio_del_tutto_suona(archivio):
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=4)
    _scrivi(pre, kick - dt.timedelta(hours=1),
            {"entro_ore": 2, "righe": [_riga("A vs B", kick)]})
    _scrivi(live, kick, {"partite": ["A vs B"], "righe": []})
    r = cr.controlla(adesso=ADESSO)
    assert any("NESSUN giro di lungo raggio" in p for p in r["problemi"])


def test_B_una_partita_giocata_senza_prezzo_di_chiusura_suona(archivio):
    """Il buco che conta per il test prospettico: un prezzo di due settimane
    prima non e' una chiusura."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=4)
    # il solo prezzo e' di 20 ore prima del via: fuori dalle 3 ore
    _scrivi(pre, ADESSO - dt.timedelta(hours=24),
            {"entro_ore": 0, "righe": [_riga("A vs B", kick)]})
    _scrivi(live, kick, {"partite": ["A vs B"], "righe": []})
    r = cr.controlla(adesso=ADESSO)
    assert any(p.startswith("B)") for p in r["problemi"]), r["problemi"]
    assert r["senza_chiusura"][0][0] == "A vs B"


def test_C_il_buco_dell_08_08_la_sentinella_che_non_gira(archivio):
    """IL CASO VERO, quello che ha aperto la Fase 144: venticinque partite in
    corso e il raccoglitore in-play a zero run. Nessun rosso da nessuna parte,
    e se n'e' accorto l'utente.

    ⚠️ Kickoff a -8h e non a -2h: dalla Fase 147 le partite delle ultime 6 ore
    non si giudicano (una sessione committa alla fine e puo' essere ancora
    accesa). Il buco resta lo stesso, si vede solo un giro dopo."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=8)
    righe = [_riga(f"A{i} vs B{i}", kick) for i in range(25)]
    _scrivi(pre, ADESSO - dt.timedelta(hours=10), {"entro_ore": 0, "righe": righe})
    _scrivi(pre, kick - dt.timedelta(minutes=40), {"entro_ore": 2, "righe": righe})
    # in-play: NIENTE
    r = cr.controlla(adesso=ADESSO)
    assert r["partite_giocate_in_finestra"] == 25
    assert r["copertura_inplay"] == 0.0
    assert any(p.startswith("C)") for p in r["problemi"]), r["problemi"]


def test_C_una_copertura_in_play_parziale_ma_decente_non_suona(archivio):
    """Il live e' nato ieri e le sessioni possono legittimamente non coprire
    tutto: la soglia e' esplicita e generosa, o l'allarme diventa rumore."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=8)      # fuori dalla finestra cieca
    righe = [_riga(f"A{i} vs B{i}", kick) for i in range(10)]
    _scrivi(pre, ADESSO - dt.timedelta(hours=10), {"entro_ore": 0, "righe": righe})
    _scrivi(pre, kick - dt.timedelta(hours=1), {"entro_ore": 2, "righe": righe})
    _scrivi(live, kick, {"partite": [f"A{i} vs B{i}" for i in range(8)], "righe": []})
    r = cr.controlla(adesso=ADESSO)
    assert r["copertura_inplay"] == 0.8
    assert not any(p.startswith("C)") for p in r["problemi"])


def test_D_una_lega_sparita_suona(archivio):
    """Il file lo dichiara gia' da solo (Fase 142): il punto e' che nessuno
    andrebbe mai a leggerlo."""
    pre, live = archivio
    kick = _archivio_sano(pre, live)
    _scrivi(pre, ADESSO - dt.timedelta(hours=2),
            {"entro_ore": 0, "leghe_senza_partite_esposte": ["la_liga"],
             "righe": [_riga("A vs B", kick)]})
    r = cr.controlla(adesso=ADESSO)
    assert any("leghe senza partite esposte" in p for p in r["problemi"])


def test_le_partite_incomplete_sono_una_nota_non_un_allarme(archivio):
    """Distinzione voluta: il budget esaurito e' gia' segnalato dal run rosso
    del raccoglitore. Ri-suonare qui raddoppierebbe il rumore sullo stesso
    fatto, e il guardiano serve per cio' che NON suona altrove."""
    pre, live = archivio
    kick = _archivio_sano(pre, live)
    _scrivi(pre, ADESSO - dt.timedelta(hours=2),
            {"entro_ore": 0, "righe": [_riga("A vs B", kick)],
             "partite_incomplete": [{"partita": "X vs Y", "mercati_persi": "tutti"}]})
    r = cr.controlla(adesso=ADESSO)
    assert not r["problemi"]
    assert any("partite incomplete" in n for n in r["note"])


def test_archivio_vuoto_non_esplode(archivio):
    """Il primo giro in assoluto, o un clone appena fatto."""
    r = cr.controlla(adesso=ADESSO)
    assert any("NESSUN giro di lungo raggio" in p for p in r["problemi"])
    assert r["partite_giocate_in_finestra"] == 0


def test_l_eta_si_legge_dal_NOME_non_dal_mtime(archivio):
    """Su un runner effimero il mtime di ogni file e' l'istante del `git
    clone`: leggerlo li' farebbe sembrare tutto appena raccolto, e il
    guardiano direbbe sempre che va bene."""
    pre, live = archivio
    kick = _archivio_sano(pre, live)
    vecchio = pre / "2026-08-01T00-00-00.json"
    arch.scrivi(vecchio, {"entro_ore": 0, "righe": [_riga("A vs B", kick)]})
    # mtime di adesso, nome di una settimana fa: deve valere il nome
    letti = cr.carica(pre, ADESSO - dt.timedelta(hours=48))
    assert all(d["_quando"] > ADESSO - dt.timedelta(hours=48) for d in letti)
    assert "2026-08-01T00-00-00" not in {d["_file"][:19] for d in letti}


def test_il_workflow_del_guardiano_gira_piu_di_una_volta_al_giorno():
    """Se un giro salta, il successivo dev'essere a ore, non a un giorno: sei
    ore di buco nella raccolta si recuperano ancora, ventiquattro no."""
    import yaml

    wf = yaml.safe_load((ROOT / ".github" / "workflows"
                         / "controlla-raccolta.yml").read_text())
    cron = wf[True]["schedule"][0]["cron"]
    ore = cron.split()[1]
    assert "," in ore or "/" in ore, f"gira una volta sola al giorno: {cron!r}"
    assert len(ore.split(",")) >= 3
    # e non deve avere un concurrency group: il guardiano non va cancellato
    assert "concurrency" not in wf


# ---------------------------------------------------------------------------
# LA RIPARAZIONE (Fase 144-quinquies)
# Osservazione dell'utente: «un cane da guardia che si limita ad avvertirmi mi
# sposta il lavoro addosso invece di toglierlo». Giusto — ma solo per cio' che
# si PUO' riparare, e la differenza va tenuta netta.
# ---------------------------------------------------------------------------

def test_il_lungo_raggio_stantio_e_dichiarato_RIPARABILE(archivio):
    """Le partite lontane sono ancora esposte: il dato e' li' da riprendere."""
    pre, live = archivio
    kick = _archivio_sano(pre, live)
    for f in arch.snapshots(pre):
        if arch.leggi(f).get("entro_ore") == 0:
            f.unlink()
    _scrivi(pre, ADESSO - dt.timedelta(hours=30),
            {"entro_ore": 0, "righe": [_riga("A vs B", kick)]})
    r = cr.controlla(adesso=ADESSO)
    assert "lungo_raggio" in r["riparabili"]


def test_una_chiusura_persa_NON_e_riparabile(archivio):
    """La distinzione che conta. La partita e' finita: quel prezzo non esiste
    piu' da nessuna parte, e mettere «riparabile» qui sarebbe una bugia che
    manderebbe il sistema a rincorrere un dato inesistente — e, peggio, a
    dichiararsi a posto dopo averlo «riparato»."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=4)
    _scrivi(pre, ADESSO - dt.timedelta(hours=24),
            {"entro_ore": 0, "righe": [_riga("A vs B", kick)]})
    _scrivi(live, kick, {"partite": ["A vs B"], "righe": []})
    r = cr.controlla(adesso=ADESSO)
    assert any(p.startswith("B)") for p in r["problemi"])
    assert "chiusura" not in " ".join(r["riparabili"])
    assert r["riparabili"] == [] or r["riparabili"] == ["lungo_raggio"]


def test_l_in_play_e_riparabile_solo_se_si_gioca_ancora(monkeypatch):
    """Accendere una sessione per partite finite non recupera niente: sarebbe
    un runner acceso a vuoto e un «riparato» falso nel rapporto."""
    import fetch_smarkets_matches as fsm
    monkeypatch.setattr(fsm, "scandaglia_live", lambda: ([], 40, []))
    fatto = cr.ripara({"in_play"})
    assert any("NON riparabile" in x for x in fatto)
    assert any("non si sta giocando" in x for x in fatto)


def test_se_si_gioca_ancora_la_sessione_si_accende(monkeypatch):
    import fetch_smarkets_matches as fsm
    monkeypatch.setattr(fsm, "scandaglia_live",
                        lambda: ([{"nome": "A vs B"}] * 7, 40, []))
    chiamate = []
    monkeypatch.setattr(cr, "_accendi_workflow",
                        lambda n: chiamate.append(n) or True)
    fatto = cr.ripara({"in_play"})
    assert chiamate == ["smarkets-live.yml"]
    assert any("7 partite in corso" in x and "accesa" in x for x in fatto)


def test_un_dispatch_fallito_e_DETTO_non_taciuto(monkeypatch):
    """Se il dispatch non passa, dirlo: altrimenti il rapporto direbbe
    «riparato» e il buco resterebbe, che e' il caso peggiore — la falsa
    sicurezza al posto del problema."""
    import fetch_smarkets_matches as fsm
    monkeypatch.setattr(fsm, "scandaglia_live", lambda: ([{"nome": "x"}], 1, []))
    monkeypatch.setattr(cr, "_accendi_workflow", lambda n: False)
    fatto = cr.ripara({"in_play"})
    assert any("NON accesa" in x for x in fatto)


def test_il_workflow_ri_controlla_dopo_aver_riparato():
    """IL PUNTO dell'intera riparazione. Senza il ri-controllo, un guasto
    cronico resterebbe verde per sempre: il guardiano direbbe «ho riparato» a
    ogni giro senza che niente cambi. Una riparazione che non si verifica e'
    una speranza, ed e' peggio del problema di partenza perche' aggiunge la
    falsa sicurezza."""
    testo = (ROOT / "scripts" / "controlla_raccolta.py").read_text()
    dopo = testo.split("fatto = ripara(")[1]
    assert "controlla(ore=a.ore)" in dopo, (
        "dopo la riparazione non si ri-controlla: il guardiano si fiderebbe "
        "di se stesso")
    assert "BUCHI RIMASTI DOPO LA RIPARAZIONE" in dopo


def test_il_workflow_del_guardiano_puo_riparare():
    """Servono i permessi giusti, o la riparazione fallisce in silenzio:
    scrivere il file del lungo raggio (contents) e accendere la sessione
    in-play (actions)."""
    import yaml
    wf = yaml.safe_load((ROOT / ".github" / "workflows"
                         / "controlla-raccolta.yml").read_text())
    assert wf["permissions"]["contents"] == "write"
    assert wf["permissions"]["actions"] == "write"
    passi = wf["jobs"]["controlla"]["steps"]
    controllo = next(s for s in passi if "buchi" in (s.get("name") or "").lower())
    assert "--ripara" in controllo["run"]
    assert "GH_TOKEN" in (controllo.get("env") or {})
    # e cio' che la riparazione raccoglie va committato, o e' stato inutile
    assert any("git commit" in (s.get("run") or "") for s in passi)
    # il timeout deve reggere una riparazione (budget 20 min) piu' i controlli
    assert wf["jobs"]["controlla"]["timeout-minutes"] >= 30


# ---------------------------------------------------------------------------
# LA SOGLIA SULLE CHIUSURE PERSE (Fase 147)
# Il guardiano e' stato rosso 5 volte su 5 per 1 partita su 44. Un rosso
# permanente maschera il prossimo guasto vero: e' il difetto contro cui avevo
# messo in guardia scrivendo il guardiano stesso.
# ---------------------------------------------------------------------------

def _giornata(pre, live, n_partite, n_senza_chiusura):
    kick = ADESSO - dt.timedelta(hours=3)
    righe = [_riga(f"A{i} vs B{i}", kick) for i in range(n_partite)]
    _scrivi(pre, ADESSO - dt.timedelta(hours=10), {"entro_ore": 0, "righe": righe})
    # la chiusura c'e' per tutte tranne le prime n_senza_chiusura
    _scrivi(pre, kick - dt.timedelta(hours=1),
            {"entro_ore": 2, "righe": righe[n_senza_chiusura:]})
    _scrivi(live, kick, {"partite": [r["partita"] for r in righe], "righe": []})


def test_UNA_chiusura_persa_su_quaranta_non_e_un_allarme(archivio):
    """Il caso vero: 1/44. E' la coda normale del jitter del cron (orario,
    finestra 2h, slittamento 30-40 min), non il giro che non gira."""
    pre, live = archivio
    _giornata(pre, live, 44, 1)
    r = cr.controlla(adesso=ADESSO)
    assert not any(p.startswith("B)") for p in r["problemi"]), r["problemi"]
    assert any(n.startswith("B)") for n in r["note"]), "ma dev'essere DICHIARATA"
    assert "sotto soglia" in " ".join(r["note"])


def test_TRE_chiusure_perse_sono_un_allarme(archivio):
    """Tre su quaranta e' tre volte la coda attesa: li' il giro orario non
    sta girando, ed e' il caso per cui il guardiano esiste."""
    pre, live = archivio
    _giornata(pre, live, 44, 3)
    r = cr.controlla(adesso=ADESSO)
    assert any(p.startswith("B)") for p in r["problemi"]), r["problemi"]


def test_su_una_giornata_PICCOLA_conta_la_frazione(archivio):
    """Due partite su sei sono il 33%: in assoluto sono poche, ma e' un terzo
    della giornata. La soglia assoluta da sola lascerebbe passare il guasto
    nei giorni di calendario magro."""
    pre, live = archivio
    _giornata(pre, live, 6, 2)
    r = cr.controlla(adesso=ADESSO)
    assert any(p.startswith("B)") for p in r["problemi"]), r["problemi"]


def test_la_soglia_non_nasconde_il_dato(archivio):
    """Tollerare non vuol dire dimenticare: la partita persa resta scritta nel
    rapporto anche quando non suona (R6 -- un buco dichiarato e' innocuo, uno
    silenzioso no)."""
    pre, live = archivio
    _giornata(pre, live, 44, 1)
    r = cr.controlla(adesso=ADESSO)
    assert len(r["senza_chiusura"]) == 1
    assert r["senza_chiusura"][0][0] == "A0 vs B0"


def test_l_anticipo_e_il_MINIMO_non_il_massimo(archivio):
    """L'errore vero del 10/08, in un test.

    Con `max` si prende la cattura piu' LONTANA dal fischio -- che per una
    partita vista ogni ora e' quella del giorno prima -- e si conclude che le
    chiusure mancano quando ci sono tutte. Qui la partita e' vista a T-24h e
    di nuovo a T-30min: l'anticipo giusto e' 30 minuti, non 1440.
    """
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=2)
    riga = [_riga("A vs B", kick)]
    _scrivi(pre, kick - dt.timedelta(hours=24), {"entro_ore": 0, "righe": riga})
    _scrivi(pre, kick - dt.timedelta(minutes=30), {"entro_ore": 2, "righe": riga})
    _scrivi(live, kick, {"partite": ["A vs B"], "righe": []})

    r = cr.controlla(adesso=ADESSO)
    assert not r["senza_chiusura"]
    assert r["anticipo_chiusura_min"]["migliore"] == 30.0, (
        "con max darebbe 1440: la cattura di ieri invece di quella di stasera")


def test_l_anticipo_dice_la_QUALITA_non_solo_la_presenza(archivio):
    """45 partite tutte prese a T-2h59min sarebbero «100% coperte» e inutili
    per il test prospettico, dove la chiusura e' il prezzo dell'ultimo momento.
    La copertura da sola non lo distingue; la mediana si'."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=4)
    righe = [_riga(f"A{i} vs B{i}", kick) for i in range(4)]
    _scrivi(pre, kick - dt.timedelta(hours=10), {"entro_ore": 0, "righe": righe})
    _scrivi(pre, kick - dt.timedelta(minutes=170), {"entro_ore": 2, "righe": righe})
    _scrivi(live, kick, {"partite": [r["partita"] for r in righe], "righe": []})
    r = cr.controlla(adesso=ADESSO)
    assert not r["senza_chiusura"], "sono coperte..."
    assert r["anticipo_chiusura_min"]["mediana"] == 170.0, "...ma male"


def test_le_partite_APPENA_giocate_non_si_giudicano(archivio):
    """Il falso allarme dell'11/08: quattro qualificazioni UEFA segnalate come
    scoperte mentre erano ancora in corso, e la sessione che le stava
    raccogliendo era accesa. Una sessione dura 5 ore e committa alla FINE:
    contare come mancante cio' che non e' ancora stato committato fa gridare
    al lupo ogni pomeriggio."""
    pre, live = archivio
    vecchia = ADESSO - dt.timedelta(hours=20)
    recente = ADESSO - dt.timedelta(hours=1)
    righe = [_riga("vecchia vs x", vecchia)] + \
            [_riga(f"recente{i} vs y", recente) for i in range(4)]
    _scrivi(pre, ADESSO - dt.timedelta(hours=22), {"entro_ore": 0, "righe": righe})
    _scrivi(pre, recente - dt.timedelta(minutes=40), {"entro_ore": 2, "righe": righe})
    _scrivi(live, vecchia, {"partite": ["vecchia vs x"], "righe": []})

    r = cr.controlla(adesso=ADESSO)
    assert r["partite_non_ancora_giudicabili"] == 4
    assert r["copertura_inplay"] == 1.0, "l'unica giudicabile e' coperta"
    assert not any(p.startswith("C)") for p in r["problemi"]), r["problemi"]
    assert any("non ancora giudicabili" in n for n in r["note"]), \
        "ma dev'essere DETTO che sono in attesa, non taciuto"


def test_un_buco_VECCHIO_suona_lo_stesso(archivio):
    """La cecita' sulle ultime 6 ore non deve diventare cecita' e basta."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=20)
    righe = [_riga(f"A{i} vs B{i}", kick) for i in range(10)]
    _scrivi(pre, ADESSO - dt.timedelta(hours=22), {"entro_ore": 0, "righe": righe})
    _scrivi(pre, kick - dt.timedelta(minutes=40), {"entro_ore": 2, "righe": righe})
    r = cr.controlla(adesso=ADESSO)
    assert any(p.startswith("C)") for p in r["problemi"]), r["problemi"]


# --------------------------------------------------------------------------
# IL NOME DEL FILE, E IL SUFFISSO CHE HA ACCECATO IL GUARDIANO (Fase 151)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("nome,atteso", [
    ("2026-08-11T13-49-21.json.gz", "2026-08-11T13:49:21+00:00"),
    # ⚠️ IL CASO VERO. Dal 09/08 i file portano il numero del gemello in coda,
    # e il parser di prima moriva su questo: `13:49:21:g1` non e' un orario.
    ("2026-08-11T13-49-21-g1.json.gz", "2026-08-11T13:49:21+00:00"),
    ("2026-08-11T13-49-21-g4.json.gz", "2026-08-11T13:49:21+00:00"),
    ("2026-08-11T13-49-21-g0.json.gz", "2026-08-11T13:49:21+00:00"),
    # e qualunque suffisso futuro: il nome e' un'etichetta a cui si aggiungono
    # pezzi, non una forma fissa
    ("2026-08-11T13-49-21-qualsiasi-cosa.json", "2026-08-11T13:49:21+00:00"),
    ("2026-08-11T13-49-21.json", "2026-08-11T13:49:21+00:00"),
])
def test_l_istante_si_legge_anche_col_suffisso(nome, atteso):
    assert cr.istante_del_file(nome).isoformat() == atteso


@pytest.mark.parametrize("nome", [
    "README.md", "manifest.json", "2026-08-11.json", "", "T13-49-21.json",
])
def test_un_nome_senza_istante_non_esplode_e_non_inventa(nome):
    """None e non un istante finto: un file senza data va SALTATO, non
    datato a caso — con una data inventata finirebbe dentro o fuori
    finestra a seconda del capriccio del parser."""
    assert cr.istante_del_file(nome) is None


def test_i_file_dei_gemelli_finiscono_dentro_la_finestra(tmp_path):
    """Il test che sarebbe servito. Con il parser di prima questa `carica`
    ritornava una lista VUOTA, la copertura in-play usciva 0% e il guardiano
    gridava «la sentinella non sta girando» — su un archivio pieno.

    Un controllo che sbaglia cosi' e' peggio di uno assente: non tace, dice
    la cosa sbagliata con la voce di un guasto vero."""
    for nome in ("2026-08-11T10-00-14-g1", "2026-08-11T13-49-21-g1",
                 "2026-08-11T09-00-00"):
        arch.scrivi(tmp_path / f"{nome}.json",
                        {"righe": [], "partite": ["A vs B"], "gemello": 1})
    da = dt.datetime(2026, 8, 11, tzinfo=dt.timezone.utc)
    letti = cr.carica(tmp_path, da)
    assert len(letti) == 3, [d["_file"] for d in letti]
    assert {d["_quando"].hour for d in letti} == {9, 10, 13}


# --------------------------------------------------------------------------
# A-bis · LA FRESCHEZZA DEGLI OUTRIGHT (Fase 153)
# --------------------------------------------------------------------------

def _archivio_outright(tmp_path, giorni_fa, adesso):
    """Una cartella outright con un solo snapshot, vecchio di N giorni."""
    cart = tmp_path / "outright_snapshots"
    cart.mkdir(parents=True, exist_ok=True)
    giorno = (adesso - dt.timedelta(days=giorni_fa)).date()
    (cart / f"{giorno}.json").write_text("{}")
    # rumore che NON deve confondere il conto: non sono snapshot
    (cart / "README.md").write_text("x")
    (cart / "history.csv").write_text("x")
    return cart


def test_outright_fermi_da_troppo_suonano(monkeypatch, tmp_path):
    """Il caso vero: il 12/08/2026 l'ultimo snapshot era del 26 luglio,
    DICIOTTO giorni prima, con la stagione che apriva tre giorni dopo. Il
    guardiano taceva perche' quel collettore non aveva un workflow — e un
    collettore che non esiste non fa scattare nessun allarme sulla propria
    assenza."""
    adesso = dt.datetime(2026, 8, 12, 17, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(cr, "OUTRIGHT", _archivio_outright(tmp_path, 18, adesso))
    r = cr.controlla(adesso=adesso)
    assert any(p.startswith("A-bis)") for p in r["problemi"]), r["problemi"]
    assert "outright" in r["riparabili"]
    # 18,7 e non 18: lo snapshot porta la data, quindi vale mezzanotte,
    # e "adesso" sono le 17:00 di diciotto giorni dopo.
    assert r["eta_outright_giorni"] == 18.7


def test_un_giorno_saltato_non_suona(monkeypatch, tmp_path):
    """Il giro e' giornaliero e il cron slitta di 30-40 minuti: una soglia a
    24h suonerebbe per il ritardo invece che per il guasto. Gli outright si
    muovono in settimane — un giorno saltato e' rumore."""
    adesso = dt.datetime(2026, 8, 12, 17, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(cr, "OUTRIGHT", _archivio_outright(tmp_path, 1, adesso))
    r = cr.controlla(adesso=adesso)
    assert not any(p.startswith("A-bis)") for p in r["problemi"]), r["problemi"]


def test_cartella_outright_vuota_suona(monkeypatch, tmp_path):
    """«Nessuno snapshot» e «snapshot vecchissimo» sono lo stesso guasto e
    devono dare lo stesso allarme: senza questo, una cartella mai creata
    passerebbe per sana."""
    vuota = tmp_path / "mai_creata"
    monkeypatch.setattr(cr, "OUTRIGHT", vuota)
    r = cr.controlla(adesso=dt.datetime(2026, 8, 12, 17, tzinfo=dt.timezone.utc))
    assert any(p.startswith("A-bis)") for p in r["problemi"])
    assert r["eta_outright_giorni"] is None


# ---------------------------------------------------------------------------
# LA DIPENDENZA NON DICHIARATA (Fase 156)
# Il collettore outright della Fase 153 non ha MAI prodotto uno snapshot: 4 run
# su 4 morti su `ModuleNotFoundError: requests`, perche' sui runner di Actions
# nessuno installa il progetto e `requests` non c'e'. Il guardiano lo aveva
# visto (controllo A-bis, 4,6 giorni) ma moriva a sua volta sullo stesso
# import mentre provava a riparare — dieci run rossi e nessun verdetto.
# Due guardie, una per ciascuno dei due difetti.
# ---------------------------------------------------------------------------

def _script_che_vogliono_requests() -> set[str]:
    """I moduli di `scripts/` che finiscono per importare `requests`.

    Punto fisso su un grafo di import volutamente grossolano: basta che un
    modulo importi (in qualunque forma) un altro modulo di `scripts/` che ne
    ha bisogno. Grossolano verso il SICURO — al massimo chiede un `pip
    install` di troppo, che costa due secondi; il contrario costa un
    collettore morto per giorni.
    """
    import re

    sorgenti = {p.stem: p.read_text() for p in (ROOT / "scripts").glob("*.py")}
    serve = {n for n, t in sorgenti.items()
             if re.search(r"^\s*import requests|^\s*from requests\b", t, re.M)}
    cambiato = True
    while cambiato:
        cambiato = False
        for nome, testo in sorgenti.items():
            if nome in serve:
                continue
            for dep in serve:
                if re.search(rf"\b(import|from)\s+(scripts\.)?{dep}\b", testo):
                    serve.add(nome)
                    cambiato = True
                    break
    return serve


def test_ogni_workflow_installa_requests_se_lo_script_lo_usa():
    """La guardia che sarebbe bastata: un workflow che lancia uno script il
    quale (anche indirettamente) importa `requests` DEVE installarlo."""
    import re

    serve = _script_che_vogliono_requests()
    assert "archive_outrights" in serve, (
        "il grafo non vede piu' la dipendenza nota: e' la guardia a essere "
        "rotta, non il codice")

    mancanti = []
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        testo = wf.read_text()
        lanciati = set(re.findall(r"python\s+(?:-u\s+)?scripts/(\w+)\.py", testo))
        lanciati |= set(re.findall(r"python\s+-m\s+scripts\.(\w+)", testo))
        if not (lanciati & serve):
            continue
        if not re.search(r"pip install[^\n]*\brequests\b", testo):
            mancanti.append(f"{wf.name} lancia {sorted(lanciati & serve)}")
    assert not mancanti, (
        "workflow che usano `requests` senza installarlo: " + "; ".join(mancanti))


def test_una_riparazione_che_non_si_importa_NON_uccide_il_guardiano(monkeypatch):
    """Il difetto peggiore dei due. Se l'import fallisce, `ripara` deve
    tornare la riga «NON archiviati» e lasciare vivo il controllo: un
    guardiano che muore riparando smette di sorvegliare anche cio' che
    funziona."""
    import builtins

    vero = builtins.__import__

    def finto(nome, *a, **k):
        if nome == "archive_outrights":
            raise ModuleNotFoundError("No module named 'requests'")
        return vero(nome, *a, **k)

    monkeypatch.delitem(sys.modules, "archive_outrights", raising=False)
    monkeypatch.setattr(builtins, "__import__", finto)

    fatto = cr.ripara({"outright"})
    assert fatto and "NON archiviati" in fatto[0], fatto
    assert "ModuleNotFoundError" in fatto[0]
