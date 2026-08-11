import pandas as pd, numpy as np, sys, difflib
pd.set_option('display.width',250)
uno = pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno3.pkl')
reg = pd.read_csv('/home/user/Polymarket-oracle/data/allenatori_wikidata/registro_incarichi.csv', parse_dates=['nostro_da'])
uno = uno.merge(reg[['club_id','manager_key','nostro_da','nota_verifica']],
                left_on=['club_id','manager_key','data_da'],
                right_on=['club_id','manager_key','nostro_da'],how='left')
print("1-partita per fonte della verifica:"); print(uno.verificato_da.value_counts())
print(pd.crosstab(uno.verificato_da, uno.ruolo))
# riclassifica
def classifica(r):
    if r.dom_pre==r.manager_key or r.dom_post==r.manager_key: return 'TITOLARE_SPEZZATO'
    if r.uguale_avversario or (0.75 < r.sim_dom_pre < 1.0): return 'SOSPETTO_FONTE'
    if r.n_pre==0 or r.n_post==0: return 'BORDO'
    if r.dom_pre==r.dom_post and r.q_pre>=0.6 and r.q_post>=0.6: return 'STAND_IN'
    if r.dom_pre!=r.dom_post: return 'TRAGHETTATORE'
    return 'AMBIGUO'
uno['classe3']=uno.apply(classifica,axis=1)
print("\nTUTTE le 172:"); print(pd.crosstab(uno.classe3, uno.ruolo, dropna=False))
cpc = uno[uno.verificato_da=='caso_per_caso']
print("\nSOLO le %d verificate CASO PER CASO (verita' vera):"%len(cpc))
print(pd.crosstab(cpc.classe3, cpc.ruolo, dropna=False))
def wilson(k,n):
    if n==0: return (np.nan,np.nan)
    from math import sqrt
    z=1.96; p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(c-h,3),round(c+h,3))
for cl in ['STAND_IN','TRAGHETTATORE','TITOLARE_SPEZZATO','SOSPETTO_FONTE','BORDO']:
    s=cpc[cpc.classe3==cl]
    if len(s)==0: continue
    for target in ['vice','traghettatore','titolare']:
        k=int((s.ruolo==target).sum())
        if k: print(f"  {cl:18s} -> {target:14s} {k}/{len(s)} = {k/len(s):.2f} IC95 {wilson(k,len(s))}")
print("\n--- Ricardo Gomes: competizioni delle sue 3 partite e di quelle di Bedouet ---")
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
b=tutte[(tutte.club_name=='FC Girondins Bordeaux')&(tutte.date.between('2018-09-01','2018-12-31'))]
print(b[['date','competition_id','allenatore','avversario_name']].sort_values('date').to_string())
uno.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno4.pkl')
