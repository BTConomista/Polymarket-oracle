"""Carriere dei giocatori — STRATO 1: quello che abbiamo già in casa.

IL PRINCIPIO. La carriera di un giocatore si costruisce a **strati**, dal più
economico al più caro, e ogni riga dichiara **da quale strato viene** (colonna
`fonte`, regola R2). Questo modulo costruisce lo **strato 1**: le presenze che
`files/player_scores/appearances.csv.gz` contiene già, e che nessuno aveva mai
guardato come *carriera* invece che come singole partite.

QUANTO COPRE (misurato, non stimato):
- **48 competizioni**, non 5 — oltre alle nostre ci sono i massimi campionati di
  Turchia, Olanda, Portogallo, Belgio, Russia, Grecia, Scozia, Danimarca e
  Ucraina, le coppe europee (CL/EL/Conference, qualificazioni comprese), le
  coppe nazionali, le supercoppe, la Coppa d'Africa e il Mondiale per club;
- **dal 2012-07-03** in avanti;
- **6.580 dei 7.709** giocatori della popolazione hanno almeno una presenza
  fuori dalle 5 leghe: per loro una parte di carriera "esterna" c'è già.

COSA MANCA, ed è lo STRATO 2 (Wikipedia, non ancora costruito):
1. **tutto ciò che precede il 2012-07-03** — sono **1.045** giocatori censurati
   al bordo del dataset: per loro il "prima" è tagliato dai dati, non dalla
   realtà;
2. le **seconde divisioni** (nessuna nel dataset: niente Serie B, Championship,
   Segunda...);
3. i campionati **extra-europei** (niente Brasile, Argentina, MLS, Giappone...).

⚠️ LICENZA: questo strato eredita la posizione **non risolta** della fonte
Transfermarkt (`docs/DATI.md` §4). Lo strato 2 ne aprirebbe una seconda, diversa
e più vincolante: Wikipedia/DBpedia sono **CC BY-SA**, cioè share-alike virale
su un repo pubblico.

⏱️ REGOLA R8 — IL PUNTO CHE RENDE PERICOLOSA UNA TABELLA DI CARRIERE.
«Presenze in carriera» è un numero che per sua natura **include il futuro**:
la carriera di un giocatore contiene anche le partite che deve ancora giocare.
Usarlo come feature per una partita del 2019 significherebbe sapere cosa farà
nel 2024. Per questo l'API sicura NON è una colonna, è la funzione
`career_before(as_of=...)`: conta **solo** ciò che è successo prima di quella
data. La tabella piena esiste (`load_careers()`), ma è `post` e va usata solo
per descrivere, mai per prevedere.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

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
    return df.dropna(subset=["date"])


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


def load_careers(appearances: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una riga per **giocatore × club × competizione × stagione**.

    ⚠️ È una tabella `post`: contiene l'intera carriera nota, futuro compreso
    rispetto a qualunque partita passata. Per fare feature usa `career_before`.

    Colonne: `player_id`, `player_name`, `club_id`, `competition_id`, `season`,
    `date_from`, `date_to`, `appearances`, `goals`, `assists`, `minutes`,
    `yellow_cards`, `red_cards`, `is_top5`, `fonte`.
    """
    if appearances is None:
        appearances = _load_appearances()
    pop = population(appearances)
    df = appearances[appearances["player_id"].isin(pop)].copy()
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
