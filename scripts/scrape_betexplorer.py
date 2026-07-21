#!/usr/bin/env python3
"""
Fase B — Scraper BetExplorer: quote Over/Under 2.5 di APERTURA e CHIUSURA.

Per una lega-stagione:
  1. scarica la pagina risultati (1 richiesta) ed estrae le ~380 partite
     (data, squadre, punteggio finale, match_id);
  2. per ogni partita chiama l'endpoint AJAX delle quote O/U
     (GET /match-odds/{id}/1/ou/ con header X-Requested-With), throttle 2-3 s;
  3. filtra la linea ESATTAMENTE 2.5, estrae per bookmaker quota di apertura
     (attributi data-opening-*) e di chiusura (data-odd) di Over e Under;
  4. sceglie il book per riga: Pinnacle -> media multi-book (>=3 book completi)
     -> Bet365 -> singolo book disponibile, dichiarando la fonte riga per riga;
  5. scrive files/ou25_{slug}.csv + checkpoint JSONL riprendibile.

Uso:
  python scrape_betexplorer.py --league serie-a-2017-2018
  python scrape_betexplorer.py --league serie-a-2017-2018 --probe-limit 3 --dump-first 3

Il probe (3 partite + dump HTML grezzo in debug/) serve a validare il parsing
PRIMA del run completo: se BetExplorer ha cambiato markup, si sistema
parse_ou_html() guardando i dump.

Etica: throttle randomizzato 2-3 s, User-Agent dichiarato, retry con backoff,
una sola stagione per run (come da piano).
"""

import argparse
import csv
import json
import random
import re
import statistics
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.betexplorer.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 (research-scraper; contact in repo)")

# slug betexplorer -> (country, nome lega, stagione)
LEAGUES = {
    "serie-a-2017-2018":        ("italy",   "Serie A",        "2017-18"),
    "serie-a-2018-2019":        ("italy",   "Serie A",        "2018-19"),
    "premier-league-2017-2018": ("england", "Premier League", "2017-18"),
    "premier-league-2018-2019": ("england", "Premier League", "2018-19"),
    "laliga-2017-2018":         ("spain",   "La Liga",        "2017-18"),
    "laliga-2018-2019":         ("spain",   "La Liga",        "2018-19"),
}

TARGET_LINE = "2.5"
MATCH_HREF = re.compile(r"^/football/[^/]+/[^/]+/[^/]+/([A-Za-z0-9]{6,10})/(?:#.*)?$")
SCORE_RE = re.compile(r"^(\d+):(\d+)")
NUM_RE = re.compile(r"^\d+(?:\.\d+)?$")


def log(msg):
    print(msg, flush=True)


def polite_sleep(lo=2.0, hi=3.0):
    time.sleep(random.uniform(lo, hi))


def get(session, url, referer=None, ajax=False, tries=4):
    headers = {"User-Agent": UA, "Accept-Language": "en-GB,en;q=0.9"}
    if referer:
        headers["Referer"] = referer
    if ajax:
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
    for attempt in range(1, tries + 1):
        try:
            r = session.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code in (403, 429):
                wait = 30 * attempt
                log(f"  HTTP {r.status_code} su {url} — backoff {wait}s (tentativo {attempt}/{tries})")
                time.sleep(wait)
            elif r.status_code == 404:
                log(f"  HTTP 404 su {url}")
                return None
            else:
                time.sleep(8 * attempt)
        except requests.RequestException as e:
            log(f"  errore rete {e} — retry (tentativo {attempt}/{tries})")
            time.sleep(8 * attempt)
    return None


# ---------------------------------------------------------------- results page

def parse_results_page(html):
    """Estrae le partite dalla pagina risultati (tutta la stagione e' server-side)."""
    soup = BeautifulSoup(html, "html.parser")
    matches, seen = [], set()
    for tr in soup.find_all("tr"):
        team_a, score_a = None, None
        for a in tr.find_all("a", href=True):
            m = MATCH_HREF.match(a["href"].split("#")[0] if "#" in a["href"] else a["href"])
            if not m:
                continue
            text = a.get_text(" ", strip=True)
            if " - " in text:
                team_a = a
            elif SCORE_RE.match(text) or text.upper() in ("POSTP.", "CAN.", "AWA."):
                score_a = a
        if team_a is None:
            continue
        href = team_a["href"].split("#")[0]
        mid = MATCH_HREF.match(href).group(1)
        if mid in seen:
            continue
        seen.add(mid)
        home, _, away = team_a.get_text(" ", strip=True).partition(" - ")
        score_txt = score_a.get_text(strip=True) if score_a else ""
        sm = SCORE_RE.match(score_txt)
        date_td = tr.find("td", class_=re.compile(r"h-text-right"))
        matches.append({
            "match_id": mid,
            "href": href,
            "home": home.strip(),
            "away": away.strip(),
            "home_goals": sm.group(1) if sm else "",
            "away_goals": sm.group(2) if sm else "",
            "score_raw": score_txt,
            "date": date_td.get_text(strip=True) if date_td else "",
        })
    return matches


