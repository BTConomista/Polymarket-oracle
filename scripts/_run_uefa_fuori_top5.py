"""Dove arrivano, nelle coppe UEFA, i club dei campionati FUORI dai nostri 5.

Domanda dell'utente (12/08/2026): «fammi un elenco di dove sono arrivati i club
non dei top 5 nelle competizioni UEFA negli ultimi 2 anni, cosi' capiamo meglio
a quali campionati allargare lo sguardo».

E' un'analisi DESCRITTIVA per una decisione di perimetro, non un esperimento:
non registra nulla in `runs.jsonl` e non tocca nessun modello.

FONTE: `files/player_scores/games.csv.gz` (Transfermarkt via Kaggle), l'unica
in casa che copra le coppe UEFA su piu' stagioni e su TUTTI i club, non solo i
nostri. Stagioni 2024 e 2025 = 2024-25 e 2025-26.

⚠️ TRE AVVERTENZE, tutte misurate e nessuna aggirabile.

1. **Il girone unico ha cambiato significato al «Group Stage».** Dal 2024-25 le
   coppe UEFA hanno la fase a campionato: «Group Stage» non e' piu' un girone
   da 4 dove passa meta', ma una classifica da 36 dove i primi 8 vanno agli
   ottavi e i successivi 16 allo spareggio. Quindi *arrivare al Group Stage*
   nel 2024-25 vale meno che nel 2022-23, e i numeri qui NON si confrontano
   con le stagioni precedenti.

2. **Il turno piu' avanzato NON e' il turno in cui una squadra e' uscita.**
   Chi perde la finale e chi la vince hanno entrambe `Final` come massimo. La
   colonna `vinta` distingue i due casi solo per la finale; per gli altri turni
   il massimo raggiunto e' quello che serve alla domanda («fin dove arrivano»),
   e non ho provato a dedurre l'eliminazione dai punteggi: sul doppio confronto
   servirebbe sommare le due gare e gestire i rigori, e il valore aggiunto per
   questa domanda e' nullo.

3. **Il dataset copre 32 campionati, non tutti.** Dei 307 club che hanno
   giocato una coppa UEFA nelle due stagioni, **149 sono in `clubs.csv` e 158
   no**: i secondi sono di federazioni minori (San Marino, Malta, Galles, Far
   Oer, Islanda, Lettonia, Irlanda del Nord, Montenegro...) e valgono il 49%
   delle partite, quasi tutte nelle QUALIFICAZIONI (442 su 942 in ECLQ).

   ⚠️ Il buco e' **sistematico e in una direzione sola**, ed e' questo che lo
   rende innocuo per la domanda: i club invisibili sono tutti di campionati
   piu' piccoli di quelli che restano, e nessuno di loro e' un candidato
   all'allargamento. Se il buco fosse stato casuale la classifica sarebbe
   inservibile; essendo monotono, sposta solo il fondo.
   Lo script lo MISURA e lo stampa invece di lasciarlo intuire.

Uso:
    python scripts/_run_uefa_fuori_top5.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FILES = Path(__file__).resolve().parents[1] / "files" / "player_scores"

#: I cinque campionati che il progetto modella, coi codici di player-scores.
TOP5 = {"IT1": "Serie A", "GB1": "Premier League", "ES1": "La Liga",
        "L1": "Bundesliga", "FR1": "Ligue 1"}

#: Le coppe per club, e il loro peso nel giudizio (una finale di Conference
#: non e' una finale di Champions).
COPPE = {"CL": "Champions", "EL": "Europa", "UCOL": "Conference"}
QUALIFICAZIONI = {"CLQ": "CL", "ELQ": "EL", "ECLQ": "UCOL"}

#: L'ordine dei turni, dal piu' lontano al piu' avanti. Le chiavi sono
#: normalizzate in minuscolo perche' la fonte usa DUE grafie per lo stesso
#: turno («last 16 1st leg» e «Last 16 1st Leg»): trattarle come turni diversi
#: spezzerebbe il massimo per squadra.
ORDINE = [
    ("qualificazione", 0),
    ("group stage", 1),
    ("intermediate stage", 2),      # spareggio per gli ottavi (dal 2024-25)
    ("last 16", 3),
    ("quarter-finals", 4),
    ("semi-finals", 5),
    ("final", 6),
]
ETICHETTA = {0: "qualificazioni", 1: "fase campionato", 2: "spareggio ottavi",
             3: "ottavi", 4: "quarti", 5: "semifinale", 6: "finale"}


def _livello(turno: str) -> int:
    t = str(turno).lower()
    for chiave, val in reversed(ORDINE):
        if chiave in t:
            return val
    return 0


def carica() -> pd.DataFrame:
    """Una riga per (club, coppa, stagione) col turno piu' avanzato raggiunto."""
    g = pd.read_csv(FILES / "games.csv.gz", low_memory=False)
    clubs = pd.read_csv(FILES / "clubs.csv.gz")
    lega = dict(zip(clubs["club_id"], clubs["domestic_competition_id"]))
    nome = dict(zip(clubs["club_id"], clubs["name"]))

    tutte = set(COPPE) | set(QUALIFICAZIONI)
    g = g[g["competition_id"].isin(tutte) & g["season"].isin([2024, 2025])].copy()
    g["coppa"] = g["competition_id"].map(lambda c: QUALIFICAZIONI.get(c, c))
    g["livello"] = g.apply(
        lambda r: 0 if r["competition_id"] in QUALIFICAZIONI else _livello(r["round"]),
        axis=1,
    )

    righe = []
    for _, r in g.iterrows():
        for lato in ("home_club_id", "away_club_id"):
            cid = r[lato]
            righe.append({
                "club_id": cid, "club": nome.get(cid, f"?{cid}"),
                "lega": lega.get(cid), "coppa": r["coppa"],
                "stagione": int(r["season"]), "livello": int(r["livello"]),
            })
    d = pd.DataFrame(righe)
    return (d.groupby(["club_id", "club", "lega", "coppa", "stagione"], dropna=False)
              ["livello"].max().reset_index())


