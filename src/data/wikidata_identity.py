"""Verifica d'identità dei giocatori Wikipedia contro **Wikidata** (terza fonte).

PERCHÉ ESISTE
-------------
La verifica della Fase precedente (`wikipedia_careers.verifica_identita`) legge
la data di nascita **dall'HTML** della pagina (`<span class="bday">`). Funziona
quando il markup c'è; quando non c'è — infobox senza `bday`, template diverso,
data solo in prosa — il confronto è impossibile e il giocatore finisce in
`quarantena` (dentro il database, ma non confermato) o `respinta` (perso).
Al 01/08/2026 sono **483 giocatori** in questo limbo.

Wikidata risolve esattamente questo, e lo risolve **meglio**:

* è **strutturata**: `P569` (data di nascita) è un valore tipizzato, non testo
  da estrarre. Non dipende dal template né dalla lingua;
* è la **stessa entità** della pagina che abbiamo scaricato — il `Q-id` è
  inciso nella pagina stessa (`wgWikibaseItemId`), quindi non c'è alcun
  passaggio di *matching per nome*: il punto debole di ogni verifica per
  omonimia qui non esiste;
* dà anche `P54` (militanza in squadra) con i qualificatori `P580`/`P582`
  (inizio/fine) — cioè la **finestra temporale** della carriera, che l'infobox
  dà in modo irregolare.

Il costo è **zero richieste per il Q-id** (già estratti dalla cache HTML in
`data/carriere_wikipedia/wikidata_qid.csv.gz`) e **una richiesta per giocatore
da dirimere** — 483, non 24.000.

⚖️ ROBOTS.TXT — verificato riga per riga il 01/08/2026
------------------------------------------------------
`https://www.wikidata.org/robots.txt` contiene, in quest'ordine::

    Disallow: /wiki/Special:EntityData/
    Allow:    /wiki/Special:EntityData/*.

La regola che si applica è quella col **pattern più lungo** (RFC 9309 §2.2.2),
quindi un URL che finisce con un'estensione (`.json`) è **permesso**: è l'endpoint
che Wikidata pubblica apposta per l'accesso automatico.

⚠️ Attenzione: `urllib.robotparser` della standard library implementa
*first-match-wins* e su questa coppia risponde `False` — **sbagliato**. Per
questo il controllo qui sotto è scritto a mano invece di riusare quella libreria
o `wikipedia_careers.PATH_VIETATI` (che vieta tutto `/wiki/Special:`, giusto per
i domini Wikipedia e sbagliato per questo).

⚖️ LICENZA: i dati Wikidata sono **CC0** (pubblico dominio) — a differenza del
testo di Wikipedia, che è CC BY-SA. Nessun vincolo di condivisione allo stesso
modo su ciò che deriva da qui.

⏱️ R8: `data_nascita` è **statico** (anagrafica); le finestre `P580/P582` sono
`post` rispetto alla partita, ma qui non alimentano nessuna feature — servono
solo a stabilire *di chi si parla*, che è un uso fuori dal tempo della partita.
"""

from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "wikidata_cache"        # NON versionata
OUT_DIR = ROOT / "data" / "carriere_wikipedia"       # versionata

USER_AGENT = (
    "Polymarket-oracle/1.0 (ricerca statistica non commerciale; "
    "contatto: camarda.federico1@gmail.com) ClaudeBot"
)
CRAWL_DELAY = 1.0
TIMEOUT = 30

FONTE = "wikidata"
LICENZA = "CC0"

# Tolleranza sul confronto fra date di nascita. Tre giorni: le fonti calcistiche
# discordano di un giorno con una certa frequenza (fuso orario della
# registrazione, data di dichiarazione vs data di nascita). Stesso valore usato
# da `wikipedia_careers.verifica_identita`, per non introdurre due soglie
# diverse per la stessa domanda.
TOLLERANZA_GIORNI = 3

P_NASCITA = "P569"
P_SQUADRA = "P54"
P_INIZIO = "P580"
P_FINE = "P582"
P_PRESENZE = "P1350"