# ------------------------------------------------------------------- OU parsing

def _cell_open_close(td):
    """Estrae (apertura, chiusura) da una cella quota, con fallback multipli."""
    close_v, open_v = None, None
    candidates = [td] + td.find_all(True)
    for el in candidates:
        attrs = getattr(el, "attrs", {}) or {}
        if close_v is None:
            v = attrs.get("data-odd")
            if v and NUM_RE.match(str(v).strip()):
                close_v = str(v).strip()
        if open_v is None:
            for k, v in attrs.items():
                if "opening" in k.lower() and "odd" in k.lower() and v:
                    v = str(v).strip()
                    if NUM_RE.match(v):
                        open_v = v
                        break
    if close_v is None:
        # ultimo fallback: testo visibile della cella
        t = td.get_text(strip=True)
        if NUM_RE.match(t):
            close_v = t
    return open_v, close_v


def parse_ou_html(html):
    """
    Ritorna righe {bookmaker, line, over_open, over_close, under_open, under_close}
    dal frammento HTML restituito dall'endpoint AJAX /match-odds/{id}/1/ou/.
    Struttura attesa: tabella con righe bookmaker; colonna linea (testo tipo '2.5'
    senza data-odd) + due celle quota (Over, Under) con data-odd / data-opening-odd.
    """
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        a = tr.find("a")
        book = a.get_text(" ", strip=True) if a else ""
        if not book:
            th = tr.find("th")
            book = th.get_text(" ", strip=True) if th else ""
        if not book:
            continue

        odds_cells, line = [], None
        for td in tds:
            has_odd_attr = td.has_attr("data-odd") or td.find(attrs={"data-odd": True}) is not None
            txt = td.get_text(strip=True)
            if has_odd_attr:
                odds_cells.append(td)
            elif line is None and NUM_RE.match(txt) and float(txt) <= 15:
                line = txt
        if not odds_cells:
            # markup senza data-odd: prova ultime due celle numeriche come Over/Under
            numeric = [td for td in tds if NUM_RE.match(td.get_text(strip=True))]
            if line is None and len(numeric) >= 3:
                line = numeric[0].get_text(strip=True)
                odds_cells = numeric[1:3]
            elif len(numeric) >= 2:
                odds_cells = numeric[-2:]
        if len(odds_cells) < 2 or line is None:
            continue

        o_open, o_close = _cell_open_close(odds_cells[0])
        u_open, u_close = _cell_open_close(odds_cells[1])
        out.append({
            "bookmaker": book, "line": line,
            "over_open": o_open, "over_close": o_close,
            "under_open": u_open, "under_close": u_close,
        })
    return out


# --------------------------------------------------------------- book selection

def _complete(r):
    return all(r.get(k) for k in ("over_open", "over_close", "under_open", "under_close"))


