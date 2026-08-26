"""🗄️  actual_database2526.csv — TUTTO il 2025-26 in una tabella sola.

COSA PRODUCE
────────────
`data/actual_database2526.csv`: **una riga per PARTITA** della stagione
2025-26, per ogni competizione di cui il repo ha dati, con accanto tutto ciò
che è riconducibile a quella partita — anagrafica, risultato per periodo,
stadio, meteo, arbitro, allenatori, moduli, statistiche di squadra da tre
fonti e per periodo, quote, statistiche dei giocatori, formazioni, cambi,
cronaca degli eventi.

PERCHÉ QUESTA GRANA (e cosa costa)
──────────────────────────────────
Il repo tiene i dati 2025-26 su **quattro grane diverse**: partita,
squadra-partita-periodo, giocatore-partita, evento (fino al singolo tocco
Opta). Un CSV solo può averne UNA. La partita è l'unica che le regge tutte:

* squadra-partita → si affianca in `casa_*` / `trasferta_*`;
* giocatore-partita → non entra in colonne (≈30 giocatori × ~190 statistiche
  a partita). Entra **impacchettato** in `tf_casa_giocatori_json` /
  `tf_trasferta_giocatori_json`, nella forma tabellare
  `{"campi":[…],"righe":[[…],…]}` che `json_tabellare` documenta, più
  le colonne riassuntive (`*_formazione`, `*_marcatori`, `*_ammoniti`,
  `*_rating_medio`, …). ⚠️ Il pacchetto tiene le 34 voci di `CAMPI_GIOCATORE`,
  non tutte le ~190: con tutte peserebbe 69 MB da solo. Le escluse sono le
  anagrafiche del giocatore (nazionalità, altezza, data di nascita, valore,
  piede) — dati `statico` per R8, che non descrivono QUESTA partita e vivono
  in `files/tre_fonti_*/giocatori.csv.gz`. Di quelle restano gli aggregati di
  squadra (`*_altezza_media_cm`, `*_valore_schierati_eur`);
* evento → entra come **cronaca compatta** (`cronaca`: gol, cartellini,
  sostituzioni col minuto) e come **conteggi** (`tf_n_eventi_opta`,
  `tf_n_posizioni_heatmap`, `tf_n_tiri_tracciati`). L'event data completo
  resta dov'è, e non è un ripiego: sono 2,7 milioni di tocchi Opta, 4,8
  milioni di posizioni e 300 mila tiri, cioè due-tre ordini di grandezza più
  delle 4.169 partite. Il tiro-per-tiro è stato **provato** in questo file e
  tolto: impacchettato pesava 25 MB su 55, un quarto del totale, per un dato
  che vive completo in `files/tre_fonti_*/eventi.csv.gz` (categoria «Tiro»).
  Il conteggio dice che c'è e quanto è denso; il dato si prende di là.

⚠️ Quindi questo file è **completo alla grana della partita**, non un dump di
tutto il repo. Cosa NON c'è, e dove sta, è scritto nel README della sezione
«actual_database2526» di `docs/DATI.md`.

LE FONTI CHE CONFLUISCONO
─────────────────────────
  1. `files/tre_fonti_*_2526`      16 competizioni · SofaScore+Opta+Understat
  2. `data/coppe_2526`             6 coppe nazionali · player-scores/diretta
  3. `files/diretta_*_2526`        5 campionati + 6 coppe · diretta.it
  4. `data/{lega}_matches.csv`     5 campionati · football-data+Understat+quote
  5. `files/sofascore_coppe_europee_2526`  CL/EL/Conference · tiri e momentum
  6. `files/player_scores`         arbitro/allenatore da Transfermarkt
  7. `data/ranking_uefa`           coefficienti UEFA di club
  8. `data/squad_value_2526_transfermarkt.csv`   valore rosa

CONVENZIONI DI NOME DELLE COLONNE
─────────────────────────────────
    <blocco>_<lato>_<periodo>_<statistica>
  blocco    tf (tre fonti) · dir (diretta.it) · snap (snapshot) · sof (SofaScore
            coppe europee) · cop (raccolta coppe) · ps (player-scores)
  lato      casa · trasferta · (assente = dato di partita)
  periodo   tot · 1t · 2t · sup1 · sup2 · (assente = non ha periodo)
La fonte originale resta nel nome della statistica quando c'era —
`(SofaScore)`, `(WhoScored)`, `(Understat)` — perché due fonti che misurano la
stessa grandezza NON sono la stessa colonna (vedi `tre_fonti.preferita`).

REGOLE RISPETTATE
─────────────────
* **R3** — nessun file di dati viene modificato: si legge attraverso i moduli
  (`src.data.tre_fonti`, `team_stats`, `player_stats`, `allenatori`, …) che
  applicano le riparazioni in lettura.
* **R6** — le colonne interamente vuote su TUTTE le competizioni vengono
  scartate: una colonna che c'è e non contiene niente è un finto pieno.
* **R8** — il file mescola per natura dati `pre` (arbitro, quote, moduli) e
  `post` (gol, xG, rating). La colonna `disponibilita_temporale_note` non
  esiste: la separazione vive in `docs/DATI.md`. Chi costruisce feature da qui
  deve applicarla a mano — è un archivio, non un dataset di training.

USO
───
    python scripts/build_actual_database2526.py
    python scripts/build_actual_database2526.py --out /tmp/prova.csv --solo serie_a
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

from src.data import sources  # noqa: E402
from src.data import tre_fonti as tf  # noqa: E402

log = logging.getLogger("actual_database2526")

USCITA_DEFAULT = RADICE / "data" / "actual_database2526.csv"
STAGIONE = "2025-26"

# ── le 25 competizioni chieste, più quelle che il repo ha in aggiunta ────────
# chiave = etichetta canonica nel file; valore = (paese, tipo, livello)
COMPETIZIONI: dict[str, tuple[str, str, str]] = {
    "Serie A": ("IT", "campionato", "1"),
    "Serie B": ("IT", "campionato", "2"),
    "Premier League": ("EN", "campionato", "1"),
    "Championship": ("EN", "campionato", "2"),
    "LaLiga": ("ES", "campionato", "1"),
    "LaLiga2": ("ES", "campionato", "2"),
    "Bundesliga": ("DE", "campionato", "1"),
    "2. Bundesliga": ("DE", "campionato", "2"),
    "Ligue 1": ("FR", "campionato", "1"),
    "Ligue 2": ("FR", "campionato", "2"),
    "Coppa Italia": ("IT", "coppa nazionale", "-"),
    "Supercoppa Italiana": ("IT", "supercoppa", "-"),
    "DFB-Pokal": ("DE", "coppa nazionale", "-"),
    "DFL-Supercup": ("DE", "supercoppa", "-"),
    "Copa del Rey": ("ES", "coppa nazionale", "-"),
    "Supercopa de España": ("ES", "supercoppa", "-"),
    "FA Cup": ("EN", "coppa nazionale", "-"),
    "EFL Cup": ("EN", "coppa nazionale", "-"),
    "EFL Trophy": ("EN", "coppa nazionale", "-"),
    "Community Shield": ("EN", "supercoppa", "-"),
    "Coupe de France": ("FR", "coppa nazionale", "-"),
    "Trophée des Champions": ("FR", "supercoppa", "-"),
    "UEFA Champions League": ("EU", "coppa UEFA", "-"),
    "UEFA Europa League": ("EU", "coppa UEFA", "-"),
    "UEFA Conference League": ("EU", "coppa UEFA", "-"),
    # in più rispetto alla lista delle 25: c'è il dato, quindi entra
    "Supercoppa UEFA": ("EU", "coppa UEFA", "-"),
}

# le 25 chieste, nell'ordine dell'immagine dell'utente
LISTA_UTENTE = [
    "Serie A", "Serie B", "Premier League", "Championship", "LaLiga", "LaLiga2",
    "Bundesliga", "2. Bundesliga", "Ligue 1", "Ligue 2", "Coppa Italia",
    "Supercoppa Italiana", "DFB-Pokal", "DFL-Supercup", "Copa del Rey",
    "Supercopa de España", "FA Cup", "EFL Cup", "EFL Trophy", "Community Shield",
    "Coupe de France", "Trophée des Champions", "UEFA Champions League",
    "UEFA Europa League", "UEFA Conference League",
]

# come le fonti chiamano ogni competizione → etichetta canonica
NOMI_COMPETIZIONE: dict[str, str] = {
    "serie a": "Serie A",
    "premier league": "Premier League",
    "laliga": "LaLiga",
    "la liga": "LaLiga",
    "laliga2": "LaLiga2",
    "laliga 2": "LaLiga2",
    "bundesliga": "Bundesliga",
    "2bundesliga": "2. Bundesliga",
    "2. bundesliga": "2. Bundesliga",
    "ligue1": "Ligue 1",
    "ligue 1": "Ligue 1",
    "coppa italia": "Coppa Italia",
    "italy cup": "Coppa Italia",
    "supercoppa italiana": "Supercoppa Italiana",
    "dfb-pokal": "DFB-Pokal",
    "dfb pokal": "DFB-Pokal",
    "dfl-supercup": "DFL-Supercup",
    "franz-beckenbauer-supercup": "DFL-Supercup",
    "copa del rey": "Copa del Rey",
    "supercopa de españa": "Supercopa de España",
    "supercopa": "Supercopa de España",
    "fa cup": "FA Cup",
    "efl cup": "EFL Cup",
    "carabao cup": "EFL Cup",
    "community shield": "Community Shield",
    "coupe de france": "Coupe de France",
    "coppa di francia": "Coupe de France",
    "trophée des champions": "Trophée des Champions",
    "trophee des champions": "Trophée des Champions",
    "uefa champions league": "UEFA Champions League",
    "champions league": "UEFA Champions League",
    "uefa europa league": "UEFA Europa League",
    "europa league": "UEFA Europa League",
    "uefa conference league": "UEFA Conference League",
    "conference league": "UEFA Conference League",
    "supercoppa uefa": "Supercoppa UEFA",
    "uefa super cup": "Supercoppa UEFA",
}

# raccolta tre-fonti → etichetta canonica (le raccolte sono per competizione)
TF_COMPETIZIONE: dict[str, str] = {
    "serie_a": "Serie A",
    "premier_league": "Premier League",
    "la_liga": "LaLiga",
    "laliga2": "LaLiga2",
    "bundesliga": "Bundesliga",
    "bundesliga2": "2. Bundesliga",
    "ligue_1": "Ligue 1",
    "community_shield": "Community Shield",
    "dfl_supercup": "DFL-Supercup",
    "supercopa_espana": "Supercopa de España",
    "supercoppa_italiana": "Supercoppa Italiana",
    "supercoppa_uefa": "Supercoppa UEFA",
    "trophee_des_champions": "Trophée des Champions",
    "uefa_champions_league": "UEFA Champions League",
    "uefa_conference_league": "UEFA Conference League",
    "uefa_europa_league": "UEFA Europa League",
}

# lega dello snapshot congelato → etichetta canonica
SNAPSHOT_COMPETIZIONE = {
    "serie_a": "Serie A",
    "premier_league": "Premier League",
    "la_liga": "LaLiga",
    "bundesliga": "Bundesliga",
    "ligue_1": "Ligue 1",
}

PERIODO_SIGLA = {
    "Totale": "tot",
    "1° tempo": "1t",
    "2° tempo": "2t",
    "1° supplementare": "sup1",
    "2° supplementare": "sup2",
    "Supplementari": "sup",
}

# colonne di `squadre()` che descrivono la PARTITA e non la squadra: sono
# identiche sulle due righe (casa e trasferta) e vanno issate a colonna singola.
# La lista è verificata a runtime da `_classifica_colonne`, che segnala se una
# colonna qui elencata risulta invece diversa fra i due lati.
CHIAVI_SQUADRE = (
    "Competizione", "Stagione", "Turno", "Data", "Ora", "Fuso",
    "Data e ora ISO (UTC)", "Timestamp", "Riga", "Livello", "Fonti",
    "Squadra", "Campo", "Avversario", "Periodo", "Discordanze",
)

# i campi per giocatore che finiscono nel JSON impacchettato. Curati: nel file
# grezzo ce ne sono ~190 per giocatore, e ~30 giocatori a partita — un JSON
# completo peserebbe più di tutto il resto della tabella messo insieme.
CAMPI_GIOCATORE: dict[str, str] = {
    "Giocatore": "nome",
    "Ruolo": "ruolo",
    "Maglia": "maglia",
    "Stato": "stato",
    "Capitano (SofaScore)": "cap",
    "Minuti giocati (SofaScore)": "min",
    "Entrato al minuto (WhoScored)": "entra",
    "Uscito al minuto (WhoScored)": "esce",
    "Gol (SofaScore)": "gol",
    "Assist (SofaScore)": "assist",
    "Autogol (SofaScore)": "autogol",
    "Tiri totali (SofaScore)": "tiri",
    "Tiri in porta (SofaScore)": "tiri_porta",
    "Gol previsti (xG) (SofaScore)": "xg",
    "Assist previsti (xA) (SofaScore)": "xa",
    "Passaggi totali (SofaScore)": "pass",
    "Passaggi riusciti (SofaScore)": "pass_ok",
    "Passaggi chiave (SofaScore)": "pass_chiave",
    "Tocchi (SofaScore)": "tocchi",
    "Dribbling riusciti (SofaScore)": "dribbling",
    "Contrasti (SofaScore)": "contrasti",
    "Palle intercettate (SofaScore)": "intercetti",
    "Duelli vinti (SofaScore)": "duelli_v",
    "Falli commessi (SofaScore)": "falli",
    "Parate (SofaScore)": "parate",
    "Gol evitati (SofaScore)": "gol_evit",
    "Km percorsi (SofaScore)": "km",
    "Rating (SofaScore)": "rating",
    "ratings (WhoScored)": "rating_ws",
    "Gialli (Understat)": "gialli",
    "Rossi (Understat)": "rossi",
    "xGChain (Understat)": "xgchain",
    "xGBuildup (Understat)": "xgbuildup",
    "ID giocatore (SofaScore)": "id_sofa",
}


# ════════════════════════════════════════════════════════════════════════════
# utilità
# ════════════════════════════════════════════════════════════════════════════
def _senza_accenti(testo: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", testo)
                   if not unicodedata.combining(c))


def norm_squadra(nome: object) -> str:
    """Chiave di confronto fra grafie diverse dello stesso club.

    Toglie accenti, punteggiatura e le sigle societarie più comuni. NON è un
    aggancio per somiglianza: serve solo a far combaciare «Bayern München» e
    «Bayern Munchen», non «Real Sociedad B» e «Real Sociedad» — che infatti
    restano due chiavi diverse (⚠️ vedi il caso `Real Sociedad B` nel README
    di `files/tre_fonti_laliga2_2526`).
    """
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return ""
    grezzo = str(nome).strip()
    # gli alias già collaudati del progetto (287 voci): «Internazionale» →
    # «Inter», «Hellas Verona» → «Verona». Sono la stessa mappa che usa il
    # loader, quindi la chiave qui e i nomi degli snapshot combaciano.
    testo = _senza_accenti(sources.canonical_team(grezzo)).lower().strip()
    testo = re.sub(r"[^a-z0-9 ]+", " ", testo)
    parole = [p for p in testo.split() if p not in {
        "fc", "cf", "ac", "as", "ss", "ssc", "sc", "afc", "cd", "ud", "sd",
        "rc", "cp", "club", "calcio", "de", "the", "1899", "1909", "1913",
    }]
    return " ".join(parole) if parole else testo.replace(" ", "")


def canon_competizione(nome: object) -> str | None:
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return None
    grezzo = str(nome).strip()
    diretto = NOMI_COMPETIZIONE.get(grezzo.lower())
    if diretto:
        return diretto
    senza = _senza_accenti(grezzo).lower()
    for chiave, valore in NOMI_COMPETIZIONE.items():
        if _senza_accenti(chiave).lower() == senza:
            return valore
    return grezzo if grezzo in COMPETIZIONI else None


def norm_data(data: object) -> str:
    """La data in ISO, da qualunque delle grafie che le fonti usano.

    ⚠️ Non è un dettaglio: `aggancio_statistiche_squadra.csv` scrive
    `15.11.2025` e `aggancio_partite.csv` `2025-11-15`. Tagliare i primi dieci
    caratteri e sperare fa fallire il join **senza errore** — 476 righe di
    Coupe de France perse in silenzio, che è esattamente il modo in cui i dati
    si rompono senza che nessuno se ne accorga.
    """
    testo = _testo(data)
    if not testo:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", testo):
        return testo[:10]
    trovato = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4}).*", testo)
    if trovato:
        giorno, mese, anno = trovato.groups()
        return f"{anno}-{int(mese):02d}-{int(giorno):02d}"
    try:
        return pd.to_datetime(testo, dayfirst=True).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return testo[:10]


def chiave_partita(competizione: object, data: object,
                   casa: object, trasferta: object) -> str:
    """La chiave con cui le fonti si agganciano fra loro."""
    return "|".join([
        _testo(competizione),
        norm_data(data),
        norm_squadra(casa),
        norm_squadra(trasferta),
    ])


def _pulisci(valore: object) -> object:
    if valore is None:
        return None
    if isinstance(valore, float):
        if np.isnan(valore):
            return None
        if valore.is_integer():
            return int(valore)
        return round(valore, 4)
    if isinstance(valore, (np.integer,)):
        return int(valore)
    if isinstance(valore, (np.floating,)):
        return _pulisci(float(valore))
    if isinstance(valore, (np.bool_, bool)):
        return bool(valore)
    if pd.isna(valore):
        return None
    return valore


def _testo(valore: object) -> str:
    """`str(x or "")` è una trappola con i NaN: `float("nan") or ""` è NaN,
    e `str(NaN)` è la stringa «nan» — che è truthy, non vuota, e ha rotto in
    silenzio la colonna del vincente delle quote (tutti e tre gli esiti 1X2
    risultavano vinti). Questa funzione è l'unica via per portare a testo un
    valore che può essere mancante."""
    if valore is None or (isinstance(valore, float) and np.isnan(valore)):
        return ""
    try:
        if pd.isna(valore):
            return ""
    except (TypeError, ValueError):
        pass
    return str(valore).strip()


def json_compatto(oggetto) -> str | None:
    if not oggetto:
        return None
    return json.dumps(oggetto, ensure_ascii=False, separators=(",", ":"))


def json_tabellare(righe: list[dict], ordine: list[str] | None = None) -> str | None:
    """Una tabellina dentro una cella: `{"campi":[...],"righe":[[...],...]}`.

    Perché non una lista di oggetti (`[{"nome":…,"gol":…}, …]`), che sarebbe
    più leggibile: perché ripeterebbe i **nomi dei campi** per ogni giocatore
    di ogni partita. Misurato sulle 4.169 righe vere: 4.849 byte a cella
    contro 3.330, cioè **12 MB in più** su una colonna sola. La forma
    tabellare resta JSON valido, resta auto-descrittiva (i nomi ci sono, una
    volta), e si rilegge in una riga:

        import json, pandas as pd
        v = json.loads(riga["tf_casa_giocatori_json"])
        pd.DataFrame(v["righe"], columns=v["campi"])

    ⚠️ Qui i valori assenti sono `null` **espliciti**, non chiavi mancanti:
    la matrice è rettangolare per costruzione. Un `null` significa «questa
    fonte non ha misurato quel campo per quel giocatore», mai «zero».
    """
    if not righe:
        return None
    if ordine is None:
        ordine = []
        for riga in righe:
            for campo in riga:
                if campo not in ordine:
                    ordine.append(campo)
    else:
        presenti = {campo for riga in righe for campo in riga}
        ordine = [campo for campo in ordine if campo in presenti]
    corpo = [[riga.get(campo) for campo in ordine] for riga in righe]
    return json.dumps({"campi": ordine, "righe": corpo},
                      ensure_ascii=False, separators=(",", ":"))


# ════════════════════════════════════════════════════════════════════════════
# 1 · TRE FONTI — la spina dorsale di 16 competizioni
# ════════════════════════════════════════════════════════════════════════════
def _classifica_colonne(squadre: pd.DataFrame) -> tuple[set[str], set[str]]:
    """Divide le colonne statistiche in «di partita» e «di squadra».

    Il criterio è MISURATO, non dedotto dal nome: una colonna il cui valore
    coincide sulla riga di casa e su quella di trasferta in ogni partita
    descrive la partita (arbitro, stadio, meteo, punteggio), e va issata a
    colonna singola; le altre descrivono la squadra e si affiancano.

    Il confronto si fa sul periodo `Totale` e tratta NaN==NaN come uguale.
    """
    tot = squadre[squadre["Periodo"] == "Totale"]
    casa = tot[tot["Campo"] == "Casa"].set_index("_chiave")
    fuori = tot[tot["Campo"] == "Trasferta"].set_index("_chiave")
    comuni = casa.index.intersection(fuori.index)
    casa, fuori = casa.loc[comuni], fuori.loc[comuni]

    di_partita: set[str] = set()
    di_squadra: set[str] = set()
    for colonna in squadre.columns:
        if colonna in CHIAVI_SQUADRE or colonna.startswith("_"):
            continue
        a = casa[colonna].astype("string").fillna("∅")
        b = fuori[colonna].astype("string").fillna("∅")
        (di_partita if len(comuni) and (a.values == b.values).mean() > 0.995
         else di_squadra).add(colonna)
    return di_partita, di_squadra


def blocco_tre_fonti(raccolta: str) -> pd.DataFrame:
    """Una riga per partita, con le statistiche di squadra affiancate."""
    squadre = tf.squadre(raccolta, spareggio=True)
    if squadre.empty:
        return pd.DataFrame()

    competizione = TF_COMPETIZIONE.get(raccolta) or canon_competizione(
        squadre["Competizione"].dropna().iloc[0])
    # ⚠️ In Europa League e Conference `Gol casa (SofaScore)` SOMMA la lotteria
    # dei rigori: «Partizan-AEK Larnaca 7-7» era 2-1. La convenzione non si
    # eredita fra raccolte e non si deduce dal torneo — si misura, e
    # `punteggio_vero` applica la misura (tf.RIGORI_NEL_PUNTEGGIO).
    if "Gol casa (SofaScore)" in squadre.columns:
        casa_reg, via_reg = tf.punteggio_vero(squadre)
        squadre["Gol casa regolamentari"] = casa_reg
        squadre["Gol trasferta regolamentari"] = via_reg
        squadre["Rigori nel punteggio grezzo"] = tf.RIGORI_NEL_PUNTEGGIO.get(
            raccolta, False)
        # I 90 minuti sono la somma delle due frazioni: e' l'identita' che
        # `gol_sono_regolamentari` verifica (Gol = 1T + 2T + suppl.), letta al
        # contrario. Serve perche' il punteggio «vero» INCLUDE i supplementari,
        # e su una coppa i due numeri sono diversi.
        for lato in ("Casa", "Trasferta"):
            primo = pd.to_numeric(squadre.get(f"{lato} 1T (SofaScore)"),
                                  errors="coerce")
            secondo = pd.to_numeric(squadre.get(f"{lato} 2T (SofaScore)"),
                                    errors="coerce")
            squadre[f"Gol {lato.lower()} 90"] = (primo + secondo).where(
                primo.notna() & secondo.notna())

    squadre["_competizione"] = competizione
    squadre["_casa"] = np.where(squadre["Campo"] == "Casa",
                                squadre["Squadra"], squadre["Avversario"])
    squadre["_trasferta"] = np.where(squadre["Campo"] == "Casa",
                                     squadre["Avversario"], squadre["Squadra"])
    squadre["_chiave"] = [
        chiave_partita(competizione, d, c, t)
        for d, c, t in zip(squadre["Data"], squadre["_casa"], squadre["_trasferta"])
    ]

    di_partita, di_squadra = _classifica_colonne(squadre)

    # -- anagrafica della partita ------------------------------------------
    tot = squadre[(squadre["Periodo"] == "Totale") & (squadre["Campo"] == "Casa")]
    anagrafica = tot[["_chiave", "_competizione", "_casa", "_trasferta",
                      "Stagione", "Turno", "Data", "Ora", "Fuso",
                      "Data e ora ISO (UTC)", "Timestamp", "Fonti"]].copy()
    anagrafica = anagrafica.rename(columns={
        "_competizione": "competizione", "_casa": "casa", "_trasferta": "trasferta",
        "Stagione": "stagione", "Turno": "turno", "Data": "data", "Ora": "ora",
        "Fuso": "fuso", "Data e ora ISO (UTC)": "data_ora_utc",
        "Timestamp": "timestamp", "Fonti": "tf_fonti",
    })
    anagrafica = anagrafica.drop_duplicates("_chiave").set_index("_chiave")

    # -- colonne di partita -------------------------------------------------
    ordinate = [c for c in squadre.columns if c in di_partita]
    livello_partita = (tot.drop_duplicates("_chiave")
                          .set_index("_chiave")[ordinate]
                          .rename(columns=lambda c: f"tf_{c}"))

    pezzi = [anagrafica, livello_partita]

    # -- colonne di squadra, per lato e per periodo -------------------------
    ordinate_squadra = [c for c in squadre.columns if c in di_squadra]
    for periodo, sigla in PERIODO_SIGLA.items():
        fetta = squadre[squadre["Periodo"] == periodo]
        if fetta.empty:
            continue
        for campo, lato in (("Casa", "casa"), ("Trasferta", "trasferta")):
            lati = fetta[fetta["Campo"] == campo].drop_duplicates("_chiave")
            if lati.empty:
                continue
            pezzo = lati.set_index("_chiave")[ordinate_squadra]
            pezzo.columns = [f"tf_{lato}_{sigla}_{c}" for c in ordinate_squadra]
            pezzi.append(pezzo)

    partite = pd.concat(pezzi, axis=1)
    partite.index.name = "_chiave"
    log.info("  tre fonti %-24s %4d partite · %4d colonne",
             raccolta, len(partite), partite.shape[1])
    return partite.reset_index()


# ── giocatori: pacchetto JSON + colonne riassuntive ─────────────────────────
def _riga_giocatore(riga: pd.Series) -> dict:
    fuori = {}
    for colonna, breve in CAMPI_GIOCATORE.items():
        if colonna not in riga.index:
            continue
        valore = _pulisci(riga[colonna])
        if valore is not None and valore != "":
            fuori[breve] = valore
    return fuori


def _riassunto_giocatori(gruppo: pd.DataFrame) -> dict:
    """Le colonne leggibili a occhio, ricavate dalle righe dei giocatori."""
    def col(nome: str) -> pd.Series:
        return (gruppo[nome] if nome in gruppo.columns
                else pd.Series(np.nan, index=gruppo.index))

    minuti = pd.to_numeric(col("Minuti giocati (SofaScore)"), errors="coerce")
    gol = pd.to_numeric(col("Gol (SofaScore)"), errors="coerce")
    assist = pd.to_numeric(col("Assist (SofaScore)"), errors="coerce")
    rating = pd.to_numeric(col("Rating (SofaScore)"), errors="coerce")
    gialli = pd.to_numeric(col("Gialli (Understat)"), errors="coerce")
    rossi = pd.to_numeric(col("Rossi (Understat)"), errors="coerce")
    km = pd.to_numeric(col("Km percorsi (SofaScore)"), errors="coerce")
    valore = pd.to_numeric(col("Valore di mercato (SofaScore)"), errors="coerce")
    altezza = pd.to_numeric(col("Altezza cm (SofaScore)"), errors="coerce")
    nomi = col("Giocatore").astype("string")
    stato = col("Stato").astype("string").fillna("")
    maglia = col("Maglia")
    ruolo = col("Ruolo").astype("string").fillna("")

    titolare = stato.str.lower().str.startswith("titolare", na=False)
    giocata = minuti.fillna(0) > 0

    def elenco(maschera: pd.Series) -> str | None:
        pezzi = []
        for nome, num, ruo in zip(nomi[maschera], maglia[maschera], ruolo[maschera]):
            numero = "" if pd.isna(num) else f"{int(num)}. "
            suffisso = f" ({ruo})" if ruo else ""
            pezzi.append(f"{numero}{nome}{suffisso}")
        return "; ".join(pezzi) if pezzi else None

    def con_conteggio(valori: pd.Series) -> str | None:
        pezzi = [f"{n} x{int(v)}" if v > 1 else str(n)
                 for n, v in zip(nomi[valori.fillna(0) > 0], valori[valori.fillna(0) > 0])]
        return "; ".join(pezzi) if pezzi else None

    autogol = pd.to_numeric(col("Autogol (SofaScore)"), errors="coerce")
    mvp = col("Migliore in campo (WhoScored)")
    migliore = nomi[mvp.astype("string").fillna("").str.lower().isin(
        {"true", "sì", "si", "1", "1.0"})]

    # ⚠️ `giocatori()` non è strettamente una riga per giocatore-partita:
    # restano righe non fuse fra le fonti (56 in Serie A, 200 in Liga), che
    # nel pacchetto compaiono come un secondo record dello stesso giocatore.
    # Il conteggio le dichiara invece di lasciarle scoprire a chi somma i gol.
    identificativi = (gruppo["ID partita (SofaScore)"]
                      if "ID partita (SofaScore)" in gruppo.columns
                      else pd.Series(np.nan, index=gruppo.index))
    return {
        "n_righe_non_fuse": int(identificativi.isna().sum()),
        "formazione": elenco(titolare),
        "panchina": elenco(~titolare),
        "n_in_distinta": int(len(gruppo)),
        "n_scesi_in_campo": int(giocata.sum()),
        "marcatori": con_conteggio(gol),
        "autogol": con_conteggio(autogol),
        "assist": con_conteggio(assist),
        "ammoniti": con_conteggio(gialli),
        "espulsi": con_conteggio(rossi),
        "rating_medio": round(float(rating[giocata].mean()), 3)
                        if giocata.any() and rating[giocata].notna().any() else None,
        "migliore_in_campo": "; ".join(migliore.dropna().tolist()) or None,
        "km_totali": round(float(km.sum()), 2) if km.notna().any() else None,
        "altezza_media_cm": round(float(altezza[giocata].mean()), 1)
                            if giocata.any() and altezza[giocata].notna().any() else None,
        "valore_schierati_eur": (int(valore[titolare].sum())
                                 if valore[titolare].notna().any() else None),
        "giocatori_json": json_tabellare(
            [_riga_giocatore(r) for _, r in gruppo.iterrows()],
            list(CAMPI_GIOCATORE.values())),
    }


def blocco_giocatori_tf(raccolta: str) -> pd.DataFrame:
    giocatori = tf.giocatori(raccolta, spareggio=True)
    if giocatori.empty:
        return pd.DataFrame()
    competizione = TF_COMPETIZIONE.get(raccolta) or canon_competizione(
        giocatori["Competizione"].dropna().iloc[0])
    casa = np.where(giocatori["Campo"] == "Casa",
                    giocatori["Squadra"], giocatori["Avversario"])
    trasferta = np.where(giocatori["Campo"] == "Casa",
                         giocatori["Avversario"], giocatori["Squadra"])
    giocatori["_chiave"] = [chiave_partita(competizione, d, c, t)
                            for d, c, t in zip(giocatori["Data"], casa, trasferta)]

    righe: dict[str, dict] = defaultdict(dict)
    for (chiave, campo), gruppo in giocatori.groupby(["_chiave", "Campo"], sort=False):
        lato = "casa" if campo == "Casa" else "trasferta"
        for nome, valore in _riassunto_giocatori(gruppo).items():
            righe[chiave][f"tf_{lato}_{nome}"] = valore

    fuori = pd.DataFrame.from_dict(righe, orient="index")
    fuori.index.name = "_chiave"
    return fuori.reset_index()


# ── eventi: cronaca compatta, tiri, momentum, quote, serie ──────────────────
def _minuto(riga: pd.Series) -> str:
    minuto = riga.get("Minuto")
    if pd.isna(minuto):
        return "?"
    recupero = riga.get("Recupero")
    base = f"{int(minuto)}"
    return f"{base}+{int(recupero)}'" if pd.notna(recupero) and recupero else f"{base}'"


def _cronaca(gruppo: pd.DataFrame) -> str | None:
    """Gol, cartellini e cambi in una riga di testo, in ordine di minuto."""
    gruppo = gruppo.sort_values(["Minuto", "Recupero"], na_position="last")
    pezzi = []
    for _, riga in gruppo.iterrows():
        tipo = _testo(riga.get("Tipo"))
        sotto = riga.get("Sottotipo")
        etichetta = tipo + (f"/{sotto}" if pd.notna(sotto) and sotto else "")
        if tipo == "Sostituzione":
            chi = f"{riga.get('Entra')} ← {riga.get('Esce')}"
        else:
            chi = riga.get("Giocatore")
            chi = "" if pd.isna(chi) else str(chi)
        assist = riga.get("Assist")
        coda = f" (assist {assist})" if pd.notna(assist) and assist else ""
        punteggio = riga.get("Punteggio")
        coda += f" [{punteggio}]" if pd.notna(punteggio) and punteggio else ""
        lato = riga.get("Campo")
        lato = "" if pd.isna(lato) else f" — {lato}"
        voce = f"{_minuto(riga)} {etichetta}"
        voce += f" {chi}" if chi else ""
        pezzi.append(voce + coda + lato)
    return " | ".join(pezzi) if pezzi else None


# I mercati la cui etichetta di esito è auto-esplicativa: diventano colonne
# piatte. Gli altri due (`Match goals`, `Asian handicap`) NO, e il motivo è nel
# dato: ⚠️ la SOGLIA non c'è. Le righe di `Match goals` sono 14 a partita, in
# coppie Over/Under, e l'unica cosa che le distingue è l'ORDINE; quella di
# `Asian handicap` è dentro l'etichetta insieme al nome della squadra
# («(-0.25) Lazio»). Inventare «Over 2.5» leggendo la terza coppia sarebbe un
# finto pieno da manuale (R6): qui restano l'ordinale e l'etichetta grezza, e
# chi vuole la soglia la deduce sapendo che la sta deducendo.
MERCATI_PIATTI = {
    "Full time": "1x2",
    "1st half": "1x2_1t",
    "Double chance": "dc",
    "Both teams to score": "gg",
    "Draw no bet": "dnb",
    "Cards in match": "cartellini",
    "Corners 2-Way": "corner",
    "First team to score": "primo_gol",
}


def _sigla_esito(esito: object, casa: object, trasferta: object) -> str:
    """Etichetta stabile: i nomi delle squadre diventano casa/trasferta."""
    testo = _testo(esito)
    if not testo:
        return "?"
    if norm_squadra(testo) and norm_squadra(testo) == norm_squadra(casa):
        return "casa"
    if norm_squadra(testo) and norm_squadra(testo) == norm_squadra(trasferta):
        return "trasferta"
    return re.sub(r"[^A-Za-z0-9]+", "", testo) or "?"


def _quote_partita(gruppo: pd.DataFrame) -> dict:
    """Le quote di una partita: colonne piatte per i mercati etichettati,
    più `tf_quote_json` che tiene TUTTO com'è, ordine compreso."""
    casa = gruppo["Casa"].iloc[0]
    trasferta = gruppo["Trasferta"].iloc[0]
    fuori: dict[str, object] = {}
    pacchetto = []
    contatore: dict[str, int] = defaultdict(int)

    for _, riga in gruppo.iterrows():
        mercato = _testo(riga.get("Sottotipo"))
        etichetta = _sigla_esito(riga.get("Esito"), casa, trasferta)
        iniziale = _pulisci(riga.get("Quota iniziale"))
        finale = _pulisci(riga.get("Quota finale"))
        vincente = bool(_testo(riga.get("Vincente")))
        contatore[mercato] += 1
        breve = MERCATI_PIATTI.get(mercato)
        # nel pacchetto finiscono SOLO i mercati senza colonne piatte
        # (`Match goals` e `Asian handicap`): per gli altri sarebbe una copia
        # della stessa riga, e le copie in un file da 4.169 righe pesano.
        if breve is None:
            pacchetto.append({k: v for k, v in {
                "mercato": mercato,
                "esito": _pulisci(riga.get("Esito")),
                "n": contatore[mercato],
                "apre": iniziale,
                "chiude": finale,
                "vinto": vincente or None,
            }.items() if v is not None})

        if breve is None:
            continue
        radice = f"tf_quota_{breve}_{etichetta}"
        if iniziale is not None:
            fuori[f"{radice}_apre"] = iniziale
        if finale is not None:
            fuori[f"{radice}_chiude"] = finale
        if vincente:
            fuori[f"tf_quota_{breve}_vincente"] = etichetta

    fuori["tf_quote_json"] = json_tabellare(
        pacchetto, ["mercato", "esito", "n", "apre", "chiude", "vinto"])
    fuori["tf_n_quote"] = int(len(gruppo))
    return fuori


