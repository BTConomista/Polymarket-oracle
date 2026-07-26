#!/usr/bin/env python3
"""Le leve di PANCHINA e le COVARIATE sul path Dixon-Coles standalone (senza
quote), portate per la prima volta fuori dalla Serie A: Bundesliga e Ligue 1.

Contesto: `cantiere/report/10_modelli_nuove_leghe.md` §8 punto 7 lascia aperto
esattamente questo fronte. Tutte le leve testate finora sulle due leghe nuove
stavano dal lato MERCATO (router θ, φ35 sul market-implied, devig, ricalibrazioni)
e sono risultate negative o nel rumore. Qui si guarda l'ALTRO motore: il DC
standalone, l'unico che funziona quando le quote non ci sono.

PARTE 1 — le quattro leve di panchina (tutte gia' in produzione, riusate):
  A. temperature scaling post-hoc      src/evaluation/calibration.fit_temperature
                                       protocollo di scripts/calibrate.py
  B. ricalibrazione per-classe 1X2     calibration.fit_class_recalibration
                                       protocollo di scripts/_run_class_recal.py
  C. diagonale inflazionata            run_backtest(draw_inflation=True)
  D. ensemble di emivite 180+730       protocollo di scripts/_run_ensemble.py

PARTE 2 — le covariate (rest_full, midweek, squad_value, absence), col
protocollo della Fase 79 (scripts/_run_fase79_leve_per_lega.py), PIU' la
variante nuova: le covariate di congestione RICOSTRUITE con i 3.045 calendari
di coppa recuperati (cantiere/data/ricerca/fixtures_*.csv) e mai integrati.
E' la prima volta che `midweek_europe` viene misurata su un calendario completo.

METODO (vincolante, CLAUDE.md + regole di sessione)
  - walk-forward settimanale via `scripts.backtest.run_backtest` (fonte unica);
  - finestra standard 6 stagioni di test 2020-21 → 2025-26;
  - config = Serie A PURA (nessuna ri-taratura per-lega: le curve sono piatte,
    report 06 §4), cosi' il riferimento e' il numero pubblicato
    (1X2 log-loss 0.9919 bundesliga / 1.0041 ligue_1);
  - ogni parametro di ogni leva e' scelto FUORI CAMPIONE (leave-future-out per
    A/B; nessun parametro libero per C/D che si fittano dentro il walk-forward
    sulle sole partite passate);
  - metriche dalla fonte unica `experiment_log.compute_metrics`; il log-loss
    per-partita usato dal bootstrap e' identico a `metrics.log_loss_1x2`
    (che ne e' la media) — verificato in `_sanity`;
  - bootstrap appaiato B=10.000 (stessa funzione di `scripts/_fase52_common.boot`)
    e verdetto esplicito CONCLUSIVO / nel rumore;
  - calibrazione (ECE + affidabilita' per classe) misurata PRIMA e DOPO ogni
    leva: una leva puo' non guadagnare in log-loss e raddrizzare la calibrazione.

ISOLAMENTO (R4): questo script LEGGE tutto e SCRIVE solo
  cantiere/out/leve_dc_panchina.json
piu' una cache di predizioni intermedie in una directory temporanea FUORI dal
repo (--cache, default nello scratchpad di sessione). Nessuno snapshot, nessun
file di produzione, nessun file di altri agenti viene toccato. Nessun git.

Uso:
    python cantiere/scripts/leve_dc_panchina.py --stage wf       # backtest (lungo)
    python cantiere/scripts/leve_dc_panchina.py --stage betas    # beta per stagione
    python cantiere/scripts/leve_dc_panchina.py --stage analyze  # -> JSON
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from src.config import SERIE_A                       # noqa: E402
from src.data import database, fixtures as fxmod, loader  # noqa: E402
from src.evaluation import calibration, experiment_log, metrics  # noqa: E402

OUT = ROOT / "cantiere" / "out" / "leve_dc_panchina.json"
CANTIERE_DATA = ROOT / "cantiere" / "data"
TRACER = ROOT / "cantiere" / "out"

# --------------------------------------------------------------------------- #
# Le due leghe nuove vivono nel cantiere: si dirotta il percorso dello snapshot
# senza toccare il codice di produzione (R4). Identico a tranche3_tracer.py.
# --------------------------------------------------------------------------- #
_orig_snapshot_path = database.snapshot_path


def _snapshot_path(league_key: str = "serie_a") -> Path:
    if league_key in nuove_leghe.NEW_LEAGUES:
        return CANTIERE_DATA / f"{league_key}_matches.csv"
    return _orig_snapshot_path(league_key)


database.snapshot_path = _snapshot_path

from backtest import run_backtest, promoted_teams     # noqa: E402
from src.models.dixon_coles import DixonColesModel    # noqa: E402

# --------------------------------------------------------------------------- #
# Costanti dell'esperimento
# --------------------------------------------------------------------------- #
LEAGUES = ["bundesliga", "ligue_1"]
TEST_SEASONS = ["2021", "2122", "2223", "2324", "2425", "2526"]
# Per le leve post-hoc A/B servono anche le stagioni-predizione precedenti, da
# cui si tara il parametro (protocollo di scripts/calibrate.py: pred_seasons =
# SEASONS[1:], MIN_PRIOR_SEASONS = 2 -> le prime 6 testabili sono le nostre).
PRIOR_SEASONS = ["1819", "1920"]
PRED_SEASONS = PRIOR_SEASONS + TEST_SEASONS
PC = ["m_home", "m_draw", "m_away"]
_IDX = {"H": 0, "D": 1, "A": 2}
B, SEED = 10_000, 4242

# Riferimento pubblicato (report 06 / cantiere/out/tranche3_tracer.json).
RIFERIMENTO = {"bundesliga": 0.9919, "ligue_1": 1.0041}

# Calendari di club: base (quelli usati per costruire gli snapshot) e nome del
# campionato "di casa" dentro il calendario.
FIXT = {
    "bundesliga": (CANTIERE_DATA / "club_fixtures_bundesliga.csv", "Bundesliga"),
    "ligue_1": (CANTIERE_DATA / "club_fixtures_ligue_1.csv", "Ligue 1"),
}

# Le varianti di walk-forward. Chiave -> kwargs extra di run_backtest.
# `_fix` = calendario di club RICOSTRUITO coi file recuperati.
VARIANTS: dict[str, dict] = {
    "base":               {},
    "draw_infl":          {"draw_inflation": True},
    "hl180":              {"_half_life": 180.0},
    "hl730":              {"_half_life": 730.0},
    "cov_rest_full":      {"covariates": ("rest_full",)},
    "cov_midweek":        {"covariates": ("midweek",)},
    "cov_squad_value":    {"covariates": ("squad_value",)},
    "cov_absence":        {"covariates": ("absence",)},
    "cov_rest_full_fix":  {"covariates": ("rest_full",), "_fix_fixtures": True},
    "cov_midweek_fix":    {"covariates": ("midweek",), "_fix_fixtures": True},
}

# Ordine di esecuzione: prima cio' che sblocca piu' risultati con meno costo.
JOB_ORDER = [
    ("base", PRIOR_SEASONS),          # sblocca A e B (leve post-hoc)
    ("draw_infl", TEST_SEASONS),      # leva C
    ("cov_midweek_fix", TEST_SEASONS),  # la covariata mai misurata bene
    ("cov_midweek", TEST_SEASONS),      # il suo controllo (calendario bucato)
    ("cov_rest_full_fix", TEST_SEASONS),
    ("cov_rest_full", TEST_SEASONS),
    ("hl180", TEST_SEASONS),          # leva D
    ("hl730", TEST_SEASONS),          # leva D
    ("cov_squad_value", TEST_SEASONS),
    ("cov_absence", TEST_SEASONS),
]


def cache_dir() -> Path:
    return Path(os.environ.get("LEVE_DC_CACHE", "/tmp/leve_dc_panchina_cache"))


# --------------------------------------------------------------------------- #
# Calendario di club ricostruito (i 3.045 file recuperati, mai integrati)
# --------------------------------------------------------------------------- #
def merged_fixtures(league: str) -> pd.DataFrame:
    """Calendario base + i file `fixtures_{lega}_*.csv` recuperati, deduplicati
    su (squadra, data, competizione). Stessa ricetta di
    `cantiere/scripts/stima_celle_residue.py` (blocco D5), che ha verificato che
    il SOLO calendario base riproduce esattamente le colonne dello snapshot."""
    cf, _ = FIXT[league]
    F = pd.read_csv(cf)
    F["date"] = pd.to_datetime(F["date"])
    cols = ["season", "team", "date", "competition", "home_away", "opponent"]
    add = []
    for f in sorted(glob.glob(str(CANTIERE_DATA / "ricerca" / f"fixtures_{league}_*.csv"))):
        t = pd.read_csv(f)
        t["date"] = pd.to_datetime(t["date"])
        add.append(t[cols])
    if not add:
        return F
    key = ["team", "date", "competition"]
    return pd.concat([F[cols]] + add, ignore_index=True).drop_duplicates(subset=key)


def base_fixtures(league: str) -> pd.DataFrame:
    cf, _ = FIXT[league]
    F = pd.read_csv(cf)
    F["date"] = pd.to_datetime(F["date"])
    return F


_orig_load_league = loader.load_league


def _patch_loader_fixed() -> None:
    """Sostituisce a runtime le 4 colonne di congestione con quelle ricalcolate
    sul calendario COMPLETO. Non tocca lo snapshot su disco (R4)."""
    cache: dict[str, pd.DataFrame] = {}

    def load_league_fixed(league_key: str = "serie_a", *a, **kw):
        df = _orig_load_league(league_key, *a, **kw)
        if league_key not in FIXT:
            return df
        if league_key not in cache:
            cache[league_key] = merged_fixtures(league_key)
        _, own = FIXT[league_key]
        return fxmod.add_rest_days_full(df, cache[league_key], own_competition=own)

    loader.load_league = load_league_fixed


# --------------------------------------------------------------------------- #
# Walk-forward (stage `wf`)
# --------------------------------------------------------------------------- #
def _worker(job):
    league, variant, season = job
    fp = cache_dir() / f"{league}__{variant}__{season}.csv"
    if fp.exists():
        return job, 0.0
    kw = dict(VARIANTS[variant])
    hl = kw.pop("_half_life", SERIE_A["half_life_days"])
    # I worker del Pool sono PERSISTENTI e ricevono job di varianti diverse: se
    # non si ripristinasse il loader, un job `_fix` contaminerebbe tutti i job
    # successivi dello stesso worker (compreso il suo stesso controllo). Si
    # riparte SEMPRE dal loader originale.
    loader.load_league = _orig_load_league
    if kw.pop("_fix_fixtures", False):
        _patch_loader_fixed()
    t0 = time.time()
    df = run_backtest(league, season, hl,
                      shrinkage=SERIE_A["shrinkage"],
                      shots_blend=SERIE_A["shots_blend"],
                      blend_signal=SERIE_A["blend_signal"],
                      promoted_prior=(SERIE_A["promoted_prior"],
                                      SERIE_A["promoted_prior"]),
                      verbose=False, **kw)
    df["season"] = season
    fp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    return job, time.time() - t0


def seed_cache_from_tracer() -> int:
    """Le predizioni `base` 2020-21→2025-26 esistono gia' (tracer della tranche
    3, stessa identica config): si riusano invece di ricalcolarle. La loro
    identita' col ricalcolo e' verificata da `_sanity` su una stagione."""
    n = 0
    for league in LEAGUES:
        src = TRACER / f"tracer_pred_{league}.csv"
        if not src.exists():
            continue
        d = pd.read_csv(src)
        for s in TEST_SEASONS:
            fp = cache_dir() / f"{league}__base__{s}.csv"
            if fp.exists():
                continue
            sub = d[d["test_season"].astype(str) == s].drop(columns=["test_season"])
            if sub.empty:
                continue
            fp.parent.mkdir(parents=True, exist_ok=True)
            sub.to_csv(fp, index=False)
            n += 1
    return n


def stage_wf(only: list[str] | None, jobs_limit: int | None) -> None:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    seeded = seed_cache_from_tracer()
    print(f"cache seed dal tracer: {seeded} stagioni-lega riusate", flush=True)
    jobs = []
    for variant, seasons in JOB_ORDER:
        if only and variant not in only:
            continue
        for league in LEAGUES:
            for s in seasons:
                fp = cache_dir() / f"{league}__{variant}__{s}.csv"
                if not fp.exists():
                    jobs.append((league, variant, s))
    if jobs_limit:
        jobs = jobs[:jobs_limit]
    print(f"{len(jobs)} walk-forward da eseguire (2 processi)", flush=True)
    t0 = time.time()
    with Pool(2) as pool:
        for i, (job, dt) in enumerate(pool.imap_unordered(_worker, jobs), start=1):
            print(f"  [{i}/{len(jobs)}] {job[0]:<11} {job[1]:<18} {job[2]}  "
                  f"{dt:5.1f}s  (tot {time.time()-t0:6.0f}s)", flush=True)
    print("stage wf completato.", flush=True)


# --------------------------------------------------------------------------- #
# Beta per stagione (stage `betas`)
# --------------------------------------------------------------------------- #
COV_FITS = {
    "rest_full": ("rest_full", False),
    "midweek": ("midweek", False),
    "rest_full_fix": ("rest_full", True),
    "midweek_fix": ("midweek", True),
    "squad_value": ("squad_value", False),
    "absence": ("absence", False),
}


def stage_betas() -> None:
    """Un fit a inizio-stagione per covariata: il SEGNO del β e la sua stabilita'
    sono il risultato principale (protocollo Fase 79 `_fitted_params`)."""
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    fp_out = cache_dir() / "betas.json"
    res = json.loads(fp_out.read_text()) if fp_out.exists() else {}
    cfg = dict(half_life_days=SERIE_A["half_life_days"], shrinkage=SERIE_A["shrinkage"],
               shots_blend=SERIE_A["shots_blend"], blend_signal=SERIE_A["blend_signal"],
               promoted_prior=(SERIE_A["promoted_prior"], SERIE_A["promoted_prior"]))
    for league in LEAGUES:
        res.setdefault(league, {})
        for name, (cov, fix) in COV_FITS.items():
            if name in res[league]:
                continue
            loader.load_league = _orig_load_league
            if fix:
                _patch_loader_fixed()
            all_m = loader.load_league(league)
            betas = []
            for s in TEST_SEASONS:
                cur = all_m[all_m["season"].astype(str) == s]
                as_of = cur["date"].min()
                prom = promoted_teams(all_m, s)
                m = DixonColesModel(covariates=(cov,), **cfg)
                m.fit(all_m, as_of_date=as_of, promoted_teams=prom)
                betas.append(float(m.beta[cov]))
            res[league][name] = betas
            print(f"  {league:<11} beta {name:<15} "
                  f"{['%+.4f' % v for v in betas]}", flush=True)
            fp_out.write_text(json.dumps(res, indent=2))
    loader.load_league = _orig_load_league
    print("stage betas completato.", flush=True)


# --------------------------------------------------------------------------- #
# Analisi
# --------------------------------------------------------------------------- #
def load_variant(league: str, variant: str, seasons: list[str]) -> pd.DataFrame | None:
    frames = []
    for s in seasons:
        fp = cache_dir() / f"{league}__{variant}__{s}.csv"
        if not fp.exists():
            return None
        d = pd.read_csv(fp, parse_dates=["date"])
        d["season"] = s
        frames.append(d)
    key = ["season", "date", "home_team", "away_team"]
    return (pd.concat(frames, ignore_index=True)
            .sort_values(key).reset_index(drop=True))


def ll_1x2(P: np.ndarray, outcomes) -> np.ndarray:
    """Log-loss per partita. La sua MEDIA e' esattamente metrics.log_loss_1x2."""
    P = np.clip(np.asarray(P, float), 1e-15, 1.0)
    y = np.array([_IDX[o] for o in outcomes])
    return -np.log(P[np.arange(len(y)), y])


