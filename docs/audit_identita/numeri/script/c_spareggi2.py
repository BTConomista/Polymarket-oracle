import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import player_stats as PS, player_identity as PI, careers as C

tutto = PS.load_player_matches(tutte=True, solo_campionato=False)
o = PI.collega_per_eliminazione(tutto)
o.to_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out_tutto.pkl")
print("TOTALE con spareggi:", o["player_id"].notna().sum(), "/", len(o))
f = o[o["Fase"].isin(PS.FASI_FUORI_CAMPIONATO)] if "Fase" in o else None
print("fuori campionato agganciate:", f["player_id"].notna().sum(), "/", len(f))
print(f.groupby(["lega","data"]).apply(lambda g: (g["player_id"].isna().sum(), len(g))))

app = C._load_appearances()
a = app[app["date"] >= pd.Timestamp("2025-07-01")]
for d in sorted(f["data"].unique()):
    d = pd.Timestamp(d)
    print(d.date(), "presenze player-scores quel giorno:", (a["date"]==d).sum(),
          "competizioni:", sorted(a.loc[a["date"]==d,"competition_id"].unique()))