def blocco_eventi_tf(raccolta: str) -> pd.DataFrame:
    eventi = tf.eventi(raccolta, spareggio=True)
    if eventi.empty:
        return pd.DataFrame()
    competizione = TF_COMPETIZIONE.get(raccolta) or canon_competizione(
        eventi["Competizione"].dropna().iloc[0])
    eventi["_chiave"] = [chiave_partita(competizione, d, c, t) for d, c, t
                         in zip(eventi["Data"], eventi["Casa"], eventi["Trasferta"])]
    categorie = set(eventi["Categoria"].dropna().unique())
    righe: dict[str, dict] = defaultdict(dict)

    # gol / cartellini / sostituzioni ─ la fonte preferita per i gol è SofaScore
    if "Evento" in categorie:
        fetta = eventi[eventi["Categoria"] == "Evento"]
        if fetta["Fonte"].nunique() > 1:
            fetta = fetta[fetta["Fonte"] == tf.preferita("gol")]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            righe[chiave]["tf_cronaca"] = _cronaca(gruppo)
            righe[chiave]["tf_n_eventi"] = int(len(gruppo))

    # tiro per tiro: entra il CONTEGGIO, non i tiri.
    # ⚠️ Non è una svista. Il tiro è grana EVENTO, non grana partita — la
    # stessa ragione per cui i 2,7 milioni di tocchi Opta restano fuori. E il
    # costo è misurato: impacchettato in JSON pesava 25 MB su un file di 55,
    # un quarto del totale per un dato che vive già, completo e con più
    # colonne, in `files/tre_fonti_*/eventi.csv.gz` (categoria «Tiro»).
    # Il conteggio per fonte dice che c'è e quanto è denso.
    if "Tiro" in categorie:
        fetta = eventi[eventi["Categoria"] == "Tiro"]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            righe[chiave]["tf_n_tiri_tracciati"] = int(len(gruppo))
            for fonte, quanti in gruppo["Fonte"].value_counts().items():
                righe[chiave][f"tf_n_tiri_{_testo(fonte).lower()}"] = int(quanti)

    # curva di pressione: ~92 punti a partita, uno per minuto
    if "Momentum" in categorie:
        fetta = eventi[eventi["Categoria"] == "Momentum"]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            gruppo = gruppo.sort_values("Minuto")
            valori = [_pulisci(v) for v in pd.to_numeric(gruppo["Valore"],
                                                         errors="coerce")]
            righe[chiave]["tf_momentum_json"] = json_compatto(valori)

    # quote: 10 mercati, apertura e chiusura ─ vedi `_quote_partita`
    if "Quota" in categorie:
        fetta = eventi[eventi["Categoria"] == "Quota"]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            righe[chiave].update(_quote_partita(gruppo))

    # strisce statistiche mostrate prima della partita ("5/7 under 2.5")
    if "Serie" in categorie:
        fetta = eventi[eventi["Categoria"] == "Serie"]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            pezzi = [f"{r.get('Tipo')}: {r.get('Valore')}"
                     for _, r in gruppo.iterrows() if pd.notna(r.get("Tipo"))]
            righe[chiave]["tf_serie"] = "; ".join(pezzi) or None

    if "Migliore in campo" in categorie:
        fetta = eventi[eventi["Categoria"] == "Migliore in campo"]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            for _, riga in gruppo.iterrows():
                lato = ("casa" if "Home" in _testo(riga.get("Tipo"))
                        else "trasferta")
                righe[chiave][f"tf_{lato}_mvp"] = riga.get("Giocatore")
                righe[chiave][f"tf_{lato}_mvp_rating"] = _pulisci(riga.get("Valore"))

    if "Cronaca" in categorie:
        fetta = eventi[eventi["Categoria"] == "Cronaca"]
        for chiave, gruppo in fetta.groupby("_chiave", sort=False):
            righe[chiave]["tf_n_righe_commento"] = int(len(gruppo))

    fuori = pd.DataFrame.from_dict(righe, orient="index")
    fuori.index.name = "_chiave"
    return fuori.reset_index()


