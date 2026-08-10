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


def test_ogni_riga_porta_DUE_tempi_e_il_tipo_di_giro(monkeypatch):
    """Due tempi, e servono entrambi (Fase 144-ter).

    La prima stesura dava a tutte le righe di un giro lo stesso istante. Con
    25 partite un giro pieno dura minuti -- misurato sul runner: **9'50"** --
    quindi quell'istante era il tempo SBAGLIATO per quasi tutte le righe:
    una serie temporale con la data finta. Ora `istante_utc` dice quando
    QUELLA partita e' stata letta, `giro_utc` raggruppa il passaggio.
    """
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        ([{"partita": ev["nome"], "mercato": "1x2"}], 0))
    righe, incomplete = live.un_giro(_VIVE, pieno=False)
    assert len(righe) == 2 and not incomplete
    assert all(r["giro"] == "nucleo" for r in righe)
    assert all(r["istante_utc"].endswith("+00:00") for r in righe), "l'istante e' UTC"
    assert len({r["giro_utc"] for r in righe}) == 1, "stesso giro, stesso giro_utc"
    # e l'istante e' PER PARTITA: puo' coincidere in un test istantaneo, ma
    # non dev'essere lo stesso campo di `giro_utc`
    assert all(r["istante_utc"] >= r["giro_utc"] for r in righe)


def test_le_partite_si_interrogano_in_parallelo(monkeypatch):
    """Non per fare piu' richieste al secondo -- il limitatore in
    `fetch_smarkets_outrights` le tiene comunque a ~3/s -- ma per sovrapporre
    le ATTESE DI RETE, che sul runner sono l'80% del tempo."""
    import time as _t
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        (_t.sleep(0.2) or [{"partita": ev["nome"]}], 0))
    molte = [dict(_VIVE[0], event_id=i, nome=f"p{i}") for i in range(6)]
    t0 = _t.monotonic()
    righe, _ = live.un_giro(molte, pieno=False)
    durata = _t.monotonic() - t0
    assert len(righe) == 6
    assert durata < 0.2 * 6 * 0.6, (
        f"{durata:.2f}s per 6 partite da 0.2s: sembra sequenziale")


def test_il_limitatore_delle_richieste_e_condiviso_fra_i_thread():
    """Il `sleep` per-chiamata basta a un thread solo; con sei darebbe sei
    volte il ritmo e il 429 arriverebbe subito. Il limitatore serializza gli
    istanti di PARTENZA, non le attese."""
    import concurrent.futures as _cf
    import time as _t
    import fetch_smarkets_outrights as fso

    t0 = _t.monotonic()
    with _cf.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda _: fso._attendi_il_turno(), range(6)))
    durata = _t.monotonic() - t0
    # sei turni a 0.35s l'uno non possono stare in meno di ~5 intervalli
    assert durata >= 5 * fso._THROTTLE * 0.9, (
        f"{durata:.2f}s per 6 turni: il ritmo non e' rispettato")


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


# ---------------------------------------------------------------------------
# LO SCAGLIONAMENTO (Fase 144-bis, segnalato dall'utente e misurato)
# 141 partite del perimetro su 82 orari distinti, con salti di 15/30/60/75/90
# minuti: sono paesi diversi. Un sabato sera vero e' 18:00 -> 18:30 -> 18:45.
# ---------------------------------------------------------------------------

def _futura(eid, nome, kickoff):
    return {"event_id": eid, "nome": nome, "lega": "serie_a",
            "fascia": "campionato", "inizio": kickoff.isoformat(),
            "_inizio": kickoff}


def test_si_segue_una_partita_gia_PRIMA_del_via():
    """Il pezzo della richiesta che il raccoglitore in-play non copriva: «poco
    prima dell'inizio». Restava appeso alla corsa oraria di chiusura, che pero'
    slitta di 30-40 minuti e puo' mancare del tutto una partita."""
    adesso = dt.datetime(2026, 8, 8, 17, 50, tzinfo=UTC)
    future = [_futura(1, "A vs B", adesso + dt.timedelta(minutes=10)),
              _futura(2, "C vs D", adesso + dt.timedelta(minutes=55))]
    seguire, prossimo = live.da_seguire([], future, adesso, orizzonte_pre=20)
    assert [e["nome"] for e in seguire] == ["A vs B"], "solo quella entro 20'"
    assert all(e["fase"] == "pre" for e in seguire)
    assert prossimo == adesso + dt.timedelta(minutes=10)


def test_una_partita_live_non_viene_duplicata_dal_calendario():
    """La stessa partita compare in `vive` e nel calendario: raccoglierla due
    volte per giro raddoppierebbe le righe senza aggiungere niente."""
    adesso = dt.datetime(2026, 8, 8, 18, 10, tzinfo=UTC)
    vive = [{"event_id": 1, "nome": "A vs B", "lega": "serie_a",
             "fascia": "campionato", "inizio": "x", "inplay": True}]
    future = [_futura(1, "A vs B", adesso - dt.timedelta(minutes=10))]
    seguire, _ = live.da_seguire(vive, future, adesso)
    assert len(seguire) == 1 and seguire[0]["fase"] == "live"


