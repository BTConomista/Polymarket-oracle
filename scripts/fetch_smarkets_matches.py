"""Raccoglie le quote PRE-PARTITA di Smarkets, con banco e puntatore (Fase 116).

PERIMETRO (allargato alla Fase 142, decisione utente): i **5 campionati**
modellati, le **coppe nazionali** dei 5 paesi, le competizioni **UEFA per
club** e le **seconde divisioni** dei 5 paesi -- 158 partite misurate l'08/08
contro le 58 di prima. Ogni riga porta `fascia` (campionato/coppa/seconda) ed
e' quella che si filtra: `lega` e' la colonna storica e contiene anche
`coppa_italia` e `serie_b`.

PERCHE' ESISTE. Il test prospettico della Fase 78 -- previsioni congelate
prima del calcio d'inizio e scorate dopo -- e' il gold standard che il
progetto non ha mai potuto eseguire, e ha una scadenza vera: la stagione
2026-27 comincia il **16 agosto** e cio' che non si raccoglie prima del
fischio d'inizio e' perso per sempre (`newseason.md` §2).

Smarkets e' la fonte giusta, ed e' stato verificato alla Fase 115 che da'
**piu' di quanto Betfair darebbe gratis**:
  - **banco e puntatore** (`bids`/`offers`) con le **quantita'** -- su Betfair
    il ladder e il volume sono nei piani ADVANCED/PRO a pagamento;
  - **100 mercati per partita**: 1X2, risultato esatto, GG/NG, O/U 0.5-6.5…
    cioe' i mercati che il progetto prezza e non ha **mai** validato contro
    una quota esterna (finora solo l'handicap asiatico, Fase 88);
  - margine quasi nullo: la somma dei prezzi medi sta a ~100.5%.
E soprattutto: API **pubblica, senza chiave, senza account**, raggiungibile
dall'ambiente cloud del progetto. Nessun VPS, nessun rischio per l'account di
nessuno (il muro di Betfair era contrattuale, non tecnico: Fase 115).

COSA RACCOGLIE. Due regimi, perche' servono due cose diverse:
  - **denso** (default, `--entro-ore 72`): tutti i mercati delle partite
    imminenti. E' la traiettoria che si addensa verso il calcio d'inizio, ed
    e' quella che vale per il test prospettico;
  - **lungo raggio** (`--tutte-le-esposte --solo-principali`): tutte le
    partite che Smarkets espone -- misurato il 28/07/2026: **una giornata per
    lega, ~48 partite in tutto** -- ma solo sui mercati che il motore consuma.
    Serve perche' il listino dell'esordio e' **gia' quotato oggi** e si muove
    da oggi: col solo regime denso non si raccoglierebbe nulla fino al 12
    agosto, e quei 18 giorni di traiettoria sono irrecuperabili
    (`newseason.md` §2).

Il risultato esatto e' ~24 delle ~30 righe per partita: tenerlo fuori dal
lungo raggio e' cio' che rende sostenibile un giro al giorno per una stagione
intera, senza perdere nulla di cio' che il motore usa davvero.

COSA *NON* FA. Non piazza scommesse e non legge conti: e' sola lettura di
dati pubblici. Il progetto non scommette (CLAUDE.md §5).

SE LA RETE FA I CAPRICCI (Fase 141). Il giro **non muore piu' su un guasto
singolo**: un `HTTP 503` alla 22a partita di 58 aveva buttato via 7.870 righe
gia' raccolte. Ora una partita che fallisce costa se stessa, e' DICHIARATA in
`partite_incomplete` dentro il file, e le altre si salvano; l'uscita e' rossa
solo se si perde una partita intera. `--budget-minuti` (45) e' il tetto al
tempo totale: allo scadere si scrive cio' che si ha invece di insistere.
⚠️ Perche' questo serva a qualcosa, il passo di commit del workflow deve
girare **anche se questo script esce rosso** (`if: !cancelled()`).

FORMATO. Un file per esecuzione in `data/smarkets_matches/YYYY-MM-DDTHH-MM.json.gz`,
**versionato e COMPRESSO** (dalla Fase 136: a listino intero il giro giornaliero
fa ~16 MB, il gzip toglie 19,6x senza perdere un byte; l'archivio `.json`
storico resta leggibile, vedi `src/data/smarkets_archive.py`): sono dati che non si possono ri-scaricare dopo (stessa
politica di `data/outright_snapshots/`). Una riga per
(partita, mercato, contratto) con banco, puntatore, medio, spread e volumi.

USO:
    python scripts/fetch_smarkets_matches.py                 # entro 72h
    python scripts/fetch_smarkets_matches.py --entro-ore 24  # solo l'imminente
    python scripts/fetch_smarkets_matches.py --dry-run       # cosa prenderebbe
    python scripts/fetch_smarkets_matches.py --tutti-i-mercati
    python scripts/fetch_smarkets_matches.py --tutte-le-esposte --solo-principali
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Riuso deliberato del client gia' scritto e collaudato per gli outright
# (Fase 97): stesso throttle, stessa gestione del 429, stessa lettura del
# libro ordini. Duplicarli avrebbe voluto dire due comportamenti da tenere
# allineati a mano.
from fetch_smarkets_outrights import _get, book_price   # noqa: E402
from src.data import smarkets_archive as _archivio   # noqa: E402

DEST = ROOT / "data" / "smarkets_matches"

# Le nostre 5 leghe, riconosciute dal segmento di competizione nel `full_slug`
# dell'evento (verificato dal vivo alla Fase 116: tutte e 5 hanno gia' il
# calendario 2026-27 caricato). Il confronto e' ESATTO sul segmento di
# competizione, non "contiene": non perche' `germany-2-bundesliga` collida con
# `germany-bundesliga` (non collide: il "2-" sta in mezzo -- verificato alla
# Fase 116, la prima stesura di questo commento sbagliava), ma perche' un
# match largo su un'API che puo' rinominare i suoi slug e' il modo tipico di
# raccogliere la lega sbagliata senza accorgersene.
#
# ⚠️ Una lega puo' avere PIU' slug: Smarkets li rinomina senza preavviso. Il
# 31/07/2026 `spain-laliga` e' diventato `spain-la-liga` e la Liga e' sparita
# dalla raccolta in silenzio -- proprio la lega che parte per prima (15 agosto).
# Trovato il 01/08/2026 con un giro di controllo a mano, non dal workflow: la
# guardia di allora scattava solo se sparivano TUTTE e 5 (vedi `leghe_assenti`,
# scritta per questo). I vecchi slug NON si tolgono: l'archivio gia' raccolto
# li contiene, e un rinominamento puo' anche essere rimesso indietro.
SLUG_LEGA = {
    "italy-serie-a": "serie_a",
    "england-premier-league": "premier_league",
    "spain-laliga": "la_liga",       # fino al 30/07/2026
    "spain-la-liga": "la_liga",      # dal 31/07/2026 (misurato dal vivo)
    "germany-bundesliga": "bundesliga",
    "france-ligue-1": "ligue_1",
}

# ---------------------------------------------------------------------------
# IL PERIMETRO ALLARGATO (Fase 142, decisione utente 08/08/2026)
#
# Misurato l'08/08: Smarkets espone **865 partite su 124 competizioni** e noi
# ne prendevamo 58, il 6,7%. Fuori restavano cose che il progetto usa o
# vorrebbe usare -- fra cui la Coppa Italia che giocava **quel giorno**.
# Allargato a: coppe nazionali dei nostri 5 paesi, competizioni UEFA per club,
# seconde divisioni dei 5 paesi. Perche' queste tre e non altre:
#   - COPPE: il progetto ha gia' i dati di coppa 2025-26 (Fase 138, 662
#     partite) e non ha **mai** avuto una quota per quelle partite;
#   - SECONDE DIVISIONI: e' il buco del prior neopromosse δ (Fase 7/8), che
#     oggi e' una costante per lega *proprio perche'* non abbiamo dati sulla
#     serie cadetta;
#   - UEFA: il progetto non ha mai avuto una scala di forza comune fra
#     campionati, e il mercato la prezza per noi.
# Costo misurato: +11 min e +710 KB sul giro giornaliero (era 20 min/593 KB).
#
# ⚠️ NON SONO LEGHE, e la colonna si chiama `lega` per compatibilita' con
# l'archivio gia' scritto: ogni riga porta anche `fascia`
# (campionato/coppa/seconda), ed e' quella che va usata per filtrare.
SLUG_ESTESO = {
    # --- coppe nazionali (fascia "coppa") ---
    "italy-coppa-italia": ("coppa_italia", "coppa"),
    "england-league-cup": ("league_cup", "coppa"),
    # --- supercoppe ---
    "germany-supercup": ("supercoppa_germania", "coppa"),
    "france-super-cup": ("supercoppa_francia", "coppa"),
    "uefa-super-cup": ("supercoppa_uefa", "coppa"),
    # --- UEFA per club ---
    "uefa-champions-league-qualification": ("ucl_qual", "coppa"),
    "uefa-europa-league-qualification": ("uel_qual", "coppa"),
    # --- seconde divisioni dei 5 paesi (fascia "seconda") ---
    "italy-serie-b": ("serie_b", "seconda"),
    "england-championship": ("championship", "seconda"),
    "spain-la-liga-2": ("la_liga_2", "seconda"),
    "germany-2-bundesliga": ("bundesliga_2", "seconda"),
    "france-ligue-2": ("ligue_2", "seconda"),
}

# LE ATTESE: competizioni che vogliamo e che l'API **non espone ancora**.
#
# PERCHE' SI TIRA A INDOVINARE, QUI E SOLO QUI. Coppa del Rey, DFB-Pokal,
# Coupe de France, FA Cup e i gironi UEFA cominciano piu' avanti, e l'API di
# Smarkets espone **solo** cio' che e' `upcoming`: non c'e' modo di leggere
# oggi il nome che avranno (provati `/competitions/` e `/sports/`: 404;
# `state=new`: zero eventi). Le alternative erano due, entrambe peggiori:
# aspettare che compaiano e perdere i primi giorni di traiettoria -- che non
# tornano (`newseason.md` §2) -- oppure includere per prefisso di paese, che
# tirerebbe dentro anche National League North e le femminili.
#
# Indovinare qui e' **sicuro** perche' non e' un'assunzione silenziosa: uno
# slug sbagliato semplicemente non combacia mai, e il RADAR qui sotto ci dice
# che cosa e' comparso davvero. Piu' varianti per la stessa coppa costano
# zero, quindi se ne mettono piu' d'una dove la convenzione non e' ovvia
# (osservate dal vivo: `italy-coppa-italia` usa il nome nativo,
# `england-league-cup` e `france-super-cup` no).
SLUG_ATTESI = {
    "england-fa-cup": ("fa_cup", "coppa"),
    "england-community-shield": ("community_shield", "coppa"),
    "spain-copa-del-rey": ("copa_del_rey", "coppa"),
    "spain-copa-rey": ("copa_del_rey", "coppa"),
    "spain-super-cup": ("supercoppa_spagna", "coppa"),
    "spain-supercopa": ("supercoppa_spagna", "coppa"),
    "germany-dfb-pokal": ("dfb_pokal", "coppa"),
    "germany-pokal": ("dfb_pokal", "coppa"),
    "france-coupe-de-france": ("coupe_de_france", "coppa"),
    "france-french-cup": ("coupe_de_france", "coppa"),
    "italy-super-cup": ("supercoppa_italia", "coppa"),
    "italy-supercoppa": ("supercoppa_italia", "coppa"),
    "uefa-champions-league": ("ucl", "coppa"),
    "uefa-europa-league": ("uel", "coppa"),
    "uefa-conference-league": ("uecl", "coppa"),
    "uefa-europa-conference-league": ("uecl", "coppa"),
}

# Il perimetro effettivo: verificati + attesi. Gli attesi non fanno danno
# finche' non compaiono, e il giorno che compaiono sono gia' dentro.
PERIMETRO = {**SLUG_ESTESO, **SLUG_ATTESI}

# IL RADAR (R6 applicato al perimetro, non alla cella).
#
# Il modo realistico in cui perderemo una competizione non e' un errore di
# codice: e' che si chiami diversamente da come l'abbiamo scritta, e che
# nessuno se ne accorga -- esattamente com'e' andata con `spain-laliga` ->
# `spain-la-liga` il 31/07, trovata a mano cinque giorni dopo. Il radar
# elenca ogni competizione dei nostri paesi (o UEFA) che il listino espone e
# che NOI non raccogliamo, e la scrive nel log e nel file. Non decide niente:
# toglie il silenzio.
RADAR_PREFISSI = ("italy-", "england-", "spain-", "germany-", "france-", "uefa-")
# Fuori dal radar cio' che non vogliamo comunque: non e' rumore da guardare
# ogni giorno. Stessa logica di EXCLUDE_COMP in fetch_smarkets_outrights.py.
RADAR_ESCLUSI = re.compile(
    r"women|ladies|femminile|-u\d\d|youth|reserves?|primavera|national-league|"
    r"regionalliga|oberliga|serie-c|serie-d|liga-3|division-3|ligue-3|"
    r"3-liga|league-1|league-2|federacion|national-2|national-3")

# I mercati che il progetto prezza davvero (docs/PANCHINA.md, listino Tier 1).
# Il nome e' quello che usa Smarkets, verificato dal vivo.
MERCATI_BASE = {
    "Full-time result": "1x2",
    "Both teams to score": "ggng",
    "Over/under 1.5": "ou15",
    "Over/under 2.5": "ou25",
    "Over/under 3.5": "ou35",
    "Correct score": "risultato_esatto",
}

# I mercati che il motore consuma davvero: il market-implied inverte 1X2+O/U
# 2.5 (src/models/market_implied.py) e il GG/NG e' quello che il progetto non
# ha mai potuto validare contro una quota esterna. Il regime di lungo raggio si
# ferma a questi.
MERCATI_PRINCIPALI = {"1x2", "ou25", "ggng"}

_ORA = re.compile(r"^(\d{4}-\d{2}-\d{2})T")


def _competizione(full_slug: str | None) -> str | None:
    """Il segmento di competizione dello slug, o None se lo slug e' malformato."""
    m = re.match(r"/sport/football/([^/]+)/", full_slug or "")
    return m.group(1) if m else None


