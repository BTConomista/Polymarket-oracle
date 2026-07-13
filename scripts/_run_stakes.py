"""Fase 29 — Posta in palio dalla classifica: i "dead rubber" spiegano il gap?

La Fase 28 ha mostrato che il finale di stagione e' piu' difficile per TUTTI, con
un indizio (non concluso) che il modello ci perda un po' di piu' del mercato. Se
la causa e' la MOTIVAZIONE (squadre gia' salve e fuori dall'Europa che non hanno
piu' nulla in gioco), allora il gap dovrebbe essere maggiore proprio nelle
partite "dead rubber" — e questo si puo' testare SENZA dati esterni, derivando la
posta in palio dalla classifica a ogni giornata.

Definizione (euristica di raggiungibilita', pulita nel finale dove le gare
rimaste R sono poche): per ogni squadra, con la classifica PRIMA della partita,
  - reach = 3*R (punti ancora ottenibili)
  - fighting_relegation = (punti - linea_salvezza[18a]) <= reach   (rischia/lotta)
  - chasing_europe      = punti >= linea_europa[7a] - reach        (puo' arrivarci
    o e' gia' sopra, quindi in corsa titolo/Europa)
  - dead_rubber = NON fighting_relegation AND NON chasing_europe   (limbo mid-table)
Partita "dead" = ENTRAMBE le squadre in dead_rubber (niente in gioco per nessuno).

Test: il gap (modello - mercato, 1X2) e' maggiore nelle partite dead vs live,
soprattutto nelle ultime giornate? CI bootstrap. E' un DIAGNOSTICO (come Fase
13/20): se c'e' segnale, la posta in palio diventa una covariata candidata.

Uso:  python scripts/_run_stakes.py     (6 backtest; ~alcuni minuti)
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader
from src.evaluation import experiment_log, metrics

TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
CFG = dict(half_life_days=365, shrinkage=1.5, shots_blend=0.75,
           blend_signal="xg", promoted_prior=(0.23, 0.23))
B, SEED = 10_000, 29
_OI = {"H": 0, "D": 1, "A": 2}
N_TEAMS = 20
TOTAL_GAMES = 2 * (N_TEAMS - 1)   # 38


def _worker(season):
    from scripts.backtest import run_backtest
    df = run_backtest("serie_a", season, CFG["half_life_days"], shrinkage=CFG["shrinkage"],
                      shots_blend=CFG["shots_blend"], blend_signal=CFG["blend_signal"],
                      promoted_prior=CFG["promoted_prior"], verbose=False)
    df["season"] = season
    return season, df.sort_values("date").reset_index(drop=True)


def annotate_stakes(df: pd.DataFrame) -> pd.DataFrame:
    """Aggiunge dead_home, dead_away, match_dead usando la classifica PRIMA di
    ogni partita (punti/gare-giocate dai match precedenti della stagione)."""
    pts = {}          # punti correnti per squadra
    played = {}       # gare giocate
    df = df.copy()
    df["giornata"] = np.minimum(np.arange(len(df)) // 10 + 1, TOTAL_GAMES)
    dead_h, dead_a = [], []
    # processa per data: la classifica "prima" e' quella al termine delle date
    # precedenti (le partite di stessa data usano lo stesso snapshot).
    for _, day in df.groupby(df["date"], sort=True):
        snap_pts = dict(pts); snap_played = dict(played)
        # linee di classifica dallo snapshot (0 per squadre non ancora presenti)
        teams = set(snap_pts) | set(day["home_team"]) | set(day["away_team"])
        board = sorted((snap_pts.get(t, 0) for t in teams), reverse=True)
        def line(rank):
            return board[rank] if len(board) > rank else 0
        safety = line(17)   # 18a posizione (indice 17): prima retrocessa
        europe = line(6)    # 7a posizione (indice 6): ~ Europa
        for _, m in day.iterrows():
            for who, lst in (("home", dead_h), ("away", dead_a)):
                t = m[f"{who}_team"]
                p = snap_pts.get(t, 0)
                R = TOTAL_GAMES - snap_played.get(t, 0)
                reach = 3 * R
                fighting = (p - safety) <= reach
                chasing = p >= (europe - reach)
                lst.append(bool((not fighting) and (not chasing)))
        # aggiorna la classifica coi risultati di oggi
        for _, m in day.iterrows():
            h, a, r = m["home_team"], m["away_team"], m["result"]
            pts[h] = pts.get(h, 0) + (3 if r == "H" else 1 if r == "D" else 0)
            pts[a] = pts.get(a, 0) + (3 if r == "A" else 1 if r == "D" else 0)
            played[h] = played.get(h, 0) + 1
            played[a] = played.get(a, 0) + 1
    df["dead_home"] = dead_h
    df["dead_away"] = dead_a
    df["match_dead"] = df["dead_home"] & df["dead_away"]       # entrambe
    df["match_any_dead"] = df["dead_home"] | df["dead_away"]   # almeno una
    return df


def ll_1x2(P, out):
    idx = [_OI[o] for o in out]
    return -np.log(np.clip(P[np.arange(len(out)), idx], 1e-15, 1))


def boot_diff(a, b, rng):
    ma = a[rng.integers(0, len(a), (B, len(a)))].mean(axis=1)
    mb = b[rng.integers(0, len(b), (B, len(b)))].mean(axis=1)
    d = ma - mb
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    with Pool(6) as pool:
        dfs = dict(pool.map(_worker, TEST_SEASONS))
    big = pd.concat([annotate_stakes(dfs[s]) for s in TEST_SEASONS], ignore_index=True)

    all_m = loader.load_league("serie_a")
    fp = experiment_log.data_fingerprint(all_m)
    for s in TEST_SEASONS:
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase29_stakes", "league": "serie_a", "test_season": s,
             **{k: v for k, v in CFG.items() if k != "promoted_prior"},
             "promoted_prior": 0.23}, experiment_log.compute_metrics(dfs[s]), fp))

    out = big["result"].tolist()
    model = big[["m_home", "m_draw", "m_away"]].to_numpy()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in big.itertuples()])
    gap = ll_1x2(model, out) - ll_1x2(mkt, out)
    gio = big["giornata"].to_numpy()
    late = gio >= 32

    rng = np.random.default_rng(SEED)
    print("=" * 92)
    print("POSTA IN PALIO — gap modello-mercato nei 'dead rubber' vs partite 'live'")
    print("dead = squadra gia' salva E fuori dalla corsa Europa (dalla classifica)")
    print("gap = modello - mercato; negativo = il modello e' MIGLIORE del mercato")
    print("=" * 92)

    for defn, col in [("ENTRAMBE le squadre dead", "match_dead"),
                      ("ALMENO UNA squadra dead", "match_any_dead")]:
        dead = big[col].to_numpy()
        print(f"\n[{defn}]  dead: {dead.sum()}/{len(dead)} ({dead.mean():.1%}); "
              f"nel finale (g.>=32): {(dead & late).sum()}/{late.sum()}")
        print(f"  {'sottoinsieme':<26}{'n dead':>8}{'gap dead':>10}"
              f"{'n live':>8}{'gap live':>10}{'Δ (dead-live)':>22}")
        for name, mask in [("tutte", np.ones(len(big), bool)),
                           ("finale (g.>=32)", late),
                           ("ultime (g.>=35)", gio >= 35)]:
            gd = gap[mask & dead]; gl = gap[mask & ~dead]
            if len(gd) < 5:
                print(f"  {name:<26}{len(gd):>8}{'n/a':>10}{len(gl):>8}"
                      f"{gl.mean():>+10.4f}{'(pochi dead)':>22}")
                continue
            d, lo, hi = boot_diff(gd, gl, rng)
            star = " *" if (lo > 0 or hi < 0) else ""
            print(f"  {name:<26}{len(gd):>8}{gd.mean():>+10.4f}{len(gl):>8}"
                  f"{gl.mean():>+10.4f}   {d:+.4f}[{lo:+.4f},{hi:+.4f}]{star}")

    dead = big["match_dead"].to_numpy()
    r_all = float(np.corrcoef(big["match_any_dead"].to_numpy().astype(float), gap)[0, 1])
    r_late = float(np.corrcoef(big["match_any_dead"].to_numpy()[late].astype(float),
                               gap[late])[0, 1])
    print(f"\n  corr(almeno-una-dead, gap): tutte {r_all:+.4f}; nel finale {r_late:+.4f}")

    print("\n  Lettura: se il gap NEI DEAD RUBBER (specie nel finale) e' maggiore in")
    print("  modo statisticamente distinguibile (*), la posta in palio e' il segnale")
    print("  mancante che il mercato prezza e noi no -> covariata 'stakes' candidata.")

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase29_stakes", "league": "serie_a", "variant": "stakes_summary",
         "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(big)), "n_dead": int(dead.sum()),
         "n_dead_late": int((dead & late).sum()),
         "gap_dead_all": float(gap[dead].mean()) if dead.sum() else 0.0,
         "gap_live_all": float(gap[~dead].mean()),
         "gap_dead_late": float(gap[dead & late].mean()) if (dead & late).sum() else 0.0,
         "gap_live_late": float(gap[~dead & late].mean()),
         "corr_dead_gap_all": r_all, "corr_dead_gap_late": r_late}, fp))


if __name__ == "__main__":
    main()
