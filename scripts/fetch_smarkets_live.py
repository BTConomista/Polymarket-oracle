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
import datetime as dt
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_smarkets_matches import (  # noqa: E402
    MERCATI_NUCLEO, quote_partita, scandaglia_live)
from src.data import smarkets_archive as _archivio   # noqa: E402

DEST = ROOT / "data" / "smarkets_live"

# La sentinella gira ogni 30 minuti; la sessione dura di piu' APPOSTA, cosi'
# due sessioni consecutive si sovrappongono invece di lasciare un buco quando
# il cron arriva in ritardo. Duplicare qualche giro costa niente (file diversi,
# istanti diversi); un buco nella traiettoria in-play non si recupera.
DURATA_MINUTI = 40
OGNI_NUCLEO = 2       # minuti fra due giri stretti
OGNI_PIENO = 15       # minuti fra due giri a listino intero

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


def un_giro(vive: list[dict], pieno: bool) -> tuple[list[dict], list[dict]]:
    """Un passaggio su tutte le partite in corso. Ritorna (righe, incomplete).

    Stessa politica della Fase 141: una partita che fallisce costa se stessa,
    non il giro -- e qui vale doppio, perche' un giro perso e' un buco in una
    serie temporale che non si puo' ricampionare.
    """
    quando = dt.datetime.now(dt.timezone.utc).isoformat()
    righe, incomplete = [], []
    for ev in vive:
        try:
            r, persi = quote_partita(
                ev, tutti=pieno,
                mercati_ammessi=None if pieno else MERCATI_NUCLEO)
        except Exception as ex:                       # noqa: BLE001
            incomplete.append({"istante": quando, "partita": ev["nome"],
                               "event_id": ev["event_id"],
                               "errore": f"{type(ex).__name__}: {ex}"})
            continue
        if persi:
            incomplete.append({"istante": quando, "partita": ev["nome"],
                               "event_id": ev["event_id"],
                               "mercati_persi": persi})
        for x in r:
            # L'istante e' PER RIGA: un file di sessione contiene decine di
            # giri, e senza questo campo sarebbero indistinguibili -- cioe'
            # una serie temporale senza il tempo.
            x["istante_utc"] = quando
            x["giro"] = "pieno" if pieno else "nucleo"
        righe += r
    return righe, incomplete


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--durata-minuti", type=int, default=DURATA_MINUTI)
    ap.add_argument("--ogni-nucleo", type=int, default=OGNI_NUCLEO)
    ap.add_argument("--ogni-pieno", type=int, default=OGNI_PIENO,
                    help="0 = mai il listino pieno, solo il nucleo")
    ap.add_argument("--dry-run", action="store_true",
                    help="elenca le partite in corso e esce")
    a = ap.parse_args(argv)

    vive, totale = scandaglia_live()
    print(f"partite in corso: {totale} nel mondo, {len(vive)} del perimetro")
    for e in vive:
        print(f"   [{e['lega']:20s}] iniziata {e['inizio']}  {e['nome']}")

    if not vive:
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

    n = 0
    while dt.datetime.now(dt.timezone.utc) < fine:
        adesso = dt.datetime.now(dt.timezone.utc)
        # Il giro pieno ha la precedenza: e' il piu' raro, e farlo slittare
        # dietro al nucleo lo renderebbe sempre in ritardo.
        pieno = t_pieno is not None and adesso >= t_pieno
        if not pieno and adesso < t_nucleo:
            time.sleep(min(5, (t_nucleo - adesso).total_seconds()))
            continue

        r, inc = un_giro(vive, pieno)
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
