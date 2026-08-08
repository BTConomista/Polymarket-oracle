"""Test del raccoglitore IN-PLAY (Fase 143).

Il download non e' testabile (rete e partite vere), ma tre cose che possono
rompersi in silenzio si':

  1. **la cadenza**: un ciclo che rincorre i tick persi gira a vuoto invece di
     raccogliere, e un ciclo che non li salta accumula ritardo per sempre;
  2. **il tempo per riga**: un file di sessione contiene decine di giri, e
     senza `istante_utc` su ogni riga e' una serie temporale senza il tempo --
     cioe' inutilizzabile, senza che nulla dia errore;
  3. **la separazione dall'archivio pre-partita**: un prezzo in-play conosce
     il punteggio, uno pre-partita no. Mescolarli romperebbe in silenzio ogni
     lettore di `data/smarkets_matches/`.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fetch_smarkets_live as live   # noqa: E402
from fetch_smarkets_matches import MERCATI_NUCLEO   # noqa: E402


UTC = dt.timezone.utc


# --------------------------------------------------------------------- tick

def test_il_tick_avanza_di_un_passo_quando_si_e_in_orario():
    ultimo = dt.datetime(2026, 8, 8, 14, 0, tzinfo=UTC)
    adesso = dt.datetime(2026, 8, 8, 14, 0, 5, tzinfo=UTC)
    assert live.prossimo_tick(adesso, ultimo, 2) == \
        dt.datetime(2026, 8, 8, 14, 2, tzinfo=UTC)


def test_i_tick_persi_si_SALTANO_non_si_recuperano():
    """A 25 partite in contemporanea un giro pieno dura ~3 minuti, piu' del
    passo del nucleo. Recuperare i tick saltati farebbe girare lo script a
    vuoto rincorrendo un orario che non tornera' -- e ogni giro sprecato e'
    un giro non fatto sulla partita vera."""
    ultimo = dt.datetime(2026, 8, 8, 14, 0, tzinfo=UTC)
    adesso = dt.datetime(2026, 8, 8, 14, 7, tzinfo=UTC)      # 3 tick persi
    nuovo = live.prossimo_tick(adesso, ultimo, 2)
    assert nuovo > adesso, "il tick nuovo dev'essere nel FUTURO"
    assert nuovo == dt.datetime(2026, 8, 8, 14, 8, tzinfo=UTC)


def test_il_tick_resta_sulla_griglia_originale():
    """Saltare non vuol dire ripartire da adesso: la griglia dei :00/:02/:04
    va mantenuta, altrimenti la cadenza deriva a ogni sforamento."""
    ultimo = dt.datetime(2026, 8, 8, 14, 0, tzinfo=UTC)
    adesso = dt.datetime(2026, 8, 8, 14, 5, 30, tzinfo=UTC)
    nuovo = live.prossimo_tick(adesso, ultimo, 2)
    assert nuovo.second == 0 and nuovo.minute % 2 == 0


@pytest.mark.parametrize("passo", [1, 2, 5, 15])
def test_il_tick_e_sempre_futuro_per_qualunque_passo(passo):
    ultimo = dt.datetime(2026, 8, 8, 14, 0, tzinfo=UTC)
    for ritardo in (0, 1, 61, 3600):
        adesso = ultimo + dt.timedelta(seconds=ritardo)
        assert live.prossimo_tick(adesso, ultimo, passo) > adesso


# --------------------------------------------------------------------- giro

_VIVE = [{"event_id": 1, "nome": "A vs B", "lega": "league_cup",
          "fascia": "coppa", "inizio": "2026-08-08T12:00:00Z", "inplay": True},
         {"event_id": 2, "nome": "C vs D", "lega": "serie_a",
          "fascia": "campionato", "inizio": "2026-08-08T12:30:00Z", "inplay": True}]


def test_ogni_riga_porta_l_istante_e_il_tipo_di_giro(monkeypatch):
    """Senza `istante_utc` per riga un file di sessione e' un mucchio di
    prezzi senza tempo: il dato piu' importante di una serie temporale."""
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        ([{"partita": ev["nome"], "mercato": "1x2"}], 0))
    righe, incomplete = live.un_giro(_VIVE, pieno=False)
    assert len(righe) == 2 and not incomplete
    assert all(r["giro"] == "nucleo" for r in righe)
    assert all(r["istante_utc"].endswith("+00:00") for r in righe), "l'istante e' UTC"
    assert len({r["istante_utc"] for r in righe}) == 1, "stesso giro, stesso istante"


