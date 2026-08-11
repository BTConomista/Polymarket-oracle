import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad')
from tool import *
import pandas as pd
sofa = pd.read_csv('/home/user/Polymarket-oracle/files/sofascore_coppe_europee_2526/giocatori.csv.gz', usecols=['Squadra','Avversario','Competizione','Turno','Data'])
nomi = sorted(set(sofa['Squadra'].dropna())|set(sofa['Avversario'].dropna()))
ass=[n for n in nomi if len(A.candidati(n))==0]
amb=[n for n in nomi if len(A.candidati(n))>1]
print(f"ASSENTI {len(ass)}"); [print(' ',n) for n in ass]
print(f"AMBIGUI {len(amb)}")
for n in amb:
    c=A.candidati(n)
    print(' ',n,'->',[(i, CN[CN.club_id==i]['name'].iloc[0]) for i in c])
