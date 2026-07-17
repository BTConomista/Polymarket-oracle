"""Fase 66 — Stimare il valore rosa mancante: backtest di fedelta' PRIMA di pubblicare.

Le 73 celle (stagione, squadra) senza `squad_value` (SA 29, Liga 40, PL 4 —
buchi del datalake Transfermarkt, Fasi 4a/60/63) sono il piu' grosso vuoto
residuo nelle colonne esistenti. Protocollo stime (CLAUDE.md §5): prima di
pubblicare una stima se ne misura la fedelta' dove la verita' ESISTE.

DISEGNO. Sulle 467 celle NOTE, leave-one-out: si nasconde una cella, la si
stima dalle altre, si confronta. Il bersaglio e' il LOG-rapporto col mediano
di lega-stagione (i valori spaziano 30M-1.3B: l'errore sensato e' relativo):

    y = log(v) - log(mediana_lega_stagione)

Candidati (dal piu' economico), su DUE fronti (per-lega e pooled, principio 9):

  A0 mediana        y_hat = 0 (ogni squadra vale il mediano di lega) — baseline
  A1 ancora         y_hat = media dei y della STESSA squadra nelle stagioni
                    adiacenti note (t-1, t+1) — dove esistono
  A2 regressione    y_hat = a + b*pts_pg + c*gd_pg + d*xgd_pg + e*promoted
                    (rendimento della stagione STESSA, dichiarato: per un
                    completamento storico l'informazione in-season e' lecita)
  A3 = A2 + ancora  la regressione con l'ancora come feature (impute 0 + flag)

Validazioni: (i) leave-one-out standard; (ii) leave-TEAM-out (tutte le stagioni
di una squadra nascoste insieme) — il caso Lazio, che non ha MAI un'ancora.

Metriche: errore assoluto mediano e p90 in % del valore vero.

Uso:  python scripts/_run_fase66_squad_value_est.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database                          # noqa: E402
from src.evaluation import experiment_log              # noqa: E402

LEAGUES = ["serie_a", "premier_league", "la_liga"]
SEED = 66


def team_season_table() -> pd.DataFrame:
    """Una riga per (league, season, team): valore rosa (o NaN) + rendimento
    della stagione (punti/gara, diff. reti, diff. xG) + flag promossa."""
    rows = []
    for lg in LEAGUES:
        df = database.read_snapshot(database.snapshot_path(lg))
        df["season"] = df["season"].astype(str)
        seasons = sorted(df["season"].unique())
        teams_by_season = {s: set(g.home_team) | set(g.away_team)
                           for s, g in df.groupby("season")}
        for s, g in df.groupby("season"):
            for team in teams_by_season[s]:
                h = g[g.home_team == team]
                a = g[g.away_team == team]
                gp = len(h) + len(a)
                pts = (3 * (h.home_goals > h.away_goals).sum()
                       + (h.home_goals == h.away_goals).sum()
                       + 3 * (a.away_goals > a.home_goals).sum()
                       + (a.home_goals == a.away_goals).sum())
                gd = (h.home_goals.sum() + a.away_goals.sum()
                      - h.away_goals.sum() - a.home_goals.sum())
                xgd = (h.home_xg.sum() + a.away_xg.sum()
                       - h.away_xg.sum() - a.home_xg.sum())
                v = pd.concat([h.home_squad_value, a.away_squad_value]).dropna()
                prev = seasons[seasons.index(s) - 1] if seasons.index(s) > 0 else None
                promoted = (team not in teams_by_season.get(prev, set())
                            if prev else False)
                rows.append({
                    "league": lg, "season": s, "team": team,
                    "value": float(v.iloc[0]) if len(v) else np.nan,
                    "pts_pg": pts / gp, "gd_pg": gd / gp, "xgd_pg": xgd / gp,
                    "promoted": float(promoted),
                    "first_season": float(prev is None),
                })
    t = pd.DataFrame(rows)
    med = t.groupby(["league", "season"])["value"].transform("median")
    t["y"] = np.log(t["value"]) - np.log(med)
    t["log_med"] = np.log(med)
    return t


def anchor_feature(t: pd.DataFrame, known_mask: np.ndarray) -> np.ndarray:
    """Media dei y noti della stessa squadra nelle stagioni adiacenti."""
    seasons = sorted(t["season"].unique())
    idx_of = {s: i for i, s in enumerate(seasons)}
    anchor = np.full(len(t), np.nan)
    by_key = {}
    for i, r in enumerate(t.itertuples()):
        if known_mask[i] and np.isfinite(r.y):
            by_key[(r.league, r.team, idx_of[r.season])] = r.y
    for i, r in enumerate(t.itertuples()):
        si = idx_of[r.season]
        vals = [by_key.get((r.league, r.team, si + d)) for d in (-1, +1)]
        vals = [v for v in vals if v is not None]
        if vals:
            anchor[i] = float(np.mean(vals))
    return anchor


def _fit_ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def _pred_ols(coef: np.ndarray, X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X]) @ coef


def _design(t: pd.DataFrame, anchor: np.ndarray) -> dict[str, np.ndarray]:
    a_filled = np.where(np.isfinite(anchor), anchor, 0.0)
    a_flag = np.isfinite(anchor).astype(float)
    return {
        "A2": np.column_stack([t.pts_pg, t.gd_pg, t.xgd_pg, t.promoted]),
        "A3": np.column_stack([t.pts_pg, t.gd_pg, t.xgd_pg, t.promoted,
                               a_filled, a_flag]),
    }


def evaluate(t: pd.DataFrame, mode: str) -> dict:
    """LOO ('cell') o leave-team-out ('team'): errori % per candidato/fronte."""
    known = t.index[np.isfinite(t["y"])].to_numpy()
    rng = np.random.default_rng(SEED)
    preds: dict[str, dict[int, float]] = {}

    groups = ([("cell", [i]) for i in known] if mode == "cell" else
              [(k, list(g.index.intersection(known)))
               for k, g in t.groupby(["league", "team"]) if len(g.index.intersection(known))])

    for _, hidden in groups:
        hidden = np.asarray(hidden)
        mask_known = np.isfinite(t["y"].to_numpy()).copy()
        mask_known[hidden] = False
        anchor = anchor_feature(t, mask_known)
        D = _design(t, anchor)
        tr = np.where(mask_known)[0]
        for name, X in D.items():
            for pooled in (True, False):
                label = f"{name}{'_pooled' if pooled else '_perlega'}"
                for i in hidden:
                    if pooled:
                        use = tr
                    else:
                        use = tr[t["league"].to_numpy()[tr] == t["league"].iloc[i]]
                    coef = _fit_ols(X[use], t["y"].to_numpy()[use])
                    preds.setdefault(label, {})[i] = float(_pred_ols(coef, X[[i]])[0])
        # A0 / A1 (senza fit)
        for i in hidden:
            preds.setdefault("A0_mediana", {})[i] = 0.0
            preds.setdefault("A1_ancora", {})[i] = (
                float(anchor[i]) if np.isfinite(anchor[i]) else np.nan)

    out = {}
    y = t["y"].to_numpy()
    for label, d in preds.items():
        idx = np.array(sorted(d))
        p = np.array([d[i] for i in idx])
        ok = np.isfinite(p)
        # errore percentuale sul VALORE: |exp(pred-y) - 1|
        err = np.abs(np.exp(p[ok] - y[idx][ok]) - 1.0)
        out[label] = {
            "coverage": float(ok.mean()), "n": int(ok.sum()),
            "median_err_pct": (float(np.median(err) * 100) if len(err) else float("nan")),
            "p90_err_pct": (float(np.percentile(err, 90) * 100) if len(err) else float("nan")),
        }
    return out


def main() -> None:
    t0 = time.time()
    t = team_season_table()
    known = int(np.isfinite(t["y"]).sum())
    holes = t[~np.isfinite(t["y"])]
    print(f"celle: {len(t)} totali, {known} note, {len(holes)} buchi "
          f"({holes.groupby('league').size().to_dict()})")

    results = {}
    for mode, label in [("cell", "leave-one-out"), ("team", "leave-TEAM-out")]:
        print(f"\n=== {label} ===")
        res = evaluate(t, mode)
        results[mode] = res
        print(f"  {'candidato':16s} {'copertura':>9s} {'err mediano':>11s} {'p90':>8s}")
        for name in sorted(res, key=lambda k: res[k]["median_err_pct"]):
            r = res[name]
            print(f"  {name:16s} {r['coverage']:9.0%} {r['median_err_pct']:10.1f}% "
                  f"{r['p90_err_pct']:7.1f}%")

    experiment_log.append_run(experiment_log.make_record(
        config={"source": "fase66_squad_value_est", "seed": SEED,
                "candidates": ["A0_mediana", "A1_ancora", "A2±pooled", "A3±pooled"],
                "n_known": known, "n_holes": int(len(holes))},
        metrics_dict=results,
        fingerprint=experiment_log.data_fingerprint(
            pd.concat([database.read_snapshot(database.snapshot_path(lg))
                       for lg in LEAGUES], ignore_index=True)),
    ))
    print(f"\nRegistrato in runs.jsonl (source=fase66_squad_value_est). "
          f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
