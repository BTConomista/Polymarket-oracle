"""Fase 55 — EDA descrittiva cross-lega: conoscere Premier e La Liga (vs Serie A).

PRIMA di modellare (metodo §1: conoscere i dati). Caratterizza le tre leghe sulle
dimensioni che sono state PORTANTI nell'analisi Serie A, cosi' da formulare ipotesi
su cosa dovrebbe trasferirsi (§7: mai copiare i numeri). Nessun walk-forward qui:
solo statistiche descrittive, ognuna con la sua lettura.

Dimensioni (per lega, pooled 9 stagioni + evoluzione per stagione):
  A. frequenze esiti: 1 / X / 2, Over 2.5, GG (il draw-rate e' la firma di una lega)
  B. gol: media totale, casa, ospite; vantaggio-casa γ = ln(λ_casa/λ_ospite)
  C. dispersione dei punteggi: Var/Media dei gol (quanto lontani dalla Poisson)
  D. vantaggio-casa NEL TEMPO: crollo COVID? trend? (Serie A: casa 40%->36% nel 20-21)
  E. debolezza neopromosse: δ = ln(gol_lega/gol_promosse) — il prior di cold-start
  F. stabilita' delle forze anno-su-anno: corr attacco(t) vs attacco(t-1) (giustifica
     l'emivita lunga)
  G. qualita' xG: corr xG-gol, e bias xG (over/under-performance sistematica)
  H. efficienza del mercato: margine (overround) e log-loss del mercato vs baseline

Uso:  python scripts/_run_fase55_eda.py    (snapshot delle 3 leghe)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                          # noqa: E402
from src.evaluation import experiment_log, metrics   # noqa: E402

LEAGUES = ["serie_a", "premier_league", "la_liga"]
NAMES = {"serie_a": "Serie A", "premier_league": "Premier", "la_liga": "La Liga"}
_OI = {"H": 0, "D": 1, "A": 2}


def _season_order(df):
    return sorted(df.season.unique())


def _promoted(df, season, order):
    i = order.index(season)
    if i == 0:
        return set()
    prev = df[df.season == order[i - 1]]
    cur = df[df.season == season]
    return (set(cur.home_team) | set(cur.away_team)) - \
           (set(prev.home_team) | set(prev.away_team))


def _analyze(df):
    order = _season_order(df)
    hg, ag = df.home_goals.values, df.away_goals.values
    n = len(df)
    out = {}
    # A. esiti
    out["home_pct"] = float((df.result == "H").mean())
    out["draw_pct"] = float((df.result == "D").mean())
    out["away_pct"] = float((df.result == "A").mean())
    out["over25_pct"] = float(((hg + ag) >= 3).mean())
    out["btts_pct"] = float(((hg >= 1) & (ag >= 1)).mean())
    # B. gol
    out["goals_tot"] = float((hg + ag).mean())
    out["goals_home"] = float(hg.mean())
    out["goals_away"] = float(ag.mean())
    out["home_adv_gamma"] = float(np.log(hg.mean() / ag.mean()))
    # C. dispersione (Var/Media dei gol: >1 = piu' disperso della Poisson)
    out["vm_home"] = float(hg.var() / hg.mean())
    out["vm_away"] = float(ag.var() / ag.mean())
    # D. vantaggio-casa nel tempo (per stagione)
    per_season = {s: float((df[df.season == s].result == "H").mean()) for s in order}
    out["home_pct_by_season"] = per_season
    out["home_pct_min"] = min(per_season.values())
    out["home_pct_max"] = max(per_season.values())
    # E. neopromosse: gol segnati/subiti per gara vs media lega
    prom_scored, prom_conceded, prom_n = [], [], 0
    for s in order[1:]:
        prom = _promoted(df, s, order)
        cur = df[df.season == s]
        for _, r in cur.iterrows():
            if r.home_team in prom:
                prom_scored.append(r.home_goals); prom_conceded.append(r.away_goals); prom_n += 1
            if r.away_team in prom:
                prom_scored.append(r.away_goals); prom_conceded.append(r.home_goals); prom_n += 1
    league_scored = (hg.sum() + ag.sum()) / (2 * n)     # gol per squadra per gara
    ps = float(np.mean(prom_scored)) if prom_scored else float("nan")
    pc = float(np.mean(prom_conceded)) if prom_conceded else float("nan")
    out["promoted_scored"] = ps
    out["promoted_conceded"] = pc
    out["league_goals_per_team"] = float(league_scored)
    out["delta_attack"] = float(np.log(league_scored / ps)) if ps else float("nan")
    out["delta_defense"] = float(np.log(pc / league_scored)) if pc else float("nan")
    out["promoted_matches"] = prom_n
    # F. stabilita' delle forze anno-su-anno (attacco = gol segnati per gara)
    strengths = {}
    for s in order:
        cur = df[df.season == s]
        att = {}
        for t in set(cur.home_team) | set(cur.away_team):
            gs = pd.concat([cur[cur.home_team == t].home_goals,
                            cur[cur.away_team == t].away_goals])
            att[t] = gs.mean()
        strengths[s] = att
    corrs = []
    for a, b in zip(order[:-1], order[1:]):
        common = set(strengths[a]) & set(strengths[b])
        if len(common) >= 8:
            xa = [strengths[a][t] for t in common]
            xb = [strengths[b][t] for t in common]
            corrs.append(np.corrcoef(xa, xb)[0, 1])
    out["strength_autocorr"] = float(np.mean(corrs))
    # G. qualita' xG
    if "home_xg" in df and df.home_xg.notna().any():
        xg = np.concatenate([df.home_xg.values, df.away_xg.values])
        goals = np.concatenate([hg, ag]).astype(float)
        ok = np.isfinite(xg)
        out["xg_goal_corr"] = float(np.corrcoef(xg[ok], goals[ok])[0, 1])
        out["xg_mean"] = float(np.nanmean(xg))
        out["xg_vs_goals_bias"] = float(np.nanmean(goals[ok] - xg[ok]))
    else:
        out["xg_goal_corr"] = float("nan"); out["xg_mean"] = float("nan")
        out["xg_vs_goals_bias"] = float("nan")
    # H. efficienza del mercato: margine e log-loss vs baseline in-sample
    over = 1 / df.odds_home + 1 / df.odds_draw + 1 / df.odds_away
    out["overround"] = float(over.mean() - 1.0)
    P = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in df.itertuples()])
    y = np.array([_OI[o] for o in df.result])
    out["market_ll"] = float(-np.log(np.clip(P[np.arange(n), y], 1e-15, 1)).mean())
    base = np.array([out["home_pct"], out["draw_pct"], out["away_pct"]])
    out["baseline_ll"] = float(-np.log(np.clip(base[y], 1e-15, 1)).mean())
    out["market_edge_vs_base"] = out["baseline_ll"] - out["market_ll"]
    out["n_matches"] = n
    return out


def main():
    res = {lg: _analyze(loader.load_league(lg)) for lg in LEAGUES}

    def row(label, key, fmt="{:.3f}"):
        cells = "".join(f"{fmt.format(res[lg][key]):>14}" for lg in LEAGUES)
        print(f"  {label:<34}{cells}")

    print("=" * 78)
    print("FASE 55 — EDA CROSS-LEGA (9 stagioni 2017-2026, pooled)")
    print("=" * 78)
    print(f"  {'':<34}" + "".join(f"{NAMES[lg]:>14}" for lg in LEAGUES))
    print("\n  --- A. Frequenze esiti ---")
    row("vittoria casa %", "home_pct", "{:.1%}")
    row("pareggio %", "draw_pct", "{:.1%}")
    row("vittoria ospite %", "away_pct", "{:.1%}")
    row("Over 2.5 %", "over25_pct", "{:.1%}")
    row("GG (both to score) %", "btts_pct", "{:.1%}")
    print("\n  --- B. Gol e vantaggio-casa ---")
    row("gol totali / partita", "goals_tot")
    row("gol casa / partita", "goals_home")
    row("gol ospite / partita", "goals_away")
    row("vantaggio-casa γ=ln(casa/osp)", "home_adv_gamma")
    print("\n  --- C. Dispersione dei gol (Var/Media; 1=Poisson) ---")
    row("Var/Media gol casa", "vm_home")
    row("Var/Media gol ospite", "vm_away")
    print("\n  --- D. Vantaggio-casa nel tempo ---")
    row("vittoria casa % (min stagione)", "home_pct_min", "{:.1%}")
    row("vittoria casa % (max stagione)", "home_pct_max", "{:.1%}")
    print("\n  --- E. Debolezza neopromosse (prior δ) ---")
    row("gol/gara media lega (per sq.)", "league_goals_per_team")
    row("gol/gara segnati neopromosse", "promoted_scored")
    row("gol/gara subiti neopromosse", "promoted_conceded")
    row("δ attacco = ln(lega/promosse)", "delta_attack")
    row("δ difesa = ln(subiti/lega)", "delta_defense")
    print("\n  --- F. Stabilita' forze anno-su-anno ---")
    row("autocorr attacco (t, t-1)", "strength_autocorr")
    print("\n  --- G. Qualita' xG ---")
    row("corr xG-gol (per squadra/gara)", "xg_goal_corr")
    row("gol − xG medio (finishing bias)", "xg_vs_goals_bias", "{:+.3f}")
    print("\n  --- H. Efficienza del mercato ---")
    row("margine bookmaker (overround)", "overround", "{:.1%}")
    row("log-loss mercato 1X2", "market_ll", "{:.4f}")
    row("log-loss baseline (in-sample)", "baseline_ll", "{:.4f}")
    row("edge mercato vs baseline", "market_edge_vs_base", "{:.4f}")

    for lg in LEAGUES:
        experiment_log.append_run(experiment_log.make_record(
            {"source": "fase55_eda", "league": lg, "variant": "eda_descrittiva"},
            res[lg],
            experiment_log.data_fingerprint(loader.load_league(lg))))
    print("\nRun registrati (source=fase55_eda, una per lega).")


if __name__ == "__main__":
    main()
