import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
p=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/partite_sofa.pkl')
p['Data']=pd.to_datetime(p['Data'],format='%d.%m.%Y')
print("date:",p.Data.min().date(),"->",p.Data.max().date())
# ---------- R8 ARBITRO ----------
r=p.dropna(subset=['Arbitro'])
g=r.groupby('Arbitro').agg(n=('Arbitro','size'), u_part=('Partite arbitro','nunique'),
                           u_gial=('Gialli arbitro','nunique'), u_ross=('Rossi arbitro','nunique'),
                           d0=('Data','min'), d1=('Data','max'), val=('Partite arbitro','first'))
multi=g[g.n>1]
print("\n=== R8 storico arbitro ===")
print("arbitri distinti:",len(g),"| con >1 partita nel file:",len(multi))
print("di questi, 'Partite arbitro' COSTANTE su tutte le sue partite:",int((multi.u_part==1).sum()),
      " -> variabile:",int((multi.u_part>1).sum()))
print("Gialli costante:",int((multi.u_gial==1).sum()),"| Rossi costante:",int((multi.u_ross==1).sum()))
lung=multi[(multi.d1-multi.d0).dt.days>200]
print("arbitri con >200 giorni fra prima e ultima partita nel file:",len(lung),
      "| di questi con valore costante:",int((lung.u_part==1).sum()))
# il valore e' >= al numero di partite nel file?
print("arbitri in cui 'Partite arbitro' < numero di sue partite nel file:",int((g.val<g.n).sum()))
# incrocio con games.csv: quante partite ha diretto fino al 2025-07-01 vs fino al 2026-08-11
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
arb=tutte.dropna(subset=['arbitro']).drop_duplicates('game_id')
def conta(fino): 
    s=arb[arb.date<fino].groupby('arbitro').size(); return s
c25=conta(pd.Timestamp('2025-07-01')); c26=conta(pd.Timestamp('2026-08-11'))
com=g.join(c25.rename('nostre_al_2025'),how='inner').join(c26.rename('nostre_al_2026'))
print("\narbitri agganciabili per nome a games.csv:",len(com),"su",len(g))
com['diff25']=com.val-com.nostre_al_2025; com['diff26']=com.val-com.nostre_al_2026
print("mediana(Partite arbitro - nostre al 01/07/2025):",com.diff25.median())
print("mediana(Partite arbitro - nostre all'11/08/2026):",com.diff26.median())
print("quante volte Partite arbitro < nostre_al_2026 (impossibile se e' un totale all'estrazione):",int((com.diff26<0).sum()),"su",len(com))
print("quante volte Partite arbitro < nostre_al_2025:",int((com.diff25<0).sum()))
p.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p.pkl')