def blocco_conteggi_tf(raccolta: str) -> pd.DataFrame:
    """Quante righe di event data Opta e di heatmap esistono per la partita.

    Non entrano nel file (2,7 milioni di righe Opta, 4,8 milioni di posizioni):
    entra il **conteggio**, che dice se per quella partita quel dato esiste e
    quanto è denso. Vale R6 al contrario: una colonna a 0 qui significa
    davvero «non c'è», non «non lo so», perché la raccolta o ha il file o no.
    """
    fuori: dict[str, dict] = defaultdict(dict)
    squadre = tf.squadre(raccolta, spareggio=True, periodo="Totale")
    if squadre.empty:
        return pd.DataFrame()
    competizione = TF_COMPETIZIONE.get(raccolta)
    casa = squadre[squadre["Campo"] == "Casa"]
    per_id_ws: dict[object, str] = {}
    per_id_sofa: dict[object, str] = {}
    for _, riga in casa.iterrows():
        chiave = chiave_partita(competizione, riga["Data"], riga["Squadra"],
                                riga["Avversario"])
        if pd.notna(riga.get("ID partita (WhoScored)")):
            per_id_ws[riga["ID partita (WhoScored)"]] = chiave
        if pd.notna(riga.get("ID partita (SofaScore)")):
            per_id_sofa[riga["ID partita (SofaScore)"]] = chiave

    try:
        opta = tf.eventi_opta(raccolta, colonne=["ID partita"], spareggio=True)
        for identificativo, quante in opta["ID partita"].value_counts().items():
            chiave = per_id_ws.get(identificativo)
            if chiave:
                fuori[chiave]["tf_n_eventi_opta"] = int(quante)
    except (FileNotFoundError, KeyError, ValueError):
        log.info("  %s: nessun event data Opta", raccolta)

    try:
        posizioni = tf.heatmap(raccolta, spareggio=True)
        colonna = ("ID partita (SofaScore)" if "ID partita (SofaScore)"
                   in posizioni.columns else "ID partita")
        for identificativo, quante in posizioni[colonna].value_counts().items():
            chiave = per_id_sofa.get(identificativo) or per_id_ws.get(identificativo)
            if chiave:
                fuori[chiave]["tf_n_posizioni_heatmap"] = int(quante)
    except (FileNotFoundError, KeyError, ValueError):
        log.info("  %s: nessuna heatmap", raccolta)

    risultato = pd.DataFrame.from_dict(fuori, orient="index")
    risultato.index.name = "_chiave"
    return risultato.reset_index()


