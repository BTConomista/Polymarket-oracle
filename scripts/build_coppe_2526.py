#!/usr/bin/env python3
"""Costruisce la raccolta delle COPPE NAZIONALI 2025-26 (6 tornei, 5 paesi).

PERCHE' ESISTE. Decisione utente del 02/08/2026: prima delle coppe europee e
delle nazionali si parte dalle **coppe nazionali**, stagione 2025-26, con il
perimetro «da dove entrano i club di SECONDA divisione» — perche' i club che
oggi sono in seconda domani sono in prima, e viceversa. Il risultato serve
anche da **controparte automatica** alla raccolta manuale diretta.it: due fonti
indipendenti sulla stessa partita sono l'unico modo per accorgersi di un errore
in una delle due (regola R5, passo 2).

LE TRE FONTI, e perche' tre e non una:

  A. **player-scores** (Transfermarkt, Kaggle `davidcariboo/player-scores`) —
     l'ossatura: 5 coppe su 6, con formazioni, panchina, sostituzioni al minuto,
     gol, cartellini, arbitro, allenatore, modulo, spettatori.
     ⚠️ il suo punteggio e' contaminato dai rigori: vedi `src/data/coppe.py`.
  B. **openfootball** (`deutschland/2025-26/cup.txt`) — verifica ESTERNA e
     indipendente sulla DFB-Pokal, l'unico paese per cui il 2025-26 esiste.
     E' l'unica fonte che scrive i quattro pezzi separati (primo tempo, 90',
     supplementari, rigori), quindi e' anche il metro con cui la ricostruzione
     di (A) e' stata validata.
  C. **Wikipedia FR** — la Coupe de France, che (A) non contiene affatto.

COSA PRODUCE, in `data/coppe_2526/`:
  partite.csv     una riga per partita: data, turno, squadre, punteggio nei
                  quattro pezzi, divisione di ciascuna squadra, arbitro,
                  allenatori, modulo, stadio, spettatori
  formazioni.csv  una riga per giocatore-partita: titolare/panchina, ruolo,
                  numero, capitano, minuti giocati, gol, assist, cartellini
  eventi.csv      una riga per evento: sostituzioni/gol/cartellini col minuto
  manifesto.json  provenienza, versioni, conteggi e TUTTI i controlli

USO:
    python scripts/build_coppe_2526.py            # scarica e costruisce
    python scripts/build_coppe_2526.py --verifica # solo i controlli, non scrive
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from src.data.club_matching import Agganciatore  # noqa: E402
from src.data.coppe import (  # noqa: E402
    COPPE,
    applica_date_corrette,
    FINALI_MANCANTI,
    STAGIONE,
    TURNO_INGRESSO_SECONDA,
    leggi_finale_wikipedia,
    leggi_openfootball,
    ricostruisci_punteggio,
)
from src.data.coupe_de_france import (  # noqa: E402
    estrai_partite as cdf_partite,
    scarica_wikitext as cdf_wikitext,
    verifica as cdf_verifica,
)

USCITA = RADICE / "data" / "coppe_2526"
DATASET = "davidcariboo/player-scores"
OPENFOOTBALL_DFB = (
    "https://raw.githubusercontent.com/openfootball/deutschland/master/2025-26/cup.txt"
)
FOOTBALL_DATA = "https://www.football-data.co.uk/mmz4281/2526/{}.csv"

# seconda divisione per paese su football-data, e prima divisione nel registro
SECONDA_DIVISIONE = {"IT": "I2", "EN": "E1", "ES": "SP2", "DE": "D2"}
PAESE_COPPA = {"CIT": "IT", "FAC": "EN", "CGB": "EN", "CDR": "ES", "DFB": "DE"}


def _log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# fonte A — player-scores
# --------------------------------------------------------------------------- #
def scarica_player_scores() -> Path:
    import kagglehub

    p = Path(kagglehub.dataset_download(DATASET))
    _log(f"  player-scores: {p}")
    return p


def livelli_divisione(ag: Agganciatore) -> tuple[dict[str, set[int]], dict[str, set[int]], dict]:
    """`club_id` di prima e seconda divisione 2025-26, per paese.

    ⚠️ La prima divisione NON puo' venire da `club_names.domestic_competition_id`:
    quel campo marca **chiunque sia mai stato** in quella lega nella storia del
    dataset. Sono 37 club per `GB1` — Wigan, Reading, QPR, Huddersfield, West
    Brom — tutti oggi in divisioni inferiori. Usarlo faceva risultare **Wigan
    Athletic in prima divisione** nel 2025-26, cioe' esattamente il tipo di
    finto pieno che la regola R6 impone di cercare: un valore plausibile, di
    formato giusto, e sbagliato.

    La fonte corretta ce l'abbiamo in casa: gli **snapshot congelati** delle
    cinque leghe, filtrati sulla stagione 2526. La seconda divisione viene da
    football-data.co.uk, che e' l'unica fonte raggiungibile che la elenchi per
    tutti i paesi che servono.
    """
    snapshot = {"IT": "serie_a", "EN": "premier_league", "ES": "la_liga",
                "DE": "bundesliga", "FR": "ligue_1"}
    primi = {}
    for paese, lega in snapshot.items():
        d = pd.read_csv(RADICE / "data" / f"{lega}_matches.csv")
        d = d[d.season == 2526]
        nomi = sorted(set(d.home_team) | set(d.away_team))
        agganci = {n: ag.aggancia(n) for n in nomi}
        primi[paese] = {v for v in agganci.values() if v is not None}
        mancanti = [n for n, v in agganci.items() if v is None]
        _log(f"  1a divisione {paese}: {len(primi[paese])}/{len(nomi)} agganciati"
             + (f"  MANCANO: {', '.join(mancanti)}" if mancanti else ""))
        if mancanti:
            raise LookupError(
                f"prima divisione {paese}: {len(mancanti)} club senza aggancio "
                f"({', '.join(mancanti)}). Un club di prima divisione non "
                f"agganciato verrebbe marcato «terza o sotto»: aggiungere "
                f"l'alias in src/data/club_matching.ALIAS prima di procedere."
            )
    secondi, resa = {}, {}
    for paese, codice in SECONDA_DIVISIONE.items():
        r = requests.get(FOOTBALL_DATA.format(codice), timeout=60)
        r.raise_for_status()
        testo = r.content.decode("utf-8", errors="replace")
        d = pd.read_csv(pd.io.common.StringIO(testo), on_bad_lines="skip")
        nomi = sorted(set(d.HomeTeam.dropna()) | set(d.AwayTeam.dropna()))
        agganci = {n: ag.aggancia(n) for n in nomi}
        secondi[paese] = {v for v in agganci.values() if v is not None}
        resa[paese] = {
            "club_elencati": len(nomi),
            "agganciati": len(secondi[paese]),
            "non_agganciati": sorted(n for n, v in agganci.items() if v is None),
        }
        _log(f"  2a divisione {paese} ({codice}): "
             f"{len(secondi[paese])}/{len(nomi)} agganciati")
    return primi, secondi, resa


def costruisci_da_player_scores(base: Path, ag: Agganciatore) -> tuple[pd.DataFrame, ...]:
    games = pd.read_csv(base / "games.csv")
    s = games[(games.season == STAGIONE)
              & (games.competition_id.isin(COPPE))].copy()
    s["date"] = pd.to_datetime(s.date)
    s, date_corrette = applica_date_corrette(s)
    for c in date_corrette:
        _log(f"  data corretta: {c['competizione']} {c['da']} -> {c['a']} "
             f"(club {c['home_club_id']}, {c['righe']} riga/e)")
    ids = set(s.game_id)
    _log(f"  partite di coppa 2025-26: {len(s)}")

    eventi = pd.read_csv(base / "game_events.csv")
    eventi = eventi[eventi.game_id.isin(ids)].copy()
    lineup = pd.read_csv(base / "game_lineups.csv", low_memory=False)
    lineup = lineup[lineup.game_id.isin(ids)].copy()
    pres = pd.read_csv(base / "appearances.csv")
    pres = pres[pres.game_id.isin(ids)].copy()

    primi, secondi, resa = livelli_divisione(ag)

    def livello(cid, paese):
        if cid in primi.get(paese, ()):
            return 1
        if cid in secondi.get(paese, ()):
            return 2
        return 3  # terza divisione o sotto — il registro non li distingue

    per_partita = {g: d for g, d in eventi.groupby("game_id")}
    righe = []
    for _, r in s.iterrows():
        paese = PAESE_COPPA[r.competition_id]
        ev = per_partita.get(r.game_id, eventi.iloc[0:0])
        p = ricostruisci_punteggio(r, ev)
        righe.append({
            "competizione": COPPE[r.competition_id][0],
            "paese": paese,
            "turno": r["round"],
            "data": r.date.date().isoformat(),
            "casa": r.home_club_name,
            "ospite": r.away_club_name,
            "gol_casa_90": p.gol_casa_90, "gol_ospite_90": p.gol_ospite_90,
            "gol_casa_finale": p.gol_casa_finale,
            "gol_ospite_finale": p.gol_ospite_finale,
            "rigori_casa": p.rigori_casa, "rigori_ospite": p.rigori_ospite,
            "supplementari": p.supplementari,
            "gol_casa_dichiarato": r.home_club_goals,
            "gol_ospite_dichiarato": r.away_club_goals,
            "eventi_incompleti": p.eventi_incompleti,
            "divisione_casa": livello(r.home_club_id, paese),
            "divisione_ospite": livello(r.away_club_id, paese),
            "dentro_perimetro": None,  # riempito sotto
            "arbitro": r.referee, "stadio": r.stadium, "spettatori": r.attendance,
            "allenatore_casa": r.home_club_manager_name,
            "allenatore_ospite": r.away_club_manager_name,
            "modulo_casa": r.home_club_formation,
            "modulo_ospite": r.away_club_formation,
            "game_id": r.game_id, "competition_id": r.competition_id,
            "home_club_id": r.home_club_id, "away_club_id": r.away_club_id,
            "fonte": "player-scores", "url": r.url,
        })
    partite = pd.DataFrame(righe)

    # perimetro: dal turno in cui entra la seconda divisione, per coppa
    inizio = {}
    for cid in COPPE:
        x = partite[partite.competition_id == cid]
        con2 = x[(x.divisione_casa == 2) | (x.divisione_ospite == 2)]
        inizio[cid] = con2.data.min() if len(con2) else None
    partite["dentro_perimetro"] = [
        inizio[c] is not None and d >= inizio[c]
        for c, d in zip(partite.competition_id, partite.data)
    ]

    # --- formazioni: titolari/panchina + minuti effettivamente giocati
    minuti = pres[["game_id", "player_id", "minutes_played", "goals",
                   "assists", "yellow_cards", "red_cards"]]
    f = lineup.merge(minuti, on=["game_id", "player_id"], how="left")
    f = f.rename(columns={
        "player_name": "giocatore", "club_id": "club_id", "type": "ruolo_partita",
        "position": "posizione", "number": "numero",
        "team_captain": "capitano", "minutes_played": "minuti",
        "goals": "gol", "assists": "assist",
        "yellow_cards": "gialli", "red_cards": "rossi",
    })
    f["ruolo_partita"] = f.ruolo_partita.map(
        {"starting_lineup": "titolare", "substitutes": "panchina"}
    ).fillna(f.ruolo_partita)
    chiave = partite.set_index("game_id")[["competizione", "turno", "data"]]
    f = f.join(chiave, on="game_id")
    formazioni = f[["competizione", "turno", "data", "game_id", "club_id",
                    "giocatore", "player_id", "ruolo_partita", "posizione",
                    "numero", "capitano", "minuti", "gol", "assist",
                    "gialli", "rossi"]]

    e = eventi.rename(columns={
        "type": "tipo", "minute": "minuto", "club_name": "club",
        "description": "descrizione", "player_id": "giocatore_id",
        "player_in_id": "entrato_id", "player_assist_id": "assist_id",
    })
    e = e.join(chiave, on="game_id")
    eventi_out = e[["competizione", "turno", "data", "game_id", "minuto",
                    "tipo", "club", "club_id", "giocatore_id", "entrato_id",
                    "assist_id", "descrizione"]].sort_values(
        ["game_id", "minuto"])

    return partite, formazioni, eventi_out, resa, inizio, date_corrette


# --------------------------------------------------------------------------- #
# fonte B — openfootball, la verifica esterna
# --------------------------------------------------------------------------- #
def verifica_dfb(partite: pd.DataFrame, ag: Agganciatore) -> dict:
    """Confronta la DFB-Pokal ricostruita con openfootball, partita per partita."""
    testo = requests.get(OPENFOOTBALL_DFB, timeout=60).text
    of = leggi_openfootball(testo)
    _log(f"  openfootball DFB-Pokal: {len(of)} partite lette")

    nostre = partite[partite.competition_id == "DFB"].copy()
    of["id_casa"] = [ag.aggancia(n) for n in of.casa]
    of["id_ospite"] = [ag.aggancia(n) for n in of.ospite]
    of = of.dropna(subset=["id_casa", "id_ospite"])

    m = nostre.merge(of, left_on=["home_club_id", "away_club_id"],
                     right_on=["id_casa", "id_ospite"],
                     suffixes=("", "_of"))
    confronti = {}
    for campo in ["gol_casa_90", "gol_ospite_90", "gol_casa_finale",
                  "gol_ospite_finale", "rigori_casa", "rigori_ospite"]:
        a, b = m[campo], m[f"{campo}_of"]
        entrambi = a.notna() & b.notna()
        confronti[campo] = {
            "confrontabili": int(entrambi.sum()),
            "uguali": int((a[entrambi] == b[entrambi]).sum()),
        }
    divergenti = m[(m.gol_casa_finale != m.gol_casa_finale_of)
                   | (m.gol_ospite_finale != m.gol_ospite_finale_of)]
    return {
        "partite_openfootball": int(len(of)),
        "partite_nostre_dfb": int(len(nostre)),
        "appaiate": int(len(m)),
        "confronti": confronti,
        "divergenti": divergenti[["casa", "ospite", "gol_casa_finale",
                                  "gol_ospite_finale", "gol_casa_finale_of",
                                  "gol_ospite_finale_of"]].to_dict("records"),
        "solo_in_openfootball": int(len(of) - len(m)),
    }


# --------------------------------------------------------------------------- #
# fonte C — Coupe de France
# --------------------------------------------------------------------------- #
def costruisci_coupe_de_france() -> tuple[pd.DataFrame, dict]:
    w = cdf_wikitext()
    p = cdf_partite(w)
    v = cdf_verifica(p)
    _log(f"  Coupe de France: {len(p)} partite dal 7° turno")
    d = pd.DataFrame([{
        "competizione": "Coupe de France", "paese": "FR", "turno": x.turno,
        "data": x.data, "casa": x.casa, "ospite": x.ospite,
        "gol_casa_90": None, "gol_ospite_90": None,
        "gol_casa_finale": x.gol_casa, "gol_ospite_finale": x.gol_ospite,
        "rigori_casa": x.rigori_casa, "rigori_ospite": x.rigori_ospite,
        "supplementari": None,
        "gol_casa_dichiarato": x.gol_casa, "gol_ospite_dichiarato": x.gol_ospite,
        "eventi_incompleti": False,
        "divisione_casa": x.livello_casa, "divisione_ospite": x.livello_ospite,
        "dentro_perimetro": True,
        "sigla_divisione_casa": x.divisione_casa,
        "sigla_divisione_ospite": x.divisione_ospite,
        "arbitro": None, "stadio": x.stadio, "spettatori": None,
        "allenatore_casa": None, "allenatore_ospite": None,
        "modulo_casa": None, "modulo_ospite": None,
        "game_id": None, "competition_id": "CDF",
        "home_club_id": None, "away_club_id": None,
        "fonte": "wikipedia-fr", "url": None,
    } for x in p])
    return d, v


def costruisci_finali_mancanti(ag: Agganciatore) -> tuple[pd.DataFrame, list[dict]]:
    """Le tre finali che `games.csv` non contiene (Coppa Italia, FA Cup, Pokal).

    ⚠️ I `club_id` si risolvono QUI. Lasciarli vuoti sembra innocuo — il nome
    della squadra c'e' — ma rende le tre finali invisibili a ogni join che usi
    gli identificatori invece dei nomi, che e' la strada giusta ovunque.
    """
    s = requests.Session()
    # Wikipedia scrive i nomi in inglese e in forma breve: servono gli alias.
    alias = {"Internazionale": "Inter Milan", "Lazio": "SS Lazio",
             "Chelsea": "Chelsea FC", "Manchester City": "Manchester City",
             "Bayern Munich": "Bayern Munich", "VfB Stuttgart": "VfB Stuttgart"}
    righe, quadro = [], []
    for cid, (pagina, nome) in FINALI_MANCANTI.items():
        f = leggi_finale_wikipedia(pagina, sessione=s)
        quadro.append({"competizione": nome, **f})
        _log(f"  finale {nome}: {f['casa']} {f['gol_casa']}-{f['gol_ospite']} "
             f"{f['ospite']} ({f['data']})")
        righe.append({
            "competizione": nome, "paese": PAESE_COPPA[cid], "turno": "Final",
            "data": f["data"], "casa": f["casa"], "ospite": f["ospite"],
            "gol_casa_90": None, "gol_ospite_90": None,
            "gol_casa_finale": f["gol_casa"], "gol_ospite_finale": f["gol_ospite"],
            "rigori_casa": f["rigori_casa"], "rigori_ospite": f["rigori_ospite"],
            "supplementari": None,
            "gol_casa_dichiarato": f["gol_casa"],
            "gol_ospite_dichiarato": f["gol_ospite"],
            "eventi_incompleti": False,
            "divisione_casa": 1, "divisione_ospite": 1,
            "dentro_perimetro": True,
            "arbitro": f["arbitro"], "stadio": f["stadio"],
            "spettatori": f["spettatori"],
            "allenatore_casa": None, "allenatore_ospite": None,
            "modulo_casa": None, "modulo_ospite": None,
            "game_id": None, "competition_id": cid,
            "home_club_id": ag.aggancia(alias.get(f["casa"], f["casa"])),
            "away_club_id": ag.aggancia(alias.get(f["ospite"], f["ospite"])),
            "fonte": "wikipedia-en", "url": None,
        })
    return pd.DataFrame(righe), quadro


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verifica", action="store_true",
                    help="esegue tutti i controlli senza scrivere i file")
    args = ap.parse_args()

    _log("== A. player-scores")
    base = scarica_player_scores()
    ag = Agganciatore()
    partite, formazioni, eventi, resa2a, inizio, date_corrette = costruisci_da_player_scores(base, ag)

    _log("== B. openfootball (verifica esterna DFB-Pokal)")
    controllo = verifica_dfb(partite, ag)

    _log("== C. Coupe de France (Wikipedia)")
    cdf, cdf_v = costruisci_coupe_de_france()

    _log("== D. le tre finali assenti da games.csv (Wikipedia)")
    finali, finali_q = costruisci_finali_mancanti(ag)

    tutte = pd.concat([partite, finali, cdf], ignore_index=True)
    tutte = tutte.sort_values(["competizione", "data", "casa"],
                              na_position="last").reset_index(drop=True)

    quadro = {
        "generato": date.today().isoformat(),
        "fonti": {
            "player_scores": {"dataset": DATASET, "cartella": str(base)},
            "openfootball": OPENFOOTBALL_DFB,
            "wikipedia": "fr:Coupe de France de football 2025-2026",
            "football_data": FOOTBALL_DATA.format("<codice>"),
        },
        "partite_totali": int(len(tutte)),
        "per_competizione": {
            k: {
                "partite": int(v),
                "turno_ingresso_seconda_divisione":
                    TURNO_INGRESSO_SECONDA.get(
                        tutte.loc[tutte.competizione == k, "competition_id"].iloc[0],
                        "7° turno"),
                "dentro_perimetro":
                    int(tutte[(tutte.competizione == k) & tutte.dentro_perimetro].shape[0]),
            }
            for k, v in tutte.competizione.value_counts().items()
        },
        "formazioni": {
            "righe": int(len(formazioni)),
            "partite_coperte": int(formazioni.game_id.nunique()),
            "titolari": int((formazioni.ruolo_partita == "titolare").sum()),
            "panchina": int((formazioni.ruolo_partita == "panchina").sum()),
        },
        "eventi": {
            "righe": int(len(eventi)),
            "per_tipo": {k: int(v) for k, v in eventi.tipo.value_counts().items()},
        },
        "punteggio": {
            "partite_con_rigori": int(partite.rigori_casa.notna().sum()),
            "partite_con_supplementari": int(partite.supplementari.sum()),
            # quante volte il punteggio di games.csv diverge da quello vero.
            # Le due voci sotto lo spiegano: la stragrande maggioranza e' la
            # contaminazione da rigori, il resto sono eventi mancanti.
            "dichiarato_diverso_dal_ricostruito": int(
                ((partite.gol_casa_dichiarato != partite.gol_casa_finale)
                 | (partite.gol_ospite_dichiarato != partite.gol_ospite_finale)).sum()),
            "eventi_incompleti": int(partite.eventi_incompleti.sum()),
            "ricomposte_esattamente": int((~partite.eventi_incompleti).sum()),
        },
        "verifica_esterna_dfb": controllo,
        "verifica_coupe_de_france": cdf_v,
        "finali_recuperate_da_wikipedia": finali_q,
        "senza_formazioni": {
            "partite": int(tutte.game_id.isna().sum()),
            "quali": "Coupe de France (201) + le 3 finali assenti da games.csv; "
                     "Wikipedia non pubblica i titolari se non per le finali",
        },
        "aggancio_seconde_divisioni": resa2a,
        "date_corrette": date_corrette,
    }

    _log("\n== quadro")
    _log(json.dumps(quadro, indent=1, ensure_ascii=False, default=str)[:3000])

    if args.verifica:
        _log("\n(--verifica: nessun file scritto)")
        return 0

    # --- la lista di lavoro per chi raccoglie a mano su diretta.it.
    # Non e' un doppione di partite.csv: e' ordinata per competizione e data,
    # tiene solo il perimetro, e dice per OGNI partita se le formazioni le
    # abbiamo gia' (`gia_abbiamo_formazioni`) — cosi' la priorita' si vede
    # dalla riga invece di doverla ricordare.
    lavoro = tutte[tutte.dentro_perimetro].copy()
    lavoro["gia_abbiamo_formazioni"] = lavoro.game_id.notna()
    lavoro = lavoro.sort_values(["competizione", "data", "casa"])[[
        "competizione", "paese", "turno", "data", "casa", "ospite",
        "gol_casa_finale", "gol_ospite_finale", "rigori_casa", "rigori_ospite",
        "divisione_casa", "divisione_ospite", "gia_abbiamo_formazioni",
    ]]

    USCITA.mkdir(parents=True, exist_ok=True)
    for nome, d in [("partite", tutte), ("formazioni", formazioni),
                    ("eventi", eventi), ("da_raccogliere", lavoro)]:
        f = USCITA / f"{nome}.csv"
        d.to_csv(f, index=False)
        quadro.setdefault("file", {})[f"{nome}.csv"] = {
            "righe": int(len(d)),
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        }
        _log(f"  scritto {f.relative_to(RADICE)} ({len(d)} righe)")
    (USCITA / "manifesto.json").write_text(
        json.dumps(quadro, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    _log(f"  scritto {(USCITA / 'manifesto.json').relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
