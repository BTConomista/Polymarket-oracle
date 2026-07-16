"""Fase 62 — Si puo' RICOSTRUIRE la chiusura O/U 2.5 che manca nel 2017-19?

Dopo la Fase 61 l'unico buco rimasto negli snapshot e' l'O/U delle stagioni
2017-18 e 2018-19 (3 leghe): li' esiste UNA sola linea O/U (BbAv, pre-match,
timing "apertura") mentre l'1X2 ha ENTRAMBE le linee (Pinnacle PS/PSC). La
domanda dell'utente: con i modelli che abbiamo, si puo' STIMARE la linea
mancante (la chiusura O/U) da cio' che c'e' — O/U apertura + movimento 1X2
apertura->chiusura?

BACKTEST (metodo S1.2/S1.3): sulle 21 (lega, stagione) 2019-20+ dove abbiamo
TUTTE e quattro le linee, si finge di non avere la chiusura O/U e la si stima;
poi si confronta con quella vera. Candidati (dal piu' economico):

  M0 identita'      p_hat = p_open  (baseline: quanto si muove davvero la linea?)
  M1 engine-shift   inverti (1X2_o, OU_o) -> (lam_o, mu_o) -> q_o; inverti
                    (1X2_c, OU_o) -> q_c;  p_hat = p_open + (q_c - q_o).
                    Il motore market-implied (Fase 26) misura SOLO lo shift
                    dell'O/U implicato dal movimento 1X2 e lo applica
                    all'apertura vera: il bias sistematico dell'inversione si
                    cancella nella differenza.
  M2 engine-abs     p_hat = over2.5 dalla matrice invertita su (1X2_c, OU_o)
                    (versione assoluta di M1: NON cancella il bias — controllo).
  M3 recal WF       logit(p_hat) = a + b*logit(p_open), fit walk-forward sulle
                    stagioni precedenti della stessa lega (SENZA 1X2: quanta
                    parte del movimento e' ricalibrazione sistematica?).
  M4 recal+shift    come M3 + c*(shift M1 in logit) — le due leve insieme.

METRICHE per candidato:
  - fedelta': MAE vs p_close vero (devig); "movimento catturato" = corr e beta
    di (p_hat - p_open) su (p_close - p_open);
  - utilita' a valle: log-loss sugli esiti Over reali di p_open / p_close vero /
    p_hat, con bootstrap appaiato (B=10000) sulle differenze chiave.

Onesta': anche il candidato migliore produce una STIMA, non un prezzo di
mercato: l'eventuale uso nel 2017-19 va tenuto SEPARATO dalle colonne quota
reali (mai mischiare stima e dato, regola di progetto).

Uso:  python scripts/_run_fase62_ou_close_est.py          (tutte e 3 le leghe)
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
from src.models import market_implied as mi            # noqa: E402

B, SEED = 10_000, 62
RHO = -0.06          # correzione punteggi bassi del motore (Fase 24/26)
LEAGUES = ["serie_a", "premier_league", "la_liga"]
# Stagioni con ENTRAMBE le linee O/U (vedi mappa Fase 61): 2019-20 in poi.
BOTH_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
# Walk-forward per M3/M4: prima stagione di test = 2021 (train >= 1 stagione).
WF_TEST = ["2021", "2122", "2223", "2324", "2425", "2526"]


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def _load(league: str) -> pd.DataFrame:
    """Righe con TUTTE e 4 le linee, gia' devigate + esito Over reale."""
    df = database.read_snapshot(database.snapshot_path(league))
    df = df[df["season"].astype(str).isin(BOTH_SEASONS)].copy()
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25",
            "odds_home_open", "odds_draw_open", "odds_away_open",
            "odds_over25_open", "odds_under25_open"]
    df = df.dropna(subset=need).reset_index(drop=True)

    p1x2_c = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                       for r in df.itertuples()])
    p1x2_o = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open,
                                         r.odds_away_open)
                       for r in df.itertuples()])
    df[["pH_c", "pD_c", "pA_c"]] = p1x2_c
    df[["pH_o", "pD_o", "pA_o"]] = p1x2_o
    df["p_over_c"] = [metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
                      for r in df.itertuples()]
    df["p_over_o"] = [metrics.devig_binary(r.odds_over25_open,
                                           r.odds_under25_open)[0]
                      for r in df.itertuples()]
    df["is_over"] = ((df["home_goals"] + df["away_goals"]) >= 3).astype(int)
    df["season"] = df["season"].astype(str)
    return df


