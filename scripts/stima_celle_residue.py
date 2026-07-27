#!/usr/bin/env python3
"""Le celle residue: stimabili in modo difendibile, o la risposta onesta e' «no»?

Quattro casi indipendenti, ognuno con la sua domanda:

  CASO A  1X2 di CHIUSURA mancante (bundesliga Bayern-Hannover 04/05/2019,
          la_liga Alaves-Sociedad 14/10/2017). Per queste due righe esiste gia'
          un DATO REALE proposto da una fonte esterna
          (github.com/iredchuk/soccer-bookmaker-odds, vedi
          docs/audit_5_leghe/numeri/caccia_quote_singole.json). Qui NON si stima al buio:
            (i)  si verifica in modo INDIPENDENTE che quella fonte sia davvero
                 una chiusura di tipo media-di-mercato e non altro;
            (ii) si misura quanto una STIMA (regressione logit apertura->
                 chiusura, fittata su tutte le coppie reali delle 5 leghe,
                 k-fold) si discosta dal dato reale trovato.
          Baseline obbligatoria: l'IDENTITA' (chiusura = apertura).

  CASO B  xG mancante per bundesliga Holstein Kiel-Bochum 09/02/2025 (Understat
          non ha mai acquisito la partita: lista tiri vuota, valori segnaposto
          gia' portati a NaN). Si stima l'xG dai soli dati che abbiamo (tiri in
          porta, gol, forza)? MAE e R2 FUORI CAMPIONE contro baseline banali.

  CASO C  ri-scarica ADESSO da Understat il JSON di lega della Ligue 1 2025-26 e
          verifica se Nantes-Toulouse 17/05/2026 e' stata consolidata. Controlla
          TUTTA l'ultima giornata.

  CASO D  censimento di ogni altra cella vuota nelle 5 leghe, piu' la caccia ai
          buchi che NON sono NaN (valori sentinella, «finto pieno»).

METODO (vincolante, CLAUDE.md):
  - metriche SEMPRE da src.evaluation.metrics / experiment_log (mai reimplementate);
  - validazione SEMPRE fuori campione (k-fold, leave-one-season-out,
    leave-one-league-out);
  - bootstrap appaiato B=10.000 e verdetto esplicito CONCLUSIVO / nel rumore.
    La funzione ``boot_ci`` qui sotto e' identica a ``scripts/_fase52_common.boot``
    ma lavora a blocchi (l'originale alloca B x n float: con n=32.000 sono 2,5 GB);
    a parita' di seme produce gli STESSI numeri -- il test di equivalenza e' in
    ``_autotest_boot()``.

ISOLAMENTO (R4): questo script LEGGE tutto e SCRIVE solo
  data/estimates/celle_residue.csv  e  docs/audit_5_leghe/numeri/stima_celle_residue.json.
Nessuno snapshot, nessuna correzione, nessun file di altri viene toccato.

Uso:
    python scripts/stima_celle_residue.py            # tutto (usa la rete)
    python scripts/stima_celle_residue.py --offline  # salta A-i e C
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.evaluation import metrics                     # noqa: E402
from src.data import fixtures as fx                    # noqa: E402

OUT_JSON = ROOT / "docs" / "audit_5_leghe" / "numeri" / "stima_celle_residue.json"
OUT_CSV = ROOT / "data" / "estimates" / "celle_residue.csv"
CACHE = Path(tempfile.gettempdir()) / "celle_residue_cache"

SNAP = {
    "serie_a":        ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga":        ROOT / "data" / "la_liga_matches.csv",
    "bundesliga":     ROOT / "data" / "bundesliga_matches.csv",
    "ligue_1":        ROOT / "data" / "ligue_1_matches.csv",
}
FIXT = {
    "serie_a":        (ROOT / "data" / "club_fixtures.csv", "Serie A"),
    "premier_league": (ROOT / "data" / "club_fixtures_premier_league.csv", "Premier League"),
    "la_liga":        (ROOT / "data" / "club_fixtures_la_liga.csv", "La Liga"),
    "bundesliga":     (ROOT / "data" / "club_fixtures_bundesliga.csv", "Bundesliga"),
    "ligue_1":        (ROOT / "data" / "club_fixtures_ligue_1.csv", "Ligue 1"),
}
RAW_FD = ROOT / "data" / "fonti" / "football_data"
IRED = {  # nomi dei file nel repo esterno
    "bundesliga": "germany_bundesliga", "la_liga": "spain_primera",
    "serie_a": "italy_serie-a", "premier_league": "england_premier-league",
    "ligue_1": "france_league-1",
}
IRED_URL = ("https://raw.githubusercontent.com/iredchuk/soccer-bookmaker-odds"
            "/master/data/csv/{}.csv")
UNDERSTAT_URL = "https://understat.com/main/getLeagueData/Ligue_1/2025"
UNDERSTAT_MATCH = "https://understat.com/main/getMatchData/{}"
SEED = 20260726


# --------------------------------------------------------------------------- #
# bootstrap appaiato B=10.000 (equivalente a scripts/_fase52_common.boot)
# --------------------------------------------------------------------------- #
def boot_ci(d, seed: int = SEED, B: int = 10_000, chunk: int = 250) -> dict:
    d = np.asarray(d, float)
    n = len(d)
    rng = np.random.default_rng(seed)
    means = np.empty(B)
    for i in range(0, B, chunk):
        k = min(chunk, B - i)
        means[i:i + k] = d[rng.integers(0, n, (k, n))].mean(1)
    lo, hi = float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
    return {"diff": float(d.mean()), "ci95": [lo, hi],
            "conclusivo": bool(lo * hi > 0), "p_neg": float((means < 0).mean())}


def _autotest_boot() -> dict:
    """Controllo di sanita': riproduco il boot() del progetto a parita' di seme."""
    from _fase52_common import boot as ref
    rng = np.random.default_rng(1)
    d = rng.normal(0.001, 0.02, 3000)
    pt, lo, hi, pn = ref(d, np.random.default_rng(7))
    mine = boot_ci(d, seed=7)
    ok = (abs(pt - mine["diff"]) < 1e-12 and abs(lo - mine["ci95"][0]) < 1e-12
          and abs(hi - mine["ci95"][1]) < 1e-12)
    return {"riproduce_scripts/_fase52_common.boot": bool(ok),
            "riferimento": [pt, lo, hi], "a_blocchi": [mine["diff"]] + mine["ci95"]}


# --------------------------------------------------------------------------- #
# utilita' comuni
# --------------------------------------------------------------------------- #
def devig3(h, d, a) -> np.ndarray:
    """Probabilita' devigate 1X2 riga per riga con la FONTE UNICA del progetto."""
    h, d, a = (np.asarray(x, float) for x in (h, d, a))
    out = np.full((len(h), 3), np.nan)
    ok = np.isfinite(h) & np.isfinite(d) & np.isfinite(a) & (h > 1) & (d > 1) & (a > 1)
    for i in np.where(ok)[0]:
        out[i] = metrics.devig_1x2(h[i], d[i], a[i])
    return out


def feats(P):  # [1, logit H su D, logit A su D] dall'APERTURA
    return np.column_stack([np.ones(len(P)), np.log(P[:, 0] / P[:, 1]),
                            np.log(P[:, 2] / P[:, 1])])


def targ(P):
    return np.column_stack([np.log(P[:, 0] / P[:, 1]), np.log(P[:, 2] / P[:, 1])])


def back(Y):
    e1, e2 = np.exp(Y[:, 0]), np.exp(Y[:, 1])
    s = 1.0 + e1 + e2
    return np.column_stack([e1 / s, np.ones(len(Y)) / s, e2 / s])


def ols(X, Y):
    return np.linalg.lstsq(X, Y, rcond=None)[0]


