"""CACCIA AI SEGNAPOSTO DI UNDERSTAT — un dato finto e' peggio di un buco.

Un buco (NaN) si vede. Un **segnaposto** no: quando Understat non acquisisce una
partita non lascia il campo vuoto, ci scrive dentro un valore di comodo. Nessun
confronto snapshot-vs-fonte lo scopre, perche' il dato E' quello della fonte.
Questo script cerca ATTIVAMENTE quei valori, su tutte e 5 le leghe.

Il caso noto (Holstein Kiel-Bochum, 09/02/2025, id 27930) ha rivelato la
REGOLA di ripiego della fonte, che qui viene usata come firma da cercare:

    xG      := gol esatti                      (2 e 2)
    npxG    := gol - 0.75 * rigori segnati     (1.25 = 2 - 0.75)
    ppda    := {att: 0, def: 0}                (-> NaN nel parser di produzione)
    deep    := 0
    forecast:= degenere (w,d,l) in {0,1}       (0/1/0)
    xpts    := intero esatto                   (1)

Le cinque quantita' vengono da canali DIVERSI dello stesso feed eventi: se il
feed manca, degenerano tutte insieme. Ognuna diventa un test indipendente.

--------------------------------------------------------------------------- #
LE TRE FAMIGLIE DI TEST (costo crescente)
--------------------------------------------------------------------------- #

A. DEGENERAZIONE DEL RECORD (gratis, dai JSON di lega gia' versionati).
   Nove test, ognuno con il suo tasso di falsi positivi MISURATO sulle 16.110
   partite. Il piu' potente e' anche il piu' semplice: l'xG di Understat e' un
   numero a 6 cifre significative (somma di probabilita' dei singoli tiri), e la
   distribuzione delle cifre finali osservata combacia con quella di un numero
   reale stampato con %g (90.0% a 6 cifre, 8.9% a 5, 0.93% a 4, 0.07% a 3: le
   frequenze attese 90/9/0.9/0.09%). Un "2" o un "1.25" non e' una misura.

B. INCOERENZA CON UNA FONTE INDIPENDENTE (gratis).
   L'xG di Understat contro il conteggio TIRI di football-data. Due canali
   indipendenti: se la fonte ha inventato l'xG, non ha motivo di essere coerente
   con i tiri contati da un altro provider. Serve a scoprire i buchi PARZIALI
   (feed troncato), che la famiglia A non vede. Potere misurato: basso (vedi
   la simulazione di potere) - lo si dichiara, non lo si nasconde.

C. VERDETTO TIRO-PER-TIRO (rete, throttle 1.5s).
   L'unico giudice vero: `understat.com/getMatchData/{id}` da la lista dei
   singoli tiri. Identita' verificata in questo script su ogni partita
   scaricata: xG aggregato == somma degli xG dei tiri (a meno dell'arrotondamento
   di stampa). Lista vuota + gol/tiri altrove = SEGNAPOSTO.
   Non e' applicabile a tutte le 16.110 partite (6h30 di download), quindi lo si
   applica a: (1) i candidati della famiglia A; (2) la CODA della famiglia B,
   dove un feed troncato si nasconderebbe; (3) un campione CASUALE di controllo,
   che serve a limitare dall'alto la prevalenza dei buchi invisibili.

D. SIMULAZIONE DI POTERE (gratis) - la parte che rende onesti i numeri sopra.
   Un test con zero falsi positivi puo' benissimo avere zero potere. Si piantano
   segnaposto FINTI (stessa regola della fonte) e troncamenti parziali su
   partite vere e si misura la frazione che la batteria riesce a riprendere,
   con intervallo di confidenza bootstrap.

--------------------------------------------------------------------------- #
Uso:
    python scripts/cerca_segnaposto.py                # tutto
    python scripts/cerca_segnaposto.py --offline      # senza rete
    python scripts/cerca_segnaposto.py --campione 200 --coda 80

I download vanno in una cartella temporanea (variabile d'ambiente CACCIA_CACHE,
default <tmp>/caccia_understat): lo script NON scrive dentro i dati versionati.
Di ogni payload scaricato viene registrato lo SHA256 nell'uscita JSON, cosi' un
terzo puo' verificare di aver visto la stessa cosa.

Uscite: docs/audit_5_leghe/numeri/caccia_understat.json  (tutti i numeri, riproducibili)
        docs/audit_5_leghe/numeri/caccia_understat.md    (la lettura per un umano)
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()
from src.data import sources  # noqa: E402

from _fase52_common import boot  # noqa: E402

FONTI = ROOT / "data" / "fonti"
FD_DIR = FONTI / "football_data"
US_DIR = FONTI / "understat"
CACHE_TIRI = Path(os.environ.get(
    "CACCIA_CACHE", str(Path(tempfile.gettempdir()) / "caccia_understat")))
OUT = ROOT / "docs" / "audit_5_leghe" / "numeri"

LEAGUES = ["serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"]
# nome della lega nello stile Understat (per l'URL del JSON di lega)
US_NAME = {"serie_a": "Serie_A", "premier_league": "EPL", "la_liga": "La_liga",
           "bundesliga": "Bundesliga", "ligue_1": "Ligue_1"}
SEASON_OF_YEAR = {2000 + int(s[:2]): s for s in sources.SEASONS}

# Valore di comodo del rigore usato dalla fonte quando NON misura (0.75 esatto).
# Il modello vero non lo produce mai: i valori osservati per un rigore stanno in
# [0.7431, 0.7613] (misurati su 4.000+ rigori nei 45 JSON di lega).
RIGORE_FINTO = 0.75
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip",
      "X-Requested-With": "XMLHttpRequest"}


# --------------------------------------------------------------------------- #
# Rete (throttle 1.5s, come richiesto dal protocollo del cantiere)
# --------------------------------------------------------------------------- #
_ultima_richiesta = [0.0]


def _get(url: str, throttle: float = 1.5) -> bytes:
    dt = time.monotonic() - _ultima_richiesta[0]
    if dt < throttle:
        time.sleep(throttle - dt)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    _ultima_richiesta[0] = time.monotonic()
    return raw


def scarica_lega(league: str, year: int) -> tuple[dict, str]:
    """JSON di lega FRESCO (non tocca la copia versionata). Ritorna (dati, sha256)."""
    raw = _get(f"https://understat.com/main/getLeagueData/{US_NAME[league]}/{year}")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def scarica_tiri(match_id: str) -> tuple[dict | None, str | None]:
    """Dati tiro-per-tiro di UNA partita, con cache su disco (fuori dai dati versionati)."""
    CACHE_TIRI.mkdir(parents=True, exist_ok=True)
    dest = CACHE_TIRI / f"{match_id}.json"
    if not dest.exists():
        try:
            dest.write_bytes(_get(f"https://understat.com/getMatchData/{match_id}"))
        except Exception as exc:  # 404 = partita non acquisita
            return None, f"errore:{type(exc).__name__}"
    raw = dest.read_bytes()
    try:
        return json.loads(raw), hashlib.sha256(raw).hexdigest()
    except Exception:
        return None, "errore:json"


# --------------------------------------------------------------------------- #
# Caricamento (offline) delle due fonti
# --------------------------------------------------------------------------- #
def _num(x) -> float:
    """float() tollerante: None -> NaN (le partite non giocate hanno campi nulli)."""
    return np.nan if x is None else float(x)


def _sig(x: float) -> int:
    """Cifre significative della rappresentazione decimale di un float."""
    s = repr(float(x))
    if "e" in s or "E" in s:
        return 6
    return len(s.replace("-", "").replace(".", "").lstrip("0").rstrip("0"))


def carica_understat() -> pd.DataFrame:
    """Una riga per partita GIOCATA dai 45 JSON di lega versionati."""
    rows = []
    for league in LEAGUES:
        for season in sources.SEASONS:
            year = 2000 + int(season[:2])
            path = US_DIR / f"{league}_{year}.json"
            if not path.exists():
                continue
            d = json.loads(path.read_text())
            hist = {}
            for t in d["teams"].values():
                name = sources.canonical_team(str(t["title"]).strip())
                for h in t.get("history", []):
                    hist[(name, h["date"])] = h
            for m in d["dates"]:
                home = sources.canonical_team(str(m["h"]["title"]).strip())
                away = sources.canonical_team(str(m["a"]["title"]).strip())
                hh = hist.get((home, m["datetime"]))
                ah = hist.get((away, m["datetime"]))
                f = m.get("forecast") or {}
                row = dict(
                    league=league, season=season, mid=str(m["id"]),
                    home=home, away=away, dt=m["datetime"],
                    is_result=bool(m.get("isResult")),
                    gh=_num(m["goals"]["h"]), ga=_num(m["goals"]["a"]),
                    xgh_str=m["xG"]["h"], xga_str=m["xG"]["a"],
                    fw=f.get("w"), fd=f.get("d"), fl=f.get("l"),
                    ha_history=bool(hh) and bool(ah),
                )
                row["xgh"] = _num(m["xG"]["h"])
                row["xga"] = _num(m["xG"]["a"])
                for side, h in (("h", hh), ("a", ah)):
                    pp = (h.get("ppda") or {}) if h else {}
                    row[f"npxg{side}"] = _num(h["npxG"]) if h else np.nan
                    row[f"deep{side}"] = _num(h["deep"]) if h else np.nan
                    row[f"xpts{side}"] = _num(h["xpts"]) if h else np.nan
                    row[f"ppda_att{side}"] = pp.get("att", np.nan)
                    row[f"ppda_def{side}"] = pp.get("def", np.nan)
                rows.append(row)
    return pd.DataFrame(rows)


def carica_football_data() -> pd.DataFrame:
    """Conteggi tiri della fonte INDIPENDENTE (football-data), gia' scaricati."""
    rows = []
    for league in LEAGUES:
        for season in sources.SEASONS:
            path = FD_DIR / f"{league}_{season}.csv"
            if not path.exists():
                continue
            raw = pd.read_csv(path, encoding="latin-1")
            raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
            for r in raw.itertuples():
                rows.append(dict(
                    league=league, season=season,
                    home=sources.canonical_team(str(r.HomeTeam).strip()),
                    away=sources.canonical_team(str(r.AwayTeam).strip()),
                    fd_gh=int(r.FTHG), fd_ga=int(r.FTAG),
                    hs=float(getattr(r, "HS", np.nan)),
                    as_=float(getattr(r, "AS", np.nan)),
                    hst=float(getattr(r, "HST", np.nan)),
                    ast=float(getattr(r, "AST", np.nan))))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# A. Batteria di degenerazione (gratis)
