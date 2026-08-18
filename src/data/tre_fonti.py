"""⚽ LE RACCOLTE A TRE FONTI — 2025-26 da SofaScore, Opta (WhoScored), Understat.

`squadre()`, `giocatori()`, `eventi()`, `eventi_opta()`, `heatmap()` sono le
funzioni da usare. **Ognuna prende la LEGA come primo argomento**
(`leghe_disponibili()` dice quali ci sono). Leggono il file grezzo consegnato e
ne restituiscono una versione **corretta in lettura**: i file su disco restano
identici a come sono arrivati (R3 — nessuna modifica a mano ai dati), le
riparazioni vivono qui e sono quindi verificabili, ripetibili e reversibili.

COSA PORTANO che il progetto non aveva per un campionato: **event data Opta**
(ogni tocco con X/Y, secondo, qualificatori), **posizioni** (heatmap),
**arbitro, stadio, spettatori, modulo**, **tracking fisico**, **momentum**,
**classifica**. E' un salto di granularita', non piu' dati della stessa forma —
vale il principio §1.10 del CLAUDE.md, per cui un esito negativo misurato su
dati di squadra non dice nulla su dati piu' fini.

════════════════════════════════════════════════════════════════════════════
LE DUE FAMIGLIE DI DIFETTI, e perche' la distinzione e' il cuore del modulo
════════════════════════════════════════════════════════════════════════════

Con una lega sola non si puo' sapere se un difetto e' **del formato** o un
**incidente di quella consegna**. Con tre si misura, e il risultato divide le
riparazioni in due:

A · SI RIPETONO SU TUTTE → riparazione generale
  1. **`ID partita` impila tre numerazioni.** Il file ha QUATTRO colonne con
     quel nome: le tre per-fonte hanno 380 valori distinti ciascuna e sono
     sane; la quarta ne ha 436 (Serie A), 384 (Premier), 538 (Liga) — perche'
     mescola SofaScore ~14M, WhoScored ~1,9M e Understat ~30k. Un join su
     quella colonna appaia partite diverse **senza dare errore**: finto pieno
     (R6). Viene **rinominata** `ID partita (misto, NON usare)`, non
     cancellata: una colonna sparita si ri-scopre leggendo il grezzo, e si
     ri-usa.
  2. **Understat perde gol.** 2 righe in Serie A, 3 in Premier, 4 in Liga.
     ⚠️ L'ipotesi ovvia — «convenzione sugli autogol» — e' **FALSA**, ed e'
     stata verificata invece che assunta: `Autogol` vale 0 su entrambe le
     fonti, gli eventi danno `Gol / regular` con un `Tiro` e uno `scoreChange`
     allo stesso minuto, e lo snapshot football-data conferma i punteggi.
     La DIREZIONE e' sempre la stessa (+1 a SofaScore su 9 righe su 9), ed e'
     per questo che `_allinea_gol` e' una **regola col suo tripwire** e non
     una lista di eccezioni — vedi la sua docstring.
  3. **La discordanza «possesso» e' un FALSO POSITIVO.** Il file la marca su
     760 righe su 760 in tutte e tre le leghe: `Ball possession` (SofaScore)
     e' una percentuale, `possession` (WhoScored) un conteggio. Non possono
     coincidere mai. Vedi `discordanze()`.

B · NON SI RIPETONO → riparazione per-lega
  4. **Le righe orfane della fusione.** 2 in Serie A («Verona» di Understat
     contro «Hellas Verona» delle altre due, senza `Avversario`), **zero** in
     Premier e Liga. Era un incidente su un nome, non un difetto sistematico:
     resta in `ORFANE`, per-lega, e non va promossa a regola. Il dato non era
     perso — la partita esisteva gia' completa sotto l'altra grafia.
  5. **Le colonne vuote.** `Meteo (WhoScored)` ha **tre** stati misurati:
     0,0% in Serie A, **0,3% in Liga** (2 righe su 760), 98,4% in Premier.
     Non e' un difetto dell'export ma una copertura diversa della fonte.
     Da cui `colonne_vuote(lega)` e soprattutto `copertura()`, che distingue
     *vuota* / *quasi vuota* / *piena*: lo stato di mezzo e' il piu' insidioso,
     perche' un `notna().any()` risponde «funziona» su due righe.

════════════════════════════════════════════════════════════════════════════

CHI VINCE quando due fonti divergono, dichiarato e non implicito:

   | grandezza | fonte     | perche' |
   |---|---|---|
   | gol       | SofaScore | verificata su 4 fonti, Understat ne perde |
   | minuti    | SofaScore | Understat differisce di ±1-4' su migliaia di righe: e' la convenzione sul minuto del cambio, non un errore. Si sceglie per coerenza, non per qualita' |
   | xG        | **entrambe, separate** | sono due MODELLI diversi (971,4 contro 1077,5 di somma stagionale in Serie A): fonderle non ha senso, e la differenza e' informazione. `preferita('xG')` ALZA apposta |

════════════════════════════════════════════════════════════════════════════
LA RACCOLTA CHE HA ROTTO TRE COSTANTI (LaLiga2, consegna 18/08/2026)
════════════════════════════════════════════════════════════════════════════

LaLiga2 (Segunda Division) e' la prima raccolta di **seconda divisione**, e ha
il valore che hanno i casi limite: non ha aggiunto dati simili a quelli che
c'erano, ha mostrato quali «costanti» erano solo cinque campioni d'accordo fra
loro. Tre in particolare, tutte scoperte misurando e non leggendo:

1. **«a tre fonti» era un nome, non una misura.** Qui le fonti sono DUE, e
   nessuna delle due assenze e' un incidente di raccolta: Understat non ha la
   Segunda (tre verifiche indipendenti) e WhoScored non pubblica l'Opta su
   questa competizione (468 pagine su 468, con controllo positivo su una
   partita di LaLiga scaricata nello stesso momento). Nessun `eventi_opta`, e
   una `Cronaca` che non esiste: le categorie di `eventi` sono **sei**, non
   sette. Vedi `FONTI_PER_RACCOLTA`.

2. **«campionato» non implica «snapshot».** Per cinque leghe le due cose
   coincidevano, e diversi controlli ciclavano su `DIMENSIONI` aprendo
   `data/{lega}_matches.csv` come se ci fosse sempre. LaLiga2 e' un campionato
   e uno snapshot non ce l'ha — non e' in `LEAGUE_CONFIGS`. Vedi
   `ha_snapshot()`.

3. ⚠️⚠️ **`eventi.ID partita` era avvelenata da sempre, in TUTTE le raccolte a
   due fonti, e nessuno l'aveva vista.** In `squadre` e `giocatori` il difetto
   si nota perche' accanto alla colonna mista ci sono quelle per-fonte; in
   `eventi` quelle colonne non esistono, quindi non c'era niente con cui
   accorgersene. La Serie A ha **760 id distinti per 380 partite**: un join su
   quella colonna perde in silenzio le 9.373 righe di tiri di Understat. Il
   difetto e' stato trovato solo perche' LaLiga2 ne porta una **variante
   piu' rumorosa** — colonna di TESTO, con una frase al posto del numero — che
   rompe il join anche sulle righe sane. Ora `_ripara_id_eventi` lo chiude su
   tutte le raccolte. Vedi `ID_EVENTI_MISTO`.

⭐ La lezione generale, che vale oltre questa lega: **un difetto silenzioso si
scopre quando arriva il caso che lo rende rumoroso.** Cinque leghe concordi non
sono una verifica — sono cinque volte la stessa assunzione.

⚠️ DUE COSE CHE NON SI RIPARANO, e vanno sapute.

* **`Spettatori` e' `post`, non `pre`.** Sta accanto a `Stadio` e `Capienza`,
  che sono anagrafici e noti prima del fischio, ma si conosce solo a partita
  giocata: usarla come feature sarebbe look-ahead (R8). Vedi `disponibilita()`.
* **`eventi` non e' una tabella, e' un contenitore.** Sette categorie con
  schemi diversi nello stesso file, e la **grana cambia con la categoria**:
  cinque su sette descrivono la PARTITA e hanno `Squadra` vuota per
  costruzione. Agganciarle per (data, squadra) produce 96.510 righe «orfane»
  che orfane non sono. Usa `chiave_di(categoria)`.
  ⚠️ `categoria` e' solo-nominale: prima della seconda lega era il primo
  argomento posizionale, che ora e' la lega.
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

# ⚠️ MA NON TUTTE LE RACCOLTE HANNO TUTTE E TRE LE FONTI, e non e' un difetto:
# Understat copre i campionati e NON le competizioni UEFA. Chiamare «a tre
# fonti» una raccolta che ne ha una sarebbe un finto pieno nel nome.
FONTI_PER_RACCOLTA: dict[str, tuple[str, ...]] = {
    "serie_a": FONTI, "premier_league": FONTI, "la_liga": FONTI,
    "bundesliga": FONTI, "ligue_1": FONTI,
    # ⚠️ LALIGA2 (Segunda Division) E' LA PRIMA RACCOLTA DI **SECONDA
    # DIVISIONE**, e le mancano DUE fonti su tre — ma non allo stesso modo,
    # e la differenza e' tutta nel fatto che entrambe le assenze sono state
    # **misurate** invece che dedotte dal silenzio (la prova sta in `grezzi/`):
    #
    #  * **Understat non ha la Segunda.** Verificato in tre modi indipendenti:
    #    il menu del sito elenca sei sole leghe di prima divisione; cinque
    #    varianti di URL (`La_liga_2`, `Segunda`, `Segunda_Division`,
    #    `LaLiga2`, `Spain_2`) rispondono tutte 404; e — il modo piu' insidioso
    #    — le pagine squadra chieste per il 2025 servono **in silenzio un altro
    #    anno** (Almeria e Cadiz danno 2023/24, Deportivo 2026/27). Quest'ultimo
    #    e' un finto pieno da manuale (R6): chi si fermasse al primo `200 OK`
    #    archivierebbe la stagione sbagliata credendola giusta.
    #  * **WhoScored c'e' ma senza Opta.** 468 pagine su 468 senza
    #    `matchCentreData`, ~101 KB di HTML contro 1,14 MB di una partita di
    #    LaLiga scaricata nello stesso momento dalla stessa scheda. Il
    #    **controllo positivo** e' cio' che separa «la fonte non copre questa
    #    competizione» da «lo scaricatore si e' rotto», ed e' per questo che
    #    vale piu' di sei tentativi falliti. Da qui: **niente `eventi_opta`**.
    #
    # Quel che WhoScored da' comunque e' `initialMatchDataForScrappers` — gol,
    # cartellini e cambi al minuto — 8.188 righe dentro `eventi`, ed e' l'unica
    # seconda fonte su questa competizione.
    "laliga2": ("SofaScore", "WhoScored"),
    "uefa_champions_league": ("SofaScore", "WhoScored"),
    "uefa_europa_league": ("SofaScore", "WhoScored"),   # niente Understat: -37 colonne
    "uefa_conference_league": ("SofaScore",),           # solo SofaScore: -75 colonne
    # LE SEI SUPERCOPPE 2025-26 (consegna 13/08/2026). Solo la UEFA ha due
    # fonti; le cinque nazionali arrivano con SofaScore soltanto.
    #
    # ⚠️ E le cinque a UNA fonte portano lo stesso **19 colonne `(WhoScored)`
    # completamente vuote**: lo schema le prevede e la consegna non le riempie.
    # Non e' un finto pieno (sono NaN oneste) ma e' la sua anticamera — chi
    # guarda l'elenco delle colonne conclude «c'e' anche WhoScored» e ha torto.
    # Da cui `fonti()`, che dice quali fonti coprono DAVVERO la raccolta, e
    # `COLONNE_VUOTE`, che le elenca.
    "supercoppa_uefa": ("SofaScore", "WhoScored"),
    "supercoppa_italiana": ("SofaScore",),
    "supercopa_espana": ("SofaScore",),
    "community_shield": ("SofaScore",),
    "dfl_supercup": ("SofaScore",),
    "trophee_des_champions": ("SofaScore",),
}

#: Le raccolte che sono SUPERCOPPE, con la partita/e che contengono. Non e' una
#: comodita': serve a dire «10 attese» invece di inchiodare un numero, come
#: `DIMENSIONI` fa per i campionati. Due sono a **final four** (semifinali +
#: finale), le altre quattro a partita secca.
SUPERCOPPE: dict[str, int] = {
    "supercoppa_uefa": 1, "community_shield": 1, "dfl_supercup": 1,
    "trophee_des_champions": 1,
    "supercoppa_italiana": 3, "supercopa_espana": 3,   # final four
}

# ⚠️⚠️ IL PUNTEGGIO DELLE UEFA SOMMA LA LOTTERIA DEI RIGORI.
# `Gol casa (SofaScore)` su una partita decisa ai rigori NON e' il risultato
# della partita: e' risultato + rigori. Omonia-Wolfsberger del 28/08/2025 legge
# «6» dove il campo ha detto 1 (5 rigori). E' lo stesso difetto che il CLAUDE.md
# documenta per games.csv sulle coppe nazionali (68 partite su 458), e che li'
# e' costato una ricostruzione.
#
# ⭐ Qui pero' l'export lo DICHIARA, con tre colonne derivate:
#     Decisa ai rigori (derivata)              si/no
#     Gol casa senza rigori (derivata)         il punteggio VERO
#     Gol trasferta senza rigori (derivata)
# Sono 6 partite su 409 in Conference. Usa quelle, non `Gol casa`.
COLONNE_PUNTEGGIO_VERO = (
    "Gol casa senza rigori (derivata)",
    "Gol trasferta senza rigori (derivata)",
)

#: ⚠️⚠️ LA CONVENZIONE SUL PUNTEGGIO NON E' UNIFORME, ed e' costata un difetto
#: silenzioso per un mese. `True` = `Gol casa/trasferta` SOMMA la lotteria dei
#: rigori e va riparato; `False` = e' gia' il risultato della partita.
#:
#: La prima stesura (integrazione UEFA, 12/08/2026) aveva ragionato per FILE:
#: la Conference dichiarava le colonne derivate, quindi «le raccolte UEFA sono
#: coperte». **Falso**: l'Europa League ha lo stesso difetto e NON ha le colonne
#: derivate, quindi `punteggio_vero()` le restituiva il punteggio gonfiato su
#: 7 partite — fra cui un «Partizan-AEK Larnaca 7-7» che era 2-1.
#:
#: E il verso non e' nemmeno costante dentro la stessa famiglia: la CHAMPIONS,
#: consegnata il giorno dopo, e' PULITA. Quindi non si deduce dal torneo, non si
#: deduce dalla fonte, e non si deduce dalla presenza dei rigori: **si misura**.
#:
#: Come e' stata misurata (tre prove indipendenti, `_run_punteggio_coppe.py`):
#:   1. contando i gol VERI negli eventi (`Tipo=Gol`, piu' `Tipo=Rigore` col
#:      `Sottotipo=scored` — che non esiste: i rigori segnati sono gia' `Gol`
#:      con `Sottotipo=penalty`, i `Rigore` sono tutti `missed`):
#:      EL «Gol − Rigori» = eventi su **14/14** squadra-partita, «Gol» su 1/14;
#:      Conference **12/12** contro 0/12;
#:   2. contro la colonna DERIVATA che la Conference dichiara: la sottrazione
#:      la riproduce **6/6** — cioe' la regola non e' inventata da noi;
#:   3. sulle **1.334** squadra-partita SENZA lotteria, `Gol` == eventi
#:      1.334/1.334: la riparazione tocca solo dove deve.
#: Per Champions e supercoppe la prova e' l'identita' dei tempi
#: (`gol_sono_regolamentari`): 281/281 e 10/10, con 8 partite ai rigori dentro.
RIGORI_NEL_PUNTEGGIO: dict[str, bool] = {
    "uefa_europa_league": True,      # 7 partite, nessuna colonna derivata
    "uefa_conference_league": True,  # 6 partite, colonne derivate presenti
    "uefa_champions_league": False,  # 4 partite ai rigori, punteggio gia' pulito
    "supercoppa_uefa": False, "supercoppa_italiana": False,
    "community_shield": False, "trophee_des_champions": False,
    "supercopa_espana": False, "dfl_supercup": False,
}

#: Le colonne della lotteria, quando c'e'.
COLONNE_RIGORI = ("Rigori casa (SofaScore)", "Rigori trasferta (SofaScore)")


def fonti(lega: str = LEGA_DEFAULT) -> tuple[str, ...]:
    """Le fonti che coprono DAVVERO questa raccolta.

    Non e' sempre tre: Understat non copre le competizioni UEFA, e la
    Conference arriva con SofaScore soltanto. Chiedere `xG (Understat)` a una
    raccolta UEFA non da' NaN — da' KeyError, perche' la colonna non c'e'.
    """
    return FONTI_PER_RACCOLTA.get(lega, FONTI)


def punteggio_vero(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Il punteggio della PARTITA, non partita + lotteria dei rigori.

    ⚠️ Nelle raccolte UEFA `Gol casa (SofaScore)` somma i rigori sulle partite
    decise ai rigori: Omonia-Wolfsberger legge «6» dove il campo ha detto 1.
    Dove l'export fornisce le colonne derivate le usa; altrove torna le colonne
    normali.

    ⭐ E «altrove» non vuol dire «dove non ci sono i rigori». Le SUPERCOPPE
    2025-26 hanno la lotteria (4 partite su 10) e **non** hanno le colonne
    derivate — perche' non ne hanno bisogno: li' l'export tiene i rigori in una
    colonna a parte (`Rigori casa (SofaScore)`) e `Gol casa` e' gia' il tempo
    regolamentare. Non e' una promessa dell'export: e' **misurato**, e la
    verifica e' `gol_sono_regolamentari()`, che va eseguita su ogni consegna
    nuova invece di fidarsi.
    """
    if all(c in df.columns for c in COLONNE_PUNTEGGIO_VERO):
        return df[COLONNE_PUNTEGGIO_VERO[0]], df[COLONNE_PUNTEGGIO_VERO[1]]
    return df["Gol casa (SofaScore)"], df["Gol trasferta (SofaScore)"]


