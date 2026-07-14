"""Fase 40 — ROI PER MERCATO e PER ESITO: cosa nascondeva il value-betting 1X2 piatto.

Tutte le analisi di ROI (Fase 1/14/15) usavano il value-betting 1X2 INDISTINTO
(qualunque esito con edge>soglia), trovando ~−15%. Ma questo LUMPA insieme casa,
pari e trasferta. La Fase 35 ha mostrato che il mercato SOTTO-prezza i pareggi delle
partite equilibrate (0.296 vs reale 0.332): forse l'edge (o l'assenza di edge) e'
molto diverso per esito e per mercato. Qui lo scomponiamo.

Analisi (predizioni Fase 35, db_phi_equilibrio; scommessa a quota di chiusura):
  A. ROI del value-betting PER ESITO (casa / pari / trasferta separati).
  B. Strategia PAREGGIO nelle partite EQUILIBRATE (|lam-mu| < soglia FISSA 0.5),
     per stagione + bootstrap CI sul ROI (il lead piu' promettente).
  C. ROI del value-betting O/U 2.5.

Onesta': lo storico sovrastima quasi sempre la redditivita'; il pareggio e' un evento
ad alta varianza (~32%) -> CI larghi. Disciplina Fase 17: CI che include lo zero =
non concluso.

Uso:  python scripts/_run_market_specific_roi.py    (usa i backtest in cache)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                       # noqa: E402
from src.evaluation import experiment_log, metrics  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "outputs"
SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
DRAW_THR = 0.5          # soglia FISSA pre-dichiarata |lam-mu| per la strategia pari
EDGE = 0.03
B, SEED = 10_000, 40


def _load():
    fr = []
    for s in SEASONS:
        d = pd.read_csv(CACHE / f"db_phi_equilibrio_{s}.csv"); d["season"] = s
        fr.append(d)
    df = pd.concat(fr, ignore_index=True)
    df = df[np.isfinite(df[["odds_home", "odds_draw", "odds_away"]].to_numpy()).all(axis=1)].copy()
    mkt = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                    for r in df.itertuples()])
    df["mk_home"], df["mk_draw"], df["mk_away"] = mkt[:, 0], mkt[:, 1], mkt[:, 2]
    df["balance"] = (df.exp_home_goals - df.exp_away_goals).abs()
    df["is_draw"] = (df.result == "D").astype(float)
    return df


def _boot_roi(ret, rng):
    if len(ret) == 0:
        return 0.0, 0.0, 0.0, 0.0
    m = ret[rng.integers(0, len(ret), (B, len(ret)))].mean(1)
    return float(ret.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m > 0).mean())


def main():
    df = _load()
    rng = np.random.default_rng(SEED)
    summary = {}

    # --- A. value betting PER ESITO ---
    print("=" * 82)
    print(f"A. ROI value-betting PER ESITO (edge modello-mercato > {EDGE}, quota di chiusura)")
    print("=" * 82)
    print(f"  {'esito':<10}{'n bet':>7}{'ROI%':>9}{'win%':>8}{'CI95 ROI%':>22}{'P(>0)':>7}")
    for lab, mcol, ocol, res in [("casa", "m_home", "odds_home", "H"),
                                 ("pari", "m_draw", "odds_draw", "D"),
                                 ("trasferta", "m_away", "odds_away", "A")]:
        bet = df[df[mcol] - df[{"m_home": "mk_home", "m_draw": "mk_draw", "m_away": "mk_away"}[mcol]] > EDGE]
        ret = (np.where(bet.result == res, bet[ocol] - 1.0, -1.0)).astype(float)
        mean, lo, hi, ppos = _boot_roi(ret, rng)
        win = (bet.result == res).mean() if len(bet) else 0.0
        print(f"  {lab:<10}{len(bet):>7}{100*mean:>+9.1f}{100*win:>8.1f}"
              f"   [{100*lo:+.1f}, {100*hi:+.1f}]{100*ppos:>7.0f}")
        summary[f"roi_{res}"] = float(mean); summary[f"n_{res}"] = int(len(bet))

    # --- B. strategia PAREGGIO in partite equilibrate ---
    print("\n" + "=" * 82)
    print(f"B. Strategia PAREGGIO se |lam-mu| < {DRAW_THR} (soglia FISSA), per stagione")
    print("=" * 82)
    sel = df[df.balance < DRAW_THR].copy()
    sel["ret"] = sel.is_draw * sel.odds_draw - 1.0
    print(f"  {'stagione':<10}{'n':>6}{'ROI%':>9}{'win%':>8}")
    for s in SEASONS:
        ss = sel[sel.season == s]
        print(f"  {s:<10}{len(ss):>6}{100*ss.ret.mean():>+9.1f}{100*ss.is_draw.mean():>8.1f}")
    mean, lo, hi, ppos = _boot_roi(sel.ret.values, rng)
    print(f"  {'POOLED':<10}{len(sel):>6}{100*mean:>+9.1f}{100*sel.is_draw.mean():>8.1f}"
          f"   CI95 [{100*lo:+.1f}, {100*hi:+.1f}]  P(ROI>0)={100*ppos:.0f}%")
    pos = sum(1 for s in SEASONS if sel[sel.season == s].ret.mean() > 0)
    print(f"  stagioni con ROI>0: {pos}/6   (rif.: scommettere TUTTI i pari = "
          f"{100*(df.is_draw*df.odds_draw-1).mean():+.1f}%)")
    summary["draw_balanced_roi"] = float(mean); summary["draw_balanced_ci_lo"] = float(lo)
    summary["draw_balanced_ci_hi"] = float(hi); summary["draw_balanced_p_pos"] = float(ppos)
    summary["draw_balanced_n"] = int(len(sel)); summary["draw_balanced_seasons_pos"] = pos

    # gradiente per soglia (mostra la monotonia = non cherry-picking)
    print("\n  gradiente (piu' equilibrio -> piu' ROI): ", end="")
    for thr in [0.8, 0.6, 0.4, 0.25]:
        ss = df[df.balance < thr]
        r = (ss.is_draw * ss.odds_draw - 1).mean()
        print(f"|<{thr}: {100*r:+.1f}% (n={len(ss)})  ", end="")
    print()

    # --- C. value betting O/U ---
    print("\n" + "=" * 82)
    print(f"C. ROI value-betting O/U 2.5 (edge > {EDGE})")
    print("=" * 82)
    ou_mk = np.array([metrics.devig_binary(r.odds_over, r.odds_under)[0]
                      if np.isfinite([r.odds_over, r.odds_under]).all() else np.nan
                      for r in df.itertuples()])
    dfou = df.assign(ou_mk=ou_mk).dropna(subset=["ou_mk"])
    over_bet = dfou[dfou.m_over - dfou.ou_mk > EDGE]
    under_bet = dfou[(1 - dfou.m_over) - (1 - dfou.ou_mk) > EDGE]
    for lab, bet, ocol, win_cond in [
            ("Over", over_bet, "odds_over", over_bet.is_over == 1 if len(over_bet) else None),
            ("Under", under_bet, "odds_under", under_bet.is_over == 0 if len(under_bet) else None)]:
        if len(bet) == 0:
            print(f"  {lab:<8} nessuna scommessa"); continue
        ret = np.where(win_cond, bet[ocol] - 1.0, -1.0).astype(float)
        mean, lo, hi, ppos = _boot_roi(ret, rng)
        print(f"  {lab:<8}{len(bet):>6} bet  ROI {100*mean:>+6.1f}%  "
              f"CI95 [{100*lo:+.1f}, {100*hi:+.1f}]  P(>0)={100*ppos:.0f}%")
        summary[f"roi_ou_{lab.lower()}"] = float(mean); summary[f"n_ou_{lab.lower()}"] = int(len(bet))

    experiment_log.append_run(experiment_log.make_record(
        {"source": "fase40_market_specific_roi", "league": "serie_a",
         "variant": "roi_by_outcome_and_market", "draw_threshold": DRAW_THR,
         "edge": EDGE, "bootstrap_B": B, "bootstrap_seed": SEED, "promoted_prior": 0.23},
        {"n_matches": int(len(df)), **summary},
        experiment_log.data_fingerprint(loader.load_league("serie_a"))))
    print("\nRun registrato (source=fase40_market_specific_roi).")


if __name__ == "__main__":
    main()