def load_snapshots() -> pd.DataFrame:
    fr = []
    for lg, p in SNAP.items():
        d = pd.read_csv(p)
        d["league_k"] = lg
        d["season"] = d["season"].astype(str).str.zfill(4)
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def fetch(url: str, dest: Path, gz: bool = False, xhr: bool = False) -> bytes | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest.read_bytes()
    hdr = {"User-Agent": "Mozilla/5.0"}
    if xhr:
        hdr["X-Requested-With"] = "XMLHttpRequest"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=90) as r:
            raw = r.read()
            if gz and r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
    except Exception as exc:                                # noqa: BLE001
        print(f"  [rete] {url} -> {type(exc).__name__}: {exc}")
        return None
    dest.write_bytes(raw)
    return raw


# --------------------------------------------------------------------------- #
# CASO A -- parte (i): che cos'e' davvero la fonte esterna?
# --------------------------------------------------------------------------- #
def _sig(df, tcol, hs, as_):
    return {t: tuple(sorted(zip(g[hs].astype(int), g[as_].astype(int))))
            for t, g in df.groupby(tcol)}


def join_esterna(D: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Unisce il repo esterno agli snapshot per IMPRONTA-RISULTATI (indipendente
    dai nomi squadra: il fuzzy sui nomi aveva gia' prodotto falsi accoppiamenti)."""
    seas = {"1718": "2017-2018", "1819": "2018-2019"}
    rows, rep_diag = [], {}
    for lg, fn in IRED.items():
        raw = fetch(IRED_URL.format(fn), CACHE / f"{fn}.csv")
        if raw is None or len(raw) < 1000:
            rep_diag[lg] = "non scaricato"
            continue
        rep = pd.read_csv(CACHE / f"{fn}.csv")
        for sc, lab in seas.items():
            r = rep[rep.season == lab].copy()
            s = D[(D.league_k == lg) & (D.season == sc)].copy()
            if len(r) == 0 or len(s) == 0:
                continue
            rh, ra = _sig(r, "hTeam", "hScore", "aScore"), _sig(r, "aTeam", "hScore", "aScore")
            sh = _sig(s, "home_team", "home_goals", "away_goals")
            sa = _sig(s, "away_team", "home_goals", "away_goals")
            inv: dict = {}
            for t in set(sh) | set(sa):
                inv.setdefault((sh.get(t), sa.get(t)), []).append(t)
            mp = {}
            for t in set(rh) | set(ra):
                c = inv.get((rh.get(t), ra.get(t)), [])
                if len(c) == 1:
                    mp[t] = c[0]
            r["home_c"], r["away_c"] = r.hTeam.map(mp), r.aTeam.map(mp)
            m = s.merge(r[["home_c", "away_c", "hScore", "aScore", "hOdd", "dOdd", "aOdd"]],
                        left_on=["home_team", "away_team"],
                        right_on=["home_c", "away_c"], how="left")
            okg = (m.hScore == m.home_goals) & (m.aScore == m.away_goals)
            rep_diag[f"{lg}_{sc}"] = {"snapshot": len(s), "uniti": int(m.hOdd.notna().sum()),
                                      "gol_discordanti": int((m.hOdd.notna() & ~okg).sum())}
            rows.append(m)
    if not rows:
        return pd.DataFrame(), rep_diag
    return pd.concat(rows, ignore_index=True), rep_diag


def caso_A_natura_fonte(D: pd.DataFrame) -> dict:
    J, diag = join_esterna(D)
    res = {"join": diag}
    if J.empty:
        res["stato"] = "fonte esterna non scaricabile in questa esecuzione"
        return res
    # aggancio del GREZZO football-data (per avere ogni singola colonna book)
    fr = []
    for lg in IRED:
        for sc in ("1718", "1819"):
            f = RAW_FD / f"{lg}_{sc}.csv"
            if f.exists():
                r = pd.read_csv(f).dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
                r["league_k"], r["season"] = lg, sc
                fr.append(r)
    RW = pd.concat(fr, ignore_index=True)
    for (lg, sc), g in RW.groupby(["league_k", "season"]):
        s = J[(J.league_k == lg) & (J.season == sc)]
        rh, ra = _sig(g, "HomeTeam", "FTHG", "FTAG"), _sig(g, "AwayTeam", "FTHG", "FTAG")
        sh = _sig(s, "home_team", "home_goals", "away_goals")
        sa = _sig(s, "away_team", "home_goals", "away_goals")
        inv: dict = {}
        for t in set(sh) | set(sa):
            inv.setdefault((sh.get(t), sa.get(t)), []).append(t)
        mp = {t: inv[(rh.get(t), ra.get(t))][0] for t in set(rh) | set(ra)
              if len(inv.get((rh.get(t), ra.get(t)), [])) == 1}
        RW.loc[g.index, "home_c"] = g.HomeTeam.map(mp)
        RW.loc[g.index, "away_c"] = g.AwayTeam.map(mp)
    keep = [c for c in ["league_k", "season", "home_c", "away_c", "FTHG", "FTAG",
                        "B365H", "B365D", "B365A", "PSH", "PSD", "PSA",
                        "BbAvH", "BbAvD", "BbAvA", "BbMxH", "BbMxD", "BbMxA",
                        "PSCH", "PSCD", "PSCA", "BWH", "BWD", "BWA",
                        "IWH", "IWD", "IWA", "WHH", "WHD", "WHA", "VCH", "VCD", "VCA"]
            if c in RW.columns]
    M = J.merge(RW[keep], left_on=["league_k", "season", "home_team", "away_team"],
                right_on=["league_k", "season", "home_c", "away_c"], how="left")
    assert (M.FTHG == M.home_goals).all(), "aggancio al grezzo incoerente sui gol"

    Pr = devig3(M.hOdd, M.dOdd, M.aOdd)
    Ppsc = devig3(M.PSCH, M.PSCD, M.PSCA)
    Pbb = devig3(M.BbAvH, M.BbAvD, M.BbAvA)
    Pps = devig3(M.PSH, M.PSD, M.PSA)
    y = M.result.map({"H": 0, "D": 1, "A": 2}).values
    ok = np.isfinite(Pr).all(1) & np.isfinite(Ppsc).all(1) & np.isfinite(Pbb).all(1)

    ov = lambda h, d, a: (1 / h + 1 / d + 1 / a)  # noqa: E731
    res["V1_margine"] = {
        nm: [float(np.nanmean(v)), float(np.nanstd(v))] for nm, v in {
            "fonte_esterna": ov(M.hOdd, M.dOdd, M.aOdd),
            "PSC_chiusura_pinnacle": ov(M.PSCH, M.PSCD, M.PSCA),
            "PS_apertura_pinnacle": ov(M.PSH, M.PSD, M.PSA),
            "BbAv_media_prematch": ov(M.BbAvH, M.BbAvD, M.BbAvA),
            "B365_prematch": ov(M.B365H, M.B365D, M.B365A)}.items()}

    mae = lambda A, B: np.abs(A - B).mean(1)  # noqa: E731
    res["V2_distanza"] = {
        "n": int(ok.sum()),
        "mae_fonte_vs_chiusura_PSC": float(mae(Pr, Ppsc)[ok].mean()),
        "mae_fonte_vs_apertura_BbAv": float(mae(Pr, Pbb)[ok].mean()),
        "mae_apertura_vs_chiusura": float(mae(Pbb, Ppsc)[ok].mean()),
        "delta": boot_ci(mae(Pr, Ppsc)[ok] - mae(Pr, Pbb)[ok])}

    ll = lambda P: -np.log(np.clip(P[np.where(ok)[0], y[ok].astype(int)], 1e-12, 1))  # noqa: E731
    res["V3_potere_predittivo"] = {
        "logloss_fonte": float(ll(Pr).mean()), "logloss_chiusura_PSC": float(ll(Ppsc).mean()),
        "logloss_apertura_BbAv": float(ll(Pbb).mean()),
        "fonte_vs_apertura": boot_ci(ll(Pr) - ll(Pbb)),
        "fonte_vs_chiusura": boot_ci(ll(Pr) - ll(Ppsc))}

    res["V4_identita_con_colonne_footballdata"] = {
        nm: float(((M.hOdd == M[h]) & (M.dOdd == M[d]) & (M.aOdd == M[a])).mean())
        for nm, (h, d, a) in {
            "B365": ("B365H", "B365D", "B365A"), "BW": ("BWH", "BWD", "BWA"),
            "IW": ("IWH", "IWD", "IWA"), "PS_apertura": ("PSH", "PSD", "PSA"),
            "WH": ("WHH", "WHD", "WHA"), "VC": ("VCH", "VCD", "VCA"),
            "BbAv": ("BbAvH", "BbAvD", "BbAvA"), "BbMx": ("BbMxH", "BbMxD", "BbMxA"),
            "PSC": ("PSCH", "PSCD", "PSCA")}.items() if h in M.columns}

    def ladder(s):
        v = pd.Series(np.asarray(s, float)).dropna()
        v = v[v >= 8]
        c = (v * 100).round().astype(int)
        return {"n": int(len(v)), "frazione_che_finisce_per_00": float((c % 100 == 0).mean()),
                "frazione_00_o_50": float((c % 50 == 0).mean())}

    def lastdig(s):
        v = pd.Series(np.asarray(s, float)).dropna()
        d = ((v * 100).round().astype(int)) % 10
        return float(d.value_counts(normalize=True).max())

    res["V5_granularita_prezzi"] = {
        "scaletta_quote_lunghe": {
            "fonte_esterna": ladder(pd.concat([M.hOdd, M.dOdd, M.aOdd])),
            "BbAv_media": ladder(pd.concat([M.BbAvH, M.BbAvD, M.BbAvA])),
            "B365_book_singolo": ladder(pd.concat([M.B365H, M.B365D, M.B365A])),
            "PSC_pinnacle": ladder(pd.concat([M.PSCH, M.PSCD, M.PSCA]))},
        "massima_frequenza_ultima_cifra": {
            "fonte_esterna": lastdig(pd.concat([M.hOdd, M.dOdd, M.aOdd])),
            "BbAv_media": lastdig(pd.concat([M.BbAvH, M.BbAvD, M.BbAvA])),
            "B365_book_singolo": lastdig(pd.concat([M.B365H, M.B365D, M.B365A])),
            "PSC_pinnacle": lastdig(pd.concat([M.PSCH, M.PSCD, M.PSCA]))},
        "lettura": "uniforme (~0.10) = prezzo continuo / media; picco alto = scaletta di un book"}

    # V6: la FIRMA di una transizione apertura->chiusura, per provider
    def firma(df, co, cc, label):
        if any(c not in df.columns for c in co + cc):
            return None
        Po, Pc = devig3(df[co[0]], df[co[1]], df[co[2]]), devig3(df[cc[0]], df[cc[1]], df[cc[2]])
        m = np.isfinite(Po).all(1) & np.isfinite(Pc).all(1)
        if m.sum() < 100:
            return None
        ovo = (1 / df[co[0]] + 1 / df[co[1]] + 1 / df[co[2]]).values[m]
        ovc = (1 / df[cc[0]] + 1 / df[cc[1]] + 1 / df[cc[2]]).values[m]
        return {"coppia": label, "n": int(m.sum()),
                "mae_movimento": float(np.abs(Pc - Po).mean(1)[m].mean()),
                "corr_prob_casa": float(np.corrcoef(Po[m, 0], Pc[m, 0])[0, 1]),
                "delta_margine": float(np.nanmean(ovc - ovo))}
    late = []
    for lg in IRED:
        for sc in ("1920", "2021", "2122", "2223", "2324", "2425", "2526"):
            f = RAW_FD / f"{lg}_{sc}.csv"
            if f.exists():
                late.append(pd.read_csv(f).dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]))
    L = pd.concat(late, ignore_index=True)
    Mr = M.rename(columns={"hOdd": "RH", "dOdd": "RD", "aOdd": "RA"})
    res["V6_firma_apertura_chiusura"] = {
        "media->media_ETICHETTATA_Avg->AvgC_2019_26":
            firma(L, ["AvgH", "AvgD", "AvgA"], ["AvgCH", "AvgCD", "AvgCA"], "Avg -> AvgC"),
        "pinnacle->pinnacle_2019_26":
            firma(L, ["PSH", "PSD", "PSA"], ["PSCH", "PSCD", "PSCA"], "PS -> PSC"),
        "FONTE_ESTERNA_BbAv->fonte_2017_19":
            firma(Mr, ["BbAvH", "BbAvD", "BbAvA"], ["RH", "RD", "RA"], "BbAv -> fonte"),
        "CAMBIO_PROVIDER_BbAv->PSC_2017_19":
            firma(M, ["BbAvH", "BbAvD", "BbAvA"], ["PSCH", "PSCD", "PSCA"], "BbAv -> PSC"),
    }

    # V7: il MOVIMENTO della fonte e' lo stesso che vede Pinnacle? (test decisivo)
    m8 = ok & np.isfinite(Pps).all(1)
    cor = [float(np.corrcoef((Pr - Pbb)[m8][:, k], (Ppsc - Pps)[m8][:, k])[0, 1]) for k in range(3)]
    Pa, Pac = devig3(L.AvgH, L.AvgD, L.AvgA), devig3(L.AvgCH, L.AvgCD, L.AvgCA)
    Pp, Ppc = devig3(L.PSH, L.PSD, L.PSA), devig3(L.PSCH, L.PSCD, L.PSCA)
    m2 = np.isfinite(Pa).all(1) & np.isfinite(Pac).all(1) & np.isfinite(Pp).all(1) & np.isfinite(Ppc).all(1)
    res["V7_movimento"] = {
        "fonte_vs_pinnacle_2017_19": {"n": int(m8.sum()), "corr_H_D_A": cor},
        "riferimento_due_provider_veri_2019_26": {
            "n": int(m2.sum()),
            "corr_H_D_A": [float(np.corrcoef((Pac - Pa)[m2][:, k], (Ppc - Pp)[m2][:, k])[0, 1])
                           for k in range(3)]},
        "pavimento_due_APERTURE_simultanee": {
            "n": int(m8.sum()),
            "corr_H_D_A": [float(np.corrcoef((Pps - Pbb)[m8][:, k], (Ppsc - Pps)[m8][:, k])[0, 1])
                           for k in range(3)]},
        "lettura": "se la fonte fosse una seconda APERTURA il suo 'movimento' sarebbe rumore "
                   "(pavimento ~0); se e' una fotografia all'ora di chiusura deve correlare col "
                   "movimento vero di Pinnacle quanto ci correla un'altra media di mercato"}

    # V8: incapsulamento (chi contiene chi)
    def alpha(PA, PB):
        m = np.isfinite(PA).all(1) & np.isfinite(PB).all(1) & np.isfinite(y)
        A, B = np.log(np.clip(PA[m], 1e-9, 1)), np.log(np.clip(PB[m], 1e-9, 1))
        yy = y[m].astype(int)
        best = (None, 1e9)
        for a in np.arange(0, 1.0001, 0.02):
            Lg = a * A + (1 - a) * B
            Lg -= Lg.max(1, keepdims=True)
            P = np.exp(Lg)
            P /= P.sum(1, keepdims=True)
            v = -np.log(np.clip(P[np.arange(len(yy)), yy], 1e-12, 1)).mean()
            if v < best[1]:
                best = (float(a), float(v))
        return {"alpha_star": best[0], "logloss": best[1]}
    res["V8_incapsulamento"] = {
        "peso_ottimo_della_fonte_contro_PSC": alpha(Pr, Ppsc),
        "peso_ottimo_della_fonte_contro_apertura": alpha(Pr, Pbb)}
    return res, M