def ll_bin(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d: np.ndarray, rng) -> tuple[float, float, float, float]:
    """CI95 appaiato su d = variante - riferimento (negativo = la variante
    migliora). Identica a scripts/_fase52_common.boot."""
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return (float(d.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m < 0).mean()))


def verdetto(lo: float, hi: float) -> str:
    if hi < 0:
        return "CONCLUSIVO: migliora"
    if lo > 0:
        return "CONCLUSIVO: peggiora"
    return "nel rumore"


def market_ll(df: pd.DataFrame) -> np.ndarray:
    ll = np.full(len(df), np.nan)
    for i, r in enumerate(df.itertuples()):
        if np.isfinite([r.odds_home, r.odds_draw, r.odds_away]).all():
            p = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
            ll[i] = -np.log(max(p[_IDX[r.result]], 1e-15))
    return ll


def calib(P: np.ndarray, outcomes, nbins: int = 10) -> dict:
    """Calibrazione delle 3N probabilita' 1X2 appiattite: ECE (media |p-freq|
    pesata sui bin di uguale ampiezza), MCE, e affidabilita' per classe."""
    P = np.asarray(P, float)
    Y = np.zeros_like(P)
    for i, o in enumerate(outcomes):
        Y[i, _IDX[o]] = 1.0
    p, y = P.ravel(), Y.ravel()
    edges = np.linspace(0.0, 1.0, nbins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, nbins - 1)
    ece = mce = 0.0
    for b in range(nbins):
        m = idx == b
        if not m.any():
            continue
        gap = abs(p[m].mean() - y[m].mean())
        ece += gap * m.mean()
        mce = max(mce, gap)
    return {
        "ECE": float(ece), "MCE": float(mce),
        "per_classe": {k: {"predetta": float(P[:, j].mean()),
                           "reale": float(Y[:, j].mean())}
                       for j, k in enumerate(["H", "D", "A"])},
    }