def test_una_partita_gia_cominciata_ma_non_ancora_live_non_conta_come_futura():
    """Fra il calcio d'inizio e il momento in cui l'API la marca `live` c'e'
    una finestra: non dev'essere scambiata per «prossimo via», o la sessione
    resterebbe accesa credendo che debba ancora cominciare."""
    adesso = dt.datetime(2026, 8, 8, 18, 2, tzinfo=UTC)
    future = [_futura(9, "gia' iniziata", adesso - dt.timedelta(minutes=2))]
    seguire, prossimo = live.da_seguire([], future, adesso)
    assert seguire == [] and prossimo is None


def test_il_prossimo_via_e_il_PRIMO_futuro_non_l_ultimo():
    adesso = dt.datetime(2026, 8, 8, 17, 0, tzinfo=UTC)
    future = [_futura(1, "tardi", adesso + dt.timedelta(hours=3)),
              _futura(2, "presto", adesso + dt.timedelta(minutes=45)),
              _futura(3, "medio", adesso + dt.timedelta(hours=2))]
    _, prossimo = live.da_seguire([], future, adesso)
    assert prossimo == adesso + dt.timedelta(minutes=45)


def test_l_orizzonte_di_attesa_copre_i_salti_veri_misurati():
    """I salti misurati l'08/08 fra un via e il successivo: 15, 30, 60, 75, 90
    minuti. La sessione non deve spegnersi in nessuno di questi buchi --
    altrimenti muore fra le 18:00 e le 18:45 e per riaccendersi dipende di
    nuovo dal cron, che e' il problema che stiamo togliendo di mezzo."""
    for salto in (15, 30, 60, 75, 90):
        assert salto <= live.ORIZZONTE_ATTESA, (
            f"un buco di {salto} min spegnerebbe la sessione")
    # ma i due salti lunghi misurati (165 e 210) devono spegnerla: li' non si
    # gioca davvero, e tenere acceso un runner a vuoto non serve a nessuno
    assert live.ORIZZONTE_ATTESA < 165


def test_l_orizzonte_pre_e_piu_corto_dell_attesa():
    """Se fossero uguali, una partita entrerebbe nell'orizzonte esattamente
    quando la sessione smette di aspettarla."""
    assert live.ORIZZONTE_PRE < live.ORIZZONTE_ATTESA


def test_la_riga_dichiara_se_e_pre_o_live(monkeypatch):
    """La stessa serie attraversa il calcio d'inizio, e un prezzo che non
    conosce il punteggio non e' confrontabile con uno che lo conosce."""
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        ([{"partita": ev["nome"]}], 0))
    ev = {"event_id": 1, "nome": "A vs B", "fase": "pre"}
    righe, _ = live.un_giro([ev], pieno=False)
    assert righe[0]["fase"] == "pre"
    ev["fase"] = "live"
    righe, _ = live.un_giro([ev], pieno=False)
    assert righe[0]["fase"] == "live"


def test_il_ritmo_si_tara_da_solo_sui_rifiuti():
    """Un numero fisso non puo' essere giusto in due ambienti diversi.

    Misurato l'08/08 allo STESSO ritmo nominale (2,9 richieste/s): da questo
    ambiente 24 richieste su 24 accettate, dal runner di GitHub 151 mercati
    persi per 429. Quindi l'intervallo non e' una costante da indovinare: si
    alza quando l'API rifiuta e ridiscende piano quando accetta.
    """
    import fetch_smarkets_outrights as fso

    partenza = fso.ritmo_corrente()
    try:
        fso._rallenta()
        assert fso.ritmo_corrente() > partenza, "un 429 deve rallentare"
        for _ in range(500):
            fso._accelera()
        assert fso.ritmo_corrente() == pytest.approx(fso._INTERVALLO_MIN), (
            "dopo tanti successi si deve tornare al minimo")
        # e non si scende MAI sotto il minimo, per quanti successi arrivino
        for _ in range(200):
            fso._accelera()
        assert fso.ritmo_corrente() >= fso._INTERVALLO_MIN
        # ne' si sale all'infinito
        for _ in range(50):
            fso._rallenta()
        assert fso.ritmo_corrente() <= fso._INTERVALLO_MAX
    finally:
        fso._INTERVALLO[0] = partenza


def test_la_risalita_e_piu_lenta_della_discesa():
    """Asimmetria voluta: un 429 e' un fatto (l'API ha detto no), un successo
    e' solo l'assenza di un rifiuto. Tornare veloci alla stessa velocita' con
    cui si rallenta farebbe oscillare il ritmo intorno al limite, prendendo
    un 429 ogni pochi secondi."""
    import fetch_smarkets_outrights as fso
    assert fso._CRESCITA > 1 / fso._DECADIMENTO, (
        "la risalita e' piu' rapida della discesa: il ritmo oscillerebbe")


