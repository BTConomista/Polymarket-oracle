#!/usr/bin/env python3
"""Posizioni e tiri di UN giocatore, da `files/tre_fonti_{lega}_2526/`.

Questo script e' l'esempio eseguibile del quaderno che lo contiene: ogni numero
citato in `README.md` e nei quattro capitoli esce da qui, e si ri-ottiene con

    python docs/esempio_heatmap_giocatori/heatmap_giocatore.py \
        --lega serie_a --giocatore "Donyell Malen"
    python docs/esempio_heatmap_giocatori/heatmap_giocatore.py \
        --lega premier_league --id 839956 --da-giornata 20

⚠️ Le due CONVENZIONI di coordinate del bundle sono diverse e la colonna si
chiama `X` in entrambi i file (vedi 01_convenzioni_e_trappole.md §1):

    heatmap.csv.gz   X = 0 porta PROPRIA  -> 100 porta AVVERSARIA (gia'
                     normalizzata per la direzione d'attacco)
    eventi.csv.gz    X = DISTANZA dalla porta avversaria (0 = linea di porta),
                     nella stessa scala 0-100 della lunghezza del campo

Percio' un tiro va portato nel frame della heatmap con `100 - X`. Mescolarle
mette i tiri nella meta' campo sbagliata senza che niente si lamenti: lo script
NON si fida e verifica entrambe le convenzioni prima di calcolare qualsiasi
cosa (`verifica_convenzioni`), fermandosi se non tornano.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RADICE = Path(__file__).resolve().parents[2]

# --- costanti di verifica -------------------------------------------------
# Il dischetto del rigore e' il punto di taratura gratuito: e' sempre nello
# stesso posto, in ogni lega e in ogni stagione. Se questi due numeri non
# tornano, la convenzione del file NON e' quella che crediamo.
RIGORE_X, RIGORE_Y = 11.5, 50.0
# X medio atteso per ruolo nella heatmap, in ordine crescente. Serve a
# smascherare una X invertita, che i rigori da soli non vedrebbero (il
# dischetto e' simmetrico rispetto a nulla, ma un rigore sta sempre a 11,5 m
# dalla porta: e' l'ORDINE dei ruoli che dice il verso).
ORDINE_RUOLI = ["G", "D", "M", "F"]

FASCIA = ["difesa profonda", "propria meta", "centrocampo basso",
          "centrocampo alto", "trequarti", "area e fondo"]
CORSIA = ["corsia sinistra", "centro-sinistra", "centro-destra", "corsia destra"]


def _leggi(lega: str, nome: str) -> pd.DataFrame:
    p = RADICE / "files" / f"tre_fonti_{lega}_2526" / nome
    if not p.exists():
        sys.exit(f"manca {p}\n(le leghe disponibili sono quelle con una cartella "
                 f"files/tre_fonti_*_2526/)")
    return pd.read_csv(p, encoding="utf-8-sig", low_memory=False)


def verifica_convenzioni(lega: str, hm: pd.DataFrame, tiri: pd.DataFrame,
                         giocatori: pd.DataFrame) -> dict:
    """Si ferma se le coordinate non sono quelle attese. Due controlli
    indipendenti, perche' uno solo non basta (vedi il docstring)."""
    esito = {}

    # 1 - la heatmap: X cresce verso la porta avversaria?
    ruoli = giocatori[["Giocatore", "Ruolo"]].drop_duplicates("Giocatore") \
        .set_index("Giocatore")["Ruolo"]
    medie = hm.assign(Ruolo=hm.Giocatore.map(ruoli)).groupby("Ruolo")["X"].mean()
    medie = medie.reindex(ORDINE_RUOLI).dropna()
    if not medie.is_monotonic_increasing:
        sys.exit(f"[{lega}] X della heatmap NON cresce da portiere ad attaccante: "
                 f"{medie.round(1).to_dict()}\nLa convenzione non e' quella attesa: "
                 f"fermati e guarda il file prima di calcolare qualsiasi cosa.")
    esito["X_media_per_ruolo"] = medie.round(1).to_dict()

    # 2 - i tiri: il dischetto del rigore e' dove deve essere?
    rig = tiri[tiri.Situazione == "penalty"]
    if len(rig) == 0:
        sys.exit(f"[{lega}] nessun rigore nei tiri: la taratura non e' verificabile.")
    mx, my = rig.X.mean(), rig.Y.mean()
    if abs(mx - RIGORE_X) > 0.2 or abs(my - RIGORE_Y) > 0.2:
        sys.exit(f"[{lega}] i {len(rig)} rigori cadono in (X {mx:.2f}, Y {my:.2f}) "
                 f"invece di ({RIGORE_X}, {RIGORE_Y}): la convenzione dei tiri e' "
                 f"cambiata, o stai leggendo il file sbagliato.")
    esito["rigori"] = {"n": int(len(rig)), "X": round(float(mx), 2), "Y": round(float(my), 2)}
    return esito


