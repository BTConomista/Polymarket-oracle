import pandas as pd, numpy as np, sys, time
sys.path.insert(0,'/home/user/Polymarket-oracle')
from src.data import allenatori as A
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
AS='2020-01-01'
t=time.time(); e_full=A.esperienza_prima(AS,tutte); t1=time.time()-t
e_trunc=A.esperienza_prima(AS,tutte[tutte.date<pd.Timestamp(AS)])
print("tempo di una chiamata su 176k righe: %.2f s"%t1)
print("stesse chiavi:", e_full.index.equals(e_trunc.index), len(e_full))
diff=(e_full!=e_trunc)&~(e_full.isna()&e_trunc.isna())
print("celle divergenti troncando il futuro:", int(diff.to_numpy().sum()), "su", e_full.size)

# MUTAZIONE 1: aggiungo 5.000 partite FUTURE inventate a un allenatore reale
fut=tutte.tail(5000).copy(); fut['date']=pd.Timestamp('2030-01-01'); fut['manager_key']='massimiliano allegri'
mut=pd.concat([tutte,fut],ignore_index=True)
e_mut=A.esperienza_prima(AS,mut)
d=(e_full.reindex(e_mut.index)!=e_mut)&~(e_full.reindex(e_mut.index).isna()&e_mut.isna())
print("MUT1 (5.000 partite future): celle cambiate:", int(d.to_numpy().sum()))

# MUTAZIONE 2: creo una competizione NUOVA che nasce nel futuro e ci metto l'esordio finto
fut2=tutte.tail(3).copy(); fut2['date']=pd.Timestamp('2031-01-01'); fut2['competition_id']='ZZZ'
fut2['manager_key']='carlo ancelotti'
mut2=pd.concat([tutte,fut2],ignore_index=True)
e_mut2=A.esperienza_prima(AS,mut2)
d2=(e_full!=e_mut2)&~(e_full.isna()&e_mut2.isna())
print("MUT2 (competizione nuova nel futuro): celle cambiate:", int(d2.to_numpy().sum()))

# MUTAZIONE 3: sposto INDIETRO il bordo di una competizione con una riga passata
old=tutte.copy()
riga=old[old.competition_id=='IT1'].head(1).copy(); riga['date']=pd.Timestamp('2000-01-01')
mut3=pd.concat([tutte,riga],ignore_index=True)
e3=A.esperienza_prima(AS,mut3)
c3=(e_full.censurata!=e3.censurata.reindex(e_full.index))
print("MUT3 (bordo IT1 spostato al 2000, riga PASSATA): allenatori che cambiano censurata:", int(c3.sum()))

# MUTAZIONE 4: la partita DEL GIORNO STESSO entra? (test del confine)
g=tutte[tutte.date==pd.Timestamp(AS)]
print("partite esattamente il", AS, ":", len(g))
if len(g):
    k=g.manager_key.iloc[0]
    print("  allenatore", k, "partite_prima:", int(e_full.loc[k,'partite_prima']),
          "| conteggio diretto date<as_of:", int((tutte[(tutte.manager_key==k)&(tutte.date<pd.Timestamp(AS))]).shape[0]),
          "| date<=as_of:", int((tutte[(tutte.manager_key==k)&(tutte.date<=pd.Timestamp(AS))]).shape[0]))
