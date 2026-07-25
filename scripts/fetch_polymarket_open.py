"""Scarica gli eventi/mercati APERTI da Polymarket (Gamma API) e, su richiesta,
ricostruisce le partite di calcio in 1X2 + O/U + BTTS pronte per market_implied.

Perche' esiste: Polymarket e' l'unica fonte LIVE raggiungibile dall'ambiente
cloud (il proxy la lascia passare — vedi docs/MANUALE_SOPRAVVIVENZA.md §1) da
cui possiamo prendere quote prospettiche reali di partite non ancora giocate.
E' il candidato naturale per il test prospettico 2026-27 (Fase 78) e per dare
in pasto quote vere al motore market-implied (Fase 26/39).

NB: e' un tool LIVE, non fa parte della pipeline offline-first. Il suo output
NON va committato negli snapshot congelati (data/serie_a_matches.csv ecc.):
scrive in --outdir (default data/polymarket/, non versionato).

API (verificata sul campo, 2026-07-24):
  GET https://gamma-api.polymarket.com/events/keyset?closed=false&limit=100
  -> {"events": [...], "next_cursor": "..."}  (paginazione keyset)
  Si avanza passando ?after_cursor=<next_cursor>; si ferma quando manca il
  cursore o il batch e' vuoto.

Struttura dati (importante):
  - un "event" raggruppa piu' "markets" (event["markets"]);
  - outcomes / outcomePrices sono STRINGHE JSON (vanno json.loads);
  - una singola partita e' spezzata in piu' eventi:
      "A vs. B"                -> 1X2, come 3 mercati Yes/No
                                  ("Will A win?" / "...end in a draw?" / "Will B win?")
      "A vs. B - More Markets" -> O/U 1.5/2.5/3.5/4.5 + Both Teams to Score
      "A vs. B - Halftime/Exact Score/..."  -> mercati Tier 3
  - i prezzi (outcomePrices) sono gia' PROBABILITA' implicite (con vig).

Esempi:
  python scripts/fetch_polymarket_open.py                       # dump completo, tutti i tag
  python scripts/fetch_polymarket_open.py --tag Soccer          # solo calcio
  python scripts/fetch_polymarket_open.py --tag "Serie A"       # solo un tag (lega)
  python scripts/fetch_polymarket_open.py --soccer-matches      # partite -> 1X2+O/U+BTTS
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

GAMMA_URL = "https://gamma-api.polymarket.com/events/keyset"

# suffissi di titolo/slug che indicano sotto-eventi della stessa partita
_SUB_SUFFIXES = (
    "more-markets", "halftime-result", "second-half-result",
    "exact-score", "first-to-score", "corners", "cards",
    "total",          # "Total Corners" ha slug ...-total (audit Fase 92: senza
                      # questo il conteggio delle partite usciva gonfiato del ~67%)
)


# --------------------------------------------------------------------------- #
# Fetch                                                                        #
# --------------------------------------------------------------------------- #
def fetch_open_events(closed="false", limit=100, max_pages=0,
                      sleep=0.2, quiet=False):
    """Scarica tutti gli eventi via paginazione keyset. Ritorna una lista."""
    params = {"closed": closed, "limit": limit}
    events, pages = [], 0
    while True:
        for attempt in range(4):
            try:
                r = requests.get(GAMMA_URL, params=params, timeout=30)
                r.raise_for_status()
                break
            except requests.RequestException as exc:
                if attempt == 3:
                    raise
                wait = 2 ** (attempt + 1)
                if not quiet:
                    print(f"  ! errore rete ({exc}); retry tra {wait}s",
                          file=sys.stderr)
                time.sleep(wait)
        data = r.json()
        batch = data.get("events", [])
        events.extend(batch)
        pages += 1
        if not quiet:
            print(f"  pagina {pages}: +{len(batch)} eventi "
                  f"(totale {len(events)})", file=sys.stderr)

        cursor = data.get("next_cursor")
        if not cursor or not batch:
            break
        if max_pages and pages >= max_pages:
            if not quiet:
                print(f"  ! raggiunto --max-pages={max_pages}, stop",
                      file=sys.stderr)
            break
        params["after_cursor"] = cursor
        time.sleep(sleep)
    return events


# --------------------------------------------------------------------------- #
# Helper                                                                       #
# --------------------------------------------------------------------------- #
def event_tags(e):
    return [(t.get("label") if isinstance(t, dict) else str(t))
            for t in (e.get("tags") or [])]


def _loads(x, default):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except (json.JSONDecodeError, TypeError):
            return default
    return x if x is not None else default


def market_outcomes(m):
    """Ritorna dict {outcome_label: prezzo_float} per un mercato."""
    names = _loads(m.get("outcomes"), [])
    prices = _loads(m.get("outcomePrices"), [])
    out = {}
    for n, p in zip(names, prices):
        try:
            out[str(n)] = float(p)
        except (TypeError, ValueError):
            out[str(n)] = None
    return out


def _base_slug(slug):
    """Toglie i suffissi di sotto-evento per ottenere lo slug della partita."""
    for suf in _SUB_SUFFIXES:
        slug = re.sub(rf"-{suf}$", "", slug)
    return slug


def _which_team(question, home, away):
    """A quale squadra si riferisce «Will X win on ...?» — 'home', 'away' o None.

    Si confronta il nome COMPLETO (vince il piu' lungo). La prima parola e' un
    criterio ambiguo e va usata solo come ripiego: 'Manchester City' e
    'Manchester United' la condividono, e con quel criterio la domanda
    sull'OSPITE finiva nel ramo della casa -> `away` restava None e l'intero
    1X2 della partita andava perso (audit Fase 90: 59 partite su 59 con prima
    parola condivisa uscivano senza 1X2; nelle nostre leghe riguarda i derby di
    Manchester e Real Madrid/Betis/Sociedad).
    """
    ql = question.lower()
    hits = [(len(name), role)
            for role, name in (("home", home), ("away", away))
            if name and name.lower() in ql]
    if hits:
        hits.sort(reverse=True)
        if len(hits) > 1 and hits[0][0] == hits[1][0]:
            return None                      # ambiguita' vera: meglio scartare
        return hits[0][1]
    # ripiego sulla prima parola, ma SOLO se ne combacia esattamente una
    first = [role for role, name in (("home", home), ("away", away))
             if name and name.split()[0].lower() in ql]
    return first[0] if len(first) == 1 else None


_OU_LABEL = re.compile(r"^O/U\s*(\d+(?:\.\d+)?)$", re.I)


def _full_match_label(market):
    """Etichetta del mercato ripulita dal titolo della partita, o None.

    Serve a distinguere il mercato del MATCH INTERO dai suoi omonimi per-tempo
    ('1st Half O/U 1.5') e per-squadra ('<squadra> O/U 1.5'), che contengono la
    stessa sottostringa: con una `re.search` l'ultimo incontrato sovrascriveva
    la linea vera (audit Fase 90: O/U 2.5 sbagliato in 6 partite su 28, es.
    0.500 estratto contro 0.295 reale).
    """
    git = (market.get("groupItemTitle") or "").strip()
    if git:
        return git
    # senza groupItemTitle l'etichetta e' la coda della domanda,
    # "Squadra A vs. Squadra B: O/U 2.5"
    q = (market.get("question") or "")
    return q.rsplit(":", 1)[-1].strip() if ":" in q else None


# --------------------------------------------------------------------------- #
# Ricostruzione partite di calcio                                             #
# --------------------------------------------------------------------------- #
def build_soccer_matches(events):
    """Aggrega i sotto-eventi per partita ed estrae 1X2 + O/U + BTTS.

    Ritorna una lista di record: uno per partita, con le probabilita' implicite
    (grezze, con vig) e la versione 1X2 devigata (normalizzata a somma 1).
    """
    soccer = [e for e in events if "Soccer" in event_tags(e)]
    groups = {}
    for e in soccer:
        title = e.get("title") or ""
        if " vs." not in title:
            continue  # scarto futures/outright (winner, capocannoniere, ...)
        key = _base_slug(e.get("slug") or "")
        groups.setdefault(key, []).append(e)

    matches = []
    for key, evs in groups.items():
        rec = {"key": key, "one_x_two": None, "over_under": {}, "btts": None,
               "home": None, "away": None, "end_date": None, "tags": None,
               "event_slugs": [ev.get("slug") for ev in evs]}
        for ev in evs:
            title = ev.get("title") or ""
            base_title = re.split(r"\s+-\s+", title)[0]
            if rec["tags"] is None:
                rec["tags"] = [t for t in event_tags(ev)
                               if t not in ("Sports", "Games", "Soccer")]
            if " vs." in base_title and rec["home"] is None:
                parts = base_title.split(" vs.")
                rec["home"] = parts[0].strip()
                rec["away"] = parts[1].strip() if len(parts) > 1 else None
                rec["end_date"] = ev.get("endDate")

            for m in (ev.get("markets") or []):
                q = (m.get("question") or "")
                o = market_outcomes(m)

                # 1X2: tre mercati Yes/No nell'evento base
                role = None
                if "end in a draw" in q.lower():
                    role = "draw"
                elif re.match(r"^Will .* win", q) and rec.get("home"):
                    role = _which_team(q, rec["home"], rec.get("away"))
                if role:
                    rec.setdefault("_p", {})[role] = o.get("Yes")
                    # spread bid/ask: misura se il prezzo e' VIVO. Su Polymarket
                    # outcomePrices e' l'ultimo scambio, non un mid: su un book
                    # morto (spread 0.01-0.99) il "prezzo" e' arbitrario e la
                    # somma dei tre esiti finisce fuori da ogni margine sensato
                    # (osservati overround 0.895 e 1.679 su partite illiquide).
                    try:
                        sp = float(m.get("bestAsk")) - float(m.get("bestBid"))
                        rec.setdefault("_spread", []).append(sp)
                    except (TypeError, ValueError):
                        rec.setdefault("_spread", []).append(float("nan"))

                # O/U e BTTS: SOLO l'etichetta esatta del match intero
                # (vedi _full_match_label: 'O/U 2.5' si', '1st Half O/U 2.5' no)
                label = _full_match_label(m)
                if label:
                    mu = _OU_LABEL.match(label)
                    if mu and "Over" in o:
                        rec["over_under"][mu.group(1)] = {
                            "over": o.get("Over"), "under": o.get("Under")}
                    elif label.lower() == "both teams to score" and "Yes" in o:
                        rec["btts"] = {"yes": o.get("Yes"), "no": o.get("No")}

        p = rec.pop("_p", {})
        spreads = [s for s in rec.pop("_spread", []) if s == s]   # scarta i NaN
        rec["max_spread"] = round(max(spreads), 4) if spreads else None
        if all(p.get(k) is not None for k in ("home", "draw", "away")):
            s = p["home"] + p["draw"] + p["away"]
            rec["one_x_two"] = {
                "raw": {k: round(p[k], 4) for k in ("home", "draw", "away")},
                "devig": {k: round(p[k] / s, 4)
                          for k in ("home", "draw", "away")},
                "overround": round(s, 4),
                # PREZZO UTILIZZABILE? Un book vivo ha overround > 1 (il vig) e
                # spread stretti. Fuori da questa banda il prezzo e' l'ultimo
                # scambio su un book fermo: NON darlo in pasto a market_implied.
                "usable": bool(1.0 <= s <= 1.6
                               and (rec["max_spread"] is None
                                    or rec["max_spread"] <= 0.15)),
            }
        matches.append(rec)

    # ordina: prima le partite col 1X2 completo, poi per data
    matches.sort(key=lambda r: (r["one_x_two"] is None, r["end_date"] or ""))
    return matches


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--closed", choices=["false", "true", "all"],
                    default="false", help="stato eventi (default: false = aperti)")
    ap.add_argument("--tag", action="append", default=[],
                    help="filtra per etichetta di tag esatta (ripetibile)")
    ap.add_argument("--limit", type=int, default=100, help="eventi per pagina")
    ap.add_argument("--max-pages", type=int, default=0,
                    help="tetto di sicurezza sul numero di pagine (0 = nessuno)")
    ap.add_argument("--soccer-matches", action="store_true",
                    help="ricostruisci le partite di calcio (1X2+O/U+BTTS)")
    ap.add_argument("--outdir", default="data/polymarket",
                    help="cartella di output (default: data/polymarket)")
    ap.add_argument("--no-save", action="store_true",
                    help="non scrivere file, solo riepilogo a video")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    # "all" -> nessun filtro sullo stato (stringa vuota); altrimenti "false"/"true"
    closed = "" if args.closed == "all" else args.closed
    events = fetch_open_events(closed=closed, limit=args.limit,
                               max_pages=args.max_pages, quiet=args.quiet)

    if args.tag:
        wanted = set(args.tag)
        events = [e for e in events if wanted & set(event_tags(e))]

    n_markets = sum(len(e.get("markets") or []) for e in events)
    print(f"Eventi: {len(events)} | mercati: {n_markets}"
          + (f" | filtro tag: {args.tag}" if args.tag else ""))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    outdir = Path(args.outdir)
    if not args.no_save:
        outdir.mkdir(parents=True, exist_ok=True)
        raw_path = outdir / f"open_events_{stamp}.json"
        raw_path.write_text(json.dumps(events, ensure_ascii=False, indent=2))
        print(f"  scritto: {raw_path}")

    if args.soccer_matches:
        # attenzione: --tag "Serie A" esclude gli eventi senza quel tag; per la
        # ricostruzione serve il tag "Soccer", quindi conviene NON filtrare via
        # --tag e passare invece il set completo (build_soccer_matches filtra da se').
        matches = build_soccer_matches(events)
        with_1x2 = [m for m in matches if m["one_x_two"]]
        print(f"Partite di calcio: {len(matches)} "
              f"({len(with_1x2)} con 1X2 completo)")
        for m in with_1x2[:15]:
            x = m["one_x_two"]["devig"]
            ou = m["over_under"].get("2.5", {})
            print(f"  {m['end_date'][:10] if m['end_date'] else '????':10} "
                  f"{(m['home'] or '?')[:22]:22} vs {(m['away'] or '?')[:22]:22} "
                  f"| 1={x['home']:.2f} X={x['draw']:.2f} 2={x['away']:.2f}"
                  + (f" | O2.5={ou['over']:.2f}" if ou.get('over') else ""))
        if not args.no_save:
            mpath = outdir / f"soccer_matches_{stamp}.json"
            mpath.write_text(json.dumps(matches, ensure_ascii=False, indent=2))
            print(f"  scritto: {mpath}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
