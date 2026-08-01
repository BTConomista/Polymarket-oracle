"""Carriere — STRATO 2: l'infobox di Wikipedia.

COSA AGGIUNGE allo strato 1 (`careers.py`, da `appearances.csv`), che copre 48
competizioni ma solo **dal 2012-07-03** e senza seconde divisioni né campionati
extra-europei:

1. **tutto ciò che precede il 2012** — sono 1.045 giocatori della nostra
   popolazione troncati al bordo del dataset;
2. le **seconde divisioni** e i **settori giovanili**;
3. i campionati **extra-europei**.

Esempio misurato: Lewandowski nello strato 1 comincia il 2012-08-12 al
Borussia Dortmund. L'infobox dà **Delta Warsaw 2005, Legia Warsaw II 2005-06,
Znicz Pruszków 2006-08, Lech Poznań 2008-10** — cinque anni di carriera che
`appearances.csv` non può conoscere.

PERCHÉ L'INFOBOX E NON LA TABELLA «Career statistics». È la lezione della Fase
del 31/07/2026: il fronte era rimasto aperto per **due ricerche** perché si
contava la tabella *più ricca e più rara* (62,2% di copertura) invece del blocco
*più povero e quasi universale* — l'infobox, al **99,7%**, che contiene già i
tre campi che servono: anni **con la fine**, club, presenze.

⚖️ LICENZA — DA LEGGERE PRIMA DI RIDISTRIBUIRE.
Il contenuto di Wikipedia è **CC BY-SA** (4.0 per il testo delle voci). Sono
**due** obblighi, non uno:
- **BY**: attribuzione. Ogni riga prodotta da qui porta `fonte='wikipedia'` e
  l'URL esatto della pagina in `source_url`;
- **SA**: share-alike. Una banca dati **derivata** che incorpori questo
  contenuto e venga **distribuita** deve essere a sua volta CC BY-SA. Il repo è
  pubblico, quindi l'obbligo è attivo.
Per questo l'output vive in una cartella **separata e auto-dichiarata**
(`data/carriere_wikipedia/`, con il proprio avviso di licenza) invece di essere
mescolato al resto: tiene lo share-alike circoscritto a ciò che lo eredita
davvero, invece di lasciarlo ambiguo sull'intero progetto.

🤖 CONFORMITÀ. Si usano **solo** le pagine `/wiki/<Nome>`, verificate permesse
dal `robots.txt` di ogni dominio linguistico usato (`/w/`, `/api/` e
`/wiki/Special:` sono invece vietati e non vengono toccati). Ritmo limitato,
cache su disco perché una pagina si scarichi **una volta sola**, User-Agent
onesto e identificabile. Nessuna protezione viene aggirata.

⚠️ TRAPPOLA NOTA: `urllib.robotparser` NON implementa RFC 9309 (applica
*first-match-wins* invece di longest-match) e su Wikipedia si auto-chiude
percorsi leciti. Le regole qui sotto sono state verificate a mano.
"""

from __future__ import annotations

import gzip
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "wikipedia_cache"          # NON versionata
OUT_DIR = ROOT / "data" / "carriere_wikipedia"          # versionata, CC BY-SA

USER_AGENT = (
    "Polymarket-oracle/1.0 (ricerca statistica non commerciale; "
    "contatto: camarda.federico1@gmail.com) ClaudeBot"
)
CRAWL_DELAY = 1.0            # secondi fra richieste allo stesso dominio
TIMEOUT = 30

FONTE = "wikipedia"
LICENZA = "CC BY-SA 4.0"

# Percorsi VIETATI dal robots.txt di Wikipedia: se un URL cade qui, non si
# scarica. Verificati a mano su en/pt/es/it/de/fr il 31/07/2026.
PATH_VIETATI = ("/w/", "/api/", "/wiki/Special:", "/wiki/Spezial:",
                "/wiki/Spesial:", "/wiki/Special%3A", "/trap/")

# Marcatori di sezione dell'infobox (inglese). Gli altri domini linguistici
# hanno etichette diverse: per ora si usa SOLO l'inglese, che l'audit ha
# misurato coprire il 99,7% — le altre lingue hanno dato guadagno ZERO su 333.
INTESTAZIONI_SENIOR = ("senior career",)
INTESTAZIONI_GIOVANILI = ("youth career", "college career")
INTESTAZIONI_FINE = ("international career", "managerial career",
                     "medal record", "honours")


@dataclass
class Tappa:
    """Una riga del blocco carriera dell'infobox."""
    player_id: int
    ordine: int
    club: str
    anno_da: int | None
    anno_a: int | None
    aperta: bool          # "2026–" senza fine: tappa ancora in corso
    presenze: int | None
    gol: int | None
    prestito: bool
    giovanili: bool
    source_url: str
    identita: str = "non_verificata"   # confermata_data | confermata_club | quarantena | respinta
    fonte: str = FONTE
    licenza: str = LICENZA


