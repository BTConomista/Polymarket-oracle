"""Fase 99 — La correzione di LIVELLO dei conteggi (il lead trasversale della Fase 98).

Perche'. Tre fronti della Fase 98, che non si parlavano, hanno misurato lo stesso
difetto: il totale atteso di corner/cartellini e' SISTEMATICAMENTE storto fuori
campione (Premier cartellini -0.201, Serie A corner +0.352, listino corner +0.117 su
TUTTE e quattro le soglie). Un bias costante su tutte le linee non e' un fatto sui
dati: e' la firma di una media sbagliata. La causa e' identificata: l'emivita 365g,
tarata sui GOL, non insegue la DERIVA TEMPORALE dei conteggi (i cartellini crescono,
i corner calano). E' anche cio' che CAUSA i 3 peggioramenti conclusivi della NB
(Fase 98 fronte 1): allargare la distribuzione attorno a un centro storto sposta
massa dal lato sbagliato.

L'ipotesi: una costante moltiplicativa di livello, stimata SOLO SUL PASSATO, vale piu'
di tutte le correzioni di forma provate finora (NB compresa, e ~5x l'arbitro).

Quattro stimatori, tutti walk-forward e senza look-ahead:
  c=1        nessuna correzione (il modello della Fase 96, controllo);
  c_oos      rapporto sum(reali)/sum(attesi) su TUTTE le stagioni di test gia'
             passate (disponibile dal 2o fold in poi; al 1o fold vale 1);
  c_last2    stesso rapporto sulle ULTIME DUE stagioni di test: il compromesso fra
             la memoria lunga di c_oos (che media via la deriva) e il rumore di c_last;
  c_last     stesso rapporto ma sulla SOLA stagione di test piu' recente — insegue
             piu' in fretta, ma su ~380 partite invece che su migliaia;
  c_trend    OLS della media stagionale sull'indice di stagione, calcolata sulle sole
             stagioni di TRAIN ed estrapolata di un passo. E' l'unico disponibile
             gia' dal PRIMO fold, e l'unico che modella la deriva invece di
             correggerne la media.

Per ciascuno: bias residuo, log-loss binario OOS sulle linee Over/Under standard,
scarto di calibrazione, e CI bootstrap APPAIATO (5000 ricampionamenti) sulla
differenza per-partita contro il controllo c=1. Il tutto in croce con la forma
(Poisson e NB), perche' la domanda vera della Fase 98 e': la forma serve DOPO che il
centro e' a posto?

Diagnostico aggiuntivo: sweep dell'emivita usata per il solo LIVELLO di base (365g
ufficiale contro 60-720g) — dice se il difetto si potrebbe togliere alla radice
invece che con una pezza a valle. E' un ausilio alla lettura, NON una selezione:
il numero adottabile e' quello degli stimatori walk-forward qui sopra.

Riusa `_run_counts_nb.py` (caricamento, fit dei conteggi, stima di r, metriche) per
non duplicare il modello: la media resta quella della Fase 96, si cambia SOLO la
costante di livello.

NON registra run (diagnostico). Uso: python scripts/_run_counts_level.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import _run_counts_nb as nb  # noqa: E402  (modello e metriche della Fase 98)

N_BOOT = 5000
SEED = 909
HALF_LIVES = [60.0, 120.0, 180.0, 270.0, 365.0, 540.0, 720.0]
ESTIMATORS = ["c=1", "c_oos", "c_last2", "c_last", "c_trend"]


# --------------------------------------------------------------- stimatori di livello
def c_trend_from_train(train: pd.DataFrame, col_h: str, col_a: str) -> float:
    """OLS della media stagionale sull'indice di stagione, estrapolata di un passo.

    Ritorna il FATTORE da applicare al livello del modello: (media prevista per la
    stagione di test) / (media pesata che il modello userebbe). Si stima la seconda
    con la stessa emivita del modello per restare confrontabili.
    """
    tot = train[col_h] + train[col_a]
    per_season = tot.groupby(train["season"]).mean()
    if len(per_season) < 3:
        return float("nan")             # niente retta: il chiamante usa fattore neutro
    x = np.arange(len(per_season), dtype=float)
    y = per_season.to_numpy(dtype=float)
    b, a = np.polyfit(x, y, 1)          # y = b*x + a
    pred_next = a + b * len(per_season)  # estrapolazione di UN passo
    if pred_next <= 0:
        return float("nan")
    return float(pred_next)


def build_predictions_level(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Come `nb.build_predictions`, ma emette anche i quattro fattori di livello.

    Ogni fattore e' stimato con informazione disponibile PRIMA della stagione di test.
    """
    ch, ca = ("HC", "AC") if kind == "corners" else ("HY", "AY")
    frames = []
    for lg, g in df.groupby("league"):
        seasons = sorted(g["season"].unique())
        done: list[pd.DataFrame] = []
        for s in seasons[2:]:
            train = g[g["season"] < s]
            test = g[g["season"] == s]
            if len(train) < 400 or test.empty:
                continue
            as_of = test["date"].min()
            att, dfn, base, hadv, aadv = nb.fit_counts(train, ch, ca, as_of)

            # --- dispersione NB: identica alla Fase 98 (solo passato) ---
            if done:
                past = pd.concat(done, ignore_index=True)
                y_p, m_p = past["real"].to_numpy(float), past["exp"].to_numpy(float)
            else:
                m_in = nb._predict(train, att, dfn, base, hadv, aadv)
                y_in = (train[ch] + train[ca]).to_numpy(float)
                ok_in = np.isfinite(m_in)
                y_p, m_p = y_in[ok_in], m_in[ok_in]
            r_nb = nb.r_mle(y_p, m_p, nb.r_mom(y_p, m_p))

            # --- i quattro fattori di livello ---
            c_oos = float(np.sum(y_p) / np.sum(m_p)) if done else 1.0
            if done:
                last = done[-1]
                c_last = float(last["real"].sum() / last["exp"].sum())
                l2 = pd.concat(done[-2:], ignore_index=True)
                c_last2 = float(l2["real"].sum() / l2["exp"].sum())
            else:
                c_last = c_last2 = 1.0
            m_tr = nb._predict(train, att, dfn, base, hadv, aadv)
            ok_tr = np.isfinite(m_tr)
            mean_model = float(np.mean(m_tr[ok_tr])) if ok_tr.any() else np.nan
            pred_next = c_trend_from_train(train, ch, ca)
            c_trend = (float(pred_next / mean_model)
                       if np.isfinite(pred_next) and mean_model and mean_model > 0
                       else 1.0)

            m_te = nb._predict(test, att, dfn, base, hadv, aadv)
            ok = np.isfinite(m_te)
            frames.append(pd.DataFrame({
                "league": lg, "season": s, "kind": kind,
                "exp": m_te[ok],
                "real": (test[ch] + test[ca]).to_numpy(float)[ok],
                "r_nb": r_nb,
                "c=1": 1.0, "c_oos": c_oos, "c_last2": c_last2,
                "c_last": c_last, "c_trend": c_trend,
            }))
            done.append(frames[-1][["exp", "real"]])
    return pd.concat(frames, ignore_index=True)


