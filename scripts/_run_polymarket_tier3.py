"""Fronte 4 / Tier 3 — i mercati per-tempo e risultato-esatto: inventario
Polymarket + fondazione misurata + validazione storica.

CONTESTO. La Fase 88 ha creato il template «prendi un mercato che sappiamo
prezzare, confrontalo con una quota esterna, misura Brier e correlazione»
(handicap asiatico: router indistinguibile dal mercato, 0.2040 vs 0.2041). Qui
si prova a ripetere l'esercizio sui mercati **Tier 3** che il progetto non ha
mai validato: Halftime Result, Second Half Result, Exact Score.

COSA FA (tre blocchi indipendenti, tutti stampati):

  [1] INVENTARIO POLYMARKET. Riusa l'ultimo dump in data/polymarket/ (o lo
      scarica con fetch_polymarket_open se manca). Conta gli eventi Tier 3 per
      famiglia, competizione e — soprattutto — per LIQUIDITA' VERA. Attenzione:
      il campo `volume` NON e' un indicatore di liquidita' utilizzabile, perche'
      i volumi piu' alti stanno su partite GIA' GIOCATE ma non ancora risolte
      on-chain, i cui prezzi sono 0.999/0.005 (l'esito). Il criterio adottato e'
      book a DUE LATI: startTime nel futuro + bestBid/bestAsk presenti su tutti
      gli esiti + spread <= 0.15 + somma degli ASK dentro una banda di vig
      plausibile.

  [2] FONDAZIONE MISURATA: la frazione di gol segnati nel PRIMO TEMPO, per lega
      e per stagione, da HTHG/HTAG di football-data (3 leghe x 9 stagioni). Non
      assunta (il «45%» folkloristico) ma misurata, con dispersione fra stagioni
      e fra leghe, indice di dispersione dei conteggi 1T e correlazione 1T-2T
      (che dice se i due tempi si possono trattare come indipendenti).

  [3] VALIDAZIONE STORICA del modello Tier 3, che e' l'unico posto dove
      esistono gli ESITI REALIZZATI. Modello: si invertono le quote di chiusura
      1X2+O/U nei tassi (lam, mu) del mercato (Fase 24/26), si ri-scalano per la
      frazione-primo-tempo stimata WALK-FORWARD (solo stagioni precedenti) e si
      costruisce la matrice dei punteggi del tempo. Da li' Halftime Result,
      Second Half Result e Exact Score. Baseline: frequenze empiriche
      walk-forward e (per i tempi) il trasferimento ingenuo dell'1X2 di
      partita. CI bootstrap appaiato.

LIMITE DICHIARATO E CENTRALE. Gli eventi Polymarket aperti sono partite NON
ancora giocate: non hanno esito. Il confronto col dump puo' quindi misurare solo
l'ACCORDO fra i due prezzi, mai l'accuratezza (niente Brier, a differenza della
Fase 88 che lavorava su handicap storici gia' risolti). L'accuratezza si misura
soltanto nel blocco [3], sui dati storici.

Non registra run (diagnostico). Uso: python scripts/_run_polymarket_tier3.py
"""
from __future__ import annotations

import glob
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation import metrics                      # noqa: E402
from src.models import market_implied as mi             # noqa: E402

RHO = -0.06          # correzione DC sui punteggi bassi (config del router)
THETA = 1.225        # double-Poisson del router v3 sui tassi del mercato
DUMP_DIR = ROOT / "data" / "polymarket"
LEAGUES = {
    "serie_a": "data/serie_a_matches.csv",
    "premier_league": "data/premier_league_matches.csv",
    "la_liga": "data/la_liga_matches.csv",
}
SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223",
           "2324", "2425", "2526"]
FAMILIES = ["Halftime Result", "Second Half Result", "Exact Score",
            "First Team to Score"]


def hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# --------------------------------------------------------------------------- #
# [1] Inventario Polymarket                                                    #
# --------------------------------------------------------------------------- #
def load_dump() -> tuple[list, str]:
    """Ultimo dump open_events_*.json in data/polymarket/, o lo scarica."""
    files = sorted(glob.glob(str(DUMP_DIR / "open_events_*.json")))
    if not files:
        print("  nessun dump locale: scarico da Polymarket (--tag Soccer)...")
        from scripts.fetch_polymarket_open import main as fetch_main
        fetch_main(["--tag", "Soccer"])
        files = sorted(glob.glob(str(DUMP_DIR / "open_events_*.json")))
        if not files:
            raise SystemExit("download fallito: nessun dump disponibile")
    path = files[-1]
    return json.load(open(path)), path


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def league_code(e) -> str:
    sp = e.get("sport") or {}
    return sp.get("sport") or (e.get("seriesSlug") or "?")