def seleziona(df: pd.DataFrame, nome: str | None, pid: int | None) -> pd.DataFrame:
    """SEMPRE per ID quando c'e'. Il nome NON e' un'identita': nell'archivio
    delle coppe europee convivono due `Haaland` (839956 Erling del Manchester
    City e 1126486 di SK Brann), e un filtro sul cognome li fonde in silenzio."""
    if pid is not None:
        return df[df["ID giocatore"] == pid]
    sel = df[df.Giocatore.str.contains(nome, na=False, case=False)]
    ids = sorted(int(i) for i in sel["ID giocatore"].dropna().unique())
    if len(ids) > 1:
        per_id = sel.groupby("ID giocatore")["Giocatore"].first()
        elenco = "\n".join(f"  --id {int(i):<8} {n}" for i, n in per_id.items())
        sys.exit(f"'{nome}' corrisponde a {len(ids)} giocatori diversi:\n{elenco}\n"
                 f"Il nome non basta a identificare: ri-lancia con --id.")
    return sel


def _giornata(serie: pd.Series) -> pd.Series:
    return serie.str.extract(r"(\d+)")[0].astype(int)


def analizza(lega: str, nome: str | None, pid: int | None,
             da_giornata: int | None, griglia=(120, 80), sigma=4.5) -> dict:
    hm_all = _leggi(lega, "heatmap.csv.gz")
    ev = _leggi(lega, "eventi.csv.gz")
    gioc = _leggi(lega, "giocatori.csv.gz")

    # ⚠️ una riga per tiro PER FONTE: SofaScore e Understat scrivono lo stesso
    # tiro con coordinate leggermente diverse. Senza questo filtro i tiri
    # raddoppiano (140 righe per i 70 tiri di Malen), e un dedup su
    # (data, minuto, X, Y) NON li unisce proprio perche' le X differiscono.
    tiri_all = ev[(ev.Categoria == "Tiro") & (ev.Fonte == "SofaScore")].copy()

    ver = verifica_convenzioni(lega, hm_all, tiri_all, gioc)

    hm = seleziona(hm_all, nome, pid).copy()
    ti = seleziona(tiri_all, nome, pid).copy()
    if hm.empty:
        sys.exit(f"nessuna posizione per questo giocatore in {lega}.")

    hm["gio"] = _giornata(hm.Turno)
    ti["gio"] = _giornata(ti.Turno)
    tutte_le_giornate = sorted(hm.gio.unique())
    if da_giornata is not None:
        hm = hm[hm.gio >= da_giornata]
        ti = ti[ti.gio >= da_giornata]

    X, Y = hm.X.to_numpy(float), hm.Y.to_numpy(float)
    n = len(X)

    # densita' lisciata, normalizzata sul PROPRIO massimo -> confronta le FORME.
    # Per l'intensita' serve un numero separato (posizioni per 90), perche' due
    # mappe normalizzate ognuna sul suo massimo non sono confrontabili in valore.
    from scipy.ndimage import gaussian_filter
    nx, ny = griglia
    H, _, _ = np.histogram2d(X, Y, bins=[nx, ny], range=[[0, 100], [0, 100]])
    G = gaussian_filter(H, sigma=(sigma, sigma), mode="constant")
    G = G / G.max()

    # zone a conteggio GREZZO: sono queste che si mostrano in un tooltip, mai
    # il valore della cella lisciata, che non e' una quantita' interpretabile.
    C, _, _ = np.histogram2d(X, Y, bins=[6, 4], range=[[0, 100], [0, 100]])

    # X del tiro E' GIA' la distanza dalla porta (convenzione diversa dalla
    # heatmap): qui serve cosi', senza il `100 - X` che occorre solo per
    # DISEGNARE i tiri nel frame della heatmap.
    dist = ti.X.to_numpy(float)
    larg = ti.Y.to_numpy(float)
    zone = {
        "terzo_offensivo": float((X >= 66.7).mean() * 100),
        "terzo_centrale": float(((X >= 33.3) & (X < 66.7)).mean() * 100),
        "terzo_difensivo": float((X < 33.3).mean() * 100),
        "area_avversaria": float(((X >= 83) & (Y >= 21) & (Y <= 79)).mean() * 100),
        "corsia_destra": float((Y >= 66.7).mean() * 100),
        "corsia_centrale": float(((Y >= 33.3) & (Y < 66.7)).mean() * 100),
        "corsia_sinistra": float((Y < 33.3).mean() * 100),
        "X_media": float(X.mean()), "Y_media": float(Y.mean()),
        "X_sd": float(X.std()), "Y_sd": float(Y.std()),
    }
    tiri_st = {} if ti.empty else {
        "n": int(len(ti)),
        "distanza_mediana_m": float(np.median(dist) / 100 * 105),
        "dentro_area_pct": float((dist / 100 * 105 <= 16.5).mean() * 100),
        "larghezza_sd_m": float((larg / 100 * 68).std()),
        "corridoio_centrale_pct": float(((larg >= 35.3) & (larg <= 64.7)).mean() * 100),
        "gol": int((ti.Esito == "goal").sum()),
        "xG": float(ti.xG.sum()),
    }
    return {
        "lega": lega, "giocatore": sorted(hm.Giocatore.unique()),
        "id": sorted(int(i) for i in hm["ID giocatore"].dropna().unique()),
        "squadra": sorted(hm.Squadra.unique()),
        "verifiche": ver,
        "punti": n, "gare": int(hm.Turno.nunique()),
        "giornate": sorted(int(g) for g in hm.gio.unique()),
        "giornate_totali_del_giocatore": [int(g) for g in tutte_le_giornate],
        "zone": zone, "tiri": tiri_st,
        "griglia": {"nx": nx, "ny": ny, "sigma": sigma,
                    "v": [round(float(v), 4) for v in G.T.ravel()]},
        "zone_grezze": [{"ix": ix, "iy": iy, "n": int(C[ix, iy]),
                         "pct": round(C[ix, iy] / n * 100, 1),
                         "fascia": FASCIA[ix], "corsia": CORSIA[iy]}
                        for iy in range(4) for ix in range(6)],
    }


