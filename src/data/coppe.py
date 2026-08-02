"""Coppe nazionali 2025-26: risultati, formazioni, sostituzioni.

Copre le cinque coppe che il dataset player-scores (Transfermarkt) contiene —
Coppa Italia, FA Cup, EFL Cup (Carabao), Copa del Rey, DFB-Pokal. La sesta, la
**Coupe de France**, non e' in quel dataset e vive in `coupe_de_france.py`.

---------------------------------------------------------------------------
⚠️ IL PUNTEGGIO DI `games.csv` NON E' IL PUNTEGGIO DELLA PARTITA
---------------------------------------------------------------------------
E' il fatto piu' importante di questo modulo, ed e' esattamente la trappola
gia' pagata dal progetto e registrata in docs/PIANO_DATABASE_GIOCATORI.md
(«Chemnitzer-Mainz, DFB-Pokal 2014 | **10-9** | 5-5 dopo i supplementari, poi
5-4 ai rigori (**somma dei due**)»). Nella stagione 2025-26 lo stesso difetto
tocca **68 partite su 458 (14,8%)**:

    Eintracht Braunschweig v VfB Stuttgart   games.csv: 11-12

La partita e' finita **4-4** dopo i supplementari, e lo Stuttgart ha vinto
**8-7** ai rigori. `home_club_goals` somma i due. Un 11-12 non e' un dato
mancante — e' un **finto pieno** (regola R6): sembra un punteggio, si comporta
come un punteggio, e sballerebbe qualunque modello sui gol.

**La ricostruzione**, verificata contro una fonte esterna e indipendente
(openfootball, che scrive `7-8 pen. 4-4 a.e.t. (3-3, 1-1)` per quella partita):

    gol_casa(t)  = numero di eventi `Goals` con `club_id == casa` e `minute <= t`
    rigori_casa  = home_club_goals - gol_casa(∞)

Due dettagli che NON si potevano indovinare e sono stati misurati:

1. **Gli autogol sono gia' attribuiti alla squadra che ne BENEFICIA**, non a
   quella del giocatore. Contarli al contrario faceva scendere la ricostruzione
   dal 98,5% al 89,7%: e' cosi' che l'ipotesi sbagliata e' stata scartata.
2. **I rigori si ricavano per sottrazione, non si contano.** La sequenza in
   `game_events` e' **troncata**: in Grimsby-Manchester United sono registrati
   23 tiri, ma i rigori veri furono 12-11 (25+). Il totale di `games.csv`, per
   quanto contaminato, e' piu' completo della sequenza — quindi la sottrazione
   e' la stima buona e il conteggio no.

Resa misurata: **448/458 partite (97,8%)** ricomposte esattamente. I 10 residui
sono dichiarati riga per riga (`eventi_incompleti`), non nascosti: 9 sono turni
preliminari dilettantistici di Copa del Rey dove manca anche il nome di un club.

**Controprova esterna:** sulle 42 partite di DFB-Pokal che openfootball copre e
che si riescono ad appaiare, la ricostruzione coincide **42/42 su ognuno dei sei
campi** (90' casa e ospite, finale casa e ospite, rigori casa e ospite). Zero
divergenze. E' la verifica che rende la ricostruzione un fatto e non un'ipotesi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd
import requests

# competition_id di player-scores -> nome leggibile + lega di riferimento
COPPE: dict[str, tuple[str, str]] = {
    "CIT": ("Coppa Italia", "serie_a"),
    "FAC": ("FA Cup", "premier_league"),
    "CGB": ("EFL Cup", "premier_league"),
    "CDR": ("Copa del Rey", "la_liga"),
    "DFB": ("DFB-Pokal", "bundesliga"),
}

# Turno in cui entrano i club di SECONDA divisione — il perimetro deciso
# dall'utente il 02/08/2026. NON e' una costante di formato copiata da
# Wikipedia: e' misurata sui dati (primo turno in cui compare un club che
# football-data elenca nella seconda divisione 2025-26 di quel paese).
TURNO_INGRESSO_SECONDA: dict[str, str] = {
    "CIT": "Qualifying Round",
    "FAC": "Third Round",
    "CGB": "First Round",
    "CDR": "First Round",
    "DFB": "First Round",
}

STAGIONE = 2025  # `season` di player-scores per la stagione 2025-26


@dataclass(frozen=True)
class Punteggio:
    """Il punteggio di una partita di coppa, nei quattro pezzi che servono."""

    gol_casa_90: int
    gol_ospite_90: int
    gol_casa_finale: int   # dopo eventuali supplementari
    gol_ospite_finale: int
    rigori_casa: int | None
    rigori_ospite: int | None
    supplementari: bool
    eventi_incompleti: bool


def _conta(gol: pd.DataFrame, club_id: int, fino: int | None = None) -> int:
    x = gol if fino is None else gol[gol["minute"] <= fino]
    return int((x["club_id"] == club_id).sum())


def ricostruisci_punteggio(
    partita: pd.Series, eventi_partita: pd.DataFrame
) -> Punteggio:
    """Il punteggio VERO di una partita, dai suoi eventi.

    `partita` e' una riga di `games.csv`; `eventi_partita` sono le righe di
    `game_events.csv` di quella sola partita.
    """
    casa, ospite = int(partita["home_club_id"]), int(partita["away_club_id"])
    gol = eventi_partita[eventi_partita["type"] == "Goals"]
    ha_rigori = (eventi_partita["type"] == "Shootout").any()

    c90, o90 = _conta(gol, casa, 90), _conta(gol, ospite, 90)
    cfin, ofin = _conta(gol, casa), _conta(gol, ospite)

    dc = int(partita["home_club_goals"])
    do = int(partita["away_club_goals"])
    rc = ro = None
    incompleti = False
    if ha_rigori:
        rc, ro = dc - cfin, do - ofin
        # una sequenza di rigori non puo' essere negativa ne' pari:
        # se lo e', la sottrazione non regge e va dichiarata.
        if rc < 0 or ro < 0 or rc == ro:
            rc = ro = None
            incompleti = True
    elif (dc, do) != (cfin, ofin):
        incompleti = True

    return Punteggio(
        gol_casa_90=c90, gol_ospite_90=o90,
        gol_casa_finale=cfin, gol_ospite_finale=ofin,
        rigori_casa=rc, rigori_ospite=ro,
        supplementari=bool((gol["minute"] > 90).any()),
        eventi_incompleti=incompleti,
    )


# --------------------------------------------------------------------------- #
# openfootball: la verifica ESTERNA e indipendente
# --------------------------------------------------------------------------- #
# Formato riga (repo openfootball/deutschland, file `<stagione>/cup.txt`):
#     17:00  SG Sonnenhof Großaspach v Bayer Leverkusen  0-4 (0-1)
#     19:45  Eintracht Braunschweig  v VfB Stuttgart     7-8 pen. 4-4 a.e.t. (3-3, 1-1)
#            FK Pirmasens            v Hamburger SV      1-2 a.e.t. (1-1, 0-0)
# cioe': [rigori pen.] risultato_finale [a.e.t.] (novantesimo[, primo tempo])
# ⚠️ la separazione fra le due squadre e' ` v `, con UNO spazio quando il nome
# di casa e' lungo abbastanza da mangiarsi l'allineamento a colonne
# («SG Sonnenhof Großaspach v Bayer Leverkusen»). Pretendere due spazi faceva
# saltare in silenzio proprio le squadre dal nome lungo — 16 partite su 63.
_RIGA = re.compile(
    r"^\s+(?:\d\d:\d\d\s+)?(?P<casa>\S.*?)\s+v\s+(?P<ospite>\S.*?)\s{2,}"
    r"(?:(?P<rc>\d+)-(?P<ro>\d+)\s+pen\.\s+)?"
    r"(?P<gc>\d+)-(?P<go>\d+)"
    r"(?P<aet>\s+a\.e\.t\.)?"
    r"(?:\s*\((?P<p1>\d+)-(?P<p2>\d+)(?:,\s*(?P<h1>\d+)-(?P<h2>\d+))?\))?"
)
_TURNO = re.compile(r"^▪\s*(.+?)\s*$")


def leggi_openfootball(testo: str) -> pd.DataFrame:
    """Le partite di un file `cup.txt` di openfootball, coi punteggi separati.

    Rende le colonne: turno, casa, ospite, gol_casa_ht/gol_ospite_ht,
    gol_casa_90/gol_ospite_90, gol_casa_finale/gol_ospite_finale,
    rigori_casa/rigori_ospite, supplementari.
    """
    righe, turno = [], None
    for linea in testo.splitlines():
        t = _TURNO.match(linea)
        if t:
            turno = t.group(1)
            continue
        m = _RIGA.match(linea)
        if not m:
            continue
        d = m.groupdict()
        aet = d["aet"] is not None
        # il gruppo (a-b) e' il 90' quando c'e' l'a.e.t., altrimenti e' il
        # primo tempo: e' la stessa parentesi con due significati, e leggerla
        # al contrario e' l'errore facile.
        if aet:
            g90 = (int(d["p1"]), int(d["p2"])) if d["p1"] else (None, None)
            ht = (int(d["h1"]), int(d["h2"])) if d["h1"] else (None, None)
        else:
            g90 = (int(d["gc"]), int(d["go"]))
            ht = (int(d["p1"]), int(d["p2"])) if d["p1"] else (None, None)
        righe.append({
            "turno": turno,
            "casa": d["casa"].strip(), "ospite": d["ospite"].strip(),
            "gol_casa_ht": ht[0], "gol_ospite_ht": ht[1],
            "gol_casa_90": g90[0], "gol_ospite_90": g90[1],
            "gol_casa_finale": int(d["gc"]), "gol_ospite_finale": int(d["go"]),
            "rigori_casa": int(d["rc"]) if d["rc"] else None,
            "rigori_ospite": int(d["ro"]) if d["ro"] else None,
            "supplementari": aet,
        })
    return pd.DataFrame(righe)


# --------------------------------------------------------------------------- #
# le tre finali che il dataset NON ha
# --------------------------------------------------------------------------- #
# Misurato il 02/08/2026: `games.csv` contiene la finale di Copa del Rey e
# quella di EFL Cup, ma NON quelle di Coppa Italia, FA Cup e DFB-Pokal — pur
# avendo 846 partite di maggio 2026 in altre competizioni. Non e' un taglio
# temporale del dataset: e' un'assenza puntuale. Le tre finali si prendono da
# Wikipedia, dove vivono in una pagina dedicata con un'infobox strutturata.
FINALI_MANCANTI: dict[str, tuple[str, str]] = {
    "CIT": ("2026 Coppa Italia final", "Coppa Italia"),
    "FAC": ("2026 FA Cup final", "FA Cup"),
    "DFB": ("2026 DFB-Pokal final", "DFB-Pokal"),
}

_INFOBOX = re.compile(r"\{\{\s*Infobox football match\b", re.I)


def _corpo_infobox(wikitext: str) -> str:
    """Il corpo dell'infobox, con annidamento corretto.

    Serve leggere QUESTO e non tutto il wikitext: campi come `date` o
    `referee` compaiono anche dentro i `{{cite web}}` delle note, e una
    ricerca ingenua prende il primo che capita — che è quello sbagliato.
    """
    m = _INFOBOX.search(wikitext)
    if not m:
        return ""
    i, prof = m.start() + 2, 1
    while i < len(wikitext) - 1 and prof:
        if wikitext[i:i + 2] == "{{":
            prof += 1
            i += 2
            continue
        if wikitext[i:i + 2] == "}}":
            prof -= 1
            i += 2
            continue
        i += 1
    return wikitext[m.start() + 2:i - 2]


def _campo(corpo: str, nome: str) -> str | None:
    """Il valore di `|nome = ...` al primo livello dell'infobox."""
    m = re.search(rf"(?:^|\n)\s*\|\s*{nome}\s*=\s*(.*?)(?=\n\s*\|\s*\w|\Z)",
                  corpo, re.S)
    if not m:
        return None
    v = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", " ", m.group(1), flags=re.S)
    v = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]|]+)\]\]", r"\1", v)
    v = re.sub(r"\{\{[^{}]*\}\}", " ", v)
    v = v.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", v).strip() or None


