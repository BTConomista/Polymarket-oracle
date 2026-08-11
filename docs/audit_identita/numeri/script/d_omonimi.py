import sys, pandas as pd, collections
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import player_identity as PI, careers as C

out = pd.read_pickle("/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/out.pkl")
ok = out[out["player_id"].notna()].copy()
ok["player_id"] = ok["player_id"].astype(int)
print("righe agganciate:", len(ok), " player_id distinti:", ok["player_id"].nunique())

# --- 1. OMONIMI: la stessa stringa `Giocatore` -> piu' persone
g = ok.groupby("Giocatore")["player_id"].nunique()
om = g[g > 1]
print("\n[1] stringhe `Giocatore` che mappano a >1 player_id:", len(om), "su", len(g))
print(om.sort_values(ascending=False).head(20))

# --- 2. lo stesso player_id sotto piu' stringhe (alias o collasso?)
h = ok.groupby("player_id")["Giocatore"].nunique()
print("\n[2] player_id sotto >1 stringa `Giocatore`:", (h>1).sum(), "su", len(h))
for pid in h[h>1].index[:25]:
    s = ok[ok["player_id"]==pid]
    print("   ", pid, sorted(set(s["Giocatore"])), sorted(set(s["Squadra"])), sorted(set(s["lega"])))

# --- 3. TEST DISCRIMINANTE: nessuno gioca due partite diverse lo stesso giorno
ok["_partita"] = [tuple(sorted(x)) for x in zip(ok["Squadra"], ok["Avversario"])]
dup = ok.groupby(["player_id","data"])["_partita"].nunique()
print("\n[3] (player_id, data) con >1 partita distinta:", (dup>1).sum(), "su", len(dup))
for (pid,d) in dup[dup>1].index[:40]:
    s = ok[(ok["player_id"]==pid)&(ok["data"]==d)]
    print("   pid", pid, str(d.date()), sorted(set(zip(s["lega"],s["Squadra"],s["Avversario"],s["Giocatore"]))))