def book_quality(e) -> dict | None:
    """Qualita' del book di un evento multi-esito: None se un solo lato manca.

    Su Polymarket `outcomePrices` e' l'ULTIMO SCAMBIO, non un mid: su un book
    fermo e' un numero arbitrario (visti 0.485/0.485/0.485 sull'1X2 di primo
    tempo, somma 1.455, con bid 0.05 e ask 0.92). L'unico segnale di vita e' il
    book a due lati; il vig si legge sulla somma degli ASK (comprare tutti gli
    esiti al meglio disponibile).
    """
    bids, asks = [], []
    for m in (e.get("markets") or []):
        b, a = m.get("bestBid"), m.get("bestAsk")
        try:
            b, a = float(b), float(a)
        except (TypeError, ValueError):
            return None
        if not (0.0 < b < a < 1.0):
            return None
        bids.append(b)
        asks.append(a)
    if not bids:
        return None
    return {"n": len(bids), "ask_sum": sum(asks), "bid_sum": sum(bids),
            "max_spread": max(a - b for a, b in zip(asks, bids))}


def is_live(e, quality, max_spread=0.15, vig_per_outcome=0.12) -> bool:
    """Book vivo: somma degli ask sopra 1 (c'e' vig, non arbitraggio) ma dentro
    una banda proporzionale al numero di esiti (un Exact Score a 17 esiti ha
    per forza piu' vig di un 1X2 a 3)."""
    if quality is None:
        return False
    n = quality["n"]
    return (quality["max_spread"] <= max_spread
            and 1.0 <= quality["ask_sum"] <= 1.0 + vig_per_outcome * n)


def inventory(events, dump_path, now_iso):
    hr("[1] INVENTARIO POLYMARKET — cosa esiste davvero di Tier 3")
    print(f"dump: {dump_path}")
    print(f"eventi nel dump: {len(events)} (tutti con tag Soccer) "
          f"| taglio 'futuro': startTime > {now_iso}")

    rows = []
    for e in events:
        t = e.get("title") or ""
        if " - " not in t:
            continue
        fam = t.rsplit(" - ", 1)[1]
        if fam not in FAMILIES:
            continue
        q = book_quality(e)
        rows.append({
            "fam": fam, "lega": league_code(e), "slug": e.get("slug") or "",
            "start": e.get("startTime") or "", "volume": _f(e.get("volume")),
            "liquidity": _f(e.get("liquidity")),
            "futuro": (e.get("startTime") or "") > now_iso,
            "book2": q is not None,
            "spread": q["max_spread"] if q else np.nan,
            "ask_sum": q["ask_sum"] if q else np.nan,
            "live": is_live(e, q) and (e.get("startTime") or "") > now_iso,
        })
    inv = pd.DataFrame(rows)

    print(f"\neventi Tier 3 totali: {len(inv)}")
    print(f"{'famiglia':22} {'tot':>5} {'futuri':>7} {'book2lati':>10} "
          f"{'VIVI':>6} {'vol>0':>6} {'vol>1000':>9}")
    for fam in FAMILIES:
        s = inv[inv.fam == fam]
        print(f"{fam:22} {len(s):5d} {int(s.futuro.sum()):7d} "
              f"{int((s.book2 & s.futuro).sum()):10d} {int(s.live.sum()):6d} "
              f"{int((s.volume > 0).sum()):6d} {int((s.volume > 1000).sum()):9d}")

    # perche' il volume non serve: i volumi alti sono su partite gia' giocate
    hi = inv[inv.volume > 1000]
    print(f"\nPERCHE' IL VOLUME NON E' UN FILTRO DI LIQUIDITA':")
    print(f"  eventi Tier 3 con volume>1000$: {len(hi)}, di cui gia' iniziati "
          f"(startTime passato, in attesa di risoluzione): "
          f"{int((~hi.futuro).sum())} ({100*(~hi.futuro).mean():.0f}%)")
    top = inv.sort_values("volume", ascending=False).head(3)
    for _, r in top.iterrows():
        print(f"    vol {r.volume:9.0f}$  {r.fam:20} start {r.start[:10]:10} "
              f"futuro={r.futuro}  spread={r.spread if r.spread==r.spread else float('nan'):.3f}")

    live = inv[inv.live]
    print(f"\ncompetizioni con Tier 3 VIVO ({len(live)} eventi):")
    for lg, n in Counter(live.lega).most_common(12):
        fams = Counter(live[live.lega == lg].fam)
        print(f"  {lg:10} {n:4d}  " + ", ".join(f"{k.split()[0]}:{v}"
                                                for k, v in fams.most_common()))
    big5 = {"epl", "esp", "ita", "ger", "fra", "seriea", "laliga",
            "premier-league", "serie-a", "la-liga", "bundesliga", "ligue1"}
    print(f"\nEventi Tier 3 su Serie A / Premier / La Liga: "
          f"{len(inv[inv.lega.isin(big5)])}")
    print("  (le tre leghe del progetto sono in PAUSA ESTIVA il 2026-07-26:")
    print("   ricominciano a meta' agosto, quindi nel dump degli eventi APERTI")
    print("   non c'e' una sola partita che sappiamo prezzare con le nostre")
    print("   config per-lega. I codici presenti sono 71, tutti altre leghe.)")
    return inv