def _slug_lega(full_slug: str | None) -> str | None:
    """La chiave d'archivio della competizione, o None se e' fuori perimetro.

    Il confronto e' ESATTO sul segmento di competizione, non "contiene": un
    match largo su un'API che puo' rinominare i suoi slug e' il modo tipico di
    raccogliere la competizione sbagliata senza accorgersene. Dalla Fase 142
    guarda in tre mappe invece di una, ma la regola non cambia.
    """
    c = _competizione(full_slug)
    if c is None:
        return None
    if c in SLUG_LEGA:
        return SLUG_LEGA[c]
    voce = PERIMETRO.get(c)
    return voce[0] if voce else None


def _fascia(full_slug: str | None) -> str | None:
    """`campionato` per i 5 modellati, `coppa`/`seconda` per il resto.

    E' il campo con cui si filtra: la colonna `lega` porta anche
    `coppa_italia` e `serie_b` dalla Fase 142, e un lettore che facesse
    `groupby('lega')` credendole campionati sbaglierebbe in silenzio.
    """
    c = _competizione(full_slug)
    if c is None:
        return None
    if c in SLUG_LEGA:
        return "campionato"
    voce = PERIMETRO.get(c)
    return voce[1] if voce else None


def fuori_perimetro(competizioni: dict[str, int]) -> dict[str, int]:
    """Il RADAR: competizioni dei nostri paesi (o UEFA) che NON raccogliamo.

    `competizioni` e' {slug: quante partite} come il listino l'ha esposto.
    Ritorna il sottoinsieme che ci riguarderebbe e che sta fuori: e' li' che
    comparira' `germany-dfb-pokal` col nome vero se l'abbiamo indovinato
    sbagliato, ed e' l'unico modo di accorgersene senza guardare a mano.
    """
    return {c: n for c, n in competizioni.items()
            if c.startswith(RADAR_PREFISSI)
            and c not in SLUG_LEGA and c not in PERIMETRO
            and not RADAR_ESCLUSI.search(c)}


