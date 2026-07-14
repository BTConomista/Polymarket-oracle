"""Fase 41 — Bakeoff per-mercato: quale MODELLO vince su ogni mercato Tier 1.

Studio di fattibilita' del "portafoglio di specialisti" (CLAUDE.md principio 8):
invece di un modello unico per tutti i mercati, si valuta OGNI mercato con piu'
modelli e si sceglie il migliore per quel mercato. Qui il bakeoff su ~20 mercati
Tier 1, walk-forward 6 stagioni:

  - baseline        : frequenza in-sample dell'esito (costante ottima a posteriori);
  - DC (gol+xG)     : matrice ricostruita dai λ,μ del backtest ufficiale (rho -0.05);
  - market-implied  : λ,μ invertiti dalle quote 1X2+O/U del match (rho -0.06).

(Per i mercati 1X2/pari il DC+φ35 della Fase 35 e' il migliore, gia' dimostrato
alle Fasi 35/39: qui non si ri-deriva, si annota.)

Onesta': la matrice del DC e' RICOSTRUITA dai λ,μ salvati con rho fisso -0.05 (il
backtest non salva la matrice); l'errore di ricostruzione vs le prob. 1X2/O2.5/GG
salvate e' stampato come controllo (piccolo -> lo studio di fattibilita' regge). I
mercati derivati NON hanno quote nei dati (come il GG/NG): confronto vs baseline.

Uso:  python scripts/_run_markets_bakeoff.py    (usa i backtest in cache)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402
from src.models import market_implied as mi        # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO_DC, RHO_MI = -0.05, -0.06
B, SEED = 10_000, 41
MAXG = mi.MAX_GOALS

# mercati BINARI: nome -> (chiave in derive_markets, funzione esito(hg,ag)->bool)
BIN = {
    "O/U 1.5": ("over_1.5", lambda h, a: h + a >= 2),
    "O/U 2.5": ("over_2.5", lambda h, a: h + a >= 3),
    "O/U 3.5": ("over_3.5", lambda h, a: h + a >= 4),
    "GG/NG": ("btts", lambda h, a: (h >= 1) & (a >= 1)),
    "1X": ("dc_1x", lambda h, a: h >= a),
    "2X": ("dc_2x", lambda h, a: a >= h),
    "12": ("dc_12", lambda h, a: h != a),
    "casa O0.5": ("home_ov_0.5", lambda h, a: h >= 1),
    "casa O1.5": ("home_ov_1.5", lambda h, a: h >= 2),
    "ospite O0.5": ("away_ov_0.5", lambda h, a: a >= 1),
    "ospite O1.5": ("away_ov_1.5", lambda h, a: a >= 2),
    "clean sheet casa": ("cs_home", lambda h, a: a == 0),
    "clean sheet ospite": ("cs_away", lambda h, a: h == 0),
    "casa vince a 0": ("wtn_home", lambda h, a: (h > a) & (a == 0)),
    "casa +2": ("home_by_2plus", lambda h, a: (h - a) >= 2),
    "ospite +2": ("away_by_2plus", lambda h, a: (a - h) >= 2),
    "pari/dispari (disp)": ("odd_total", lambda h, a: ((h + a) % 2) == 1),
}


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_base_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    ok = np.isfinite(df[["odds_home", "odds_draw", "odds_away",
                         "odds_over", "odds_under"]].to_numpy()).all(axis=1)
    return df[ok].reset_index(drop=True)


def _ll(p, y):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _boot(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m < 0).mean())


def main():
    df = _load()
    hg = df.home_goals.to_numpy(); ag = df.away_goals.to_numpy()
    n = len(df)

    # matrici per riga: DC (da λ,μ salvati) e market-implied (da quote)
    dc_mats, mi_mats = [], []
    for r in df.itertuples():
        dc_mats.append(mi.score_matrix(r.exp_home_goals, r.exp_away_goals, RHO_DC))
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over, r.odds_under)
        lam, mu = mi.implied_lambda_mu(pH, pD, pA, pO, RHO_MI)
        mi_mats.append(mi.score_matrix(lam, mu, RHO_MI))
    dc_der = [mi.derive_markets(M) for M in dc_mats]
    mi_der = [mi.derive_markets(M) for M in mi_mats]

    # controllo ricostruzione DC vs prob salvate
    err = max(
        np.abs(np.array([d["home_win"] for d in dc_der]) - df.m_home).max(),
        np.abs(np.array([d["draw"] for d in dc_der]) - df.m_draw).max(),
        np.abs(np.array([d["over_2.5"] for d in dc_der]) - df.m_over).max(),
        np.abs(np.array([d["btts"] for d in dc_der]) - df.m_btts).max())
    print(f"[controllo] errore max ricostruzione matrice DC vs prob salvate = {err:.4f}\n")

    rng = np.random.default_rng(SEED)
    print("=" * 90)
    print("FASE 41 — BAKEOFF PER-MERCATO (log-loss walk-forward, 6 stagioni, n=%d)" % n)
    print("Per ogni mercato: baseline / DC / market-implied. Grassetto = migliore.")
    print("=" * 90)
    print(f"  {'mercato':<22}{'baseline':>10}{'DC':>10}{'mkt-impl':>10}   {'MIGLIORE':<14}{'Δ best vs DC (CI)':>22}")
    rows = {}

    def report(name, base_ll, dc_ll, mi_ll):
        best = min([("baseline", base_ll.mean()), ("DC", dc_ll.mean()),
                    ("market-implied", mi_ll.mean())], key=lambda x: x[1])
        # Δ del migliore-non-DC vs DC (se il migliore e' il DC, Δ=0)
        if best[0] == "market-implied":
            mean, lo, hi, _ = _boot(mi_ll - dc_ll, rng); ci = f"[{mean:+.4f}: {lo:+.4f},{hi:+.4f}]"
        elif best[0] == "baseline":
            mean, lo, hi, _ = _boot(base_ll - dc_ll, rng); ci = f"[{mean:+.4f}: {lo:+.4f},{hi:+.4f}]"
        else:
            ci = "—"
        print(f"  {name:<22}{base_ll.mean():>10.4f}{dc_ll.mean():>10.4f}{mi_ll.mean():>10.4f}   "
              f"{best[0]:<14}{ci:>22}")
        rows[name] = {"baseline": float(base_ll.mean()), "DC": float(dc_ll.mean()),
                      "market_implied": float(mi_ll.mean()), "best": best[0]}

    # 1X2 (3-classi) — baseline in-sample per stagione
    yidx = np.array([{"H": 0, "D": 1, "A": 2}[o] for o in df.result])
    def multi_ll(P):
        return -np.log(np.clip(P[np.arange(n), yidx], 1e-15, 1))
    base_1x2 = np.zeros(n)
    for s in SEASONS:
        m = (df.season == s).to_numpy()
        fr = np.array([ (yidx[m] == k).mean() for k in range(3)])
        base_1x2[m] = -np.log(np.clip(fr[yidx[m]], 1e-15, 1))
    dc_1x2 = multi_ll(np.array([[d["home_win"], d["draw"], d["away_win"]] for d in dc_der]))
    mi_1x2 = multi_ll(np.array([[d["home_win"], d["draw"], d["away_win"]] for d in mi_der]))
    report("1X2", base_1x2, dc_1x2, mi_1x2)

    # binari
    for name, (key, fn) in BIN.items():
        y = fn(hg, ag).astype(float)
        base = np.zeros(n)
        for s in SEASONS:
            m = (df.season == s).to_numpy(); base[m] = _ll(np.full(m.sum(), y[m].mean()), y[m])
        dc = _ll(np.array([d[key] for d in dc_der]), y)
        mim = _ll(np.array([d[key] for d in mi_der]), y)
        report(name, base, dc, mim)

    # multigol (3-classi)
    tot = hg + ag
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    def mg_ll(der):
        P = np.array([[d["mg_0_1"], d["mg_2_3"], d["mg_4plus"]] for d in der])
        return -np.log(np.clip(P[np.arange(n), ymg], 1e-15, 1))
    base_mg = np.zeros(n)
    for s in SEASONS:
        m = (df.season == s).to_numpy(); fr = np.array([(ymg[m] == c).mean() for c in range(3)])
        base_mg[m] = -np.log(np.clip(fr[ymg[m]], 1e-15, 1))
    report("multigol (0-1/2-3/4+)", base_mg, mg_ll(dc_der), mg_ll(mi_der))

    # risultato esatto
    hc = np.minimum(hg, MAXG); acc = np.minimum(ag, MAXG)
    def cs_ll(mats):
        return np.array([-np.log(max(mats[k][hc[k], acc[k]], 1e-15)) for k in range(n)])
    base_cs = np.zeros(n)
    for s in SEASONS:
        m = (df.season == s).to_numpy()
        freq = np.zeros((MAXG + 1, MAXG + 1))
        for a2, b2 in zip(hc[m], acc[m]):
            freq[a2, b2] += 1
        freq /= freq.sum()
        base_cs[m] = np.array([-np.log(max(freq[hc[k], acc[k]], 1e-15)) for k in np.where(m)[0]])
    report("risultato esatto", base_cs, cs_ll(dc_mats), cs_ll(mi_mats))

    # --- portafoglio di specialisti ---
    print("\n" + "=" * 90)
    print("PORTAFOGLIO DI SPECIALISTI (modello migliore per mercato):")
    from collections import Counter
    cnt = Counter(v["best"] for v in rows.values())
    for model in ["DC", "market-implied", "baseline"]:
        mk = [m for m, v in rows.items() if v["best"] == model]
        print(f"  {model:<16} ({cnt[model]:2d} mercati): {', '.join(mk)}")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase41_markets_bakeoff", "league": "serie_a", "variant": "specialist_bakeoff",
         "rho_dc": RHO_DC, "rho_mi": RHO_MI, "reconstruction_error": float(err),
         "bootstrap_B": B, "bootstrap_seed": SEED},
        {"n_matches": n, **{f"{m}__{k}": v for m, r in rows.items() for k, v in r.items() if k != "best"},
         **{f"best__{m}": r["best"] for m, r in rows.items()}},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase41_markets_bakeoff).")


if __name__ == "__main__":
    main()
