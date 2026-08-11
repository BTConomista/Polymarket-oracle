"""IL CANE DA GUARDIA: «avrei dovuto raccogliere, l'ho fatto?» (Fase 144).

PERCHE' ESISTE, e perche' e' diverso da tutto il resto.

L'08/08/2026 il progetto ha passato una giornata a irrobustire la raccolta:
ritentativi sui 5xx, buchi dichiarati nel file, budget di tempo, gruppi di
concorrenza separati, tre guardiani sul YAML. Tutte cose che rispondono alla
domanda **«il giro e' andato bene?»**.

Poi il raccoglitore in-play e' stato messo in produzione alle 13:47, GitHub
non ha fatto partire nessun cron, e per mezz'ora non ha raccolto niente
mentre venticinque partite del perimetro erano in corso. Nessun run rosso,
nessuna mail, nessun allarme: **un giro che non parte non produce nulla, e
"nulla" e' esattamente cio' che produce anche una notte tranquilla.**
Se n'e' accorto l'utente. Che se ne accorga l'utente e' il difetto.

Questo script risponde a una domanda diversa e piu' difficile:
**«avrei dovuto raccogliere qualcosa, e l'ho fatto?»** Non guarda i run,
guarda l'ARCHIVIO -- cioe' il risultato -- e cerca il silenzio dove sarebbe
dovuto esserci un dato. E' la regola R6 applicata al processo invece che alla
cella: il buco peggiore non e' il file mancante, e' il file mancante che
somiglia a una notte senza partite.

COSA CONTROLLA (ogni controllo dichiara la sua tolleranza e il suo perche'):

  A. FRESCHEZZA DEL LUNGO RAGGIO -- l'ultimo giro «tutte le esposte» non deve
     avere piu' di 26 ore. E' l'unico giro che vede le partite lontane, e se
     smette nessuno se ne accorge per settimane: le partite continuano a
     essere raccolte dai giri densi quando si avvicinano, solo senza la coda
     di traiettoria che e' il motivo per cui il giro esiste (newseason.md §2).
     26 e non 24: il cron parte con 30-40 minuti di ritardo (misurato), e una
     soglia a 24 suonerebbe per il ritardo invece che per il guasto.

  B. COPERTURA DI CHIUSURA -- ogni partita del perimetro che ha giocato nelle
     ultime 36 ore deve avere almeno un prezzo raccolto entro 3 ore dal calcio
     d'inizio. E' la misura che conta per il test prospettico della Fase 78:
     un prezzo di due settimane prima non e' una chiusura.

  C. COPERTURA IN-PLAY -- ogni partita che ha giocato nelle ultime 36 ore
     dovrebbe avere righe in-play dentro la sua finestra. Qui la tolleranza e'
     esplicita e generosa (si segnala solo se la copertura scende sotto la
     meta' delle partite), perche' il live e' nato oggi e le sessioni possono
     legittimamente non coprire tutto.

  D. BUCHI GIA' DICHIARATI -- `partite_incomplete` e `fuori_perimetro` non
     vuoti nei file recenti. Sono informazioni che i file gia' contengono e
     che nessuno andrebbe mai a leggere.

⚠️ CIO' CHE QUESTO SCRIPT **NON** PUO' FARE. Non puo' garantire di girare: e'
esso stesso un cron, e vale per lui la stessa inaffidabilita' che sorveglia.
E' il problema di chi sorveglia il sorvegliante, e non ha una soluzione dentro
GitHub Actions -- ha solo mitigazioni: gira spesso, e quando trova qualcosa
esce ROSSO, che e' il canale che arriva davvero all'utente (e' cosi' che e'
cominciata la sessione dell'08/08). Se un giorno smettessero di arrivare mail
rosse *e* i dati, non ci sarebbe niente qui dentro ad accorgersene.

USO:
    python scripts/controlla_raccolta.py            # il rapporto
    python scripts/controlla_raccolta.py --ore 72   # finestra piu' larga
    python scripts/controlla_raccolta.py --json F   # rapporto leggibile a macchina
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "scripts"))

from src.data import smarkets_archive as _archivio   # noqa: E402
import gemelli_prova as _prova   # noqa: E402

LIVE = ROOT / "data" / "smarkets_live"

# Le soglie, tutte qui e tutte motivate nel docstring.
ORE_LUNGO_RAGGIO = 26      # freschezza dell'ultimo giro «tutte le esposte»
ORE_FINESTRA = 36          # quanto indietro si guarda per le partite giocate
ORE_CHIUSURA = 3           # «chiusura» = un prezzo entro N ore dal via
QUOTA_INPLAY_MINIMA = 0.5  # sotto questa frazione di partite coperte, si segnala

# ⚠️ QUANTO INDIETRO BISOGNA GUARDARE PERCHE' L'IN-PLAY SIA GIUDICABILE.
#
# Una sessione in-play dura fino a 5 ore e **committa solo alla fine**: cio'
# che ha raccolto un'ora fa non e' ancora nell'archivio. Contarlo come
# mancante fa gridare al lupo ogni pomeriggio -- ed e' successo l'11/08, con
# quattro qualificazioni UEFA segnalate come scoperte mentre erano in corso e
# la sessione che le stava raccogliendo era ancora accesa.
#
# 6 ore = i 300 minuti della sessione piu' un margine per il commit e per il
# ritardo del cron. Le partite piu' recenti di cosi' NON si giudicano: si
# dichiarano «in attesa» e le guarda il controllo dopo (che gira ogni 6 ore --
# la stessa scala, non e' un caso).
#
# ⚠️ Il prezzo di questa scelta e' dichiarato: il guardiano e' CIECO
# sull'in-play delle ultime 6 ore. Un guasto che comincia adesso lo vede al
# giro successivo, non a questo.
ORE_INPLAY_GIUDICABILE = 6

# ⚠️ QUANDO UNA CHIUSURA MANCANTE E' RUMORE E QUANDO E' UN GUASTO (Fase 147).
#
# Il guardiano e' stato ROSSO 5 volte su 5 da quando esiste, sempre per lo
# stesso allarme: **1 partita su 44** senza prezzo entro 3h dal via. E' il
# difetto contro cui avevo messo in guardia scrivendo il guardiano stesso --
# «un allarme che suona sempre si smette di leggere» -- e l'ho costruito lo
# stesso.
#
# La soglia non e' arbitraria, viene dal comportamento misurato. La corsa di
# chiusura e' oraria con finestra 2h, e il cron slitta di 30-40 minuti: una
# partita sfugge quando nessun giro cade nella sua finestra, ed e' un evento
# raro ma non nullo. **Una mancanza ogni ~40 partite e' la coda normale di
# quel jitter**; tre o piu' no, quello e' il giro orario che non gira.
#
# Sotto soglia resta una NOTA nel rapporto: il dato perso e' dichiarato lo
# stesso, semplicemente non sveglia nessuno.
CHIUSURE_PERSE_PER_ALLARME = 3      # in assoluto
CHIUSURE_PERSE_QUOTA = 0.10         # oppure in frazione, per giornate piccole


def _iso(s):
    try:
        return dt.datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# L'istante nel nome del file: `2026-08-11T13-49-21` con QUALUNQUE coda dopo.
#
# ⚠️ LA CODA E' IL PUNTO, ed e' costata due giorni di cecita'. La prima
# stesura faceva `base.split("T")` e poi `o.replace("-", ":")`: su
# `2026-08-11T13-49-21-g1` produce `13:49:21:g1`, che non e' un orario, quindi
# `ValueError`, quindi `continue`. Dal 09/08 alle 20:02 -- quando i file hanno
# cominciato a portare il suffisso del gemello -- il guardiano ha smesso di
# vedere **ogni singolo file in-play**, e ha continuato a dire «copertura 0%»
# senza sbagliare un conto: contava zero su un insieme vuoto.
#
# E' il modo peggiore in cui un controllo puo' rompersi: non tace, **grida**,
# e grida esattamente il messaggio che ci si aspetta da un guasto vero. Chi
# leggeva la mail andava a cercare la sentinella, non il parser.
_ISTANTE_NEL_NOME = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})")


def istante_del_file(nome: str) -> dt.datetime | None:
    """L'istante di raccolta dal nome del file, o None se non lo porta.

    Tollera qualunque suffisso dopo i secondi (`-g1`, `-prova`, ...): il nome
    e' un'etichetta a cui si aggiungono pezzi nel tempo, e un parser che
    pretende la forma esatta si rompe al primo pezzo nuovo.
    """
    m = _ISTANTE_NEL_NOME.match(nome)
    if not m:
        return None
    g, hh, mm, ss = m.groups()
    return dt.datetime.fromisoformat(f"{g}T{hh}:{mm}:{ss}+00:00")


def carica(cartella: Path, da: dt.datetime) -> list[dict]:
    """I file dell'archivio toccati dopo `da`, gia' letti.

    Si filtra sul NOME (che porta l'istante) e non sul mtime: il mtime di un
    file appena clonato da git e' l'istante del clone, non della raccolta --
    su un runner effimero sarebbero tutti "di adesso".
    """
    fuori = []
    for f in _archivio.snapshots(cartella):
        quando = istante_del_file(f.name)
        if quando is None or quando < da:
            continue
        d = _archivio.leggi(f)
        d["_file"] = f.name
        d["_quando"] = quando
        fuori.append(d)
    return fuori


def partite_giocate(prematch: list[dict], adesso: dt.datetime,
                    ore: int) -> dict[str, dt.datetime]:
    """Le partite del perimetro il cui calcio d'inizio cade nella finestra.

    Si ricavano dal NOSTRO archivio pre-partita, non da una chiamata all'API:
    cosi' il controllo funziona anche se la rete e' giu' -- ed e' proprio
    quando la rete e' giu' che serve. Il limite e' dichiarato: se non abbiamo
    MAI visto una partita, questo controllo non puo' sapere che esisteva.
    """
    fuori: dict[str, dt.datetime] = {}
    for d in prematch:
        for r in d.get("righe") or []:
            k = _iso(r.get("inizio"))
            if k and adesso - dt.timedelta(hours=ore) <= k <= adesso:
                fuori[r["partita"]] = k
    return fuori


def controlla(adesso: dt.datetime | None = None, ore: int = ORE_FINESTRA) -> dict:
    """Il rapporto completo. `problemi` vuoto = tutto a posto."""
    adesso = adesso or dt.datetime.now(dt.timezone.utc)
    da = adesso - dt.timedelta(hours=max(ore, ORE_LUNGO_RAGGIO) + 24)
    prematch = carica(_archivio.ARCHIVIO, da)
    inplay = carica(LIVE, da) if LIVE.exists() else []

    # `problemi` sono stringhe da leggere, `riparabili` sono etichette da
    # AGIRE. Tenerli separati evita che la riparazione debba interpretare del
    # testo -- cioe' evita che una modifica al messaggio rompa la riparazione.
    problemi, note, riparabili = [], [], set()

    # --- A. freschezza del lungo raggio -------------------------------------
    lunghi = [d for d in prematch if d.get("entro_ore") == 0]
    if not lunghi:
        problemi.append(
            f"A) NESSUN giro di lungo raggio negli ultimi {int((adesso-da).total_seconds()//3600)}h: "
            "e' il solo giro che vede le partite lontane, e la sua traiettoria "
            "non si recupera dopo.")
        riparabili.add("lungo_raggio")
        eta_lungo = None
    else:
        ultimo = max(lunghi, key=lambda d: d["_quando"])
        eta_lungo = (adesso - ultimo["_quando"]).total_seconds() / 3600
        if eta_lungo > ORE_LUNGO_RAGGIO:
            problemi.append(
                f"A) l'ultimo giro di lungo raggio ha {eta_lungo:.1f}h "
                f"(soglia {ORE_LUNGO_RAGGIO}h): {ultimo['_file']}")
            riparabili.add("lungo_raggio")

    # --- B. copertura di chiusura -------------------------------------------
    giocate = partite_giocate(prematch, adesso, ore)
    senza_chiusura, anticipi = [], []
    for partita, kickoff in sorted(giocate.items(), key=lambda kv: kv[1]):
        limite = kickoff - dt.timedelta(hours=ORE_CHIUSURA)
        # ⚠️ Il MINIMO, cioe' la cattura piu' VICINA al fischio. Sembra ovvio e
        # non lo e': in uno script usa-e-getta ho usato `max` e ho concluso che
        # mancavano 21 chiusure su 45 quando c'erano tutte (10/08). `max` da'
        # la cattura piu' LONTANA, che per una partita vista ogni ora e' quella
        # di ieri. Il conto giusto sta qui dentro, testato, cosi' non c'e' piu'
        # motivo di riscriverlo a mano ogni volta.
        viste = [(kickoff - d["_quando"]).total_seconds() / 60
                 for d in prematch
                 if limite <= d["_quando"] <= kickoff
                 and any(r["partita"] == partita for r in (d.get("righe") or []))]
        if viste:
            anticipi.append(min(viste))
        else:
            senza_chiusura.append((partita, kickoff.isoformat()))
    if senza_chiusura:
        quota_perse = len(senza_chiusura) / max(1, len(giocate))
        testo = (f"{len(senza_chiusura)}/{len(giocate)} partite giocate nelle "
                 f"ultime {ore}h senza un prezzo entro {ORE_CHIUSURA}h dal via: "
                 + ", ".join(p for p, _ in senza_chiusura[:6])
                 + (" …" if len(senza_chiusura) > 6 else ""))
        # Sopra soglia e' un guasto (il giro orario non gira); sotto e' la coda
        # normale del jitter del cron, e resta una nota.
        if (len(senza_chiusura) >= CHIUSURE_PERSE_PER_ALLARME
                or quota_perse > CHIUSURE_PERSE_QUOTA):
            problemi.append("B) " + testo)
        else:
            note.append("B) " + testo + "  [sotto soglia: e' la coda normale "
                        "del ritardo del cron, non un guasto]")

    # --- C. copertura in-play ------------------------------------------------
    coperte = set()
    for d in inplay:
        coperte.update(d.get("partite") or [])
    # Solo le partite abbastanza vecchie da essere gia' state committate.
    limite_giudicabile = adesso - dt.timedelta(hours=ORE_INPLAY_GIUDICABILE)
    giudicabili = {p: k for p, k in giocate.items() if k <= limite_giudicabile}
    in_attesa = len(giocate) - len(giudicabili)
    quota = (len(coperte & set(giudicabili)) / len(giudicabili)
             if giudicabili else 1.0)
    if in_attesa:
        note.append(f"C) {in_attesa} partite delle ultime "
                    f"{ORE_INPLAY_GIUDICABILE}h non ancora giudicabili: una "
                    f"sessione in-play dura fino a 5h e committa alla fine")
    if giudicabili and quota < QUOTA_INPLAY_MINIMA:
        problemi.append(
            f"C) in-play su {len(coperte & set(giudicabili))}/{len(giudicabili)} "
            f"partite giocate ({quota:.0%}, soglia {QUOTA_INPLAY_MINIMA:.0%}): "
            "la sentinella non sta girando, oppure gira quando non serve.")
        riparabili.add("in_play")

    # --- D. buchi gia' dichiarati nei file ------------------------------------
    recenti = [d for d in prematch if adesso - d["_quando"] <= dt.timedelta(hours=ore)]
    for d in recenti:
        if d.get("partite_incomplete"):
            note.append(f"D) {d['_file']}: {len(d['partite_incomplete'])} "
                        f"partite incomplete dichiarate")
        if d.get("leghe_senza_partite_esposte"):
            problemi.append(f"D) {d['_file']}: leghe senza partite esposte "
                            f"{d['leghe_senza_partite_esposte']}")
        if d.get("fuori_perimetro"):
            note.append(f"D) {d['_file']}: fuori perimetro "
                        f"{list(d['fuori_perimetro'])[:4]}")

    # --- E. LA MISURA PER GEMELLO (Fase 147) --------------------------------
    # Il guardiano misura la copertura AGGREGATA, ed e' giusto per il suo
    # mestiere. Ma con quattro gemelli, se uno muore gli altri tre coprono, la
    # copertura resta 100% e non lo sappiamo -- mentre «quanto spesso fallisce
    # un singolo gemello» e' esattamente il numero per cui la prova si fa.
    # Qui non si SEGNALA niente: si CONTA, e il conto finisce nel rapporto.
    gemelli: dict = {}
    for d in inplay:
        g = d.get("gemello")
        if g is None:
            continue                       # file pre-Fase 147
        s = gemelli.setdefault(str(g), {"sessioni": 0, "giri": 0, "righe": 0,
                                        "partite": set(), "giri_incompleti": 0,
                                        "mercati_persi": 0, "ritmo_max": 0.0})
        s["sessioni"] += 1
        s["giri"] += sum((d.get("giri") or {}).values())
        s["righe"] += len(d.get("righe") or [])
        s["partite"].update(d.get("partite") or [])
        inc = d.get("giri_incompleti") or []
        s["giri_incompleti"] += len(inc)
        s["mercati_persi"] += sum(x.get("mercati_persi", 0) for x in inc
                                  if isinstance(x.get("mercati_persi"), int))
        s["ritmo_max"] = max(s["ritmo_max"],
                             d.get("intervallo_fra_richieste_s") or 0.0)
    for s in gemelli.values():
        s["partite"] = len(s["partite"])

    return {
        "adesso_utc": adesso.isoformat(),
        # per gemello, e il livello previsto oggi: senza il secondo, «il
        # gemello 3 ha zero sessioni» e' indistinguibile fra «e' morto» e
        # «oggi non era previsto dal calendario».
        "per_gemello": gemelli,
        "gemelli_previsti_oggi": _prova.gemelli_previsti(adesso.date()),
        "giorno_di_prova": _prova.giorno_di_prova(adesso.date()),
        "finestra_ore": ore,
        "file_prematch": len(prematch),
        "file_inplay": len(inplay),
        "eta_lungo_raggio_ore": round(eta_lungo, 1) if eta_lungo is not None else None,
        "partite_giocate_in_finestra": len(giocate),
        "senza_chiusura": senza_chiusura,
        # Quanto prima del fischio e' arrivato l'ultimo prezzo. Non e' un
        # allarme -- e' la QUALITA' della chiusura: 45 partite tutte prese a
        # T-3h sarebbero "100% coperte" e inutili per il test prospettico.
        "anticipo_chiusura_min": ({
            "n": len(anticipi),
            "mediana": round(sorted(anticipi)[len(anticipi) // 2], 1),
            "migliore": round(min(anticipi), 1),
            "peggiore": round(max(anticipi), 1),
        } if anticipi else None),
        "copertura_inplay": round(quota, 3),
        "partite_non_ancora_giudicabili": in_attesa,
        "problemi": problemi,
        "note": note,
        # Cosa si puo' rimettere in piedi da soli, e cosa no. Le partite gia'
        # giocate senza prezzo di chiusura NON sono qui dentro: quel prezzo non
        # esiste piu', e fingere di ripararlo sarebbe peggio che dichiararlo.
        "riparabili": sorted(riparabili),
    }


def ripara(riparabili: set | list) -> list[str]:
    """Rimette in piedi cio' che si puo'. Ritorna cosa ha fatto.

    ⚠️ DUE MODI DIVERSI, e la differenza non e' un dettaglio implementativo.

    Il **lungo raggio** si ripara FACENDOLO QUI, in modo sincrono: le partite
    lontane sono ancora esposte, quindi il dato e' ancora li' da prendere. E
    farlo qui ha una proprieta' che vale piu' della semplicita': **si puo'
    verificare subito se ha funzionato**, ri-eseguendo il controllo dopo. Una
    riparazione che non si puo' verificare e' una speranza.

    L'**in-play** non si puo' fare qui -- durerebbe ore e questo e' un
    controllo da quindici minuti -- e soprattutto non si puo' recuperare: se
    la partita e' finita, quel prezzo non esiste piu'. L'unica riparazione
    sensata e' accendere una sessione **se si sta ancora giocando**, e si fa
    chiedendo a GitHub di lanciare il workflow. Fatto e non verificabile
    subito: sara' il controllo dopo a dire se e' servito.

    ⚠️ Cio' che NON e' qui dentro: le partite gia' giocate senza prezzo di
    chiusura. Quel prezzo non esiste piu' e non c'e' niente da riparare --
    fingere il contrario sarebbe peggio che dichiararlo.
    """
    fatto = []

    if "lungo_raggio" in riparabili:
        print("\n🔧 riparazione: rifaccio il giro di lungo raggio "
              "(le partite lontane sono ancora esposte)")
        sys.path.insert(0, str(ROOT / "scripts"))
        import fetch_smarkets_matches as fsm
        try:
            # budget stretto: questo e' un controllo, non la raccolta ufficiale
            fsm.main(["--tutte-le-esposte", "--tutti-i-mercati",
                      "--budget-minuti", "20"])
            fatto.append("lungo raggio rifatto")
        except SystemExit as e:
            # anche una raccolta incompleta ha scritto il suo file: e' meglio
            # di niente, e il ri-controllo dira' se basta
            fatto.append(f"lungo raggio rifatto, con riserve ({e})")
        except Exception as e:                        # noqa: BLE001
            fatto.append(f"lungo raggio NON riparato ({type(e).__name__}: {e})")

    if "in_play" in riparabili:
        sys.path.insert(0, str(ROOT / "scripts"))
        from fetch_smarkets_matches import scandaglia_live
        try:
            vive, _, _ = scandaglia_live()
        except Exception as ex:                       # noqa: BLE001
            # ⚠️ SI DICE PERCHE'. Questo `except` muto ha gia' inghiottito un
            # errore di programmazione (10/08: `scandaglia_live` era passata
            # da due valori a tre e l'unpacking falliva), facendo credere alla
            # riparazione che non si stesse giocando -- cioe' rispondendo «non
            # c'e' niente da riparare» a un guasto suo. Un guasto di rete e un
            # bug qui producono lo stesso `vive = []`: almeno si distinguono
            # nel log.
            print(f"   ⚠ scandaglio fallito ({type(ex).__name__}: {ex}): "
                  f"non so se si sta giocando, tratto come «no»")
            vive = []
        if not vive:
            fatto.append("in-play NON riparabile: non si sta giocando "
                         "(le partite di prima sono finite, quei prezzi non "
                         "esistono piu')")
        else:
            ok = _accendi_workflow("smarkets-live.yml")
            fatto.append(
                f"in-play: {len(vive)} partite in corso, sessione "
                + ("accesa" if ok else "NON accesa (dispatch fallito)"))
    return fatto


def _accendi_workflow(nome: str) -> bool:
    """Chiede a GitHub di lanciare un workflow. Vero se la richiesta e' passata.

    Usa `gh`, che sui runner c'e' gia'. Il token automatico basta: il
    `workflow_dispatch` e' una delle due eccezioni alla regola per cui gli
    eventi generati da GITHUB_TOKEN non creano nuovi run.
    ⚠️ Se quella regola cambiasse, questa riparazione smetterebbe in silenzio
    -- ed e' per questo che il controllo successivo ri-misura la copertura
    invece di fidarsi del fatto che il dispatch sia partito.
    """
    import subprocess
    try:
        r = subprocess.run(
            ["gh", "workflow", "run", nome], capture_output=True, text=True,
            timeout=60, cwd=ROOT)
        if r.returncode != 0:
            print(f"   ⚠ dispatch fallito: {r.stderr.strip()[:200]}")
        return r.returncode == 0
    except FileNotFoundError:
        print("   ⚠ `gh` non disponibile qui: la riparazione in-play vale "
              "solo dentro GitHub Actions")
        return False
    except Exception as e:                            # noqa: BLE001
        print(f"   ⚠ dispatch fallito: {type(e).__name__}: {e}")
        return False


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ore", type=int, default=ORE_FINESTRA)
    ap.add_argument("--json", type=Path, help="scrive il rapporto anche in JSON")
    ap.add_argument("--ripara", action="store_true",
                    help="non limitarsi a segnalare: rimetti in piedi cio' "
                         "che si puo', poi ri-controlla")
    a = ap.parse_args(argv)

    r = controlla(ore=a.ore)
    print(f"CONTROLLO RACCOLTA — {r['adesso_utc'][:19]}Z (finestra {r['finestra_ore']}h)")
    print(f"  file pre-partita: {r['file_prematch']} | in-play: {r['file_inplay']}")
    print(f"  ultimo lungo raggio: "
          + (f"{r['eta_lungo_raggio_ore']}h fa" if r["eta_lungo_raggio_ore"] is not None else "MAI"))
    print(f"  partite giocate in finestra: {r['partite_giocate_in_finestra']} | "
          f"copertura in-play: {r['copertura_inplay']:.0%}")
    ac = r.get("anticipo_chiusura_min")
    if ac:
        print(f"  ultimo prezzo prima del fischio: mediana T-{ac['mediana']:.0f}min "
              f"(migliore T-{ac['migliore']:.0f}, peggiore T-{ac['peggiore']:.0f}) "
              f"su {ac['n']} partite")
    if r["per_gemello"]:
        print(f"  {_prova.descrizione()}")
        print(f"  {'gemello':>8s} {'sessioni':>9s} {'giri':>6s} {'partite':>8s} "
              f"{'mercati persi':>14s} {'ritmo max':>10s}")
        for g, s in sorted(r["per_gemello"].items()):
            print(f"  {g:>8s} {s['sessioni']:9d} {s['giri']:6d} {s['partite']:8d} "
                  f"{s['mercati_persi']:14d} {s['ritmo_max']:10.2f}")
    for n in r["note"]:
        print(f"  · {n}")
    if a.json:
        a.json.write_text(json.dumps(r, indent=1, ensure_ascii=False))

    if not r["problemi"]:
        print("\n✅ nessun buco: la raccolta sta facendo il suo lavoro.")
        return

    print("\n⚠️  BUCHI TROVATI:")
    for x in r["problemi"]:
        print(f"   {x}")

    if not (a.ripara and r["riparabili"]):
        raise SystemExit("\n⛔ RACCOLTA CON BUCHI:\n" +
                         "\n".join(f"   {x}" for x in r["problemi"]))

    fatto = ripara(r["riparabili"])
    print("\n🔧 riparazione:")
    for x in fatto:
        print(f"   {x}")
    if a.json:
        a.json.write_text(json.dumps({**r, "riparazione": fatto},
                                     indent=1, ensure_ascii=False))

    # ⚠️ IL RI-CONTROLLO E' IL PUNTO. Una riparazione che non si verifica e'
    # una speranza: se dichiarassimo "riparato" senza guardare, un guasto
    # cronico resterebbe verde per sempre -- che e' peggio del problema di
    # partenza, perche' aggiunge la falsa sicurezza.
    dopo = controlla(ore=a.ore)
    if not dopo["problemi"]:
        print("\n✅ riparato e verificato: il buco non c'e' piu'.")
        return
    raise SystemExit(
        "\n⛔ BUCHI RIMASTI DOPO LA RIPARAZIONE:\n"
        + "\n".join(f"   {x}" for x in dopo["problemi"])
        + "\n   (cio' che si poteva rimettere in piedi e' stato tentato: "
        + "; ".join(fatto) + ")")


if __name__ == "__main__":
    main()