def gol_sono_regolamentari(df: pd.DataFrame) -> pd.Series:
    """TRIPWIRE: `Gol casa/trasferta` e' il 90', o ci sono dentro i rigori?

    L'identita' che lo decide non e' un'opinione — e' una scomposizione esatta:

        Gol casa = Casa 1T + Casa 2T        (e lo stesso per la trasferta)

    Se i rigori fossero sommati dentro `Gol`, l'uguaglianza salterebbe di
    esattamente il numero dei rigori segnati. Misurata sulle sei supercoppe:
    **10 partite su 10 la rispettano**, comprese le 4 decise ai rigori
    (PSG-Tottenham 2-2 e rigori 4-3, Palace-Liverpool 2-2 e 3-2,
    PSG-Marsiglia 2-2 e 4-1, Bologna-Inter 1-1 e 3-2).

    ⚠️ Non e' una verifica «una volta e via»: e' una **guardia**. Se una
    consegna futura contenesse i TEMPI SUPPLEMENTARI, i loro gol non stanno ne'
    nel 1T ne' nel 2T e l'identita' salterebbe **pur essendo il dato giusto**.
    In quel caso non si aggiusta il codice: si guarda la partita e si scrive
    che cosa e' successo (R5, «spiegare prima di accusare»).

    Torna una Series booleana allineata a `df`, una riga per squadra-partita.
    """
    serve = ("Gol casa (SofaScore)", "Gol trasferta (SofaScore)",
             "Casa 1T (SofaScore)", "Trasferta 1T (SofaScore)",
             "Casa 2T (SofaScore)", "Trasferta 2T (SofaScore)")
    mancanti = [c for c in serve if c not in df.columns]
    if mancanti:
        raise KeyError(f"servono i tempi per verificare il punteggio: mancano {mancanti}")
    casa = df["Casa 1T (SofaScore)"] + df["Casa 2T (SofaScore)"]
    fuori = df["Trasferta 1T (SofaScore)"] + df["Trasferta 2T (SofaScore)"]
    return (df["Gol casa (SofaScore)"] == casa) & (df["Gol trasferta (SofaScore)"] == fuori)


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


