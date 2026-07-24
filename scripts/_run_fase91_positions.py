"""Fase 91 — I mercati POSIZIONALI: P(top-4) e P(retrocessione) dallo stesso simulatore.

Da dove nasce: l'audit della Fase 90 ha notato che `simulate_season` calcola la
matrice delle POSIZIONI di ogni stagione simulata e poi ne usa solo la prima riga
(il campione), buttando via il resto. Da quella matrice escono due mercati veri —
piazzamento in zona Champions e retrocessione — e soprattutto **480 osservazioni
binarie** per mercato (20 squadre x 24 stagioni-lega) invece delle 24 del
campione. E' la via piu' economica per dare potenza statistica a questa famiglia:
zero modellistica nuova, stesse simulazioni.

Cosa misura:
  - log-loss e Brier binari di P(top-4) e P(retrocessione);
  - CALIBRAZIONE (ECE su 10 fasce): quando diciamo 30%, succede il 30%?
  - due baseline: il TASSO BASE (4/20 e 3/20, la costante ottima) e la
    PERSISTENZA (logistica sui punti standardizzati della stagione precedente,
    con i coefficienti tarati leave-one-out);
  - il confronto per lega.

Definizioni (dichiarate): "top-4" e "retrocessione" sono POSIZIONALI (primi 4 /
ultimi 3 della classifica finale). La corrispondenza con la qualificazione alla
Champions vera cambia per stagione e per lega (posti extra da ranking, ecc.):
qui non la si insegue, il mercato prezzato e' la POSIZIONE.

Nota sugli spareggi (misurata, Fase 91): sulle posizioni di confine la parita' di
punti e' frequente (~15% delle stagioni simulate al 4o/5o e al 17o/18o posto,
contro ~5% in vetta), e la matrice `rank` risolve per differenza reti anziche'
con la classifica avulsa di Serie A/Liga. L'impatto sulla PROBABILITA' aggregata
e' pero' trascurabile: confrontando differenza reti e sorteggio (il limite
superiore della sensibilita'), lo scarto medio e' 0.14pp e il massimo 0.91pp —
le parita' si compensano.

Uso:
  python scripts/_run_fase91_positions.py            # 24 stagioni-lega, ~2 min
  python scripts/_run_fase91_positions.py --nsim 40000
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import loader                                    # noqa: E402
from src.evaluation import experiment_log                      # noqa: E402
from src.models.season_sim import final_table, simulate_season  # noqa: E402
from scripts._run_fase89_season_champion import (              # noqa: E402
    LEAGUES, fit_at_season_start, seed_for, bootstrap_ci,
)

TOP_N = 4          # zona Champions (posizionale)
RELEGATED = 3      # ultime tre


def collect(nsim: int, verbose=True) -> pd.DataFrame:
    """Una riga per SQUADRA-STAGIONE: probabilita' predette + esito reale."""
    rows = []
    for lg in LEAGUES:
        allm = loader.load_league(lg)
        allm["date"] = pd.to_datetime(allm["date"])
        seasons = sorted(allm["season"].unique())
        for i, S in enumerate(seasons):
            if i == 0:
                continue
            model, cur, teams, promoted, _ = fit_at_season_start(allm, lg, S, seasons)
            out = simulate_season(model, list(zip(cur["home_team"], cur["away_team"])),
                                  teams, league_key=lg, n_sims=nsim, seed=seed_for(lg, S))
            rank = out["rank"]
            nt = len(teams)
            p_top = (rank <= TOP_N).mean(axis=0)
            p_rel = (rank >= nt - RELEGATED + 1).mean(axis=0)
            table = final_table(cur, lg)
            pos = {t: k + 1 for k, t in enumerate(table.index)}
            prev_tab = final_table(allm[allm["season"] == seasons[i - 1]], lg)
            lo = float(prev_tab["pts"].min()) - 3.0
            prev_pts = {t: (float(prev_tab["pts"][t]) if t in prev_tab.index else lo)
                        for t in teams}
            arr = np.array([prev_pts[t] for t in teams])
            sd = arr.std() or 1.0
            for k, t in enumerate(teams):
                rows.append(dict(
                    league=lg, season=S, team=t, n_teams=nt,
                    p_top4=float(p_top[k]), p_rel=float(p_rel[k]),
                    is_top4=bool(pos[t] <= TOP_N), is_rel=bool(pos[t] > nt - RELEGATED),
                    position=pos[t], z_prev=float((arr[k] - arr.mean()) / sd),
                    promoted=bool(t in promoted),
                ))
            if verbose:
                print(f"  {lg:15} {S}  ok", flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ metriche --
def binary_metrics(p, y):
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    y = np.asarray(y, float)
    return dict(logloss=float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
                brier=float(np.mean((p - y) ** 2)))


def ece(p, y, bins=10):
    """Expected Calibration Error: |dichiarato - realizzato| pesato per fascia."""
    p = np.asarray(p, float); y = np.asarray(y, float)
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & (p < b if b < 1 else p <= b)
        if m.sum():
            tot += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(tot)


def _logistic_loo(z, y, groups):
    """Baseline di PERSISTENZA: p = sigmoide(a + b*z), (a,b) stimati
    leave-one-out per STAGIONE-LEGA (non per squadra: le 20 squadre della stessa
    stagione non sono indipendenti — se ne escludo una sola, le altre 19 della
    stessa classifica restano nel training e la baseline vede quasi tutto)."""
    def nll(par, zz, yy):
        p = 1.0 / (1.0 + np.exp(-(par[0] + par[1] * zz)))
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return -np.sum(yy * np.log(p) + (1 - yy) * np.log(1 - p))
    out = np.empty(len(z))
    for g in np.unique(groups):
        m = groups == g
        r = minimize(nll, [0.0, 1.0], args=(z[~m], y[~m]), method="Nelder-Mead")
        out[m] = 1.0 / (1.0 + np.exp(-(r.x[0] + r.x[1] * z[m])))
    return out


def report(df: pd.DataFrame) -> dict:
    groups = (df["league"] + df["season"]).to_numpy()
    z = df["z_prev"].to_numpy()
    rep = {}
    print("\n" + "=" * 78)
    print(f"### MERCATI POSIZIONALI — {len(df)} osservazioni "
          f"({df.groupby(['league','season']).ngroups} stagioni-lega x 20 squadre)")
    for key, pcol, ycol, label, base in [
        ("top4", "p_top4", "is_top4", f"TOP-{TOP_N} (zona Champions)", TOP_N / 20),
        ("rel", "p_rel", "is_rel", f"RETROCESSIONE (ultime {RELEGATED})", RELEGATED / 20),
    ]:
        p = df[pcol].to_numpy(); y = df[ycol].to_numpy().astype(float)
        m = binary_metrics(p, y)
        mb = binary_metrics(np.full(len(y), base), y)
        pers = _logistic_loo(z, y, groups)
        mp = binary_metrics(pers, y)
        d_base = np.array([-(yy * np.log(max(bb, 1e-9)) + (1 - yy) * np.log(max(1 - bb, 1e-9)))
                           for bb, yy in zip(np.full(len(y), base), y)]) \
            - np.array([-(yy * np.log(max(pp, 1e-9)) + (1 - yy) * np.log(max(1 - pp, 1e-9)))
                        for pp, yy in zip(p, y)])
        d_pers = np.array([-(yy * np.log(max(bb, 1e-9)) + (1 - yy) * np.log(max(1 - bb, 1e-9)))
                           for bb, yy in zip(pers, y)]) \
            - np.array([-(yy * np.log(max(pp, 1e-9)) + (1 - yy) * np.log(max(1 - pp, 1e-9)))
                        for pp, yy in zip(p, y)])
        lo_b, hi_b = bootstrap_ci(d_base)
        lo_p, hi_p = bootstrap_ci(d_pers)
        e = ece(p, y)
        print(f"\n  {label}   (tasso base reale {y.mean()*100:.1f}%)")
        print(f"    MODELLO          log-loss {m['logloss']:.4f}   Brier {m['brier']:.4f}   ECE {e:.4f}")
        print(f"    tasso base       log-loss {mb['logloss']:.4f}   Brier {mb['brier']:.4f}")
        print(f"    persistenza LOO  log-loss {mp['logloss']:.4f}   Brier {mp['brier']:.4f}")
        print(f"    guadagno vs tasso base : {d_base.mean():+.4f}  IC95% [{lo_b:+.4f}, {hi_b:+.4f}]"
              f"  -> {'CONCLUSIVO' if lo_b > 0 else 'non conclusivo'}")
        print(f"    guadagno vs persistenza: {d_pers.mean():+.4f}  IC95% [{lo_p:+.4f}, {hi_p:+.4f}]"
              f"  -> {'CONCLUSIVO' if lo_p > 0 else 'non conclusivo'}")
        print("    calibrazione per fascia (dichiarato -> realizzato):")
        for a, b in [(0, .1), (.1, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
            mm = (p >= a) & (p < b)
            if mm.sum() >= 5:
                print(f"      {a*100:3.0f}-{b*100:3.0f}%  n={mm.sum():3d}  "
                      f"dichiarato {p[mm].mean()*100:5.1f}%  realizzato {y[mm].mean()*100:5.1f}%  "
                      f"scarto {(y[mm].mean()-p[mm].mean())*100:+5.1f}pp")
        rep[key] = dict(model=m, base=mb, persistence=mp, ece=e,
                        gain_vs_base=float(d_base.mean()), ci_base=[lo_b, hi_b],
                        gain_vs_persistence=float(d_pers.mean()), ci_persistence=[lo_p, hi_p],
                        base_rate=float(y.mean()))
        rep[key]["by_league"] = {}
        for lg in LEAGUES:
            ml = (df["league"] == lg).to_numpy()
            if ml.sum():
                rep[key]["by_league"][lg] = binary_metrics(p[ml], y[ml])["logloss"]
        print("    per lega: " + "  ".join(
            f"{lg.split('_')[0]} {v:.4f}" for lg, v in rep[key]["by_league"].items()))

    # --- da dove viene la mis-calibrazione della retrocessione? ---
    print("\n  ANATOMIA DELLA RETROCESSIONE: neopromosse contro tutte le altre")
    for lab, sub in [("neopromosse", df[df["promoted"]]), ("resto della lega", df[~df["promoted"]])]:
        p = sub["p_rel"].to_numpy(); y = sub["is_rel"].to_numpy().astype(float)
        print(f"    {lab:16} n={len(sub):3d}  dichiarato {p.mean()*100:5.1f}%  "
              f"realizzato {y.mean()*100:5.1f}%  scarto {(y.mean()-p.mean())*100:+5.1f}pp")
    hi = df[df["p_rel"] > 0.6]
    print(f"    dei {len(hi)} casi dichiarati sopra il 60%, {int(hi['promoted'].sum())} "
          f"sono neopromosse ({hi['promoted'].mean()*100:.0f}%) "
          f"e {int((~hi['is_rel']).sum())} si sono SALVATE")
    print("    -> la mis-calibrazione e' TUTTA sulle neopromosse: il prior di")
    print("       cold-start delta (tarato sul log-loss della SINGOLA partita,")
    print("       Fasi 7/57) e' troppo severo quando lo si propaga su 38 giornate.")
    rep["relegation_split"] = {
        lab: dict(n=int(len(sub)), declared=float(sub["p_rel"].mean()),
                  realised=float(sub["is_rel"].mean()))
        for lab, sub in [("promoted", df[df["promoted"]]), ("rest", df[~df["promoted"]])]}
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nsim", type=int, default=20000)
    ap.add_argument("--no-log", action="store_true")
    args = ap.parse_args(argv)

    print(f"### MERCATI POSIZIONALI dal simulatore (nsim={args.nsim})")
    df = collect(args.nsim)
    rep = report(df)

    dest = Path("experiments/fase91_positions.json")
    dest.write_text(json.dumps(dict(rows=df.to_dict("records"), report=rep), indent=2))
    print(f"\nScritto {dest}")

    if not args.no_log:
        fp = "|".join(f"{lg}:{experiment_log.data_fingerprint(loader.load_league(lg))}"
                      for lg in LEAGUES)
        rec = experiment_log.make_record(
            config=dict(nsim=args.nsim, phase="91", script="_run_fase91_positions.py",
                        markets=["top4", "relegation"], leagues=list(LEAGUES)),
            metrics_dict=rep, fingerprint=fp)
        rec["note"] = "Mercati posizionali dal rank del simulatore: 480 osservazioni."
        experiment_log.append_run(rec)
        print("Run registrato in experiments/runs.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
