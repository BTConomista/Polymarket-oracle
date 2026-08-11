import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import player_stats as PS, player_identity as PI

d = PS.load_player_matches(tutte=True)
print("righe totali (solo_campionato=True):", len(d))
print(d.groupby("lega").size())
out = PI.collega_per_eliminazione(d)
out.to_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
print("agganciate:", out["player_id"].notna().sum(), "/", len(out))
print("scoperte:", out["player_id"].isna().sum())
print(out.groupby("lega")["player_id"].apply(lambda s: s.isna().sum()))
sc = out[out["player_id"].isna()]
print(sc[["lega","data","Squadra","Avversario","Giocatore"]].to_string())