def _engine_over(pH, pD, pA, p_over) -> float:
    """P(Over 2.5) dalla matrice DC invertita su (1X2, O/U) — Fase 26."""
    lam, mu = mi.implied_lambda_mu(pH, pD, pA, p_over, RHO)
    M = mi.score_matrix(lam, mu, RHO)
    return mi._1x2_over(M)[3]


def _engine_shifts(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(q_open, q_close): O/U del motore su (1X2_open, OU_open) e su
    (1X2_close, OU_open). Lo shift M1 e' q_close - q_open."""
    q_o = np.empty(len(df))
    q_c = np.empty(len(df))
    for i, r in enumerate(df.itertuples()):
        q_o[i] = _engine_over(r.pH_o, r.pD_o, r.pA_o, r.p_over_o)
        q_c[i] = _engine_over(r.pH_c, r.pD_c, r.pA_c, r.p_over_o)
    return q_o, q_c


def _fit_linear(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """OLS con intercetta (minimi quadrati in spazio logit)."""
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def _predict_linear(coef: np.ndarray, X: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    return A @ coef


def _log_loss_binary(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, dtype=float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot_diff(la: np.ndarray, lb: np.ndarray, rng) -> tuple[float, float, float, float]:
    """Bootstrap appaiato su media(la - lb): (delta, lo, hi, P(delta<0))."""
    d = la - lb
    n = len(d)
    idx = rng.integers(0, n, size=(B, n))
    boots = d[idx].mean(axis=1)
    return (float(d.mean()), float(np.percentile(boots, 2.5)),
            float(np.percentile(boots, 97.5)), float((boots < 0).mean()))


def run_league(league: str) -> tuple[dict, str]:
    t0 = time.time()
    df = _load(league)
    fingerprint = experiment_log.data_fingerprint(df)
    print(f"\n=== {league} — {len(df)} partite, stagioni {sorted(df.season.unique())} ===")

    # Movimento reale della linea O/U (quanto c'e' da catturare)
    move = df["p_over_c"].to_numpy() - df["p_over_o"].to_numpy()
    print(f"  movimento open->close O/U: media {move.mean():+.4f}, "
          f"|.| medio {np.abs(move).mean():.4f}, sd {move.std():.4f}")

    # M1/M2: shift del motore (costoso: 2 inversioni per riga)
    q_o, q_c = _engine_shifts(df)
    shift = q_c - q_o
    m1 = np.clip(df["p_over_o"].to_numpy() + shift, 1e-4, 1 - 1e-4)
    m2 = np.clip(q_c, 1e-4, 1 - 1e-4)

    # M3/M4: ricalibrazione walk-forward in logit (per lega)
    m3 = np.full(len(df), np.nan)
    m4 = np.full(len(df), np.nan)
    lo_open = _logit(df["p_over_o"])
    lo_close = _logit(df["p_over_c"])
    lo_shift = _logit(np.clip(df["p_over_o"] + shift, 1e-4, 1 - 1e-4)) - lo_open
    for ts in WF_TEST:
        tr = df.index[df.season < ts].to_numpy()
        te = df.index[df.season == ts].to_numpy()
        if len(tr) == 0 or len(te) == 0:
            continue
        c3 = _fit_linear(lo_open[tr].reshape(-1, 1), lo_close[tr])
        m3[te] = _sigmoid(_predict_linear(c3, lo_open[te].reshape(-1, 1)))
        X4 = np.column_stack([lo_open, lo_shift])
        c4 = _fit_linear(X4[tr], lo_close[tr])
        m4[te] = _sigmoid(_predict_linear(c4, X4[te]))

    wf = ~np.isnan(m3)          # righe con predizione walk-forward (2021+)
    y = df["is_over"].to_numpy()
    p_open = df["p_over_o"].to_numpy()
    p_close = df["p_over_c"].to_numpy()

    cands = {"M0_identita": p_open, "M1_engine_shift": m1, "M2_engine_abs": m2,
             "M3_recal_wf": m3, "M4_recal_shift_wf": m4}

    rng = np.random.default_rng(SEED)
    out = {"league": league, "n": int(len(df)), "n_wf": int(wf.sum()),
           "move_mean": float(move.mean()), "move_abs": float(np.abs(move).mean()),
           "move_sd": float(move.std())}
    print(f"  {'candidato':18s} {'MAE vs close':>12s} {'corr mov.':>9s} "
          f"{'beta':>6s} | {'LL':>7s} {'d vs open':>22s} {'d vs close':>22s}")

    ll_open_all = _log_loss_binary(p_open, y)
    ll_close_all = _log_loss_binary(p_close, y)
    for name, p_hat in cands.items():
        mask = wf if name.startswith(("M3", "M4")) else np.ones(len(df), bool)
        ph, pc, po, yy = p_hat[mask], p_close[mask], p_open[mask], y[mask]
        mae = float(np.abs(ph - pc).mean())
        pred_move = ph - po
        true_move = pc - po
        if pred_move.std() > 1e-9:
            corr = float(np.corrcoef(pred_move, true_move)[0, 1])
            beta = float(np.cov(true_move, pred_move)[0, 1] / pred_move.var())
        else:
            corr, beta = float("nan"), float("nan")
        ll = _log_loss_binary(ph, yy)
        d_o = _boot_diff(ll, _log_loss_binary(po, yy), rng)
        d_c = _boot_diff(ll, _log_loss_binary(pc, yy), rng)
        out[name] = {"mae_vs_close": mae, "corr_move": corr, "beta_move": beta,
                     "logloss": float(ll.mean()),
                     "d_vs_open": d_o, "d_vs_close": d_c}
        print(f"  {name:18s} {mae:12.4f} {corr:9.3f} {beta:6.2f} | "
              f"{ll.mean():7.4f} {d_o[0]:+.4f} [{d_o[1]:+.4f},{d_o[2]:+.4f}] "
              f"{d_c[0]:+.4f} [{d_c[1]:+.4f},{d_c[2]:+.4f}]")

    # riferimento: quanto vale la chiusura vera rispetto all'apertura
    d_ref = _boot_diff(ll_close_all, ll_open_all, rng)
    out["close_vs_open"] = d_ref
    print(f"  {'(close vero)':18s} {'—':>12s} {'—':>9s} {'—':>6s} | "
          f"{ll_close_all.mean():7.4f} {d_ref[0]:+.4f} [{d_ref[1]:+.4f},{d_ref[2]:+.4f}]"
          f"  <- valore informativo reale della chiusura")
    print(f"  ({time.time()-t0:.0f}s)")
    return out, fingerprint


def main() -> None:
    t0 = time.time()
    results = [run_league(lg) for lg in LEAGUES]

    print("\n=== SINTESI (utilita' della stima vs apertura, log-loss) ===")
    for r, _ in results:
        best = min((k for k in r if k.startswith("M")),
                   key=lambda k: r[k]["logloss"])
        print(f"  {r['league']:15s} migliore: {best} "
              f"(LL {r[best]['logloss']:.4f}; close vero "
              f"{r['close_vs_open'][0]:+.4f} vs open)")

    for r, fingerprint in results:
        experiment_log.append_run(experiment_log.make_record(
            config={"source": "fase62_ou_close_est", "league": r["league"],
                    "rho": RHO, "seasons": BOTH_SEASONS, "wf_test": WF_TEST,
                    "bootstrap_B": B, "seed": SEED},
            metrics_dict={k: v for k, v in r.items() if k != "league"},
            fingerprint=fingerprint,
        ))
    print(f"\nRegistrati {len(results)} run in experiments/runs.jsonl "
          f"(source=fase62_ou_close_est). Totale {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
