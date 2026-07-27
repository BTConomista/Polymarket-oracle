"""La leva phi(|lambda-mu|) sulle due leghe nuove, con costanti scelte per GRIGLIA.

CONTESTO. Nel tracer della tranche 3 (docs/audit_5_leghe/06_tranche3.md, passo 5) la
phi35 e' stata provata sulle leghe nuove con i parametri fittati per MASSIMA
VEROSIMIGLIANZA sui pareggi (`mi.fit_balance_phi`): bundesliga +0.00122 sull'1X2
(CI non conclusivo), ligue_1 -0.00036 (phi0 fittato = 0). Il progetto ha pero'
scoperto altrove (Liga, confronto F80 vs F81) che le costanti scelte per GRIGLIA
sui MERCATI battono quelle da MLE sui punteggi, e che il guadagno vero si vede sul
GG/NG e non sull'1X2. Questo script rifa' il test col metodo forte.

FORMULA (verificata riga per riga contro src/models/market_implied.py):

    phi(lam, mu) = phi0 * exp(-kappa * |lam - mu|)          # mi.balance_phi
    M_phi = normalize( B * (1 + phi * I) )                  # score_matrix(diag_inflation)

dove B e' la matrice base gia' normalizzata (marginali Poisson o double-Poisson
mean-preserving con parametro theta, piu' la correzione Dixon-Coles su rho).

IDENTITA' USATA PER VETTORIZZARE (esatta, non un'approssimazione). Per QUALUNQUE
mercato definito come somma di celle su un insieme S:

    P_S(phi) = (P_S(0) + phi * D_S) / (1 + phi * D)

con D_S = somma delle celle DIAGONALI dentro S e D = traccia di B. Dimostrazione:
B*(1+phi*I) somma a 1 + phi*D, e sull'insieme S somma a P_S(0) + phi*D_S. Quindi
basta calcolare (P_S, D_S, D) UNA volta per riga e tutta la griglia (phi0, kappa)
si valuta in numpy. Un test di sanita' nello script confronta il risultato con
`mi.price_markets` / `mi.score_matrix` cella per cella.

METODO
  - finestra MERCATO standard: stagioni 1920..2526 (7 stagioni: la chiusura O/U
    reale non esiste prima), righe con chiusura 1X2+O/U completa;
  - inversione delle quote devigate -> (lam, mu) con rho = -0.06 (mi.implied_lambda_mu);
  - selezione dei parametri FUORI CAMPIONE con DUE selettori:
      * LOSO  (leave-one-season-out): per la stagione s i parametri vengono dal
        log-loss sulle ALTRE 6 stagioni;
      * LFO   (leave-future-out, walk-forward): per la stagione s i parametri
        vengono SOLO dalle stagioni PASSATE (la 1a stagione e' solo-training).
        E' il selettore realmente utilizzabile in produzione ed e' quello usato
        dalla Fase 81; il LOSO usa anche il futuro, quindi e' ottimistico.
  - riferimento: phi = 0 (matrice tau liscia), stesso theta;
  - bootstrap appaiato B=10.000 (boot di scripts/_fase52_common.py) e verdetto
    esplicito CONCLUSIVO / nel rumore, piu' una soglia Bonferroni dichiarata.

Uso: python scripts/leve_phi_griglia.py [--leagues ...] [--quick]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.data import loader                          # noqa: E402
from src.evaluation import metrics                   # noqa: E402
from src.models import market_implied as mi          # noqa: E402
from scripts._fase52_common import boot, dp_matrices  # noqa: E402

OUT = ROOT / "docs" / "audit_5_leghe" / "numeri" / "leve_phi_griglia.json"
SCRATCH = Path("/tmp/claude-0/-home-user-Polymarket-oracle/"
               "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad")
SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
LEAGUES = ["bundesliga", "ligue_1", "serie_a", "premier_league", "la_liga"]
SNAPSHOT = {"bundesliga": ROOT / "data/bundesliga_matches.csv",
            "ligue_1": ROOT / "data/ligue_1_matches.csv"}
RHO = -0.06
SEED = 3535
MAXG = mi.MAX_GOALS
K = np.arange(MAXG + 1)

# --- la griglia (phi0, kappa) richiesta dal compito -------------------------- #
PHI0S = np.round(np.arange(0.0, 1.0001, 0.05), 3)      # 21 valori
KAPPAS = np.round(np.arange(0.0, 4.0001, 0.25), 3)     # 17 valori
# phi0 = 0 annulla phi qualunque sia kappa -> un solo punto, niente duplicati
GRID = [(0.0, 0.0)] + [(float(p), float(k)) for p in PHI0S if p > 0 for k in KAPPAS]
# CONFUTAZIONE 1: sotto-griglia kappa=0 = inflazione-pareggio COSTANTE (la vecchia
# draw-inflation, Fase 12b, gia' chiusa). Se una phi costante fa lo stesso lavoro,
# la dipendenza dall'EQUILIBRIO |lam-mu| — cioe' la leva phi35 vera e propria —
# non sta aggiungendo nulla.
GRID_COST = [(0.0, 0.0)] + [(float(p), 0.0) for p in PHI0S if p > 0]
# CONFUTAZIONE 2: griglia ESTESA, per capire se l'ottimo del GG/NG e' interno o
# schiacciato sul bordo phi0=1 (un ottimo sul bordo non e' una stima, e' un knob).
PHI0S_EXT = np.round(np.arange(0.0, 3.0001, 0.10), 3)
GRID_EXT = [(0.0, 0.0)] + [(float(p), float(k)) for p in PHI0S_EXT if p > 0 for k in KAPPAS]
THETAS = [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30]
THETA_PROV = 1.20      # valore di prova PROVVISORIO (l'agente-theta gira a parte)

# --- mercati ---------------------------------------------------------------- #
_I, _J = np.meshgrid(K, K, indexing="ij")
_TOT = _I + _J
MASKS = {                       # mercati BINARI: maschera di celle
    "draw": _I == _J,
    "dc_1x": _I >= _J,
    "dc_2x": _J >= _I,
    "btts": (_I >= 1) & (_J >= 1),          # GG/NG
    "over_1.5": _TOT >= 2,
    "over_2.5": _TOT >= 3,
    "over_3.5": _TOT >= 4,
    "cs_home": _J == 0,
}
BIN_MK = list(MASKS)
CAT_MK = ["1X2", "multigol", "risultato_esatto"]
ALL_MK = BIN_MK + CAT_MK
LAB = {"draw": "pareggio", "dc_1x": "doppia 1X", "dc_2x": "doppia X2",
       "btts": "GG/NG", "over_1.5": "O/U 1.5", "over_2.5": "O/U 2.5",
       "over_3.5": "O/U 3.5", "cs_home": "clean sheet casa", "1X2": "1X2",
       "multigol": "multigol", "risultato_esatto": "ris. esatto"}
# I mercati che il ROUTER di price_markets prende dalla matrice tau (SENZA phi):
# li' la phi non li tocca per costruzione. Qui li valutiamo comunque DALLA matrice
# phi, per misurare il danno che farebbe se fosse applicata a tutto.
TAU_ROUTED = {"over_1.5", "over_2.5", "over_3.5", "multigol", "cs_home"}


# ------------------------------------------------------------------ dati --- #
def carica(league: str) -> pd.DataFrame:
    if league in SNAPSHOT:
        df = pd.read_csv(SNAPSHOT[league])
    else:
        df = loader.load_league(league)
    df["season"] = df["season"].astype(str)
    df = df[df["season"].isin(SEASONS)].copy()
    cols = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    ok = np.isfinite(df[cols].to_numpy(dtype=float)).all(axis=1)
    df = df[ok].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    # giornata (serve solo alla variante knee34), stessa formula di Fase 50/80
    m = np.zeros(len(df), int)
    for _, g in df.groupby("season"):
        cnt: dict = {}
        for i in g.index:
            h, a = df.at[i, "home_team"], df.at[i, "away_team"]
            hi, ai = cnt.get(h, 0), cnt.get(a, 0)
            m[i] = int(round((hi + ai) / 2)) + 1
            cnt[h], cnt[a] = hi + 1, ai + 1
    df["matchday"] = m
    return df


def inverti(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """(lam, mu) impliciti nella chiusura devigata. Cache nello scratchpad."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fp = SCRATCH / f"phi_rates_{league}.csv"
    if fp.exists():
        c = pd.read_csv(fp)
        if len(c) == len(df):
            df["lam"], df["mu"] = c["lam"].to_numpy(), c["mu"].to_numpy()
            return df
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, RHO)
    df["lam"], df["mu"] = lam, mu
    df[["date", "season", "home_team", "away_team", "lam", "mu"]].to_csv(fp, index=False)
    return df