def _sanity(rng) -> dict:
    """Tre controlli di sanita' con un numero noto da riprodurre."""
    out = {}
    # 1) il riferimento pubblicato del progetto, dalla fonte unica delle metriche
    for league in LEAGUES:
        d = load_variant(league, "base", TEST_SEASONS)
        if d is None:
            continue
        m = experiment_log.compute_metrics(d)
        out[f"riferimento_1x2_{league}"] = {
            "atteso": RIFERIMENTO[league],
            "ricalcolato": round(float(m["x2_model_logloss"]), 6),
            "scarto": round(float(m["x2_model_logloss"]) - RIFERIMENTO[league], 8),
            "n_partite": int(len(d)),
            "mercato": round(float(m["x2_market_logloss"]), 6)}
        # 2) il log-loss per-partita del bootstrap ha come media la fonte unica
        out[f"identita_logloss_{league}"] = float(
            abs(ll_1x2(d[PC].to_numpy(), d["result"].tolist()).mean()
                - metrics.log_loss_1x2(d[PC].to_numpy(), d["result"].tolist())))
    # 3) il calendario di club BASE riproduce le colonne dello snapshot
    for league in LEAGUES:
        M = pd.read_csv(CANTIERE_DATA / f"{league}_matches.csv")
        M["date"] = pd.to_datetime(M["date"])
        _, own = FIXT[league]
        rec = fxmod.add_rest_days_full(M, base_fixtures(league), own_competition=own)
        out[f"calendario_base_riproduce_snapshot_{league}"] = bool(
            (rec.home_midweek_europe.values == M.home_midweek_europe.values).all()
            and (rec.away_midweek_europe.values == M.away_midweek_europe.values).all()
            and np.allclose(rec.home_rest_days_full.values,
                            M.home_rest_days_full.values, equal_nan=True))
    return out


