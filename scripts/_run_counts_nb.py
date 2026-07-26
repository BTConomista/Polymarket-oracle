"""Fase 98 — Binomiale negativa per i conteggi FUORI dalla matrice (corner, cartellini).

Perche'. La Fase 96 ha derivato i mercati Over/Under di corner e cartellini con una
POISSON attorno al totale atteso, ma ha misurato che quei conteggi sono SOVRA-dispersi
(indice var/media 1.12-1.48). La Poisson e' quindi la forma sbagliata: a parita' di
media mette troppa massa al centro e troppo poca sulle code. La binomiale negativa (NB)
e' la forma naturale per un conteggio sovra-disperso — la stessa distribuzione che la
Fase 27 aveva BOCCIATO sui GOL, dove il segno della dispersione e' opposto
(sotto-dispersione, theta>1 della double-Poisson). Qui il segno e' quello giusto,
quindi il tentativo ha senso strutturale.

Cosa fa (tutto walk-forward, nessun look-ahead):
 1. riusa la struttura di scripts/_run_outside_matrix.py per il TOTALE ATTESO
    (att/dif per squadra, fattori casa/ospite con vincolo hadv+aadv=2 implicito nella
    costruzione, emivita 365g, shrinkage 1.5);
 2. stima il parametro di dispersione r della NB SOLO SUL PASSATO. Metodo dichiarato:
    **MLE di r a medie fissate** (le medie sono quelle del modello di conteggio), con
    il metodo dei momenti come valore iniziale e come controllo (entrambi riportati).
    I residui usati sono OUT-OF-SAMPLE quando disponibili (le stagioni di test gia'
    passate); per la primissima stagione di test, che non ne ha, si ripiega sui residui
    in-sample del train (dichiarato nella tabella con la colonna `fonte`);
 3. confronta Poisson vs NB sui mercati Over/Under (corner 8.5/9.5/10.5/11.5;
    cartellini 2.5/3.5/4.5) con log-loss binario OOS, scarto di calibrazione
    (P media - frequenza reale) e Brier;
 4. ripete il confronto per LEGA (le tre leghe hanno dispersione diversa);
 5. CI bootstrap APPAIATO sulla differenza per-partita di log-loss (Poisson - NB),
    5000 ricampionamenti, per dire se il guadagno e' conclusivo;
 6. incrocia il guadagno con la sovra-dispersione stimata (il guadagno e' maggiore
    dove la sovra-dispersione e' maggiore?).

Nota di coerenza con la Fase 96: il modello sui "cartellini" usa i GIALLI (HY+AY),
esattamente come `walk_forward(kind="cards")` della Fase 96, per essere confrontabile;
la colonna `cards` con i rossi pesati x2 e' usata solo nella tabella di struttura.

NON registra run (diagnostico). Uso: python scripts/_run_counts_nb.py
"""
from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import nbinom, poisson

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RAW_SA = "data/football_data_raw/serie_a_*.csv"
BUNDLES = {
    "premier_league": "files/football_data_premier_league_bundle.json",
    "la_liga": "files/football_data_la_liga_bundle.json",
}
HALF_LIFE = 365.0     # stessa memoria del DC ufficiale
SHRINK = 1.5
R_MAX = 1e6           # r -> infinito equivale alla Poisson
N_BOOT = 5000
SEED = 12345

MARKETS = {
    "corners": [8.5, 9.5, 10.5, 11.5],
    "cards": [2.5, 3.5, 4.5],
}


# --------------------------------------------------------------------------- dati
def _season_of(name: str) -> str:
    return name.split("_")[-1].replace(".csv", "")


