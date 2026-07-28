"""Rose 2026-27 da Wikipedia — la fonte che dice chi c'è DAVVERO (Fase 121).

PERCHE' ESISTE. L'anagrafica della Fase 120 prende le rose dal dataset CC0,
che è una **fotografia del 27/02/2026**: non sa nulla del mercato estivo, e per
le neopromosse non ha niente (10 record stantii, 4 squadre assenti). Serve una
fonte che stia al passo con la stagione che comincia.

PERCHE' WIKIPEDIA, e non Transfermarkt. Il `robots.txt` di Transfermarkt vieta
`ClaudeBot`/`anthropic-ai` (Fase 119). Wikipedia invece **consente**, ha una API
ufficiale, ed è aggiornata da persone in tempo quasi reale: la voce dell'Inter
al 28/07/2026 dichiarava «Rosa e numerazione aggiornate al **26 luglio 2026**»
citando il sito ufficiale del club. Per una rosa a inizio stagione è
esattamente ciò che serve.

PERCHE' LA WIKIPEDIA ITALIANA PER TUTTI, anche per i club stranieri. Ogni
lingua usa un template diverso — `{{Calciatore in rosa}}` (it),
`{{Feff joueur}}` (fr), tabelle con `{{birth date and age}}` (en), altro ancora
in de/es — e cinque parser sarebbero cinque punti di rottura silenziosa.
Verificato che it.wikipedia copre anche i club esteri con lo **stesso**
template (Real Madrid 29 giocatori, Manchester City 32): **un solo parser**.

COSA NON FA. Non dice chi è infortunato o squalificato **oggi**: quello è stato
quotidiano e vive nella raccolta giornaliera, non nell'anagrafica. Qui c'è chi
è tesserato, con numero, ruolo e nazionalità.

USO:
    python scripts/fetch_rose_wikipedia.py                 # tutte e 96
    python scripts/fetch_rose_wikipedia.py --lega serie_a  # una lega
    python scripts/fetch_rose_wikipedia.py --dry-run       # solo la copertura
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEST = ROOT / "data" / "stagione_2026_2027" / "club"
API = "https://it.wikipedia.org/w/api.php?"
STAGIONE = "2026-2027"

# Wikipedia limita le richieste: il 429 è arrivato davvero durante la messa a
# punto (Fase 121). Un secondo fra una chiamata e l'altra, e backoff sul 429.
THROTTLE = 1.0

# La convenzione della Wikimedia chiede uno User-Agent che identifichi il bot e
# dia un contatto: <https://meta.wikimedia.org/wiki/User-Agent_policy>.
UA = {"User-Agent": "Polymarket-oracle/1.0 (ricerca calcistica; "
                    "https://github.com/BTConomista/Polymarket-oracle)"}

# Il template della rosa nella Wikipedia italiana.
#   {{Calciatore in rosa|n=10|nazione=ARG|ruolo=A|nome=[[Lautaro Martínez]]|altro=c}}
GIOCATORE = re.compile(
    r"\{\{Calciatore in rosa"
    r"(?=[^}]*?\|\s*n\s*=\s*(?P<n>[^|}]*))?"
    r"(?=[^}]*?\|\s*nazione\s*=\s*(?P<nazione>[^|}]*))?"
    r"(?=[^}]*?\|\s*ruolo\s*=\s*(?P<ruolo>[^|}]*))?"
    r"[^}]*?\|\s*nome\s*=\s*(?P<nome>\[\[[^\]]*\]\]|[^|}]*)")

# «Rosa e numerazione aggiornate al 26 luglio 2026» — la data che la voce
# dichiara. Vale più di quella del nostro scarico: dice quanto è fresco il dato.
AGGIORNATA = re.compile(r"[Rr]os[ae][^.\n]{0,80}aggiornat[ae]\s+al\s+([^.<\n]{4,40})")


def _pulisci_data(grezza: str | None) -> str | None:
    """La data dichiarata dalla voce, senza il contorno del wikitesto.

    Wikipedia la scrive in modi diversi -- ``26 luglio 2026''``, ``13 luglio
    2026))``, ``{{data|18|07|2026}}`` -- e lasciarla grezza significherebbe
    scrivere apostrofi e parentesi dentro un campo che dice una data.
    """
    if not grezza:
        return None
    s = grezza.strip()
    m = re.match(r"\{\{data\|(\d{1,2})\|(\d{1,2})\|(\d{4})\}\}", s)
    if m:
        return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}"
    return re.sub(r"[\'\"\)\(\]\[}{|]+$", "", s).strip() or None

# Pagine da NON scambiare per una stagione di club: la ricerca, quando non
# trova la voce giusta, restituisce volentieri la competizione.
NON_CLUB = ("UEFA ", "Serie A ", "Serie B ", "Premier League ", "Fußball-",
            "Ligue 1 ", "Coppa ", "Supercoppa", "Campionato ", "Liga ")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def _api(params: dict, tentativi: int = 4) -> dict:
    url = API + urllib.parse.urlencode({**params, "format": "json"})
    for k in range(tentativi):
        time.sleep(THROTTLE)
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == tentativi - 1:
                raise
            time.sleep(5 * 2 ** k)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            # Un «connection reset by peer» a meta' di 96 squadre buttava via
            # tutto il giro (successo davvero, Fase 121). Un errore di rete
            # transitorio non e' un dato mancante: si riprova.
            if k == tentativi - 1:
                raise
            time.sleep(2 ** k)
    return {}


def _titolo_plausibile(titolo: str, semi: list[str]) -> bool:
    """La pagina trovata è la stagione di QUESTO club?

    Senza questo controllo la ricerca restituisce la competizione: cercando
    «Paris Saint-Germain 2026-2027» il primo risultato era *UEFA Champions
    League 2026-2027*, che contiene la stagione giusta e nessuna rosa. Si
    pretende quindi che il titolo (a) contenga la stagione, (b) non sia una
    competizione nota, (c) condivida una parola sostanziale col nome del club.
    """
    if STAGIONE not in titolo or titolo.startswith(NON_CLUB):
        return False
    parole_titolo = set(_norm(titolo).split())
    for seme in semi:
        for parola in _norm(seme).split():
            if len(parola) > 3 and parola in parole_titolo:
                return True
    return False


def trova_pagina(semi: list[str]) -> tuple[str, str] | None:
    """Cerca la voce della stagione provando più nomi per lo stesso club."""
    visti: set[str] = set()
    for seme in semi:
        if not seme:
            continue
        ris = _api({"action": "query", "list": "search",
                    "srsearch": f"{seme} {STAGIONE}", "srlimit": 6})
        for cand in ris.get("query", {}).get("search", []):
            titolo = cand["title"]
            if titolo in visti or not _titolo_plausibile(titolo, semi):
                continue
            visti.add(titolo)
            testo = _api({"action": "parse", "page": titolo,
                          "prop": "wikitext"}).get("parse", {}) \
                                              .get("wikitext", {}).get("*", "")
            if "Calciatore in rosa" in testo:
                return titolo, testo
    return None


def leggi_rosa(wikitext: str) -> list[dict]:
    rosa = []
    for m in GIOCATORE.finditer(wikitext):
        nome = re.sub(r"\[\[|\]\]", "", (m.group("nome") or "")).strip()
        if "|" in nome:                       # [[Luis Henrique (calciatore)|Luis Henrique]]
            nome = nome.split("|")[-1].strip()
        if not nome:
            continue
        numero = (m.group("n") or "").strip()
        rosa.append({
            "nome": nome,
            "numero": int(numero) if numero.isdigit() else None,
            "ruolo": (m.group("ruolo") or "").strip() or None,
            "nazione": (m.group("nazione") or "").strip() or None,
        })
    return rosa


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lega", help="solo questa lega")
    ap.add_argument("--dry-run", action="store_true", help="non scrive i file")
    a = ap.parse_args(argv)

    schede = sorted(DEST.glob("*/*/anagrafica.json"))
    if not schede:
        raise SystemExit("nessuna anagrafica: esegui prima "
                         "scripts/build_stagione_anagrafica.py")

    oggi = dt.datetime.now(dt.timezone.utc)
    trovate, mancanti = 0, []
    for scheda in schede:
        d = json.loads(scheda.read_text(encoding="utf-8"))
        if a.lega and d["lega"] != a.lega:
            continue
        semi = [d.get("nome_dataset"), d["nome_smarkets"]]
        esito = trova_pagina([s for s in semi if s])
        if esito is None:
            mancanti.append((d["lega"], d["nome_smarkets"]))
            print(f"  ✗ {d['nome_smarkets']:30s} nessuna voce con rosa")
            continue

        titolo, testo = esito
        rosa = leggi_rosa(testo)
        if not rosa:
            mancanti.append((d["lega"], d["nome_smarkets"]))
            print(f"  ✗ {d['nome_smarkets']:30s} voce trovata ma rosa vuota: {titolo}")
            continue

        agg = AGGIORNATA.search(testo)
        doc = {
            "_fonte": "it.wikipedia.org (licenza CC BY-SA), API ufficiale",
            "_nota": ("Chi è TESSERATO, non chi è disponibile: infortuni e "
                      "squalifiche sono stato quotidiano e vivono in "
                      "giornaliero/, non qui."),
            "squadra": d["nome_smarkets"],
            "lega": d["lega"],
            "voce": titolo,
            "url": f"https://it.wikipedia.org/wiki/{urllib.parse.quote(titolo.replace(' ', '_'))}",
            # La data che DICHIARA la voce: è quella che conta per la freschezza,
            # non l'istante in cui abbiamo scaricato.
            "aggiornata_al_dichiarato": _pulisci_data(agg.group(1) if agg else None),
            "scaricato_utc": oggi.isoformat(),
            "rosa_n": len(rosa),
            # ⚠️ IL NUMERO DI MAGLIA E' IL DISCRIMINE, ed e' un dato non una
            # stima: le voci elencano nella stessa sezione i tesserati della
            # prima squadra (con numero) e i giovani aggregati (``n=`` vuoto e
            # senza voce propria). Al Napoli sono 26 + 21. Contarli insieme era
            # il difetto che rendeva ``rosa_n`` illeggibile (Fase 120).
            "rosa_prima_squadra_n": sum(1 for g in rosa if g["numero"] is not None),
            "rosa": rosa,
        }
        if not a.dry_run:
            (scheda.parent / "rosa_wikipedia.json").write_text(
                json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        trovate += 1
        print(f"  ✓ {d['nome_smarkets']:30s} {len(rosa):2d} giocatori  "
              f"({_pulisci_data(agg.group(1) if agg else None) or 'data non dichiarata'})")

    tot = trovate + len(mancanti)
    print(f"\nrose trovate: {trovate}/{tot}")
    if mancanti:
        print("mancanti (da risolvere a mano, NON stimare):")
        for lega, nome in mancanti:
            print(f"   [{lega}] {nome}")


if __name__ == "__main__":
    main()
