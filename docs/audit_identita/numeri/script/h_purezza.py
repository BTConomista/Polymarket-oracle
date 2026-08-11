import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI, player_stats as PS
pd.set_option("display.width",220)

d = PS.load_player_matches(tutte=True)
p1 = PI.collega(d)                      # solo primo passaggio
print("PASSO 1 (data+token):", p1["player_id"].notna().sum(), "/", len(p1))
out = pd.read_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
print("dopo eliminazione+intersezione+registro:", out["player_id"].notna().sum(), "/", len(out))
print("aggiunte dai passaggi 2/3/registro:", out["player_id"].notna().sum()-p1["player_id"].notna().sum())

ok = out[out["player_id"].notna()].copy(); ok["player_id"]=ok["player_id"].astype(int)
app = C._load_appearances()
a = app[app["date"]>=pd.Timestamp("2025-07-01")][["player_id","date","player_club_id","competition_id"]]
m = ok[["player_id","data"]].rename(columns={"data":"date"}).merge(a, on=["player_id","date"], how="left")
assert len(m)==len(ok), (len(m),len(ok))
ok["_cid"]=m["player_club_id"].to_numpy(); ok["_comp"]=m["competition_id"].to_numpy()

pur = ok.groupby("Squadra")["_cid"].agg(lambda s: s.value_counts(normalize=True).max())
print("\nsquadre diretta:", len(pur), "| purezza minima:", round(pur.min(),6))
print(pur[pur<1].to_string())

lega2comp = {"serie_a":"IT1","premier_league":"GB1","la_liga":"ES1","bundesliga":"L1","ligue_1":"FR1"}
ok["_att"]=ok["lega"].map(lega2comp)
bad = ok[ok["_comp"]!=ok["_att"]]
print("\nrighe la cui presenza player-scores e' in un'ALTRA competizione:", len(bad))
print(bad.groupby(["lega","_comp"]).size().to_string())
print(bad[["lega","data","Squadra","Avversario","Giocatore","player_id","_comp"]].head(20).to_string())