def diagnosi_midweek() -> dict:
    """Quante righe della finestra di test sono affette dal difetto noto della
    covariata (coppe mancanti nel calendario di club)."""
    res = {}
    for league in LEAGUES:
        M = pd.read_csv(CANTIERE_DATA / f"{league}_matches.csv")
        M["date"] = pd.to_datetime(M["date"])
        _, own = FIXT[league]
        base = fxmod.add_rest_days_full(M, base_fixtures(league), own_competition=own)
        new = fxmod.add_rest_days_full(M, merged_fixtures(league), own_competition=own)
        per_season = {}
        for s in sorted(M["season"].astype(str).unique()):
            m = M["season"].astype(str).values == s
            falsi0 = int(((base.home_midweek_europe[m] == 0) & (new.home_midweek_europe[m] == 1)).sum()
                         + ((base.away_midweek_europe[m] == 0) & (new.away_midweek_europe[m] == 1)).sum())
            riposo = int(((base.home_rest_days_full[m] != new.home_rest_days_full[m])
                          | (base.away_rest_days_full[m] != new.away_rest_days_full[m])).sum())
            gare = int(m.sum())
            per_season[s] = {
                "partite": gare, "celle_midweek_da_0_a_1": falsi0,
                "quota_celle": round(falsi0 / (2 * gare), 4),
                "partite_con_riposo_diverso": riposo,
                "affetta": bool(falsi0 or riposo)}
        mtest = M["season"].astype(str).isin(TEST_SEASONS).values
        res[league] = {
            "per_stagione": per_season,
            "finestra_test": {
                "partite": int(mtest.sum()),
                "celle_midweek_da_0_a_1": int(
                    ((base.home_midweek_europe[mtest] == 0) & (new.home_midweek_europe[mtest] == 1)).sum()
                    + ((base.away_midweek_europe[mtest] == 0) & (new.away_midweek_europe[mtest] == 1)).sum()),
                "partite_con_riposo_diverso": int(
                    ((base.home_rest_days_full[mtest] != new.home_rest_days_full[mtest])
                     | (base.away_rest_days_full[mtest] != new.away_rest_days_full[mtest])).sum()),
                "stagioni_NON_affette": [s for s in TEST_SEASONS
                                         if not per_season.get(s, {}).get("affetta", True)]},
            "tasso_midweek_medio": {
                "base": round(float(np.mean([base.home_midweek_europe.values,
                                             base.away_midweek_europe.values])), 4),
                "ricostruito": round(float(np.mean([new.home_midweek_europe.values,
                                                    new.away_midweek_europe.values])), 4)},
        }
    return res


