"""Scoring del test prospettico 2026-27 (Fase 78, passo P4).

SCRITTO PRIMA DI VEDERE UN SOLO RISULTATO — ed e' il punto. Scegliere la
metrica, il perimetro e la baseline **dopo** aver visto gli esiti significa
sceglierli sapendo gia' chi vince: e' la forma piu' facile di look-ahead, e
non lascia traccia nel codice. Questo file e' datato nel registro di git, e la
sua data e' precedente a ogni partita del 2026-27.

COSA FA. Legge (a) le previsioni congelate del Modello 1
(`prospettico_2026_27_m1.csv`, Fase 129), (b) opzionalmente quelle del
Modello 2, (c) i risultati veri, e produce log-loss/Brier per mercato e per
lega, piu' la calibrazione. Registra un run in `experiments/runs.jsonl` con
`source = "prospettico_2627"`.

I RISULTATI. Arrivano da football-data (stagione `2627`), non da Smarkets: la
borsa da' prezzi, non esiti. Il file dei risultati e' un CSV con almeno
`league, home, away, home_goals, away_goals` e i nomi **canonici** (quelli di
`sources.canonical_team`). Finche' la stagione non e' cominciata non esiste, e
lo script lo dice invece di fallire in modo oscuro.

CRITERI PRE-REGISTRATI (passo P6, fissati il 01/08/2026, prima di ogni dato):

  1. **Metrica principale**: log-loss sull'**1X2**. Una sola. Il Brier e gli
     altri mercati si riportano, ma la conclusione si legge sull'1X2, perche'
     e' l'unico che a questi campioni ha potenza (Fase 98: 4-5× il GG/NG e
     l'O/U 2.5).
  2. **Bersaglio della prima giornata**: la **baseline** (frequenza storica
     dell'esito), NON il mercato. Contro il mercato servono 574 partite; con
     48 la potenza e' ~10% e non si conclude nulla. La prima giornata
     **collauda il protocollo**: fixture veri, congelamento, quote, scoring.
  3. **Successo dichiarato in anticipo**, in ordine di ambizione:
       - M1 batte la baseline con IC95% che esclude lo zero -> serve n >= 184
         (~4 giornate su 5 leghe). Prima di allora si riporta il segno, non si
         conclude;
       - M2 (market-implied) riproduce il mercato entro il rumore;
       - M1 **calibrato**: ECE < 0.05 sull'1X2. Questo si puo' guardare
         subito, perche' non e' un confronto.
  4. **Aspettativa dichiarata**: M1 **perde** contro il mercato. E' previsto
     (alfa*=0 ovunque, Fase 16) e non e' un fallimento del test: il test serve
     a misurare **quanto** perde su partite mai viste, e se resta calibrato.
  5. **Quante ipotesi**: una per mercato per lega e' tanto. Si dichiara il
     numero di confronti fatti e si legge l'1X2 pooled come primario; il resto
     e' esplorativo, e va scritto che lo e'.
  6. **Niente ROI**: il progetto non simula denaro (CLAUDE.md §5-6).

USO:
    python scripts/_run_prospettico_scoring.py --risultati data/....csv
    python scripts/_run_prospettico_scoring.py --dry-run   # verifica a vuoto
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation import metrics                       # noqa: E402
from src.evaluation.experiment_log import append_run     # noqa: E402

M1 = ROOT / "experiments" / "prospettico_2026_27_m1.csv"
M2 = ROOT / "experiments" / "prospettico_2026_27_m2.csv"
OUT = ROOT / "experiments" / "prospettico_2026_27_scoring.json"

# Mercato congelato -> come si calcola l'esito dai gol. Ogni voce e' una
# funzione (gol_casa, gol_ospite) -> {0,1}. Scritte qui, in un posto solo,
# perche' un esito calcolato due volte in due modi e' un bug che non si vede.
BINARI = {
    "over_0.5":      lambda h, a: (h + a) > 0.5,
    "over_1.5":      lambda h, a: (h + a) > 1.5,
    "over_2.5":      lambda h, a: (h + a) > 2.5,
    "over_3.5":      lambda h, a: (h + a) > 3.5,
    "over_4.5":      lambda h, a: (h + a) > 4.5,
    "btts":          lambda h, a: (h > 0) & (a > 0),
    "odd_total":     lambda h, a: ((h + a) % 2) == 1,
    "dc_1x":         lambda h, a: h >= a,
    "dc_12":         lambda h, a: h != a,
    "dc_2x":         lambda h, a: h <= a,
    "home_ov_0.5":   lambda h, a: h > 0.5,
    "home_ov_1.5":   lambda h, a: h > 1.5,
    "away_ov_0.5":   lambda h, a: a > 0.5,
    "away_ov_1.5":   lambda h, a: a > 1.5,
    "cs_home":       lambda h, a: a == 0,          # clean sheet casa
    "cs_away":       lambda h, a: h == 0,
    "wtn_home":      lambda h, a: (h > a) & (a == 0),   # vince a zero
    "wtn_away":      lambda h, a: (a > h) & (h == 0),
    "home_by_2plus": lambda h, a: (h - a) >= 2,
    "away_by_2plus": lambda h, a: (a - h) >= 2,
    "mg_0_1":        lambda h, a: (h + a) <= 1,
    "mg_2_3":        lambda h, a: ((h + a) >= 2) & ((h + a) <= 3),
    "mg_4plus":      lambda h, a: (h + a) >= 4,
}


def commit_corrente() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True
                              ).stdout.strip()
    except Exception:                                    # pragma: no cover
        return "sconosciuto"


def esito_1x2(h: np.ndarray, a: np.ndarray) -> list[str]:
    return ["H" if x > y else ("D" if x == y else "A") for x, y in zip(h, a)]


def ece(prob: np.ndarray, esito: np.ndarray, bins: int = 10) -> float:
    """Expected Calibration Error su una previsione binaria: |previsto −
    osservato| mediato sui bin, pesato per quante osservazioni cadono in
    ciascuno. E' la misura del criterio 3 (ECE < 0.05)."""
    prob = np.asarray(prob, float)
    esito = np.asarray(esito, float)
    bordi = np.linspace(0, 1, bins + 1)
    tot, n = 0.0, len(prob)
    for i in range(bins):
        m = (prob >= bordi[i]) & (prob < bordi[i + 1] if i < bins - 1
                                  else prob <= bordi[i + 1])
        if m.sum():
            tot += m.sum() / n * abs(prob[m].mean() - esito[m].mean())
    return float(tot)


