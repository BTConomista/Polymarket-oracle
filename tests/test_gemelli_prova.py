"""Test del calendario della prova a gemelli (Fase 147).

Il calendario e' un esperimento, non una configurazione: se sbaglia, la
settimana di raccolta produce dati che non rispondono alla domanda. Quindi si
verifica il DISEGNO, non solo il codice -- che ogni livello abbia abbastanza
giorni, e che il contro-bilanciamento ci sia davvero.
"""
from __future__ import annotations

import collections
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gemelli_prova as gp   # noqa: E402


def _giorno(n):
    return gp.INIZIO + dt.timedelta(days=n - 1)


def test_ogni_livello_ha_abbastanza_giorni():
    """Con un giorno solo per livello, una giornata storta e' il livello."""
    per_livello = collections.Counter(gp.CALENDARIO.values())
    assert per_livello[1] >= 4 and per_livello[2] >= 4 and per_livello[4] >= 4
    assert sum(per_livello.values()) == 14


def test_il_contro_bilanciamento_esiste_davvero():
    """LA PARTE CHE CONTA DEL DISEGNO. Senza inversione della seconda
    settimana, N=4 cadrebbe sempre di venerdi'-sabato (giorni pieni) e N=1
    sempre di lunedi'-martedi': la differenza fra i livelli sarebbe
    indistinguibile dalla differenza fra i giorni della settimana."""
    giorni_per_livello = collections.defaultdict(set)
    for n, liv in gp.CALENDARIO.items():
        giorni_per_livello[liv].add(_giorno(n).weekday())

    # i due livelli estremi devono vedere sia inizio sia fine settimana
    for liv in (1, 4):
        g = giorni_per_livello[liv]
        assert min(g) <= 1 and max(g) >= 4, (
            f"il livello {liv} cade solo su {sorted(g)}: non e' bilanciato")


def test_il_residuo_noto_e_dichiarato():
    """N=2 cade sempre a meta' settimana e con 14 giorni non e' evitabile.
    Il test lo FISSA: se un giorno lo si corregge, questo test va aggiornato
    di proposito -- e se peggiora, fallisce."""
    g = {_giorno(n).weekday() for n, liv in gp.CALENDARIO.items() if liv == 2}
    assert g == {2, 3}, f"il residuo su N=2 e' cambiato: {sorted(g)}"
    assert "N=2 cade sempre di mercoledi'" in gp.__doc__


def test_i_gemelli_si_accendono_IN_ORDINE():
    """Al livello 2 lavorano l'1 e il 2, non una coppia a caso: cosi' la serie
    del gemello 1 e' continua per tutti e 14 i giorni ed e' il termine di
    paragone di tutti i confronti."""
    for n in gp.CALENDARIO:
        oggi = _giorno(n)
        attivi = [k for k in range(1, 5) if gp.attivo_oggi(k, oggi)]
        assert attivi == list(range(1, len(attivi) + 1)), (
            f"giorno {n}: attivi {attivi}, non consecutivi da 1")
        assert 1 in attivi, "il gemello 1 dev'essere sempre attivo"


def test_il_gemello_1_lavora_tutti_i_quattordici_giorni():
    assert all(gp.attivo_oggi(1, _giorno(n)) for n in gp.CALENDARIO)


def test_fuori_dalla_prova_la_raccolta_NON_si_ferma():
    """Il rischio di un calendario: che il giorno 15 smetta tutto in silenzio."""
    dopo = gp.INIZIO + dt.timedelta(days=30)
    assert gp.giorno_di_prova(dopo) is None
    assert gp.gemelli_previsti(dopo) == gp.GEMELLI_FUORI_PROVA >= 1
    assert gp.attivo_oggi(1, dopo)
    prima = gp.INIZIO - dt.timedelta(days=3)
    assert gp.attivo_oggi(1, prima), "prima della prova si raccoglie lo stesso"