def confronto(league: str, base: pd.DataFrame, variante: pd.DataFrame,
              rng, nome: str) -> dict:
    """Δ log-loss 1X2 (e O/U) variante − base, bootstrap appaiato, calibrazione."""
    assert (base[["season", "home_team", "away_team"]].values
            == variante[["season", "home_team", "away_team"]].values).all(), \
        f"righe non allineate per {nome}"
    lb = ll_1x2(base[PC].to_numpy(), base["result"].tolist())
    lv = ll_1x2(variante[PC].to_numpy(), variante["result"].tolist())
    mean, lo, hi, p = boot(lv - lb, rng)
    ob = ll_bin(base["m_over"].to_numpy(), base["is_over"].to_numpy())
    ov = ll_bin(variante["m_over"].to_numpy(), variante["is_over"].to_numpy())
    omean, olo, ohi, op = boot(ov - ob, rng)
    per_stagione = {}
    for s in sorted(base["season"].unique()):
        m = (base["season"] == s).to_numpy()
        per_stagione[s] = {"base": round(float(lb[m].mean()), 5),
                           "variante": round(float(lv[m].mean()), 5),
                           "delta": round(float((lv - lb)[m].mean()), 5)}
    return {
        "nome": nome, "n_partite": int(len(base)),
        "x2_base": round(float(lb.mean()), 5),
        "x2_variante": round(float(lv.mean()), 5),
        "delta_1x2": round(mean, 6), "ci95": [round(lo, 6), round(hi, 6)],
        "P_migliora": round(p, 3), "verdetto": verdetto(lo, hi),
        "stagioni_migliorate": int(sum(v["delta"] < 0 for v in per_stagione.values())),
        "per_stagione": per_stagione,
        "ou_base": round(float(ob.mean()), 5), "ou_variante": round(float(ov.mean()), 5),
        "delta_ou": round(omean, 6), "ou_ci95": [round(olo, 6), round(ohi, 6)],
        "ou_verdetto": verdetto(olo, ohi), "ou_P_migliora": round(op, 3),
        "calibrazione_base": calib(base[PC].to_numpy(), base["result"].tolist()),
        "calibrazione_variante": calib(variante[PC].to_numpy(), variante["result"].tolist()),
    }


