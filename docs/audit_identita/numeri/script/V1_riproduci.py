import sys, unicodedata as ud
sys.path.insert(0, "/home/user/Polymarket-oracle")
import pandas as pd
from pathlib import Path
from src.data.club_matching import normalizza, Agganciatore

R = Path("/home/user/Polymarket-oracle")
def scr(c):
    try: return ud.name(c).split()[0]
    except ValueError: return "?"

# --- fonte 1: club_names
cn = pd.read_csv(R/"files/player_scores/club_names.csv.gz")
print("club_names righe:", len(cn), "colonne:", list(cn.columns))
mixed = []
for cid, nome in zip(cn.club_id, cn.name):
    if not isinstance(nome,str): continue
    sc = {scr(c) for c in nome if c.isalpha()}
    if len(sc)>1 and "LATIN" in sc:
        mixed.append((cid,nome,sorted(sc)))
print("\n[club_names] mixed-script LATIN+altro:", len(mixed))
for cid,n,sc in mixed:
    print(f"  {cid} {n!r} {sc} -> {sorted(normalizza(n))}")

# --- fonte 2: tappe wikipedia
tp = pd.read_csv(R/"data/carriere_wikipedia/tappe.csv.gz", usecols=["club"], low_memory=False)
nomi = set(tp.club.dropna().astype(str))
print("\ntappe nomi unici:", len(nomi))
mx2=[]
for n in sorted(nomi):
    sc = {scr(c) for c in n if c.isalpha()}
    if len(sc)>1 and "LATIN" in sc:
        mx2.append((n,sorted(sc)))
print("[tappe] mixed-script:", len(mx2))
for n,sc in mx2:
    print(f"  {n!r} {sc} -> {sorted(normalizza(n))}")