# ------------------------------------------------- quantita' per la griglia -- #
def quantita(lam, mu, hg, ag, theta: float) -> dict:
    """(P_S, D_S) per ogni mercato + la traccia D, dalle matrici base.

    P_S = prob del mercato a phi=0; D_S = parte DIAGONALE di P_S. Con questi tre
    numeri per riga, P_S(phi) = (P_S + phi*D_S)/(1 + phi*D) per ogni phi."""
    M = dp_matrices(np.asarray(lam, float), np.asarray(mu, float), RHO, theta)
    n = len(M)
    diag = np.einsum("nii->ni", M)                 # (n, 11) celle diagonali
    D = diag.sum(1)
    q = {"D": D, "n": n}
    for mk, msk in MASKS.items():
        q[f"P_{mk}"] = (M * msk[None]).sum(axis=(1, 2))
        q[f"D_{mk}"] = diag[:, np.diag(msk)].sum(1)
    # --- 1X2 (3 esiti): prob dell'esito REALIZZATO ---
    pH = (M * (_I > _J)[None]).sum(axis=(1, 2))
    pA = (M * (_I < _J)[None]).sum(axis=(1, 2))
    pD = D.copy()
    win = np.where(hg > ag, pH, np.where(hg < ag, pA, pD))
    q["P_1X2"] = win
    q["D_1X2"] = np.where(hg == ag, pD, 0.0)
    # --- multigol (3 bande sui gol totali): banda realizzata ---
    tot = hg + ag
    band = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    bmask = [(_TOT <= 1), (_TOT >= 2) & (_TOT <= 3), (_TOT >= 4)]
    Pb = np.stack([(M * b[None]).sum(axis=(1, 2)) for b in bmask], 1)
    Db = np.stack([diag[:, np.diag(b)].sum(1) for b in bmask], 1)
    q["P_multigol"] = Pb[np.arange(n), band]
    q["D_multigol"] = Db[np.arange(n), band]
    # --- risultato esatto: la cella osservata ---
    hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
    cell = M[np.arange(n), hc, ac]
    q["P_risultato_esatto"] = cell
    q["D_risultato_esatto"] = np.where(hc == ac, cell, 0.0)
    q["bal"] = np.abs(np.asarray(lam, float) - np.asarray(mu, float))
    return q


