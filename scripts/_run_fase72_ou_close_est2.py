"""Fase 72 — Si puo' spremere ANCORA la stima E3 pooled (Fase 62-bis)?

L'utente vuole "migliorare al massimo" la stima della chiusura O/U 2.5
2017-19 prima di accettarla come tetto dei dati (Fase A/D del piano
CACCIA_OU_2017_19.md chiuse/rischiose). E3 pooled resta il riferimento
adottato (`data/estimates/ou_close_2017_19.csv`, MAE walk-forward ~0.0117):

  E3  logit(p_open) + Dlogit(H) + Dlogit(D) + Dlogit(A)   (riferimento)

Candidati nuovi, ciascuno una leva ORTOGONALE a E3 (una cosa alla volta):

  E5  E3 + dH*dA            interazione: le due favorite si accorciano/
                            allungano insieme (partita aperta) o in direzioni
                            opposte (solo un lato cambia) — E3 e' lineare nei
                            3 movimenti separati, non vede questa curvatura.
  E6  E3 + season_frac      frazione di stagione trascorsa (rank data / n
                            partite lega-stagione, 0=inizio, 1=fine): la
                            Fase 30 ha trovato un cambio STRUTTURALE reale
                            nelle giornate finali (vantaggio-casa crolla) —
                            possibile che anche il movimento O/U catturato
                            da E3 vari nella stessa finestra.
  E7  E3 ridge              stesso disegno di E3, L2 invece di OLS puro
                            (alpha piccolo, grid 0.3/1/3/10): controllo di
                            robustezza — con 5 parametri su ~8000 righe
                            l'overfitting e' gia' improbabile, quindi ci si
                            aspetta un pareggio, non un guadagno.
  E8  GBM(E3 features)      gradient boosting (shallow) sulle stesse 4
                            feature di E3: cattura curvature/interazioni
                            automaticamente. Le Fasi 21-23 hanno gia' trovato
                            che il GBM non batte modelli lineari su
                            mercato/esiti — qui il compito e' diverso
                            (mimare un prezzo, non predire un esito), quindi
                            vale la pena il test invece di assumere lo stesso
                            risultato.

Stesso protocollo di Fase 62-bis (stesse righe — 2019-20+, 3 leghe — stesso
walk-forward WF_TEST, stesso pooling cross-lega, stesso bootstrap B):
i numeri sono confrontabili 1:1 con E3/E3_pooled gia' in runs.jsonl.
Criterio: MAE vs chiusura vera (fedelta', il compito della stima); si adotta
un candidato nuovo SOLO se batte E3 pooled con margine reale (non rumore) —
altrimenti resta l'attuale (disciplina multiple-testing, si preferisce il
piu' semplice fra candidati vicini).

Uso:  python scripts/_run_fase72_ou_close_est2.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import experiment_log                     # noqa: E402
from scripts._run_fase62_ou_close_est import (                # noqa: E402
    LEAGUES, WF_TEST, B, _boot_diff, _load, _log_loss_binary, _logit,
    _sigmoid,
)

SEED = 722
RIDGE_ALPHAS = [0.3, 1.0, 3.0, 10.0]


def _fit_linear(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def _fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    """Ridge con intercetta NON penalizzata (standard)."""
    A = np.column_stack([np.ones(len(X)), X])
    p = A.shape[1]
    penalty = np.eye(p) * alpha
    penalty[0, 0] = 0.0
    coef = np.linalg.solve(A.T @ A + penalty, A.T @ y)
    return coef


def _predict_linear(coef: np.ndarray, X: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    return A @ coef


def _season_frac(df: pd.DataFrame) -> np.ndarray:
    """Rank della data dentro (lega, stagione), normalizzato 0..1."""
    out = np.empty(len(df))
    dt = pd.to_datetime(df["date"])
    for season in df["season"].unique():
        m = (df["season"] == season).to_numpy()
        order = dt[m].rank(method="average").to_numpy()
        out[m] = (order - 1) / max(order.max() - 1, 1)
    return out


def _features(df: pd.DataFrame) -> dict[str, np.ndarray]:
    lo_open = _logit(df["p_over_o"])
    dH = _logit(df["pH_c"]) - _logit(df["pH_o"])
    dD = _logit(df["pD_c"]) - _logit(df["pD_o"])
    dA = _logit(df["pA_c"]) - _logit(df["pA_o"])
    return {
        "lo_open": lo_open, "dH": dH, "dD": dD, "dA": dA,
        "dHA": dH * dA,
        "season_frac": _season_frac(df),
    }


E3_COLS = ["lo_open", "dH", "dD", "dA"]
CANDIDATES: dict[str, list[str]] = {
    "E3": E3_COLS,                              # riferimento (Fase 62-bis)
    "E5_interact": E3_COLS + ["dHA"],
    "E6_season": E3_COLS + ["season_frac"],
}


def _wf_predict(data, feats, cols, pooled, fit_fn) -> dict[str, np.ndarray]:
    """Predizione walk-forward pooled/per-lega per un set di colonne feature."""
    preds = {lg: np.full(len(data[lg]), np.nan) for lg in LEAGUES}
    for ts in WF_TEST:
        for lg in LEAGUES:
            df, F = data[lg], feats[lg]
            te = df.index[df.season == ts].to_numpy()
            if len(te) == 0:
                continue
            if pooled:
                Xtr, ytr = [], []
                for lg2 in LEAGUES:
                    d2, F2 = data[lg2], feats[lg2]
                    tr2 = d2.index[d2.season < ts].to_numpy()
                    Xtr.append(np.column_stack([F2[c] for c in cols])[tr2])
                    ytr.append(_logit(d2["p_over_c"])[tr2])
                Xtr = np.vstack(Xtr); ytr = np.concatenate(ytr)
            else:
                tr = df.index[df.season < ts].to_numpy()
                Xtr = np.column_stack([F[c] for c in cols])[tr]
                ytr = _logit(df["p_over_c"])[tr]
            coef = fit_fn(Xtr, ytr)
            Xte = np.column_stack([F[c] for c in cols])[te]
            preds[lg][te] = _sigmoid(_predict_linear(coef, Xte))
    return preds


def _eval_candidate(label, data, preds, rng, results) -> None:
    maes = []
    for lg in LEAGUES:
        df = data[lg]
        mask = ~np.isnan(preds[lg])
        ph = preds[lg][mask]
        pc = df["p_over_c"].to_numpy()[mask]
        po = df["p_over_o"].to_numpy()[mask]
        y = df["is_over"].to_numpy()[mask]
        mae = float(np.abs(ph - pc).mean())
        mv_p, mv_t = ph - po, pc - po
        corr = float(np.corrcoef(mv_p, mv_t)[0, 1]) if mv_p.std() > 1e-9 else float("nan")
        ll = _log_loss_binary(ph, y)
        d_c = _boot_diff(ll, _log_loss_binary(pc, y), rng)
        maes.append(mae)
        results.setdefault(label, {})[lg] = {
            "mae": mae, "corr": corr, "logloss": float(ll.mean()), "d_vs_close": d_c}
        print(f"{label:22s} {lg:15s} {mae:7.4f} {corr:6.3f} {ll.mean():7.4f} "
              f"{d_c[0]:+.4f} [{d_c[1]:+.4f},{d_c[2]:+.4f}]")
    results[label]["mae_mean"] = float(np.mean(maes))
    print(f"{label:22s} {'MEDIA':15s} {np.mean(maes):7.4f}")


def _run_gbm(data, feats, rng, results) -> None:
    from sklearn.ensemble import GradientBoostingRegressor

    label = "E8_gbm_pooled"
    preds = {lg: np.full(len(data[lg]), np.nan) for lg in LEAGUES}
    for ts in WF_TEST:
        Xtr, ytr = [], []
        for lg2 in LEAGUES:
            d2, F2 = data[lg2], feats[lg2]
            tr2 = d2.index[d2.season < ts].to_numpy()
            Xtr.append(np.column_stack([F2[c] for c in E3_COLS])[tr2])
            ytr.append(_logit(d2["p_over_c"])[tr2])
        Xtr = np.vstack(Xtr); ytr = np.concatenate(ytr)
        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=2, learning_rate=0.05,
            subsample=0.8, random_state=SEED)
        model.fit(Xtr, ytr)
        for lg in LEAGUES:
            df, F = data[lg], feats[lg]
            te = df.index[df.season == ts].to_numpy()
            if len(te) == 0:
                continue
            Xte = np.column_stack([F[c] for c in E3_COLS])[te]
            preds[lg][te] = _sigmoid(model.predict(Xte))
    _eval_candidate(label, data, preds, rng, results)


def main() -> None:
    t0 = time.time()
    data: dict[str, pd.DataFrame] = {}
    feats: dict[str, dict[str, np.ndarray]] = {}
    for lg in LEAGUES:
        df = _load(lg)
        data[lg] = df
        feats[lg] = _features(df)
        print(f"  {lg}: {len(df)} partite pronte ({time.time()-t0:.0f}s)")

    rng = np.random.default_rng(SEED)
    results: dict[str, dict] = {}
    print(f"\n{'candidato':22s} {'lega':15s} {'MAE':>7s} {'corr':>6s} "
          f"{'LL':>7s} {'d vs close (LL)':>24s}")

    # E3 (riferimento) ed E5/E6: pooled, OLS -- confrontabili 1:1 con Fase 62-bis
    for cname, cols in CANDIDATES.items():
        preds = _wf_predict(data, feats, cols, pooled=True, fit_fn=_fit_linear)
        _eval_candidate(f"{cname}_pooled", data, preds, rng, results)

    # E7: E3 pooled + ridge, grid di alpha
    for alpha in RIDGE_ALPHAS:
        preds = _wf_predict(data, feats, E3_COLS, pooled=True,
                            fit_fn=lambda X, y, a=alpha: _fit_ridge(X, y, a))
        _eval_candidate(f"E7_ridge_a{alpha}_pooled", data, preds, rng, results)

    # E8: GBM pooled sulle feature di E3
    try:
        _run_gbm(data, feats, rng, results)
    except ImportError:
        print("scikit-learn non disponibile: salto E8_gbm_pooled")

    print("\n=== CLASSIFICA (MAE medio 3 leghe, walk-forward 2021+) ===")
    for label in sorted(results, key=lambda k: results[k]["mae_mean"]):
        print(f"  {label:22s} {results[label]['mae_mean']:.4f}")

    fingerprint = experiment_log.data_fingerprint(
        pd.concat(data.values(), ignore_index=True))
    experiment_log.append_run(experiment_log.make_record(
        config={"source": "fase72_ou_close_est2",
                "candidates": list(results), "ridge_alphas": RIDGE_ALPHAS,
                "wf_test": WF_TEST, "bootstrap_B": B, "seed": SEED},
        metrics_dict=results,
        fingerprint=fingerprint,
    ))
    print(f"\nRegistrato in experiments/runs.jsonl (source=fase72_ou_close_est2). "
          f"Totale {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