def percorso_permesso(url: str) -> bool:
    """Il robots.txt di wikidata.org, applicato con la regola del match più lungo.

    `Disallow: /wiki/Special:EntityData/` + `Allow: /wiki/Special:EntityData/*.`
    → un URL con un'estensione nel nome finale è permesso, gli altri no.
    """
    p = urllib.parse.urlparse(url).path
    if not p.startswith("/wiki/Special:EntityData/"):
        # tutto il resto di /wiki/Special: e' vietato come su Wikipedia
        return not p.startswith("/wiki/Special:")
    resto = p[len("/wiki/Special:EntityData/"):]
    return "." in resto          # l'Allow richiede il punto (estensione)


def _cache_path(qid: str) -> Path:
    return CACHE_DIR / f"{qid}.json.gz"


_ultimo_fetch = 0.0


def fetch_entity(qid: str, *, use_cache: bool = True) -> dict | None:
    """L'entità Wikidata `qid`, dall'endpoint `Special:EntityData`.

    Ritorna None se l'entità non esiste (404). Alza sugli altri errori: un
    errore di rete NON è un dato, e trattarlo come "assente" creerebbe un buco
    che nessuno saprebbe più distinguere da un'assenza vera (R6).
    """
    global _ultimo_fetch
    if not qid or not qid.startswith("Q"):
        return None
    cp = _cache_path(qid)
    if use_cache and cp.exists():
        return json.loads(gzip.decompress(cp.read_bytes()).decode("utf-8"))

    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    if not percorso_permesso(url):
        raise ValueError(f"percorso vietato dal robots.txt: {url}")

    attesa = CRAWL_DELAY - (time.monotonic() - _ultimo_fetch)
    if attesa > 0:
        time.sleep(attesa)
    _ultimo_fetch = time.monotonic()

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
    dati = json.loads(raw.decode("utf-8"))
    ent = (dati.get("entities") or {}).get(qid)
    if ent is None:
        return None
    # si salva SOLO l'entità che interessa: il JSON completo di un redirect può
    # contenerne due, e riscriverlo intero triplica la cache per niente
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_bytes(gzip.compress(json.dumps(ent, ensure_ascii=False).encode("utf-8")))
    return ent


def _claim_valori(ent: dict, prop: str) -> list[dict]:
    return [
        c for c in (ent.get("claims") or {}).get(prop, [])
        if (c.get("mainsnak") or {}).get("snaktype") == "value"
    ]


def data_nascita(ent: dict) -> str | None:
    """`P569` come `YYYY-MM-DD`, o None.

    Wikidata annota la **precisione** (9 = anno, 10 = mese, 11 = giorno). Una
    data precisa all'anno è scritta `+1969-00-00T00:00:00Z`: usarla come se
    fosse un giorno darebbe un confronto falso. Qui si accetta solo la
    precisione al giorno (11) — sotto quella, la risposta onesta è "non lo so".
    """
    for c in _claim_valori(ent, P_NASCITA):
        v = c["mainsnak"]["datavalue"]["value"]
        if v.get("precision", 0) < 11:
            continue
        t = v.get("time", "")
        if t.startswith("+") and len(t) >= 11:
            return t[1:11]
    return None


@dataclass
class Militanza:
    """Una riga `P54` con i suoi qualificatori temporali."""
    club_qid: str
    da: str | None = None       # P580, YYYY-MM-DD (o YYYY-MM / YYYY)
    a: str | None = None        # P582
    presenze: int | None = None


def _qual_data(c: dict, prop: str) -> str | None:
    for q in (c.get("qualifiers") or {}).get(prop, []):
        if q.get("snaktype") != "value":
            continue
        v = q.get("datavalue", {}).get("value", {})
        t = v.get("time", "")
        prec = v.get("precision", 0)
        if not t.startswith("+"):
            continue
        # si tronca alla precisione DICHIARATA: 9=anno, 10=mese, 11=giorno.
        # Scrivere "2004-01-01" quando la fonte dice "2004" sarebbe inventare
        # due campi su tre (R6: il finto pieno).
        return t[1:5] if prec <= 9 else t[1:8] if prec == 10 else t[1:11]
    return None


def militanze(ent: dict) -> list[Militanza]:
    out = []
    for c in _claim_valori(ent, P_SQUADRA):
        v = c["mainsnak"]["datavalue"]["value"]
        presenze = None
        for q in (c.get("qualifiers") or {}).get(P_PRESENZE, []):
            if q.get("snaktype") == "value":
                try:
                    presenze = int(float(q["datavalue"]["value"]["amount"]))
                except Exception:
                    presenze = None
        out.append(Militanza(
            club_qid=v.get("id", ""),
            da=_qual_data(c, P_INIZIO), a=_qual_data(c, P_FINE),
            presenze=presenze,
        ))
    return out


