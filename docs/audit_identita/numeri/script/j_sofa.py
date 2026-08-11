import sys, pandas as pd
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI
pd.set_option("display.width",220)

g = pd.read_csv("files/sofascore_coppe_europee_2526/giocatori.csv.gz")
print("righe:", len(g), "| 'ID giocatore' non nulli:", g["ID giocatore"].notna().sum())
print("id distinti:", g["ID giocatore"].nunique(), "| nomi distinti:", g["Giocatore"].nunique())
print("tipo:", g["ID giocatore"].dtype, "| min/max:", g["ID giocatore"].min(), g["ID giocatore"].max())

# R6: l'id e' STABILE? un id -> piu' nomi? un nome -> piu' id?
a = g.groupby("ID giocatore")["Giocatore"].nunique()
b = g.groupby("Giocatore")["ID giocatore"].nunique()
print("\nid sotto >1 nome:", (a>1).sum(), " | nomi sotto >1 id (OMONIMI):", (b>1).sum())
print("persone coinvolte negli omonimi:", g[g["Giocatore"].isin(b[b>1].index)]["ID giocatore"].nunique())
for n in b[b>1].index[:12]:
    s=g[g["Giocatore"]==n]
    print("   ", n, sorted(set(zip(s["ID giocatore"], s["Data di nascita"].astype(str)))))

# e' lo stesso spazio di id dei nostri player_id?
nomi = pd.read_csv(C.DATA_DIR/"players.csv.gz", usecols=["player_id","name","date_of_birth"])
sofa_ids=set(g["ID giocatore"].dropna().astype(int)); nostri=set(nomi["player_id"])
print("\nid SofaScore che esistono anche come player_id nostro:", len(sofa_ids & nostri), "su", len(sofa_ids))
# controprova: se fosse lo stesso spazio, i nomi coinciderebbero
comuni = sorted(sofa_ids & nostri)[:200]
mm = nomi[nomi["player_id"].isin(comuni)].set_index("player_id")["name"]
tab = g.drop_duplicates("ID giocatore").set_index("ID giocatore")["Giocatore"]
acc = sum(1 for i in comuni if i in mm.index and PI.normalizza_nome(mm[i]) & PI.normalizza_nome(tab.get(i,"")))
print("su", len(comuni), "id in comune, quanti hanno ANCHE il nome compatibile:", acc)
