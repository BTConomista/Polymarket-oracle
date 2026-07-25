"""Archivio storico dei mercati OUTRIGHT di stagione — Fase 97.

PERCHE' ESISTE. Il limite piu' duro del simulatore di stagione (Fase 89) e' che
NON esistono quote outright storiche: si puo' dimostrare «battiamo le baseline»,
non «battiamo il mercato». Quel limite non si puo' rimuovere all'indietro, ma si
puo' smettere di subirlo in avanti: **congelando i prezzi ogni volta che si
guarda**, fra qualche stagione lo storico ce l'avremo.

Questo script fa esattamente quello e nient'altro: scarica, filtra, congela.
L'output e' VERSIONATO (`data/outright_snapshots/`, NON in .gitignore, a
differenza del dump grezzo di `fetch_polymarket_open.py`): e' il punto di
questo strumento — uno snapshot che vive solo in un container effimero non
costruisce nessuno storico.

DUE FONTI, COMPLEMENTARI (nessuna domina l'altra — misurato il 25/07/2026):

  POLYMARKET (`fetch_polymarket_open.py`)     campione in tutte e 5 le leghe;
    qualificazioni europee (ma erano code della stagione conclusa);
    NIENTE retrocessione. Sulla Serie A e' la fonte buona.
  SMARKETS (`fetch_smarkets_outrights.py`)    campione in tutte e 5;
    RETROCESSIONE e piazzamenti Top 2/3/4/5/6 e top-half (che Polymarket non
    quota affatto). Sulla Premier e' molto piu' liquido (spread 0.11pp contro
    un overround del 5.8%); sulla Serie A e' molto meno liquido.

Sono entrambe BORSE, non bookmaker: i prezzi sono ordini di utenti e la somma
dei mercati esclusivi esce ~100-104%, non 108-115%. Altre fonti (OddsPortal,
BetExplorer, The Odds API, DraftKings, bwin, Betfair) sono state testate e
scartate: il perche' di ognuna e' in `fetch_smarkets_outrights.py`.

USO
  python scripts/archive_outrights.py                 # scarica e archivia oggi
  python scripts/archive_outrights.py --from-dump F   # riusa un dump Polymarket
  python scripts/archive_outrights.py --only smarkets # una fonte sola
  python scripts/archive_outrights.py --show          # mostra l'archivio esistente

FORMATO. Un file per data in `data/outright_snapshots/YYYY-MM-DD.json` (dati
completi) piu' `history.csv` in formato lungo (una riga per data x FONTE x lega
x mercato x squadra), che e' quello da leggere per le analisi.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_polymarket_open import (            # noqa: E402
    event_tags, fetch_open_events, market_outcomes,
)
from scripts.fetch_smarkets_outrights import fetch_outrights as fetch_smarkets  # noqa: E402

DEST = Path("data/outright_snapshots")

# tag Polymarket -> chiave interna. Attenzione: Polymarket usa piu' etichette
# per la stessa lega ("EPL" e "Premier League") e a volte minuscole
# ("bundesliga"): il confronto e' case-insensitive.
LEAGUE_TAGS = {
    "serie a": "serie_a",
    "epl": "premier_league", "premier league": "premier_league",
    "la liga": "la_liga", "laliga": "la_liga",
    "bundesliga": "bundesliga",
    "ligue 1": "ligue_1",
}

# tipo di mercato, riconosciuto dal titolo (in ordine: il primo che matcha vince)
# ATTENZIONE ALL'ORDINE: "Ligue 1: Team to qualify for UEFA Champions League"
# contiene la parola "champions", quindi le qualificazioni vanno riconosciute
# PRIMA del mercato campione — altrimenti finiscono li' dentro e la Ligue 1
# esce con 36 esiti invece di 18.
MARKET_TYPES = [
    ("qual_ucl", ("qualify for uefa champions league",)),
    ("qual_uel", ("qualify for uefa europa league",)),
    ("qual_uecl", ("qualify for uefa conference league",)),
    ("relegation", ("relegat", "finish bottom")),
    ("top_scorer", ("top scorer", "golden boot")),
    ("champion", ("champion",)),
]

# Mercati a vincitore UNICO: gli esiti sono mutuamente esclusivi e la somma dei
# prezzi e' l'overround, quindi si puo' devigare rinormalizzando a 1. Gli altri
# (qualificazione: qualificano in 4-5) sono binari INDIPENDENTI e la somma vale
# legittimamente 2-4: rinormalizzarli sarebbe un errore concettuale.
EXCLUSIVE = {"champion", "top_scorer"}

# segnaposto senza mercato vero: vanno esclusi PRIMA di rinormalizzare, altrimenti
# la somma esce assurda (osservato 3.07 invece di ~1.07)
PLACEHOLDERS = {"team a", "team b", "team c", "team d", "other"}


def _league_of(tags) -> str | None:
    low = {t.lower() for t in tags}
    for tag, key in LEAGUE_TAGS.items():
        if tag in low:
            return key
    return None


def _type_of(title: str) -> str | None:
    tl = title.lower()
    for key, kws in MARKET_TYPES:
        if any(k in tl for k in kws):
            return key
    return None


def _is_placeholder(name: str, bid, ask, volume) -> bool:
    """Segnaposto = nome generico E nessun mercato vero dietro."""
    if (name or "").strip().lower() not in PLACEHOLDERS:
        return False
    try:
        dead = (float(bid or 0) <= 0.001 and float(ask or 1) >= 0.999)
    except (TypeError, ValueError):
        dead = True
    return dead or not float(volume or 0)


def extract(events) -> list[dict]:
    """Una riga per (lega, mercato, squadra) con prezzo grezzo e devigato."""
    rows = []
    for e in events:
        title = e.get("title") or ""
        if " vs." in title:
            continue                                   # e' una partita, non un outright
        league = _league_of(event_tags(e))
        mtype = _type_of(title)
        if not league or not mtype:
            continue
        entries = []
        for m in (e.get("markets") or []):
            name = m.get("groupItemTitle") or m.get("question") or ""
            o = market_outcomes(m)
            p = o.get("Yes")
            if p is None:
                continue
            if _is_placeholder(name, m.get("bestBid"), m.get("bestAsk"), m.get("volumeNum")):
                continue
            entries.append(dict(team=name.strip(), price=float(p),
                                best_bid=m.get("bestBid"), best_ask=m.get("bestAsk"),
                                volume=m.get("volumeNum"), liquidity=m.get("liquidityNum")))
        if not entries:
            continue
        total = sum(x["price"] for x in entries)
        exclusive = mtype in EXCLUSIVE
        # quota di esiti gia' DECISI (0 o 1): se e' alta il mercato non e' una
        # previsione ma la coda di una stagione conclusa. Verificato il
        # 25/07/2026: i "qualify for" si riferiscono alla stagione APPENA
        # FINITA (19 esiti su 20 gia' a zero) e non al 2026-27.
        settled = sum(1 for x in entries if x["price"] <= 0.01 or x["price"] >= 0.99)
        for x in entries:
            # devig proporzionale SOLO dove gli esiti sono esclusivi
            x["prob"] = (x["price"] / total if total else None) if exclusive else x["price"]
            x.update(source="polymarket", league=league, market=mtype,
                     event_title=title, event_slug=e.get("slug"),
                     overround=round(total, 4) if exclusive else None,
                     price_sum=round(total, 4), exclusive=exclusive,
                     settled_share=round(settled / len(entries), 3),
                     n_entries=len(entries),
                     event_liquidity=float(e.get("liquidity") or 0),
                     event_volume=float(e.get("volume") or 0))
        rows.extend(entries)
    return rows


def save(rows, when: str) -> tuple[Path, Path]:
    DEST.mkdir(parents=True, exist_ok=True)
    snap = DEST / f"{when}.json"
    snap.write_text(json.dumps(
        dict(snapshot_date=when, source="polymarket-gamma", n_rows=len(rows), rows=rows),
        indent=2, ensure_ascii=False))

    # history.csv: formato lungo, append-only ma idempotente sulla data.
    # Le colonne sono l'UNIONE dei campi delle due fonti: quelle che una fonte
    # non ha restano vuote (Polymarket non ha spread/libro, Smarkets non ha
    # volume/liquidita').
    import csv
    hist = DEST / "history.csv"
    cols = ["snapshot_date", "source", "league", "market", "team", "price", "prob",
            "exclusive", "overround", "price_sum", "settled_share",
            "n_entries", "n_priced", "best_bid", "best_ask", "spread",
            "price_side", "book", "volume", "liquidity",
            "event_liquidity", "event_volume", "event_title", "event_slug",
            "market_name", "market_id"]
    old = []
    if hist.exists():
        with open(hist) as f:
            old = [r for r in csv.DictReader(f) if r.get("snapshot_date") != when]
    with open(hist, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in old:
            w.writerow({c: r.get(c, "") for c in cols})
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols} | {"snapshot_date": when})
    return snap, hist


def show():
    hist = DEST / "history.csv"
    if not hist.exists():
        print("Archivio vuoto: esegui prima senza --show.")
        return
    import csv
    import collections
    with open(hist) as f:
        rows = list(csv.DictReader(f))
    by_date = collections.Counter(r["snapshot_date"] for r in rows)
    print(f"### ARCHIVIO OUTRIGHT — {len(rows)} righe, {len(by_date)} istantanee")
    for d, n in sorted(by_date.items()):
        sub = [r for r in rows if r["snapshot_date"] == d]
        mk = {(r["source"], r["league"], r["market"]) for r in sub}
        src = collections.Counter(r["source"] for r in sub)
        print(f"  {d}: {n:4d} righe, {len(mk)} mercati  ({dict(src)})")
    last = max(by_date)
    print(f"\n  ultima istantanea ({last}), favorito per fonte x mercato:")
    seen = {}
    for r in rows:
        # il prezzo di riferimento e' il mid; su un libro con sole offerte
        # (Smarkets, mercati Top-N) resta solo l'ask: si mostra quello
        v = r.get("prob") or r.get("price") or r.get("best_ask") or ""
        if r["snapshot_date"] != last or v == "":
            continue
        k = (r["league"], r["market"], r["source"])
        if k not in seen or float(v) > seen[k][1]:
            seen[k] = (r, float(v))
    for (lg, mk, src), (r, v) in sorted(seen.items()):
        note = "" if r.get("book") in ("two_sided", "") else f" [{r['book']}]"
        print(f"    {lg:15} {mk:11} {src:11} {r['team'][:22]:22} {v*100:5.1f}%"
              f"  ({r['n_entries']} esiti){note}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-dump", help="riusa un dump JSON gia' scaricato (Polymarket)")
    ap.add_argument("--show", action="store_true", help="mostra l'archivio e esci")
    ap.add_argument("--date", help="data dello snapshot (default: oggi UTC)")
    ap.add_argument("--only", choices=["polymarket", "smarkets"],
                    help="archivia una fonte sola (default: entrambe)")
    args = ap.parse_args(argv)

    if args.show:
        show()
        return 0

    when = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows, n_events = [], 0
    if args.only != "smarkets":
        if args.from_dump:
            events = json.loads(Path(args.from_dump).read_text())
        else:
            print("Scarico i mercati aperti da Polymarket...", file=sys.stderr)
            events = fetch_open_events(quiet=True)
        n_events = len(events)
        rows += extract(events)
    if args.only != "polymarket":
        print("Scarico gli outright da Smarkets...", file=sys.stderr)
        rows += fetch_smarkets(quiet=True)
    snap, hist = save(rows, when)

    print(f"### ISTANTANEA {when} — {len(rows)} righe"
          + (f" ({n_events} eventi Polymarket)" if n_events else ""))
    import collections
    per = collections.Counter((r["source"], r["league"], r["market"]) for r in rows)
    live, stale = [], []
    for (src, lg, mk), n in sorted(per.items()):
        sub = [r for r in rows if (r["source"], r["league"], r["market"]) == (src, lg, mk)]
        priced = [r for r in sub if r.get("prob") is not None]
        # senza mid si mostra l'ask: il favorito e' quello che costa di piu'
        best = (max(priced, key=lambda r: r["prob"]) if priced else
                max(sub, key=lambda r: r.get("best_ask") or -1))
        val = best.get("prob") if priced else best.get("best_ask")
        if val is None:
            continue
        if best.get("book") == "partial":
            ov = "LIBRO PARZIALE (solo offerte: e' un tetto, non un prezzo)"
        elif best["exclusive"]:
            ov = f"overround {best['overround']:.3f}"
        else:
            ov = f"somma {best['price_sum']:.2f} (non esclusivo)"
        line = (f"  {src:11} {lg:15} {mk:11} {n:3d} esiti   favorito "
                f"{best['team'][:20]:20} {val*100:5.1f}%   {ov}")
        (stale if (best.get("settled_share") or 0) >= 0.9 else live).append(line)
    print("  -- previsioni VERE (mercato ancora aperto sull'esito) --")
    for l in live:
        print(l)
    if stale:
        print("  -- code di stagioni CONCLUSE (>=90% degli esiti gia' a 0 o 1):")
        print("     archiviate per completezza, NON usarle come previsioni --")
        for l in stale:
            print(l)
    for src in sorted({r["source"] for r in rows}):
        miss = {"champion", "relegation"} - {m for s, _, m in per if s == src}
        if miss:
            print(f"\n  {src}: NON quota {sorted(miss)} in nessuna lega")
    print(f"\nScritto {snap}\nAggiornato {hist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