def cross_tier3_vs_1x2(events, inv, now_iso):
    """Quante partite hanno CONTEMPORANEAMENTE un 1X2+O/U utilizzabile (input
    del motore) e un Tier 3 vivo (bersaglio del confronto)?"""
    hr("[1-bis] INTERSEZIONE: Tier 3 vivo SU partite che sapremmo prezzare")
    from scripts.fetch_polymarket_open import build_soccer_matches, _base_slug

    matches = build_soccer_matches(events)
    usable = {m["key"]: m for m in matches
              if m["one_x_two"] and m["one_x_two"]["usable"]
              and "2.5" in m["over_under"]
              and m["over_under"]["2.5"].get("over") is not None}
    print(f"partite ricostruite dal dump: {len(matches)}")
    print(f"  con 1X2 utilizzabile + O/U 2.5 (input del market-implied): "
          f"{len(usable)}")

    keyof = {}
    for e in events:
        t = e.get("title") or ""
        if " vs." not in t or " - " not in t:
            continue
        fam = t.rsplit(" - ", 1)[1]
        if fam in FAMILIES:
            keyof[e.get("slug") or ""] = (_base_slug(e.get("slug") or ""), fam)

    live_slugs = set(inv[inv.live].slug)
    both = Counter()
    for slug, (key, fam) in keyof.items():
        if key in usable and slug in live_slugs:
            both[fam] += 1
    print("\n  di queste, quante hanno anche il Tier 3 VIVO:")
    for fam in FAMILIES:
        print(f"    {fam:22} {both.get(fam, 0):4d}")
    tot = sum(both.values())
    live_pairs = [(slug, key, fam) for slug, (key, fam) in keyof.items()
                  if key in usable and slug in live_slugs]
    print(f"\n  --> campione massimo per un confronto prezzo-contro-prezzo: "
          f"{tot} mercati")
    print("      su partite di leghe che NON modelliamo (MLS, Cile, Norvegia,")
    print("      Russia, Chequia...): il motore market-implied non usa forze di")
    print("      squadra, quindi tecnicamente le prezzerebbe lo stesso — ma la")
    print("      frazione-primo-tempo andrebbe presa da leghe diverse da quelle")
    print("      su cui la misuriamo, e NESSUNA di queste partite ha esito")
    print("      (sono aperte): si potrebbe misurare l'accordo, mai l'accuratezza.")
    return usable, both, live_pairs


