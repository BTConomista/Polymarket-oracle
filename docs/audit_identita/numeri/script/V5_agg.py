import sys
sys.path.insert(0,"/home/user/Polymarket-oracle")
sys.path.insert(0,"/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad")
import pandas as pd, importlib
import src.data.club_matching as CM
R="/home/user/Polymarket-oracle/"
cn = pd.read_csv(R+"files/player_scores/club_names.csv.gz")

# --- registro: chi contiene taganrog / brw / vik / bik / vologda ?
for tok in ["taganrog","brw","vik","bik","vologda","cherkasy","cherkashchyna","zacharo","olympiacos"]:
    hits=[(int(c),n) for c,n in zip(cn.club_id,cn.name) if tok in str(n).lower()]
    print(f"{tok:15s} {len(hits)} -> {hits[:8]}")