def test_il_giro_stretto_chiede_solo_il_nucleo(monkeypatch):
    visti = []
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        (visti.append((tutti, mercati_ammessi)) or [], 0))
    live.un_giro(_VIVE[:1], pieno=False)
    live.un_giro(_VIVE[:1], pieno=True)
    assert visti[0] == (False, MERCATI_NUCLEO)
    assert visti[1] == (True, None)


def test_il_nucleo_contiene_il_risultato_esatto():
    """Non e' un lusso: e' il mercato da cui si ricostruisce il punteggio
    (minimo componentwise dei punteggi ancora quotati). Senza, la traiettoria
    in-play e' una serie di prezzi di cui non si sa a che partita corrisponde."""
    assert "risultato_esatto" in MERCATI_NUCLEO
    assert {"1x2", "ou25", "ggng"} <= MERCATI_NUCLEO


def test_una_partita_che_fallisce_non_porta_via_il_giro(monkeypatch):
    """Stessa politica della Fase 141, e qui vale doppio: un giro perso e' un
    buco in una serie temporale che non si puo' ricampionare."""
    def quote(ev, tutti, mercati_ammessi=None):
        if ev["event_id"] == 1:
            raise RuntimeError("503")
        return [{"partita": ev["nome"], "mercato": "1x2"}], 0

    monkeypatch.setattr(live, "quote_partita", quote)
    righe, incomplete = live.un_giro(_VIVE, pieno=False)
    assert [r["partita"] for r in righe] == ["C vs D"]
    assert len(incomplete) == 1 and incomplete[0]["partita"] == "A vs B"
    assert "RuntimeError" in incomplete[0]["errore"]


def test_i_mercati_persi_dentro_una_partita_sono_dichiarati(monkeypatch):
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        ([{"partita": ev["nome"]}], 3))
    righe, incomplete = live.un_giro(_VIVE[:1], pieno=True)
    assert righe and incomplete[0]["mercati_persi"] == 3


# ------------------------------------------------------------------ archivio

def test_l_archivio_in_play_e_SEPARATO_da_quello_pre_partita():
    """Un prezzo in-play conosce il punteggio, uno pre-partita no: non sono
    confrontabili. Se finissero nella stessa cartella, `ultimo_listino_completo()`
    e ogni altro lettore di `data/smarkets_matches/` li leggerebbero come se
    fossero la stessa cosa -- senza un errore, che e' il modo peggiore."""
    from src.data import smarkets_archive as arch
    assert live.DEST != arch.ARCHIVIO
    assert live.DEST.name == "smarkets_live"


def test_nessuno_legge_l_archivio_in_play_a_mano():
    """Stessa guardia dell'archivio pre-partita (Fase 136): i file sono
    compressi, e chi globa `*.json` o fa `read_text()` si perde tutto in
    silenzio. Si passa da `src/data/smarkets_archive.py`."""
    import re

    radice = Path(__file__).resolve().parents[1]
    sospetti = []
    for cartella in ("scripts", "src", "tests"):
        for f in (radice / cartella).rglob("*.py"):
            if f.name == "smarkets_archive.py":
                continue
            for riga in f.read_text(encoding="utf-8").splitlines():
                if "smarkets_live" in riga and re.search(r'glob\(|"\*\.json"', riga):
                    sospetti.append(f"{f.relative_to(radice)}: {riga.strip()[:90]}")
    assert not sospetti, "\n".join(sospetti)