# ════════════════════════════════════════════════════════════════════════════
# 2 · COPPE NAZIONALI — data/coppe_2526 (6 tornei, 662 partite)
# ════════════════════════════════════════════════════════════════════════════
COPPE_DIR = RADICE / "data" / "coppe_2526"

# come è stata agganciata ogni partita di coppa: resta nel file, in
# `cop_metodo_aggancio`, perché un aggancio dedotto e uno letto da un id non
# valgono uguale e chi legge deve poterli distinguere.
METODI_AGGANCIO: dict[str, str] = {}

CAMPI_GIOCATORE_COPPA = {
    "Giocatore": "nome", "Ruolo": "ruolo", "Stato": "stato", "Rating": "rating",
    "MINUTES_PLAYED": "min", "GOALS": "gol", "ASSISTS_GOAL": "assist",
    "OWN_GOALS": "autogol", "SHOTS_TOTAL": "tiri", "SHOTS_ON_TARGET": "tiri_porta",
    "EXPECTED_GOALS": "xg", "EXPECTED_ASSISTS": "xa", "PASSES_TOTAL": "pass",
    "PASSES_ACCURATE": "pass_ok", "KEY_PASSES": "pass_chiave",
    "TOUCHES": "tocchi", "DRIBBLES_SUCCESSFUL": "dribbling",
    "TACKLES_TOTAL": "contrasti", "INTERCEPTIONS": "intercetti",
    "DUELS_WON": "duelli_v", "FOULS": "falli", "SAVES": "parate",
    "GOALS_CONCEDED": "gol_concessi", "CARDS_YELLOW": "gialli",
    "CARDS_RED": "rossi", "player_id": "player_id",
}


def _etichetta_minuto(minuto: object) -> str:
    """Il minuto arriva numerico da una fonte e testuale («103\'») dall'altra."""
    testo = _testo(minuto)
    if not testo:
        return ""
    try:
        return f"{int(float(testo))}'"
    except ValueError:
        return testo if testo.endswith("'") else f"{testo}'"


def _leggi_coppe(nome: str) -> pd.DataFrame:
    percorso = COPPE_DIR / f"{nome}.csv"
    if not percorso.exists():
        log.warning("manca %s", percorso)
        return pd.DataFrame()
    return pd.read_csv(percorso, low_memory=False)


def _mappa_chiavi_coppe(partite: pd.DataFrame) -> tuple[dict, dict, dict]:
    """`game_id → chiave` e `(comp, data, casa, ospite) diretta → game_id`.

    ⚠️ Serve un doppio salto perché le due metà della raccolta chiamano i club
    in modo diverso: `partite.csv` usa i nomi Transfermarkt (`player-scores`),
    i file `aggancio_*` quelli di diretta.it. `aggancio_partite.csv` è il ponte
    che le unisce, e senza di lui un join per nome fallirebbe **in silenzio**.
    """
    per_game: dict[object, str] = {}
    for _, riga in partite.iterrows():
        if pd.notna(riga.get("game_id")):
            per_game[riga["game_id"]] = riga["_chiave"]

    ponte = _leggi_coppe("aggancio_partite")
    diretta_a_game: dict[tuple, object] = {}
    for _, riga in ponte.iterrows():
        if pd.isna(riga.get("game_id")):
            continue
        competizione = canon_competizione(riga.get("competizione"))
        diretta_a_game[(competizione, norm_data(riga.get("data")),
                        norm_squadra(riga.get("casa")),
                        norm_squadra(riga.get("ospite")))] = riga["game_id"]

    # terza via: i nomi di diretta.it che coincidono con quelli Transfermarkt.
    # Serve ai 204 turni (quasi tutti di Coupe de France) che `partite.csv`
    # prende da Wikipedia e che quindi NON hanno un `game_id` da mappare.
    per_nome = {(riga["competizione"], norm_data(riga["data"]),
                 norm_squadra(riga["casa"]), norm_squadra(riga["ospite"])):
                riga["_chiave"] for _, riga in partite.iterrows()}
    per_giorno: dict[tuple, list[tuple[str, str, str]]] = defaultdict(list)
    for _, riga in partite.iterrows():
        per_giorno[(riga["competizione"], norm_data(riga["data"]))].append(
            (norm_squadra(riga["casa"]), norm_squadra(riga["ospite"]),
             riga["_chiave"]))
    return per_game, diretta_a_game, per_nome, per_giorno


def _compatibili(uno: str, altro: str) -> bool:
    """Due grafie dello stesso club, quando una è l'abbreviazione dell'altra.

    «AC Seyssinet» (Wikipedia) e «Seyssinet» (diretta.it) sono lo stesso club;
    «Espoir» e «Eveil» no. Il criterio è l'inclusione fra insiemi di parole,
    non la somiglianza fra stringhe — e da solo NON basta: chi lo usa deve
    pretendere che il candidato sia **unico** su quella data (vedi
    `_chiave_da_aggancio`). Un aggancio univoco e sbagliato è il difetto che
    nessun conteggio vede (R6).
    """
    if not uno or not altro:
        return False
    if uno == altro:
        return True
    parole_uno, parole_altro = set(uno.split()), set(altro.split())
    return parole_uno <= parole_altro or parole_altro <= parole_uno


def _chiave_da_aggancio(riga: pd.Series, per_game: dict, diretta_a_game: dict,
                        per_nome: dict, per_giorno: dict | None = None) -> str | None:
    """Quattro vie, in ordine di sicurezza decrescente: l'id, il ponte, il
    nome esatto, e — solo se resta una candidata sola in quel giorno —
    l'abbreviazione. L'ultima serve ai turni bassi di Coupe de France, dove la
    spina viene da Wikipedia («AC Seyssinet») e le statistiche da diretta.it
    («Seyssinet»)."""
    if pd.notna(riga.get("game_id")) and riga["game_id"] in per_game:
        chiave = per_game[riga["game_id"]]
        METODI_AGGANCIO.setdefault(chiave, "game_id")
        return chiave
    competizione = canon_competizione(riga.get("competizione")
                                      or riga.get("Competizione"))
    data = norm_data(riga.get("data") if pd.notna(riga.get("data"))
                     else riga.get("Data"))
    casa = riga.get("casa", riga.get("Casa"))
    ospite = riga.get("ospite", riga.get("Ospite"))
    coordinate = (competizione, data, norm_squadra(casa), norm_squadra(ospite))
    identificativo = diretta_a_game.get(coordinate)
    if identificativo is not None and identificativo in per_game:
        chiave = per_game[identificativo]
        METODI_AGGANCIO.setdefault(chiave, "ponte aggancio_partite")
        return chiave
    esatto = per_nome.get(coordinate)
    if esatto is not None:
        METODI_AGGANCIO.setdefault(esatto, "nome esatto")
        return esatto
    if per_giorno is None:
        return None
    candidate = [chiave for casa_s, ospite_s, chiave
                 in per_giorno.get((competizione, data), [])
                 if _compatibili(coordinate[2], casa_s)
                 and _compatibili(coordinate[3], ospite_s)]
    if len(candidate) != 1:
        return None
    METODI_AGGANCIO.setdefault(candidate[0], "abbreviazione univoca nel giorno")
    return candidate[0]


