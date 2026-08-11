import pandas as pd, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
out=A.panchine(tutte).sort_values(['club_id','data_da']).reset_index(drop=True)
# rifaccio il ciclo di ricuci per estrarre ospite/assorbibile
assorbibile = out["interruzione"] & (out["partite"] <= 1)
spell=out["spell_id"].to_list() if "spell_id" in out else None
print("spell_id esposto da panchine()?", "spell_id" in out.columns)