def esiti(hg, ag) -> dict:
    """y (0/1) dei mercati binari."""
    tot = hg + ag
    return {"draw": (hg == ag), "dc_1x": (hg >= ag), "dc_2x": (ag >= hg),
            "btts": (hg >= 1) & (ag >= 1), "over_1.5": tot >= 2,
            "over_2.5": tot >= 3, "over_3.5": tot >= 4, "cs_home": ag == 0}


def ll_market(q: dict, y: dict, mk: str, phi: np.ndarray) -> np.ndarray:
    """log-loss per riga del mercato ``mk`` con inflazione ``phi`` (array per riga)."""
    den = 1.0 + phi * q["D"]
    if mk in MASKS:
        p = np.clip((q[f"P_{mk}"] + phi * q[f"D_{mk}"]) / den, 1e-15, 1 - 1e-15)
        yy = y[mk].astype(float)
        return -(yy * np.log(p) + (1 - yy) * np.log(1 - p))
    p = np.clip((q[f"P_{mk}"] + phi * q[f"D_{mk}"]) / den, 1e-15, None)
    return -np.log(p)


# ------------------------------------------------------ selezione a griglia -- #
def somme_stagione(q, y, seasons_idx, grid, thetas_q) -> dict:
    """Per ogni (theta, phi0, kappa) e ogni mercato: SOMMA del log-loss per stagione.
    Ritorna dict mk -> array (G, S) con G = len(thetas)*len(grid)."""
    S = len(seasons_idx)
    G = len(thetas_q) * len(grid)
    res = {mk: np.zeros((G, S)) for mk in ALL_MK}
    g = 0
    for qt in thetas_q:
        bal = qt["bal"]
        for phi0, kap in grid:
            phi = np.zeros_like(bal) if phi0 == 0 else phi0 * np.exp(-kap * bal)
            for mk in ALL_MK:
                ll = ll_market(qt, y, mk, phi)
                for si, idx in enumerate(seasons_idx):
                    res[mk][g, si] = ll[idx].sum()
            g += 1
    return res


def seleziona(somme_mk, n_per_season, modo: str) -> list[int]:
    """Indice di griglia scelto per ogni stagione di test, FUORI CAMPIONE.
    modo='loso': training = tutte le altre stagioni.
    modo='lfo' : training = solo le stagioni PRECEDENTI (la 1a non e' testabile)."""
    S = somme_mk.shape[1]
    tot = somme_mk.sum(1); ntot = n_per_season.sum()
    out = []
    for s in range(S):
        if modo == "loso":
            m = (tot - somme_mk[:, s]) / (ntot - n_per_season[s])
        else:
            if s == 0:
                out.append(-1); continue
            m = somme_mk[:, :s].sum(1) / n_per_season[:s].sum()
        out.append(int(np.argmin(m)))
    return out


