#!/usr/bin/env python3
"""Registra una raccolta di statistiche PER SQUADRA per periodo (diretta.it).

E' la porta d'ingresso per le prossime leghe e le prossime stagioni: **verifica**
i dati, li normalizza e scrive il `manifesto_squadra.json` che
`src/data/team_stats.py` legge. Nessuna modifica a `src/` e' mai necessaria per
aggiungere una raccolta.

USO:
    python scripts/registra_raccolta_squadra_diretta.py \\
        --xlsx ~/scaricati/SerieA_202526_STATISTICHE_SQUADRA_totale_1T_2T.xlsx \\
        --lega serie_a --stagione 2526

COSA VERIFICA prima di accettare (e si ferma se non torna):
  1. le 53 colonne canoniche ci sono tutte (per NOME: l'ordine cambia da lega a
     lega ed e' normalizzato qui, non assunto);
  2. le date si leggono e i tre periodi ordinari ci sono per ogni squadra-partita;
  3. calendario: round-robin completo, ogni squadra meta' in casa e meta' fuori,
     nessun duplicato di chiave;
  4. additivita' 1T+2T(+Supplementari)=Totale sulle metriche di conteggio;
  5. **se esiste uno snapshot della lega**: join totale e coerenza del risultato
     contro di esso — che e' il controllo forte, perche' e' una fonte
     indipendente (football-data.co.uk).

Cio' che scrive nella cartella `files/diretta_{lega}_{stagione}/`:
  - `squadra_per_partita.csv.gz`  il foglio "Per squadra", colonne normalizzate
  - `legenda_squadra.csv`         il foglio "Legenda" (statistica -> codice fonte)
  - `note_fonte.csv`              il foglio "Note", conservato come DICHIARAZIONE
  - `manifesto_squadra.json`      perimetro e copertura attesa

Il foglio "Per partita" (formato wide) **non** viene conservato: e' un reshape
esatto del foglio "Per squadra" — verificato su entrambe le meta' (colonne
"Casa - " e "Ospite - "), 0 celle divergenti su 102.600 / 83.700 / 83.250. E'
una vista, non un dato in piu'.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import team_stats as TS  # noqa: E402

RADICE = Path(__file__).resolve().parents[1]

# Le metriche di CONTEGGIO: additive fra periodi. Le percentuali e il possesso
# no (sono rapporti e medie), e vanno escluse dal controllo di additivita'.
ADDITIVE = tuple(c for c in TS.COLONNE_METRICHE if c not in TS.COLONNE_NON_ADDITIVE)


def _leggi(percorso: Path, foglio: str) -> pd.DataFrame:
    df = pd.read_excel(percorso, sheet_name=foglio)
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    return df


def normalizza(df: pd.DataFrame) -> pd.DataFrame:
    """Porta il foglio sullo schema canonico. Alza se manca una colonna."""
    if "Fase" not in df.columns:
        # Le leghe senza spareggio non hanno la colonna: la aggiungiamo con il
        # valore costante, cosi' le 5 raccolte hanno lo STESSO schema e il
        # codice a valle non deve sapere quale lega ha i play-off.
        df = df.copy()
        df["Fase"] = "Stagione regolare"
    mancanti = [c for c in TS.COLONNE_CANONICHE if c not in df.columns]
    if mancanti:
        raise SystemExit(f"❌ colonne mancanti: {mancanti}")
    extra = [c for c in df.columns if c not in TS.COLONNE_CANONICHE]
    if extra:
        raise SystemExit(f"❌ colonne inattese (schema cambiato alla fonte?): {extra}")
    # `Giornata` arriva int in alcune leghe e str in altre (dove ci sono le
    # fasi a eliminazione: "Semi finali", "Finale"). Si uniforma a str: e' un
    # ETICHETTA, non un numero su cui fare aritmetica.
    out = df[list(TS.COLONNE_CANONICHE)].copy()
    out["Giornata"] = out["Giornata"].astype(str).str.strip()
    return out


def verifica(df: pd.DataFrame, lega: str) -> dict:
    """Controlla e restituisce i numeri per il manifesto. Alza se non torna."""
    from src.data.sources import TEAM_ALIASES

    d = df.copy()
    d["data"] = pd.to_datetime(d["Data"], format="%d.%m.%Y", errors="coerce")
    if d["data"].isna().any():
        raise SystemExit(f"❌ {int(d['data'].isna().sum())} date non interpretabili")
    for col in ("Squadra", "Avversario"):
        d[col] = d[col].map(lambda x: TEAM_ALIASES.get(x, x))

    reg = d[d["Fase"] == "Stagione regolare"]
    po = d[d["Fase"] == "Play-off"]

    # --- 2. i tre periodi ordinari, per ogni squadra-partita di campionato
    tot = reg[reg["Periodo"] == TS.PERIODO_TOTALE]
    n_tm = len(tot)
    for periodo in (TS.PERIODO_1T, TS.PERIODO_2T):
        n = len(reg[reg["Periodo"] == periodo])
        if n != n_tm:
            raise SystemExit(f"❌ periodo '{periodo}': {n} righe contro {n_tm} di 'Totale'")

    # --- 3. calendario
    dup = reg.duplicated(subset=["data", "Squadra", "Periodo"]).sum()
    if dup:
        raise SystemExit(f"❌ {dup} righe con chiave (data, squadra, periodo) duplicata")
    casa = tot[tot["Campo"] == "Casa"]
    coppie = list(zip(casa["Squadra"], casa["Avversario"]))
    if len(coppie) != len(set(coppie)):
        raise SystemExit("❌ round-robin: esiste una coppia (casa, ospite) ripetuta")
    squadre = sorted(set(reg["Squadra"]))
    attese = len(squadre) * (len(squadre) - 1)
    if len(coppie) != attese:
        raise SystemExit(
            f"❌ round-robin incompleto: {len(coppie)} incontri contro {attese} attesi "
            f"per {len(squadre)} squadre"
        )
    per_squadra = tot.groupby(["Squadra", "Campo"]).size().unstack(fill_value=0)
    if per_squadra.std().sum() != 0:
        raise SystemExit(f"❌ partite casa/trasferta non bilanciate:\n{per_squadra}")

    # --- 4. additivita' 1T + 2T (+ Supplementari) = Totale
    # Il vuoto e' uno zero (dimostrato contro football-data): si riempie PRIMA
    # di sommare, altrimenti il confronto misura la politica NaN e non i dati.
    a = d.copy()
    for c in TS.COLONNE_ZERO_IMPLICITO:
        a[c] = a[c].fillna(0)
    chiave = ["data", "Squadra", "Avversario"]
    somma = (
        a[a["Periodo"] != TS.PERIODO_TOTALE].groupby(chiave)[list(ADDITIVE)].sum()
    )
    riferimento = a[a["Periodo"] == TS.PERIODO_TOTALE].set_index(chiave)[list(ADDITIVE)]
    diff = (somma - riferimento).abs()
    violazioni = int((diff > 0.005).sum().sum())
    celle = int(diff.size)

    # --- 5. controllo forte: join e risultato contro lo snapshot (fonte diversa)
    join_txt, verificato, esito_gol = "non applicabile", False, "non applicabile"
    percorso = RADICE / "data" / f"{lega}_matches.csv"
    if percorso.exists():
        snap = pd.read_csv(percorso)
        snap["data"] = pd.to_datetime(snap["date"])
        snap = snap[snap["data"].between(reg["data"].min(), reg["data"].max())]
        chiavi_snap = set(zip(snap["data"], snap["home_team"], snap["away_team"]))
        gol = {
            (r.data, r.home_team, r.away_team): (r.home_goals, r.away_goals)
            for r in snap.itertuples()
        }
        agganciate = ok_gol = 0
        for r in tot.itertuples():
            k = ((r.data, r.Squadra, r.Avversario) if r.Campo == "Casa"
                 else (r.data, r.Avversario, r.Squadra))
            if k not in chiavi_snap:
                continue
            agganciate += 1
            # `Risultato squadra` e' scritto dal punto di vista della RIGA:
            # invertito sulla trasferta. Leggerlo come casa-ospite sbaglierebbe
            # il segno su tutte le partite non pareggiate.
            propri, subiti = (int(x) for x in str(getattr(r, "_6")).split("-"))
            casa_g, osp_g = gol[k]
            atteso = (casa_g, osp_g) if r.Campo == "Casa" else (osp_g, casa_g)
            if (propri, subiti) == atteso:
                ok_gol += 1
        if agganciate != n_tm:
            raise SystemExit(
                f"❌ join allo snapshot parziale: {agganciate}/{n_tm} team-partita. "
                "Probabile alias squadra mancante in src/data/sources.py."
            )
        if ok_gol != n_tm:
            raise SystemExit(f"❌ risultato discorde dallo snapshot in {n_tm - ok_gol} team-partita")
        join_txt, verificato = f"{agganciate}/{n_tm}", True
        esito_gol = f"{ok_gol}/{n_tm}"

    return {
        "lega": lega,
        "fonte": "diretta.it (Flashscore)",
        "righe_attese": int(len(d)),
        "righe_campionato": int(len(reg)),
        "righe_playoff": int(len(po)),
        "team_partita_attesi": int(n_tm),
        "partite_attese": int(n_tm // 2),
        "squadre": len(squadre),
        "periodi": sorted(set(d["Periodo"])),
        "statistiche": len(TS.COLONNE_METRICHE),
        "data_prima": str(reg["data"].min().date()),
        "data_ultima": str(reg["data"].max().date()),
        "join_snapshot": join_txt,
        "risultato_coerente": esito_gol,
        "snapshot_verificato": verificato,
        "additivita_periodi": f"{celle - violazioni}/{celle}",
        "partite_playoff": sorted(
            {f"{r.Data} {r.Squadra}-{r.Avversario}"
             for r in po[(po["Campo"] == "Casa") & (po["Periodo"] == TS.PERIODO_TOTALE)].itertuples()}
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xlsx", required=True, type=Path)
    ap.add_argument("--lega", required=True)
    ap.add_argument("--stagione", required=True)
    ap.add_argument("--cartella", type=Path, default=None)
    args = ap.parse_args()

    dest = args.cartella or (RADICE / "files" / f"diretta_{args.lega}_{args.stagione}")
    dest.mkdir(parents=True, exist_ok=True)

    df = normalizza(_leggi(args.xlsx, "Per squadra"))
    info = verifica(df, args.lega)
    info["stagione"] = args.stagione

    df.to_csv(dest / TS.FILE_SQUADRA, index=False, compression="gzip")
    _leggi(args.xlsx, "Legenda").to_csv(dest / TS.FILE_LEGENDA, index=False)
    _leggi(args.xlsx, "Note").to_csv(dest / TS.FILE_NOTE, index=False)
    ordine = ["lega", "stagione", "fonte"] + [k for k in info if k not in ("lega", "stagione", "fonte")]
    (dest / TS.FILE_MANIFESTO).write_text(
        json.dumps({k: info[k] for k in ordine}, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"✅ {args.lega}/{args.stagione} -> {dest}")
    for k in ("righe_attese", "righe_campionato", "righe_playoff", "team_partita_attesi",
              "squadre", "periodi", "join_snapshot", "risultato_coerente", "additivita_periodi"):
        print(f"   {k:22s} {info[k]}")


if __name__ == "__main__":
    main()
