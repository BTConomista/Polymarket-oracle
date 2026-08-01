"""Statistiche PER SQUADRA PER PARTITA, divise in PERIODI (Totale / 1T / 2T).

Fonte: **diretta.it/Flashscore**, dato a monte di **Opta**, raccolta **a mano**
dall'utente (niente scraping). Stessa fonte e stessa posizione di licenza del
dato per giocatore (`src/data/player_stats.py`): il progetto **non rivendica
alcuna licenza** su questi dati. Vedi il README della raccolta.

COS'E' DI NUOVO, e perche' non e' un doppione del per-giocatore. Le 45 metriche
sono di squadra, ma la novita' non e' quella: e' la **scomposizione per periodo**
— ogni squadra-partita esiste in tre righe (Totale, 1° tempo, 2° tempo). E' il
primo dato del progetto che separa i due tempi su metriche vere, cioe' il dato
che serve al residuo aperto della Fase 96/99 (il secondo tempo e' mal calibrato
mentre il primo no -> serve un modello a due stadi).
Le metriche CONTINUE non sono ricostruibili sommando il per-giocatore
(xG combacia in 55/758 celle, xGOT 104/758, xA 66/758): questo file e' misura
autonoma, non un aggregato.

PERIMETRO. Cinque leghe, stagione 2025-26: 1.752 partite di campionato
(380+380+380+306+306). Nulla e' incardinato su una lega o una stagione: una
raccolta nuova = una cartella `files/diretta_{lega}_{stagione}/` con dentro un
`manifesto_squadra.json`, registrata da
`scripts/registra_raccolta_squadra_diretta.py`, **senza toccare `src/`**.

⚠️ TRE COSE DA SAPERE PRIMA DI USARLI (tutte misurate, non ipotesi).

1. **Le righe `Play-off` NON sono campionato.** Ligue 1 (4 partite) e
   Bundesliga (2) includono gli spareggi promozione/retrocessione, che
   coinvolgono club di seconda divisione e **non esistono negli snapshot**.
   `load_team_matches()` le esclude di default (`solo_campionato=True`) e la
   colonna `Fase` resta a dichiararle. In Ligue 1 si SOVRAPPONGONO per data
   alla stagione regolare: solo `Fase` le separa, mai la data.

2. **Il vuoto e' uno ZERO, non un dato mancante.** Tre colonne sparse
   (`Cartellini gialli`, `Cartellini rossi`, `Gol di testa`) sono vuote quando
   la statistica vale zero: il sito omette la riga. Dimostrato contro
   football-data.co.uk — fonte indipendente — su 1.625/1.626 team-partita.
   Il file su disco resta **fedele alla fonte** (i vuoti sono vuoti: regola R3,
   nessuna modifica silenziosa al dato); e' il caricatore a riempirli, con
   `zeri_espliciti=True`. Caricarli come mancanti non farebbe sparire dei
   cartellini: farebbe sparire gli **zeri**, gonfiando ogni media per partita.

3. **`Risultato squadra` ed `Esito` sono di FINE PARTITA, anche sulle righe di
   periodo** (identici nelle tre righe, 760/760 per lega). La riga
   "1° tempo" porta il risultato finale. E' il caso da manuale della regola R8:
   usarli come contesto del primo tempo e' look-ahead diretto. E ne segue che
   **il punteggio all'intervallo non e' in questo dataset**: va preso da
   `HTHG/HTAG` di football-data, oppure dedotto (vedi `gol_dedotti`).

⏱️ REGOLA R8. Tutte e 45 le metriche sono `post`: esistono solo a partita
finita. `Giornata`, `Data`, `Squadra`, `Campo`, `Avversario`, `Periodo`, `Fase`
sono `pre`. `Risultato squadra` ed `Esito` sono `post` (vedi punto 3). La forma
normale d'uso e' `team_form()`, che aggrega le partite PRECEDENTI.

Il modulo non e' letto da `backtest.py` ne' da alcun modello: e' infrastruttura.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

FILES = Path(__file__).resolve().parents[2] / "files"

PREFISSO = "diretta_"
FILE_SQUADRA = "squadra_per_partita.csv.gz"
FILE_MANIFESTO = "manifesto_squadra.json"
FILE_LEGENDA = "legenda_squadra.csv"
FILE_NOTE = "note_fonte.csv"

# Il manifesto del dato di squadra e' un file DIVERSO da quello del dato per
# giocatore (`manifesto.json`). Non e' pignoleria: `player_stats.raccolte()`
# scopre le raccolte cercando `manifesto.json`, quindi una cartella che contiene
# solo dati di squadra (Bundesliga e Ligue 1, che non hanno il per-giocatore)
# resta invisibile a quel caricatore invece di farlo fallire su un file che non
# c'e'. I due dataset convivono nella stessa cartella senza vedersi.

PERIODO_TOTALE = "Totale"
PERIODO_1T = "1° tempo"
PERIODO_2T = "2° tempo"
PERIODO_SUPPL = "Supplementari"

# ⚠️ I 5 file consegnati hanno QUATTRO ordini di colonna diversi: ogni file
# segue l'ordine con cui il sito mostrava le statistiche per QUELLA lega
# (verificato contro il foglio Legenda di ciascuno — e' coerenza della fonte,
# non corruzione). Lo snapshot che scriviamo normalizza su un ordine unico,
# cosi' il repo mantiene la sua garanzia di schema identico fra leghe.
# Corollario da non dimenticare: le colonne si leggono per NOME, mai per
# posizione.
COLONNE_CHIAVE = (
    "Giornata", "Data", "Squadra", "Campo", "Avversario",
    "Risultato squadra", "Esito", "Periodo", "Fase",
)

COLONNE_METRICHE = (
    "Goal previsti (xG)",
    "Possesso palla %",
    "Tiri totali",
    "Tiri in porta",
    "Grandi occasioni",
    "Calci d'angolo",
    "Passaggi riusciti",
    "Passaggi totali",
    "Passaggi %",
    "Cartellini gialli",
    "Cartellini rossi",
    "xG sui Tiri in porta (xGOT)",
    "Tiri fuori",
    "Tiri fermati",
    "Tiri dall'area di rigore",
    "Tiri da fuori area",
    "Pali colpiti",
    "Palloni toccati nell'area avversaria",
    "Passaggi filtranti riusciti",
    "Fuorigioco",
    "Punizioni",
    "Passaggi lunghi riusciti",
    "Passaggi lunghi totali",
    "Passaggi lunghi %",
    "Passaggi offensivi riusciti",
    "Passaggi offensivi totali",
    "Passaggi offensivi %",
    "Cross riusciti",
    "Cross totali",
    "Cross %",
    "Assist previsti (xA)",
    "Rimesse Laterali",
    "Falli",
    "Tackles riusciti",
    "Tackles totali",
    "Tackles %",
    "Contrasti vinti",
    "Respinte difensive",
    "Palle intercettate",
    "Errori che hanno portato al tiro",
    "Errori che hanno portato al gol",
    "Parate",
    "xGot affrontati",
    "Gol evitati",
    "Gol di testa",
)

COLONNE_CANONICHE = COLONNE_CHIAVE + COLONNE_METRICHE

# Le tre colonne in cui la fonte omette la riga quando il valore e' zero.
# NON e' un elenco a naso: sono le uniche tre con celle vuote in tutte e 5 le
# raccolte, e per tutte e tre l'uguaglianza vuoto==0 e' stata verificata
# contro football-data.
COLONNE_ZERO_IMPLICITO = ("Cartellini gialli", "Cartellini rossi", "Gol di testa")

# Le percentuali e il possesso NON sono additivi fra periodi: sono rapporti e
# medie, non conteggi. Sommare 1T e 2T su queste colonne e' un errore.
COLONNE_NON_ADDITIVE = (
    "Possesso palla %", "Passaggi %", "Passaggi lunghi %",
    "Passaggi offensivi %", "Cross %", "Tackles %",
)

PRE_COLUMNS = ("Giornata", "Data", "Squadra", "Campo", "Avversario", "Periodo", "Fase")
POST_COLUMNS = ("Risultato squadra", "Esito") + COLONNE_METRICHE


def raccolte_squadra() -> list[dict]:
    """Le raccolte di squadra disponibili, lette dai manifesti."""
    out = []
    for d in sorted(FILES.glob(f"{PREFISSO}*")):
        m = d / FILE_MANIFESTO
        if not m.is_file():
            continue
        try:
            info = json.loads(m.read_text())
        except json.JSONDecodeError:
            log.warning("manifesto illeggibile in %s: raccolta ignorata", d)
            continue
        info["cartella"] = d
        out.append(info)
    return out


def _raccolta(lega: str | None, stagione: str | None) -> dict:
    disponibili = raccolte_squadra()
    if not disponibili:
        raise FileNotFoundError(
            f"nessuna raccolta di squadra in {FILES}/{PREFISSO}*. "
            "Registrarne una con scripts/registra_raccolta_squadra_diretta.py"
        )
    scelte = [
        r for r in disponibili
        if (lega is None or r.get("lega") == lega)
        and (stagione is None or r.get("stagione") == stagione)
    ]
    if not scelte:
        eleggibili = [f"{r.get('lega')}/{r.get('stagione')}" for r in disponibili]
        raise KeyError(f"raccolta {lega}/{stagione} non trovata. Disponibili: {eleggibili}")
    if len(scelte) > 1:
        eleggibili = [f"{r.get('lega')}/{r.get('stagione')}" for r in scelte]
        raise ValueError(f"piu' raccolte corrispondono: {eleggibili}. Specificare lega e stagione.")
    return scelte[0]


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():  # pragma: no cover - dipende dal checkout
        raise FileNotFoundError(
            f"{path} non trovato. Le raccolte vivono in files/diretta_*/ e sono "
            "versionate: se manca, il checkout e' incompleto."
        )
    df = pd.read_csv(path)
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    return df


def load_team_matches(
    lega: str | None = None,
    stagione: str | None = None,
    *,
    strict: bool = True,
    tutte: bool = False,
    solo_campionato: bool = True,
    zeri_espliciti: bool = True,
) -> pd.DataFrame:
    """Una riga per (squadra, partita, periodo), con `data`, `lega` e `stagione`.

    ``solo_campionato`` (default) tiene le sole righe ``Fase == 'Stagione
    regolare'``: le partite di spareggio non appartengono al campionato e non
    hanno riscontro negli snapshot. Metterlo a ``False`` le include, e allora
    ogni conteggio va tenuto separato per `Fase` — mescolarle e' l'errore piu'
    facile su questi file.

    ``zeri_espliciti`` (default) riempie con 0 le tre colonne in cui la fonte
    omette la riga quando il valore e' zero (vedi ``COLONNE_ZERO_IMPLICITO``).
    Metterlo a ``False`` restituisce il dato **esattamente come sta su disco**,
    che e' la fedelta' alla fonte, non la semantica giusta.

    Con ``strict`` (default) verifica la copertura dichiarata nel manifesto e
    alza se non torna: meglio fallire che restituire in silenzio meno righe.
    """
    if tutte:
        pezzi = [
            load_team_matches(
                r.get("lega"), r.get("stagione"), strict=strict,
                solo_campionato=solo_campionato, zeri_espliciti=zeri_espliciti,
            )
            for r in raccolte_squadra()
        ]
        return pd.concat(pezzi, ignore_index=True) if pezzi else pd.DataFrame()

    r = _raccolta(lega, stagione)
    df = _read(r["cartella"] / FILE_SQUADRA)
    df["data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")
    df["lega"] = r.get("lega")
    df["stagione"] = r.get("stagione")

    # I nomi squadra si portano sulla convenzione dei nostri snapshot. Senza,
    # il join si ferma in silenzio: l'edizione italiana di diretta.it traduce i
    # nomi stranieri, e su Bundesliga si fermava a 60/612 team-partita.
    from .sources import TEAM_ALIASES

    for col in ("Squadra", "Avversario"):
        if col in df.columns:
            df[col] = df[col].map(lambda x: TEAM_ALIASES.get(x, x))

    if strict:
        attese = r.get("righe_attese")
        if attese is not None and len(df) != attese:
            raise ValueError(
                f"{r.get('lega')}/{r.get('stagione')}: attese {attese} righe "
                f"squadra-partita-periodo, trovate {len(df)}"
            )

    if solo_campionato:
        df = df[df["Fase"] == "Stagione regolare"].reset_index(drop=True)
        if strict:
            att = r.get("team_partita_attesi")
            if att is not None:
                n = df.groupby(["data", "Squadra", "Avversario"]).ngroups
                if n != att:
                    raise ValueError(
                        f"{r.get('lega')}/{r.get('stagione')}: attesi {att} "
                        f"team-partita di campionato, trovati {n}"
                    )

    if zeri_espliciti:
        for c in COLONNE_ZERO_IMPLICITO:
            if c in df.columns:
                df[c] = df[c].fillna(0)
    return df


def load_legend(lega: str | None = None, stagione: str | None = None) -> pd.DataFrame:
    """Mappa `statistica -> codice della fonte`, come la pubblica diretta.it.

    ⚠️ Copre 29 delle 45 colonne metriche per corrispondenza letterale del
    nome: le 5 statistiche mostrate come "% (riusciti/totali)" diventano 3
    colonne ciascuna, e "Possesso palla" si chiama "Possesso palla %" nel dato.
    Non e' un buco: e' la ricetta con cui la fonte le ha divise.
    """
    return _read(_raccolta(lega, stagione)["cartella"] / FILE_LEGENDA)


def load_note_fonte(lega: str | None = None, stagione: str | None = None) -> pd.DataFrame:
    """Il foglio "Note" della fonte, conservato integrale come DICHIARAZIONE.

    ⚠️ Non e' documentazione affidabile: e' cio' che la fonte dichiara di se'.
    Almeno un'affermazione e' **falsa** — la nota della Bundesliga dice che i
    tempi supplementari non sono compresi nel Totale, e i numeri dicono il
    contrario (39/39 metriche additive tornano con 1T+2T+Suppl, 8/39 senza).
    E' conservato proprio per poter mostrare la differenza fra il dichiarato e
    il misurato (regola R4).
    """
    return _read(_raccolta(lega, stagione)["cartella"] / FILE_NOTE)


def statistic_columns(df: pd.DataFrame | None = None) -> list[str]:
    """Le colonne che sono STATISTICHE (tutte `post`), escluse le anagrafiche."""
    if df is None:
        df = load_team_matches(strict=False)
    return [c for c in df.columns if c in COLONNE_METRICHE]


def gol_dedotti(df: pd.DataFrame) -> pd.Series:
    """I gol SUBITI da ogni riga, dedotti da `xGot affrontati - Gol evitati`.

    ⚠️ E' una STIMA con errore misurato, non un dato. La colonna dei gol non
    esiste in questo dataset. L'identita' regge perche' "Gol evitati" e'
    definito come (xGOT affrontato - gol subiti), ma **gli autogol non entrano
    nell'xGOT di chi ne beneficia**, quindi la deduzione puo' solo
    SOTTOSTIMARE, mai sovrastimare.

    Errore misurato contro `HTHG/HTAG` di football-data (fonte indipendente),
    sulle 3 leghe con lo spareggio escluso: 1° tempo esatto in 1.952/1.984
    (98,4%), 2° tempo in 1.943/1.982 (98,0%), e lo scarto e' **sempre -1, mai
    +1**. Da usare dichiarando l'errore; dove servono i gol veri
    dell'intervallo, football-data ce li ha.
    """
    return (df["xGot affrontati"] - df["Gol evitati"]).round(0)


def join_to_snapshot(
    df: pd.DataFrame | None = None, snapshot: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Aggancia ogni riga alla partita corrispondente dello snapshot di lega.

    Aggiunge `home_team`, `away_team`, `home_goals`, `away_goals` e `in_casa`.
    Alza se anche una sola riga resta orfana: un join che perde righe in
    silenzio e' il modo in cui il progetto ha gia' pagato un bug (§7 del
    CLAUDE.md, caso "Hellas Verona").

    ⚠️ Vale sulle sole righe di campionato. Le partite di spareggio non hanno
    riscontro in `data/*_matches.csv` — sono di seconda divisione — quindi
    passare un frame con `Fase == 'Play-off'` fa alzare, ed e' voluto.
    """
    if df is None:
        df = load_team_matches()
    leghe = sorted(set(df["lega"].dropna())) if "lega" in df.columns else []
    if len(leghe) != 1:
        raise ValueError(
            f"join_to_snapshot lavora su UNA lega per volta, trovate {leghe or 'nessuna'}"
        )
    lega = leghe[0]

    if snapshot is None:
        from . import database

        percorso = database.snapshot_path(lega)
        if not percorso.exists():
            raise FileNotFoundError(
                f"nessuno snapshot per '{lega}': le competizioni fuori dalle 5 "
                "leghe modellate non hanno un riferimento partita in "
                "data/*_matches.csv."
            )
        snapshot = database.read_snapshot(percorso)

    snap = snapshot.copy()
    snap["data"] = pd.to_datetime(snap["date"])
    snap = snap[snap["data"].between(df["data"].min(), df["data"].max())]
    cols = ["data", "home_team", "away_team", "home_goals", "away_goals"]

    casa = df.merge(
        snap[cols], left_on=["data", "Squadra", "Avversario"],
        right_on=["data", "home_team", "away_team"], how="left",
    )
    trasferta = df.merge(
        snap[cols], left_on=["data", "Squadra", "Avversario"],
        right_on=["data", "away_team", "home_team"], how="left",
    )
    out = casa.copy()
    manca = out["home_team"].isna()
    for c in ("home_team", "away_team", "home_goals", "away_goals"):
        out.loc[manca, c] = trasferta.loc[manca, c]
    out["in_casa"] = out["Squadra"] == out["home_team"]

    orfane = int(out["home_team"].isna().sum())
    if orfane:
        raise ValueError(
            f"{orfane} righe squadra-partita non agganciate allo snapshot "
            f"{lega}: il join deve essere totale, non parziale."
        )
    return out


