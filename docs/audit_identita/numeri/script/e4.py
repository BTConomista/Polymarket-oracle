import pandas as pd, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
df = tutte.sort_values(["club_id","date","game_id"]).copy()
cambio = df["manager_key"] != df.groupby("club_id")["manager_key"].shift()
df["spell_id"]=cambio.cumsum()
out=A._aggrega_mandati(df,"spell_id").sort_values(["club_id","data_da"]).reset_index(drop=True)
prima=out.groupby("club_id")["manager_key"].shift(); dopo=out.groupby("club_id")["manager_key"].shift(-1)
out["interruzione"]=prima.notna()&(prima==dopo)
ass=out["interruzione"]&(out["partite"]<=1)
spell=out["spell_id"].to_list(); gruppo=list(spell); ospite={}
club_corrente=ultimo_vivo=None
for i in range(len(out)):
    club=out["club_id"].iloc[i]
    if club!=club_corrente: club_corrente,ultimo_vivo=club,None
    if ass.iloc[i] and ultimo_vivo is not None:
        ospite[spell[i]]=ultimo_vivo; continue
    if (i>=2 and spell[i-1] in ospite and out["club_id"].iloc[i-2]==club
        and out["manager_key"].iloc[i]==out["manager_key"].iloc[i-2]):
        gruppo[i]=gruppo[i-2]
    ultimo_vivo=gruppo[i]
mk=dict(zip(spell,out["manager_key"]))
same=[s for s,h in ospite.items() if mk[s]==mk.get(h)]
print("interruzioni assorbite:",len(ospite))
print("di cui attribuite a un mandato dello STESSO allenatore (una partita di X contata come 'partite_altrui' di X):",len(same))
for s in same[:10]:
    print("   ",out[out.spell_id==s][['club_name','manager_key','data_da','partite']].to_string(header=False))
# quante volte gruppo[i]=gruppo[i-2] punta a un gruppo MORTO
morti=[i for i in range(len(out)) if gruppo[i]!=spell[i] and gruppo[i] in ospite]
print("\nriconnessioni che puntano a un mandato gia' assorbito (=merge fallito):",len(morti))