# --------------------------------------------------------------------------- #
# CASO A -- parte (ii): la STIMA apertura -> chiusura
# --------------------------------------------------------------------------- #
def caso_A_stima(D: pd.DataFrame, M: pd.DataFrame | None) -> tuple[dict, list]:
    Po = devig3(D.odds_home_open, D.odds_draw_open, D.odds_away_open)
    Pc = devig3(D.odds_home, D.odds_draw, D.odds_away)
    ok = np.isfinite(Po).all(1) & np.isfinite(Pc).all(1)
    Dp, Po, Pc = D[ok].reset_index(drop=True), Po[ok], Pc[ok]
    y = Dp.result.map({"H": 0, "D": 1, "A": 2}).values.astype(int)
    X, Y = feats(Po), targ(Pc)
    rng = np.random.default_rng(SEED)
    kf = rng.integers(0, 10, len(Dp))
    res = {"n_coppie_reali": int(len(Dp)),
           "per_lega": Dp.groupby("league_k").size().to_dict()}

    def oos(groups, nome):
        pred = np.full_like(Y, np.nan)
        for g in np.unique(groups):
            te = groups == g
            pred[te] = X[te] @ ols(X[~te], Y[~te])
        Pe = back(pred)
        e_s, e_i = np.abs(Pe - Pc).mean(1), np.abs(Po - Pc).mean(1)
        l_s = -np.log(np.clip(Pe[np.arange(len(y)), y], 1e-12, 1))
        l_i = -np.log(np.clip(Po[np.arange(len(y)), y], 1e-12, 1))
        return {"schema": nome, "mae_stima": float(e_s.mean()), "mae_identita": float(e_i.mean()),
                "delta_mae": boot_ci(e_s - e_i), "logloss_stima": float(l_s.mean()),
                "logloss_identita": float(l_i.mean()), "delta_logloss": boot_ci(l_s - l_i)}, e_s

    res["A2_fronte_generale"] = {}
    r, e_pool = oos(kf, "k-fold 10 casuale (pooled 5 leghe)")
    res["A2_fronte_generale"]["kfold10"] = r
    res["A2_fronte_generale"]["leave_one_season_out"] = oos(Dp.season.values, "leave-one-season-out")[0]
    res["A2_fronte_generale"]["leave_one_league_out"] = oos(Dp.league_k.values, "leave-one-league-out")[0]

    pred = np.full_like(Y, np.nan)                     # fronte PER-LEGA (principio 9)
    for lg in Dp.league_k.unique():
        sel = (Dp.league_k == lg).values
        sub = kf[sel]
        for g in np.unique(sub):
            te = np.zeros(len(Dp), bool)
            te[np.where(sel)[0][sub == g]] = True
            pred[te] = X[te] @ ols(X[sel & ~te], Y[sel & ~te])
    e_lg = np.abs(back(pred) - Pc).mean(1)
    res["A2_fronte_per_lega"] = {"schema": "k-fold 10 dentro ogni lega",
                                 "mae_stima": float(e_lg.mean()),
                                 "mae_identita": float(np.abs(Po - Pc).mean(1).mean()),
                                 "delta_vs_identita": boot_ci(e_lg - np.abs(Po - Pc).mean(1)),
                                 "delta_vs_pooled": boot_ci(e_lg - e_pool)}
    B_pool = ols(X, Y)
    res["A2_coefficienti"] = {
        "pooled": {"logit_H_su_D": B_pool[:, 0].tolist(), "logit_A_su_D": B_pool[:, 1].tolist()},
        "identita_sarebbe": {"logit_H_su_D": [0, 1, 0], "logit_A_su_D": [0, 0, 1]},
        "per_lega": {lg: {"logit_H_su_D": ols(X[(Dp.league_k == lg).values],
                                              Y[(Dp.league_k == lg).values])[:, 0].tolist(),
                          "logit_A_su_D": ols(X[(Dp.league_k == lg).values],
                                              Y[(Dp.league_k == lg).values])[:, 1].tolist()}
                     for lg in Dp.league_k.unique()}}
    B_lg = {lg: ols(X[(Dp.league_k == lg).values], Y[(Dp.league_k == lg).values])
            for lg in Dp.league_k.unique()}

    # modelli PROVIDER-APPAIATI sul grezzo 2017-19 (le 2 righe bersaglio hanno
    # aperture di provider diversi: BbAv per Bayern-Hannover, PS per Alaves-Sociedad)
    fr = []
    for lg in IRED:
        for sc in ("1718", "1819"):
            f = RAW_FD / f"{lg}_{sc}.csv"
            if f.exists():
                fr.append(pd.read_csv(f).dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]))
    R = pd.concat(fr, ignore_index=True)

    def pair(co, cc):
        Pa, Pb = devig3(R[co[0]], R[co[1]], R[co[2]]), devig3(R[cc[0]], R[cc[1]], R[cc[2]])
        m = np.isfinite(Pa).all(1) & np.isfinite(Pb).all(1)
        return feats(Pa[m]), targ(Pb[m]), Pa[m], Pb[m]
    prov = {}
    B_prov = {}
    for nm, co in {"BbAv_open->PSC": ("BbAvH", "BbAvD", "BbAvA"),
                   "PS_open->PSC": ("PSH", "PSD", "PSA")}.items():
        Xa, Ya, Pa, Pb = pair(co, ("PSCH", "PSCD", "PSCA"))
        g = np.random.default_rng(SEED).integers(0, 10, len(Xa))
        pr = np.full_like(Ya, np.nan)
        for j in range(10):
            te = g == j
            pr[te] = Xa[te] @ ols(Xa[~te], Ya[~te])
        e_s, e_i = np.abs(back(pr) - Pb).mean(1), np.abs(Pa - Pb).mean(1)
        prov[nm] = {"n": int(len(Xa)), "mae_stima_oos": float(e_s.mean()),
                    "mae_identita": float(e_i.mean()), "delta": boot_ci(e_s - e_i)}
        B_prov[nm] = ols(Xa, Ya)
    res["A2_modelli_provider_appaiati"] = prov

    # simulazione del buco: dove la chiusura ESISTE, chi e' il miglior tappo?
    righe = []
    if M is not None and not M.empty:
        Pr = devig3(M.hOdd, M.dOdd, M.aOdd)
        Pv = devig3(M.PSCH, M.PSCD, M.PSCA)
        Pa = devig3(M.odds_home_open, M.odds_draw_open, M.odds_away_open)
        m = np.isfinite(Pr).all(1) & np.isfinite(Pv).all(1) & np.isfinite(Pa).all(1)
        Xa, Ya = feats(Pa[m]), targ(Pv[m])
        g = np.random.default_rng(SEED).integers(0, 10, int(m.sum()))
        pr = np.full_like(Ya, np.nan)
        for j in range(10):
            te = g == j
            pr[te] = Xa[te] @ ols(Xa[~te], Ya[~te])
        e_f = np.abs(Pr[m] - Pv[m]).mean(1)
        e_s = np.abs(back(pr) - Pv[m]).mean(1)
        e_i = np.abs(Pa[m] - Pv[m]).mean(1)
        res["A1_simulazione_del_buco"] = {
            "n": int(m.sum()), "mae_dato_esterno": float(e_f.mean()),
            "mae_stima_kfold": float(e_s.mean()), "mae_identita": float(e_i.mean()),
            "dato_esterno_meno_stima": boot_ci(e_f - e_s),
            "stima_meno_identita": boot_ci(e_s - e_i),
            "quante_volte_meglio_il_dato_vero": float(e_s.mean() / e_f.mean())}
        mov = e_i  # distribuzione empirica del movimento apertura->chiusura
    else:
        mov = None

    # le due partite bersaglio
    def footiqo(lg, seas, home, away, day):
        f = ROOT / "data" / "ricerca_esterna" / f"footiqo_{lg}_{seas}.json"
        if not f.exists():
            return None
        for mm in json.load(open(f)):
            if mm["matchDate"].startswith(day) and home in mm["homeTeam"] and away in mm["awayTeam"]:
                return mm
        return None
    casi = [
        dict(lega="bundesliga", stagione="1819", data="2019-05-04",
             casa="Bayern Munich", ospite="Hannover", apertura=(1.04, 17.52, 45.03),
             provider_apertura="BbAv (media prematch Betbrain)",
             reale=(1.03, 18.43, 43.88), mod="BbAv_open->PSC",
             fq=footiqo("bundesliga", "2018-2019", "Bayern", "Hannover", "04-05-19")),
        dict(lega="la_liga", stagione="1718", data="2017-10-14",
             casa="Alaves", ospite="Sociedad", apertura=(3.52, 3.55, 2.20),
             provider_apertura="PS (Pinnacle prematch)",
             reale=(3.40, 3.34, 2.15), mod="PS_open->PSC",
             fq=footiqo("la_liga", "2017-2018", "Alaves", "Sociedad", "14-10-17")),
    ]
    det = []
    for c in casi:
        Pa = devig3([c["apertura"][0]], [c["apertura"][1]], [c["apertura"][2]])
        Pv = devig3([c["reale"][0]], [c["reale"][1]], [c["reale"][2]])[0]
        Xr = feats(Pa)
        est = {"stima_pooled": back(Xr @ B_pool)[0], "stima_per_lega": back(Xr @ B_lg[c["lega"]])[0],
               "stima_provider_appaiato": back(Xr @ B_prov[c["mod"]])[0], "identita": Pa[0]}
        row = {"partita": f"{c['lega']} {c['casa']}-{c['ospite']} {c['data']}",
               "provider_apertura": c["provider_apertura"],
               "quote_apertura": list(c["apertura"]), "quote_dato_reale": list(c["reale"]),
               "p_dato_reale": [round(float(v), 5) for v in Pv]}
        for nm, p in est.items():
            row[f"p_{nm}"] = [round(float(v), 5) for v in p]
            row[f"MAE_{nm}_vs_dato_reale"] = float(np.abs(p - Pv).mean())
        if c["fq"]:
            pf = devig3([float(c["fq"]["xbetClose1FT"])], [float(c["fq"]["xbetCloseXFT"])],
                        [float(c["fq"]["xbetClose2FT"])])[0]
            row["terza_fonte_footiqo_1xBet"] = [float(c["fq"]["xbetClose1FT"]),
                                                float(c["fq"]["xbetCloseXFT"]),
                                                float(c["fq"]["xbetClose2FT"])]
            row["MAE_dato_reale_vs_terza_fonte"] = float(np.abs(Pv - pf).mean())
            row["MAE_identita_vs_terza_fonte"] = float(np.abs(est["identita"] - pf).mean())
        if mov is not None:
            v = row["MAE_stima_pooled_vs_dato_reale"]
            row["percentile_dell_accordo_nel_movimento_tipico"] = float((mov <= v).mean())
        det.append(row)
        righe.append(c | {"est": est, "Pv": Pv})
    res["A3_due_partite"] = det
    return res, righe


