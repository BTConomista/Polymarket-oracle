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

open_sparse_1x2_ou.csv (Fase 69):
  le quote di APERTURA per le partite "sparse" senza apertura vera che NON
  fanno parte del buco sistemico 2017-19 O/U (quello ha un piano di raccolta
  dati dedicato, vedi docs/CACCIA_OU_2017_19.md): 2 partite 1X2 (il grezzo
  non ha mai avuto la colonna, o la maschera anti-contaminazione l'ha
  scartata) + 1 partita O/U isolata in stagione 2020-21. Bakeoff (richiesta
  utente) tra 5 metodi -- identita', regressione lineare pooled, regressione
  logit pooled, regressione lineare per-lega, blend identita'+logit -- via
  5-fold CV su TUTTE le coppie apertura/chiusura reali (10.258 per l'1X2,
  7.978 per l'O/U, tutte le 3 leghe/9 stagioni): il logit pooled vince o
  pareggia sempre i metodi piu' complessi, nessun blend fa meglio del
  migliore singolo.

  Errore atteso (MAE 5-fold, probabilita'): **1X2 ~0.020** (praticamente pari
  all'identita': il movimento di linea 1X2 e' quasi tutto rumore piccolo),
  **O/U ~0.0196** (qui la regressione aiuta davvero, ~7% in meno della sola
  identita'). Molto piu' affidabile della stima squad_value (~17-29%).

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
# Colonne richieste per APPLICARE l'estimatore alle target (2017-19, Fase 73):
# la chiusura O/U (odds_over25/under25) non c'e' piu' (e' cio' che si stima),
# l'input O/U e' l'apertura reale (odds_over25_open); il movimento 1X2 usa la
# chiusura (PSC) e l'apertura (PS) dell'1X2.
_ODDS_TARGET = ["odds_home", "odds_draw", "odds_away",
                "odds_home_open", "odds_draw_open", "odds_away_open",
                "odds_over25_open", "odds_under25_open"]


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def _devig(df: pd.DataFrame) -> pd.DataFrame:
    """Probabilita' devigate (molt., fonte unica metrics.devig_*) + feature.

    ``p_over_line`` = la linea O/U di APERTURA (odds_over25_open). Dalla Fase 73
    l'unica linea O/U del 2017-19 (BbAv, pre-match) vive correttamente nella
    colonna di apertura, non piu' in quella di chiusura: l'input dell'estimatore
    e' quindi uniforme (apertura) sia nel fit (2019-20+) sia nell'applicazione
    (2017-19)."""
    out = df.copy()
    p_c = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in df.itertuples()])
    p_o = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                      r.odds_away_open) for r in df.itertuples()])
    out[["pH_c", "pD_c", "pA_c"]] = p_c
    out[["pH_o", "pD_o", "pA_o"]] = p_o
    out["p_over_line"] = [
        metrics.devig_binary(r.odds_over25_open, r.odds_under25_open)[0]
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
        df = _devig(df)     # p_over_line = apertura O/U (odds_over25_open)
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
        # Input per l'applicazione (2017-19): apertura O/U (odds_over25_open,
        # BbAv reale, Fase 73) + 1X2 chiusura (PSC) e apertura (PS). La chiusura
        # O/U NON serve (e' cio' che stimiamo). Alaves-Sociedad 14/10/2017
        # (unica riga 2017-19 senza chiusura 1X2 PSC, Fase 73) cade qui.
        df = df.dropna(subset=_ODDS_TARGET).copy()
        if n_tot - len(df):
            print(f"  {lg}: {n_tot - len(df)} partite saltate (input mancanti)")
        df = _devig(df)     # p_over_line = apertura O/U (odds_over25_open)
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


OPEN_SPARSE_PATH = ESTIMATES_DIR / "open_sparse_1x2_ou.csv"
# Stagioni del buco SISTEMICO O/U (piano dedicato, CACCIA_OU_2017_19.md) --
# le righe O/U mancanti li' NON sono "sparse", non vanno stimate qui.
SYSTEMIC_OU_SEASONS = {"1718", "1819"}
N_FOLDS = 5           # k-fold per l'errore atteso del bakeoff (Fase 69)
_CV_SEED = 42          # riproducibilita': stesso split ad ogni run


def _fit_logit_1d(x_prob: np.ndarray, y_prob: np.ndarray) -> tuple[float, float]:
    """Regressione logit(y) = alpha + beta*logit(x) (minimi quadrati)."""
    X = np.column_stack([np.ones(len(x_prob)), _logit(x_prob)])
    coef, *_ = np.linalg.lstsq(X, _logit(y_prob), rcond=None)
    return float(coef[0]), float(coef[1])


def _kfold_mae_logit(x_prob: np.ndarray, y_prob: np.ndarray,
                     k: int = N_FOLDS, seed: int = _CV_SEED) -> float:
    """MAE out-of-sample media k-fold della regressione logit(y)~logit(x)
    (Fase 69, bakeoff apertura~chiusura): stessa famiglia di stima gia' usata
    per ou_close (Fase 62/62-bis), qui validata su tutte le coppie reali
    invece che walk-forward (non e' una predizione nel tempo, e' un riempi-
    mento di buchi puntuali sparsi in tutte le stagioni)."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(x_prob))
    folds = np.array_split(idx, k)
    maes = []
    for i in range(k):
        test = folds[i]
        train = np.concatenate([folds[j] for j in range(k) if j != i])
        a, b = _fit_logit_1d(x_prob[train], y_prob[train])
        pred = _sigmoid(a + b * _logit(x_prob[test]))
        maes.append(float(np.abs(pred - y_prob[test]).mean()))
    return float(np.mean(maes))


def _kfold_mae_1x2(pc: np.ndarray, po: np.ndarray, k: int = N_FOLDS,
                   seed: int = _CV_SEED) -> float:
    """MAE k-fold sui 3 ESITI del 1X2 insieme (home/draw fittati, away per
    differenza+rinormalizzazione) -- rispecchia esattamente l'applicazione in
    build_open_sparse, cosi' l'errore dichiarato copre anche l'esito away
    (che non ha un fit proprio)."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(pc))
    folds = np.array_split(idx, k)
    maes = []
    for i in range(k):
        test, train = folds[i], np.concatenate([folds[j] for j in range(k) if j != i])
        a_h, b_h = _fit_logit_1d(pc[train, 0], po[train, 0])
        a_d, b_d = _fit_logit_1d(pc[train, 1], po[train, 1])
        ph = _sigmoid(a_h + b_h * _logit(pc[test, 0]))
        pdw = _sigmoid(a_d + b_d * _logit(pc[test, 1]))
        pa = np.clip(1 - ph - pdw, 1e-6, None)
        s = ph + pdw + pa
        pred = np.column_stack([ph / s, pdw / s, pa / s])
        maes.append(float(np.abs(pred - po[test]).mean()))
    return float(np.mean(maes))


def build_open_sparse() -> tuple[pd.DataFrame, float, float]:
    """Stima l'apertura per le partite sparse senza apertura vera (Fase 69).

    Bakeoff (5 metodi, 5-fold CV su tutte le coppie apertura/chiusura reali):
    identita', lineare pooled, LOGIT pooled (vincitore o pari ovunque),
    lineare per-lega, blend identita'+logit (mai meglio del singolo migliore).
    Dettaglio numerico nel diario (Fase 69) e nel docstring del modulo.
    """
    frames = []
    for lg in LEAGUES:
        df = database.read_snapshot(database.snapshot_path(lg))
        df["season"] = df["season"].astype(str)
        df["league"] = lg
        frames.append(df)
    all_df = pd.concat(frames, ignore_index=True)

    # ---- fit 1X2: home e draw diretti, away per differenza/rinormalizz. ---
    has_1x2 = all_df[["odds_home", "odds_draw", "odds_away", "odds_home_open",
                      "odds_draw_open", "odds_away_open"]].notna().all(axis=1)
    fit_1x2 = all_df[has_1x2]
    pc_1x2 = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                       for r in fit_1x2.itertuples()])
    po_1x2 = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                         r.odds_away_open)
                       for r in fit_1x2.itertuples()])
    a_h, b_h = _fit_logit_1d(pc_1x2[:, 0], po_1x2[:, 0])
    a_d, b_d = _fit_logit_1d(pc_1x2[:, 1], po_1x2[:, 1])
    mae_1x2 = _kfold_mae_1x2(pc_1x2, po_1x2)
    print(f"fit logit pooled 1X2 (n={len(fit_1x2)}): "
          f"home a={a_h:.4f} b={b_h:.4f} | draw a={a_d:.4f} b={b_d:.4f} | "
          f"MAE congiunto (3 esiti, home+draw fittati + away rinormalizzato) "
          f"{mae_1x2:.4f}")

    # ---- fit O/U --------------------------------------------------------
    has_ou = all_df[["odds_over25", "odds_under25", "odds_over25_open",
                     "odds_under25_open"]].notna().all(axis=1)
    fit_ou = all_df[has_ou]
    pc_ou = np.array([metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
                      for r in fit_ou.itertuples()])
    po_ou = np.array([metrics.devig_binary(r.odds_over25_open, r.odds_under25_open)[0]
                      for r in fit_ou.itertuples()])
    a_ou, b_ou = _fit_logit_1d(pc_ou, po_ou)
    mae_ou = _kfold_mae_logit(pc_ou, po_ou)
    print(f"fit logit pooled O/U  (n={len(fit_ou)}): "
          f"a={a_ou:.4f} b={b_ou:.4f} (MAE {mae_ou:.4f})")

    # ---- individua i buchi SPARSI (fuori dal gap sistemico O/U) ---------
    systemic = all_df["season"].isin(SYSTEMIC_OU_SEASONS)
    need_1x2 = all_df["odds_home_open"].isna() & all_df["odds_home"].notna()
    need_ou = (all_df["odds_over25_open"].isna() & ~systemic
              & all_df["odds_over25"].notna())
    targets = all_df[need_1x2 | need_ou].copy()

    rows = []
    for r in targets.itertuples():
        row = {"league": r.league, "season": r.season,
               "date": r.date.strftime("%Y-%m-%d"),
               "home_team": r.home_team, "away_team": r.away_team,
               "p_home_open_est": np.nan, "p_draw_open_est": np.nan,
               "p_away_open_est": np.nan,
               "p_over25_open_est": np.nan, "p_under25_open_est": np.nan}
        if pd.isna(r.odds_home_open) and pd.notna(r.odds_home):
            pc = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            ph = float(_sigmoid(a_h + b_h * _logit(pc[0])))
            pdw = float(_sigmoid(a_d + b_d * _logit(pc[1])))
            pa = max(1e-6, 1 - ph - pdw)
            s = ph + pdw + pa
            row["p_home_open_est"] = round(ph / s, 4)
            row["p_draw_open_est"] = round(pdw / s, 4)
            row["p_away_open_est"] = round(pa / s, 4)
        if pd.isna(r.odds_over25_open) and r.season not in SYSTEMIC_OU_SEASONS \
                and pd.notna(r.odds_over25):
            pco = metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
            po = float(_sigmoid(a_ou + b_ou * _logit(pco)))
            row["p_over25_open_est"] = round(po, 4)
            row["p_under25_open_est"] = round(1 - po, 4)
        rows.append(row)

    est = pd.DataFrame(rows).sort_values(["league", "season", "date"])
    print(f"\nopen_sparse: {len(est)} partite stimate (fuori dal gap sistemico O/U)")
    for r in est.itertuples():
        print(f"  {r.league:14s} {r.season} {r.date} {r.home_team}-{r.away_team}: "
              f"1X2={r.p_home_open_est}/{r.p_draw_open_est}/{r.p_away_open_est}  "
              f"OU={r.p_over25_open_est}")
    return est, mae_1x2, mae_ou


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
    cols = ["league", "season", "team", "squad_value_est", "method",
           "expected_median_err_pct"]
    est = pd.DataFrame(rows, columns=cols).sort_values(["league", "season", "team"])
    n_anch = (est["method"] == "anchored").sum()
    print(f"\nsquad_value: {len(est)} stime ({n_anch} anchored ~{ERR_ANCHORED:.0f}%, "
          f"{len(est)-n_anch} regression ~{ERR_REGRESSION:.0f}%)"
          + (" -- nessun buco residuo (Fase 70)" if not rows else ""))
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

    sparse, mae_1x2, mae_ou = build_open_sparse()
    sparse.to_csv(OPEN_SPARSE_PATH, index=False)
    print(f"\n-> {OPEN_SPARSE_PATH.relative_to(ROOT)}: {len(sparse)} partite "
          f"(MAE atteso 1X2 ~{mae_1x2:.4f}, O/U ~{mae_ou:.4f})")
    print("   ⚠️  STIME di modello (bakeoff logit pooled, Fase 69): vedi docs/DATI.md §Stime.")
    experiment_log.append_run(experiment_log.make_record(
        config={"source": "build_estimates_open_sparse",
                "model": "logit_pooled(chiusura->apertura)",
                "bakeoff_metodi": ["identita", "lineare_pooled", "logit_pooled",
                                  "lineare_perlega", "blend_identita_logit"],
                "n_folds": N_FOLDS},
        metrics_dict={"n_estimates": int(len(sparse)),
                      "mae_5fold_1x2": mae_1x2, "mae_5fold_ou": mae_ou},
        fingerprint=experiment_log.data_fingerprint(fit),
    ))
    print(f"Registrati in experiments/runs.jsonl. ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
