"""Fase 94 — La varianza mancante: iniettare la deriva di forza in-stagione.

DIAGNOSI (Fasi 89-bis, 91, 93 + questa). Il simulatore di stagione ha due
difetti misurati che sembravano indipendenti:
  - il favorito per il TITOLO e' troppo sicuro (60.1% dichiarato, 41.7% realizzato);
  - le NEOPROMOSSE sono troppo condannate alla retrocessione (54.7% contro 48.6%).

Sembravano due problemi. Sono lo stesso. La verifica che li unifica:
  1. a livello di SINGOLA PARTITA le neopromosse NON sono predette troppo deboli
     (P(sconfitta) dichiarata 51.71%, realizzata 51.71%; punti attesi su 38
     giornate 36.4 contro 35.4 reali). Quindi delta NON e' il colpevole, e
     ritararlo sarebbe stato un cerotto sul sintomo;
  2. ma la classifica SIMULATA e' piu' schiacciata di quella vera: la
     dispersione reale supera la simulata in 21 stagioni su 24, e il valore
     reale cade in media all'83o percentile della distribuzione simulata
     (dovrebbe cadere al 50o).
  3. il conto torna: dispersione simulata 15.45 = 13.61 (differenze fra squadre)
     + 7.44 (rumore dei risultati), in quadratura. Per arrivare ai 17.51 reali
     serve INCERTEZZA in piu', non separazione in piu'.

Quell'incertezza ha un nome e una misura: la DERIVA DI FORZA in-stagione
(Fase 89-bis, sd 0.189 sulla forza netta, di cui ~38% in varianza e' errore di
stima -> deriva vera ~0.15). A luglio e' imprevedibile: un modello onesto la
rappresenta come incertezza, non come conoscenza.

COSA FA QUESTO SCRIPT
  A. calibra sigma sulla DISPERSIONE della classifica (24 osservazioni che NON
     sono i mercati: nessun overfitting sui 24 campioni);
  B. rivaluta con quel sigma i tre mercati stagionali (campione, top-4,
     retrocessione) e la calibrazione delle neopromosse.

  C. emette il VERDETTO per mercato (guadagno, IC95% bootstrap appaiato sulle
     24 stagioni-lega, conteggio dei segni), perche' l'adozione e' PER MERCATO
     (§1.8) e non si legge da un aggregato.

Uso:
  python scripts/_run_fase94_drift.py                 # calibrazione + valutazione
  python scripts/_run_fase94_drift.py --sd 0.15       # salta la calibrazione
  python scripts/_run_fase94_drift.py --sd-map        # il sigma PER-SQUADRA
      adottato (src.config.DRIFT_SD: 0.30 neopromosse / 0.16 le altre) — e' la
      configurazione che il progetto usa per il mercato retrocessione

Nota sull'ECE: 10 fasce EQUISPAZIATE (la funzione e' quella della Fase 91,
scripts/_run_fase91_positions.ece). Il binning va dichiarato: due ECE calcolati
con binning diversi non sono confrontabili.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DRIFT_SD, drift_sd_map                  # noqa: E402
from src.data import loader                                    # noqa: E402
from src.evaluation import experiment_log                      # noqa: E402
from src.models.season_sim import final_table, simulate_season  # noqa: E402
from scripts._run_fase89_season_champion import (              # noqa: E402
    LEAGUES, fit_at_season_start, seed_for, bootstrap_ci,
)
from scripts._run_fase91_positions import ece                  # noqa: E402

GRID = (0.00, 0.08, 0.12, 0.15, 0.18, 0.22, 0.28)
NSIM = 20000


def _cases():
    for lg in LEAGUES:
        allm = loader.load_league(lg)
        allm["date"] = pd.to_datetime(allm["date"])
        seasons = sorted(allm["season"].unique())
        for i, S in enumerate(seasons):
            if i == 0:
                continue
            yield lg, S, allm, seasons, i


def evaluate(sd, nsim=NSIM, verbose=False) -> pd.DataFrame:  # sd: float | "map"
    """Un giro completo di simulazioni con deriva ``sd``: una riga per squadra.

    ``sd`` e' uno scalare oppure la stringa ``"map"``, che attiva il sigma
    PER-SQUADRA di `src.config.drift_sd_map` (0.30 neopromosse / 0.16 le altre).
    E' la configurazione ADOTTATA per il mercato retrocessione: senza questa
    opzione il risultato pubblicato non era ri-derivabile dallo script (lo
    script conosceva solo un sigma uniforme — audit Fase 101).
    """
    rows = []
    for lg, S, allm, seasons, i in _cases():
        model, cur, teams, promoted, _ = fit_at_season_start(allm, lg, S, seasons)
        sd_arg = drift_sd_map(teams, promoted) if sd == "map" else sd
        out = simulate_season(model, list(zip(cur["home_team"], cur["away_team"])),
                              teams, league_key=lg, n_sims=nsim, seed=seed_for(lg, S),
                              drift_sd=sd_arg)
        tab = final_table(cur, lg)
        pos = {t: k + 1 for k, t in enumerate(tab.index)}
        nt = len(teams)
        champ = tab.index[0]
        p = out["champion_prob"]
        rank = out["rank"]
        # dispersione: il valore REALE a che percentile cade fra le simulazioni?
        sd_sims = out["points"].std(axis=1)
        sd_real = float(tab["pts"].astype(float).std(ddof=0))
        pct = float((sd_sims < sd_real).mean())
        for k, t in enumerate(teams):
            rows.append(dict(
                league=lg, season=S, team=t, promoted=bool(t in promoted),
                p_champ=float(p[k]), is_champ=bool(t == champ),
                p_top4=float((rank[:, k] <= 4).mean()),
                is_top4=bool(pos[t] <= 4),
                p_rel=float((rank[:, k] >= nt - 2).mean()),
                is_rel=bool(pos[t] > nt - 3),
                spread_pct=pct))
        if verbose:
            print(f"    {lg:15} {S}  percentile dispersione {pct*100:5.1f}%", flush=True)
    return pd.DataFrame(rows)


def spread_score(df: pd.DataFrame) -> float:
    """Quanto la dispersione simulata e' tarata: |percentile medio - 50%|.
    0 = perfetta. E' il bersaglio della calibrazione, ed e' indipendente dagli
    esiti dei mercati (campione/top-4/retrocessione)."""
    per_case = df.groupby(["league", "season"])["spread_pct"].first()
    return float(abs(per_case.mean() - 0.5))


def markets(df: pd.DataFrame) -> dict:
    def ll_bin(p, y):
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    ch = df[df["is_champ"]]
    fav = df.loc[df.groupby(["league", "season"])["p_champ"].idxmax()]
    prom = df[df["promoted"]]
    return dict(
        champion_logloss=float(-np.log(ch["p_champ"].clip(1e-9)).mean()),
        favourite_declared=float(fav["p_champ"].mean()),
        favourite_realised=float(fav["is_champ"].mean()),
        top4_logloss=ll_bin(df["p_top4"].to_numpy(), df["is_top4"].to_numpy().astype(float)),
        rel_logloss=ll_bin(df["p_rel"].to_numpy(), df["is_rel"].to_numpy().astype(float)),
        promoted_rel_declared=float(prom["p_rel"].mean()),
        promoted_rel_realised=float(prom["is_rel"].mean()),
        spread_pct=float(df.groupby(["league", "season"])["spread_pct"].first().mean()),
        # ECE a 10 FASCE EQUISPAZIATE (stessa funzione della Fase 91,
        # scripts/_run_fase91_positions.ece): il binning va dichiarato, perche'
        # l'ECE non e' confrontabile fra binning diversi.
        top4_ece=ece(df["p_top4"].to_numpy(), df["is_top4"].to_numpy().astype(float)),
        rel_ece=ece(df["p_rel"].to_numpy(), df["is_rel"].to_numpy().astype(float)),
    )


# --------------------------------------------------------------------------- #
# VERDETTO per-mercato (§1.8: si adotta o si scarta UN MERCATO ALLA VOLTA)
# --------------------------------------------------------------------------- #
def _per_case_logloss(df: pd.DataFrame) -> pd.DataFrame:
    """Log-loss dei tre mercati per ogni (lega, stagione): 24 osservazioni.

    Sono le unita' indipendenti dell'esperimento — le 20 squadre di una stessa
    classifica non lo sono (sommano a 1 posto per posto), quindi il bootstrap
    ricampiona le stagioni-lega, non le squadre.
    """
    def ll_bin(p, y):
        p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
        y = np.asarray(y, float)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

    rows = []
    for (lg, S), g in df.groupby(["league", "season"]):
        champ = g.loc[g["is_champ"], "p_champ"]
        rows.append(dict(
            league=lg, season=S,
            champion=float(-np.log(max(float(champ.iloc[0]), 1e-12))),
            top4=ll_bin(g["p_top4"], g["is_top4"].astype(float)),
            rel=ll_bin(g["p_rel"], g["is_rel"].astype(float))))
    return pd.DataFrame(rows).sort_values(["league", "season"])


def verdetto(df0: pd.DataFrame, df1: pd.DataFrame) -> dict:
    """Guadagno per mercato = log-loss SENZA deriva − log-loss CON, con IC95%
    bootstrap appaiato sulle 24 stagioni-lega e conteggio dei segni."""
    a, b = _per_case_logloss(df0), _per_case_logloss(df1)
    assert list(zip(a.league, a.season)) == list(zip(b.league, b.season))
    out = {}
    for mk, lab in (("rel", "retrocessione"), ("champion", "campione"),
                    ("top4", "top-4")):
        gain = (a[mk].to_numpy() - b[mk].to_numpy())
        lo, hi = bootstrap_ci(gain, n_boot=10000, seed=94)
        out[mk] = dict(etichetta=lab, guadagno=float(gain.mean()),
                       ci95=[lo, hi], migliori=int((gain > 0).sum()),
                       n=int(len(gain)),
                       conclusivo=bool(lo > 0 or hi < 0))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sd", type=float, default=None,
                    help="salta la calibrazione e usa questo sigma")
    ap.add_argument("--sd-map", action="store_true",
                    help="usa il sigma PER-SQUADRA di src.config.DRIFT_SD "
                         f"(promosse {DRIFT_SD['promoted']}, altre "
                         f"{DRIFT_SD['other']}) invece di uno scalare: e' la "
                         "configurazione ADOTTATA per la retrocessione")
    ap.add_argument("--nsim", type=int, default=NSIM)
    ap.add_argument("--no-log", action="store_true")
    args = ap.parse_args(argv)
    if args.sd_map and args.sd is not None:
        ap.error("--sd e --sd-map sono alternativi")

    results = {}
    df_zero = None          # il braccio SENZA deriva, tenuto per il verdetto
    if args.sd_map:
        sd_star = "map"
        df_star = evaluate(sd_star, args.nsim)
        results[sd_star] = dict(spread_pct=float(df_star.groupby(["league", "season"])
                                                 ["spread_pct"].first().mean()),
                                score=spread_score(df_star), markets=markets(df_star),
                                drift_sd=dict(DRIFT_SD))
    elif args.sd is None:
        print("### A. CALIBRAZIONE di sigma sulla DISPERSIONE della classifica")
        print("    (bersaglio: il valore reale deve cadere al 50o percentile delle")
        print("     simulazioni; oggi cade all'83o perche' la simulata e' schiacciata)")
        print(f"    {'sigma':>7}{'percentile medio':>20}{'|scarto dal 50%|':>20}")
        best = None
        for sd in GRID:
            df = evaluate(sd, args.nsim)
            sc = spread_score(df)
            pct = df.groupby(["league", "season"])["spread_pct"].first().mean()
            results[sd] = dict(spread_pct=float(pct), score=sc, markets=markets(df))
            print(f"    {sd:7.2f}{pct*100:19.1f}%{sc*100:19.1f}pp", flush=True)
            if sd == 0.0:
                df_zero = df
            if best is None or sc < best[1]:
                best = (sd, sc, df)
        sd_star, _, df_star = best
        print(f"\n  sigma* = {sd_star:.2f}")
    else:
        sd_star = args.sd
        df_star = evaluate(sd_star, args.nsim)
        results[sd_star] = dict(spread_pct=float(df_star.groupby(["league", "season"])
                                                 ["spread_pct"].first().mean()),
                                score=spread_score(df_star), markets=markets(df_star))

    # Il braccio SENZA deriva serve come DataFrame (non solo come aggregati):
    # il verdetto per-mercato e' un bootstrap APPAIATO sulle 24 stagioni-lega.
    df0 = df_zero if df_zero is not None else evaluate(0.0, args.nsim)
    m0 = results.get(0.0, {}).get("markets") or markets(df0)
    m1 = results[sd_star]["markets"]
    etichetta_sd = (f"mappa promosse {DRIFT_SD['promoted']:.2f} / altre "
                    f"{DRIFT_SD['other']:.2f}" if sd_star == "map"
                    else f"{sd_star:.2f}")

    print("\n" + "=" * 78)
    print(f"### B. EFFETTO SUI MERCATI STAGIONALI  (deriva 0.00 -> {etichetta_sd})")
    fmt = "  {:38}{:>12}{:>12}"
    print(fmt.format("", "SENZA", "CON"))
    print(fmt.format("dispersione: percentile medio (50% = ok)",
                     f"{m0['spread_pct']*100:.1f}%", f"{m1['spread_pct']*100:.1f}%"))
    print(fmt.format("campione: log-loss",
                     f"{m0['champion_logloss']:.4f}", f"{m1['champion_logloss']:.4f}"))
    print(fmt.format("favorito: dichiarato",
                     f"{m0['favourite_declared']*100:.1f}%", f"{m1['favourite_declared']*100:.1f}%"))
    print(fmt.format("favorito: realizzato (invariato)",
                     f"{m0['favourite_realised']*100:.1f}%", f"{m1['favourite_realised']*100:.1f}%"))
    print(fmt.format("top-4: log-loss",
                     f"{m0['top4_logloss']:.4f}", f"{m1['top4_logloss']:.4f}"))
    print(fmt.format("retrocessione: log-loss",
                     f"{m0['rel_logloss']:.4f}", f"{m1['rel_logloss']:.4f}"))
    print(fmt.format("neopromosse: retroc. dichiarata",
                     f"{m0['promoted_rel_declared']*100:.1f}%",
                     f"{m1['promoted_rel_declared']*100:.1f}%"))
    print(fmt.format("neopromosse: retroc. realizzata (invariata)",
                     f"{m0['promoted_rel_realised']*100:.1f}%",
                     f"{m1['promoted_rel_realised']*100:.1f}%"))
    print(fmt.format("top-4: ECE (10 fasce equispaziate)",
                     f"{m0['top4_ece']:.4f}", f"{m1['top4_ece']:.4f}"))
    print(fmt.format("retrocessione: ECE (10 fasce equispaziate)",
                     f"{m0['rel_ece']:.4f}", f"{m1['rel_ece']:.4f}"))

    # ---- C. verdetto PER MERCATO, con incertezza ---------------------------- #
    # Senza questo blocco il risultato adottato (retrocessione si', campione e
    # top-4 no) non era ri-derivabile: `bootstrap_ci` era importato e mai usato
    # e lo script pubblicava solo aggregati (audit Fase 101).
    ver = verdetto(df0, df_star)
    print("\n### C. VERDETTO PER MERCATO  (guadagno = log-loss SENZA − CON;")
    print("       bootstrap appaiato B=10.000 sulle stagioni-lega, seed 94)")
    print("  {:16}{:>11}{:>24}{:>12}{:>13}".format(
        "mercato", "guadagno", "IC95%", "migliori", "verdetto"))
    for mk in ("rel", "champion", "top4"):
        v = ver[mk]
        print("  {:16}{:>+11.4f}{:>24}{:>12}{:>13}".format(
            v["etichetta"], v["guadagno"],
            f"[{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]",
            f"{v['migliori']}/{v['n']}",
            "CONCLUSIVO" if v["conclusivo"] else "nel rumore"))
    results[sd_star]["verdetto_per_mercato"] = ver

    dest = Path("experiments/fase94_drift.json")
    dest.write_text(json.dumps({str(k): v for k, v in results.items()}, indent=2))
    print(f"\nScritto {dest}")

    if not args.no_log:
        fp = "|".join(f"{lg}:{experiment_log.data_fingerprint(loader.load_league(lg))}"
                      for lg in LEAGUES)
        rec = experiment_log.make_record(
            config=dict(phase="94", script="_run_fase94_drift.py",
                        drift_sd=(dict(DRIFT_SD) if sd_star == "map" else sd_star),
                        nsim=args.nsim, grid=list(GRID),
                        ece_bins=10, ece_binning="equispaziato"),
            metrics_dict={"senza": m0, "con": m1,
                          "verdetto_per_mercato": ver}, fingerprint=fp)
        rec["note"] = "Deriva di forza in-stagione iniettata nel simulatore."
        experiment_log.append_run(rec)
        print("Run registrato in experiments/runs.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
