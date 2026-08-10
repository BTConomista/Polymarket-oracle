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
    e se n'e' accorto l'utente."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=2)
    righe = [_riga(f"A{i} vs B{i}", kick) for i in range(25)]
    _scrivi(pre, ADESSO - dt.timedelta(hours=10), {"entro_ore": 0, "righe": righe})
    _scrivi(pre, kick - dt.timedelta(hours=1), {"entro_ore": 2, "righe": righe})
    # in-play: NIENTE
    r = cr.controlla(adesso=ADESSO)
    assert r["partite_giocate_in_finestra"] == 25
    assert r["copertura_inplay"] == 0.0
    assert any(p.startswith("C)") for p in r["problemi"]), r["problemi"]


def test_C_una_copertura_in_play_parziale_ma_decente_non_suona(archivio):
    """Il live e' nato ieri e le sessioni possono legittimamente non coprire
    tutto: la soglia e' esplicita e generosa, o l'allarme diventa rumore."""
    pre, live = archivio
    kick = ADESSO - dt.timedelta(hours=2)
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
# LA SOGLIA SULLE CHIUSURE PERSE (Fase 145)
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