def ultimo_anno(ms: list[Militanza]) -> int | None:
    """L'anno più recente toccato dalla carriera secondo Wikidata.

    Una militanza **aperta** (`P580` senza `P582`) significa "ancora in corso":
    non ha un ultimo anno, e restituire l'anno d'inizio la farebbe sembrare
    finita. In quel caso la risposta è None — "non è finita", non "è finita nel
    2019".
    """
    anni = []
    for m in ms:
        if m.da and not m.a:
            return None
        if m.a:
            try:
                anni.append(int(m.a[:4]))
            except ValueError:
                pass
    return max(anni) if anni else None


@dataclass
class Verdetto:
    """L'esito della verifica su un giocatore."""
    player_id: int
    qid: str
    identita_prima: str
    esito: str = "indeterminato"
    # confermata | smentita | indeterminato
    motivo: str = ""
    nascita_wikidata: str | None = None
    nascita_attesa: str | None = None
    scarto_giorni: int | None = None
    ultimo_anno_carriera: int | None = None
    n_militanze: int = 0
    fonte: str = FONTE
    licenza: str = LICENZA
    militanze: list[Militanza] = field(default_factory=list)


def _giorni(a: str, b: str) -> int | None:
    import datetime as dt
    try:
        da = dt.date.fromisoformat(a[:10])
        db = dt.date.fromisoformat(b[:10])
    except ValueError:
        return None
    return abs((da - db).days)


def verifica(player_id: int, qid: str, nascita_attesa, identita_prima: str,
             prima_presenza=None, *, use_cache: bool = True) -> Verdetto:
    """Il verdetto di Wikidata su «la pagina che abbiamo letto è questo giocatore?».

    La regola è **gerarchica**, come quella su Wikipedia — non un OR, che non
    sarebbe mai più forte del suo ramo più debole:

    1. **date confrontabili** → confermata se lo scarto è ≤ `TOLLERANZA_GIORNI`,
       altrimenti smentita. È il ramo decisivo: `P569` è strutturata, quindi qui
       non c'è margine d'interpretazione;
    2. **niente data su Wikidata**, ma la carriera secondo `P54` **finisce prima**
       che il nostro giocatore scendesse in campo la prima volta → smentita per
       incompatibilità temporale (è il caso del padre omonimo);
    3. altrimenti → **indeterminato**. Non "confermato": un'assenza di prova non
       è una prova, e marcare come confermato ciò che non lo è ricrea proprio il
       problema che questa verifica esiste per chiudere.
    """
    v = Verdetto(player_id=int(player_id), qid=str(qid),
                 identita_prima=identita_prima,
                 nascita_attesa=str(nascita_attesa)[:10] if nascita_attesa else None)
    ent = fetch_entity(qid, use_cache=use_cache)
    if ent is None:
        v.motivo = "entita' assente su Wikidata"
        return v

    v.nascita_wikidata = data_nascita(ent)
    v.militanze = militanze(ent)
    v.n_militanze = len(v.militanze)
    v.ultimo_anno_carriera = ultimo_anno(v.militanze)

    if v.nascita_wikidata and v.nascita_attesa:
        g = _giorni(v.nascita_wikidata, v.nascita_attesa)
        v.scarto_giorni = g
        if g is not None:
            v.esito = "confermata" if g <= TOLLERANZA_GIORNI else "smentita"
            v.motivo = f"P569 {v.nascita_wikidata} vs attesa {v.nascita_attesa} ({g} gg)"
            return v

    if v.ultimo_anno_carriera and prima_presenza is not None:
        try:
            anno_nostro = int(str(prima_presenza)[:4])
        except ValueError:
            anno_nostro = None
        if anno_nostro and v.ultimo_anno_carriera < anno_nostro:
            v.esito = "smentita"
            v.motivo = (f"carriera Wikidata chiusa nel {v.ultimo_anno_carriera}, "
                        f"prima presenza nostra nel {anno_nostro}")
            return v

    v.motivo = "P569 assente o imprecisa, nessuna incompatibilita' temporale"
    return v
