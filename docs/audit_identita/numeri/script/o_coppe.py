import sys, pandas as pd
sys.path.insert(0,"/home/user/Polymarket-oracle")
from src.data import careers as C
pd.set_option("display.width",220)
g = pd.read_csv("data/coppe_2526/aggancio_giocatori.csv")
g["data"]=pd.to_datetime(g["data"])
print("scoperte per competizione:"); print(g[g.player_id.isna()].groupby("competizione").size().to_string())
print("\nscoperte: hanno game_id?"); print(g[g.player_id.isna()]["game_id"].notna().value_counts().to_string())
print("\nrighe senza club_id:", g["club_id"].isna().sum(), "| di queste senza player_id:", g[g.club_id.isna()].player_id.isna().sum())

ok=g[g.player_id.notna()].copy(); ok["player_id"]=ok["player_id"].astype(int)
# TEST: due partite diverse lo stesso giorno per lo stesso player_id
ok["_p"]=[tuple(sorted([a,b])) for a,b in zip(ok["squadra"], ok["squadra"])]
dup = ok.groupby(["player_id","data"])["squadra"].nunique()
print("\n(player_id, data) con >1 SQUADRA nelle coppe:", (dup>1).sum(), "su", len(dup))
for (p,d) in dup[dup>1].index[:15]:
    print("   ", p, d.date(), ok[(ok.player_id==p)&(ok.data==d)][["competizione","squadra","nome_diretta"]].to_dict("records"))

# coerenza con le presenze player-scores: stesso giorno, stesso club?
app=C._load_appearances(); a=app[app.date>=pd.Timestamp("2025-07-01")][["player_id","date","player_club_id"]]
a=a.drop_duplicates(["player_id","date"])
m=ok[["player_id","data"]].rename(columns={"data":"date"}).merge(a,on=["player_id","date"],how="left")
ok["_cid"]=m["player_club_id"].to_numpy()
print("\nrighe agganciate senza NESSUNA presenza quel giorno:", ok["_cid"].isna().sum(), f"({ok['_cid'].isna().mean():.3f})")
h=ok[ok["_cid"].notna() & ok["club_id"].notna()]
bad=h[h["_cid"]!=h["club_id"]]
print("righe con club INCOERENTE:", len(bad), "su", len(h), f"({len(bad)/len(h):.4f})")
print(bad.groupby("competizione").size().to_string())
print(bad[["competizione","data","squadra","nome_diretta","player_id","club_id","_cid","metodo"]].head(15).to_string())
