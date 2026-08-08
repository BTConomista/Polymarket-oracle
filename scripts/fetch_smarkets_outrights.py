"""Quote outright da SMARKETS (borsa scommesse) — Fase 97.

PERCHE' SMARKETS E NON UN BOOKMAKER. Cercavamo una SECONDA fonte di prezzi
outright oltre a Polymarket, per due motivi: (a) avere un controllo incrociato
sulle probabilita' (se due mercati indipendenti concordano, il prezzo e' solido);
(b) coprire i mercati che Polymarket non quota. Sono stati testati dall'ambiente
cloud, il 25/07/2026:

    Smarkets      API v3 PUBBLICA, senza chiave, JSON     -> ADOTTATA
    OddsPortal    raggiungibile, ma il feed .dat e' AES-cifrato (blob base64):
                  servirebbe estrarre la chiave dal bundle JS -> scartata
    BetExplorer   raggiungibile, ma i percorsi outright danno 404: non ha
                  una sezione outright -> scartata
    The Odds API  200 ma richiede una chiave (401 senza) -> non disponibile
    DraftKings    403 (geo)          bwin / Betfair       000/403 -> bloccati

Smarkets e' una BORSA (come Polymarket, non come un bookmaker): i prezzi sono
ordini di utenti, non quote con margine del banco. La somma dei mid dei mercati
esclusivi esce ~100-102%, non 108-115% come da un bookmaker.

COSA AGGIUNGE RISPETTO A POLYMARKET (misurato il 25/07/2026):
  - la RETROCESSIONE, che Polymarket non quota in nessuna lega — ed e' il
    mercato dove il nostro simulatore e' meglio tarato (Fase 94, deriva adottata);
  - i piazzamenti Top 2/3/4/5/6 e il top-half (Premier, Liga, Ligue 1);
  - sulla PREMIER e' molto piu' liquido di Polymarket (spread 0.24pp su Arsenal
    contro un overround del 5.8%). Sulla SERIE A e' il contrario: spread di
    10.9pp su Inter, praticamente illiquido -> li' vale Polymarket.
  Le due fonti sono COMPLEMENTARI, non ridondanti: nessuna delle due domina.

ATTENZIONE AI PREZZI. L'API restituisce interi in centesimi di punto percentuale
(0-10000): 3448 = 34.48%. Il libro puo' essere vuoto da un lato — con solo il
bid o solo l'ask il mid non esiste e va trattato come dato mancante, non come
prezzo (per questo `mid` puo' essere None e c'e' sempre `spread`).

USO
  python scripts/fetch_smarkets_outrights.py            # stampa le quote di oggi
  python scripts/fetch_smarkets_outrights.py --json F   # scrive il dump grezzo
Come libreria: `rows = fetch_outrights()` (usato da scripts/archive_outrights.py).

API (nessuna autenticazione):
  /v3/events/?parent_id=N      figli di un nodo         (NON /events/N/children/)
  /v3/events/{id}/markets/     mercati di un evento
  /v3/markets/{id}/contracts/  esiti (le squadre)
  /v3/markets/{id}/quotes/     libro ordini per contratto
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.smarkets.com/v3"
FOOTBALL_ROOT = 121005          # nodo "Football"
OUTRIGHT_NODE = 649058          # nodo "Outright": qui vivono i mercati di stagione

# nome dell'evento outright -> chiave interna di lega. Il confronto e' su nome
# NORMALIZZATO (minuscolo, senza punteggiatura) e ancorato: "laliga 2627".
# Serve l'ancoraggio perche' "Championship 26/27" e "Premier League 26/27"
# convivono nello stesso nodo, e una sotto-stringa ingenua le confonderebbe.
LEAGUE_EVENTS = {
    "serie a": "serie_a",
    "premier league": "premier_league",
    "laliga": "la_liga", "la liga": "la_liga",
    "bundesliga": "bundesliga",
    "ligue 1": "ligue_1",
}
# NON aggiungere qui "championship" ne' "serie b" senza risolvere prima
# l'ambiguita' di paese: Smarkets pubblica DUE eventi outright chiamati
# entrambi "Championship 26/27" (inglese e scozzese) con slug identico
# `championship-26-27` e nessun campo che li distingua. La prima versione li
# archiviava insieme e la "Championship" usciva col favorito Livingston FC
# (club scozzese). Le seconde divisioni entreranno quando serviranno davvero,
# con una disambiguazione esplicita (es. per elenco squadre).

# tipo di mercato dal nome. ORDINE SIGNIFICATIVO: il primo che matcha vince.
# Il valore puo' essere una funzione: serve per i piazzamenti, dove il NUMERO
# fa parte del mercato ("Top 4" e "Top 6" sono mercati diversi e collassarli
# entrambi su "place" renderebbe l'archivio inutilizzabile).
MARKET_TYPES = [
    ("relegation", (r"relegation$",)),
    ("top_scorer", (r"top goalscorer", r"golden boot")),
    ("top_half",   (r"finish in top half",)),
    ("top_N",      (r"top (\d+)$",)),                # Top 2/3/4/5/6 -> top2, top4...
    ("champion",   (r"winner$",)),
]

# mercati-novita' da NON archiviare: sono condizionati (escludono una squadra) o
# non riguardano la classifica finale. "w/o Paris Saint Germain - Winner"
# matcherebbe "winner$" e finirebbe archiviato come mercato campione: sbagliato.
# ATTENZIONE: questi pattern girano sul nome GREZZO minuscolo, non su _norm(),
# perche' _norm toglie la punteggiatura e "w/o" diventerebbe "wo" (bug reale:
# la prima versione archiviava "LaLiga - w/o Barcelona & Real Madrid" come
# mercato campione, con due favoriti diversi per la stessa lega).
SKIP = (r"\bw/o\b", r"who will finish higher", r"number of promoted",
        r"best promoted", r"top london", r"top midlands", r"on christmas")

# mercati a esito UNICO (esclusivi): la somma dei prezzi e' l'overround.
# Gli altri (retrocessione, top-N) sono binari INDIPENDENTI: la somma vale
# legittimamente ~3 (tre retrocesse) o ~4 (quattro posti) — rinormalizzare
# sarebbe un errore. Verifica di sanita' riuscita il 25/07/2026: la
# retrocessione Premier somma 287.4% ~ 3 squadre.
EXCLUSIVE = {"champion", "top_scorer"}

# competizioni OMONIME da escludere prima del riconoscimento di lega. Il match
# di lega e' ancorato all'inizio del nome ("serie a 2627"), e questo da solo NON
# basta: "Serie A Women 26/27" comincia con "serie a" e finirebbe archiviato
# come Serie A maschile — due campionati diversi nella stessa serie storica.
EXCLUDE_COMP = (r"\bwomen\b", r"\bwomens\b", r"\bladies\b", r"\bfemminile\b",
                r"\bu\d\d\b", r"\byouth\b", r"\breserves?\b", r"\bprimavera\b",
                r"\bplayoffs?\b", r"promotion")

_norm = lambda s: re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


_THROTTLE = 0.35        # s fra una chiamata e l'altra: l'API limita a ~3/s e
                        # senza pausa il giro completo prende un 429 a meta'

# I codici HTTP che significano «riprova fra un attimo», non «la richiesta e'
# sbagliata». 429 e' il rate limit (gia' gestito dalla Fase 97); i 5xx sono il
# server che vacilla, ed erano trattati come errori definitivi -- il che ha
# ucciso il giro di lungo raggio dell'08/08/2026 con un **503 alla 22a partita
# su 58**, buttando via le 21 gia' raccolte. Un 503 e' per definizione
# temporaneo ("Service Unavailable"): l'unica risposta sensata e' aspettare.
# 4xx restano fatali: se chiediamo un mercato che non esiste, riprovare cinque
# volte non lo fa apparire, e mascherarlo sarebbe peggio.
HTTP_TRANSITORI = {429, 500, 502, 503, 504}


def _get(path: str, retries: int = 5):
    url = path if path.startswith("http") else API + path
    for k in range(retries):
        try:
            time.sleep(_THROTTLE)
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as ex:
            # rate limit o server che vacilla: si aspetta e si riprova, non e'
            # un errore vero. L'attesa e' 3, 6, 12, 24s: un 503 di Smarkets
            # dura tipicamente qualche secondo, e un backoff piu' corto
            # rischia di sprecare i tentativi tutti dentro lo stesso guasto.
            if ex.code not in HTTP_TRANSITORI or k == retries - 1:
                raise
            time.sleep(3 * 2 ** k)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if k == retries - 1:
                raise
            time.sleep(2 ** k)
    return {}


def _paged(path: str, key: str = "events"):
    out, url = [], path
    while url:
        d = _get(url)
        out += d.get(key, [])
        nx = (d.get("pagination") or {}).get("next_page")
        url = "/events/" + nx if nx else None
    return out


def league_of(name: str) -> str | None:
    """Riconosce la lega dal nome dell'evento outright ("Serie A 26/27")."""
    n = _norm(name)
    if any(re.search(p, n) for p in EXCLUDE_COMP):
        return None
    for pat, key in LEAGUE_EVENTS.items():
        # ancorato all'inizio: "serie a 2627" si', "italy serie a women" no
        if n.startswith(pat):
            return key
    return None


