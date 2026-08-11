import sys, pandas as pd, math, collections
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C
app = C._load_appearances()
r = app[app["date"]>=pd.Timestamp("2025-07-01")]
print("competizioni player-scores 2025-26 e presenze:")
print(r.groupby("competition_id").size().sort_values(ascending=False).to_string())