def blocco_coppe() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Spina dorsale delle coppe nazionali + tutto ciò che vi si aggancia."""
    partite = _leggi_coppe("partite")
    if partite.empty:
        return pd.DataFrame(), pd.DataFrame()

    partite["competizione"] = partite["competizione"].map(canon_competizione)
    partite["_chiave"] = [
        chiave_partita(c, d, x, y) for c, d, x, y in
        zip(partite["competizione"], partite["data"],
            partite["casa"], partite["ospite"])
    ]
    doppi = partite["_chiave"].duplicated().sum()
    if doppi:
        log.warning("coppe: %d chiavi duplicate (andata/ritorno stesso giorno?)", doppi)

    spina = partite.rename(columns={
        "data": "data", "casa": "casa", "ospite": "trasferta", "turno": "turno",
        "paese": "cop_paese",
    })
    spina["stagione"] = STAGIONE
    rinomina = {c: f"cop_{c}" for c in spina.columns
                if c not in {"_chiave", "competizione", "casa", "trasferta",
                             "data", "turno", "stagione", "cop_paese"}}
    spina = spina.rename(columns=rinomina)

    per_game, diretta_a_game, per_nome, per_giorno = _mappa_chiavi_coppe(partite)
    accumulo: dict[str, dict] = defaultdict(dict)

    # -- statistiche di squadra, per periodo -------------------------------
    stat = _leggi_coppe("aggancio_statistiche_squadra")
    if not stat.empty:
        stat["_chiave"] = [_chiave_da_aggancio(r, per_game, diretta_a_game, per_nome, per_giorno)
                           for _, r in stat.iterrows()]
        metriche = [c for c in stat.columns if c not in {
            "Competizione", "Turno", "Data", "Casa", "Ospite", "Periodo",
            "Lato", "Squadra", "ID partita", "competizione", "game_id",
            "club_id", "_chiave"}]
        for (chiave, periodo, lato), gruppo in stat.groupby(
                ["_chiave", "Periodo", "Lato"], sort=False):
            if not chiave:
                continue
            sigla = PERIODO_SIGLA.get(periodo, _testo(periodo) or "?")
            nome_lato = "casa" if lato == "Casa" else "trasferta"
            riga = gruppo.iloc[0]
            for metrica in metriche:
                valore = _pulisci(riga[metrica])
                if valore is not None:
                    accumulo[chiave][f"cop_{nome_lato}_{sigla}_{metrica}"] = valore

    # -- statistiche dei giocatori ------------------------------------------
    giocatori = _leggi_coppe("aggancio_statistiche")
    if not giocatori.empty:
        giocatori = giocatori.copy()
        giocatori["_chiave"] = [_chiave_da_aggancio(r, per_game, diretta_a_game, per_nome, per_giorno)
                                for _, r in giocatori.iterrows()]
        for (chiave, lato), gruppo in giocatori.groupby(["_chiave", "Lato"],
                                                        sort=False):
            if not chiave:
                continue
            nome_lato = "casa" if lato == "Casa" else "trasferta"
            pacchetto = []
            for _, riga in gruppo.iterrows():
                voce = {}
                for colonna, breve in CAMPI_GIOCATORE_COPPA.items():
                    if colonna in riga.index:
                        valore = _pulisci(riga[colonna])
                        if valore is not None and valore != "":
                            voce[breve] = valore
                pacchetto.append(voce)
            accumulo[chiave][f"cop_{nome_lato}_giocatori_json"] = json_tabellare(
                pacchetto, list(CAMPI_GIOCATORE_COPPA.values()))
            accumulo[chiave][f"cop_{nome_lato}_n_giocatori"] = int(len(gruppo))

    # -- formazioni (player-scores: minuti, gol, assist, cartellini) --------
    formazioni = _leggi_coppe("formazioni")
    if not formazioni.empty:
        formazioni["_chiave"] = formazioni["game_id"].map(per_game)
        for (chiave, club), gruppo in formazioni.groupby(["_chiave", "club_id"],
                                                          sort=False):
            if not isinstance(chiave, str):
                continue
            riga_partita = partite[partite["_chiave"] == chiave]
            if riga_partita.empty:
                continue
            lato = ("casa" if riga_partita.iloc[0].get("home_club_id") == club
                    else "trasferta")
            # ⚠️ `ruolo_partita` vale «titolare»/«panchina», in italiano.
            # Cercarci dentro «start» — come farebbe chi arriva da una fonte
            # inglese — non solleva un errore: restituisce zero titolari e una
            # colonna vuota su 458 partite. È il difetto che questo file ha
            # avuto per una versione, e si è visto solo da una copertura
            # assurda (formazioni piene all'84% invece che al 95%).
            titolare = (gruppo["ruolo_partita"].astype("string").str.lower()
                              .str.contains("titolar", na=False))
            titolari = gruppo[titolare]
            elenco = "; ".join(
                f"{'' if pd.isna(n) else str(n).strip() + '. '}{g}"
                for n, g in zip(titolari["numero"], titolari["giocatore"]))
            accumulo[chiave][f"cop_{lato}_formazione_ps"] = elenco or None
            accumulo[chiave][f"cop_{lato}_n_in_distinta_ps"] = int(len(gruppo))
            accumulo[chiave][f"cop_{lato}_n_titolari_ps"] = int(titolare.sum())
            for campo, colonna in (("gol", "gol"), ("assist", "assist"),
                                   ("gialli", "gialli"), ("rossi", "rossi")):
                valori = pd.to_numeric(gruppo[colonna], errors="coerce").fillna(0)
                nomi = gruppo["giocatore"][valori > 0]
                accumulo[chiave][f"cop_{lato}_{campo}_ps"] = "; ".join(nomi) or None
            # la distinta per esteso: è la fonte PIÙ COMPLETA che le coppe
            # abbiano sui giocatori (458 partite contro le ~300 con le
            # statistiche di diretta.it), e porta minuti, gol, assist,
            # cartellini, capitano, posizione e `player_id`.
            campi = ["giocatore", "player_id", "numero", "ruolo_partita",
                     "posizione", "capitano", "minuti", "gol", "assist",
                     "gialli", "rossi"]
            accumulo[chiave][f"cop_{lato}_formazione_json"] = json_tabellare(
                [{c: _pulisci(r[c]) for c in campi if c in r.index}
                 for _, r in gruppo.iterrows()], campi)

    # -- eventi col minuto ---------------------------------------------------
    for nome, prefisso in (("aggancio_eventi", "diretta"), ("eventi", "ps")):
        eventi = _leggi_coppe(nome)
        if eventi.empty:
            continue
        if nome == "eventi":
            eventi["_chiave"] = eventi["game_id"].map(per_game)
        else:
            eventi["_chiave"] = [_chiave_da_aggancio(r, per_game, diretta_a_game, per_nome, per_giorno)
                                 for _, r in eventi.iterrows()]
        for chiave, gruppo in eventi.groupby("_chiave", sort=False):
            if not isinstance(chiave, str):
                continue
            gruppo = gruppo.sort_values("minuto" if "minuto" in gruppo.columns
                                        else "Minuto")
            pezzi = []
            for _, riga in gruppo.iterrows():
                minuto = riga.get("minuto", riga.get("Minuto"))
                tipo = _testo(riga.get("tipo") or riga.get("Tipo evento"))
                chi = _testo(riga.get("giocatore") or riga.get("Giocatore")
                             or riga.get("descrizione"))
                lato = _testo(riga.get("Lato") or riga.get("club"))
                punteggio = _testo(riga.get("Punteggio dopo"))
                voce = f"{_etichetta_minuto(minuto)} {tipo} {chi}"
                if punteggio:
                    voce += f" [{punteggio}]"
                if lato:
                    voce += f" — {lato}"
                pezzi.append(voce.strip())
            accumulo[chiave][f"cop_cronaca_{prefisso}"] = " | ".join(pezzi) or None

    # -- quali blocchi esistono davvero per quella partita -------------------
    incrocio = _leggi_coppe("incrocio_per_partita")
    if not incrocio.empty:
        incrocio["_chiave"] = incrocio["game_id"].map(per_game)
        colonne = [c for c in incrocio.columns if c.startswith("b_")] + ["incrociabile"]
        for _, riga in incrocio.iterrows():
            if not isinstance(riga["_chiave"], str):
                continue
            for colonna in colonne:
                accumulo[riga["_chiave"]][f"cop_{colonna}"] = _pulisci(riga[colonna])

    for chiave, metodo in METODI_AGGANCIO.items():
        accumulo[chiave]["cop_metodo_aggancio"] = metodo

    extra = pd.DataFrame.from_dict(accumulo, orient="index")
    extra.index.name = "_chiave"
    conteggio = pd.Series(METODI_AGGANCIO).value_counts().to_dict()
    log.info("  coppe nazionali          %4d partite · %4d colonne di corredo · "
             "agganci %s", len(spina), extra.shape[1], conteggio)
    return spina, extra.reset_index()


# ════════════════════════════════════════════════════════════════════════════
# 3 · DIRETTA.IT — statistiche di squadra e di giocatore dei 5 campionati
# ════════════════════════════════════════════════════════════════════════════
DIRETTA_LEGHE = {
    "serie_a": "Serie A", "premier_league": "Premier League",
    "la_liga": "LaLiga", "bundesliga": "Bundesliga", "ligue_1": "Ligue 1",
}


def blocco_diretta(lega: str) -> pd.DataFrame:
    """Le 45 statistiche di diretta.it, affiancate per lato e per periodo.

    ⚠️ Non sono un doppione di SofaScore anche dove le grandezze si chiamano
    uguale: sono un'altra misura della stessa partita, ed è il motivo per cui
    restano in colonne proprie (`dir_*`) invece di essere fuse. Il progetto
    tratta xG allo stesso modo — due fonti, due colonne (`tre_fonti.preferita`).
    """
    from src.data import player_stats as ps, team_stats as ts

    competizione = DIRETTA_LEGHE[lega]
    accumulo: dict[str, dict] = defaultdict(dict)

    squadre = ts.load_team_matches(lega=lega)
    if squadre.empty:
        return pd.DataFrame()
    metriche = [c for c in squadre.columns if c not in {
        "Giornata", "Data", "Squadra", "Campo", "Avversario", "Periodo",
        "Fase", "data", "lega", "stagione", "Risultato squadra", "Esito"}]
    for _, riga in squadre.iterrows():
        casa = riga["Squadra"] if riga["Campo"] == "Casa" else riga["Avversario"]
        via = riga["Avversario"] if riga["Campo"] == "Casa" else riga["Squadra"]
        chiave = chiave_partita(competizione, riga["Data"], casa, via)
        lato = "casa" if riga["Campo"] == "Casa" else "trasferta"
        sigla = PERIODO_SIGLA.get(riga["Periodo"], _testo(riga["Periodo"]))
        accumulo[chiave][f"dir_{lato}_giornata"] = _pulisci(riga.get("Giornata"))
        accumulo[chiave][f"dir_{lato}_fase"] = _pulisci(riga.get("Fase"))
        accumulo[chiave][f"dir_{lato}_risultato"] = _pulisci(riga.get("Risultato squadra"))
        accumulo[chiave][f"dir_{lato}_esito"] = _pulisci(riga.get("Esito"))
        for metrica in metriche:
            valore = _pulisci(riga[metrica])
            if valore is not None:
                accumulo[chiave][f"dir_{lato}_{sigla}_{metrica}"] = valore

    # -- giocatori: riassunto (il pacchetto completo è già quello di tre fonti)
    giocatori = ps.load_player_matches(lega=lega)
    if not giocatori.empty:
        for (data, squadra, campo), gruppo in giocatori.groupby(
                ["Data", "Squadra", "Campo"], sort=False):
            avversario = gruppo["Avversario"].iloc[0]
            casa = squadra if campo == "Casa" else avversario
            via = avversario if campo == "Casa" else squadra
            chiave = chiave_partita(competizione, data, casa, via)
            lato = "casa" if campo == "Casa" else "trasferta"
            minuti = pd.to_numeric(gruppo.get("Minuti giocati"), errors="coerce")
            rating = pd.to_numeric(gruppo.get("Rating"), errors="coerce")
            accumulo[chiave][f"dir_{lato}_n_giocatori"] = int(len(gruppo))
            accumulo[chiave][f"dir_{lato}_minuti_totali"] = _pulisci(minuti.sum())
            if rating.notna().any():
                accumulo[chiave][f"dir_{lato}_rating_medio"] = round(
                    float(rating[minuti.fillna(0) > 0].mean()), 3)
            for etichetta, colonna in (("marcatori", "Gol"), ("assist", "Assist"),
                                       ("ammoniti", "Cartellini gialli"),
                                       ("espulsi", "Cartellini rossi")):
                if colonna not in gruppo.columns:
                    continue
                valori = pd.to_numeric(gruppo[colonna], errors="coerce").fillna(0)
                nomi = gruppo["Giocatore"][valori > 0]
                accumulo[chiave][f"dir_{lato}_{etichetta}"] = "; ".join(nomi) or None

    # -- formazioni, cambi ed eventi: solo Bundesliga e Ligue 1 li hanno ------
    for cosa, funzione in (("formazione", "load_lineups"),
                           ("cambi", "load_substitutions"),
                           ("cronaca", "load_events")):
        try:
            frame = getattr(ps, funzione)(lega=lega)
        except (FileNotFoundError, KeyError, ValueError):
            continue
        if frame.empty:
            continue
        for (data, squadra, campo), gruppo in frame.groupby(
                ["Data", "Squadra", "Campo"], sort=False):
            avversario = None
            fetta = squadre[(squadre["Data"] == data) & (squadre["Squadra"] == squadra)]
            if not fetta.empty:
                avversario = fetta["Avversario"].iloc[0]
            if avversario is None:
                continue
            casa = squadra if campo == "Casa" else avversario
            via = avversario if campo == "Casa" else squadra
            chiave = chiave_partita(competizione, data, casa, via)
            lato = "casa" if campo == "Casa" else "trasferta"
            if cosa == "formazione":
                titolari = gruppo[gruppo["Stato"].astype("string").str.lower()
                                        .str.contains("titolare", na=False)]
                accumulo[chiave][f"dir_{lato}_modulo"] = _pulisci(
                    gruppo["Modulo squadra"].dropna().iloc[0]
                    if gruppo["Modulo squadra"].notna().any() else None)
                accumulo[chiave][f"dir_{lato}_formazione"] = "; ".join(
                    f"{'' if pd.isna(n) else str(int(n)) + '. '}{g}"
                    for n, g in zip(titolari["Numero maglia"],
                                    titolari["Giocatore"])) or None
            elif cosa == "cambi":
                accumulo[chiave][f"dir_{lato}_cambi"] = "; ".join(
                    f"{_etichetta_minuto(m)} {e} ← {u}"
                    for m, e, u in zip(gruppo["Minuto"], gruppo["Entra"],
                                       gruppo["Esce"])) or None
            else:
                accumulo[chiave][f"dir_{lato}_cronaca"] = "; ".join(
                    f"{_etichetta_minuto(r['Minuto'])} {_testo(r['Evento'])} "
                    f"{_testo(r['Giocatore'])}".strip()
                    for _, r in gruppo.iterrows()) or None

    fuori = pd.DataFrame.from_dict(accumulo, orient="index")
    fuori.index.name = "_chiave"
    log.info("  diretta.it %-22s %4d partite · %4d colonne",
             lega, len(fuori), fuori.shape[1])
    return fuori.reset_index()


# ════════════════════════════════════════════════════════════════════════════
# 4 · SNAPSHOT CONGELATI — quote football-data, xG/PPDA Understat, riposo
# ════════════════════════════════════════════════════════════════════════════
def blocco_snapshot() -> pd.DataFrame:
    """Le colonne su cui gira tutto il resto del progetto, per le 5 leghe.

    Sono l'unica fonte di **quote di apertura e chiusura di football-data**,
    di `*_rest_days_full` (riposo vero da calendario di club) e delle stime
    dichiarate sugli assenti. Il filtro sulla stagione usa il codice `2526`,
    che è come lo snapshot la scrive.
    """
    pezzi = []
    for lega, competizione in SNAPSHOT_COMPETIZIONE.items():
        percorso = RADICE / "data" / f"{lega}_matches.csv"
        if not percorso.exists():
            log.warning("manca lo snapshot %s", percorso)
            continue
        frame = pd.read_csv(percorso)
        frame = frame[frame["season"] == 2526].copy()
        if frame.empty:
            continue
        frame["_chiave"] = [chiave_partita(competizione, d, c, t) for d, c, t
                            in zip(frame["date"], frame["home_team"],
                                   frame["away_team"])]
        frame = frame.drop(columns=["season", "league", "home_team", "away_team"])
        frame = frame.rename(columns={c: f"snap_{c}" for c in frame.columns
                                      if c != "_chiave"})
        pezzi.append(frame)
        log.info("  snapshot   %-22s %4d partite", lega, len(frame))
    if not pezzi:
        return pd.DataFrame()
    return pd.concat(pezzi, ignore_index=True)


# ════════════════════════════════════════════════════════════════════════════
# 5 · COPPE EUROPEE — raccolta SofaScore dedicata (912 partite)
# ════════════════════════════════════════════════════════════════════════════
SOF_DIR = RADICE / "files" / "sofascore_coppe_europee_2526"
SOF_XLSX = SOF_DIR / "originale_sofascore.xlsx"

def _chiave_sof(riga: pd.Series) -> str:
    return chiave_partita(canon_competizione(riga["Competizione"]),
                          riga["Data"], riga["Casa"],
                          riga.get("Trasferta", riga.get("Avversario")))


def blocco_coppe_europee() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Champions, Europa e Conference dal 1° preliminare alla finale.

    ⚠️ Il foglio `Partite` dell'`.xlsx` è il pezzo più ricco della consegna e
    **non ha un CSV**: arbitro con lo storico di carriera, stadio con capienza
    e coordinate, superficie, moduli, allenatori. Leggerlo dall'`.xlsx` non è
    un vezzo, è l'unico modo di averlo.
    """
    if not SOF_XLSX.exists():
        log.warning("manca %s", SOF_XLSX)
        return pd.DataFrame(), pd.DataFrame()

    fogli = pd.ExcelFile(SOF_XLSX)
    partite = fogli.parse("Partite")
    partite["competizione"] = partite["Competizione"].map(canon_competizione)
    partite["_chiave"] = [
        chiave_partita(c, d, x, y) for c, d, x, y in
        zip(partite["competizione"], partite["Data"], partite["Casa"],
            partite["Trasferta"])]

    spina = pd.DataFrame({
        "_chiave": partite["_chiave"],
        "competizione": partite["competizione"],
        "stagione": STAGIONE,
        "turno": partite["Turno"],
        "data": partite["Data"].map(norm_data),
        "ora": partite["Ora"],
        "casa": partite["Casa"],
        "trasferta": partite["Trasferta"],
    })
    corredo = partite.drop(columns=["Competizione", "competizione", "Turno",
                                    "Data", "Ora", "Casa", "Trasferta"])
    corredo = corredo.rename(columns={c: f"sof_{c}" for c in corredo.columns
                                      if c != "_chiave"})
    accumulo: dict[str, dict] = defaultdict(dict)

    # -- statistiche di squadra: il file è LUNGO (Voce/Valore casa/trasferta)
    stat = pd.read_csv(SOF_DIR / "statistiche_squadra.csv.gz", low_memory=False)
    stat["_chiave"] = [_chiave_sof(r) for _, r in stat.iterrows()]
    for _, riga in stat.iterrows():
        sigla = PERIODO_SIGLA.get(riga["Periodo"], _testo(riga["Periodo"]))
        voce = _testo(riga["Voce"])
        for colonna, lato in (("Valore casa", "casa"),
                              ("Valore trasferta", "trasferta")):
            valore = _pulisci(riga[colonna])
            if valore is not None:
                accumulo[riga["_chiave"]][f"sof_{lato}_{sigla}_{voce}"] = valore

    # -- giocatori: solo il CONTEGGIO ---------------------------------------
    # ⚠️ Misurato, non supposto: le 912 partite di questa raccolta sono tutte
    # dentro le 961 delle raccolte tre-fonti UEFA (0 partite con giocatori qui
    # e non li'), stessa fonte SofaScore, stesso numero di giocatori a partita,
    # e l'unico campo in piu' e' la nazionalita' — un dato `statico` del
    # giocatore, non della partita. Impacchettarli due volte costava 10 MB per
    # zero informazione: qui resta il conteggio, il pacchetto e'
    # `tf_{lato}_giocatori_json`.
    giocatori = pd.read_csv(SOF_DIR / "giocatori.csv.gz", low_memory=False)
    giocatori["_chiave"] = [
        chiave_partita(canon_competizione(r["Competizione"]), r["Data"],
                       r["Squadra"] if r["Campo"] == "Casa" else r["Avversario"],
                       r["Avversario"] if r["Campo"] == "Casa" else r["Squadra"])
        for _, r in giocatori.iterrows()]
    for (chiave, campo), gruppo in giocatori.groupby(["_chiave", "Campo"],
                                                     sort=False):
        lato = "casa" if campo == "Casa" else "trasferta"
        accumulo[chiave][f"sof_{lato}_n_giocatori"] = int(len(gruppo))

    # -- eventi, cambi, tiri, momentum, posizioni medie, colori --------------
    eventi = pd.read_csv(SOF_DIR / "eventi.csv.gz", low_memory=False)
    eventi["_chiave"] = [
        chiave_partita(canon_competizione(r["Competizione"]), r["Data"],
                       r["Squadra"] if r["Campo"] == "Casa" else None,
                       None if r["Campo"] == "Casa" else r["Squadra"])
        for _, r in eventi.iterrows()]
    # ⚠️ eventi non porta l'avversario: si ri-aggancia per ID partita, che c'è
    per_id = dict(zip(partite["ID partita"], partite["_chiave"]))
    eventi["_chiave"] = eventi["ID partita"].map(per_id)
    for chiave, gruppo in eventi.groupby("_chiave", sort=False):
        gruppo = gruppo.sort_values(["Minuto", "Recupero"], na_position="last")
        pezzi = []
        for _, riga in gruppo.iterrows():
            chi = _testo(riga.get("Giocatore")) or (
                f"{_testo(riga.get('Entra'))} ← {_testo(riga.get('Esce'))}")
            tipo = _testo(riga.get("Tipo"))
            sotto = _testo(riga.get("Sottotipo"))
            punteggio = _testo(riga.get("Punteggio"))
            voce = f"{_etichetta_minuto(riga.get('Minuto'))} {tipo}"
            voce += f"/{sotto}" if sotto else ""
            voce += f" {chi}" if chi else ""
            voce += f" [{punteggio}]" if punteggio else ""
            voce += f" — {_testo(riga.get('Campo'))}"
            pezzi.append(voce)
        accumulo[chiave]["sof_cronaca"] = " | ".join(pezzi) or None

    cambi = pd.read_csv(SOF_DIR / "cambi.csv.gz", low_memory=False)
    cambi["_chiave"] = cambi["ID partita"].map(per_id)
    for (chiave, campo), gruppo in cambi.groupby(["_chiave", "Campo"], sort=False):
        lato = "casa" if campo == "Casa" else "trasferta"
        accumulo[chiave][f"sof_{lato}_cambi"] = "; ".join(
            f"{_etichetta_minuto(m)} {_testo(e)} ← {_testo(u)}"
            for m, e, u in zip(gruppo["Minuto"], gruppo["Entra"],
                               gruppo["Esce"])) or None

    # i tiri, come sopra: conteggio. Stesso doppione misurato (0 partite con
    # tiri qui e non nelle raccolte tre-fonti), stessa grana-evento.
    tiri = pd.read_csv(SOF_DIR / "tiri.csv.gz", low_memory=False)
    tiri["_chiave"] = tiri["ID partita"].map(per_id)
    for chiave, gruppo in tiri.groupby("_chiave", sort=False):
        accumulo[chiave]["sof_n_tiri_tracciati"] = int(len(gruppo))

    momentum = pd.read_csv(SOF_DIR / "momentum.csv.gz", low_memory=False)
    momentum["_chiave"] = momentum["ID partita"].map(per_id)
    for chiave, gruppo in momentum.groupby("_chiave", sort=False):
        valori = [_pulisci(v) for v in pd.to_numeric(
            gruppo.sort_values("Minuto")["Momentum"], errors="coerce")]
        accumulo[chiave]["sof_momentum_json"] = json_compatto(valori)

    for foglio, etichetta in (("Posizioni medie", "posizioni_medie"),
                              ("Colori maglie", "colori")):
        if foglio not in fogli.sheet_names:
            continue
        frame = fogli.parse(foglio)
        colonna_id = next((c for c in frame.columns if "ID partita" in c), None)
        if colonna_id is None:
            continue
        frame["_chiave"] = frame[colonna_id].map(per_id)
        for chiave, gruppo in frame.groupby("_chiave", sort=False):
            pacchetto = [{k: _pulisci(v) for k, v in riga.items()
                          if k not in {"_chiave", colonna_id}
                          and _pulisci(v) is not None}
                         for _, riga in gruppo.iterrows()]
            accumulo[chiave][f"sof_{etichetta}_json"] = json_tabellare(pacchetto)

    extra = pd.DataFrame.from_dict(accumulo, orient="index")
    extra.index.name = "_chiave"
    extra = extra.reset_index().merge(corredo, on="_chiave", how="outer")
    log.info("  coppe europee (SofaScore) %4d partite · %4d colonne",
             len(spina), extra.shape[1])
    return spina, extra