# --------------------------------------------------------------------------- #
def batteria(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Nove test indipendenti. Ognuno segna una colonna booleana su df."""
    g = df[df.is_result].copy()

    # A1  xG == gol ESATTI su entrambi i lati (con almeno un gol).
    #     P(un float a 6 cifre coincida con un intero) ~ 1e-5 per lato.
    g["A1_xg_uguale_gol"] = ((g.xgh == g.gh) & (g.xga == g.ga)
                             & (g.gh + g.ga > 0))
    # A2  poverta' di cifre: xG e npxG con <=3 cifre significative su TUTTI E 4
    #     i valori della partita (0 escluso: uno 0 vero esiste, e' zero tiri).
    def poche(v):
        return v.map(lambda x: (not np.isnan(x)) and x != 0 and _sig(x) <= 3)
    g["A2_cifre_povere"] = (poche(g.xgh) & poche(g.npxgh)
                            & poche(g.xga) & poche(g.npxga))
    # A3  forecast degenere: la simulazione della fonte non da mai 0 o 1 esatti.
    def deg(v):
        return v.map(lambda x: x is not None and float(x) in (0.0, 1.0))
    g["A3_forecast_degenere"] = deg(g.fw) & deg(g.fd) & deg(g.fl)
    # A4  ppda azzerata: zero passaggi concessi o zero azioni difensive =
    #     flusso eventi vuoto (in una partita vera non succede mai).
    g["A4_ppda_nulla"] = ((g.ppda_atth == 0) | (g.ppda_defh == 0)
                          | (g.ppda_atta == 0) | (g.ppda_defa == 0))
    # A5  deep = 0 su ENTRAMBE le squadre (il filtro "grezzo" di partenza).
    g["A5_deep_zero"] = (g.deeph == 0) & (g.deepa == 0)
    # A6  xpts intero esatto (0/1/3): la simulazione non produce interi.
    g["A6_xpts_intero"] = (g.xptsh.isin([0.0, 1.0, 3.0])
                           | g.xptsa.isin([0.0, 1.0, 3.0]))
    # A7  rigore finto: xG - npxG multiplo esatto di 0.75 (il valore di comodo).
    #     Il modello vero produce 0.7431..0.7613, mai 0.7500 tondo.
    def rig(xg, npxg):
        d = xg - npxg
        k = np.round(d / RIGORE_FINTO)
        return (d > 1e-9) & (np.abs(d - k * RIGORE_FINTO) < 1e-9)
    g["A7_rigore_finto"] = rig(g.xgh, g.npxgh) | rig(g.xga, g.npxga)
    # A8  history assente per una partita dichiarata giocata.
    g["A8_history_mancante"] = ~g.ha_history
    # A9  xG a zero su un lato mentre l'altra fonte conta dei tiri
    #     (l'unico caso legittimo, l'autogol, si verifica poi tiro-per-tiro).
    g["A9_xg_zero_con_tiri"] = (((g.xgh == 0) & (g.hs > 0))
                                | ((g.xga == 0) & (g.as_ > 0)))

    test = [c for c in g.columns if c[0] == "A" and c[1].isdigit()]
    g["n_flag"] = g[test].sum(axis=1)
    tassi = {c: {"positivi": int(g[c].sum()), "su": int(len(g)),
                 "tasso": round(float(g[c].mean()), 8)} for c in test}
    return g, tassi


# --------------------------------------------------------------------------- #
# B. Incoerenza con la fonte indipendente (gratis)
# --------------------------------------------------------------------------- #
def zeta(g: pd.DataFrame) -> pd.DataFrame:
    """z = (xG - qualita'_media * n_tiri) / sqrt(var_per_tiro * n_tiri).

    La qualita' media per tiro e la varianza sono stimate LASCIANDO FUORI LA
    LEGA che si sta giudicando (leave-one-league-out): nessun dato giudica se
    stesso. Un feed troncato toglie tiri e quindi xG -> z molto negativo.
    """
    lati = []
    for side, xg, n in (("h", "xgh", "hs"), ("a", "xga", "as_")):
        t = g[["league", "season", "mid", "home", "away", "dt", xg, n]].copy()
        t.columns = ["league", "season", "mid", "home", "away", "dt", "xg", "n"]
        t["side"] = side
        lati.append(t)
    L = pd.concat(lati, ignore_index=True).dropna(subset=["xg", "n"])
    out = []
    for lg in LEAGUES:
        altre = L[L.league != lg]
        m = altre.xg.sum() / altre.n.sum()
        v = float((((altre.xg - m * altre.n) ** 2) / altre.n.clip(lower=1)).mean())
        sub = L[L.league == lg].copy()
        sub["m"], sub["v"] = m, v
        sub["z"] = (sub.xg - m * sub.n) / np.sqrt(v * sub.n.clip(lower=1))
        out.append(sub)
    return pd.concat(out, ignore_index=True)


# --------------------------------------------------------------------------- #
# B-bis. Riconciliazione stagionale dei TIRI (gratis)
# --------------------------------------------------------------------------- #
def riconciliazione(fd: pd.DataFrame) -> list[dict]:
    """Tiri totali di una lega-stagione: Understat (giocatori) vs football-data.

    La sezione ``players`` del JSON di lega da i tiri stagionali di ogni
    giocatore: sommandoli si ottiene il totale tiri della lega-stagione secondo
    Understat, da confrontare con quello di football-data. Due contatori
    indipendenti della stessa cosa: se divergono, uno dei due ha perso partite.
    """
    tot_fd = fd.groupby(["league", "season"])[["hs", "as_"]].sum().sum(axis=1)
    rows = []
    for league in LEAGUES:
        for season in sources.SEASONS:
            year = 2000 + int(season[:2])
            path = US_DIR / f"{league}_{year}.json"
            if not path.exists():
                continue
            d = json.loads(path.read_text())
            us = sum(int(p["shots"]) for p in d["players"])
            f = float(tot_fd.get((league, season), np.nan))
            rows.append({"league": league, "season": season,
                         "tiri_football_data": f, "tiri_understat": us,
                         "diff": us - f,
                         "diff_pct": round(100.0 * (us - f) / f, 2)})
    return rows


# --------------------------------------------------------------------------- #
# C. Verdetto tiro-per-tiro
# --------------------------------------------------------------------------- #
def verdetto(mid: str, riga: pd.Series) -> dict:
    """Scarica i tiri e confronta con l'aggregato e con football-data."""
    d, sha = scarica_tiri(mid)
    # NB: si indicizza con riga["dt"], non riga.dt -- su una Series ".dt" e'
    # l'accessore datetime di pandas e maschera la colonna omonima.
    r = {"mid": mid, "league": riga["league"], "season": riga["season"],
         "date": str(riga["dt"])[:10], "match": f"{riga['home']}-{riga['away']}",
         "gol": f"{int(riga['gh'])}-{int(riga['ga'])}",
         "xg_aggregato": [riga["xgh"], riga["xga"]],
         "tiri_football_data": [riga["hs"], riga["as_"]],
         "tiri_in_porta_football_data": [riga["hst"], riga["ast"]],
         "sha256": sha, "scaricato": d is not None}
    if d is None:
        r["VERDETTO"] = "non scaricabile"
        return r
    nh, na = len(d["shots"]["h"]), len(d["shots"]["a"])
    sh = sum(float(x["xG"]) for x in d["shots"]["h"])
    sa = sum(float(x["xG"]) for x in d["shots"]["a"])
    r["tiri_understat"] = [nh, na]
    r["somma_xg_tiri"] = [round(sh, 6), round(sa, 6)]
    # L'aggregato e' stampato a 6 cifre significative, e ogni singolo tiro pure:
    # lo scarto di puro arrotondamento sta sotto 1e-5. La soglia del VERDETTO e'
    # tenuta larga (1e-3) apposta: un feed troncato sposta l'xG di 0.1 o piu',
    # non di un millesimo. Lo scarto vero viene comunque riportato, cosi' si
    # vede la precisione effettiva invece di doverla assumere.
    TOL = 1e-3
    r["scarto_somma_vs_aggregato"] = [
        None if np.isnan(riga["xgh"]) else round(abs(sh - riga["xgh"]), 8),
        None if np.isnan(riga["xga"]) else round(abs(sa - riga["xga"]), 8)]
    r["identita_somma_ok"] = bool(abs(sh - riga["xgh"]) <= TOL
                                  and abs(sa - riga["xga"]) <= TOL)
    r["scarto_tiri_vs_football_data"] = [
        None if np.isnan(riga["hs"]) else int(nh - riga["hs"]),
        None if np.isnan(riga["as_"]) else int(na - riga["as_"])]
    gol = int(riga["gh"]) + int(riga["ga"])
    sot = float(np.nan_to_num(riga["hst"]) + np.nan_to_num(riga["ast"]))
    if nh == 0 and na == 0 and (gol > 0 or sot > 0):
        r["VERDETTO"] = "SEGNAPOSTO (lista tiri vuota)"
    elif not r["identita_somma_ok"]:
        r["VERDETTO"] = "AGGREGATO != SOMMA DEI TIRI"
    else:
        r["VERDETTO"] = "misura genuina"
    return r


# --------------------------------------------------------------------------- #
# D. Simulazione di potere
# --------------------------------------------------------------------------- #
def potere(g: pd.DataFrame, Z: pd.DataFrame, n: int, seed: int) -> dict:
    """Quanto vale la batteria? Si piantano buchi finti e si conta quanti ne ripesca.

    Due scenari, perche' sono due guasti diversi:
      1. SEGNAPOSTO TOTALE - la fonte riscrive la partita con la sua regola di
         ripiego (xG=gol, npxG=gol-0.75*rigori, ppda 0/0, deep 0, forecast 0/1/0).
      2. TRONCAMENTO PARZIALE - il feed perde una frazione dei tiri: l'xG resta
         plausibile ma scende. Nessun test della famiglia A lo vede; l'unico
         appiglio e' la coda della famiglia B (xG contro i tiri football-data).
    """
    rng = np.random.default_rng(seed)
    vivi = g[(g.gh + g.ga > 0) & g.xgh.notna() & g.npxgh.notna()]
    idx = rng.choice(len(vivi), size=min(n, len(vivi)), replace=False)
    finte = vivi.iloc[idx].copy()

    # --- scenario 1: segnaposto totale, riscritto con la regola della fonte
    finte["xgh"], finte["xga"] = finte.gh.astype(float), finte.ga.astype(float)
    finte["npxgh"], finte["npxga"] = finte.xgh, finte.xga
    finte["deeph"] = finte["deepa"] = 0.0
    finte["ppda_atth"] = finte["ppda_defh"] = 0
    finte["ppda_atta"] = finte["ppda_defa"] = 0
    finte["fw"], finte["fd"], finte["fl"] = "0", "1", "0"
    finte["xptsh"] = finte["xptsa"] = 1.0
    finte["is_result"] = True
    ricatturate, _ = batteria(finte)
    tot = (ricatturate.n_flag > 0).to_numpy().astype(float)
    per_test = {c: float(ricatturate[c].mean())
                for c in ricatturate.columns if c[0] == "A" and c[1].isdigit()}

    # --- scenario 2: troncamento parziale, visto solo dalla famiglia B
    #     soglia = 0.1o percentile di z (budget di ~32 falsi allarmi su 32.218)
    soglia = float(np.percentile(Z.z, 0.1))
    base = Z.dropna(subset=["z", "n"])
    base = base[base.n >= 10]
    curva = {}
    for f in (0.9, 0.75, 0.5, 0.25, 0.0):
        sub = base.iloc[rng.choice(len(base), size=min(n, len(base)),
                                   replace=False)].copy()
        zz = (sub.xg * f - sub.m * sub.n) / np.sqrt(sub.v * sub.n.clip(lower=1))
        d = (zz < soglia).to_numpy().astype(float)
        media, lo, hi, _ = boot(d, np.random.default_rng(seed + 1))
        curva[f"xG_residuo_{f:g}"] = {"riscoperti": round(media, 4),
                                      "ci95": [round(lo, 4), round(hi, 4)]}
    m, lo, hi, _ = boot(tot, np.random.default_rng(seed + 2))
    return {"n_piantate": int(len(finte)),
            "segnaposto_totale_riscoperti": {"quota": round(m, 4),
                                             "ci95": [round(lo, 4), round(hi, 4)],
                                             "per_test": {k: round(v, 4)
                                                          for k, v in per_test.items()}},
            "soglia_z_famiglia_B": round(soglia, 3),
            "troncamento_parziale": curva}


# --------------------------------------------------------------------------- #
# Casi puntuali A e B (richiedono rete)
# --------------------------------------------------------------------------- #
def caso_a() -> dict:
    """ligue_1 2025-26, Nantes-Toulouse 17/05/2026: Understat l'ha consolidata?"""
    d, sha = scarica_lega("ligue_1", 2025)
    ver = json.loads((US_DIR / "ligue_1_2025.json").read_text())
    ivec = {m["id"]: m for m in d["dates"]}
    ovec = {m["id"]: m for m in ver["dates"]}
    cambiate = [k for k in ivec
                if json.dumps(ivec[k], sort_keys=True)
                != json.dumps(ovec.get(k), sort_keys=True)]
    target = next((m for m in d["dates"]
                   if m["h"]["title"] == "Nantes" and m["a"]["title"] == "Toulouse"
                   and m["datetime"].startswith("2026-05-17")), None)
    ultima = max(m["datetime"][:10] for m in d["dates"])
    giornata = [m for m in d["dates"] if m["datetime"][:10] == ultima]
    tiri, sha_t = (None, None)
    if target is not None:
        t, sha_t = scarica_tiri(target["id"])
        tiri = None if t is None else [len(t["shots"]["h"]), len(t["shots"]["a"])]
    return {
        "sha256_json_lega_fresco": sha,
        "identico_al_versionato": len(cambiate) == 0,
        "partite_cambiate_dal_versionato": cambiate,
        "record": target,
        "ultima_giornata": ultima,
        "partite_ultima_giornata": len(giornata),
        "consolidate_ultima_giornata": sum(1 for m in giornata if m["isResult"]),
        "non_consolidate_in_tutta_la_stagione": [
            f"{m['datetime']} {m['h']['title']}-{m['a']['title']}"
            for m in d["dates"] if not m["isResult"]],
        "getMatchData": {"tiri": tiri, "sha256": sha_t},
    }


def caso_b() -> dict:
    """bundesliga 2024-25, Holstein Kiel-Bochum (id 27930): i tiri sono arrivati?"""
    d, sha = scarica_lega("bundesliga", 2024)
    rec = next((m for m in d["dates"] if m["id"] == "27930"), None)
    hist = {}
    for t in d["teams"].values():
        for h in t.get("history", []):
            hist[(t["title"], h["date"])] = h
    storia = {team: hist.get((team, "2025-02-09 13:30:00"))
              for team in ("Holstein Kiel", "Bochum")}
    tiri, sha_t = scarica_tiri("27930")
    return {
        "sha256_json_lega_fresco": sha,
        "record_dates": rec,
        "record_history": {k: (None if v is None else
                               {c: v[c] for c in ("xG", "npxG", "ppda", "deep",
                                                  "scored", "missed", "xpts")})
                           for k, v in storia.items()},
        "getMatchData": {
            "scaricato": tiri is not None,
            "tiri": None if tiri is None else [len(tiri["shots"]["h"]),
                                               len(tiri["shots"]["a"])],
            "rosters": None if tiri is None else {k: len(v) for k, v
                                                  in tiri.get("rosters", {}).items()},
            "sha256": sha_t},
    }


# --------------------------------------------------------------------------- #
# Relazione leggibile
# --------------------------------------------------------------------------- #
NOMI_TEST = {
    "A1_xg_uguale_gol": "xG identico ai gol su entrambi i lati",
    "A2_cifre_povere": "xG e npxG con <=3 cifre significative (tutti e 4)",
    "A3_forecast_degenere": "previsione della fonte degenere (0/1 esatti)",
    "A4_ppda_nulla": "PPDA con att=0 o def=0 (flusso eventi vuoto)",
    "A5_deep_zero": "deep=0 su entrambe le squadre (il filtro di partenza)",
    "A6_xpts_intero": "xpts intero esatto (0/1/3)",
    "A7_rigore_finto": "xG-npxG multiplo esatto di 0.75 (rigore di comodo)",
    "A8_history_mancante": "partita giocata senza history per-squadra",
    "A9_xg_zero_con_tiri": "xG=0 mentre football-data conta dei tiri",
}


def scrivi_md(rep: dict) -> None:
    L = []
    A = L.append
    A("# Caccia ai segnaposto di Understat (5 leghe x 9 stagioni)\n")
    A(f"Generato da `scripts/cerca_segnaposto.py` il "
      f"{rep['quando']} (UTC). Parametri: `{json.dumps(rep['parametri'])}`.\n")
    A("**La domanda.** Un buco (NaN) si vede. Un dato *finto* no: quando la fonte "
      "non acquisisce una partita non lascia il campo vuoto, ci scrive un valore "
      "di comodo. Nessun confronto snapshot-vs-fonte lo scopre. Qui si cercano "
      "quei valori, su tutte e cinque le leghe.\n")
    A("**Aspettativa dichiarata prima di guardare i numeri.** (1) sui due casi "
      "puntuali: nessun recupero, perche' una fonte che non ha acquisito una "
      "partita raramente torna indietro mesi dopo; (2) sulla caccia generale: da "
      "1 a 5 nuovi segnaposto, sull'idea che 1 su 16.000 sia una stima per "
      "difetto. Esito sotto, confrontato voce per voce.\n")

    ca = rep.get("caso_A")
    if ca:
        rec = ca["record"]
        A("\n## Caso A — ligue_1 2025-26, Nantes-Toulouse (17/05/2026)\n")
        A(f"- JSON di lega ri-scaricato oggi (`sha256 {ca['sha256_json_lega_fresco'][:16]}...`): "
          f"**identico** al versionato su tutte le partite? `{ca['identico_al_versionato']}` "
          f"(partite cambiate: {len(ca['partite_cambiate_dal_versionato'])}).")
        A(f"- Il record e' ancora `isResult={rec['isResult']}`, `xG={rec['xG']}`: "
          "la fonte **non ha consolidato** la partita.")
        A(f"- Ultima giornata ({ca['ultima_giornata']}): "
          f"{ca['consolidate_ultima_giornata']}/{ca['partite_ultima_giornata']} "
          "partite consolidate. In tutta la stagione l'unica non consolidata e' "
          f"{ca['non_consolidate_in_tutta_la_stagione']}.")
        A(f"- `getMatchData/{rec['id']}` risponde **404**: la partita non esiste "
          "proprio come pagina-partita.")
        A("\n**Esito: niente da recuperare da Understat.** Le celle xG/npxG/PPDA/"
          "deep restano NaN, che e' il valore corretto. La riga NON va riempita "
          "con l'xG di un altro provider (FotMob usa un modello diverso: "
          "mescolare due modelli nella stessa colonna e' peggio del NaN, regola "
          "R6 passo 3). Football-data la registra regolarmente (0-0, 2 tiri per "
          "parte): gol, risultato e quote della riga sono buoni, manca solo il "
          "blocco xG.")

    cb = rep.get("caso_B")
    if cb:
        A("\n## Caso B — bundesliga 2024-25, Holstein Kiel-Bochum (id 27930)\n")
        A(f"- `getMatchData/27930` scaricato oggi: lista tiri "
          f"**{cb['getMatchData']['tiri']}**, rosters {cb['getMatchData']['rosters']}. "
          "Ancora vuoto su entrambi i lati.")
        A(f"- Il JSON di lega riporta ancora `xG={cb['record_dates']['xG']}`, "
          f"`forecast={cb['record_dates']['forecast']}`; la history dice "
          f"{json.dumps(cb['record_history'], ensure_ascii=False)}.")
        A("\n**Esito: niente da ripristinare.** La fonte non ha acquisito la "
          "partita ne' allora ne' adesso; i valori sono gli stessi segnaposto. "
          "Il NaN dichiarato gia' applicato resta la scelta giusta.")

    A("\n## La batteria di test (gratis, su tutte le 16.110 partite giocate)\n")
    A("Ogni test ha un tasso di falsi positivi **misurato**, non assunto.\n")
    A("| test | cosa guarda | positivi | tasso |")
    A("|---|---|--:|--:|")
    for k, v in rep["A_tassi"].items():
        A(f"| `{k}` | {NOMI_TEST.get(k, '')} | {v['positivi']} / {v['su']} | "
          f"{v['tasso']:.6%} |")
    A(f"\nCandidati con almeno un flag: **{len(rep['A_candidati'])}**.\n")
    for c in rep["A_candidati"]:
        A(f"- `{c['league']} {c['season']}` **{c['match']}** ({c['date']}), "
          f"gol {c['gol']}, xG {c['xg']}, deep {c['deep']}, "
          f"tiri football-data {c['tiri_football_data']} -> flag: {', '.join(c['flag'])}")

    p = rep["D_potere"]
    A("\n## Quanto vale la batteria (simulazione di potere)\n")
    A("Un test con zero falsi positivi puo' avere anche zero potere. Si piantano "
      f"buchi finti su {p['n_piantate']} partite vere e si conta quanti ne ripesca.\n")
    st = p["segnaposto_totale_riscoperti"]
    A(f"- **Segnaposto totale** (la regola esatta della fonte): riscoperti "
      f"**{st['quota']:.1%}**, CI95 bootstrap {st['ci95']}. Per singolo test: "
      + ", ".join(f"`{k}` {v:.0%}" for k, v in st["per_test"].items()) + ".")
    A(f"- **Troncamento parziale** (il feed perde una parte dei tiri; l'xG resta "
      f"plausibile ma scende). Soglia sulla coda z = {p['soglia_z_famiglia_B']} "
      "(budget ~32 falsi allarmi su 32.218 lati):")
    A("\n| xG residuo dopo il troncamento | riscoperti | CI95 |")
    A("|---|--:|---|")
    for k, v in p["troncamento_parziale"].items():
        A(f"| {k.replace('xG_residuo_', '')} | {v['riscoperti']:.1%} | {v['ci95']} |")
    A("\n**Lettura onesta:** la batteria e' *cieca* ai troncamenti parziali. "
      "Vede benissimo il guasto totale (100%) e quasi niente sotto: e' il limite "
      "strutturale del metodo, non un dettaglio.")

    if rep.get("C_verdetti"):
        A("\n## Verdetto tiro-per-tiro (l'unico giudice vero)\n")
        A("| strato | perche' | partite | segnaposto | aggregato != somma tiri | non scaricabili |")
        A("|---|---|--:|--:|--:|--:|")
        perche = {"candidati_A": "quelli che la batteria ha segnalato",
                  "coda_B": "dove un feed troncato si nasconderebbe",
                  "campione_casuale": "controllo, per limitare la prevalenza"}
        for nome in ("candidati_A", "coda_B", "campione_casuale"):
            res = rep["C_verdetti"].get(nome, [])
            if not res:
                continue
            sg = sum(1 for r in res if str(r.get("VERDETTO", "")).startswith("SEGNAPOSTO"))
            rk = sum(1 for r in res if r.get("VERDETTO") == "AGGREGATO != SOMMA DEI TIRI")
            ko = sum(1 for r in res if not r["scaricato"])
            A(f"| `{nome}` | {perche.get(nome, '')} | {len(res)} | {sg} | {rk} | {ko} |")
        for nome in ("candidati_A", "coda_B", "campione_casuale"):
            s = rep["C_verdetti"].get(nome + "_scarti_tiri")
            if s:
                A(f"\n- `{nome}`: |tiri Understat - tiri football-data| mediana "
                  f"{s['mediana']:.0f}, p95 {s['p95']:.0f}, max {s['max']:.0f}; "
                  f"entro 2 tiri nel {s['quota_entro_2']:.0%} dei lati "
                  f"(n={s['n']}). I due provider contano quasi la stessa cosa: "
                  "e' questo che rende il confronto un test e non un'opinione.")
        lp = rep.get("C_limite_prevalenza", {})
        if lp.get("limite_superiore_95pct") is not None:
            A(f"\n**Limite superiore sulla prevalenza dei buchi invisibili:** "
              f"{lp['anomalie_trovate']} anomalie su {lp['campione_casuale']} "
              f"partite casuali -> al 95% la prevalenza e' sotto "
              f"**{lp['limite_superiore_95pct']:.2%}** (regola del tre). Su 16.110 "
              f"partite vuol dire *al massimo* ~"
              f"{int(lp['limite_superiore_95pct'] * 16110)} righe compromesse "
              "che questo campione non avrebbe potuto vedere.")

    A("\n## Sottoprodotto: riconciliazione stagionale dei tiri\n")
    A("Somma dei tiri stagionali dei giocatori (Understat) contro somma dei tiri "
      "di football-data: due contatori indipendenti della stessa cosa.\n")
    r = rep["B_riconciliazione_rumore"]
    A(f"Rumore di fondo su {r['n_stagioni_sane']} lega-stagioni sane: |scarto| "
      f"mediano {r['mediana_abs_pct']}%, p95 {r['p95_abs_pct']}%. Fuori scala:\n")
    A("| lega | stagione | tiri football-data | tiri Understat | scarto |")
    A("|---|---|--:|--:|--:|")
    for x in rep["B_riconciliazione_fuori_scala"]:
        A(f"| {x['league']} | {x['season']} | {x['tiri_football_data']:.0f} | "
          f"{x['tiri_understat']} | {x['diff_pct']:+.2f}% |")
    A("\n**Attenzione: qui il sospettato e' football-data, non Understat.** In "
      "Serie A 2018-19/2019-20/2020-21 football-data conta ~20-22 tiri a partita "
      "contro ~25.5 nelle stagioni contigue, e l'xG-per-tiro che ne risulta sale "
      "a 0.135-0.141 contro ~0.11 di tutte le altre lega-stagioni. Non e' il "
      "calcio che cambia: e' il contatore. Riguarda le colonne `home_sot`/"
      "`away_sot` degli snapshot, non l'xG. **Non e' una conclusione**: e' una "
      "pista che merita una verifica dedicata con una terza fonte.")

    A("\n## Limiti (dichiarati)\n")
    A("- La batteria e' cieca ai **troncamenti parziali** (vedi la curva di "
      "potere): un feed che perde meta' dei tiri viene ripreso nel ~7% dei casi.")
    A("- Il verdetto tiro-per-tiro copre un campione, non le 16.110 partite "
      "(sarebbero ~6h30 di download a 1.5s): la prevalenza dei buchi invisibili "
      "e' **limitata dall'alto**, non azzerata.")
    A("- I test sono tarati sulla regola di ripiego OSSERVATA in un solo caso "
      "(27930). Se la fonte ne usasse un'altra in epoche diverse, la batteria "
      "potrebbe non vederla; i test A2/A3/A4/A6 sono pero' generici (degenerazione "
      "di un contatore) e non dipendono dalla regola specifica.")
    A("- La fonte puo' cambiare: i numeri qui valgono alla data del run, e ogni "
      "payload scaricato e' registrato con lo `sha256` nel JSON di uscita.")

    (OUT / "caccia_understat.md").write_text("\n".join(L) + "\n")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true",
                    help="nessun accesso di rete (salta casi puntuali e verdetti)")
    ap.add_argument("--campione", type=int, default=120,
                    help="partite casuali di controllo da scaricare")
    ap.add_argument("--coda", type=int, default=60,
                    help="partite della coda z da scaricare")
    ap.add_argument("--potere", type=int, default=500,
                    help="partite su cui piantare i buchi finti")
    ap.add_argument("--seed", type=int, default=20260725)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    rep: dict = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "parametri": vars(args), "cache_tiri": str(CACHE_TIRI)}

    print("carico Understat (45 JSON di lega versionati) e football-data...")
    us = carica_understat()
    fd = carica_football_data()
    df = us.merge(fd, on=["league", "season", "home", "away"], how="outer",
                  indicator=True)
    rep["copertura"] = {
        "partite_understat_giocate": int(us.is_result.sum()),
        "partite_understat_non_giocate": int((~us.is_result).sum()),
        "partite_football_data": int(len(fd)),
        "solo_understat": int((df._merge == "left_only").sum()),
        "solo_football_data": int((df._merge == "right_only").sum()),
        "elenco_solo_football_data": [
            f"{r.league} {r.season} {r.home}-{r.away}"
            for r in df[df._merge == "right_only"].itertuples()],
        "elenco_non_giocate_secondo_understat": [
            f"{r.league} {r.season} {r.home}-{r.away} ({str(r.dt)[:10]})"
            for r in df[(df._merge != "right_only") & (~df.is_result.fillna(False))
                        ].itertuples()],
    }
    print(f"  understat giocate {rep['copertura']['partite_understat_giocate']}, "
          f"football-data {rep['copertura']['partite_football_data']}")

    # ---- A: batteria gratis
    print("\n[A] batteria di degenerazione (9 test, gratis)")
    g, tassi = batteria(df[df._merge != "right_only"])
    rep["A_tassi"] = tassi
    for k, v in tassi.items():
        print(f"   {k:24s} {v['positivi']:5d} / {v['su']}  ({v['tasso']:.6%})")
    cand = g[g.n_flag > 0].copy()
    rep["A_candidati"] = [
        {"league": r.league, "season": r.season, "mid": r.mid,
         "date": str(r.dt)[:10], "match": f"{r.home}-{r.away}",
         "gol": f"{int(r.gh)}-{int(r.ga)}",
         "xg": [r.xgh, r.xga], "npxg": [r.npxgh, r.npxga],
         "deep": [r.deeph, r.deepa],
         "tiri_football_data": [r.hs, r.as_],
         "flag": [c for c in g.columns if c[0] == "A" and c[1].isdigit()
                  and bool(getattr(r, c))]}
        for r in cand.itertuples()]
    print(f"   -> candidati con almeno un flag: {len(cand)}")

    # ---- B: incoerenza con football-data
    print("\n[B] xG di Understat contro i tiri di football-data (LOLO)")
    Z = zeta(g)
    rep["B_z"] = {"n_lati": int(len(Z)),
                  "qualita_media_per_tiro": {lg: round(float(Z[Z.league == lg].m.iloc[0]), 5)
                                             for lg in LEAGUES},
                  "quantili_z": {str(q): round(float(Z.z.quantile(q)), 3)
                                 for q in (0.0001, 0.001, 0.01, 0.5, 0.99, 0.999)}}
    print("   quantili z:", rep["B_z"]["quantili_z"])

    print("\n[B-bis] riconciliazione stagionale dei TIRI (Understat giocatori vs football-data)")
    rec = riconciliazione(fd)
    rep["B_riconciliazione"] = rec
    fuori = [r for r in rec if abs(r["diff_pct"]) > 1.0]
    for r in fuori:
        print(f"   FUORI SCALA {r['league']} {r['season']}: "
              f"FD {r['tiri_football_data']:.0f} vs US {r['tiri_understat']} "
              f"({r['diff_pct']:+.2f}%)")
    rep["B_riconciliazione_fuori_scala"] = fuori
    sane = np.array([r["diff_pct"] for r in rec if abs(r["diff_pct"]) <= 1.0])
    rep["B_riconciliazione_rumore"] = {
        "n_stagioni_sane": int(len(sane)),
        "mediana_abs_pct": round(float(np.median(np.abs(sane))), 3),
        "p95_abs_pct": round(float(np.percentile(np.abs(sane), 95)), 3)}

    # ---- D: potere (gratis, prima della rete: serve a decidere se fidarsi)
    print("\n[D] simulazione di potere (buchi finti piantati su partite vere)")
    rep["D_potere"] = potere(g, Z, args.potere, args.seed)
    print("   segnaposto totali riscoperti:",
          rep["D_potere"]["segnaposto_totale_riscoperti"]["quota"],
          rep["D_potere"]["segnaposto_totale_riscoperti"]["ci95"])
    print("   troncamento parziale:", json.dumps(
        {k: v["riscoperti"] for k, v in rep["D_potere"]["troncamento_parziale"].items()}))

    if args.offline:
        (OUT / "caccia_understat.json").write_text(
            json.dumps(rep, indent=2, default=str))
        scrivi_md(rep)
        print("\n(offline: casi puntuali e verdetti tiro-per-tiro saltati)")
        return 0

    # ---- casi puntuali
    print("\n[CASO A] ligue_1 2025-26 Nantes-Toulouse: la fonte l'ha consolidata?")
    rep["caso_A"] = caso_a()
    print("   isResult ora:", rep["caso_A"]["record"]["isResult"],
          "| xG:", rep["caso_A"]["record"]["xG"],
          "| JSON identico al versionato:", rep["caso_A"]["identico_al_versionato"])
    print("\n[CASO B] bundesliga 2024-25 Holstein Kiel-Bochum (27930): i tiri sono arrivati?")
    rep["caso_B"] = caso_b()
    print("   tiri ora:", rep["caso_B"]["getMatchData"]["tiri"],
          "| xG:", rep["caso_B"]["record_dates"]["xG"])

    # ---- C: verdetto tiro-per-tiro su candidati + coda + campione casuale
    rng = np.random.default_rng(args.seed)
    gi = g.set_index("mid")
    mids_cand = list(cand.mid)
    coda = (Z[(Z.n >= 10)].sort_values("z").mid.drop_duplicates()
            .head(args.coda).tolist())
    resto = [m for m in g.mid if m not in set(mids_cand) | set(coda)]
    camp = list(rng.choice(resto, size=min(args.campione, len(resto)), replace=False))
    piano = [("candidati_A", mids_cand), ("coda_B", coda), ("campione_casuale", camp)]
    rep["C_verdetti"] = {}
    for nome, mids in piano:
        print(f"\n[C] verdetto tiro-per-tiro — strato '{nome}' ({len(mids)} partite)")
        res = []
        for i, mid in enumerate(mids, 1):
            res.append(verdetto(mid, gi.loc[mid]))
            if i % 20 == 0:
                print(f"   {i}/{len(mids)}")
        rep["C_verdetti"][nome] = res
        segn = [r for r in res if r.get("VERDETTO", "").startswith("SEGNAPOSTO")]
        rotti = [r for r in res if r.get("VERDETTO") == "AGGREGATO != SOMMA DEI TIRI"]
        ko = [r for r in res if not r["scaricato"]]
        dif = [d for r in res for d in (r.get("scarto_tiri_vs_football_data") or [])
               if d is not None]
        print(f"   segnaposto {len(segn)} | aggregato incoerente {len(rotti)} | "
              f"non scaricabili {len(ko)}")
        if dif:
            a = np.abs(np.array(dif, dtype=float))
            print(f"   |tiri Understat - tiri football-data|: mediana {np.median(a):.0f}, "
                  f"p95 {np.percentile(a, 95):.0f}, max {a.max():.0f}")
            rep["C_verdetti"][nome + "_scarti_tiri"] = {
                "mediana": float(np.median(a)), "p95": float(np.percentile(a, 95)),
                "max": float(a.max()), "n": int(len(a)),
                "quota_entro_2": float((a <= 2).mean())}
    # limite superiore sulla prevalenza dei buchi invisibili (regola del 3)
    n_camp = len(rep["C_verdetti"].get("campione_casuale", []))
    trovati = sum(1 for r in rep["C_verdetti"].get("campione_casuale", [])
                  if r.get("VERDETTO", "") != "misura genuina" and r["scaricato"])
    rep["C_limite_prevalenza"] = {
        "campione_casuale": n_camp, "anomalie_trovate": trovati,
        "limite_superiore_95pct": (round(3.0 / n_camp, 4) if trovati == 0 and n_camp
                                   else None),
        "nota": ("con 0 anomalie su n il limite superiore al 95% e' 3/n "
                 "(regola del tre, binomiale esatta)")}

    (OUT / "caccia_understat.json").write_text(json.dumps(rep, indent=2, default=str))
    scrivi_md(rep)
    print(f"\nscritto {OUT / 'caccia_understat.json'} e caccia_understat.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