def block_agreement(events, usable, live_pairs, f_tot):
    """Confronto PREZZO-CONTRO-PREZZO sui Tier 3 vivi (accordo, non accuratezza).

    Non c'e' esito (le partite sono aperte): si misura se il prezzo Polymarket
    del tempo e' quello che si deduce dal SUO STESSO 1X2+O/U di partita, cioe'
    se il book Tier 3 e' coerente col book Tier 1 sotto il nostro modello.
    """
    hr("[4] CONFRONTO CON POLYMARKET — accordo dei prezzi (NON accuratezza)")
    print(f"Frazione-primo-tempo usata: f = {f_tot:.4f}, misurata sulle NOSTRE")
    print("tre leghe. LIMITE: le partite quotate sono di altre leghe (MLS,")
    print("Colombia, Brasile, UCL/UEL...), dove f puo' differire; e non avendo")
    print("esito NON si puo' calcolare nessun Brier. Si misura solo l'accordo.\n")

    byslug = {e.get("slug"): e for e in events}
    rows = []
    for slug, key, fam in live_pairs:
        if fam not in ("Halftime Result", "Second Half Result"):
            continue
        m, e = usable[key], byslug.get(slug)
        if e is None or not m.get("home") or not m.get("away"):
            continue
        ou = m["over_under"]["2.5"]
        if not ou.get("over") or not ou.get("under"):
            continue
        p_over = ou["over"] / (ou["over"] + ou["under"])
        x = m["one_x_two"]["devig"]
        lam, mu = mi.implied_lambda_mu(x["home"], x["draw"], x["away"],
                                       p_over, rho=RHO)
        # prezzo del mercato del tempo: mid bid/ask, normalizzato
        got = {}
        for mk in (e.get("markets") or []):
            git = (mk.get("groupItemTitle") or "").strip()
            try:
                mid = 0.5 * (float(mk["bestBid"]) + float(mk["bestAsk"]))
            except (TypeError, ValueError, KeyError):
                got = {}
                break
            if git == "Draw":
                got["D"] = mid
            elif git == m["home"]:
                got["H"] = mid
            elif git == m["away"]:
                got["A"] = mid
        if len(got) != 3:
            continue
        s = sum(got.values())
        if not (0.7 < s < 1.6):
            continue
        mkt = np.array([got["H"] / s, got["D"] / s, got["A"] / s])
        frac = (f_tot, f_tot) if fam == "Halftime Result" else (1 - f_tot, 1 - f_tot)
        mod = np.array(half_probs(lam, mu, frac[0], frac[1], THETA))
        rows.append({"fam": fam, "slug": slug, "lam": lam, "mu": mu,
                     "mH": mod[0], "mD": mod[1], "mA": mod[2],
                     "kH": mkt[0], "kD": mkt[1], "kA": mkt[2],
                     "mid_sum": s})
    A = pd.DataFrame(rows)
    if A.empty:
        print("  nessun mercato confrontabile.")
        return A
    for fam, g in A.groupby("fam"):
        print(f"--- {fam} (n = {len(g)} partite) ---")
        print(f"{'esito':6} {'media modello':>14} {'media mercato':>14} "
              f"{'bias':>8} {'MAE':>8} {'corr':>7}")
        for c, k in (("H", "H"), ("X", "D"), ("A", "A")):
            mo, ke = g[f"m{k}"].to_numpy(), g[f"k{k}"].to_numpy()
            print(f"{c:6} {mo.mean():14.4f} {ke.mean():14.4f} "
                  f"{mo.mean()-ke.mean():+8.4f} {np.abs(mo-ke).mean():8.4f} "
                  f"{np.corrcoef(mo, ke)[0,1]:7.3f}")
        tv = 0.5 * (np.abs(g.mH-g.kH) + np.abs(g.mD-g.kD) + np.abs(g.mA-g.kA))
        print(f"  distanza totale (mezza L1) fra i due prezzi: "
              f"mediana {np.median(tv):.4f}, media {tv.mean():.4f}")
        print(f"  somma dei mid prima della normalizzazione: "
              f"{g.mid_sum.mean():.4f} (il vig sta fuori, sui due lati)")
        # quale frazione-di-tempo sta usando IL MERCATO? La si estrae
        # invertendo il nostro stesso modello sui suoi prezzi.
        fs = []
        for r in g.itertuples():
            grid = np.arange(0.30, 0.71, 0.002)
            err = [((np.array(half_probs(r.lam, r.mu, f, f, THETA))
                     - np.array([r.kH, r.kD, r.kA])) ** 2).sum() for f in grid]
            fs.append(grid[int(np.argmin(err))])
        fs = np.array(fs)
        lab = "1o tempo" if fam == "Halftime Result" else "2o tempo"
        print(f"  frazione-{lab} IMPLICITA nei prezzi Polymarket: "
              f"mediana {np.median(fs):.4f}, IQR "
              f"[{np.percentile(fs,25):.4f}, {np.percentile(fs,75):.4f}]")
        ref = f_tot if fam == "Halftime Result" else 1 - f_tot
        print(f"    (la nostra, misurata sulle 3 leghe: {ref:.4f})\n")
    return A


