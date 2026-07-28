"""Coordinate degli stadi, da Wikipedia (Fase 122).

PERCHE'. Senza latitudine e longitudine il meteo non si può nemmeno chiedere,
e il meteo previsto è uno dei dati **irrecuperabili** del piano (una previsione
non si ricostruisce a posteriori: dopo esiste solo il consuntivo).

FONTE. `it.wikipedia.org`, `action=query&prop=coordinates`: le coordinate sono
un campo **strutturato** della voce, non testo da interpretare. Wikipedia
consente il bot e ha una API ufficiale (a differenza di Transfermarkt, Fase 119).

DOVE FINISCONO. In `_anagrafica/stadi.json`, un file solo. NON dentro le 96
`anagrafica.json`: il nome dello stadio sta lì, le coordinate qui, e chi le usa
fa il join. Così ri-scaricare le coordinate non significa riscrivere 96 file.

USO:
    python scripts/fetch_stadi_coordinate.py
    python scripts/fetch_stadi_coordinate.py --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_rose_wikipedia import _api  # noqa: E402  (stesso client: throttle e backoff)

STAGIONE = ROOT / "data" / "stagione_2026_2027"
DEST = STAGIONE / "_anagrafica" / "stadi.json"


def coordinate(titolo: str) -> dict | None:
    """Coordinate di una voce, se la voce le dichiara."""
    d = _api({"action": "query", "prop": "coordinates", "titles": titolo})
    for pagina in (d.get("query", {}).get("pages", {}) or {}).values():
        co = pagina.get("coordinates")
        if co:
            return {"lat": co[0]["lat"], "lon": co[0]["lon"], "voce": pagina["title"]}
    return None


def cerca_stadio(nome: str) -> dict | None:
    """Prima il titolo esatto, poi una ricerca. Mai un ripiego silenzioso."""
    diretto = coordinate(nome)
    if diretto:
        return diretto
    ris = _api({"action": "query", "list": "search",
                "srsearch": f"{nome} stadio", "srlimit": 3})
    for cand in ris.get("query", {}).get("search", []):
        co = coordinate(cand["title"])
        if co:
            return co
    return None


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    schede = sorted((STAGIONE / "club").glob("*/*/anagrafica.json"))
    if not schede:
        raise SystemExit("nessuna anagrafica: esegui prima "
                         "scripts/build_stagione_anagrafica.py")

    stadi: dict[str, dict] = {}
    mancanti: list[str] = []
    for f in schede:
        d = json.loads(f.read_text(encoding="utf-8"))
        nome = (d.get("stadio") or {}).get("nome")
        if not nome:
            mancanti.append(f"{d['nome_smarkets']} (nessuno stadio in anagrafica)")
            continue
        if nome in stadi:                       # stadi condivisi: una sola ricerca
            stadi[nome]["squadre"].append(d["nome_smarkets"])
            continue
        co = cerca_stadio(nome)
        if co is None:
            mancanti.append(f"{d['nome_smarkets']} — stadio '{nome}'")
            print(f"  ✗ {d['nome_smarkets']:28s} {nome}")
            continue
        stadi[nome] = {**co, "squadre": [d["nome_smarkets"]],
                       "capienza": (d.get("stadio") or {}).get("capienza")}
        print(f"  ✓ {d['nome_smarkets']:28s} {nome:32s} {co['lat']:.4f},{co['lon']:.4f}")

    print(f"\nstadi con coordinate: {len(stadi)} | senza: {len(mancanti)}")
    for m in mancanti:
        print(f"   ✗ {m}")

    if a.dry_run:
        print("\n--dry-run: nessun file scritto.")
        return
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "_fonte": "it.wikipedia.org (CC BY-SA), prop=coordinates",
        "_nota": ("le coordinate servono al meteo previsto. Gli stadi mancanti "
                  "sono elencati e vanno risolti a mano: NON stimare una "
                  "posizione, un meteo sulla città sbagliata è peggio di nessun "
                  "meteo."),
        "generato_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stadi_n": len(stadi),
        "mancanti": mancanti,
        "stadi": stadi,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scritto {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
