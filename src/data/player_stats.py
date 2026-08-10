"""Statistiche PER GIOCATORE PER PARTITA — il dato "Tier B" del progetto.

Fonte: **diretta.it/Flashscore**, raccolta **a mano** dall'utente (niente
scraping). Ogni raccolta vive in `files/diretta_{lega}_{stagione}/` con il
proprio `README.md` e un `manifesto.json`.
⚠️ Il dato a monte e' di **Opta**: il progetto NON rivendica alcuna licenza su
di esso e la posizione e' dichiaratamente non risolta. Vedi il README della
raccolta.

COSA CONTIENE una raccolta: **97 statistiche per giocatore-partita** — tocchi,
passaggi (anche progressivi), dribbling, contrasti, recuperi, intercetti, falli
individuali, xG/xA/xGOT individuali, grandi occasioni, blocco portiere. E'
l'intero "Tier B" che il piano dava per irraggiungibile
(`docs/PIANO_DATABASE_GIOCATORI.md` §12).

PERIMETRO, e come si allarga. Oggi c'e' **Serie A 2025-26** (11.894 righe, 379
partite su 380). L'utente ha in programma le altre 4 leghe e poi le competizioni
europee e internazionali: per questo **nulla qui e' incardinato su una lega o
una stagione**. Aggiungerne una = creare una cartella e registrarla con
`scripts/registra_raccolta_diretta.py`, senza toccare `src/`. E' la stessa
scelta gia' fatta per `LEAGUE_CONFIGS` (§7 del `CLAUDE.md`).

⚠️ Le coppe europee e le nazionali avranno un limite in piu': **non hanno uno
snapshot** in `data/*_matches.csv`, quindi `join_to_snapshot()` non le copre e
alza un errore esplicito. Serve un'altra via d'aggancio prima di usarle.

⏱️ REGOLA R8 — E' IL PUNTO PIU' FACILE DA SBAGLIARE.
Tutte e 97 le statistiche sono `post`: esistono solo a partita finita. Usarle
per prevedere la partita che le ha prodotte e' look-ahead. La forma normale
d'uso e' `team_form()`, che aggrega le partite PRECEDENTI. Le colonne grezze di
`load_player_matches()` NON vanno passate a un modello cosi' come sono.

Il modulo non e' letto da `backtest.py` ne' da alcun modello: e'
l'infrastruttura per il go/no-go descritto in §12.3 del piano.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

FILES = Path(__file__).resolve().parents[2] / "files"

# Ogni raccolta vive in `files/diretta_{lega}_{stagione}/` con dentro un
# `manifesto.json` che dichiara perimetro e copertura attesa. Aggiungere una
# lega o una stagione = aggiungere una cartella, MAI toccare questo codice:
# e' la stessa scelta gia' fatta per LEAGUE_CONFIGS (§7 del CLAUDE.md).
PREFISSO = "diretta_"
FILE_PARTITE = "partita_per_partita.csv.gz"
FILE_STAGIONE = "riepilogo_stagionale.csv.gz"
FILE_LEGENDA = "legenda.csv"
FILE_MANIFESTO = "manifesto.json"

# I quattro fogli "di contorno" arrivati con la Bundesliga (Fase 145): elenco
# partite, formazioni (panchinari compresi), sostituzioni, cronaca. Le prime
# tre leghe non li hanno — sono opzionali per costruzione, e i caricatori qui
# sotto dicono ESPLICITAMENTE quali raccolte li espongono invece di restituire
# un DataFrame vuoto (un vuoto silenzioso e' indistinguibile da «non ci sono
# eventi», ed e' il tipo di finto pieno che la regola R6 vieta).
FILE_ELENCO = "partite.csv.gz"
FILE_FORMAZIONI = "formazioni.csv.gz"
FILE_CAMBI = "cambi.csv.gz"
FILE_EVENTI = "eventi.csv.gz"

# La colonna `Fase` distingue il campionato dalle partite che campionato non
# sono (lo spareggio promozione/retrocessione di Bundesliga e Ligue 1). Le due
# consegne usano PAROLE DIVERSE per la stessa cosa — «Campionato»/«Spareggio»
# nei file giocatore, «Stagione regolare»/«Play-off» in quelli di squadra — e
# la differenza va dichiarata, non normalizzata di nascosto sul disco (R4).
FASI_CAMPIONATO = ("Campionato", "Stagione regolare")
FASI_FUORI_CAMPIONATO = ("Spareggio", "Play-off", "Playoff")

# Le uniche colonne NON `post` (regola R8). Tutto il resto esiste solo a
# partita finita. `Titolare/Subentrato` e' `post` nel dato storico ma
# diventerebbe `pre` se raccolto dalla formazione ufficiale ~1h prima: qui
# arriva a posteriori, quindi resta `post`.
PRE_COLUMNS = ("Giornata", "Data", "Squadra", "Campo", "Avversario")
STATIC_COLUMNS = ("Giocatore", "Ruolo")


def raccolte() -> list[dict]:
    """Le raccolte disponibili, lette dai manifesti. Vuota se non ce ne sono.

    Non c'e' un elenco incardinato nel codice: si scopre cosa c'e' sul disco.
    Cosi' una lega nuova entra copiando una cartella e registrandola con
    `scripts/registra_raccolta_diretta.py`, senza modifiche a `src/`.
    """
    import json

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
    disponibili = raccolte()
    if not disponibili:
        raise FileNotFoundError(
            f"nessuna raccolta trovata in {FILES}/{PREFISSO}*. "
            "Registrarne una con scripts/registra_raccolta_diretta.py"
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


def load_player_matches(
    lega: str | None = None,
    stagione: str | None = None,
    *,
    strict: bool = True,
    tutte: bool = False,
    solo_campionato: bool = True,
) -> pd.DataFrame:
    """Una riga per giocatore-partita, con `data`, `lega` e `stagione`.

    Senza argomenti carica **l'unica** raccolta presente; con `lega`/`stagione`
    ne sceglie una; con ``tutte=True`` le impila tutte (le colonne `lega` e
    `stagione` restano a distinguerle).

    ``solo_campionato`` (default) tiene le sole righe di campionato dove la
    raccolta ha la colonna ``Fase``, ed e' un no-op dove non ce l'ha. Serve
    perche' lo **spareggio promozione/retrocessione** non e' campionato: non sta
    negli snapshot, quindi `join_to_snapshot()` lo lascerebbe orfano e alzerebbe.
    Metterlo a ``False`` lo include, e allora ogni conteggio va tenuto separato
    per `Fase` — mescolarli e' l'errore piu' facile su questi file.

    ⚠️ Le 97 statistiche sono TUTTE `post` (R8): non passarle a un modello per
    la partita che le ha prodotte. Usa `team_form()`.

    Con ``strict`` (default) verifica la copertura dichiarata nel manifesto e
    alza se non torna: meglio fallire che restituire in silenzio meno righe.
    """
    if tutte:
        pezzi = [
            load_player_matches(r.get("lega"), r.get("stagione"), strict=strict,
                                solo_campionato=solo_campionato)
            for r in raccolte()
        ]
        return pd.concat(pezzi, ignore_index=True) if pezzi else pd.DataFrame()

    r = _raccolta(lega, stagione)
    df = _read(r["cartella"] / FILE_PARTITE)
    df["data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")
    df["lega"] = r.get("lega")
    df["stagione"] = r.get("stagione")
    # I nomi squadra si portano sulla convenzione dei nostri snapshot
    # (football-data) con la mappa canonica del progetto. Senza, il join si
    # ferma in silenzio: sulla Premier 2025-26 si fermava a 544/760, perche'
    # diretta.it scrive "Manchester Utd" e noi "Man United".
    from .sources import TEAM_ALIASES

    for col in ("Squadra", "Avversario"):
        if col in df.columns:
            df[col] = df[col].map(lambda x: TEAM_ALIASES.get(x, x))

    if strict:
        attese = r.get("righe_attese")
        if attese is not None and len(df) != attese:
            raise ValueError(
                f"{r.get('lega')}/{r.get('stagione')}: attese {attese} righe "
                f"giocatore-partita, trovate {len(df)}"
            )

    if solo_campionato and "Fase" in df.columns:
        ignote = set(df["Fase"].dropna()) - set(FASI_CAMPIONATO) - set(FASI_FUORI_CAMPIONATO)
        if ignote:
            raise ValueError(
                f"{r.get('lega')}/{r.get('stagione')}: fasi sconosciute {sorted(ignote)}. "
                "Aggiungerle a FASI_CAMPIONATO o FASI_FUORI_CAMPIONATO invece di "
                "lasciarle decidere al caso a un filtro che non le conosce."
            )
        df = df[df["Fase"].isin(FASI_CAMPIONATO)].reset_index(drop=True)

    if strict:
        # `team_partita_attesi` e' un conteggio DI CAMPIONATO: confrontarlo con
        # un caricamento che include lo spareggio farebbe fallire una guardia
        # per un motivo che non e' un difetto.
        att_tm = r.get("team_partita_attesi") if solo_campionato else None
        if att_tm is not None:
            n = df.groupby(["data", "Squadra", "Avversario"]).ngroups
            if n != att_tm:
                raise ValueError(
                    f"{r.get('lega')}/{r.get('stagione')}: attesi {att_tm} "
                    f"team-partita, trovati {n}"
                )
    return df


def _foglio_extra(nome_file: str, cosa: str, lega, stagione) -> pd.DataFrame:
    """Uno dei quattro fogli di contorno, se la raccolta ce l'ha.

    Alza con l'elenco di chi ce l'ha invece di restituire un DataFrame vuoto:
    un vuoto silenzioso e' indistinguibile da «non e' successo niente».
    """
    r = _raccolta(lega, stagione)
    percorso = r["cartella"] / nome_file
    if not percorso.exists():
        con = [f"{x.get('lega')}/{x.get('stagione')}" for x in raccolte()
               if (x["cartella"] / nome_file).exists()]
        raise FileNotFoundError(
            f"{r.get('lega')}/{r.get('stagione')} non espone {cosa}: la fonte non "
            f"lo ha consegnato per questa raccolta. Ce l'hanno: {con or 'nessuna'}."
        )
    df = _read(percorso)
    if "Data" in df.columns:
        df["data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")
    # Stessa normalizzazione dei nomi squadra del caricatore principale: senza,
    # questi fogli non si incrociano con le altre tabelle e il disallineamento
    # non da' errore — da' zero righe in comune (l'edizione italiana del sito
    # scrive "Augusta" dove noi scriviamo "Augsburg").
    from .sources import TEAM_ALIASES

    for col in ("Squadra", "Avversario", "Casa", "Trasferta"):
        if col in df.columns:
            df[col] = df[col].map(lambda x: TEAM_ALIASES.get(x, x))
    df["lega"] = r.get("lega")
    df["stagione"] = r.get("stagione")
    return df


def load_match_list(lega=None, stagione=None) -> pd.DataFrame:
    """L'elenco delle partite come lo pubblica la fonte (con `ID partita`)."""
    return _foglio_extra(FILE_ELENCO, "l'elenco partite", lega, stagione)