def anomalia_del_listino(eventi_totali: int, nostri: int) -> str | None:
    """Il listino ricevuto e' plausibile? Ritorna il motivo, o None se va bene.

    PERCHE' ESISTE (R6, «il buco peggiore e' il finto pieno»). Senza questo
    controllo, «nessuna partita in finestra» e «l'API non ci parla piu'»
    producono lo **stesso** identico esito: zero righe, workflow verde. Se
    Smarkets rinominasse uno slug di competizione, o filtrasse gli IP dei
    runner, raccoglieremmo il nulla per mesi senza che nessuno se ne accorga --
    e i dati pre-partita non si recuperano dopo (`newseason.md` §2).

    La regola non e' assunta, e' **misurata** (28/07/2026, il punto piu'
    profondo dell'off-season: nessuna delle 5 leghe gioca prima del 15 agosto):
    il listino esponeva **709** eventi calcio su 101 competizioni, e tutte e 5
    le nostre erano presenti con **9-10 partite ciascuna**. Quindi «zero
    partite nostre in un listino non vuoto» non e' uno stato che l'off-season
    produce: e' un'anomalia. Zero eventi in assoluto lo e' a maggior ragione --
    da qualche parte nel mondo si gioca sempre.

    ⚠️ `nostri` sono le partite dei 5 CAMPIONATI, non del perimetro (Fase
    142). La differenza non e' formale: le coppe vanno e vengono per
    costruzione -- la Coppa Italia fuori stagione ha zero partite ed e'
    giusto cosi' -- quindi contarle qui dentro spegnerebbe la guardia proprio
    nel caso che deve prendere. Se sparissero tutti e 5 i campionati e
    restassero le coppe, `nostri` deve valere zero e l'allarme deve suonare.
    """
    if eventi_totali == 0:
        return ("il listino delle partite future e' VUOTO: 0 eventi calcio in "
                "tutto. L'API ha risposto ma non dice nulla.")
    if nostri == 0:
        return (f"{eventi_totali} eventi calcio nel listino, ma NESSUNO delle "
                f"nostre 5 leghe: gli slug di competizione attesi "
                f"({', '.join(sorted(SLUG_LEGA))}) non compaiono. "
                "Probabile rinominamento a monte.")
    return None