def market_type(name: str) -> str | None:
    if any(re.search(p, (name or "").lower()) for p in SKIP):
        return None
    n = _norm(name.split(" - ")[-1] if " - " in name else name)
    for key, pats in MARKET_TYPES:
        for p in pats:
            m = re.search(p, n)
            if m:
                return f"top{m.group(1)}" if key == "top_N" else key
    return None


def book_price(book: dict) -> dict:
    """Prezzo di UN contratto dal suo libro ordini.

    L'API da' interi in centesimi di punto percentuale (3448 = 34.48%).
    Il mid esiste solo col libro a DUE lati; un libro monco NON e' un prezzo —
    ma resta informazione (l'ask e' un tetto al valore equo) e va conservata
    marcata. La prima versione la buttava, e cosi' spariva l'INTERO gruppo di
    mercati Top 2/4/5/6 e top-half della Premier, che ha solo offerte.
    """
    bid = max((x["price"] for x in book.get("bids") or []), default=None)
    ask = min((x["price"] for x in book.get("offers") or []), default=None)
    two = bid is not None and ask is not None
    return dict(
        price=(bid + ask) / 20000 if two else None,
        price_side=("mid" if two else "ask_only" if ask is not None
                    else "bid_only" if bid is not None else "empty"),
        best_bid=bid / 10000 if bid is not None else None,
        best_ask=ask / 10000 if ask is not None else None,
        spread=(ask - bid) / 10000 if two else None)


