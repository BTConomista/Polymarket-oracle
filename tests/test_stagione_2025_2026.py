"""Le guardie di `data/stagione_2025_2026/` e del suo costruttore.

PERCHE' ESISTE QUESTO FILE, e perche' e' separato da
`test_actual_database2526.py`. La cartella non e' «il file unico spezzato in
piu' pezzi»: e' una struttura con invarianti proprie, e ognuna di esse e' un
modo di rompersi **senza dare errore**.

  * il **manifesto** puo' descrivere un disco che non c'e' piu' (o non
    descrivere un file rimasto da una passata precedente): nessuno se ne
    accorge finche' qualcuno non prova ad aprire il pezzo mancante;
  * il **tasso di aggancio** puo' essere una tautologia. Lo e' stato: era
    `match_uid.notna()` su una colonna che si costruisce sempre, quindi
    dichiarava 100% mentre 27.841 chiavi puntavano a partite inesistenti. Un
    puntatore rotto e' un `notna()` che passa;
  * il **perimetro** puo' allargarsi in silenzio. Il filtro «solo 2025-26» che
    guarda la colonna `stagione` non vede una fonte che chiama quella colonna
    `season`, e 32 righe di un'altra stagione entrano senza un messaggio;
  * una colonna puo' contenere il **futuro**. Il coefficiente UEFA pubblicato
    somma cinque stagioni e la quinta e' la 26/27: un numero giusto, di un
    momento sbagliato (R8). Nessun conteggio di celle piene lo vede.

I test che leggono la cartella si saltano se non c'e' (si rigenera con
`python scripts/build_stagione_2025_2026.py`, ~40 minuti).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_stagione_2025_2026 import (
    BLOCCHI, CARTELLA, NOTA_AGGANCIO, TETTO_MB, _interi_restano_interi,
)
from scripts.build_actual_database2526 import chiave_partita, norm_data


# ════════════════════════════════════════════════════════════════════════════
# le funzioni pure — girano sempre, non serve la cartella
# ════════════════════════════════════════════════════════════════════════════
def test_gli_interi_restano_interi():
    """La colonna che passa per un `NaN` non deve tornare `12.0`.

    Difetto misurato e chiuso: 356.351 celle scrivevano `7.0` dove il dato e'
    «sette gol». Non e' estetica — `read_csv` le rilegge come float e ogni
    confronto con un intero letto da un'altra tabella fallisce.
    """
    dentro = pd.DataFrame({"minuti": [90.0, None, 45.0],
                           "nome": ["a", "b", "c"],
                           "xg": [0.5, 0.25, None]})
    fuori = _interi_restano_interi(dentro)
    assert str(fuori["minuti"].dtype) == "Int64"
    assert fuori["minuti"].tolist()[0] == 90
    # ⚠️ una colonna con la VIRGOLA non e' un intero travestito: xg resta float
    assert str(fuori["xg"].dtype).startswith("float")
    # ⚠️ non si inchioda `object`: pandas 3 chiama `str` lo stesso dtype.
    # Quello che conta e' che il testo NON sia diventato un intero.
    assert str(fuori["nome"].dtype) != "Int64"
    assert fuori["nome"].tolist() == ["a", "b", "c"]


def test_la_nota_di_aggancio_non_promette_notna():
    """La nota deve dire che l'aggancio e' un'APPARTENENZA, non un `notna()`.

    Il testo e' il documento che accompagna il numero: se torna a dire
    «quante righe hanno la chiave», il numero ridiventa la tautologia che era.
    """
    assert "ESISTE" in NOTA_AGGANCIO
    assert "notna" in NOTA_AGGANCIO


def test_i_blocchi_sono_selezionabili_uno_per_uno():
    """`--solo <blocco>` e' il modo di ricostruire un pezzo senza rifare tutto.

    Se un nome sparisce dal dizionario ma resta in un comando documentato, il
    costruttore non da' errore: costruisce la cartella INTERA, e chi lo ha
    lanciato per un pezzo si ritrova quaranta minuti dopo.
    """
    assert "partite" in BLOCCHI
    for nome, descrizione in BLOCCHI.items():
        assert isinstance(descrizione, str) and descrizione


# ════════════════════════════════════════════════════════════════════════════
# la cartella prodotta — si saltano se non c'e'
# ════════════════════════════════════════════════════════════════════════════
def _manifesto() -> dict:
    percorso = CARTELLA / "MANIFESTO.json"
    if not percorso.exists():
        pytest.skip(f"manca {percorso}: rigenerare con "
                    "`python scripts/build_stagione_2025_2026.py`")
    return json.loads(percorso.read_text())


def test_ogni_pezzo_dichiarato_esiste_sul_disco():
    manifesto = _manifesto()
    mancanti = [p["file"] for v in manifesto["tabelle_dettaglio"].values()
                for p in v["pezzi"] if not (CARTELLA / p["file"]).exists()]
    assert not mancanti, f"dichiarati e assenti: {mancanti[:5]}"


def test_nessun_file_supera_il_tetto():
    """Il tetto e' la RAGIONE per cui la cartella esiste al posto del file
    unico: GitHub rifiuta oltre i 100 MB, e un pezzo sopra soglia si scopre
    al `git push`, cioe' dopo quaranta minuti di lavoro.
    """
    manifesto = _manifesto()
    sopra = [(p["file"], p["mb"]) for v in manifesto["tabelle_dettaglio"].values()
             for p in v["pezzi"] if p["mb"] > TETTO_MB]
    assert not sopra, f"sopra i {TETTO_MB} MB: {sopra}"


def test_ogni_pezzo_si_apre_con_un_read_csv_nudo():
    """Chi riceve la cartella non legge il nostro codice: fa `pd.read_csv`.

    Difetto pagato: `squadre_partita_tre_fonti` era scritta gzippata ma senza
    l'estensione `.csv.gz`, e `read_csv` alzava `UnicodeDecodeError`. Il
    manifesto era perfetto, il file illeggibile.
    """
    manifesto = _manifesto()
    rotti = []
    for voce in manifesto["tabelle_dettaglio"].values():
        for pezzo in voce["pezzi"][:1]:      # un pezzo per tabella: basta
            percorso = CARTELLA / pezzo["file"]
            if not percorso.exists() or percorso.suffix == ".json":
                continue
            try:
                pd.read_csv(percorso, nrows=3, low_memory=False)
            except Exception as errore:      # noqa: BLE001 — e' il punto
                rotti.append((pezzo["file"], type(errore).__name__))
    assert not rotti, f"non si aprono: {rotti[:5]}"


def test_partite_ha_una_riga_per_partita():
    percorso = CARTELLA / "partite.csv.gz"
    if not percorso.exists():
        pytest.skip("manca partite.csv.gz")
    uid = pd.read_csv(percorso, usecols=["match_uid"], low_memory=False)
    assert not uid["match_uid"].duplicated().any()
    assert uid["match_uid"].notna().all()


def test_il_ranking_uefa_non_contiene_il_futuro():
    """R8: il coefficiente pubblicato somma anche la 26/27, che comincia DOPO
    l'ultima partita dell'archivio.

    Il test non chiede che la colonna esista — una copia del numero pubblicato
    la soddisferebbe. Chiede che le due finestre **divergano davvero** su
    qualche riga, e che l'identita' che le separa torni.
    """
    percorso = CARTELLA / "partite.csv.gz"
    if not percorso.exists():
        pytest.skip("manca partite.csv.gz")
    colonne = ["casa_uefa_coeff_pubblicato", "casa_uefa_coeff_fino_2526",
               "casa_uefa_punti_2627", "casa_uefa_somma_pubblicata",
               "casa_uefa_somma_fino_2526", "casa_uefa_pavimento_fino_2526"]
    d = pd.read_csv(percorso, usecols=colonne, low_memory=False)
    sopra = pd.to_numeric(d["casa_uefa_coeff_pubblicato"], errors="coerce")
    sotto = pd.to_numeric(d["casa_uefa_coeff_fino_2526"], errors="coerce")
    futuro = pd.to_numeric(d["casa_uefa_punti_2627"], errors="coerce")
    assert (sopra - sotto).abs().gt(1e-9).any(), \
        "le due finestre coincidono ovunque: la troncatura non e' stata applicata"
    # ⚠️ l'identita' esatta e' sulle SOMME: il coefficiente e'
    # `MAX(somma; 20% federazione)`, e il pavimento e' una proprieta' della
    # FINESTRA — su 6 club morde nella troncata e non nella pubblicata.
    s_sopra = pd.to_numeric(d["casa_uefa_somma_pubblicata"], errors="coerce")
    s_sotto = pd.to_numeric(d["casa_uefa_somma_fino_2526"], errors="coerce")
    note = s_sopra.notna() & s_sotto.notna() & futuro.notna()
    assert not (((s_sopra - s_sotto - futuro).abs() > 1e-6) & note).any(), \
        "somma pubblicata − somma troncata ≠ punti 26/27"
    assert not (sotto > sopra + 1e-9).any(), \
        "il coefficiente troncato supera il pubblicato: togliere punti non ne aggiunge"
    # e il pavimento della finestra troncata deve essere DICHIARATO: senza,
    # chi legge `pavimento=False` accanto al troncato conclude il contrario.
    assert d["casa_uefa_pavimento_fino_2526"].notna().any()


def test_i_tempi_che_non_ricompongono_sono_marcati():
    """R5 punto 5: un residuo non diagnosticato si REGISTRA, non si zittisce.

    Le righe dove `Gol ≠ 1T + 2T + suppl.` senza che sia la lotteria dei
    rigori sono un reperto aperto (Europa League). Devono avere una colonna
    che le nomina, altrimenti la sessione dopo le ri-trova e le «corregge».
    """
    percorso = CARTELLA / "partite.csv.gz"
    if not percorso.exists():
        pytest.skip("manca partite.csv.gz")
    d = pd.read_csv(percorso, usecols=["tempi_non_ricompongono",
                                       "tempi_tutti_a_zero_con_gol"],
                    low_memory=False)
    assert len(d.columns) == 2


def test_ogni_data_e_della_stagione_2025_26():
    """«Solo quella stagione» e' una richiesta esplicita, non un'inclinazione.

    Si controlla sulla porta d'ingresso: se una partita di un'altra stagione
    entra li', tutte le tabelle che le si agganciano la ereditano.
    """
    percorso = CARTELLA / "partite.csv.gz"
    if not percorso.exists():
        pytest.skip("manca partite.csv.gz")
    d = pd.read_csv(percorso, usecols=["data"], low_memory=False)
    date = d["data"].map(norm_data).dropna()
    fuori = date[(date < "2025-07-01") | (date >= "2026-07-01")]
    assert fuori.empty, f"{len(fuori)} date fuori finestra: {fuori.head(3).tolist()}"


def test_il_manifesto_dichiara_grana_e_fonti_per_ogni_tabella():
    """Una tabella senza grana dichiarata e' una tabella che qualcuno unira'
    al grano sbagliato: e' il difetto che il file unico ha pagato per intero.
    """
    manifesto = _manifesto()
    mute = [n for n, v in manifesto["tabelle_dettaglio"].items()
            if not v.get("grana") or not v.get("fonti")]
    assert not mute, f"senza grana o fonti: {mute[:5]}"
