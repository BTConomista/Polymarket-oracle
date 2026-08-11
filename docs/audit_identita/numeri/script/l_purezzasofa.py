import sys, pandas as pd, collections
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI

g = pd.read_csv("files/sofascore_coppe_europee_2526/giocatori.csv.gz")
g["data"] = pd.to_datetime(g["Data"], format="%d.%m.%Y", errors="coerce")
ana = g.drop_duplicates("ID giocatore")[["ID giocatore","Giocatore","Data di nascita"]].copy()
ana["nasc"] = pd.to_datetime(ana["Data di nascita"], format="%d.%m.%Y", errors="coerce")
ana["tok"]  = ana["Giocatore"].map(PI.normalizza_nome)

nomi = pd.read_csv(C.DATA_DIR/"players.csv.gz", usecols=["player_id","name","date_of_birth"])
nomi["nasc"]=pd.to_datetime(nomi["date_of_birth"], errors="coerce"); nomi["tok"]=nomi["name"].map(PI.normalizza_nome)
byd = collections.defaultdict(list)
for r in nomi.dropna(subset=["nasc"]).itertuples(): byd[r.nasc].append((r.player_id, r.tok))
date_note = set(byd)

mappa={}; senza_data=0; senza_token=0; amb=0
for r in ana.dropna(subset=["nasc"]).itertuples():
    sid = getattr(r,"_1")
    if r.nasc not in date_note: senza_data+=1; continue
    pts = sorted(((len(t & r.tok), p) for p,t in byd[r.nasc]), reverse=True)
    if pts[0][0]==0: senza_token+=1
    elif len(pts)==1 or pts[0][0]>pts[1][0]: mappa[sid]=pts[0][1]
    else: amb+=1
print(f"agganciati {len(mappa)} | nessun nato quel giorno {senza_data} | nato ma nome incompatibile {senza_token} | ambigui {amb}")

# PUREZZA: chi e' sceso in campo in coppa il giorno D deve avere una presenza quel giorno
app = C._load_appearances()
presenze = set(zip(app["player_id"], app["date"]))
gio = g[g["Minuti giocati"].fillna(0) > 0].copy()
gio["pid"] = gio["ID giocatore"].map(mappa)
v = gio[gio["pid"].notna()]
hit = [(p,d) in presenze for p,d in zip(v["pid"].astype(int), v["data"])]
import math
n=len(hit); k=sum(hit); p=k/n; se=math.sqrt(p*(1-p)/n)
print(f"\nrighe con minuti>0 e ponte: {n} | presenza player-scores nella STESSA data: {k} ({p:.4f}) IC95 [{p-1.96*se:.4f},{p+1.96*se:.4f}]")
mis = v[[not h for h in hit]]
print("\nmancate, per competizione SofaScore:"); print(mis.groupby("Competizione").size().to_string())
print("\nmancate, per turno (top 8):"); print(mis.groupby("Turno").size().sort_values(ascending=False).head(8).to_string())
# controprova negativa: un ponte a caso quanto farebbe?
import numpy as np
rng=np.random.default_rng(0); tutti=nomi["player_id"].to_numpy()
fake=rng.choice(tutti, size=n)
print("\ncontrollo placebo (id a caso):", sum((int(a),b) in presenze for a,b in zip(fake, v["data"]))/n)