# --------------------------------------------------------------- valutazione - #
def valuta(q_by_theta, y, seasons_idx, grid, thetas_q_keys, scelte) -> np.ndarray:
    """log-loss per riga concatenato sulle stagioni testabili, coi parametri scelti."""
    parts = []
    for si, idx in enumerate(seasons_idx):
        g = scelte[si]
        if g < 0 or len(idx) == 0:
            continue
        ti, gi = divmod(g, len(grid))
        phi0, kap = grid[gi]
        qt = q_by_theta[thetas_q_keys[ti]]
        bal = qt["bal"]
        phi = np.zeros_like(bal) if phi0 == 0 else phi0 * np.exp(-kap * bal)
        parts.append((idx, phi, qt))
    return parts


def _ll_da_parts(parts, y, mk) -> np.ndarray:
    return np.concatenate([ll_market(qt, y, mk, phi)[idx] for idx, phi, qt in parts])


def verdetto(d, rng, k_tests: int = 1):
    """boot appaiato (fonte: scripts/_fase52_common.boot) + soglia Bonferroni."""
    mean, lo, hi, pneg = boot(d, rng)
    # CI Bonferroni: stesso schema di ricampionamento, livello 1-0.05/k
    B = 10_000
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    a = 100.0 * (0.05 / k_tests) / 2.0
    blo, bhi = float(np.percentile(m, a)), float(np.percentile(m, 100 - a))
    v = "CONCLUSIVO" if lo > 0 else ("PEGGIORA" if hi < 0 else "nel rumore")
    return dict(guadagno=float(mean), ci95=[float(lo), float(hi)],
                ci_bonf=[blo, bhi], p_positivo=float(1 - pneg), verdetto=v,
                conclusivo_bonf=bool(blo > 0))


# ----------------------------------------------------- sanita' vettorizzazione #
def test_sanita() -> dict:
    """Verifica che l'identita' (P_S + phi*D_S)/(1+phi*D) riproduca ESATTAMENTE
    mi.score_matrix(diag_inflation=phi) e mi.price_markets."""
    rng = np.random.default_rng(0)
    lam = rng.uniform(0.5, 2.6, 40); mu = rng.uniform(0.4, 2.2, 40)
    hg = rng.integers(0, 4, 40); ag = rng.integers(0, 4, 40)
    err = 0.0
    for theta in (1.0, 1.2):
        q = quantita(lam, mu, hg, ag, theta)
        for phi0, kap in [(0.3, 1.5), (0.7, 0.5), (1.0, 4.0)]:
            phi = phi0 * np.exp(-kap * np.abs(lam - mu))
            den = 1.0 + phi * q["D"]
            for i in range(40):
                M = mi.score_matrix(lam[i], mu[i], RHO,
                                    diag_inflation=float(phi[i]),
                                    dp_theta=(None if theta == 1.0 else theta))
                d = mi.derive_markets(M)
                mine = {
                    "draw": (q["P_draw"][i] + phi[i] * q["D_draw"][i]) / den[i],
                    "btts": (q["P_btts"][i] + phi[i] * q["D_btts"][i]) / den[i],
                    "over_2.5": (q["P_over_2.5"][i] + phi[i] * q["D_over_2.5"][i]) / den[i],
                    "dc_1x": (q["P_dc_1x"][i] + phi[i] * q["D_dc_1x"][i]) / den[i],
                    "cs_home": (q["P_cs_home"][i] + phi[i] * q["D_cs_home"][i]) / den[i],
                }
                for k_, v_ in mine.items():
                    err = max(err, abs(v_ - d[k_]))
    # controllo che la phi della griglia sia la stessa di mi.balance_phi
    err_phi = max(abs(0.3 * np.exp(-1.5 * abs(l - m)) - mi.balance_phi(l, m, 0.3, 1.5))
                  for l, m in zip(lam, mu))
    return {"max_err_prob_vs_score_matrix": float(err),
            "max_err_phi_vs_balance_phi": float(err_phi),
            "ok": bool(err < 1e-12 and err_phi < 1e-15)}


# --------------------------------------------------------- ricalibrazione mu -- #
def _knee_basis(md, knee=34.0):
    md = np.asarray(md, float)
    return np.column_stack([np.ones_like(md), (md - 19.5) / 18.5,
                            np.maximum(0.0, md - knee) / (38.0 - knee)])


def _fit_knee(rate, y, md):
    from scipy.optimize import minimize
    X = _knee_basis(md); base = np.asarray(rate, float); y = np.asarray(y, float)
    return minimize(lambda c: float(np.sum(base * np.exp(X @ c) - y * (X @ c))),
                    np.zeros(3),
                    jac=lambda c: X.T @ (base * np.exp(X @ c) - y),
                    method="L-BFGS-B").x


