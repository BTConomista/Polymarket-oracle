"""Raccoglie le quote DURANTE la partita, a cadenza fissa (Fase 143).

PERCHE' ESISTE. Il live e' l'unica famiglia di mercati che il progetto
dichiara scoperta da sempre (CLAUDE.md §6: «restano scoperti HT/FT congiunto,
le combinazioni, e il live»), ed e' irrecuperabile piu' di ogni altro dato:
una quota pre-partita si puo' almeno cercare a posteriori da qualche parte, il
prezzo dell'1X2 al 67' con la partita sull'1-1 non esiste da nessuna parte
appena finisce la partita. Richiesta dell'utente (08/08/2026).

⚠️ IL PROBLEMA NON E' SAPERE QUANDO SI GIOCA: E' CHE IL CRON NON E' PUNTUALE.
Gli orari li abbiamo (Smarkets da' `start_datetime` in UTC con la Z, e il
fuso non e' un problema da risolvere ma da NON introdurre: qui si lavora tutto
in UTC, mai in ora locale). Il problema misurato l'08/08 e' che il cron di
GitHub Actions parte con **30-40 minuti di ritardo** -- i giri delle :07 sono
partiti alle 08:54, 09:49, 10:45, 11:37. Per «ogni due minuti durante la
partita» e' fatale, e mettere un cron ogni due minuti non aiuterebbe: sarebbe
altrettanto in ritardo, e i run finirebbero per cancellarsi a vicenda.

La soluzione e' un job che parte UNA VOLTA e cicla al suo interno: solo
l'avvio e' in ritardo, la cadenza interna e' esatta. Il limite di un job e'
6 ore e il repo e' pubblico, quindi i minuti di Actions non si pagano.

COME FUNZIONA. Una sentinella (il cron) accende questo script; lui guarda che
cosa e' in corso, e se non c'e' niente esce subito senza scrivere. Se c'e'
qualcosa entra in un ciclo a due velocita':
  - **nucleo** ogni 2 minuti: 1X2, O/U 2.5, GG/NG, risultato esatto (~30 righe
    a partita). E' la traiettoria fine, quella che mostra il salto del prezzo
    quando arriva un gol;
  - **listino pieno** ogni 15 minuti: tutti i ~103 mercati che Smarkets espone
    in-play, corner e cartellini e marcatori compresi (~500 righe a partita).
Cadenza scelta dall'utente l'08/08 come punto di partenza prudente: «partiamo
piu' leggeri e vediamo». Si alza misurando, non a sentimento.

IL PUNTEGGIO NON E' UN CAMPO, MA C'E'. Non esiste alcun endpoint di tabellone
(provati `/events/{id}/scores/` e `/state/`: 404). Lo stato della partita si
legge da COSA e' ancora quotato:
  - `stato_mercato` vale `settled` per i mercati gia' decisi. A 3 gol fatti,
    O/U 0.5/1.5/2.5 sono `settled` e la 3.5 e' `live`: il numero di gol e' la
    linea piu' alta regolata, arrotondata per eccesso;
  - il RISULTATO ESATTO tiene solo i punteggi ancora raggiungibili, e il
    minimo componentwise e' il punteggio corrente.
Verificato dal vivo su Cambridge-Barnet (08/08, 13:30): sopravvivevano 2-1,
2-2, 2-3, 3-1, 3-2, 3-3 -> minimo 2-1; e O/U 2.5 `settled` con 3.5 `live` ->
3 gol. **Due segnali indipendenti, stessa risposta.** Lo stesso vale per
corner e cartellini, che hanno le loro linee O/U.

⚠️ Qui si RACCOGLIE e basta: la ricostruzione del punteggio e' una regola da
validare su partite a risultato noto, e finche' non lo e' non entra nel file.
Il file contiene cio' che l'API ha detto, non cio' che ne deduciamo.

DOVE FINISCE. `data/smarkets_live/`, **cartella separata** da
`data/smarkets_matches/` e non un file in piu' li' dentro: sono dati con una
semantica diversa (un prezzo in-play non e' confrontabile con uno pre-partita)
e mescolarli romperebbe in silenzio ogni lettore dell'archivio pre-partita --
`ultimo_listino_completo()` per primo. Un file per SESSIONE, riscritto a ogni
giro: se il job muore si perde al massimo l'ultimo ciclo, non la sessione.

USO:
    python scripts/fetch_smarkets_live.py                  # sessione standard
    python scripts/fetch_smarkets_live.py --dry-run        # cosa raccoglierebbe
    python scripts/fetch_smarkets_live.py --durata-minuti 5 --ogni-nucleo 1
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import datetime as dt
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_smarkets_matches import (  # noqa: E402
    MERCATI_NUCLEO, quote_partita, scandaglia_live, scandaglia_upcoming)
from src.data import smarkets_archive as _archivio   # noqa: E402

DEST = ROOT / "data" / "smarkets_live"

# La sentinella gira ogni 30 minuti; la sessione dura di piu' APPOSTA, cosi'
# due sessioni consecutive si sovrappongono invece di lasciare un buco quando
# il cron arriva in ritardo. Duplicare qualche giro costa niente (file diversi,
# istanti diversi); un buco nella traiettoria in-play non si recupera.
# ⚠️ RI-PENSATO (Fase 144, poche ore dopo). La prima stesura durava 40 minuti
# e si appoggiava alla sentinella per la continuita': sbagliato due volte.
# (a) La sentinella e' un cron di GitHub, cioe' la cosa meno affidabile che
#     abbiamo -- il workflow live e' rimasto ZERO run per mezz'ora con 25
#     partite in corso, e se n'e' accorto l'utente.
# (b) Una sessione corta perde le partite che cominciano MENTRE gira.
# Ora la sessione copre un blocco intero (5 ore, sotto il tetto di 6 di un
# job) e si spegne da sola quando il calcio finisce: cosi' un solo cron andato
# a buon fine basta a coprire un pomeriggio, invece di dieci.
DURATA_MINUTI = 300
OGNI_NUCLEO = 2       # minuti fra due giri stretti
OGNI_PIENO = 15       # minuti fra due giri a listino intero

# ⚠️ LO SCAGLIONAMENTO (Fase 144-bis, segnalato dall'utente e misurato).
# Le partite non cominciano tutte insieme: 141 partite del perimetro su **82
# orari distinti**, con salti di 15/30/60/75/90 minuti fra un via e il
# successivo (misurato l'08/08; 11 salti su 17 stanno sotto i 90 minuti).
# Sono paesi diversi, e un sabato sera vero e' 18:00 -> 18:30 -> 18:45.
#
# Due conseguenze, entrambe dimenticate nella prima stesura:
#
#  1. ORIZZONTE_PRE -- si segue una partita gia' PRIMA del via, non solo da
#     `state=live`. Era il pezzo della richiesta dell'utente («poco prima
#     dell'inizio») che il raccoglitore in-play non copriva affatto: restava
#     appeso alla corsa oraria di chiusura, che pero' slitta di 30-40 minuti
#     e puo' quindi mancare del tutto una partita. Cosi' invece la traiettoria
#     attraversa il fischio d'inizio senza interruzione.
#
#  2. ORIZZONTE_ATTESA -- non ci si spegne se il prossimo via e' vicino. Con
#     la sola regola dei giri vuoti la sessione sarebbe morta nel buco fra le
#     18:00 e le 18:45, cioe' esattamente dove lo scaglionamento la mette.
#     90 minuti coprono tutti i salti misurati tranne i due lunghi (165 e 210
#     minuti), dove spegnersi e' giusto: li' non si gioca davvero.
ORIZZONTE_PRE = 20
ORIZZONTE_ATTESA = 90

# Ogni quanti giri si ri-legge il listino delle partite FUTURE. Il listino dei
# live e' 1-2 pagine, quello completo ne fa 5: rileggerlo a ogni giro
# costerebbe piu' delle quote di una partita. Ogni 5 giri (~10 minuti) e'
# abbastanza fitto: una partita entra nell'orizzonte 20 minuti prima del via.
GIRI_PER_RILEGGERE_IL_CALENDARIO = 5

# Dopo quanti giri consecutivi SENZA partite del perimetro ci si spegne.
# Non zero: fra la fine di un blocco e l'inizio del successivo puo' esserci
# una pausa, e ri-accendersi dipende di nuovo dal cron. 10 giri di nucleo
# sono ~20 minuti di silenzio -- abbastanza per non spegnersi durante
# l'intervallo di una partita, poco per non tenere acceso un runner a vuoto.
GIRI_VUOTI_PER_SPEGNERSI = 10

# Ogni quanti giri si committa. Il file viene RISCRITTO su disco a ogni giro
# (costa niente), ma su disco del runner non serve a nulla: quello che conta
# e' il commit, ed e' la lezione della Fase 141 -- i dati in memoria, o su un
# runner che muore, sono dati persi. Committare a ogni giro sarebbe pero' un
# commit ogni due minuti: si sceglie un compromesso, e il peggio che puo'
# succedere e' perdere gli ultimi ~10 minuti di una sessione.
GIRI_PER_COMMIT = 5


def prossimo_tick(adesso: dt.datetime, ultimo: dt.datetime,
                  passo_min: int) -> dt.datetime:
    """Il prossimo istante di raccolta, SENZA recuperare gli arretrati.

    Se un giro ha sforato (a 25 partite in contemporanea un giro pieno dura
    ~3 minuti, piu' del passo del nucleo) la cosa giusta e' saltare i tick
    persi e ripartire dal primo futuro. Recuperarli farebbe girare lo script
    a vuoto rincorrendo un orario che non tornera'.
    """
    passo = dt.timedelta(minutes=passo_min)
    nuovo = ultimo + passo
    if nuovo <= adesso:
        saltati = int((adesso - nuovo) / passo) + 1
        nuovo += saltati * passo
    return nuovo


def da_seguire(vive: list[dict], future: list[dict],
               adesso: dt.datetime,
               orizzonte_pre: int = ORIZZONTE_PRE
               ) -> tuple[list[dict], dt.datetime | None]:
    """Chi va raccolto ADESSO, e quando c'e' il prossimo calcio d'inizio.

    Non basta `state=live`: una partita che comincia fra un quarto d'ora e' il
    momento in cui il prezzo pre-partita vale di piu' e sta per sparire per
    sempre. Si comincia a seguirla `orizzonte_pre` minuti prima, cosi' la
    traiettoria attraversa il fischio d'inizio senza un buco.

    Il secondo valore serve a decidere se spegnersi: con gli orari scaglionati
    (15/30/60/75 minuti fra un via e l'altro) «adesso non si gioca» non vuol
    dire «oggi non si gioca piu'».
    """
    per_id = {e["event_id"]: dict(e, fase="live") for e in vive}
    prossimo = None
    for e in future:
        k = e.get("_inizio")
        if k is None or e["event_id"] in per_id:
            continue
        if k <= adesso:
            continue                     # gia' cominciata: la copre `vive`
        if prossimo is None or k < prossimo:
            prossimo = k
        if k <= adesso + dt.timedelta(minutes=orizzonte_pre):
            per_id[e["event_id"]] = dict(e, fase="pre")
    return list(per_id.values()), prossimo


# Quante partite si interrogano in parallelo. Non e' per fare piu' richieste
# al secondo -- quelle restano limitate da `_attendi_il_turno` a ~3/s in tutto
# il processo -- ma per SOVRAPPORRE LE ATTESE DI RETE. Misurato l'08/08: dal
# runner di GitHub una chiamata costa ~1.8s di cui solo 0.35 di throttle, e in
# sequenza un giro pieno su 25 partite ha preso 9'50", zero giri di nucleo.
# 6 lavoratori bastano a saturare il ritmo consentito (6 / 1.8s ≈ 3.3 al
# secondo) senza sfondarlo: oltre, aspetterebbero solo il limitatore.
LAVORATORI = 6


def un_giro(vive: list[dict], pieno: bool) -> tuple[list[dict], list[dict]]:
    """Un passaggio su tutte le partite in corso. Ritorna (righe, incomplete).

    Stessa politica della Fase 141: una partita che fallisce costa se stessa,
    non il giro -- e qui vale doppio, perche' un giro perso e' un buco in una
    serie temporale che non si puo' ricampionare.
    """
    giro_id = dt.datetime.now(dt.timezone.utc).isoformat()
    righe, incomplete = [], []

    def una(ev):
        letto = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            r, persi = quote_partita(
                ev, tutti=pieno,
                mercati_ammessi=None if pieno else MERCATI_NUCLEO)
        except Exception as ex:                       # noqa: BLE001
            return [], [{"istante": letto, "partita": ev["nome"],
                         "event_id": ev["event_id"],
                         "errore": f"{type(ex).__name__}: {ex}"}]
        inc = ([{"istante": letto, "partita": ev["nome"],
                 "event_id": ev["event_id"], "mercati_persi": persi}]
               if persi else [])
        for x in r:
            # ⚠️ DUE tempi, e servono entrambi (Fase 144-ter).
            # `istante_utc` e' quando QUESTA partita e' stata letta: un giro su
            # 25 partite dura minuti, e spalmare tutte le righe sullo stesso
            # istante sarebbe una serie temporale con il tempo sbagliato.
            # `giro_utc` e' l'inizio del giro, e serve a raggruppare le righe
            # che appartengono allo stesso passaggio.
            x["istante_utc"] = letto
            x["giro_utc"] = giro_id
            x["giro"] = "pieno" if pieno else "nucleo"
            # `pre` o `live`: la stessa serie attraversa il calcio d'inizio, e
            # un prezzo che non conosce il punteggio non e' confrontabile con
            # uno che lo conosce. Senza questo campo la distinzione andrebbe
            # ri-dedotta ogni volta dall'orario, cioe' si perderebbe.
            x["fase"] = ev.get("fase", "live")
        return r, inc

    # Le partite in parallelo, le CHIAMATE comunque a ritmo limitato: e' la
    # latenza che si sovrappone, non il numero di richieste al secondo.
    with cf.ThreadPoolExecutor(max_workers=min(LAVORATORI, max(1, len(vive)))) as pool:
        for r, inc in pool.map(una, vive):
            righe += r
            incomplete += inc
    return righe, incomplete


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--durata-minuti", type=int, default=DURATA_MINUTI)
    ap.add_argument("--ogni-nucleo", type=int, default=OGNI_NUCLEO)
    ap.add_argument("--ogni-pieno", type=int, default=OGNI_PIENO,
                    help="0 = mai il listino pieno, solo il nucleo")
    ap.add_argument("--orizzonte-pre", type=int, default=ORIZZONTE_PRE,
                    help="da quanti minuti PRIMA del via si segue una partita")
    ap.add_argument("--orizzonte-attesa", type=int, default=ORIZZONTE_ATTESA,
                    help="non ci si spegne se il prossimo via e' entro N minuti")
    ap.add_argument("--dry-run", action="store_true",
                    help="elenca le partite da seguire e esce")
    a = ap.parse_args(argv)

    vive, totale = scandaglia_live()
    future, _, _ = scandaglia_upcoming()
    adesso0 = dt.datetime.now(dt.timezone.utc)
    seguire, prossimo_via = da_seguire(vive, future, adesso0, a.orizzonte_pre)
    print(f"partite in corso: {totale} nel mondo, {len(vive)} del perimetro | "
          f"da seguire adesso (live + entro {a.orizzonte_pre}'): {len(seguire)}")
    for e in sorted(seguire, key=lambda x: x["inizio"]):
        print(f"   [{e['lega']:20s}] {e['fase']:4s} {e['inizio']}  {e['nome']}")
    if prossimo_via:
        print(f"   prossimo calcio d'inizio: {prossimo_via.isoformat()} "
              f"(fra {(prossimo_via - adesso0).total_seconds()/60:.0f} min)")

    # Si parte anche a mani vuote se il prossimo via e' vicino: e' lo
    # scaglionamento: una sessione che esce subito perche' «adesso non si
    # gioca» tornerebbe a dipendere dal cron per la partita di fra un'ora.
    attesa0 = ((prossimo_via - adesso0).total_seconds() / 60
               if prossimo_via else None)
    if not seguire and not (attesa0 is not None and attesa0 <= a.orizzonte_attesa):
        # NON e' un errore e NON scrive nulla: e' lo stato normale per venti
        # ore al giorno. Ma si dice quante ne stanno giocando nel mondo, cosi'
        # «zero» resta un'informazione: zero nostre su zero mondiali e' notte,
        # zero nostre su cinquanta mondiali va guardato.
        print("nessuna partita del perimetro in corso: niente da raccogliere.")
        return
    if a.dry_run:
        print("\n--dry-run: nessuna quota richiesta, nessun file scritto.")
        return

    avvio = dt.datetime.now(dt.timezone.utc)
    fine = avvio + dt.timedelta(minutes=a.durata_minuti)
    DEST.mkdir(parents=True, exist_ok=True)
    dest = DEST / f"{avvio.strftime('%Y-%m-%dT%H-%M-%S')}.json"

    righe, incomplete, giri = [], [], collections.Counter()
    # `future` e' gia' letto sopra: il ciclo lo rilegge ogni tanto, non subito.
    t_nucleo = avvio
    t_pieno = avvio if a.ogni_pieno > 0 else None

    def scrivi():
        dati = {
            "fonte": "api.smarkets.com/v3 (borsa, API pubblica senza chiave)",
            "tipo": "IN-PLAY: prezzi raccolti a partita in corso. NON sono "
                    "confrontabili con quelli pre-partita di "
                    "data/smarkets_matches/ (li' il prezzo non conosce il "
                    "punteggio, qui si').",
            "sessione_avvio_utc": avvio.isoformat(),
            "sessione_fine_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cadenza_minuti": {"nucleo": a.ogni_nucleo, "pieno": a.ogni_pieno},
            "giri": dict(giri),
            "partite": sorted({r["partita"] for r in righe}),
            "nota_punteggio": (
                "il punteggio NON e' un campo dell'API: si ricostruisce da "
                "`stato_mercato` (le linee O/U gia' `settled`) e dal minimo "
                "componentwise dei punteggi ancora quotati. Qui NON e' "
                "dedotto: il file contiene cio' che l'API ha detto."),
            "nota_prezzi": ("probabilita' 0-1, mai quote decimali. "
                            "`istante_utc` e' per riga: il file e' una serie "
                            "temporale, non uno scatto."),
            "avvertenza": ("dati di MERCATO raccolti prospetticamente. Il "
                           "progetto non scommette: sola lettura (CLAUDE.md §5)."),
            "giri_incompleti": incomplete,
            "righe": righe,
        }
        return _archivio.scrivi(dest, dati)

    n, vuoti = 0, 0
    while dt.datetime.now(dt.timezone.utc) < fine:
        adesso = dt.datetime.now(dt.timezone.utc)
        # Il giro pieno ha la precedenza: e' il piu' raro, e farlo slittare
        # dietro al nucleo lo renderebbe sempre in ritardo.
        pieno = t_pieno is not None and adesso >= t_pieno
        if not pieno and adesso < t_nucleo:
            time.sleep(min(5, (t_nucleo - adesso).total_seconds()))
            continue

        # RI-SCANDAGLIO A OGNI GIRO (Fase 144). Nella prima stesura `vive` era
        # calcolato una volta all'avvio: una partita che cominciava DURANTE la
        # sessione non veniva raccolta da quella sessione, e doveva aspettare
        # il cron successivo -- 30-40 minuti dopo, quando esiste. Con sessioni
        # da 5 ore sarebbe stato il caso normale, non l'eccezione.
        # Costa una chiamata di listino per giro, contro le decine dei
        # prezzi: e' rumore nel conto del tempo.
        try:
            vive, _ = scandaglia_live()
        except Exception as ex:                       # noqa: BLE001
            print(f"  ⚠ scandaglio live fallito ({type(ex).__name__}): "
                  f"si tiene l'elenco precedente")
        # Il calendario delle FUTURE costa 5 pagine invece di 1-2: si rilegge
        # ogni tanto, non a ogni giro. Una partita entra nell'orizzonte 20
        # minuti prima del via, quindi ~10 minuti di stantio sono innocui.
        if n % GIRI_PER_RILEGGERE_IL_CALENDARIO == 0:
            try:
                future, _, _ = scandaglia_upcoming()
            except Exception as ex:                   # noqa: BLE001
                print(f"  ⚠ calendario non riletto ({type(ex).__name__})")

        seguire, prossimo_via = da_seguire(vive, future, adesso, a.orizzonte_pre)

        if not seguire:
            # ⚠️ Qui NON basta contare i giri vuoti: con gli orari scaglionati
            # (18:00 -> 18:30 -> 18:45) «adesso non si gioca» non vuol dire
            # «oggi non si gioca piu'», e spegnersi nel buco significherebbe
            # dipendere di nuovo dal cron per riaccendersi.
            attesa = ((prossimo_via - adesso).total_seconds() / 60
                      if prossimo_via else None)
            if attesa is not None and attesa <= a.orizzonte_attesa:
                if vuoti == 0:
                    print(f"  · pausa: nessuna partita adesso, la prossima "
                          f"fra {attesa:.0f} min -- si resta accesi")
                vuoti = 0
                # si dorme fino a poco prima del via, invece di girare a vuoto
                sonno = max(30.0, min(
                    (attesa - a.orizzonte_pre) * 60, 300.0))
                time.sleep(sonno)
                t_nucleo = prossimo_tick(
                    dt.datetime.now(dt.timezone.utc), t_nucleo, a.ogni_nucleo)
                continue
            vuoti += 1
            if vuoti >= GIRI_VUOTI_PER_SPEGNERSI:
                q = f", la prossima fra {attesa/60:.1f}h" if attesa else ""
                print(f"  nessuna partita del perimetro da {vuoti} giri{q}: "
                      f"la sessione si spegne (non e' un errore).")
                break
            t_nucleo = prossimo_tick(adesso, t_nucleo, a.ogni_nucleo)
            continue
        vuoti = 0

        r, inc = un_giro(seguire, pieno)
        righe += r
        incomplete += inc
        giri["pieno" if pieno else "nucleo"] += 1
        n += 1
        print(f"  giro {n} ({'pieno' if pieno else 'nucleo'}): "
              f"{len(r)} righe, {len(righe)} totali"
              + (f"  ⚠ {len(inc)} problemi" if inc else ""))

        adesso = dt.datetime.now(dt.timezone.utc)
        if pieno:
            t_pieno = prossimo_tick(adesso, t_pieno, a.ogni_pieno)
        t_nucleo = prossimo_tick(adesso, t_nucleo, a.ogni_nucleo)

        if n % GIRI_PER_COMMIT == 0:
            scrivi()

    scritto = scrivi()
    dove = scritto.relative_to(ROOT) if scritto.is_relative_to(ROOT) else scritto
    print(f"\nscritto {dove}  ({len(righe)} righe, {sum(giri.values())} giri "
          f"({giri['nucleo']} nucleo + {giri['pieno']} pieni), "
          f"{len(vive)} partite)")


if __name__ == "__main__":
    main()
