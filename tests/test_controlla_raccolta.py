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
