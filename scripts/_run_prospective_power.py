"""Fase 98 — POTENZA STATISTICA del test prospettico: quante partite servono?

Il test prospettico 2026-27 (Fase 78, APERTO) congela le previsioni prima del
kickoff e le scora dopo. Ma nessuno ha mai calcolato **quante partite servono
perche' il test concluda qualcosa**. Il gap modello-vs-mercato sull'1X2 vale
circa +0.0165 di log-loss (Serie A): e' un effetto piccolo su una variabile
per-partita molto rumorosa, quindi la domanda non e' retorica.

Metodo (tutto sui dati veri, walk-forward, nessun look-ahead):

1. per ogni partita si costruisce la differenza APPAIATA
       d_i = logloss_modello_i - logloss_riferimento_i
   con riferimento = mercato di chiusura devigato (1X2, O/U 2.5), oppure il
   motore market-implied (GG/NG, che il book non quota), oppure la baseline
   ex-ante (frequenze delle stagioni PRECEDENTI della stessa lega);
2. si misura la deviazione standard EMPIRICA di d_i e la sua struttura di
   correlazione (autocorrelazione lag-1 dentro la stagione, ICC per giornata e
   per stagione, bootstrap a cluster) -> effetto di disegno
       DEFF = (SE_cluster / SE_iid)^2,   sd_eff = sd(d) * sqrt(DEFF);
3. potenza di un test appaiato a due code al 5%:
       SE(n) = sd_eff / sqrt(n)
       MDE(n) = (z_0.975 + z_0.80) * SE(n) = 2.802 * SE(n)
       n* = ( (z_0.975 + z_0.80) * sd_eff / delta )^2
4. lo stesso per il mercato OUTRIGHT (campione di stagione), dove ogni
   stagione-lega da' UNA sola osservazione (log-loss a 20 esiti): si riusa il
   backtest della Fase 89 (24 stagioni-lega) e la baseline di persistenza LOO.

Uso:
  python scripts/_run_prospective_power.py
  python scripts/_run_prospective_power.py --leagues serie_a --seasons 2425 2526
  python scripts/_run_prospective_power.py --cache /path/cache.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import league_config              # noqa: E402
from src.data import loader                       # noqa: E402
from src.models import market_implied as mi       # noqa: E402
from scripts.backtest import run_backtest         # noqa: E402

LEAGUES = ("serie_a", "premier_league", "la_liga")
SEASONS = ("2021", "2122", "2223", "2324", "2425", "2526")
Z_ALPHA = norm.ppf(0.975)      # 1.9600 — test a DUE code al 5%
Z_POWER = norm.ppf(0.80)       # 0.8416 — potenza 80%
K_POWER = Z_ALPHA + Z_POWER    # 2.8016
RHO_DC = -0.06                 # rho della matrice DC usato dal motore (Fase 24)
EPS = 1e-12


# --------------------------------------------------------------------------- #
# 1. Dataset walk-forward
# --------------------------------------------------------------------------- #
def build_dataset(leagues, seasons) -> pd.DataFrame:
    """Backtest walk-forward (config ufficiale per-lega) + probabilita' di
    mercato. Una riga per partita con: probabilita' DC, mercato devigato,
    motore market-implied (lambda,mu invertiti dalle quote 1X2+O/U)."""
    frames = []
    for lg in leagues:
        cfg = league_config(lg)
        for S in seasons:
            d = run_backtest(lg, S, cfg["half_life_days"], shrinkage=cfg["shrinkage"],
                             shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
                             promoted_prior=(cfg["promoted_prior"],) * 2, verbose=False)
            d["league"] = lg
            frames.append(d)
            print(f"  backtest {lg:15} {S}: {len(d)} partite", flush=True)
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["league", "season", "date"]).reset_index(drop=True)
    df["matchday"] = df.groupby(["league", "season"]).cumcount() // 10 + 1

    # --- mercato 1X2 devigato (moltiplicativo, come metrics.devig_1x2) ------- #
    inv = np.column_stack([1.0 / df["odds_home"], 1.0 / df["odds_draw"],
                           1.0 / df["odds_away"]])
    k = inv / inv.sum(axis=1, keepdims=True)
    df["k_home"], df["k_draw"], df["k_away"] = k[:, 0], k[:, 1], k[:, 2]

    # --- mercato Over/Under 2.5 devigato ------------------------------------ #
    io = 1.0 / df["odds_over"]
    iu = 1.0 / df["odds_under"]
    df["k_over"] = io / (io + iu)

    # --- motore market-implied: lambda,mu dalle quote -> ogni mercato -------- #
    btts, mi_over = [], []
    for r in df.itertuples():
        if not np.isfinite(r.k_home) or not np.isfinite(r.k_over):
            btts.append(np.nan); mi_over.append(np.nan); continue
        lam, mu = mi.implied_lambda_mu(r.k_home, r.k_draw, r.k_away, r.k_over, rho=RHO_DC)
        m = mi.derive_markets(mi.score_matrix(lam, mu, RHO_DC))
        btts.append(m["btts"]); mi_over.append(m["over_2.5"])
    df["mi_btts"] = btts
    df["mi_over"] = mi_over
    return df


def add_baselines(df: pd.DataFrame, leagues) -> pd.DataFrame:
    """Baseline EX-ANTE: frequenze delle stagioni PRECEDENTI della stessa lega
    (nessun look-ahead; piu' onesta della baseline in-sample di compute_metrics,
    che usa le frequenze della stagione di test stessa)."""
    cols = {}
    for lg in leagues:
        allm = loader.load_league(lg)
        allm = allm.sort_values("date")
        for S in sorted(df.loc[df["league"] == lg, "season"].unique()):
            past = allm[allm["season"] < S]
            if past.empty:
                continue
            res = past["result"]
            b = (float((res == "H").mean()), float((res == "D").mean()), float((res == "A").mean()))
            tot = past["home_goals"] + past["away_goals"]
            bo = float((tot >= 3).mean())
            bg = float(((past["home_goals"] >= 1) & (past["away_goals"] >= 1)).mean())
            cols[(lg, S)] = (b[0], b[1], b[2], bo, bg)
    key = list(zip(df["league"], df["season"]))
    arr = np.array([cols.get(k, (np.nan,) * 5) for k in key], float)
    for i, c in enumerate(["b_home", "b_draw", "b_away", "b_over", "b_btts"]):
        df[c] = arr[:, i]
    return df


# --------------------------------------------------------------------------- #
# 2. Differenze appaiate per-partita
# --------------------------------------------------------------------------- #
def ll_multi(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    P = np.clip(P, EPS, 1.0)
    return -np.log(P[np.arange(len(y)), y])


def ll_bin(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def paired_series(df: pd.DataFrame) -> dict:
    """Dizionario {nome confronto: DataFrame(league, season, matchday, d)}."""
    idx = {"H": 0, "D": 1, "A": 2}
    y3 = df["result"].map(idx).to_numpy()
    yo = df["is_over"].to_numpy(float)
    yb = df["is_btts"].to_numpy(float)

    m3 = df[["m_home", "m_draw", "m_away"]].to_numpy()
    k3 = df[["k_home", "k_draw", "k_away"]].to_numpy()
    b3 = df[["b_home", "b_draw", "b_away"]].to_numpy()

    out = {}
    def put(name, d, mask):
        m = mask & np.isfinite(d)
        out[name] = pd.DataFrame({"league": df["league"][m].to_numpy(),
                                  "season": df["season"][m].to_numpy(),
                                  "matchday": df["matchday"][m].to_numpy(),
                                  "d": d[m]})

    fin3 = np.isfinite(k3).all(axis=1)
    finb = np.isfinite(b3).all(axis=1)
    fino = np.isfinite(df["k_over"].to_numpy())
    finmi = np.isfinite(df["mi_btts"].to_numpy())

    put("1X2 : DC vs mercato",   ll_multi(m3, y3) - ll_multi(k3, y3), fin3)
    put("1X2 : DC vs baseline",  ll_multi(m3, y3) - ll_multi(b3, y3), finb)
    put("1X2 : mercato vs baseline", ll_multi(k3, y3) - ll_multi(b3, y3), fin3 & finb)
    put("O/U 2.5 : DC vs mercato",
        ll_bin(df["m_over"], yo) - ll_bin(df["k_over"], yo), fino)
    put("O/U 2.5 : DC vs baseline",
        ll_bin(df["m_over"], yo) - ll_bin(df["b_over"], yo), finb)
    put("GG/NG : DC vs market-implied",
        ll_bin(df["m_btts"], yb) - ll_bin(df["mi_btts"], yb), finmi)
    put("GG/NG : DC vs baseline",
        ll_bin(df["m_btts"], yb) - ll_bin(df["b_btts"], yb), finb)
    put("GG/NG : market-implied vs baseline",
        ll_bin(df["mi_btts"], yb) - ll_bin(df["b_btts"], yb), finmi & finb)
    return out


# --------------------------------------------------------------------------- #
# 3. Struttura di correlazione ed effetto di disegno
# --------------------------------------------------------------------------- #
def acf1(d: pd.DataFrame) -> float:
    """Autocorrelazione lag-1 di d, dentro ogni (lega, stagione)."""
    num = den = 0.0
    for _, g in d.groupby(["league", "season"], sort=False):
        x = g["d"].to_numpy()
        if len(x) < 3:
            continue
        x = x - x.mean()
        num += float(np.sum(x[:-1] * x[1:]))
        den += float(np.sum(x * x))
    return num / den if den > 0 else np.nan


def icc(d: pd.DataFrame, keys) -> float:
    """ICC one-way (varianza fra cluster / varianza totale), stimatore ANOVA."""
    g = d.groupby(keys, sort=False)["d"]
    n_i = g.size().to_numpy(float)
    means = g.mean().to_numpy()
    k = len(n_i)
    N = n_i.sum()
    if k < 2:
        return np.nan
    grand = d["d"].mean()
    ssb = float(np.sum(n_i * (means - grand) ** 2))
    ssw = float(np.sum((d["d"].to_numpy() - d.groupby(keys, sort=False)["d"].transform("mean").to_numpy()) ** 2))
    msb = ssb / (k - 1)
    msw = ssw / (N - k) if N > k else np.nan
    n0 = (N - float(np.sum(n_i ** 2)) / N) / (k - 1)
    v = (msb - msw) / n0
    return float(v / (v + msw)) if np.isfinite(msw) and (v + msw) > 0 else np.nan


def cluster_se(d: pd.DataFrame, keys, B=2000, seed=0) -> float:
    """SE della media di d via bootstrap a CLUSTER (ricampiona interi cluster)."""
    rng = np.random.default_rng(seed)
    groups = [g["d"].to_numpy() for _, g in d.groupby(keys, sort=False)]
    k = len(groups)
    if k < 3:
        return np.nan
    means = np.empty(B)
    sizes = np.array([len(g) for g in groups], float)
    sums = np.array([g.sum() for g in groups], float)
    for b in range(B):
        pick = rng.integers(0, k, k)
        means[b] = sums[pick].sum() / sizes[pick].sum()
    return float(means.std(ddof=1))


def summarize(name: str, d: pd.DataFrame) -> dict:
    x = d["d"].to_numpy()
    n = len(x)
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    se_iid = sd / np.sqrt(n)
    se_md = cluster_se(d, ["league", "season", "matchday"])
    se_se = cluster_se(d, ["league", "season"])
    deff_md = (se_md / se_iid) ** 2 if np.isfinite(se_md) else np.nan
    deff_se = (se_se / se_iid) ** 2 if np.isfinite(se_se) else np.nan
    deff = float(np.nanmax([1.0, deff_md, deff_se]))
    return dict(name=name, n=n, mean=mean, sd=sd, se_iid=se_iid,
                t_iid=mean / se_iid, acf1=acf1(d),
                icc_matchday=icc(d, ["league", "season", "matchday"]),
                icc_season=icc(d, ["league", "season"]),
                se_cluster_matchday=se_md, se_cluster_season=se_se,
                deff_matchday=deff_md, deff_season=deff_se, deff_used=deff,
                sd_eff=sd * np.sqrt(deff))


# --------------------------------------------------------------------------- #
# 4. Potenza
# --------------------------------------------------------------------------- #
def n_star(sd_eff: float, delta: float) -> float:
    return float((K_POWER * sd_eff / abs(delta)) ** 2)


def power_at(n: int, sd_eff: float, delta: float) -> float:
    """Potenza di un t-test appaiato a due code (approssimazione normale)."""
    ncp = abs(delta) * np.sqrt(n) / sd_eff
    return float(norm.cdf(ncp - Z_ALPHA) + norm.cdf(-ncp - Z_ALPHA))


def power_table(s: dict, ns=(30, 100, 380, 1140, 2280)) -> pd.DataFrame:
    rows = []
    for n in ns:
        se = s["sd_eff"] / np.sqrt(n)
        rows.append(dict(n=n, se=se, mde=K_POWER * se,
                         power=power_at(n, s["sd_eff"], s["mean"])))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 5. Outright (campione di stagione): 1 osservazione per stagione-lega
# --------------------------------------------------------------------------- #
def outright_power() -> dict | None:
    p = Path("experiments/fase89_season_champion.json")
    if not p.exists():
        return None
    from scripts._run_fase89_season_champion import _persistence_loo  # noqa: E402
    df = pd.DataFrame(json.loads(p.read_text())["backtest"])
    pers, best = _persistence_loo(df, np.arange(0.5, 4.01, 0.1), (0.0, 0.5, 1.0))
    d = df["logloss"].to_numpy() - pers          # modello - baseline (neg = meglio)
    n = len(d)
    mean, sd = float(d.mean()), float(d.std(ddof=1))
    se = sd / np.sqrt(n)
    rng = np.random.default_rng(0)
    bs = np.array([d[rng.integers(0, n, n)].mean() for _ in range(20000)])
    return dict(n=n, mean=mean, sd=sd, se=se, t=mean / se,
                ci=(float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))),
                n_star=n_star(sd, mean), best_beta_w2=list(best),
                ll_model=float(df["logloss"].mean()), ll_base=float(pers.mean()),
                power_by_n={k: power_at(k, sd, mean) for k in (3, 4, 5, 6, 10, 15, 24)},
                # sensibilita': se il vantaggio vero fosse meta'/un quarto
                n_star_half=n_star(sd, mean / 2), n_star_quarter=n_star(sd, mean / 4))


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leagues", nargs="*", default=list(LEAGUES))
    ap.add_argument("--seasons", nargs="*", default=list(SEASONS))
    ap.add_argument("--cache", default=None, help="CSV di cache del dataset walk-forward")
    ap.add_argument("--target", type=float, default=0.0165,
                    help="effetto di riferimento sull'1X2 (gap storico Serie A)")
    args = ap.parse_args(argv)

    cache = Path(args.cache) if args.cache else None
    if cache and cache.exists():
        print(f"Dataset da cache: {cache}")
        df = pd.read_csv(cache)
    else:
        print("Backtest walk-forward (puo' richiedere minuti)...")
        df = build_dataset(args.leagues, args.seasons)
        df = add_baselines(df, args.leagues)
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache, index=False)
    df["season"] = df["season"].astype(str)

    print(f"\nPartite totali: {len(df)}  "
          f"({df['league'].nunique()} leghe x {df['season'].nunique()} stagioni)")

    series = paired_series(df)
    summaries = {k: summarize(k, v) for k, v in series.items()}

    print("\n" + "=" * 100)
    print("A. DIFFERENZE APPAIATE PER-PARTITA  (d = logloss_modello - logloss_riferimento)")
    print("=" * 100)
    print(f"{'confronto':38} {'n':>5} {'media d':>10} {'sd(d)':>8} {'SE iid':>8} "
          f"{'t':>7} {'acf1':>7} {'ICC-gio':>8} {'ICC-sta':>8} {'DEFF':>6}")
    for s in summaries.values():
        print(f"{s['name']:38} {s['n']:5d} {s['mean']:+10.4f} {s['sd']:8.4f} "
              f"{s['se_iid']:8.4f} {s['t_iid']:+7.2f} {s['acf1']:+7.3f} "
              f"{s['icc_matchday']:+8.4f} {s['icc_season']:+8.4f} {s['deff_used']:6.2f}")
    print("\n(d>0 = il riferimento e' migliore. DEFF = (SE bootstrap a cluster / SE iid)^2,")
    print(" preso come max fra cluster-giornata e cluster-stagione, mai sotto 1.)")

    print("\n" + "-" * 100)
    print("A-bis. CONTROLLO: gap per lega (deve riprodurre i numeri gia' noti, es. Serie A ~ +0.0165)")
    print("-" * 100)
    print(f"{'confronto':38} " + " ".join(f"{lg:>16}" for lg in args.leagues))
    for name, d in series.items():
        cells = []
        for lg in args.leagues:
            x = d.loc[d["league"] == lg, "d"].to_numpy()
            cells.append(f"{x.mean():+9.4f}({len(x):4d})" if len(x) else " " * 16)
        print(f"{name:38} " + " ".join(f"{c:>16}" for c in cells))

    print("\n" + "=" * 100)
    print("B. CAMPIONE -> ERRORE STANDARD -> COSA SI PUO' CONCLUDERE")
    print("=" * 100)
    for s in summaries.values():
        t = power_table(s)
        print(f"\n{s['name']}   [gap osservato {s['mean']:+.4f}, sd_eff {s['sd_eff']:.4f}]")
        print(f"  {'n partite':>10} {'SE':>9} {'MDE 80%':>10} {'potenza sul gap':>16}  interpretazione")
        for _, r in t.iterrows():
            n = int(r['n'])
            lab = {30: "1 giornata (3 leghe)", 100: "~3 giornate", 380: "1 stagione (1 lega)",
                   1140: "1 stagione x 3 leghe", 2280: "2 stagioni x 3 leghe"}[n]
            print(f"  {n:10d} {r['se']:9.4f} {r['mde']:10.4f} {r['power']:16.1%}  {lab}")
        ns = n_star(s["sd_eff"], s["mean"])
        print(f"  n* per rilevare il gap osservato ({s['mean']:+.4f}) con potenza 80%: "
              f"{ns:,.0f} partite  = {ns/380:.1f} stagioni-lega = {ns/30:.0f} giornate-3-leghe")

    s1 = summaries["1X2 : DC vs mercato"]
    nt = n_star(s1["sd_eff"], args.target)
    print(f"\n  [1X2 vs mercato] n* per l'effetto di riferimento {args.target:+.4f}: "
          f"{nt:,.0f} partite = {nt/380:.1f} stagioni-lega = {nt/1140:.1f} stagioni-3-leghe")

    print("\n" + "=" * 100)
    print("C. DISEGNI ALTERNATIVI")
    print("=" * 100)
    for s in summaries.values():
        ns = n_star(s["sd_eff"], s["mean"])
        print(f"  {s['name']:38} -> {ns/30:8.0f} giornate-3-leghe | "
              f"{ns/1140:6.1f} stagioni-3-leghe | {ns:,.0f} partite")
    print("\n  Scorare 'per stagione intera' (una media per stagione-lega) NON aumenta")
    print("  l'informazione: la media di stagione ha SE = sd_eff/sqrt(380) e servono")
    print("  comunque n*/380 stagioni-lega. Aggregare puo' solo PERDERE potenza")
    print("  (butta via la struttura appaiata dentro la stagione).")
    for s in summaries.values():
        ns = n_star(s["sd_eff"], s["mean"])
        print(f"  {s['name']:38} -> {ns/380:6.1f} stagioni-lega scorate per intero")

    print("\n" + "=" * 100)
    print("D. MERCATO OUTRIGHT (campione di stagione): 1 osservazione per stagione-lega")
    print("=" * 100)
    o = outright_power()
    if o is None:
        print("  experiments/fase89_season_champion.json assente: sezione saltata.")
    else:
        print(f"  osservazioni (stagione-lega): {o['n']}")
        print(f"  log-loss modello MC {o['ll_model']:.4f} vs baseline persistenza LOO "
              f"{o['ll_base']:.4f}  (beta,w2 = {o['best_beta_w2']})")
        print(f"  d = modello - baseline: media {o['mean']:+.4f}, sd {o['sd']:.4f}, "
              f"SE {o['se']:.4f}, t {o['t']:+.2f}")
        print(f"  IC95% bootstrap sulla media: [{o['ci'][0]:+.4f}, {o['ci'][1]:+.4f}]")
        print(f"  n* per potenza 80% sul vantaggio osservato: {o['n_star']:.1f} stagioni-lega")
        print(f"  n* se il vantaggio vero fosse la META': {o['n_star_half']:.0f}; "
              f"un QUARTO: {o['n_star_quarter']:.0f}")
        print("  potenza per numero di stagioni-lega osservate in UNA stagione:")
        for k, v in o["power_by_n"].items():
            print(f"    {k:2d} leghe -> potenza {v:5.1%}")

    print("\n" + "=" * 100)
    print("E. NOTE E LIMITI")
    print("=" * 100)
    print("  - il gap 'osservato' e' quello STORICO (walk-forward, chiusura devigata")
    print("    moltiplicativa); il test prospettico vero potrebbe avere un effetto diverso.")
    print("  - la potenza e' calcolata sull'ipotesi che il gap resti costante; e' una")
    print("    stima OTTIMISTICA se il modello degrada o il mercato migliora.")
    print("  - la baseline usata qui e' EX-ANTE (stagioni precedenti), quindi leggermente")
    print("    piu' debole della baseline in-sample di compute_metrics.")
    print("  - GG/NG non ha quote nei dati: il riferimento e' il motore market-implied,")
    print("    non un mercato reale.")
    print("  - l'outright ha n piccolo e distribuzione molto asimmetrica: il t-test")
    print("    normale e' indicativo, il bootstrap e' il riferimento.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
