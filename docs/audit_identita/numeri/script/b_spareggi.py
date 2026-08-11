import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import player_stats as PS, player_identity as PI

tutto = PS.load_player_matches(tutte=True, solo_campionato=False)
print("righe con spareggi:", len(tutto))
print(tutto.groupby(["lega","Fase"], dropna=False).size())
fuori = tutto[tutto["Fase"].isin(PS.FASI_FUORI_CAMPIONATO)] if "Fase" in tutto else None
print("\nrighe fuori campionato:", len(fuori))
o = PI.collega_per_eliminazione(fuori)
print("agganciate fuori campionato:", o["player_id"].notna().sum(), "/", len(o))
print(o.groupby("lega")["player_id"].apply(lambda s: (s.isna().sum(), len(s))))
o.to_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/fuori.pkl")