def scora(prev: pd.DataFrame, ris: pd.DataFrame, etichetta: str) -> dict:
    """log-loss/Brier per mercato, piu' 1X2 pooled e per lega."""
    df = prev.merge(ris, on=["league", "home", "away"], how="inner",
                    validate="one_to_one")
    if df.empty:
        raise SystemExit(
            "nessuna partita agganciata fra previsioni e risultati. "
            "Controllare i nomi canonici (sources.canonical_team) e la lega.")
    h = df["home_goals"].to_numpy(int)
    a = df["away_goals"].to_numpy(int)
    esiti = esito_1x2(h, a)

    p1x2 = df[["home_win", "draw", "away_win"]].to_numpy(float)
    base = np.tile(metrics.base_rates_1x2(esiti), (len(df), 1))

    out = {
        "modello": etichetta,
        "partite_scorate": int(len(df)),
        "partite_congelate": int(len(prev)),
        "1x2": {
            "log_loss": metrics.log_loss_1x2(p1x2, esiti),
            "brier": metrics.brier_1x2(p1x2, esiti),
            "log_loss_baseline": metrics.log_loss_1x2(base, esiti),
            # ECE sul solo esito "casa", il piu' frequente: con n piccolo un
            # ECE per tutte e tre le classi e' rumore puro.
            "ece_home": ece(p1x2[:, 0], np.array([e == "H" for e in esiti])),
        },
        "per_lega": {}, "per_mercato": {},
    }
    for lega, g in df.groupby("league"):
        gi = g.index
        e = [esiti[df.index.get_loc(i)] for i in gi]
        out["per_lega"][lega] = {
            "n": int(len(g)),
            "log_loss_1x2": metrics.log_loss_1x2(
                g[["home_win", "draw", "away_win"]].to_numpy(float), e),
        }
    for mercato, regola in BINARI.items():
        if mercato not in df.columns:
            continue
        y = regola(h, a).astype(float)
        p = df[mercato].to_numpy(float)
        out["per_mercato"][mercato] = {
            "log_loss": metrics.log_loss_binary(p, y),
            "brier": metrics.brier_binary(p, y),
            # La baseline giusta per un binario e' la sua frequenza osservata:
            # la costante ottima a posteriori, quindi un confronto CONSERVATIVO
            # per il modello (stessa nota della Fase 15 su compute_metrics).
            "log_loss_baseline": metrics.log_loss_binary(
                np.full(len(y), y.mean()), y),
            "frequenza_osservata": float(y.mean()),
            "probabilita_media": float(p.mean()),
        }
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--risultati", type=Path, default=None,
                    help="CSV con league,home,away,home_goals,away_goals")
    ap.add_argument("--dry-run", action="store_true",
                    help="verifica che tutto sia al suo posto, senza risultati")
    a = ap.parse_args(argv)

    if not M1.exists():
        raise SystemExit(f"mancano le previsioni congelate: {M1.relative_to(ROOT)}")
    prev1 = pd.read_csv(M1)
    print(f"M1: {len(prev1)} partite congelate ({M1.relative_to(ROOT)})")
    if M2.exists():
        print(f"M2: {len(pd.read_csv(M2))} partite ({M2.relative_to(ROOT)})")
    else:
        print("M2: non ancora prodotto (si genera vicino al calcio d'inizio)")

    if a.dry_run or a.risultati is None:
        mancanti = [m for m in BINARI if m not in prev1.columns]
        print(f"mercati binari scorabili: {len(BINARI) - len(mancanti)}/{len(BINARI)}"
              + (f"  (mancano: {mancanti})" if mancanti else ""))
        print("nessun risultato fornito: niente da scorare.\n"
              "Quando la giornata e' finita:\n"
              "  python scripts/_run_prospettico_scoring.py --risultati <csv>")
        return

    ris = pd.read_csv(a.risultati)
    attese = {"league", "home", "away", "home_goals", "away_goals"}
    if not attese <= set(ris.columns):
        raise SystemExit(f"il CSV dei risultati deve avere {sorted(attese)}")

    esito = {"generato_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "commit": commit_corrente(),
             "risultati_da": str(a.risultati),
             "criteri_preregistrati": "vedi docstring di questo file, fissati 2026-08-01",
             "modelli": []}
    esito["modelli"].append(scora(prev1, ris, "M1_dixon_coles"))
    if M2.exists():
        esito["modelli"].append(scora(pd.read_csv(M2), ris, "M2_market_implied"))

    for m in esito["modelli"]:
        u = m["1x2"]
        print(f"\n=== {m['modello']}  n={m['partite_scorate']}")
        print(f"   log-loss 1X2 {u['log_loss']:.4f}  "
              f"(baseline {u['log_loss_baseline']:.4f}, "
              f"Δ {u['log_loss'] - u['log_loss_baseline']:+.4f})")
        print(f"   Brier 1X2    {u['brier']:.4f}   ECE(casa) {u['ece_home']:.4f}")
        if m["partite_scorate"] < 184:
            print(f"   ⚠️  n={m['partite_scorate']} < 184: si riporta il SEGNO, "
                  "non si conclude (criterio 3).")

    OUT.write_text(json.dumps(esito, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {OUT.relative_to(ROOT)}")

    for m in esito["modelli"]:
        append_run({
            "timestamp": esito["generato_utc"], "commit": esito["commit"],
            "config": {"source": "prospettico_2627", "modello": m["modello"],
                       "stagione": "2627", "giornata": "in corso"},
            "metrics": {"n": m["partite_scorate"],
                        "log_loss_1x2": m["1x2"]["log_loss"],
                        "brier_1x2": m["1x2"]["brier"],
                        "log_loss_1x2_baseline": m["1x2"]["log_loss_baseline"],
                        "ece_home": m["1x2"]["ece_home"]},
        })
    print(f"registrati {len(esito['modelli'])} run in experiments/runs.jsonl")


if __name__ == "__main__":
    main()
