"""⚽ LA RACCOLTA A TRE FONTI — Serie A 2025-26 da SofaScore, Opta e Understat.

`squadre()`, `giocatori()`, `eventi()`, `eventi_opta()`, `heatmap()` sono le
funzioni da usare. Ognuna legge il file grezzo consegnato e ne restituisce una
versione **corretta in lettura**: i file su disco restano identici a come sono
arrivati (regola R3 — nessuna modifica a mano ai dati), le riparazioni vivono
qui e sono quindi verificabili, ripetibili e reversibili.

PERCHE' UNA RACCOLTA NUOVA E NON UN'ESTENSIONE DI QUELLE ESISTENTI. Porta tre
cose che il progetto non aveva per un campionato:

* **event data Opta** (`eventi_opta`, 562.672 righe): ogni tocco con coordinate
  X/Y, il secondo, i qualificatori e i tipi derivati. E' un salto di
  granularita', non piu' dati della stessa forma — vale il principio §1.10 del
  CLAUDE.md, per cui un esito negativo misurato su dati di squadra non dice
  nulla su dati piu' fini;
* **posizioni** (`heatmap`, 556.996 righe): dove ogni giocatore ha toccato;
* **arbitro, stadio, spettatori, modulo** per partita di campionato: li
  avevamo solo per le coppe.

LE CINQUE RIPARAZIONI APPLICATE IN LETTURA, e perche' ognuna.

1. **«Verona» contro «Hellas Verona»** (`squadre`, `giocatori`). Understat
   scrive `Verona`, SofaScore e WhoScored `Hellas Verona`: la fusione a monte
   ha lasciato **2 righe orfane** senza `Avversario`, con le sole colonne
   Understat. E' il caso che il §5 del CLAUDE.md porta come esempio storico
   (`TEAM_ALIASES`, «un join che indovina e' peggio di un join che dichiara di
   non sapere»). Il dato **non e' perso**: la partita esiste gia', completa,
   sotto `Hellas Verona` — le 2 righe sono un duplicato PARZIALE. Quindi si
   scartano, non si fondono: fondere significherebbe scegliere quale valore
   tenere dove le due grafie divergono, e non ce n'e' bisogno.
   Effetto: 762 righe «Totale» tornano le **760** attese (380 partite × 2).

2. **La colonna `ID partita` avvelenata** (`giocatori`). Il file ha QUATTRO
   colonne `ID partita`: le tre per-fonte hanno 380 valori distinti ciascuna e
   sono sane; la quarta, senza suffisso, ne ha **436** perche' impila tre
   sistemi di numerazione incompatibili (SofaScore ~14M, WhoScored ~1,9M,
   Understat ~30k). Un join su quella colonna appaierebbe partite diverse
   **senza dare errore**: e' il finto pieno della regola R6. Viene **rinominata
   `ID partita (misto, NON usare)`** invece che cancellata — cancellarla
   nasconderebbe che nel file c'e', e la prossima sessione la ri-troverebbe
   leggendo il grezzo.

3. **Le colonne dichiarate e VUOTE.** `Meteo (WhoScored)` e' piena allo **0,0%**
   e `Tocchi` (in `heatmap`) al **100% NaN**. Non sono un difetto se dichiarate,
   ma nessuno deve costruirci sopra credendole disponibili: `colonne_vuote()`
   le elenca, e i loader le lasciano dove sono con un avviso nel manifesto.

4. **La discordanza sui GOL: Understat perde 2 gol veri.** Il file dichiara da
   solo 6.616 righe discordanti (34,6%) nella colonna `Discordanze`: 6.597 sui
   minuti, 44 sui tiri, **2 sui gol**. I gol sono il bersaglio del modello,
   quindi sono stati istruiti uno per uno (R5):

       2026-02-15  Nikola Moro    (Bologna)   SofaScore 1 · Understat 0
       2025-12-27  Pierre Kalulu  (Juventus)  SofaScore 1 · Understat 0

   ⚠️ L'ipotesi ovvia — «sara' una convenzione sugli autogol» — e' **FALSA**, ed
   e' stata verificata invece che assunta: `Autogol` vale 0 su entrambe le
   fonti, gli eventi registrano `Gol / regular` con un `Tiro` e uno
   `scoreChange` allo stesso minuto, e il nostro snapshot football-data
   conferma il punteggio (Torino 1-2 Bologna, Pisa 0-2 Juventus). Quattro
   segnali indipendenti concordi: **e' una lacuna di Understat**, non una
   convenzione. Da cui la regola 5.

5. **Chi vince quando due fonti divergono**, dichiarato e non implicito:

   | grandezza | fonte preferita | perche' |
   |---|---|---|
   | gol | **SofaScore** | verificata su 4 fonti, Understat ne perde 2 |
   | minuti | **SofaScore** | Understat differisce di ±1-4' su 6.597 righe: e' la convenzione sul minuto del cambio, non un errore. Si sceglie per coerenza, non per qualita' |
   | xG | **entrambe, separate** | sono due modelli diversi (971,4 contro 1077,5 di somma stagionale): fonderle non ha senso, e la differenza e' informazione |

   `preferita()` restituisce la colonna da usare; le altre restano nel frame.

⚠️ TRE COSE CHE QUESTA RACCOLTA **NON** RIPARA, e vanno sapute.

* **La legenda e' incompleta.** Dichiara 198 colonne per `squadre`, il file ne
  ha **214**; e non descrive affatto le 34 colonne di `eventi_opta`. Le 16
  colonne non documentate sono elencate in `colonne_non_documentate()`.
* **`Spettatori` e' `post`, non `pre`.** Sta accanto a `Stadio` e `Capienza`,
  che sono anagrafici e noti prima del fischio, ma si conosce solo a partita
  giocata: usarla come feature sarebbe look-ahead (R8). `disponibilita()` da'
  la classificazione colonna per colonna.
* **`eventi` non e' una tabella, e' un contenitore.** Sette categorie di riga
  con schemi diversi nello stesso file (Cronaca, Evento, Tiro, Momentum,
  Quota, Serie, Migliore in campo). `eventi(categoria=...)` ne isola una;
  leggerlo tutto insieme e' quasi sempre un errore.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .sources import TEAM_ALIASES

log = logging.getLogger(__name__)

RACCOLTA = Path(__file__).resolve().parents[2] / "files" / "tre_fonti_serie_a_2526"

LEGA = "serie_a"
STAGIONE = "2526"

# Le tre fonti fuse a monte. L'ordine e' quello di preferenza dichiarato in §5.
FONTI = ("SofaScore", "WhoScored", "Understat")

# Colonne che esistono nello schema e non contengono NULLA. Dichiararle costa
# una riga; scoprirlo a valle costa un'analisi buttata.
COLONNE_VUOTE: dict[str, tuple[str, ...]] = {
    "squadre": ("Meteo (WhoScored)",),
    "heatmap": ("Tocchi",),
}

# La colonna che sembra un identificatore di partita e impila tre numerazioni.
ID_AVVELENATO = "ID partita"
ID_RINOMINATO = "ID partita (misto, NON usare)"

# Le tre colonne SANE, una per fonte. Sono quelle da usare per qualunque join.
ID_PARTITA_PER_FONTE = {
    "SofaScore": "ID partita (SofaScore)",
    "WhoScored": "ID partita (WhoScored)",
    "Understat": "ID partita (Understat)",
}

# Le due righe orfane della fusione «Verona»/«Hellas Verona» (riparazione 1).
# Sono identificate per (data, squadra, fonte-unica), non per indice di riga:
# un indice cambierebbe se il file venisse ri-consegnato con un ordine diverso.
ORFANE_VERONA = (
    ("2025-09-15", "Verona"),
    ("2025-08-25", "Verona"),
)

# Le due righe dove Understat perde un gol vero (riparazione 4). Verificate
# contro eventi + snapshot football-data: NON sono autogol.
GOL_PERSI_DA_UNDERSTAT = (
    ("2026-02-15", "Nikola Moro", "Bologna"),
    ("2025-12-27", "Pierre Kalulu", "Juventus"),
)

# Quale fonte vince, per grandezza (riparazione 5).
PREFERENZA: dict[str, str] = {
    "gol": "SofaScore",
    "minuti": "SofaScore",
}

# La GRANA di ogni categoria di `eventi`, cioe' la chiave con cui si aggancia.
# Non e' un dettaglio: cinque categorie su sette descrivono la PARTITA e hanno
# `Squadra` vuota per costruzione. Agganciarle per (data, squadra) fa risultare
# 96.510 righe «orfane» che orfane non sono — un difetto apparente prodotto
# dalla chiave sbagliata, non dai dati. Stessa famiglia dell'errore di LATO
# gia' pagato sulle coppe (`coppe_query`) e su `gol_dedotti`.
GRANA: dict[str, str] = {
    "Cronaca": "partita",
    "Momentum": "partita",
    "Quota": "partita",
    "Serie": "partita",
    "Migliore in campo": "partita",
    "Evento": "squadra",
    "Tiro": "squadra",
}

# Le chiavi corrispondenti, per non farle indovinare a chi legge.
CHIAVE = {
    "partita": ("Data", "Casa", "Trasferta"),
    "squadra": ("Data", "Squadra"),
}


def chiave_di(categoria: str) -> tuple[str, ...]:
    """Le colonne con cui agganciare una categoria di `eventi`.

    Misurato con queste chiavi: 380/380 partite per le cinque categorie di
    partita, 760/760 squadra-partita per `Evento`, 759/759 per `Tiro`
    (una squadra-partita senza un solo tiro), 379/379 per `Quota` (una
    partita senza quote).
    """
    if categoria not in GRANA:
        raise ValueError(f"categoria {categoria!r} sconosciuta. Valide: {sorted(GRANA)}")
    return CHIAVE[GRANA[categoria]]

# Disponibilita' temporale (R8). Solo le colonne dove sbagliare costa: il resto
# e' `post` per costruzione (ogni statistica esiste a partita finita).
DISPONIBILITA_PRE = (
    "Stadio", "Città", "Paese", "Capienza", "Arbitro",
    "Modulo casa", "Modulo trasferta", "Allenatore casa", "Allenatore trasferta",
    "Quota iniziale",
)
DISPONIBILITA_POST_INSIDIOSE = (
    # Sembrano anagrafiche perche' stanno in mezzo alle `pre`, e non lo sono.
    "Spettatori",
)


def _percorso(nome: str) -> Path:
    p = RACCOLTA / f"{nome}.csv.gz"
    if not p.exists():
        raise FileNotFoundError(
            f"manca {p}. La raccolta a tre fonti non e' nel repo: vedi "
            f"{RACCOLTA / 'README.md'}"
        )
    return p


def _normalizza_squadre(df: pd.DataFrame) -> pd.DataFrame:
    """Porta i nomi squadra alla grafia canonica del progetto (TEAM_ALIASES).

    Non e' cosmesi: senza, `Hellas Verona` e `Verona` restano due squadre per
    qualunque join, ed e' esattamente il bug che il §5 del CLAUDE.md racconta.
    """
    for col in ("Squadra", "Avversario", "Casa", "Trasferta"):
        if col in df.columns:
            df[col] = df[col].map(lambda x: TEAM_ALIASES.get(x, x) if isinstance(x, str) else x)
    return df


def _rinomina_id_avvelenato(df: pd.DataFrame) -> pd.DataFrame:
    """Rinomina (non cancella) la colonna che impila tre numerazioni.

    Rinominare invece di cancellare e' voluto: chi legge il frame vede che nel
    grezzo quella colonna c'e', e vede nel nome perche' non va usata. Una
    colonna sparita si ri-scopre leggendo il file, e si ri-usa.
    """
    if ID_AVVELENATO in df.columns and any(c in df.columns for c in ID_PARTITA_PER_FONTE.values()):
        df = df.rename(columns={ID_AVVELENATO: ID_RINOMINATO})
    return df


def squadre(*, solo_partite: bool = True, periodo: str | None = None) -> pd.DataFrame:
    """Squadra-partita-periodo (Totale / 1° tempo / 2° tempo), 214 colonne.

    `solo_partite=False` include anche le **60 righe di livello Stagione**, che
    sono la CLASSIFICA (posizione, punti, differenza reti, qualificazione) in
    tre versioni per squadra: generale, casa, trasferta. Hanno uno schema
    diverso — 19 colonne piene su 214 — quindi di default restano fuori: una
    riga di classifica in mezzo alle righe di partita e' il tipo di sorpresa
    che rompe un `groupby` senza dire niente.

    Le 2 righe orfane «Verona» vengono scartate (riparazione 1): sono un
    duplicato parziale, la partita completa c'e' gia' sotto «Hellas Verona».
    """
    df = pd.read_csv(_percorso("squadre"), low_memory=False)

    prima = len(df)
    maschera_orfane = pd.Series(False, index=df.index)
    for data, squadra in ORFANE_VERONA:
        maschera_orfane |= (df["Data"] == data) & (df["Squadra"] == squadra) & df["Avversario"].isna()
    df = df[~maschera_orfane].copy()
    if prima - len(df):
        log.info("scartate %d righe orfane Verona/Hellas Verona", prima - len(df))

    if solo_partite:
        df = df[df["Livello"] == "Partita"].copy()
    if periodo is not None:
        df = df[df["Periodo"] == periodo].copy()

    df = _normalizza_squadre(df)
    return df.reset_index(drop=True)


def classifica() -> pd.DataFrame:
    """Le 60 righe di livello Stagione: la classifica in tre versioni.

    `Tipo classifica` distingue generale / casa / trasferta. E' l'unico posto
    del progetto dove la classifica di Serie A esiste come dato invece che
    come qualcosa da ricalcolare dai risultati.
    """
    df = pd.read_csv(_percorso("squadre"), low_memory=False)
    df = df[df["Livello"] == "Stagione"].copy()
    piene = [c for c in df.columns if df[c].notna().any()]
    return _normalizza_squadre(df[piene]).reset_index(drop=True)


def giocatori(*, livello: str | None = "Partita") -> pd.DataFrame:
    """Giocatore-partita, 190 colonne da tre fonti.

    `livello` filtra la colonna omonima: `Partita` (17.829 righe, il default),
    `Rosa` (711) o `Stagione` (586). Come per `squadre`, tre grane diverse nello
    stesso file sono una trappola se non si sceglie.

    Applica: normalizzazione dei nomi squadra, rinomina dell'`ID partita`
    avvelenato, e la correzione dei 2 gol persi da Understat (riparazione 4).
    """
    df = pd.read_csv(_percorso("giocatori"), low_memory=False)
    if livello is not None and "Livello" in df.columns:
        df = df[df["Livello"] == livello].copy()

    df = _rinomina_id_avvelenato(df)
    df = _normalizza_squadre(df)

    # I 2 gol che Understat non registra. Non si "corregge Understat": si
    # allinea la sua colonna al fatto accertato su quattro fonti, e lo si
    # segna in una colonna apposta perche' resti visibile.
    df["gol_corretto_da_noi"] = False
    if "Gol (Understat)" in df.columns:
        for data, giocatore, squadra in GOL_PERSI_DA_UNDERSTAT:
            m = (df["Data"] == data) & (df["Giocatore"] == giocatore)
            if m.any():
                df.loc[m, "Gol (Understat)"] = df.loc[m, "Gol (SofaScore)"]
                df.loc[m, "gol_corretto_da_noi"] = True

    return df.reset_index(drop=True)


def eventi(categoria: str | None = None) -> pd.DataFrame:
    """Il contenitore a sette categorie. Passane UNA, quasi sempre.

    | categoria | righe | grana | cos'e' |
    |---|--:|---|---|
    | `Cronaca` | 42.822 | partita | il commento testuale di SofaScore |
    | `Momentum` | 34.951 | partita | la curva di pressione, ~92 punti a partita |
    | `Quota` | 13.822 | partita | quota iniziale e finale, con l'esito marcato |
    | `Tiro` | 18.754 | **squadra** | tiro-per-tiro con xG e xGOT, da SofaScore **e** Understat |
    | `Evento` | 6.945 | **squadra** | gol, sostituzioni, cartellini |
    | `Serie` | 4.155 | partita | strisce tipo «5/7 under 2.5» |
    | `Migliore in campo` | 760 | partita | 2 per partita |

    Leggerlo senza filtro da' un frame in cui 47 colonne sono piene a macchia
    di leopardo, perche' ogni categoria ne usa un sottoinsieme diverso.

    ⚠️ **LA GRANA CAMBIA CON LA CATEGORIA, E SBAGLIARLA SEMBRA UN DIFETTO DEI
    DATI.** Cinque categorie su sette descrivono la PARTITA, non una squadra:
    su quelle `Squadra` e' `NaN` per costruzione, e agganciarle con la chiave
    `(data, squadra)` fa risultare **96.510 righe orfane** che orfane non sono.
    Con la chiave giusta l'aggancio e' totale su tutte e sette (misurato:
    380/380 partite per le cinque di partita, 760/760 squadra-partita per
    `Evento`, 759/759 per `Tiro`, 379/379 per `Quota`). Usa `GRANA[categoria]`
    per scegliere la chiave invece di indovinarla.
    """
    df = pd.read_csv(_percorso("eventi"), low_memory=False)
    if categoria is not None:
        valide = set(df["Categoria"].dropna().unique())
        if categoria not in valide:
            raise ValueError(f"categoria {categoria!r} assente. Valide: {sorted(valide)}")
        df = df[df["Categoria"] == categoria].copy()
    return _normalizza_squadre(df).reset_index(drop=True)


def eventi_opta(*, partita: int | None = None, colonne: list[str] | None = None) -> pd.DataFrame:
    """Event data Opta: 562.672 righe, ogni tocco con coordinate e secondo.

    E' il file piu' pesante della raccolta (24 MB compressi): `colonne` e
    `partita` esistono per non caricarlo tutto quando non serve. `partita` e'
    l'`ID partita` **di WhoScored**, che qui e' l'unico presente e quindi non
    ha il problema della colonna mista di `giocatori`.

    39 tipi di evento; `Pass` da solo e' il 64% delle righe. Le coordinate sono
    piene al 100%; `Porta Y`/`Porta Z` (dove il tiro attraversa la porta)
    esistono su 9.381 righe, cioe' i tiri.

    ⚠️ Nessuna delle sue 34 colonne e' descritta dalla legenda consegnata.
    """
    df = pd.read_csv(_percorso("eventi_opta"), low_memory=False, usecols=colonne)
    if partita is not None and "ID partita" in df.columns:
        df = df[df["ID partita"] == partita].copy()
    return _normalizza_squadre(df).reset_index(drop=True)


def heatmap(*, partita: int | None = None) -> pd.DataFrame:
    """Posizioni: una riga per tocco, con X/Y su scala 0-100. Fonte SofaScore.

    380 partite, 586 giocatori, 556.996 righe. `partita` e' l'`ID partita` di
    SofaScore. La colonna `Tocchi` e' **vuota al 100%**: c'e' nello schema e non
    contiene niente (vedi `colonne_vuote`).
    """
    df = pd.read_csv(_percorso("heatmap"), low_memory=False)
    if partita is not None:
        df = df[df["ID partita"] == partita].copy()
    return _normalizza_squadre(df).reset_index(drop=True)


def legenda(*, versione: str = "v2") -> pd.DataFrame:
    """La documentazione consegnata: mappa ogni colonna sulla chiave della fonte.

    ⚠️ Ne esistono DUE, con schemi diversi, ed e' voluto tenerle entrambe.

    | versione | righe | schema | copertura |
    |---|--:|---|---|
    | `v1` | 440 | `Sezione, Voce, Dettaglio, ...` | **incompleta**: 198 colonne dichiarate per `squadre` che ne ha 214, e `eventi_opta` non documentato affatto |
    | `v2` | 522 | `Sezione, File, Colonna o voce, ...` | **completa: 503 colonne su 503, zero scoperte** (misurato) |

    La v1 e' conservata (`legenda_v1_incompleta.csv.gz`) perche' e' cio' che e'
    stato consegnato per primo, e perche' il manifesto ne registra lo sha256:
    buttarla renderebbe non verificabile la storia della raccolta (regola
    5-ter, si conserva l'originale come consegnato).

    Il default e' `v2`: chi chiede "la legenda" vuole quella che documenta
    tutto.
    """
    if versione == "v2":
        return pd.read_csv(_percorso("legenda"))
    if versione == "v1":
        return pd.read_csv(_percorso("legenda_v1_incompleta"))
    raise ValueError(f"versione {versione!r} sconosciuta: usa 'v1' o 'v2'")


# ---------------------------------------------------------------------------
# Le funzioni che DICHIARANO i limiti, invece di lasciarli scoprire a valle.
# ---------------------------------------------------------------------------
def colonne_vuote() -> dict[str, tuple[str, ...]]:
    """Le colonne che esistono nello schema e non contengono nulla."""
    return dict(COLONNE_VUOTE)


#: Il nome con cui la legenda v2 chiama ciascun file della raccolta.
_NOME_IN_LEGENDA = {
    "squadre": "Squadre", "giocatori": "Giocatori", "eventi": "Eventi",
    "eventi_opta": "Eventi_Opta", "heatmap": "Heatmap",
}


def colonne_non_documentate(*, versione: str = "v2") -> dict[str, list[str]]:
    """Le colonne dei file che la legenda NON descrive. Con la v2: **nessuna**.

    Esiste ancora, benche' oggi torni vuoto su tutti e cinque i file, perche' e'
    la guardia che se ne accorgera' se una consegna futura aggiunge colonne
    senza aggiornare la legenda. Un controllo che passa non e' un controllo
    inutile: e' un controllo che non ha ancora avuto lavoro da fare.

    Misurato con la v2 al 11/08/2026: squadre 214/214, giocatori 190/190,
    eventi 47/47, eventi_opta 34/34, heatmap 18/18 — **503 su 503**.
    Con la `v1` invece resta scoperto tutto `eventi_opta` e parte di `squadre`.
    """
    leg = legenda(versione=versione)
    fuori: dict[str, list[str]] = {}
    righe = leg[leg["Sezione"] == "Legenda"]
    for nome, in_legenda in _NOME_IN_LEGENDA.items():
        cols = list(pd.read_csv(_percorso(nome), nrows=0).columns)
        if "File" in righe.columns:                       # schema v2
            descritte = set(righe[righe["File"] == in_legenda]["Colonna o voce"].dropna())
        else:                                             # schema v1
            descritte = set(righe["Dettaglio"].dropna())
        fuori[nome] = [c for c in cols if c not in descritte]
    return fuori


def disponibilita(colonna: str) -> str:
    """`pre`, `post` o `statico` per una colonna (regola R8).

    Serve perche' l'errore qui e' invisibile: il numero e' giusto, e' il
    MOMENTO a essere sbagliato. Il caso insidioso di questa raccolta e'
    `Spettatori`, che sta fra colonne anagrafiche ed e' `post`.
    """
    base = colonna.split("(")[0].strip()
    if base in DISPONIBILITA_POST_INSIDIOSE:
        return "post"
    if base in DISPONIBILITA_PRE:
        return "pre"
    return "post"


def preferita(grandezza: str) -> str:
    """La fonte da usare quando due divergono, per la grandezza indicata.

    Dichiarata invece che implicita: chi legge un numero deve poter sapere
    quale fonte l'ha prodotto e perche' quella. Vedi la riparazione 5 in testa
    al modulo per il ragionamento su ciascuna.
    """
    if grandezza not in PREFERENZA:
        raise ValueError(
            f"nessuna preferenza dichiarata per {grandezza!r}. "
            f"Dichiarate: {sorted(PREFERENZA)}. Per l'xG la scelta e' voluta: "
            "le due fonti sono due MODELLI diversi e non vanno fuse."
        )
    return PREFERENZA[grandezza]


def discordanze() -> pd.DataFrame:
    """Le righe che il file stesso dichiara discordanti fra le sue fonti.

    6.616 righe su 19.126 (34,6%): 6.597 sui minuti (±1-4', la convenzione sul
    minuto del cambio), 44 sui tiri, **2 sui gol** — questi ultimi istruiti
    uno per uno e corretti in `giocatori()`, perche' non erano una convenzione
    ma una lacuna di Understat.
    """
    g = giocatori(livello=None)
    return g[g["Discordanze"].notna()].copy()