def select_row(book_rows):
    """Applica la preferenza: Pinnacle -> media multi-book -> Bet365 -> singolo."""
    l25 = [r for r in book_rows if r["line"] == TARGET_LINE]
    if not l25:
        return None
    full = [r for r in l25 if _complete(r)]
    pool = full if full else [r for r in l25 if r.get("over_close") and r.get("under_close")]
    if not pool:
        return None

    def pick(rows, source):
        r = rows[0]
        return {
            "over_open": r["over_open"] or "", "over_close": r["over_close"] or "",
            "under_open": r["under_open"] or "", "under_close": r["under_close"] or "",
            "book_source": source, "n_books_line25": len(l25),
        }

    pinn = [r for r in pool if "pinnacle" in r["bookmaker"].lower()]
    if pinn:
        return pick(pinn, "pinnacle")
    if len(full) >= 3:
        def avg(key):
            return f"{statistics.mean(float(r[key]) for r in full):.3f}"
        return {
            "over_open": avg("over_open"), "over_close": avg("over_close"),
            "under_open": avg("under_open"), "under_close": avg("under_close"),
            "book_source": f"avg{len(full)}", "n_books_line25": len(l25),
        }
    b365 = [r for r in pool if "bet365" in r["bookmaker"].lower().replace(" ", "")]
    if b365:
        return pick(b365, "bet365")
    return pick(pool, pool[0]["bookmaker"].lower().replace(" ", "_"))


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True, choices=sorted(LEAGUES))
    ap.add_argument("--probe-limit", type=int, default=0,
                    help="scrappa solo N partite (validazione parsing)")
    ap.add_argument("--dump-first", type=int, default=0,
                    help="salva in debug/ l'HTML AJAX grezzo delle prime N partite")
    ap.add_argument("--throttle-min", type=float, default=2.0)
    ap.add_argument("--throttle-max", type=float, default=3.0)
    args = ap.parse_args()

    country, league_name, season = LEAGUES[args.league]
    files_dir = Path("files"); files_dir.mkdir(exist_ok=True)
    debug_dir = Path("debug"); debug_dir.mkdir(exist_ok=True)
    ckpt_path = files_dir / f"ckpt_{args.league}.jsonl"
    csv_path = files_dir / f"ou25_{args.league}.csv"

    done = {}
    if ckpt_path.exists():
        for ln in ckpt_path.read_text().splitlines():
            try:
                rec = json.loads(ln)
                done[rec["match_id"]] = rec
            except json.JSONDecodeError:
                pass
        log(f"Checkpoint: {len(done)} partite gia' scrappate, riprendo.")

    session = requests.Session()
    results_url = f"{BASE}/football/{country}/{args.league}/results/"
    log(f"Scarico risultati: {results_url}")
    r = get(session, results_url)
    if r is None:
        log("ERRORE: pagina risultati non raggiungibile."); sys.exit(1)
    matches = parse_results_page(r.text)
    log(f"Partite trovate: {len(matches)} (attese ~380)")
    if len(matches) < 300:
        (debug_dir / f"results_{args.league}.html").write_text(r.text)
        log("ATTENZIONE: meno di 300 partite — HTML salvato in debug/ per ispezione.")
        if not matches:
            sys.exit(1)

    todo = [m for m in matches if m["match_id"] not in done]
    if args.probe_limit:
        todo = todo[: args.probe_limit]
        log(f"PROBE MODE: solo {len(todo)} partite.")

    n_ok = n_noline = n_fail = 0
    with ckpt_path.open("a") as ck:
        for i, m in enumerate(todo, 1):
            polite_sleep(args.throttle_min, args.throttle_max)
            ajax_url = f"{BASE}/match-odds/{m['match_id']}/1/ou/"
            resp = get(session, ajax_url, referer=BASE + m["href"], ajax=True)
            rec = dict(m); rec.update({"league": league_name, "season": season})
            if resp is None:
                rec["status"] = "http_fail"; n_fail += 1
            else:
                try:
                    payload = resp.json()
                    ou_html = payload.get("odds") or payload.get("html") or ""
                except ValueError:
                    ou_html = resp.text
                if i <= args.dump_first:
                    (debug_dir / f"ou_{m['match_id']}.html").write_text(ou_html)
                book_rows = parse_ou_html(ou_html)
                sel = select_row(book_rows)
                if sel:
                    rec.update(sel); rec["status"] = "ok"; n_ok += 1
                else:
                    rec["status"] = "no_line_25"; n_noline += 1
                    rec["lines_seen"] = sorted({br["line"] for br in book_rows})
            ck.write(json.dumps(rec) + "\n"); ck.flush()
            done[m["match_id"]] = rec
            if i % 25 == 0 or i == len(todo):
                log(f"  [{i}/{len(todo)}] ok={n_ok} no_line={n_noline} fail={n_fail}")
            if args.probe_limit:
                log(json.dumps(rec, indent=2, ensure_ascii=False))

    # CSV finale dall'insieme checkpoint (ordina per data poi squadre)
    cols = ["league", "season", "date", "home", "away", "home_goals", "away_goals",
            "over_open", "under_open", "over_close", "under_close",
            "book_source", "n_books_line25", "match_id", "status"]
    def sort_key(r):
        d = r.get("date", "")
        p = d.split(".")
        return (p[2], p[1], p[0]) if len(p) == 3 else ("", "", d)
    rows = sorted(done.values(), key=sort_key)
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for rec in rows:
            w.writerow(rec)
    ok_total = sum(1 for r in rows if r.get("status") == "ok")
    log(f"\nCSV scritto: {csv_path} — {len(rows)} righe, {ok_total} con quote O/U 2.5 "
        f"({100.0 * ok_total / max(len(rows), 1):.1f}% copertura)")
    log("Ora esegui: python check_acceptance.py " + str(csv_path))


if __name__ == "__main__":
    main()