def leghe_assenti(nostre: list[dict]) -> set[str]:
    """Quali delle nostre 5 leghe non hanno NESSUNA partita esposta.

    PERCHE' ESISTE (01/08/2026, R6 di nuovo -- e questa volta pagata). La
    guardia sopra e' a soglia zero-su-cinque: scatta solo se sparisce tutto.
    Ma il modo realistico in cui un'API rinomina uno slug e' **una lega alla
    volta**: il 31/07/2026 `spain-laliga` e' diventato `spain-la-liga`, la
    Liga e' uscita dalla raccolta e il workflow e' rimasto verde con 38
    partite invece di 48. Quattro leghe su cinque sono un «finto pieno»
    perfetto: il file c'e', e' grosso, e non contiene la lega che parte per
    prima.

    Il 28/07/2026 -- il punto piu' profondo dell'off-season -- tutte e 5 erano
    esposte con 9-10 partite: «lega a zero» non e' uno stato che il calendario
    produca, nemmeno a stagione ferma.

    Non solleva: **segnala**. Far fallire il giro PRIMA della raccolta
    perderebbe anche le altre quattro leghe, e sono dati che non si
    ri-scaricano (`newseason.md` §2). Chi chiama raccoglie tutto, scrive il
    file, e solo dopo esce con codice diverso da zero.
    """
    # Il filtro sulla fascia non e' ridondante dalla Fase 142: `nostre`
    # contiene anche coppe e cadetterie, e senza il filtro basterebbe una
    # collisione di chiave (una coppa che si chiamasse `serie_a`) perche' la
    # guardia si spegnesse da sola.
    esposte = {e["lega"] for e in nostre if e.get("fascia") == "campionato"}
    return set(SLUG_LEGA.values()) - esposte


