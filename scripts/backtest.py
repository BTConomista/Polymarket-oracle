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

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader, sources
from src.evaluation import metrics
from src.models.dixon_coles import DixonColesModel


def run_backtest(
    league_key: str,
    test_season: str,
    half_life_days: float,
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
        model = DixonColesModel(half_life_days=half_life_days)
        model.fit(all_matches, as_of_date=as_of)
        print(f"  settimana {w}/{n_weeks}  ({as_of.date()}): "
              f"{len(group)} partite, allenato su {(all_matches['date'] < as_of).sum()} gare",
              flush=True)

        for _, m in group.iterrows():
            pred = model.predict_match(m["home_team"], m["away_team"])
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


def _market_probs_1x2(df: pd.DataFrame) -> np.ndarray:
    out = np.full((len(df), 3), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            out[i] = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
    return out


def _market_prob_over(df: pd.DataFrame) -> np.ndarray:
    out = np.full(len(df), np.nan)
    for i, (_, r) in enumerate(df.iterrows()):
        if np.isfinite([r.odds_over, r.odds_under]).all():
            out[i], _ = metrics.devig_binary(r.odds_over, r.odds_under)
    return out


def report(df: pd.DataFrame) -> None:
    outcomes = df["result"].tolist()
    model_1x2 = df[["m_home", "m_draw", "m_away"]].to_numpy()
    market_1x2 = _market_probs_1x2(df)
    has_mkt = ~np.isnan(market_1x2).any(axis=1)

    is_over = df["is_over"].to_numpy()
    model_over = df["m_over"].to_numpy()
    market_over = _market_prob_over(df)
    has_ou = ~np.isnan(market_over)

    baseline = metrics.base_rates_1x2(outcomes)
    baseline_probs = np.tile(baseline, (len(df), 1))

    def line(name, ll, br):
        print(f"    {name:<28} log-loss={ll:.4f}   brier={br:.4f}")

    print("\n" + "=" * 64)
    print(f"RISULTATI BACKTEST — {len(df)} partite")
    print("=" * 64)

    print("\n[1X2]  (log-loss e brier: piu' bassi = meglio)")
    line("Modello Dixon-Coles",
         metrics.log_loss_1x2(model_1x2, outcomes),
         metrics.brier_1x2(model_1x2, outcomes))
    line("Baseline (freq. costanti)",
         metrics.log_loss_1x2(baseline_probs, outcomes),
         metrics.brier_1x2(baseline_probs, outcomes))
    if has_mkt.any():
        o = [outcomes[i] for i in range(len(df)) if has_mkt[i]]
        line("Mercato (quote chiusura)",
             metrics.log_loss_1x2(market_1x2[has_mkt], o),
             metrics.brier_1x2(market_1x2[has_mkt], o))
        # Confronto modello vs mercato sullo STESSO sottoinsieme.
        line("Modello (stesso sottoinsieme)",
             metrics.log_loss_1x2(model_1x2[has_mkt], o),
             metrics.brier_1x2(model_1x2[has_mkt], o))

    print("\n[OVER/UNDER 2.5]")
    line("Modello Dixon-Coles",
         metrics.log_loss_binary(model_over, is_over),
         metrics.brier_binary(model_over, is_over))
    # Baseline: probabilita' costante = frequenza empirica di Over nella stagione.
    base_over = np.full(len(df), float(is_over.mean()))
    line("Baseline (freq. costante)",
         metrics.log_loss_binary(base_over, is_over),
         metrics.brier_binary(base_over, is_over))
    if has_ou.any():
        line("Mercato (quote chiusura)",
             metrics.log_loss_binary(market_over[has_ou], is_over[has_ou]),
             metrics.brier_binary(market_over[has_ou], is_over[has_ou]))
        line("Modello (stesso sottoinsieme)",
             metrics.log_loss_binary(model_over[has_ou], is_over[has_ou]),
             metrics.brier_binary(model_over[has_ou], is_over[has_ou]))

    _value_bet_summary(df, market_1x2, has_mkt)


def _value_bet_summary(df, market_1x2, has_mkt) -> None:
    """ROI illustrativo su value bet 1X2 (edge del modello > soglia)."""
    THRESHOLD = 0.05  # scommetti solo se prob_modello - prob_mercato > 5%
    outcomes = df["result"].tolist()
    cols_odds = ["odds_home", "odds_draw", "odds_away"]
    model_1x2 = df[["m_home", "m_draw", "m_away"]].to_numpy()

    stake = 0.0
    profit = 0.0
    n_bets = 0
    for i in range(len(df)):
        if not has_mkt[i]:
            continue
        for k, outcome_key in enumerate("HDA"):
            edge = model_1x2[i, k] - market_1x2[i, k]
            if edge > THRESHOLD:
                odds = df.iloc[i][cols_odds[k]]
                n_bets += 1
                stake += 1.0
                if outcomes[i] == outcome_key:
                    profit += odds - 1.0
                else:
                    profit -= 1.0
    print("\n[VALUE BET 1X2 — illustrativo, NON una promessa di guadagno]")
    if n_bets == 0:
        print("    Nessuna scommessa sopra la soglia di edge.")
    else:
        roi = 100.0 * profit / stake
        print(f"    Scommesse: {n_bets}  |  puntata tot: {stake:.0f} unita'  |  "
              f"profitto: {profit:+.1f}  |  ROI: {roi:+.1f}%")
        print("    (Backtest storico: sovrastima quasi sempre la realta'.)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest Dixon-Coles.")
    parser.add_argument("--league", default="serie_a")
    parser.add_argument("--test-season", default=sources.SEASONS[-1],
                        help="stagione di test (default: l'ultima)")
    parser.add_argument("--half-life-days", type=float, default=180.0,
                        help="emivita del decadimento temporale (giorni)")
    parser.add_argument("--save", default="outputs/backtest_predictions.csv",
                        help="dove salvare le predizioni per-partita")
    args = parser.parse_args()

    print(f"Backtest {args.league} — stagione test {args.test_season} "
          f"({sources.season_label(args.test_season)}), "
          f"emivita {args.half_life_days:.0f}g")
    df = run_backtest(args.league, args.test_season, args.half_life_days)

    report(df)

    out = Path(args.save)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nPredizioni salvate in {out}")


if __name__ == "__main__":
    main()
