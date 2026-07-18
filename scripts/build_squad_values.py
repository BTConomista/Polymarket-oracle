"""Riempie i valori rosa REALI negli snapshot dal dataset player-scores (Fase 67).

Sostituisce (per la colonna squad_value) la vecchia catena salimt+Understat:
stessa definizione, fonte piu' completa (vedi src/data/player_scores.py).
Riempie TUTTE le celle delle 3 leghe — inclusa la Serie A, che con la vecchia
catena non era piu' rigenerabile — e mantiene la soglia di onesta' (copertura
>= 85% dei minuti, altrimenti NaN).

Dopo il refill vanno rigenerate le STIME dei buchi residui:
    python scripts/build_estimates.py

Uso:  python scripts/build_squad_values.py            (tutte e 3 le leghe)
      python scripts/build_squad_values.py serie_a    (una sola)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, player_scores, sources   # noqa: E402
from src.evaluation import experiment_log               # noqa: E402

ALL = ["serie_a", "premier_league", "la_liga"]


def main() -> None:
    keys = sys.argv[1:] or ALL
    results = {}
    for key in keys:
        print(f"\n=== {sources.LEAGUES[key].name} ===")
        snap = database.read_snapshot(database.snapshot_path(key))
        out = player_scores.add_squad_values(snap, key)
        database.write_snapshot(out, database.snapshot_path(key))
        both = out["home_squad_value"].notna() & out["away_squad_value"].notna()
        results[key] = round(float(both.mean()), 4)
        print(f"  -> {database.snapshot_path(key).name}: copertura valore rosa "
              f"(entrambi i lati) {both.mean():.1%}")

    experiment_log.append_run(experiment_log.make_record(
        config={"source": "build_squad_values_player_scores",
                "leagues": keys, "min_coverage": player_scores.MIN_COVERAGE},
        metrics_dict={"coverage_both_sides": results},
        fingerprint="player_scores_dataset",
    ))
    print("\nRegistrato in experiments/runs.jsonl. Ora rigenera le stime "
          "residue: python scripts/build_estimates.py")


if __name__ == "__main__":
    main()