def scandaglia_upcoming() -> tuple[list[dict], int, dict[str, int]]:
    """Le partite del perimetro, il totale degli eventi calcio, e il conteggio
    per competizione.

    Il terzo valore (Fase 142) serve al radar: senza il listino COMPLETO per
    competizione non si puo' dire che cosa stiamo lasciando fuori.
    """
    nostre, totale, competizioni = [], 0, {}
    url = "/events/?type=football_match&state=upcoming&limit=200"
    while url:
        d = _get(url)
        for e in d.get("events", []):
            totale += 1
            slug = e.get("full_slug")
            c = _competizione(slug)
            if c:
                competizioni[c] = competizioni.get(c, 0) + 1
            lega = _slug_lega(slug)
            if not lega:
                continue
            try:
                inizio = dt.datetime.fromisoformat(
                    (e.get("start_datetime") or "").replace("Z", "+00:00"))
            except ValueError:
                continue
            nostre.append({"event_id": e["id"], "nome": e.get("name"),
                           "lega": lega, "fascia": _fascia(slug),
                           "inizio": e.get("start_datetime"),
                           "_inizio": inizio})
        nx = (d.get("pagination") or {}).get("next_page")
        url = f"/events/{nx}" if nx else None
    return nostre, totale, competizioni


def entro_finestra(nostre: list[dict], entro_ore: int,
                   adesso: dt.datetime | None = None) -> list[dict]:
    """Il sottoinsieme che inizia entro N ore. `entro_ore` <= 0 = nessun
    limite (prende tutto cio' che l'API espone)."""
    if entro_ore <= 0:
        return list(nostre)
    adesso = adesso or dt.datetime.now(dt.timezone.utc)
    limite = adesso + dt.timedelta(hours=entro_ore)
    return [e for e in nostre if e["_inizio"] <= limite]


# Quanti mercati per chiamata. L'API accetta ID separati da virgola sia su
# /contracts/ sia su /quotes/, e senza questo il listino intero e' irraggiungibile:
# 110 mercati x 2 chiamate + 1 = 221 richieste per partita, cioe' oltre 15 minuti
# per SEI partite (misurato: il giro e' stato ucciso dal timeout senza scrivere).
# A lotti di 20 le richieste diventano 13 e la stessa partita si chiude in ~5s:
# **17 volte meno**. E' la differenza fra «tutti i mercati» possibile e impossibile.
LOTTO_MERCATI = 20

# Quanto puo' durare la raccolta prima di scrivere cio' che ha e fermarsi.
#
# PERCHE' ESISTE (08/08/2026). E' il contrappeso ai tentativi ripetuti sui 5xx:
# un guasto ISOLATO costa fino a 45s di attesa (3+6+12+24) e va benissimo, ma
# se Smarkets sta giu' per mezz'ora *ogni* chiamata costa 45s e il giro non
# finisce piu' -- a listino intero sono 58 partite x 13 lotti x 2 chiamate,
# cioe' ore di runner bruciate per non scrivere niente. Il rimedio non e'
# togliere i tentativi: e' dire quando smettere.
#
# 45 minuti: il giro piu' lungo che facciamo -- lungo raggio, tutti i mercati,
# 58 partite -- e' stato misurato a ~20s a partita (log dell'08/08/2026: 21
# partite in 7'30" scandaglio compreso), cioe' ~20 minuti. Il doppio abbondante
# lascia spazio a un giro piu' affollato e a qualche ritentativo senza mai
# tagliare una raccolta sana, e tiene il giro dentro l'ora prima che la corsa
# oraria di chiusura si accodi.
BUDGET_MINUTI = 45


def _etichetta_generica(m: dict, nome: str) -> str:
    """L'etichetta di un mercato fuori da MERCATI_BASE, STABILE fra partite.

    ⚠️ Non si ricava dal nome visualizzato: quello contiene i nomi delle
    squadre («Alaves 0.5 corners / Getafe 0.5 corners»), e slugificarlo dava
    **360 "tipi" su 6 partite** invece di ~56 — etichette irraggiungibili da
    qualunque raggruppamento, cioe' un archivio inutilizzabile. L'API espone
    `market_type.name` (WINNER_3_WAY, CORNERS_HANDICAP, ...) piu' un `param`
    per le linee: quello e' stabile, ed e' quello che si usa.
    """
    mt = m.get("market_type") or {}
    tipo = str(mt.get("name") or "").strip().lower()
    if not tipo:                       # l'API non lo dichiara: si ripiega sul nome
        return re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_")
    param = mt.get("param")
    if param is not None:
        tipo += "_" + re.sub(r"[^a-z0-9]+", "_", str(param).lower()).strip("_")
    return tipo


def _libri_per_contratto(quote: dict) -> dict:
    """Normalizza la risposta di /quotes/, che ha DUE forme.

    Con un mercato solo torna annidata per market_id; a lotti torna piatta per
    contract_id. Verificato dal vivo su entrambe. Distinguerle guardando la
    forma, invece che il numero di ID richiesti, evita di doverci pensare al
    prossimo cambio dell'API.
    """
    if not quote:
        return {}
    campione = next(iter(quote.values()), None)
    if isinstance(campione, dict) and ("bids" in campione or "offers" in campione):
        return quote                     # gia' per contratto
    piatta = {}                          # annidata per mercato: si appiattisce
    for libri in quote.values():
        if isinstance(libri, dict):
            piatta.update(libri)
    return piatta