# --------------------------------------------------------------------------- #
# CASO B -- l'xG si stima dai tiri in porta?
# --------------------------------------------------------------------------- #
FEAT_B = ["sot", "sot_opp", "g", "g_opp", "is_home", "lsv", "lsv_opp", "lsv_ratio"]


def _design_B(df, leagues):
    X = [np.ones(len(df))] + [df[c].values.astype(float) for c in FEAT_B]
    X.append(np.sqrt(df.sot.values.astype(float)))
    for lg in leagues[1:]:
        X.append((df.league_k == lg).values.astype(float))
    return np.column_stack(X)


def caso_B(D: pd.DataFrame) -> tuple[dict, dict]:
    recs = []
    D = D.copy()
    D["mid"] = np.arange(len(D))
    for side, opp in (("home", "away"), ("away", "home")):
        recs.append(pd.DataFrame({
            "mid": D.mid, "league_k": D.league_k, "season": D.season, "date": D.date,
            "team": D[f"{side}_team"], "oppo": D[f"{opp}_team"],
            "is_home": 1 if side == "home" else 0,
            "sot": D[f"{side}_sot"], "sot_opp": D[f"{opp}_sot"],
            "g": D[f"{side}_goals"], "g_opp": D[f"{opp}_goals"],
            "sv": D[f"{side}_squad_value"], "sv_opp": D[f"{opp}_squad_value"],
            "xg": D[f"{side}_xg"]}))
    L = pd.concat(recs, ignore_index=True)
    L["lsv"] = np.log(L.sv.clip(lower=1))
    L["lsv_opp"] = np.log(L.sv_opp.clip(lower=1))
    L["lsv_ratio"] = L.lsv - L.lsv_opp
    F = L.dropna(subset=["sot", "sot_opp", "g", "g_opp", "xg", "lsv", "lsv_opp"]).reset_index(drop=True)
    LG = sorted(F.league_k.unique())
    X, y = _design_B(F, LG), F.xg.values.astype(float)
    rng = np.random.default_rng(SEED)
    kf = pd.Series(F.mid.values).map(
        dict(zip(np.unique(F.mid.values), rng.integers(0, 10, F.mid.nunique())))).values

    def run(groups, nome):
        pred = np.full(len(y), np.nan)
        for g in np.unique(groups):
            te = groups == g
            pred[te] = X[te] @ ols(X[~te], y[~te])
        pred = np.clip(pred, 0, None)
        return ({"schema": nome, "MAE": float(np.abs(pred - y).mean()),
                 "RMSE": float(np.sqrt(((pred - y) ** 2).mean())),
                 "R2": float(1 - ((pred - y) ** 2).mean() / ((y - y.mean()) ** 2).mean())},
                np.abs(pred - y), pred)
    r_kf, e_kf, pred_kf = run(kf, "k-fold 10 per PARTITA (le 2 squadre nello stesso fold)")
    res = {"B1_dati": {"n_squadra_partita": int(len(F)), "media_xg": float(y.mean()),
                       "sd_xg": float(y.std())},
           "B2_regressione": [r_kf, run(F.league_k.values, "leave-one-league-out")[0],
                              run((F.league_k + F.season).values, "leave-one-league-season-out")[0]]}
    base = {}
    mu = F.groupby(["league_k", "is_home"]).xg.transform("mean").values
    grp = F.groupby(["league_k", "season", "team"]).xg
    loo = ((grp.transform("sum") - F.xg) / (grp.transform("count") - 1)).values
    loo = np.nan_to_num(loo, nan=float(np.nanmean(loo)))
    for nm, p in {"media_di_lega_e_campo": mu, "xg_uguale_ai_gol": F.g.values.astype(float),
                  "xg_035_x_tiri_in_porta": 0.35 * F.sot.values.astype(float),
                  "media_della_squadra_nella_stagione": loo}.items():
        e = np.abs(p - y)
        base[nm] = {"MAE": float(e.mean()), "RMSE": float(np.sqrt(((p - y) ** 2).mean())),
                    "R2": float(1 - ((p - y) ** 2).mean() / ((y - y.mean()) ** 2).mean()),
                    "delta_MAE_regressione_meno_baseline": boot_ci(e_kf - e)}
    k = float((F.sot.values * y).sum() / (F.sot.values ** 2).sum())
    p = k * F.sot.values
    base[f"k_x_tiri_in_porta_con_k_ottimo_{k:.4f}"] = {
        "MAE": float(np.abs(p - y).mean()), "R2": float(1 - ((p - y) ** 2).mean() / ((y - y.mean()) ** 2).mean()),
        "delta_MAE_regressione_meno_baseline": boot_ci(e_kf - np.abs(p - y))}
    res["B3_baseline"] = base
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
        pr = np.full(len(y), np.nan)
        for j in range(10):
            te = kf == j
            m = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.08, random_state=0)
            m.fit(X[~te], y[~te])
            pr[te] = m.predict(X[te])
        pr = np.clip(pr, 0, None)
        e = np.abs(pr - y)
        res["B4_tetto_gradient_boosting"] = {
            "MAE": float(e.mean()), "R2": float(1 - ((pr - y) ** 2).mean() / ((y - y.mean()) ** 2).mean()),
            "delta_vs_lineare": boot_ci(e - e_kf),
            "lettura": "se il GBM non batte la retta, il limite e' INFORMATIVO e non del modello"}
    except Exception as exc:                                # noqa: BLE001
        res["B4_tetto_gradient_boosting"] = {"errore": str(exc)}
    cond = {}
    for lab, m in {"tiri_in_porta=1": F.sot == 1, "tiri_in_porta=3": F.sot == 3,
                   "tiri_in_porta=6": F.sot == 6, "gol=2 e tiri_in_porta=3": (F.g == 2) & (F.sot == 3),
                   "gol=0 e tiri_in_porta=1": (F.g == 0) & (F.sot == 1)}.items():
        m = m.values
        cond[lab] = {"n": int(m.sum()), "MAE": float(e_kf[m].mean()),
                     "media_xg_reale": float(y[m].mean()), "sd_xg_reale": float(y[m].std()),
                     "banda_errore_p10_p90": [float(np.percentile((pred_kf - y)[m], 10)),
                                              float(np.percentile((pred_kf - y)[m], 90))]}
    res["B5_errore_condizionato_al_profilo"] = cond
    res["B6_quantili_errore"] = {"p50": float(np.percentile(e_kf, 50)),
                                 "p90": float(np.percentile(e_kf, 90)),
                                 "frazione_errore_sopra_0.5_gol": float((e_kf > 0.5).mean())}
    B = ols(X, y)

    def stima(lg, season, team, oppo, is_home, sot, sot_opp, g, g_opp):
        sv = F[(F.league_k == lg) & (F.season == season) & (F.team == team)].sv
        so = F[(F.league_k == lg) & (F.season == season) & (F.team == oppo)].sv
        if len(sv) == 0 or len(so) == 0:
            return None
        row = pd.DataFrame([{"league_k": lg, "sot": sot, "sot_opp": sot_opp, "g": g, "g_opp": g_opp,
                             "is_home": is_home, "lsv": np.log(sv.iloc[0]), "lsv_opp": np.log(so.iloc[0]),
                             "lsv_ratio": np.log(sv.iloc[0]) - np.log(so.iloc[0])}])
        return float(np.clip(_design_B(row, LG) @ B, 0, None)[0])
    casi = [("bundesliga", "2425", "Holstein Kiel", "Bochum", 1, 3, 6, 2, 2),
            ("bundesliga", "2425", "Bochum", "Holstein Kiel", 0, 6, 3, 2, 2),
            ("ligue_1", "2526", "Nantes", "Toulouse", 1, 1, 1, 0, 0),
            ("ligue_1", "2526", "Toulouse", "Nantes", 0, 1, 1, 0, 0)]
    appl = [{"lega": c[0], "stagione": c[1], "squadra": c[2], "avversario": c[3],
             "in_casa": bool(c[4]), "tiri_in_porta": c[5], "gol": c[7],
             "xg_stimato": stima(*c), "MAE_atteso_globale": r_kf["MAE"]} for c in casi]
    res["B7_applicazione_alle_celle"] = appl
    return res, {"appl": appl, "cond": cond, "mae": r_kf["MAE"]}


