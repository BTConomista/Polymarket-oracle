"""Ricostruire il TIRO IN PORTA di football-data dal dato tiro-per-tiro Understat.

DOMANDA (mai misurata nel progetto): si puo' COSTRUIRE `home_sot`/`away_sot`
(football-data) dalla lista tiri di Understat, e con quale errore?

Il caso che l'ha fatta nascere: bundesliga 2024-25, Union Berlin - Bochum del
14/12/2024 (Understat id 27866) e' l'unica partita delle 5 leghe senza tiri in
porta nello snapshot. Understat ha la lista tiro-per-tiro completa. I valori non
sono mai stati inseriti perche' "tiro in porta" secondo football-data e "tiro"
secondo Understat sono definizioni diverse: nessuno aveva misurato QUANTO.

METODO
------
1. Vocabolario di Understat (campo `result` di ogni tiro): Goal, SavedShot,
   MissedShots, BlockedShot, ShotOnPost, OwnGoal. Gli OwnGoal compaiono nella
   lista della squadra che li subisce (chi ha deviato nella propria porta):
   football-data li conta come tiro in porta di chi ne BENEFICIA (fatto gia'
   verificato nel progetto, audit_anomalie.check_xg).
2. Regole candidate (R1..R8, vedi RULES) piu' una regola STIMATA dai dati
   (minimi quadrati non negativi sui conteggi per categoria), validata
   FUORI CAMPIONE (leave-one-league-out e leave-one-season-out).
3. Confronto contro il dato reale su un campione CASUALE STRATIFICATO per
   lega x stagione (45 celle). Unita' statistica = la SQUADRA-partita
   (2 per partita). Metriche: quota di corrispondenze esatte, MAE, bias,
   distribuzione dello scarto; tutto per lega e per stagione.
4. Controllo di sanita' obbligatorio: le somme dei tiri di football-data in
   Serie A (HS 5.359 / 4.269 / 5.326 nel 2017-18 / 2018-19 / 2021-22) devono
   essere riprodotte dal mio apparato.

ESITO MISURATO (campione 900 partite = 1.800 squadra-partita, 20 per ognuna
delle 45 celle lega x stagione; piu' un CENSIMENTO di tutte le 305 partite di
bundesliga 2024-25):

  R1 = Goal + SavedShot  ->  86.4% di corrispondenze ESATTE, 97.7% entro +-1,
                             MAE 0.171, bias -0.139 (football-data conta appena
                             di piu' di quanto Understat classifichi in porta).
  Aggiungere gli AUTOGOL degli avversari (R3) PEGGIORA in modo conclusivo
  (bootstrap appaiato B=10.000: delta-MAE +0.0283, CI95 [+0.0189, +0.0383]).
  Cioe': la nota del progetto secondo cui football-data conterebbe l'autogol
  come tiro in porta di chi ne beneficia NON e' una regola generale (succede
  nel 15% dei casi; nell'80% il tiro in porta e' esattamente Goal+SavedShot).
  Aggiungere il palo (R2) peggiora ancora di piu'.
  Una regola a pesi STIMATI (NNLS su tutte le categorie), validata fuori
  campione leave-one-league-out e leave-one-season-out, converge su R1
  (pesi 1.018 / 0.994 / ~0) e NON la batte: R1 e' un tetto, non una scelta
  fortunata fra molte.

  L'unica epoca dove R1 crolla e' la SERIE A 2018-19 / 2019-20 / 2020-21
  (37.5% / 32.5% / 50.0% di corrispondenze esatte, bias -0.83 / -0.88 / -0.70):
  li' football-data cambio' fornitore. Lo si vede anche sui tiri TOTALI, dove
  Understat e football-data coincidono in 42 celle su 45 (|scarto| <= 0.2 tiri
  per squadra) e divergono SOLO in Serie A 2018-19 (+3.40), 2019-20 (+3.65) e
  2020-21 (+1.05): esattamente i tiri BLOCCATI (3.48 / 3.40 / 3.00), che quel
  fornitore non contava fra i tiri e contava, in parte, fra quelli in porta.

ISOLAMENTO (R4): questo script scrive SOLO in docs/audit_5_leghe/numeri/stima_sot_understat.json.
La cache dei JSON scaricati va nello scratchpad di sessione (variabile SOT_CACHE),
NON in data/fonti/understat_match/ (che viene solo LETTA).

Uso:
    python scripts/stima_sot_understat.py --per-cella 20   # scarica + analizza
    python scripts/stima_sot_understat.py --solo-analisi   # solo cache
Il download completo (900 + 305 partite) e' ~2 s a partita con throttle 1.5 s:
conviene popolare la cache a blocchi (SOT_CACHE=<dir>) e poi girare --solo-analisi.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

from src.data import sources  # noqa: E402
import nuove_leghe  # noqa: E402

nuove_leghe.registra()

from _fase52_common import boot  # noqa: E402

LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
SNAP = {
    "serie_a": ROOT / "data" / "serie_a_matches.csv",
    "premier_league": ROOT / "data" / "premier_league_matches.csv",
    "la_liga": ROOT / "data" / "la_liga_matches.csv",
    "bundesliga": ROOT / "data" / "bundesliga_matches.csv",
    "ligue_1": ROOT / "data" / "ligue_1_matches.csv",
}
UND_DIR = ROOT / "data" / "fonti" / "understat"
UND_MATCH_RO = ROOT / "data" / "fonti" / "understat_match"  # sola lettura
FD_DIR = ROOT / "data" / "fonti" / "football_data"
OUT = ROOT / "docs" / "audit_5_leghe" / "numeri" / "stima_sot_understat.json"

_SCRATCH = os.environ.get(
    "SOT_CACHE",
    "/tmp/claude-0/-home-user-Polymarket-oracle/"
    "a5fc6f34-4b89-5526-a47c-c72cff4ac735/scratchpad/understat_match")
CACHE = Path(_SCRATCH)

SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
CATS = ["Goal", "SavedShot", "MissedShots", "BlockedShot", "ShotOnPost", "OwnGoal"]

# La partita da riempire (o non riempire).
TARGET = {"league": "bundesliga", "season": "2425", "understat_id": "27866",
          "home_team": "Union Berlin", "away_team": "Bochum",
          "date": "2024-12-14"}


# --------------------------------------------------------------------------- #
# Regole candidate: da un dict di conteggi -> tiri in porta di quella squadra.
# `c` = conteggi della squadra, `o` = conteggi dell'AVVERSARIO.
# --------------------------------------------------------------------------- #
RULES: dict[str, object] = {
    # R1: la definizione "da manuale" -- in porta = finito in rete o parato.
    "R1_goal_saved": lambda c, o: c["Goal"] + c["SavedShot"],
    # R2: R1 + legno. Alcuni provider contano il palo come "in porta".
    "R2_R1_post": lambda c, o: c["Goal"] + c["SavedShot"] + c["ShotOnPost"],
    # R3: R1 + gli autogol REGALATI dagli avversari (football-data li conta
    #     come tiro in porta della squadra che ne beneficia).
    "R3_R1_og": lambda c, o: c["Goal"] + c["SavedShot"] + o["OwnGoal"],
    # R4: R2 + autogol avversari.
    "R4_R1_post_og": lambda c, o: c["Goal"] + c["SavedShot"] + c["ShotOnPost"] + o["OwnGoal"],
    # R5: R3 + i tiri respinti da un difensore. Ipotesi "provider largo":
    #     il salto di HST/HS in Serie A 2018-20 suggerisce che in quell'epoca
    #     qualcuno contasse anche i BlockedShot.
    "R5_R3_blocked": lambda c, o: c["Goal"] + c["SavedShot"] + o["OwnGoal"] + c["BlockedShot"],
    # R6: R5 + legno = tutto tranne i tiri fuori.
    "R6_tutto_meno_fuori": lambda c, o: (c["Goal"] + c["SavedShot"] + c["ShotOnPost"]
                                         + c["BlockedShot"] + o["OwnGoal"]),
    # R7: solo i gol (limite inferiore assoluto, serve da riferimento).
    "R7_solo_gol": lambda c, o: c["Goal"] + o["OwnGoal"],
    # R8: tutti i tiri Understat della squadra (limite superiore).
    "R8_tutti_i_tiri": lambda c, o: sum(c[k] for k in CATS if k != "OwnGoal") + o["OwnGoal"],
}


# --------------------------------------------------------------------------- #
# Dati
# --------------------------------------------------------------------------- #
def _und_year(season: str) -> int:
    return 2000 + int(season[:2])


def snapshot(league: str) -> pd.DataFrame:
    df = pd.read_csv(SNAP[league], parse_dates=["date"])
    df["league"] = league
    df["season"] = df["season"].astype(str).str.zfill(4)
    return df


def understat_index(league: str, season: str) -> pd.DataFrame:
    """id Understat + squadre canoniche + data, per una stagione."""
    path = UND_DIR / f"{league}_{_und_year(season)}.json"
    data = json.loads(path.read_text())
    rows = []
    for m in data.get("dates", []):
        if not m.get("isResult"):
            continue
        rows.append({
            "league": league, "season": season, "understat_id": str(m["id"]),
            "home_team": sources.canonical_team(str(m["h"]["title"]).strip()),
            "away_team": sources.canonical_team(str(m["a"]["title"]).strip()),
            "u_date": pd.to_datetime(m["datetime"]).normalize(),
            "u_hg": int(m["goals"]["h"]), "u_ag": int(m["goals"]["a"]),
        })
    return pd.DataFrame(rows)


def build_join() -> pd.DataFrame:
    """Tabella partita-per-partita: snapshot (con i SOT veri) + id Understat.

    Chiave: (lega, stagione, casa, trasferta) -- unica in un girone all'italiana.
    Verificata anche sui gol: se i gol non coincidono, la riga viene scartata
    (accoppiamento sbagliato).
    """
    out = []
    for lg in LEAGUES:
        snap = snapshot(lg)
        for s in SEASONS:
            sub = snap[snap.season == s]
            if sub.empty:
                continue
            idx = understat_index(lg, s)
            m = sub.merge(idx, on=["league", "season", "home_team", "away_team"],
                          how="left", suffixes=("", "_u"))
            out.append(m)
    df = pd.concat(out, ignore_index=True)
    df["gol_ok"] = (df.u_hg == df.home_goals) & (df.u_ag == df.away_goals)
    return df


# --------------------------------------------------------------------------- #
# Fetch tiro-per-tiro (cache, throttle 1.5s)
# --------------------------------------------------------------------------- #
def match_shots(match_id: str, *, allow_net: bool = True,
                throttle: float = 1.5) -> dict | None:
    for d in (UND_MATCH_RO, CACHE):
        p = d / f"{match_id}.json"
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
    if not allow_net:
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    url = f"https://understat.com/getMatchData/{match_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip",
        "X-Requested-With": "XMLHttpRequest"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        json.loads(raw)  # valida prima di scrivere
        (CACHE / f"{match_id}.json").write_bytes(raw)
        time.sleep(throttle)
    except Exception:
        return None
    try:
        return json.loads((CACHE / f"{match_id}.json").read_text())
    except Exception:
        return None


def counts(data: dict) -> tuple[dict, dict]:
    """Conteggi per categoria, lato casa e lato trasferta."""
    def cc(lst):
        k = Counter(x.get("result") for x in lst)
        return {c: int(k.get(c, 0)) for c in CATS}
    return cc(data["shots"]["h"]), cc(data["shots"]["a"])


def fd_shots_index() -> pd.DataFrame:
    """Tiri TOTALI di football-data (HS/AS) per partita: servono a distinguere
    'Understat ha perso dei tiri' da 'le due fonti classificano diversamente'."""
    rows = []
    for lg in LEAGUES:
        for s in SEASONS:
            p = FD_DIR / f"{lg}_{s}.csv"
            if not p.exists():
                continue
            raw = pd.read_csv(p, encoding="latin-1").dropna(subset=["HomeTeam", "AwayTeam"])
            if not {"HS", "AS"}.issubset(raw.columns):
                continue
            for r in raw.itertuples(index=False):
                rows.append({"league": lg, "season": s,
                             "home_team": sources.canonical_team(str(r.HomeTeam).strip()),
                             "away_team": sources.canonical_team(str(r.AwayTeam).strip()),
                             "fd_hs": float(r.HS), "fd_as": float(r.AS)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Campione
# --------------------------------------------------------------------------- #
def sample(df: pd.DataFrame, per_cella: int, seed: int = 20260726) -> pd.DataFrame:
    ok = df[df.understat_id.notna() & df.gol_ok
            & df.home_sot.notna() & df.away_sot.notna()].copy()
    rng = np.random.default_rng(seed)
    parts = []
    for (lg, s), g in ok.groupby(["league", "season"]):
        n = min(per_cella, len(g))
        idx = rng.choice(len(g), size=n, replace=False)
        parts.append(g.iloc[np.sort(idx)])
    return pd.concat(parts, ignore_index=True)


def raccogli(smp: pd.DataFrame, *, allow_net: bool, throttle: float,
             progress: Path | None) -> pd.DataFrame:
    """Una riga per SQUADRA-partita, con i conteggi Understat e il SOT vero."""
    rows, miss = [], 0
    for i, r in enumerate(smp.itertuples(index=False), 1):
        data = match_shots(str(r.understat_id), allow_net=allow_net, throttle=throttle)
        if data is None or "shots" not in data:
            miss += 1
            continue
        ch, ca = counts(data)
        for side, c, o, sot in (("home", ch, ca, r.home_sot), ("away", ca, ch, r.away_sot)):
            row = {"league": r.league, "season": r.season, "side": side,
                   "understat_id": str(r.understat_id),
                   "match": f"{r.home_team}-{r.away_team}",
                   "sot_fd": float(sot)}
            row.update({f"n_{k}": c[k] for k in CATS})
            row["n_og_opp"] = o["OwnGoal"]
            row["n_tiri_understat"] = sum(c[k] for k in CATS if k != "OwnGoal")
            row["home_team"], row["away_team"] = r.home_team, r.away_team
            for name, fn in RULES.items():
                row[name] = int(fn(c, o))
            rows.append(row)
        if progress is not None and i % 25 == 0:
            pd.DataFrame(rows).to_csv(progress, index=False)
            print(f"  ... {i}/{len(smp)} partite ({miss} non scaricate)", flush=True)
    out = pd.DataFrame(rows)
    if progress is not None and len(out):
        out.to_csv(progress, index=False)
    return out


# --------------------------------------------------------------------------- #
# Valutazione
# --------------------------------------------------------------------------- #
def metriche(y: np.ndarray, p: np.ndarray) -> dict:
    d = p - y
    return {"n": int(len(y)),
            "esatte": float((d == 0).mean()),
            "entro_1": float((np.abs(d) <= 1).mean()),
            "mae": float(np.abs(d).mean()),
            "bias": float(d.mean()),
            "sd_scarto": float(d.std(ddof=1)) if len(d) > 1 else float("nan")}


def valuta(dat: pd.DataFrame) -> dict:
    y = dat.sot_fd.values.astype(float)
    res = {}
    for name in RULES:
        res[name] = metriche(y, dat[name].values.astype(float))
    return res


def nnls(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Minimi quadrati con pesi >= 0 (proiezione iterativa: e' un problema
    piccolo e ben condizionato; scipy.optimize.nnls se disponibile)."""
    try:
        from scipy.optimize import nnls as _n
        return _n(X, y)[0]
    except Exception:
        w = np.linalg.lstsq(X, y, rcond=None)[0]
        return np.clip(w, 0, None)