# ════════════════════════════════════════════════════════════════════════════
# 6 · PLAYER-SCORES — arbitro, allenatori, spettatori, moduli (Transfermarkt)
# ════════════════════════════════════════════════════════════════════════════
# competition_id di player-scores → etichetta canonica. Le qualificazioni
# confluiscono nel tabellone principale: `CLQ` è Champions come `CL`.
PS_COMPETIZIONE = {
    "IT1": "Serie A", "GB1": "Premier League", "ES1": "LaLiga",
    "L1": "Bundesliga", "FR1": "Ligue 1",
    "CIT": "Coppa Italia", "FAC": "FA Cup", "CDR": "Copa del Rey",
    "DFB": "DFB-Pokal",
    "SCI": "Supercoppa Italiana", "SUC": "Supercopa de España",
    "GBCS": "Community Shield", "DFL": "DFL-Supercup",
    "FRCH": "Trophée des Champions", "USC": "Supercoppa UEFA",
    "CL": "UEFA Champions League", "CLQ": "UEFA Champions League",
    "EL": "UEFA Europa League", "ELQ": "UEFA Europa League",
    "UCOL": "UEFA Conference League", "ECLQ": "UEFA Conference League",
}


def blocco_player_scores() -> pd.DataFrame:
    """L'arbitro e i due allenatori, per le competizioni che Transfermarkt copre.

    È la fonte di riserva — e per le coppe nazionali spesso l'unica — di
    arbitro, allenatori, spettatori, modulo e stadio. ⚠️ `manager_name` è
    **chi sedeva in panchina quella partita**, non chi era in carica: 836
    mandati su 13.810 sono un vice per una gara sola (vedi
    `src/data/allenatori.py`). Qui serve proprio quello — chi c'era.
    """
    from src.data import allenatori as al

    partite = al.load_partite()
    partite = partite[partite["casa"] & (partite["season"] == 2025)].copy()
    partite["competizione"] = partite["competition_id"].map(PS_COMPETIZIONE)
    partite = partite[partite["competizione"].notna()]
    if partite.empty:
        return pd.DataFrame()

    partite["_chiave"] = [
        chiave_partita(c, d, x, y) for c, d, x, y in
        zip(partite["competizione"], partite["date"],
            partite["club_name"], partite["avversario_name"])]
    fuori = pd.DataFrame({
        "_chiave": partite["_chiave"],
        "ps_game_id": partite["game_id"],
        "ps_competition_id": partite["competition_id"],
        "ps_round": partite["round"],
        "ps_arbitro": partite["arbitro"],
        "ps_allenatore_casa": partite["allenatore"],
        "ps_allenatore_trasferta": partite["allenatore_avv"],
        "ps_modulo_casa": partite["formazione"],
        "ps_modulo_trasferta": partite["formazione_avv"],
        "ps_stadio": partite["stadio"],
        "ps_spettatori": partite["spettatori"],
        "ps_gol_casa": partite["gol_fatti"],
        "ps_gol_trasferta": partite["gol_subiti"],
        "ps_posizione_casa": partite["posizione"],
        "ps_posizione_trasferta": partite["posizione_avv"],
        "ps_club_id_casa": partite["club_id"],
        "ps_club_id_trasferta": partite["avversario_id"],
    }).drop_duplicates("_chiave")
    log.info("  player-scores            %4d partite", len(fuori))
    return fuori