def ha_snapshot(lega: str = LEGA_DEFAULT) -> bool:
    """C'e' un `data/{lega}_matches.csv` a cui agganciare questa raccolta?

    ⚠️ NASCE DA LALIGA2, E DA UN'ASSUNZIONE CHE PER CINQUE LEGHE NON SI ERA MAI
    VISTA: che «campionato» implichi «snapshot». Fino all'agosto 2026 le due
    cose coincidevano — i cinque campionati raccolti erano esattamente i cinque
    modellati — e diversi controlli scritti allora ciclano su `DIMENSIONI`
    aprendo `data/{lega}_matches.csv` senza chiedersi se esista.

    LaLiga2 le separa: e' un campionato a tutti gli effetti (42 giornate, girone
    all'italiana) e uno snapshot **non ce l'ha**, perche' la seconda divisione
    spagnola non e' in `LEAGUE_CONFIGS` — niente quote, niente backtest, niente
    `δ` tarato. Conseguenza pratica: per questa raccolta il criterio
    «aggancio 924/924» **non esiste**, e sostituirlo con un aggancio inventato
    sarebbe peggio che non averlo. I controlli interni (i gol degli eventi
    contro il punteggio, l'identita' `Gol = 1T + 2T`) prendono il suo posto.

    La verita' su «quali leghe modelliamo» sta in un punto solo — §7 del
    CLAUDE.md — e questa funzione la chiede li' invece di ri-elencarla.
    """
    from ..config import LEAGUE_CONFIGS
    return lega in LEAGUE_CONFIGS


# Colonne che esistono nello schema e non contengono NULLA. Sono PER LEGA, e
# non e' un dettaglio: `Meteo (WhoScored)` e' vuota allo 0,0% in Serie A e
# piena al 95,9% in Premier. Non e' un difetto dell'export ma una copertura
# diversa della fonte — trattarla come costante avrebbe fatto scartare un dato
# buono su una lega per un buco che stava sull'altra.
#
# ⚠️ NELLE SUPERCOPPE LE COLONNE VUOTE SONO 41, e non e' un difetto: sono TRE
# famiglie con tre cause diverse, e distinguerle e' il punto.
#
#   (1) le 19 `(WhoScored)`  — la fonte non copre le cinque supercoppe
#       nazionali. Lo schema le prevede lo stesso: chi legge l'elenco delle
#       colonne conclude «c'e' anche WhoScored» e ha torto. Vedi `fonti()`.
#   (2) le 6 dei TEMPI SUPPLEMENTARI — vuote perche' i supplementari non si
#       sono giocati. ⭐ Non e' una curiosita': e' la conferma indipendente del
#       tripwire `gol_sono_regolamentari()`. Se un giorno si giocassero, queste
#       si riempirebbero E l'identita' `Gol = 1T + 2T` salterebbe: due segnali
#       che si controllano a vicenda.
#   (3) le 14 di CLASSIFICA (`Punti`, `Posizione`, `Vittorie`, `Girone`...) —
#       una supercoppa non ha una classifica. Vuote per natura del torneo.
#
# `Rigori casa/trasferta (SofaScore)` e' vuota nelle due supercoppe che NON
# hanno avuto lotteria (Supercopa e DFL) e piena nelle altre quattro: e' una
# colonna condizionale, non un buco.
_WHOSCORED_ASSENTE = (
    "Allenatore casa (WhoScored)", "Allenatore trasferta (WhoScored)",
    "Arbitro (WhoScored)", "Eventi Opta (WhoScored)", "ID casa (WhoScored)",
    "ID partita (WhoScored)", "ID trasferta (WhoScored)", "Meteo (WhoScored)",
    "Minuti giocati (WhoScored)", "Modulo casa (WhoScored)",
    "Modulo trasferta (WhoScored)", "Novanta minuti (WhoScored)",
    "Primo tempo (WhoScored)", "Rigori (WhoScored)", "Risultato (WhoScored)",
    "Spettatori (WhoScored)", "Stadio (WhoScored)", "Supplementari (WhoScored)",
    "possession % (normalizzato) (WhoScored)",
)
_SUPPLEMENTARI = (
    "Casa suppl. (SofaScore)", "Casa 1° suppl. (SofaScore)",
    "Casa 2° suppl. (SofaScore)", "Trasferta suppl. (SofaScore)",
    "Trasferta 1° suppl. (SofaScore)", "Trasferta 2° suppl. (SofaScore)",
)
_CLASSIFICA = (
    "Differenza reti", "Girone", "Gol fatti", "Gol subiti", "Note classifica",
    "Pareggi", "Partite giocate", "Posizione", "Punti", "Qualificazione",
    "Sconfitte", "Tipo classifica", "Vittorie",
)
_SUPERCOPPA_UNA_FONTE = (_WHOSCORED_ASSENTE + _SUPPLEMENTARI + _CLASSIFICA
                         + ("Discordanze", "Spettatori (SofaScore)",
                            "Riempimento % (SofaScore)"))