def load_lineups(lega=None, stagione=None) -> pd.DataFrame:
    """Le formazioni, **panchinari non entrati compresi** (`Stato`).

    ⚠️ E' l'unico foglio che contiene chi NON e' sceso in campo, e serve a
    spiegare una divergenza vera: i cartellini mostrati alla panchina stanno
    nelle statistiche di SQUADRA e non possono stare in quelle per giocatore
    (Fase 145). Con la formazione ufficiale sarebbe anche il primo dato `pre`
    della famiglia, ma qui arriva a posteriori: resta `post`.
    """
    return _foglio_extra(FILE_FORMAZIONI, "le formazioni", lega, stagione)


def load_substitutions(lega=None, stagione=None) -> pd.DataFrame:
    """Le sostituzioni (minuto, chi esce, chi entra)."""
    return _foglio_extra(FILE_CAMBI, "le sostituzioni", lega, stagione)


def load_events(lega=None, stagione=None) -> pd.DataFrame:
    """La cronaca: gol, autogol, rigori, cartellini, col minuto.

    ⚠️ **INCOMPLETA per costruzione**: e' la cronaca redazionale del sito, non
    un tracciato. Sulla Bundesliga 2025-26 elenca 907 gol dei 990 realmente
    segnati (69 partite su 308 non li riportano tutti). Gol, assist e cartellini
    per giocatore NON vengono da qui ma dalle statistiche individuali, che sono
    complete. Usarla per contare e' sbagliato; usarla per **datare** un evento
    (il minuto) o per spiegare una divergenza e' il suo mestiere.
    """
    return _foglio_extra(FILE_EVENTI, "la cronaca eventi", lega, stagione)