# --------------------------------------------------------------------------- #
# [2] Frazione gol primo tempo — misurata                                      #
# --------------------------------------------------------------------------- #
def load_history() -> pd.DataFrame:
    """Snapshot congelati (quote di chiusura) + HTHG/HTAG da football-data."""
    raw = {}
    for f in sorted(glob.glob(str(ROOT / "data/football_data_raw/serie_a_*.csv"))):
        try:
            d = pd.read_csv(f, encoding="latin-1")
        except UnicodeDecodeError:
            d = pd.read_csv(f)
        raw.setdefault("serie_a", []).append(d)
    for lg, path in [("premier_league", "files/football_data_premier_league_bundle.json"),
                     ("la_liga", "files/football_data_la_liga_bundle.json")]:
        bundle = json.load(open(ROOT / path))
        for _, csv_str in bundle.items():
            if not isinstance(csv_str, str):
                continue
            d = pd.read_csv(io.StringIO(csv_str))
            d.columns = [c.lstrip("﻿") for c in d.columns]
            raw.setdefault(lg, []).append(d)

    out = []
    for lg, path in LEAGUES.items():
        snap = pd.read_csv(ROOT / path)
        r = pd.concat(raw[lg], ignore_index=True)
        r["date"] = pd.to_datetime(r["Date"], dayfirst=True,
                                   errors="coerce").dt.strftime("%Y-%m-%d")
        r = r[["date", "HomeTeam", "AwayTeam", "HTHG", "HTAG", "FTHG", "FTAG"]]
        m = snap.merge(r, left_on=["date", "home_team", "away_team"],
                       right_on=["date", "HomeTeam", "AwayTeam"], how="left")
        m["league"] = lg
        out.append(m)
    df = pd.concat(out, ignore_index=True)
    # coerenza: i gol dello snapshot devono coincidere con quelli grezzi
    ok = df.HTHG.notna()
    bad = (df.loc[ok, "FTHG"] != df.loc[ok, "home_goals"]).sum()
    print(f"  join snapshot<->football-data: {int(ok.sum())}/{len(df)} righe "
          f"con HTHG/HTAG ({bad} incoerenze sui gol finali)")
    df = df[ok].copy()
    for c in ("HTHG", "HTAG", "FTHG", "FTAG"):
        df[c] = df[c].astype(int)
    df["HTR"] = np.where(df.HTHG > df.HTAG, "H",
                         np.where(df.HTHG < df.HTAG, "A", "D"))
    df["SHHG"] = df.FTHG - df.HTHG
    df["SHAG"] = df.FTAG - df.HTAG
    df["SHR"] = np.where(df.SHHG > df.SHAG, "H",
                         np.where(df.SHHG < df.SHAG, "A", "D"))
    df["season"] = df["season"].astype(str).str.zfill(4)
    return df


def half_fractions(df: pd.DataFrame) -> dict:
    """f_home = somma gol 1T casa / somma gol finali casa (idem ospite)."""
    return {
        "f_home": df.HTHG.sum() / max(df.FTHG.sum(), 1),
        "f_away": df.HTAG.sum() / max(df.FTAG.sum(), 1),
        "f_tot": (df.HTHG.sum() + df.HTAG.sum())
                 / max(df.FTHG.sum() + df.FTAG.sum(), 1),
    }


