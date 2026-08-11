import sys, pandas as pd, collections
sys.path.insert(0, "/home/user/Polymarket-oracle")
from src.data import careers as C, player_identity as PI

g = pd.read_csv("files/sofascore_coppe_europee_2526/giocatori.csv.gz")
ana = g.drop_duplicates("ID giocatore")[["ID giocatore","Giocatore","Data di nascita","Nazionalità"]].copy()
ana["nasc"] = pd.to_datetime(ana["Data di nascita"], format="%d.%m.%Y", errors="coerce")
print("anagrafica SofaScore:", len(ana), "| con data di nascita:", ana["nasc"].notna().sum())

nomi = pd.read_csv(C.DATA_DIR/"players.csv.gz", usecols=["player_id","name","date_of_birth","country_of_citizenship"])
nomi["nasc"] = pd.to_datetime(nomi["date_of_birth"], errors="coerce")
print("anagrafica player-scores:", len(nomi), "| con data di nascita:", nomi["nasc"].notna().sum())
nomi["tok"] = nomi["name"].map(PI.normalizza_nome)
ana["tok"]  = ana["Giocatore"].map(PI.normalizza_nome)

# --- METODO A: (data di nascita, insieme token) esatto
idx = collections.defaultdict(list)
for r in nomi.dropna(subset=["nasc"]).itertuples():
    idx[(r.nasc, r.tok)].append(r.player_id)
uni=amb=zero=0; mappa={}
for r in ana.dropna(subset=["nasc"]).itertuples():
    c = idx.get((r.nasc, r.tok), [])
    if len(c)==1: uni+=1; mappa[getattr(r,"_1")]=c[0]
    elif len(c)>1: amb+=1
    else: zero+=1
print(f"\n[A] (nascita, token esatti): univoci {uni}, ambigui {amb}, nessun candidato {zero}  (su {ana['nasc'].notna().sum()})")

# --- METODO B: stessa data di nascita + almeno un token in comune, argmax stretto
byd = collections.defaultdict(list)
for r in nomi.dropna(subset=["nasc"]).itertuples():
    byd[r.nasc].append((r.player_id, r.tok))
uniB=ambB=zeroB=0
for r in ana.dropna(subset=["nasc"]).itertuples():
    cand = byd.get(r.nasc, [])
    if not cand: zeroB+=1; continue
    pts = sorted(((len(t & r.tok), p) for p,t in cand), reverse=True)
    if pts[0][0]>0 and (len(pts)==1 or pts[0][0]>pts[1][0]): uniB+=1
    elif pts[0][0]==0: zeroB+=1
    else: ambB+=1
print(f"[B] (nascita + argmax token stretto): univoci {uniB}, ambigui {ambB}, nessuno {zeroB}")

# quante RIGHE coprirebbe il metodo B?
ok_ids = set()
for r in ana.dropna(subset=["nasc"]).itertuples():
    cand = byd.get(r.nasc, [])
    if not cand: continue
    pts = sorted(((len(t & r.tok), p) for p,t in cand), reverse=True)
    if pts[0][0]>0 and (len(pts)==1 or pts[0][0]>pts[1][0]): ok_ids.add(getattr(r,"_1"))
print("righe giocatore-partita coperte dal metodo B:", g["ID giocatore"].isin(ok_ids).sum(), "/", len(g))

# quanto conta per NOI: quante righe sono di squadre dei nostri 5 campionati?
pop = set(C.population())
nostri_sofa = {i for i,p in mappa.items() if p in pop}
print("\nid SofaScore che agganciano a un giocatore delle NOSTRE 5 leghe (metodo A):", len(nostri_sofa))
print("righe corrispondenti:", g["ID giocatore"].isin(nostri_sofa).sum(), "/", len(g))
