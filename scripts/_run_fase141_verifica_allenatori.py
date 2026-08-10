"""La verifica esterna degli allenatori: TUTTI i numeri della fase (Fase 141).

Ogni cifra citata nel diario e nel README per questa fase esce da qui. Non è un
backtest: è il verbale di un confronto fra due fonti indipendenti sulla stessa
domanda — *chi era in carica in quel momento*.

LE QUATTRO DOMANDE.

1. **Copertura del ponte** — quanti club e quanti allenatori si agganciano a
   Wikidata, e per quale via (lato club `P286`, lato persona `P6087`).
2. **Accordo** — quanti dei nostri 1.190 mandati la fonte esterna conferma, e
   quanti no, divisi per *tipo* di disaccordo. ⚠️ Un disaccordo non è un
   errore nostro finché non si guarda: `assente_da_wikidata` significa che la
   fonte tace, non che noi sbagliamo.
3. **Identità** — le chiavi-nome che risolvono a più di un Q-id. È la domanda
   che la Fase 140 poteva solo dichiarare.
4. **I sandwich** — dei 62 casi `A→X→A` della Fase 140, quanti il confronto
   automatico chiude e quanti restano.

USO:
    python scripts/_run_fase141_verifica_allenatori.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import allenatori as A                      # noqa: E402

WD = ROOT / "data" / "allenatori_wikidata"
DEST = ROOT / "experiments" / "fase141_verifica_allenatori.json"


def _leggi(nome: str) -> pd.DataFrame:
    p = WD / nome
    if not p.exists():
        print(f"⚠️  manca {p.relative_to(ROOT)} — esegui prima "
              f"scripts/aggancia_allenatori_wikidata.py")
        return pd.DataFrame()
    return pd.read_csv(p)


def main() -> None:
    club = _leggi("club_qid.csv")
    lato_club = _leggi("mandati_wikidata.csv")
    persone = _leggi("persone_qid.csv")
    lato_pers = _leggi("mandati_persona.csv")
    conf = _leggi("confronto.csv")
    if conf.empty:
        sys.exit(1)

    print("=" * 72)
    print("1 · IL PONTE VERSO WIKIDATA")
    print("=" * 72)
    risolti = int((club.stato == "risolto").sum())
    print(f"  club agganciati            {risolti}/{len(club)}")
    print(f"  club con storia P286 vuota {int((club.mandati_p286 == 0).sum())}")
    print(f"  mandati dal lato CLUB      {len(lato_club)} "
          f"({lato_club.manager_qid.nunique() if len(lato_club) else 0} allenatori, "
          f"{lato_club.club_id.nunique() if len(lato_club) else 0} club)")
    if len(lato_club):
        per_club = lato_club.groupby("club_id").size()
        print(f"    per club: mediana {per_club.median():.0f}, "
              f"min {per_club.min()}, max {per_club.max()} "
              f"— ⚠️ la copertura NON è uniforme, e un'assenza non è una smentita")
        complete = int((lato_club.wd_da.notna() & lato_club.wd_a.notna()).sum())
        print(f"    con entrambe le date: {complete}/{len(lato_club)}")
        if "prec_da" in lato_club:
            gr = (lato_club.prec_da.value_counts(dropna=False)
                  .rename({11.0: "giorno", 10.0: "mese", 9.0: "anno"}))
            print(f"    precisione data d'inizio: {gr.to_dict()}")
    if len(persone):
        print(f"  allenatori agganciati      "
              f"{int((persone.stato == 'risolto').sum())}/{len(persone)}")
        print("    stati:", persone.stato.value_counts().to_dict())
        print(f"  mandati dal lato PERSONA   {len(lato_pers)}")

    print()
    print("=" * 72)
    print("2 · ACCORDO SUI NOSTRI MANDATI")
    print("=" * 72)
    conf["confermato"] = conf.verdetto.str.startswith("confermato")
    print(f"  mandati confrontati: {len(conf)}")
    for v, n in conf.verdetto.value_counts().items():
        print(f"    {v:22s} {n:5d}  ({100*n/len(conf):5.1f}%)")
    print(f"  ACCORDO TOTALE: {int(conf.confermato.sum())}/{len(conf)} "
          f"({100*conf.confermato.mean():.1f}%)")
    print(f"  conferme per lato: {conf[conf.confermato].lato.value_counts().to_dict()}")
    # il peso in PARTITE, non in mandati: un mandato lungo non vale come un
    # traghettatore di una gara, e il conteggio per mandati lo nasconde
    print(f"\n  in PARTITE: {int(conf[conf.confermato].partite.sum())}/"
          f"{int(conf.partite.sum())} "
          f"({100*conf[conf.confermato].partite.sum()/conf.partite.sum():.1f}%) "
          f"— il residuo pesa meno in partite che in mandati perché è fatto "
          f"soprattutto di mandati brevi")
    print("\n  mediana di partite per verdetto:")
    print(conf.groupby("verdetto")["partite"].agg(["count", "median", "sum"])
          .to_string(header=["mandati", "mediana", "partite"]))

    print()
    print("=" * 72)
    print("3 · IDENTITÀ — le chiavi-nome con più di un Q-id")
    print("=" * 72)
    con_qid = conf[conf.manager_qid.notna()]
    multi = (con_qid.groupby("manager_key")["manager_qid"].nunique())
    multi = multi[multi > 1]
    print(f"  chiavi con più di un Q-id: {len(multi)}")
    dettaglio = {}
    for k in multi.index:
        righe = (con_qid[con_qid.manager_key == k][["manager_qid", "club"]]
                 .drop_duplicates())
        dettaglio[k] = [{"qid": q, "club": c} for q, c in
                        righe.itertuples(index=False)]
        for q, c in righe.itertuples(index=False):
            print(f"    {k:22s} {q:12s} {c}")
    print("\n  ⚠️ Due Q-id NON dimostrano due persone: possono anche essere un "
          "\n     duplicato di Wikidata. È un disaccordo della fonte con sé "
          "stessa,\n     e va sciolto caso per caso.")

    print()
    print("=" * 72)
    print("4 · I SANDWICH A→X→A DELLA FASE 140")
    print("=" * 72)
    s = conf[conf.interruzione]
    print(f"  mandati marcati interruzione: {len(s)}")
    print(f"    chiusi dal confronto automatico: {int(s.confermato.sum())}")
    print(f"    ancora aperti                  : {int((~s.confermato).sum())}")
    print("\n  come si distribuiscono i loro verdetti:")
    print(s.verdetto.value_counts().to_string())
    esempi = s[s.verdetto == "nome_diverso"].head(8)
    if len(esempi):
        print("\n  esempi già risolti dalla fonte (chi era DAVVERO in carica):")
        for _, r in esempi.iterrows():
            print(f"    {r.club:26s} noi «{r.allenatore}» ({r.partite}g) "
                  f"→ Wikidata: {r.nota}")

    residuo = conf[~conf.confermato]
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "fase": 141,
        "ponte": {
            "club_totali": int(len(club)), "club_risolti": risolti,
            "club_senza_p286": int((club.mandati_p286 == 0).sum()),
            "mandati_lato_club": int(len(lato_club)),
            "allenatori_lato_club": int(lato_club.manager_qid.nunique()) if len(lato_club) else 0,
            "allenatori_totali": int(len(persone)) if len(persone) else None,
            "allenatori_risolti": int((persone.stato == "risolto").sum()) if len(persone) else None,
            "mandati_lato_persona": int(len(lato_pers)),
        },
        "accordo": {
            "mandati": int(len(conf)),
            "confermati": int(conf.confermato.sum()),
            "quota": round(float(conf.confermato.mean()), 4),
            "per_verdetto": conf.verdetto.value_counts().to_dict(),
            "per_lato": conf[conf.confermato].lato.value_counts().to_dict(),
            "partite_confermate": int(conf[conf.confermato].partite.sum()),
            "partite_totali": int(conf.partite.sum()),
        },
        "identita": {"chiavi_multi_qid": len(multi), "dettaglio": dettaglio},
        "sandwich": {
            "totali": int(len(s)),
            "chiusi": int(s.confermato.sum()),
            "aperti": int((~s.confermato).sum()),
            "per_verdetto": s.verdetto.value_counts().to_dict(),
        },
        "residuo": {"mandati": int(len(residuo)),
                    "partite": int(residuo.partite.sum())},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
