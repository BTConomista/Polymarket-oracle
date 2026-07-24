"""Scarica le fonti ORIGINALI (football-data.co.uk + Understat) con provenienza.

Perche' esiste (luglio 2026): fino alla Fase 89 il manuale di sopravvivenza
dava `football-data.co.uk` e `understat.com` come BLOCCATI dal proxy (403), e i
dati arrivavano come bundle caricati a mano (`files/*.json`). In questa sessione
entrambi gli host rispondono 200: e' un fatto nuovo, verificato, che permette
(a) di ri-verificare gli snapshot congelati contro la fonte-madre e
(b) di importare leghe nuove senza bundle manuali.

Cosa fa:
  - football-data:  GET {BASE}/mmz4281/{stagione}/{codice}.csv     (CSV grezzo)
  - Understat:      GET https://understat.com/getLeagueData/{lega}/{anno}
                    con header X-Requested-With: XMLHttpRequest (OBBLIGATORIO:
                    senza, il sito risponde 404; la vecchia pagina HTML non
                    contiene piu' `var datesData` -- i dati sono passati a AJAX)
                    -> JSON {teams, players, dates}, identico allo schema che
                    `src/data/understat.parse_season_xg` gia' sa leggere.

Ogni file scaricato viene registrato in un MANIFEST con URL, timestamp UTC,
dimensione e SHA256: la provenienza di ogni numero deve essere ricostruibile
(CLAUDE.md §1.5). Cache: non riscarica se il file esiste (usare --force).

Uso:
    python cantiere/scripts/fetch_sources.py                 # 5 leghe, 9 stagioni
    python cantiere/scripts/fetch_sources.py --leagues bundesliga ligue_1
    python cantiere/scripts/fetch_sources.py --force
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cantiere" / "data" / "fonti"
FD_DIR = OUT / "football_data"
UD_DIR = OUT / "understat"
MANIFEST = OUT / "manifest.json"

FD_URL = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
UD_URL = "https://understat.com/getLeagueData/{league}/{year}"

# Le 9 stagioni del progetto (stesse di src/data/sources.SEASONS).
SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]

# lega interna -> (codice football-data, nome Understat)
LEAGUES: dict[str, tuple[str, str]] = {
    "serie_a": ("I1", "Serie_A"),
    "premier_league": ("E0", "EPL"),
    "la_liga": ("SP1", "La_liga"),
    "bundesliga": ("D1", "Bundesliga"),
    "ligue_1": ("F1", "Ligue_1"),
}

THROTTLE_S = 1.5  # cortesia verso le fonti (nessuna delle due chiede di piu')


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get(url: str, *, xhr: bool = False, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; polymarket-oracle-research/1.0)",
        "Accept-Encoding": "gzip",
        **({"X-Requested-With": "XMLHttpRequest"} if xhr else {}),
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw


def _load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"files": {}}


def _save_manifest(man: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, indent=2, sort_keys=True))


def fetch(leagues: list[str], seasons: list[str], *, force: bool) -> dict:
    FD_DIR.mkdir(parents=True, exist_ok=True)
    UD_DIR.mkdir(parents=True, exist_ok=True)
    man = _load_manifest()
    errors: list[str] = []

    for key in leagues:
        code, ud_name = LEAGUES[key]
        for season in seasons:
            # --- football-data ---
            dest = FD_DIR / f"{key}_{season}.csv"
            if force or not dest.exists():
                url = FD_URL.format(season=season, code=code)
                try:
                    data = _get(url)
                    # Le stagioni recenti hanno il BOM UTF-8 in testa: va tolto
                    # solo per il CONTROLLO (il file si salva byte per byte).
                    if not data.lstrip().lstrip(b"\xef\xbb\xbf").startswith(b"Div"):
                        raise ValueError(f"contenuto inatteso ({data[:60]!r})")
                    dest.write_bytes(data)
                    man["files"][str(dest.relative_to(ROOT))] = {
                        "url": url, "fetched_utc": datetime.now(timezone.utc).isoformat(),
                        "bytes": len(data), "sha256": _sha256(data),
                    }
                    print(f"  [FD] {key} {season}: {len(data):>7} B")
                except (urllib.error.URLError, ValueError) as exc:
                    errors.append(f"FD {key} {season}: {exc}")
                    print(f"  [FD] {key} {season}: ERRORE {exc}")
                time.sleep(THROTTLE_S)

            # --- Understat ---
            year = 2000 + int(season[:2])
            dest = UD_DIR / f"{key}_{year}.json"
            if force or not dest.exists():
                url = UD_URL.format(league=ud_name, year=year)
                try:
                    data = _get(url, xhr=True)
                    obj = json.loads(data)  # valida che sia JSON vero
                    if not {"dates", "teams", "players"} <= set(obj):
                        raise ValueError(f"chiavi inattese: {sorted(obj)[:5]}")
                    dest.write_bytes(data)
                    man["files"][str(dest.relative_to(ROOT))] = {
                        "url": url, "fetched_utc": datetime.now(timezone.utc).isoformat(),
                        "bytes": len(data), "sha256": _sha256(data),
                        "n_dates": len(obj["dates"]), "n_teams": len(obj["teams"]),
                    }
                    print(f"  [UD] {key} {year}: {len(obj['dates'])} gare, "
                          f"{len(obj['teams'])} squadre")
                except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
                    errors.append(f"UD {key} {year}: {exc}")
                    print(f"  [UD] {key} {year}: ERRORE {exc}")
                time.sleep(THROTTLE_S)

    _save_manifest(man)
    if errors:
        print(f"\n{len(errors)} errori:")
        for e in errors:
            print(f"  - {e}")
    return man


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=list(LEAGUES))
    ap.add_argument("--seasons", nargs="*", default=SEASONS)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    unknown = set(args.leagues) - set(LEAGUES)
    if unknown:
        print(f"Leghe sconosciute: {sorted(unknown)}")
        return 2
    print(f"Scarico {len(args.leagues)} leghe x {len(args.seasons)} stagioni "
          f"-> {OUT.relative_to(ROOT)}")
    fetch(args.leagues, args.seasons, force=args.force)
    print(f"\nManifest: {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