FEATS = ["n_Goal", "n_SavedShot", "n_MissedShots", "n_BlockedShot",
         "n_ShotOnPost", "n_og_opp"]


def regola_stimata(dat: pd.DataFrame, gruppo: str) -> dict:
    """Regola a pesi stimati, validata FUORI CAMPIONE lasciando fuori un
    `gruppo` per volta (lega o stagione). Il peso e' un 'quanto conta questa
    categoria come tiro in porta'."""
    y = dat.sot_fd.values.astype(float)
    X = dat[FEATS].values.astype(float)
    pred = np.full(len(y), np.nan)
    pesi = {}
    for g in sorted(dat[gruppo].unique()):
        te = (dat[gruppo] == g).values
        w = nnls(X[~te], y[~te])
        pred[te] = X[te] @ w
        pesi[str(g)] = {f: round(float(v), 4) for f, v in zip(FEATS, w)}
    w_all = nnls(X, y)
    return {"pesi_per_fold": pesi,
            "pesi_su_tutto": {f: round(float(v), 4) for f, v in zip(FEATS, w_all)},
            "oos_continuo": metriche(y, pred),
            "oos_arrotondato": metriche(y, np.rint(pred))}


def per_gruppo(dat: pd.DataFrame, col: str, regole: list[str]) -> dict:
    out = {}
    for g, sub in dat.groupby(col):
        y = sub.sot_fd.values.astype(float)
        out[str(g)] = {r: metriche(y, sub[r].values.astype(float)) for r in regole}
        out[str(g)]["_n_squadra_partita"] = int(len(sub))
    return out


