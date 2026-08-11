import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI, player_stats as PS
pd.set_option("display.width",250); pd.set_option("display.max_columns",50)

out = pd.read_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
k = out[(out["Giocatore"]=="Kiko")]
print("righe diretta 'Kiko' per data:")
print(k.groupby(["data","Squadra"]).size().to_string())
date4 = [pd.Timestamp(x) for x in ["2025-09-13","2025-09-27","2026-03-21","2026-04-25"]]
print("\nnelle 4 date contestate quante righe 'Kiko' ci sono?")
print(k[k["data"].isin(date4)][["data","Squadra","Avversario","player_id","Minuti giocati" if "Minuti giocati" in k.columns else "Giocatore"]].to_string())

app = C._load_appearances()
nomi = pd.read_csv(C.DATA_DIR/"players.csv.gz", usecols=["player_id","name","date_of_birth"])
get = app[(app["player_club_id"]==3709)&(app["date"]>=pd.Timestamp("2025-07-01"))]
print("\nrosa Getafe 2025-26 in player-scores con 'kiko' nel nome:")
ids = get["player_id"].unique()
print(nomi[nomi["player_id"].isin(ids) & nomi["name"].str.lower().str.contains("kiko")])
print("\nGetafe: chi ha giocato nelle 4 date (player-scores)")
for d in date4:
    g = get[get["date"]==d]
    nn = nomi[nomi["player_id"].isin(g["player_id"])]
    print(" ", d.date(), len(g), "presenze;  nomi:", sorted(nn["name"])[:25])
