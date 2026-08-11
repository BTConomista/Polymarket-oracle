"""Raccoglie TUTTI i nomi di club di TUTTE le fonti del repo."""
import json, glob, unicodedata as ud
import pandas as pd
from pathlib import Path

R = Path("/home/user/Polymarket-oracle")

def fonti() -> dict[str, set[str]]:
    f: dict[str, set[str]] = {}
    for p in sorted(R.glob("data/*_matches.csv")):
        d = pd.read_csv(p, usecols=["home_team", "away_team"])
        f[p.name] = set(d.home_team.dropna()) | set(d.away_team.dropna())
    d = pd.read_csv(R / "files/player_scores/club_names.csv.gz")
    f["club_names.csv.gz"] = set(d.name.dropna())
    d = pd.read_csv(R / "data/coppe_2526/partite.csv", usecols=["casa", "ospite"])
    f["coppe_2526/partite.csv"] = set(d.casa.dropna()) | set(d.ospite.dropna())
    d = pd.read_excel(R / "files/sofascore_coppe_europee_2526/originale_sofascore.xlsx",
                      sheet_name="Partite", usecols=["Casa", "Trasferta"])
    f["sofascore Partite"] = set(d.Casa.dropna()) | set(d.Trasferta.dropna())
    j = json.loads((R / "data/squadre_smarkets_2026_27.json").read_text())
    sm = set()
    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, str): sm.add(o)
    walk(j["per_lega"])
    f["squadre_smarkets_2026_27.json"] = sm
    d = pd.read_csv(R / "data/carriere_wikipedia/tappe.csv.gz", usecols=["club"], low_memory=False)
    f["carriere_wikipedia/tappe"] = set(d.club.dropna().astype(str))
    return f

if __name__ == "__main__":
    for k, v in fonti().items():
        print(f"{k:34s} {len(v):5d} nomi")