# -------------------------------------------------------------------------- metriche
def lines_for(kind: str) -> list[float]:
    return nb.MARKETS[kind]


def eval_grid(pred: pd.DataFrame, kind: str, rng: np.random.Generator) -> pd.DataFrame:
    """log-loss OOS per (stimatore x forma), con CI appaiato contro (c=1, stessa forma)."""
    lines = lines_for(kind)
    m0 = pred["exp"].to_numpy(float)
    y = pred["real"].to_numpy(float)
    r = pred["r_nb"].to_numpy(float)

    def ll_of(c: np.ndarray, shape: str) -> np.ndarray:
        """log-loss per-partita mediata sulle linee (una riga per partita)."""
        m = m0 * c
        acc = np.zeros(len(m))
        for ln in lines:
            p = nb.p_over_pois(m, ln) if shape == "Poisson" else nb.p_over_nb(m, ln, r)
            acc += nb._ll(p, (y > ln).astype(float))
        return acc / len(lines)

    rows = []
    for shape in ("Poisson", "NB"):
        ref = ll_of(pred["c=1"].to_numpy(float), shape)
        for est in ESTIMATORS:
            c = pred[est].to_numpy(float)
            cur = ll_of(c, shape)
            diff = ref - cur                      # >0 = lo stimatore MIGLIORA
            lo, hi, share = nb.paired_boot(diff, rng)
            mean = float(np.mean(diff))
            bias = float(np.mean(m0 * c) - np.mean(y))
            rows.append({
                "kind": kind, "forma": shape, "stimatore": est,
                "c_medio": float(np.mean(c)), "bias": bias,
                "LL": float(np.mean(cur)), "delta": mean, "lo": lo, "hi": hi,
                "P>0": share,
                "conclusivo": "SI" if (lo > 0 or hi < 0) else "no",
            })
    return pd.DataFrame(rows)