def test_l_interruttore_spegne_tutto(monkeypatch):
    """La via di fuga se il carico peggiora le cose: deve spegnere ANCHE il
    gemello 1, o non e' un interruttore."""
    monkeypatch.setattr(gp, "PROVA_ATTIVA", False)
    oggi = _giorno(6)                       # un giorno a 4 gemelli
    assert gp.gemelli_previsti(oggi) == 0
    assert not any(gp.attivo_oggi(k, oggi) for k in range(1, 5))
    assert "SPENTA" in gp.descrizione(oggi)


def test_la_descrizione_dice_dove_siamo():
    """Finisce nel log di ogni sessione: senza, fra dieci giorni nessuno sa
    a che livello girava quel file."""
    d = gp.descrizione(_giorno(5))
    assert "giorno 5/14" in d and "4 gemelli" in d


# ---------------------------------------------------------------------------
# I QUATTRO WORKFLOW
# ---------------------------------------------------------------------------

def _wf(n):
    import yaml
    return yaml.safe_load((Path(__file__).resolve().parents[1] / ".github"
                           / "workflows" / f"gemello-{n}.yml").read_text())


def test_i_quattro_gemelli_sono_IDENTICI_tranne_le_tre_cose_che_devono_cambiare():
    """Quattro file quasi uguali divergono: qualcuno corregge un bug in uno e
    dimentica gli altri tre, e la prova misura quattro sistemi diversi invece
    dello stesso sistema quattro volte. Il test fissa che l'unica differenza
    sia numero, cron e gruppo."""
    import re
    testi = {}
    for n in range(1, 5):
        t = (Path(__file__).resolve().parents[1] / ".github" / "workflows"
             / f"gemello-{n}.yml").read_text()
        t = t.replace(f"gemello-{n}", "GRUPPO").replace(f"gemello {n}", "N")
        t = t.replace(f"Gemello {n}", "N").replace(f"--gemello {n}", "--gemello N")
        t = t.replace(f"(gemello {n})", "(N)").replace(f"Gemello {n}:", "N:")
        t = re.sub(r"cron: '\d+ \* \* \* \*'", "cron: CRON", t)
        testi[n] = t
    for n in (2, 3, 4):
        assert testi[n] == testi[1], (
            f"il gemello {n} e' divergente dal gemello 1: i quattro devono "
            f"differire SOLO per numero, cron e gruppo")


def test_ogni_gemello_ha_un_gruppo_di_concorrenza_SUO():
    """Se condividessero il gruppo, quattro gemelli diventerebbero uno in
    fila: la ridondanza sparirebbe e la prova misurerebbe altro."""
    gruppi = {_wf(n)["concurrency"]["group"] for n in range(1, 5)}
    assert len(gruppi) == 4, f"gruppi non distinti: {gruppi}"
    assert all(_wf(n)["concurrency"]["cancel-in-progress"] is False
               for n in range(1, 5))


def test_i_cron_sono_sfalsati():
    """Quattro listini nello stesso secondo sono un picco inutile, e quattro
    run nella stessa coda hanno la stessa sorte se GitHub e' sotto carico."""
    minuti = sorted(int(_wf(n)[True]["schedule"][0]["cron"].split()[0])
                    for n in range(1, 5))
    assert len(set(minuti)) == 4
    distanze = [minuti[i + 1] - minuti[i] for i in range(3)] + [60 - minuti[-1] + minuti[0]]
    assert min(distanze) >= 10, f"due gemelli troppo vicini: {minuti}"


def test_ogni_gemello_passa_il_PROPRIO_numero_allo_script():
    """Il difetto silenzioso di quattro file copiati: uno passa il numero
    sbagliato e due gemelli si credono lo stesso -- i file si sovrascrivono e
    la misura per gemello e' falsa."""
    for n in range(1, 5):
        passi = _wf(n)["jobs"]["raccogli"]["steps"]
        raccolta = next(s for s in passi if "Raccogli" in (s.get("name") or ""))
        assert f"--gemello {n}" in raccolta["run"], f"gemello {n} passa un numero sbagliato"


# --------------------------------------------------------------------------
# LO ZERO: il giro di riparazione, fuori dall'esperimento
# --------------------------------------------------------------------------

