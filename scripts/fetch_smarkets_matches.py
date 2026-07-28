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

COSA RACCOGLIE. Solo le partite **imminenti** (default: entro 72 ore) delle 5
leghe. Non tutte le partite future a ogni giro: la traiettoria interessante e'
quella che si addensa verso il calcio d'inizio, e restringere tiene i file
piccoli e le chiamate poche (cortesia verso un'API gratuita).

COSA *NON* FA. Non piazza scommesse e non legge conti: e' sola lettura di
dati pubblici. Il progetto non scommette (CLAUDE.md §5).

FORMATO. Un file per esecuzione in `data/smarkets_matches/YYYY-MM-DDTHH-MM.json`,
**versionato**: sono dati che non si possono ri-scaricare dopo (stessa
politica di `data/outright_snapshots/`). Una riga per
(partita, mercato, contratto) con banco, puntatore, medio, spread e volumi.

USO:
    python scripts/fetch_smarkets_matches.py                 # entro 72h
    python scripts/fetch_smarkets_matches.py --entro-ore 24  # solo l'imminente
    python scripts/fetch_smarkets_matches.py --dry-run       # cosa prenderebbe
    python scripts/fetch_smarkets_matches.py --tutti-i-mercati
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

DEST = ROOT / "data" / "smarkets_matches"

# Le nostre 5 leghe, riconosciute dal segmento di competizione nel `full_slug`
# dell'evento (verificato dal vivo alla Fase 116: tutte e 5 hanno gia' il
# calendario 2026-27 caricato). Il confronto e' ESATTO sul segmento di
# competizione, non "contiene": non perche' `germany-2-bundesliga` collida con
# `germany-bundesliga` (non collide: il "2-" sta in mezzo -- verificato alla
# Fase 116, la prima stesura di questo commento sbagliava), ma perche' un
# match largo su un'API che puo' rinominare i suoi slug e' il modo tipico di
# raccogliere la lega sbagliata senza accorgersene.
SLUG_LEGA = {
    "italy-serie-a": "serie_a",
    "england-premier-league": "premier_league",
    "spain-laliga": "la_liga",
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

_ORA = re.compile(r"^(\d{4}-\d{2}-\d{2})T")


def _slug_lega(full_slug: str | None) -> str | None:
    m = re.match(r"/sport/football/([^/]+)/", full_slug or "")
    return SLUG_LEGA.get(m.group(1)) if m else None


def partite_imminenti(entro_ore: int) -> list[dict]:
    """Le partite delle nostre 5 leghe che iniziano entro N ore."""
    limite = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=entro_ore)
    out, url = [], "/events/?type=football_match&state=upcoming&limit=200"
    while url:
        d = _get(url)
        for e in d.get("events", []):
            lega = _slug_lega(e.get("full_slug"))
            if not lega:
                continue
            try:
                inizio = dt.datetime.fromisoformat(
                    (e.get("start_datetime") or "").replace("Z", "+00:00"))
            except ValueError:
                continue
            if inizio <= limite:
                out.append({"event_id": e["id"], "nome": e.get("name"),
                            "lega": lega, "inizio": e.get("start_datetime")})
        nx = (d.get("pagination") or {}).get("next_page")
        url = f"/events/{nx}" if nx else None
    return out


def quote_partita(ev: dict, tutti: bool) -> list[dict]:
    """Le quote di una partita: una riga per (mercato, contratto)."""
    righe = []
    mercati = (_get(f"/events/{ev['event_id']}/markets/") or {}).get("markets", [])
    for m in mercati:
        nome = m.get("name") or ""
        etichetta = MERCATI_BASE.get(nome)
        if etichetta is None:
            if not tutti:
                continue
            etichetta = re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_")
        contratti = (_get(f"/markets/{m['id']}/contracts/") or {}).get("contracts", [])
        quote = _get(f"/markets/{m['id']}/quotes/") or {}
        libri = quote.get(str(m["id"]), quote)
        for c in contratti:
            libro = (libri or {}).get(str(c["id"])) or {}
            p = book_price(libro)
            righe.append({
                "lega": ev["lega"], "partita": ev["nome"],
                "inizio": ev["inizio"], "event_id": ev["event_id"],
                "mercato": etichetta, "mercato_smarkets": nome,
                "market_id": m["id"], "contratto": c.get("name"),
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
    ap.add_argument("--tutti-i-mercati", action="store_true",
                    help="tutti i ~100 mercati, non solo quelli del listino")
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra le partite che prenderebbe, senza chiedere quote")
    a = ap.parse_args(argv)

    evs = partite_imminenti(a.entro_ore)
    print(f"partite delle 5 leghe entro {a.entro_ore}h: {len(evs)}")
    for e in evs:
        print(f"   [{e['lega']:15s}] {e['inizio']}  {e['nome']}")
    if a.dry_run:
        print("\n--dry-run: nessuna quota richiesta, nessun file scritto.")
        return
    if not evs:
        print("\nnessuna partita in finestra: niente da raccogliere (non e' un errore).")
        return

    righe = []
    for i, e in enumerate(evs, 1):
        righe += quote_partita(e, a.tutti_i_mercati)
        print(f"  [{i}/{len(evs)}] {e['nome']}: {len(righe)} righe totali")

    quando = dt.datetime.now(dt.timezone.utc)
    DEST.mkdir(parents=True, exist_ok=True)
    dest = DEST / f"{quando.strftime('%Y-%m-%dT%H-%M')}.json"
    dest.write_text(json.dumps({
        "fonte": "api.smarkets.com/v3 (borsa, API pubblica senza chiave)",
        "raccolto_utc": quando.isoformat(),
        "entro_ore": a.entro_ore,
        "tutti_i_mercati": a.tutti_i_mercati,
        "nota_prezzi": ("probabilita' 0-1: p_banco/p_puntatore sono i due lati "
                        "del libro, p_mid il punto medio (somma ~1.005 sulle "
                        "coppie complementari). MAI quote decimali."),
        "avvertenza": ("dati di MERCATO raccolti prospetticamente. Il progetto "
                       "non scommette: sola lettura (CLAUDE.md §5)."),
        "righe": righe,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {dest.relative_to(ROOT)}  ({len(righe)} righe, "
          f"{len({r['partita'] for r in righe})} partite)")


if __name__ == "__main__":
    main()
