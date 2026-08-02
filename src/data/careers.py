"""⭐ IL DATABASE CARRIERE — una tabella sola, da due fonti.

`load_database()` è la funzione da usare: una riga per tappa di carriera, con
la colonna `fonte` a dire da dove viene ciascuna.

| fonte | copre | grana |
|---|---|---|
| `appearances/player-scores` | **48 competizioni** dal 2012-07-03 — oltre alle nostre 5 leghe, i massimi campionati di Turchia, Olanda, Portogallo, Belgio, Russia, Grecia, Scozia, Danimarca e Ucraina, le coppe europee, le coppe nazionali, la Coppa d'Africa | date **esatte** |
| `wikipedia` | ciò che l'altra non può avere: **prima del 2012**, le **seconde divisioni**, i campionati **extra-europei**, il settore **giovanile** | **anno** |

PERIMETRO (decisione dell'utente, 31/07/2026: *«vale la pena avere il database
completo di tutte le competizioni alle quali possiamo avere accesso»*):
**29.531 giocatori**, **1.231 club**, **197.812 tappe** dalla prima fonte, più
quelle che la raccolta Wikipedia aggiunge. `population()` isola i **7.709**
giocatori delle nostre 5 leghe, ma è un *filtro*, non il perimetro.

⚠️ **NON sommare le presenze fra le due fonti**: Wikipedia conta il solo
campionato nazionale, `appearances` conta tutte e 48 le competizioni. Le righe
si impilano, i numeri no.

⚖️ Licenza: le righe `wikipedia` sono CC BY-SA 4.0 (attribuzione nel campo
`source_url` di ciascuna). Dettagli in `data/carriere_wikipedia/README.md`.

⏱️ REGOLA R8 — IL PUNTO CHE RENDE PERICOLOSA UNA TABELLA DI CARRIERE.
«Presenze in carriera» è un numero che per sua natura **include il futuro**: la
carriera di un giocatore contiene anche le partite che deve ancora giocare.
Usarlo come feature per una partita del 2019 significherebbe sapere cosa farà
nel 2024. Per questo l'API sicura non è una colonna ma la funzione
`career_before(as_of=...)`, che conta **solo** ciò che precede strettamente
quella data. `load_database()` è `post`: descrive, non prevede.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

ROOT_DATA = Path(__file__).resolve().parents[2] / "data"
DATA_DIR = Path(__file__).resolve().parents[2] / "files" / "player_scores"
APPEARANCES = DATA_DIR / "appearances.csv.gz"
CLUBS = DATA_DIR / "clubs.csv.gz"
PLAYERS = DATA_DIR / "players.csv.gz"

# Le 5 leghe che il progetto modella.
TOP5 = ("IT1", "GB1", "ES1", "L1", "FR1")
# Inizio della finestra del progetto: le 9 stagioni degli snapshot.
WINDOW_START = pd.Timestamp("2017-07-01")
# Bordo sinistro del dataset a monte: prima di qui non c'è NULLA, e non perché
# i giocatori non giocassero (§9.4/§E.4 di docs/AUDIT_FONTI_GIOCATORI.md).
DATASET_START = pd.Timestamp("2012-07-03")
# Chi ha la prima presenza entro questa data è CENSURATO, non esordiente.
CENSORING_CUTOFF = pd.Timestamp("2012-09-30")

FONTE_STRATO1 = "appearances/player-scores"


def _load_appearances() -> pd.DataFrame:
    df = pd.read_csv(
        APPEARANCES,
        usecols=["player_id", "player_club_id", "date", "player_name",
                 "competition_id", "goals", "assists", "minutes_played",
                 "yellow_cards", "red_cards"],
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["fonte"] = FONTE_STRATO1
    return _con_integrazioni(df)


# Presenze che la fonte primaria NON ha e che noi abbiamo da un'altra parte.
# Vivono in un file a sé e si uniscono in lettura: il CSV di player-scores non
# si tocca (R3 — e comunque è di terzi: una riga scritta lì sparirebbe al primo
# ri-scaricamento, senza che nessuno se ne accorga).
#
# Ogni riga porta `fonte`, `motivo` e la data della verifica, e resta
# distinguibile a valle: chi vuole la sola fonte primaria filtra su `fonte`.
# Non è una stima — è un dato reale preso da una raccolta che abbiamo già.
INTEGRAZIONI = "presenze_integrate.csv"


def _con_integrazioni(df: pd.DataFrame) -> pd.DataFrame:
    """Unisce le presenze integrate, se il registro esiste.

    ⚠️ Non sovrascrive mai: se la fonte primaria ha già quella presenza
    (stesso giocatore, stessa data), la riga integrata viene SCARTATA. Il
    registro serve a colmare un buco, non a correggere la fonte — e un giorno
    la fonte potrebbe aggiungere ciò che oggi le manca, senza che nessuno
    rilegga questo file.
    """
    percorso = ROOT_DATA / INTEGRAZIONI
    if not percorso.exists():
        return df
    extra = pd.read_csv(percorso)
    extra["date"] = pd.to_datetime(extra["date"], errors="coerce")
    extra = extra.dropna(subset=["date"])
    if extra.empty:
        return df
    gia = set(zip(df["player_id"], df["date"]))
    extra = extra[[(p, d) not in gia
                   for p, d in zip(extra["player_id"], extra["date"])]]
    if extra.empty:
        return df
    return pd.concat([df, extra[df.columns]], ignore_index=True)


def season_of(dates: pd.Series) -> pd.Series:
    """Stagione calcistica in forma `2017-18`, con taglio al 1° luglio.

    Il taglio a luglio e non a gennaio non è un dettaglio: la coda COVID della
    2019-20 arriva al 2 agosto 2020 e finirebbe altrimenti nella stagione dopo
    (stessa scelta già fatta in `player_scores.py`).
    """
    y = dates.dt.year.where(dates.dt.month >= 7, dates.dt.year - 1)
    return y.astype(str) + "-" + (y + 1).astype(str).str[-2:]


def population(appearances: pd.DataFrame | None = None) -> pd.Index:
    """I giocatori del database: ≥1 presenza nelle 5 leghe dal 2017-07.

    **≥1 presenza, non "≥1 stagione"**: è una soglia oggettiva e riproducibile,
    mentre "una stagione" richiederebbe un numero arbitrario di partite. E
    soprattutto, alzare la soglia escluderebbe **proprio i giocatori di
    rotazione** — quelli la cui presenza o assenza varia di più da una partita
    all'altra, cioè il segnale che un database di giocatori dovrebbe catturare.
    Sono 7.709 con ≥1, 4.870 con ≥19: la differenza costa solo tempo di calcolo.
    """
    if appearances is None:
        appearances = _load_appearances()
    dentro = appearances[
        appearances["competition_id"].isin(TOP5)
        & (appearances["date"] >= WINDOW_START)
    ]
    return pd.Index(sorted(dentro["player_id"].unique()), name="player_id")


def load_careers(
    appearances: pd.DataFrame | None = None, *, only_population: bool = False
) -> pd.DataFrame:
    """Una riga per **giocatore × club × competizione × stagione**.

    Per default copre **tutti i 29.531 giocatori** del dataset (197.812 righe):
    è la base da cui partire se un domani si allarga oltre le 5 leghe. Con
    ``only_population=True`` si restringe ai 7.709 delle nostre leghe (89.625
    righe).

    ⚠️ È una tabella `post`: contiene l'intera carriera nota, futuro compreso
    rispetto a qualunque partita passata. Per fare feature usa `career_before`.

    Colonne: `player_id`, `player_name`, `club_id`, `competition_id`, `season`,
    `date_from`, `date_to`, `appearances`, `goals`, `assists`, `minutes`,
    `yellow_cards`, `red_cards`, `is_top5`, `fonte`.
    """
    if appearances is None:
        appearances = _load_appearances()
    df = appearances
    if only_population:
        df = df[df["player_id"].isin(population(appearances))]
    df = df.copy()
    df["season"] = season_of(df["date"])

    out = (
        df.groupby(["player_id", "player_club_id", "competition_id", "season"],
                   as_index=False)
        .agg(
            player_name=("player_name", "first"),
            date_from=("date", "min"),
            date_to=("date", "max"),
            appearances=("date", "size"),
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            minutes=("minutes_played", "sum"),
            yellow_cards=("yellow_cards", "sum"),
            red_cards=("red_cards", "sum"),
        )
        .rename(columns={"player_club_id": "club_id"})
    )
    out["is_top5"] = out["competition_id"].isin(TOP5)
    out["fonte"] = FONTE_STRATO1
    return out.sort_values(["player_id", "date_from"]).reset_index(drop=True)


def career_before(
    as_of: str | pd.Timestamp,
    appearances: pd.DataFrame | None = None,
    player_ids: list[int] | None = None,
) -> pd.DataFrame:
    """⏱️ LA FORMA SICURA (R8): la carriera **fino al giorno prima** di `as_of`.

    Restituisce, per ogni giocatore, i totali di carriera **strettamente
    precedenti** ad `as_of`. È questa la funzione da usare per costruire una
    feature: chiamarla con la data della partita da prevedere non può, per
    costruzione, guardare il futuro.

    Colonne: `appearances_before`, `goals_before`, `assists_before`,
    `minutes_before`, `top5_appearances_before`, `other_appearances_before`,
    `competitions_before`, `clubs_before`, `first_appearance`, `censored_left`.

    `censored_left` è **True** quando la prima presenza nota cade al bordo del
    dataset: per quei giocatori i totali sono un **limite inferiore**, non una
    misura. Ignorarlo significa credere che Ancelotti abbia esordito nel 2012
    (§D.2 di `docs/AUDIT_FONTI_GIOCATORI.md`: lo stesso errore è già costato
    155 allenatori su 496).
    """
    as_of = pd.Timestamp(as_of)
    if appearances is None:
        appearances = _load_appearances()
    df = appearances[appearances["date"] < as_of]
    if player_ids is not None:
        df = df[df["player_id"].isin(player_ids)]

    out = df.groupby("player_id").agg(
        appearances_before=("date", "size"),
        goals_before=("goals", "sum"),
        assists_before=("assists", "sum"),
        minutes_before=("minutes_played", "sum"),
        competitions_before=("competition_id", "nunique"),
        clubs_before=("player_club_id", "nunique"),
        first_appearance=("date", "min"),
    )
    top5 = (
        df[df["competition_id"].isin(TOP5)].groupby("player_id").size()
        .rename("top5_appearances_before")
    )
    out = out.join(top5).fillna({"top5_appearances_before": 0})
    out["top5_appearances_before"] = out["top5_appearances_before"].astype(int)
    out["other_appearances_before"] = (
        out["appearances_before"] - out["top5_appearances_before"]
    )
    out["censored_left"] = out["first_appearance"] <= CENSORING_CUTOFF
    return out


def load_wikipedia_careers(solo_ok: bool = True) -> pd.DataFrame:
    """STRATO 2: le tappe estratte dall'infobox di Wikipedia.

    ⚖️ **Queste righe sono CC BY-SA 4.0** (vedi
    `data/carriere_wikipedia/README.md`). Restano in una tabella **separata**
    proprio perché lo share-alike non si estenda per contatto a tutto il resto.

    Ritorna un DataFrame vuoto — non alza — se la raccolta non è ancora stata
    eseguita: lo strato 2 è opzionale per costruzione.
    """
    import json

    # Il deliverable versionato ha la precedenza sul file di lavoro: cosi' chi
    # clona il repo legge le carriere senza dover rieseguire la raccolta.
    versato = ROOT_DATA / "carriere_wikipedia" / "tappe.csv.gz"
    if versato.exists():
        # `low_memory=False`: le colonne del verdetto Wikidata sono vuote per la
        # grande maggioranza delle righe (solo 483 giocatori sono stati dirimenti),
        # quindi a blocchi pandas ne inferisce tipi diversi e avvisa. Il tipo
        # giusto e' uno solo, e leggere in un colpo lo rende deterministico.
        return pd.read_csv(versato, low_memory=False)

    percorso = ROOT_DATA / "carriere_wikipedia" / "esiti.jsonl"
    if not percorso.exists():
        return pd.DataFrame(columns=[
            "player_id", "ordine", "club", "anno_da", "anno_a", "aperta",
            "presenze", "gol", "prestito", "giovanili", "source_url",
            "fonte", "licenza",
        ])
    righe = []
    with percorso.open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except json.JSONDecodeError:
                continue          # riga tronca da un'interruzione: si salta
            if solo_ok and r.get("stato") != "ok":
                continue
            righe.extend(r.get("tappe", []))
    return pd.DataFrame(righe)


def wikipedia_progress() -> dict:
    """Stato della raccolta dello strato 2 (è lunga: ~1s a giocatore)."""
    import json

    percorso = ROOT_DATA / "carriere_wikipedia" / "esiti.jsonl"
    if not percorso.exists():
        return {"tentati": 0}
    stati: dict[str, int] = {}
    tappe = 0
    with percorso.open() as f:
        for riga in f:
            try:
                r = json.loads(riga)
            except json.JSONDecodeError:
                continue
            stati[r["stato"]] = stati.get(r["stato"], 0) + 1
            tappe += len(r.get("tappe", []))
    return {"tentati": sum(stati.values()), "tappe": tappe, **stati}


def load_database(appearances: pd.DataFrame | None = None) -> pd.DataFrame:
    """⭐ **IL DATABASE CARRIERE — uno solo, non due.**

    Una riga per tappa di carriera, da **entrambe le fonti**, con `fonte` a
    dire da quale viene. È questa la funzione da usare.

    - `fonte = "appearances/player-scores"` → misurata partita per partita,
      48 competizioni, **dal 2012-07-03**, con le date esatte;
    - `fonte = "wikipedia"` → dall'infobox, copre **anche prima del 2012**, le
      seconde divisioni e i campionati extra-europei, ma con **grana annuale**.

    Il `club_id` è normalizzato **su entrambe** le fonti: le righe Wikipedia lo
    ricevono da `club_matching`, con `aggancio` a dire se è `univoco`,
    `ambiguo` o `assente`. Le righe dello strato 1 hanno `aggancio = "nativo"`
    perché il `club_id` ce l'hanno per costruzione.

    ⚠️ **NON sommare le presenze fra le due fonti.** Contano cose diverse:
    Wikipedia conta il solo campionato nazionale, `appearances` conta tutte le
    48 competizioni. Le righe si impilano, i numeri no.

    ⏱️ La grana temporale è disomogenea (date esatte contro anni): un taglio
    R8 sulle righe Wikipedia è approssimato all'anno.
    """
    from .club_matching import Agganciatore

    s1 = load_careers(appearances)
    s1 = s1.rename(columns={"date_from": "data_da", "date_to": "data_a"})
    s1["anno_da"] = s1["data_da"].dt.year
    s1["anno_a"] = s1["data_a"].dt.year
    s1["aggancio"] = "nativo"
    s1["giovanili"] = False
    s1["prestito"] = pd.NA

    s2 = load_wikipedia_careers()
    if not s2.empty:
        s2 = s2.rename(columns={"club": "club_name", "presenze": "appearances",
                                "gol": "goals"})
        agg = Agganciatore().aggancia_serie(s2["club_name"])
        s2["club_id"] = agg["club_id_agganciato"]
        s2["aggancio"] = agg["aggancio"]
        s2["is_top5"] = pd.NA
        # il nome del giocatore non sta nella tappa: si prende dallo strato 1,
        # che e' sullo stesso `player_id` (nessun matching per nome)
        nomi = s1.drop_duplicates("player_id").set_index("player_id")["player_name"]
        s2["player_name"] = s2["player_id"].map(nomi)

    colonne = ["player_id", "player_name", "club_id", "club_name",
               "competition_id", "season", "data_da", "data_a", "anno_da",
               "anno_a", "appearances", "goals", "assists", "minutes",
               "is_top5", "giovanili", "prestito", "aggancio", "fonte"]
    out = pd.concat([s1, s2], ignore_index=True, sort=False)
    for c in colonne:
        if c not in out.columns:
            out[c] = pd.NA
    return out[colonne + [c for c in out.columns if c not in colonne]]


def coverage_report(appearances: pd.DataFrame | None = None) -> dict:
    """Cosa lo strato 1 copre e cosa no — i numeri che decidono se serve il 2.

    Va rieseguito, non citato a memoria: è il criterio con cui si decide se
    pagare il costo (e la licenza share-alike) dello strato Wikipedia.
    """
    if appearances is None:
        appearances = _load_appearances()
    pop = population(appearances)
    sub = appearances[appearances["player_id"].isin(pop)]

    primo_top = (
        sub[sub["competition_id"].isin(TOP5) & (sub["date"] >= WINDOW_START)]
        .groupby("player_id")["date"].min()
    )
    primo_qls = sub.groupby("player_id")["date"].min()
    storia = (primo_top - primo_qls).dt.days

    return {
        "giocatori": len(pop),
        "competizioni": int(sub["competition_id"].nunique()),
        "con_storia_precedente": int((storia > 0).sum()),
        "senza_storia_precedente": int((storia == 0).sum()),
        "censurati_a_sinistra": int((primo_qls <= CENSORING_CUTOFF).sum()),
        "con_presenze_fuori_top5": int(
            sub[~sub["competition_id"].isin(TOP5)]["player_id"].nunique()
        ),
        "prima_data": str(sub["date"].min().date()),
    }