def stampa(r: dict) -> None:
    print(f"\n{'='*66}\n{' / '.join(r['giocatore'])}  ·  {' / '.join(r['squadra'])}"
          f"  ·  {r['lega']}\n{'='*66}")
    print(f"ID {r['id']}   {r['punti']} posizioni su {r['gare']} partite")
    print(f"giornate: {r['giornate'][0]}-{r['giornate'][-1]} "
          f"({len(r['giornate'])} presenze)")
    mancanti = sorted(set(range(r['giornate'][0], r['giornate'][-1] + 1)) - set(r['giornate']))
    if mancanti:
        print(f"  ⚠️ senza posizioni dentro la finestra: giornate {mancanti} "
              f"(non e' un buco della raccolta: non e' andato in campo)")
    print(f"\nverifiche di convenzione superate:")
    print(f"  X media per ruolo : {r['verifiche']['X_media_per_ruolo']}")
    print(f"  rigori            : n={r['verifiche']['rigori']['n']}, "
          f"X={r['verifiche']['rigori']['X']}, Y={r['verifiche']['rigori']['Y']}")
    z = r["zone"]
    print(f"\nzone (% delle posizioni)")
    for k in ["terzo_offensivo", "terzo_centrale", "terzo_difensivo", "area_avversaria",
              "corsia_destra", "corsia_centrale", "corsia_sinistra"]:
        print(f"  {k:18s} {z[k]:6.1f}")
    print(f"  {'X media':18s} {z['X_media']:6.1f}   (0 porta propria, 100 avversaria)")
    print(f"  {'Y media':18s} {z['Y_media']:6.1f}   (50 = centro)")
    print(f"  {'X sd':18s} {z['X_sd']:6.1f}   escursione verticale")
    if r["tiri"]:
        t = r["tiri"]
        print(f"\ntiri ({t['n']}, sole righe SofaScore)")
        print(f"  distanza mediana        {t['distanza_mediana_m']:6.1f} m")
        print(f"  dentro l'area           {t['dentro_area_pct']:6.1f} %")
        print(f"  dispersione in larghezza{t['larghezza_sd_m']:6.1f} m")
        print(f"  corridoio centrale      {t['corridoio_centrale_pct']:6.1f} %")
        print(f"  gol {t['gol']}  ·  xG {t['xG']:.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lega", default="serie_a")
    ap.add_argument("--giocatore", help="nome (parziale). Se e' ambiguo lo script si ferma")
    ap.add_argument("--id", type=int, dest="pid", help="ID giocatore: da preferire SEMPRE")
    ap.add_argument("--da-giornata", type=int, help="finestra: dalla giornata N in poi")
    ap.add_argument("--json", type=Path, help="dove scrivere il risultato completo")
    a = ap.parse_args()
    if not a.giocatore and a.pid is None:
        ap.error("serve --giocatore o --id")
    r = analizza(a.lega, a.giocatore, a.pid, a.da_giornata)
    stampa(r)
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(r))
        print(f"\nscritto {a.json}")


if __name__ == "__main__":
    main()