def confronto_appaiato(dat: pd.DataFrame, a: str, b: str, seed: int = 7) -> dict:
    """|errore(a)| - |errore(b)| appaiato, bootstrap B=10.000. Negativo = a meglio."""
    y = dat.sot_fd.values.astype(float)
    d = np.abs(dat[a].values - y) - np.abs(dat[b].values - y)
    rng = np.random.default_rng(seed)
    m, lo, hi, p = boot(d.astype(float), rng)
    return {"delta_mae": m, "ci95": [lo, hi], "frac_neg": p,
            "conclusivo": bool(hi < 0 or lo > 0)}


def matrice(dat: pd.DataFrame, regola: str) -> dict:
    """Corrispondenze esatte e bias per LEGA x STAGIONE (n=40 per cella)."""
    e, b = {}, {}
    for (lg, s), g in dat.groupby(["league", "season"]):
        d = g[regola].values - g.sot_fd.values
        e.setdefault(str(s), {})[lg] = round(float((d == 0).mean()), 3)
        b.setdefault(str(s), {})[lg] = round(float(d.mean()), 3)
    return {"esatte": e, "bias": b}


# --------------------------------------------------------------------------- #
# Diagnostiche: perche' sbaglia quando sbaglia
# --------------------------------------------------------------------------- #
def diagnostica_autogol(dat: pd.DataFrame) -> dict:
    """Il progetto afferma che football-data conta l'AUTOGOL come tiro in porta
    di chi ne beneficia (audit_anomalie.check_xg). Qui si mette alla prova."""
    sub = dat[dat.n_og_opp > 0]
    if sub.empty:
        return {"n": 0}
    d1 = sub.R1_goal_saved.values - sub.sot_fd.values
    d3 = sub.R3_R1_og.values - sub.sot_fd.values
    # se FD contasse SEMPRE l'autogol, R1 sbaglierebbe di -1 (per autogol) e R3 no
    return {
        "n_squadra_partita_con_autogol_avversario": int(len(sub)),
        "R1_esatte": float((d1 == 0).mean()), "R3_esatte": float((d3 == 0).mean()),
        "R1_bias": float(d1.mean()), "R3_bias": float(d3.mean()),
        "quota_compatibile_con_conteggio_autogol": float((d1 == -sub.n_og_opp.values).mean()),
        "quota_incompatibile_R1_esatta": float((d1 == 0).mean()),
        "esatte_globali_per_confronto": float(
            (dat.R1_goal_saved.values == dat.sot_fd.values).mean()),
    }


