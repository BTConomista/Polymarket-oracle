import sys; sys.path.insert(0,'.')
from tool import *
from prova import nome_di
import pandas as pd
CP = pd.read_csv('/home/user/Polymarket-oracle/data/coppe_2526/partite.csv')
lungo = pd.concat([
    CP[['competizione','paese','turno','casa','divisione_casa','sigla_divisione_casa']].rename(
        columns={'casa':'squadra','divisione_casa':'divisione','sigla_divisione_casa':'sigla'}),
    CP[['competizione','paese','turno','ospite','divisione_ospite','sigla_divisione_ospite']].rename(
        columns={'ospite':'squadra','divisione_ospite':'divisione','sigla_divisione_ospite':'sigla'}),
])
def st(n):
    c=A.candidati(n); return 'univoco' if len(c)==1 else ('ambiguo' if len(c)>1 else 'assente')
nomi = sorted(lungo.squadra.dropna().unique())
S = {n:st(n) for n in nomi}
lungo['stato'] = lungo.squadra.map(S)
print('--- per nome unico')
prof = lungo.drop_duplicates('squadra').groupby(['competizione','stato']).size().unstack(fill_value=0)
print(prof.to_string())
print()
ass = [n for n in nomi if S[n]=='assente']
sub = lungo[lungo.stato=='assente'].drop_duplicates('squadra')
print('assenti totali:', len(ass))
print(sub.groupby('competizione').size().to_string())
print()
print('assenti per divisione (Coupe de France):')
print(sub[sub.competizione.str.contains('Coupe', case=False, na=False)].groupby('divisione', dropna=False).size().sort_values(ascending=False).to_string())