def per_league(pred: pd.DataFrame, kind: str, est: str, rng: np.random.Generator) -> pd.DataFrame:
    lines = lines_for(kind)
    rows = []
    for lg, g in pred.groupby("league"):
        m0 = g["exp"].to_numpy(float)
        y = g["real"].to_numpy(float)
        r = g["r_nb"].to_numpy(float)
        c = g[est].to_numpy(float)
        acc0 = np.zeros(len(m0))
        acc1 = np.zeros(len(m0))
        for ln in lines:
            acc0 += nb._ll(nb.p_over_pois(m0, ln), (y > ln).astype(float))
            acc1 += nb._ll(nb.p_over_pois(m0 * c, ln), (y > ln).astype(float))
        diff = (acc0 - acc1) / len(lines)
        lo, hi, share = nb.paired_boot(diff, rng)
        mean = float(np.mean(diff))
        rows.append({
            "kind": kind, "league": lg, "n": len(g),
            "bias_pre": float(np.mean(m0) - np.mean(y)),
            "bias_post": float(np.mean(m0 * c) - np.mean(y)),
            "c_medio": float(np.mean(c)),
            "delta": mean, "lo": lo, "hi": hi, "P>0": share,
            "conclusivo": "SI" if (lo > 0 or hi < 0) else "no",
        })
    return pd.DataFrame(rows)