def test_lo_zero_lavora_sempre_anche_a_prova_spenta(monkeypatch):
    """Il giro che il cane da guardia lancia per riparare un buco non ha un
    livello nell'esperimento: deve partire e basta. Se dipendesse dal
    calendario, la riparazione smetterebbe di funzionare nei giorni in cui la
    prova prevede pochi gemelli — cioe' proprio quando serve di piu'."""
    for giorno in (gp.INIZIO, gp.INIZIO + dt.timedelta(days=6),
                   gp.INIZIO + dt.timedelta(days=99)):
        assert gp.attivo_oggi(0, giorno) is True
    monkeypatch.setattr(gp, "PROVA_ATTIVA", False)
    assert gp.attivo_oggi(0, gp.INIZIO) is True


def test_non_esistono_DUE_raccoglitori_in_play_accesi_INSIEME():
    """IL TRANELLO DATATO, e il motivo per cui questo test esiste.

    `smarkets-live.yml` e i quattro `gemello-N.yml` fanno **la stessa identica
    cosa**: raccolgono le quote in-play. Il cron del primo e' stato spento
    l'11/08/2026 proprio per questo — finche' erano accesi entrambi, un giorno
    che il calendario chiama «N=1» aveva in realta' DUE raccoglitori, e delle
    8 sessioni attribuite al gemello 1 **3 venivano da li'**.

    Ma il commento in testa a quel file dice «il cron torna il 24/08», e il
    24/08 e' il giorno dopo la fine della prova — quando
    `GEMELLI_FUORI_PROVA = 1` rimette in piedi il gemello 1. Seguire
    quell'istruzione alla lettera ricrea esattamente il guasto: due
    raccoglitori sulle stesse partite, per giunta in **due gruppi di
    concorrenza diversi**, quindi nemmeno capaci di cancellarsi a vicenda.

    Il test non sceglie QUALE dei due debba vivere — e' una decisione da
    prendere, non da indovinare. Pretende solo che non siano accesi tutti e
    due: o il cron di `smarkets-live.yml` resta spento (e il file conserva
    `workflow_dispatch`, che e' il canale con cui il cane da guardia ripara),
    oppure lo si riaccende e allora `GEMELLI_FUORI_PROVA` deve valere 0.
    """
    import yaml

    wf = yaml.safe_load((Path(__file__).resolve().parents[1] / ".github"
                         / "workflows" / "smarkets-live.yml").read_text())
    # in YAML 1.1 la chiave `on:` si carica come il booleano True
    trigger = wf.get(True) or wf.get("on") or {}
    cron_acceso = bool(trigger.get("schedule"))

    if cron_acceso:
        assert gp.GEMELLI_FUORI_PROVA == 0, (
            "smarkets-live.yml ha il cron ACCESO e gemelli_prova.py lascia "
            f"{gp.GEMELLI_FUORI_PROVA} gemello/i fuori dalla prova: sono due "
            "raccoglitori in-play sulle stesse partite, in gruppi di "
            "concorrenza diversi. Spegnere uno dei due.")
    else:
        # Il cron spento non deve portarsi via l'autoriparazione: il guardiano
        # accende questo workflow con `gh workflow run`, e senza
        # `workflow_dispatch` la riparazione in-play sparirebbe in silenzio.
        assert "workflow_dispatch" in trigger, (
            "cron spento E workflow_dispatch assente: il cane da guardia non "
            "ha piu' modo di riaccendere la raccolta in-play")


def test_lo_zero_non_e_un_gemello_e_non_sposta_i_livelli():
    """Il conto dei gemelli previsti non deve cambiare per l'esistenza dello
    zero: e' fuori dall'esperimento, non un livello in piu'."""
    for giorno_n, attesi in gp.CALENDARIO.items():
        oggi = gp.INIZIO + dt.timedelta(days=giorno_n - 1)
        assert gp.gemelli_previsti(oggi) == attesi
        # e i gemelli attivi restano esattamente 1..attesi
        attivi = [n for n in range(1, 5) if gp.attivo_oggi(n, oggi)]
        assert attivi == list(range(1, attesi + 1))
