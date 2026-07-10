"""Driver Fase 4e — validazione congestione VERA (rest_full vs rest solo-lega).

Rifà il test negativo della Fase 4c (covariata `rest` sul calendario di sola
Serie A) e lo confronta con `rest_full` (calendario di club completo, Fase 4e),
sulle stagioni con copertura reale di coppe/Europa (2020-21 -> 2024-25).

Un solo fattore cambia tra `rest` e `rest_full`: la SORGENTE del calendario.
Config del modello = ufficiale corrente (emivita 365g, shrinkage 1.5,
shots_blend 0.75, blend xG). Ogni run viene registrato in experiments/runs.jsonl.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log
from scripts.backtest import run_backtest

SEASONS = ["2021", "2122", "2223", "2324", "2425"]  # copertura coppe/Europa reale
COVSETS = [(), ("rest",), ("rest_full",)]
HALF_LIFE, SHRINK, BLEND, SIGNAL = 365.0, 1.5, 0.75, "xg"

all_matches = loader.load_league("serie_a")
fp = experiment_log.data_fingerprint(all_matches)

results = {}  # (season, covlabel) -> metrics
for season in SEASONS:
    for cov in COVSETS:
        label = cov[0] if cov else "baseline"
        df = run_backtest("serie_a", season, HALF_LIFE, shrinkage=SHRINK,
                          shots_blend=BLEND, blend_signal=SIGNAL,
                          covariates=cov, verbose=False)
        m = experiment_log.compute_metrics(df)
        results[(season, label)] = m
        config = {
            "league": "serie_a", "test_season": season,
            "half_life_days": HALF_LIFE, "shrinkage": SHRINK,
            "shots_blend": 0.75, "blend_signal": SIGNAL,
            "covariates": list(cov), "source": "fase4e_congestione",
        }
        record = experiment_log.make_record(config, m, fp)
        experiment_log.append_run(record)
        print(f"[{season}] {label:10s} 1X2 ll={m['x2_model_logloss']:.4f} "
              f"brier={m['x2_model_brier']:.4f}  OU ll={m['ou_model_logloss']:.4f}  "
              f"mercato ll={m['x2_market_logloss']:.4f}", flush=True)

# ---- Tabella riassuntiva 1X2 log-loss (piu' basso = meglio) ----
print("\n" + "=" * 78)
print("RIEPILOGO 1X2 log-loss — baseline vs rest (solo Serie A) vs rest_full (completo)")
print("=" * 78)
print(f"{'stag.':<7}{'baseline':>10}{'rest':>10}{'rest_full':>11}"
      f"{'d(rest)':>10}{'d(rest_full)':>14}{'mercato':>10}")
agg = {"baseline": 0.0, "rest": 0.0, "rest_full": 0.0, "market": 0.0}
n = 0
for season in SEASONS:
    b = results[(season, "baseline")]["x2_model_logloss"]
    r = results[(season, "rest")]["x2_model_logloss"]
    rf = results[(season, "rest_full")]["x2_model_logloss"]
    mk = results[(season, "baseline")]["x2_market_logloss"]
    print(f"{season:<7}{b:>10.4f}{r:>10.4f}{rf:>11.4f}{r-b:>+10.4f}{rf-b:>+14.4f}{mk:>10.4f}")
    agg["baseline"] += b; agg["rest"] += r; agg["rest_full"] += rf; agg["market"] += mk
    n += 1
print("-" * 78)
print(f"{'MEDIA':<7}{agg['baseline']/n:>10.4f}{agg['rest']/n:>10.4f}"
      f"{agg['rest_full']/n:>11.4f}{(agg['rest']-agg['baseline'])/n:>+10.4f}"
      f"{(agg['rest_full']-agg['baseline'])/n:>+14.4f}{agg['market']/n:>10.4f}")
print("\nd(...) < 0 = la covariata MIGLIORA vs baseline;  > 0 = peggiora.")
