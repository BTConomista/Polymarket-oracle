import pandas as pd, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
df=tutte.sort_values(["club_id","date","game_id"]).copy()
df["spell_id"]=(df["manager_key"]!=df.groupby("club_id")["manager_key"].shift()).cumsum()
out=A._aggrega_mandati(df,"spell_id").sort_values(["club_id","data_da"]).reset_index(drop=True)
prima=out.groupby("club_id")["manager_key"].shift(); dopo=out.groupby("club_id")["manager_key"].shift(-1)
out["interruzione"]=prima.notna()&(prima==dopo)
ass=out["interruzione"]&(out["partite"]<=1)
spell=out["spell_id"].to_list(); gruppo=list(spell); ospite={}
club_corrente=vivo=vivo_key=None
for i in range(len(out)):
    club=out["club_id"].iloc[i]; k=out["manager_key"].iloc[i]
    if club!=club_corrente: club_corrente,vivo,vivo_key=club,None,None
    if vivo is not None and k==vivo_key:          # FIX: riaggancio all'ultimo SOPRAVVISSUTO
        gruppo[i]=vivo
    elif ass.iloc[i] and vivo is not None:
        ospite[spell[i]]=vivo; continue
    vivo, vivo_key = gruppo[i], k
mappa=dict(zip(spell,gruppo)); df["gruppo"]=df["spell_id"].map(mappa)
ass_set=set(ospite); vive=df[~df["spell_id"].isin(ass_set)]
r=A._aggrega_mandati(vive,"gruppo").rename(columns={"gruppo":"spell_id"}).sort_values(["club_id","data_da"]).reset_index(drop=True)
altrui=df[df["spell_id"].isin(ass_set)].copy(); altrui["ospite"]=altrui["spell_id"].map(ospite)
c=altrui.groupby("ospite").agg(partite_altrui=("game_id","size"),interruzioni=("spell_id","nunique"))
r=r.merge(c,left_on="spell_id",right_index=True,how="left")
r[["partite_altrui","interruzioni"]]=r[["partite_altrui","interruzioni"]].fillna(0).astype(int)
dup=(r.manager_key==r.groupby("club_id").manager_key.shift())
mk=dict(zip(spell,out["manager_key"]))
print("FIX -> mandati:",len(r)," consecutivi stesso allenatore:",int(dup.sum()))
print("     assorbite:",len(ospite)," di cui host con lo stesso nome:",sum(1 for s,h in ospite.items() if mk[s]==mk.get(h)))
print("     partite conservate:",r.partite.sum()+r.partite_altrui.sum(),"su",len(tutte))
cid=int(r[r.club_name.str.contains('Nottingham',na=False)].club_id.iloc[0])
print(r[(r.club_id==cid)&r.data_da.between('2023-06-01','2026-01-01')][['manager_key','data_da','data_a','partite','interruzioni','partite_altrui']].to_string())
old=A.panchine(tutte,ricuci=True)
print("\nprima del fix: mandati",len(old)," consecutivi stesso allenatore",int((old.sort_values(['club_id','data_da']).manager_key==old.sort_values(['club_id','data_da']).groupby('club_id').manager_key.shift()).sum()))
