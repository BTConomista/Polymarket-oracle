"""Fronte 5 — la "forza degli undici attesi": si puo' costruire un PROXY delle
formazioni dai dati storici, e aggiunge informazione?

CONTESTO. Non abbiamo le formazioni ufficiali pre-partita (escono ~1h prima del
kickoff e andrebbero raccolte in tempo reale). Abbiamo pero'
files/player_scores/appearances.csv.gz = chi ha giocato e quanti minuti in OGNI
partita di IT1/GB1/ES1 dal 2012. E' un dato POST-partita: usarlo per la partita
stessa sarebbe look-ahead grossolano. Ma le presenze **delle giornate
precedenti** sono legittime, e da esse si puo' stimare *chi giochera'* e *quanto
vale l'undici atteso*.

LA COSTRUZIONE (walk-forward, solo dati con data < T).
Per la squadra X alla partita del giorno T, dalla finestra delle ultime
K=6 partite di campionato di X con data < T (minimo 4):

  minuti(p)  = somma dei minuti di p nella finestra          (cap 90 a partita)
  XI atteso  = gli 11 giocatori con piu' minuti nella finestra
  xi_conc    = Sum_{XI} minuti(p) / (11 * 90 * |W|)     in (0,1]
               1 = undici fisso che gioca sempre; basso = rotazione/emergenza
  xi_val     = Sum_{XI} v(p, T)   valore di mercato dell'undici atteso
               v = ultima valutazione Transfermarkt con data < T (max 550g)
  core       = gli 11 con piu' minuti su TUTTE le partite precedenti in stagione
  w(p)       = minuti di p nelle ultime L=2 partite / (90*L), in [0,1]
  missing    = 1 - Sum_{core} v(p)*w(p) / Sum_{core} v(p)
               quota di VALORE del nucleo che di recente non e' sceso in campo
               (proxy di infortuni/squalifiche/rotazioni: chi non ha giocato le
               ultime due e' il candidato assente)

Feature di partita (differenziali casa-ospite):
  d_xival   = log(xi_val_casa) - log(xi_val_ospite)
  d_missing = missing_casa - missing_ospite       (>0 = casa piu' decimata)
  d_conc    = xi_conc_casa - xi_conc_ospite

I TEST.
  A) mercato, campione pieno (3 leghe x 9 stagioni): la feature spiega il
     residuo della CHIUSURA devigata sul binario "casa vs ospite | non pareggio"?
     Se si', e' informazione che il mercato non ha (edge). Attesa: no.
  B) modello, campione Fase 93 (experiments/fase93_discrimination.csv, 3 leghe
     x 6 stagioni, partite non pareggiate, con m_* del DC e k_* del mercato):
     la feature spiega il residuo del DIXON-COLES? Se si', e' informazione che
     il nostro modello non ha.
  C) le stesse regressioni RISTRETTE alle partite equilibrate (terzile basso di
     |lam-mu| del mercato) della SECONDA META' di stagione, dove la Fase 93
     localizza il deficit di discriminazione.
  D) ridondanza: la feature sopravvive al controllo per il valore rosa
     (gia' bocciato in Fase 4c/11) e per il logit del modello?
  E) valore fuori campione: beta stimato sulle stagioni precedenti, applicato
     alla successiva; guadagno di log-loss con IC bootstrap appaiato.

Uso:  python scripts/_run_lineup_proxy.py
      python scripts/_run_lineup_proxy.py --rebuild   (ignora la cache feature)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import player_scores, sources          # noqa: E402
from src.data.transfermarkt import MAX_VALUE_AGE_DAYS  # noqa: E402
from src.evaluation import metrics                   # noqa: E402
from src.models import market_implied as mi          # noqa: E402

LEAGUES = {"serie_a": "IT1", "premier_league": "GB1", "la_liga": "ES1"}
K_RECENT = 6        # partite nella finestra dell'undici atteso
MIN_GAMES = 4       # minimo di partite precedenti per pubblicare la feature
L_AVAIL = 2         # ultime partite usate come segnale di disponibilita'
MIN_VAL_COV = 0.80  # copertura minima delle valutazioni sull'undici atteso
CACHE = ROOT / "outputs" / "lineup_proxy_features.csv"
F93 = ROOT / "experiments" / "fase93_discrimination.csv"
RNG = np.random.default_rng(20260726)


# --------------------------------------------------------------- dati grezzi
def load_appearances() -> pd.DataFrame:
    app = pd.read_csv(
        player_scores.DATA_DIR / "appearances.csv.gz",
        usecols=["game_id", "player_id", "player_club_id", "date",
                 "competition_id", "minutes_played"])
    app = app[app["competition_id"].isin(LEAGUES.values())].copy()
    app["date"] = pd.to_datetime(app["date"])
    clubs = pd.read_csv(player_scores.DATA_DIR / "clubs.csv.gz",
                        usecols=["club_id", "name"])
    name_of = dict(zip(clubs["club_id"], clubs["name"]))
    app["team"] = [sources.canonical_team(name_of.get(c, f"?{c}"))
                   for c in app["player_club_id"]]
    app["minutes_played"] = app["minutes_played"].clip(0, 90)
    return app


def snapshot(league: str) -> pd.DataFrame:
    m = pd.read_csv(ROOT / "data" / f"{league}_matches.csv", parse_dates=["date"])
    m["season"] = m["season"].astype(str)
    m["league"] = league
    return m


# --------------------------------------------------------------- copertura
def coverage_report(app: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league, comp in LEAGUES.items():
        m = snapshot(league)
        a = app[app["competition_id"] == comp]
        tg = set(zip(a["team"], a["date"]))
        ok = np.array([(h, d) in tg and (w, d) in tg
                       for h, w, d in zip(m["home_team"], m["away_team"], m["date"])])
        per_game = a.groupby(["team", "date"]).size()
        for season, g in m.groupby("season"):
            idx = m["season"] == season
            rows.append({"league": league, "season": season, "n_matches": int(idx.sum()),
                         "app_both_sides": int(ok[idx.to_numpy()].sum()),
                         "cov": round(float(ok[idx.to_numpy()].mean()), 4)})
        rows.append({"league": league, "season": "TOT", "n_matches": len(m),
                     "app_both_sides": int(ok.sum()), "cov": round(float(ok.mean()), 4),
                     "players_per_team_game_med": float(per_game.median()),
                     "first_app": str(a["date"].min().date()),
                     "last_app": str(a["date"].max().date())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------- feature
def team_features(app_league: pd.DataFrame, matches: pd.DataFrame,
                  valuations) -> dict:
    """{(team, date): dict di feature} calcolate SOLO su partite precedenti."""
    a = app_league.copy()
    a["season"] = pd.NA
    for code, (lo, hi) in player_scores.season_windows(matches).items():
        a.loc[a["date"].between(lo, hi), "season"] = code
    a = a.dropna(subset=["season"])

    out: dict = {}
    for (season, team), grp in a.groupby(["season", "team"], sort=False):
        dates = np.sort(grp["date"].unique())
        by_date = {d: g for d, g in grp.groupby("date")}
        for i, d in enumerate(dates):
            if i < MIN_GAMES:
                continue
            win = dates[max(0, i - K_RECENT):i]                 # solo < d
            allp = dates[:i]
            mins = {}
            for dd in win:
                for p, mn in zip(by_date[dd]["player_id"], by_date[dd]["minutes_played"]):
                    mins[p] = mins.get(p, 0.0) + float(mn)
            mins_all = {}
            for dd in allp:
                for p, mn in zip(by_date[dd]["player_id"], by_date[dd]["minutes_played"]):
                    mins_all[p] = mins_all.get(p, 0.0) + float(mn)
            recent = {}
            for dd in allp[-L_AVAIL:]:
                for p, mn in zip(by_date[dd]["player_id"], by_date[dd]["minutes_played"]):
                    recent[p] = recent.get(p, 0.0) + float(mn)

            top11 = sorted(mins, key=mins.get, reverse=True)[:11]
            when = pd.Timestamp(d)
            vals = np.array([player_scores._value_asof(valuations, int(p), when)
                             for p in top11])
            cov = float(np.isfinite(vals).mean())
            xi_val = float(np.nansum(vals)) if cov >= MIN_VAL_COV else np.nan
            conc = sum(mins[p] for p in top11) / (11.0 * 90.0 * len(win))

            core = sorted(mins_all, key=mins_all.get, reverse=True)[:11]
            cvals = np.array([player_scores._value_asof(valuations, int(p), when)
                              for p in core])
            w = np.array([min(1.0, recent.get(p, 0.0) / (90.0 * min(L_AVAIL, len(allp))))
                          for p in core])
            ok = np.isfinite(cvals)
            miss_val = (1.0 - float((cvals[ok] * w[ok]).sum() / cvals[ok].sum())
                        if ok.sum() >= 8 and cvals[ok].sum() > 0 else np.nan)
            miss_cnt = 1.0 - float(w.mean())

            out[(team, pd.Timestamp(d))] = {
                "xi_val": xi_val, "xi_conc": float(conc),
                "miss_val": miss_val, "miss_cnt": miss_cnt,
                "val_cov": cov, "n_prev": int(len(allp)),
            }
    return out


def build_features(rebuild: bool = False) -> pd.DataFrame:
    if CACHE.exists() and not rebuild:
        return pd.read_csv(CACHE, parse_dates=["date"])
    app = load_appearances()
    valuations = player_scores._valuations()
    frames = []
    for league, comp in LEAGUES.items():
        m = snapshot(league)
        feats = team_features(app[app["competition_id"] == comp], m, valuations)
        rows = []
        for r in m.itertuples():
            fh = feats.get((r.home_team, r.date))
            fa = feats.get((r.away_team, r.date))
            if fh is None or fa is None:
                continue
            rows.append({
                "league": league, "season": r.season, "date": r.date,
                "home_team": r.home_team, "away_team": r.away_team,
                "xi_val_h": fh["xi_val"], "xi_val_a": fa["xi_val"],
                "xi_conc_h": fh["xi_conc"], "xi_conc_a": fa["xi_conc"],
                "miss_val_h": fh["miss_val"], "miss_val_a": fa["miss_val"],
                "miss_cnt_h": fh["miss_cnt"], "miss_cnt_a": fa["miss_cnt"],
            })
        f = pd.DataFrame(rows)
        frames.append(f)
        print(f"  {league}: feature su {len(f)}/{len(m)} partite")
    out = pd.concat(frames, ignore_index=True)
    out["d_xival"] = np.log(out["xi_val_h"]) - np.log(out["xi_val_a"])
    out["d_missing"] = out["miss_val_h"] - out["miss_val_a"]
    out["d_misscnt"] = out["miss_cnt_h"] - out["miss_cnt_a"]
    out["d_conc"] = out["xi_conc_h"] - out["xi_conc_a"]
    CACHE.parent.mkdir(exist_ok=True)
    out.to_csv(CACHE, index=False)
    return out


# --------------------------------------------------------------- stima
def logit(p):
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def fit_offset_logit(X: np.ndarray, y: np.ndarray, off: np.ndarray):
    """MLE di y ~ Bernoulli(sigma(off + X beta)). Ritorna (beta, se)."""
    X = np.atleast_2d(X)
    if X.shape[0] != len(y):
        X = X.T

    def nll(b):
        z = off + X @ b
        return float(np.sum(np.logaddexp(0, z) - y * z))

    def grad(b):
        p = 1 / (1 + np.exp(-(off + X @ b)))
        return X.T @ (p - y)

    r = minimize(nll, np.zeros(X.shape[1]), jac=grad, method="BFGS")
    b = r.x
    p = 1 / (1 + np.exp(-(off + X @ b)))
    W = p * (1 - p)
    cov = np.linalg.pinv(X.T @ (X * W[:, None]))
    return b, np.sqrt(np.diag(cov))


def boot_beta(X, y, off, B=2000):
    X = np.atleast_2d(X)
    if X.shape[0] != len(y):
        X = X.T
    n = len(y)
    bs = []
    for _ in range(B):
        i = RNG.integers(0, n, n)
        try:
            b, _ = fit_offset_logit(X[i], y[i], off[i])
            bs.append(b)
        except Exception:
            pass
    bs = np.array(bs)
    return np.percentile(bs, [2.5, 97.5], axis=0)


def report_fit(name, X, y, off, cols, B=1500):
    b, se = fit_offset_logit(X, y, off)
    lo, hi = boot_beta(X, y, off, B=B)
    print(f"  {name}  (n={len(y)})")
    for j, c in enumerate(cols):
        z = b[j] / se[j] if se[j] > 0 else np.nan
        print(f"     {c:<12} beta={b[j]:+.4f}  se={se[j]:.4f}  z={z:+.2f}  "
              f"IC95%boot=[{lo[j]:+.4f},{hi[j]:+.4f}]"
              f"{'  *' if lo[j]*hi[j] > 0 else ''}")
    # guadagno di log-loss IN SAMPLE (ottimistico per costruzione)
    p0 = 1 / (1 + np.exp(-off))
    p1 = 1 / (1 + np.exp(-(off + np.atleast_2d(X).reshape(len(y), -1) @ b)))
    ll0 = -np.mean(y * np.log(p0) + (1 - y) * np.log(1 - p0))
    ll1 = -np.mean(y * np.log(p1) + (1 - y) * np.log(1 - p1))
    print(f"     log-loss binario: base {ll0:.4f} -> con feature {ll1:.4f} "
          f"(guadagno IN-SAMPLE {ll0 - ll1:+.4f})")
    return b, se, (lo, hi)


def zs(v):
    v = np.asarray(v, float)
    return (v - np.nanmean(v)) / np.nanstd(v)


# --------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()

    print("=" * 78)
    print("1) COPERTURA DEL DATO PRESENZE (appearances.csv.gz)")
    print("=" * 78)
    app = load_appearances()
    cov = coverage_report(app)
    print(cov[cov["season"] == "TOT"].to_string(index=False))
    print("\n  copertura per stagione (min sulle 9 stagioni, per lega):")
    for lg, g in cov[cov["season"] != "TOT"].groupby("league"):
        print(f"     {lg:<15} min={g['cov'].min():.4f}  media={g['cov'].mean():.4f}")

    print("\n" + "=" * 78)
    print("2) COSTRUZIONE FEATURE WALK-FORWARD (solo partite con data < T)")
    print("=" * 78)
    F = build_features(rebuild=args.rebuild)
    F["season"] = F["season"].astype(str)
    print(f"  partite con feature: {len(F)} (su 10260 = 3 leghe x 9 stagioni x 380)")
    print("  distribuzioni:")
    for c in ["d_xival", "d_missing", "d_misscnt", "d_conc"]:
        s = F[c].dropna()
        print(f"     {c:<10} n={len(s)}  media={s.mean():+.4f}  sd={s.std():.4f}  "
              f"p5={s.quantile(.05):+.3f}  p95={s.quantile(.95):+.3f}")
    m1 = F[["miss_val_h", "miss_val_a"]].stack()
    print(f"     quota di valore del nucleo NON sceso in campo nelle ultime "
          f"{L_AVAIL} partite: media {m1.mean():.3f} (sd {m1.std():.3f})")

    # ------------------------------------------------ campione MERCATO (9 st.)
    print("\n" + "=" * 78)
    print("3) TEST A — la feature batte la CHIUSURA? (9 stagioni, 3 leghe)")
    print("=" * 78)
    snaps = pd.concat([snapshot(l) for l in LEAGUES], ignore_index=True)
    d = snaps.merge(F, on=["league", "season", "date", "home_team", "away_team"],
                    how="inner")
    d = d.dropna(subset=["odds_home", "odds_draw", "odds_away",
                         "d_xival", "d_missing", "d_conc"])
    K = np.array([metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
                  for r in d.itertuples()])
    d["k_home"], d["k_draw"], d["k_away"] = K[:, 0], K[:, 1], K[:, 2]
    d["k_home_c"] = d["k_home"] / (1 - d["k_draw"])
    # lam,mu del mercato dal 1X2 devigato (rho=0) -> |lam-mu| = equilibrio
    lm = np.array([mi.implied_lambda_mu(r.k_home, r.k_draw, r.k_away)
                   for r in d.itertuples()])
    d["lam"], d["mu"] = lm[:, 0], lm[:, 1]
    d["abs_lm"] = (d["lam"] - d["mu"]).abs()
    d["half"] = d.groupby(["league", "season"])["date"].rank(pct=True)
    nd = d[d["result"] != "D"].copy()
    nd["y"] = (nd["result"] == "H").astype(float)
    print(f"  partite non pareggiate con quote e feature: {len(nd)}")

    cols = ["d_xival", "d_missing", "d_conc"]
    Xm = np.column_stack([zs(nd[c]) for c in cols])
    offm = logit(nd["k_home_c"].to_numpy())
    print("\n  [A1] tutte le partite — offset = chiusura devigata")
    report_fit("mercato", Xm, nd["y"].to_numpy(), offm, cols)

    print("\n  [A2] sanita': la feature e' correlata con quello che il mercato sa?")
    for c in cols:
        r = np.corrcoef(nd[c], offm)[0, 1]
        print(f"     corr({c}, logit chiusura condiz.) = {r:+.4f}")
    sv = nd.dropna(subset=["home_squad_value", "away_squad_value"])
    if len(sv):
        dsv = np.log(sv["home_squad_value"]) - np.log(sv["away_squad_value"])
        print(f"     corr(d_xival, log-rapporto VALORE ROSA stagionale) = "
              f"{np.corrcoef(sv['d_xival'], dsv)[0, 1]:+.4f}  (n={len(sv)})")

    # sottoinsiemi
    print("\n  [A3] sottoinsiemi (terzile basso di |lam-mu| = equilibrate; "
          "2a meta' = rank data > 0.5)")
    q33 = nd["abs_lm"].quantile(1 / 3)
    subs = {
        "equilibrate": nd["abs_lm"] <= q33,
        "2a meta'": nd["half"] > 0.5,
        "equilibrate & 2a meta'": (nd["abs_lm"] <= q33) & (nd["half"] > 0.5),
    }
    print(f"     soglia |lam-mu| terzile basso = {q33:.3f}")
    for name, msk in subs.items():
        s = nd[msk]
        X = np.column_stack([zs(s[c]) for c in cols])
        report_fit(name, X, s["y"].to_numpy(), logit(s["k_home_c"].to_numpy()),
                   cols, B=1000)

    # ------------------------------------------------ campione MODELLO (F93)
    print("\n" + "=" * 78)
    print("4) TEST B — la feature aggiunge al DIXON-COLES? (dataset Fase 93)")
    print("=" * 78)
    g = pd.read_csv(F93, parse_dates=["date"])
    g["season"] = g["season"].astype(str)
    g = g.merge(F, on=["league", "season", "date", "home_team", "away_team"],
                how="inner").dropna(subset=cols)
    g["abs_lm"] = d.set_index(["league", "season", "date", "home_team", "away_team"]) \
        .reindex(pd.MultiIndex.from_frame(
            g[["league", "season", "date", "home_team", "away_team"]]))["abs_lm"].to_numpy()
    g["half"] = g.groupby(["league", "season"])["date"].rank(pct=True)
    print(f"  partite Fase 93 con feature: {len(g)} (su 5083)")
    y = g["home_won"].to_numpy()
    Xg = np.column_stack([zs(g[c]) for c in cols])
    offdc = logit(g["m_home_c"].to_numpy())
    offmk = logit(g["k_home_c"].to_numpy())

    print("\n  [B1] offset = DIXON-COLES (m_home_c)")
    report_fit("DC", Xg, y, offdc, cols)
    print("\n  [B2] offset = mercato (k_home_c), stesso campione — controllo")
    report_fit("mercato", Xg, y, offmk, cols)

    print("\n  [B3] correlazione con il DEFICIT di discriminazione (Fase 93)")
    for c in cols:
        r = np.corrcoef(g[c], g["deficit"])[0, 1]
        # il deficit ha segno: il modello puo' sbagliare in entrambe le direzioni
        r2 = np.corrcoef(np.abs(g[c]), g["deficit"])[0, 1]
        print(f"     corr({c}, deficit)={r:+.4f}   corr(|{c}|, deficit)={r2:+.4f}")

    print("\n  [B4] sottoinsiemi sul deficit del DC")
    q33g = np.nanquantile(g["abs_lm"], 1 / 3)
    for name, msk in {
        "equilibrate": g["abs_lm"] <= q33g,
        "2a meta'": g["half"] > 0.5,
        "equilibrate & 2a meta'": (g["abs_lm"] <= q33g) & (g["half"] > 0.5),
    }.items():
        s = g[msk.fillna(False)]
        X = np.column_stack([zs(s[c]) for c in cols])
        report_fit(name, X, s["home_won"].to_numpy(),
                   logit(s["m_home_c"].to_numpy()), cols, B=1000)

    # ------------------------------------------------ ridondanza
    print("\n" + "=" * 78)
    print("5) TEST D — ridondanza col valore rosa e col logit del modello")
    print("=" * 78)
    gv = g.dropna(subset=["d_xival"]).copy()
    sv = snaps.set_index(["league", "season", "date", "home_team", "away_team"])
    key = pd.MultiIndex.from_frame(
        gv[["league", "season", "date", "home_team", "away_team"]])
    gv["hsv"] = sv.reindex(key)["home_squad_value"].to_numpy()
    gv["asv"] = sv.reindex(key)["away_squad_value"].to_numpy()
    gv = gv.dropna(subset=["hsv", "asv"])
    gv["d_sv"] = np.log(gv["hsv"]) - np.log(gv["asv"])
    print(f"  n={len(gv)}   corr(d_xival, d_sv)={np.corrcoef(gv['d_xival'], gv['d_sv'])[0,1]:+.4f}"
          f"   corr(d_xival, logit DC)={np.corrcoef(gv['d_xival'], logit(gv['m_home_c']))[0,1]:+.4f}")
    cols2 = ["d_xival", "d_missing", "d_conc", "d_sv"]
    X2 = np.column_stack([zs(gv[c]) for c in cols2])
    report_fit("DC + valore rosa", X2, gv["home_won"].to_numpy(),
               logit(gv["m_home_c"].to_numpy()), cols2)

    # ------------------------------------------------ fuori campione
    print("\n" + "=" * 78)
    print("6) TEST E — valore FUORI CAMPIONE (beta stimato sulle stagioni "
          "precedenti)")
    print("=" * 78)
    for label, dset, offcol in (("DC (Fase 93)", g, "m_home_c"),
                                ("mercato (9 stagioni)", nd, "k_home_c")):
        dd = dset.sort_values("date")
        seasons = sorted(dd["season"].unique())
        gains, n_used = [], 0
        for i, s in enumerate(seasons):
            if i < 2:
                continue
            tr = dd[dd["season"].isin(seasons[:i])]
            te = dd[dd["season"] == s]
            mu_, sd_ = tr[cols].mean(), tr[cols].std()
            Xtr = ((tr[cols] - mu_) / sd_).to_numpy()
            Xte = ((te[cols] - mu_) / sd_).to_numpy()
            ytr = (tr["home_won"] if "home_won" in tr else tr["y"]).to_numpy()
            yte = (te["home_won"] if "home_won" in te else te["y"]).to_numpy()
            b, _ = fit_offset_logit(Xtr, ytr, logit(tr[offcol].to_numpy()))
            o = logit(te[offcol].to_numpy())
            p0 = 1 / (1 + np.exp(-o))
            p1 = 1 / (1 + np.exp(-(o + Xte @ b)))
            l0 = -(yte * np.log(p0) + (1 - yte) * np.log(1 - p0))
            l1 = -(yte * np.log(p1) + (1 - yte) * np.log(1 - p1))
            gains.append(l0 - l1)
            n_used += len(te)
            print(f"     {label} stagione {s}: n={len(te):4d}  "
                  f"guadagno log-loss {np.mean(l0 - l1):+.5f}  beta={np.round(b,3)}")
        if gains:
            allg = np.concatenate(gains)
            bs = np.array([allg[RNG.integers(0, len(allg), len(allg))].mean()
                           for _ in range(3000)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            pos = sum(1 for x in gains if x.mean() > 0)
            print(f"     >>> {label}: guadagno medio {allg.mean():+.5f}  "
                  f"IC95% [{lo:+.5f},{hi:+.5f}]  stagioni positive {pos}/{len(gains)}"
                  f"  (n={n_used})")

    print("\nFATTO.")


if __name__ == "__main__":
    main()