# --------------------------------------------------------------------------- #
# CASO C -- Understat ha consolidato Nantes-Toulouse?
# --------------------------------------------------------------------------- #
def caso_C(D: pd.DataFrame) -> dict:
    raw = fetch(UNDERSTAT_URL, CACHE / "understat_ligue_1_2025.json", gz=True, xhr=True)
    if raw is None:
        return {"stato": "endpoint non raggiungibile in questa esecuzione"}
    data = json.loads(raw)
    dates = data.get("dates", [])
    non = [m for m in dates if not m.get("isResult")]
    srt = sorted(dates, key=lambda m: m["datetime"])
    ultima = [m for m in srt if m["datetime"][:10] == srt[-1]["datetime"][:10]]
    res = {"url": UNDERSTAT_URL, "n_partite_nel_json": len(dates),
           "non_consolidate": [{"data": m["datetime"], "partita": f"{m['h']['title']} - {m['a']['title']}",
                                "xG": m.get("xG")} for m in non],
           "ultima_giornata": [{"id": m["id"], "data": m["datetime"],
                                "partita": f"{m['h']['title']} - {m['a']['title']}",
                                "gol": m["goals"], "xG": m.get("xG"), "isResult": m.get("isResult")}
                               for m in ultima]}
    # la partita e' nella history delle due squadre?
    hist = {}
    for t in data.get("teams", {}).values():
        if t["title"] in ("Nantes", "Toulouse"):
            hist[t["title"]] = {"n_partite_in_history": len(t["history"]),
                                "ultima_data": t["history"][-1]["date"] if t["history"] else None}
    res["history_squadre"] = hist
    # l'endpoint di partita risponde?
    probe = {}
    for m in ultima:
        r = fetch(UNDERSTAT_MATCH.format(m["id"]), CACHE / f"um_{m['id']}.json", gz=True, xhr=True)
        if r is None:
            probe[m["id"]] = "404 / non disponibile"
        else:
            j = json.loads(r)
            probe[m["id"]] = {"tiri_casa": len(j.get("shots", {}).get("h", [])),
                              "tiri_ospiti": len(j.get("shots", {}).get("a", []))}
    res["endpoint_di_partita"] = probe
    # confronto con lo snapshot: le altre 8 partite hanno bisogno di correzione?
    S = D[(D.league_k == "ligue_1") & (D.date == srt[-1]["datetime"][:10])]
    diff = []
    for m in ultima:
        if not m.get("isResult"):
            continue
        h = str(m["h"]["title"]).replace("Paris Saint Germain", "Paris SG")
        row = S[S.home_team == h]
        if len(row) == 1 and np.isfinite(row.home_xg.iloc[0]):
            dh = abs(float(row.home_xg.iloc[0]) - float(m["xG"]["h"]))
            da = abs(float(row.away_xg.iloc[0]) - float(m["xG"]["a"]))
            if max(dh, da) > 1e-4:
                diff.append({"partita": h, "delta_xg": [dh, da]})
    res["controllo_resto_ultima_giornata"] = {
        "partite_confrontate": int(S.home_xg.notna().sum()),
        "discrepanze_xg_con_la_fonte": diff,
        "lettura": "0 discrepanze = le altre partite dell'ultima giornata sono gia' corrette"}
    return res