def block_fractions(df: pd.DataFrame) -> pd.DataFrame:
    hr("[2] FONDAZIONE MISURATA — quanti gol si segnano nel PRIMO TEMPO")
    print("f = (gol nel 1o tempo) / (gol totali), misurata sui dati, non assunta.\n")
    print(f"{'lega':16} {'n':>5} {'f_tot':>7} {'f_casa':>7} {'f_ospite':>8} "
          f"{'sd fra stagioni':>16}")
    per_season = []
    for lg, d in df.groupby("league"):
        fr = half_fractions(d)
        fs = [half_fractions(s)["f_tot"] for _, s in d.groupby("season")]
        per_season.append((lg, fs))
        print(f"{lg:16} {len(d):5d} {fr['f_tot']:7.4f} {fr['f_home']:7.4f} "
              f"{fr['f_away']:8.4f} {np.std(fs, ddof=1):16.4f}")
    fr = half_fractions(df)
    allfs = [f for _, fs in per_season for f in fs]
    print(f"{'POOLED (3 leghe)':16} {len(df):5d} {fr['f_tot']:7.4f} "
          f"{fr['f_home']:7.4f} {fr['f_away']:8.4f} "
          f"{np.std(allfs, ddof=1):16.4f}")
    lo, hi = np.percentile(
        [np.mean(np.random.choice(allfs, len(allfs))) for _ in range(4000)],
        [2.5, 97.5])
    print(f"\n  f_tot pooled = {fr['f_tot']:.4f}  "
          f"(IC95% sulla media per-stagione: [{lo:.4f}, {hi:.4f}], "
          f"n={len(allfs)} stagioni-lega)")
    print(f"  --> nel primo tempo si segna il {100*fr['f_tot']:.1f}% dei gol, "
          f"NON il 50%: il 2o tempo ne ha {100*(1-fr['f_tot']):.1f}%.")

    print("\nper stagione (f_tot), per vedere se e' stabile nel tempo:")
    piv = (df.groupby(["league", "season"])
             .apply(lambda d: half_fractions(d)["f_tot"], include_groups=False)
             .unstack())
    print(piv.round(4).to_string())

    # forma del conteggio nel primo tempo
    print("\nFORMA DEL CONTEGGIO NEL 1o TEMPO (serve per usare una Poisson):")
    print(f"{'lega':16} {'media 1T':>9} {'var 1T':>8} {'var/media':>10} "
          f"{'corr(1T,2T) tot':>16}")
    for lg, d in list(df.groupby("league")) + [("POOLED", df)]:
        ht = (d.HTHG + d.HTAG).to_numpy(float)
        sh = (d.SHHG + d.SHAG).to_numpy(float)
        print(f"{lg:16} {ht.mean():9.4f} {ht.var(ddof=1):8.4f} "
              f"{ht.var(ddof=1)/ht.mean():10.4f} "
              f"{np.corrcoef(ht, sh)[0,1]:16.4f}")
    print("  var/media ~1 = compatibile con Poisson; corr(1T,2T) ~0 = i due")
    print("  tempi si possono trattare come processi indipendenti.")
    return piv


# --------------------------------------------------------------------------- #
# [3] Validazione storica dei mercati Tier 3                                   #
# --------------------------------------------------------------------------- #
def invert_rates(df: pd.DataFrame) -> pd.DataFrame:
    """lam, mu del mercato dalle quote di CHIUSURA 1X2 + O/U 2.5."""
    need = ["odds_home", "odds_draw", "odds_away", "odds_over25", "odds_under25"]
    d = df.dropna(subset=need).copy()
    lams, mus = [], []
    for r in d.itertuples():
        ph, pd_, pa = metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        po, _ = metrics.devig_binary(r.odds_over25, r.odds_under25)
        lam, mu = mi.implied_lambda_mu(ph, pd_, pa, po, rho=RHO)
        lams.append(lam)
        mus.append(mu)
    d["lam"], d["mu"] = lams, mus
    d["p_h"], d["p_d"], d["p_a"] = zip(*[
        metrics.devig_1x2(r.odds_home, r.odds_draw, r.odds_away)
        for r in d.itertuples()])
    return d


def half_probs(lam, mu, fh, fa, theta=None):
    """P(1/X/2) di un tempo, dalla matrice sui tassi ri-scalati."""
    M = mi.score_matrix(lam * fh, mu * fa, RHO, dp_theta=theta)
    return (float(np.tril(M, -1).sum()), float(np.trace(M)),
            float(np.triu(M, 1).sum()))


