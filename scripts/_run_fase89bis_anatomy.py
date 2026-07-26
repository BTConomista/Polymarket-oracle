"""Fase 89-bis — Anatomia degli errori del mercato campione, e cosa servirebbe.

Domanda dell'utente: «quante volte hai indovinato il vincitore, e hai capito
perche' hai sbagliato le altre? altri dati potrebbero aiutarti?»

Tre analisi, tutte sui 24 casi del backtest della Fase 89
(`experiments/fase89_season_champion.json`, prodotto da
`_run_fase89_season_champion.py`):

  A. ANATOMIA — dove finisce il campione vero nella nostra classifica, e cosa
     separa i centri dagli errori;
  B. IL VALORE ROSA AIUTA? — test della covariata `squad_value` (che a inizio
     stagione contiene il MERCATO ESTIVO, l'informazione che i risultati passati
     non possono avere) sullo stesso protocollo walk-forward;
  C. LA DERIVA DI FORZA — quanto cambia la forza di una squadra DENTRO una
     stagione: la varianza che il simulatore, tenendo le forze fisse, ignora.

Uso:
  python scripts/_run_fase89bis_anatomy.py            # A + C (veloce)
  python scripts/_run_fase89bis_anatomy.py --squad-value   # anche B (~4 min)
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
from src.models.dixon_coles import DixonColesModel       # noqa: E402
from src.models.season_sim import final_table, simulate_season  # noqa: E402

LEAGUES = ("serie_a", "premier_league", "la_liga")
RESULTS = Path("experiments/fase89_season_champion.json")


def seed_for(*parts) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0x7FFFFFFF


# ------------------------------------------------------------------ A ------ #
def anatomy(df: pd.DataFrame) -> dict:
    n = len(df)
    hits = df[df.favourite_correct]
    print("=" * 74)
    print(f"### A. ANATOMIA — favorito azzeccato {len(hits)}/{n} = {len(hits)/n*100:.0f}%\n")

    print("  Dove finisce il CAMPIONE VERO nella nostra classifica di probabilita':")
    for k, v in df.rank_of_champion.value_counts().sort_index().items():
        cum = (df.rank_of_champion <= k).sum()
        print(f"    {k}o posto: {v:2d}/{n}   cumulato {cum}/{n} ({cum/n*100:.0f}%)")

    print("\n  LA SEPARAZIONE CHE SPIEGA TUTTO — il titolo resta o cambia mano?")
    keep, chg = df[df.repeat], df[~df.repeat]
    print(f"    titolo CONFERMATO ({len(keep)} stagioni): azzeccate "
          f"{keep.favourite_correct.sum()}/{len(keep)} = {keep.favourite_correct.mean()*100:.0f}%")
    print(f"    titolo CAMBIA mano ({len(chg)} stagioni): azzeccate "
          f"{chg.favourite_correct.sum()}/{len(chg)} = {chg.favourite_correct.mean()*100:.0f}%")
    print("    -> il modello, fittato sui risultati passati, non ha alcun")
    print("       meccanismo per anticipare un cambio al vertice.")

    def topk(r, k):
        return sum(sorted(r["probs"].values(), reverse=True)[:k])
    df["p_top2"] = df.apply(lambda r: topk(r, 2), axis=1)
    df["p_top3"] = df.apply(lambda r: topk(r, 3), axis=1)
    t2 = df[df.rank_of_champion <= 2]
    print("\n  DOVE STA DAVVERO L'ERRORE (il modello riconosce le contendenti?):")
    print(f"    P(vince uno dei nostri primi 2): dichiarata {df.p_top2.mean()*100:.1f}%  "
          f"reale {(df.rank_of_champion<=2).mean()*100:.1f}%  "
          f"scarto {((df.rank_of_champion<=2).mean()-df.p_top2.mean())*100:+.1f}pp")
    print(f"    P(vince uno dei nostri primi 3): dichiarata {df.p_top3.mean()*100:.1f}%  "
          f"reale {(df.rank_of_champion<=3).mean()*100:.1f}%  "
          f"scarto {((df.rank_of_champion<=3).mean()-df.p_top3.mean())*100:+.1f}pp")
    # Confronto CONDIZIONATO: dato che il campione e' uno dei nostri primi due,
    # la nostra probabilita' che sia il PRIMO e' p1/(p1+p2), non p1 (che e'
    # marginale). Confrontare p1 con una frequenza condizionata mescolava due
    # quantita' diverse e sottostimava la sovra-confidenza (audit Fase 90).
    def _share_top1(r):
        p = sorted(r["probs"].values(), reverse=True)
        return p[0] / (p[0] + p[1])
    share = t2.apply(_share_top1, axis=1).mean()
    print(f"    scelta DENTRO il top-2: giusta {(t2.rank_of_champion==1).sum()}/{len(t2)} = "
          f"{(t2.rank_of_champion==1).mean()*100:.1f}%  "
          f"(dichiaravamo {share*100:.1f}% = media di p1/(p1+p2))")
    print("    -> calibrati sul GRUPPO di testa, sbagliati nella SCELTA fra i suoi membri:")
    print(f"       diamo {share*100:.0f}% al nostro primo contro i due, ne azzecchiamo "
          f"{(t2.rank_of_champion==1).mean()*100:.0f}%.")

    print("\n  Calibrazione per fascia di confidenza:")
    for lo, hi, lab in [(0, .5, "sotto 50%"), (.5, .7, "50-70%"), (.7, 1.01, "sopra 70%")]:
        g = df[(df.p_favourite >= lo) & (df.p_favourite < hi)]
        if len(g):
            print(f"    {lab:10} n={len(g):2d}  dichiarato {g.p_favourite.mean()*100:5.1f}%  "
                  f"realizzato {g.favourite_correct.mean()*100:5.1f}%  "
                  f"scarto {(g.favourite_correct.mean()-g.p_favourite.mean())*100:+6.1f}pp")

    return dict(hit_rate=float(df.favourite_correct.mean()),
                hit_when_title_kept=[int(keep.favourite_correct.sum()), int(len(keep))],
                hit_when_title_changes=[int(chg.favourite_correct.sum()), int(len(chg))],
                champion_in_top2=int((df.rank_of_champion <= 2).sum()),
                champion_in_top3=int((df.rank_of_champion <= 3).sum()),
                p_top2_declared=float(df.p_top2.mean()),
                p_top2_realised=float((df.rank_of_champion <= 2).mean()),
                pick_within_top2=[int((t2.rank_of_champion == 1).sum()), int(len(t2))],
                pick_within_top2_declared=float(share))


def temperature_recal(df: pd.DataFrame) -> dict:
    """La sovra-confidenza si corregge ammorbidendo le probabilita' post-hoc?

    p_i(T) = p_i^(1/T) / somma_j p_j^(1/T).  T>1 appiattisce.
    Si riporta il T ottimo IN-SAMPLE (ottimistico) e il log-loss LEAVE-ONE-OUT
    (onesto: T tarato sulle altre 23 stagioni). Aggiunto qui alla Fase 90:
    i numeri erano stati calcolati a mano e non erano riproducibili da alcuno
    script, contro la regola di riproducibilita' del progetto.
    """
    P, y = [], []
    for _, r in df.iterrows():
        teams = list(r["probs"])
        P.append(np.array([r["probs"][t] for t in teams], float))
        y.append(teams.index(r["champion"]))

    def ll(T, idx):
        tot = 0.0
        for i in idx:
            q = np.power(np.clip(P[i], 1e-12, None), 1.0 / T)
            q /= q.sum()
            tot += -np.log(max(q[y[i]], 1e-12))
        return tot / len(idx)

    grid = np.arange(0.80, 3.005, 0.01)
    allidx = list(range(len(P)))
    T_in = float(grid[int(np.argmin([ll(T, allidx) for T in grid]))])
    base, best_in = ll(1.0, allidx), ll(T_in, allidx)
    loo = []
    for i in allidx:
        rest = [j for j in allidx if j != i]
        T = float(grid[int(np.argmin([ll(T, rest) for T in grid]))])
        loo.append(ll(T, [i]))
    loo_mean = float(np.mean(loo))
    print("\n" + "=" * 74)
    print("### D. RICALIBRAZIONE A TEMPERATURA (basta ammorbidire post-hoc?)")
    print(f"  nessuna correzione (T=1)     : {base:.4f}")
    print(f"  T ottimo IN-SAMPLE = {T_in:.2f}     : {best_in:.4f}  (guadagno {base-best_in:.4f})")
    print(f"  LEAVE-ONE-OUT (onesto)       : {loo_mean:.4f}  "
          f"-> {'PEGGIO' if loo_mean > base else 'meglio'} del non fare nulla")
    print("  con n=24 non si stima onestamente nemmeno UN parametro:")
    print("  la correzione va fatta strutturalmente, non post-hoc.")
    return dict(base=float(base), T_insample=T_in, ll_insample=float(best_in),
                gain_insample=float(base - best_in), ll_loo=loo_mean)


# ------------------------------------------------------------------ B ------ #
def squad_value_test(nsim=20000) -> dict:
    """La covariata squad_value (= mercato estivo) migliora la previsione?"""
    print("\n" + "=" * 74)
    print("### B. IL VALORE ROSA AIUTA? (covariata squad_value, stesso protocollo)")
    print("    CAVEAT dichiarato: squad_value e' rilevato attorno al 1o settembre,")
    print("    cioe' 2-3 giornate DOPO il via. Non contiene risultati (e' una")
    print("    valutazione di mercato dei giocatori) ma non e' rigorosamente")
    print("    pre-stagionale: il test e' favorevole alla covariata, non contro.\n")
    rows = []
    for lg in LEAGUES:
        allm = loader.load_league(lg); allm["date"] = pd.to_datetime(allm["date"])
        seasons = sorted(allm.season.unique()); cfg = league_config(lg); d = cfg["promoted_prior"]
        for i, S in enumerate(seasons):
            if i == 0:
                continue
            cur = allm[allm.season == S].sort_values("date"); start = cur.date.min()
            prev = seasons[i - 1]
            tprev = (set(allm[allm.season == prev].home_team)
                     | set(allm[allm.season == prev].away_team))
            teams = sorted(set(cur.home_team) | set(cur.away_team))
            promoted = set(teams) - tprev
            fixtures = list(zip(cur.home_team, cur.away_team))
            feats = {}
            for r in cur.itertuples():
                feats.setdefault(r.home_team, r.home_squad_value)
                feats.setdefault(r.away_team, r.away_squad_value)
            champ = final_table(cur, lg).index[0]; k = teams.index(champ)
            prev_champ = final_table(allm[allm.season == prev], lg).index[0]
            res = {}
            for name, covs in [("base", ()), ("sv", ("squad_value",))]:
                m = DixonColesModel(half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
                                    shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
                                    promoted_prior=(d, d), covariates=covs)
                m.fit(allm, as_of_date=start, promoted_teams=promoted)
                # STESSO simulatore per le due braccia (stessi spareggi, stessi
                # semi): l'unica differenza dev'essere la covariata. Con due
                # implementazioni diverse ~9% del delta era artefatto di
                # spareggio (audit Fase 90).
                fn = (lambda h, a: {"home_squad_value": feats[h],
                                    "away_squad_value": feats[a]}) if covs else None
                p = simulate_season(m, fixtures, teams, league_key=lg,
                                    n_sims=nsim, seed=seed_for(lg, S),
                                    features=fn)["champion_prob"]
                res[name] = (float(p[k]), bool(teams[int(p.argmax())] == champ),
                             m.beta.get("squad_value"))
            rows.append(dict(league=lg, season=S, repeat=(champ == prev_champ),
                             base_p=res["base"][0], base_hit=res["base"][1],
                             sv_p=res["sv"][0], sv_hit=res["sv"][1], beta=res["sv"][2]))
    df = pd.DataFrame(rows)
    ll_b = -np.log(df.base_p.clip(1e-9)); ll_s = -np.log(df.sv_p.clip(1e-9))
    diff = (ll_b - ll_s).to_numpy()
    rng = np.random.default_rng(0)
    bs = diff[rng.integers(0, len(diff), size=(10000, len(diff)))].mean(axis=1)
    lo, hi = float(np.quantile(bs, .025)), float(np.quantile(bs, .975))
    print(f"  log-loss base {ll_b.mean():.4f}  ->  +squad_value {ll_s.mean():.4f}  "
          f"(delta {ll_s.mean()-ll_b.mean():+.4f})")
    print(f"  guadagno {diff.mean():+.4f}  IC95% [{lo:+.4f}, {hi:+.4f}]  -> "
          f"{'CONCLUSIVO' if lo > 0 else 'NON conclusivo'}")
    print(f"  favorito azzeccato: base {df.base_hit.sum()}/{len(df)}  +sv {df.sv_hit.sum()}/{len(df)}")
    ch = df[~df.repeat]
    print(f"  sulle {len(ch)} stagioni di CAMBIO: base {ch.base_hit.sum()}/{len(ch)}  "
          f"+sv {ch.sv_hit.sum()}/{len(ch)}")
    print(f"  beta medio {df.beta.mean():+.4f} (sempre positivo: il segnale esiste,")
    print("  ma e' gia' contenuto nei gol/xG -> ridondante, come alle Fasi 4c/66-70)")
    return dict(logloss_base=float(ll_b.mean()), logloss_squad_value=float(ll_s.mean()),
                gain=float(diff.mean()), ci=[lo, hi],
                hit_base=int(df.base_hit.sum()), hit_sv=int(df.sv_hit.sum()),
                beta_mean=float(df.beta.mean()))


# ------------------------------------------------------------------ C ------ #
def strength_drift() -> dict:
    """Quanto si muove la forza di una squadra DENTRO una stagione."""
    print("\n" + "=" * 74)
    print("### C. LA DERIVA DI FORZA IN-STAGIONE (la varianza che il MC ignora)")
    rows = []
    for lg in LEAGUES:
        allm = loader.load_league(lg); allm["date"] = pd.to_datetime(allm["date"])
        seasons = sorted(allm.season.unique()); cfg = league_config(lg); d = cfg["promoted_prior"]
        for i, S in enumerate(seasons):
            if i == 0:
                continue
            cur = allm[allm.season == S].sort_values("date")
            prev = seasons[i - 1]
            tprev = (set(allm[allm.season == prev].home_team)
                     | set(allm[allm.season == prev].away_team))
            teams = sorted(set(cur.home_team) | set(cur.away_team))
            promoted = set(teams) - tprev

            def fit(as_of):
                m = DixonColesModel(half_life_days=cfg["half_life_days"],
                                    shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                                    blend_signal=cfg["blend_signal"], promoted_prior=(d, d))
                return m.fit(allm, as_of_date=as_of, promoted_teams=promoted)
            m0 = fit(cur.date.min())
            m1 = fit(cur.date.max() + pd.Timedelta(days=1))
            for t in teams:
                rows.append(dict(
                    pre=m0.attack.get(t, 0) - m0.defense.get(t, 0),
                    post=m1.attack.get(t, 0) - m1.defense.get(t, 0)))
    D = pd.DataFrame(rows); D["delta"] = D.post - D.pre
    ratio = float(D.delta.std() / D.pre.std())
    print(f"  osservazioni (squadra-stagione)             : {len(D)}")
    print(f"  deviazione standard della deriva in stagione: {D.delta.std():.3f}")
    print(f"  dispersione delle forze fra squadre         : {D.pre.std():.3f}")
    print(f"  rapporto deriva/dispersione                 : {ratio*100:.0f}%")
    print(f"  correlazione forza pre vs post              : {D.pre.corr(D.post):.3f}")
    print("  ATTENZIONE (limite): la stima di inizio stagione e' piu' rumorosa di")
    print("  quella di fine, quindi questa deviazione mescola deriva VERA ed errore")
    print("  di stima -> e' un LIMITE SUPERIORE della deriva, non una misura pura.")
    return dict(n=len(D), drift_sd=float(D.delta.std()), between_sd=float(D.pre.std()),
                ratio=ratio, corr_pre_post=float(D.pre.corr(D.post)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--squad-value", action="store_true",
                    help="esegue anche il test B (~4 minuti)")
    ap.add_argument("--nsim", type=int, default=20000)
    args = ap.parse_args(argv)

    if not RESULTS.exists():
        print(f"Manca {RESULTS}: esegui prima scripts/_run_fase89_season_champion.py")
        return 1
    df = pd.DataFrame(json.load(open(RESULTS))["backtest"])

    out = {"anatomy": anatomy(df), "temperature": temperature_recal(df)}
    if args.squad_value:
        out["squad_value"] = squad_value_test(args.nsim)
    out["drift"] = strength_drift()

    dest = Path("experiments/fase89bis_anatomy.json")
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nScritto {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
