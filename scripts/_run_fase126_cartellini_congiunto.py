"""Cartellini: marginali sotto-disperse + nervosismo di partita (Fase 126).

DA DOVE NASCE. La Fase 98 aveva misurato i cartellini **sovra-dispersi** sul
TOTALE (var/media 1.12-1.48) e adottato la binomiale negativa. La Fase 125 li
ha misurati **sotto-dispersi** per LATO (0.954). Non e' una contraddizione: e'
la stessa cosa vista a due livelli, e l'identita' lo dimostra esattamente.

    var(totale) = var(casa) + var(ospite) + 2·cov(casa, ospite)
      4.7308    =   1.8699  +   2.0258    + 2·0.4175            ✓ (6 decimali)

Ogni lato e' sotto-disperso (0.970 e 0.924), ma i due lati sono **correlati
positivamente** (corr +0.2145): una partita nervosa produce cartellini per
entrambe. **Tutta** la sovra-dispersione del totale viene da li': a lati
indipendenti il totale avrebbe rapporto 0.945, cioe' sarebbe sotto-disperso.

CONSEGUENZA. La binomiale negativa sul totale stava tappando la **correlazione**
usando un parametro di **forma**: la patch giusta per il motivo sbagliato. Il
modello che separa le due cose ha:
  - marginali per lato **double-Poisson** con theta > 1 (sotto-dispersione),
    la stessa `_dp_pmf` gia' in produzione sui gol;
  - un **fattore di nervosismo** Z condiviso dalla partita, con media 1 e
    varianza sigma^2, che induce la correlazione fra i due lati.

    gialli_casa | Z ~ dp(lambda_casa · Z, theta)
    gialli_osp  | Z ~ dp(lambda_osp  · Z, theta)     indipendenti DATO Z

CONFRONTO (walk-forward, sul TOTALE, che e' cio' che il mercato O/U prezza):
  1. Poisson sul totale            (la forma della Fase 96)
  2. Binomiale negativa sul totale (quella adottata alla Fase 98)
  3. dp per lato, lati INDIPENDENTI (deve perdere: ignora la correlazione)
  4. dp per lato + nervosismo Z    (la struttura proposta qui)

USO:
    python scripts/_run_fase126_cartellini_congiunto.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import special

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from _run_fase125_cartellini import (  # noqa: E402
    K_SHRINK, _fattore, carica)

DEST = ROOT / "experiments" / "fase126_cartellini_congiunto.json"

# `_dp_pmf` copre 0..10 per LATO (e' la griglia dei gol gia' in produzione):
# il TOTALE arriva quindi a 20. Osservato: fino a 13, quindi la coda basta.
N_LATO = 10
N_MAX = 2 * N_LATO   # totale rappresentato: 0..20
NODI_Z = 11         # nodi di quadratura per il nervosismo


def _dp(rate: float, theta: float) -> np.ndarray:
    from src.models.market_implied import _dp_pmf
    return _dp_pmf(max(rate, 1e-3), theta)


def _nodi_gamma(sigma2: float, n: int = NODI_Z) -> tuple[np.ndarray, np.ndarray]:
    """Nodi e pesi per Z ~ Gamma(media 1, varianza sigma2), discretizzata.

    Perche' Gamma: e' positiva (un fattore moltiplicativo negativo non ha
    senso), ha media 1 per costruzione, e con sigma2 -> 0 collassa su Z = 1,
    cioe' sul modello a lati indipendenti. Il caso "niente nervosismo" resta
    dunque un caso particolare, non un modello diverso.
    """
    if sigma2 <= 1e-6:
        return np.array([1.0]), np.array([1.0])
    from scipy import stats
    k = 1.0 / sigma2
    d = stats.gamma(a=k, scale=sigma2)
    q = np.linspace(0.5 / n, 1 - 0.5 / n, n)      # quantili equiprobabili
    z = d.ppf(q)
    return z / (z.mean()), np.full(n, 1.0 / n)     # ri-centrato su media 1


_CACHE: dict = {}


def _tabella_dp(theta: float, lo: float, hi: float,
                passo: float = 0.02) -> tuple[np.ndarray, float]:
    """PMF double-Poisson tabulate su una GRIGLIA di tassi.

    Senza tabella il conto e' proibitivo e l'ho pagato sul campo: la prima
    stesura chiamava ``_dp_pmf`` per ogni partita e per ogni nodo, cioe'
    42 combinazioni x 19.761 partite x 11 nodi x 2 lati ~ **18 milioni** di
    bisezioni a 0.32 ms l'una: un'ora e mezza. Con la griglia se ne calcolano
    ~900, una volta per theta.

    Passo 0.02 su tassi ~1-4: errore di arrotondamento ~1%, molto sotto le
    differenze che stiamo misurando.
    """
    chiave = (round(theta, 4), round(lo, 2), round(hi, 2), passo)
    if chiave not in _CACHE:
        from src.models.market_implied import _dp_pmf
        griglia = np.arange(max(lo - passo, 1e-3), hi + 2 * passo, passo)
        tab = np.vstack([_dp_pmf(float(r), theta)[:N_LATO + 1] for r in griglia])
        _CACHE[chiave] = (tab, float(griglia[0]))
    return _CACHE[chiave]


def pmf_totale_batch(lam_c: np.ndarray, lam_o: np.ndarray, theta: float,
                     sigma2: float, passo: float = 0.02) -> np.ndarray:
    """Distribuzione del TOTALE per TUTTE le partite insieme.

    Per ogni nodo del nervosismo si convolvono le due marginali; la
    convoluzione e' vettorizzata sulle partite (una moltiplicazione
    riga-per-riga fra tabelle gia' pronte).
    """
    z, w = _nodi_gamma(sigma2)
    lo = float(min(lam_c.min(), lam_o.min()) * z.min())
    hi = float(max(lam_c.max(), lam_o.max()) * z.max())
    tab, base = _tabella_dp(theta, lo, hi, passo)
    out = np.zeros((len(lam_c), N_MAX + 1))
    for zi, wi in zip(z, w):
        ic = np.clip(np.rint((lam_c * zi - base) / passo).astype(int), 0, len(tab) - 1)
        io_ = np.clip(np.rint((lam_o * zi - base) / passo).astype(int), 0, len(tab) - 1)
        pc, po = tab[ic], tab[io_]
        conv = np.zeros((len(lam_c), N_MAX + 1))
        for k in range(N_LATO + 1):
            conv[:, k:k + N_LATO + 1] += pc[:, [k]] * po
        out += wi * conv
    s = out.sum(axis=1, keepdims=True)
    return np.divide(out, s, out=np.zeros_like(out), where=s > 0)


def _ll(pmf_righe: np.ndarray, y: np.ndarray) -> float:
    yi = np.clip(y.astype(int), 0, N_MAX)
    p = np.clip(pmf_righe[np.arange(len(y)), yi], 1e-12, None)
    return float(np.mean(np.log(p)))


def _ll_poisson_tot(y, lam):
    lam = np.clip(lam, 1e-6, None)
    return float(np.mean(y * np.log(lam) - lam - special.gammaln(y + 1)))


def _ll_negbin_tot(y, lam, alpha):
    lam = np.clip(lam, 1e-6, None)
    r = 1.0 / max(alpha, 1e-9)
    return float(np.mean(special.gammaln(y + r) - special.gammaln(r)
                         - special.gammaln(y + 1) + r * np.log(r / (r + lam))
                         + y * np.log(lam / (r + lam))))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--k", type=float, default=K_SHRINK)
    a = p.parse_args(argv)

    lati = carica()
    # ricompone le due righe per lato in una riga per partita
    casa = lati[lati.casa == 1].set_index("game_id")
    osp = lati[lati.casa == 0].set_index("game_id")
    comuni = casa.index.intersection(osp.index)
    casa, osp = casa.loc[comuni], osp.loc[comuni]
    print(f"partite: {len(comuni):,}")

    stagioni = sorted(lati.season.unique())
    Y, LC, LO = [], [], []
    for s in stagioni[3:]:
        st = lati[lati.season < s]
        if len(st) < 2000:
            continue
        fut = comuni[(casa.season == s).values]
        if len(fut) == 0:
            continue
        for lega in casa.loc[fut].lega.unique():
            sel = fut[(casa.loc[fut].lega == lega).values]
            stl = st[st.lega == lega]
            if len(stl) < 500 or len(sel) == 0:
                continue
            base = stl.gialli.mean()
            f_sq = _fattore(stl, "squadra", a.k)
            f_av = _fattore(stl.assign(_a=stl.avversario), "_a", a.k)
            f_ca = _fattore(stl, "casa", a.k)
            f_ar = _fattore(stl, "referee", a.k)
            for df, dst in ((casa.loc[sel], LC), (osp.loc[sel], LO)):
                lam = (base
                       * df.squadra.map(f_sq).fillna(1.0).values
                       * df.avversario.map(f_av).fillna(1.0).values
                       * df.casa.map(f_ca).fillna(1.0).values
                       * df.referee.map(f_ar).fillna(1.0).values)
                dst.append(lam)
            Y.append((casa.loc[sel].gialli + osp.loc[sel].gialli).values)

    y = np.concatenate(Y); lc = np.concatenate(LC); lo_ = np.concatenate(LO)
    lam_tot = lc + lo_
    print(f"osservazioni valutate: {len(y):,} | totale medio osservato "
          f"{y.mean():.3f}, previsto {lam_tot.mean():.3f}")
    print(f"rapporto var/media del totale: {y.var()/y.mean():.3f}")

    # 1) Poisson sul totale
    ll_pois = _ll_poisson_tot(y, lam_tot)
    # 2) NegBin sul totale, alpha su griglia
    alphas = np.arange(0.001, 0.12, 0.002)
    lls = [_ll_negbin_tot(y, lam_tot, x) for x in alphas]
    alpha = float(alphas[int(np.argmax(lls))]); ll_nb = float(max(lls))

    # 3) e 4): dp per lato, con e senza nervosismo. theta e sigma2 su griglia.
    def valuta(theta, sigma2):
        return _ll(pmf_totale_batch(lc, lo_, theta, sigma2), y)

    print("\ncerco theta e sigma^2 (griglia)...")
    migliori = None
    for th in (1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30):
        for s2 in (0.0, 0.02, 0.04, 0.06, 0.08, 0.10):
            v = valuta(th, s2)
            if migliori is None or v > migliori[0]:
                migliori = (v, th, s2)
    ll_best, th_best, s2_best = migliori
    ll_indip = valuta(th_best, 0.0)

    print(f"\nRISULTATI (log-verosimiglianza per partita sul TOTALE, piu' alta = meglio)")
    print(f"  1. Poisson sul totale            {ll_pois:+.5f}   (forma della Fase 96)")
    print(f"  2. NegBin  sul totale            {ll_nb:+.5f}   alpha={alpha:.3f}  (Fase 98)")
    print(f"  3. dp per lato, INDIPENDENTI     {ll_indip:+.5f}   theta={th_best:.2f}")
    print(f"  4. dp per lato + NERVOSISMO      {ll_best:+.5f}   theta={th_best:.2f}, "
          f"sigma^2={s2_best:.2f}")
    print(f"\n  4 contro 2 (il modello adottato): {ll_best - ll_nb:+.5f}")
    print(f"  3 contro 2 (senza correlazione) : {ll_indip - ll_nb:+.5f}"
          f"   <- deve perdere: ignora la correlazione")

    # IC appaiato su 4 vs 2
    pmf4 = pmf_totale_batch(lc, lo_, th_best, s2_best)
    yi = np.clip(y.astype(int), 0, N_MAX)
    l4 = np.log(np.clip(pmf4[np.arange(len(y)), yi], 1e-12, None))
    r = 1.0 / alpha
    l2 = (special.gammaln(y + r) - special.gammaln(r) - special.gammaln(y + 1)
          + r * np.log(r / (r + lam_tot)) + y * np.log(lam_tot / (r + lam_tot)))
    d = l4 - l2
    rng = np.random.default_rng(31); idx = np.arange(len(d))
    bs = [d[rng.choice(idx, size=len(idx), replace=True)].mean() for _ in range(3000)]
    lo95, hi95 = np.percentile(bs, [2.5, 97.5])
    print(f"  IC95% appaiato su (4 - 2): [{lo95:+.5f}, {hi95:+.5f}]  "
          f"{'✅ conclusivo' if lo95 > 0 else ('❌ perde' if hi95 < 0 else '· nel rumore')}")

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "fase": 126, "n_partite": int(len(y)),
        "identita_varianza": ("var(tot) = var(casa)+var(osp)+2cov; tutta la "
                              "sovra-dispersione del totale e' correlazione"),
        "ll": {"poisson_totale": ll_pois, "negbin_totale": ll_nb,
               "dp_lati_indipendenti": ll_indip, "dp_lati_nervosismo": ll_best},
        "parametri": {"alpha_negbin": alpha, "theta": th_best, "sigma2": s2_best},
        "guadagno_vs_negbin": {"delta": ll_best - ll_nb,
                               "ic95": [float(lo95), float(hi95)]},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
