"""Coupe de France 2025-26 da Wikipedia — l'unica delle sei coppe che
player-scores non copre affatto.

PERCHE' ESISTE. Il dataset player-scores (Transfermarkt) ha `competitions.csv`
con 10 coppe nazionali e **nessuna francese** (rilievo gia' registrato in
docs/AUDIT_FONTI_GIOCATORI.md §420). Per la Coppa Italia, la FA Cup, la
Carabao, la Copa del Rey e la DFB-Pokal abbiamo risultati, formazioni ed
eventi; per la Coupe de France non avevamo nemmeno il risultato.

LA FONTE. `fr.wikipedia.org`, pagina «Coupe de France de football 2025-2026».
Le partite vivono nel template `{{Feuille de match}}`, che e' **strutturato**:

    {{Feuille de match|enroulée = oui
    |date = {{Date|15|11|2025}} | heure = {{Heure|15|30}}
    |équipe 1 = [[Club sportif moulien|CS moulien]] <small>(R1)</small>
    |équipe 2 = '''[[AS Le Gosier]] <small>(R1)</small>'''
    |score = 2 - 3
    |score tab = 4 - 3          <- eventuale sequenza di rigori
    |stade = Stade Jacques Ponrémy, [[Le Moule]]
    }}

Tre regali di questo formato, che nessuna altra fonte ci dava:
  1. il **livello di divisione** di ogni club e' scritto nel `<small>(N2)</small>`
     accanto al nome — proprio l'informazione che serve al perimetro deciso
     dall'utente («da dove entrano i club di seconda divisione»);
  2. i **rigori** sono in un campo separato (`score tab`), quindi il punteggio
     della partita non e' contaminato — l'errore che invece games.csv commette
     sulle altre cinque coppe (vedi `src/data/coppe.py`);
  3. la squadra **vincente** e' in grassetto, quindi la qualificazione e'
     verificabile contro il punteggio invece che dedotta.

PERIMETRO. Dal **7° turno** (`Septième tour`), che e' dove entrano i 18 club di
Ligue 2 — misurato sulla tabella «Calendrier» della pagina stessa, non assunto.
I turni regionali precedenti (1°-6°) restano fuori: sono migliaia di partite fra
club dilettantistici, nessuno dei quali incontra una squadra professionistica.

⚠️ **Quello che questa fonte NON da':** le formazioni. Wikipedia riporta i
titolari solo per la finale. Per la Coupe de France abbiamo quindi calendario,
risultato e divisione, ma **non** i titolari e le sostituzioni: e' un buco
dichiarato, non un buco nascosto (regola R6).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import requests

PAGINA = "Coupe de France de football 2025-2026"
API = "https://fr.wikipedia.org/w/api.php"
USER_AGENT = "PolymarketOracle/1.0 (ricerca calcistica; camarda.federico1@gmail.com)"

# Sezioni della pagina da cui si prendono le partite, in ordine di torneo.
# Il 7° turno e' il primo perche' e' dove entra la Ligue 2 (§ perimetro).
TURNI = [
    ("Septième tour", "7° turno"),
    ("Huitième tour", "8° turno"),
    ("Trente-deuxièmes de finale", "32esimi"),
    ("Seizièmes de finale", "16esimi"),
    ("Huitièmes de finale", "Ottavi"),
    ("Quarts de finale", "Quarti"),
    ("Demi-finales", "Semifinali"),
    ("Finale", "Finale"),
]

# Sigle di divisione usate da Wikipedia -> livello della piramide francese.
# L1/L2 sono professionistiche; N = National (3°), N2 (4°), N3 (5°),
# R1/R2/R3 = regionali (6° e sotto), D1/D2/D3 = distrettuali, più le leghe
# d'oltremare (che non hanno un livello nella piramide metropolitana).
LIVELLO_DIVISIONE = {
    "L1": 1, "L2": 2, "N": 3, "N1": 3, "N2": 4, "N3": 5,
    "R1": 6, "R2": 7, "R3": 8, "D1": 9, "D2": 10, "D3": 11,
}

MESI = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "décembre": 12,
}


@dataclass
class Partita:
    turno: str
    data: str | None
    casa: str
    ospite: str
    divisione_casa: str | None
    divisione_ospite: str | None
    livello_casa: int | None
    livello_ospite: int | None
    gol_casa: int | None
    gol_ospite: int | None
    rigori_casa: int | None
    rigori_ospite: int | None
    vincente: str | None
    stadio: str | None
    note: list[str] = field(default_factory=list)


def scarica_wikitext(pagina: str = PAGINA, sessione: requests.Session | None = None) -> str:
    """Il sorgente wiki della pagina. Una sola richiesta."""
    s = sessione or requests.Session()
    r = s.get(
        API,
        params={"action": "parse", "page": pagina, "prop": "wikitext", "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise LookupError(f"Wikipedia: {j['error'].get('info', 'pagina assente')}")
    return j["parse"]["wikitext"]["*"]


def _pulisci_nome(grezzo: str) -> tuple[str, str | None, bool]:
    """`[[Link|AS Le Gosier]] <small>(R1)</small>` -> (nome, divisione, vincente).

    Il grassetto marca la squadra qualificata: si legge PRIMA di toglierlo.
    """
    vincente = "'''" in grezzo
    div = None
    m = re.search(r"<small>\s*\(([^)]+)\)\s*</small>", grezzo)
    if m:
        div = m.group(1).strip()
    s = re.sub(r"<small>.*?</small>", " ", grezzo, flags=re.S)
    s = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", " ", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", " ", s)
    # [[Pagina|Etichetta]] -> Etichetta ; [[Pagina]] -> Pagina
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]|]+)\]\]", r"\1", s)
    s = s.replace("'''", "").replace("''", "")
    s = re.sub(r"\s+", " ", s).strip(" -–—\t")
    return s, div, vincente


def _data_iso(campo: str) -> str | None:
    """`{{Date|15|11|2025}}` o `15 novembre 2025` -> `2025-11-15`."""
    m = re.search(r"\{\{[Dd]ate\|(\d{1,2})\|(\d{1,2})\|(\d{4})", campo)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.search(r"\{\{[Dd]ate\|(\d{1,2})\|([a-zéûôA-Z]+)\|(\d{4})", campo)
    if m and m.group(2).lower() in MESI:
        return f"{int(m.group(3)):04d}-{MESI[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.search(r"(\d{1,2})\s+([a-zéûôA-Z]+)\s+(\d{4})", campo)
    if m and m.group(2).lower() in MESI:
        return f"{int(m.group(3)):04d}-{MESI[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return None


def _punteggio(campo: str) -> tuple[int | None, int | None]:
    """`2 - 3`, `2-3`, `2 – 3` -> (2, 3). Tutto il resto -> (None, None)."""
    s = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", " ", campo, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", " ", s)
    m = re.search(r"(\d+)\s*[-–—]\s*(\d+)", s)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def _campi_template(corpo: str) -> dict[str, str]:
    """Spacchetta `|chiave = valore` rispettando le parentesi annidate."""
    campi: dict[str, str] = {}
    prof_g = prof_q = 0
    pezzo: list[str] = []
    for ch in corpo:
        if ch == "|" and prof_g == 0 and prof_q == 0:
            pezzo_s = "".join(pezzo)
            if "=" in pezzo_s:
                k, v = pezzo_s.split("=", 1)
                campi[k.strip().lower()] = v.strip()
            pezzo = []
            continue
        if corpo[max(0, len("".join(pezzo)) - 1):] and ch == "{":
            prof_g += 1
        elif ch == "}":
            prof_g = max(0, prof_g - 1)
        elif ch == "[":
            prof_q += 1
        elif ch == "]":
            prof_q = max(0, prof_q - 1)
        pezzo.append(ch)
    pezzo_s = "".join(pezzo)
    if "=" in pezzo_s:
        k, v = pezzo_s.split("=", 1)
        campi[k.strip().lower()] = v.strip()
    return campi


def _trova_template(testo: str, nome: str = "Feuille de match") -> list[str]:
    """I corpi di tutti i `{{nome|...}}`, con annidamento corretto."""
    fuori: list[str] = []
    apri = f"{{{{{nome}"
    i = 0
    while True:
        j = testo.find(apri, i)
        if j < 0:
            return fuori
        k, prof = j + 2, 1
        while k < len(testo) - 1 and prof:
            if testo[k:k + 2] == "{{":
                prof += 1
                k += 2
                continue
            if testo[k:k + 2] == "}}":
                prof -= 1
                k += 2
                continue
            k += 1
        fuori.append(testo[j + 2:k - 2])
        i = k


def _sezioni(wikitext: str) -> dict[str, str]:
    """Testo di ogni sezione `== Titolo ==` / `=== Titolo ===` della pagina."""
    tagli = [(m.start(), m.group(2).strip(), len(m.group(1)))
             for m in re.finditer(r"^(={2,4})\s*(.+?)\s*=*\s*$", wikitext, re.M)]
    fuori: dict[str, str] = {}
    for n, (pos, titolo, liv) in enumerate(tagli):
        fine = len(wikitext)
        for pos2, _t2, liv2 in tagli[n + 1:]:
            if liv2 <= liv:
                fine = pos2
                break
        fuori[titolo] = wikitext[pos:fine]
    return fuori


def estrai_partite(wikitext: str) -> list[Partita]:
    """Tutte le partite dal 7° turno in poi, in ordine di torneo."""
    sez = _sezioni(wikitext)
    fuori: list[Partita] = []
    for titolo, etichetta in TURNI:
        corpo = sez.get(titolo)
        if corpo is None:
            corpo = next((v for k, v in sez.items() if k.startswith(titolo)), None)
        if corpo is None:
            continue
        for t in _trova_template(corpo):
            c = _campi_template(t)
            grezzo_c = c.get("équipe 1") or c.get("equipe 1") or ""
            grezzo_o = c.get("équipe 2") or c.get("equipe 2") or ""
            if not grezzo_c or not grezzo_o:
                continue
            casa, div_c, vinta_c = _pulisci_nome(grezzo_c)
            osp, div_o, vinta_o = _pulisci_nome(grezzo_o)
            gc, go = _punteggio(c.get("score", ""))
            rc, ro = _punteggio(c.get("score tab", ""))
            stadio = c.get("stade", "") or None
            if stadio:
                stadio, _, _ = _pulisci_nome(stadio)
            fuori.append(Partita(
                turno=etichetta, data=_data_iso(c.get("date", "")),
                casa=casa, ospite=osp,
                divisione_casa=div_c, divisione_ospite=div_o,
                livello_casa=LIVELLO_DIVISIONE.get((div_c or "").upper()),
                livello_ospite=LIVELLO_DIVISIONE.get((div_o or "").upper()),
                gol_casa=gc, gol_ospite=go, rigori_casa=rc, rigori_ospite=ro,
                vincente=(casa if vinta_c else (osp if vinta_o else None)),
                stadio=stadio or None,
            ))
    return fuori


def verifica(partite: list[Partita]) -> dict[str, object]:
    """Controlli di coerenza: il grassetto deve concordare col punteggio.

    Non e' decorazione. Il vincente (grassetto) e il punteggio sono due
    informazioni SCRITTE SEPARATAMENTE nella stessa fonte: se concordano, la
    lettura del template e' corretta; se divergono, o abbiamo letto male noi o
    la pagina e' incoerente — in entrambi i casi va dichiarato, non ignorato.
    """
    incoerenti = []
    for p in partite:
        if p.vincente is None or p.gol_casa is None:
            continue
        if p.rigori_casa is not None:
            atteso = p.casa if p.rigori_casa > p.rigori_ospite else p.ospite
        elif p.gol_casa != p.gol_ospite:
            atteso = p.casa if p.gol_casa > p.gol_ospite else p.ospite
        else:
            continue  # pari senza rigori dichiarati: nulla da verificare
        if atteso != p.vincente:
            incoerenti.append(f"{p.turno}: {p.casa} {p.gol_casa}-{p.gol_ospite} "
                              f"{p.ospite} (grassetto su «{p.vincente}»)")
    return {
        "partite": len(partite),
        "con_punteggio": sum(p.gol_casa is not None for p in partite),
        "con_rigori": sum(p.rigori_casa is not None for p in partite),
        "con_data": sum(p.data is not None for p in partite),
        "con_divisione_entrambe": sum(
            p.divisione_casa is not None and p.divisione_ospite is not None
            for p in partite),
        "incoerenti": incoerenti,
    }