def leva_posthoc(league: str, kind: str, rng) -> dict | None:
    """Leve A e B: il parametro si tara SOLO sulle stagioni-predizione
    precedenti (leave-future-out) e si applica alla stagione di test."""
    preds = {}
    for s in PRED_SEASONS:
        fp = cache_dir() / f"{league}__base__{s}.csv"
        if not fp.exists():
            return None
        preds[s] = pd.read_csv(fp, parse_dates=["date"])
    rows, par = [], {}
    Pb, Pv, outc, seas = [], [], [], []
    for i, s in enumerate(PRED_SEASONS):
        if i < len(PRIOR_SEASONS):
            continue
        prior = pd.concat([preds[PRED_SEASONS[j]] for j in range(i)], ignore_index=True)
        df = preds[s]
        if kind == "temperature":
            T = calibration.fit_temperature(prior[PC].to_numpy(), prior["result"].tolist())
            newp = calibration.apply_temperature(df[PC].to_numpy(), T)
            par[s] = round(float(T), 4)
        else:
            w = calibration.fit_class_recalibration(prior[PC].to_numpy(),
                                                    prior["result"].tolist())
            newp = calibration.apply_class_recalibration(df[PC].to_numpy(), w)
            par[s] = [round(float(x), 4) for x in w]
        b = ll_1x2(df[PC].to_numpy(), df["result"].tolist())
        v = ll_1x2(newp, df["result"].tolist())
        rows.append({"stagione": s, "parametro": par[s],
                     "base": round(float(b.mean()), 5),
                     "variante": round(float(v.mean()), 5),
                     "delta": round(float((v - b).mean()), 5),
                     "n_prior": int(len(prior))})
        Pb.append(df[PC].to_numpy()); Pv.append(newp)
        outc += df["result"].tolist(); seas += [s] * len(df)
    Pb, Pv = np.vstack(Pb), np.vstack(Pv)
    lb, lv = ll_1x2(Pb, outc), ll_1x2(Pv, outc)
    mean, lo, hi, p = boot(lv - lb, rng)
    return {
        "protocollo": ("scripts/calibrate.py" if kind == "temperature"
                       else "scripts/_run_class_recal.py"),
        "n_partite": int(len(outc)),
        "x2_base": round(float(lb.mean()), 5), "x2_variante": round(float(lv.mean()), 5),
        "delta_1x2": round(mean, 6), "ci95": [round(lo, 6), round(hi, 6)],
        "P_migliora": round(p, 3), "verdetto": verdetto(lo, hi),
        "stagioni_migliorate": int(sum(r["delta"] < 0 for r in rows)),
        "per_stagione": rows,
        "calibrazione_base": calib(Pb, outc),
        "calibrazione_variante": calib(Pv, outc),
    }


def leva_ensemble(league: str, rng) -> dict | None:
    """Leva D: ensemble di emivite (protocollo scripts/_run_ensemble.py: si
    mescolano le PROBABILITA' 1X2 delle stesse righe). Nessun parametro
    fittato: il peso 50/50 e' fissato in anticipo."""
    P = {}
    for v, hl in (("hl180", 180.0), ("base", 365.0), ("hl730", 730.0)):
        d = load_variant(league, v, TEST_SEASONS)
        if d is None:
            return None
        P[hl] = d
    b = P[365.0]
    key = ["season", "home_team", "away_team"]
    for hl in (180.0, 730.0):
        assert (P[hl][key].values == b[key].values).all(), "righe non allineate"
    combos = {
        "singola 180g": P[180.0][PC].to_numpy(),
        "singola 730g": P[730.0][PC].to_numpy(),
        "ensemble 180+730 (50/50)": 0.5 * P[180.0][PC].to_numpy() + 0.5 * P[730.0][PC].to_numpy(),
        "ensemble 180+365+730 (1/3)": (P[180.0][PC].to_numpy() + b[PC].to_numpy()
                                       + P[730.0][PC].to_numpy()) / 3.0,
        "ensemble 365+730 (50/50)": 0.5 * b[PC].to_numpy() + 0.5 * P[730.0][PC].to_numpy(),
    }
    outc = b["result"].tolist()
    lb = ll_1x2(b[PC].to_numpy(), outc)
    res = {"x2_base_365g": round(float(lb.mean()), 5), "n_partite": int(len(b)),
           "varianti": {}}
    for name, Pv in combos.items():
        lv = ll_1x2(Pv, outc)
        mean, lo, hi, p = boot(lv - lb, rng)
        per_s = {s: round(float((lv - lb)[(b["season"] == s).to_numpy()].mean()), 5)
                 for s in sorted(b["season"].unique())}
        res["varianti"][name] = {
            "x2": round(float(lv.mean()), 5), "delta_1x2": round(mean, 6),
            "ci95": [round(lo, 6), round(hi, 6)], "P_migliora": round(p, 3),
            "verdetto": verdetto(lo, hi),
            "stagioni_migliorate": int(sum(v < 0 for v in per_s.values())),
            "per_stagione": per_s,
            "calibrazione": calib(Pv, outc)}
    res["calibrazione_base"] = calib(b[PC].to_numpy(), outc)
    return res


