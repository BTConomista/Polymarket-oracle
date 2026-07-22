"""Probe diagnostico (Fase A, CACCIA_OU_2017_19.md): scarica via kagglehub una
lista di dataset candidati e stampa nel log — non committa nulla — colonne,
copertura stagionale e se esiste una coppia O/U 2.5 apertura/chiusura
DISTINTA per 2017-18/2018-19. Va lanciato dal runner GitHub Actions (rete
libera verso Kaggle, bloccata dalla sessione cloud, vedi MANUALE_SOPRAVVIVENZA.md).
"""
import sys

import kagglehub
import pandas as pd

CANDIDATES = [
    "mexwell/historical-football-resultsbetting-odds-data",
    "louischen7/football-results-and-betting-odds-data-of-epl",
    "thedevastator/uncovering-betting-patterns-in-the-premier-leagu",
    "eladsil/football-games-odds",
    "ahmadasadi00/football-betting-odds",
    "rayenjlassi/more-than-20k-footballsoccer-match",
]

DATE_HINTS = ["date", "Date", "match_date", "Datum"]
OU_HINTS = ["over", "under", "ou", "OU", "2.5", "O2.5", "U2.5", "total"]
OPEN_CLOSE_HINTS = ["open", "close", "Open", "Close", "OPEN", "CLOSE"]


def describe_csv(path):
    try:
        df = pd.read_csv(path, nrows=5000, low_memory=False)
    except Exception as e:
        print(f"    ! errore lettura {path}: {e}")
        return
    cols = list(df.columns)
    print(f"    colonne ({len(cols)}): {cols}")
    date_col = next((c for c in cols if any(h in c for h in DATE_HINTS)), None)
    if date_col:
        try:
            parsed = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
            print(f"    colonna data '{date_col}': range campione {parsed.min()} -> {parsed.max()}")
        except Exception as e:
            print(f"    ! errore parsing data: {e}")
    ou_cols = [c for c in cols if any(h in c for h in OU_HINTS)]
    print(f"    colonne O/U-like: {ou_cols}")
    oc_cols = [c for c in cols if any(h in c for h in OPEN_CLOSE_HINTS)]
    print(f"    colonne open/close-like: {oc_cols}")


def probe(slug):
    print(f"\n=== {slug} ===")
    try:
        path = kagglehub.dataset_download(slug)
    except Exception as e:
        print(f"  ! download fallito: {e}")
        return
    print(f"  scaricato in {path}")
    import os
    for root, _dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith(".csv"):
                full = os.path.join(root, f)
                size_mb = os.path.getsize(full) / 1e6
                print(f"  file: {f} ({size_mb:.1f} MB)")
                if size_mb > 200:
                    print("    ! troppo grande per il probe, salto la lettura")
                    continue
                describe_csv(full)


if __name__ == "__main__":
    targets = sys.argv[1:] or CANDIDATES
    for slug in targets:
        probe(slug)
