"""Integra i calendari di coppa recuperati da Wikipedia nei calendari di club,
e ricalcola le colonne di congestione derivate (Fase 103).

PERCHE' ESISTE. La Fase 100 (docs/audit_5_leghe/numeri/caccia_calendari.md) ha
trovato 3.045 righe di calendario mancanti da openfootball (Europa/Conference
League 2025-26 su tutte e 5 le leghe, DFB-Pokal/Copa del Rey/Coupe de France a
copertura parziale, supercoppe e Mondiale per club mai modellati) e le ha
raccolte da Wikipedia in data/ricerca_esterna/fixtures_*.csv, verificate
contro una terza fonte indipendente (openligadb.de: 0 righe su 114 non
confermate). Non erano mai state applicate: la regola R4 di quel cantiere
imponeva di non toccare snapshot/src/scripts, solo produrre report + dati
grezzi. Questo script chiude quel lavoro: applica il recupero e chiude i
1.603 falsi zero di midweek_europe dichiarati in
data/estimates/celle_residue.csv (caso D), citati anche in CLAUDE.md (regola
R6) e docs/DATI.md (§1-bis).

COSA FA, per ciascuna delle 5 leghe:
  1. unisce data/ricerca_esterna/fixtures_<lega>_*.csv al calendario di club
     esistente (club_fixtures[_<lega>].csv), con lo stesso dedup usato da
     fixtures.build_club_fixtures: subset=(season, team, date, competition,
     opponent);
  2. ricalcola home/away_rest_days_full e home/away_midweek_europe
     (fixtures.add_rest_days_full) sullo snapshot congelato della lega;
  3. VERIFICA il risultato contro l'oracolo gia' pubblicato in
     data/estimates/celle_residue.csv (citato in CLAUDE.md/DATI.md): il
     numero di celle midweek che passano da 0 a 1 e il numero di partite con
     riposo cambiato devono combaciare ESATTAMENTE lega per lega, e nessuna
     cella deve regredire (1->0, o riposo che aumenta rispetto a prima) —
     altrimenti lo script si ferma e non scrive NULLA (nemmeno per le leghe
     che avrebbero combaciato): e' una verifica-poi-applica in un unico blocco,
     non lega per lega, cosi' un'integrazione parziale non lascia il repo in
     uno stato a meta'.
  4. solo se OGNI lega supera tutti i controlli: scrive club_fixtures*.csv e
     gli snapshot aggiornati.

Non serve un registro correzioni per-cella (data/correzioni_dichiarate.csv,
regola R3): le 4 colonne toccate sono dato DERIVATO da una pipeline
deterministica (fixtures.add_rest_days_full), non un valore osservato
corretto a mano -- la stessa distinzione che la pipeline di produzione gia'
fa a ogni rebuild (build_database.py --fixtures).

Uso:
    python scripts/integra_calendari_coppa.py            # applica (5 leghe)
    python scripts/integra_calendari_coppa.py --check     # solo verifica
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, fixtures, sources

RICERCA_DIR = Path(__file__).resolve().parents[1] / "data" / "ricerca_esterna"

LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]

# Oracolo pubblicato: data/estimates/celle_residue.csv (caso D), citato in
# CLAUDE.md (regola R6) e docs/DATI.md (§1-bis). Sono numeri GIA' dichiarati
# altrove nel progetto -- se il merge non li riproduce esattamente, qualcosa e'
# cambiato (file mancanti, snapshot diverso, bug) e lo script deve fermarsi,
# non scrivere silenziosamente un numero diverso da quello pubblicato.
ORACLE_CELLS = {
    "serie_a": 236, "premier_league": 251, "la_liga": 454,
    "bundesliga": 180, "ligue_1": 482,
}
ORACLE_ROWS_REST_CHANGED = {
    "serie_a": 314, "premier_league": 282, "la_liga": 407,
    "bundesliga": 189, "ligue_1": 508,
}
# Righe recuperate per lega (caccia_calendari.md §7): guardia contro file
# mancanti/parziali in data/ricerca_esterna/.
ORACLE_RECOVERED_ROWS = {
    "serie_a": 499, "premier_league": 526, "la_liga": 677,
    "bundesliga": 326, "ligue_1": 1017,
}


def _read_recovered(league: str) -> pd.DataFrame:
    files = sorted(RICERCA_DIR.glob(f"fixtures_{league}_*.csv"))
    if not files:
        raise SystemExit(f"{league}: nessun file ricerca_esterna trovato in {RICERCA_DIR}")
    parts = [pd.read_csv(f, dtype={"season": str}) for f in files]
    rec = pd.concat(parts, ignore_index=True)
    rec["date"] = pd.to_datetime(rec["date"])
    return rec[fixtures.FIXTURE_COLUMNS]


def _merge(existing: pd.DataFrame, recovered: pd.DataFrame) -> pd.DataFrame:
    merged = pd.concat([existing, recovered], ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"]).dt.normalize()
    merged = merged.drop_duplicates(
        subset=["season", "team", "date", "competition", "opponent"]
    )
    return merged.sort_values(["date", "team", "competition"]).reset_index(drop=True)


def integrate(league: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Calcola (senza scrivere) il calendario unito e lo snapshot ricalcolato,
    e verifica il risultato contro l'oracolo. Ritorna (esito, club_fixtures
    unito, snapshot ricalcolato)."""
    fx_path = fixtures.club_fixtures_path(league)
    existing = fixtures.read_club_fixtures(fx_path)
    recovered = _read_recovered(league)

    n_recovered = len(recovered)
    if n_recovered != ORACLE_RECOVERED_ROWS[league]:
        raise SystemExit(
            f"{league}: {n_recovered} righe recuperate, attese "
            f"{ORACLE_RECOVERED_ROWS[league]} (caccia_calendari.md §7) - "
            "controllare data/ricerca_esterna/ prima di continuare"
        )

    merged = _merge(existing, recovered)
    rows_added = len(merged) - len(existing)

    snap_path = database.snapshot_path(league)
    snap = database.read_snapshot(snap_path)
    own_comp = sources.own_league_competition(league)
    before = snap
    after = fixtures.add_rest_days_full(snap, merged, own_competition=own_comp)

    flips_h = (before.home_midweek_europe == 0) & (after.home_midweek_europe == 1)
    flips_a = (before.away_midweek_europe == 0) & (after.away_midweek_europe == 1)
    n_cells = int(flips_h.sum() + flips_a.sum())

    regress_mw = int((
        ((before.home_midweek_europe == 1) & (after.home_midweek_europe == 0))
        | ((before.away_midweek_europe == 1) & (after.away_midweek_europe == 0))
    ).sum())
    rest_increased = int((
        ((after.home_rest_days_full > before.home_rest_days_full + 1e-9)
         & before.home_rest_days_full.notna() & after.home_rest_days_full.notna())
        | ((after.away_rest_days_full > before.away_rest_days_full + 1e-9)
           & before.away_rest_days_full.notna() & after.away_rest_days_full.notna())
    ).sum())

    rest_changed_h = (before.home_rest_days_full != after.home_rest_days_full) & ~(
        before.home_rest_days_full.isna() & after.home_rest_days_full.isna())
    rest_changed_a = (before.away_rest_days_full != after.away_rest_days_full) & ~(
        before.away_rest_days_full.isna() & after.away_rest_days_full.isna())
    n_rows_rest_changed = int((rest_changed_h | rest_changed_a).sum())

    regressions = regress_mw + rest_increased
    ok = (
        n_cells == ORACLE_CELLS[league]
        and n_rows_rest_changed == ORACLE_ROWS_REST_CHANGED[league]
        and regressions == 0
    )

    result = dict(
        league=league, rows_added=rows_added, cells=n_cells,
        oracle_cells=ORACLE_CELLS[league], rows_rest_changed=n_rows_rest_changed,
        oracle_rows_rest_changed=ORACLE_ROWS_REST_CHANGED[league],
        regressions=regressions, ok=ok,
    )
    return result, merged, after


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="solo verifica contro l'oracolo, non scrive nulla")
    args = parser.parse_args()

    print(f"{'lega':16s} {'righe agg.':>10s} {'celle':>13s} {'partite riposo':>16s} {'regr.':>6s}  esito")
    computed = {}
    all_ok = True
    for league in LEAGUES:
        r, merged, after = integrate(league)
        computed[league] = (merged, after)
        all_ok &= r["ok"]
        status = "OK" if r["ok"] else "MISMATCH"
        print(f"{league:16s} {r['rows_added']:10d} "
              f"{r['cells']:5d}/{r['oracle_cells']:<5d} "
              f"{r['rows_rest_changed']:7d}/{r['oracle_rows_rest_changed']:<6d} "
              f"{r['regressions']:6d}  {status}")

    if not all_ok:
        raise SystemExit(
            "\nAlmeno una lega non combacia con l'oracolo pubblicato "
            "(data/estimates/celle_residue.csv): nessun file e' stato scritto, "
            "per nessuna lega."
        )

    if args.check:
        print("\n--check: tutti i numeri combaciano con l'oracolo, nessun file scritto.")
        return

    for league, (merged, after) in computed.items():
        fixtures.write_club_fixtures(merged, fixtures.club_fixtures_path(league))
        database.write_snapshot(after, database.snapshot_path(league))
    print("\nApplicato: club_fixtures*.csv e gli snapshot delle 5 leghe sono aggiornati.")


if __name__ == "__main__":
    main()
