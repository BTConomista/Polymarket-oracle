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
   ma nessuno deve costruirci sopra credendole disponibili: `colonne_vuote(lega)`
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

FILES = Path(__file__).resolve().parents[2] / "files"

STAGIONE = "2526"
LEGA_DEFAULT = "serie_a"

# Le tre fonti fuse a monte. L'ordine e' quello di preferenza dichiarato in §5.
FONTI = ("SofaScore", "WhoScored", "Understat")


def raccolta(lega: str = LEGA_DEFAULT) -> Path:
    """La cartella della raccolta a tre fonti di una lega."""
    return FILES / f"tre_fonti_{lega}_{STAGIONE}"


def leghe_disponibili() -> list[str]:
    """Le leghe per cui la raccolta esiste su disco.

    Serve perche' le consegne arrivano una lega per volta: al 11/08/2026 sono
    Serie A (sei file) e Premier (cinque — la heatmap arriva dopo).
    """
    trovate = []
    for p in sorted(FILES.glob(f"tre_fonti_*_{STAGIONE}")):
        nome = p.name[len("tre_fonti_"):-len(f"_{STAGIONE}")]
        if (p / "squadre.csv.gz").exists():
            trovate.append(nome)
    return trovate


# Colonne che esistono nello schema e non contengono NULLA. Sono PER LEGA, e
# non e' un dettaglio: `Meteo (WhoScored)` e' vuota allo 0,0% in Serie A e
# piena al 95,9% in Premier. Non e' un difetto dell'export ma una copertura
# diversa della fonte — trattarla come costante avrebbe fatto scartare un dato
# buono su una lega per un buco che stava sull'altra.
COLONNE_VUOTE: dict[str, dict[str, tuple[str, ...]]] = {
    "serie_a": {"squadre": ("Meteo (WhoScored)",), "heatmap": ("Tocchi",)},
    "premier_league": {"heatmap": ("Tocchi",)},
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

# ⚠️ Le righe ORFANE della fusione sono PER LEGA, e finora ce ne sono solo in
# Serie A: «Verona» (Understat) contro «Hellas Verona» (le altre due) ha
# lasciato 2 righe senza `Avversario`. In Premier il difetto NON si ripete —
# 760/760 righe pulite — quindi non e' un difetto sistematico dell'export ma
# un incidente su un nome. Le righe si identificano per (data, squadra), non
# per indice: un indice cambierebbe a ogni ri-consegna con ordine diverso.
ORFANE: dict[str, tuple[tuple[str, str], ...]] = {
    "serie_a": (("2025-09-15", "Verona"), ("2025-08-25", "Verona")),
}

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


def _percorso(nome: str, lega: str) -> Path:
    """Il file `nome` della raccolta di `lega`, con un errore che dice cosa fare.

    Le consegne arrivano una lega per volta e non sempre complete: la Premier
    e' arrivata senza `heatmap`. Un FileNotFoundError generico manderebbe a
    cercare un bug dove c'e' solo un file che deve ancora arrivare.
    """
    base = raccolta(lega)
    p = base / f"{nome}.csv.gz"
    if not p.exists():
        if base.exists():
            presenti = sorted(x.stem.replace(".csv", "") for x in base.glob("*.csv.gz"))
            raise FileNotFoundError(
                f"la raccolta di {lega} non ha ancora {nome!r}. "
                f"Presenti: {presenti}. Vedi {base / 'README.md'}"
            )
        raise FileNotFoundError(
            f"nessuna raccolta a tre fonti per {lega!r}. "
            f"Disponibili: {leghe_disponibili()}"
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


def squadre(lega: str = LEGA_DEFAULT, *, solo_partite: bool = True, periodo: str | None = None) -> pd.DataFrame:
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
    df = pd.read_csv(_percorso("squadre", lega), low_memory=False)

    prima = len(df)
    maschera_orfane = pd.Series(False, index=df.index)
    for data, squadra in ORFANE.get(lega, ()):
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


def classifica(lega: str = LEGA_DEFAULT) -> pd.DataFrame:
    """Le 60 righe di livello Stagione: la classifica in tre versioni.

    `Tipo classifica` distingue generale / casa / trasferta. E' l'unico posto
    del progetto dove la classifica di Serie A esiste come dato invece che
    come qualcosa da ricalcolare dai risultati.
    """
    df = pd.read_csv(_percorso("squadre", lega), low_memory=False)
    df = df[df["Livello"] == "Stagione"].copy()
    piene = [c for c in df.columns if df[c].notna().any()]
    return _normalizza_squadre(df[piene]).reset_index(drop=True)


def giocatori(lega: str = LEGA_DEFAULT, *, livello: str | None = "Partita") -> pd.DataFrame:
    """Giocatore-partita, 190 colonne da tre fonti.

    `livello` filtra la colonna omonima: `Partita` (17.829 righe, il default),
    `Rosa` (711) o `Stagione` (586). Come per `squadre`, tre grane diverse nello
    stesso file sono una trappola se non si sceglie.

    Applica: normalizzazione dei nomi squadra, rinomina dell'`ID partita`
    avvelenato, e la correzione dei 2 gol persi da Understat (riparazione 4).
    """
    df = pd.read_csv(_percorso("giocatori", lega), low_memory=False)
    if livello is not None and "Livello" in df.columns:
        df = df[df["Livello"] == livello].copy()

    df = _rinomina_id_avvelenato(df)
    df = _normalizza_squadre(df)

    df = _allinea_gol(df)
    return df.reset_index(drop=True)


def _allinea_gol(df: pd.DataFrame) -> pd.DataFrame:
    """Allinea i gol di Understat a SofaScore dove il file dichiara discordanza.

    ⚠️ E' una REGOLA, non una lista di eccezioni, e la differenza conta. La
    prima stesura elencava le 2 righe della Serie A per (data, giocatore):
    avrebbe girato sulla Premier senza correggere nulla e senza dire niente —
    un silenzio indistinguibile da «qui non ci sono difetti».

    La regola e' legittima perche' la DIREZIONE e' verificata, non assunta:
    su tutte e 5 le righe discordanti delle due leghe (2 Serie A, 3 Premier)
    la differenza e' **sempre +1 a favore di SofaScore** e `Autogol` vale
    **sempre 0** su entrambe le fonti. Le prime due sono state istruite a mano
    su quattro fonti indipendenti (eventi + snapshot football-data): gli eventi
    danno `Gol / regular` con un `Tiro` e uno `scoreChange` allo stesso minuto.
    E' una lacuna di Understat, non una convenzione sugli autogol — l'ipotesi
    ovvia, che era falsa.

    ⚠️ IL TRIPWIRE: se un giorno una riga discordasse nell'altro verso
    (Understat > SofaScore), la regola non varrebbe piu' e la funzione **alza**.
    Meglio fermarsi che applicare in silenzio una correzione la cui premessa e'
    caduta.
    """
    df["gol_corretto_da_noi"] = False
    if not {"Gol (SofaScore)", "Gol (Understat)", "Discordanze"} <= set(df.columns):
        return df

    marcate = df["Discordanze"].fillna("").str.contains(r"\bgol\b", regex=True)
    sofa = pd.to_numeric(df.loc[marcate, "Gol (SofaScore)"], errors="coerce")
    under = pd.to_numeric(df.loc[marcate, "Gol (Understat)"], errors="coerce")

    al_contrario = (under > sofa).fillna(False)
    if al_contrario.any():
        righe = df.loc[marcate][al_contrario][["Data", "Giocatore"]].to_dict("records")
        raise RuntimeError(
            "premessa caduta: Understat dichiara PIU' gol di SofaScore su "
            f"{righe}. La regola vale solo perche' la direzione e' sempre la "
            "stessa (Understat sottostima). Istruire questi casi a mano prima "
            "di proseguire — vedi la docstring di _allinea_gol."
        )

    da_correggere = marcate & (
        pd.to_numeric(df["Gol (SofaScore)"], errors="coerce")
        > pd.to_numeric(df["Gol (Understat)"], errors="coerce")
    ).fillna(False)
    df.loc[da_correggere, "Gol (Understat)"] = df.loc[da_correggere, "Gol (SofaScore)"]
    df.loc[da_correggere, "gol_corretto_da_noi"] = True
    if da_correggere.any():
        log.info("allineati %d gol persi da Understat", int(da_correggere.sum()))
    return df


def eventi(lega: str = LEGA_DEFAULT, *, categoria: str | None = None) -> pd.DataFrame:
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

    ⚠️ `categoria` e' SOLO-NOMINALE di proposito. Prima della seconda lega il
    primo argomento posizionale era la categoria; ora e' la lega, e una
    chiamata vecchia come `eventi("Momentum")` verrebbe letta come «la lega
    Momentum». Meglio un errore secco che un frame sbagliato in silenzio.

    ⚠️ **LA GRANA CAMBIA CON LA CATEGORIA, E SBAGLIARLA SEMBRA UN DIFETTO DEI
    DATI.** Cinque categorie su sette descrivono la PARTITA, non una squadra:
    su quelle `Squadra` e' `NaN` per costruzione, e agganciarle con la chiave
    `(data, squadra)` fa risultare **96.510 righe orfane** che orfane non sono.
    Con la chiave giusta l'aggancio e' totale su tutte e sette (misurato:
    380/380 partite per le cinque di partita, 760/760 squadra-partita per
    `Evento`, 759/759 per `Tiro`, 379/379 per `Quota`). Usa `GRANA[categoria]`
    per scegliere la chiave invece di indovinarla.
    """
    df = pd.read_csv(_percorso("eventi", lega), low_memory=False)
    if categoria is not None:
        valide = set(df["Categoria"].dropna().unique())
        if categoria not in valide:
            raise ValueError(f"categoria {categoria!r} assente. Valide: {sorted(valide)}")
        df = df[df["Categoria"] == categoria].copy()
    return _normalizza_squadre(df).reset_index(drop=True)


def eventi_opta(lega: str = LEGA_DEFAULT, *, partita: int | None = None, colonne: list[str] | None = None) -> pd.DataFrame:
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
    df = pd.read_csv(_percorso("eventi_opta", lega), low_memory=False, usecols=colonne)
    if partita is not None and "ID partita" in df.columns:
        df = df[df["ID partita"] == partita].copy()
    return _normalizza_squadre(df).reset_index(drop=True)


def heatmap(lega: str = LEGA_DEFAULT, *, partita: int | None = None) -> pd.DataFrame:
    """Posizioni: una riga per tocco, con X/Y su scala 0-100. Fonte SofaScore.

    380 partite, 586 giocatori, 556.996 righe. `partita` e' l'`ID partita` di
    SofaScore. La colonna `Tocchi` e' **vuota al 100%**: c'e' nello schema e non
    contiene niente (vedi `colonne_vuote`).
    """
    df = pd.read_csv(_percorso("heatmap", lega), low_memory=False)
    if partita is not None:
        df = df[df["ID partita"] == partita].copy()
    return _normalizza_squadre(df).reset_index(drop=True)


def legenda(lega: str = LEGA_DEFAULT, *, versione: str = "v2") -> pd.DataFrame:
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
        return pd.read_csv(_percorso("legenda", lega))
    if versione == "v1":
        return pd.read_csv(_percorso("legenda_v1_incompleta", lega))
    raise ValueError(f"versione {versione!r} sconosciuta: usa 'v1' o 'v2'")


# ---------------------------------------------------------------------------
# Le funzioni che DICHIARANO i limiti, invece di lasciarli scoprire a valle.
# ---------------------------------------------------------------------------
def colonne_vuote(lega: str = LEGA_DEFAULT) -> dict[str, tuple[str, ...]]:
    """Le colonne che esistono nello schema e non contengono nulla, PER LEGA.

    Non e' una costante del formato: `Meteo (WhoScored)` e' vuota allo 0,0% in
    Serie A e piena al **95,9%** in Premier. Trattarla come costante avrebbe
    fatto scartare un dato buono su una lega per un buco che stava sull'altra —
    ed e' il motivo per cui questa funzione prende `lega` invece di essere un
    dizionario globale.
    """
    return dict(COLONNE_VUOTE.get(lega, {}))


#: Il nome con cui la legenda v2 chiama ciascun file della raccolta.
_NOME_IN_LEGENDA = {
    "squadre": "Squadre", "giocatori": "Giocatori", "eventi": "Eventi",
    "eventi_opta": "Eventi_Opta", "heatmap": "Heatmap",
}


def colonne_non_documentate(lega: str = LEGA_DEFAULT, *, versione: str = "v2") -> dict[str, list[str]]:
    """Le colonne dei file che la legenda NON descrive. Con la v2: **nessuna**.

    Esiste ancora, benche' oggi torni vuoto su tutti e cinque i file, perche' e'
    la guardia che se ne accorgera' se una consegna futura aggiunge colonne
    senza aggiornare la legenda. Un controllo che passa non e' un controllo
    inutile: e' un controllo che non ha ancora avuto lavoro da fare.

    Misurato con la v2 al 11/08/2026: squadre 214/214, giocatori 190/190,
    eventi 47/47, eventi_opta 34/34, heatmap 18/18 — **503 su 503**.
    Con la `v1` invece resta scoperto tutto `eventi_opta` e parte di `squadre`.
    """
    leg = legenda(lega, versione=versione)
    fuori: dict[str, list[str]] = {}
    righe = leg[leg["Sezione"] == "Legenda"]
    for nome, in_legenda in _NOME_IN_LEGENDA.items():
        try:
            cols = list(pd.read_csv(_percorso(nome, lega), nrows=0).columns)
        except FileNotFoundError:
            continue          # file non ancora consegnato per questa lega
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


# Le discordanze dichiarate dal file che NON sono disaccordi fra le fonti, ma
# un confronto fra grandezze diverse. Vanno ignorate: contarle come difetti
# gonfia il rumore e nasconde quelle vere.
DISCORDANZE_FALSE = ("possesso",)


def discordanze(lega: str = LEGA_DEFAULT, *, includi_false: bool = False) -> pd.DataFrame:
    """Le righe che il file dichiara discordanti fra le sue fonti.

    A livello GIOCATORE (6.672 righe su 19.126, 34,9%): 6.597 minuti,
    109 passaggi chiave, 44 tiri, 20 passaggi totali, 7 assist, **2 gol** —
    questi ultimi istruiti uno per uno e corretti in `giocatori()`, perche' non
    erano una convenzione ma una lacuna di Understat.

    ⚠️ **UNA DELLE DISCORDANZE DICHIARATE E' FALSA, ed e' la piu' numerosa a
    livello squadra.** Il file marca `possesso` su **760 righe su 762** — cioe'
    praticamente tutte — e sembra dire «le due fonti non vanno d'accordo sul
    possesso palla». Misurato, non e' cosi':

        Ball possession (SofaScore)  →  21-79,  somma 100 fra le due squadre
        possession (WhoScored)       →  201-800, somma ~898

    La prima e' una **percentuale**, la seconda un **conteggio**. Non possono
    essere uguali mai, quindi il flag e' vero *per costruzione* e non porta
    informazione: e' un'**unita' diversa**, non un disaccordo.

    E' la regola R7 applicata a una dichiarazione invece che a una misura: il
    difetto non e' il numero, e' la statistica scelta per raccontarlo. Il
    contro-esempio nello stesso file dimostra che il resto e' affidabile: la
    discordanza sui `corner` e' marcata su **18 righe**, e ri-calcolandola in
    modo indipendente (SofaScore contro `cornersTotal` di WhoScored) escono
    **le stesse 18**, tutte a −1. Li' il confronto e' fra grandezze omogenee e
    il file ha ragione.

    Di default le false sono escluse. `includi_false=True` le rimette, per chi
    voglia vederle.
    """
    g = giocatori(lega, livello=None)
    return _filtra_discordanze(g, includi_false)


def discordanze_squadra(lega: str = LEGA_DEFAULT, *, includi_false: bool = False) -> pd.DataFrame:
    """Come `discordanze`, ma sul livello squadra-partita.

    E' arrivata con la terza consegna (11/08/2026): prima la colonna
    `Discordanze` esisteva solo su `giocatori`. Dichiara `possesso` su 760
    righe — **falso positivo**, vedi `discordanze` — e `corner` su 18, che
    invece sono vere e valgono tutte −1.
    """
    s = squadre(lega, periodo="Totale")
    if "Discordanze" not in s.columns:
        raise RuntimeError(
            "questa consegna di squadre.csv non ha la colonna Discordanze: "
            "e' una versione precedente all'11/08/2026"
        )
    return _filtra_discordanze(s, includi_false)


def _filtra_discordanze(df: pd.DataFrame, includi_false: bool) -> pd.DataFrame:
    """Toglie i TOKEN falsi dalla lista, non le righe che li contengono.

    ⚠️ La differenza non e' cosmetica, ed e' costata un test rosso: una riga
    puo' dichiarare piu' grandezze insieme (`possesso; corner`). Scartare la
    riga perche' contiene un token falso butta via anche la discordanza VERA
    che ci sta accanto — e infatti tutte e 18 le righe con `corner` hanno
    anche `possesso`, quindi il filtro ingenuo le azzerava tutte.
    """
    righe = df[df["Discordanze"].notna()].copy()
    if includi_false:
        return righe

    def ripulisci(v: str) -> str:
        tenuti = [t.strip() for t in str(v).split(";")
                  if t.strip() and t.strip() not in DISCORDANZE_FALSE]
        return "; ".join(tenuti)

    righe["Discordanze"] = righe["Discordanze"].map(ripulisci)
    return righe[righe["Discordanze"] != ""].copy()
