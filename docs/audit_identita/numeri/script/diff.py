import sys, json, glob
import pandas as pd
sys.path.insert(0,'/home/user/Polymarket-oracle')
import src.data.club_matching as cm

B='/home/user/Polymarket-oracle/'
reg = pd.read_csv(B+'files/player_scores/club_names.csv.gz')

# raccogli tutti i nomi delle 4 fonti + registro (come nel censimento)
nomi=set()
for f in sorted(glob.glob(B+'files/sofascore_coppe_europee_2526/*.csv.gz')):
    d=pd.read_csv(f, low_memory=False)
    for c in ('Squadra','Casa','Trasferta','Avversario'):
        if c in d.columns: nomi|=set(d[c].dropna().unique())
j=json.load(open(B+'data/squadre_smarkets_2026_27.json'))
for l in j['per_lega'].values(): nomi|=set(l)
for f in sorted(glob.glob(B+'data/coppe_2526/*.csv')):
    d=pd.read_csv(f, low_memory=False)
    for c in d.columns:
        if any(k in c.lower() for k in ('squadra','casa','trasferta','club','avversario')) and d[c].dtype==object:
            nomi|=set(d[c].dropna().unique())
for lg in ('serie_a','premier_league','la_liga','bundesliga','ligue_1'):
    d=pd.read_csv(B+f'data/{lg}_matches.csv', low_memory=False)
    for c in ('home_team','away_team'): nomi|=set(d[c].dropna().unique())
nomi |= set(reg['name'].dropna())
nomi = sorted(n for n in nomi if isinstance(n,str))
print('nomi:', len(nomi))

A0 = cm.Agganciatore(reg)
pre_norm = {n: cm.normalizza(n) for n in nomi}
pre_cand = {n: A0.candidati(n) for n in nomi}
pre_idx  = dict(A0._per_id)

# --- patch
cm._TRADUZIONE = str.maketrans({
    "ø":"o","Ø":"o","ł":"l","Ł":"l","đ":"d","Đ":"d",
    "ß":"ss","æ":"ae","Æ":"ae","œ":"oe","ð":"d","þ":"th","ı":"i",
    "ə":"a","Ə":"a","ħ":"h","Ħ":"h",
})
A1 = cm.Agganciatore(reg)
post_norm = {n: cm.normalizza(n) for n in nomi}
post_cand = {n: A1.candidati(n) for n in nomi}
post_idx  = dict(A1._per_id)

dn=[n for n in nomi if pre_norm[n]!=post_norm[n]]
dc=[n for n in nomi if pre_cand[n]!=post_cand[n]]
print('normalizza cambiata:', len(dn), dn)
print('candidati cambiati:', len(dc))
for n in dc: print('  ',repr(n), pre_cand[n],'->',post_cand[n])
print('indice registro cambiato:', pre_idx!=post_idx, [k for k in pre_idx if pre_idx[k]!=post_idx.get(k)])
# nessun nome diventa AMBIGUO
peggio=[n for n in nomi if len(pre_cand[n])==1 and len(post_cand[n])!=1]
print('nomi che erano univoci e non lo sono piu:', peggio)
# collisioni: qualche altro nome ora condivide l'insieme dei token con quelli cambiati
for n in dn:
    coll=[m for m in nomi if m!=n and post_norm[m]==post_norm[n]]
    print('collisioni per',repr(n),'->',sorted(post_norm[n]),':',coll)