def outright_events(quiet: bool = True) -> list[dict]:
    """Gli eventi outright delle leghe che ci interessano."""
    evs = _paged(f"/events/?parent_id={OUTRIGHT_NODE}&limit=200")
    keep = []
    for e in evs:
        lg = league_of(e.get("name", ""))
        if lg and e.get("state") in ("upcoming", "live"):
            keep.append(dict(e, _league=lg))
    if not quiet:
        print(f"  {len(keep)} eventi outright utili su {len(evs)}", file=sys.stderr)
    return keep


def fetch_outrights(quiet: bool = True) -> list[dict]:
    """Una riga per (lega, mercato, squadra) con bid/ask/mid e liquidita'."""
    rows = []
    for e in outright_events(quiet):
        lg, eid = e["_league"], e["id"]
        for m in _get(f"/events/{eid}/markets/").get("markets", []):
            mt = market_type(m.get("name", ""))
            if not mt or m.get("state") != "open":
                continue
            contracts = _get(f"/markets/{m['id']}/contracts/").get("contracts", [])
            quotes = _get(f"/markets/{m['id']}/quotes/")
            entries = []
            for c in contracts:
                if c.get("state_or_outcome") not in ("open", None):
                    continue
                entries.append(dict(team=c.get("name", "").strip(),
                                    contract_id=c["id"],
                                    **book_price(quotes.get(c["id"], {}))))
            if not any(x["price_side"] != "empty" for x in entries):
                continue
            priced = [x for x in entries if x["price"] is not None]
            total = sum(x["price"] for x in priced)
            exclusive = mt in EXCLUSIVE
            # la somma si puo' usare per devigare solo se QUASI TUTTI gli esiti
            # hanno un mid: rinormalizzare su un libro mezzo vuoto inventerebbe
            # probabilita' dal nulla
            full = len(priced) >= 0.9 * len(entries) and total > 0
            settled = sum(1 for x in priced if x["price"] <= 0.01 or x["price"] >= 0.99)
            for x in entries:
                if x["price"] is None:
                    x["prob"] = None
                elif exclusive:
                    x["prob"] = x["price"] / total if full else None
                else:
                    x["prob"] = x["price"]
                x.update(source="smarkets", league=lg, market=mt,
                         market_name=m.get("name"), market_id=m["id"],
                         event_title=e.get("name"), event_slug=e.get("slug"),
                         exclusive=exclusive,
                         overround=round(total, 4) if exclusive and full else None,
                         price_sum=round(total, 4) if full else None,
                         book="two_sided" if full else "partial",
                         settled_share=round(settled / len(priced), 3) if priced else None,
                         n_entries=len(entries), n_priced=len(priced))
            rows.extend(entries)
            if not quiet:
                print(f"  {lg:15} {mt:11} {len(priced):2d}/{len(entries):2d} con mid  "
                      f"somma {total*100:6.1f}%   {m.get('name')}", file=sys.stderr)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", help="scrivi il dump grezzo su file")
    args = ap.parse_args(argv)

    rows = fetch_outrights(quiet=False)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
        print(f"Scritto {args.json}", file=sys.stderr)

    import collections
    per = collections.defaultdict(list)
    for r in rows:
        # market_id nella chiave: Smarkets pubblica DUE eventi "Championship
        # 26/27" distinti, e senza l'id i due libri si fondevano in un mercato
        # fantasma da 31 esiti (il campionato ne ha 24)
        per[(r["league"], r["market"], r["market_id"], r["market_name"])].append(r)
    print(f"### SMARKETS — {len(rows)} righe, {len(per)} mercati")
    for (lg, mt, mid, nm), sub in sorted(per.items()):
        pr = [x for x in sub if x["price"] is not None]
        ref = pr or sub
        # su un libro con solo offerte il favorito e' quello con l'ask PIU' ALTO
        # (costa di piu' perche' e' piu' probabile): col min si stampava come
        # "favorito" il piu' sfavorito del listino
        best = max(pr, key=lambda r: r["price"]) if pr else \
            max(sub, key=lambda r: r["best_ask"] if r["best_ask"] is not None else -1)
        sp = [x["spread"] for x in pr if x["spread"] is not None]
        med = sorted(sp)[len(sp) // 2] if sp else None
        val = best["price"] if best["price"] is not None else best["best_ask"]
        tags = [] if ref[0].get("book") == "two_sided" else ["LIBRO PARZIALE"]
        if (ref[0].get("settled_share") or 0) >= 0.9:
            tags.append("gia' deciso")
        somma = f"{ref[0]['price_sum']*100:5.1f}%" if ref[0].get("price_sum") else "    -"
        print(f"  {lg:15} {mt:11} {len(pr):2d}/{len(sub):2d} mid  favorito "
              f"{best['team'][:22]:22} {val*100:5.1f}%  somma {somma}  spread mediano "
              f"{f'{med*100:4.2f}pp' if med is not None else '    -'}  {' '.join(tags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
