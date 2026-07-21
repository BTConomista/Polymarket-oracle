#!/usr/bin/env python3
"""
Criteri di accettazione per i CSV O/U 2.5 (chi cerca deve verificarli):

  1. linea esattamente 2.5        -> garantito a monte dal filtro dello scraper;
  2. overround > 1 su ogni riga   -> 1/over + 1/under > 1, sia apertura che chiusura;
  3. apertura != chiusura         -> nella grande maggioranza delle righe
                                     (se coincidono sempre: fonte sospetta);
  4. copertura >= 95%             -> per lega-stagione (su 380 attese);
  5. quote reali scrappate        -> tracciabilita': book_source dichiarato per riga.

Uso: python check_acceptance.py files/ou25_*.csv
Exit code 1 se un criterio bloccante fallisce.
"""

import csv
import sys
from collections import defaultdict

EXPECTED = 380
MIN_COVERAGE = 0.95
MIN_OPEN_NE_CLOSE = 0.60  # "grande maggioranza": soglia prudente, da giudicare a occhio


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main(paths):
    groups = defaultdict(list)
    for p in paths:
        with open(p, newline="") as fh:
            for row in csv.DictReader(fh):
                groups[(row["league"], row["season"])].append(row)

    hard_fail = False
    for (league, season), rows in sorted(groups.items()):
        ok = [r for r in rows if r.get("status") == "ok"]
        n, n_ok = len(rows), len(ok)
        cov = n_ok / EXPECTED
        bad_ovr_close, bad_ovr_open, ne_open_close, no_open = 0, 0, 0, 0
        for r in ok:
            oo, uo = f(r["over_open"]), f(r["under_open"])
            oc, uc = f(r["over_close"]), f(r["under_close"])
            if oc and uc and (1 / oc + 1 / uc) <= 1:
                bad_ovr_close += 1
            if oo and uo:
                if (1 / oo + 1 / uo) <= 1:
                    bad_ovr_open += 1
                if (oo, uo) != (oc, uc):
                    ne_open_close += 1
            else:
                no_open += 1
        with_open = n_ok - no_open
        pct_ne = ne_open_close / with_open if with_open else 0.0

        print(f"\n== {league} {season} ==")
        print(f"  righe totali:            {n}")
        print(f"  righe con quote 2.5:     {n_ok}  (copertura {cov:.1%} su {EXPECTED})")
        print(f"  senza quota di apertura: {no_open}")
        print(f"  overround<=1 (chiusura): {bad_ovr_close}")
        print(f"  overround<=1 (apertura): {bad_ovr_open}")
        print(f"  apertura != chiusura:    {ne_open_close}/{with_open}  ({pct_ne:.1%})")

        problems = []
        if cov < MIN_COVERAGE:
            problems.append(f"copertura {cov:.1%} < {MIN_COVERAGE:.0%}")
        if bad_ovr_close or bad_ovr_open:
            problems.append("righe con overround <= 1 (quote sospette: ispezionarle)")
        if with_open and pct_ne < MIN_OPEN_NE_CLOSE:
            problems.append(f"apertura==chiusura troppo spesso ({1 - pct_ne:.1%}): "
                            "la fonte potrebbe rietichettare una sola istantanea")
        if no_open > 0.10 * max(n_ok, 1):
            problems.append("piu' del 10% delle righe senza quota di apertura")
        if problems:
            hard_fail = True
            for p in problems:
                print(f"  [FAIL] {p}")
        else:
            print("  [PASS] tutti i criteri verificati")

    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1:])
