"""Fase 31 — Posta in palio, versione RICCA e su 8 stagioni.

La Fase 29 definiva "dead rubber" solo come "salva E fuori dall'Europa" (limbo di
meta' classifica) e ne catturava 12: sbagliato ai due ESTREMI, perche' contava
una squadra gia' RETROCESSA come "in lotta salvezza" e una gia' CAMPIONE come "in
corsa titolo". Qui la definizione corretta: una squadra e' DECISA se non ha piu'
NESSUNA corsa aperta, considerando entrambi gli estremi (gia' salva, gia'
retrocessa, gia' campione/qualificata). Stati distinti + molte combinazioni a
livello partita. Finestra estesa a 8 stagioni (2018-19 e 2019-20 incluse).

Domanda: escludendo le partite "decise", quanto diventa il gap col mercato? E il
gap e' diverso nelle varie combinazioni di posta in palio?

Uso:  python scripts/_run_stakes2.py     (8 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics

TEST_SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
B, SEED = 10_000, 31
_OI = {"H": 0, "D": 1, "A": 2}
TOTG = 38


def _worker(season):
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df.sort_values("date").reset_index(drop=True)


def team_state(p, R, board):
    """Stato di una squadra data la classifica (board = punti ordinati desc).
    Ritorna (settled: bool, etichetta)."""
    reach = 3 * R
    def line(rk):
        return board[rk] if len(board) > rk else 0
    safe_line = line(16)    # 17a: ultima salva
    releg_line = line(17)   # 18a: prima retrocessa
    euro_line = line(6)     # 7a: ~Europa
    title_line = line(0)    # 1a
    second_line = line(1)

    math_safe = p > releg_line + reach
    math_relegated = p + reach < safe_line
    relegation_open = (not math_safe) and (not math_relegated)
    europe_open = abs(p - euro_line) <= reach
    is_leader = p >= title_line
    champion = is_leader and (p - second_line) > reach
    title_open = (abs(p - title_line) <= reach) and (not champion)

    settled = (not relegation_open) and (not europe_open) and (not title_open)
    if math_relegated:
        lab = "retrocessa"
    elif champion:
        lab = "campione"
    elif not settled:
        lab = "in_corsa"
    elif math_safe and p >= euro_line:
        lab = "europa_decisa"
    else:
        lab = "salva_limbo"
    return settled, lab


def annotate(df):
    pts, played = {}, {}
    df = df.copy()
    df["giornata"] = np.minimum(np.arange(len(df)) // 10 + 1, TOTG)
    s_h, s_a, l_h, l_a = [], [], [], []
    for _, day in df.groupby(df["date"], sort=True):
        snap_p, snap_pl = dict(pts), dict(played)
        teams = set(snap_p) | set(day["home_team"]) | set(day["away_team"])
        board = sorted((snap_p.get(t, 0) for t in teams), reverse=True)
        for _, m in day.iterrows():
            for who, sl, ll in (("home", s_h, l_h), ("away", s_a, l_a)):
                t = m[f"{who}_team"]
                st, lab = team_state(snap_p.get(t, 0), TOTG - snap_pl.get(t, 0), board)
                sl.append(st); ll.append(lab)
        for _, m in day.iterrows():
            h, a, r = m["home_team"], m["away_team"], m["result"]
            pts[h] = pts.get(h, 0) + (3 if r == "H" else 1 if r == "D" else 0)
            pts[a] = pts.get(a, 0) + (3 if r == "A" else 1 if r == "D" else 0)
            played[h] = played.get(h, 0) + 1
            played[a] = played.get(a, 0) + 1
    df["settled_home"], df["settled_away"] = s_h, s_a
    df["lab_home"], df["lab_away"] = l_h, l_a
    df["n_settled"] = df["settled_home"].astype(int) + df["settled_away"].astype(int)
    return df


def ll_1x2(P, out):
    idx = [_OI[o] for o in out]
    return -np.log(np.clip(P[np.arange(len(out)), idx], 1e-15, 1))


def boot_mean(d, rng):
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def main():
    with Pool(min(8, len(TEST_SEASONS))) as pool:
        dfs = dict(pool.map(_worker, TEST_SEASONS))
    big = pd.concat([annotate(dfs[s]) for s in TEST_SEASONS], ignore_index=True)

    all_m = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_m)
    for s in TEST_SEASONS:
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase31_stakes2", "league": "serie_a", "test_season": s,
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, experiment_log.compute_metrics(dfs[s]), fp))

    out = big["result"].tolist()
    model = big[["m_home", "m_draw", "m_away"]].to_numpy()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in big.itertuples()])
    gap = ll_1x2(model, out) - ll_1x2(mkt, out)
    rng = np.random.default_rng(SEED)
    n = len(big)

    print("=" * 92)
    print(f"POSTA IN PALIO (ricca, 8 stagioni, n={n}) — gap = modello - mercato")
    print("=" * 92)
    labs = Counter(big["lab_home"]) + Counter(big["lab_away"])
    print("  Stati-squadra (su 2*n = %d):" % (2 * n),
          {k: labs[k] for k in ["in_corsa", "salva_limbo", "europa_decisa",
                                 "retrocessa", "campione"]})

    print(f"\n  {'categoria partita':<26}{'n':>7}{'gap medio':>12}{'CI95':>22}")
    cats = [
        ("entrambe in corsa", big["n_settled"] == 0),
        ("una decisa, una in corsa", big["n_settled"] == 1),
        ("entrambe decise", big["n_settled"] == 2),
        ("coinvolge una retrocessa", (big["lab_home"] == "retrocessa") | (big["lab_away"] == "retrocessa")),
        ("coinvolge una campione", (big["lab_home"] == "campione") | (big["lab_away"] == "campione")),
    ]
    for name, mask in cats:
        m = mask.to_numpy()
        if m.sum() < 5:
            print(f"  {name:<26}{m.sum():>7}{'(pochi)':>12}")
            continue
        mean, lo, hi = boot_mean(gap[m], rng)
        print(f"  {name:<26}{m.sum():>7}{mean:>+12.4f}   [{lo:+.4f}, {hi:+.4f}]")

    # Domanda chiave: escludendo le partite "decise", quanto diventa il gap?
    print("\n  Effetto sul GAP COMPLESSIVO escludendo le partite con squadre decise:")
    for name, keep in [("tutte le partite", np.ones(n, bool)),
                       ("escludendo 'entrambe decise'", (big["n_settled"] < 2).to_numpy()),
                       ("escludendo 'almeno una decisa'", (big["n_settled"] == 0).to_numpy()),
                       ("solo partite con >=1 decisa", (big["n_settled"] >= 1).to_numpy())]:
        mean, lo, hi = boot_mean(gap[keep], rng)
        print(f"    {name:<32}{keep.sum():>7}  gap {mean:+.4f}  [{lo:+.4f}, {hi:+.4f}]")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase31_stakes2", "league": "serie_a", "variant": "stakes2_summary",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23,
         "seasons": TEST_SEASONS},
        {"n_matches": n,
         "gap_all": float(gap.mean()),
         "gap_both_live": float(gap[(big["n_settled"] == 0).to_numpy()].mean()),
         "gap_one_settled": float(gap[(big["n_settled"] == 1).to_numpy()].mean()),
         "gap_both_settled": float(gap[(big["n_settled"] == 2).to_numpy()].mean()),
         "gap_excl_both_settled": float(gap[(big["n_settled"] < 2).to_numpy()].mean()),
         "n_both_settled": int((big["n_settled"] == 2).sum()),
         "n_any_settled": int((big["n_settled"] >= 1).sum()),
         **{f"n_state_{k}": int(labs[k]) for k in
            ["in_corsa", "salva_limbo", "europa_decisa", "retrocessa", "campione"]}}, fp))

    print("\n  Lettura: 'entrambe in corsa' e' il riferimento pulito. Se le partite con")
    print("  squadre decise hanno gap DIVERSO (piu' basso = il modello ci va meglio),")
    print("  escluderle alza il gap 'vero' — ma con n piccolo serve prudenza.")


if __name__ == "__main__":
    main()