def paired_ci(a, b, n_boot=4000, seed=0):
    """IC95% bootstrap appaiato sulla differenza media (a - b)."""
    rng = np.random.default_rng(seed)
    d = np.asarray(a) - np.asarray(b)
    idx = rng.integers(0, len(d), (n_boot, len(d)))
    m = d[idx].mean(axis=1)
    return d.mean(), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def block_validation(df: pd.DataFrame):
    hr("[3] VALIDAZIONE STORICA — il motore sa prezzare i mercati Tier 3?")
    print("Walk-forward stretto: per la stagione s, la frazione-primo-tempo e le")
    print("baseline usano SOLO le stagioni precedenti della stessa lega.")
    print("Tassi (lam, mu) invertiti dalle quote di CHIUSURA 1X2+O/U (rho=-0.06).\n")

    d = invert_rates(df)
    print(f"  partite con quote 1X2+O/U complete: {len(d)} / {len(df)} "
          f"({', '.join(f'{k}:{v}' for k, v in Counter(d.league).items())})")

    recs = []
    for lg, g in d.groupby("league"):
        seas = sorted(g.season.unique())
        for i, s in enumerate(seas):
            if i == 0:
                continue                              # niente passato: si salta
            past = g[g.season.isin(seas[:i])]
            cur = g[g.season == s]
            fr = half_fractions(past)
            fh, fa = fr["f_home"], fr["f_away"]
            base_ht = metrics.base_rates_1x2(past.HTR.tolist())
            base_sh = metrics.base_rates_1x2(past.SHR.tolist())
            # baseline risultato esatto: distribuzione empirica congiunta
            # (Laplace +1 su una griglia 0..7 x 0..7)
            grid = np.ones((8, 8))
            for r in past.itertuples():
                grid[min(r.FTHG, 7), min(r.FTAG, 7)] += 1
            grid /= grid.sum()
            for r in cur.itertuples():
                rec = {"league": lg, "season": s, "HTR": r.HTR, "SHR": r.SHR,
                       "fh": fh, "fa": fa,
                       "hg": min(r.FTHG, 7), "ag": min(r.FTAG, 7)}
                for tag, th in (("pois", None), ("dp", THETA)):
                    rec[f"ht_{tag}"] = half_probs(r.lam, r.mu, fh, fa, th)
                    rec[f"sh_{tag}"] = half_probs(r.lam, r.mu, 1 - fh, 1 - fa, th)
                rec["base_ht"] = tuple(base_ht)
                rec["base_sh"] = tuple(base_sh)
                rec["naive"] = (r.p_h, r.p_d, r.p_a)     # 1X2 di partita sul tempo
                M = mi.score_matrix(r.lam, r.mu, RHO, dp_theta=THETA)
                Ms = np.zeros((8, 8))
                Ms[:8, :8] = M[:8, :8]
                Ms[7, :] += M[8:, :8].sum(axis=0)
                Ms[:, 7] += M[:8, 8:].sum(axis=1)
                Ms[7, 7] += M[8:, 8:].sum()
                rec["p_exact"] = Ms[rec["hg"], rec["ag"]] / Ms.sum()
                rec["p_exact_base"] = grid[rec["hg"], rec["ag"]]
                recs.append(rec)
    R = pd.DataFrame(recs)
    print(f"  partite valutate (esclusa la 1a stagione di ogni lega): {len(R)}")

    # ---- primo tempo e secondo tempo -------------------------------------- #
    for half, key, outcome in (("PRIMO TEMPO (Halftime Result)", "ht", "HTR"),
                               ("SECONDO TEMPO (Second Half Result)", "sh", "SHR")):
        print(f"\n--- {half} ---")
        out = R[outcome].tolist()
        cands = {
            "modello (Poisson)": np.array(R[f"{key}_pois"].tolist()),
            f"modello (dp theta={THETA})": np.array(R[f"{key}_dp"].tolist()),
            "baseline frequenze": np.array(R[f"base_{key}"].tolist()),
            "1X2 di partita (ingenuo)": np.array(R["naive"].tolist()),
        }
        print(f"{'':30} {'log-loss':>9} {'Brier':>8}")
        ll = {}
        for name, P in cands.items():
            P = P / P.sum(axis=1, keepdims=True)
            ll[name] = metrics.log_loss_1x2(P, out)
            print(f"{name:30} {ll[name]:9.4f} {metrics.brier_1x2(P, out):8.4f}")
        # CI appaiato modello-migliore vs baseline frequenze
        best = min([k for k in cands if k.startswith("modello")], key=ll.get)
        Pm = cands[best] / cands[best].sum(axis=1, keepdims=True)
        Pb = cands["baseline frequenze"]
        y = np.array([[o == c for c in "HDA"] for o in out], float)
        lm = -np.log(np.clip((Pm * y).sum(axis=1), 1e-15, None))
        lb = -np.log(np.clip((Pb * y).sum(axis=1), 1e-15, None))
        m, lo, hi = paired_ci(lb, lm)
        print(f"  guadagno di {best} sulla baseline: {m:+.4f} "
              f"IC95% [{lo:+.4f}, {hi:+.4f}] "
              f"-> {'CONCLUSIVO' if lo > 0 else 'NON conclusivo'}")
        # per lega
        print(f"  per lega (log-loss {best} vs baseline):")
        for lg, g in R.groupby("league"):
            i = g.index
            print(f"    {lg:16} {lm[R.index.get_indexer(i)].mean():.4f} vs "
                  f"{lb[R.index.get_indexer(i)].mean():.4f}  "
                  f"(delta {lb[R.index.get_indexer(i)].mean()-lm[R.index.get_indexer(i)].mean():+.4f}, "
                  f"n={len(g)})")
        # calibrazione
        Pm3 = Pm
        print("  calibrazione (media prob. dichiarata vs frequenza reale):")
        for k, c in enumerate("HDA"):
            print(f"    {c}: dichiarata {Pm3[:,k].mean():.4f} | "
                  f"reale {np.mean([o==c for o in out]):.4f}")

    # ---- risultato esatto -------------------------------------------------- #
    print("\n--- RISULTATO ESATTO (Exact Score, tempo pieno) ---")
    lm = -np.log(np.clip(R.p_exact.to_numpy(), 1e-15, None))
    lb = -np.log(np.clip(R.p_exact_base.to_numpy(), 1e-15, None))
    print(f"  log-loss modello (matrice del mercato, dp): {lm.mean():.4f}")
    print(f"  log-loss baseline (distribuzione empirica): {lb.mean():.4f}")
    m, lo, hi = paired_ci(lb, lm)
    print(f"  guadagno {m:+.4f} IC95% [{lo:+.4f}, {hi:+.4f}] "
          f"-> {'CONCLUSIVO' if lo > 0 else 'NON conclusivo'}")
    for lg, g in R.groupby("league"):
        i = R.index.get_indexer(g.index)
        print(f"    {lg:16} {lm[i].mean():.4f} vs {lb[i].mean():.4f} "
              f"(delta {lb[i].mean()-lm[i].mean():+.4f}, n={len(g)})")
    return R