# ------------------------------------------------------------------- main ---- #
def analizza_lega(league: str, rng, quick: bool) -> dict:
    t0 = time.time()
    df = inverti(carica(league), league)
    seasons = [s for s in SEASONS if (df.season == s).any()]
    seasons_idx = [np.where(df.season.to_numpy() == s)[0] for s in seasons]
    n_per_season = np.array([len(i) for i in seasons_idx])
    hg = df.home_goals.to_numpy().astype(int); ag = df.away_goals.to_numpy().astype(int)
    y = esiti(hg, ag)
    lam = df.lam.to_numpy(); mu = df.mu.to_numpy()
    print(f"\n{'='*100}\n{league.upper()} — {len(df)} partite, stagioni "
          f"{seasons[0]}..{seasons[-1]} ({len(seasons)}), rho={RHO}\n{'='*100}", flush=True)

    thetas = [1.0] if quick else THETAS
    q_by_theta = {t: quantita(lam, mu, hg, ag, t) for t in thetas}
    res: dict = {"n": int(len(df)), "stagioni": seasons,
                 "n_per_stagione": n_per_season.tolist()}

    # ---------- (0) riferimento MLE: replica del metodo debole ---------------- #
    mle = {}
    for si, s in enumerate(seasons):
        tr = np.concatenate([seasons_idx[j] for j in range(len(seasons)) if j != si])
        mle[s] = mi.fit_balance_phi(lam[tr], mu[tr],
                                    (hg[tr] == ag[tr]).astype(float), RHO)
    res["mle_loso"] = {s: [float(a) for a in mle[s]] for s in seasons}
    print("  [MLE leave-one-season-out]  phi0 " +
          ", ".join(f"{s}:{mle[s][0]:.3f}" for s in seasons))
    print("                              kappa " +
          ", ".join(f"{s}:{mle[s][1]:.2f}" for s in seasons))

    # ---------- (1) griglia phi (theta = 1), selezione LOSO e LFO ------------ #
    q1 = {1.0: q_by_theta[1.0]}
    S1 = somme_stagione(q1, y, seasons_idx, GRID, [q_by_theta[1.0]])
    res["griglia_phi"] = {}
    print(f"\n  [griglia phi0 x kappa = {len(GRID)} punti, theta=1]")
    for modo in ("loso", "lfo"):
        blocco = {}
        print(f"\n  --- selettore {modo.upper()} ---")
        print(f"    {'mercato':<18}{'senza phi':>10}{'con phi':>10}{'guadagno':>11}"
              f"{'CI95':>22}  verdetto      (phi0,kappa) per stagione")
        for mk in ALL_MK:
            sc = seleziona(S1[mk], n_per_season, modo)
            parts = valuta(q1, y, seasons_idx, GRID, [1.0], sc)
            if not parts:
                continue
            ll_phi = _ll_da_parts(parts, y, mk)
            parts0 = [(idx, np.zeros_like(phi), qt) for idx, phi, qt in parts]
            ll_ref = _ll_da_parts(parts0, y, mk)
            v = verdetto(ll_ref - ll_phi, rng, k_tests=len(ALL_MK))
            pars = [GRID[g % len(GRID)] if g >= 0 else None for g in sc]
            pstr = " ".join("-" if p is None else f"{p[0]:.2f}/{p[1]:.2f}" for p in pars)
            print(f"    {LAB[mk]:<18}{ll_ref.mean():>10.4f}{ll_phi.mean():>10.4f}"
                  f"{v['guadagno']:>+11.5f}  [{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}]"
                  f"  {v['verdetto']:<12}  {pstr}")
            blocco[mk] = {"ll_senza_phi": float(ll_ref.mean()),
                          "ll_con_phi": float(ll_phi.mean()),
                          "n": int(len(ll_phi)),
                          "parametri_per_stagione": [None if p is None else list(p) for p in pars],
                          "phi0_min": None if all(p is None for p in pars) else float(min(p[0] for p in pars if p)),
                          "phi0_max": None if all(p is None for p in pars) else float(max(p[0] for p in pars if p)),
                          **v}
        res["griglia_phi"][modo] = blocco

    # ---------- (1-bis) CONFUTAZIONI: phi costante e griglia estesa ---------- #
    print("\n  [confutazione A — phi COSTANTE (kappa=0): la dipendenza da |lam-mu| "
          "aggiunge qualcosa?]")
    Sc = somme_stagione(q1, y, seasons_idx, GRID_COST, [q_by_theta[1.0]])
    Se = somme_stagione(q1, y, seasons_idx, GRID_EXT, [q_by_theta[1.0]])
    conf = {}
    print(f"    {'mercato':<18}{'phi(|l-m|)':>12}{'phi costante':>14}{'delta':>11}"
          f"   phi0 costante per stagione")
    for mk in ALL_MK:
        sc = seleziona(Sc[mk], n_per_season, "loso")
        parts = valuta(q1, y, seasons_idx, GRID_COST, [1.0], sc)
        ll_c = _ll_da_parts(parts, y, mk)
        g = res["griglia_phi"]["loso"][mk]["ll_con_phi"]
        pars = [GRID_COST[i][0] for i in sc]
        conf[mk] = {"ll_phi_costante": float(ll_c.mean()), "ll_phi35": float(g),
                    "delta_phi35_meno_costante": float(g - ll_c.mean()),
                    "phi0_costante_per_stagione": [float(p) for p in pars]}
        print(f"    {LAB[mk]:<18}{g:>12.4f}{ll_c.mean():>14.4f}{g-ll_c.mean():>+11.5f}"
              f"   {' '.join(f'{p:.2f}' for p in pars)}")
    res["confutazione_phi_costante"] = conf

    print(f"\n  [confutazione B — griglia ESTESA phi0 fino a {PHI0S_EXT[-1]:.1f}: "
          f"l'ottimo e' interno o sul bordo?]")
    ext = {}
    print(f"    {'mercato':<18}{'ll bordo1.0':>12}{'ll esteso':>11}{'delta':>11}"
          f"   (phi0,kappa) estesi per stagione")
    for mk in ALL_MK:
        sc = seleziona(Se[mk], n_per_season, "loso")
        parts = valuta(q1, y, seasons_idx, GRID_EXT, [1.0], sc)
        ll_e = _ll_da_parts(parts, y, mk)
        g = res["griglia_phi"]["loso"][mk]["ll_con_phi"]
        pars = [GRID_EXT[i] for i in sc]
        nbordo = sum(1 for p in pars if p[0] >= PHI0S_EXT[-1] - 1e-9)
        ext[mk] = {"ll_esteso": float(ll_e.mean()), "ll_griglia_standard": float(g),
                   "delta": float(ll_e.mean() - g),
                   "parametri": [list(p) for p in pars],
                   "n_stagioni_sul_bordo_esteso": int(nbordo)}
        print(f"    {LAB[mk]:<18}{g:>12.4f}{ll_e.mean():>11.4f}{ll_e.mean()-g:>+11.5f}"
              f"   {' '.join(f'{p[0]:.2f}/{p[1]:.2f}' for p in pars)}")
    res["confutazione_griglia_estesa"] = ext

    # calibrazione grezza dei due mercati chiave (a phi=0): media prevista vs osservata
    cal = {}
    for mk in ("btts", "draw"):
        cal[mk] = {"p_media": float(q_by_theta[1.0][f"P_{mk}"].mean()),
                   "freq_osservata": float(y[mk].mean())}
    res["calibrazione_tau"] = cal
    print("\n  [calibrazione della matrice tau, phi=0]  " +
          "  ".join(f"{LAB[m]}: previsto {cal[m]['p_media']:.4f} vs osservato "
                    f"{cal[m]['freq_osservata']:.4f}" for m in cal))

    # ---------- (2) confronto diretto GRIGLIA vs MLE ------------------------- #
    print("\n  [griglia vs MLE, stesso protocollo LOSO]")
    cmp_ = {}
    print(f"    {'mercato':<18}{'MLE':>10}{'griglia':>10}{'delta':>11}"
          f"   (delta<0 = la griglia e' meglio)")
    for mk in ALL_MK:
        ll_mle = []
        for si, s in enumerate(seasons):
            idx = seasons_idx[si]
            phi0, kap = mle[s]
            phi = phi0 * np.exp(-kap * q_by_theta[1.0]["bal"])
            ll_mle.append(ll_market(q_by_theta[1.0], y, mk, phi)[idx])
        ll_mle = np.concatenate(ll_mle)
        g = res["griglia_phi"]["loso"][mk]["ll_con_phi"]
        cmp_[mk] = {"mle": float(ll_mle.mean()), "griglia": float(g),
                    "delta_griglia_meno_mle": float(g - ll_mle.mean())}
        print(f"    {LAB[mk]:<18}{ll_mle.mean():>10.4f}{g:>10.4f}"
              f"{g-ll_mle.mean():>+11.5f}")
    res["griglia_vs_mle"] = cmp_

    # ---------- (3) phi / theta / entrambi ----------------------------------- #
    if not quick:
        print(f"\n  [phi sola | theta solo | entrambi — griglia congiunta, "
              f"{len(THETAS)} theta x {len(GRID)} phi]")
        qs = [q_by_theta[t] for t in THETAS]
        Sj = somme_stagione(q_by_theta, y, seasons_idx, GRID, qs)
        combo = {}
        chiave = ["1X2", "btts", "draw", "over_2.5"]
        idx_theta1 = THETAS.index(1.0)
        # sottoinsiemi di griglia per le 3 varianti
        gi_phi = list(range(idx_theta1 * len(GRID), (idx_theta1 + 1) * len(GRID)))
        gi_theta = [t * len(GRID) + 0 for t in range(len(THETAS))]      # phi0=0
        gi_both = list(range(len(THETAS) * len(GRID)))
        gi_prov = [THETAS.index(THETA_PROV) * len(GRID) + 0]
        for modo in ("loso", "lfo"):
            print(f"\n  --- selettore {modo.upper()} ---")
            print(f"    {'mercato':<14}{'variante':<14}{'log-loss':>10}{'guadagno':>11}"
                  f"{'CI95':>22}  verdetto      parametri")
            blocco = {}
            for mk in chiave:
                riga = {}
                base_ll = None
                for nome, sub in (("phi_sola", gi_phi), ("theta_solo", gi_theta),
                                  ("entrambi", gi_both), ("theta_prov_1.20", gi_prov)):
                    sub = np.array(sub)
                    sc_sub = seleziona(Sj[mk][sub], n_per_season, modo)
                    sc = [int(sub[g]) if g >= 0 else -1 for g in sc_sub]
                    parts = valuta(q_by_theta, y, seasons_idx, GRID, THETAS, sc)
                    if not parts:
                        continue
                    ll = _ll_da_parts(parts, y, mk)
                    # riferimento: theta=1, phi=0, stesse stagioni
                    sc0 = [idx_theta1 * len(GRID) if g >= 0 else -1 for g in sc]
                    parts0 = valuta(q_by_theta, y, seasons_idx, GRID, THETAS, sc0)
                    ll0 = _ll_da_parts(parts0, y, mk)
                    if base_ll is None:
                        base_ll = ll0
                    v = verdetto(ll0 - ll, rng, k_tests=len(chiave) * 4)
                    pars = []
                    for g in sc:
                        if g < 0:
                            pars.append(None); continue
                        ti, gi = divmod(g, len(GRID))
                        pars.append([THETAS[ti], GRID[gi][0], GRID[gi][1]])
                    pstr = " ".join("-" if p is None else
                                    f"th{p[0]:.2f}/{p[1]:.2f}/{p[2]:.1f}" for p in pars)
                    print(f"    {LAB[mk]:<14}{nome:<14}{ll.mean():>10.4f}"
                          f"{v['guadagno']:>+11.5f}  [{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}]"
                          f"  {v['verdetto']:<12}  {pstr}")
                    riga[nome] = {"ll": float(ll.mean()), "ll_riferimento": float(ll0.mean()),
                                  "parametri_per_stagione": pars, **v}
                blocco[mk] = riga
            combo[modo] = blocco
        res["phi_theta_combo"] = combo

    # ---------- (4) GG/NG: ricalibrazione dei tassi + phi -------------------- #
    print("\n  [GG/NG — ricalibrazione moltiplicativa dei tassi + phi (theta=1)]")
    recal = {}
    mkgg = ["btts", "draw", "1X2", "over_2.5", "risultato_esatto"]
    varianti = ["lvl_mu", "lvl_both", "k34_mu"]
    for modo in ("loso", "lfo"):
        blocco = {}
        print(f"\n  --- selettore {modo.upper()} ---")
        print(f"    {'variante':<16}{'mercato':<18}{'ll':>10}{'guadagno vs tau':>17}"
              f"{'CI95':>22}  verdetto")
        for var in varianti:
            lam_r = np.zeros(len(df)); mu_r = np.zeros(len(df)); coef_log = []
            usabili = []
            for si, s in enumerate(seasons):
                if modo == "loso":
                    tr = np.concatenate([seasons_idx[j] for j in range(len(seasons)) if j != si])
                else:
                    if si == 0:
                        continue
                    tr = np.concatenate(seasons_idx[:si])
                idx = seasons_idx[si]; usabili.append(si)
                if var == "lvl_mu":
                    c = np.log(ag[tr].sum() / mu[tr].sum())
                    lam_r[idx] = lam[idx]; mu_r[idx] = mu[idx] * np.exp(c)
                    coef_log.append(float(np.exp(c)))
                elif var == "lvl_both":
                    ch = np.log(hg[tr].sum() / lam[tr].sum())
                    ca = np.log(ag[tr].sum() / mu[tr].sum())
                    lam_r[idx] = lam[idx] * np.exp(ch); mu_r[idx] = mu[idx] * np.exp(ca)
                    coef_log.append([float(np.exp(ch)), float(np.exp(ca))])
                else:
                    c = _fit_knee(mu[tr], ag[tr], df.matchday.to_numpy()[tr])
                    lam_r[idx] = lam[idx]
                    mu_r[idx] = mu[idx] * np.exp(_knee_basis(df.matchday.to_numpy()[idx]) @ c)
                    coef_log.append(float(np.exp(_knee_basis([38.0]) @ c)[0]))
            idx_ok = np.concatenate([seasons_idx[si] for si in usabili])
            qr = quantita(lam_r[idx_ok], mu_r[idx_ok], hg[idx_ok], ag[idx_ok], 1.0)
            yr = esiti(hg[idx_ok], ag[idx_ok])
            sidx_r = []
            off = 0
            for si in usabili:
                k_ = len(seasons_idx[si]); sidx_r.append(np.arange(off, off + k_)); off += k_
            npr = np.array([len(i) for i in sidx_r])
            Sr = somme_stagione({1.0: qr}, yr, sidx_r, GRID, [qr])
            for mk in mkgg:
                # senza phi
                ll_r = ll_market(qr, yr, mk, np.zeros(len(idx_ok)))
                ll_tau = ll_market(q_by_theta[1.0], y, mk, np.zeros(len(df)))[idx_ok]
                v = verdetto(ll_tau - ll_r, rng, k_tests=len(varianti) * len(mkgg) * 2)
                print(f"    {var:<16}{LAB[mk]:<18}{ll_r.mean():>10.4f}"
                      f"{v['guadagno']:>+17.5f}  [{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}]"
                      f"  {v['verdetto']}")
                blocco.setdefault(var, {})[mk] = {"ll": float(ll_r.mean()),
                                                  "ll_tau": float(ll_tau.mean()), **v}
                # con phi sopra la ricalibrazione (griglia, stesso selettore)
                sc = seleziona(Sr[mk], npr, modo)
                parts = valuta({1.0: qr}, yr, sidx_r, GRID, [1.0], sc)
                if not parts:
                    continue
                ll_rp = _ll_da_parts(parts, yr, mk)
                sel_idx = np.concatenate([sidx_r[i] for i, g in enumerate(sc) if g >= 0])
                v2 = verdetto(ll_tau[sel_idx] - ll_rp, rng,
                              k_tests=len(varianti) * len(mkgg) * 2)
                pars = [GRID[g] if g >= 0 else None for g in sc]
                print(f"    {var+'+phi':<16}{LAB[mk]:<18}{ll_rp.mean():>10.4f}"
                      f"{v2['guadagno']:>+17.5f}  [{v2['ci95'][0]:+.5f},{v2['ci95'][1]:+.5f}]"
                      f"  {v2['verdetto']}")
                blocco.setdefault(var + "+phi", {})[mk] = {
                    "ll": float(ll_rp.mean()), "ll_tau": float(ll_tau[sel_idx].mean()),
                    "parametri_per_stagione": [None if p is None else list(p) for p in pars],
                    **v2}
            blocco.setdefault("_coef", {})[var] = coef_log
        recal[modo] = blocco
    res["ricalibrazione_tassi"] = recal
    res["secondi"] = round(time.time() - t0, 1)
    print(f"\n  ({res['secondi']}s)")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    san = test_sanita()
    print("SANITA' della vettorizzazione (identita' (P+phi*D_S)/(1+phi*D) vs "
          "mi.score_matrix/derive_markets):")
    print(f"  errore massimo sulle probabilita': {san['max_err_prob_vs_score_matrix']:.2e}")
    print(f"  errore massimo su phi vs mi.balance_phi: {san['max_err_phi_vs_balance_phi']:.2e}")
    print(f"  -> {'OK' if san['ok'] else 'FALLITO'}")
    if not san["ok"]:
        return 1

    out = {"_meta": {"seed": SEED, "rho": RHO, "stagioni": SEASONS,
                     "griglia_phi0": PHI0S.tolist(), "griglia_kappa": KAPPAS.tolist(),
                     "n_punti_griglia_phi": len(GRID), "thetas": THETAS,
                     "theta_provvisorio": THETA_PROV, "bootstrap_B": 10000,
                     "sanita": san}}
    for lg in args.leagues:
        out[lg] = analizza_lega(lg, rng, args.quick)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