def diagnostica_completezza(dat: pd.DataFrame) -> dict:
    """Quando R1 sbaglia, e' perche' Understat ha PERSO dei tiri o perche' le due
    fonti CLASSIFICANO diversamente? Confronto sui tiri TOTALI (FD HS/AS)."""
    fd = fd_shots_index()
    m = dat.merge(fd, on=["league", "season", "home_team", "away_team"], how="left")
    m["fd_tiri"] = np.where(m.side == "home", m.fd_hs, m.fd_as)
    m = m[m.fd_tiri.notna()].copy()
    m["err"] = m.R1_goal_saved - m.sot_fd
    m["err_tot"] = m.n_tiri_understat - m.fd_tiri
    out = {"n": int(len(m)),
           "corr_err_sot_vs_err_totali": float(np.corrcoef(m.err, m.err_tot)[0, 1])}
    for tag, sub in (("R1_esatta", m[m.err == 0]), ("R1_sbagliata", m[m.err != 0])):
        out[tag] = {"n": int(len(sub)),
                    "media_tiri_understat": float(sub.n_tiri_understat.mean()),
                    "media_tiri_fd": float(sub.fd_tiri.mean()),
                    "media_scarto_tiri_totali": float(sub.err_tot.mean())}
    # epoca "larga" di football-data (Serie A 2018-21): l'ipotesi e' che in
    # quelle stagioni il fornitore ESCLUDESSE i tiri respinti dal conteggio dei
    # tiri (tiri_fd ~ tiri_understat - bloccati) e usasse una definizione di
    # "in porta" piu' larga (bias_sot molto negativo).
    sa = m[(m.league == "serie_a")]
    out["serie_a_per_stagione"] = {
        str(s): {"sot_fd": round(float(g.sot_fd.mean()), 2),
                 "R1": round(float(g.R1_goal_saved.mean()), 2),
                 "tiri_fd": round(float(g.fd_tiri.mean()), 2),
                 "tiri_understat": round(float(g.n_tiri_understat.mean()), 2),
                 "tiri_understat_meno_bloccati": round(
                     float((g.n_tiri_understat - g.n_BlockedShot).mean()), 2),
                 "bloccati_understat": round(float(g.n_BlockedShot.mean()), 2),
                 "bias_sot": round(float(g.err.mean()), 3),
                 "esatte": round(float((g.err == 0).mean()), 3)}
        for s, g in sa.groupby("season")}
    # lo stesso confronto su tutte le leghe, per mostrare che l'anomalia e' SOLO
    # della Serie A 2018-21 e non un difetto del metodo
    out["scarto_tiri_totali_per_lega_stagione"] = {
        str(s): {lg: round(float((g.n_tiri_understat - g.fd_tiri).mean()), 2)
                 for lg, g in gs.groupby("league")}
        for s, gs in m.groupby("season")}
    return out