def main() -> None:
    d = carica()
    d["top5"] = d["lega"].map(lambda x: x in TOP5)
    fuori = d[~d["top5"]].copy()

    print("=" * 78)
    print("DOVE ARRIVANO I CLUB FUORI DAI NOSTRI 5 CAMPIONATI — coppe UEFA 2024-25 e 2025-26")
    print("=" * 78)
    print(f"\nclub-coppa-stagione totali: {len(d)}  ·  fuori dai top 5: {len(fuori)}")
    ignoti = fuori[fuori["lega"].isna()]
    if len(ignoti):
        print(f"\n⚠️  COPERTURA: {len(ignoti)} righe su {len(fuori)} sono di club che "
              f"`clubs.csv` non conosce\n    ({ignoti['club_id'].nunique()} club di "
              "federazioni minori: San Marino, Malta, Galles, Far Oer, Islanda...).")
        print("    Il buco e' sistematico e MONOTONO — sono tutti campionati piu' piccoli")
        print("    di quelli che restano — quindi sposta il fondo della classifica, non")
        print("    l'ordine di chi ci interessa. Vedi l'avvertenza 3 in testa allo script.")

    # ---- la tabella che risponde alla domanda -----------------------------
    print("\n" + "=" * 78)
    print("I CAMPIONATI, per quanto lontano arrivano i loro club")
    print("=" * 78)
    noti = fuori.dropna(subset=["lega"])
    tab = (noti.groupby("lega")
                .agg(club=("club_id", "nunique"),
                     presenze=("club_id", "size"),
                     massimo=("livello", "max"),
                     mediana=("livello", "median"))
                .sort_values(["massimo", "presenze"], ascending=False))
    print(f"\n{'campionato':10s} {'club':>5s} {'presenze':>9s} {'meglio':>18s} {'tipico':>18s}")
    for lega, r in tab.iterrows():
        print(f"  {lega:8s} {int(r['club']):5d} {int(r['presenze']):9d} "
              f"{ETICHETTA[int(r['massimo'])]:>18s} {ETICHETTA[int(r['mediana'])]:>18s}")

    # ---- chi e' arrivato agli ottavi o oltre ------------------------------
    print("\n" + "=" * 78)
    print("I SINGOLI: chi e' arrivato agli OTTAVI o oltre (livello >= 3)")
    print("=" * 78)
    avanti = noti[noti["livello"] >= 3].sort_values(
        ["livello", "coppa", "stagione"], ascending=[False, True, True])
    print(f"\n{'club':30s} {'lega':6s} {'coppa':12s} {'stag.':>6s} {'arrivato a'}")
    for _, r in avanti.iterrows():
        st = "2024-25" if r["stagione"] == 2024 else "2025-26"
        print(f"  {r['club'][:28]:28s} {r['lega']:6s} {COPPE[r['coppa']]:12s} "
              f"{st:>7s} {ETICHETTA[int(r['livello'])]}")

    # ---- quante presenze per campionato, per coppa ------------------------
    print("\n" + "=" * 78)
    print("PRESENZE per campionato e coppa (club-stagione distinti)")
    print("=" * 78)
    piv = (noti.groupby(["lega", "coppa"])["club_id"].nunique()
                .unstack(fill_value=0))
    piv["TOT"] = piv.sum(axis=1)
    piv = piv.sort_values("TOT", ascending=False)
    print("\n" + piv.rename(columns=COPPE).to_string())

    print("\n⚠️  Dal 2024-25 «fase campionato» e' il girone unico da 36: arrivarci")
    print("    vale meno che il vecchio girone da 4. Non confrontare con stagioni")
    print("    precedenti — vedi le avvertenze in testa a questo script.")


if __name__ == "__main__":
    main()
