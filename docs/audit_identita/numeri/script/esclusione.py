import sys,json,glob; sys.path.insert(0,'.')
from tool import *
from prova import nome_di
import pandas as pd
sq=json.load(open('/home/user/Polymarket-oracle/data/squadre_smarkets_2026_27.json'))
PAESE={'premier_league':'ENG','ligue_1':'FRA','serie_a':'ITA','la_liga':'ESP','bundesliga':'DEU'}
for lg,nomi in sq['per_lega'].items():
    dirs = sorted(glob.glob(f'/home/user/Polymarket-oracle/data/stagione_2026_2027/club/{PAESE[lg]}/*/anagrafica.json'))
    ana = {}
    for f in dirs:
        d=json.load(open(f)); ana[f.split('/')[-2]] = d
    risolti = {n:A.aggancia(n) for n in nomi}
    ok = {n:c for n,c in risolti.items() if c}
    manca = [n for n,c in risolti.items() if not c]
    if not manca: continue
    # club_id dei nomi_dataset dell'anagrafica
    ana_id = {}
    for slug,d in ana.items():
        nd = d.get('nome_dataset') or d.get('nome_smarkets')
        ana_id[slug] = A.aggancia(nd)
    presi = set(ok.values())
    resto = {s:c for s,c in ana_id.items() if c not in presi}
    print(f'== {lg}: {len(nomi)} nomi smarkets, {len(ok)} risolti; anagrafica {len(ana)} club')
    print('   NON risolti:', manca)
    print('   club dell\'anagrafica non ancora presi:', {s:(c, nome_di(c) if c else None) for s,c in resto.items()})
