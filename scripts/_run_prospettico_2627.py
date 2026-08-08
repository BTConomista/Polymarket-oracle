"""Test prospettico 2026-27, giornata 1: congelamento del MODELLO 1 (DC).

Test prospettico (Fase 78): si congelano le previsioni PRIMA del calcio
d'inizio e si scorano DOPO — nessun senno di poi possibile, a differenza di
ogni backtest. E' il gold standard del progetto.

Questo script produce il **Modello 1**: il Dixon-Coles da solo, senza quote.
Il **Modello 2** (market-implied dalle quote di chiusura) e' un altro script,
perche' si esegue in un altro momento — vicino al fischio d'inizio.

STORIA (importante per non fraintendere il file che produce). Fino al
01/08/2026 questo script conteneva 7 partite di Premier **hardcoded e
plausibili, non ufficiali**: era un'anteprima illustrativa, non il test. Ora
legge i fixture **veri** dall'ultimo file di `data/smarkets_matches/`, che li
espone con lega, squadre, data e ora (Fasi 116/118). L'anteprima congelata il
2026-07-23 resta in `experiments/prospettico_2026_27.md` §2 come documento
storico: non si riscrive.

TRE COSE CHE QUESTO SCRIPT FA E LA VERSIONE PRECEDENTE SBAGLIAVA:

1. **Le neopromosse sono DICHIARATE, non dedotte** (Fase 128).
   `backtest.promoted_teams(allm, ultima_stagione)` — che la versione
   precedente chiamava — restituisce le squadre promosse **nel 2025-26**, non
   nel 2026-27: confronta due stagioni che esistono entrambe nei dati, e la
   stagione di test non esiste ancora. Qui l'insieme arriva da
   `_run_fase128_nomi_2627`, che lo ricava dal listino vero. Senza,
   una squadra come il Malaga (ultima partita 2018-05, peso 0.5^(3009/365) =
   0.0033) verrebbe tirata verso la **media della lega** invece che verso il
   prior δ: il difetto opposto a quello giusto.

2. **Il motore e' quello della lega** (Fase 92-bis/101). La versione
   precedente passava `draw_balance=True` e `DP_THETA_DC` a tutte le leghe,
   ma la φ(|λ−μ|) e il router θ sono misurati utili **solo in Serie A**: sulle
   altre quattro peggiorano. Qui le costanti arrivano da
   `src.config.market_engine`, come in `predict.py`.

3. **Si congela TUTTO il listino Tier 1**, non solo 1X2/O2.5/GG. L'1X2 si
   scora per primo perche' da' 4-5× la potenza (Fase 98), ma gli altri
   mercati dopo il fischio **non si recuperano**.

`as_of`: uno per lega, pari alla data del primo calcio d'inizio di quella
giornata 1. Non uno per partita: le partite di un turno distano 2-3 giorni e
un `as_of` piu' avanti di 2 giorni moltiplica **tutti** i pesi per
0.5^(2/365) = 0.996, un fattore comune che sposta solo l'intensita' effettiva
dello shrinkage. Differenza dichiarata, non nascosta.

USO:
    python scripts/_run_prospettico_2627.py            # congela
    python scripts/_run_prospettico_2627.py --dry-run  # mostra e non scrive
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.config import LEAGUE_CONFIGS, league_config, market_engine  # noqa: E402
from src.data import loader, sources                                # noqa: E402
from src.models import market_implied as mi                         # noqa: E402
from src.models.dixon_coles import DixonColesModel                  # noqa: E402

from _run_fase128_nomi_2627 import classifica, nomi_per_lega        # noqa: E402

SNAPSHOTS = ROOT / "data" / "smarkets_matches"
OUT = ROOT / "experiments" / "prospettico_2026_27_m1.csv"
META = ROOT / "experiments" / "prospettico_2026_27_m1.json"

# I mercati del listino Tier 1 che si congelano, in ordine di potenza attesa
# (Fase 98: l'1X2 vale 4-5× il GG/NG e l'O/U 2.5). `lam`, `mu` e la matrice
# dei punteggi restano fuori: i primi due sono gia' colonne a se', la terza
# non e' un mercato ma l'oggetto da cui tutti derivano.
MERCATI = [
    "home_win", "draw", "away_win",
    "dc_1x", "dc_12", "dc_2x",
    "over_1.5", "over_2.5", "over_3.5", "over_4.5", "over_0.5",
    "btts", "odd_total",
    "home_ov_0.5", "home_ov_1.5", "away_ov_0.5", "away_ov_1.5",
    "cs_home", "cs_away", "wtn_home", "wtn_away",
    "home_by_2plus", "away_by_2plus",
    "mg_0_1", "mg_2_3", "mg_4plus",
]


def fixture_veri(snapshot: Path) -> list[dict]:
    """I fixture della giornata 1, dal listino: lega, squadre canoniche, ora."""
    from src.data import smarkets_archive as _arch

    d = _arch.leggi(snapshot)
    viste: dict[tuple, dict] = {}
    for r in d["righe"]:
        # Il test prospettico e' definito sui 5 campionati modellati: una
        # partita di Coppa Italia non ha una previsione da congelare, perche'
        # il modello non sa prezzare Vicenza-Catania (Fase 142).
        if r.get("fascia", "campionato") != "campionato":
            continue
        casa, ospite = r["partita"].split(" vs ")
        chiave = (r["lega"], casa, ospite)
        if chiave in viste:
            continue
        viste[chiave] = {
            "league": r["lega"],
            "home_smarkets": casa, "away_smarkets": ospite,
            "home": sources.canonical_team(casa),
            "away": sources.canonical_team(ospite),
            "kickoff_utc": r["inizio"],
            "event_id": r["event_id"],
        }
    return sorted(viste.values(), key=lambda x: (x["league"], x["kickoff_utc"]))


def promosse_dichiarate(snapshot: Path) -> dict[str, set[str]]:
    """Le neopromosse 2026-27, dal listino vero (Fase 128). Si ferma se la
    riconciliazione non torna: una mappa nomi incoerente qui diventerebbe una
    previsione sbagliata congelata, cioe' un errore che non si puo' piu'
    correggere senza invalidare il test."""
    nomi = nomi_per_lega(snapshot)
    out = {}
    for lega, squadre in nomi.items():
        e = classifica(lega, squadre)
        if not e["coerente"]:
            raise SystemExit(
                f"riconciliazione incoerente su {lega}: "
                f"da mappare {e['da_mappare']}, entrate {len(e['neopromosse'])} "
                f"contro uscite {len(e['uscite_dalla_lega'])}. "
                "Eseguire scripts/_run_fase128_nomi_2627.py e correggere prima.")
        out[lega] = {v["canonico"] for v in e["neopromosse"]}
    return out


def fit_lega(league: str, as_of: pd.Timestamp, promosse: set[str]):
    """Il DC della lega, con la sua config e il suo motore."""
    cfg = league_config(league)
    eng = market_engine(league)
    allm = loader.load_league(league)
    delta = cfg["promoted_prior"]
    m = DixonColesModel(
        half_life_days=cfg["half_life_days"], shrinkage=cfg["shrinkage"],
        shots_blend=cfg["shots_blend"], blend_signal=cfg["blend_signal"],
        promoted_prior=(delta, delta),
        # φ35 solo dove e' misurata utile (Serie A): altrove peggiora.
        draw_balance=bool(eng["phi0"]),
    ).fit(allm, as_of_date=as_of, promoted_teams=promosse)
    return m, eng


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    from src.data import smarkets_archive as _arch
    snap = a.snapshot or _arch.ultimo_listino_completo(SNAPSHOTS)
    fix = fixture_veri(snap)
    promosse = promosse_dichiarate(snap)

    mancanti = set(LEAGUE_CONFIGS) - {f["league"] for f in fix}
    if mancanti:
        raise SystemExit(f"{snap.name} non contiene fixture per {sorted(mancanti)}")

    righe = []
    print(f"fixture: {snap.relative_to(ROOT)}  ({len(fix)} partite)\n")
    for league in sorted({f["league"] for f in fix}):
        della_lega = [f for f in fix if f["league"] == league]
        # as_of = il primo calcio d'inizio della giornata, uno per lega.
        as_of = pd.Timestamp(min(f["kickoff_utc"] for f in della_lega)).tz_convert(None)
        m, eng = fit_lega(league, as_of, promosse[league])
        cfg = league_config(league)
        motore = "φ35+router" if eng["phi0"] else "liscio"
        print(f"=== {league}  as_of {as_of.date()}  δ={cfg['promoted_prior']}  "
              f"motore {motore}  promosse: {sorted(promosse[league])}")
        for f in della_lega:
            lam, mu = m.expected_goals(f["home"], f["away"])
            d = mi.price_markets(lam, mu, rho=m.rho,
                                 phi0=eng["phi0"], kappa=eng["kappa"],
                                 dp_theta=eng["dp_theta_dc"])
            print(f"   {f['home']+'-'+f['away']:34s} "
                  f"1 {d['home_win']:5.1%}  X {d['draw']:5.1%}  2 {d['away_win']:5.1%}  "
                  f"O2.5 {d['over_2.5']:5.1%}  GG {d['btts']:5.1%}")
            righe.append({
                "league": league,
                "home": f["home"], "away": f["away"],
                "home_smarkets": f["home_smarkets"], "away_smarkets": f["away_smarkets"],
                "kickoff_utc": f["kickoff_utc"], "event_id": f["event_id"],
                "as_of": str(as_of.date()),
                "home_promossa": f["home"] in promosse[league],
                "away_promossa": f["away"] in promosse[league],
                "lam": round(lam, 4), "mu": round(mu, 4),
                **{k: round(float(d[k]), 5) for k in MERCATI},
            })
        print()

    if a.dry_run:
        print("--dry-run: nessun file scritto.")
        return

    pd.DataFrame(righe).to_csv(OUT, index=False)
    META.write_text(json.dumps({
        "modello": "M1 — Dixon-Coles gol+xG, senza quote",
        "congelato_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "fixture_da": str(snap.relative_to(ROOT)),
        "dati_fino_a": f"stagione {sources.SEASONS[-1]}",
        "partite": len(righe),
        "mercati_congelati": MERCATI,
        "config_per_lega": {
            l: {**league_config(l), "motore": market_engine(l),
                "neopromosse_dichiarate": sorted(promosse[l])}
            for l in sorted(promosse)},
        "avvertenza": (
            "previsione CONGELATA prima del calcio d'inizio. Il valore del test "
            "non e' battere il mercato (non lo batte: alfa*=0 ovunque) ma "
            "misurare quanto perde e se resta calibrato su partite mai viste. "
            "Con una giornata la potenza contro il mercato e' ~10% (Fase 98): "
            "questo turno collauda il protocollo, non conclude."),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"congelate {len(righe)} partite in {OUT.relative_to(ROOT)}")
    print(f"metadati in {META.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