def controlli_negativi(dat: pd.DataFrame, seed: int = 99) -> dict:
    """Prove che l'86% NON e' un artefatto (i tiri in porta sono interi piccoli:
    anche indovinare a caso ne azzecca una quota non trascurabile).

    - PLACEBO: la regola applicata ai tiri di UN'ALTRA partita della stessa
      lega-stagione. Se il metodo misurasse solo 'numeri piccoli simili',
      il placebo andrebbe quasi altrettanto bene.
    - MEDIA: predire sempre la media (arrotondata) della lega-stagione.
    - MODA: predire sempre il valore piu' frequente della lega-stagione.
    """
    rng = np.random.default_rng(seed)
    y = dat.sot_fd.values.astype(float)
    pl = np.empty(len(dat)); me = np.empty(len(dat)); mo = np.empty(len(dat))
    for _, g in dat.groupby(["league", "season"]):
        i = g.index.values
        perm = rng.permutation(len(i))
        # evita il punto fisso (una riga accoppiata con se stessa)
        for k in range(len(i)):
            if perm[k] == k and len(i) > 1:
                j = (k + 1) % len(i)
                perm[k], perm[j] = perm[j], perm[k]
        pl[dat.index.get_indexer(i)] = dat.loc[i[perm], "R1_goal_saved"].values
        me[dat.index.get_indexer(i)] = round(float(g.sot_fd.mean()))
        mo[dat.index.get_indexer(i)] = float(g.sot_fd.mode().iloc[0])
    return {"placebo_altra_partita": metriche(y, pl),
            "baseline_media_lega_stagione": metriche(y, me),
            "baseline_moda_lega_stagione": metriche(y, mo),
            "R1_per_confronto": metriche(y, dat.R1_goal_saved.values.astype(float))}


