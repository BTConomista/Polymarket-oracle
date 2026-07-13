"""Punto 3 — le covariate (in particolare stakes) aiutano il CANALE-PAREGGIO?

Domanda: dopo la Fase 35 (che condiziona il boost-pareggio su |lam-mu|), resta un
effetto delle covariate sui pareggi INDIPENDENTE dal volume/equilibrio? L'esempio
tipico: partite 'cruciali' (entrambe in corsa) con piu' cautela tattica -> piu'
pareggi. Diagnostico ECONOMICO (principio: prima la versione economica) sui residui
di pareggio della variante phi_equilibrio gia' in cache, PRIMA di ogni chirurgia sul
modello.

Se lo stakes spiegasse i pareggi oltre l'equilibrio, il residuo (reale - modello)
mostrerebbe un pattern per categoria (entrambe in corsa / mismatch / entrambe
decise), con correlazione sopra la soglia-rumore. Altrimenti: canale-pareggio gia'
saturo, niente chirurgia.

Uso:  python scripts/_run_draw_covariate.py   (usa i CSV Fase 35 in cache; registra)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log         # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]


def main():
    allm = loader.load_league("serie_a")
    meta = allm[["season", "date", "home_team", "away_team", "home_settled", "away_settled"]].copy()
    meta["season"] = meta.season.astype(str)
    frames = []
    for s in SEASONS:
        fp = CACHE / f"db_phi_equilibrio_{s}.csv"
        if not fp.exists():
            raise SystemExit("Manca la cache Fase 35 (db_phi_equilibrio_*). "
                             "Esegui prima scripts/_run_draw_balance.py")
        d = pd.read_csv(fp, parse_dates=["date"]); d["season"] = s
        frames.append(d)
    df = pd.concat(frames, ignore_index=True).merge(
        meta, on=["season", "home_team", "away_team"], how="left")
    df["is_draw"] = (df.result == "D").astype(float)
    df["resid"] = df.is_draw - df.m_draw
    df["balance"] = (df.exp_home_goals - df.exp_away_goals).abs()
    df["scat"] = np.where((df.home_settled == 0) & (df.away_settled == 0), "entrambe_in_corsa",
                 np.where((df.home_settled == 1) & (df.away_settled == 1), "entrambe_decise", "mismatch"))

    print("=" * 80)
    print("PUNTO 3 — residuo PAREGGIO (reale - modello Fase35) per categoria stakes")
    print("=" * 80)
    print(f"  {'categoria':<20}{'n':>6}{'pari reale':>12}{'m_draw':>9}{'residuo':>10}")
    stats = {}
    for c in ["entrambe_in_corsa", "mismatch", "entrambe_decise"]:
        sub = df[df.scat == c]
        print(f"  {c:<20}{len(sub):>6}{sub.is_draw.mean():>12.3f}{sub.m_draw.mean():>9.3f}{sub.resid.mean():>+10.4f}")
        stats[f"resid_{c}"] = float(sub.resid.mean()); stats[f"n_{c}"] = int(len(sub))
    cr = float(np.corrcoef((df.scat == "entrambe_in_corsa").astype(float), df.resid)[0, 1])
    mm = float(np.corrcoef((df.scat == "mismatch").astype(float), df.resid)[0, 1])
    thr = 2.0 / np.sqrt(len(df))
    print(f"\n  corr(entrambe_in_corsa, residuo) = {cr:+.4f}")
    print(f"  corr(mismatch,          residuo) = {mm:+.4f}")
    print(f"  soglia-rumore 2*SE = {thr:.4f} (n={len(df)})")
    verdict = ("nessun canale-pareggio da covariate: entrambe le corr sotto il rumore"
               if abs(cr) < thr and abs(mm) < thr else "possibile segnale (verificare walk-forward)")
    print(f"\n  VERDETTO: {verdict}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "punto3_draw_covariate", "league": "serie_a", "variant": "diagnostic",
         "half_life_days": 365, "shrinkage": 1.5, "shots_blend": 0.75,
         "blend_signal": "xg", "promoted_prior": 0.23},
        {"n_matches": int(len(df)), "corr_crucial": cr, "corr_mismatch": mm,
         "noise_threshold": float(thr), **stats},
        experiment_log.data_fingerprint(allm)))
    print("\nRun registrato (source=punto3_draw_covariate).")


if __name__ == "__main__":
    main()
