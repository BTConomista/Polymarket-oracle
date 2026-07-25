"""Confronto PROSPETTICO: la nostra P(campione 2026-27) contro i prezzi LIVE di
Polymarket (mercato outright "<Lega>: 2027 Champion").

Perche' conta. Il mercato CAMPIONE DI STAGIONE (Fase 89) e' l'unico che il
progetto sa simulare ma non ha mai potuto validare contro un mercato: non
esistono quote outright storiche (Fase 89, "«battiamo il mercato» NON e'
testabile all'indietro"). Polymarket le quota LIVE per la stagione 2026-27, con
liquidita' reale -> per la prima volta possiamo confrontare la nostra stima con
un prezzo di mercato, PRIMA che la stagione inizi. E' anche il tassello outright
del test prospettico (Fase 78).

Cosa fa:
 1. legge il dump Polymarket (scripts/fetch_polymarket_open.py --tag Soccer) e
    ne estrae il mercato "<Lega>: 2027 Champion": squadre, prezzi YES, volumi;
    scarta i placeholder senza scambi ("Team A/B/C", "Other", volume 0) e
    rinormalizza a somma 1 (devig proporzionale: il modo piu' semplice, con
    l'overround dichiarato);
 2. fitta il Dixon-Coles per-lega sui dati storici fino a oggi;
 3. simula N stagioni intere (season_sim, Fase 89) con le squadre che Polymarket
    quota (= la rosa 2026-27 reale, promosse incluse: il prior neopromosse δ
    della config si applica a chi non ha storico recente);
 4. stampa il confronto P(nostra) vs P(Polymarket) e le metriche di accordo.

LIMITI DICHIARATI (§1.6):
 - i nostri dati si fermano a fine 2025-26: le forze non vedono il mercato
   estivo 2026 (acquisti/cessioni), il prezzo Polymarket si';
 - il devig proporzionale su un book a ~+7% e' una scelta, non una verita';
 - NON e' un test di edge: senza esito (la stagione non e' ancora giocata) si
   misura solo l'ACCORDO, non chi ha ragione. Il verdetto arriva a maggio 2027.

Uso:
  python scripts/fetch_polymarket_open.py --tag Soccer      # (prima, per il dump)
  python scripts/_run_polymarket_outright.py --league serie_a
  python scripts/_run_polymarket_outright.py --all --n-sims 20000
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import LEAGUE_CONFIGS, drift_sd_map  # noqa: E402
from src.data import loader                          # noqa: E402
from src.models.dixon_coles import DixonColesModel   # noqa: E402
from src.models.season_sim import simulate_season, round_robin  # noqa: E402
from scripts.backtest import promoted_teams          # noqa: E402

# titolo dell'evento Polymarket per ciascuna lega nostra
OUTRIGHT_TITLE = {
    "serie_a": "Serie A: 2027 Champion",
    "premier_league": "EPL: 2027 Champion",
    "la_liga": "LALIGA: 2027 Champion",
}
# alias nome Polymarket -> nome nei nostri snapshot
ALIAS = {
    "Inter Milan": "Inter", "AC Milan": "Milan",
    "Manchester City": "Man City", "Manchester United": "Man United",
    "Newcastle United": "Newcastle", "Tottenham": "Tottenham",
    "Nottingham Forest": "Nott'm Forest", "Wolverhampton": "Wolves",
    "Brighton & Hove Albion": "Brighton", "West Ham United": "West Ham",
    "Leeds United": "Leeds", "Atlético Madrid": "Ath Madrid",
    "Athletic Bilbao": "Ath Bilbao", "Barcelona": "Barcelona",
    "Real Madrid": "Real Madrid", "Betis": "Betis",
    "Real Sociedad": "Sociedad", "Celta Vigo": "Celta",
    "Alavés": "Alaves", "Rayo Vallecano": "Vallecano",
}
PLACEHOLDER = ("team a", "team b", "team c", "other", "another team")


def load_dump(path: str | None) -> list:
    if path is None:
        cands = sorted(glob.glob("data/polymarket/open_events_*.json"))
        if not cands:
            raise SystemExit("Nessun dump: esegui prima "
                             "`python scripts/fetch_polymarket_open.py --tag Soccer`")
        path = cands[-1]
    print(f"dump: {path}")
    d = json.load(open(path))
    return d["events"] if isinstance(d, dict) and "events" in d else d


def market_probs(events: list, title: str) -> pd.DataFrame:
    """Estrae (squadra, p_grezza, volume) dal mercato outright, senza placeholder."""
    for e in events:
        if (e.get("title") or "") != title:
            continue
        rows = []
        for m in e.get("markets") or []:
            name = (m.get("groupItemTitle") or m.get("question") or "").strip()
            if name.lower() in PLACEHOLDER:
                continue
            vol = float(m.get("volumeNum") or m.get("volume") or 0.0)
            try:
                outs = [str(o).lower() for o in json.loads(m.get("outcomes") or "[]")]
                prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
                p = dict(zip(outs, prices)).get("yes")
            except Exception:
                p = None
            if p is None or vol <= 0:      # senza scambi = prezzo non informativo
                continue
            rows.append({"team_pm": name, "p_raw": p, "volume": vol})
        if not rows:
            raise SystemExit(f"Mercato '{title}' senza esiti utilizzabili.")
        df = pd.DataFrame(rows)
        df["team"] = df["team_pm"].map(lambda t: ALIAS.get(t, t))
        return df
    raise SystemExit(f"Mercato '{title}' non trovato nel dump.")


def our_probs(league: str, teams: list[str], n_sims: int, seed: int,
              drift: bool = False) -> pd.Series:
    cfg = LEAGUE_CONFIGS[league]
    allm = loader.load_league(league)
    as_of = allm["date"].max() + pd.Timedelta(days=1)
    known = set(allm["home_team"]) | set(allm["away_team"])
    missing = [t for t in teams if t not in known]
    if missing:
        print(f"  ⚠ squadre senza storico nei nostri dati (escluse): {missing}")
        teams = [t for t in teams if t in known]
    # neopromosse = squadre che non erano nell'ultima stagione osservata
    last = str(allm["season"].iloc[-1])
    last_teams = set(allm[allm["season"].astype(str) == last]["home_team"])
    prom = {t for t in teams if t not in last_teams}
    if prom:
        print(f"  neopromosse (prior δ={cfg['promoted_prior']}): {sorted(prom)}")
    d = cfg["promoted_prior"]
    model = DixonColesModel(
        half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
        shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
        promoted_prior=(d, d),
    ).fit(allm, as_of_date=as_of, promoted_teams=prom)
    fixtures = round_robin(teams)
    kw = {}
    if drift:
        # deriva di forza in-stagione (Fase 94): sigma per-squadra
        kw["drift_sd"] = drift_sd_map(teams, prom)
    res = simulate_season(model, fixtures, teams, league_key=league,
                          n_sims=n_sims, seed=seed, **kw)
    # champion_prob e' un array allineato all'ordine di `teams`
    return pd.Series(res["champion_prob"], index=teams, name="p_model")


def compare(league: str, events: list, n_sims: int, seed: int,
            with_drift: bool = False) -> None:
    title = OUTRIGHT_TITLE[league]
    print(f"\n{'='*78}\n{title}   ({league})\n{'='*78}")
    mk = market_probs(events, title)
    over = mk["p_raw"].sum()
    mk["p_market"] = mk["p_raw"] / over          # devig proporzionale
    print(f"esiti quotati con volume>0: {len(mk)} | somma prezzi {over:.4f} "
          f"(overround {100*(over-1):+.1f}%) | volume totale ${mk['volume'].sum():,.0f}")

    teams_q = sorted(mk["team"])
    variants = {"base": our_probs(league, teams_q, n_sims, seed, drift=False)}
    if with_drift:
        variants["deriva"] = our_probs(league, teams_q, n_sims, seed, drift=True)
    for name, s in variants.items():
        col = "p_model" if name == "base" else "p_drift"
        mk[col] = mk["team"].map(s).fillna(0.0)
        if mk[col].sum() > 0:
            mk[col] = mk[col] / mk[col].sum()
    mk = mk.sort_values("p_market", ascending=False)

    hasd = "p_drift" in mk.columns
    head = f"\n{'squadra':<18}{'Polymarket':>12}{'noi':>10}{'Δ':>9}"
    if hasd:
        head += f"{'+deriva':>10}{'Δd':>9}"
    print(head + f"{'volume $':>12}")
    for _, r in mk.iterrows():
        line = (f"{r['team']:<18}{r['p_market']:>11.1%}{r['p_model']:>10.1%}"
                f"{r['p_model']-r['p_market']:>+9.1%}")
        if hasd:
            line += f"{r['p_drift']:>10.1%}{r['p_drift']-r['p_market']:>+9.1%}"
        print(line + f"{r['volume']:>12,.0f}")

    b = mk["p_market"].to_numpy()

    def agreement(a):
        m = np.clip(a, 1e-9, 1); k = np.clip(b, 1e-9, 1)
        return (float(np.abs(a - b).mean()),
                float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 else float("nan"),
                float((m * np.log(m / k)).sum()))

    top_pm = mk.iloc[0]["team"]
    print()
    for col, name in [("p_model", "base"), ("p_drift", "+deriva (F94)")]:
        if col not in mk.columns:
            continue
        mae, corr, kl = agreement(mk[col].to_numpy())
        top = mk.sort_values(col, ascending=False).iloc[0]["team"]
        print(f"  {name:<15} MAE {mae:.4f} | corr {corr:.4f} | "
              f"KL(noi‖mercato) {kl:.4f} | favorito noi={top} (mercato={top_pm})")
    if "p_drift" in mk.columns:
        _, _, k0 = agreement(mk["p_model"].to_numpy())
        _, _, k1 = agreement(mk["p_drift"].to_numpy())
        verdict = "AVVICINA al mercato" if k1 < k0 else "ALLONTANA dal mercato"
        print(f"  -> la deriva {verdict}: ΔKL {k1-k0:+.4f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--league", default="serie_a", choices=sorted(OUTRIGHT_TITLE))
    ap.add_argument("--all", action="store_true", help="tutte e 3 le leghe")
    ap.add_argument("--dump", default=None, help="file dump (default: il piu' recente)")
    ap.add_argument("--n-sims", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--with-drift", action="store_true",
                    help="confronta anche la variante con deriva di forza (Fase 94)")
    args = ap.parse_args()

    events = load_dump(args.dump)
    leagues = sorted(OUTRIGHT_TITLE) if args.all else [args.league]
    for lg in leagues:
        compare(lg, events, args.n_sims, args.seed, with_drift=args.with_drift)
    print("\n⚠ Confronto di ACCORDO, non di edge: la stagione non e' giocata. "
          "I nostri dati si fermano a 2025-26 (nessun mercato estivo 2026).")


if __name__ == "__main__":
    main()