def sensibilita_volume(dat: pd.DataFrame) -> dict:
    """La partita da riempire ha 22 tiri in casa: molto sopra la media (12.3).
    R1 regge sui volumi alti? (Le sue rare cadute stanno proprio li'.)"""
    b = pd.cut(dat.n_tiri_understat, [-1, 7, 10, 13, 16, 19, 99],
               labels=["0-7", "8-10", "11-13", "14-16", "17-19", "20+"])
    out = {}
    for k, g in dat.groupby(b, observed=True):
        d = g.R1_goal_saved.values - g.sot_fd.values
        out[str(k)] = {"n": int(len(g)), "esatte": round(float((d == 0).mean()), 3),
                       "entro_1": round(float((np.abs(d) <= 1).mean()), 3),
                       "bias": round(float(d.mean()), 3)}
    return out


def contesto_partita_mancante() -> dict:
    """Cosa ha davvero football-data su quella riga (non solo i tiri in porta)."""
    p = FD_DIR / f"{TARGET['league']}_{TARGET['season']}.csv"
    raw = pd.read_csv(p, encoding="latin-1").dropna(subset=["HomeTeam", "AwayTeam"])
    raw["h"] = raw.HomeTeam.map(lambda x: sources.canonical_team(str(x).strip()))
    raw["a"] = raw.AwayTeam.map(lambda x: sources.canonical_team(str(x).strip()))
    r = raw[(raw.h == TARGET["home_team"]) & (raw.a == TARGET["away_team"])]
    if r.empty:
        return {}
    r = r.iloc[0]
    stat_cols = [c for c in ["HS", "AS", "HST", "AST", "HC", "AC", "HF", "AF",
                             "HY", "AY", "HR", "AR"] if c in raw.columns]
    return {
        "football_data_risultato": [int(r.FTHG), int(r.FTAG)],
        "snapshot_risultato_campo": [1, 1],
        "football_data_statistiche": {c: (None if pd.isna(r[c]) else float(r[c]))
                                      for c in stat_cols},
        "tutte_le_statistiche_vuote": bool(all(pd.isna(r[c]) for c in stat_cols)),
        "nota": ("football-data riporta il risultato del TRIBUNALE (0-2) e lascia "
                 "vuoto TUTTO il blocco statistico, non solo i tiri in porta. Lo "
                 "snapshot tiene il risultato del CAMPO (1-1, regola R1 del "
                 "cantiere): la lista tiri di Understat e' l'unico record del campo."),
    }


