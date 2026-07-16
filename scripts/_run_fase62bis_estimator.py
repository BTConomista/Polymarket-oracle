"""Fase 62-bis — Spremere la stima della chiusura O/U (prima di pubblicarla).

La Fase 62 ha mostrato che la chiusura O/U mancante (2017-19) e' parzialmente
ricostruibile: M4 (recal + shift del motore, walk-forward per lega) taglia il
MAE del 33-41%. Prima di generare le stime per il 2017-19 (che l'utente vuole
pubblicare in data/estimates/, marcate come stime), si prova a migliorare:

  M4  logit(p_open) + shift-motore                (riferimento, Fase 62)
  E2  M4 con fit POOLED cross-lega                (la mappa 1X2->O/U e' fisica
                                                   della matrice DC: universale,
                                                   il pooling triplica il train)
  E3  logit(p_open) + Dlogit(H) + Dlogit(D) + Dlogit(A)   (il movimento 1X2
      grezzo: lascia ai DATI la mappa che M4 delega alla matrice DC)
  E4  E3 + shift-motore                           (entrambe le leve)
  E2/E3/E4 valutati sia per-lega sia pooled.

Stesso protocollo della Fase 62 (stesse righe, stesso walk-forward, stesso
bootstrap): i numeri sono confrontabili 1:1. Criterio di scelta: MAE vs
chiusura vera (fedelta' — e' il compito della stima), col log-loss come
controllo che non si stia peggiorando l'utilita' a valle. Disciplina multiple
testing (Fase 17): differenze piccole tra candidati vicini = si sceglie il
PIU' SEMPLICE, non il nominalmente migliore.

Uso:  python scripts/_run_fase62bis_estimator.py
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
    B, LEAGUES, WF_TEST, _boot_diff, _engine_shifts, _fit_linear,
    _load, _log_loss_binary, _logit, _predict_linear, _sigmoid,
)

SEED = 622


def _features(df: pd.DataFrame, shift: np.ndarray) -> dict[str, np.ndarray]:
    """Le feature candidate, tutte in spazio logit (vedi 📐 Fase 62)."""
    lo_open = _logit(df["p_over_o"])
    return {
        "lo_open": lo_open,
        "sh_engine": _logit(np.clip(df["p_over_o"] + shift, 1e-4, 1 - 1e-4)) - lo_open,
        "dH": _logit(df["pH_c"]) - _logit(df["pH_o"]),
        "dD": _logit(df["pD_c"]) - _logit(df["pD_o"]),
        "dA": _logit(df["pA_c"]) - _logit(df["pA_o"]),
    }


CANDIDATES: dict[str, list[str]] = {
    "M4": ["lo_open", "sh_engine"],
    "E3": ["lo_open", "dH", "dD", "dA"],
    "E4": ["lo_open", "sh_engine", "dH", "dD", "dA"],
}


def main() -> None:
    t0 = time.time()
    # Carica le 3 leghe una volta (inversioni incluse: la parte costosa).
    data: dict[str, pd.DataFrame] = {}
    feats: dict[str, dict[str, np.ndarray]] = {}
    for lg in LEAGUES:
        df = _load(lg)
        q_o, q_c = _engine_shifts(df)
        data[lg] = df
        feats[lg] = _features(df, q_c - q_o)
        print(f"  {lg}: {len(df)} partite pronte ({time.time()-t0:.0f}s)")

    rng = np.random.default_rng(SEED)
    results: dict[str, dict] = {}
    print(f"\n{'candidato':22s} {'lega':15s} {'MAE':>7s} {'corr':>6s} {'beta':>6s} "
          f"{'LL':>7s} {'d vs close (LL)':>24s}")
    for cname, cols in CANDIDATES.items():
        for pooled in (False, True):
            label = f"{cname}{'_pooled' if pooled else ''}"
            maes, lls = [], []
            for lg in LEAGUES:
                df, F = data[lg], feats[lg]
                lo_close = _logit(df["p_over_c"])
                pred = np.full(len(df), np.nan)
                for ts in WF_TEST:
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
                        ytr = lo_close[tr]
                    coef = _fit_linear(Xtr, ytr)
                    Xte = np.column_stack([F[c] for c in cols])[te]
                    pred[te] = _sigmoid(_predict_linear(coef, Xte))
                mask = ~np.isnan(pred)
                ph = pred[mask]
                pc = df["p_over_c"].to_numpy()[mask]
                po = df["p_over_o"].to_numpy()[mask]
                y = df["is_over"].to_numpy()[mask]
                mae = float(np.abs(ph - pc).mean())
                mv_p, mv_t = ph - po, pc - po
                corr = float(np.corrcoef(mv_p, mv_t)[0, 1])
                beta = float(np.cov(mv_t, mv_p)[0, 1] / mv_p.var())
                ll = _log_loss_binary(ph, y)
                d_c = _boot_diff(ll, _log_loss_binary(pc, y), rng)
                maes.append(mae); lls.append(float(ll.mean()))
                results.setdefault(label, {})[lg] = {
                    "mae": mae, "corr": corr, "beta": beta,
                    "logloss": float(ll.mean()), "d_vs_close": d_c}
                print(f"{label:22s} {lg:15s} {mae:7.4f} {corr:6.3f} {beta:6.2f} "
                      f"{ll.mean():7.4f} {d_c[0]:+.4f} [{d_c[1]:+.4f},{d_c[2]:+.4f}]")
            results[label]["mae_mean"] = float(np.mean(maes))
            print(f"{label:22s} {'MEDIA':15s} {np.mean(maes):7.4f}")

    print("\n=== CLASSIFICA (MAE medio 3 leghe, walk-forward 2021+) ===")
    for label in sorted(results, key=lambda k: results[k]["mae_mean"]):
        print(f"  {label:22s} {results[label]['mae_mean']:.4f}")

    fingerprint = experiment_log.data_fingerprint(
        pd.concat(data.values(), ignore_index=True))
    experiment_log.append_run(experiment_log.make_record(
        config={"source": "fase62bis_estimator", "candidates": list(CANDIDATES),
                "pooled_variants": True, "wf_test": WF_TEST,
                "bootstrap_B": B, "seed": SEED},
        metrics_dict=results,
        fingerprint=fingerprint,
    ))
    print(f"\nRegistrato in experiments/runs.jsonl (source=fase62bis_estimator). "
          f"Totale {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
