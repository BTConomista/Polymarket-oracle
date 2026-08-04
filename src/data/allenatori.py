"""⚽ IL DATABASE ALLENATORI — strato 1: chi era in panchina, partita per partita.

`load_partite()` è la funzione da usare: una riga per **(partita, club)**, con
l'allenatore di quel club e quello avversario. Da lì si derivano i mandati
(`panchine()`), i cambi in corsa (`cambi_panchina()`) e l'esperienza
accumulata (`esperienza_prima()`).

FONTE: `games.csv` del dataset `davidcariboo/player-scores` (Transfermarkt via
Kaggle), lo **stesso** già usato per i valori rosa (Fase 67) e per le carriere
(`careers.py`). Nessuna fonte nuova, nessuna licenza nuova: il file era
semplicemente l'unico dei grandi mai importato. Vintage e sha256 in
`files/README.md`.

PERIMETRO. Il file copre **88.958 partite** in 65 competizioni dal 2006-06-09;
le nostre 5 leghe × 9 stagioni sono **16.111 partite**, cioè esattamente le
righe degli snapshot congelati. `load_partite()` le dà tutte per default:
l'esperienza di un allenatore si conta anche fuori (coppe europee, altri
campionati), ed è metà del punto di questo strato.

⚠️ TRE COSE DA SAPERE PRIMA DI USARLO (tutte misurate, non ipotesi).

1. **IL NOME NON È UN'IDENTITÀ.** La fonte non ha un id-allenatore: solo una
   stringa libera. `manager_key` (nome normalizzato, accenti tolti) ripara il
   caso facile — la fonte ha cambiato grafia in corsa allo stesso uomo, e le
   due grafie hanno intervalli **disgiunti**: «Ivan Juric» 292 partite fino al
   2025-11-05 contro «Ivan Jurić» 11 dal 2025-08-24, «Bruno Génésio» 346
   contro «Bruno Genesio» 34 dal 2025-08-17. Nel perimetro sono 2 gruppi su
   496 nomi (485 partite = 3,01%), globalmente 36 su 7.031.
   Ma **non ripara il caso opposto**, che è quello pericoloso: due uomini
   diversi con lo stesso nome diventano una riga sola. `Míchel` sono **due**
   allenatori spagnoli e il 2022-10-02 la stessa stringa siede su **due
   panchine lo stesso giorno**, Girona e Olympiakos. `conflitti_identita()`
   cerca esattamente questo: 11 nomi globali sono **dimostrabilmente** ≥2
   persone. Sono un limite dichiarato, non un bug da nascondere: risolverli
   richiede una fonte di identità esterna.
   ✅ **Sciolto alla Fase 141** con i Q-id di Wikidata, e la divisione NON è
   quella che questa riga diceva prima: **Míchel Sánchez** (Miguel Ángel
   Sánchez Muñoz, Q-id unico) ha Rayo 2017-19, Huesca 2019-21 e Girona dal
   2021 — *Rayo compreso*, che la prima stesura attribuiva all'altro;
   **Míchel González** (José Miguel González) ha Málaga e Getafe nel nostro
   perimetro, più Siviglia, Olympiakos, Marsiglia e Al-Qadsiah fuori.
   ⚠️ E `luis castro`, l'altro conflitto del perimetro, **non si divide qui**:
   i suoi due mandati nostri (Nantes, Levante) sono la stessa persona (nato il
   1961-09-03); la collisione del 2019 è fra una partita del perimetro e una
   fuori. Un nome ambiguo *globalmente* può essere non ambiguo nel perimetro,
   e i due conti non vanno confusi.

2. **«ESPERIENZA GLOBALE» NON ESISTE: ESISTE «ESPERIENZA VISIBILE AL
   DATASET».** Il file per le top-5 comincia il **2012-08-10**, e i campionati
   extra-europei (Brasile, Argentina, MLS, Giappone, Arabia) entrano solo dal
   **2025**. Contare le partite precedenti e chiamarlo «esperienza in
   carriera» produce falsi conclamati — Ancelotti «esordisce» in Serie A nel
   2018, Mourinho in Premier nel 2021 — perché la feature legge il **bordo del
   dataset** come un esordio. Per questo `esperienza_prima()` restituisce
   `censurata`: quando è True i totali sono un **limite inferiore**, non una
   misura (§D.2 di `docs/AUDIT_FONTI_GIOCATORI.md`, dove il difetto costa 155
   allenatori su 496).

3. **`clubs.coach_name` È UNA TRAPPOLA R8, E NON VA USATA.** È l'allenatore
   **corrente** del club (403/796 non nulli, senza data): applicata a una
   partita del 2019 le attribuisce il tecnico di oggi. Questo modulo non la
   legge, e `panchine()` esiste anche per non doverla mai guardare.

⏱️ REGOLA R8 — quali colonne sono note prima del fischio.
`pre`: `date`, `club_id`, `avversario_id`, `casa`, `competition_id`, `season`,
`round`, `stadio`, `allenatore`/`manager_key` e i loro gemelli avversari
(l'allenatore si sa da giorni; è anzi uno dei pochi dati davvero `pre` di
questo progetto). `post`: `gol_fatti`, `gol_subiti`, `esito`, `posizione`,
`spettatori`, `arbitro` (designato ~2 giorni prima, ma qui lo leggiamo a
partita finita), `formazione`. La forma sicura per una feature è
`esperienza_prima(as_of=data_partita)`, che per costruzione non può guardare
avanti.

Il modulo non è letto da `backtest.py` né da alcun modello: è infrastruttura.
Il valore predittivo dell'allenatore **non è mai stato misurato** su nessun
mercato di questo progetto, e visto il tetto informativo delle 100+ fasi
precedenti non è da dare per scontato che esista.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "files" / "player_scores"
GAMES = DATA_DIR / "games.csv.gz"
COMPETIZIONI = DATA_DIR / "competitions.csv.gz"

# Le 5 leghe che il progetto modella (stessi codici di careers.py).
TOP5 = ("IT1", "GB1", "ES1", "L1", "FR1")
# Le 9 stagioni degli snapshot congelati: 2017-18 ... 2025-26.
STAGIONI = tuple(range(2017, 2026))

# Bordo sinistro del dataset PER LE TOP-5. Prima di qui non c'è nulla, e non
# perché non si giocasse: è il punto in cui la fonte comincia a raccogliere.
INIZIO_TOP5 = pd.Timestamp("2012-08-10")
# Finestra di grazia per dire «questo allenatore era già in carica quando la
# competizione è entrata nel dataset»: un mercato estivo (~90 giorni). Chi
# esordisce dentro la finestra è CENSURATO, non esordiente.
GRAZIA_CENSURA = pd.Timedelta(days=90)

FONTE = "games/player-scores"

# Colonne per disponibilità temporale (R8). Chi costruisce una feature legge
# qui, non la propria memoria.
COLONNE_PRE = (
    "game_id", "competition_id", "competition_type", "season", "date",
    "club_id", "club_name", "casa", "avversario_id", "avversario_name",
    "allenatore", "manager_key", "allenatore_avv", "manager_key_avv",
    "round", "stadio",
)
COLONNE_POST = (
    "gol_fatti", "gol_subiti", "esito", "posizione", "posizione_avv",
    "spettatori", "arbitro", "formazione", "formazione_avv",
)


def normalizza_nome(nome: object) -> str:
    """Il nome dell'allenatore ridotto a chiave: accenti via, minuscolo.

    NFKD scompone «ć» in «c» + segno combinante, e il filtro sui combinanti
    toglie il secondo: è così che «Ivan Jurić» e «Ivan Juric» diventano la
    stessa chiave. Trattino, apostrofo e punto diventano spazio (per
    «Sanchez-Flores» / «Sanchez Flores» e per le iniziali puntate), e gli
    spazi multipli collassano.

    ⚠️ Non è un'identità: due omonimi restano una chiave sola. Vedi
    `conflitti_identita()`.
    """
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return ""
    testo = unicodedata.normalize("NFKD", str(nome))
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = testo.lower().replace("-", " ").replace("'", " ").replace(".", " ")
    return re.sub(r"\s+", " ", testo).strip()


def _leggi_games() -> pd.DataFrame:
    if not GAMES.exists():
        raise FileNotFoundError(
            f"{GAMES} non trovato: importa il dataset col workflow GitHub "
            f"Actions (.github/workflows/import_dataset.yml — push del file "
            f".github/import-dataset-trigger)")
    df = pd.read_csv(GAMES, low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


def load_competizioni() -> pd.DataFrame:
    """`competitions.csv`: tipo, paese e confederazione delle 65 competizioni.

    Serve a distinguere campionato / coppa nazionale / coppa internazionale /
    nazionali — cioè il primo mattone del `peso_competizione` che §1.10 del
    piano vorrebbe (una finale di Champions ≠ un girone minore). Qui il dato
    grezzo; il peso, quando si farà, è una scelta dichiaratamente soggettiva
    e non vive in questo modulo.
    """
    return pd.read_csv(COMPETIZIONI)


def load_partite(
    games: pd.DataFrame | None = None,
    *,
    solo_top5: bool = False,
    stagioni: tuple[int, ...] | None = None,
    solo_con_allenatore: bool = True,
) -> pd.DataFrame:
    """⭐ La vista lunga: **una riga per (partita, club)**, con l'allenatore.

    Ogni partita produce due righe (casa e trasferta), speculari: nella riga di
    un club, `allenatore` è il suo e `allenatore_avv` quello di fronte. È la
    forma che serve per costruire il pannello per-allenatore senza pivot — e
    quella che `club_games.csv` offrirebbe già pronta, se non fosse un
    **duplicato esatto** di `games.csv` (verificato: 0 celle divergenti su
    1.957.076, ricostruito in otto righe).

    Con `solo_top5=True` e `stagioni=STAGIONI` si ottiene il perimetro degli
    snapshot: 16.111 partite → 32.222 righe.

    `solo_con_allenatore=True` (default) scarta le righe senza allenatore:
    sono **1.688 club-partita su 177.916** globalmente (0,95%) e **2 su
    32.222** nel perimetro — la coda di una sola partita, Nantes-Tolosa del
    2026-05-17, che alla data dello snapshot la fonte non aveva ancora
    riempito (le manca anche l'arbitro, e nessun giocatore le è associato).
    Tenerle significherebbe spezzare un mandato in due per una riga vuota.
    """
    if games is None:
        games = _leggi_games()
    df = games
    if solo_top5:
        df = df[df["competition_id"].isin(TOP5)]
    if stagioni is not None:
        df = df[df["season"].isin(stagioni)]

    def lato(me: str, altro: str, casa: bool) -> pd.DataFrame:
        return pd.DataFrame({
            "game_id": df["game_id"].to_numpy(),
            "competition_id": df["competition_id"].to_numpy(),
            "competition_type": df["competition_type"].to_numpy(),
            "season": df["season"].to_numpy(),
            "date": df["date"].to_numpy(),
            "club_id": df[f"{me}_club_id"].to_numpy(),
            "club_name": df[f"{me}_club_name"].to_numpy(),
            "casa": casa,
            "avversario_id": df[f"{altro}_club_id"].to_numpy(),
            "avversario_name": df[f"{altro}_club_name"].to_numpy(),
            "allenatore": df[f"{me}_club_manager_name"].to_numpy(),
            "allenatore_avv": df[f"{altro}_club_manager_name"].to_numpy(),
            "gol_fatti": df[f"{me}_club_goals"].to_numpy(),
            "gol_subiti": df[f"{altro}_club_goals"].to_numpy(),
            "posizione": df[f"{me}_club_position"].to_numpy(),
            "posizione_avv": df[f"{altro}_club_position"].to_numpy(),
            "formazione": df[f"{me}_club_formation"].to_numpy(),
            "formazione_avv": df[f"{altro}_club_formation"].to_numpy(),
            "round": df["round"].to_numpy(),
            "stadio": df["stadium"].to_numpy(),
            "spettatori": df["attendance"].to_numpy(),
            "arbitro": df["referee"].to_numpy(),
        })

    out = pd.concat([lato("home", "away", True), lato("away", "home", False)],
                    ignore_index=True)
    if solo_con_allenatore:
        out = out[out["allenatore"].notna()]
    out["manager_key"] = out["allenatore"].map(normalizza_nome)
    out["manager_key_avv"] = out["allenatore_avv"].map(normalizza_nome)
    out["esito"] = pd.Series(
        ["V" if f > s else ("N" if f == s else "P")
         for f, s in zip(out["gol_fatti"], out["gol_subiti"])],
        index=out.index)
    out["is_top5"] = out["competition_id"].isin(TOP5)
    out["fonte"] = FONTE
    colonne = list(COLONNE_PRE) + list(COLONNE_POST) + ["is_top5", "fonte"]
    return (out[colonne]
            .sort_values(["date", "game_id", "casa"], ascending=[True, True, False])
            .reset_index(drop=True))


def _aggrega_mandati(df: pd.DataFrame, chiave: str) -> pd.DataFrame:
    out = df.groupby(chiave, as_index=False).agg(
        club_id=("club_id", "first"),
        club_name=("club_name", "last"),
        manager_key=("manager_key", "first"),
        allenatore=("allenatore", "last"),
        data_da=("date", "min"),
        data_a=("date", "max"),
        partite=("game_id", "size"),
        gol_fatti=("gol_fatti", "sum"),
        gol_subiti=("gol_subiti", "sum"),
        competizioni=("competition_id", "nunique"),
    )
    esiti = (df.pivot_table(index=chiave, columns="esito", values="game_id",
                            aggfunc="size").reindex(columns=["V", "N", "P"])
             .fillna(0).astype(int))
    return out.merge(esiti, left_on=chiave, right_index=True, how="left")


def panchine(
    partite: pd.DataFrame | None = None,
    *,
    ricuci: bool = False,
    max_partite_interruzione: int = 1,
) -> pd.DataFrame:
    """I **mandati**: una riga per (club, allenatore, periodo continuo).

    Derivata, non raccolta: si ordinano le partite di ogni club per data e si
    taglia dove cambia `manager_key`. Due passaggi dello stesso allenatore
    nello stesso club sono **due mandati**, non uno — è la ragione per cui
    l'intervallo grezzo (prima e ultima partita di quel nome in quel club) non
    basta: Allegri al Milan risulterebbe in carica dal 2010 al 2026 e
    «sovrapposto» a se stesso alla Juventus per 3.546 giorni.

    ⚠️ **PASSA LA TIMELINE COMPLETA, non la sola lega.** Il taglio deve vedere
    campionato, coppa nazionale ed Europa in un unico ordine di date: è quella
    la timeline vera di una panchina. Calcolare i mandati sul solo campionato
    ne **nasconde 284** sui club del perimetro (906 contro 1.190), quasi tutti
    traghettatori di una partita sola in coppa.

    ⚠️ **IL CAMPO NON È IL MANDATO CONTRATTUALE: È CHI SEDEVA IN PANCHINA
    QUELLA PARTITA.** Lo dimostra il dato stesso: al Lipsia, fra il 20/11 e
    l'11/12/2021, Marsch risulta in Bundesliga (28/11, 3/12) e Beierlorzer in
    Champions (24/11, 7/12) — un contratto non si alterna a giorni alterni, un
    vice in panchina per una partita sì. Il pattern **A → X → A** (lo stesso
    allenatore prima e dopo) è la firma di quei casi: squalifica, malattia,
    turno di coppa lasciato al vice. Sono **836 mandati su 13.810 (6,05%)**
    globalmente, di cui 412 di una partita sola, e **62 su 1.105** nella
    finestra del perimetro — Stuivenberg per Arteta il 1/1/2022, Vivas per
    Simeone il 4/1/2025, Hermann per Heynckes il 10/2/2018.
    La colonna `interruzione` li marca **sempre**. Con `ricuci=True` vengono
    riassorbiti nel mandato che li circonda (che è ciò che serve per contare i
    veri cambi in panchina), e il mandato riporta `interruzioni` e
    `partite_altrui`. Il default è **False**: marcare è una descrizione,
    ricucire è una trasformazione, e la seconda si chiede.

    Colonne: `club_id`, `club_name`, `manager_key`, `allenatore`, `mandato`
    (progressivo del club), `data_da`, `data_a`, `partite`, `V`, `N`, `P`,
    `gol_fatti`, `gol_subiti`, `competizioni`, `interruzione`, `interruzioni`,
    `partite_altrui`, `precedente`, `successivo`.
    `precedente`/`successivo` sono le chiavi dei mandati confinanti nello
    stesso club (NaN al bordo della finestra osservata): servono all'effetto
    «nuovo allenatore» senza doverli ricalcolare.
    """
    if partite is None:
        partite = load_partite()
    df = partite.sort_values(["club_id", "date", "game_id"]).copy()
    cambio = df["manager_key"] != df.groupby("club_id")["manager_key"].shift()
    df["spell_id"] = cambio.cumsum()

    out = _aggrega_mandati(df, "spell_id")
    out = out.sort_values(["club_id", "data_da"]).reset_index(drop=True)
    prima = out.groupby("club_id")["manager_key"].shift()
    dopo = out.groupby("club_id")["manager_key"].shift(-1)
    out["interruzione"] = prima.notna() & (prima == dopo)

    if ricuci:
        assorbibile = out["interruzione"] & (
            out["partite"] <= max_partite_interruzione)
        # `gruppo`: il mandato che segue un'interruzione assorbita torna a
        # essere quello di due righe prima. `ospite`: a quale mandato va
        # attribuita l'interruzione — l'ultimo **sopravvissuto** dello stesso
        # club, non semplicemente la riga prima: due interruzioni di fila
        # attribuirebbero la seconda a una riga che non esiste più.
        spell = out["spell_id"].to_list()
        gruppo = list(spell)
        ospite: dict[int, int] = {}
        club_corrente, ultimo_vivo = None, None
        for i in range(len(out)):
            club = out["club_id"].iloc[i]
            if club != club_corrente:
                club_corrente, ultimo_vivo = club, None
            if assorbibile.iloc[i] and ultimo_vivo is not None:
                ospite[spell[i]] = ultimo_vivo
                continue
            if (i >= 2 and spell[i - 1] in ospite
                    and out["club_id"].iloc[i - 2] == club
                    and out["manager_key"].iloc[i] ==
                    out["manager_key"].iloc[i - 2]):
                gruppo[i] = gruppo[i - 2]
            ultimo_vivo = gruppo[i]
        mappa = dict(zip(spell, gruppo))
        df["gruppo"] = df["spell_id"].map(mappa)
        assorbite = set(ospite)
        # le partite dell'interruzione restano in `load_partite`: qui contano
        # solo come "giocate da un altro" dentro l'intervallo del mandato
        altrui = df[df["spell_id"].isin(assorbite)].copy()
        vive = df[~df["spell_id"].isin(assorbite)]
        out = _aggrega_mandati(vive, "gruppo").rename(
            columns={"gruppo": "spell_id"})
        out = out.sort_values(["club_id", "data_da"]).reset_index(drop=True)
        altrui["ospite"] = altrui["spell_id"].map(ospite)
        conteggi = altrui.groupby("ospite").agg(
            partite_altrui=("game_id", "size"),
            interruzioni=("spell_id", "nunique"))
        out = out.merge(conteggi, left_on="spell_id", right_index=True,
                        how="left")
        out[["partite_altrui", "interruzioni"]] = (
            out[["partite_altrui", "interruzioni"]].fillna(0).astype(int))
        prima = out.groupby("club_id")["manager_key"].shift()
        dopo = out.groupby("club_id")["manager_key"].shift(-1)
        out["interruzione"] = prima.notna() & (prima == dopo)
    else:
        out["partite_altrui"] = 0
        out["interruzioni"] = 0

    out["mandato"] = out.groupby("club_id").cumcount() + 1
    out["precedente"] = out.groupby("club_id")["manager_key"].shift()
    out["successivo"] = out.groupby("club_id")["manager_key"].shift(-1)
    return out[["club_id", "club_name", "manager_key", "allenatore", "mandato",
                "data_da", "data_a", "partite", "V", "N", "P", "gol_fatti",
                "gol_subiti", "competizioni", "interruzione", "interruzioni",
                "partite_altrui", "precedente", "successivo"]]


def cambi_panchina(
    panchine_df: pd.DataFrame | None = None,
    *,
    solo_in_stagione: bool = True,
) -> pd.DataFrame:
    """Gli **eventi di cambio**: un nuovo allenatore si siede su una panchina.

    Una riga per subentro, con chi esce, chi entra, la data della prima partita
    del nuovo e i giorni dall'ultima del precedente. È il materiale
    dell'«effetto rimbalzo» (F9 dell'audit) — che questo modulo **non misura**:
    lo prepara.

    `solo_in_stagione=True` tiene solo i cambi avvenuti **dentro** una stagione
    (stessa stagione calcistica fra l'uscita e l'entrata, taglio al 1° luglio):
    un cambio estivo è una scelta programmata, un esonero a novembre no, e
    confonderli è il modo più rapido per misurare due cose diverse insieme.
    """
    if panchine_df is None:
        panchine_df = panchine()
    df = panchine_df[panchine_df["mandato"] > 1].copy()
    prec = panchine_df.set_index(["club_id", "mandato"])
    chiave = list(zip(df["club_id"], df["mandato"] - 1))
    df["data_uscita"] = prec["data_a"].reindex(chiave).to_numpy()
    df["partite_precedente"] = prec["partite"].reindex(chiave).to_numpy()
    df = df.rename(columns={"manager_key": "entra", "precedente": "esce",
                            "data_da": "data_entrata"})
    df["giorni_di_stacco"] = (df["data_entrata"] - df["data_uscita"]).dt.days
    df["stagione_uscita"] = _stagione(df["data_uscita"])
    df["stagione_entrata"] = _stagione(df["data_entrata"])
    df["in_stagione"] = df["stagione_uscita"] == df["stagione_entrata"]
    if solo_in_stagione:
        df = df[df["in_stagione"]]
    return df[["club_id", "club_name", "esce", "entra", "data_uscita",
               "data_entrata", "giorni_di_stacco", "stagione_entrata",
               "in_stagione", "partite_precedente", "partite"]].rename(
        columns={"partite": "partite_successivo"}).reset_index(drop=True)


def _stagione(date: pd.Series) -> pd.Series:
    """Stagione calcistica `2017-18`, taglio al 1° luglio (come careers.py)."""
    anno = date.dt.year.where(date.dt.month >= 7, date.dt.year - 1)
    return anno.astype("Int64").astype(str) + "-" + \
        (anno + 1).astype("Int64").astype(str).str[-2:]


def conflitti_identita(
    partite: pd.DataFrame | None = None,
    *,
    giorni: int = 0,
) -> pd.DataFrame:
    """🔎 I nomi che **non possono** essere una persona sola.

    Il test è di impossibilità fisica, nello spirito della regola R5: un
    allenatore non può stare su due panchine diverse lo stesso giorno. Con
    `giorni=0` il verdetto è netto e non ammette repliche; alzando la finestra
    (`giorni=7`) si trovano anche i casi molto probabili, al prezzo di
    includere i passaggi lampo veri fra due club.

    Non risolve niente: **elenca**. Sciogliere un omonimo richiede una fonte di
    identità esterna, che questo strato non ha. Serve a impedire che un nome
    ambiguo entri in una feature senza che nessuno lo sappia.

    Colonne: `manager_key`, `date_a`, `club_a`, `date_b`, `club_b`, `giorni`.
    """
    if partite is None:
        partite = load_partite()
    df = (partite[["manager_key", "date", "club_id", "club_name"]]
          .drop_duplicates().sort_values(["manager_key", "date"]))
    finestra = pd.Timedelta(days=giorni)
    righe = []
    for chiave, gruppo in df.groupby("manager_key", sort=False):
        if not chiave or gruppo["club_id"].nunique() < 2:
            continue
        g = gruppo.reset_index(drop=True)
        date = g["date"].to_numpy()
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if date[j] - date[i] > finestra:
                    break
                if g["club_id"][j] != g["club_id"][i]:
                    righe.append((chiave, g["date"][i], g["club_name"][i],
                                  g["date"][j], g["club_name"][j],
                                  (g["date"][j] - g["date"][i]).days))
    return pd.DataFrame(righe, columns=["manager_key", "date_a", "club_a",
                                        "date_b", "club_b", "giorni"])


def _inizio_competizioni(games: pd.DataFrame) -> pd.Series:
    """Prima data osservata di ogni competizione: il bordo, competizione per
    competizione. Non è uno solo: le top-5 partono nel 2012, il Brasile nel
    2025 — un bordo unico dichiarerebbe «esordiente» mezzo campionato."""
    return games.groupby("competition_id")["date"].min()


def esperienza_prima(
    as_of: str | pd.Timestamp,
    partite: pd.DataFrame | None = None,
    *,
    manager_keys: list[str] | None = None,
) -> pd.DataFrame:
    """⏱️ LA FORMA SICURA (R8): l'esperienza **fino al giorno prima** di `as_of`.

    Per ogni allenatore, i totali **strettamente precedenti** ad `as_of`.
    Chiamarla con la data della partita da prevedere non può, per costruzione,
    guardare avanti.

    Colonne: `partite_prima`, `top5_prima`, `altro_prima`, `club_prima`,
    `competizioni_prima`, `V_prima`, `N_prima`, `P_prima`, `primo_incarico`,
    `censurata`.

    ⚠️ `censurata=True` significa che il primo incarico visibile cade entro 90
    giorni dall'inizio della competizione in cui compare: il dataset comincia
    lì, non la carriera. Per quegli allenatori ogni totale è un **limite
    inferiore**, ed è il motivo per cui questa funzione non si chiama
    `esperienza_globale`.

    ⚠️⚠️ **E `censurata=False` NON vuol dire «esperienza completa».** Il flag
    vede una sola delle due censure — quella temporale, al bordo della
    competizione. L'altra è di **copertura**, e dall'interno del dataset non è
    rilevabile: chi ha allenato dove la fonte non guarda (seconde divisioni
    mai coperte, campionati extra-europei entrati solo nel 2025, giovanili)
    risulta senza passato e senza flag. Il controesempio è Guardiola: prima
    partita visibile il 2013-07-27 col Bayern, `censurata=False`, e quattro
    stagioni al Barcellona (2008-2012) invisibili perché la Liga nel dataset
    comincia nell'agosto 2012.
    """
    as_of = pd.Timestamp(as_of)
    if partite is None:
        partite = load_partite()
    bordi = _inizio_competizioni(partite)
    df = partite[partite["date"] < as_of]
    if manager_keys is not None:
        df = df[df["manager_key"].isin(manager_keys)]

    out = df.groupby("manager_key").agg(
        partite_prima=("game_id", "size"),
        club_prima=("club_id", "nunique"),
        competizioni_prima=("competition_id", "nunique"),
        primo_incarico=("date", "min"),
    )
    top5 = (df[df["is_top5"]].groupby("manager_key").size()
            .rename("top5_prima"))
    out = out.join(top5).fillna({"top5_prima": 0})
    out["top5_prima"] = out["top5_prima"].astype(int)
    out["altro_prima"] = out["partite_prima"] - out["top5_prima"]
    esiti = (df.pivot_table(index="manager_key", columns="esito",
                            values="game_id", aggfunc="size")
             .reindex(columns=["V", "N", "P"]).fillna(0).astype(int)
             .rename(columns={"V": "V_prima", "N": "N_prima", "P": "P_prima"}))
    out = out.join(esiti)

    prima_riga = df.loc[df.groupby("manager_key")["date"].idxmin()]
    comp_esordio = prima_riga.set_index("manager_key")["competition_id"]
    bordo = comp_esordio.map(bordi)
    out["censurata"] = out["primo_incarico"] <= (bordo + GRAZIA_CENSURA)
    return out[["partite_prima", "top5_prima", "altro_prima", "club_prima",
                "competizioni_prima", "V_prima", "N_prima", "P_prima",
                "primo_incarico", "censurata"]]


def rapporto_copertura(games: pd.DataFrame | None = None) -> dict:
    """Cosa questo strato copre e cosa no — i numeri da rieseguire, non citare.

    È il criterio con cui si decide se serve uno strato 2 (identità esterna) e
    quanto pesa la censura a sinistra. Nessun numero del diario su questo
    fronte va scritto a memoria: si rilegge da qui.
    """
    if games is None:
        games = _leggi_games()
    per = games[games["competition_id"].isin(TOP5)
                & games["season"].isin(STAGIONI)]
    club_partita = 2 * len(per)
    senza = int(per["home_club_manager_name"].isna().sum()
                + per["away_club_manager_name"].isna().sum())
    tutte = load_partite(games)
    perim = load_partite(games, solo_top5=True, stagioni=STAGIONI)
    conf = conflitti_identita(tutte)
    chiavi_perimetro = set(perim["manager_key"])
    mandati = panchine(tutte)
    # gli stessi club, ma i mandati tagliati sulla sola lega: è il confronto
    # che dice quanti traghettatori si perdono a guardare solo il campionato
    club_perimetro = set(perim["club_id"])
    finestra = mandati[mandati["club_id"].isin(club_perimetro)
                       & (mandati["data_a"] >= perim["date"].min())
                       & (mandati["data_da"] <= perim["date"].max())]
    return {
        "partite_totali": int(len(games)),
        "competizioni": int(games["competition_id"].nunique()),
        "prima_data": str(games["date"].min().date()),
        "ultima_data": str(games["date"].max().date()),
        "partite_perimetro": int(len(per)),
        "club_partita_perimetro": club_partita,
        "senza_allenatore_perimetro": senza,
        "copertura_perimetro": round(1 - senza / club_partita, 6),
        "nomi_grezzi_globali": int(tutte["allenatore"].nunique()),
        "chiavi_globali": int(tutte["manager_key"].nunique()),
        "nomi_grezzi_perimetro": int(perim["allenatore"].nunique()),
        "chiavi_perimetro": int(perim["manager_key"].nunique()),
        "conflitti_identita_globali": int(conf["manager_key"].nunique()),
        "conflitti_identita_perimetro": int(
            conf[conf["manager_key"].isin(chiavi_perimetro)]["manager_key"]
            .nunique()),
        "mandati_globali": int(len(mandati)),
        "interruzioni_globali": int(mandati["interruzione"].sum()),
        "interruzioni_di_una_partita": int(
            (mandati["interruzione"] & (mandati["partite"] == 1)).sum()),
        "mandati_club_perimetro_timeline_completa": int(len(finestra)),
        "mandati_club_perimetro_solo_lega": int(len(panchine(perim))),
        "interruzioni_club_perimetro": int(finestra["interruzione"].sum()),
    }