def load_season_totals(lega: str | None = None, stagione: str | None = None) -> pd.DataFrame:
    """Una riga per giocatore-stagione (somme e medie).

    ⚠️ E' un DERIVATO del partita-per-partita, non una seconda misura: non
    usarlo come controllo incrociato di sé stesso. Ed e' un aggregato di FINE
    stagione, quindi utilizzabile solo RITARDATO (stagione precedente).
    ⚠️ Se la raccolta ha partite mancanti (dichiarate nel manifesto alla voce
    `partite_mancanti`), i totali delle squadre coinvolte sono su meno partite.
    """
    return _read(_raccolta(lega, stagione)["cartella"] / FILE_STAGIONE)


def load_legend(lega: str | None = None, stagione: str | None = None) -> pd.DataFrame:
    """Mappa `codice fonte -> etichetta italiana` (es. BALL_RECOVERIES)."""
    return _read(_raccolta(lega, stagione)["cartella"] / FILE_LEGENDA)


def statistic_columns(df: pd.DataFrame | None = None) -> list[str]:
    """Le colonne che sono STATISTICHE (tutte `post`), escluse le anagrafiche."""
    if df is None:
        df = load_player_matches(strict=False)
    skip = set(PRE_COLUMNS) | set(STATIC_COLUMNS) | {
        "data", "lega", "stagione", "Risultato squadra", "Esito",
        "Titolare/Subentrato",
        # `Fase` e' un'etichetta di competizione, non una misura: senza questa
        # riga la Bundesliga dichiarerebbe 98 statistiche invece di 97, e il
        # manifesto scritto dallo script di registrazione ne erediterebbe il
        # conteggio sbagliato.
        "Fase",
    }
    return [c for c in df.columns if c not in skip]