def periodi_affiancati(
    df: pd.DataFrame | None = None, columns: list[str] | None = None
) -> pd.DataFrame:
    """Una riga per squadra-partita, coi periodi affiancati in colonne.

    Da `Tiri totali` escono `Tiri totali (1T)`, `Tiri totali (2T)` e
    `Tiri totali (Totale)`. E' la forma comoda per studiare la differenza fra i
    due tempi — il residuo aperto della Fase 96/99.

    ⚠️ I supplementari (2 righe in tutto, lo spareggio di Bundesliga) NON
    compaiono: la funzione lavora sui tre periodi ordinari. Sulle righe di
    campionato non esistono, quindi non si perde nulla.
    """
    if df is None:
        df = load_team_matches()
    if columns is None:
        columns = [c for c in COLONNE_METRICHE if c in df.columns]

    chiave = ["lega", "stagione", "data", "Squadra", "Avversario", "Campo"]
    etichette = {PERIODO_1T: "1T", PERIODO_2T: "2T", PERIODO_TOTALE: "Totale"}
    pezzi = []
    for periodo, suffisso in etichette.items():
        p = df[df["Periodo"] == periodo][chiave + columns].copy()
        p = p.rename(columns={c: f"{c} ({suffisso})" for c in columns})
        pezzi.append(p.set_index(chiave))
    return pd.concat(pezzi, axis=1).reset_index()