def leggi_finale_wikipedia(pagina: str, sessione: requests.Session | None = None) -> dict:
    """Una finale di coppa dalla sua pagina Wikipedia (inglese)."""
    s = sessione or requests.Session()
    r = s.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "parse", "page": pagina, "prop": "wikitext",
                "format": "json"},
        headers={"User-Agent": "PolymarketOracle/1.0 (ricerca calcistica; "
                               "camarda.federico1@gmail.com)"},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise LookupError(f"Wikipedia: {j['error'].get('info', pagina)}")
    w = j["parse"]["wikitext"]["*"]
    corpo = _corpo_infobox(w)

    # ⚠️ nell'infobox `Infobox football match` il punteggio NON sta in un campo
    # `score`: sta in `team1score`/`team2score`. Un `| score = 0–2` esiste piu'
    # in basso nella pagina, dentro il `{{Football box}}` del riepilogo — ed e'
    # la trappola: una ricerca su tutto il wikitext lo trova e sembra giusta,
    # ma legge un template diverso da quello che sta leggendo per gli altri
    # campi. Qui si legge un solo template, per intero.
    def _num(nome: str) -> int | None:
        v = _campo(corpo, nome)
        m = re.search(r"\d+", v) if v else None
        return int(m.group(0)) if m else None

    gc, go = _num("team1score"), _num("team2score")
    rc, ro = _num("penaltyscore1"), _num("penaltyscore2")

    data = None
    md = re.search(r"\{\{\s*[Ss]tart date\|(\d{4})\|(\d{1,2})\|(\d{1,2})", w)
    if md:
        data = f"{int(md.group(1)):04d}-{int(md.group(2)):02d}-{int(md.group(3)):02d}"

    spett = (_campo(corpo, "attendance") or "").replace(",", "").replace(".", "")
    ms = re.search(r"\d+", spett)

    return {
        "casa": _campo(corpo, "team1"), "ospite": _campo(corpo, "team2"),
        "gol_casa": gc, "gol_ospite": go,
        "rigori_casa": rc, "rigori_ospite": ro,
        "data": data,
        "stadio": _campo(corpo, "stadium"), "citta": _campo(corpo, "city"),
        "arbitro": _campo(corpo, "referee"),
        "spettatori": int(ms.group(0)) if ms else None,
        "pagina": pagina,
    }