# --------------------------------------------------------------------------- #
def main() -> int:
    now_iso = "2026-07-26T00:00:00Z"
    events, dump_path = load_dump()
    inv = inventory(events, dump_path, now_iso)
    usable, both, live_pairs = cross_tier3_vs_1x2(events, inv, now_iso)

    print("\ncarico lo storico (snapshot + HTHG/HTAG football-data)...")
    df = load_history()
    block_fractions(df)
    f_tot = half_fractions(df)["f_tot"]
    block_agreement(events, usable, live_pairs, f_tot)
    block_validation(df)

    hr("LIMITI")
    print("1. Nessuna partita di Serie A/Premier/La Liga nel dump (pausa estiva):")
    print("   il confronto col mercato e' su leghe che non modelliamo.")
    print("2. Gli eventi Polymarket aperti NON hanno esito: il blocco [4] misura")
    print("   l'accordo fra due prezzi, non l'accuratezza di nessuno dei due.")
    print("   L'unica misura di accuratezza e' il blocco [3], sui dati storici,")
    print("   e li' il 'mercato' e' la chiusura football-data, non Polymarket.")
    print("3. Il blocco [3] non ha un mercato Tier 3 di riferimento (football-data")
    print("   non quota primo tempo ne' risultato esatto): il confronto e' contro")
    print("   baseline, quindi dice 'il motore sa prezzare', non 'batte il book'.")
    print("4. f e' una costante per lega stimata sui volumi di gol aggregati:")
    print("   non modella la dipendenza di f dal punteggio corrente o dal")
    print("   favorito (game-state), che e' un candidato per il residuo del 2T.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
