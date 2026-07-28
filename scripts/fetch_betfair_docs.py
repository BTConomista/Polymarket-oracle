"""Specchia in locale la documentazione ufficiale delle API Betfair (Fase 110).

PERCHE' ESISTE. La Fase 109-bis ha pagato un bug (il campo `img` dello stream,
`docs/DIARIO.md`) per non aver letto la specifica ufficiale prima di scrivere
il parser -- quando quella specifica era pubblica, gratuita e raggiungibile.
Perche' non succeda di nuovo, e perche' ogni sessione futura che lavori su
Betfair parta da dentro il repo invece che da una ricerca sul web, la
documentazione viene copiata qui.

FONTE — dichiarata per ogni file (regola R2: fonte secondaria sempre esplicita):

  Betfair Developer Program — "Betfair Exchange API Documentation"
  https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/overview

  I contenuti sono di Betfair. Questa e' una COPIA DI LAVORO per uso interno
  del progetto (riferimento tecnico durante lo sviluppo), non una
  ri-pubblicazione: ogni file porta in testa l'URL della pagina originale, la
  data di estrazione e l'id Confluence, e il testo resta quello di Betfair.
  In caso di dubbio vince SEMPRE la pagina online, che puo' essere piu'
  recente: per questo lo script e' ri-eseguibile.

COME. Il sito e' un SPA JavaScript (l'HTML grezzo da' solo la navigazione), ma
l'API REST di Confluence risponde 200 **senza autenticazione**:
  /wiki/rest/api/space/<key>/content?limit=200&start=N   -> elenco pagine
  /wiki/rest/api/content/<id>?expand=body.storage        -> corpo XHTML
Il corpo si converte in Markdown con `markdownify` (dipendenza OPZIONALE:
`pip install -e ".[docs]"`, non serve al modello ne' ai test).

⚠️ Da NON confondere: questo spazio documenta l'**Exchange API** (live). Il
servizio **Historical Data** (`historicdata.betfair.com`) ha una API diversa,
i cui 5 endpoint sono documentati a parte in
`docs/betfair_api/90_historical_data_api.md`. I due si toccano in un punto che
ci riguarda: i file storici sono **registrazioni dello stream** descritto qui,
quindi la specifica dello stream vale anche per il parser di
`scripts/fetch_betfair_historic.py`.

USO:
    pip install -e ".[docs]"
    python scripts/fetch_betfair_docs.py            # scrive docs/betfair_api/
    python scripts/fetch_betfair_docs.py --list     # solo l'elenco, non scarica
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "betfair_api"

BASE = "https://betfair-developer-docs.atlassian.net/wiki"
SPACE = "1smk3cen4v3lu3yomq5qye0ni"
SPACE_URL = f"{BASE}/spaces/{SPACE}/overview"
THROTTLE = 0.35

# Pagine da NON specchiare: cronologia dei rilasci e traduzioni. Non servono al
# lavoro tecnico e triplicherebbero il peso della copia.
SKIP = re.compile(r"New API|Release Notes|Retrospective|Espa|Portugu|\.RO$", re.I)

# Ordinamento tematico: il prefisso numerico serve solo a far leggere i file
# nell'ordine in cui servono davvero, dal "come mi autentico" al dettaglio.
CATEGORIE: list[tuple[str, str, list[str]]] = [
    ("00", "guida", [
        "Betfair API Docs", "Getting Started", "Additional Information",
        "Best Practice", "Optimizing API Application Performance",
        "Developer Support", "API Demo Tools",
        "Sample Code, Client Libraries & Tutorials",
        "Interface Definition Documents", "Reference Guide",
        "Reference Guide (Offline Copy)",
    ]),
    ("10", "accesso", [
        "Login & Session Management", "Non-Interactive (bot) login",
        "Interactive Login - API Endpoint",
        "Interactive Login - Desktop Application", "Application Keys",
        "Certificate Generation With XCA", "token",
    ]),
    ("20", "betting", [
        "Betting API", "listEventTypes", "listCompetitions", "listEvents",
        "listMarketTypes", "listCountries", "listVenues", "listTimeRanges",
        "listMarketCatalogue", "listMarketBook", "listRunnerBook",
        "listMarketProfitAndLoss", "Navigation Data For Applications",
        "Market Data Request Limits", "Betfair Starting Price Betting (BSP)",
    ]),
    ("30", "tipi-e-enum", [
        "Betting Enums", "Betting Type Definitions", "Betting Exceptions",
    ]),
    ("40", "stream", ["Exchange Stream API"]),
    ("50", "mercati-nazionali", [
        "Betting On Italian Exchange", "Betting on Spanish Exchange",
    ]),
    ("60", "ordini", [
        "placeOrders", "cancelOrders", "replaceOrders", "updateOrders",
        "listCurrentOrders", "listClearedOrders",
        "listClearedOrders - Roll-up Fields Available", "Heartbeat API",
    ]),
    ("70", "account", [
        "Accounts API", "Accounts Enums", "Accounts TypeDefinitions",
        "Accounts Exceptions", "getAccountDetails", "getAccountFunds",
        "getAccountStatement", "listCurrencyRates", "Race Status API",
    ]),
    ("80", "linguaggi", ["Python", "Java", "C#", "PHP", "Javascript",
                          "Excel & VBA Sample"]),
]


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def elenco_pagine() -> list[tuple[str, str]]:
    pagine, start = [], 0
    while True:
        d = _get(f"{BASE}/rest/api/space/{SPACE}/content?limit=200&start={start}")
        res = d["page"]["results"]
        pagine += [(p["id"], p["title"]) for p in res]
        if len(res) < 200:
            return pagine
        start += 200
        time.sleep(THROTTLE)


def _slug(t: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    return re.sub(r"_+", "_", s)[:70]


def _categoria(titolo: str) -> tuple[str, str]:
    for num, nome, titoli in CATEGORIE:
        if titolo in titoli:
            return num, nome
    return "95", "altro"


def scarica(dry: bool = False) -> None:
    from markdownify import markdownify as md   # dipendenza opzionale [docs]

    pagine = [(i, t) for i, t in elenco_pagine() if not SKIP.search(t)]
    pagine.sort(key=lambda x: (_categoria(x[1])[0], x[1].lower()))
    print(f"{len(pagine)} pagine da specchiare (release-notes e traduzioni escluse)")
    if dry:
        for i, t in pagine:
            num, nome = _categoria(t)
            print(f"  [{num} {nome:18s}] {t}")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    oggi = time.strftime("%Y-%m-%d")
    indice: list[tuple[str, str, str, str]] = []

    for n, (pid, titolo) in enumerate(pagine, 1):
        d = _get(f"{BASE}/rest/api/content/{pid}?expand=body.storage")
        corpo = md(d.get("body", {}).get("storage", {}).get("value", ""),
                   heading_style="ATX")
        corpo = re.sub(r"\n{4,}", "\n\n\n", corpo).strip()
        num, nome = _categoria(titolo)
        fname = f"{num}_{nome}__{_slug(titolo)}.md"
        url = f"{BASE}/spaces/{SPACE}/pages/{pid}"
        testata = (
            f"# {titolo}\n\n"
            f"> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.\n"
            f"> Fonte: *Betfair Exchange API Documentation* — <{url}>\n"
            f"> (spazio Confluence `{SPACE}`, pagina id `{pid}`; estratto il {oggi}\n"
            f"> con `scripts/fetch_betfair_docs.py`).\n"
            f"> **In caso di dubbio vince la pagina online**, che può essere più\n"
            f"> recente di questa copia: ri-esegui lo script per aggiornarla.\n\n"
            f"---\n\n"
        )
        (OUT / fname).write_text(testata + corpo + "\n", encoding="utf-8")
        indice.append((num, nome, titolo, fname))
        if n % 10 == 0 or n == len(pagine):
            print(f"  [{n}/{len(pagine)}] {titolo}")
        time.sleep(THROTTLE)

    _scrivi_indice(indice, oggi)
    print(f"\nscritte {len(indice)} pagine in {OUT.relative_to(ROOT)}/")


def _scrivi_indice(indice: list[tuple[str, str, str, str]], oggi: str) -> None:
    righe = [
        "# Documentazione API Betfair — copia di lavoro locale",
        "",
        "> **Attribuzione.** Il contenuto di questa cartella è **testo di",
        "> Betfair**, non del progetto. Fonte unica:",
        "> **Betfair Developer Program — *Betfair Exchange API Documentation***",
        f"> <{SPACE_URL}>",
        f"> (spazio Confluence `{SPACE}`). Estratto il **{oggi}** con",
        "> `scripts/fetch_betfair_docs.py`, che è ri-eseguibile: **in caso di",
        "> divergenza vince sempre la pagina online**, che può essere più recente.",
        "",
        "**Perché esiste.** Alla Fase 109-bis un bug del parser dello stream (il",
        "campo `img`) è costato una correzione che si sarebbe evitata leggendo la",
        "specifica ufficiale *prima* di scrivere il codice. Questa copia serve a",
        "far partire ogni lavoro futuro su Betfair da dentro il repo.",
        "",
        "**Cosa NON c'è**: le note di rilascio (una ventina di pagine di",
        "cronologia) e le traduzioni (spagnolo, portoghese, rumeno) — escluse",
        "dallo script perché non servono al lavoro tecnico.",
        "",
        "## Le due API di Betfair, da non confondere",
        "",
        "| | a cosa serve | dove è documentata |",
        "|---|---|---|",
        "| **Exchange API** (live) | quote in tempo reale, piazzare scommesse, "
        "stream dei prezzi | questa cartella, file `00`-`80` |",
        "| **Historical Data** | scaricare i file storici già registrati | "
        "`90_historical_data_api.md` (fonte diversa) |",
        "",
        "Si toccano in un punto che ci riguarda: **i file storici sono",
        "registrazioni dello stream** descritto in `40_stream__*`, quindi quella",
        "specifica vale anche per il parser di",
        "`scripts/fetch_betfair_historic.py`.",
        "",
        "## Le pagine che servono per prime",
        "",
        "- **`40_stream__exchange_stream_api.md`** — il formato dei messaggi",
        "  (`mcm`, `mc`, `rc`, `ltp`, `img`, `marketDefinition.inPlay`): è la",
        "  specifica contro cui va verificato il parser dei file storici.",
        "- **`30_tipi-e-enum__betting_enums.md`** — i valori ammessi, fra cui i",
        "  tipi di mercato (`MATCH_ODDS`, `OVER_UNDER_25`, …).",
        "- **`10_accesso__*`** — come si ottiene un token di sessione (`ssoid`)",
        "  e a cosa serve l'application key.",
        "- **`50_mercati-nazionali__betting_on_italian_exchange.md`** — regole",
        "  dell'exchange italiano: rilevante perché l'account del progetto è",
        "  italiano e `historicdata.betfair.com` risponde 403 per regione.",
        "",
        "## Indice completo",
        "",
    ]
    ultima = None
    for num, nome, titolo, fname in indice:
        if (num, nome) != ultima:
            righe += ["", f"### {num} · {nome}", ""]
            ultima = (num, nome)
        righe.append(f"- [{titolo}]({fname})")
    (OUT / "README.md").write_text("\n".join(righe) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true",
                   help="mostra solo quali pagine verrebbero specchiate")
    a = p.parse_args()
    scarica(dry=a.list)


if __name__ == "__main__":
    main()
