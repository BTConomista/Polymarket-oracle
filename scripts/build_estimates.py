"""Genera data/estimates/ — STIME dichiarate di dati di mercato mancanti.

⚠️  ATTENZIONE: questo script produce STIME DI MODELLO, non prezzi di mercato.
    Vivono in data/estimates/ (mai nelle colonne quota degli snapshot), sono
    PROBABILITA' (non quote: niente margine, impossibile confonderle coi prezzi)
    e ogni analisi che le usa deve dichiararlo. Vedi docs/DATI.md §Stime.

Contenuto attuale (un file per stima; regole d'uso nel README della cartella):

ou_close_2017_19.csv (Fase 62/62-bis):
  la CHIUSURA O/U 2.5 delle stagioni 2017-18 e 2018-19 (3 leghe), che le fonti
  non hanno (una sola linea O/U pre-match). Stimata con l'estimatore vincitore
  del bakeoff Fase 62-bis (E3 pooled): regressione in spazio logit della
  chiusura sul (O/U pre-match + movimento 1X2 apertura->chiusura), fittata
  POOLED sulle 21 (lega, stagione) 2019-20+ dove la chiusura vera esiste.

  Errore atteso (walk-forward, Fase 62-bis): MAE ~0.012 in probabilita',
  corr col movimento vero 0.75-0.86. Limiti dichiarati:
    - coefficienti fittati su stagioni SUCCESSIVE a quelle stimate (unico dato
      possibile): va bene per un benchmark storico, NON per predizione;
    - nel 2017-19 le linee input sono Pinnacle/BbAv, il fit usa le medie Avg;
    - la stima cattura solo la parte di movimento CONDIVISA con l'1X2 (~60-75%
      della varianza): le notizie puro-totali (es. turnover d'attacco) no.

squad_value_2017_26.csv (Fase 66):
  il valore rosa delle 73 celle (stagione, squadra) che il datalake
  Transfermarkt non copre (SA 29, Liga 40, PL 4 — Lazio, Getafe, ecc.).
  Stimatore ibrido, scelto col leave-one-out/leave-team-out sulle 467 celle
  note (run fase66_squad_value_est):
    - "anchored" (A3 pooled): regressione su rendimento stagionale + valore
      della stessa squadra nelle stagioni adiacenti -> err mediano ~17%;
    - "regression" (A2 per-lega): solo rendimento, per le squadre senza
      NESSUNA stagione nota (es. Lazio) -> err mediano ~29% (p90 ~75%!).
  Errore GRANDE e dichiarato riga per riga: usare solo come ordine di
  grandezza, mai come valore puntuale.

Uso:  python scripts/build_estimates.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database                          # noqa: E402
from src.evaluation import experiment_log, metrics     # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ESTIMATES_DIR = ROOT / "data" / "estimates"
OU_CLOSE_PATH = ESTIMATES_DIR / "ou_close_2017_19.csv"

LEAGUES = ["serie_a", "premier_league", "la_liga"]
FIT_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TARGET_SEASONS = ["1718", "1819"]
# Errore atteso della stima, misurato WALK-FORWARD nella Fase 62-bis (E3 pooled).
EXPECTED_MAE = 0.012

_ODDS = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25",
         "odds_home_open", "odds_draw_open", "odds_away_open"]


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def _devig(df: pd.DataFrame) -> pd.DataFrame:
    """Probabilita' devigate (molt., fonte unica metrics.devig_*) + feature."""
    out = df.copy()
    p_c = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in df.itertuples()])
    p_o = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                      r.odds_away_open) for r in df.itertuples()])
    out[["pH_c", "pD_c", "pA_c"]] = p_c
    out[["pH_o", "pD_o", "pA_o"]] = p_o
    out["p_over_line"] = [metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
                          for r in df.itertuples()]
    return out


def _X(df: pd.DataFrame) -> np.ndarray:
    """Design matrix E3 (Fase 62-bis): 1, logit(OU), Dlogit(H), Dlogit(D), Dlogit(A)."""
    return np.column_stack([
        np.ones(len(df)),
        _logit(df["p_over_line"]),
        _logit(df["pH_c"]) - _logit(df["pH_o"]),
        _logit(df["pD_c"]) - _logit(df["pD_o"]),
        _logit(df["pA_c"]) - _logit(df["pA_o"]),
    ])