@dataclass
class Esito:
    """Risultato di un tentativo su un giocatore (anche negativo: R1.4)."""
    player_id: int
    nome: str
    url: str | None = None
    stato: str = "ok"      # ok | nessuna_pagina | nessun_infobox | nessun_blocco | errore | identita_non_confermata
    tappe: list[Tappa] = field(default_factory=list)
    dettaglio: str = ""
    bday_pagina: str | None = None
    identita: str = "non_verificata"


def _percorso_permesso(url: str) -> bool:
    p = urllib.parse.urlparse(url).path
    return not any(p.startswith(v) for v in PATH_VIETATI)


def _cache_path(lang: str, titolo: str) -> Path:
    safe = urllib.parse.quote(titolo, safe="")[:150]
    return CACHE_DIR / lang / f"{safe}.html.gz"


_ultimo_fetch: dict[str, float] = {}


def fetch_page(titolo: str, lang: str = "en", *, use_cache: bool = True) -> str | None:
    """Scarica `https://<lang>.wikipedia.org/wiki/<titolo>`, con cache su disco.

    Ritorna None se la pagina non esiste (404). Alza su errori diversi.
    La cache serve a scaricare **una volta sola**: è la forma più concreta di
    rispetto per il server, più del ritardo fra richieste.
    """
    url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(titolo.replace(' ', '_'))}"
    if not _percorso_permesso(url):
        raise ValueError(f"percorso vietato dal robots.txt: {url}")

    cp = _cache_path(lang, titolo)
    if use_cache and cp.exists():
        return gzip.decompress(cp.read_bytes()).decode("utf-8", errors="replace")

    scorso = _ultimo_fetch.get(lang, 0.0)
    attesa = CRAWL_DELAY - (time.monotonic() - scorso)
    if attesa > 0:
        time.sleep(attesa)
    _ultimo_fetch[lang] = time.monotonic()

    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    html = raw.decode("utf-8", errors="replace")
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_bytes(gzip.compress(html.encode("utf-8")))
    return html


_RE_ANNI = re.compile(r"(\d{4})\s*(?:[–—-]\s*(\d{4})?)?")
_RE_NUM = re.compile(r"-?\d+")


def _e_infobox(classe) -> bool:
    """L'attributo `class` arriva come lista (`['infobox','vcard',...]`) o come
    stringa a seconda della versione di bs4: gestire un solo caso fa fallire il
    parse in silenzio — bug vero, costato il primo giro di prove."""
    if not classe:
        return False
    if isinstance(classe, str):
        return "infobox" in classe.split()
    return "infobox" in list(classe)


def _parse_anni(testo: str) -> tuple[int | None, int | None, bool]:
    """'2006–2008' -> (2006, 2008, False); '2026–' -> (2026, None, True).

    ⚠️ **`0000` è un SEGNAPOSTO di Wikipedia, non un anno** — il template
    dell'infobox lo usa quando l'anno di inizio è ignoto, e lo rende
    letteralmente come `'0000 –2000'`. È un **finto pieno** (regola R6):
    lasciarlo passare darebbe carriere iniziate nell'anno zero e lunghe due
    millenni. Trovato sul campo su 7 righe del primo lotto — Hradecky,
    Handanovic, Insigne, Joe Hart e altri — tutte tappe giovanili.
    """
    t = testo.strip()
    m = _RE_ANNI.search(t)
    if not m:
        return None, None, False
    da: int | None = int(m.group(1))
    a = int(m.group(2)) if m.group(2) else None
    if da == 0:                      # segnaposto "inizio ignoto"
        da = None
    aperta = a is None and bool(re.search(r"[–—-]\s*$", t))
    if a is None and not aperta and da is not None:
        a = da           # tappa di un anno solo: '2005'
    return da, a, aperta


def _parse_intero(testo: str) -> int | None:
    m = _RE_NUM.search(testo.replace("(", "").replace(")", ""))
    return int(m.group()) if m else None


def bday_pagina(html: str) -> str | None:
    """La data di nascita dichiarata dall'infobox (`<span class="bday">`).

    E' l'unico dato che permette di sapere **se la pagina parla davvero di quel
    giocatore**, e sta gia' nella pagina scaricata: verificarlo costa **zero
    richieste in piu'**.
    """
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("span", class_="bday")
    return tag.get_text(strip=True) if tag else None


