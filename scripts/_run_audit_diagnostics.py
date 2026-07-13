"""Fase 34 — Audit critico del modello: diagnostici + test economici delle leve emerse.

Nasce da una revisione riga-per-riga del codice (formule TUTTE corrette, nessun
errore) e cerca dove il ragionamento delle fasi precedenti sia stato superficiale
o dove leve mai testate possano ancora aiutare il modello ufficiale.

Tre diagnostici (numeri veri sui 6 backtest ufficiali) + due test post-hoc
leave-future-out (versione ECONOMICA, riusa la ricalibrazione per-classe della
Fase 10, nessuna modifica al modello):

  D1  vantaggio-casa per periodo (il modello lo sovrastima a fine stagione?).
  D2  pareggio per EQUILIBRIO |lam-mu| (dimensione mai testata: Fase 18 = totale).
  D3  copertura reale di squad_value (quanto era diluito il test della Fase 4c).
  A   test economico: ricalibrare il FINALE (35-38 / 32-38) migliora il log-loss?
  B   test economico: ricalibrare le partite EQUILIBRATE migliora il log-loss?

Regola di lettura (dichiarata prima): una leva e' "viva" (da portare nel modello)
solo se il Δ log-loss e' <0 con CI95 bootstrap che esclude lo zero; altrimenti e'
la trappola "calibrazione migliora ma log-loss no" (Fase 12b).

Uso:  python scripts/_run_audit_diagnostics.py   (6 backtest ~5min, poi analisi)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import calibration, experiment_log, metrics  # noqa: E402
from scripts.backtest import run_backtest         # noqa: E402

SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
CACHE = Path(__file__).resolve().parents[1] / "outputs"
B, SEED = 10_000, 34
_IDX = {"H": 0, "D": 1, "A": 2}


def _one(season):
    fp = CACHE / f"audit_bt_{season}.csv"
    if fp.exists():
        return pd.read_csv(fp, parse_dates=["date"])
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return df


def _devig_hd(df):
    mH = np.full(len(df), np.nan); mD = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            mH[i], mD[i] = p[0], p[1]
    return mH, mD


def _ll_rows(P, outc):
    P = np.clip(P, 1e-15, 1)
    y = np.array([_IDX[o] for o in outc])
    return -np.log(P[np.arange(len(y)), y])


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def _posthoc(df, mask_fn):
    """Ricalibrazione per-classe leave-future-out sul sottoinsieme mask_fn. Ritorna
    (base_ll_rows, recal_ll_rows, pesi medi)."""
    base, recal, ws = [], [], []
    for i, s in enumerate(SEASONS):
        if i == 0:
            continue
        past = df[df.season.astype(str).isin(SEASONS[:i])]
        ps = past[mask_fn(past)]
        cur = df[df.season.astype(str) == s]
        cs = cur[mask_fn(cur)]
        if len(ps) < 30 or len(cs) == 0:
            continue
        w = calibration.fit_class_recalibration(
            ps[["m_home", "m_draw", "m_away"]].to_numpy(), ps.result.tolist())
        ws.append(w)
        Pc = cs[["m_home", "m_draw", "m_away"]].to_numpy()
        base.append(_ll_rows(Pc, cs.result.tolist()))
        recal.append(_ll_rows(calibration.apply_class_recalibration(Pc, w), cs.result.tolist()))
    return np.concatenate(base), np.concatenate(recal), np.mean(ws, axis=0)


def main():
    with Pool(min(6, len(SEASONS))) as pool:
        frames = pool.map(_one, SEASONS)
    df = pd.concat(frames, ignore_index=True).sort_values(["season", "date"]).reset_index(drop=True)
    df["md"] = df.groupby("season").cumcount() // 10 + 1
    mH, mD = _devig_hd(df)
    df["mkt_home"], df["mkt_draw"] = mH, mD
    df["is_home"] = (df.result == "H").astype(float)
    df["is_draw"] = (df.result == "D").astype(float)
    df["balance"] = (df.exp_home_goals - df.exp_away_goals).abs()
    rng = np.random.default_rng(SEED)
    summary = {}

    # ---- D1 ----
    print("=" * 82)
    print("D1 — vantaggio-casa per periodo (bias = P(casa) - reale)")
    print("=" * 82)
    print(f"  {'periodo':<14}{'n':>5}{'reale':>8}{'modP(H)':>9}{'mktP(H)':>9}{'biasMod':>9}{'biasMkt':>9}")
    for name, mask in [("inizio 1-19", df.md <= 19), ("meta 20-31", (df.md >= 20) & (df.md <= 31)),
                       ("32-34", (df.md >= 32) & (df.md <= 34)), ("35-38", df.md >= 35)]:
        sub = df[mask]; q = sub.dropna(subset=["mkt_home"])
        print(f"  {name:<14}{len(sub):>5}{sub.is_home.mean():>8.3f}{sub.m_home.mean():>9.3f}"
              f"{q.mkt_home.mean():>9.3f}{sub.m_home.mean()-sub.is_home.mean():>+9.3f}"
              f"{q.mkt_home.mean()-q.is_home.mean():>+9.3f}")
    late = df[df.md >= 35]
    summary["d1_home_bias_late_model"] = float(late.m_home.mean() - late.is_home.mean())
    summary["d1_home_bias_late_market"] = float(late.dropna(subset=["mkt_home"]).mkt_home.mean()
                                                - late.dropna(subset=["mkt_home"]).is_home.mean())

    # ---- D2 ----
    print("\n" + "=" * 82)
    print("D2 — pareggio per EQUILIBRIO |lam-mu| (mai testato; Fase 18 usava il totale)")
    print("=" * 82)
    df["bq"] = pd.qcut(df.balance, 4, labels=["equil", "medio-b", "medio-a", "sbil"])
    print(f"  {'quartile':<10}{'n':>5}{'pariReale':>11}{'modP(pari)':>12}{'mktP(pari)':>12}{'mod-reale':>11}")
    for lab in ["equil", "medio-b", "medio-a", "sbil"]:
        sub = df[df.bq == lab]; q = sub.dropna(subset=["mkt_draw"])
        print(f"  {lab:<10}{len(sub):>5}{sub.is_draw.mean():>11.3f}{sub.m_draw.mean():>12.3f}"
              f"{q.mkt_draw.mean():>12.3f}{sub.m_draw.mean()-sub.is_draw.mean():>+11.3f}")
    eq = df[df.bq == "equil"]
    summary["d2_draw_deficit_balanced_model"] = float(eq.m_draw.mean() - eq.is_draw.mean())
    summary["d2_draw_deficit_balanced_market"] = float(eq.dropna(subset=["mkt_draw"]).mkt_draw.mean()
                                                       - eq.dropna(subset=["mkt_draw"]).is_draw.mean())

    # ---- D3 ----
    print("\n" + "=" * 82)
    print("D3 — copertura squad_value (dove manca -> covariata neutra)")
    print("=" * 82)
    allm_full = loader.load_league("serie_a")   # tutte le stagioni: fingerprint canonica
    allm = allm_full[allm_full.season.astype(str).isin(SEASONS)]
    both = (allm.home_squad_value.notna() & allm.away_squad_value.notna())
    print(f"  copertura (entrambi i valori) su {len(allm)} partite: {both.mean():.1%}")
    summary["d3_squad_value_coverage"] = float(both.mean())

    # ---- A/B: test economici ----
    print("\n" + "=" * 82)
    print("TEST ECONOMICI post-hoc (leave-future-out): Δ log-loss (recal - base)")
    print("regola: VIVA solo se Δ<0 con CI95<0")
    print("=" * 82)
    med = df.balance.median()
    tests = [
        ("A_finale_35_38", lambda d: d.md >= 35),
        ("A2_finale_32_38", lambda d: d.md >= 32),
        ("B_equilibrio_mediana", lambda d, m=med: d.balance < m),
        ("RIF_globale_fase10", lambda d: np.ones(len(d), bool)),
    ]
    for name, fn in tests:
        base, recal, w = _posthoc(df, fn)
        mean, lo, hi, pneg = _boot(recal - base, rng)
        verd = "VIVA(CI<0)" if hi < 0 else ("promettente" if mean < 0 else "morta")
        print(f"  {name:<22} n={len(base):>4}  w=({w[0]:.2f},{w[1]:.2f},{w[2]:.2f})  "
              f"Δ={mean:+.4f} CI[{lo:+.4f},{hi:+.4f}] P={pneg:.0%}  -> {verd}")
        summary[f"posthoc_{name}_delta"] = mean
        summary[f"posthoc_{name}_ci_lo"] = lo
        summary[f"posthoc_{name}_ci_hi"] = hi

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase34_audit", "league": "serie_a", "variant": "diagnostics",
         "bootstrap_B": B, "bootstrap_seed": SEED, **{k: v for k, v in CFG.items()
         if k != "promoted_prior"}, "promoted_prior": 0.23},
        {"n_matches": int(len(df)), **summary},
        experiment_log.data_fingerprint(allm_full)))
    print("\nRun registrato in experiments/runs.jsonl (source=fase34_audit).")


if __name__ == "__main__":
    main()