def confutazioni(rng) -> dict:
    """Prove esplicite per DEMOLIRE i risultati positivi (richiesta dell'utente).

    1) La T del temperature scaling e' davvero >1 sulle leghe nuove, o e' un
       artefatto della finestra CUMULATIVA su cui si tara? Si rifa' il fit
       IN-SAMPLE su ciascuna delle 6 stagioni di test, per tutte e 5 le leghe
       (le predizioni del tracer esistono gia'). Controllo di sanita' incluso:
       la Serie A deve restituire il T~0.94 pubblicato dal progetto (Fase 6).
    2) L'ensemble di emivite: il guadagno regge togliendo una stagione (LOSO)?
       E viene da una emivita migliore o dalla MEDIA? (se 180 e 730 da sole
       sono peggiori della base, il guadagno e' riduzione di varianza).
    3) squad_value ha il beta piu' stabile di tutti (6/6) e non guadagna:
       almeno aiuta nelle PRIME GIORNATE, dove i rating sono poco informati?
    """
    out: dict = {}

    all_leagues = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
    T_tab = {}
    for lg in all_leagues:
        fp = TRACER / f"tracer_pred_{lg}.csv"
        if not fp.exists():
            continue
        d = pd.read_csv(fp)
        per = {str(s): round(float(calibration.fit_temperature(
                   g[PC].to_numpy(), g["result"].tolist())), 4)
               for s, g in d.groupby("test_season")}
        T_tab[lg] = {
            "T_pooled_in_sample": round(float(calibration.fit_temperature(
                d[PC].to_numpy(), d["result"].tolist())), 4),
            "T_per_stagione": per,
            "stagioni_con_T_maggiore_di_1": int(sum(v > 1 for v in per.values())),
        }
    out["1_temperatura_in_sample_5_leghe"] = {
        "nota": "T>1 = modello SOVRA-confidente (apply_temperature usa p^(1/T)).",
        "controllo_di_sanita": "serie_a deve dare T~0.94 (Fase 6, PANCHINA.md voce 10)",
        "tabella": T_tab}

    ens: dict = {}
    for league in LEAGUES:
        P = {v: load_variant(league, v, TEST_SEASONS)
             for v in ("hl180", "base", "hl730")}
        if any(v is None for v in P.values()):
            continue
        b = P["base"]
        o = b["result"].tolist()
        e = 0.5 * P["hl180"][PC].to_numpy() + 0.5 * P["hl730"][PC].to_numpy()
        d = ll_1x2(e, o) - ll_1x2(b[PC].to_numpy(), o)
        loso = {}
        for s in TEST_SEASONS:
            m = (b["season"] != s).to_numpy()
            mean, lo, hi, _ = boot(d[m], rng)
            loso[f"senza_{s}"] = {"delta": round(mean, 6),
                                  "ci95": [round(lo, 6), round(hi, 6)],
                                  "verdetto": verdetto(lo, hi)}
        ens[league] = {"loso": loso,
                       "sottoinsiemi_con_segno_negativo":
                           f"{sum(v['delta'] < 0 for v in loso.values())}/{len(loso)}",
                       "per_match_delta": round(float(d.mean()), 6)}
    # pooled sulle due leghe (stessa leva, stesso protocollo)
    pool = []
    for league in LEAGUES:
        P = {v: load_variant(league, v, TEST_SEASONS)
             for v in ("hl180", "base", "hl730")}
        if any(v is None for v in P.values()):
            continue
        b = P["base"]
        o = b["result"].tolist()
        e = 0.5 * P["hl180"][PC].to_numpy() + 0.5 * P["hl730"][PC].to_numpy()
        pool.append(ll_1x2(e, o) - ll_1x2(b[PC].to_numpy(), o))
    if pool:
        d = np.concatenate(pool)
        mean, lo, hi, p = boot(d, rng)
        ens["pooled_2_leghe"] = {
            "n_partite": int(len(d)), "delta": round(mean, 6),
            "ci95": [round(lo, 6), round(hi, 6)], "P_migliora": round(p, 4),
            "p_due_code": round(2 * (1 - p), 4), "verdetto": verdetto(lo, hi),
            "bonferroni": {
                "n_test_pre_dichiarati": 8, "soglia": 0.00625,
                "supera": bool(2 * (1 - p) < 0.00625)}}
    out["2_ensemble_emivite_robustezza"] = ens

    sv: dict = {}
    for league in LEAGUES:
        b = load_variant(league, "base", TEST_SEASONS)
        v = load_variant(league, "cov_squad_value", TEST_SEASONS)
        if b is None or v is None:
            continue
        b = b.copy()
        b["giornata"] = b.groupby("season")["date"].rank(method="dense")
        d = (ll_1x2(v[PC].to_numpy(), b["result"].tolist())
             - ll_1x2(b[PC].to_numpy(), b["result"].tolist()))
        r = {}
        for tag, m in (("prime_5_giornate", (b.giornata <= 5).to_numpy()),
                       ("dalla_6a_in_poi", (b.giornata > 5).to_numpy())):
            mean, lo, hi, _ = boot(d[m], rng)
            r[tag] = {"n": int(m.sum()), "delta": round(mean, 6),
                      "ci95": [round(lo, 6), round(hi, 6)],
                      "verdetto": verdetto(lo, hi)}
        sv[league] = r
    out["3_squad_value_inizio_stagione"] = sv
    return out