def censimento(league: str, season: str, *, allow_net: bool, throttle: float) -> dict:
    """TUTTE le partite di una lega-stagione (non un campione): serve a dare
    l'errore atteso nella cella esatta dove vive la partita mancante."""
    j = build_join()
    sub = j[(j.league == league) & (j.season == season) & j.understat_id.notna()
            & j.gol_ok & j.home_sot.notna() & j.away_sot.notna()]
    dat = raccogli(sub, allow_net=allow_net, throttle=throttle, progress=None)
    if dat.empty:
        return {"n": 0}
    y = dat.sot_fd.values.astype(float)
    out = {"league": league, "season": season, "partite": int(len(dat) // 2)}
    for r in ("R1_goal_saved", "R3_R1_og", "R2_R1_post"):
        out[r] = metriche(y, dat[r].values.astype(float))
    d = dat.R1_goal_saved.values - y
    out["distribuzione_scarto_R1"] = {str(int(k)): int(v)
                                      for k, v in sorted(Counter(d).items())}
    rng = np.random.default_rng(11)
    ok = (d == 0).astype(float)
    mu, lo, hi, _ = boot(ok, rng)
    out["esatte_ci95"] = [lo, hi]
    out["per_volume_tiri"] = sensibilita_volume(dat)
    # la RIGA che si proporrebbe ha due celle: quanto spesso sono esatte
    # ENTRAMBE? (e' il numero che conta per decidere se riempire la riga)
    dat = dat.copy()
    dat["ok"] = (dat.R1_goal_saved == dat.sot_fd)
    dat["ok1"] = (dat.R1_goal_saved - dat.sot_fd).abs() <= 1
    per_match = dat.groupby("understat_id")[["ok", "ok1"]].all()
    mu, lo, hi, _ = boot(per_match.ok.values.astype(float), np.random.default_rng(13))
    out["riga_intera_esatta"] = {"quota": float(per_match.ok.mean()), "ci95": [lo, hi],
                                 "entro_1_su_entrambi": float(per_match.ok1.mean()),
                                 "n_partite": int(len(per_match))}
    return out


# --------------------------------------------------------------------------- #
# Controllo di sanita' + il salto di raccolta di football-data
# --------------------------------------------------------------------------- #
def sanita_football_data() -> dict:
    """Riproduce numeri NOTI del progetto e quantifica il cambio di raccolta."""
    noti = {"1718": 5359, "1819": 4269, "2122": 5326}
    check, tab = {}, []
    for lg in LEAGUES:
        for s in SEASONS:
            p = FD_DIR / f"{lg}_{s}.csv"
            if not p.exists():
                continue
            raw = pd.read_csv(p, encoding="latin-1").dropna(subset=["HomeTeam", "AwayTeam"])
            if not {"HS", "HST"}.issubset(raw.columns):
                continue
            hs, hst = float(raw.HS.sum()), float(raw.HST.sum())
            aS, ast = float(raw.AS.sum()), float(raw.AST.sum())
            tab.append({"league": lg, "season": s, "n": int(len(raw)),
                        "HS": hs, "HST": hst, "AS": aS, "AST": ast,
                        "quota_in_porta": round((hst + ast) / (hs + aS), 4)})
            if lg == "serie_a" and s in noti:
                check[s] = {"atteso_HS": noti[s], "misurato_HS": int(hs),
                            "ok": int(hs) == noti[s]}
    return {"controllo_numeri_noti_serie_a_HS": check,
            "tabella_tiri_football_data": tab}


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cella", type=int, default=20)
    ap.add_argument("--throttle", type=float, default=1.5)
    ap.add_argument("--solo-analisi", action="store_true")
    ap.add_argument("--progress", default=str(CACHE.parent / "sot_progress.csv"))
    args = ap.parse_args()

    print("1) join snapshot <-> Understat", flush=True)
    j = build_join()
    cop = {
        "partite_snapshot": int(len(j)),
        "con_id_understat": int(j.understat_id.notna().sum()),
        "gol_coerenti": int((j.understat_id.notna() & j.gol_ok).sum()),
        "sot_mancanti_snapshot": int(j.home_sot.isna().sum() + j.away_sot.isna().sum()),
        "partite_senza_sot": [
            {"league": r.league, "season": r.season, "date": str(r.date.date()),
             "match": f"{r.home_team}-{r.away_team}",
             "understat_id": None if pd.isna(r.understat_id) else str(r.understat_id)}
            for r in j[j.home_sot.isna() | j.away_sot.isna()].itertuples(index=False)],
    }
    print("   ", {k: v for k, v in cop.items() if k != "partite_senza_sot"}, flush=True)

    print("2) campione stratificato", flush=True)
    smp = sample(j, args.per_cella)
    print(f"    {len(smp)} partite ({args.per_cella}/cella x 45 celle)", flush=True)

    print("3) raccolta tiro-per-tiro", flush=True)
    dat = raccogli(smp, allow_net=not args.solo_analisi, throttle=args.throttle,
                   progress=Path(args.progress))
    print(f"    {len(dat)} squadra-partita", flush=True)

    print("4) valutazione", flush=True)
    glob = valuta(dat)
    ordine = sorted(RULES, key=lambda r: (-glob[r]["esatte"], glob[r]["mae"]))
    best = ordine[0]

    # epoca: le stagioni in cui football-data conta "largo" (vedi sanita)
    dat = dat.copy()
    dat["epoca"] = np.where(dat.season.isin(["1819", "1920"]), "1819-1920", "altre")

    res = {
        "copertura": cop,
        "campione": {"per_cella": args.per_cella, "partite": int(len(smp)),
                     "squadra_partita": int(len(dat)),
                     "per_lega": dat.groupby("league").size().to_dict(),
                     "per_stagione": dat.groupby("season").size().to_dict()},
        "regole": {k: v for k, v in glob.items()},
        "classifica": ordine,
        "migliore": best,
        "per_lega": per_gruppo(dat, "league", ordine[:4]),
        "per_stagione": per_gruppo(dat, "season", ordine[:4]),
        "per_epoca": per_gruppo(dat, "epoca", ordine[:4]),
        "confronti_appaiati": {
            f"{a}_vs_{b}": confronto_appaiato(dat, a, b)
            for a, b in [(ordine[0], ordine[1]), ("R3_R1_og", "R1_goal_saved"),
                         ("R4_R1_post_og", "R3_R1_og"), ("R5_R3_blocked", "R3_R1_og")]},
        "regola_stimata_loo_lega": regola_stimata(dat, "league"),
        "regola_stimata_loo_stagione": regola_stimata(dat, "season"),
        "matrice_lega_stagione": matrice(dat, best),
        "distribuzione_scarto": {str(int(k)): int(v) for k, v in sorted(
            Counter(dat[best].values - dat.sot_fd.values).items())},
        "diagnostica_autogol": diagnostica_autogol(dat),
        "diagnostica_completezza": diagnostica_completezza(dat),
        "controlli_negativi": controlli_negativi(dat),
        "sensibilita_volume_tiri": sensibilita_volume(dat),
        "quante_regole_provate": {"fisse": len(RULES), "stimate": 2,
                                  "nota": ("R1 e' definita a priori dalla "
                                           "semantica, non scelta per griglia; "
                                           "la stimata NNLS converge su R1")},
        "sanita": sanita_football_data(),
    }

    # regola migliore stimata per EPOCA (fuori campione per stagione)
    per_ep = {}
    for ep, sub in dat.groupby("epoca"):
        if len(sub) > 50:
            per_ep[ep] = regola_stimata(sub, "season")
    res["regola_stimata_per_epoca"] = per_ep

    print("5) censimento della cella della partita mancante", flush=True)
    res["censimento_cella"] = censimento(TARGET["league"], TARGET["season"],
                                         allow_net=not args.solo_analisi,
                                         throttle=args.throttle)

    print("6) la partita mancante", flush=True)
    data = match_shots(TARGET["understat_id"], allow_net=not args.solo_analisi,
                       throttle=args.throttle)
    if data:
        ch, ca = counts(data)
        cens = res["censimento_cella"].get(best, {})
        stima = {"conteggi_casa": ch, "conteggi_trasferta": ca,
                 "per_regola": {k: {"home_sot": int(fn(ch, ca)),
                                    "away_sot": int(fn(ca, ch))}
                                for k, fn in RULES.items()},
                 "contesto_football_data": contesto_partita_mancante(),
                 "regola_scelta": best,
                 "stima_home_sot": int(RULES[best](ch, ca)),
                 "stima_away_sot": int(RULES[best](ca, ch)),
                 "errore_atteso_dal_censimento": cens,
                 "errore_atteso_per_lato": {
                     "home_22_tiri": res["sensibilita_volume_tiri"].get("20+"),
                     "away_13_tiri": res["sensibilita_volume_tiri"].get("11-13")},
                 "errore_atteso_dal_campione_stessa_lega":
                     per_gruppo(dat[dat.league == TARGET["league"]], "league", [best]),
                 "verdetto": ("PROPONIBILE (corrispondenza esatta >= 0.70 nella "
                              "cella): resta una STIMA, non un conteggio"
                              if float(cens.get("esatte", 0.0)) >= 0.70
                              else "NON RIEMPIRE: corrispondenza esatta sotto il 70%"),
                 "riga_di_correzione_PROPOSTA": {
                     "file": "data/bundesliga_matches.csv",
                     "chiave": f"{TARGET['season']} {TARGET['date']} "
                               f"{TARGET['home_team']}-{TARGET['away_team']}",
                     "home_sot": int(RULES[best](ch, ca)),
                     "away_sot": int(RULES[best](ca, ch)),
                     "natura": "STIMA (ricostruzione da Understat), non un conteggio",
                     "stato": "PROPOSTA — non applicata (decide l'utente)"}}
        res["partita_mancante"] = {**TARGET, **stima}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nScritto {OUT}", flush=True)
    for r in ordine:
        m = glob[r]
        print(f"  {r:22s} esatte={m['esatte']:.3f} entro1={m['entro_1']:.3f} "
              f"MAE={m['mae']:.3f} bias={m['bias']:+.3f}", flush=True)


if __name__ == "__main__":
    main()
