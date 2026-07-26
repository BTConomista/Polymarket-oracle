"""Fase 89 — Il mercato CAMPIONE DI STAGIONE: simulatore, backtest, confronto col mercato.

Cosa fa:
  1. BACKTEST walk-forward su 24 stagioni-lega (8 stagioni x 3 leghe: la prima
     stagione di ogni lega non e' backtestabile, manca lo storico). Per ognuna:
     fitta il DC alla data della PRIMA partita della stagione (nessun dato
     futuro), simula N stagioni intere, ricava P(campione) e la confronta col
     campione REALE (calcolato dai risultati con gli spareggi ufficiali).
  2. METRICHE e BASELINE (uniforme, "vince il campione uscente", forza dalla
     classifica precedente), con intervalli bootstrap e test dei segni.
  3. DIAGNOSTICA DI CALIBRAZIONE: quanto dichiariamo sul favorito vs quanto
     realizziamo (la sovra-confidenza attesa dalle forze fisse).
  4. PREDIZIONE 2026-27 e confronto coi prezzi Polymarket di oggi.

Uso:
  python scripts/_run_fase89_season_champion.py                 # tutto
  python scripts/_run_fase89_season_champion.py --nsim 40000
  python scripts/_run_fase89_season_champion.py --skip-2627

NOTA sulle metriche (regola CLAUDE.md §5): experiment_log.compute_metrics e' la
fonte unica per i mercati di SINGOLA PARTITA (1X2/O-U binari o ternari). Qui il
problema e' diverso — multiclasse a ~20 esiti con UNA osservazione per stagione —
e compute_metrics non e' applicabile: le metriche del campione sono definite qui
sotto (log-loss multiclasse e Brier multiclasse, formule esplicite) e NON
duplicano nulla di esistente.
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import league_config                     # noqa: E402
from src.data import loader                              # noqa: E402
from src.evaluation import experiment_log                # noqa: E402
from src.models.dixon_coles import DixonColesModel       # noqa: E402
from src.models.season_sim import final_table, round_robin, simulate_season  # noqa: E402

LEAGUES = ("serie_a", "premier_league", "la_liga")

# Rose 2026-27: 17 squadre rimaste + 3 promosse. Le retrocesse sono le ultime 3
# della classifica 2025-26 CON gli spareggi ufficiali (per la Liga cambia
# l'esito: Levante, Osasuna e Mallorca chiudono tutte a 42 punti e la classifica
# avulsa fra le tre retrocede Mallorca, non Levante).
# Fonte delle promosse: i mercati "2027 Champion" di Polymarket (24/07/2026),
# riconciliati coi nomi interni. E' un'informazione ESTERNA agli snapshot: va
# aggiornata quando il calendario ufficiale 2026-27 sara' pubblico.
PROMOTED_2627 = {
    "serie_a": ["Venezia", "Frosinone", "Monza"],
    "premier_league": ["Ipswich", "Hull", "Coventry"],
    "la_liga": ["Santander", "Malaga", "La Coruna"],
}

# Prezzi Polymarket del 24/07/2026, gia' devigati (esclusi i segnaposto morti
# "Team A/B/C"/"Other", che avevano book vuoto e falsavano la somma).
MARKET_2627 = {
    "serie_a": {"Inter": .470, "Juventus": .135, "Napoli": .126, "Milan": .116,
                "Roma": .057, "Como": .032, "Atalanta": .018, "Sassuolo": .010,
                "Venezia": .008, "Frosinone": .007, "Bologna": .007},
    "premier_league": {"Arsenal": .340, "Man City": .283, "Man United": .110,
                       "Liverpool": .110, "Chelsea": .091, "Tottenham": .026,
                       "Aston Villa": .016, "Newcastle": .005},
    "la_liga": {"Barcelona": .514, "Real Madrid": .409, "Ath Madrid": .043,
                "Ath Bilbao": .005, "Villarreal": .003, "Valencia": .002,
                "Sociedad": .002, "Betis": .002},
}


def seed_for(*parts) -> int:
    """Seed DETERMINISTICO fra processi diversi (hash() di Python e' randomizzato
    per processo: usarlo romperebbe la riproducibilita', regola CLAUDE.md §1.5)."""
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0x7FFFFFFF


def fit_at_season_start(all_matches, league_key, season, seasons):
    """Fitta il DC il giorno della prima partita di ``season`` (niente futuro)."""
    cur = all_matches[all_matches["season"] == season].sort_values("date")
    start = cur["date"].min()
    prev = seasons[seasons.index(season) - 1]
    prev_teams = (set(all_matches[all_matches["season"] == prev]["home_team"])
                  | set(all_matches[all_matches["season"] == prev]["away_team"]))
    teams = sorted(set(cur["home_team"]) | set(cur["away_team"]))
    promoted = set(teams) - prev_teams
    cfg = league_config(league_key)
    d = cfg["promoted_prior"]
    model = DixonColesModel(
        half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
        shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
        promoted_prior=(d, d),
    )
    model.fit(all_matches, as_of_date=start, promoted_teams=promoted)
    return model, cur, teams, promoted, start


# ----------------------------------------------------------------- metriche --
def logloss(p: float) -> float:
    """-ln p sull'esito realizzato (multiclasse). p e' P(campione effettivo)."""
    return -float(np.log(max(p, 1e-12)))


def brier_multiclass(probs: np.ndarray, k: int) -> float:
    """Brier multiclasse: somma_j (p_j - y_j)^2, con y one-hot sul campione."""
    y = np.zeros_like(probs)
    y[k] = 1.0
    return float(np.sum((probs - y) ** 2))


def bootstrap_ci(values, n_boot=10000, seed=1, alpha=0.05):
    """IC percentile della MEDIA per ricampionamento delle osservazioni."""
    rng = np.random.default_rng(seed)
    v = np.asarray(values, float)
    means = v[rng.integers(0, len(v), size=(n_boot, len(v)))].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def run_backtest(nsim: int, verbose=True) -> pd.DataFrame:
    rows = []
    for lg in LEAGUES:
        allm = loader.load_league(lg)
        allm["date"] = pd.to_datetime(allm["date"])
        seasons = sorted(allm["season"].unique())
        for i, S in enumerate(seasons):
            if i == 0:
                continue                       # niente storico: non backtestabile
            model, cur, teams, promoted, start = fit_at_season_start(allm, lg, S, seasons)
            fixtures = list(zip(cur["home_team"], cur["away_team"]))
            out = simulate_season(model, fixtures, teams, league_key=lg,
                                  n_sims=nsim, seed=seed_for(lg, S))
            p = out["champion_prob"]
            table = final_table(cur, lg)
            champ = table.index[0]
            k = teams.index(champ)
            prev_tab = final_table(allm[allm["season"] == seasons[i - 1]], lg)
            # Punti delle stagioni precedenti, per la baseline di PERSISTENZA
            # (vedi report()). Le squadre assenti da quella stagione (neopromosse)
            # vengono imputate a min(punti) - 3: sono in media piu' deboli
            # dell'ultima classificata, che e' appena retrocessa.
            def prev_points(table):
                lo = float(table["pts"].min()) - 3.0
                return {t: float(table["pts"][t]) if t in table.index else lo
                        for t in teams}
            prev_pts = prev_points(prev_tab)
            prev2_pts = (prev_points(final_table(allm[allm["season"] == seasons[i - 2]], lg))
                         if i >= 2 else None)
            rows.append(dict(
                league=lg, season=S, n_train_seasons=i, start=str(start.date()),
                champion=champ, p_champion=float(p[k]),
                rank_of_champion=int((-p).argsort().tolist().index(k)) + 1,
                favourite=teams[int(p.argmax())], p_favourite=float(p.max()),
                favourite_correct=bool(teams[int(p.argmax())] == champ),
                logloss=logloss(float(p[k])), brier=brier_multiclass(p, k),
                tie_rate=out["tie_rate"], n_teams=len(teams),
                promoted=sorted(promoted),
                prev_champion=prev_tab.index[0],
                repeat=bool(champ == prev_tab.index[0]),
                pts_real_champion=int(table["pts"].iloc[0]),
                pts_sim_winner_mean=float(out["points"].max(axis=1).mean()),
                probs={t: round(float(p[j]), 5) for j, t in enumerate(teams)},
                prev_points=prev_pts, prev2_points=prev2_pts,
            ))
            if verbose:
                r = rows[-1]
                print(f"  {lg:15} {S}  campione {champ:14} p={r['p_champion']*100:5.1f}% "
                      f"rank={r['rank_of_champion']:2d}  favorito {r['favourite']:14} "
                      f"{r['p_favourite']*100:5.1f}%  parita={r['tie_rate']*100:4.1f}%", flush=True)
    return pd.DataFrame(rows)


def persistence_probs(row, beta: float, w2: float = 0.0) -> np.ndarray:
    """Baseline di PERSISTENZA: probabilita' dai punti delle stagioni passate.

    E' la baseline promessa dal docstring di questa fase e mai implementata fino
    all'audit della Fase 90. E' molto piu' forte del "vince il campione uscente":
    usa TUTTA la classifica, non solo chi ha vinto.

        z_i   = punti standardizzati della squadra i (media 0, dev.std 1)
        p_i   = exp(beta * z_i) / somma_j exp(beta * z_j)

    Con ``w2 > 0`` i punti sono una media pesata delle ULTIME DUE stagioni
    (peso 1 alla piu' recente, w2 alla precedente): due stagioni sono una stima
    meno rumorosa della forza di una.
    ``beta`` = quanto la classifica passata "conta": beta=0 da' l'uniforme,
    beta grande concentra tutto sulla prima dell'anno prima.
    """
    teams = list(row["probs"])
    pts = np.array([row["prev_points"][t] for t in teams], float)
    if w2 and row.get("prev2_points"):
        p2 = np.array([row["prev2_points"][t] for t in teams], float)
        pts = (pts + w2 * p2) / (1.0 + w2)
    sd = pts.std()
    z = (pts - pts.mean()) / (sd if sd > 1e-9 else 1.0)
    e = np.exp(beta * z)
    return e / e.sum()


def _persistence_logloss(df: pd.DataFrame, beta: float, w2: float = 0.0) -> np.ndarray:
    out = []
    for _, r in df.iterrows():
        p = persistence_probs(r, beta, w2)
        k = list(r["probs"]).index(r["champion"])
        out.append(-np.log(max(float(p[k]), 1e-12)))
    return np.array(out)


def _persistence_loo(df: pd.DataFrame, betas, w2s) -> tuple[np.ndarray, tuple]:
    """Log-loss LEAVE-ONE-OUT della baseline: per ogni stagione si tarano
    (beta, w2) sulle ALTRE 23 e si valuta su quella esclusa. Cosi' la baseline
    non e' penalizzata da una taratura in-sample del modello che la batte."""
    grid = [(b, w) for b in betas for w in w2s]
    per_case = np.empty(len(df))
    for i in range(len(df)):
        sub = df.drop(df.index[i])
        best = min(grid, key=lambda bw: _persistence_logloss(sub, *bw).mean())
        per_case[i] = _persistence_logloss(df.iloc[[i]], *best)[0]
    best_all = min(grid, key=lambda bw: _persistence_logloss(df, *bw).mean())
    return per_case, best_all


def report(df: pd.DataFrame) -> dict:
    n = len(df)
    ll_model = df["logloss"].mean()
    ll_unif = float(np.mean([np.log(t) for t in df["n_teams"]]))

    # baseline "vince il campione uscente": q IN-SAMPLE (favorevole alla baseline)
    # e LEAVE-ONE-OUT (onesta).
    qs = np.arange(0.02, 0.98, 0.01)
    def ll_rep(q, sub):
        return float(np.mean([-np.log(q if r.repeat else (1 - q) / (r.n_teams - 1))
                              for r in sub.itertuples()]))
    q_in = float(qs[int(np.argmin([ll_rep(q, df) for q in qs]))])
    ll_rep_in = ll_rep(q_in, df)
    loo = []
    for i in range(n):
        sub = df.drop(df.index[i])
        q = float(qs[int(np.argmin([ll_rep(qq, sub) for qq in qs]))])
        r = df.iloc[i]
        loo.append(-np.log(q if r["repeat"] else (1 - q) / (r["n_teams"] - 1)))
    ll_rep_loo = float(np.mean(loo))

    diff = np.array(loo) - df["logloss"].to_numpy()      # baseline - modello
    lo, hi = bootstrap_ci(diff)
    wins = int((df["logloss"].to_numpy() < np.array(loo)).sum())

    # --- baseline di PERSISTENZA (la piu' forte; audit Fase 90) ---
    # griglia scelta perche' l'ottimo cada all'INTERNO (verificato: beta*~2.5,
    # w2*~1.5; con un tetto a w2=1.0 la baseline usciva sottostimata e il
    # guadagno del modello sovrastimato)
    betas = np.arange(0.0, 4.05, 0.1)
    pers1, best1 = _persistence_loo(df, betas, [0.0])
    pers2, best2 = _persistence_loo(df, betas, [0.0, 0.5, 1.0, 1.5, 2.0])
    d1 = pers1 - df["logloss"].to_numpy()
    d2 = pers2 - df["logloss"].to_numpy()
    lo1, hi1 = bootstrap_ci(d1)
    lo2, hi2 = bootstrap_ci(d2)
    w1 = int((df["logloss"].to_numpy() < pers1).sum())
    w2n = int((df["logloss"].to_numpy() < pers2).sum())

    p_fav = float(df["p_favourite"].mean())
    hit = float(df["favourite_correct"].mean())
    se = float(np.sqrt(hit * (1 - hit) / n))

    rep = dict(
        n=n, logloss_model=float(ll_model), logloss_uniform=ll_unif,
        logloss_reigning_insample=ll_rep_in, q_insample=q_in,
        logloss_reigning_loo=ll_rep_loo,
        gain_vs_reigning=float(diff.mean()), gain_ci=[lo, hi],
        seasons_model_better=wins,
        logloss_persistence1_loo=float(pers1.mean()), beta1=float(best1[0]),
        logloss_persistence2_loo=float(pers2.mean()),
        beta2=float(best2[0]), w2=float(best2[1]),
        gain_vs_persistence1=float(d1.mean()), gain_ci_persistence1=[lo1, hi1],
        seasons_better_persistence1=w1,
        gain_vs_persistence2=float(d2.mean()), gain_ci_persistence2=[lo2, hi2],
        seasons_better_persistence2=w2n,
        gain_persistence2_by_league={
            lg: float(d2[(df["league"] == lg).to_numpy()].mean())
            for lg in LEAGUES if (df["league"] == lg).any()},
        brier_model=float(df["brier"].mean()),
        rank_mean=float(df["rank_of_champion"].mean()),
        favourite_hit_rate=hit, favourite_claimed=p_fav,
        overconfidence_pp=float((hit - p_fav) * 100),
        overconfidence_sigma=float((hit - p_fav) / se) if se > 0 else float("nan"),
        tie_rate_mean=float(df["tie_rate"].mean()),
        pts_real_champion=float(df["pts_real_champion"].mean()),
        pts_sim_winner=float(df["pts_sim_winner_mean"].mean()),
    )

    print("\n" + "=" * 78)
    print("### METRICHE (log-loss sul campione effettivo; piu basso = meglio)")
    print(f"  MODELLO (MC dal DC)          : {rep['logloss_model']:.4f}   (n={n})")
    print("  --- baseline, dalla piu' debole alla piu' forte ---")
    print(f"  uniforme (1/20)              : {rep['logloss_uniform']:.4f}")
    print(f"  'vince il campione uscente'  : {rep['logloss_reigning_insample']:.4f} "
          f"(q={q_in:.2f} IN-SAMPLE) | {rep['logloss_reigning_loo']:.4f} (LOO)")
    print(f"  PERSISTENZA 1 stagione       : {pers1.mean():.4f} (LOO, beta*={best1[0]:.1f})")
    print(f"  PERSISTENZA 2 stagioni       : {pers2.mean():.4f} (LOO, beta*={best2[0]:.1f}, "
          f"w2*={best2[1]:.2f})   <-- LA PIU' FORTE")
    print("  --- guadagno del modello su ciascuna ---")
    print(f"  vs 'uscente'   : {rep['gain_vs_reigning']:+.4f}  IC95% [{lo:+.4f}, {hi:+.4f}]"
          f"  {wins}/{n} stagioni  -> {'CONCLUSIVO' if lo > 0 else 'non conclusivo'}")
    print(f"  vs persistenza1: {d1.mean():+.4f}  IC95% [{lo1:+.4f}, {hi1:+.4f}]"
          f"  {w1}/{n} stagioni  -> {'CONCLUSIVO' if lo1 > 0 else 'non conclusivo'}")
    print(f"  vs persistenza2: {d2.mean():+.4f}  IC95% [{lo2:+.4f}, {hi2:+.4f}]"
          f"  {w2n}/{n} stagioni  -> {'CONCLUSIVO' if lo2 > 0 else 'non conclusivo'}")
    print("  (i due numeri onesti sono gli ULTIMI: la baseline debole gonfia il")
    print("   guadagno di oltre un nat e porta il conteggio a 24/24)")
    print("\n  guadagno vs persistenza2, PER LEGA:")
    for lg in LEAGUES:
        mask = (df["league"] == lg).to_numpy()
        if mask.any():
            print(f"    {lg:16} {d2[mask].mean():+.4f}   "
                  f"{int((df['logloss'].to_numpy()[mask] < pers2[mask]).sum())}/{int(mask.sum())}")
    print(f"\n  Brier multiclasse            : {rep['brier_model']:.4f}")
    print(f"  rank medio del campione reale: {rep['rank_mean']:.2f}")
    print("\n### CALIBRAZIONE DEL FAVORITO (la sovra-confidenza)")
    print(f"  P media dichiarata sul favorito : {p_fav*100:.1f}%")
    print(f"  frequenza reale di vittoria     : {hit*100:.1f}%  (SE {se*100:.1f}pp)")
    print(f"  scarto                          : {rep['overconfidence_pp']:+.1f}pp "
          f"= {rep['overconfidence_sigma']:+.2f} SE")
    print(f"\n  punti del campione REALE   : {rep['pts_real_champion']:.1f}")
    print(f"  punti del vincitore SIMULATO: {rep['pts_sim_winner']:.1f}  "
          f"(scarto {rep['pts_real_champion']-rep['pts_sim_winner']:+.1f})")
    print(f"  parita di punti in testa (simulazioni): {rep['tie_rate_mean']*100:.1f}%")
    print("\n### PER LEGA")
    for lg, g in df.groupby("league"):
        print(f"   {lg:16} log-loss {g['logloss'].mean():.4f}  "
              f"favorito azzeccato {g['favourite_correct'].mean()*100:3.0f}%  "
              f"p_fav medio {g['p_favourite'].mean()*100:.1f}%")
    return rep


def predict_2627(nsim: int) -> list[dict]:
    """Predizione 2026-27 (nessun calendario noto: girone doppio completo)."""
    out_rows = []
    as_of = pd.Timestamp("2026-08-15")
    print("\n" + "=" * 78)
    print("### PREDIZIONE 2026-27  vs  PREZZI POLYMARKET (24/07/2026)")
    for lg in LEAGUES:
        allm = loader.load_league(lg)
        allm["date"] = pd.to_datetime(allm["date"])
        last = allm[allm["season"] == "2526"]
        table = final_table(last, lg)
        relegated = list(table.index[-3:])
        teams = sorted(set(table.index) - set(relegated) | set(PROMOTED_2627[lg]))
        model, _, _, _, _ = (None,) * 5
        cfg = league_config(lg); d = cfg["promoted_prior"]
        model = DixonColesModel(
            half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
            shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
            promoted_prior=(d, d))
        model.fit(allm, as_of_date=as_of, promoted_teams=set(PROMOTED_2627[lg]))
        res = simulate_season(model, round_robin(teams), teams, league_key=lg,
                              n_sims=nsim, seed=seed_for(lg, "2627"))
        p = res["champion_prob"]
        mk = MARKET_2627.get(lg, {})
        print(f"\n  {lg.upper()}  (retrocesse {relegated}; promosse {PROMOTED_2627[lg]})")
        print(f"  {'squadra':<16}{'NOSTRO':>9}{'MERCATO':>9}{'scarto':>9}  punti attesi")
        for k in np.argsort(-p)[:8]:
            t = teams[k]; pm = mk.get(t)
            sc = f"{(p[k]-pm)*100:+8.1f}" if pm is not None else "       -"
            pms = f"{pm*100:8.1f}%" if pm is not None else "       -"
            print(f"  {t:<16}{p[k]*100:8.1f}%{pms}{sc}  {res['points'][:,k].mean():6.1f}")
            out_rows.append(dict(league=lg, team=t, p_model=float(p[k]),
                                 p_market=pm, exp_points=float(res["points"][:, k].mean())))
    return out_rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nsim", type=int, default=20000)
    ap.add_argument("--skip-2627", action="store_true")
    ap.add_argument("--no-log", action="store_true", help="non registrare in runs.jsonl")
    args = ap.parse_args(argv)

    print(f"### BACKTEST CAMPIONE DI STAGIONE  (nsim={args.nsim})")
    df = run_backtest(args.nsim)
    rep = report(df)
    pred = predict_2627(args.nsim) if not args.skip_2627 else []

    out = Path("experiments/fase89_season_champion.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(
        dict(backtest=df.to_dict("records"), report=rep, pred_2627=pred), indent=2))
    print(f"\nDettaglio scritto in {out}")

    if not args.no_log:
        # make_record (invece di un dict a mano) per avere l'IMPRONTA DATI come
        # tutti gli altri 713 run: senza, un cambio silenzioso degli snapshot non
        # sarebbe rilevabile a posteriori (audit Fase 90).
        fp = "|".join(f"{lg}:{experiment_log.data_fingerprint(loader.load_league(lg))}"
                      for lg in LEAGUES)
        rec = experiment_log.make_record(
            config=dict(nsim=args.nsim, model="dixon_coles+montecarlo_stagione",
                        leagues=list(LEAGUES), phase="89",
                        script="_run_fase89_season_champion.py"),
            metrics_dict=rep, fingerprint=fp)
        rec["note"] = "Mercato campione di stagione: backtest su 24 stagioni-lega."
        experiment_log.append_run(rec)
        print("Run registrato in experiments/runs.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