# ------------------------------------------------------------------ workflow

def test_il_workflow_in_play_ha_un_gruppo_ma_non_uccide_le_sessioni_vive():
    """La scelta ribaltata nel giro di un'ora, e il perche' va tenuto scritto.

    Con sessioni da 40 minuti il gruppo era SBAGLIATO: la sessione successiva
    serviva per la continuita' e cancellarla apriva un buco. Con sessioni da 5
    ore che si spengono da sole, le sentinelle successive sono redondanti --
    e senza gruppo, a una sentinella ogni 30 minuti, si arriverebbe a dieci
    sessioni in parallelo sulle stesse partite.

    Ma `cancel-in-progress` deve restare **false**: cancellare i pending e'
    il pregio, uccidere una sessione VIVA butterebbe i giri non committati.
    """
    import re
    import yaml

    radice = Path(__file__).resolve().parents[1]
    testo = (radice / ".github" / "workflows" / "smarkets-live.yml").read_text()
    wf = yaml.safe_load(testo)
    assert wf["concurrency"]["group"], "senza gruppo si accendono N sessioni gemelle"
    assert wf["concurrency"]["cancel-in-progress"] is False, (
        "cancel-in-progress ucciderebbe una sessione viva e i suoi giri non "
        "ancora committati")

    # la sessione dev'essere lunga: e' cio' che rende il gruppo la scelta
    # giusta invece di quella sbagliata. Se qualcuno la riportasse a 40
    # minuti, il gruppo tornerebbe a essere un danno.
    assert live.DURATA_MINUTI >= 120, (
        "sessione corta + gruppo = le sessioni che servono vengono cancellate: "
        "o si allunga la sessione o si toglie il gruppo")
    tmt = wf["jobs"]["raccogli"]["timeout-minutes"]
    assert tmt > live.DURATA_MINUTI and tmt < 360, "il tetto duro di un job e' 6h"

    # e il passo che salva deve sopravvivere al fallimento del passo prima
    salva = wf["jobs"]["raccogli"]["steps"][-1]
    assert "cancelled()" in str(salva.get("if")) or "always" in str(salva.get("if"))


def test_la_sessione_si_spegne_da_sola_quando_non_si_gioca():
    """E' cio' che rende sostenibile una sessione da 5 ore: senza, un runner
    resterebbe acceso a vuoto fino al timeout ogni volta che il calcio
    finisce prima."""
    assert live.GIRI_VUOTI_PER_SPEGNERSI > 0
    # ma non troppo presto: fra un blocco e l'altro c'e' l'intervallo, e
    # ri-accendersi dipenderebbe di nuovo dal cron
    assert live.GIRI_VUOTI_PER_SPEGNERSI * live.OGNI_NUCLEO >= 15


def test_la_sessione_dura_piu_del_periodo_della_sentinella():
    """Dalla Fase 144 la sessione dura MOLTO piu' del periodo: la sentinella
    non e' piu' un metronomo ma un accendino, e un solo cron andato a buon
    fine copre un blocco intero. La disuguaglianza resta la garanzia minima:
    se la sessione fosse piu' corta del periodo, ogni ritardo del cron
    (30-40 minuti, misurato) diventerebbe un buco."""
    import re
    import yaml

    testo = (Path(__file__).resolve().parents[1] / ".github" / "workflows"
             / "smarkets-live.yml").read_text()
    wf = yaml.safe_load(testo)
    cron = wf[True]["schedule"][0]["cron"]
    periodo = int(re.match(r"\*/(\d+) ", cron).group(1))
    assert live.DURATA_MINUTI > periodo, (
        f"sessione {live.DURATA_MINUTI} min <= periodo sentinella {periodo} min: "
        f"un cron in ritardo lascerebbe un buco")
    # e il job dev'essere piu' lungo della sessione, o la tronca lui
    assert wf["jobs"]["raccogli"]["timeout-minutes"] > live.DURATA_MINUTI
