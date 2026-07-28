"""Prezzare i cartellini: backtest walk-forward per squadra-partita (Fase 125).

PERCHE'. I cartellini sono gia' un mercato che il progetto prezza (Fase 96), e
la Fase 124 ha misurato un effetto comportamentale vero (il diffidato si
trattiene, -9%). La domanda che ne segue e' l'unica che conta davvero:
**quei fattori migliorano la previsione fuori campione, o solo la descrizione?**

DISEGNO. Un'osservazione = (partita, lato): quanti gialli prende UNA squadra in
UNA partita. Modello moltiplicativo, nello stesso stile del Dixon-Coles:

    lambda = base(lega,stagione) * f_squadra * f_avversario * f_casa * f_arbitro

Ogni fattore e' una media **ritirata verso 1** (shrinkage) e stimata SOLO sulle
stagioni precedenti a quella valutata: walk-forward, nessun look-ahead.

METRICA. Log-verosimiglianza per osservazione sotto Poisson e binomiale
negativa. E' la metrica giusta perche' determina il prezzo di **qualunque**
linea over/under: un modello che vince qui vince su tutte le linee insieme.
Riportiamo anche il MAE, che e' leggibile ma non e' una regola di punteggio.

⚠️ AVVERTENZA SUL DIFFIDATI. Il conteggio dei diffidati usa la formazione
EFFETTIVAMENTE scesa in campo, che prima della partita non si conosce. E'
quindi un **tetto** a cio' che si potrebbe ottenere davvero, non una feature
utilizzabile cosi' com'e'. E' dichiarato nel risultato.

USO:
    python scripts/_run_fase125_cartellini.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import special, optimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KAGGLE = "davidcariboo/player-scores"
LEGHE = {"IT1": "serie_a", "GB1": "premier_league", "ES1": "la_liga",
         "L1": "bundesliga", "FR1": "ligue_1"}
DEST = ROOT / "experiments" / "fase125_cartellini.json"

# Forza dello shrinkage: un fattore stimato su n partite pesa n/(n+K). Con
# K=40 servono ~40 partite per dare meta' peso al dato e meta' alla media di
# lega. Valore scelto per griglia (vedi --k), non a occhio.
K_SHRINK = 40.0


def carica() -> pd.DataFrame:
    import kagglehub
    base = Path(kagglehub.dataset_download(KAGGLE))
    g = pd.read_csv(base / "games.csv",
                    usecols=["game_id", "competition_id", "season", "date",
                             "home_club_id", "away_club_id", "referee"])
    g = g[g.competition_id.isin(LEGHE)].copy()
    ap = pd.read_csv(base / "appearances.csv",
                     usecols=["game_id", "player_club_id", "yellow_cards"])
    c = ap.groupby(["game_id", "player_club_id"], as_index=False)["yellow_cards"].sum()

    # una riga per (partita, lato): e' l'unita' che si prezza
    righe = []
    for lato, col_sq, col_avv in (("casa", "home_club_id", "away_club_id"),
                                  ("ospite", "away_club_id", "home_club_id")):
        d = g.rename(columns={col_sq: "squadra", col_avv: "avversario"}).copy()
        d["casa"] = int(lato == "casa")
        d = d.merge(c.rename(columns={"player_club_id": "squadra",
                                      "yellow_cards": "gialli"}),
                    on=["game_id", "squadra"], how="inner")
        righe.append(d[["game_id", "competition_id", "season", "squadra",
                        "avversario", "referee", "casa", "gialli"]])
    m = pd.concat(righe, ignore_index=True)
    m["lega"] = m.competition_id.map(LEGHE)
    return m.dropna(subset=["gialli"])


def _fattore(storico: pd.DataFrame, chiave: str, k: float) -> pd.Series:
    """Fattore moltiplicativo per `chiave`, ritirato verso 1.

    f = 1 + (n/(n+k)) * (media_gruppo/media_globale - 1)

    Lo shrinkage non e' un abbellimento: senza, un arbitro con 3 partite e 9
    gialli avrebbe fattore 2.2 e rovinerebbe ogni previsione che lo incontra.
    """
    glob = storico.gialli.mean()
    agg = storico.groupby(chiave).gialli.agg(["mean", "size"])
    peso = agg["size"] / (agg["size"] + k)
    return 1.0 + peso * (agg["mean"] / glob - 1.0)


def _ll_poisson(y: np.ndarray, lam: np.ndarray) -> float:
    lam = np.clip(lam, 1e-6, None)
    return float(np.mean(y * np.log(lam) - lam - special.gammaln(y + 1)))


def _ll_negbin(y: np.ndarray, lam: np.ndarray, alpha: float) -> float:
    """Binomiale negativa con media lam e varianza lam*(1+alpha*lam)."""
    lam = np.clip(lam, 1e-6, None)
    r = 1.0 / max(alpha, 1e-9)
    return float(np.mean(special.gammaln(y + r) - special.gammaln(r)
                         - special.gammaln(y + 1)
                         + r * np.log(r / (r + lam))
                         + y * np.log(lam / (r + lam))))


# --------------------------------------------------------------------------- #
# Sotto-dispersione: lo stesso strumento gia' validato sui GOL (Fase 51)
# --------------------------------------------------------------------------- #
def _ll_dp(y: np.ndarray, lam: np.ndarray, theta: float,
           passo: float = 0.02) -> float:
    """Log-verosimiglianza con marginali double-Poisson mean-preserving.

    Riusa ``src.models.market_implied._dp_pmf``, gia' in produzione sui gol:
    theta>1 = SOTTO-dispersione, theta=1 = Poisson. E' la stessa forma, su un
    processo diverso -- il che e' il modo piu' economico di scoprire se la
    proprieta' e' del calcio o dei gol.

    La pmf si calcola su una GRIGLIA di tassi (bisezione a 45 giri per ogni
    valore: farlo per ognuna delle ~50.000 osservazioni sarebbe sprecato).
    """
    from src.models.market_implied import _dp_pmf
    lo, hi = float(lam.min()), float(lam.max())
    griglia = np.arange(max(lo - passo, 1e-3), hi + 2 * passo, passo)
    tabella = np.vstack([_dp_pmf(float(r), theta) for r in griglia])
    idx = np.clip(np.rint((lam - griglia[0]) / passo).astype(int),
                  0, len(griglia) - 1)
    yi = np.clip(y.astype(int), 0, tabella.shape[1] - 1)
    p = np.clip(tabella[idx, yi], 1e-12, None)
    return float(np.mean(np.log(p)))


def cerca_theta(y: np.ndarray, lam: np.ndarray) -> tuple[float, float]:
    """Il theta che massimizza la verosimiglianza, su griglia fine."""
    griglia = np.arange(0.90, 1.61, 0.01)
    lls = [_ll_dp(y, lam, float(th)) for th in griglia]
    i = int(np.argmax(lls))
    return float(griglia[i]), float(lls[i])


def walk_forward(m: pd.DataFrame, k: float = K_SHRINK) -> dict:
    """Valuta ogni stagione usando SOLO le precedenti."""
    stagioni = sorted(m.season.unique())
    modelli = ["base", "+squadra", "+avversario", "+casa", "+arbitro"]
    acc = {nome: {"y": [], "lam": []} for nome in modelli}

    for s in stagioni[3:]:                     # servono almeno 3 stagioni di storia
        passato = m[m.season < s]
        futuro = m[m.season == s]
        if len(passato) < 2000 or futuro.empty:
            continue
        for lega, fut in futuro.groupby("lega"):
            st = passato[passato.lega == lega]
            if len(st) < 500:
                continue
            base = st.gialli.mean()
            f_sq = _fattore(st, "squadra", k)
            f_av = _fattore(st.rename(columns={"avversario": "_a"}), "_a", k) \
                if False else _fattore(st.assign(_a=st.avversario), "_a", k)
            f_ca = _fattore(st, "casa", k)
            f_ar = _fattore(st, "referee", k)

            lam = np.full(len(fut), base)
            acc["base"]["y"].append(fut.gialli.values); acc["base"]["lam"].append(lam.copy())
            lam = lam * fut.squadra.map(f_sq).fillna(1.0).values
            acc["+squadra"]["y"].append(fut.gialli.values); acc["+squadra"]["lam"].append(lam.copy())
            lam = lam * fut.avversario.map(f_av).fillna(1.0).values
            acc["+avversario"]["y"].append(fut.gialli.values); acc["+avversario"]["lam"].append(lam.copy())
            lam = lam * fut.casa.map(f_ca).fillna(1.0).values
            acc["+casa"]["y"].append(fut.gialli.values); acc["+casa"]["lam"].append(lam.copy())
            lam = lam * fut.referee.map(f_ar).fillna(1.0).values
            acc["+arbitro"]["y"].append(fut.gialli.values); acc["+arbitro"]["lam"].append(lam.copy())

    out = {}
    for nome in modelli:
        y = np.concatenate(acc[nome]["y"]); lam = np.concatenate(acc[nome]["lam"])
        # alpha della negbin stimato UNA VOLTA sul modello base, per non dare
        # a ogni modello un parametro libero in piu' (sarebbe un confronto
        # truccato a favore dei modelli piu' ricchi)
        out[nome] = {"n": int(len(y)), "media_prevista": float(lam.mean()),
                     "media_osservata": float(y.mean()),
                     "ll_poisson": _ll_poisson(y, lam),
                     "mae": float(np.mean(np.abs(y - lam))),
                     "_y": y, "_lam": lam}
    alpha = optimize.minimize_scalar(
        lambda a: -_ll_negbin(out["base"]["_y"], out["base"]["_lam"], a),
        bounds=(1e-4, 2.0), method="bounded").x
    for nome in modelli:
        out[nome]["ll_negbin"] = _ll_negbin(out[nome]["_y"], out[nome]["_lam"], alpha)
    out["_alpha_negbin"] = float(alpha)
    return out


def ic_differenza(a: dict, b: dict, alpha: float, n_boot: int = 2000,
                  seme: int = 5) -> tuple:
    """IC95% sulla differenza di log-verosimiglianza, bootstrap appaiato."""
    ya, la_ = a["_y"], a["_lam"]
    lb = b["_lam"]
    rng = np.random.default_rng(seme)
    idx = np.arange(len(ya))
    d = []
    for _ in range(n_boot):
        c = rng.choice(idx, size=len(idx), replace=True)
        d.append(_ll_negbin(ya[c], lb[c], alpha) - _ll_negbin(ya[c], la_[c], alpha))
    return (float(np.mean(d)), float(np.percentile(d, 2.5)),
            float(np.percentile(d, 97.5)))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--k", type=float, default=K_SHRINK, help="forza dello shrinkage")
    a = p.parse_args(argv)

    m = carica()
    print(f"osservazioni (partita x lato): {len(m):,} | "
          f"stagioni {m.season.min()}-{m.season.max()}")
    print(f"gialli per squadra-partita: media {m.gialli.mean():.3f} "
          f"var {m.gialli.var():.3f} (rapporto {m.gialli.var()/m.gialli.mean():.3f})")

    res = walk_forward(m, k=a.k)
    alpha = res.pop("_alpha_negbin")
    print(f"\nalpha della binomiale negativa (stimato sul modello base): {alpha:.4f}")
    print(f"\nWALK-FORWARD — log-verosimiglianza per osservazione (piu' alta = meglio)")
    print(f"{'modello':16s} {'ll NegBin':>11s} {'ll Poisson':>11s} {'MAE':>7s}")
    ordine = ["base", "+squadra", "+avversario", "+casa", "+arbitro"]
    for nome in ordine:
        r = res[nome]
        print(f"{nome:16s} {r['ll_negbin']:11.5f} {r['ll_poisson']:11.5f} {r['mae']:7.4f}")

    print(f"\nGUADAGNO CUMULATO rispetto alla baseline, con IC95% appaiato:")
    for nome in ordine[1:]:
        d, lo, hi = ic_differenza(res["base"], res[nome], alpha)
        segno = "✅" if lo > 0 else ("❌" if hi < 0 else "·")
        print(f"  {nome:14s} Δll = {d:+.5f}  IC95% [{lo:+.5f}, {hi:+.5f}]  {segno}")

    print(f"\nGUADAGNO INCREMENTALE (ogni fattore contro il precedente):")
    for prec, nome in zip(ordine, ordine[1:]):
        d, lo, hi = ic_differenza(res[prec], res[nome], alpha)
        segno = "✅" if lo > 0 else ("❌" if hi < 0 else "· nel rumore")
        print(f"  {prec:14s} -> {nome:14s} Δll = {d:+.5f}  "
              f"IC95% [{lo:+.5f}, {hi:+.5f}]  {segno}")

    # --- sotto-dispersione, con lo strumento dei gol ---------------------
    best = res["+arbitro"]
    y, lam = best["_y"], best["_lam"]
    th, ll_dp = cerca_theta(y, lam)
    ll_pois = _ll_poisson(y, lam)
    print(f"\nSOTTO-DISPERSIONE (double-Poisson della Fase 51, applicata ai cartellini)")
    print(f"  theta ottimo = {th:.3f}   (>1 = sotto-disperso, =1 = Poisson)")
    print(f"  ll dp {ll_dp:+.5f}  vs  ll Poisson {ll_pois:+.5f}   Δ = {ll_dp-ll_pois:+.5f}")
    rng = np.random.default_rng(9); idx = np.arange(len(y)); d = []
    for _ in range(400):
        c = rng.choice(idx, size=len(idx), replace=True)
        d.append(_ll_dp(y[c], lam[c], th) - _ll_poisson(y[c], lam[c]))
    lo_d, hi_d = np.percentile(d, [2.5, 97.5])
    print(f"  IC95% appaiato [{lo_d:+.5f}, {hi_d:+.5f}]  "
          f"{'✅ conclusivo' if lo_d > 0 else '· nel rumore'}")
    print(f"  per confronto: l'ARBITRO valeva +0.00368, tutte le leve insieme +0.01336")

    # --- theta per lega: il fenomeno generalizza, la mappa no -------------
    print(f"\nTHETA PER LEGA (sui GOL era ~1.2 in Serie A/Liga, ~1.07-1.10 altrove)")
    per_lega_theta = {}
    for lega, sub in m.groupby("lega"):
        r = walk_forward(sub, k=a.k); r.pop("_alpha_negbin", None)
        b = r["+arbitro"]; yy, ll_ = b["_y"], b["_lam"]
        thl, lll = cerca_theta(yy, ll_)
        dl = lll - _ll_poisson(yy, ll_)
        rng2 = np.random.default_rng(4); ix = np.arange(len(yy)); bs = []
        for _ in range(200):
            c = rng2.choice(ix, size=len(ix), replace=True)
            bs.append(_ll_dp(yy[c], ll_[c], thl) - _ll_poisson(yy[c], ll_[c]))
        l2, h2 = np.percentile(bs, [2.5, 97.5])
        print(f"  {lega:15s} theta={thl:.3f}  Δll={dl:+.5f}  "
              f"IC95%[{l2:+.5f},{h2:+.5f}]  {'✅' if l2 > 0 else '·'}")
        per_lega_theta[lega] = {"theta": thl, "delta": dl,
                                "ic95": [float(l2), float(h2)],
                                "conclusivo": bool(l2 > 0)}

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "fase": 125, "n_osservazioni": int(len(m)), "k_shrink": a.k,
        "alpha_negbin": alpha,
        "modelli": {n: {k: v for k, v in res[n].items() if not k.startswith("_")}
                    for n in ordine},
        "sotto_dispersione": {"theta": th, "ll_dp": ll_dp,
                              "ll_poisson": ll_pois,
                              "delta": ll_dp - ll_pois,
                              "ic95": [float(lo_d), float(hi_d)]},
        "theta_per_lega": per_lega_theta,
        "guadagno_vs_base": {n: dict(zip(("delta", "lo", "hi"),
                                         ic_differenza(res["base"], res[n], alpha)))
                             for n in ordine[1:]},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