def test_il_ritmo_raggiunto_finisce_nel_file(monkeypatch, tmp_path):
    """Una sessione con pochi giri e' un mistero, se non si sa che l'API stava
    rifiutando. Il ritmo e' la diagnosi, e va scritta dove restera'."""
    monkeypatch.setattr(live, "scandaglia_live", lambda: (_VIVE, 100, []))
    monkeypatch.setattr(live, "scandaglia_upcoming", lambda: ([], 0, {}))
    monkeypatch.setattr(live, "quote_partita",
                        lambda ev, tutti, mercati_ammessi=None:
                        ([{"partita": ev["nome"]}], 0))
    monkeypatch.setattr(live, "DEST", tmp_path)
    live.main(["--durata-minuti", "0", "--ogni-pieno", "0"])

    from src.data import smarkets_archive as arch
    d = arch.leggi(sorted(tmp_path.glob("*.gz"))[0])
    assert d["intervallo_fra_richieste_s"] > 0


def test_i_workflow_non_bufferizzano_lo_stdout():
    """Un log che non dice QUANDO non serve a diagnosi: senza
    PYTHONUNBUFFERED tutte le righe escono con lo stesso istante e la durata
    di un giro si puo' misurare solo a posteriori dal file (successo 08/08)."""
    import yaml
    radice = Path(__file__).resolve().parents[1]
    for nome in ("smarkets-live.yml", "smarkets-prematch.yml"):
        wf = yaml.safe_load((radice / ".github" / "workflows" / nome).read_text())
        job = wf["jobs"][list(wf["jobs"])[0]]
        assert (job.get("env") or {}).get("PYTHONUNBUFFERED") == "1", nome


# ---------------------------------------------------------------------------
# IL PERIMETRO DI PROVA (Fase 146)
# Serve a provare l'infrastruttura nelle ore in cui il nostro perimetro non
# gioca: 3-7 ore al giorno contro le 5-14 di tutto il calcio (misurato 09/08).
# ---------------------------------------------------------------------------

def _altra(i, inizio="2026-08-10T20:00:00Z"):
    return {"event_id": 900 + i, "nome": f"X{i} vs Y{i}",
            "lega": "brazil-serie-a", "fascia": "prova",
            "inizio": inizio, "inplay": True}


def test_la_prova_RIEMPIE_il_carico_non_lo_aumenta():
    """Il punto che rende accettabile allargare a ~800 partite esposte: non si
    prendono tutte, si completa fino al tetto. Con le nostre gia' al tetto, la
    prova non aggiunge una sola richiesta."""
    nostre = [dict(_VIVE[0], event_id=i) for i in range(live.TETTO_PARTITE)]
    assert live.riempi_con_la_prova(nostre, [_altra(i) for i in range(50)]) == []


def test_la_prova_riempie_quando_le_nostre_sono_poche():
    nostre = [dict(_VIVE[0], event_id=i) for i in range(5)]
    scelte = live.riempi_con_la_prova(nostre, [_altra(i) for i in range(50)])
    assert len(scelte) == live.TETTO_PARTITE - 5
    assert all(e["fascia"] == "prova" for e in scelte)


def test_con_zero_nostre_la_prova_arriva_al_tetto():
    """L'ora vuota, che e' il caso per cui tutto questo esiste."""
    assert len(live.riempi_con_la_prova([], [_altra(i) for i in range(50)])) \
        == live.TETTO_PARTITE


def test_la_scelta_delle_partite_di_prova_e_STABILE():
    """L'ordine dell'API e' arbitrario: senza un criterio, l'insieme
    cambierebbe a ogni giro e la serie temporale sarebbe fatta di partite
    diverse ogni due minuti."""
    altre = [_altra(i, f"2026-08-10T{10 + i}:00:00Z") for i in range(30)]
    a = [e["nome"] for e in live.riempi_con_la_prova([], altre)]
    b = [e["nome"] for e in live.riempi_con_la_prova([], list(reversed(altre)))]
    assert a == b, "l'insieme dipende dall'ordine in cui l'API le ha elencate"


def test_le_righe_di_prova_finiscono_in_UNA_CARTELLA_SEPARATA():
    """Decisione dell'utente, e la ragione e' che un file misto sarebbe
    esattamente cio' che la separazione esiste per evitare: un modello che
    pesca il Brasile credendo di leggere la Serie A."""
    from src.data import smarkets_archive as arch
    assert live.DEST_PROVA != live.DEST != arch.ARCHIVIO
    assert live.DEST_PROVA.name == "smarkets_prova"


def test_la_cartella_di_prova_dice_cosa_NON_farci():
    """Un README che elenca solo il contenuto non protegge da niente: deve
    dire che questi dati non vanno usati per un modello, e perche'."""
    testo = (Path(__file__).resolve().parents[1] / "data" / "smarkets_prova"
             / "README.md").read_text()
    assert "non sono dati del progetto" in testo.lower()
    assert "campione di comodo" in testo
    assert "raccolti e non usati" in testo


def test_il_tetto_e_il_carico_gia_provato():
    """25 non e' un numero tondo: e' il turno di Carabao Cup dell'08/08, cioe'
    il carico su cui il sistema e' gia' stato misurato."""
    assert live.TETTO_PARTITE == 25