def verifica_identita(
    bday: str | None, nascita_attesa: str | None, tappe: list[Tappa],
    club_noti: set[str] | None = None, tolleranza_giorni: int = 3,
) -> str:
    """⚠️ LA DIFESA CONTRO GLI OMONIMI — regola GERARCHICA, non un OR.

    L'audit del 01/08/2026 ha misurato che senza questo controllo lo **0,268%**
    delle pagine raccolte e' di **un'altra persona**: carriere vere, coerenti,
    con il nostro nome sopra. E' regola **R6** allo stato puro — nessun NaN,
    nessun errore, solo il dato di qualcun altro. Casi trovati: il `player_id`
    di un giocatore nato nel 1991 che riceveva la carriera di **Pele'** (Santos
    1956, New York Cosmos 1975); Joao Moutinho con **692 presenze fantasma**.

    L'ordine conta e **non e' sostituibile da un OR**: `data OR club` porterebbe
    il falso positivo dallo 0,23% a ~10,5%, perche' un OR non puo' essere piu'
    forte del suo ramo piu' debole.

    1. data di nascita entro `tolleranza_giorni`      -> `confermata_data`
    2. data non confrontabile ma >=50% dei club noti  -> `confermata_club`
    3. date discordi MA i club coincidono             -> `quarantena`
    4. altrimenti                                      -> `respinta`

    Il passo 3 esiste perche' **32 discordanze su 45 sono la persona giusta**
    con l'anagrafica contestata fra le due fonti (Chancel Mbemba 1988 contro
    1994, con 5 club su 5 coincidenti): un taglio secco sulla data butterebbe
    dati buoni. La quarantena si dichiara, non si nasconde.
    """
    import datetime as _dt

    def _data(x):
        if not x:
            return None
        try:
            return _dt.date.fromisoformat(str(x)[:10])
        except ValueError:
            return None

    a, b = _data(bday), _data(nascita_attesa)
    coincide_data = (
        a is not None and b is not None and abs((a - b).days) <= tolleranza_giorni
    )
    if coincide_data:
        return "confermata_data"

    copertura = 0.0
    if club_noti:
        nostri = {c.lower() for c in club_noti}
        loro = {t.club.lower() for t in tappe if not t.giovanili}
        if loro:
            copertura = sum(
                1 for c in nostri if any(c in x or x in c for x in loro)
            ) / max(len(nostri), 1)

    if a is None or b is None:
        return "confermata_club" if copertura >= 0.5 else "respinta"
    return "quarantena" if copertura >= 0.5 else "respinta"


def parse_career(html: str, player_id: int, url: str) -> list[Tappa]:
    """Estrae il blocco carriera dell'infobox: senior + giovanili, marcati.

    I prestiti sono riconosciuti dal marcatore '→' che Wikipedia usa nella
    colonna club ('→ Club (loan)'): tenerli distinti conta, perché una tappa in
    prestito non è un trasferimento.
    """
    soup = BeautifulSoup(html, "lxml")
    box = soup.find("table", class_=_e_infobox)
    if box is None:
        return []

    tappe: list[Tappa] = []
    sezione: str | None = None
    ordine = 0
    for tr in box.find_all("tr"):
        testo = tr.get_text(" ", strip=True)
        basso = testo.lower()

        if any(h in basso for h in INTESTAZIONI_SENIOR):
            sezione = "senior"
            continue
        if any(h in basso for h in INTESTAZIONI_GIOVANILI):
            sezione = "giovanili"
            continue
        if any(h in basso for h in INTESTAZIONI_FINE):
            sezione = None
            continue
        if sezione is None:
            continue

        celle = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if len(celle) < 2:
            continue
        if celle[0].lower().startswith("years"):      # riga di intestazione
            continue
        anni, club = celle[0], celle[1]
        if not re.search(r"\d{4}", anni) or not club:
            continue

        da, a, aperta = _parse_anni(anni)
        prestito = "→" in club or "loan" in club.lower()
        club_pulito = club.replace("→", "").strip()
        club_pulito = re.sub(r"\s*\((loan|on loan)\)\s*", "", club_pulito, flags=re.I).strip()

        ordine += 1
        tappe.append(Tappa(
            player_id=player_id, ordine=ordine, club=club_pulito,
            anno_da=da, anno_a=a, aperta=aperta,
            presenze=_parse_intero(celle[2]) if len(celle) > 2 else None,
            gol=_parse_intero(celle[3]) if len(celle) > 3 else None,
            prestito=prestito, giovanili=(sezione == "giovanili"),
            source_url=url,
        ))
    return tappe


def fetch_player(
    player_id: int, nome: str, lang: str = "en",
    *, nascita_attesa: str | None = None, club_noti: set[str] | None = None, **kw
) -> Esito:
    """Scarica e analizza un giocatore. Registra anche gli esiti NEGATIVI.

    Un esito negativo va registrato quanto uno positivo (principio §1.4 del
    CLAUDE.md): senza, la sessione dopo ritenta gli stessi 2.000 fallimenti.
    """
    titolo = nome.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(titolo)}"
    try:
        html = fetch_page(titolo, lang, **kw)
    except Exception as e:  # pragma: no cover - dipende dalla rete
        return Esito(player_id, nome, url, "errore", dettaglio=repr(e))
    if html is None:
        return Esito(player_id, nome, url, "nessuna_pagina")
    if "infobox" not in html:
        return Esito(player_id, nome, url, "nessun_infobox")
    tappe = parse_career(html, player_id, url)
    if not tappe:
        return Esito(player_id, nome, url, "nessun_blocco")

    bday = bday_pagina(html)
    identita = verifica_identita(bday, nascita_attesa, tappe, club_noti)
    for t in tappe:
        t.identita = identita
    if identita == "respinta":
        # Le tappe si conservano nell'esito (servono a capire CHI era la pagina
        # sbagliata) ma lo stato dice che non vanno nel database.
        return Esito(player_id, nome, url, "identita_non_confermata", tappe,
                     bday_pagina=bday, identita=identita)
    return Esito(player_id, nome, url, "ok", tappe,
                 bday_pagina=bday, identita=identita)
