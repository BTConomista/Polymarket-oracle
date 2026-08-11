import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI, player_stats as PS

app = C._load_appearances()
lega2comp = {"serie_a":"IT1","premier_league":"GB1","la_liga":"ES1","bundesliga":"L1","ligue_1":"FR1"}
tot_p1=tot_fin=tot_r=0
for lega,comp in lega2comp.items():
    d = PS.load_player_matches(lega=lega, stagione="2526")
    sub = app[app["competition_id"]==comp]
    p1 = PI.collega(d, sub)
    fin = PI.collega_per_eliminazione(d, sub)
    print(f"{lega:16s} righe {len(d):6d} | passo1 filtrato {p1['player_id'].notna().sum():6d} | finale filtrato {fin['player_id'].notna().sum():6d}")
    tot_p1+=p1["player_id"].notna().sum(); tot_fin+=fin["player_id"].notna().sum(); tot_r+=len(d)
    if lega=="la_liga":
        k=fin[fin["Giocatore"]=="Kiko"]
        print("   Kiko ->", k.groupby("player_id").size().to_dict(), "| scoperte:", k["player_id"].isna().sum())
print(f"\nTOTALE con filtro competizione: passo1 {tot_p1}/{tot_r}, finale {tot_fin}/{tot_r}")
print("(riferimento senza filtro: passo1 51849, finale 54270)")