# ════════════════════════════════════════════════════════════════════════════
# 7 · COEFFICIENTI UEFA DI CLUB
# ════════════════════════════════════════════════════════════════════════════
def blocco_uefa() -> pd.DataFrame:
    """Coefficiente UEFA e paese dei due club, uno per nome normalizzato.

    ⚠️ Il coefficiente di club è `MAX(somma di 5 stagioni; 20% della
    federazione)` e il pavimento MORDE su 146 club su 410: per quelli il numero
    misura il PAESE, non la squadra (vedi `src/data/ranking_uefa.py`). La
    colonna `*_uefa_pavimento` dice quando è successo, invece di lasciarlo
    dedurre.
    """
    from src.data import ranking_uefa as ru

    try:
        club = ru.club()
    except (FileNotFoundError, ValueError) as errore:
        log.warning("coefficienti UEFA non leggibili: %s", errore)
        return pd.DataFrame()

    club = club.copy()
    club["_norm"] = club["Club"].map(norm_squadra)
    somma = pd.to_numeric(club.get("Somma stagioni"), errors="coerce")
    coefficiente = pd.to_numeric(club.get("Coefficiente UEFA"), errors="coerce")
    club["_pavimento"] = (coefficiente > somma + 1e-9)
    return club.drop_duplicates("_norm").set_index("_norm")[
        ["Paese", "Coefficiente UEFA", "Somma stagioni", "25/26", "_pavimento",
         "Pos"]]


# ════════════════════════════════════════════════════════════════════════════
# 8 · MONTAGGIO — la spina dorsale, gli innesti, le colonne normalizzate
# ════════════════════════════════════════════════════════════════════════════
# Per ogni campo normalizzato, le colonne che possono fornirlo, IN ORDINE DI
# PREFERENZA. La fonte che ha vinto finisce in `provenienza_json`: un valore
# senza la sua provenienza, in una tabella che ne fonde sette, non è un dato —
# è un numero.
COALESCENZE: dict[str, tuple[str, ...]] = {
    # DUE punteggi, non uno. `gol_casa` sono i 90 MINUTI — l'unico
    # confrontabile fra un campionato e una coppa, e quello su cui si regolano
    # i mercati 1X2. `gol_casa_finale` include i supplementari. Nessuno dei due
    # include mai la lotteria dei rigori, che sta in `rigori_casa`: in Europa
    # League e Conference l'export la somma dentro `Gol casa`, e
    # `tf.punteggio_vero` la toglie (Partizan-AEK Larnaca «7-7» era 2-1).
    "gol_casa": ("tf_Gol casa 90", "cop_gol_casa_90", "snap_home_goals"),
    "gol_trasferta": ("tf_Gol trasferta 90", "cop_gol_ospite_90",
                      "snap_away_goals"),
    "gol_casa_finale": ("tf_Gol casa regolamentari", "sof_Gol casa",
                        "cop_gol_casa_finale", "snap_home_goals", "ps_gol_casa"),
    "gol_trasferta_finale": ("tf_Gol trasferta regolamentari", "sof_Gol trasferta",
                             "cop_gol_ospite_finale", "snap_away_goals",
                             "ps_gol_trasferta"),
    "gol_casa_1t": ("tf_Casa 1T (SofaScore)", "sof_Casa 1T", "snap_home_goals_ht"),
    "gol_trasferta_1t": ("tf_Trasferta 1T (SofaScore)", "sof_Trasferta 1T",
                         "snap_away_goals_ht"),
    "gol_casa_2t": ("tf_Casa 2T (SofaScore)", "sof_Casa 2T"),
    "gol_trasferta_2t": ("tf_Trasferta 2T (SofaScore)", "sof_Trasferta 2T"),
    "gol_casa_suppl": ("tf_Casa suppl. (SofaScore)", "sof_Casa suppl."),
    "gol_trasferta_suppl": ("tf_Trasferta suppl. (SofaScore)",
                            "sof_Trasferta suppl."),
    "rigori_casa": ("tf_Rigori casa (SofaScore)", "sof_Rigori casa",
                    "cop_rigori_casa"),
    "rigori_trasferta": ("tf_Rigori trasferta (SofaScore)", "sof_Rigori trasferta",
                         "cop_rigori_ospite"),
    "arbitro": ("tf_Arbitro (SofaScore)", "tf_Arbitro (WhoScored)", "sof_Arbitro",
                "cop_arbitro", "ps_arbitro"),
    "stadio": ("tf_Stadio (SofaScore)", "tf_Stadio (WhoScored)", "sof_Stadio",
               "cop_stadio", "ps_stadio"),
    "citta": ("tf_Città (SofaScore)", "sof_Città"),
    "paese_stadio": ("tf_Paese (SofaScore)", "sof_Paese"),
    "capienza": ("tf_Capienza (SofaScore)", "sof_Capienza"),
    "spettatori": ("tf_Spettatori (SofaScore)", "tf_Spettatori (WhoScored)",
                   "sof_Spettatori", "cop_spettatori", "ps_spettatori"),
    "riempimento_pct": ("tf_Riempimento % (SofaScore)", "sof_Riempimento %"),
    "latitudine": ("tf_Latitudine (SofaScore)", "sof_Latitudine"),
    "longitudine": ("tf_Longitudine (SofaScore)", "sof_Longitudine"),
    # ⚠️ NON è il meteo. `Meteo (WhoScored)` è un codice numerico che vale
    # 5.0 e SOLO 5.0 ovunque sia pieno (varianza zero, misurata su tutte le
    # raccolte): il «98,4% piena» della Premier sono 748 righe identiche.
    # Finto pieno da manuale (R6) — resta, col nome che dice cos'è, perché
    # cancellare un dato è peggio che dichiararlo inservibile.
    "meteo_codice_whoscored": ("tf_Meteo (WhoScored)",),
    "superficie": ("sof_Superficie",),
    "allenatore_casa": ("tf_Allenatore casa (SofaScore)",
                        "tf_Allenatore casa (WhoScored)", "sof_Allenatore casa",
                        "cop_allenatore_casa", "ps_allenatore_casa"),
    "allenatore_trasferta": ("tf_Allenatore trasferta (SofaScore)",
                             "tf_Allenatore trasferta (WhoScored)",
                             "sof_Allenatore trasferta", "cop_allenatore_ospite",
                             "ps_allenatore_trasferta"),
    "modulo_casa": ("tf_Modulo casa (SofaScore)", "tf_Modulo casa (WhoScored)",
                    "sof_Modulo casa", "cop_modulo_casa", "dir_casa_modulo",
                    "ps_modulo_casa"),
    "modulo_trasferta": ("tf_Modulo trasferta (SofaScore)",
                         "tf_Modulo trasferta (WhoScored)",
                         "sof_Modulo trasferta", "cop_modulo_ospite",
                         "dir_trasferta_modulo", "ps_modulo_trasferta"),
    "formazione_casa": ("tf_casa_formazione", "dir_casa_formazione",
                        "cop_casa_formazione_ps"),
    "formazione_trasferta": ("tf_trasferta_formazione", "dir_trasferta_formazione",
                             "cop_trasferta_formazione_ps"),
    "marcatori_casa": ("tf_casa_marcatori", "dir_casa_marcatori", "cop_casa_gol_ps"),
    "marcatori_trasferta": ("tf_trasferta_marcatori", "dir_trasferta_marcatori",
                            "cop_trasferta_gol_ps"),
    "cronaca": ("tf_cronaca", "sof_cronaca", "cop_cronaca_diretta",
                "cop_cronaca_ps"),
}

