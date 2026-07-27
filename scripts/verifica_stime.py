"""VERIFICA delle stime dichiarate (data/estimates/): sono giuste? e il
ragionamento che le ha prodotte regge?

Il dato vero (chiusura O/U 2.5 delle stagioni 2017-18/2018-19) non e'
procurabile (vedi il report del ritentativo). Allora si fa l'altra meta' del
lavoro chiesta: **verificare la stima**, cercando di DIMOSTRARE CHE E' SBAGLIATA.

Cosa fa, in ordine:

  1. RIPRODUCIBILITA' — re-implementa l'estimatore E3 dalla formula documentata
     (senza chiamare build_estimates.py) e confronta riga per riga col file
     committato. Se il file non e' rigenerabile, e' gia' un problema.
  2. COEFFICIENTI — li ricalcola e ne verifica il senso (beta su logit(OU)
     vicino a 1 = "la chiusura somiglia all'apertura"; segni del movimento 1X2).
  3. ERRORE DICHIARATO — ricalcola il MAE con protocolli PIU' severi di quello
     dichiarato: leave-one-season-out (walk-forward vero), leave-one-league-out
     (il pooling regge?), e per-stagione (l'errore e' stabile nel tempo?).
  4. VALE LA PENA? — confronto con 3 alternative piu' semplici: identita'
     (chiusura = apertura), solo-logit(OU) senza movimento 1X2, media di lega.
     Se l'identita' pareggia, il modello non serve.
  5. DOMAIN SHIFT (il limite dichiarato, ora MISURATO) — i coefficienti sono
     fittati su input `Avg` (media multi-book) ma applicati a input `BbAv`
     (Betbrain). Quanto costa cambiare provider dell'input? Si misura
     rifacendo il fit con un provider diverso (B365) e valutando sul solito.
  6. FALSIFICAZIONE SUL BERSAGLIO — l'unica verifica possibile *dentro* il
     2017-19: la stima di chiusura deve battere l'apertura reale nel predire
     l'esito Over/Under davvero accaduto. Se non lo fa, la stima non aggiunge
     informazione (o la toglie).
  7. INPUT CORROTTI — le righe la cui stima poggia su una quota impossibile
     (overround assurdo, vedi audit_anomalie.py) vanno marcate come inaffidabili.
  8. ALTRE STIME — open_sparse_1x2_ou.csv e squad_value_2017_26.csv:
     coerenza con quanto dichiarato in docs/DATI.md.

Uso: python scripts/verifica_stime.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation import metrics  # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"
LEAGUES = ["serie_a", "premier_league", "la_liga"]
FIT_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
TARGET_SEASONS = ["1718", "1819"]
EPS = 1e-6


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def load_all() -> pd.DataFrame:
    frames = []
    for lg in LEAGUES:
        df = pd.read_csv(ROOT / "data" / f"{lg}_matches.csv",
                         dtype={"season": str}, parse_dates=["date"])
        df["league"] = lg
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def add_probs(df: pd.DataFrame) -> pd.DataFrame:
    """Probabilita' devigate: 1X2 chiusura/apertura, O/U apertura (input) e
    O/U chiusura (bersaglio, solo dove esiste)."""
    out = df.copy()
    pc = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                   if pd.notna(r.odds_home) else (np.nan,) * 3
                   for r in df.itertuples()])
    po = np.array([metrics.devig_1x2(r.odds_home_open, r.odds_draw_open, r.odds_away_open)
                   if pd.notna(r.odds_home_open) else (np.nan,) * 3
                   for r in df.itertuples()])
    out[["pH_c", "pD_c", "pA_c"]] = pc
    out[["pH_o", "pD_o", "pA_o"]] = po
    out["p_over_open"] = [
        metrics.devig_binary(r.odds_over25_open, r.odds_under25_open)[0]
        if pd.notna(r.odds_over25_open) else np.nan for r in df.itertuples()]
    out["p_over_close"] = [
        metrics.devig_binary(r.odds_over25, r.odds_under25)[0]
        if pd.notna(r.odds_over25) else np.nan for r in df.itertuples()]
    out["is_over"] = ((out.home_goals + out.away_goals) > 2.5).astype(float)
    return out


def design_E3(df: pd.DataFrame) -> np.ndarray:
    """1, logit(OU apertura), Dlogit(H), Dlogit(D), Dlogit(A)  [Fase 62-bis]."""
    return np.column_stack([
        np.ones(len(df)),
        logit(df["p_over_open"]),
        logit(df["pH_c"]) - logit(df["pH_o"]),
        logit(df["pD_c"]) - logit(df["pD_o"]),
        logit(df["pA_c"]) - logit(df["pA_o"]),
    ])


def fit_ols(X, y):
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def mae(a, b):
    return float(np.abs(np.asarray(a) - np.asarray(b)).mean())


def logloss_binary(p, y):
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    y = np.asarray(y, float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    res: dict = {}
    all_df = add_probs(load_all())

    fit_mask = all_df.season.isin(FIT_SEASONS) & all_df[
        ["p_over_open", "p_over_close", "pH_c", "pH_o"]].notna().all(axis=1)
    fit = all_df[fit_mask].reset_index(drop=True)
    tgt_mask = all_df.season.isin(TARGET_SEASONS) & all_df[
        ["p_over_open", "pH_c", "pH_o"]].notna().all(axis=1)
    tgt = all_df[tgt_mask].reset_index(drop=True)
    print(f"fit: {len(fit)} partite (2019-20+); bersaglio: {len(tgt)} partite (2017-19)")

    # ---------------------------------------------------------------- 1 + 2
    print("\n[1-2] RIPRODUCIBILITA' e COEFFICIENTI")
    X, y = design_E3(fit), logit(fit["p_over_close"])
    coef = fit_ols(X, y)
    print(f"  coefficienti ricalcolati [1, logit(OU), dH, dD, dA] = "
          f"{np.array2string(coef, precision=4)}")
    p_est_tgt = sigmoid(design_E3(tgt) @ coef)

    committed = pd.read_csv(ROOT / "data" / "estimates" / "ou_close_2017_19.csv",
                            dtype={"season": str})
    mine = pd.DataFrame({
        "league": tgt.league, "season": tgt.season,
        "home_team": tgt.home_team, "away_team": tgt.away_team,
        "p_mine": np.round(p_est_tgt, 4)})
    j = committed.merge(mine, on=["league", "season", "home_team", "away_team"],
                        how="outer", indicator=True)
    only_c = int((j._merge == "left_only").sum())
    only_m = int((j._merge == "right_only").sum())
    both = j[j._merge == "both"]
    dmax = float((both.p_over25_close_est - both.p_mine).abs().max()) if len(both) else np.nan
    ok_repro = only_c == 0 and only_m == 0 and dmax <= 1e-4
    print(f"  file committato: {len(committed)} righe; ri-derivate: {len(mine)}; "
          f"solo-committato={only_c}, solo-mie={only_m}, "
          f"scarto massimo={dmax:.6f} -> {'RIPRODUCIBILE' if ok_repro else 'NON riproducibile'}")
    res["riproducibilita"] = {"n_committate": len(committed), "n_riderivate": len(mine),
                              "solo_committate": only_c, "solo_riderivate": only_m,
                              "scarto_max": dmax, "ok": bool(ok_repro),
                              "coefficienti": [float(c) for c in coef]}

    # ---------------------------------------------------------------- 3
    print("\n[3] ERRORE DICHIARATO (MAE ~0.012) sotto protocolli piu' severi")
    in_mae = mae(sigmoid(X @ coef), fit.p_over_close)
    # leave-one-season-out (walk-forward vero: si fitta su tutte le altre)
    los = {}
    for s in FIT_SEASONS:
        tr, te = fit[fit.season != s], fit[fit.season == s]
        c = fit_ols(design_E3(tr), logit(tr.p_over_close))
        los[s] = mae(sigmoid(design_E3(te) @ c), te.p_over_close)
    # leave-one-league-out (il pooling regge fuori dalla lega?)
    lol = {}
    for lg in LEAGUES:
        tr, te = fit[fit.league != lg], fit[fit.league == lg]
        c = fit_ols(design_E3(tr), logit(tr.p_over_close))
        lol[lg] = mae(sigmoid(design_E3(te) @ c), te.p_over_close)
    # walk-forward stretto: fit solo sul PASSATO (nessuna informazione futura)
    wf = {}
    for i, s in enumerate(FIT_SEASONS):
        if i == 0:
            continue
        tr = fit[fit.season.isin(FIT_SEASONS[:i])]
        te = fit[fit.season == s]
        c = fit_ols(design_E3(tr), logit(tr.p_over_close))
        wf[s] = mae(sigmoid(design_E3(te) @ c), te.p_over_close)
    print(f"  in-sample                  MAE {in_mae:.4f}")
    print(f"  leave-one-season-out       MAE {np.mean(list(los.values())):.4f} "
          f"(min {min(los.values()):.4f}, max {max(los.values()):.4f})")
    print(f"  leave-one-league-out       MAE {np.mean(list(lol.values())):.4f} "
          f"({', '.join(f'{k}={v:.4f}' for k, v in lol.items())})")
    print(f"  walk-forward (solo passato) MAE {np.mean(list(wf.values())):.4f}")
    res["errore"] = {"in_sample": in_mae, "leave_one_season_out": los,
                     "leave_one_league_out": lol, "walk_forward": wf,
                     "dichiarato": 0.012}

    # ---------------------------------------------------------------- 4
    print("\n[4] VALE LA PENA? confronto con alternative piu' semplici (leave-one-season-out)")
    def loso_mae(design_fn):
        vals = []
        for s in FIT_SEASONS:
            tr, te = fit[fit.season != s], fit[fit.season == s]
            c = fit_ols(design_fn(tr), logit(tr.p_over_close))
            vals.append(mae(sigmoid(design_fn(te) @ c), te.p_over_close))
        return float(np.mean(vals))

    d_ident = mae(fit.p_over_open, fit.p_over_close)      # chiusura = apertura
    d_logit1 = loso_mae(lambda d: np.column_stack([np.ones(len(d)), logit(d.p_over_open)]))
    d_e3 = float(np.mean(list(los.values())))
    d_mean = mae(np.full(len(fit), fit.p_over_close.mean()), fit.p_over_close)
    print(f"  identita' (chiusura=apertura)      MAE {d_ident:.4f}")
    print(f"  media di lega (costante)           MAE {d_mean:.4f}")
    print(f"  solo logit(OU) (senza 1X2)         MAE {d_logit1:.4f}")
    print(f"  E3 completo (con movimento 1X2)    MAE {d_e3:.4f}"
          f"   [guadagno vs identita': {(d_ident-d_e3)/d_ident:+.1%}]")
    res["alternative"] = {"identita": d_ident, "media": d_mean,
                          "solo_logit_ou": d_logit1, "E3": d_e3}

    # ---------------------------------------------------------------- 5
    print("\n[5] DOMAIN SHIFT: e se l'input viene da un provider diverso?")
    #  input alternativo: linea O/U pre-match di Bet365 invece della media Avg.
    raw_b365 = []
    for lg in LEAGUES:
        for s in FIT_SEASONS:
            r = pd.read_csv(ROOT / "data" / "fonti" / "football_data"
                            / f"{lg}_{s}.csv", encoding="latin-1")
            r = r.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
            from src.data import sources
            raw_b365.append(pd.DataFrame({
                "league": lg, "season": s,
                "home_team": r.HomeTeam.astype(str).str.strip().map(sources.canonical_team),
                "away_team": r.AwayTeam.astype(str).str.strip().map(sources.canonical_team),
                "b365_over": pd.to_numeric(r.get("B365>2.5"), errors="coerce"),
                "b365_under": pd.to_numeric(r.get("B365<2.5"), errors="coerce")}))
    b365 = pd.concat(raw_b365, ignore_index=True)
    f2 = fit.merge(b365, on=["league", "season", "home_team", "away_team"], how="left")
    f2 = f2[f2[["b365_over", "b365_under"]].notna().all(axis=1)].copy()
    f2["p_over_b365"] = [metrics.devig_binary(r.b365_over, r.b365_under)[0]
                         for r in f2.itertuples()]
    #  fit su input Avg -> applicato a input B365 (stessa partita, stesso bersaglio)
    def design_with(d, col):
        return np.column_stack([
            np.ones(len(d)), logit(d[col]),
            logit(d.pH_c) - logit(d.pH_o), logit(d.pD_c) - logit(d.pD_o),
            logit(d.pA_c) - logit(d.pA_o)])
    c_avg = fit_ols(design_with(f2, "p_over_open"), logit(f2.p_over_close))
    mae_same = mae(sigmoid(design_with(f2, "p_over_open") @ c_avg), f2.p_over_close)
    mae_shift = mae(sigmoid(design_with(f2, "p_over_b365") @ c_avg), f2.p_over_close)
    print(f"  input dello stesso provider (Avg)  MAE {mae_same:.4f}   (n={len(f2)})")
    print(f"  input di provider DIVERSO (B365)   MAE {mae_shift:.4f}"
          f"   [+{(mae_shift-mae_same)/mae_same:.1%}]")
    print(f"  -> il cambio di provider dell'input costa ~{mae_shift-mae_same:+.4f} di MAE:"
          f" e' l'ordine di grandezza del rischio non misurato sul 2017-19 (BbAv).")
    res["domain_shift"] = {"mae_stesso_provider": mae_same,
                           "mae_provider_diverso": mae_shift, "n": len(f2)}

    # ---------------------------------------------------------------- 6
    print("\n[6] FALSIFICAZIONE sul bersaglio: la stima batte l'apertura REALE"
          " nel predire l'esito accaduto?")
    #  riferimento: nelle stagioni con la chiusura VERA, di quanto batte l'apertura?
    ll_open_fit = logloss_binary(fit.p_over_open, fit.is_over)
    ll_close_fit = logloss_binary(fit.p_over_close, fit.is_over)
    ll_est_fit = logloss_binary(sigmoid(X @ coef), fit.is_over)
    #  bersaglio 2017-19: apertura reale vs stima
    ll_open_tgt = logloss_binary(tgt.p_over_open, tgt.is_over)
    ll_est_tgt = logloss_binary(p_est_tgt, tgt.is_over)
    print(f"  2019-20+ (dove la verita' esiste):")
    print(f"     apertura reale  log-loss {ll_open_fit:.5f}")
    print(f"     CHIUSURA vera   log-loss {ll_close_fit:.5f}  "
          f"(guadagno vero {ll_open_fit-ll_close_fit:+.5f})")
    print(f"     stima E3        log-loss {ll_est_fit:.5f}  "
          f"(guadagno stimato {ll_open_fit-ll_est_fit:+.5f})")
    print(f"  2017-19 (il bersaglio, verita' ignota):")
    print(f"     apertura reale  log-loss {ll_open_tgt:.5f}")
    print(f"     stima E3        log-loss {ll_est_tgt:.5f}  "
          f"(guadagno {ll_open_tgt-ll_est_tgt:+.5f})")
    #  bootstrap appaiato sul bersaglio (B=10.000), regola CI95 del progetto
    rng = np.random.default_rng(7)
    d = []
    po, pe, yv = (tgt.p_over_open.to_numpy(), p_est_tgt, tgt.is_over.to_numpy())
    for _ in range(10000):
        idx = rng.integers(0, len(yv), len(yv))
        d.append(logloss_binary(po[idx], yv[idx]) - logloss_binary(pe[idx], yv[idx]))
    lo, hi = np.percentile(d, [2.5, 97.5])
    print(f"     bootstrap appaiato B=10.000: guadagno medio {np.mean(d):+.5f} "
          f"CI95 [{lo:+.5f}, {hi:+.5f}] -> "
          f"{'CONCLUSIVO' if lo > 0 else 'NON conclusivo'}")
    res["falsificazione"] = {
        "fit_ll_open": ll_open_fit, "fit_ll_close_vero": ll_close_fit,
        "fit_ll_stima": ll_est_fit, "tgt_ll_open": ll_open_tgt,
        "tgt_ll_stima": ll_est_tgt, "tgt_ci95": [float(lo), float(hi)],
        "tgt_guadagno_medio": float(np.mean(d))}

    # ---------------------------------------------------------------- 7
    print("\n[7] INPUT CORROTTI: stime che poggiano su quote impossibili")
    orr = 1 / tgt.odds_over25_open + 1 / tgt.odds_under25_open
    bad = tgt[orr > 1.12]
    print(f"  {len(bad)} stime poggiano su una linea O/U con overround > 1.12 "
          f"(impossibile per una media multi-book):")
    corrupted = []
    for i, r in bad.iterrows():
        corrupted.append({"league": r.league, "season": r.season,
                          "date": str(r.date.date()),
                          "match": f"{r.home_team}-{r.away_team}",
                          "overround": round(float(orr[i]), 4),
                          "p_over_input": round(float(r.p_over_open), 4),
                          "p_over_stimata": round(float(p_est_tgt[i]), 4)})
        print(f"     {corrupted[-1]}")
    res["input_corrotti"] = corrupted

    # ---------------------------------------------------------------- 8
    print("\n[8] ALTRE STIME dichiarate")
    sparse = pd.read_csv(ROOT / "data" / "estimates" / "open_sparse_1x2_ou.csv",
                         dtype={"season": str})
    sq = pd.read_csv(ROOT / "data" / "estimates" / "squad_value_2017_26.csv")
    print(f"  open_sparse_1x2_ou.csv: {len(sparse)} righe (docs/DATI.md dichiara 2)")
    for r in sparse.itertuples():
        print(f"     {r.league} {r.season} {r.date} {r.home_team}-{r.away_team}")
    print(f"  squad_value_2017_26.csv: {len(sq)} righe (docs/DATI.md dichiara 0)")
    #  le partite "sparse" hanno davvero il buco che dichiarano?
    checks = []
    for r in sparse.itertuples():
        m = all_df[(all_df.league == r.league) & (all_df.season == r.season)
                   & (all_df.home_team == r.home_team) & (all_df.away_team == r.away_team)]
        if m.empty:
            checks.append({"match": f"{r.home_team}-{r.away_team}", "trovata": False})
            continue
        m = m.iloc[0]
        checks.append({
            "match": f"{r.home_team}-{r.away_team}", "trovata": True,
            "manca_apertura_1x2": bool(pd.isna(m.odds_home_open)),
            "stima_1x2_presente": bool(pd.notna(r.p_home_open_est)),
            "manca_apertura_ou": bool(pd.isna(m.odds_over25_open)),
            "stima_ou_presente": bool(pd.notna(r.p_over25_open_est))})
    coerenti = all(c.get("trovata") and
                   (c["manca_apertura_1x2"] == c["stima_1x2_presente"]) and
                   (c["manca_apertura_ou"] == c["stima_ou_presente"]) for c in checks)
    print(f"  coerenza 'stima solo dove il dato manca davvero': "
          f"{'OK' if coerenti else 'INCOERENTE'}")
    for c in checks:
        print(f"     {c}")
    res["altre_stime"] = {"open_sparse_n": len(sparse), "squad_value_n": len(sq),
                          "coerenza": bool(coerenti), "dettaglio": checks}

    (OUT / "verifica_stime.json").write_text(json.dumps(res, indent=2, default=str))
    print(f"\n-> {(OUT / 'verifica_stime.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
