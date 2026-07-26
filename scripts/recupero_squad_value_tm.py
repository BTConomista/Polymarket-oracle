"""Recupero dei valori rosa mancanti (2025-26) da Transfermarkt — con VALIDAZIONE.

Contesto: `player_scores.team_season_values` pubblica il valore rosa solo se i
giocatori valutati coprono >=85% dei minuti stagionali. Per la stagione 2025-26
delle due leghe nuove restano scoperte 16 celle (5 Bundesliga, 11 Ligue 1). E'
la stessa situazione delle altre tre leghe alla Fase 67 (13 celle), poi risolta
alla Fase 70 con un recupero manuale da Transfermarkt.

Novita': `transfermarkt.com` risponde 200 da questa sessione (il manuale lo dava
BLOCCATO), quindi il recupero si puo' fare **da script**, non a mano.

⚠️  Le due definizioni NON coincidono:
  - nostra:      somma, sui giocatori che hanno giocato >=1' in campionato,
                 dell'ultima valutazione <= 1 settembre dell'anno di inizio;
  - Transfermarkt: valore aggregato della rosa registrato per quella stagione
                 nella pagina di competizione.
Per questo lo script NON si limita a scaricare: misura l'accordo tra le due
definizioni sui club della STESSA stagione per cui il valore player-scores
esiste (13 Bundesliga + 7 Ligue 1). Quell'accordo e' il criterio per decidere
se i valori TM sono usabili per riempire i buchi — e con quale errore dichiarato.

Uso: python cantiere/scripts/recupero_squad_value_tm.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cantiere" / "scripts"))

import nuove_leghe  # noqa: E402

nuove_leghe.registra()
from src.data import sources  # noqa: E402

OUT = ROOT / "cantiere" / "out"
CACHE = ROOT / "cantiere" / "data" / "fonti" / "transfermarkt_web"
SEASON = "2526"
SAISON_ID = 2025            # 2025-26 nella nomenclatura Transfermarkt

COMPETITIONS = {
    "bundesliga": ("bundesliga", "L1"),
    "ligue_1": ("ligue-1", "FR1"),
}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch(league_key: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    slug, code = COMPETITIONS[league_key]
    dest = CACHE / f"{league_key}_{SAISON_ID}.html"
    if dest.exists():
        return dest.read_text(encoding="utf-8", errors="replace")
    url = (f"https://www.transfermarkt.com/{slug}/startseite/wettbewerb/{code}"
           f"/plus/?saison_id={SAISON_ID}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", errors="replace")
    dest.write_text(html)
    print(f"  scaricata: {url}")
    time.sleep(2.0)     # cortesia
    return html


def parse_money(s: str) -> float:
    """'€967.65m' / '€1.02bn' / '€45.30k' -> euro."""
    s = s.replace("€", "").replace("€", "").strip()
    mult = 1.0
    if s.endswith("bn"):
        mult, s = 1e9, s[:-2]
    elif s.endswith("m"):
        mult, s = 1e6, s[:-1]
    elif s.endswith("k"):
        mult, s = 1e3, s[:-1]
    try:
        return float(s.replace(",", "")) * mult
    except ValueError:
        return float("nan")


def parse_clubs(html: str) -> pd.DataFrame:
    """Una riga per club: nome canonico, rosa, eta' media, valore totale."""
    rows = re.findall(r'<tr class="(?:odd|even)">(.*?)</tr>', html, re.S)
    out = []
    for r in rows:
        cells = [re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<td.*?</td>", r, re.S)]
        # schema atteso: ['', club, rosa, eta, stranieri, valore medio, valore totale]
        if len(cells) < 7 or not cells[1]:
            continue
        out.append({
            "team_tm": cells[1],
            "team": sources.canonical_team(cells[1]),
            "squad_size": pd.to_numeric(cells[2], errors="coerce"),
            "avg_age": pd.to_numeric(cells[3], errors="coerce"),
            "tm_value": parse_money(cells[6]),
        })
    return pd.DataFrame(out).dropna(subset=["tm_value"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for league_key in COMPETITIONS:
        print(f"\n=== {league_key} (stagione {SEASON}) ===")
        tm = parse_clubs(fetch(league_key))
        snap = pd.read_csv(ROOT / "cantiere" / "data" / f"{league_key}_matches.csv",
                           dtype={"season": str})
        snap = snap[snap.season == SEASON]
        ours = pd.concat([
            snap[["home_team", "home_squad_value"]].rename(
                columns={"home_team": "team", "home_squad_value": "ps_value"}),
            snap[["away_team", "away_squad_value"]].rename(
                columns={"away_team": "team", "away_squad_value": "ps_value"}),
        ]).groupby("team", as_index=False).first()

        j = ours.merge(tm, on="team", how="outer", indicator=True)
        orfane = j[j._merge != "both"]
        if len(orfane):
            print("  ⚠️  club non appaiati (alias?):")
            print(orfane[["team", "team_tm", "_merge"]].to_string(index=False))

        both = j[j.ps_value.notna() & j.tm_value.notna()].copy()
        both["ratio"] = both.tm_value / both.ps_value
        both["scarto%"] = (both.tm_value / both.ps_value - 1) * 100
        print(f"\n  ACCORDO tra le due definizioni su {len(both)} club con ENTRAMBI i valori:")
        print(both[["team", "ps_value", "tm_value", "scarto%"]]
              .assign(ps_value=lambda d: (d.ps_value / 1e6).round(1),
                      tm_value=lambda d: (d.tm_value / 1e6).round(1),
                      **{"scarto%": lambda d: d["scarto%"].round(1)})
              .sort_values("scarto%").to_string(index=False))
        r = both.ratio.to_numpy()
        print(f"\n  rapporto TM/nostro: mediana {np.median(r):.3f}  "
              f"media {r.mean():.3f}  min {r.min():.3f}  max {r.max():.3f}  "
              f"|scarto| mediano {np.median(np.abs(both['scarto%'])):.1f}%  "
              f"correlazione {np.corrcoef(both.ps_value, both.tm_value)[0,1]:.4f}")

        buchi = j[j.ps_value.isna() & j.tm_value.notna()]
        print(f"\n  CELLE MANCANTI riempibili: {len(buchi)}")
        print(buchi[["team", "tm_value", "squad_size", "avg_age"]]
              .assign(tm_value=lambda d: (d.tm_value / 1e6).round(1))
              .to_string(index=False))

        report[league_key] = {
            "accordo": {
                "n": int(len(both)),
                "ratio_mediana": float(np.median(r)),
                "ratio_media": float(r.mean()),
                "ratio_min": float(r.min()), "ratio_max": float(r.max()),
                "scarto_assoluto_mediano_pct": float(np.median(np.abs(both["scarto%"]))),
                "correlazione": float(np.corrcoef(both.ps_value, both.tm_value)[0, 1]),
                "per_club": both[["team", "ps_value", "tm_value", "scarto%"]]
                             .to_dict("records"),
            },
            "celle_mancanti": buchi[["team", "tm_value", "squad_size", "avg_age"]]
                               .to_dict("records"),
        }

    (OUT / "recupero_squad_value_tm.json").write_text(
        json.dumps(report, indent=2, default=str))
    print(f"\n-> {(OUT / 'recupero_squad_value_tm.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