def team_form(
    df: pd.DataFrame | None = None,
    columns: list[str] | None = None,
    window: int = 5,
    periodo: str = PERIODO_TOTALE,
) -> pd.DataFrame:
    """⏱️ LA FORMA SICURA (R8): media delle N partite PRECEDENTI, per squadra.

    Per ogni squadra-partita restituisce la media, sulle ``window`` partite
    **precedenti** di quella squadra, delle metriche indicate. La riga della
    partita corrente e' esclusa per costruzione (``shift(1)``), quindi il
    risultato e' utilizzabile come feature `pre`.

    ``periodo`` sceglie su quale periodo aggregare: con ``PERIODO_1T`` si
    ottiene la forma del solo primo tempo, che e' il motivo per cui questo
    dataset esiste.

    La prima partita di ogni squadra esce NaN: e' corretto, non un buco da
    riempire con zero.
    """
    if df is None:
        df = load_team_matches()
    if columns is None:
        columns = ["Goal previsti (xG)", "Tiri totali", "Tiri in porta",
                   "Calci d'angolo", "Possesso palla %"]
    mancanti = [c for c in columns if c not in df.columns]
    if mancanti:
        raise KeyError(f"colonne assenti nel dataset: {mancanti}")

    per_partita = (
        df[df["Periodo"] == periodo]
        .sort_values(["Squadra", "data"])[["data", "Squadra"] + columns]
        .reset_index(drop=True)
    )
    rolling = (
        per_partita.groupby("Squadra")[columns]
        .apply(lambda g: g.shift(1).rolling(window, min_periods=1).mean())
        .reset_index(level=0, drop=True)
    )
    out = per_partita[["data", "Squadra"]].copy()
    for c in columns:
        out[f"{c} (media {window} prec.)"] = rolling[c]
    return out