def join_to_snapshot(
    df: pd.DataFrame | None = None, snapshot: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Aggancia ogni riga alla partita corrispondente dello snapshot di lega.

    Aggiunge `home_team`, `away_team`, `home_goals`, `away_goals` e `in_casa`.
    Alza se anche una sola riga resta orfana: un join che perde righe in
    silenzio e' il modo in cui il progetto ha gia' pagato un bug (§7 del
    CLAUDE.md, caso "Hellas Verona").

    ⚠️ **Vale solo per le 5 leghe modellate.** Coppe europee e nazionali non
    hanno uno snapshot in `data/*_matches.csv`: per quelle raccolte questa
    funzione alza un errore esplicito invece di restituire righe orfane. Serve
    un'altra via d'aggancio (probabilmente `games.csv`), ancora da costruire.
    """
    if df is None:
        df = load_player_matches()
    leghe = sorted(set(df["lega"].dropna())) if "lega" in df.columns else []
    if len(leghe) != 1:
        raise ValueError(
            f"join_to_snapshot lavora su UNA lega per volta, trovate {leghe or 'nessuna'}"
        )
    lega = leghe[0]

    if snapshot is None:
        # Import locale: evita un ciclo all'import del pacchetto. Si legge lo
        # SNAPSHOT congelato (offline-first, §5 del CLAUDE.md), non la rete.
        from . import database

        percorso = database.snapshot_path(lega)
        if not percorso.exists():
            raise FileNotFoundError(
                f"nessuno snapshot per '{lega}': le competizioni fuori dalle 5 "
                "leghe modellate (coppe europee, nazionali) non hanno un "
                "riferimento partita in data/*_matches.csv. Serve un'altra via "
                "d'aggancio prima di poterle unire."
            )
        snapshot = database.read_snapshot(percorso)

    snap = snapshot.copy()
    snap["data"] = pd.to_datetime(snap["date"])
    # si restringe alla finestra della raccolta, non a una data incisa
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

    orfane = out["home_team"].isna().sum()
    if orfane:
        raise ValueError(
            f"{orfane} righe giocatore-partita non agganciate allo snapshot "
            f"{lega}: il join deve essere totale, non parziale."
        )
    return out


def team_form(
    df: pd.DataFrame | None = None,
    columns: list[str] | None = None,
    window: int = 5,
) -> pd.DataFrame:
    """⏱️ LA FORMA SICURA (R8): media delle N partite PRECEDENTI, per squadra.

    Per ogni squadra-partita restituisce la media, sulle ``window`` partite
    **precedenti** di quella squadra, delle statistiche indicate — sommate
    sull'undici schierato. La riga della partita corrente e' esclusa per
    costruzione (``shift(1)``), quindi il risultato e' utilizzabile come
    feature `pre`.

    La prima partita di ogni squadra esce NaN: e' corretto, non un buco da
    riempire con zero.
    """
    if df is None:
        df = load_player_matches()
    if columns is None:
        columns = ["Palloni toccati", "Passaggi totali", "Dribbling riusciti",
                   "Contrasti", "Palle intercettate", "Goal previsti (xG)"]
    mancanti = [c for c in columns if c not in df.columns]
    if mancanti:
        raise KeyError(f"colonne assenti nel dataset: {mancanti}")

    per_partita = (
        df.groupby(["data", "Squadra"], as_index=False)[columns].sum()
        .sort_values(["Squadra", "data"])
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
