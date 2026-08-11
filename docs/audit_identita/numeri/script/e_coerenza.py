import sys, pandas as pd, collections
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import player_identity as PI, careers as C

out = pd.read_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
ok = out[out["player_id"].notna()].copy(); ok["player_id"]=ok["player_id"].astype(int)

app = C._load_appearances()
a = app[app["date"] >= pd.Timestamp("2025-07-01")][["player_id","date","player_club_id"]]

# club dedotto per squadra dalle righe agganciate (stessa logica del modulo)
m = ok[["player_id","data"]].rename(columns={"data":"date"}).merge(a, on=["player_id","date"], how="left")
ok["_cid"] = m["player_club_id"].to_numpy()
print("righe agganciate SENZA presenza player-scores quel giorno:", ok["_cid"].isna().sum())
club = ok.groupby("Squadra")["_cid"].agg(lambda s: s.value_counts().idxmax() if s.notna().any() else None)
ok["_atteso"] = ok["Squadra"].map(club)
bad = ok[ok["_cid"].notna() & (ok["_cid"] != ok["_atteso"])]
print("righe con club INCOERENTE (presenza in un altro club quel giorno):", len(bad))
print(bad[["lega","data","Squadra","Giocatore","player_id","_cid","_atteso"]].head(30).to_string())

# --- OMONIMI POTENZIALI nell'anagrafica dei giocatori attivi 2025-26 top5
attivi = sorted(app[(app["date"]>=pd.Timestamp("2025-07-01")) & app["competition_id"].isin(C.TOP5)]["player_id"].unique())
nomi = pd.read_csv(C.DATA_DIR/"players.csv.gz", usecols=["player_id","name"])
nomi = nomi[nomi["player_id"].isin(attivi)]
nomi["tok"] = nomi["name"].map(lambda n: "_".join(sorted(PI.normalizza_nome(n))))
gg = nomi.groupby("tok")["player_id"].nunique()
print("\nGIOCATORI attivi 5 leghe 2025-26 (player-scores):", len(nomi))
print("insiemi-token condivisi da >1 persona:", (gg>1).sum(), "-> persone coinvolte:", nomi[nomi["tok"].isin(gg[gg>1].index)].shape[0])
for t in gg[gg>1].index:
    s = nomi[nomi["tok"]==t]
    print("   ", t, list(zip(s["player_id"], s["name"])))