COLONNE_VUOTE: dict[str, dict[str, tuple[str, ...]]] = {
    "serie_a": {"squadre": ("Meteo (WhoScored)",), "heatmap": ("Tocchi",)},
    "premier_league": {"heatmap": ("Tocchi",)},
    # ⭐ La Champions ne ha solo DUE su 183 colonne, ed e' la raccolta piu'
    # piena dell'intera famiglia: ha le due fonti, i supplementari giocati e la
    # classifica della fase campionato. `Note classifica` e' vuota perche' nel
    # nuovo formato non ci sono note; `Meteo` e' assente in ogni consegna
    # WhoScored tranne Premier e Liga (§`copertura`).
    "uefa_champions_league": {"squadre": ("Meteo (WhoScored)", "Note classifica")},
    # La UEFA ha due fonti: niente famiglia (1), e Spettatori e' PIENA.
    "supercoppa_uefa": {"squadre": _SUPPLEMENTARI + _CLASSIFICA
                        + ("Meteo (WhoScored)",)},
    "supercoppa_italiana": {"squadre": _SUPERCOPPA_UNA_FONTE},
    "community_shield": {"squadre": _SUPERCOPPA_UNA_FONTE},
    "trophee_des_champions": {"squadre": _SUPERCOPPA_UNA_FONTE},
    # Queste due non hanno avuto NESSUNA partita ai rigori: +2 colonne vuote.
    "supercopa_espana": {"squadre": _SUPERCOPPA_UNA_FONTE
                         + ("Rigori casa (SofaScore)", "Rigori trasferta (SofaScore)")},
    "dfl_supercup": {"squadre": _SUPERCOPPA_UNA_FONTE
                     + ("Rigori casa (SofaScore)", "Rigori trasferta (SofaScore)")},
    # ⚠️ In Liga `Meteo` NON e' qui perche' non e' vuota: e' **quasi** vuota,
    # 2 righe su 760 (0,3%). Lo stato di mezzo si chiede a `copertura()`, che
    # esiste apposta — vedi la sua docstring per perche' due stati non
    # bastavano. `Tocchi` invece e' a zero su tutte e tre le leghe: quella e'
    # del formato.
    "la_liga": {"heatmap": ("Tocchi",)},
    # ⚠️ LALIGA2 NE HA **38**, ed e' il numero piu' alto di ogni campionato. Le
    # tre famiglie sono le stesse delle supercoppe, con le stesse cause:
    #
    #  (1) le 17 `(WhoScored)` di `squadre` + le 10 di `giocatori`. Lo schema
    #      prevede 19 colonne WhoScored a livello squadra e **due sole sono
    #      piene** (`Risultato` e `ID partita`); a livello giocatore ne prevede
    #      10 e sono piene **zero**. Non e' un buco dell'export: WhoScored qui
    #      da' solo `initialMatchDataForScrappers`, che e' una cronaca di
    #      eventi, non una scheda partita. Il contributo di quella fonte vive
    #      tutto dentro `eventi` (8.188 righe) — ed e' esattamente il caso che
    #      `fonti()` esiste per dichiarare: chi legge l'elenco delle colonne
    #      conclude «c'e' anche WhoScored a livello squadra» e ha torto.
    #  (2) le 8 dei SUPPLEMENTARI e dei RIGORI. Vuote perche' nessuna delle 468
    #      partite e' andata oltre il 90' — playoff promozione compreso, che
    #      pure e' l'unico posto dove sarebbe potuto succedere. ⭐ E' la
    #      conferma indipendente del tripwire `gol_sono_regolamentari()`, che
    #      qui torna **468/468**: due segnali che si controllano a vicenda.
    #  (3) `Note classifica`, vuota perche' questa classifica non ha note.
    #      Le altre 13 colonne di classifica NON sono qui: sono piene sulle 66
    #      righe di livello Stagione, cioe' esattamente dove devono stare.
    #
    # ⚠️ `Discordanze` e' vuota in `giocatori` e PIENA in `squadre` (618 righe).
    # Non e' una svista: il confronto fra fonti esiste solo dove le fonti sono
    # due, e a livello giocatore qui c'e' solo SofaScore.
    "laliga2": {
        "squadre": (
            "Casa suppl. (SofaScore)", "Trasferta suppl. (SofaScore)",
            "Casa 1° suppl. (SofaScore)", "Trasferta 1° suppl. (SofaScore)",
            "Casa 2° suppl. (SofaScore)", "Trasferta 2° suppl. (SofaScore)",
            "Rigori casa (SofaScore)", "Rigori trasferta (SofaScore)",
            "ID casa (WhoScored)", "ID trasferta (WhoScored)",
            "Primo tempo (WhoScored)", "Novanta minuti (WhoScored)",
            "Supplementari (WhoScored)", "Rigori (WhoScored)",
            "Minuti giocati (WhoScored)", "Allenatore casa (WhoScored)",
            "Allenatore trasferta (WhoScored)", "Modulo casa (WhoScored)",
            "Modulo trasferta (WhoScored)", "Stadio (WhoScored)",
            "Spettatori (WhoScored)", "Arbitro (WhoScored)", "Meteo (WhoScored)",
            "Eventi Opta (WhoScored)", "possession % (normalizzato) (WhoScored)",
            "Note classifica",
        ),
        "giocatori": (
            "Discordanze", "ID squadra (WhoScored)", "Altezza cm (WhoScored)",
            "Peso kg (WhoScored)", "Età (WhoScored)",
            "Migliore in campo (WhoScored)", "Entrato al minuto (WhoScored)",
            "Uscito al minuto (WhoScored)", "ratings (WhoScored)",
            "ID giocatore (WhoScored)", "ID partita (WhoScored)",
        ),
        "heatmap": ("Tocchi",),
    },
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

#: ⚠️⚠️ LA STESSA COLONNA E' AVVELENATA ANCHE IN `eventi`, E PER 12 RACCOLTE
#: NESSUNO SE N'ERA ACCORTO.
#:
#: In `squadre` e `giocatori` il difetto si vede: accanto alla colonna mista ci
#: sono quelle per-fonte, e `_rinomina_id_avvelenato` scatta. In `eventi` le
#: colonne per-fonte **non ci sono** — `ID partita` e' l'unica — quindi non
#: c'era niente da confrontare e la riparazione non e' mai partita. La colonna
#: sembra sana: e' piena al 100% e i suoi valori sono id veri.
#:
#: Misurato su tutte e 15 le raccolte (agosto 2026), gli stati sono TRE:
#:
#:   una fonte sola (7 UEFA/supercoppe)  ->  int, UNA numerazione     SANA
#:   SofaScore + Understat (5 campionati)->  int, DUE numerazioni     MISTA
#:   SofaScore + WhoScored (laliga2)     ->  **testo**, DUE FORMATI   MISTA
#:
#: Il conteggio lo dice da solo: la Serie A ha **760 id distinti per 380
#: partite**, cioe' ogni partita compare due volte con due numeri diversi (le
#: righe `Tiro` di Understat portano l'id di Understat). Un join su quella
#: colonna non sbaglia rumorosamente: **perde in silenzio** le 9.373 righe di
#: tiri di Understat, e chi conta i tiri ne conta meta' credendo di averli
#: tutti. Finto pieno da manuale (R6).
#:
#: ⚠️ La forma di LaLiga2 e' peggiore e piu' facile da vedere insieme: la
#: colonna e' **di testo**, e le righe WhoScored non contengono un numero ma
#: una FRASE — `"14081721 (SofaScore) / 1914700 (WhoScored)"`. Effetto: il join
#: numerico fallisce su **tutte e 94.404** le righe, comprese le 86.216
#: SofaScore che un id giusto ce l'hanno, perche' `"14081721" != 14081721`.
#:
#: ⭐ Ed e' proprio la forma peggiore a essere l'unica che si ripara da sola:
#: quella frase **contiene** l'id SofaScore, quindi il 100% delle righe si
#: normalizza senza uscire dal file. Nei 5 campionati serve invece la mappa
#: `ID partita (Understat)` -> `ID partita (SofaScore)` che sta in `squadre`
#: (misurata: copre il 100% delle righe Understat su tutte e cinque).
#:
#: Il valore dice la FORMA del veleno, non solo che c'e': serve a scegliere la
#: riparazione. Le raccolte assenti da questa mappa hanno una fonte sola e la
#: colonna sana — ed e' una MISURA, non un default prudenziale.
ID_EVENTI_MISTO: dict[str, str] = {
    "serie_a": "numerico", "premier_league": "numerico", "la_liga": "numerico",
    "bundesliga": "numerico", "ligue_1": "numerico",
    "laliga2": "testuale",
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


def _percorsi(nome: str, lega: str) -> list[Path]:
    """I file di `nome` per `lega`: uno solo, oppure le parti in ordine.

    ⚠️ UN BLOCCO PUO' ARRIVARE SPEZZATO. `eventi_opta` della Liga e' stato
    consegnato in `eventi_opta_parte1.csv.gz` e `_parte2.csv.gz`, ed e' un
    taglio **grezzo**, non logico: cade dentro una partita. Levante-Espanyol
    dell'11/01/2026 ha 166 eventi (fino al 7' del primo tempo) in parte1 e i
    restanti 1.327 in parte2 — contro una mediana di 1.517 eventi a partita.

    Chi leggesse una parte sola vedrebbe quella partita **monca senza che nulla
    glielo dica**: 166 eventi sono un numero plausibile per una riga di dati, e
    nessun conteggio di righe se ne accorge. Da cui la ricomposizione qui, che
    non e' una comodita' ma una riparazione.

    L'ordine e' quello del suffisso numerico, non quello alfabetico: con dieci
    parti `parte10` verrebbe prima di `parte2`.
    """
    base = raccolta(lega)
    intero = base / f"{nome}.csv.gz"
    if intero.exists():
        return [intero]

    parti = sorted(
        base.glob(f"{nome}_parte*.csv.gz"),
        key=lambda p: int("".join(c for c in p.stem.split("_parte")[-1] if c.isdigit()) or 0),
    )
    if parti:
        return parti

    if base.exists():
        presenti = sorted({x.name.split("_parte")[0].replace(".csv.gz", "")
                           for x in base.glob("*.csv.gz")})
        raise FileNotFoundError(
            f"la raccolta di {lega} non ha ancora {nome!r}. "
            f"Presenti: {presenti}. Vedi {base / 'README.md'}"
        )
    raise FileNotFoundError(
        f"nessuna raccolta a tre fonti per {lega!r}. "
        f"Disponibili: {leghe_disponibili()}"
    )


def _percorso(nome: str, lega: str) -> Path:
    """Come `_percorsi` ma pretende un file solo. Alza se il blocco e' spezzato."""
    p = _percorsi(nome, lega)
    if len(p) > 1:
        raise RuntimeError(
            f"{nome} di {lega} e' in {len(p)} parti: usa _percorsi() e concatena, "
            "altrimenti perdi le righe delle parti successive"
        )
    return p[0]


def _leggi(nome: str, lega: str, **kwargs) -> pd.DataFrame:
    """Legge un blocco, ricomponendolo se e' arrivato spezzato."""
    parti = _percorsi(nome, lega)
    frames = [pd.read_csv(p, **kwargs) for p in parti]
    if len(frames) > 1:
        log.info("%s di %s ricomposto da %d parti", nome, lega, len(frames))
        return pd.concat(frames, ignore_index=True)
    return frames[0]


# Alias validi SOLO dentro questa raccolta, e per una ragione precisa.
#
# ⚠️ `eventi_opta` della Liga scrive «Atletico» NUDO nella colonna `Squadra`,
# mentre `Casa`/`Trasferta` dello stesso file scrivono «Atlético Madrid»: due
# convenzioni in due colonne dello stesso file. Effetto misurato: l'aggancio di
# eventi_opta si ferma a 722/760 squadra-partita, e le 38 mancanti sono tutte
# dell'Atletico — mentre le PARTITE agganciano 380/380, il che rende il difetto
# invisibile a un controllo per partita.
#
# Perche' NON in sources.TEAM_ALIASES: quella mappa e' globale al progetto, e
# «Atletico» da solo e' ambiguo fuori dalla Liga (Atletico Mineiro, Atletico
# Nacional, decine di altri). Mapparlo li' sarebbe un join che indovina — la
# cosa che la regola d'oro vieta. Qui il perimetro e' noto: il file e' di Liga
# 2025-26 e le sue 20 squadre sono quelle.
ALIAS_RACCOLTA: dict[str, dict[str, str]] = {
    "la_liga": {"Atletico": "Atlético Madrid"},
    # Stesso difetto, seconda occorrenza: la colonna `Squadra` di `eventi_opta`
    # usa una forma che le altre colonne dello stesso file non usano. In
    # Bundesliga e' la SIGLA «RBL» (RB Leipzig), mentre `Casa`/`Trasferta`
    # scrivono il nome intero. Costava 34 squadra-partita su 612.
    #
    # ⚠️ Il difetto si e' ripetuto su due leghe su cinque, sempre su UNA squadra
    # e sempre nella stessa colonna: non e' un incidente, e' una proprieta' di
    # `eventi_opta`. Chi aggiunge una lega deve MISURARE quella colonna a parte,
    # perche' l'aggancio per PARTITA resta perfetto e non lo rivela.
    "bundesliga": {"RBL": "RB Leipzig"},
    # ⚠️ TERZA occorrenza, e la peggiore: nella Supercoppa UEFA `eventi_opta`
    # scrive la forma corta per **entrambe** le squadre, su 1.393 righe su
    # 1.393 — cioe' il 100%, contro il 5% della Liga e il 6% della Bundesliga.
    # Tre raccolte su quattro che hanno `eventi_opta` hanno questo difetto: e'
    # la regola, non l'eccezione. Chi consegna una raccolta nuova con
    # `eventi_opta` deve misurare quella colonna PRIMA di dichiararla agganciata.
    "supercoppa_uefa": {"PSG": "Paris Saint-Germain",
                        "Tottenham": "Tottenham Hotspur"},
    # ⚠️ QUARTA occorrenza, e di natura diversa dalle prime tre: qui il file NON
    # e' incoerente con se stesso (le 22 squadre hanno una grafia sola in tutte
    # le colonne). E' incoerente con il RESTO DEL PROGETTO, e per una sola
    # ragione: **gli accenti**.
    #
    # La grafia canonica del progetto e' quella di football-data, che e' ASCII —
    # misurato: negli snapshot delle 5 leghe i nomi accentati sono **zero**. La
    # raccolta arriva invece con la grafia SofaScore, accentata. Delle 22
    # squadre, misurate una per una contro TUTTI i nostri snapshot:
    #
    #   6  gia' canoniche          Eibar, Granada, Huesca, e — via TEAM_ALIASES —
    #                              Malaga, Valladolid, Las Palmas
    #   3  divergono SOLO per accento   Almeria, Cadiz, Leganes   <- queste tre
    #  13  assenti dai nostri dati      mai in prima divisione nella nostra
    #                                   finestra 2017-2025
    #
    # Si mappano **solo le tre di mezzo**, e non e' timidezza: per quelle il
    # bersaglio e' un fatto verificato (lo stesso club sta nei nostri snapshot
    # scritto cosi'), mentre per le altre tredici non esiste alcun bersaglio e
    # inventarne uno sarebbe indovinare un join — la cosa che la regola d'oro
    # vieta. `TEAM_ALIASES` ha gia' `UD Almeria`->`Almeria`, `Cadiz CF`->`Cadiz`,
    # `CD Leganes`->`Leganes`: mancavano le forme NUDE, che sono quelle che usa
    # SofaScore.
    #
    # ⚠️⚠️ E QUI SOTTO C'E' LA TRAPPOLA VERA, che vale la pena leggere anche se
    # non si tocchera' mai questa lega. Fra le 22 c'e' **`Real Sociedad B`**, la
    # squadra riserve. Cercandole un corrispondente per somiglianza — come
    # farebbe qualunque fuzzy match — si trova `Sociedad`, cioe' la **prima
    # squadra**, che gioca in un'altra divisione. Sarebbe un aggancio
    # **univoco, sicuro di se' e falso**: nessun conteggio di celle piene lo
    # vedrebbe, perche' la cella risulta piena e la riga agganciata. E' la
    # stessa famiglia dell'`Espanol`->«Jove Espanol San Vicente» di
    # docs/audit_identita. Per questo la mappa qui e' scritta a mano, chiusa, e
    # NON generata da una somiglianza.
    "laliga2": {"Almería": "Almeria", "Cádiz": "Cadiz", "Leganés": "Leganes"},
}

# Quante SQUADRE e quante PARTITE ha ogni campionato. Non e' una costante:
# Bundesliga e Ligue 1 hanno 18 squadre e 306 partite, le altre tre 20 e 380.
# Serve per dire «760 attese» o «612 attese» senza inchiodare il numero.
DIMENSIONI: dict[str, tuple[int, int]] = {
    "serie_a": (20, 380), "premier_league": (20, 380), "la_liga": (20, 380),
    "bundesliga": (18, 306), "ligue_1": (18, 306),
    # LaLiga2: 22 squadre, quindi 42 giornate da 11 partite = 462. E' il primo
    # campionato del progetto che non ha ne' 20 ne' 18 squadre — la ragione per
    # cui questa mappa esiste invece di una costante.
    "laliga2": (22, 462),
}

# ⚠️ I TURNI CHE NON SONO GIORNATE DI CAMPIONATO.
#
# In Bundesliga e Ligue 1 la stagione non finisce con l'ultima giornata: c'e' lo
# **spareggio** promozione/retrocessione contro squadre di seconda divisione.
# Quelle partite nei nostri snapshot NON ci sono, e tenerle dentro gonfia i
# conteggi e tira dentro squadre che nel campionato non giocano.
#
# ⚠️ La prima stesura inchiodava un valore solo — `Turno == "Finale"`, che
# bastava per la Bundesliga (Wolfsburg-Paderborn, 2 partite). Sulla Ligue 1 lo
# spareggio e' a TRE turni («1° turno preliminare», «2° turno preliminare»,
# «Finale») e la costante ne avrebbe preso un quarto: 4 righe su 8, lasciando
# dentro 3 squadre di Ligue 2 e portando il conteggio a 616 invece di 612.
# Da cui la regola: in un CAMPIONATO, tutto cio' che non e' «Giornata N» e'
# spareggio.
#
# ⚠️ E la regola vale SOLO per i campionati. Nelle competizioni UEFA i turni
# fuori schema («3° turno preliminare», «Ottavi di finale», «Spareggi di
# knockout») sono la competizione stessa: escluderli butterebbe meta' del
# torneo. Da cui `E_CAMPIONATO`.
PREFISSO_GIORNATA = "Giornata"

#: True = campionato (i turni non-«Giornata N» sono lo spareggio, e vanno fuori).
#: False = coppa/torneo (ogni turno e' competizione, non si esclude niente).
E_CAMPIONATO: dict[str, bool] = {
    "serie_a": True, "premier_league": True, "la_liga": True,
    "bundesliga": True, "ligue_1": True,
    # ⚠️ LALIGA2 E' UN CAMPIONATO, MA IL SUO «SPAREGGIO» E' UN'ALTRA COSA — e
    # la regola sopra ci arriva col nome giusto e la ragione sbagliata.
    #
    # In Bundesliga e Ligue 1 le partite fuori-giornata sono lo spareggio
    # promozione/retrocessione **contro squadre di seconda divisione**: si
    # escludono perche' tirano dentro squadre estranee al campionato e fanno
    # fallire l'aggancio allo snapshot. Qui i turni fuori-giornata sono le 6
    # partite del **playoff promozione**, che LaLiga2 gioca **fra squadre di
    # LaLiga2** (Almeria, Castellon, Las Palmas, Malaga — tutte e quattro gia'
    # nelle 42 giornate). Misurato: **22 squadre col playoff e 22 senza**, e
    # nessuno snapshot da agganciare, perche' `data/laliga2_matches.csv` non
    # esiste. Nessuna delle due ragioni storiche vale.
    #
    # Resta `True` lo stesso, per una ragione diversa e piu' semplice: il
    # default di questo modulo e' «il campionato», cioe' il girone all'italiana
    # da 462 partite, e un playoff a eliminazione mescolato dentro un `groupby`
    # e' la stessa sorpresa che le righe di classifica sarebbero in mezzo a
    # quelle di partita. Chi vuole la stagione INTERA — ed e' una richiesta
    # legittima, quelle 6 partite sono competizione vera e non partite di
    # un'altra lega — passa `spareggio=True` e le riprende tutte.
    "laliga2": True,
    "uefa_champions_league": False,
    "uefa_europa_league": False, "uefa_conference_league": False,
    # Le supercoppe: il turno e' «Finale» (o «Semifinali» nelle due a final
    # four). Trattarle da campionato butterebbe via TUTTA la raccolta, perche'
    # nessun turno si chiama «Giornata N».
    "supercoppa_uefa": False, "supercoppa_italiana": False,
    "supercopa_espana": False, "community_shield": False,
    "dfl_supercup": False, "trophee_des_champions": False,
}


def _togli_spareggio(df: pd.DataFrame, lega: str, spareggio: bool) -> pd.DataFrame:
    """Toglie le righe dello spareggio promozione/retrocessione, se richiesto.

    Default: FUORI, e solo nei CAMPIONATI. E' la stessa convenzione di
    `player_stats.load_player_matches`, e per la stessa ragione: quelle partite
    nei nostri snapshot **non ci sono** — sono di seconda divisione — quindi
    tenerle dentro fa fallire l'aggancio e gonfia i conteggi.

    Nelle competizioni UEFA non tocca nulla: li' i turni fuori schema sono la
    competizione (vedi `E_CAMPIONATO`).
    """
    if spareggio or "Turno" not in df.columns or not E_CAMPIONATO.get(lega, False):
        return df
    fuori = df["Turno"].notna() & ~df["Turno"].astype(str).str.startswith(PREFISSO_GIORNATA)
    if fuori.any():
        log.info("escluse %d righe di spareggio (%s): turni %s", int(fuori.sum()), lega,
                 sorted(df.loc[fuori, "Turno"].unique()))
    return df[~fuori].copy()


def _normalizza_squadre(df: pd.DataFrame, lega: str = LEGA_DEFAULT) -> pd.DataFrame:
    """Porta i nomi squadra alla grafia canonica del progetto.

    Due passaggi, in quest'ordine: prima gli alias LOCALI alla raccolta
    (`ALIAS_RACCOLTA`, che riparano le convenzioni interne al file), poi quelli
    globali del progetto (`TEAM_ALIASES`).

    Non e' cosmesi: senza, `Hellas Verona` e `Verona` restano due squadre per
    qualunque join, ed e' esattamente il bug che il §5 del CLAUDE.md racconta.
    """
    locali = ALIAS_RACCOLTA.get(lega, {})

    def canonico(x):
        if not isinstance(x, str):
            return x
        return TEAM_ALIASES.get(locali.get(x, x), locali.get(x, x))

    for col in ("Squadra", "Avversario", "Casa", "Trasferta"):
        if col in df.columns:
            df[col] = df[col].map(canonico)
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


def _ripara_id_eventi(df: pd.DataFrame, lega: str) -> pd.DataFrame:
    """Da' a `eventi` una colonna-chiave utilizzabile, e marca quella che non lo e'.

    Fa due cose, e la seconda e' la meta' che conta:

    1. **aggiunge** `ID partita (SofaScore)`, l'id della partita nella
       numerazione di SofaScore, su ogni riga — cosi' `eventi` si aggancia a
       `squadre`, a `giocatori` e alla `heatmap`, che quella numerazione la
       usano gia';
    2. **rinomina** la colonna grezza in `ID partita (misto, NON usare)` dove
       e' mista. Rinominare invece di cancellare e' la stessa scelta di
       `_rinomina_id_avvelenato`: chi legge il frame vede che nel grezzo la
       colonna c'e', e vede nel nome perche' non va usata.

    Le due forme del veleno chiedono due riparazioni diverse (vedi
    `ID_EVENTI_MISTO`): quella testuale si risolve dentro il file, quella
    numerica ha bisogno della mappa che sta in `squadre`.

    ⚠️ IL TRIPWIRE. Se la riparazione non copre TUTTE le righe, la funzione
    alza. Una chiave di join a meta' e' peggio di una chiave assente: la
    assente rompe subito, quella a meta' fa sparire righe in silenzio — che e'
    esattamente il difetto che questa funzione esiste per chiudere.
    """
    if ID_AVVELENATO not in df.columns or ID_AVVELENATO not in df:
        return df
    forma = ID_EVENTI_MISTO.get(lega)
    if forma is None:
        return df              # una fonte sola: la colonna e' gia' un id pulito

    colonna_pulita = ID_PARTITA_PER_FONTE["SofaScore"]
    if forma == "testuale":
        # "14081721 (SofaScore) / 1914700 (WhoScored)" -> 14081721
        pulito = df[ID_AVVELENATO].astype(str).str.extract(r"^\s*(\d+)")[0]
    else:
        pulito = _id_sofascore_dalle_altre_fonti(df, lega)
    pulito = pd.to_numeric(pulito, errors="coerce").astype("Int64")

    scoperte = int(pulito.isna().sum())
    if scoperte:
        raise RuntimeError(
            f"la riparazione dell'ID partita di eventi({lega!r}) lascia scoperte "
            f"{scoperte} righe su {len(df)}. Non si prosegue con una chiave a meta': "
            f"vedi ID_EVENTI_MISTO e misura la colonna prima di dichiararla riparata."
        )

    df = df.rename(columns={ID_AVVELENATO: ID_RINOMINATO})
    df[colonna_pulita] = pulito
    return df


def _id_sofascore_dalle_altre_fonti(df: pd.DataFrame, lega: str) -> pd.Series:
    """L'id SofaScore riga per riga, traducendo quello delle altre fonti.

    Le righe con `Fonte == "SofaScore"` portano gia' il numero giusto; per le
    altre serve la corrispondenza fra le due numerazioni, che sta in `squadre`
    ed e' l'unico posto del progetto dove le due colonne convivono sulla stessa
    riga. Misurata all'agosto 2026: copre il **100%** delle righe Understat su
    tutte e cinque le leghe.
    """
    fonte = df["Fonte"] if "Fonte" in df.columns else pd.Series("SofaScore", index=df.index)
    pulito = pd.to_numeric(df[ID_AVVELENATO], errors="coerce")

    for nome_fonte in fonte.dropna().unique():
        if nome_fonte == "SofaScore":
            continue
        colonna = ID_PARTITA_PER_FONTE.get(nome_fonte)
        if colonna is None:
            continue
        chiavi = _leggi("squadre", lega, low_memory=False,
                        usecols=[colonna, ID_PARTITA_PER_FONTE["SofaScore"]]).dropna()
        mappa = dict(zip(chiavi[colonna], chiavi[ID_PARTITA_PER_FONTE["SofaScore"]]))
        righe = fonte == nome_fonte
        pulito.loc[righe] = pulito.loc[righe].map(mappa)
    return pulito


def squadre(lega: str = LEGA_DEFAULT, *, solo_partite: bool = True,
            periodo: str | None = None, spareggio: bool = False) -> pd.DataFrame:
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
    df = _leggi("squadre", lega, low_memory=False)

    prima = len(df)
    maschera_orfane = pd.Series(False, index=df.index)
    for data, squadra in ORFANE.get(lega, ()):
        maschera_orfane |= (df["Data"] == data) & (df["Squadra"] == squadra) & df["Avversario"].isna()
    df = df[~maschera_orfane].copy()
    if prima - len(df):
        log.info("scartate %d righe orfane Verona/Hellas Verona", prima - len(df))

    df = _togli_spareggio(df, lega, spareggio)
    if solo_partite:
        df = df[df["Livello"] == "Partita"].copy()
    if periodo is not None:
        df = df[df["Periodo"] == periodo].copy()

    df = _normalizza_squadre(df, lega)
    df = _scorpora_rigori(df, lega)
    return df.reset_index(drop=True)


def _scorpora_rigori(df: pd.DataFrame, lega: str) -> pd.DataFrame:
    """Aggiunge le colonne derivate del punteggio dove l'export non le da'.

    La riparazione vive **in lettura**, come tutte le altre di questo modulo: i
    file restano come consegnati (R3) e chi legge trova le stesse due colonne
    che la Conference dichiara da sola, con lo stesso significato. Cosi'
    `punteggio_vero()` funziona su ogni raccolta senza sapere quale sia.

    Non tocca nulla dove `RIGORI_NEL_PUNTEGGIO` dice `False` — e li' aggiungere
    le colonne sarebbe peggio che non farlo: sottrarre i rigori dal punteggio
    della Champions darebbe **1 − 4 = −3** sulla finale PSG-Arsenal.
    """
    if not RIGORI_NEL_PUNTEGGIO.get(lega, False):
        return df
    if all(c in df.columns for c in COLONNE_PUNTEGGIO_VERO):
        return df          # l'export le dichiara gia' (Conference)
    if not all(c in df.columns for c in COLONNE_RIGORI):
        raise KeyError(
            f"{lega} e' dichiarata col punteggio gonfiato dai rigori ma non ha "
            f"{COLONNE_RIGORI}: la riparazione non e' applicabile, verifica la consegna")
    rig_c = pd.to_numeric(df[COLONNE_RIGORI[0]], errors="coerce").fillna(0)
    rig_t = pd.to_numeric(df[COLONNE_RIGORI[1]], errors="coerce").fillna(0)
    df = df.copy()
    df[COLONNE_PUNTEGGIO_VERO[0]] = df["Gol casa (SofaScore)"] - rig_c
    df[COLONNE_PUNTEGGIO_VERO[1]] = df["Gol trasferta (SofaScore)"] - rig_t
    df["Decisa ai rigori (derivata)"] = pd.Series(
        ["si" if x else "no" for x in (rig_c + rig_t > 0)], index=df.index)
    n = int((rig_c + rig_t > 0).sum())
    if n:
        log.info("%s: scorporata la lotteria dei rigori da %d squadra-partita", lega, n)
    return df


def classifica(lega: str = LEGA_DEFAULT) -> pd.DataFrame:
    """Le 60 righe di livello Stagione: la classifica in tre versioni.

    `Tipo classifica` distingue generale / casa / trasferta. E' l'unico posto
    del progetto dove la classifica di Serie A esiste come dato invece che
    come qualcosa da ricalcolare dai risultati.
    """
    df = _leggi("squadre", lega, low_memory=False)
    df = df[df["Livello"] == "Stagione"].copy()
    piene = [c for c in df.columns if df[c].notna().any()]
    return _normalizza_squadre(df[piene], lega).reset_index(drop=True)


def giocatori(lega: str = LEGA_DEFAULT, *, livello: str | None = "Partita",
              spareggio: bool = False) -> pd.DataFrame:
    """Giocatore-partita, 190 colonne da tre fonti.

    `livello` filtra la colonna omonima: `Partita` (17.829 righe, il default),
    `Rosa` (711) o `Stagione` (586). Come per `squadre`, tre grane diverse nello
    stesso file sono una trappola se non si sceglie.

    Applica: normalizzazione dei nomi squadra, rinomina dell'`ID partita`
    avvelenato, e la correzione dei 2 gol persi da Understat (riparazione 4).
    """
    df = _leggi("giocatori", lega, low_memory=False)
    df = _togli_spareggio(df, lega, spareggio)
    if livello is not None and "Livello" in df.columns:
        df = df[df["Livello"] == livello].copy()

    df = _rinomina_id_avvelenato(df)
    df = _normalizza_squadre(df, lega)

    df = _allinea_gol(df, lega)
    return df.reset_index(drop=True)


def _allinea_gol(df: pd.DataFrame, lega: str) -> pd.DataFrame:
    """Allinea i gol di Understat a SofaScore dove il file dichiara discordanza.

    SofaScore vince in ENTRAMBI i versi, e i due versi hanno due cause diverse,
    misurate su tutte e cinque le leghe (13 righe discordanti in totale):

    | verso | righe | autogol nella partita | causa |
    |---|--:|--:|---|
    | SofaScore > Understat | **12** | **0/12** | Understat PERDE un gol vero |
    | Understat > SofaScore | **1** | **1/1** | Understat ATTRIBUISCE l'autogol al marcatore avversario |

    La separazione e' perfetta: la presenza di un autogol nella partita predice
    il verso 13 volte su 13.

    ⚠️ COME CI SIAMO ARRIVATI, e perche' conta. La prima stesura della regola
    valeva in UN verso solo, con un tripwire che alzava se Understat avesse
    dichiarato PIU' gol. Sulla Ligue 1 il tripwire **e' scattato**: Emersonn
    (Toulouse, 05/10/2025) 1 contro 2. Istruito a mano — Lyon-Toulouse 1-2, e
    dei due gol del Tolosa uno e' l'**autogol di Clinton Mata all'87'**, che
    Understat accredita a Emersonn. Il tripwire ha fatto esattamente il suo
    mestiere: fermare invece di applicare una regola la cui premessa era caduta.

    E c'e' un'ironia utile: l'ipotesi «sara' la convenzione sugli autogol» era
    **falsa** per i primi 9 casi (verificata e smentita su 4 fonti) ed e' **vera**
    per il decimo. Lo stesso sintomo, due cause — motivo per cui la verifica va
    rifatta e non ereditata.

    ⚠️ IL TRIPWIRE CHE RESTA: uno scarto maggiore di 1 gol, o un
    `Understat > SofaScore` in una partita SENZA autogol, romperebbe la
    spiegazione. In quel caso la funzione alza invece di correggere in silenzio.
    """
    df["gol_corretto_da_noi"] = False
    if not {"Gol (SofaScore)", "Gol (Understat)", "Discordanze"} <= set(df.columns):
        return df

    marcate = df["Discordanze"].fillna("").str.contains(r"\bgol\b", regex=True)
    if not marcate.any():
        return df

    sofa = pd.to_numeric(df["Gol (SofaScore)"], errors="coerce")
    under = pd.to_numeric(df["Gol (Understat)"], errors="coerce")
    scarto = (sofa - under).abs()

    grosse = marcate & (scarto > 1).fillna(False)
    if grosse.any():
        raise RuntimeError(
            f"scarto sui gol maggiore di 1 su {df.loc[grosse, ['Data', 'Giocatore']].to_dict('records')}. "
            "Le due cause note (Understat perde un gol / accredita un autogol) valgono "
            "1 gol ciascuna: qui c'e' altro. Istruire a mano — vedi _allinea_gol."
        )

    # Il verso «Understat di piu'» si spiega SOLO con un autogol nella partita.
    sopra = marcate & (under > sofa).fillna(False)
    if sopra.any():
        _verifica_autogol(df.loc[sopra], lega)

    da_correggere = marcate & (sofa != under) & sofa.notna() & under.notna()
    df.loc[da_correggere, "Gol (Understat)"] = df.loc[da_correggere, "Gol (SofaScore)"]
    df.loc[da_correggere, "gol_corretto_da_noi"] = True
    if da_correggere.any():
        log.info("allineati %d gol a SofaScore (%s)", int(da_correggere.sum()), lega)
    return df


def _verifica_autogol(righe: pd.DataFrame, lega: str) -> None:
    """Alza se una riga «Understat > SofaScore» NON ha un autogol a spiegarla.

    E' il tripwire della seconda causa. Senza, una riga con quel verso verrebbe
    corretta assumendo una spiegazione che non e' stata verificata su di lei.
    """
    try:
        ev = _leggi("eventi", lega, low_memory=False)
    except FileNotFoundError:
        return                                   # senza eventi non si puo' verificare
    autogol = ev[(ev.get("Categoria") == "Evento") & (ev.get("Sottotipo") == "ownGoal")]
    senza = [
        {"Data": r["Data"], "Giocatore": r["Giocatore"]}
        for _, r in righe.iterrows()
        if not len(autogol[autogol["Data"] == r["Data"]])
    ]
    if senza:
        raise RuntimeError(
            f"Understat dichiara PIU' gol di SofaScore su {senza}, e in quelle partite "
            "NON c'e' un autogol. La spiegazione nota (Understat accredita l'autogol al "
            "marcatore avversario) qui non vale: istruire a mano prima di proseguire."
        )


def eventi(lega: str = LEGA_DEFAULT, *, categoria: str | None = None,
           spareggio: bool = False) -> pd.DataFrame:
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

    ⚠️ **NON SONO SEMPRE SETTE, E `Evento` NON VIENE SEMPRE DA UNA FONTE SOLA.**
    Due cose che nei primi cinque campionati erano costanti e non lo sono:

    * in **LaLiga2** le categorie sono **sei**: `Cronaca` non c'e' perche'
      l'endpoint `/comments` di SofaScore risponde 404 su **468 partite su
      468** — l'unico dei dodici endpoint per partita a non rispondere. Non e'
      una raccolta parziale, e' una competizione su cui quel dato non esiste;
    * sempre in LaLiga2, `Evento` arriva da **due fonti insieme** — 9.377 righe
      SofaScore e 8.188 WhoScored — che raccontano **gli stessi** gol,
      cartellini e cambi. Nelle altre raccolte l'unica categoria a due fonti e'
      `Tiro`. ⚠️ Chi contasse i gol da `eventi(categoria="Evento")` senza
      filtrare la fonte ne conterebbe **circa il doppio**: 1.229 su SofaScore e
      1.222 su WhoScored, per 1.229 gol veri. Filtra sempre `Fonte`, e per i
      gol la fonte e' SofaScore (`preferita("gol")`), che qui ricostruisce il
      punteggio su **936 squadra-partita su 936**.

    ⚠️ Sulla colonna `ID partita` — che in questo file e' avvelenata in **ogni**
    raccolta a due fonti, LaLiga2 compresa — vedi `ID_EVENTI_MISTO` e
    `_ripara_id_eventi`: qui esce riparata, come `ID partita (SofaScore)`.
    """
    df = _leggi("eventi", lega, low_memory=False)
    df = _ripara_id_eventi(df, lega)
    df = _togli_spareggio(df, lega, spareggio)
    if categoria is not None:
        valide = set(df["Categoria"].dropna().unique())
        if categoria not in valide:
            raise ValueError(f"categoria {categoria!r} assente. Valide: {sorted(valide)}")
        df = df[df["Categoria"] == categoria].copy()
    return _normalizza_squadre(df, lega).reset_index(drop=True)


def eventi_opta(lega: str = LEGA_DEFAULT, *, partita: int | None = None,
                colonne: list[str] | None = None, spareggio: bool = False) -> pd.DataFrame:
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
    df = _leggi("eventi_opta", lega, low_memory=False, usecols=colonne)
    df = _togli_spareggio(df, lega, spareggio)
    if partita is not None and "ID partita" in df.columns:
        df = df[df["ID partita"] == partita].copy()
    return _normalizza_squadre(df, lega).reset_index(drop=True)


def heatmap(lega: str = LEGA_DEFAULT, *, partita: int | None = None,
            spareggio: bool = False) -> pd.DataFrame:
    """Posizioni: una riga per tocco, con X/Y su scala 0-100. Fonte SofaScore.

    380 partite, 586 giocatori, 556.996 righe. `partita` e' l'`ID partita` di
    SofaScore. La colonna `Tocchi` e' **vuota al 100%**: c'e' nello schema e non
    contiene niente (vedi `colonne_vuote`).
    """
    df = _leggi("heatmap", lega, low_memory=False)
    df = _togli_spareggio(df, lega, spareggio)
    if partita is not None:
        df = df[df["ID partita"] == partita].copy()
    return _normalizza_squadre(df, lega).reset_index(drop=True)


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
        return _leggi("legenda", lega)
    if versione == "v1":
        return _leggi("legenda_v1_incompleta", lega)
    raise ValueError(f"versione {versione!r} sconosciuta: usa 'v1' o 'v2'")


# ---------------------------------------------------------------------------
# Le funzioni che DICHIARANO i limiti, invece di lasciarli scoprire a valle.
# ---------------------------------------------------------------------------
def colonne_vuote(lega: str = LEGA_DEFAULT) -> dict[str, tuple[str, ...]]:
    """Le colonne che esistono nello schema e non contengono nulla, PER LEGA.

    Non e' una costante del formato: `Meteo (WhoScored)` e' vuota allo 0,0% in
    Serie A e piena al **98,4%** in Premier. Trattarla come costante avrebbe
    fatto scartare un dato buono su una lega per un buco che stava sull'altra —
    ed e' il motivo per cui questa funzione prende `lega`.

    ⚠️ Elenca solo le colonne **davvero** a zero. Per lo stato intermedio —
    quello pericoloso — usa `copertura()`.
    """
    return dict(COLONNE_VUOTE.get(lega, {}))


#: Sotto questa quota una colonna e' «quasi vuota»: ci sono valori, ma troppo
#: pochi per costruirci sopra. Non e' una soglia statistica, e' il confine
#: oltre il quale un `notna().any()` smette di essere una risposta utile.
SOGLIA_QUASI_VUOTA = 0.05


def copertura(colonna: str, lega: str = LEGA_DEFAULT, *, blocco: str = "squadre") -> dict:
    """Quanto e' piena una colonna, e in quale dei TRE stati si trova.

    ⚠️ Nasce dalla terza lega, e dal fatto che due stati non bastavano.
    `Meteo (WhoScored)` misurata sulle tre raccolte:

        Serie A          0,0%    (0 righe su 760)   -> vuota
        La Liga          0,3%    (2 righe su 760)   -> QUASI VUOTA
        Premier         98,4%  (748 righe su 760)   -> piena

    Lo stato di mezzo e' il piu' insidioso dei tre, ed e' una forma di finto
    pieno (R6): un `notna().any()` risponde «si', la colonna funziona», e chi
    ci costruisce sopra lavora su 2 righe credendone 760. Una colonna a zero
    almeno si dichiara da sola.

    Restituisce lo stato invece di un booleano proprio per non far collassare
    di nuovo tre casi in due.
    """
    frame = {"squadre": lambda: squadre(lega, solo_partite=False),
             "giocatori": lambda: giocatori(lega, livello=None),
             "heatmap": lambda: heatmap(lega),
             "eventi": lambda: eventi(lega)}[blocco]()
    if colonna not in frame.columns:
        raise KeyError(f"{colonna!r} non e' in {blocco} di {lega}")
    quota = float(frame[colonna].notna().mean())
    if quota == 0.0:
        stato = "vuota"
    elif quota < SOGLIA_QUASI_VUOTA:
        stato = "quasi vuota"
    else:
        stato = "piena"
    return {"colonna": colonna, "lega": lega, "blocco": blocco,
            "quota": quota, "righe_piene": int(frame[colonna].notna().sum()),
            "righe": len(frame), "stato": stato}


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
            cols = list(_leggi(nome, lega, nrows=0).columns)
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
