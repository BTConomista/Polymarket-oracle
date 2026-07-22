"""Fase 73 — La dispersione max-vs-media aiuta a stimare la chiusura O/U?

La correzione di etichettatura O/U 2017-19 (l'unica linea e' un'APERTURA reale,
BbAv, non una chiusura) sblocca un input mai usato: le colonne BbMx>2.5/BbMx<2.5
(Betbrain MASSIMO) esistono per il 2017-19 accanto a BbAv (media). La loro
DISPERSIONE (premio best-vs-media) misura il disaccordo tra book all'apertura,
un possibile predittore di quanto la linea si muovera' verso la chiusura --
un'informazione che E3 (solo movimento 1X2) non usa.

Analogo nel fit (2019-20+): Max>2.5/Max<2.5 (massimo) vs Avg>2.5/Avg<2.5 (media).
Distribuzioni confrontabili tra le due ere (verificato: premio medio ~0.042
Betbrain vs ~0.038 panel recente).

Candidati (walk-forward pooled, STESSO protocollo di Fase 62-bis/72 -> numeri
confrontabili 1:1 con E3/E3_pooled gia' in runs.jsonl):

  E3  [1, logit(p_open), dH, dD, dA]                    (riferimento)
  E9  E3 + disp                                          (dispersione additiva)
  E10 E3 + disp*logit(p_open)                            (la dispersione modula
                                                          la fiducia nell'apertura)
  E11 E3 + disp + disp*logit(p_open)                     (entrambe)

disp = 0.5*[(max_over/avg_over - 1) + (max_under/avg_under - 1)], premio best-vs-
media medio sui due lati (>=0). Feature di MAGNITUDINE (non segnata): l'ipotesi
e' che moduli quanto la linea si muove, non la direzione (quella la da' il 1X2).

Criterio: MAE vs chiusura vera. Si adotta E9/E10/E11 solo se batte E3 con margine
reale (disciplina multiple-testing: fra candidati vicini vince il piu' semplice).

Uso:  python scripts/_run_fase73_ou_close_disp.py
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, sources                       # noqa: E402
from src.evaluation import experiment_log, metrics           # noqa: E402
from scripts._run_fase62_ou_close_est import (                # noqa: E402
    B, LEAGUES, WF_TEST, _boot_diff, _load, _log_loss_binary, _logit,
    _sigmoid,
)

SEED = 732
ROOT = Path(__file__).resolve().parents[1]
FROZEN_DIR = ROOT / "data" / "football_data_raw"


def _raw_season(lg: str, code: str) -> pd.DataFrame:
    if lg == "serie_a":
        return pd.read_csv(FROZEN_DIR / f"serie_a_{code}.csv", encoding="latin-1")
    bundle = json.load(open(ROOT / "files" / f"football_data_{lg}_bundle.json"))
    return pd.read_csv(io.StringIO(bundle[f"{lg}_{code}.csv"]), encoding="latin-1")


def _dispersion(lg: str, seasons: list[str]) -> pd.DataFrame:
    """Premio best-vs-media dell'O/U all'apertura, per (season, home, away).

    2019-20+: Max>2.5/Avg>2.5 (panel football-data). 2017-19: BbMx/BbAv (Betbrain).
    Ritorna colonne canonicalizzate per il join con lo snapshot."""
    frames = []
    for code in seasons:
        raw = _raw_season(lg, code)
        raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
        if "Max>2.5" in raw.columns:
            ao, au, mo, mu = "Avg>2.5", "Avg<2.5", "Max>2.5", "Max<2.5"
        else:
            ao, au, mo, mu = "BbAv>2.5", "BbAv<2.5", "BbMx>2.5", "BbMx<2.5"
        a_o = pd.to_numeric(raw[ao], errors="coerce")
        a_u = pd.to_numeric(raw[au], errors="coerce")
        m_o = pd.to_numeric(raw[mo], errors="coerce")
        m_u = pd.to_numeric(raw[mu], errors="coerce")
        disp = 0.5 * ((m_o / a_o - 1.0) + (m_u / a_u - 1.0))
        frames.append(pd.DataFrame({
            "season": str(code),
            "home_team": raw["HomeTeam"].astype(str).str.strip().map(sources.canonical_team),
            "away_team": raw["AwayTeam"].astype(str).str.strip().map(sources.canonical_team),
            "disp": disp.values,
        }))
    return pd.concat(frames, ignore_index=True)


def _load_with_disp(lg: str) -> pd.DataFrame:
    """_load (Fase 62) + colonna disp agganciata dai grezzi."""
    df = _load(lg)
    seasons = sorted(df["season"].astype(str).unique())
    disp = _dispersion(lg, seasons)
    merged = df.merge(disp, on=["season", "home_team", "away_team"], how="left",
                      validate="one_to_one")
    return merged


def _fit_linear(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def _predict_linear(coef: np.ndarray, X: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    return A @ coef


def _features(df: pd.DataFrame) -> dict[str, np.ndarray]:
    lo_open = _logit(df["p_over_o"])
    disp = df["disp"].to_numpy()
    return {
        "lo_open": lo_open,
        "dH": _logit(df["pH_c"]) - _logit(df["pH_o"]),
        "dD": _logit(df["pD_c"]) - _logit(df["pD_o"]),
        "dA": _logit(df["pA_c"]) - _logit(df["pA_o"]),
        "disp": disp,
        "disp_x_open": disp * lo_open,
    }


E3 = ["lo_open", "dH", "dD", "dA"]
CANDIDATES = {
    "E3": E3,
    "E9_disp": E3 + ["disp"],
    "E10_disp_x_open": E3 + ["disp_x_open"],
    "E11_both": E3 + ["disp", "disp_x_open"],
}


def main() -> None:
    t0 = time.time()
    data, feats = {}, {}
    for lg in LEAGUES:
        df = _load_with_disp(lg)
        n_disp = int(df["disp"].notna().sum())
        data[lg] = df
        feats[lg] = _features(df)
        print(f"  {lg}: {len(df)} partite, disp non-null {n_disp} ({time.time()-t0:.0f}s)")

    rng = np.random.default_rng(SEED)
    results: dict[str, dict] = {}
    print(f"\n{'candidato':20s} {'lega':15s} {'MAE':>7s} {'corr':>6s} "
          f"{'d vs E3 (MAE)':>14s}")

    # baseline E3 per lega (per il confronto appaiato)
    e3_pred: dict[str, np.ndarray] = {}
    for cname, cols in CANDIDATES.items():
        maes = []
        for lg in LEAGUES:
            df, F = data[lg], feats[lg]
            pred = np.full(len(df), np.nan)
            for ts in WF_TEST:
                te = df.index[df.season == ts].to_numpy()
                if len(te) == 0:
                    continue
                Xtr, ytr = [], []
                for lg2 in LEAGUES:
                    d2, F2 = data[lg2], feats[lg2]
                    tr2 = d2.index[(d2.season < ts) & d2["disp"].notna()].to_numpy()
                    Xtr.append(np.column_stack([F2[c] for c in cols])[tr2])
                    ytr.append(_logit(d2["p_over_c"])[tr2])
                Xtr = np.vstack(Xtr); ytr = np.concatenate(ytr)
                coef = _fit_linear(Xtr, ytr)
                Xte = np.column_stack([F[c] for c in cols])[te]
                pred[te] = _sigmoid(_predict_linear(coef, Xte))
            mask = ~np.isnan(pred) & df["disp"].notna().to_numpy()
            ph = pred[mask]
            pc = df["p_over_c"].to_numpy()[mask]
            po = df["p_over_o"].to_numpy()[mask]
            mae = float(np.abs(ph - pc).mean())
            corr = float(np.corrcoef(ph - po, pc - po)[0, 1])
            maes.append(mae)
            if cname == "E3":
                e3_pred[lg] = pred
                dstr = ""
            else:
                # differenza appaiata di |err| vs E3 sulle STESSE righe
                e3 = e3_pred[lg][mask]
                d_ae = np.abs(ph - pc) - np.abs(e3 - pc)
                dd = _boot_diff(np.abs(ph - pc), np.abs(e3 - pc), rng)
                dstr = f"{dd[0]:+.4f} [{dd[1]:+.4f},{dd[2]:+.4f}]"
            results.setdefault(cname, {})[lg] = {"mae": mae, "corr": corr}
            print(f"{cname:20s} {lg:15s} {mae:7.4f} {corr:6.3f} {dstr:>14s}")
        results[cname]["mae_mean"] = float(np.mean(maes))
        print(f"{cname:20s} {'MEDIA':15s} {np.mean(maes):7.4f}")

    print("\n=== CLASSIFICA (MAE medio 3 leghe, walk-forward 2021+) ===")
    for label in sorted(results, key=lambda k: results[k]["mae_mean"]):
        print(f"  {label:20s} {results[label]['mae_mean']:.4f}")

    fingerprint = experiment_log.data_fingerprint(
        pd.concat([d.drop(columns=["disp"]) for d in data.values()], ignore_index=True))
    experiment_log.append_run(experiment_log.make_record(
        config={"source": "fase73_ou_close_disp", "candidates": list(CANDIDATES),
                "feature_new": "dispersione max-vs-media (BbMx/BbAv, Max/Avg)",
                "wf_test": WF_TEST, "bootstrap_B": B, "seed": SEED},
        metrics_dict=results, fingerprint=fingerprint,
    ))
    print(f"\nRegistrato in experiments/runs.jsonl (source=fase73_ou_close_disp). "
          f"Totale {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
