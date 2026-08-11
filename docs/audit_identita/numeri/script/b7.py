import pandas as pd, numpy as np
from math import sqrt
pd.set_option('display.width',250)
uno=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno4.pkl')
G=45; V=21
def cl(r):
    if r.dom_pre==r.manager_key or r.dom_post==r.manager_key: return 'TITOLARE_SPEZZATO'
    if 0.75<r.sim_dom_pre<1.0 or r.uguale_avversario: return 'SOSPETTO_FONTE'
    gp = r.gap_pre if pd.notna(r.gap_pre) else 9999
    gd = r.gap_post if pd.notna(r.gap_post) else 9999
    if gp>G and gd>G: return 'ISOLATA_FUORI_COPERTURA'
    if r.dom_pre==r.dom_post and r.q_pre>=0.6 and r.q_post>=0.6 and gp<=V and gd<=V: return 'STAND_IN'
    if r.dom_pre!=r.dom_post and min(gp,gd)<=V: return 'TRAGHETTATORE'
    return 'AMBIGUO'
uno['classe4']=uno.apply(cl,axis=1)
print("TUTTE le 172 (1 partita, perimetro):")
print(pd.crosstab(uno.classe4,uno.ruolo,dropna=False))
cpc=uno[uno.verificato_da=='caso_per_caso']
print("\nsolo le %d CASO PER CASO:"%len(cpc))
print(pd.crosstab(cpc.classe4,cpc.ruolo,dropna=False))
cpc=cpc.copy(); cpc['causa']=cpc.nota_verifica.fillna('').str.extract(r'\(([^)]*)\)')[0]
print(); print(pd.crosstab(cpc.classe4,cpc.causa))
def wil(k,n):
    z=1.96;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return (round(c-h,3),round(c+h,3))
print("\nPUREZZA sulle caso_per_caso (classe -> ruolo maggioritario, IC95 Wilson):")
for c,s in cpc.groupby('classe4'):
    top=s.ruolo.value_counts().idxmax(); k=int((s.ruolo==top).sum())
    print(f"  {c:24s} n={len(s):3d}  {top:14s} {k}/{len(s)} = {k/len(s):.2f}  IC95 {wil(k,len(s))}")
print("\ncontrollo: quante ISOLATA hanno il club con <=3 partite in TUTTO il dataset")
tutte=pd.read_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/tutte.pkl')
npc=tutte.groupby('club_id').size()
iso=uno[uno.classe4=='ISOLATA_FUORI_COPERTURA']
print("  partite totali del club: mediana %.0f, min %d, max %d"%(iso.club_id.map(npc).median(),iso.club_id.map(npc).min(),iso.club_id.map(npc).max()))
print("  di questi club, quanti sono in una top5 in quella stagione:", int(tutte[tutte.club_id.isin(iso.club_id)&tutte.is_top5].club_id.nunique()),"su",iso.club_id.nunique())
uno.to_pickle('/tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/uno5.pkl')
