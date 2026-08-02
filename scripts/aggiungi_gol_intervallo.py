#!/usr/bin/env python3
"""Aggiunge agli snapshot i GOL ALL'INTERVALLO (`home_goals_ht`, `away_goals_ht`).

PERCHE'. Il progetto ha un residuo aperto e localizzato (Fasi 96/99, pista
6-bis): il secondo tempo e' mal calibrato mentre il primo no, quindi serve un
modello a **due stadi** — primo tempo indipendente, secondo tempo **condizionato
al punteggio dell'intervallo**. Quel punteggio pero' non era in nessuna tabella:
`data/*_matches.csv` non ha colonne di primo tempo, e la Fase 98 lo rileggeva
ogni volta dai grezzi, in tre modi diversi a seconda della lega. Le statistiche
di squadra della Fase 131 non lo contengono nemmeno loro (`Risultato squadra` e'
il risultato FINALE anche sulla riga «1° tempo», regola R8).

COSA FA. Prende `HTHG`/`HTAG` da **football-data.co.uk** — la stessa fonte da cui
gli snapshot derivano gia' i gol finali, quindi non e' un innesto di terzi — e li
scrive come due colonne nuove. **Nessuna cella esistente viene toccata**: e'
un'aggiunta, non una correzione (regola R3, che vale per le modifiche).

⚠️ **DALLA FASE 137 QUESTO SCRIPT NON E' PIU' LA FONTE DELLE DUE COLONNE.** Le
produce `loader._normalize`, dentro la pipeline di produzione, dalla stessa riga
grezza da cui prende i gol finali. Il motivo e' un difetto vero: questo script
scrive sugli snapshot GIA' FATTI, quindi correggeva una volta sola — un solo
`build_database.py --refresh` avrebbe ricostruito lo snapshot da zero e
cancellato le due colonne. Verificato che i due percorsi coincidono:
**32.222/32.222 celle identiche** sulle 5 leghe.

Resta utile per cio' che il loader non fa: **ricontrollare** uno snapshot gia'
scritto contro la fonte, con i quattro controlli qui sotto e il conto della
frazione di gol nel primo tempo. Con `--dry-run` non scrive nulla.

DA DOVE, lega per lega (i tre regimi gia' in essere, `docs/DATI.md` §4):
  - Serie A            -> `data/football_data_raw/` (CSV grezzi versionati)
  - Premier / La Liga  -> `files/football_data_*_bundle.json` (bundle congelati)
  - Bundesliga / Ligue 1 -> scaricati (non hanno fonte grezza congelata in repo),
    con cache in `data/fonti/` come fa gia' `scripts/fetch_sources.py`

COSA VERIFICA prima di scrivere (e si ferma se non torna):
  1. join (data + squadre) **totale** contro lo snapshot;
  2. `FTHG`/`FTAG` della fonte == `home_goals`/`away_goals` dello snapshot —
     e' il controllo che dimostra di aver agganciato la riga GIUSTA, non una
     riga qualsiasi che combacia per data;
  3. `HTHG <= FTHG` e `HTAG <= FTAG` su ogni riga (un intervallo non puo' avere
     piu' gol del finale);
  4. nessun NaN nelle due colonne nuove.

USO:
    python scripts/aggiungi_gol_intervallo.py            # tutte e 5 le leghe
    python scripts/aggiungi_gol_intervallo.py --lega serie_a --dry-run
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import database  # noqa: E402
from src.data.sources import LEAGUES, TEAM_ALIASES, csv_url  # noqa: E402

RADICE = Path(__file__).resolve().parents[1]
CACHE = RADICE / "data" / "fonti"
STAGIONI = ("1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526")
COLONNE = ("home_goals_ht", "away_goals_ht")


def _parse(testo: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(testo), encoding_errors="replace")
    # il BOM arriva in due travestimenti a seconda di come il testo e' stato
    # salvato: come carattere U+FEFF o come il suo mojibake latin-1
    df.columns = [str(c).replace("﻿", "").replace("ï»¿", "").strip() for c in df.columns]
    return df.dropna(subset=["HomeTeam"])


def _grezzi(lega: str) -> pd.DataFrame:
    """I CSV football-data della lega, da dove sono (tre regimi diversi)."""
    pezzi = []
    if lega == "serie_a":
        for s in STAGIONI:
            p = RADICE / "data" / "football_data_raw" / f"serie_a_{s}.csv"
            pezzi.append(_parse(p.read_text(encoding="latin-1")))
    elif lega in ("premier_league", "la_liga"):
        bundle = json.loads((RADICE / "files" / f"football_data_{lega}_bundle.json").read_text())
        for k in sorted(bundle):
            pezzi.append(_parse(bundle[k]))
    else:
        # Bundesliga e Ligue 1 non hanno fonte grezza congelata: si scaricano,
        # con cache su disco perche' rifarlo a ogni esecuzione e' inutile.
        CACHE.mkdir(parents=True, exist_ok=True)
        for s in STAGIONI:
            p = CACHE / f"{lega}_{s}.csv"
            if not p.exists():
                url = csv_url(s, LEAGUES[lega])
                with urllib.request.urlopen(url, timeout=60) as r:
                    p.write_bytes(r.read())
            pezzi.append(_parse(p.read_text(encoding="latin-1")))
    df = pd.concat(pezzi, ignore_index=True)
    df["data"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True)
    for col in ("HomeTeam", "AwayTeam"):
        df[col] = df[col].map(lambda x: TEAM_ALIASES.get(x, x))
    return df


def _divergenze_dichiarate(lega: str) -> set:
    """Le partite in cui il progetto diverge DAPPOSTA da football-data.

    Regola R1: lo snapshot porta il risultato del CAMPO, non quello del
    tribunale sportivo. Dove una correzione del genere e' stata applicata, i
    gol finali NON coincidono con la fonte, ed e' corretto cosi'. L'elenco si
    legge dal registro (`data/correzioni_dichiarate.csv`), non si incide qui:
    se un domani ne comparisse un'altra, questo script la conosce gia'.
    """
    reg = RADICE / "data" / "correzioni_dichiarate.csv"
    if not reg.exists():  # pragma: no cover
        return set()
    d = pd.read_csv(reg)
    d = d[(d["league"] == lega) & (d["stato"] == "applicata")
          & (d["colonna"].isin(["home_goals", "away_goals"]))]
    return {
        (pd.Timestamp(r.date), r.home_team, r.away_team) for r in d.itertuples()
    }


def aggiungi(lega: str, dry_run: bool = False) -> dict:
    percorso = database.snapshot_path(lega)
    snap = pd.read_csv(percorso)
    snap["data_dt"] = pd.to_datetime(snap["date"])

    fd = _grezzi(lega)
    ref = {
        (r.data, r.HomeTeam, r.AwayTeam): (r.FTHG, r.FTAG, r.HTHG, r.HTAG)
        for r in fd.itertuples()
    }

    attese = _divergenze_dichiarate(lega)

    ht_h, ht_a, orfane, gol_discordi, impossibili, senza_ht = [], [], 0, 0, 0, []
    for r in snap.itertuples():
        v = ref.get((r.data_dt, r.home_team, r.away_team))
        if v is None:
            orfane += 1
            ht_h.append(None)
            ht_a.append(None)
            continue
        fthg, ftag, hthg, htag = v
        # controllo 2: e' la riga GIUSTA? i gol finali devono coincidere.
        # ⚠️ Tranne dove il progetto ha DICHIARATO di divergere apposta dalla
        # fonte: la regola R1 tiene il risultato del CAMPO, non quello del
        # tribunale sportivo. Quelle divergenze non si scoprono qui, si leggono
        # dal registro delle correzioni — cosi' l'eccezione non e' incisa nel
        # codice e resta una sola (Union Berlin-Bochum 14/12/2024).
        if int(fthg) != int(r.home_goals) or int(ftag) != int(r.away_goals):
            if (r.data_dt, r.home_team, r.away_team) not in attese:
                gol_discordi += 1
        # controllo 3: l'intervallo non puo' superare il finale
        if pd.notna(hthg) and pd.notna(htag) and (hthg > fthg or htag > ftag):
            impossibili += 1
        if pd.isna(hthg) or pd.isna(htag):
            # la fonte non ha l'intervallo per questa partita: NaN dichiarato,
            # mai inventato (R3). Un buco dichiarato e' innocuo; il finto
            # pieno no (R6).
            senza_ht.append(f"{r.date} {r.home_team}-{r.away_team}")
            ht_h.append(pd.NA)
            ht_a.append(pd.NA)
            continue
        ht_h.append(int(hthg))
        ht_a.append(int(htag))

    if orfane:
        raise SystemExit(
            f"❌ {lega}: {orfane}/{len(snap)} partite dello snapshot non agganciate "
            "alla fonte. Probabile alias mancante in src/data/sources.py."
        )
    if gol_discordi:
        raise SystemExit(
            f"❌ {lega}: {gol_discordi} partite con gol finali discordi fra snapshot e "
            "fonte: il join aggancia righe sbagliate, non scrivo nulla."
        )
    if impossibili:
        raise SystemExit(f"❌ {lega}: {impossibili} partite con gol all'intervallo > finale")

    snap = snap.drop(columns=["data_dt"])
    # Int64 (nullable): una partita su 16.111 non ha l'intervallo alla fonte e
    # deve poter restare vuota senza diventare un float o uno zero finto.
    snap["home_goals_ht"] = pd.array(ht_h, dtype="Int64")
    snap["away_goals_ht"] = pd.array(ht_a, dtype="Int64")
    if int(snap[list(COLONNE)].isna().any(axis=1).sum()) != len(senza_ht):
        raise SystemExit(f"❌ {lega}: NaN non dichiarati nelle colonne nuove")

    esito = {
        "lega": lega,
        "partite": len(snap),
        "join": f"{len(snap) - orfane}/{len(snap)}",
        "gol_finali_coerenti": f"{len(snap) - gol_discordi}/{len(snap)}",
        "gol_1t_totali": int(snap["home_goals_ht"].sum() + snap["away_goals_ht"].sum()),
        "gol_totali": int(snap["home_goals"].sum() + snap["away_goals"].sum()),
        "senza_intervallo": senza_ht,
        "divergenze_R1_attese": len(attese),
    }
    esito["frazione_1t"] = round(esito["gol_1t_totali"] / esito["gol_totali"], 4)
    if not dry_run:
        snap.to_csv(percorso, index=False)
    return esito


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lega", default=None, choices=sorted(LEAGUES))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    leghe = [args.lega] if args.lega else sorted(LEAGUES)
    tot_1t = tot = 0
    for lega in leghe:
        e = aggiungi(lega, args.dry_run)
        tot_1t += e["gol_1t_totali"]
        tot += e["gol_totali"]
        print(f"{'(dry) ' if args.dry_run else '✅ '}{e['lega']:15s} "
              f"partite {e['partite']:5d} | join {e['join']:>11s} | "
              f"gol finali coerenti {e['gol_finali_coerenti']:>11s} | "
              f"gol 1T {e['gol_1t_totali']:5d}/{e['gol_totali']:5d} = f {e['frazione_1t']}")
        for x in e["senza_intervallo"]:
            print(f"      ⚠️ senza intervallo alla fonte (NaN dichiarato): {x}")
    if len(leghe) > 1:
        print(f"\n   frazione di gol nel 1° tempo, 5 leghe: f = {tot_1t/tot:.4f}  "
              f"({tot_1t}/{tot})")
        print("   ⚠️ confronto: la Fase 96 misurava f = 0.4396 [0.4338, 0.4458] su 3 leghe")


if __name__ == "__main__":
    main()
