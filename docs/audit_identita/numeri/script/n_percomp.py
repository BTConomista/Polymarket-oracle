import sys, pandas as pd, math, collections
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI
g = pd.read_csv("files/sofascore_coppe_europee_2526/giocatori.csv.gz")
g["data"]=pd.to_datetime(g["Data"], format="%d.%m.%Y", errors="coerce")
ana=g.drop_duplicates("ID giocatore")[["ID giocatore","Giocatore","Data di nascita"]].copy()
ana["nasc"]=pd.to_datetime(ana["Data di nascita"],format="%d.%m.%Y",errors="coerce"); ana["tok"]=ana["Giocatore"].map(PI.normalizza_nome)
nomi=pd.read_csv(C.DATA_DIR/"players.csv.gz",usecols=["player_id","name","date_of_birth"])
nomi["nasc"]=pd.to_datetime(nomi["date_of_birth"],errors="coerce"); nomi["tok"]=nomi["name"].map(PI.normalizza_nome)
byd=collections.defaultdict(list)
for r in nomi.dropna(subset=["nasc"]).itertuples(): byd[r.nasc].append((r.player_id,r.tok))
mappa={}
for r in ana.dropna(subset=["nasc"]).itertuples():
    c=byd.get(r.nasc,[])
    if not c: continue
    pts=sorted(((len(t&r.tok),p) for p,t in c),reverse=True)
    if pts[0][0]>0 and (len(pts)==1 or pts[0][0]>pts[1][0]): mappa[getattr(r,"_1")]=pts[0][1]
app=C._load_appearances(); pres=set(zip(app["player_id"],app["date"]))
gio=g[g["Minuti giocati"].fillna(0)>0].copy(); gio["pid"]=gio["ID giocatore"].map(mappa)
v=gio[gio["pid"].notna()].copy()
v["conferma"]=[(int(p),d) in pres for p,d in zip(v["pid"],v["data"])]
def ic(s):
    n=len(s); k=s.sum(); p=k/n; se=math.sqrt(p*(1-p)/n)
    return f"{k}/{n} = {p:.4f} IC95 [{max(0,p-1.96*se):.4f},{min(1,p+1.96*se):.4f}]"
print("conferma per competizione:")
for c,s in v.groupby("Competizione")["conferma"]: print(f"  {c:20s} {ic(s)}")
print("\nConference: fase preliminare vs principale")
conf=v[v["Competizione"]=="Conference League"]
prelim=conf["Turno"].str.contains("preliminare|Spareggi",case=False,na=False)
print("  preliminari/spareggi:", ic(conf[prelim]["conferma"]))
print("  fase principale     :", ic(conf[~prelim]["conferma"]))
print("\ncopertura del ponte per competizione (righe con pid / righe tot):")
gio2=g.copy(); gio2["pid"]=gio2["ID giocatore"].map(mappa)
print(gio2.groupby("Competizione")["pid"].agg(lambda s:f"{s.notna().sum()}/{len(s)} = {s.notna().mean():.3f}").to_string())