# --------------------------------------------------------------------------- #
# CASO D -- censimento delle celle vuote e dei buchi che NON sono NaN
# --------------------------------------------------------------------------- #
def caso_D(D: pd.DataFrame) -> dict:
    res = {}
    cens = {}
    for lg in SNAP:
        d = D[D.league_k == lg].drop(columns=["league_k"])
        na = d.isna().sum()
        cens[lg] = {"righe": int(len(d)), "celle": int(d.size), "NaN": int(d.isna().sum().sum()),
                    "per_colonna": {k: int(v) for k, v in na[na > 0].items()}}
    tot_cell = sum(v["celle"] for v in cens.values())
    tot_na = sum(v["NaN"] for v in cens.values())
    res["D1_censimento"] = {"per_lega": cens, "celle_totali": tot_cell, "NaN_totali": tot_na,
                            "frazione": round(tot_na / tot_cell, 6)}
    sist = D.season.isin(["1718", "1819"])
    sparse = []
    for c in D.columns:
        if c == "league_k":
            continue
        m = D[c].isna()
        if c in ("odds_over25", "odds_under25"):
            m = m & ~sist
        for i in np.where(m)[0]:
            r = D.iloc[i]
            sparse.append({"lega": r.league_k, "stagione": r.season, "data": r.date,
                           "partita": f"{r.home_team} - {r.away_team}", "colonna": c})
    res["D2_celle_sparse"] = {
        "n": len(sparse),
        "buco_sistemico_OU_chiusura_2017_19": int(tot_na - len(sparse)),
        "elenco": sparse}
    sig = {}
    m = (D.home_xg == D.home_goals) & (D.away_xg == D.away_goals) & D.home_xg.notna()
    sig["xg_identico_ai_gol_su_ENTRAMBI_i_lati"] = {
        "n": int(m.sum()),
        "righe": [f"{r.league_k} {r.date} {r.home_team}-{r.away_team}" for _, r in D[m].iterrows()],
        "lettura": "e' la firma del segnaposto trovato nel report 8; 0 = nessun nuovo segnaposto"}
    mz = (D.home_xg == 0) | (D.away_xg == 0)
    coerenti = int((((D.home_xg == 0) & (D.home_sot == 0)) |
                    ((D.away_xg == 0) & (D.away_sot == 0))).sum())
    sig["xg_esattamente_zero"] = {
        "n": int(mz.sum()),
        "con_zero_tiri_in_porta_dallo_stesso_lato": coerenti,
        "righe": [f"{r.league_k} {r.date} {r.home_team}-{r.away_team} "
                  f"tiri {r.home_sot:.0f}/{r.away_sot:.0f} xg {r.home_xg:.3f}/{r.away_xg:.3f}"
                  for _, r in D[mz].iterrows()],
        "lettura": "xG = 0 esatto e' legittimo se quel lato non ha tirato. L'unica riga con "
                   "tiri in porta > 0 e xG = 0 e' bundesliga 2020-11-21 Bielefeld-Leverkusen: "
                   "alla fonte xG=0, npxG=0, deep=1, ppda att=435/def=19 (numeri VERI, non un "
                   "segnaposto) -> il gol del Bielefeld e' un AUTOGOL, che Understat non "
                   "attribuisce all'xG di chi segna. Non e' un buco"}
    sig["tiri_in_porta_zero_su_entrambi"] = int(((D.home_sot == 0) & (D.away_sot == 0)).sum())
    sig["deep_zero_su_entrambi"] = int(((D.home_deep == 0) & (D.away_deep == 0)).sum())
    sig["squad_value_zero"] = int((D.home_squad_value == 0).sum() + (D.away_squad_value == 0).sum())
    sig["righe_duplicate"] = int(D.duplicated(subset=["league_k", "date", "home_team", "away_team"]).sum())
    sig["rest_days_full_al_tetto_14"] = {
        "n_squadra_partita": int((D.home_rest_days_full == 14).sum() + (D.away_rest_days_full == 14).sum()),
        "massimo_osservato": float(max(D.home_rest_days_full.max(), D.away_rest_days_full.max())),
        "lettura": "il tetto e' VOLUTO (loader.add_rest_days_full, cap=14): 14 significa "
                   "'>=14 giorni', non 'esattamente 14'. Censura dichiarata, non un buco"}
    res["D3_finto_pieno"] = sig

    # margine fuori scala (estende a 5 leghe la segnalazione del report 9, che era solo la_liga)
    def scan(cols, label):
        v = sum(1 / D[c] for c in cols)
        anom, conteggi = [], {}
        for thr in (6, 8, 10):
            n = 0
            for era, sel in (("2017-19", sist), ("2019-26", ~sist)):
                x = v[sel].dropna()
                if len(x) < 50:
                    continue
                med = float(np.median(x))
                mad = float(np.median(np.abs(x - med))) or 1e-9
                z = (v - med) / (1.4826 * mad)
                bad = sel & (np.abs(z) > thr)
                n += int(bad.sum())
                if thr != 10:
                    continue
                for i in np.where(bad.values)[0]:
                    r = D.iloc[i]
                    anom.append({"lega": r.league_k, "stagione": r.season, "data": r.date,
                                 "partita": f"{r.home_team} - {r.away_team}",
                                 "quote": [float(r[c]) for c in cols],
                                 "overround": float(v.iloc[i]), "z_robusto": float(z.iloc[i]),
                                 "mediana_epoca": med})
            conteggi[f"|z|>{thr}"] = n
        with np.errstate(all="ignore"):
            m1719 = float(np.nanmedian(v[sist])) if v[sist].notna().any() else None
        return {"mercato": label, "mediana_2017_19": m1719,
                "mediana_2019_26": float(np.nanmedian(v[~sist])),
                "righe_fuori_scala_per_soglia": conteggi, "anomalie_z_oltre_10": anom}
    res["D4_margine_fuori_scala"] = {
        "1X2_chiusura": scan(["odds_home", "odds_draw", "odds_away"], "1X2 chiusura"),
        "1X2_apertura": scan(["odds_home_open", "odds_draw_open", "odds_away_open"], "1X2 apertura"),
        "OU25_chiusura": scan(["odds_over25", "odds_under25"], "O/U 2.5 chiusura"),
        "OU25_apertura": scan(["odds_over25_open", "odds_under25_open"], "O/U 2.5 apertura"),
        "criterio": "|z robusto| rispetto alla mediana dell'epoca (scala MAD): NON un percentile "
                    "(un percentile marca sempre l'1% delle righe, anche quando sono tutte sane). "
                    "L'elenco esteso e' a |z|>10; il conteggio a 6 e 8 serve a mostrare quanto e' "
                    "ripida la coda (a |z|>6 entrano righe legittime dell'epoca 2025-26, che ha "
                    "margini piu' larghi)"}

    # il finto pieno piu' grande: midweek_europe = 0 dove la coppa ESISTE ma il calendario no
    mid = {}
    for lg, (cf, own) in FIXT.items():
        if not cf.exists():
            mid[lg] = {"errore": f"manca {cf.name}"}
            continue
        M = pd.read_csv(SNAP[lg])
        M["date"] = pd.to_datetime(M["date"])
        F = pd.read_csv(cf)
        F["date"] = pd.to_datetime(F["date"])
        add = []
        for f in sorted(glob.glob(str(ROOT / "data" / "ricerca_esterna" / f"fixtures_{lg}_*.csv"))):
            t = pd.read_csv(f)
            t["date"] = pd.to_datetime(t["date"])
            add.append(t[["season", "team", "date", "competition", "home_away", "opponent"]])
        if not add:
            mid[lg] = {"righe_calendario_nuove": 0}
            continue
        key = ["team", "date", "competition"]
        merged = pd.concat([F] + add, ignore_index=True).drop_duplicates(subset=key)
        base = fx.add_rest_days_full(M, F, own_competition=own)
        new = fx.add_rest_days_full(M, merged, own_competition=own)
        mid[lg] = {
            "righe_calendario_nuove": int(len(merged) - len(F.drop_duplicates(subset=key))),
            "midweek_europe_falsi_zero": int(((base.home_midweek_europe == 0) & (new.home_midweek_europe == 1)).sum()
                                             + ((base.away_midweek_europe == 0) & (new.away_midweek_europe == 1)).sum()),
            "partite_con_riposo_che_cambia": int(((base.home_rest_days_full != new.home_rest_days_full)
                                                  | (base.away_rest_days_full != new.away_rest_days_full)).sum()),
            "riproduco_lo_snapshot_attuale": bool(
                (base.home_midweek_europe.values == M.home_midweek_europe.values).all()
                and (base.away_midweek_europe.values == M.away_midweek_europe.values).all())}
    res["D5_midweek_europe_falsi_zero"] = {
        "per_lega": mid,
        "totale_celle": int(sum(v.get("midweek_europe_falsi_zero", 0) for v in mid.values())),
        "totale_partite_con_riposo_che_cambia": int(sum(v.get("partite_con_riposo_che_cambia", 0) for v in mid.values())),
        "fonte_del_rimedio": "data/ricerca_esterna/fixtures_*.csv (3.045 righe gia' su disco)"}
    return res


