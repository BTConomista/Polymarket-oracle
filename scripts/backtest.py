"""Backtest del modello Dixon-Coles su una stagione di test.

Metodologia (per evitare il look-ahead, cioe' "barare" guardando il futuro):

  - alleniamo su TUTTE le stagioni tranne l'ultima; l'ultima e' quella di TEST;
  - procediamo settimana per settimana ("walk-forward"): prima di ogni giornata
    rialleniamo il modello usando SOLO le partite gia' avvenute (tutte le stagioni
    precedenti + le giornate gia' giocate della stagione di test), poi prediciamo
    le partite di quella giornata. E' esattamente cio' che potremmo fare nella
    realta': ogni settimana rialleniamo e prediciamo il turno successivo.

Alla fine confrontiamo, su 1X2 e Over/Under 2.5:
  - il MODELLO,
  - il MERCATO (quote di chiusura dei bookmaker, margine rimosso),
  - una BASELINE banale (frequenze storiche costanti),
tramite log-loss e Brier score (piu' bassi = meglio).

E' incluso anche un semplice conto di ROI su "value bet" (scommesse dove il
modello assegna piu' probabilita' del mercato). ATTENZIONE: e' puramente
illustrativo. Un backtest su dati storici sovrastima quasi sempre la redditivita'
reale; NON e' una promessa di guadagno.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import experiment_log
from src.models.dixon_coles import DixonColesModel


def run_backtest(
    league_key: str,
    test_season: str,
    half_life_days: float,
    shrinkage: float = 0.0,
    shots_blend: float = 1.0,
    blend_signal: str = "sot",
    covariates: tuple[str, ...] = (),
    verbose: bool = True,
) -> pd.DataFrame:
    """Esegue il walk-forward e ritorna un DataFrame con una riga per partita."""
    all_matches = loader.load_league(league_key)
    test = all_matches[all_matches["season"] == test_season].copy()
    if test.empty:
        raise SystemExit(f"Nessun dato per la stagione di test {test_season}.")

    # Raggruppiamo la stagione di test per settimana solare: rialleniamo una
    # volta a settimana (realistico) invece che ad ogni singola partita.
    # Usiamo il lunedi' della settimana come chiave: e' un timestamp, quindi si
    # ordina correttamente in senso cronologico.
    test["_week"] = test["date"] - pd.to_timedelta(test["date"].dt.dayofweek, unit="D")

    rows: list[dict] = []
    n_weeks = test["_week"].nunique()
    for w, (_, group) in enumerate(test.groupby("_week", sort=True), start=1):
        as_of = group["date"].min()
        model = DixonColesModel(half_life_days=half_life_days, shrinkage=shrinkage,
                                shots_blend=shots_blend, blend_signal=blend_signal,
                                covariates=covariates)
        model.fit(all_matches, as_of_date=as_of)
        if verbose:
            print(f"  settimana {w}/{n_weeks}  ({as_of.date()}): "
                  f"{len(group)} partite, allenato su {(all_matches['date'] < as_of).sum()} gare",
                  flush=True)

        for _, m in group.iterrows():
            pred = model.predict_match(m["home_team"], m["away_team"], features=m)
            row = {
                "date": m["date"],
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "home_goals": m["home_goals"],
                "away_goals": m["away_goals"],
                "result": m["result"],
                "is_over": int(m["home_goals"] + m["away_goals"] >= 3),
                # Probabilita' del modello
                "m_home": pred.prob_home_win,
                "m_draw": pred.prob_draw,
                "m_away": pred.prob_away_win,
                "m_over": pred.prob_over_2_5,
                # Quote di mercato (per il confronto)
                "odds_home": m["odds_home"],
                "odds_draw": m["odds_draw"],
                "odds_away": m["odds_away"],
                "odds_over": m["odds_over25"],
                "odds_under": m["odds_under25"],
            }
            rows.append(row)

    return pd.DataFrame(rows)


def report(m: dict, n_matches: int) -> None:
    """Stampa il report leggibile a partire dalle metriche calcolate."""
    def line(name, ll, br=None):
        extra = f"   brier={br:.4f}" if br is not None else ""
        print(f"    {name:<28} log-loss={ll:.4f}{extra}")

    print("\n" + "=" * 64)
    print(f"RISULTATI BACKTEST — {n_matches} partite")
    print("=" * 64)

    print("\n[1X2]  (log-loss e brier: piu' bassi = meglio)")
    line("Modello Dixon-Coles", m["x2_model_logloss"], m["x2_model_brier"])
    line("Baseline (freq. costanti)", m["x2_baseline_logloss"], m["x2_baseline_brier"])
    line("Mercato (quote chiusura)", m["x2_market_logloss"], m["x2_market_brier"])

    print("\n[OVER/UNDER 2.5]")
    line("Modello Dixon-Coles", m["ou_model_logloss"], m["ou_model_brier"])
    line("Baseline (freq. costante)", m["ou_baseline_logloss"])
    line("Mercato (quote chiusura)", m["ou_market_logloss"], m["ou_market_brier"])

    print("\n[VALUE BET 1X2 — illustrativo, NON una promessa di guadagno]")
    if m["value_bet_n"] == 0:
        print("    Nessuna scommessa sopra la soglia di edge.")
    else:
        print(f"    Scommesse: {m['value_bet_n']}  |  ROI: {m['value_bet_roi_pct']:+.1f}%")
        print("    (Backtest storico: sovrastima quasi sempre la realta'.)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest Dixon-Coles.")
    parser.add_argument("--league", default="serie_a")
    parser.add_argument("--test-season", default=sources.SEASONS[-1],
                        help="stagione di test (default: l'ultima)")
    parser.add_argument("--half-life-days", type=float, default=730.0,
                        help="emivita del decadimento temporale in giorni "
                             "(default 730, valore scelto via scripts/tune.py)")
    parser.add_argument("--shrinkage", type=float, default=1.5,
                        help="forza della regolarizzazione verso la media "
                             "(default 1.5, valore scelto via scripts/tune.py)")
    parser.add_argument("--shots-blend", type=float, default=0.75,
                        help="peso alpha gol vs segnale secondario (1=solo gol, "
                             "0=solo segnale; default 0.75, scelto in Fase 4b)")
    parser.add_argument("--blend-signal", default="xg", choices=["sot", "xg", "npxg"],
                        help="segnale secondario da mescolare (default xg=xG reale; "
                             "sot=tiri in porta)")
    parser.add_argument("--covariates", nargs="*", default=[],
                        choices=["squad_value", "absence"],
                        help="covariate di partita da aggiungere (Fase 4c)")
    parser.add_argument("--quiet", action="store_true",
                        help="non stampare il log settimanale")
    parser.add_argument("--save", default="outputs/backtest_predictions.csv",
                        help="dove salvare le predizioni per-partita")
    args = parser.parse_args()

    print(f"Backtest {args.league} — stagione test {args.test_season} "
          f"({sources.season_label(args.test_season)}), "
          f"emivita {args.half_life_days:.0f}g, shrinkage {args.shrinkage}, "
          f"shots_blend {args.shots_blend} ({args.blend_signal})")
    df = run_backtest(args.league, args.test_season, args.half_life_days,
                      shrinkage=args.shrinkage, shots_blend=args.shots_blend,
                      blend_signal=args.blend_signal, covariates=tuple(args.covariates),
                      verbose=not args.quiet)

    m = experiment_log.compute_metrics(df)
    report(m, len(df))

    # Registra l'esperimento (config + metriche + provenienza) per replicabilita'.
    config = {
        "league": args.league,
        "test_season": args.test_season,
        "half_life_days": args.half_life_days,
        "shrinkage": args.shrinkage,
        "shots_blend": args.shots_blend,
        "blend_signal": args.blend_signal,
        "covariates": list(args.covariates),
    }
    all_matches = loader.load_league(args.league)
    record = experiment_log.make_record(
        config, m, experiment_log.data_fingerprint(all_matches))
    experiment_log.append_run(record)
    print(f"\nEsperimento registrato in experiments/runs.jsonl "
          f"(commit {record['git_commit'][:8]}, dati {record['data_fingerprint']})")

    out = Path(args.save)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Predizioni salvate in {out}")


if __name__ == "__main__":
    main()