def build_ou_close() -> pd.DataFrame:
    # ---- fit POOLED sulle stagioni con la chiusura O/U vera -----------------
    fit_frames = []
    for lg in LEAGUES:
        df = database.read_snapshot(database.snapshot_path(lg))
        df["season"] = df["season"].astype(str)
        df = df[df["season"].isin(FIT_SEASONS)].dropna(
            subset=_ODDS + ["odds_over25_open", "odds_under25_open"])
        df = _devig(df)
        # nel fit l'input O/U e' la linea di APERTURA (nel 2017-19 la linea
        # unica disponibile e' pre-match: stesso timing)
        df["p_over_line"] = [
            metrics.devig_binary(r.odds_over25_open, r.odds_under25_open)[0]
            for r in df.itertuples()]
        df["p_over_close"] = [
            metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
            for r in df.itertuples()]
        df["league"] = lg
        fit_frames.append(df)
    fit = pd.concat(fit_frames, ignore_index=True)
    A = _X(fit)
    y = _logit(fit["p_over_close"])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    in_mae = float(np.abs(_sigmoid(A @ coef) - fit["p_over_close"]).mean())
    print(f"fit E3 pooled su {len(fit)} partite ({len(FIT_SEASONS)} stagioni x 3 leghe)")
    print(f"  coefficienti [1, logit(OU), dH, dD, dA] = "
          f"{np.array2string(coef, precision=4)}")
    print(f"  MAE in-sample {in_mae:.4f} (atteso out-of-sample ~{EXPECTED_MAE}, "
          f"walk-forward Fase 62-bis)")

    # ---- applica alle stagioni SENZA chiusura O/U ---------------------------
    est_frames = []
    for lg in LEAGUES:
        df = database.read_snapshot(database.snapshot_path(lg))
        df["season"] = df["season"].astype(str)
        df = df[df["season"].isin(TARGET_SEASONS)]
        n_tot = len(df)
        df = df.dropna(subset=_ODDS).copy()
        if n_tot - len(df):
            print(f"  {lg}: {n_tot - len(df)} partite saltate (input mancanti)")
        df = _devig(df)     # p_over_line = linea unica (pre-match), gia' giusta
        p_est = _sigmoid(_X(df) @ coef)
        est_frames.append(pd.DataFrame({
            "league": lg, "season": df["season"],
            "date": pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"),
            "home_team": df["home_team"], "away_team": df["away_team"],
            "p_over25_close_est": np.round(p_est, 4),
        }))
        moved = np.abs(p_est - df["p_over_line"].to_numpy())
        print(f"  {lg}: {len(df)} stime ({TARGET_SEASONS}); "
              f"|stima - linea pre-match| medio {moved.mean():.4f}")
    return pd.concat(est_frames, ignore_index=True), coef, in_mae, fit


SQUAD_VALUE_PATH = ESTIMATES_DIR / "squad_value_2017_26.csv"
# Errori attesi dal backtest leave-one-out / leave-team-out (Fase 66).
ERR_ANCHORED, ERR_REGRESSION = 17.0, 29.0


def build_squad_value() -> pd.DataFrame:
    """Stima le celle (stagione, squadra) senza valore rosa (Fase 66)."""
    from scripts._run_fase66_squad_value_est import (
        _design, _fit_ols, _pred_ols, anchor_feature, team_season_table)

    t = team_season_table()
    known = np.isfinite(t["y"].to_numpy())
    anchor = anchor_feature(t, known)
    D = _design(t, anchor)
    y = t["y"].to_numpy()

    # A3 pooled (celle CON ancora) — fit su tutte le note
    coef3 = _fit_ols(D["A3"][known], y[known])
    # A2 per-lega (celle SENZA ancora)
    coef2 = {lg: _fit_ols(D["A2"][known & (t["league"] == lg).to_numpy()],
                          y[known & (t["league"] == lg).to_numpy()])
             for lg in t["league"].unique()}

    holes = t[~known].copy()
    rows = []
    for i, r in holes.iterrows():
        if np.isfinite(anchor[i]):
            y_hat = float(_pred_ols(coef3, D["A3"][[i]])[0])
            method, err = "anchored", ERR_ANCHORED
        else:
            y_hat = float(_pred_ols(coef2[r.league], D["A2"][[i]])[0])
            method, err = "regression", ERR_REGRESSION
        value = float(np.exp(y_hat + r.log_med))
        rows.append({
            "league": r.league, "season": r.season, "team": r.team,
            "squad_value_est": round(value, -5),      # arrotonda ai 100k EUR
            "method": method, "expected_median_err_pct": err,
        })
    est = pd.DataFrame(rows).sort_values(["league", "season", "team"])
    n_anch = (est["method"] == "anchored").sum()
    print(f"\nsquad_value: {len(est)} stime ({n_anch} anchored ~{ERR_ANCHORED:.0f}%, "
          f"{len(est)-n_anch} regression ~{ERR_REGRESSION:.0f}%)")
    return est, t


def main() -> None:
    t0 = time.time()
    ESTIMATES_DIR.mkdir(parents=True, exist_ok=True)
    est, coef, in_mae, fit = build_ou_close()
    est.to_csv(OU_CLOSE_PATH, index=False)
    print(f"\n-> {OU_CLOSE_PATH.relative_to(ROOT)}: {len(est)} stime "
          f"({est.league.nunique()} leghe, stagioni {sorted(est.season.unique())})")
    print("   ⚠️  STIME di modello, non prezzi di mercato: vedi docs/DATI.md §Stime.")

    experiment_log.append_run(experiment_log.make_record(
        config={"source": "build_estimates_ou_close", "model": "E3_pooled",
                "fit_seasons": FIT_SEASONS, "target_seasons": TARGET_SEASONS,
                "coefficients": [round(float(c), 6) for c in coef],
                "expected_mae_wf": EXPECTED_MAE},
        metrics_dict={"n_estimates": int(len(est)), "in_sample_mae": in_mae},
        fingerprint=experiment_log.data_fingerprint(fit),
    ))

    sq, t_table = build_squad_value()
    sq.to_csv(SQUAD_VALUE_PATH, index=False)
    print(f"-> {SQUAD_VALUE_PATH.relative_to(ROOT)}: {len(sq)} stime "
          f"({sq.league.nunique()} leghe)")
    print("   ⚠️  errore mediano atteso 17-29% (riga per riga nel file): "
          "ordini di grandezza, non valori puntuali.")
    experiment_log.append_run(experiment_log.make_record(
        config={"source": "build_estimates_squad_value",
                "model": "A3_pooled(anchored)+A2_perlega(regression)",
                "expected_err": {"anchored": ERR_ANCHORED,
                                 "regression": ERR_REGRESSION}},
        metrics_dict={"n_estimates": int(len(sq)),
                      "n_anchored": int((sq["method"] == "anchored").sum())},
        fingerprint=experiment_log.data_fingerprint(fit),
    ))
    print(f"Registrati in experiments/runs.jsonl. ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
