"""Costruisce l'elenco dei nomi che SMARKETS usa per le nostre 96 squadre (Fase 149).

PERCHE' NON BASTAVA L'ANAGRAFICA CHE C'E' GIA'.
`data/stagione_2026_2027/club/*/*/anagrafica.json` ha un campo che si chiama
**`nome_smarkets`** ed e' esattamente quello che serviva per riconoscere una
nostra squadra dentro `club-friendlies`. Misurato l'11/08/2026: dei suoi 96
valori, **32 coincidono** con un nome che Smarkets ha davvero usato nel nostro
archivio, 64 no -- `Juventus Turin` contro `Juventus`, `Inter Milano` contro
`Inter Milan`, `AS Roma` contro `Roma`, `Man Utd` contro `Manchester United`.
Il campo porta il nome di una fonte e contiene il nome di un'altra (sembra il
nome del dataset player-scores). E' un **finto pieno** da manuale (R6): non e'
vuoto, non e' `NaN`, non lo trova nessun controllo di completezza -- e chi lo
usa per un join perde due terzi delle righe **in silenzio**.

⚠️ Questo script NON corregge l'anagrafica: R3 vieta la modifica a mano dei
dati, e quel file e' letto anche da `scripts/raccolta_giornaliera.py` (che ha
un test rosso aperto proprio sul join dei nomi -- e' probabilmente lo stesso
difetto, ma e' di un'altra sessione). Qui ci si limita a **non usarlo** e a
dichiarare il perche'.

DA DOVE VIENE IL DATO GIUSTO. Dall'archivio che abbiamo gia': ogni riga di
`data/smarkets_matches/` con `fascia == "campionato"` porta il nome
dell'evento **come Smarkets lo scrive**, per una partita di uno dei 5
campionati che modelliamo. Non e' una traduzione ne' una stima: e' la fonte
che parla di se stessa. Le 96 squadre delle 5 leghe compaiono tutte (una
giornata per lega e' gia' sufficiente: 10 partite = 20 nomi per lega).

⚠️ IL LIMITE, dichiarato. L'elenco vale per le squadre che hanno **gia'
giocato** (o che sono gia' quotate) nel periodo scandito. Una squadra che
non compare nell'archivio non ci finisce, e la sua amichevole resta fuori dal
perimetro: si chiude ri-eseguendo questo script, non a mano.

USO:
    python scripts/costruisci_squadre_smarkets.py            # scrive il file
    python scripts/costruisci_squadre_smarkets.py --verifica # controlla e basta
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVIO = ROOT / "data" / "smarkets_matches"
DEST = ROOT / "data" / "squadre_smarkets_2026_27.json"

# Le 5 leghe modellate: se una mancasse, l'elenco sarebbe parziale e lo
# diciamo invece di scriverlo lo stesso.
LEGHE = ("serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1")


def _righe(percorso: Path):
    apri = gzip.open if percorso.suffix == ".gz" else open
    try:
        dati = json.load(apri(percorso, "rt"))
    except (OSError, ValueError):
        return []
    return dati["righe"] if isinstance(dati, dict) and "righe" in dati else dati


def raccogli(file_scanditi: int = 80) -> dict[str, list[str]]:
    """{lega: [nomi Smarkets]} dai file piu' recenti dell'archivio.

    Si guardano gli ultimi `file_scanditi` e non tutto l'archivio perche' i
    nomi cambiano fra stagioni (una retrocessa del 2025 non ci serve) e
    perche' leggere l'archivio intero costerebbe minuti per un dato che sta
    in una manciata di file.
    """
    per_lega: dict[str, set[str]] = collections.defaultdict(set)
    for percorso in sorted(ARCHIVIO.glob("*.json*"))[-file_scanditi:]:
        for riga in _righe(percorso):
            if riga.get("fascia") != "campionato":
                continue
            casa, _, ospite = str(riga.get("partita", "")).partition(" vs ")
            for nome in (casa.strip(), ospite.strip()):
                if nome:
                    per_lega[riga["lega"]].add(nome)
    return {lega: sorted(nomi) for lega, nomi in sorted(per_lega.items())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verifica", action="store_true",
                    help="non scrive: dice solo cosa troverebbe")
    ap.add_argument("--file-scanditi", type=int, default=80)
    args = ap.parse_args()

    per_lega = raccogli(args.file_scanditi)
    totale = sum(len(v) for v in per_lega.values())
    for lega in LEGHE:
        print(f"  {lega:16s} {len(per_lega.get(lega, [])):3d} squadre")
    mancanti = [lega for lega in LEGHE if len(per_lega.get(lega, [])) < 18]
    if mancanti:
        # 18 e non 20: la Bundesliga ne ha 18, ed e' il minimo delle 5.
        print(f"⚠️ leghe con meno di 18 squadre nell'archivio recente: {mancanti} "
              f"— l'elenco sarebbe parziale, non lo scrivo")
        return 1
    print(f"  totale {totale} squadre")

    if args.verifica:
        return 0

    DEST.write_text(json.dumps({
        "cosa": "I nomi che SMARKETS usa per le squadre dei 5 campionati modellati.",
        "perche": ("Serve a riconoscere una nostra squadra dentro `club-friendlies`, "
                   "dove il perimetro si decide da CHI gioca e non da dove (Fase 149). "
                   "NON usare `nome_smarkets` dell'anagrafica 2026-27: misurato "
                   "l'11/08/2026, coincide col nome vero solo 32 volte su 96."),
        "fonte": ("generato da scripts/costruisci_squadre_smarkets.py leggendo "
                  f"gli ultimi {args.file_scanditi} file di data/smarkets_matches/ "
                  "(righe con fascia == 'campionato')"),
        "disponibilita_temporale": "statico (anagrafica di nomi, R8)",
        "totale": totale,
        "per_lega": per_lega,
    }, ensure_ascii=False, indent=1) + "\n")
    print(f"scritto {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