def per_line(pred: pd.DataFrame, kind: str, est: str, rng: np.random.Generator) -> pd.DataFrame:
    m0 = pred["exp"].to_numpy(float)
    y = pred["real"].to_numpy(float)
    c = pred[est].to_numpy(float)
    rows = []
    for ln in lines_for(kind):
        yb = (y > ln).astype(float)
        p0 = nb.p_over_pois(m0, ln)
        p1 = nb.p_over_pois(m0 * c, ln)
        diff = nb._ll(p0, yb) - nb._ll(p1, yb)
        lo, hi, share = nb.paired_boot(diff, rng)
        mean = float(np.mean(diff))
        rows.append({
            "kind": kind, "linea": ln,
            "cal_pre": float(np.mean(p0) - np.mean(yb)),
            "cal_post": float(np.mean(p1) - np.mean(yb)),
            "delta": mean, "lo": lo, "hi": hi, "P>0": share,
            "conclusivo": "SI" if (lo > 0 or hi < 0) else "no",
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------- diagnostico: emivita del livello
def halflife_sweep(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Bias OOS del modello al variare dell'emivita (diagnostico, non una selezione)."""
    ch, ca = ("HC", "AC") if kind == "corners" else ("HY", "AY")
    rows = []
    orig = nb.HALF_LIFE
    try:
        for hl in HALF_LIVES:
            nb.HALF_LIFE = hl
            bias_num, bias_den, n = 0.0, 0.0, 0
            for lg, g in df.groupby("league"):
                seasons = sorted(g["season"].unique())
                for s in seasons[2:]:
                    train = g[g["season"] < s]
                    test = g[g["season"] == s]
                    if len(train) < 400 or test.empty:
                        continue
                    att, dfn, base, hadv, aadv = nb.fit_counts(
                        train, ch, ca, test["date"].min())
                    m = nb._predict(test, att, dfn, base, hadv, aadv)
                    y = (test[ch] + test[ca]).to_numpy(float)
                    ok = np.isfinite(m)
                    bias_num += float(np.sum(m[ok]))
                    bias_den += float(np.sum(y[ok]))
                    n += int(ok.sum())
            rows.append({"kind": kind, "emivita": hl, "n": n,
                         "bias_medio": (bias_num - bias_den) / max(n, 1),
                         "rapporto": bias_num / max(bias_den, 1e-9)})
    finally:
        nb.HALF_LIFE = orig
    return pd.DataFrame(rows)


# ------------------------------------------ emivita scelta walk-forward (alla radice)
def _oos_by_halflife(df: pd.DataFrame, kind: str) -> dict:
    """Predizioni OOS per ogni (emivita, lega, stagione). Nessuna selezione: solo dati."""
    ch, ca = ("HC", "AC") if kind == "corners" else ("HY", "AY")
    out: dict = {}
    orig = nb.HALF_LIFE
    try:
        for hl in HALF_LIVES:
            nb.HALF_LIFE = hl
            for lg, g in df.groupby("league"):
                seasons = sorted(g["season"].unique())
                for s in seasons[2:]:
                    train = g[g["season"] < s]
                    test = g[g["season"] == s]
                    if len(train) < 400 or test.empty:
                        continue
                    att, dfn, base, hadv, aadv = nb.fit_counts(
                        train, ch, ca, test["date"].min())
                    m = nb._predict(test, att, dfn, base, hadv, aadv)
                    y = (test[ch] + test[ca]).to_numpy(float)
                    ok = np.isfinite(m)
                    out[(hl, lg, s)] = (m[ok], y[ok])
    finally:
        nb.HALF_LIFE = orig
    return out


def halflife_walkforward(df: pd.DataFrame, kind: str,
                         rng: np.random.Generator) -> pd.DataFrame:
    """Sceglie l'emivita del conteggio fold per fold sul SOLO passato, poi la valuta.

    E' la versione onesta dello sweep diagnostico: invece di leggere la curva del bias
    e prendere il minimo (che sarebbe selezione sui dati di test), a ogni fold si
    sceglie l'emivita che minimizza il log-loss sulle stagioni di test GIA' passate.
    Al primo fold, che non ne ha, si usa l'ufficiale 365g.
    """
    lines = lines_for(kind)
    oos = _oos_by_halflife(df, kind)

    def ll_of(m: np.ndarray, y: np.ndarray) -> np.ndarray:
        acc = np.zeros(len(m))
        for ln in lines:
            acc += nb._ll(nb.p_over_pois(m, ln), (y > ln).astype(float))
        return acc / len(lines)

    rows, d_ref, d_wf, chosen = [], [], [], []
    for lg in sorted(df["league"].unique()):
        seasons = sorted({s for (hl, l, s) in oos if l == lg})
        past: list[str] = []
        for s in seasons:
            if past:
                scores = {hl: float(np.mean(np.concatenate(
                    [ll_of(*oos[(hl, lg, ps)]) for ps in past]))) for hl in HALF_LIVES}
                hl_star = min(scores, key=scores.get)
            else:
                hl_star = 365.0
            m_ref, y_ref = oos[(365.0, lg, s)]
            m_wf, y_wf = oos[(hl_star, lg, s)]
            d_ref.append(ll_of(m_ref, y_ref))
            d_wf.append(ll_of(m_wf, y_wf))
            chosen.append({"league": lg, "season": s, "emivita_scelta": hl_star,
                           "bias_365": float(np.mean(m_ref) - np.mean(y_ref)),
                           "bias_wf": float(np.mean(m_wf) - np.mean(y_wf))})
            past.append(s)
    a, b = np.concatenate(d_ref), np.concatenate(d_wf)
    lo, hi, share = nb.paired_boot(a - b, rng)
    rows.append({"kind": kind, "n": len(a),
                 "LL_365": float(np.mean(a)), "LL_wf": float(np.mean(b)),
                 "delta": float(np.mean(a - b)), "lo": lo, "hi": hi, "P>0": share,
                 "conclusivo": "SI" if (lo > 0 or hi < 0) else "no"})
    return pd.DataFrame(rows), pd.DataFrame(chosen)


# --------------------------------------------------- il bias di fold PERSISTE? (la chiave)
def bias_persistence(pred: pd.DataFrame, kind: str,
                     rng: np.random.Generator) -> pd.DataFrame:
    """Il bias di un fold predice quello del fold successivo?

    E' la domanda che decide tutto: qualunque correzione di livello stimata sul passato
    funziona SE E SOLO SE il bias e' persistente. Un bias che c'e' nella MEDIA POOLED ma
    cambia segno di stagione in stagione non e' correggibile — e' rumore aggregato.
    Correlazione di lag 1 sui bias per fold, con CI bootstrap sulle coppie.
    """
    per_fold = (pred.groupby(["league", "season"])
                .apply(lambda g: float(g["exp"].mean() - g["real"].mean()),
                       include_groups=False)
                .rename("bias").reset_index())
    pairs = []
    for lg, g in per_fold.groupby("league"):
        b = g.sort_values("season")["bias"].to_numpy(float)
        for i in range(1, len(b)):
            pairs.append((b[i - 1], b[i]))
    arr = np.array(pairs)
    x, y = arr[:, 0], arr[:, 1]
    r = float(np.corrcoef(x, y)[0, 1])
    idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
    rb = np.array([np.corrcoef(x[i], y[i])[0, 1] for i in idx[:1000]])
    lo, hi = np.percentile(rb, [2.5, 97.5])
    segni = int(np.sum(np.sign(x) == np.sign(y)))
    return pd.DataFrame([{
        "kind": kind, "coppie": len(x), "corr_lag1": r,
        "lo": float(lo), "hi": float(hi),
        "stesso_segno": f"{segni}/{len(x)}",
        "sd_bias": float(np.std(per_fold["bias"])),
        "bias_pooled": float(np.mean(per_fold["bias"])),
        "conclusivo": "SI" if (lo > 0 or hi < 0) else "no",
    }])


# ------------------------------------------------------------------------------- stampa
def _fmt(v: float, nd: int = 5) -> str:
    return f"{v:+.{nd}f}"


def report(kind: str, rng: np.random.Generator, df: pd.DataFrame) -> dict:
    print(f"\n{'=' * 78}\n{kind.upper()} — linee {lines_for(kind)}\n{'=' * 78}")
    pred = build_predictions_level(df, kind)
    print(f"partite OOS: {len(pred)}  |  fold: {pred.groupby(['league','season']).ngroups}")

    fattori = (pred.groupby(["league", "season"])[ESTIMATORS].first()
               .reset_index().round(4))
    print("\nFattori di livello stimati (solo passato), per fold:")
    print(fattori.to_string(index=False))

    grid = eval_grid(pred, kind, rng)
    print("\nlog-loss OOS (media sulle linee) — delta>0 = MIGLIORA sul controllo c=1:")
    show = grid.copy()
    for col in ("bias", "delta", "lo", "hi"):
        show[col] = show[col].map(lambda v: _fmt(v))
    show["LL"] = show["LL"].map(lambda v: f"{v:.5f}")
    show["c_medio"] = show["c_medio"].map(lambda v: f"{v:.4f}")
    print(show.to_string(index=False))

    best = grid[(grid["stimatore"] != "c=1") & (grid["forma"] == "Poisson")]
    best = best.sort_values("delta", ascending=False).iloc[0]
    est = str(best["stimatore"])
    print(f"\nMigliore stimatore di livello (forma Poisson): {est}  "
          f"delta {_fmt(best['delta'])} [{_fmt(best['lo'])}, {_fmt(best['hi'])}]")

    print(f"\nPer lega (stimatore {est}, forma Poisson):")
    pl = per_league(pred, kind, est, rng)
    for col in ("bias_pre", "bias_post", "delta", "lo", "hi"):
        pl[col] = pl[col].map(lambda v: _fmt(v, 4 if "bias" in str(col) else 5))
    print(pl.to_string(index=False))

    print(f"\nPer linea (stimatore {est}, forma Poisson) — cal = P media - frequenza reale:")
    pline = per_line(pred, kind, est, rng)
    for col in ("cal_pre", "cal_post", "delta", "lo", "hi"):
        pline[col] = pline[col].map(lambda v: _fmt(v, 4 if "cal" in str(col) else 5))
    print(pline.to_string(index=False))

    # la domanda della Fase 98: la NB serve ANCORA dopo la correzione di livello?
    g = grid.set_index(["forma", "stimatore"])
    nb_gain_pre = float(g.loc[("NB", "c=1"), "LL"] - g.loc[("Poisson", "c=1"), "LL"])
    nb_gain_post = float(g.loc[("NB", est), "LL"] - g.loc[("Poisson", est), "LL"])
    print(f"\nLa forma NB serve ancora? guadagno NB-su-Poisson: "
          f"prima {_fmt(-nb_gain_pre)}, dopo la correzione {_fmt(-nb_gain_post)}")

    pers = bias_persistence(pred, kind, rng)
    print("\nIl bias di fold PERSISTE? (se no, nessuna correzione di livello puo' funzionare)")
    pp = pers.copy()
    for col in ("corr_lag1", "lo", "hi", "sd_bias", "bias_pooled"):
        pp[col] = pp[col].map(lambda v: _fmt(v, 4))
    print(pp.to_string(index=False))

    wf, chosen = halflife_walkforward(df, kind, rng)
    print("\nAlla RADICE invece che a valle — emivita scelta fold per fold sul solo passato:")
    print(chosen.to_string(index=False))
    w = wf.copy()
    for col in ("delta", "lo", "hi"):
        w[col] = w[col].map(lambda v: _fmt(v))
    for col in ("LL_365", "LL_wf"):
        w[col] = w[col].map(lambda v: f"{v:.5f}")
    print(w.to_string(index=False))

    sweep = halflife_sweep(df, kind)
    print("\nDiagnostico — emivita del livello vs bias OOS (NON e' una selezione):")
    s2 = sweep.copy()
    s2["bias_medio"] = s2["bias_medio"].map(lambda v: _fmt(v, 4))
    s2["rapporto"] = s2["rapporto"].map(lambda v: f"{v:.4f}")
    print(s2.to_string(index=False))

    return {"grid": grid, "per_league": per_league(pred, kind, est, rng),
            "sweep": sweep, "hl_wf": wf, "hl_chosen": chosen,
            "persistenza": pers, "est": est}


def main() -> None:
    rng = np.random.default_rng(SEED)
    df = nb.load_raw()
    print(f"Partite caricate: {len(df)} ({df['league'].nunique()} leghe, "
          f"{df['season'].nunique()} stagioni)")
    out = {}
    for kind in ("corners", "cards"):
        out[kind] = report(kind, rng, df)

    print(f"\n{'=' * 78}\nLETTURA\n{'=' * 78}")
    print("La correzione di livello e' una costante moltiplicativa stimata SOLO sul "
          "passato: non aggiunge informazione, toglie un errore sistematico. Va letta "
          "come un FIX del modello di conteggio della Fase 96, non come un modello "
          "nuovo. Limite dichiarato: nessuna quota su corner/cartellini nei dati -> "
          "si misura la bonta' probabilistica, mai l'efficienza contro un book.")


if __name__ == "__main__":
    main()