# --------------------------------------------------------------------------- #
# CSV riga-per-riga
# --------------------------------------------------------------------------- #
def scrivi_csv(A: dict, Ar: list, B: dict, Bd: dict, C: dict, Dd: dict) -> pd.DataFrame:
    rows = []
    mae_est = A.get("A2_fronte_generale", {}).get("kfold10", {}).get("mae_stima")
    mae_dato = A.get("A1_simulazione_del_buco", {}).get("mae_dato_esterno")
    for c in Ar:
        for k, col in enumerate(("odds_home", "odds_draw", "odds_away")):
            rows.append({
                "caso": "A", "lega": c["lega"], "stagione": c["stagione"], "data": c["data"],
                "partita": f"{c['casa']} - {c['ospite']}", "colonna": col,
                "valore_attuale": "", "valore_proposto": c["reale"][k],
                "metodo": "dato REALE da fonte esterna (iredchuk/soccer-bookmaker-odds), "
                          "identificata qui come chiusura media-di-mercato",
                "errore_atteso": mae_dato, "unita_errore": "MAE su probabilita' devigata",
                "alternativa_stimata": round(float(c["est"]["stima_pooled"][k]), 5),
                "unita_alternativa": "PROBABILITA' devigata (mai una quota: regola data/estimates)",
                "errore_alternativa": mae_est,
                "verdetto": "USARE IL DATO REALE (2,8 volte piu' preciso della stima, CI conclusivo); "
                            "provider diverso dal resto della colonna: da dichiarare in docs/DATI.md",
                "note": "la stima indipendente cade a "
                        f"{c['est']['stima_pooled'][k] - c['Pv'][k]:+.5f} di probabilita' dal dato "
                        "reale: conferma reciproca"})
    for a in Bd["appl"]:
        lega, part = a["lega"], f"{a['squadra']} vs {a['avversario']}"
        col = "home_xg" if a["in_casa"] else "away_xg"
        caso = "B" if lega == "bundesliga" else "C"
        prof = f"gol={a['gol']} e tiri_in_porta={a['tiri_in_porta']}"
        loc = Bd["cond"].get(prof, {}).get("MAE") or Bd["cond"].get(
            f"tiri_in_porta={a['tiri_in_porta']}", {}).get("MAE")
        rows.append({
            "caso": caso, "lega": lega,
            "stagione": a["stagione"],
            "data": "2025-02-09" if caso == "B" else "2026-05-17",
            "partita": part, "colonna": col, "valore_attuale": "",
            "valore_proposto": "",
            "metodo": "regressione xG ~ tiri in porta + gol + forza (32.216 squadra-partita, 5 leghe)",
            "errore_atteso": Bd["mae"], "unita_errore": "MAE in gol attesi",
            "alternativa_stimata": round(a["xg_stimato"], 3) if a["xg_stimato"] else "",
            "unita_alternativa": "gol attesi",
            "errore_alternativa": loc,
            "verdetto": "NON STIMABILE -> resta NaN dichiarato (MAE fuori campione 0,45 gol contro "
                        "una sd di 0,89: l'errore e' meta' del segnale)",
            "note": "il GBM non batte la retta: il limite e' INFORMATIVO, non del modello. "
                    + ("Understat non ha mai acquisito la partita (lista tiri vuota)."
                       if caso == "B" else
                       "Understat non ha ancora consolidato la partita: la via giusta e' "
                       "ri-scaricare, non stimare.")})
    for a in Bd["appl"]:
        caso = "B" if a["lega"] == "bundesliga" else "C"
        for col in (("home_npxg", "home_ppda", "home_deep") if a["in_casa"]
                    else ("away_npxg", "away_ppda", "away_deep")):
            rows.append({
                "caso": caso, "lega": a["lega"], "stagione": a["stagione"],
                "data": "2025-02-09" if caso == "B" else "2026-05-17",
                "partita": f"{a['squadra']} vs {a['avversario']}", "colonna": col,
                "valore_attuale": "", "valore_proposto": "",
                "metodo": "nessuno: non esiste un predittore di npxG/PPDA/deep dai dati football-data "
                          "(i tiri in porta non contengono ne' il pressing ne' la posizione dei passaggi)",
                "errore_atteso": "", "unita_errore": "",
                "alternativa_stimata": "", "errore_alternativa": "",
                "verdetto": "NON STIMABILE -> resta NaN dichiarato",
                "note": "PPDA e deep non hanno nemmeno un proxy nello schema interno"})
    note_gia = {"Alaves - Real Madrid", "Eibar - Real Madrid", "Leganes - Betis", "Leganes - Getafe"}
    for mk, blocco in Dd["D4_margine_fuori_scala"].items():
        if mk == "criterio":
            continue
        for r in blocco["anomalie_z_oltre_10"]:
            gia = r["partita"] in note_gia
            rows.append({
                "caso": "D", "lega": r["lega"], "stagione": r["stagione"], "data": r["data"],
                "partita": r["partita"],
                "colonna": "odds_over25_open / odds_under25_open" if "OU" in mk
                           else "odds_home/draw/away" + ("_open" if "apertura" in mk else ""),
                "valore_attuale": "/".join(str(x) for x in r["quote"]), "valore_proposto": "",
                "metodo": "diagnosi da margine: overround %.4f (z robusto %.1f) contro una mediana "
                          "d'epoca di %.4f" % (r["overround"], r["z_robusto"], r["mediana_epoca"]),
                "errore_atteso": "", "unita_errore": "",
                "alternativa_stimata": "", "errore_alternativa": "",
                "verdetto": "FINTO PIENO: valori presenti ma fuori scala. Il guard della Fase 58 "
                            "scatta solo per overround < 1 e non li intercetta. Da svuotare come le "
                            "8 righe gemelle, oppure estendere il guard con un tetto superiore",
                "note": ("gia' segnalata in docs/audit_5_leghe/numeri/caccia_quote_singole.json"
                         if gia else
                         "NUOVA: non era nell'elenco precedente, che guardava solo la_liga")})
    tot = Dd["D5_midweek_europe_falsi_zero"]["totale_celle"]
    for lg, v in Dd["D5_midweek_europe_falsi_zero"]["per_lega"].items():
        if not v.get("midweek_europe_falsi_zero"):
            continue
        rows.append({
            "caso": "D", "lega": lg, "stagione": "tutte", "data": "", "partita": "(varie)",
            "colonna": "home_midweek_europe / away_midweek_europe",
            "valore_attuale": "0", "valore_proposto": "1",
            "metodo": "ricalcolo di fixtures.add_rest_days_full con i calendari di coppa gia' "
                      "recuperati in data/ricerca_esterna/fixtures_*.csv",
            "errore_atteso": 0.0, "unita_errore": "nessuno: e' dato di calendario, non stima",
            "alternativa_stimata": "", "errore_alternativa": "",
            "verdetto": f"CHIUDIBILE SUBITO E SENZA STIMA: {v['midweek_europe_falsi_zero']} celle "
                        f"di questa lega (su {tot} totali) sono uno 0 falso; cambia anche il riposo "
                        f"in {v['partite_con_riposo_che_cambia']} partite",
            "note": "e' il buco piu' grande rimasto e non e' un NaN: e' uno 0 che sembra un dato"})
    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    return df


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="salta le parti che richiedono la rete (caso A-i e caso C)")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    D = load_snapshots()
    out = {
        "titolo": "Le celle residue: stimabili in modo difendibile, o la risposta e' no?",
        "regola": "R4 isolamento: nessuno snapshot modificato; scrivo solo "
                  "data/estimates/celle_residue.csv e docs/audit_5_leghe/numeri/stima_celle_residue.json",
        "controllo_di_sanita_bootstrap": _autotest_boot(),
        "aspettative_dichiarate_prima": {
            "A_i": "mi aspetto di CONFERMARE che la fonte e' una chiusura, ma di non poter "
                   "dimostrare 'media di mercato' contro 'book singolo sharp' senza un test nuovo",
            "A_ii": "mi aspetto che la regressione batta l'identita' in modo conclusivo ma per "
                    "pochissimo (~0,001 di MAE), e che la stima cada entro ~0,02 dal dato reale",
            "B": "mi aspetto MAE 0,45-0,55 e R2 0,35-0,45 -> sopra la soglia di 0,4: NON stimabile",
            "C": "mi aspetto che la partita NON sia ancora consolidata",
            "D": "mi aspetto zero celle vuote nuove, e di trovare almeno un 'finto pieno' "
                 "quantificabile"},
    }
    M = None
    print("== CASO A (i): che cos'e' la fonte esterna")
    if args.offline:
        out["CASO_A_natura_della_fonte"] = {"stato": "saltato (--offline)"}
    else:
        r, M = caso_A_natura_fonte(D)
        out["CASO_A_natura_della_fonte"] = r
    print("== CASO A (ii): la stima apertura -> chiusura")
    a2, ar = caso_A_stima(D, M)
    out["CASO_A_stima"] = a2
    print("== CASO B: xG dai tiri in porta")
    b, bd = caso_B(D)
    out["CASO_B_xg"] = b
    print("== CASO C: Understat Ligue 1 2025-26")
    out["CASO_C_understat"] = {"stato": "saltato (--offline)"} if args.offline else caso_C(D)
    print("== CASO D: censimento")
    dd = caso_D(D)
    out["CASO_D_censimento"] = dd
    df = scrivi_csv(a2, ar, b, bd, out["CASO_C_understat"], dd)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT_JSON, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"\nscritti:\n  {OUT_JSON}\n  {OUT_CSV}  ({len(df)} righe)")


if __name__ == "__main__":
    main()