def quote_partita(ev: dict, tutti: bool,
                  solo_principali: bool = False) -> tuple[list[dict], int]:
    """Le quote di una partita: una riga per (mercato, contratto).

    Ritorna anche **quanti mercati sono andati persi** per un guasto di rete,
    perche' un raccolto parziale che si spaccia per completo e' esattamente il
    «finto pieno» della regola R6: il file c'e', e' grosso, e mancano venti
    mercati che nessuno cerchera' mai piu'. Chi chiama lo dichiara nel file.
    """
    righe, persi = [], 0
    mercati = (_get(f"/events/{ev['event_id']}/markets/") or {}).get("markets", [])

    # Prima si sceglie COSA serve, poi si chiede in blocco: cosi' il costo
    # dipende dai mercati richiesti, non da quelli esposti.
    scelti: dict[str, tuple[str, str]] = {}
    for m in mercati:
        nome = m.get("name") or ""
        etichetta = MERCATI_BASE.get(nome)
        if etichetta is None:
            if not tutti:
                continue
            etichetta = _etichetta_generica(m, nome)
        if solo_principali and etichetta not in MERCATI_PRINCIPALI:
            continue
        scelti[str(m["id"])] = (etichetta, nome)

    ids = list(scelti)
    for i in range(0, len(ids), LOTTO_MERCATI):
        gruppo = ids[i:i + LOTTO_MERCATI]
        lotto = ",".join(gruppo)
        # Un lotto che non arriva costa 20 mercati, non la partita e non il
        # giro: si annota e si prosegue. Il contrario -- propagare -- e' cio'
        # che l'08/08/2026 ha fatto perdere 21 partite gia' in memoria.
        try:
            contratti = (_get(f"/markets/{lotto}/contracts/") or {}).get("contracts", [])
            libri = _libri_per_contratto(_get(f"/markets/{lotto}/quotes/") or {})
        except Exception as ex:                       # noqa: BLE001 - vedi sopra
            persi += len(gruppo)
            print(f"      ⚠ {len(gruppo)} mercati persi ({type(ex).__name__}: {ex})")
            continue
        for c in contratti:
            mid = str(c.get("market_id") or "")
            if mid not in scelti:
                continue          # l'API puo' restituire piu' di quanto chiesto
            etichetta, nome = scelti[mid]
            libro = libri.get(str(c["id"])) or {}
            p = book_price(libro)
            righe.append({
                "lega": ev["lega"],
                # `fascia` e' il campo con cui si filtra dalla Fase 142:
                # `lega` porta anche coppe e cadetterie, e un lettore che le
                # scambiasse per campionati sbaglierebbe in silenzio.
                "fascia": ev.get("fascia", "campionato"),
                "partita": ev["nome"],
                "inizio": ev["inizio"], "event_id": ev["event_id"],
                "mercato": etichetta, "mercato_smarkets": nome,
                "market_id": mid, "contratto": c.get("name"),
                "contract_id": c["id"],
                # book_price (Fase 97): prezzi come PROBABILITA' 0-1, mai quote
                "p_mid": p["price"], "lato": p["price_side"],
                "p_banco": p["best_bid"], "p_puntatore": p["best_ask"],
                "spread": p["spread"],
                # la liquidita': cio' che su Betfair costa (piani a pagamento)
                "vol_banco": sum(x.get("quantity", 0) for x in libro.get("bids") or []),
                "vol_puntatore": sum(x.get("quantity", 0) for x in libro.get("offers") or []),
            })
    return righe, persi


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entro-ore", type=int, default=72,
                    help="raccogli le partite che iniziano entro N ore (default 72)")
    ap.add_argument("--tutte-le-esposte", action="store_true",
                    help="ignora la finestra: tutto cio' che l'API espone (~1 giornata/lega)")
    ap.add_argument("--tutti-i-mercati", action="store_true",
                    help="tutti i ~100 mercati, non solo quelli del listino")
    ap.add_argument("--solo-principali", action="store_true",
                    help=f"solo i mercati che il motore consuma: {sorted(MERCATI_PRINCIPALI)}")
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra le partite che prenderebbe, senza chiedere quote")
    ap.add_argument("--budget-minuti", type=int, default=BUDGET_MINUTI,
                    help=f"tempo massimo di raccolta, poi scrive cio' che ha "
                         f"(default {BUDGET_MINUTI}; <=0 = nessun limite)")
    a = ap.parse_args(argv)

    nostre, totale, competizioni = scandaglia_upcoming()

    # R6: prima di tutto, il listino ricevuto ha senso? Un giro che raccoglie
    # zero perche' l'API e' muta deve FALLIRE, non uscire verde come un giro
    # che raccoglie zero perche' e' off-season. Si conta sui soli CAMPIONATI:
    # le coppe hanno zero partite per mezza stagione ed e' normale.
    campionati = [e for e in nostre if e["fascia"] == "campionato"]
    perche = anomalia_del_listino(totale, len(campionati))
    if perche:
        raise SystemExit(f"ANOMALIA nel listino Smarkets: {perche}")

    # La guardia per-lega (01/08/2026): NON solleva qui, o perderemmo anche le
    # leghe che ci sono. Si raccoglie, si scrive, si esce rosso alla fine.
    mancanti = leghe_assenti(nostre)
    ignorate = fuori_perimetro(competizioni)

    entro = 0 if a.tutte_le_esposte else a.entro_ore
    evs = entro_finestra(nostre, entro)
    quali = "esposte" if entro <= 0 else f"entro {entro}h"
    per_fascia = collections.Counter(e["fascia"] for e in evs)
    print(f"eventi calcio nel listino: {totale} su {len(competizioni)} "
          f"competizioni | perimetro esposto: {len(nostre)} "
          f"({len(campionati)} dei 5 campionati) | in raccolta ({quali}): "
          f"{len(evs)}  " + " ".join(f"{k}={v}" for k, v in sorted(per_fascia.items())))
    if ignorate:
        # Il radar (Fase 142). NON e' un allarme: e' l'elenco di cio' che
        # stiamo lasciando fuori pur riguardandoci, ed e' il posto dove
        # comparira' `germany-dfb-pokal` col nome vero se l'abbiamo scritto
        # sbagliato in SLUG_ATTESI. Silenzio qui = una coppa persa in silenzio.
        print(f"\n📡 fuori perimetro ma dei nostri paesi/UEFA "
              f"({sum(ignorate.values())} partite su {len(ignorate)} competizioni): "
              + ", ".join(f"{c}({n})" for c, n in sorted(ignorate.items())))
    if mancanti:
        print(f"\n⚠️  LEGHE SENZA NESSUNA PARTITA ESPOSTA: "
              f"{', '.join(sorted(mancanti))}. Probabile rinominamento dello "
              f"slug di competizione a monte (e' gia' successo: spain-laliga "
              f"-> spain-la-liga, 31/07/2026). Controllare SLUG_LEGA contro il "
              f"listino vero PRIMA del calcio d'inizio: i dati pre-partita non "
              f"si recuperano dopo.\n")
    # ORDINE DI RACCOLTA = ORDINE DI CALCIO D'INIZIO (Fase 142). Non e'
    # cosmetica: se il budget scade si perde la CODA, e la coda dev'essere
    # cio' che manca di piu' -- una partita fra tre settimane la ri-prendiamo
    # domani, una che comincia fra un'ora no. Prima della Fase 142 il ciclo
    # seguiva l'ordine dell'API, cioe' un ordine arbitrario, e col perimetro
    # allargato toccare il tetto e' diventato plausibile.
    evs = sorted(evs, key=lambda x: x["_inizio"])
    for e in evs:
        print(f"   [{e['lega']:20s}] {e['inizio']}  {e['nome']}")

    if not evs:
        # Non e' un errore, ma non e' nemmeno un non-evento: si dice quanto
        # manca, cosi' «zero» resta un'informazione e non un silenzio.
        prossima = min(nostre, key=lambda x: x["_inizio"])
        ore = (prossima["_inizio"] - dt.datetime.now(dt.timezone.utc)).total_seconds() / 3600
        print(f"\nnessuna partita entro {entro}h, ma {len(nostre)} sono gia' "
              f"esposte: la prima fra {ore:.0f}h ({prossima['inizio']}). "
              "Per prenderle: --tutte-le-esposte.")
        return
    if a.dry_run:
        print("\n--dry-run: nessuna quota richiesta, nessun file scritto.")
        return

    # UNA PARTITA CHE FALLISCE NON FA FALLIRE IL GIRO (08/08/2026).
    # Il giro di lungo raggio delle 06:24 e' morto su un HTTP 503 alla 22a
    # partita su 58, e con lui le 21 gia' in memoria: mai scritte, mai
    # committate, perse per sempre (`newseason.md` §2 -- cio' che non si
    # raccoglie prima del fischio non torna piu'). L'eccezione propagava fino
    # in cima perche' era piu' comodo scrivere il ciclo cosi', non perche'
    # qualcuno avesse deciso che 1 partita su 58 vale le altre 57.
    righe, incomplete = [], []
    scade = (dt.datetime.now(dt.timezone.utc)
             + dt.timedelta(minutes=a.budget_minuti)) if a.budget_minuti > 0 else None
    for i, e in enumerate(evs, 1):
        if scade and dt.datetime.now(dt.timezone.utc) >= scade:
            # Il tempo e' finito: si dichiara cio' che resta e si va a
            # scrivere. Meglio 40 partite salvate e 18 dichiarate perse che
            # 58 perse in silenzio dentro un giro che non finisce.
            for resto in evs[i - 1:]:
                incomplete.append({"partita": resto["nome"],
                                   "event_id": resto["event_id"],
                                   "lega": resto["lega"],
                                   "mercati_persi": "tutti",
                                   "errore": f"budget di {a.budget_minuti} "
                                             f"minuti esaurito"})
            print(f"  ⏱ budget di {a.budget_minuti} minuti esaurito: "
                  f"{len(evs) - i + 1} partite non raccolte, si salva il resto")
            break
        try:
            r, persi = quote_partita(e, a.tutti_i_mercati, a.solo_principali)
        except Exception as ex:                       # noqa: BLE001 - vedi sopra
            incomplete.append({"partita": e["nome"], "event_id": e["event_id"],
                               "lega": e["lega"], "mercati_persi": "tutti",
                               "errore": f"{type(ex).__name__}: {ex}"})
            print(f"  [{i}/{len(evs)}] {e['nome']}: PERSA "
                  f"({type(ex).__name__}: {ex})")
            continue
        righe += r
        if persi:
            incomplete.append({"partita": e["nome"], "event_id": e["event_id"],
                               "lega": e["lega"], "mercati_persi": persi,
                               "errore": "lotti di mercati non arrivati"})
        print(f"  [{i}/{len(evs)}] {e['nome']}: {len(righe)} righe totali"
              + (f"  ⚠ {persi} mercati persi" if persi else ""))

    if not righe:
        # Qui evs non era vuoto (quel caso e' gia' uscito sopra): zero righe
        # significa che NON siamo riusciti a chiedere nulla. Scrivere un file
        # vuoto lo renderebbe indistinguibile da un'off-season.
        raise SystemExit(
            f"raccolta FALLITA: {len(evs)} partite in finestra e zero righe "
            f"raccolte. L'API non ha risposto a nessuna richiesta di quote.")

    quando = dt.datetime.now(dt.timezone.utc)
    DEST.mkdir(parents=True, exist_ok=True)
    # Con i SECONDI, non con i soli minuti: i due regimi (denso e lungo raggio)
    # possono capitare nello stesso minuto, e due file con lo stesso nome
    # significherebbero uno dei due perso in silenzio.
    dest = DEST / f"{quando.strftime('%Y-%m-%dT%H-%M-%S')}.json"
    dati = {
        "fonte": "api.smarkets.com/v3 (borsa, API pubblica senza chiave)",
        "raccolto_utc": quando.isoformat(),
        # 0 = nessun limite (regime di lungo raggio). Serve a sapere, rileggendo
        # l'archivio fra mesi, CHE COSA questo file poteva contenere: un file
        # denso e uno di lungo raggio non sono confrontabili riga per riga.
        "entro_ore": entro,
        "tutti_i_mercati": a.tutti_i_mercati,
        "solo_principali": a.solo_principali,
        "eventi_calcio_nel_listino": totale,
        "partite_nostre_esposte": len(nostre),
        # Dalla Fase 142 il file non contiene solo campionati: senza questi
        # tre campi, chi rilegge fra mesi non puo' sapere CHE COSA questo
        # giro poteva contenere -- e un file di coppe non e' confrontabile
        # riga per riga con uno di soli campionati.
        "perimetro": sorted({(e["fascia"], e["lega"]) for e in evs}),
        "partite_per_fascia": dict(sorted(per_fascia.items())),
        # Il radar: cosa il listino esponeva dei nostri paesi e noi NON
        # abbiamo preso. Un elenco non vuoto non e' un errore -- e' l'unico
        # posto dove si vede una coppa nuova col nome che non avevamo previsto.
        "fuori_perimetro": dict(sorted(ignorate.items())),
        # Un buco DICHIARATO e' innocuo, uno silenzioso no (R6). Chi rilegge
        # l'archivio fra mesi deve poter distinguere «la Liga non c'era» da
        # «la Liga non l'abbiamo chiesta».
        "leghe_senza_partite_esposte": sorted(mancanti),
        # Stesso motivo (R6): chi rilegge deve poter distinguere «quel mercato
        # non era quotato» da «quel mercato non e' arrivato». Vuoto = raccolta
        # completa di tutto cio' che era in finestra.
        "partite_incomplete": incomplete,
        "nota_prezzi": ("probabilita' 0-1: p_banco/p_puntatore sono i due lati "
                        "del libro, p_mid il punto medio (somma ~1.005 sulle "
                        "coppie complementari). MAI quote decimali."),
        "avvertenza": ("dati di MERCATO raccolti prospetticamente. Il progetto "
                       "non scommette: sola lettura (CLAUDE.md §5)."),
        "righe": righe,
    }
    dest = _archivio.scrivi(dest, dati)
    # `relative_to` solleva se il file sta fuori dal repo (ci capita nei test,
    # e capiterebbe con un DEST spostato): un errore nel messaggio d'errore
    # nasconderebbe il motivo vero dell'uscita rossa.
    dove = dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest
    print(f"\nscritto {dove}  ({len(righe)} righe, "
          f"{len({r['partita'] for r in righe})} partite)")

    # Solo ORA si esce rosso: il file e' salvo, l'allarme e' visibile.
    # (Perche' questo funzioni davvero, il passo di commit del workflow deve
    # girare ANCHE se questo passo fallisce: `if: always()` in
    # .github/workflows/smarkets-prematch.yml. Senza, il file resta sul runner
    # e viene buttato -- ed e' quello che e' successo fino all'08/08/2026.)
    allarmi = []
    if mancanti:
        allarmi.append("nessuna partita esposta per "
                       + ", ".join(sorted(mancanti)))
    # Rosso solo per una partita PERSA INTERA, non per qualche mercato: una
    # partita persa e' un buco nella traiettoria pre-partita che nessun giro
    # successivo riempie (quel prezzo, a quell'ora, non esiste piu'), mentre
    # qualche mercato mancante lascia la traiettoria leggibile ed e' gia'
    # dichiarato nel file. La soglia distingue «serve un umano» da «e' andata
    # storta una richiesta»: senza, un 503 isolato su 58 partite manderebbe
    # una mail rossa e le mail rosse che non chiedono nulla si smettono di
    # leggere.
    perse = [x for x in incomplete if x["mercati_persi"] == "tutti"]
    if perse:
        allarmi.append(f"{len(perse)} partite perse per intero: "
                       + ", ".join(x["partita"] for x in perse))
    if allarmi:
        raise SystemExit("raccolta INCOMPLETA: " + "; ".join(allarmi)
                         + f" (dati comunque salvati in {dove})")


if __name__ == "__main__":
    main()
