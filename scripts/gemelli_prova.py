"""Il calendario della PROVA A GEMELLI, e l'interruttore (Fase 145).

PERCHE' UN CALENDARIO E NON QUATTRO WORKFLOW ACCESI A MANO.

La prova deve rispondere a una domanda precisa dell'utente: **aggiungere
gemelli aumenta i rifiuti?** Per rispondere serve una curva, non un aneddoto:
lo stesso sistema con 1, 2, 3, 4 gemelli, e i rifiuti contati **ogni mille
richieste** (non al giorno: il sabato ha 25 partite e il martedi' tre, e senza
normalizzare misureremmo il calendario invece del carico).

E' la regola §1.2 del progetto -- «una cosa alla volta, e si misura: cambia un
solo fattore per esperimento, altrimenti non sai *cosa* ha funzionato». La
prima stesura del piano accendeva quattro gemelli dal primo giorno: avremmo
saputo che «con quattro funziona», non se **servivano**.

⚠️ IL CONTRO-BILANCIAMENTO, che e' la parte non ovvia. Se i livelli seguissero
i giorni in ordine (1,1,2,2,4,4,3) i quattro gemelli cadrebbero **sempre** di
venerdi'-sabato, cioe' nei giorni pieni, e uno solo sempre di lunedi'-martedi'.
La differenza fra i livelli sarebbe indistinguibile dalla differenza fra i
giorni. La seconda settimana e' quindi **invertita**: cosi' N=1 e N=4 vedono
entrambi due giorni vuoti e due pieni.
Residuo dichiarato: **N=2 cade sempre di mercoledi'-giovedi'** e con quattordici
giorni non e' contro-bilanciabile. Il mercoledi' ha le coppe europee, quindi
non e' un giorno vuoto -- ma il limite va saputo leggendo i risultati.

COME SI USA. Ogni gemello ha un numero (1..4) e chiede `attivo_oggi(n)`: se il
suo numero supera i gemelli previsti per oggi, esce subito senza raccogliere.
Cosi' i quattro workflow restano sempre accesi e **il livello si cambia senza
toccare niente ogni giorno** -- che sarebbe una cosa da ricordarsi, cioe' la
cosa che questo progetto ha deciso di non avere piu' (Fase 144).
"""

from __future__ import annotations

import datetime as dt

# ⚠️ L'INTERRUTTORE. `False` spegne TUTTI i gemelli in un colpo, compreso il
# primo: e' la via di fuga se il carico peggiora le cose invece di migliorarle.
# Il gemello 1 e' quello che gira anche fuori dalla prova, quindi spegnere
# tutto significa fermare la raccolta in-play: si fa solo di proposito.
PROVA_ATTIVA = True

# Il giorno 1. Da qui si contano i quattordici giorni.
INIZIO = dt.date(2026, 8, 10)          # lunedi'

# giorno della prova (1-14) -> quanti gemelli devono raccogliere.
# Il calendario e' scritto per esteso invece che generato: si legge, si
# discute e si corregge senza dover eseguire codice.
CALENDARIO = {
    1: 1, 2: 1,      # lun-mar   settimana 1
    3: 2, 4: 2,      # mer-gio
    5: 4, 6: 4,      # ven-sab
    7: 3,            # dom
    8: 4, 9: 4,      # lun-mar   settimana 2  (INVERTITA, vedi docstring)
    10: 2, 11: 2,    # mer-gio
    12: 1, 13: 1,    # ven-sab
    14: 3,           # dom
}

# Fuori dai quattordici giorni: si torna al regime normale, un gemello solo.
# NON zero: la raccolta non deve fermarsi perche' la prova e' finita.
GEMELLI_FUORI_PROVA = 1


def giorno_di_prova(oggi: dt.date | None = None) -> int | None:
    """Che giorno della prova e' oggi (1-14), o None se siamo fuori."""
    oggi = oggi or dt.datetime.now(dt.timezone.utc).date()
    n = (oggi - INIZIO).days + 1
    return n if 1 <= n <= max(CALENDARIO) else None


def gemelli_previsti(oggi: dt.date | None = None) -> int:
    """Quanti gemelli devono raccogliere oggi."""
    if not PROVA_ATTIVA:
        return 0
    g = giorno_di_prova(oggi)
    return CALENDARIO[g] if g else GEMELLI_FUORI_PROVA


def attivo_oggi(gemello: int, oggi: dt.date | None = None) -> bool:
    """Il gemello numero `gemello` deve raccogliere oggi?

    I gemelli si accendono in ordine: al livello 2 lavorano l'1 e il 2, non
    una coppia a caso. Cosi' il gemello 1 e' sempre attivo e la sua serie e'
    continua per tutti e quattordici i giorni -- e' il termine di paragone.
    """
    return 1 <= gemello <= gemelli_previsti(oggi)


def descrizione(oggi: dt.date | None = None) -> str:
    """Una riga da stampare nel log: dove siamo nella prova."""
    oggi = oggi or dt.datetime.now(dt.timezone.utc).date()
    g = giorno_di_prova(oggi)
    if not PROVA_ATTIVA:
        return "prova SPENTA (PROVA_ATTIVA=False): nessun gemello raccoglie"
    if g is None:
        return (f"fuori dalla prova (iniziata il {INIZIO}, 14 giorni): "
                f"regime normale, {GEMELLI_FUORI_PROVA} gemello")
    return (f"prova a gemelli, giorno {g}/14 ({oggi}): "
            f"{CALENDARIO[g]} gemelli previsti")
