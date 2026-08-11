import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
m = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/mandati.pkl')
perim = tutte[tutte.is_top5 & tutte.season.isin(A.STAGIONI)]
club_p = set(perim.club_id); d0,d1 = perim.date.min(), perim.date.max()
fin = m[m.club_id.isin(club_p) & (m.data_a>=d0) & (m.data_da<=d1)].copy()
print("mandati club-perimetro finestra:", len(fin), " di 1 partita:", int((fin.partite==1).sum()),
      " interruzioni:", int(fin.interruzione.sum()))
reg = pd.read_csv('data/allenatori_wikidata/registro_incarichi.csv', parse_dates=['nostro_da','nostro_a'])
j = fin.merge(reg[['club_id','manager_key','nostro_da','ruolo','in_carica','verificato_da','verdetto']],
              left_on=['club_id','manager_key','data_da'], right_on=['club_id','manager_key','nostro_da'], how='left')
print("agganciati al registro:", int(j.ruolo.notna().sum()), "/", len(j))
print(pd.crosstab(j.partite==1, j.ruolo, dropna=False))
print(pd.crosstab(j.interruzione, j.ruolo, dropna=False))
j.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/fin.pkl')
