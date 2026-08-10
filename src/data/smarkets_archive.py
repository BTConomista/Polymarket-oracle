"""L'archivio degli snapshot Smarkets: elencarlo e leggerlo, in un punto solo.

PERCHE' ESISTE. Dalla Fase 136 il raccoglitore scrive **compresso**
(`.json.gz`): a listino intero il giro giornaliero produce ~16 MB per
esecuzione, cioe' oltre 4 GB su una stagione, e in un repo git ogni file e' un
oggetto nuovo. Il gzip toglie **19,6x** senza perdere un byte — e' la stessa
scelta gia' fatta per i dati diretta.it (868 KB contro 29 MB).

Ma l'archivio **gia' raccolto** e' in `.json` non compresso, e va letto lo
stesso: un formato nuovo non deve rendere illeggibile cio' che c'e'. Da qui
questo modulo, che e' l'unico posto dove la doppia estensione e' un problema.

⚠️ L'archivio mescola DUE REGIMI, e confonderli e' un errore vero:
  - **lungo raggio**: tutte le partite esposte delle 5 leghe (`entro_ore: 0`);
  - **chiusura**: solo le partite entro poche ore (`entro_ore: 2`).
Un file di chiusura ha una lega sola ed e' legittimo. Chi cerca «il listino»
deve chiedere `ultimo_listino_completo()`, non «il file piu' recente»: quella
assunzione ha gia' fatto fallire due test il 02/08/2026.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

ARCHIVIO = Path(__file__).resolve().parents[2] / "data" / "smarkets_matches"

# Le 5 leghe modellate: un file che le contiene tutte e' un listino completo.
LEGHE_ATTESE = 5


def snapshots(cartella: Path | None = None) -> list[Path]:
    """Tutti gli snapshot, ordinati cronologicamente (il nome e' un timestamp).

    Comprende sia i `.json` storici sia i `.json.gz` nuovi. L'ordinamento e'
    sul nome **senza estensione**, altrimenti un `.json.gz` scritto un minuto
    dopo un `.json` finirebbe prima di lui.
    """
    d = cartella or ARCHIVIO
    if not d.is_dir():
        return []
    trovati = list(d.glob("*.json")) + list(d.glob("*.json.gz"))
    return sorted(trovati, key=lambda p: p.name.replace(".json.gz", "").replace(".json", ""))


def leggi(path: Path) -> dict:
    """Il contenuto di uno snapshot, compresso o no."""
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def scrivi(path: Path, dati: dict) -> Path:
    """Scrive uno snapshot compresso, restituendo il percorso finale.

    Il `.gz` viene aggiunto qui e non dal chiamante, cosi' il formato e' deciso
    in un punto solo. `mtime=0` rende il file **riproducibile**: senza, due
    esecuzioni con gli stessi dati darebbero byte diversi e git vedrebbe una
    modifica che non c'e'.
    """
    finale = path if path.name.endswith(".gz") else path.with_suffix(path.suffix + ".gz")
    finale.parent.mkdir(parents=True, exist_ok=True)
    grezzo = json.dumps(dati, ensure_ascii=False, indent=1).encode("utf-8")
    with gzip.GzipFile(finale, "wb", compresslevel=9, mtime=0) as f:
        f.write(grezzo)
    return finale


def ultimo(cartella: Path | None = None) -> Path | None:
    """L'ultimo snapshot, qualunque regime. Nessuno se l'archivio e' vuoto."""
    tutti = snapshots(cartella)
    return tutti[-1] if tutti else None


def ultimo_listino_completo(cartella: Path | None = None,
                            leghe_attese: int = LEGHE_ATTESE) -> Path:
    """L'ultimo snapshot che contiene TUTTE le leghe modellate.

    E' cio' che serve a chi cerca il calendario o la mappa dei nomi: un file di
    chiusura ne contiene una sola ed e' corretto che sia cosi'. Alza con un
    messaggio esplicito invece di restituire un file parziale — un listino
    parziale scambiato per completo e' il tipo di errore che nessun conteggio
    intercetta.

    ⚠️ Si contano le sole righe di **fascia `campionato`** (Fase 142). Dal
    perimetro allargato un file contiene anche coppe e seconde divisioni, e
    `len({lega})` conterebbe `coppa_italia` e `serie_b` come se fossero
    campionati: un file con due leghe e quattro coppe supererebbe la soglia
    di cinque ed entrerebbe qui dentro travestito da listino completo.
    I file scritti PRIMA della Fase 142 non hanno il campo — sono tutti e soli
    campionati, quindi l'assenza vale `campionato`.
    """
    tutti = snapshots(cartella)
    for f in reversed(tutti):
        righe = leggi(f).get("righe") or []
        leghe = {r.get("lega") for r in righe
                 if r.get("fascia", "campionato") == "campionato"}
        if len(leghe) >= leghe_attese:
            return f
    raise FileNotFoundError(
        f"nessuno dei {len(tutti)} snapshot in {cartella or ARCHIVIO} copre "
        f"tutte e {leghe_attese} le leghe: l'archivio contiene solo giri di "
        "chiusura, oppure il raccoglitore di lungo raggio non ha mai girato."
    )