ORDINE_TESTA = [
    "match_uid", "competizione", "competizione_in_lista_utente", "paese",
    "tipo_competizione", "livello_divisione", "stagione", "turno", "fase",
    "data", "ora", "data_ora_utc", "casa", "trasferta",
    "gol_casa", "gol_trasferta", "esito_1x2",
    "gol_casa_finale", "gol_trasferta_finale", "esito_finale",
    "gol_casa_1t", "gol_trasferta_1t",
    "gol_casa_2t", "gol_trasferta_2t", "gol_casa_suppl", "gol_trasferta_suppl",
    "rigori_casa", "rigori_trasferta", "supplementari", "lotteria_rigori",
    "stadio", "citta", "paese_stadio", "capienza", "spettatori",
    "riempimento_pct", "latitudine", "longitudine", "superficie", "meteo_codice_whoscored",
    "arbitro", "allenatore_casa", "allenatore_trasferta",
    "modulo_casa", "modulo_trasferta", "formazione_casa", "formazione_trasferta",
    "marcatori_casa", "marcatori_trasferta", "cronaca",
    "giocatori_casa_in_colonna", "giocatori_trasferta_in_colonna",
    "casa_uefa_coeff", "trasferta_uefa_coeff", "casa_uefa_paese",
    "trasferta_uefa_paese", "casa_uefa_pavimento", "trasferta_uefa_pavimento",
    "fonti_disponibili", "n_fonti", "provenienza_json",
]

PREFISSI = ("tf_", "dir_", "snap_", "cop_", "sof_", "ps_")


def _coalesce(tabella: pd.DataFrame) -> pd.DataFrame:
    """Riempie i campi normalizzati e registra da dove viene ogni valore."""
    provenienza = [dict() for _ in range(len(tabella))]
    for campo, candidate in COALESCENZE.items():
        valori = pd.Series(np.nan, index=tabella.index, dtype="object")
        da = pd.Series(None, index=tabella.index, dtype="object")
        for colonna in candidate:
            if colonna not in tabella.columns:
                continue
            vuoti = valori.isna()
            if not vuoti.any():
                break
            candidato = tabella[colonna]
            prendi = vuoti & candidato.notna()
            valori.loc[prendi] = candidato.loc[prendi]
            da.loc[prendi] = colonna
        tabella[campo] = valori
        for posizione, fonte in enumerate(da):
            # ⚠️ `if fonte` non basta: una Series object costruita da None
            # contiene NaN, che è truthy — e finiva dentro il JSON come
            # letterale `NaN`, che nessun parser JSON accetta.
            # il prefisso, non il nome intero: `tf` invece di
            # `tf_Gol casa regolamentari`. La colonna esatta si ritrova
            # dall'ordine di `COALESCENZE`, che è fisso e documentato; il nome
            # per esteso su 4.169 righe × 30 campi pesava 4 MB.
            if isinstance(fonte, str) and fonte:
                provenienza[posizione][campo] = fonte.split("_", 1)[0]
    tabella["provenienza_json"] = [json_compatto(p) for p in provenienza]
    return tabella


def _esito(casa: object, trasferta: object) -> str | None:
    if pd.isna(casa) or pd.isna(trasferta):
        return None
    if casa > trasferta:
        return "1"
    if casa < trasferta:
        return "2"
    return "X"


def costruisci(solo: list[str] | None = None) -> pd.DataFrame:
    """Monta la tabella: spina dorsale, innesti, colonne normalizzate."""
    raccolte = [r for r in tf.leghe_disponibili()
                if solo is None or r in solo]

    log.info("── spina dorsale ─────────────────────────────────────────────")
    spine: list[pd.DataFrame] = []
    # ⚠️ Gli innesti si raggruppano per FAMIGLIA e si impilano PRIMA di essere
    # agganciati. Agganciarli uno per uno era un bug vero e silenzioso: la
    # seconda competizione porta le stesse colonne della prima
    # (`tf_casa_formazione`…), il merge le avrebbe duplicate, e scartarle
    # perché «già presenti» buttava via il dato di 15 competizioni su 16.
    # Si vedeva solo da un numero fuori posto — `formazione_casa` piena al
    # 14,8% invece che al 95%.
    famiglie: dict[str, list[pd.DataFrame]] = defaultdict(list)
    for raccolta in raccolte:
        base = blocco_tre_fonti(raccolta)
        if base.empty:
            continue
        spine.append(base)
        famiglie["tf_giocatori"].append(blocco_giocatori_tf(raccolta))
        famiglie["tf_eventi"].append(blocco_eventi_tf(raccolta))
        famiglie["tf_conteggi"].append(blocco_conteggi_tf(raccolta))

    if solo is None or "coppe" in (solo or []):
        spina_coppe, corredo_coppe = blocco_coppe()
        if not spina_coppe.empty:
            spine.append(spina_coppe)
            famiglie["coppe"].append(corredo_coppe)
        spina_europa, corredo_europa = blocco_coppe_europee()
        if not spina_europa.empty:
            spine.append(spina_europa)
            famiglie["sofascore_europa"].append(corredo_europa)

    if not spine:
        raise SystemExit("nessuna fonte leggibile: niente da costruire")

    tabella = pd.concat(spine, ignore_index=True)
    prima = len(tabella)
    # ⚠️ Le competizioni UEFA arrivano da DUE raccolte (tre-fonti e la
    # consegna SofaScore dedicata): le righe si fondono sulla chiave, non si
    # sommano. `groupby.first` tiene il primo valore non nullo colonna per
    # colonna, quindi la fusione non perde nulla di ciò che una sola delle due
    # aveva.
    tabella = tabella.groupby("_chiave", as_index=False, sort=False).first().copy()
    log.info("spina dorsale: %d righe → %d partite distinte", prima, len(tabella))

    log.info("── innesti ───────────────────────────────────────────────────")
    if solo is None:
        for lega in DIRETTA_LEGHE:
            famiglie["diretta"].append(blocco_diretta(lega))
        famiglie["snapshot"].append(blocco_snapshot())
        famiglie["player_scores"].append(blocco_player_scores())

    for nome, pezzi in famiglie.items():
        pezzi = [p for p in pezzi
                 if p is not None and not p.empty and "_chiave" in p.columns]
        if not pezzi:
            continue
        innesto = pd.concat(pezzi, ignore_index=True)
        innesto = innesto.groupby("_chiave", as_index=False, sort=False).first()
        doppie = [c for c in innesto.columns
                  if c != "_chiave" and c in tabella.columns]
        if doppie:
            log.warning("famiglia %s: %d colonne già presenti, scartate (%s…)",
                        nome, len(doppie), ", ".join(doppie[:4]))
            innesto = innesto.drop(columns=doppie)
        tabella = tabella.merge(innesto, on="_chiave", how="left")
        log.info("  innestata famiglia %-18s %4d partite · %4d colonne",
                 nome, innesto["_chiave"].nunique(), innesto.shape[1] - 1)

    log.info("── colonne normalizzate ──────────────────────────────────────")
    tabella["competizione"] = tabella["competizione"].map(
        lambda c: canon_competizione(c) or c)
    metadati = tabella["competizione"].map(
        lambda c: COMPETIZIONI.get(c, ("?", "?", "?")))
    tabella["paese"] = [m[0] for m in metadati]
    tabella["tipo_competizione"] = [m[1] for m in metadati]
    tabella["livello_divisione"] = [m[2] for m in metadati]
    tabella["competizione_in_lista_utente"] = tabella["competizione"].isin(LISTA_UTENTE)
    tabella["stagione"] = STAGIONE
    tabella["data"] = tabella["data"].map(norm_data)
    if "cop_supplementari" in tabella.columns:
        tabella["fase"] = tabella.get("dir_casa_fase")
    tabella = _coalesce(tabella)

    tabella["supplementari"] = (
        pd.to_numeric(tabella.get("gol_casa_suppl"), errors="coerce").notna()
        | pd.to_numeric(tabella.get("gol_trasferta_suppl"), errors="coerce").notna())
    # dove i 90 minuti non si ricavano dalle frazioni ma la partita e' finita
    # nei tempi regolamentari, il punteggio finale E' quello dei 90 minuti.
    for lato in ("casa", "trasferta"):
        novanta = pd.to_numeric(tabella[f"gol_{lato}"], errors="coerce")
        finale = pd.to_numeric(tabella[f"gol_{lato}_finale"], errors="coerce")
        prendi = novanta.isna() & finale.notna() & ~tabella["supplementari"]
        tabella.loc[prendi, f"gol_{lato}"] = finale[prendi]
    tabella["esito_1x2"] = [_esito(c, t) for c, t in
                            zip(tabella["gol_casa"], tabella["gol_trasferta"])]
    tabella["esito_finale"] = [_esito(c, t) for c, t in
                               zip(tabella["gol_casa_finale"],
                                   tabella["gol_trasferta_finale"])]
    tabella["lotteria_rigori"] = (
        pd.to_numeric(tabella.get("rigori_casa"), errors="coerce").notna()
        | pd.to_numeric(tabella.get("rigori_trasferta"), errors="coerce").notna())

    # coefficienti UEFA dei due club
    uefa = blocco_uefa()
    if not uefa.empty:
        for lato in ("casa", "trasferta"):
            norme = tabella[lato].map(norm_squadra)
            tabella[f"{lato}_uefa_coeff"] = norme.map(uefa["Coefficiente UEFA"])
            tabella[f"{lato}_uefa_paese"] = norme.map(uefa["Paese"])
            tabella[f"{lato}_uefa_pavimento"] = norme.map(uefa["_pavimento"])

    # dove sta il pacchetto dei giocatori di QUESTA partita. Non è il
    # pacchetto: è il suo indirizzo. Copiarlo in una colonna «unificata»
    # avrebbe raddoppiato 38 MB di JSON per zero informazione nuova.
    candidati = ("tf_{lato}_giocatori_json", "cop_{lato}_giocatori_json",
                 "cop_{lato}_formazione_json")
    for lato in ("casa", "trasferta"):
        dove = pd.Series(None, index=tabella.index, dtype="object")
        for modello in candidati:
            colonna = modello.format(lato=lato)
            if colonna in tabella.columns:
                dove = dove.where(dove.notna(),
                                  tabella[colonna].notna().map({True: colonna,
                                                                False: None}))
        tabella[f"giocatori_{lato}_in_colonna"] = dove

    # provenienza a colpo d'occhio
    presenze = {}
    for prefisso, etichetta in (("tf_", "tre_fonti"), ("dir_", "diretta"),
                                ("snap_", "snapshot"), ("cop_", "coppe"),
                                ("sof_", "sofascore_europa"),
                                ("ps_", "player_scores")):
        colonne = [c for c in tabella.columns if c.startswith(prefisso)]
        presenze[etichetta] = (tabella[colonne].notna().any(axis=1)
                               if colonne else pd.Series(False, index=tabella.index))
    tabella["fonti_disponibili"] = [
        "+".join(e for e, v in presenze.items() if v.iloc[i]) or None
        for i in range(len(tabella))]
    tabella["n_fonti"] = sum(v.astype(int) for v in presenze.values())

    tabella["match_uid"] = tabella["_chiave"]
    tabella = tabella.drop(columns=["_chiave"])

    # R6: una colonna che c'è e non contiene niente è un finto pieno
    vuote = [c for c in tabella.columns if tabella[c].isna().all()]
    if vuote:
        log.info("scartate %d colonne interamente vuote", len(vuote))
        tabella = tabella.drop(columns=vuote)

    testa = [c for c in ORDINE_TESTA if c in tabella.columns]
    coda = [c for c in tabella.columns if c not in testa]
    coda.sort(key=lambda c: (next((i for i, p in enumerate(PREFISSI)
                                   if c.startswith(p)), len(PREFISSI)), c))
    tabella = tabella[testa + coda]
    tabella = tabella.sort_values(["competizione", "data", "casa"],
                                  kind="stable").reset_index(drop=True)
    return tabella


def main() -> None:
    argomenti = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argomenti.add_argument("--out", type=Path, default=USCITA_DEFAULT)
    argomenti.add_argument("--solo", nargs="*", default=None,
                           help="limita alle raccolte indicate (per prove)")
    argomenti.add_argument("-v", "--verboso", action="store_true")
    opzioni = argomenti.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(message)s" if not opzioni.verboso
                        else "%(levelname)s %(name)s %(message)s")

    tabella = costruisci(opzioni.solo)
    opzioni.out.parent.mkdir(parents=True, exist_ok=True)
    tabella.to_csv(opzioni.out, index=False)
    peso = opzioni.out.stat().st_size / 1e6
    log.info("──────────────────────────────────────────────────────────────")
    log.info("scritto %s", opzioni.out)
    log.info("%d partite · %d colonne · %.1f MB", len(tabella),
             tabella.shape[1], peso)
    log.info("competizioni: %d", tabella["competizione"].nunique())
    for competizione, quante in tabella["competizione"].value_counts().items():
        log.info("   %-26s %4d", competizione, quante)


if __name__ == "__main__":
    main()