def load_raw() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(RAW_SA)):
        try:
            d = pd.read_csv(f, encoding="latin-1")
        except Exception:
            d = pd.read_csv(f)
        d["league"] = "serie_a"
        d["season"] = _season_of(f)
        frames.append(d)
    for lg, path in BUNDLES.items():
        for k, v in json.load(open(path)).items():
            if not isinstance(v, str):
                continue
            d = pd.read_csv(io.StringIO(v))
            d.columns = [c.lstrip("﻿") for c in d.columns]
            d["league"] = lg
            d["season"] = _season_of(k)
            frames.append(d)
    keep = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HC", "AC",
            "HY", "AY", "HR", "AR", "league", "season"]
    out = []
    for d in frames:
        cols = [c for c in keep if c in d.columns]
        out.append(d[cols].copy())
    df = pd.concat(out, ignore_index=True)
    df["date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "HC", "AC", "HY", "AY"]).sort_values("date")
    df["corners"] = df["HC"] + df["AC"]
    df["cards_y"] = df["HY"] + df["AY"]
    df["cards"] = df["HY"] + df["AY"] + 2 * df["HR"].fillna(0) + 2 * df["AR"].fillna(0)
    df["goals"] = df["FTHG"] + df["FTAG"]
    return df.reset_index(drop=True)


# ------------------------------------------------------------------- modello medie
def fit_counts(train: pd.DataFrame, col_h: str, col_a: str, as_of: pd.Timestamp):
    """Identica alla Fase 96: forze attacco/difesa sul conteggio, forma chiusa pesata."""
    w = 0.5 ** ((as_of - train["date"]).dt.days / HALF_LIFE)
    tot = (train[col_h] * w).sum() + (train[col_a] * w).sum()
    n = 2 * w.sum()
    base = tot / n if n else 1.0
    hadv = ((train[col_h] * w).sum() / w.sum()) / max(base, 1e-9)
    aadv = ((train[col_a] * w).sum() / w.sum()) / max(base, 1e-9)
    att, dfn = {}, {}
    teams = set(train["HomeTeam"]) | set(train["AwayTeam"])
    for t in teams:
        mh, ma = train["HomeTeam"] == t, train["AwayTeam"] == t
        wt = w[mh].sum() + w[ma].sum()
        prod = (train.loc[mh, col_h] * w[mh]).sum() + (train.loc[ma, col_a] * w[ma]).sum()
        conc = (train.loc[mh, col_a] * w[mh]).sum() + (train.loc[ma, col_h] * w[ma]).sum()
        k = SHRINK * 10.0
        att[t] = (prod + k * base) / (wt + k) / max(base, 1e-9)
        dfn[t] = (conc + k * base) / (wt + k) / max(base, 1e-9)
    return att, dfn, base, hadv, aadv


def _predict(rows: pd.DataFrame, att, dfn, base, hadv, aadv) -> np.ndarray:
    ah = rows["HomeTeam"].map(att).to_numpy(dtype=float)
    aa = rows["AwayTeam"].map(att).to_numpy(dtype=float)
    dh = rows["HomeTeam"].map(dfn).to_numpy(dtype=float)
    da = rows["AwayTeam"].map(dfn).to_numpy(dtype=float)
    return base * hadv * ah * da + base * aadv * aa * dh


# ------------------------------------------------------------------ dispersione NB
def r_mom(y: np.ndarray, m: np.ndarray) -> float:
    """Metodo dei momenti: E[(y-m)^2] = m + m^2/r  ->  r = sum(m^2) / sum((y-m)^2 - m)."""
    num = float(np.sum(m ** 2))
    den = float(np.sum((y - m) ** 2 - m))
    if den <= 0:
        return R_MAX
    return float(min(max(num / den, 1e-3), R_MAX))


def r_mle(y: np.ndarray, m: np.ndarray, start: float) -> float:
    """MLE del solo r a medie fissate: max_r  sum_i log NB(y_i; r, p_i=r/(r+m_i))."""
    def nll(log_r: float) -> float:
        r = float(np.exp(log_r))
        p = r / (r + m)
        return float(-np.sum(nbinom.logpmf(y, r, p)))

    lo, hi = np.log(1e-2), np.log(R_MAX)
    x0 = float(np.clip(np.log(start), lo + 1e-6, hi - 1e-6))
    res = minimize_scalar(nll, bracket=None, bounds=(lo, hi), method="bounded",
                          options={"xatol": 1e-4})
    best = res.x if res.success else x0
    return float(min(np.exp(best), R_MAX))


def p_over_pois(m: np.ndarray, line: float) -> np.ndarray:
    return 1.0 - poisson.cdf(int(np.floor(line)), m)


def p_over_nb(m: np.ndarray, line: float, r) -> np.ndarray:
    p = r / (r + m)
    return 1.0 - nbinom.cdf(int(np.floor(line)), r, p)


# ------------------------------------------------------------------- walk-forward
def build_predictions(df: pd.DataFrame, kind: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Predizioni OOS per stagione + stima walk-forward di r (solo passato).

    Ritorna (predizioni con colonne exp/real/r_nb, tabella diagnostica delle stime di r).
    """
    ch, ca = ("HC", "AC") if kind == "corners" else ("HY", "AY")
    pred_frames, diag = [], []
    for lg, g in df.groupby("league"):
        seasons = sorted(g["season"].unique())
        done: list[pd.DataFrame] = []          # stagioni di test gia' predette (OOS)
        for s in seasons[2:]:
            train = g[g["season"] < s]
            test = g[g["season"] == s]
            if len(train) < 400 or test.empty:
                continue
            as_of = test["date"].min()
            att, dfn, base, hadv, aadv = fit_counts(train, ch, ca, as_of)

            # --- stima di r SOLO sul passato ---
            if done:
                past = pd.concat(done, ignore_index=True)
                y_p, m_p, src = past["real"].to_numpy(float), past["exp"].to_numpy(float), "OOS"
            else:
                m_in = _predict(train, att, dfn, base, hadv, aadv)
                y_in = (train[ch] + train[ca]).to_numpy(float)
                ok = np.isfinite(m_in)
                y_p, m_p, src = y_in[ok], m_in[ok], "in-sample"
            rm = r_mom(y_p, m_p)
            rl = r_mle(y_p, m_p, rm)
            diag.append({"league": lg, "season": s, "kind": kind, "n_fit": len(y_p),
                         "fonte": src, "r_mom": rm, "r_mle": rl,
                         "disp_at_mean": 1.0 + float(np.mean(m_p)) / rl})

            m_te = _predict(test, att, dfn, base, hadv, aadv)
            ok = np.isfinite(m_te)
            rows = pd.DataFrame({
                "league": lg, "season": s,
                "exp": m_te[ok],
                "real": (test[ch] + test[ca]).to_numpy(float)[ok],
                "base": 2 * base,
                "r_nb": rl,
            })
            pred_frames.append(rows)
            done.append(rows[["exp", "real"]])
    return (pd.concat(pred_frames, ignore_index=True),
            pd.DataFrame(diag))


# ----------------------------------------------------------------------- metriche
def _ll(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def paired_boot(diff: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    """CI bootstrap appaiato sulla media della differenza per-partita."""
    n = len(diff)
    idx = rng.integers(0, n, size=(N_BOOT, n))
    means = diff[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi), float((means > 0).mean())


def compare(pred: pd.DataFrame, lines: list[float], rng: np.random.Generator,
            label: str) -> list[dict]:
    out = []
    m = pred["exp"].to_numpy(float)
    r = pred["r_nb"].to_numpy(float)
    for L in lines:
        y = (pred["real"].to_numpy(float) > L).astype(float)
        pp = p_over_pois(m, L)
        pn = p_over_nb(m, L, r)
        ll_p, ll_n = _ll(pp, y), _ll(pn, y)
        d = ll_p - ll_n                       # >0 = NB migliore
        lo, hi, sh = paired_boot(d, rng)
        out.append({
            "gruppo": label, "linea": L, "n": len(y), "freq": float(y.mean()),
            "P_pois": float(pp.mean()), "P_nb": float(pn.mean()),
            "gap_pois": float(pp.mean() - y.mean()), "gap_nb": float(pn.mean() - y.mean()),
            "ll_pois": float(ll_p.mean()), "ll_nb": float(ll_n.mean()),
            "d_ll": float(d.mean()), "lo": lo, "hi": hi, "share_pos": sh,
            "brier_pois": float(np.mean((pp - y) ** 2)),
            "brier_nb": float(np.mean((pn - y) ** 2)),
        })
    return out


# ------------------------------------------------------------------------- output
def structure(df: pd.DataFrame) -> None:
    print("\n=== 0. SOVRA-DISPERSIONE MARGINALE dei totali (per lega) ===")
    print(f"{'lega':<16}{'n':>6}{'corner mu':>11}{'var/mu':>9}"
          f"{'gialli mu':>11}{'var/mu':>9}{'cart.(+R) var/mu':>18}")
    for lg, g in df.groupby("league"):
        c, k, kk = g["corners"], g["cards_y"], g["cards"]
        print(f"{lg:<16}{len(g):>6}{c.mean():>11.2f}{c.var()/c.mean():>9.3f}"
              f"{k.mean():>11.2f}{k.var()/k.mean():>9.3f}{kk.var()/kk.mean():>18.3f}")
    print("  (marginale = include anche la varianza fra partite dovuta alle squadre;")
    print("   la dispersione CONDIZIONATA al totale atteso e' quella che serve alla NB.)")


def run_market(df: pd.DataFrame, kind: str, rng: np.random.Generator) -> pd.DataFrame:
    name = "CORNER" if kind == "corners" else "CARTELLINI (gialli HY+AY, come F96)"
    print(f"\n{'='*78}\n=== {name} ===\n{'='*78}")
    pred, diag = build_predictions(df, kind)
    print(f"  n={len(pred)} partite OOS | MAE {np.abs(pred['exp']-pred['real']).mean():.3f} "
          f"vs baseline {np.abs(pred['base']-pred['real']).mean():.3f}")

    print("\n--- stima walk-forward del parametro NB (solo passato) ---")
    def _fmt(v: float) -> str:
        return "  ~inf(P)" if v >= 0.99 * R_MAX else f"{v:>8.2f}"

    print(f"{'lega':<16}{'stag.':>7}{'fonte':>11}{'n_fit':>7}{'r_MoM':>10}{'r_MLE':>10}"
          f"{'var/mu implicito':>19}")
    for _, d in diag.iterrows():
        print(f"{d['league']:<16}{d['season']:>7}{d['fonte']:>11}{d['n_fit']:>7}"
              f"  {_fmt(d['r_mom'])}  {_fmt(d['r_mle'])}{d['disp_at_mean']:>19.3f}")
    print("  r piccolo = molta sovra-dispersione; r -> inf = Poisson "
          f"(cap {R_MAX:.0e}). var/mu implicito = 1 + mu/r alla media del campione.")

    print("\n--- dispersione CONDIZIONATA sui residui OOS (var/mu = sum((y-m)^2)/sum(m)) "
          "e BIAS della media (controllo anti-bug) ---")
    print(f"  {'lega':<16}{'var/mu cond.':>14}{'media attesa':>14}{'media reale':>13}"
          f"{'bias':>9}")
    disp_rows = []
    for lg, g in list(pred.groupby("league")) + [("TUTTE", pred)]:
        dc = float(((g["real"] - g["exp"]) ** 2).sum() / g["exp"].sum())
        disp_rows.append({"kind": kind, "league": lg, "disp_cond": dc})
        print(f"  {lg:<16}{dc:>14.3f}{g['exp'].mean():>14.3f}{g['real'].mean():>13.3f}"
              f"{g['exp'].mean()-g['real'].mean():>+9.3f}")
    print("  (il bias della media NON e' costante ne' di segno unico fra leghe/stagioni:")
    print("   e' la deriva temporale dei conteggi vista dal walk-forward, non un errore")
    print("   di normalizzazione. La NB non tocca la media: se la media e' storta, la NB")
    print("   puo' peggiorare le linee dal lato sbagliato.)")
    disp_tab = pd.DataFrame(disp_rows)

    rows = compare(pred, MARKETS[kind], rng, "TUTTE")
    for lg, g in pred.groupby("league"):
        rows += compare(g, MARKETS[kind], rng, lg)
    res = pd.DataFrame(rows)
    res["kind"] = kind

    print("\n--- Poisson vs NB sui mercati Over/Under (OOS) ---")
    print(f"{'gruppo':<16}{'linea':>7}{'n':>6}{'freq':>7}{'P_pois':>8}{'P_nb':>7}"
          f"{'gapP':>8}{'gapNB':>8}{'LL_pois':>9}{'LL_nb':>9}{'d_LL':>9}"
          f"{'IC95 appaiato':>22}{'%>0':>7}{'BrP':>8}{'BrNB':>8}")
    for _, x in res.iterrows():
        print(f"{x['gruppo']:<16}{('O'+str(x['linea'])):>7}{int(x['n']):>6}"
              f"{x['freq']:>7.3f}{x['P_pois']:>8.3f}{x['P_nb']:>7.3f}"
              f"{x['gap_pois']:>+8.3f}{x['gap_nb']:>+8.3f}"
              f"{x['ll_pois']:>9.4f}{x['ll_nb']:>9.4f}{x['d_ll']:>+9.5f}"
              f"{('['+format(x['lo'],'+.5f')+','+format(x['hi'],'+.5f')+']'):>22}"
              f"{x['share_pos']:>7.2f}{x['brier_pois']:>8.4f}{x['brier_nb']:>8.4f}")
    print("  d_LL = LL_poisson - LL_nb: POSITIVO = la NB e' migliore. "
          "IC95 tutto sopra 0 = conclusivo.")

    # aggregato su tutte le linee del mercato (differenza media per-partita-linea)
    m = pred["exp"].to_numpy(float); r = pred["r_nb"].to_numpy(float)
    y_all, dp, dn = [], [], []
    for L in MARKETS[kind]:
        y = (pred["real"].to_numpy(float) > L).astype(float)
        pp = p_over_pois(m, L)
        pn = p_over_nb(m, L, r)
        y_all.append(y); dp.append(_ll(pp, y)); dn.append(_ll(pn, y))
    d_match = (np.mean(dp, axis=0) - np.mean(dn, axis=0))   # per PARTITA, media sulle linee
    lo, hi, sh = paired_boot(d_match, rng)
    ll_pois_mean = float(np.mean(dp))
    print(f"\n  AGGREGATO {kind}: LL Poisson {ll_pois_mean:.4f} -> LL NB "
          f"{float(np.mean(dn)):.4f} ({100*d_match.mean()/ll_pois_mean:+.2f}% relativo)")
    print(f"  d_LL medio per partita (media sulle linee) "
          f"{d_match.mean():+.5f}  IC95 [{lo:+.5f}, {hi:+.5f}]  %boot>0 {sh:.2f}  -> "
          f"{'NB MIGLIORE (conclusivo)' if lo > 0 else ('POISSON MIGLIORE (conclusivo)' if hi < 0 else 'NON CONCLUSIVO')}")
    return res, diag, disp_tab


def dispersion_vs_gain(res_all: pd.DataFrame, disp_all: pd.DataFrame) -> None:
    print(f"\n{'='*78}\n=== 5. IL GUADAGNO E' MAGGIORE DOVE LA SOVRA-DISPERSIONE E' MAGGIORE? ===\n{'='*78}")
    d = disp_all[disp_all["league"] != "TUTTE"].set_index(["kind", "league"])["disp_cond"]
    g = res_all[res_all["gruppo"] != "TUTTE"].groupby(["kind", "gruppo"])["d_ll"].mean()
    print(f"{'mercato':<10}{'lega':<16}{'var/mu cond. OOS':>19}{'d_LL medio':>13}")
    xs, ys = [], []
    for (kind, lg), disp in d.items():
        gain = g.get((kind, lg), np.nan)
        print(f"{kind:<10}{lg:<16}{disp:>19.3f}{gain:>+13.5f}")
        if np.isfinite(gain):
            xs.append(disp); ys.append(gain)
    if len(xs) >= 3:
        rho = float(np.corrcoef(xs, ys)[0, 1])
        print(f"\n  correlazione (dispersione condizionata, guadagno) su {len(xs)} celle "
              f"lega x mercato: r = {rho:+.3f}")
        print("  ATTENZIONE: 6 celle sono pochissime — indicativo, non conclusivo.")


def main() -> None:
    rng = np.random.default_rng(SEED)
    df = load_raw()
    print(f"Partite caricate: {len(df)} ({df['league'].nunique()} leghe, "
          f"{df['season'].nunique()} stagioni)")
    structure(df)
    res_c, diag_c, disp_c = run_market(df, "corners", rng)
    res_k, diag_k, disp_k = run_market(df, "cards", rng)
    res_all = pd.concat([res_c, res_k], ignore_index=True)
    disp_all = pd.concat([disp_c, disp_k], ignore_index=True)
    dispersion_vs_gain(res_all, disp_all)
    print("\nLimiti dichiarati: nessuna quota di mercato su corner/cartellini nei dati "
          "-> si misura la BONTA' probabilistica (log-loss/Brier/calibrazione), NON "
          "l'efficienza contro un book. Le linee sono quelle standard, non quelle "
          "effettivamente offerte partita per partita. La media resta quella del "
          "modello di conteggio della Fase 96: la NB cambia SOLO la forma, non il "
          "centro.")


if __name__ == "__main__":
    main()