def stage_analyze() -> None:
    rng = np.random.default_rng(SEED)
    res: dict = {
        "titolo": "Le leve di panchina e le covariate sul path Dixon-Coles "
                  "standalone, su Bundesliga e Ligue 1",
        "regola": "R4 isolamento: scrive solo cantiere/out/leve_dc_panchina.json; "
                  "nessun git; metriche dalla fonte unica experiment_log/metrics.",
        "impostazione": {
            "leghe": LEAGUES, "stagioni_test": TEST_SEASONS,
            "stagioni_taratura_leve_posthoc": PRIOR_SEASONS,
            "config": {k: SERIE_A[k] for k in SERIE_A},
            "config_nota": "config Serie A PURA, non ri-tarata: e' il riferimento "
                           "pubblicato (report 06, curve di taratura piatte)",
            "bootstrap": {"B": B, "seed": SEED, "tipo": "appaiato per-partita"},
            "riferimento_pubblicato_1x2": RIFERIMENTO},
        "aspettative_dichiarate_prima": {
            "A_temperature": "il DC ha log-loss PEGGIORE sulle leghe nuove: se il "
                             "peggioramento fosse sovra-confidenza, T>1. Ma in Serie A "
                             "T~0.94 (SOTTO-confidenza): mi aspetto T<1 anche qui e un "
                             "guadagno dell'ordine di -0.0003, cioe' NEL RUMORE.",
            "B_class_recal": "in Serie A il bias per classe (casa alta, pareggio basso) "
                             "e' robusto. Bundesliga e' 'latina' sul draw-bias di mercato "
                             "(w_D=1.089) e Ligue 1 'inglese' (0.981): mi aspetto w_D>1 in "
                             "Bundesliga e w_D~1 o <1 in Ligue 1, guadagno nel rumore.",
            "C_draw_inflation": "il blocco precedente ha mostrato che una phi COSTANTE fa "
                                "meglio della phi(|lam-mu|): questa e' la phi costante sul "
                                "path DC. E' la leva con la probabilita' a priori piu' alta "
                                "delle quattro. In Ligue 1 pero' la selezione della phi35 "
                                "sceglieva phi0=0 in 7/7 stagioni (nessun deficit di "
                                "pareggi): li' mi aspetto ~0.",
            "D_ensemble": "in Serie A -0.0006 in 4/6 stagioni, borderline. Nessun motivo "
                          "per cui debba replicarsi: mi aspetto nel rumore.",
            "covariate": "NEGATIVA. Il progetto le ha bocciate su 3 leghe su 3. Le due "
                         "cose che rendono il test non inutile: il calendario di club delle "
                         "leghe nuove e' appena stato costruito, e la Bundesliga ha 18 "
                         "squadre (meno congestione di campionato, piu' coppa).",
            "midweek_ricostruito": "il difetto noto (coppe mancanti) rende la covariata "
                                   "RUMOROSA, non sbagliata in una direzione: correggerla "
                                   "dovrebbe rendere il beta piu' netto e piu' stabile, non "
                                   "necessariamente far guadagnare log-loss."},
    }
    res["controllo_di_sanita"] = _sanity(rng)
    res["diagnosi_covariata_midweek"] = diagnosi_midweek()

    fp_b = cache_dir() / "betas.json"
    betas = json.loads(fp_b.read_text()) if fp_b.exists() else {}

    p1: dict = {}
    for league in LEAGUES:
        base = load_variant(league, "base", TEST_SEASONS)
        if base is None:
            continue
        mkt = market_ll(base)
        p1.setdefault("_mercato", {})[league] = round(float(np.nanmean(mkt)), 5)
        for kind, code in (("temperature", "A_temperature_scaling"),
                           ("class", "B_ricalibrazione_per_classe")):
            r = leva_posthoc(league, kind, rng)
            if r:
                p1.setdefault(code, {})[league] = r
        d = load_variant(league, "draw_infl", TEST_SEASONS)
        if d is not None:
            p1.setdefault("C_diagonale_inflazionata", {})[league] = confronto(
                league, base, d, rng, "draw_inflation")
        e = leva_ensemble(league, rng)
        if e:
            p1.setdefault("D_ensemble_emivite", {})[league] = e
    res["parte1_leve_panchina"] = p1

    p2: dict = {}
    for league in LEAGUES:
        base = load_variant(league, "base", TEST_SEASONS)
        if base is None:
            continue
        for variant in ("cov_rest_full", "cov_midweek", "cov_squad_value",
                        "cov_absence", "cov_rest_full_fix", "cov_midweek_fix"):
            d = load_variant(league, variant, TEST_SEASONS)
            if d is None:
                continue
            r = confronto(league, base, d, rng, variant)
            bkey = variant.replace("cov_", "")
            r["beta_per_stagione"] = betas.get(league, {}).get(bkey)
            if r["beta_per_stagione"]:
                bs = r["beta_per_stagione"]
                r["beta_media"] = round(float(np.mean(bs)), 5)
                r["beta_segno_stabile"] = f"{max(sum(b < 0 for b in bs), sum(b > 0 for b in bs))}/{len(bs)}"
            p2.setdefault(variant, {})[league] = r
        # confronto diretto covariata bucata vs ricostruita
        for a, b in (("cov_midweek", "cov_midweek_fix"),
                     ("cov_rest_full", "cov_rest_full_fix")):
            da, db = load_variant(league, a, TEST_SEASONS), load_variant(league, b, TEST_SEASONS)
            if da is None or db is None:
                continue
            p2.setdefault(f"{b}_VS_{a}", {})[league] = confronto(
                league, da, db, rng, f"{b} vs {a}")
    res["parte2_covariate"] = p2
    res["confutazioni"] = confutazioni(rng)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, default=str))
    print(f"-> {OUT}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["wf", "betas", "analyze"], required=True)
    ap.add_argument("--only", nargs="*", default=None,
                    help="limita lo stage wf ad alcune varianti")
    ap.add_argument("--jobs-limit", type=int, default=None)
    args = ap.parse_args()
    cache_dir().mkdir(parents=True, exist_ok=True)
    if args.stage == "wf":
        stage_wf(args.only, args.jobs_limit)
    elif args.stage == "betas":
        stage_betas()
    else:
        stage_analyze()
    return 0


if __name__ == "__main__":
    sys.exit(main())
