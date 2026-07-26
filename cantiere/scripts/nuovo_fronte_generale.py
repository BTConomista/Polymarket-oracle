"""IL FRONTE GENERALE — esiste una versione UNICA cross-lega che batte il per-lega?

DOMANDA
-------
Il protocollo del progetto (CLAUDE.md §1.9) impone di sviluppare ogni modello su
DUE FRONTI: **per-lega** (costanti ritarate sul singolo campionato) e **generale**
(una versione unica, pooled, valida ovunque). Nessuno dei due e' giusto a priori.
Con cinque leghe la domanda si puo' finalmente misurare in modo pulito.

Due fatti freschi la rendono urgente:
  (a) lo stimatore della chiusura O/U, che il progetto usava POOLED per decisione
      ufficiale, con 5 leghe risulta MIGLIORE per-lega (CI conclusivo);
  (b) il θ del router si divide in due famiglie nette (≈1.24 in serie_a/la_liga,
      ≈1.08-1.10 in premier/bundesliga/ligue_1), che e' il contrario di un
      parametro universale.

IL PROTOCOLLO (identico per tutte e quattro le leve)
----------------------------------------------------
Per ogni lega L e ogni parametro p si confrontano DUE strategie, entrambe
onestamente fuori campione sulle righe di L su cui si misura:

  PER-LEGA   (leave-one-season-out DENTRO L): per la stagione s, p e' scelto sul
             log-loss delle ALTRE stagioni di L. Ogni riga di L e' di test.
  POOLED     (leave-one-league-out): p e' scelto sul log-loss delle ALTRE QUATTRO
             leghe (tutte le stagioni). Il pooled non vede MAI L.

Il confronto e' un bootstrap appaiato riga-per-riga su
    d = LL(pooled) − LL(per-lega)
(negativo = il fronte generale vince) con B = 10.000, CI95 esplicito e verdetto
CONCLUSIVO / nel rumore. Si riportano anche i due contro il RIFERIMENTO neutro
(θ=1, φ=0, ρ=−0.06, config Serie A) perche' "pareggiano" puo' voler dire
"nessuno dei due serve".

Due varianti in piu' del fronte generale, mai testate dal progetto:
  DUE-FAMIGLIE (oracolo)  θ pooled sulle sole leghe di training della STESSA
             famiglia di L, con la famiglia presa dal θ noto di L. E' PARZIALMENTE
             SPORCA (l'appartenenza di L usa i risultati di L) e va letta come un
             TETTO SUPERIORE, non come una strategia giocabile. Dichiarato.
  DUE-FAMIGLIE (onesto)   la famiglia (e, in alternativa, il valore di θ per
             regressione) e' predetta da una covariata di LEGA osservabile senza
             i risultati: il MARGINE mediano del book sulla chiusura 1X2. E' una
             ipotesi PRE-REGISTRATA dal progetto stesso (Fase 53: «la
             sotto-dispersione decresce con la liquidita' del mercato»), non
             pescata qui. La covariata di L usa solo le sue quote, mai i suoi gol.

MULTIPLE TESTING. Le leve sono 4 (θ, φ, ρ, DC) e i mercati per leva sono ≤ 25.
Ogni tabella dichiara il numero di test e riporta, oltre al CI95, la soglia di
Bonferroni sul numero di mercati della stessa famiglia.

FINESTRE
--------
  path MERCATO (θ, φ, ρ): stagioni 1920→2526 (7), righe con chiusura 1X2+O/U 2.5
      completa. E' la finestra standard del progetto (prima non esiste la
      chiusura O/U reale).
  path DC: test 2021→2526 (6 stagioni), walk-forward settimanale con
      `scripts/backtest.run_backtest` — la finestra standard del progetto.

CONTROLLI DI SANITA' (obbligatori, §CLAUDE.md)
----------------------------------------------
  * il θ MLE per lega deve riprodurre i numeri gia' pubblicati nel cantiere
    (serie_a 1.232, la_liga 1.242, premier 1.085, bundesliga 1.080, ligue_1 1.103);
  * il log-loss 1X2 del mercato a θ=1/φ=0 deve riprodurre i numeri del report 10
    (bundesliga 0.9744, ligue_1 0.9850);
  * il DC di riferimento deve riprodurre il tracer (bundesliga 0.9919,
    ligue_1 1.0041, serie_a 0.9797, premier 0.9831).
Se un controllo non torna, lo script lo dichiara e non nasconde il numero.

USO
---
  python cantiere/scripts/nuovo_fronte_generale.py dc-run     # griglia DC (lunga)
  python cantiere/scripts/nuovo_fronte_generale.py theta
  python cantiere/scripts/nuovo_fronte_generale.py phi
  python cantiere/scripts/nuovo_fronte_generale.py rho
  python cantiere/scripts/nuovo_fronte_generale.py dc         # analisi della griglia
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

OUT = ROOT / "cantiere" / "out" / "nuovo_fronte_generale.json"
SCRATCH = Path("/tmp/claude-0/-home-user-Polymarket-oracle/"
               "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad") / "fronte_generale"
SCRATCH.mkdir(parents=True, exist_ok=True)

LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
SNAP = {"serie_a": ROOT / "data", "premier_league": ROOT / "data",
        "la_liga": ROOT / "data", "bundesliga": ROOT / "cantiere" / "data",
        "ligue_1": ROOT / "cantiere" / "data"}

MKT_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526"]
DC_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
RHO_PROD = -0.06
SEED = 909
B_BOOT = 10_000

# Famiglie del θ (report 10 §2.1): la divisione e' un FATTO gia' misurato, non
# una scoperta di questo script. Serve solo alla variante "oracolo".
FAMIGLIA_ORACOLO = {"serie_a": "A", "la_liga": "A",
                    "premier_league": "B", "bundesliga": "B", "ligue_1": "B"}


# --------------------------------------------------------------------------- #
#  bootstrap appaiato — fonte unica del progetto
# --------------------------------------------------------------------------- #
def _boot_mat(d: np.ndarray, rng) -> np.ndarray:
    """Identico a `scripts/_fase52_common.boot` (stesso schema di ricampionamento
    con reinserimento, stesse B righe), ma a blocchi per non allocare una matrice
    B x n da 1 GB quando n e' quello delle 5 leghe insieme."""
    n = len(d)
    passo = max(1, min(B_BOOT, int(2e7 // max(n, 1))))
    out = np.empty(B_BOOT)
    for i in range(0, B_BOOT, passo):
        k = min(passo, B_BOOT - i)
        out[i:i + k] = d[rng.integers(0, n, (k, n))].mean(1)
    return out


def verdetto(d: np.ndarray, rng, k_tests: int = 1) -> dict:
    """d = LL(A) − LL(B) riga per riga. mean<0 ⇒ A e' MEGLIO di B.
    Ritorna delta, CI95, CI Bonferroni sul numero di test dichiarato, verdetto."""
    d = np.asarray(d, float)
    if not np.any(d):
        return {"delta": 0.0, "ci95": [0.0, 0.0], "ci_bonf": [0.0, 0.0],
                "p_due_code": 1.0, "n": int(len(d)), "verdetto": "identici"}
    m = _boot_mat(d, rng)
    lo, hi = float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
    a = 100.0 * (0.05 / k_tests) / 2.0
    blo, bhi = float(np.percentile(m, a)), float(np.percentile(m, 100 - a))
    p_neg = float((m < 0).mean())
    v = "A MEGLIO" if hi < 0 else ("B MEGLIO" if lo > 0 else "nel rumore")
    return {"delta": float(d.mean()), "ci95": [lo, hi], "ci_bonf": [blo, bhi],
            "p_due_code": float(2.0 * min(p_neg, 1.0 - p_neg)),
            "n": int(len(d)), "verdetto": v,
            "conclusivo_bonf": bool(bhi < 0 or blo > 0)}


# --------------------------------------------------------------------------- #
#  PATH MERCATO — dati, inversione, matrici, mercati
# --------------------------------------------------------------------------- #
def carica_mercato(league: str) -> pd.DataFrame:
    df = pd.read_csv(SNAP[league] / f"{league}_matches.csv",
                     dtype={"season": str}, parse_dates=["date"])
    df = df[df.season.isin(MKT_SEASONS)]
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    df = df.dropna(subset=need)
    return df.sort_values("date").reset_index(drop=True)


def inverti(df: pd.DataFrame, league: str, rho: float) -> tuple[np.ndarray, np.ndarray]:
    """(λ, μ) impliciti nella chiusura devigata, motore di produzione.
    Cache su scratch; per ρ = −0.06 riusa la cache gia' prodotta dal fronte θ."""
    from src.evaluation import metrics
    from src.models import market_implied as mi
    fp = SCRATCH / f"rates_{league}_rho{rho:+.3f}.csv"
    vecchia = (ROOT.parent / "x")  # placeholder, sostituita sotto
    alt = SCRATCH.parent / "theta_griglia" / f"rates_{league}_rho{rho:+.2f}.csv"
    for cand in (fp, alt):
        if cand.exists():
            c = pd.read_csv(cand)
            if len(c) == len(df):
                return c["lam"].to_numpy(), c["mu"].to_numpy()
    del vecchia
    lam = np.zeros(len(df)); mu = np.zeros(len(df))
    for i, r in enumerate(df.itertuples()):
        pH, pD, pA = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        pO, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam[i], mu[i] = mi.implied_lambda_mu(pH, pD, pA, pO, rho)
    pd.DataFrame({"lam": lam, "mu": mu}).to_csv(fp, index=False)
    return lam, mu


# ---- maschere dei mercati Tier 1 (stesse chiavi di mi.derive_markets) ------- #
def _masks():
    from src.models import market_implied as mi
    K = np.arange(mi.MAX_GOALS + 1)
    I, J = np.meshgrid(K, K, indexing="ij")
    T = I + J
    return {
        "home_win": I > J, "draw": I == J, "away_win": I < J,
        "dc_1x": I >= J, "dc_2x": J >= I,
        "over_0.5": T >= 1, "over_1.5": T >= 2, "over_2.5": T >= 3,
        "over_3.5": T >= 4, "over_4.5": T >= 5,
        "btts": (I >= 1) & (J >= 1),
        "home_ov_0.5": I >= 1, "home_ov_1.5": I >= 2,
        "away_ov_0.5": J >= 1, "away_ov_1.5": J >= 2,
        "odd_total": (T % 2) == 1,
        "home_by_2plus": (I - J) >= 2, "away_by_2plus": (J - I) >= 2,
        "cs_home": J == 0, "cs_away": I == 0,
        "wtn_home": (I >= 1) & (J == 0), "wtn_away": (J >= 1) & (I == 0),
    }


MASKS = _masks()
BIN_MK = [k for k in MASKS if k not in ("home_win", "away_win")] + ["home_win", "away_win"]
BIN_MK = list(MASKS)
CAT_MK = ["1X2", "multigol", "risultato_esatto"]
ALL_MK = BIN_MK + CAT_MK
# I mercati su cui il progetto decide: l'1X2 e' la metrica ufficiale, il risultato
# esatto e' la verosimiglianza congiunta (≡ MLE), gli altri tre sono i mercati
# derivati piu' citati. Sono il set PRIMARIO dichiarato prima di misurare.
PRIMARI = ["1X2", "risultato_esatto", "btts", "over_2.5", "draw"]


def esiti_bin(hg, ag) -> dict:
    K = {k: None for k in MASKS}
    tot = hg + ag
    K["home_win"] = hg > ag; K["draw"] = hg == ag; K["away_win"] = ag > hg
    K["dc_1x"] = hg >= ag; K["dc_2x"] = ag >= hg
    for t, name in ((1, "over_0.5"), (2, "over_1.5"), (3, "over_2.5"),
                    (4, "over_3.5"), (5, "over_4.5")):
        K[name] = tot >= t
    K["btts"] = (hg >= 1) & (ag >= 1)
    K["home_ov_0.5"] = hg >= 1; K["home_ov_1.5"] = hg >= 2
    K["away_ov_0.5"] = ag >= 1; K["away_ov_1.5"] = ag >= 2
    K["odd_total"] = (tot % 2) == 1
    K["home_by_2plus"] = (hg - ag) >= 2; K["away_by_2plus"] = (ag - hg) >= 2
    K["cs_home"] = ag == 0; K["cs_away"] = hg == 0
    K["wtn_home"] = (hg >= 1) & (ag == 0); K["wtn_away"] = (ag >= 1) & (hg == 0)
    return K


def ll_da_matrici(M: np.ndarray, hg, ag) -> dict[str, np.ndarray]:
    """log-loss per riga di ogni mercato del listino, dalle matrici (n,11,11)."""
    from src.models import market_implied as mi
    n = len(M); MAXG = mi.MAX_GOALS
    y = esiti_bin(hg, ag)
    out = {}
    for mk, msk in MASKS.items():
        p = np.clip((M * msk[None]).sum(axis=(1, 2)), 1e-15, 1 - 1e-15)
        yy = y[mk].astype(float)
        out[mk] = -(yy * np.log(p) + (1 - yy) * np.log(1 - p))
    pH = (M * MASKS["home_win"][None]).sum(axis=(1, 2))
    pD = (M * MASKS["draw"][None]).sum(axis=(1, 2))
    pA = (M * MASKS["away_win"][None]).sum(axis=(1, 2))
    P3 = np.column_stack([pH, pD, pA]); P3 = P3 / P3.sum(1, keepdims=True)
    y3 = np.where(hg > ag, 0, np.where(hg == ag, 1, 2))
    out["1X2"] = -np.log(np.clip(P3[np.arange(n), y3], 1e-15, None))
    tot = hg + ag
    K = np.arange(MAXG + 1); I, J = np.meshgrid(K, K, indexing="ij"); T = I + J
    bands = [T <= 1, (T >= 2) & (T <= 3), T >= 4]
    Pb = np.stack([(M * b[None]).sum(axis=(1, 2)) for b in bands], 1)
    Pb = Pb / Pb.sum(1, keepdims=True)
    ymg = np.where(tot <= 1, 0, np.where(tot <= 3, 1, 2))
    out["multigol"] = -np.log(np.clip(Pb[np.arange(n), ymg], 1e-15, None))
    hc = np.minimum(hg, MAXG); ac = np.minimum(ag, MAXG)
    out["risultato_esatto"] = -np.log(np.clip(M[np.arange(n), hc, ac], 1e-15, None))
    return out


# --------------------------------------------------------------------------- #
#  IL MOTORE DEL CONFRONTO: per-lega (LOSO) vs pooled (LOLO)
# --------------------------------------------------------------------------- #
def confronta(ll: dict, seasons: dict, valori: list, mercati: list,
              rng, extra_pooled=None) -> dict:
    """``ll[league][valore][mercato]`` = log-loss per riga.
    ``seasons[league]`` = array delle stagioni, allineato alle righe.

    Costruisce, per ogni lega e mercato:
      - PER-LEGA : LOSO dentro la lega;
      - POOLED   : LOLO (fit sulle altre 4 leghe intere);
      - varianti pooled aggiuntive passate in ``extra_pooled``
        (dict nome -> funzione(league, mercato) -> valore scelto);
      - RIFERIMENTO: il primo valore della lista (neutro).
    e i bootstrap appaiati pooled-vs-perlega, pooled-vs-rif, perlega-vs-rif.
    """
    ligas = list(ll)
    rif = valori[0]
    # media del log-loss per (lega, stagione, valore, mercato) — tutto il resto
    # si costruisce da qui.
    somme = {lg: {v: {m: {} for m in mercati} for v in valori} for lg in ligas}
    n_st = {lg: {} for lg in ligas}
    for lg in ligas:
        s = seasons[lg]
        for st in sorted(set(s)):
            idx = s == st
            n_st[lg][st] = int(idx.sum())
            for v in valori:
                for m in mercati:
                    somme[lg][v][m][st] = float(ll[lg][v][m][idx].sum())

    def media_su(leghe_stagioni, v, m):
        num = sum(somme[lg][v][m][st] for lg, st in leghe_stagioni)
        den = sum(n_st[lg][st] for lg, st in leghe_stagioni)
        return num / den

    res = {}
    K = len(mercati)
    for lg in ligas:
        st_lg = sorted(set(seasons[lg]))
        altre = [(l2, st) for l2 in ligas if l2 != lg for st in sorted(set(seasons[l2]))]
        res[lg] = {}
        for m in mercati:
            # --- PER-LEGA (LOSO) --------------------------------------------- #
            sel_pl = np.zeros(len(seasons[lg])); scelte_pl = {}
            for st in st_lg:
                tr = [(lg, s2) for s2 in st_lg if s2 != st]
                best = min(valori, key=lambda v: media_su(tr, v, m))
                scelte_pl[str(st)] = best
                cur = seasons[lg] == st
                sel_pl[cur] = ll[lg][best][m][cur]
            # --- POOLED (LOLO) ----------------------------------------------- #
            best_p = min(valori, key=lambda v: media_su(altre, v, m))
            sel_po = ll[lg][best_p][m]
            ref = ll[lg][rif][m]
            blk = {
                "per_lega": {"scelte": scelte_pl, "ll": float(sel_pl.mean())},
                "pooled": {"scelta": best_p, "ll": float(sel_po.mean())},
                "riferimento": {"valore": rif, "ll": float(ref.mean())},
                "pooled_vs_per_lega": verdetto(sel_po - sel_pl, rng, K),
                "pooled_vs_rif": verdetto(sel_po - ref, rng, K),
                "per_lega_vs_rif": verdetto(sel_pl - ref, rng, K),
            }
            for nome, fn in (extra_pooled or {}).items():
                v = fn(lg, m, media_su)
                if v is None:
                    continue
                sel_e = ll[lg][v][m]
                blk[nome] = {"scelta": v, "ll": float(sel_e.mean()),
                             "vs_per_lega": verdetto(sel_e - sel_pl, rng, K),
                             "vs_pooled": verdetto(sel_e - sel_po, rng, K)}
            res[lg][m] = blk
    return res


def pool_5_leghe(res: dict, ll: dict, seasons: dict, valori: list,
                 mercati: list, rng) -> dict:
    """Verdetto GLOBALE: concatena le differenze riga-per-riga delle 5 leghe.
    E' la risposta alla domanda «il fronte generale vince o perde», una volta
    sola invece che cinque."""
    ligas = list(ll); out = {}
    for m in mercati:
        dpl, dpo, dref_po, dref_pl = [], [], [], []
        for lg in ligas:
            st_lg = sorted(set(seasons[lg]))
            sel_pl = np.zeros(len(seasons[lg]))
            for st in st_lg:
                v = res[lg][m]["per_lega"]["scelte"][str(st)]
                cur = seasons[lg] == st
                sel_pl[cur] = ll[lg][v][m][cur]
            sel_po = ll[lg][res[lg][m]["pooled"]["scelta"]][m]
            ref = ll[lg][valori[0]][m]
            dpl.append(sel_pl); dpo.append(sel_po)
            dref_po.append(sel_po - ref); dref_pl.append(sel_pl - ref)
        A = np.concatenate(dpo); Bv = np.concatenate(dpl)
        out[m] = {"ll_pooled": float(A.mean()), "ll_per_lega": float(Bv.mean()),
                  "pooled_vs_per_lega": verdetto(A - Bv, rng, len(mercati)),
                  "pooled_vs_rif": verdetto(np.concatenate(dref_po), rng, len(mercati)),
                  "per_lega_vs_rif": verdetto(np.concatenate(dref_pl), rng, len(mercati))}
    return out


def salva(chiave: str, blocco) -> None:
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    prev[chiave] = blocco
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(prev, indent=2, default=str))
    print(f"  -> salvato in {OUT.name}: [{chiave}]", flush=True)


# --------------------------------------------------------------------------- #
#  PATH DC — griglia di config in walk-forward (la parte lunga)
# --------------------------------------------------------------------------- #
# Griglia dichiarata PRIMA di misurare: un asse alla volta attorno alla config
# ufficiale (§1.2 del CLAUDE.md). δ (prior neopromosse) e' tenuto FISSO a 0.23
# per non confonderlo con gli altri assi: e' gia' per-lega per costruzione e la
# sua ri-taratura e' stata misurata altrove (nel rumore su 5 leghe su 5).
DC_CONFIGS: dict[str, dict] = {
    "rif":        dict(half_life_days=365.0, shrinkage=1.5, shots_blend=0.75),
    "hl_730":     dict(half_life_days=730.0, shrinkage=1.5, shots_blend=0.75),
    "hl_180":     dict(half_life_days=180.0, shrinkage=1.5, shots_blend=0.75),
    "blend_0.50": dict(half_life_days=365.0, shrinkage=1.5, shots_blend=0.50),
    "shr_3.0":    dict(half_life_days=365.0, shrinkage=3.0, shots_blend=0.75),
    "blend_1.00": dict(half_life_days=365.0, shrinkage=1.5, shots_blend=1.00),
    "shr_0.5":    dict(half_life_days=365.0, shrinkage=0.5, shots_blend=0.75),
}
DC_DELTA = 0.23


def _dc_job(arg):
    league, season, nome = arg
    fp = SCRATCH / "dc" / f"{league}_{season}_{nome}.csv"
    if fp.exists():
        return (league, season, nome, "cache")
    fp.parent.mkdir(parents=True, exist_ok=True)
    from src.data import database
    _orig = database.snapshot_path

    def _sp(key="serie_a"):
        if key in nuove_leghe.NEW_LEAGUES:
            return ROOT / "cantiere" / "data" / f"{key}_matches.csv"
        return _orig(key)
    database.snapshot_path = _sp
    from backtest import run_backtest
    cfg = DC_CONFIGS[nome]
    t0 = time.time()
    df = run_backtest(league, season, cfg["half_life_days"],
                      shrinkage=cfg["shrinkage"], shots_blend=cfg["shots_blend"],
                      blend_signal="xg", promoted_prior=(DC_DELTA, DC_DELTA),
                      verbose=False)
    keep = ["date", "home_team", "away_team", "result", "home_goals", "away_goals",
            "m_home", "m_draw", "m_away", "m_over", "odds_home", "odds_draw",
            "odds_away", "odds_over25", "odds_under25"]
    keep = [c for c in keep if c in df.columns]
    df[keep].to_csv(fp, index=False)
    return (league, season, nome, f"{time.time()-t0:.0f}s")


def dc_run(jobs: int, leagues: list[str], configs: list[str]) -> None:
    tasks = [(lg, s, c) for c in configs for lg in leagues for s in DC_SEASONS]
    tasks = [t for t in tasks
             if not (SCRATCH / "dc" / f"{t[0]}_{t[1]}_{t[2]}.csv").exists()]
    print(f"griglia DC: {len(tasks)} run da fare "
          f"({len(configs)} config x {len(leagues)} leghe x {len(DC_SEASONS)} stagioni)",
          flush=True)
    if jobs > 1:
        with Pool(jobs) as pool:
            for r in pool.imap_unordered(_dc_job, tasks):
                print(f"  ok {r[0]:<15} {r[1]} {r[2]:<11} {r[3]}", flush=True)
    else:
        for t in tasks:
            r = _dc_job(t)
            print(f"  ok {r[0]:<15} {r[1]} {r[2]:<11} {r[3]}", flush=True)


# --------------------------------------------------------------------------- #
#  COVARIATA DI LEGA, osservabile SENZA i risultati
# --------------------------------------------------------------------------- #
def covariata_margine(df: pd.DataFrame) -> float:
    """Margine (overround) MEDIANO del book sulla chiusura 1X2:
        m = 1/quota_casa + 1/quota_pari + 1/quota_ospite − 1.
    Si calcola dalle sole QUOTE: nessun gol, nessun esito. E' la covariata
    PRE-REGISTRATA dal progetto stesso (Fase 53: «la sotto-dispersione decresce
    con la liquidita' del mercato»; il margine e' il proxy standard di
    illiquidita'). Usarla per predire θ su una lega mai vista e' lecito."""
    o = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    return float(np.median((1.0 / o).sum(1) - 1.0))


def stampa_tabella(res: dict, glob: dict, mercati: list, titolo: str) -> None:
    print(f"\n{'='*118}\n{titolo}\n{'='*118}")
    for m in mercati:
        print(f"\n  --- {m} ---")
        print(f"    {'lega':<16}{'per-lega':>10}{'pooled':>10}{'rif':>10}"
              f"{'Δ(pool−perlega)':>17}{'CI95':>24}  verdetto")
        for lg, blk in res.items():
            b = blk[m]; v = b["pooled_vs_per_lega"]
            print(f"    {lg:<16}{b['per_lega']['ll']:>10.4f}{b['pooled']['ll']:>10.4f}"
                  f"{b['riferimento']['ll']:>10.4f}{v['delta']:>+17.5f}"
                  f"  [{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}]  {v['verdetto']}")
        g = glob[m]["pooled_vs_per_lega"]
        print(f"    {'POOL 5 LEGHE':<16}{glob[m]['ll_per_lega']:>10.4f}"
              f"{glob[m]['ll_pooled']:>10.4f}{'':>10}{g['delta']:>+17.5f}"
              f"  [{g['ci95'][0]:+.5f},{g['ci95'][1]:+.5f}]  {g['verdetto']}")


# --------------------------------------------------------------------------- #
#  1 · θ POOLED
# --------------------------------------------------------------------------- #
THETAS = [round(1.0 + 0.025 * i, 3) for i in range(17)]      # 1.000 … 1.400
THETA_PRODUZIONE = 1.225        # costante del router v3, tarata sulla Serie A
# Numeri gia' pubblicati dal cantiere, da riprodurre (controllo di sanita').
SANITA_THETA_MLE = {"serie_a": 1.232, "la_liga": 1.242, "premier_league": 1.085,
                    "bundesliga": 1.080, "ligue_1": 1.103}
SANITA_LL_1X2 = {"bundesliga": 0.9744, "ligue_1": 0.9850}


def _carica_path_mercato(rho: float, thetas: list, mercati: list):
    """Ritorna (ll, seasons, dati) con ll[lega][θ][mercato] = LL per riga."""
    from scripts._fase52_common import dp_matrices
    ll = {}; seasons = {}; dati = {}
    for lg in LEAGUES:
        df = carica_mercato(lg)
        lam, mu = inverti(df, lg, rho)
        hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
        seasons[lg] = df.season.to_numpy()
        dati[lg] = {"df": df, "lam": lam, "mu": mu, "hg": hg, "ag": ag}
        ll[lg] = {}
        for t in thetas:
            M = dp_matrices(lam, mu, rho, t)
            d = ll_da_matrici(M, hg, ag)
            ll[lg][t] = {m: d[m] for m in mercati}
        print(f"  {lg:<16} {len(df):5d} partite, "
              f"{len(set(seasons[lg]))} stagioni, {len(thetas)} valori", flush=True)
    return ll, seasons, dati


def cmd_theta(args) -> int:
    from scripts._fase52_common import fit_theta
    rng = np.random.default_rng(SEED)
    t0 = time.time()
    print("ASPETTATIVA DICHIARATA PRIMA DI MISURARE\n"
          "  Il θ MLE si divide in due famiglie (≈1.24 vs ≈1.08). Mi aspetto quindi\n"
          "  che il POOLED su 5 leghe PERDA contro il per-lega, e che perda soprattutto\n"
          "  sulle due leghe estreme (serie_a/la_liga da un lato). Mi aspetto che il\n"
          "  pooled a DUE FAMIGLIE recuperi quasi tutto il divario. Se invece il pooled\n"
          "  pareggia, vuol dire che la valle di θ e' cosi' piatta che la scelta non\n"
          "  conta — e allora nemmeno il per-lega serve.\n")
    ll, seasons, dati = _carica_path_mercato(RHO_PROD, THETAS, ALL_MK)

    # ---------------- controlli di sanita' ---------------------------------- #
    san = {"theta_mle": {}, "ll_1x2_theta1": {}}
    for lg in LEAGUES:
        d = dati[lg]
        san["theta_mle"][lg] = float(fit_theta(d["lam"], d["mu"], d["hg"],
                                               d["ag"], RHO_PROD))
        san["ll_1x2_theta1"][lg] = float(ll[lg][1.0]["1X2"].mean())
    san["scarto_max_theta_mle"] = max(
        abs(san["theta_mle"][lg] - v) for lg, v in SANITA_THETA_MLE.items())
    san["scarto_max_ll_1x2"] = max(
        abs(san["ll_1x2_theta1"][lg] - v) for lg, v in SANITA_LL_1X2.items())
    san["ok"] = bool(san["scarto_max_theta_mle"] < 0.01
                     and san["scarto_max_ll_1x2"] < 0.001)
    print("\nCONTROLLO DI SANITA'")
    for lg in LEAGUES:
        rif = SANITA_THETA_MLE[lg]
        print(f"  θ MLE {lg:<16} mio {san['theta_mle'][lg]:.3f}  "
              f"pubblicato {rif:.3f}  scarto {san['theta_mle'][lg]-rif:+.4f}")
    for lg, v in SANITA_LL_1X2.items():
        print(f"  LL 1X2 (θ=1) {lg:<12} mio {san['ll_1x2_theta1'][lg]:.4f}  "
              f"pubblicato {v:.4f}  scarto {san['ll_1x2_theta1'][lg]-v:+.5f}")
    print(f"  -> {'OK' if san['ok'] else 'FALLITO'}")

    # ---------------- covariata di lega ------------------------------------- #
    cov = {lg: covariata_margine(dati[lg]["df"]) for lg in LEAGUES}
    print("\nCOVARIATA DI LEGA (margine mediano della chiusura 1X2, senza esiti)")
    for lg in sorted(cov, key=cov.get):
        print(f"  {lg:<16} margine {cov[lg]*100:5.2f}%   "
              f"θ MLE {san['theta_mle'][lg]:.3f}   famiglia-oracolo {FAMIGLIA_ORACOLO[lg]}")
    r_sp = float(pd.Series(cov).rank().corr(
        pd.Series(san["theta_mle"]).rank()))
    print(f"  correlazione di rango margine↔θ MLE: {r_sp:+.3f}  "
          f"(atteso POSITIVO se «θ decresce con la liquidita'»)")

    # ---------------- varianti del fronte generale --------------------------- #
    def f_produzione(lg, m, media_su):
        return min(THETAS, key=lambda t: abs(t - THETA_PRODUZIONE))

    def f_oracolo(lg, m, media_su):
        fam = FAMIGLIA_ORACOLO[lg]
        tr = [(l2, st) for l2 in LEAGUES
              if l2 != lg and FAMIGLIA_ORACOLO[l2] == fam
              for st in sorted(set(seasons[l2]))]
        return min(THETAS, key=lambda t: media_su(tr, t, m)) if tr else None

    def f_onesto(lg, m, media_su):
        """Famiglia predetta dalla COVARIATA, con la soglia imparata SOLO sulle
        4 leghe di training: si spaccano le 4 al loro mediano, si sceglie il θ
        del gruppo, e L va nel gruppo col centroide di covariata piu' vicino."""
        altre = [l2 for l2 in LEAGUES if l2 != lg]
        x = np.array([cov[l2] for l2 in altre])
        soglia = float(np.median(x))
        g_alto = [l2 for l2 in altre if cov[l2] >= soglia]
        g_basso = [l2 for l2 in altre if cov[l2] < soglia]
        if not g_alto or not g_basso:
            return None
        c_alto = np.mean([cov[l2] for l2 in g_alto])
        c_basso = np.mean([cov[l2] for l2 in g_basso])
        grp = g_alto if abs(cov[lg] - c_alto) <= abs(cov[lg] - c_basso) else g_basso
        tr = [(l2, st) for l2 in grp for st in sorted(set(seasons[l2]))]
        return min(THETAS, key=lambda t: media_su(tr, t, m))

    def f_regressione(lg, m, media_su):
        """θ predetto da una retta θ = a + b·margine fittata sui θ ottimi
        IN-SAMPLE delle 4 leghe di training, poi agganciato alla griglia."""
        altre = [l2 for l2 in LEAGUES if l2 != lg]
        y = []
        for l2 in altre:
            tr = [(l2, st) for st in sorted(set(seasons[l2]))]
            y.append(min(THETAS, key=lambda t: media_su(tr, t, m)))
        x = np.array([cov[l2] for l2 in altre]); y = np.array(y, float)
        if np.ptp(x) < 1e-12:
            return None
        b, a = np.polyfit(x, y, 1)
        pred = a + b * cov[lg]
        return min(THETAS, key=lambda t: abs(t - float(pred)))

    extra = {"pooled_produzione_1.225": f_produzione,
             "pooled_2fam_ORACOLO": f_oracolo,
             "pooled_2fam_onesto": f_onesto,
             "pooled_regressione_covariata": f_regressione}

    print("\ncalcolo dei confronti (bootstrap appaiato B=10.000)...", flush=True)
    res = confronta(ll, seasons, THETAS, ALL_MK, rng, extra)
    glob = pool_5_leghe(res, ll, seasons, THETAS, ALL_MK, rng)
    stampa_tabella(res, glob, PRIMARI, "θ — POOLED (leave-one-league-out) vs PER-LEGA "
                                       "(leave-one-season-out)")

    print("\n  --- le varianti del fronte generale, sul set primario ---")
    print(f"    {'lega':<16}{'mercato':<18}{'variante':<30}{'θ':>7}{'Δ vs per-lega':>15}"
          f"{'CI95':>24}  verdetto")
    for lg in LEAGUES:
        for m in PRIMARI:
            for nome in extra:
                b = res[lg][m].get(nome)
                if not b:
                    continue
                v = b["vs_per_lega"]
                print(f"    {lg:<16}{m:<18}{nome:<30}{b['scelta']:>7.3f}"
                      f"{v['delta']:>+15.5f}  [{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}]"
                      f"  {v['verdetto']}")

    salva("theta", {"_meta": {"griglia": THETAS, "mercati": ALL_MK,
                              "primari": PRIMARI, "rho": RHO_PROD,
                              "stagioni": MKT_SEASONS, "bootstrap_B": B_BOOT,
                              "seed": SEED, "secondi": round(time.time() - t0, 1)},
                    "sanita": san, "covariata_margine": cov,
                    "corr_rango_margine_theta": r_sp,
                    "per_lega": res, "pool_5_leghe": glob})
    return 0


# --------------------------------------------------------------------------- #
#  2 · φ(φ0, κ) POOLED
# --------------------------------------------------------------------------- #
PHI0S = [round(0.05 * i, 3) for i in range(21)]              # 0.00 … 1.00
KAPPAS = [round(0.25 * i, 3) for i in range(17)]             # 0.00 … 4.00
PHI_GRID = [(0.0, 0.0)] + [(p, k) for p in PHI0S if p > 0 for k in KAPPAS]
# la φ tocca solo la famiglia-esiti: i mercati puro-totale/marginale il router li
# prende dalla τ (mi._TAU_MARKETS). Set primario dichiarato: la famiglia-pareggio.
PHI_MK = ["1X2", "draw", "dc_1x", "dc_2x", "btts", "risultato_esatto", "over_2.5"]
PHI_PRIMARI = ["1X2", "draw", "btts", "dc_1x"]


def cmd_phi(args) -> int:
    rng = np.random.default_rng(SEED + 1)
    t0 = time.time()
    print("ASPETTATIVA DICHIARATA PRIMA DI MISURARE\n"
          "  La φ35 e' gia' bocciata sulle due leghe nuove e non conclusiva sulle tre\n"
          "  storiche; in Ligue 1 la selezione sceglie φ0 = 0 in ogni stagione. Mi\n"
          "  aspetto quindi che POOLED e PER-LEGA siano entrambi ~identici al\n"
          "  riferimento φ=0 e fra loro: un PAREGGIO che significa «la leva non c'e'»,\n"
          "  non «il fronte generale funziona». Se il pooled dovesse VINCERE, la lettura\n"
          "  sarebbe che il per-lega stava pescando rumore stagione per stagione.\n")
    from scripts._fase52_common import dp_matrices
    ll = {}; seasons = {}
    for lg in LEAGUES:
        df = carica_mercato(lg)
        lam, mu = inverti(df, lg, RHO_PROD)
        hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
        seasons[lg] = df.season.to_numpy()
        M = dp_matrices(lam, mu, RHO_PROD, 1.0)
        # identita' esatta: P_S(φ) = (P_S + φ·D_S)/(1 + φ·D)   (vedi leve_phi_griglia)
        diag = np.einsum("nii->ni", M)
        D = diag.sum(1)
        base = ll_da_matrici(M, hg, ag)          # solo per il controllo φ=0
        P = {}; DS = {}
        for mk in PHI_MK:
            if mk in MASKS:
                P[mk] = (M * MASKS[mk][None]).sum(axis=(1, 2))
                DS[mk] = diag[:, np.diag(MASKS[mk])].sum(1)
            elif mk == "1X2":
                pH = (M * MASKS["home_win"][None]).sum(axis=(1, 2))
                pA = (M * MASKS["away_win"][None]).sum(axis=(1, 2))
                P[mk] = np.where(hg > ag, pH, np.where(hg < ag, pA, D))
                DS[mk] = np.where(hg == ag, D, 0.0)
            else:                                 # risultato esatto
                n = len(M); hc = np.minimum(hg, 10); ac = np.minimum(ag, 10)
                cell = M[np.arange(n), hc, ac]
                P[mk] = cell; DS[mk] = np.where(hc == ac, cell, 0.0)
        y = esiti_bin(hg, ag)
        bal = np.abs(lam - mu)
        ll[lg] = {}
        for (p0, kap) in PHI_GRID:
            phi = np.zeros_like(bal) if p0 == 0 else p0 * np.exp(-kap * bal)
            den = 1.0 + phi * D
            blocco = {}
            for mk in PHI_MK:
                q = (P[mk] + phi * DS[mk]) / den
                if mk in MASKS:
                    q = np.clip(q, 1e-15, 1 - 1e-15); yy = y[mk].astype(float)
                    blocco[mk] = -(yy * np.log(q) + (1 - yy) * np.log(1 - q))
                else:
                    blocco[mk] = -np.log(np.clip(q, 1e-15, None))
            ll[lg][(p0, kap)] = blocco
        err = max(float(np.abs(ll[lg][(0.0, 0.0)][mk] - base[mk]).max())
                  for mk in PHI_MK)
        print(f"  {lg:<16} {len(df):5d} partite, griglia {len(PHI_GRID)} punti, "
              f"errore identita' vs matrice {err:.2e}", flush=True)

    res = confronta(ll, seasons, PHI_GRID, PHI_MK, rng)
    glob = pool_5_leghe(res, ll, seasons, PHI_GRID, PHI_MK, rng)
    stampa_tabella(res, glob, PHI_PRIMARI,
                   "φ(φ0,κ) — POOLED (leave-one-league-out) vs PER-LEGA (LOSO)")
    print("\n  --- parametri scelti ---")
    for m in PHI_PRIMARI:
        print(f"    {m}")
        for lg in LEAGUES:
            b = res[lg][m]
            print(f"      {lg:<16} pooled {str(b['pooled']['scelta']):<14} "
                  f"per-lega {list(b['per_lega']['scelte'].values())}")
    salva("phi", {"_meta": {"n_griglia": len(PHI_GRID), "phi0": PHI0S,
                            "kappa": KAPPAS, "mercati": PHI_MK,
                            "primari": PHI_PRIMARI, "stagioni": MKT_SEASONS,
                            "bootstrap_B": B_BOOT, "seed": SEED + 1,
                            "secondi": round(time.time() - t0, 1)},
                  "per_lega": res, "pool_5_leghe": glob})
    return 0


# --------------------------------------------------------------------------- #
#  3 · ρ POOLED  (oggi −0.06 FISSO per tutte le leghe, mai ri-tarato)
# --------------------------------------------------------------------------- #
RHOS = [round(-0.16 + 0.02 * i, 3) for i in range(10)]       # −0.16 … +0.02


def cmd_rho(args) -> int:
    rng = np.random.default_rng(SEED + 2)
    t0 = time.time()
    print("ASPETTATIVA DICHIARATA PRIMA DI MISURARE\n"
          "  ρ = −0.06 non e' mai stato ri-tarato: e' un numero ereditato. Sull'1X2 e\n"
          "  sull'O/U 2.5 mi aspetto ZERO differenza qualunque ρ, perche' l'inversione\n"
          "  ri-fitta (λ,μ) sulle STESSE probabilita' di mercato — ρ e' assorbito. La\n"
          "  differenza puo' esserci solo sui mercati DERIVATI (GG/NG, risultato esatto,\n"
          "  clean sheet). Se il pooled pareggia col per-lega, la struttura della matrice\n"
          "  e' universale e la costante ereditata regge: sarebbe una conferma, non un\n"
          "  non-risultato.\n")
    from scripts._fase52_common import dp_matrices
    ll = {lg: {} for lg in LEAGUES}; seasons = {}
    for lg in LEAGUES:
        df = carica_mercato(lg)
        hg = df.home_goals.to_numpy(int); ag = df.away_goals.to_numpy(int)
        seasons[lg] = df.season.to_numpy()
        for r in RHOS:
            lam, mu = inverti(df, lg, r)
            M = dp_matrices(lam, mu, r, 1.0)
            d = ll_da_matrici(M, hg, ag)
            ll[lg][r] = {m: d[m] for m in ALL_MK}
        print(f"  {lg:<16} {len(df):5d} partite x {len(RHOS)} ρ  "
              f"({time.time()-t0:.0f}s)", flush=True)

    # il riferimento deve essere ρ = −0.06 (il valore di produzione): lo metto
    # in testa alla lista dei valori, che `confronta` usa come riferimento.
    valori = [RHO_PROD] + [r for r in RHOS if r != RHO_PROD]
    res = confronta(ll, seasons, valori, ALL_MK, rng)
    glob = pool_5_leghe(res, ll, seasons, valori, ALL_MK, rng)
    stampa_tabella(res, glob, PRIMARI,
                   "ρ — POOLED (leave-one-league-out) vs PER-LEGA (LOSO); "
                   "riferimento ρ = −0.06 di produzione")
    print("\n  --- ρ scelti ---")
    for m in PRIMARI:
        print(f"    {m}")
        for lg in LEAGUES:
            b = res[lg][m]
            print(f"      {lg:<16} pooled {b['pooled']['scelta']:+.3f}  "
                  f"per-lega {list(b['per_lega']['scelte'].values())}  "
                  f"Δ pooled vs rif {b['pooled_vs_rif']['delta']:+.5f} "
                  f"[{b['pooled_vs_rif']['ci95'][0]:+.5f},"
                  f"{b['pooled_vs_rif']['ci95'][1]:+.5f}]")
    salva("rho", {"_meta": {"griglia": RHOS, "riferimento": RHO_PROD,
                            "mercati": ALL_MK, "primari": PRIMARI,
                            "stagioni": MKT_SEASONS, "bootstrap_B": B_BOOT,
                            "seed": SEED + 2,
                            "secondi": round(time.time() - t0, 1)},
                  "per_lega": res, "pool_5_leghe": glob})
    return 0


# --------------------------------------------------------------------------- #
#  4 · IPERPARAMETRI DEL DC
# --------------------------------------------------------------------------- #
SANITA_DC = {"bundesliga": 0.9919, "ligue_1": 1.0041, "serie_a": 0.9797,
             "premier_league": 0.9831}


def cmd_dc(args) -> int:
    rng = np.random.default_rng(SEED + 3)
    t0 = time.time()
    print("ASPETTATIVA DICHIARATA PRIMA DI MISURARE\n"
          "  Le curve di ri-taratura sono piatte su tutte e 5 le leghe (Fasi 8/57 e\n"
          "  tranche 3). Mi aspetto quindi un PAREGGIO fra pooled e per-lega, con una\n"
          "  leggera preferenza per il POOLED: se il segnale e' piatto, la selezione\n"
          "  per-lega su 5-6 stagioni pesca rumore mentre il pooled su ~10.000 partite\n"
          "  no. Se davvero il pooled vince, e' la prova diretta che gli iperparametri\n"
          "  del DC sono generali — che e' quello che il progetto gia' sostiene, ma per\n"
          "  argomento e non per misura.\n")
    base = SCRATCH / "dc"
    ll = {}; seasons = {}; disponibili = {}
    for lg in LEAGUES:
        blocchi = {}
        for c in DC_CONFIGS:
            fs = [base / f"{lg}_{s}_{c}.csv" for s in DC_SEASONS]
            if not all(f.exists() for f in fs):
                continue
            fr = []
            for s, f in zip(DC_SEASONS, fs):
                d = pd.read_csv(f); d["season"] = s
                fr.append(d)
            blocchi[c] = pd.concat(fr, ignore_index=True)
        if not blocchi:
            print(f"  {lg}: nessuna config completa, salto")
            continue
        disponibili[lg] = sorted(blocchi)
        rif = blocchi[sorted(blocchi)[0]]
        seasons[lg] = rif["season"].to_numpy()
        ll[lg] = {}
        for c, d in blocchi.items():
            p = d[["m_home", "m_draw", "m_away"]].to_numpy(float)
            p = p / p.sum(1, keepdims=True)
            y = np.where(d.result.to_numpy() == "H", 0,
                         np.where(d.result.to_numpy() == "D", 1, 2))
            l3 = -np.log(np.clip(p[np.arange(len(d)), y], 1e-15, None))
            over = ((d.home_goals + d.away_goals) >= 3).to_numpy(float)
            po = np.clip(d.m_over.to_numpy(float), 1e-15, 1 - 1e-15)
            lou = -(over * np.log(po) + (1 - over) * np.log(1 - po))
            ll[lg][c] = {"1X2": l3, "over_2.5": lou}
        print(f"  {lg:<16} {len(rif):5d} partite, config disponibili "
              f"{len(blocchi)}/{len(DC_CONFIGS)}: {sorted(blocchi)}", flush=True)

    comuni = sorted(set.intersection(*[set(v) for v in disponibili.values()]))
    print(f"\n  config presenti in TUTTE le leghe: {comuni}")
    if "rif" not in comuni or len(comuni) < 2:
        print("  griglia insufficiente: rieseguire `dc-run`.")
        return 1
    valori = ["rif"] + [c for c in comuni if c != "rif"]
    for lg in ll:
        ll[lg] = {c: ll[lg][c] for c in valori}

    san = {lg: float(ll[lg]["rif"]["1X2"].mean()) for lg in ll}
    print("\nCONTROLLO DI SANITA' (la config `rif` deve riprodurre il tracer)")
    for lg, v in SANITA_DC.items():
        if lg in san:
            print(f"  {lg:<16} mio {san[lg]:.4f}  pubblicato {v:.4f}  "
                  f"scarto {san[lg]-v:+.5f}")
    scarti = [abs(san[lg] - v) for lg, v in SANITA_DC.items() if lg in san]
    print(f"  -> scarto massimo {max(scarti):.5f} "
          f"({'OK' if max(scarti) < 0.002 else 'ATTENZIONE'})")
    print("  (nota: il tracer usa δ per-lega dove esiste; qui δ=0.23 ovunque per\n"
          "   non confondere l'asse δ con gli altri — piccoli scarti sono attesi)")

    mercati = ["1X2", "over_2.5"]
    res = confronta(ll, seasons, valori, mercati, rng)
    glob = pool_5_leghe(res, ll, seasons, valori, mercati, rng)
    stampa_tabella(res, glob, mercati,
                   "IPERPARAMETRI DC — POOLED (leave-one-league-out) vs PER-LEGA (LOSO)")
    print("\n  --- config scelte ---")
    for m in mercati:
        print(f"    {m}")
        for lg in ll:
            b = res[lg][m]
            print(f"      {lg:<16} pooled {b['pooled']['scelta']:<12} "
                  f"per-lega {list(b['per_lega']['scelte'].values())}")
    print("\n  --- la griglia grezza (log-loss 1X2 per config e lega) ---")
    print(f"    {'config':<12}" + "".join(f"{lg[:11]:>12}" for lg in ll))
    for c in valori:
        print(f"    {c:<12}" + "".join(f"{ll[lg][c]['1X2'].mean():>12.4f}" for lg in ll))
    salva("dc", {"_meta": {"config": {c: DC_CONFIGS[c] for c in valori},
                           "delta_fisso": DC_DELTA, "stagioni": DC_SEASONS,
                           "mercati": mercati, "bootstrap_B": B_BOOT,
                           "seed": SEED + 3, "secondi": round(time.time() - t0, 1)},
                 "sanita_ll_rif": san, "per_lega": res, "pool_5_leghe": glob})
    return 0


# --------------------------------------------------------------------------- #
#  5 · LA DOMANDA ARCHITETTURALE: 1 DC su 5 leghe insieme vs 5 DC separati
# --------------------------------------------------------------------------- #
# PREMESSA MATEMATICA (verificata riga per riga su src/models/dixon_coles.py,
# `_fit_counts`). La verosimiglianza del DC su insiemi di squadre DISGIUNTI e'
# una SOMMA di termini per lega:
#     ll = Σ_leghe Σ_partite [ g_h·log λ − λ + g_a·log μ − μ + log τ ],
#     λ = exp(att_h + dif_a + γ),   μ = exp(att_a + dif_h).
# Se γ e ρ fossero LIBERI per lega, il problema si spezzerebbe in 5 problemi
# indipendenti e il fit congiunto darebbe ESATTAMENTE i 5 fit separati: zero
# guadagno, per costruzione, non per misura. Nessuna squadra e' condivisa, quindi
# non c'e' informazione da trasferire.
# Quello che il fit congiunto fa DAVVERO nel codice esistente e' IMPORRE tre
# vincoli: un solo γ (vantaggio-casa), un solo ρ, e — per via del vincolo di
# identificabilita' `media(attacco)=0` GLOBALE piu' lo shrinkage verso 0 — un solo
# LIVELLO di gol, con le 5 leghe tirate verso la media comune. E' un modello
# strettamente piu' povero: puo' vincere solo se quei tre parametri sono davvero
# universali e la stima congiunta li rende meno rumorosi.
# E' esattamente la domanda del fronte generale, posta sull'architettura.
DC_POOL_SEASONS = ["2324", "2425", "2526"]


def _prep_leghe():
    from src.data import database
    _orig = database.snapshot_path

    def _sp(key="serie_a"):
        if key in nuove_leghe.NEW_LEAGUES:
            return ROOT / "cantiere" / "data" / f"{key}_matches.csv"
        return _orig(key)
    database.snapshot_path = _sp
    from src.data import loader
    from backtest import promoted_teams
    tutte = {}
    for lg in LEAGUES:
        d = loader.load_league(lg).copy()
        d["home_team"] = lg + "|" + d["home_team"].astype(str)
        d["away_team"] = lg + "|" + d["away_team"].astype(str)
        d["league"] = lg
        tutte[lg] = d
    return tutte, promoted_teams


def cmd_pool(args) -> int:
    from src.models.dixon_coles import DixonColesModel
    rng = np.random.default_rng(SEED + 4)
    t0 = time.time()
    print("ASPETTATIVA DICHIARATA PRIMA DI MISURARE\n"
          "  Il fit congiunto non puo' guadagnare informazione (squadre disgiunte):\n"
          "  puo' solo IMPORRE γ, ρ e livello comuni. γ e' notoriamente diverso per\n"
          "  lega (molto piu' forte in Liga) e i livelli di gol pure. Mi aspetto quindi\n"
          "  che il congiunto PERDA, e che perda soprattutto sulle leghe agli estremi\n"
          "  del vantaggio-casa. Se invece pareggia, vuol dire che γ e ρ sono cosi'\n"
          "  simili fra leghe che vincolarli non costa nulla.\n")
    tutte, promoted_teams = _prep_leghe()
    tutto = pd.concat(tutte.values(), ignore_index=True)
    cfg = DC_CONFIGS["rif"]
    righe = []
    par = {}
    for s in DC_POOL_SEASONS:
        for lg in LEAGUES:
            d = tutte[lg]
            test = d[d.season == s]
            if test.empty:
                continue
            as_of = test.date.min()
            promo_lg = {lg + "|" + t for t in
                        {x.split("|", 1)[1] for x in promoted_teams(d, s)}}
            promo_all = set()
            for l2 in LEAGUES:
                promo_all |= promoted_teams(tutte[l2], s)
            for arm, train, promo in (("separati", d, promo_lg),
                                      ("congiunto", tutto, promo_all)):
                m = DixonColesModel(half_life_days=cfg["half_life_days"],
                                    shrinkage=cfg["shrinkage"],
                                    shots_blend=cfg["shots_blend"],
                                    blend_signal="xg",
                                    promoted_prior=(DC_DELTA, DC_DELTA))
                m.fit(train, as_of_date=as_of, promoted_teams=promo)
                par[f"{arm}|{lg}|{s}"] = {"gamma": float(m.home_advantage),
                                          "rho": float(m.rho)}
                for r in test.itertuples():
                    p = m.predict_match(r.home_team, r.away_team)
                    righe.append({"season": s, "league": lg, "arm": arm,
                                  "res": ("H" if r.home_goals > r.away_goals else
                                          ("D" if r.home_goals == r.away_goals else "A")),
                                  "pH": p.prob_home_win, "pD": p.prob_draw,
                                  "pA": p.prob_away_win})
                print(f"  {s} {lg:<16} {arm:<10} γ={m.home_advantage:+.4f} "
                      f"ρ={m.rho:+.4f}  ({time.time()-t0:.0f}s)", flush=True)
    R = pd.DataFrame(righe)
    R.to_csv(SCRATCH / "pool_dc.csv", index=False)

    def ll(sub):
        p = sub[["pH", "pD", "pA"]].to_numpy(float)
        p = p / p.sum(1, keepdims=True)
        y = np.where(sub.res.to_numpy() == "H", 0,
                     np.where(sub.res.to_numpy() == "D", 1, 2))
        return -np.log(np.clip(p[np.arange(len(sub)), y], 1e-15, None))

    print(f"\n{'='*100}\n1 DC CONGIUNTO (5 leghe, γ/ρ/livello comuni) vs 5 DC SEPARATI"
          f"\n{'='*100}")
    print(f"  {'lega':<16}{'separati':>10}{'congiunto':>11}{'Δ(cong−sep)':>13}"
          f"{'CI95':>24}  verdetto")
    out = {}
    for lg in LEAGUES + ["TUTTE"]:
        a = R[R.arm == "separati"] if lg == "TUTTE" else R[(R.arm == "separati") & (R.league == lg)]
        b = R[R.arm == "congiunto"] if lg == "TUTTE" else R[(R.arm == "congiunto") & (R.league == lg)]
        a = a.sort_values(["season", "league"]).reset_index(drop=True)
        b = b.sort_values(["season", "league"]).reset_index(drop=True)
        if len(a) == 0:
            continue
        la, lb = ll(a), ll(b)
        v = verdetto(lb - la, rng, len(LEAGUES))
        out[lg] = {"ll_separati": float(la.mean()), "ll_congiunto": float(lb.mean()),
                   "n": int(len(a)), **v}
        print(f"  {lg:<16}{la.mean():>10.4f}{lb.mean():>11.4f}{v['delta']:>+13.5f}"
              f"  [{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}]  {v['verdetto']}")
    print("\n  --- γ (vantaggio-casa) e ρ stimati ---")
    print(f"    {'stagione':<10}{'lega':<16}{'γ separato':>12}{'γ congiunto':>13}"
          f"{'ρ separato':>12}{'ρ congiunto':>13}")
    for s in DC_POOL_SEASONS:
        for lg in LEAGUES:
            k1, k2 = f"separati|{lg}|{s}", f"congiunto|{lg}|{s}"
            if k1 in par:
                print(f"    {s:<10}{lg:<16}{par[k1]['gamma']:>12.4f}"
                      f"{par[k2]['gamma']:>13.4f}{par[k1]['rho']:>12.4f}"
                      f"{par[k2]['rho']:>13.4f}")
    salva("dc_congiunto", {"_meta": {"stagioni": DC_POOL_SEASONS, "config": cfg,
                                     "delta": DC_DELTA, "protocollo":
                                     "un fit per (lega, stagione) a inizio stagione, "
                                     "nessun re-fit settimanale: identico nei due bracci",
                                     "bootstrap_B": B_BOOT, "seed": SEED + 4,
                                     "secondi": round(time.time() - t0, 1)},
                           "parametri": par, "risultati": out})
    return 0


def cmd_sanita(args) -> int:
    """Solo i controlli di sanita', senza i bootstrap (veloce)."""
    from scripts._fase52_common import fit_theta
    ll, seasons, dati = _carica_path_mercato(RHO_PROD, [1.0], ALL_MK)
    for lg in LEAGUES:
        d = dati[lg]
        th = fit_theta(d["lam"], d["mu"], d["hg"], d["ag"], RHO_PROD)
        print(f"  {lg:<16} n={len(d['df']):5d}  θ MLE {th:.3f} "
              f"(pubblicato {SANITA_THETA_MLE[lg]:.3f})  "
              f"LL 1X2 {ll[lg][1.0]['1X2'].mean():.4f}  "
              f"margine {covariata_margine(d['df'])*100:.2f}%")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dc-run", "theta", "phi", "rho", "dc", "pool", "sanita"])
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--leagues", nargs="*", default=LEAGUES)
    ap.add_argument("--configs", nargs="*", default=list(DC_CONFIGS))
    args = ap.parse_args()

    if args.cmd == "dc-run":
        dc_run(args.jobs, args.leagues, args.configs)
        return 0
    fn = {"theta": cmd_theta, "phi": cmd_phi, "rho": cmd_rho, "dc": cmd_dc,
          "pool": cmd_pool, "sanita": cmd_sanita}[args.cmd]
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
