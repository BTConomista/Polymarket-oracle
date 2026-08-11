import sys, pandas as pd
sys.path.insert(0,"/home/user/Polymarket-oracle")
pd.set_option("display.width",220)
out = pd.read_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
ok = out[out.player_id.notna()].copy(); ok["player_id"]=ok["player_id"].astype(int)

# `Ruolo` e' dichiarato STATIC_COLUMNS in player_stats.py: e' vero?
r = ok.groupby("player_id")["Ruolo"].nunique()
print("player_id con >1 `Ruolo` nella stagione:", (r>1).sum(), "su", len(r), f"({(r>1).mean():.3f})")
print("righe interessate:", ok[ok.player_id.isin(r[r>1].index)].shape[0], f"({ok.player_id.isin(r[r>1].index).mean():.3f})")
print(ok[ok.player_id.isin(r[r>1].index)].groupby("Ruolo").size().to_string())
ex = r[r>1].index[:5]
for p in ex:
    s=ok[ok.player_id==p]
    print("  esempio pid",p, s["Giocatore"].iloc[0], dict(s["Ruolo"].value_counts()))

# `Giocatore` come chiave: e' unica DENTRO la squadra?
u = ok.groupby(["Squadra","Giocatore"])["player_id"].nunique()
print("\ncoppie (Squadra, Giocatore) che coprono >1 persona:", (u>1).sum(), "su", len(u))
print(u[u>1].to_string())
import pathlib
reg = pathlib.Path("data/aggancio_manuale.csv")
print("\nregistro manuale:", reg.exists())
if reg.exists():
    m=pd.read_csv(reg); print(m.to_string())
