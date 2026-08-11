import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI
pd.set_option("display.width",200)

out = pd.read_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
ok = out[out["player_id"].notna()].copy(); ok["player_id"]=ok["player_id"].astype(int)
clubs = pd.read_csv(C.CLUBS, usecols=["club_id","name"]).set_index("club_id")["name"]
nomi  = pd.read_csv(C.DATA_DIR/"players.csv.gz", usecols=["player_id","name","date_of_birth","current_club_id"]).set_index("player_id")

for nome in ["Kiko","Wesley","Vitinha","Lopez David","Gueye Idrissa","Gonzalez Nicolas"]:
    s = ok[ok["Giocatore"]==nome]
    print("\n===", nome, "| righe:", len(s))
    for pid, g in s.groupby("player_id"):
        r = nomi.loc[pid]
        print(f"   pid={pid} '{r['name']}' nato {r['date_of_birth']} | squadre diretta: {sorted(set(g['Squadra']))} | n={len(g)}")

app = C._load_appearances()
print("\n--- Kiko 934031: presenze 2025-26 per club")
a = app[(app["player_id"]==934031)&(app["date"]>=pd.Timestamp("2025-07-01"))]
print(a.groupby(["player_club_id","competition_id"]).size())
for cid in a["player_club_id"].unique(): print("   club",cid,"=",clubs.get(cid))
print("club 3709 =", clubs.get(3709), "| club 979 =", clubs.get(979))
print("\nchi altro e' 'Kiko' nell'anagrafica fra gli agganciati Getafe:")
print(ok[(ok['Giocatore']=='Kiko')].groupby(['player_id','Squadra']).size())
