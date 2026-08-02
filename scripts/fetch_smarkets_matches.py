"""Raccoglie le quote PRE-PARTITA di Smarkets per le 5 leghe, con banco e
puntatore (Fase 116).

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


def _slug_lega(full_slug: str | None) -> str | None:
    m = re.match(r"/sport/football/([^/]+)/", full_slug or "")
    return SLUG_LEGA.get(m.group(1)) if m else None


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
    esposte = {e["lega"] for e in nostre}
    return set(SLUG_LEGA.values()) - esposte


def scandaglia_upcoming() -> tuple[list[dict], int]:
    """Tutte le partite delle 5 leghe che Smarkets espone, e quanti eventi
    calcio ha mostrato in totale (il secondo serve solo alla diagnosi)."""
    nostre, totale = [], 0
    url = "/events/?type=football_match&state=upcoming&limit=200"
    while url:
        d = _get(url)
        for e in d.get("events", []):
            totale += 1
            lega = _slug_lega(e.get("full_slug"))
            if not lega:
                continue
            try:
                inizio = dt.datetime.fromisoformat(
                    (e.get("start_datetime") or "").replace("Z", "+00:00"))
            except ValueError:
                continue
            nostre.append({"event_id": e["id"], "nome": e.get("name"),
                           "lega": lega, "inizio": e.get("start_datetime"),
                           "_inizio": inizio})
        nx = (d.get("pagination") or {}).get("next_page")
        url = f"/events/{nx}" if nx else None
    return nostre, totale


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


def quote_partita(ev: dict, tutti: bool, solo_principali: bool = False) -> list[dict]:
    """Le quote di una partita: una riga per (mercato, contratto)."""
    righe = []
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
        lotto = ",".join(ids[i:i + LOTTO_MERCATI])
        contratti = (_get(f"/markets/{lotto}/contracts/") or {}).get("contracts", [])
        libri = _libri_per_contratto(_get(f"/markets/{lotto}/quotes/") or {})
        for c in contratti:
            mid = str(c.get("market_id") or "")
            if mid not in scelti:
                continue          # l'API puo' restituire piu' di quanto chiesto
            etichetta, nome = scelti[mid]
            libro = libri.get(str(c["id"])) or {}
            p = book_price(libro)
            righe.append({
                "lega": ev["lega"], "partita": ev["nome"],
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
    return righe


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
    a = ap.parse_args(argv)

    nostre, totale = scandaglia_upcoming()

    # R6: prima di tutto, il listino ricevuto ha senso? Un giro che raccoglie
    # zero perche' l'API e' muta deve FALLIRE, non uscire verde come un giro
    # che raccoglie zero perche' e' off-season.
    perche = anomalia_del_listino(totale, len(nostre))
    if perche:
        raise SystemExit(f"ANOMALIA nel listino Smarkets: {perche}")

    # La guardia per-lega (01/08/2026): NON solleva qui, o perderemmo anche le
    # leghe che ci sono. Si raccoglie, si scrive, si esce rosso alla fine.
    mancanti = leghe_assenti(nostre)

    entro = 0 if a.tutte_le_esposte else a.entro_ore
    evs = entro_finestra(nostre, entro)
    quali = "esposte" if entro <= 0 else f"entro {entro}h"
    print(f"eventi calcio nel listino: {totale} | partite delle 5 leghe "
          f"esposte: {len(nostre)} | in raccolta ({quali}): {len(evs)}")
    if mancanti:
        print(f"\n⚠️  LEGHE SENZA NESSUNA PARTITA ESPOSTA: "
              f"{', '.join(sorted(mancanti))}. Probabile rinominamento dello "
              f"slug di competizione a monte (e' gia' successo: spain-laliga "
              f"-> spain-la-liga, 31/07/2026). Controllare SLUG_LEGA contro il "
              f"listino vero PRIMA del calcio d'inizio: i dati pre-partita non "
              f"si recuperano dopo.\n")
    for e in sorted(evs, key=lambda x: x["_inizio"]):
        print(f"   [{e['lega']:15s}] {e['inizio']}  {e['nome']}")

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

    righe = []
    for i, e in enumerate(evs, 1):
        righe += quote_partita(e, a.tutti_i_mercati, a.solo_principali)
        print(f"  [{i}/{len(evs)}] {e['nome']}: {len(righe)} righe totali")

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
        # Un buco DICHIARATO e' innocuo, uno silenzioso no (R6). Chi rilegge
        # l'archivio fra mesi deve poter distinguere «la Liga non c'era» da
        # «la Liga non l'abbiamo chiesta».
        "leghe_senza_partite_esposte": sorted(mancanti),
        "nota_prezzi": ("probabilita' 0-1: p_banco/p_puntatore sono i due lati "
                        "del libro, p_mid il punto medio (somma ~1.005 sulle "
                        "coppie complementari). MAI quote decimali."),
        "avvertenza": ("dati di MERCATO raccolti prospetticamente. Il progetto "
                       "non scommette: sola lettura (CLAUDE.md §5)."),
        "righe": righe,
    }
    dest = _archivio.scrivi(dest, dati)
    print(f"\nscritto {dest.relative_to(ROOT)}  ({len(righe)} righe, "
          f"{len({r['partita'] for r in righe})} partite)")

    # Solo ORA si esce rosso: il file e' salvo, l'allarme e' visibile.
    if mancanti:
        raise SystemExit(
            f"raccolta INCOMPLETA: nessuna partita esposta per "
            f"{', '.join(sorted(mancanti))} (dati comunque salvati in "
            f"{dest.relative_to(ROOT)})")


if __name__ == "__main__":
    main()
